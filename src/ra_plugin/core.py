"""Model-independent, crash-safe Research Assurance state core."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import tempfile
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Sequence

from .contracts import (
    Checkpoint,
    ContractError,
    EvidenceRef,
    HumanReview,
    ResearchClaim,
    ResearchSession,
    RunBundle,
    SCHEMA_VERSION,
    UnknownVersionError,
)


class RAError(RuntimeError):
    """Base error for deterministic core failures."""


class ValidationError(RAError, ValueError):
    pass


class ConflictError(RAError, ValueError):
    pass


class IntegrityError(RAError):
    pass


class ReviewUnavailable(RAError):
    """Raised when a reviewed/accepted promotion cannot be proven."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        raise ValidationError("text values must be strings")
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value).strip())


def normalize_list(values: Iterable[Any]) -> list[str]:
    normalized = {normalize_text(item) for item in values}
    return sorted(item for item in normalized if item)


def canonical_json(value: Any) -> str:
    """Stable JSON used for all semantic digests."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def conclusion_digest(claim: ResearchClaim) -> str:
    return digest(
        {
            "claim_id": claim.claim_id,
            "statement": normalize_text(claim.statement),
            "conclusion": normalize_text(claim.conclusion or ""),
            "qualifiers": normalize_list(claim.qualifiers),
        }
    )


def evidence_set_digest(evidence_ids: Iterable[str]) -> str:
    return digest({"evidence_ids": sorted(set(normalize_text(item) for item in evidence_ids))})


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return value


class StateStore:
    """Small JSON store with an integrity envelope and atomic replacement."""

    FORMAT = "ra-plugin-state"

    def __init__(self, path: os.PathLike[str] | str):
        self.path = Path(path)
        self.artifact_dir = self.path.parent / f"{self.path.stem}.artifacts"

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> Optional[ResearchSession]:
        if not self.path.exists():
            return None
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise IntegrityError(f"cannot read state: {exc}") from exc
        if not isinstance(raw, Mapping) or raw.get("format") != self.FORMAT:
            raise IntegrityError("unrecognized or incomplete state envelope")
        if raw.get("complete") is not True:
            raise IntegrityError("state is explicitly incomplete")
        try:
            session_raw = raw["session"]
            expected = raw["integrity_digest"]
        except KeyError as exc:
            raise IntegrityError("state envelope is missing integrity fields") from exc
        actual = digest(session_raw)
        if not isinstance(expected, str) or not hashlib.sha256(bytes.fromhex(actual)).hexdigest():
            # The second check intentionally avoids trusting a non-string value.
            raise IntegrityError("invalid integrity digest")
        if actual != expected:
            raise IntegrityError("state integrity digest mismatch")
        try:
            return ResearchSession.from_dict(session_raw)
        except (ContractError, UnknownVersionError, TypeError) as exc:
            raise IntegrityError(f"invalid persisted session: {exc}") from exc

    def save(self, session: ResearchSession) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        session_raw = _jsonable(session.to_dict())
        envelope = {
            "format": self.FORMAT,
            "schema_version": SCHEMA_VERSION,
            "complete": True,
            "integrity_digest": digest(session_raw),
            "session": session_raw,
        }
        encoded = (canonical_json(envelope) + "\n").encode("utf-8")
        fd, tmp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def write_evidence_bytes(self, content: bytes) -> tuple[str, str]:
        content_digest = hashlib.sha256(content).hexdigest()
        target = self.artifact_dir / f"{content_digest}.bin"
        if not target.exists():
            fd, tmp_name = tempfile.mkstemp(prefix=f".{content_digest}.", dir=str(self.artifact_dir))
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp_name, target)
            except Exception:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
                raise
        return content_digest, str(target.relative_to(self.path.parent))


class SessionCore:
    """Trusted implementation of the six canonical operations."""

    def __init__(self, state_path: os.PathLike[str] | str):
        self.store = StateStore(state_path)
        self._session: Optional[ResearchSession] = None

    @property
    def session(self) -> ResearchSession:
        return self._load_required()

    def _load(self) -> Optional[ResearchSession]:
        if self._session is None:
            self._session = self.store.load()
        return self._session

    def _load_required(self) -> ResearchSession:
        session = self._load()
        if session is None:
            raise ValidationError("no research session has been started")
        return session

    def _persist(self) -> None:
        if self._session is None:
            raise ValidationError("no research session has been started")
        self.store.save(self._session)

    def _event(self, operation: str, request_id: Optional[str], details: Mapping[str, Any] | None = None) -> None:
        event: Dict[str, Any] = {"operation": operation, "at": now_iso()}
        if request_id:
            event["request_id"] = request_id
        if details:
            event["details"] = _jsonable(details)
        self.session.events.append(event)
        self.session.updated_at = event["at"]

    def _mutate(
        self,
        operation: str,
        idempotency_key: str,
        payload: Mapping[str, Any],
        fn: Callable[[], Dict[str, Any]],
    ) -> Dict[str, Any]:
        key = normalize_text(idempotency_key)
        if not key:
            raise ValidationError("idempotency_key is required for mutating operations")
        session = self._load_required()
        fingerprint = digest({"operation": operation, "payload": _jsonable(payload)})
        previous = session.request_results.get(key)
        if previous:
            if previous.get("fingerprint") != fingerprint:
                raise ConflictError(f"idempotency key {key!r} was reused with conflicting content")
            result = dict(previous.get("result", {}))
            result["replayed"] = True
            return result
        result = fn()
        session.request_results[key] = {"fingerprint": fingerprint, "result": _jsonable(result)}
        self._event(operation, key)
        self._persist()
        result = dict(result)
        result["replayed"] = False
        return result

    def session_start(
        self,
        objective: str,
        scope: str,
        *,
        session_id: Optional[str] = None,
        idempotency_key: str = "session.start",
    ) -> Dict[str, Any]:
        objective_n, scope_n = normalize_text(objective), normalize_text(scope)
        if not objective_n or not scope_n:
            raise ValidationError("objective and scope are required")
        existing = self._load()
        if existing is not None:
            if existing.objective != objective_n or existing.scope != scope_n:
                raise ConflictError("a different session already exists in this state store")
            return {"session_id": existing.session_id, "state_digest": self.state_digest(), "replayed": True}
        chosen_id = normalize_text(session_id) if session_id else str(uuid.uuid4())
        self._session = ResearchSession(
            session_id=chosen_id,
            objective=objective_n,
            scope=scope_n,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        self._event("session.start", idempotency_key)
        self.store.save(self._session)
        result = {"session_id": chosen_id, "state_digest": self.state_digest(), "replayed": False}
        self.session.request_results[normalize_text(idempotency_key)] = {
            "fingerprint": digest({"operation": "session.start", "payload": {"objective": objective_n, "scope": scope_n, "session_id": chosen_id}}),
            "result": result,
        }
        self.store.save(self.session)
        return result

    def session_resume(self) -> Dict[str, Any]:
        session = self._load_required()
        self._refresh_reviews()
        return {"session_id": session.session_id, "state_digest": self.state_digest(), "session": session.to_dict()}

    def session_status(self) -> Dict[str, Any]:
        session = self._load_required()
        self._refresh_reviews()
        return {
            "session_id": session.session_id,
            "objective": session.objective,
            "scope": session.scope,
            "evidence_count": len(session.evidence_refs),
            "claim_count": len(session.claims),
            "checkpoint_count": len(session.checkpoints),
            "review_count": len(session.reviews),
            "valid_reviews": sum(review.status == "VALID" for review in session.reviews),
            "state_digest": self.state_digest(),
            "updated_at": session.updated_at,
        }

    def evidence_capture(
        self,
        *,
        evidence_id: str,
        uri: str,
        title: str = "",
        excerpt: str = "",
        content: bytes | str | None = None,
        content_digest: Optional[str] = None,
        source_version: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        evidence_id_n, uri_n = normalize_text(evidence_id), normalize_text(uri)
        title_n, excerpt_n = normalize_text(title), normalize_text(excerpt)
        if not evidence_id_n or not uri_n:
            raise ValidationError("evidence_id and uri are required")
        declared = normalize_text(content_digest) if content_digest else None
        actual_digest, artifact_ref = None, None
        if content is not None:
            content_bytes = content.encode("utf-8") if isinstance(content, str) else bytes(content)
            actual_digest, artifact_ref = self.store.write_evidence_bytes(content_bytes)
        elif declared is not None and (len(declared) != 64 or any(c not in "0123456789abcdefABCDEF" for c in declared)):
            raise ValidationError("content_digest must be a SHA-256 hex digest")
        payload = {
            "evidence_id": evidence_id_n,
            "uri": uri_n,
            "title": title_n,
            "excerpt": excerpt_n,
            "content_digest": actual_digest or declared,
            "declared_content_digest": declared if content is not None else None,
            "source_version": normalize_text(source_version) if source_version else None,
            "metadata": dict(metadata or {}),
        }

        def apply() -> Dict[str, Any]:
            session = self.session
            existing = next((item for item in session.evidence_refs if item.evidence_id == evidence_id_n), None)
            if existing:
                existing_payload = {
                    "evidence_id": existing.evidence_id,
                    "uri": existing.uri,
                    "title": existing.title,
                    "excerpt": existing.excerpt,
                    "content_digest": existing.content_digest,
                    "source_version": existing.source_version,
                    "metadata": existing.metadata,
                }
                comparable = {key: payload[key] for key in existing_payload}
                if existing_payload != comparable:
                    raise ConflictError(f"evidence identity {evidence_id_n!r} conflicts with existing content")
                return {"evidence_id": evidence_id_n, "content_digest": existing.content_digest, "artifact_ref": existing.artifact_ref}
            ref = EvidenceRef(
                evidence_id=evidence_id_n,
                uri=uri_n,
                title=title_n,
                excerpt=excerpt_n,
                captured_at=now_iso(),
                content_digest=actual_digest or declared,
                declared_content_digest=declared if content is not None else None,
                artifact_ref=artifact_ref,
                source_version=normalize_text(source_version) if source_version else None,
                metadata=dict(metadata or {}),
            )
            session.evidence_refs.append(ref)
            return {"evidence_id": ref.evidence_id, "content_digest": ref.content_digest, "artifact_ref": ref.artifact_ref}

        return self._mutate("evidence.capture", idempotency_key, payload, apply)

    def claim_propose(
        self,
        *,
        claim_id: str,
        statement: str,
        evidence_ids: Sequence[str] = (),
        qualifiers: Sequence[str] = (),
        conclusion: Optional[str] = None,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        claim_id_n, statement_n = normalize_text(claim_id), normalize_text(statement)
        if not claim_id_n or not statement_n:
            raise ValidationError("claim_id and statement are required")
        evidence_n = normalize_list(evidence_ids)
        qualifiers_n = normalize_list(qualifiers)
        payload = {
            "claim_id": claim_id_n,
            "statement": statement_n,
            "evidence_ids": evidence_n,
            "qualifiers": qualifiers_n,
            "conclusion": normalize_text(conclusion) if conclusion else None,
        }

        def apply() -> Dict[str, Any]:
            session = self.session
            known = {ref.evidence_id for ref in session.evidence_refs}
            unknown = set(evidence_n) - known
            if unknown:
                raise ValidationError(f"claim references unknown evidence: {sorted(unknown)}")
            existing = next((item for item in session.claims if item.claim_id == claim_id_n), None)
            if existing:
                old = {
                    "statement": existing.statement,
                    "evidence_ids": normalize_list(existing.evidence_ids),
                    "qualifiers": normalize_list(existing.qualifiers),
                    "conclusion": normalize_text(existing.conclusion or ""),
                }
                new = {
                    "statement": statement_n,
                    "evidence_ids": evidence_n,
                    "qualifiers": qualifiers_n,
                    "conclusion": normalize_text(conclusion) if conclusion else "",
                }
                if old == new:
                    return {"claim_id": existing.claim_id, "revision": existing.revision, "conclusion_digest": conclusion_digest(existing)}
                existing.statement = statement_n
                existing.evidence_ids = evidence_n
                existing.qualifiers = qualifiers_n
                existing.conclusion = normalize_text(conclusion) if conclusion else None
                existing.revision += 1
                existing.status = "PROPOSED"
                self._refresh_reviews()
                return {"claim_id": existing.claim_id, "revision": existing.revision, "conclusion_digest": conclusion_digest(existing)}
            claim = ResearchClaim(
                claim_id=claim_id_n,
                statement=statement_n,
                evidence_ids=evidence_n,
                qualifiers=qualifiers_n,
                conclusion=normalize_text(conclusion) if conclusion else None,
            )
            session.claims.append(claim)
            return {"claim_id": claim.claim_id, "revision": claim.revision, "conclusion_digest": conclusion_digest(claim)}

        return self._mutate("claim.propose", idempotency_key, payload, apply)

    def checkpoint_create(self, *, reason: str = "", idempotency_key: str) -> Dict[str, Any]:
        reason_n = normalize_text(reason)
        payload = {"reason": reason_n}

        def apply() -> Dict[str, Any]:
            checkpoint_id = f"cp-{len(self.session.checkpoints) + 1:04d}"
            checkpoint = Checkpoint(
                checkpoint_id=checkpoint_id,
                session_id=self.session.session_id,
                state_digest=self.state_digest(),
                created_at=now_iso(),
                reason=reason_n,
            )
            self.session.checkpoints.append(checkpoint)
            return {"checkpoint_id": checkpoint_id, "state_digest": checkpoint.state_digest}

        return self._mutate("checkpoint.create", idempotency_key, payload, apply)

    def _refresh_reviews(self) -> None:
        session = self._load_required()
        claims = {claim.claim_id: claim for claim in session.claims}
        changed = False
        for review in session.reviews:
            claim = claims.get(review.claim_id)
            current_status = "STALE"
            if claim is not None:
                if (
                    review.conclusion_digest == conclusion_digest(claim)
                    and review.evidence_set_digest == evidence_set_digest(claim.evidence_ids)
                ):
                    current_status = "VALID"
            if review.status != current_status:
                review.status = current_status
                changed = True
        if changed:
            session.updated_at = now_iso()

    def conclusion_review(
        self,
        *,
        claim_id: str,
        reviewer_id: str,
        decision: str,
        evidence_ids: Optional[Sequence[str]] = None,
        conclusion: Optional[str] = None,
        notes: str = "",
        idempotency_key: str,
    ) -> Dict[str, Any]:
        claim_id_n, reviewer_n, decision_n = normalize_text(claim_id), normalize_text(reviewer_id), normalize_text(decision)
        payload = {
            "claim_id": claim_id_n,
            "reviewer_id": reviewer_n,
            "decision": decision_n,
            "evidence_ids": normalize_list(evidence_ids or []),
            "conclusion": normalize_text(conclusion) if conclusion else None,
            "notes": normalize_text(notes),
        }

        def apply() -> Dict[str, Any]:
            self._refresh_reviews()
            claim = next((item for item in self.session.claims if item.claim_id == claim_id_n), None)
            if claim is None:
                raise ValidationError(f"unknown claim: {claim_id_n}")
            if decision_n not in HumanReview.VALID_DECISIONS:
                raise ValidationError(f"unsupported review decision: {decision_n}")
            expected_evidence = evidence_set_digest(claim.evidence_ids)
            if evidence_ids is not None and evidence_set_digest(evidence_ids) != expected_evidence:
                raise ValidationError("review evidence set does not match the current claim")
            expected_conclusion = conclusion_digest(claim)
            if conclusion is not None and normalize_text(conclusion) != normalize_text(claim.conclusion or claim.statement):
                raise ValidationError("review conclusion does not match the current claim")
            review = HumanReview(
                review_id=f"review-{digest({'claim_id': claim_id_n, 'conclusion': expected_conclusion, 'evidence': expected_evidence, 'reviewer': reviewer_n, 'decision': decision_n})[:20]}",
                session_id=self.session.session_id,
                claim_id=claim_id_n,
                reviewer_id=reviewer_n,
                decision=decision_n,
                conclusion_digest=expected_conclusion,
                evidence_set_digest=expected_evidence,
                reviewed_at=now_iso(),
                notes=normalize_text(notes),
            )
            self.session.reviews.append(review)
            claim.status = decision_n
            return {"review_id": review.review_id, "status": review.status, "decision": review.decision}

        return self._mutate("conclusion.review", idempotency_key, payload, apply)

    def promote_conclusion(self, *, claim_id: str) -> Dict[str, Any]:
        self._refresh_reviews()
        claim = next((item for item in self.session.claims if item.claim_id == claim_id), None)
        if claim is None:
            raise ReviewUnavailable("cannot promote an unknown claim")
        valid = [
            review
            for review in self.session.reviews
            if review.claim_id == claim_id
            and review.status == "VALID"
            and review.decision in {"ACCEPT", "ACCEPT_WITH_LIMITATIONS"}
        ]
        if not valid:
            raise ReviewUnavailable("no current human-review receipt is available")
        review = valid[-1]
        return {"claim_id": claim_id, "decision": review.decision, "review_id": review.review_id, "promoted": True}

    def state_digest(self) -> str:
        return digest(self._load_required().to_dict())

    def export_run_bundle(
        self,
        *,
        task_id: str,
        condition: str,
        harness: Mapping[str, Any],
        model: Mapping[str, Any],
        final_answer: str = "",
        usage: Optional[Mapping[str, Any]] = None,
        events: Optional[Sequence[Mapping[str, Any]]] = None,
        run_id: Optional[str] = None,
        interruption_markers: Optional[Sequence[Mapping[str, Any]]] = None,
        raw_artifact_refs: Optional[Sequence[Mapping[str, Any]]] = None,
        output_path: Optional[os.PathLike[str] | str] = None,
    ) -> Dict[str, Any]:
        session = self._load_required()
        self._refresh_reviews()
        bundle = RunBundle(
            run_id=run_id or str(uuid.uuid4()),
            task_id=normalize_text(task_id),
            condition=normalize_text(condition),
            harness=dict(harness),
            model=dict(model),
            events=list(session.events) + [dict(item) for item in (events or [])],
            evidence_refs=list(session.evidence_refs),
            claims=list(session.claims),
            checkpoints=list(session.checkpoints),
            reviews=list(session.reviews),
            contradictions=list(session.contradictions),
            unresolved_questions=list(session.unresolved_questions),
            final_answer=normalize_text(final_answer),
            usage={
                "input_tokens": None,
                "output_tokens": None,
                "cost": None,
                "elapsed_ms": None,
                **dict(usage or {}),
            },
            interruption_markers=[dict(item) for item in (interruption_markers or [])],
            raw_artifact_refs=[dict(item) for item in (raw_artifact_refs or [])],
        )
        raw = _jsonable(bundle.to_dict())
        if output_path is not None:
            target = Path(output_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(canonical_json(raw) + "\n", encoding="utf-8")
        return raw


class ModelFacingAPI:
    """Unprivileged facade: intentionally has no review-writing method."""

    def __init__(self, core: SessionCore):
        self._core = core

    def session_start(self, **kwargs: Any) -> Dict[str, Any]:
        return self._core.session_start(**kwargs)

    def session_resume(self) -> Dict[str, Any]:
        return self._core.session_resume()

    def session_status(self) -> Dict[str, Any]:
        return self._core.session_status()

    def evidence_capture(self, **kwargs: Any) -> Dict[str, Any]:
        return self._core.evidence_capture(**kwargs)

    def claim_propose(self, **kwargs: Any) -> Dict[str, Any]:
        return self._core.claim_propose(**kwargs)

    def checkpoint_create(self, **kwargs: Any) -> Dict[str, Any]:
        return self._core.checkpoint_create(**kwargs)

    def export_run_bundle(self, **kwargs: Any) -> Dict[str, Any]:
        return self._core.export_run_bundle(**kwargs)
