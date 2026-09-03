"""Versioned, deterministic contracts for the RA-plugin MVP.

The contracts deliberately stay small.  They are JSON-compatible records and
are validated at the trusted boundary before being persisted or exported.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar, Dict, List, Mapping, Optional, Type, TypeVar


SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})


class ContractError(ValueError):
    """Raised when a contract is malformed or uses an unsupported version."""


class UnknownVersionError(ContractError):
    """Raised instead of guessing how to interpret a future contract."""


T = TypeVar("T", bound="VersionedContract")


def require_version(value: Any, *, expected: str = SCHEMA_VERSION) -> str:
    if not isinstance(value, str) or value not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnknownVersionError(f"unsupported schema version: {value!r}")
    if value != expected:
        raise UnknownVersionError(f"expected schema version {expected!r}, got {value!r}")
    return value


def _required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty string")
    return value


class VersionedContract:
    contract_name: ClassVar[str] = "Contract"

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result.setdefault("schema_version", SCHEMA_VERSION)
        return result

    @classmethod
    def from_dict(cls: Type[T], raw: Mapping[str, Any]) -> T:
        if not isinstance(raw, Mapping):
            raise ContractError(f"{cls.contract_name} must be an object")
        require_version(raw.get("schema_version"))
        try:
            return cls(**dict(raw))
        except TypeError as exc:
            raise ContractError(f"invalid {cls.contract_name}: {exc}") from exc


@dataclass
class EvidenceRef(VersionedContract):
    contract_name: ClassVar[str] = "EvidenceRef"
    evidence_id: str
    uri: str
    title: str = ""
    excerpt: str = ""
    captured_at: Optional[str] = None
    content_digest: Optional[str] = None
    declared_content_digest: Optional[str] = None
    artifact_ref: Optional[str] = None
    source_version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_version(self.schema_version)
        _required_text(self.evidence_id, "evidence_id")
        _required_text(self.uri, "uri")
        if self.content_digest is not None and (
            not isinstance(self.content_digest, str) or len(self.content_digest) != 64
        ):
            raise ContractError("content_digest must be a SHA-256 hex digest")


@dataclass
class ResearchClaim(VersionedContract):
    contract_name: ClassVar[str] = "ResearchClaim"
    claim_id: str
    statement: str
    evidence_ids: List[str] = field(default_factory=list)
    qualifiers: List[str] = field(default_factory=list)
    conclusion: Optional[str] = None
    status: str = "PROPOSED"
    revision: int = 1
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_version(self.schema_version)
        _required_text(self.claim_id, "claim_id")
        _required_text(self.statement, "statement")
        if self.status not in {"PROPOSED", "ACCEPTED", "REJECTED", "NEEDS_MORE_EVIDENCE", "ACCEPT_WITH_LIMITATIONS"}:
            raise ContractError(f"unsupported claim status: {self.status}")
        if not isinstance(self.revision, int) or self.revision < 1:
            raise ContractError("revision must be a positive integer")


@dataclass
class Checkpoint(VersionedContract):
    contract_name: ClassVar[str] = "Checkpoint"
    checkpoint_id: str
    session_id: str
    state_digest: str
    created_at: str
    reason: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_version(self.schema_version)
        for name in ("checkpoint_id", "session_id", "state_digest", "created_at"):
            _required_text(getattr(self, name), name)


@dataclass
class HumanReview(VersionedContract):
    contract_name: ClassVar[str] = "HumanReview"
    review_id: str
    session_id: str
    claim_id: str
    reviewer_id: str
    decision: str
    conclusion_digest: str
    evidence_set_digest: str
    reviewed_at: str
    policy_version: str = "1.0"
    status: str = "VALID"
    notes: str = ""
    schema_version: str = SCHEMA_VERSION

    VALID_DECISIONS: ClassVar[frozenset[str]] = frozenset(
        {"ACCEPT", "REJECT", "NEEDS_MORE_EVIDENCE", "ACCEPT_WITH_LIMITATIONS"}
    )

    def __post_init__(self) -> None:
        require_version(self.schema_version)
        for name in (
            "review_id",
            "session_id",
            "claim_id",
            "reviewer_id",
            "conclusion_digest",
            "evidence_set_digest",
            "reviewed_at",
        ):
            _required_text(getattr(self, name), name)
        if self.decision not in self.VALID_DECISIONS:
            raise ContractError(f"unsupported review decision: {self.decision}")
        if self.status not in {"VALID", "STALE"}:
            raise ContractError(f"unsupported review status: {self.status}")


@dataclass
class ResearchSession(VersionedContract):
    contract_name: ClassVar[str] = "ResearchSession"
    session_id: str
    objective: str
    scope: str
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)
    claims: List[ResearchClaim] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    experiments: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    checkpoints: List[Checkpoint] = field(default_factory=list)
    reviews: List[HumanReview] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    request_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_version(self.schema_version)
        _required_text(self.session_id, "session_id")
        _required_text(self.objective, "objective")
        _required_text(self.scope, "scope")
        # Boundary validation prevents hand-built dictionaries from bypassing
        # privilege and version checks when state is loaded from disk.
        self.evidence_refs = [
            item if isinstance(item, EvidenceRef) else EvidenceRef.from_dict(item)
            for item in self.evidence_refs
        ]
        self.claims = [
            item if isinstance(item, ResearchClaim) else ResearchClaim.from_dict(item)
            for item in self.claims
        ]
        self.checkpoints = [
            item if isinstance(item, Checkpoint) else Checkpoint.from_dict(item)
            for item in self.checkpoints
        ]
        self.reviews = [
            item if isinstance(item, HumanReview) else HumanReview.from_dict(item)
            for item in self.reviews
        ]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["schema_version"] = self.schema_version
        return result

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ResearchSession":
        if not isinstance(raw, Mapping):
            raise ContractError("ResearchSession must be an object")
        require_version(raw.get("schema_version"))
        return cls(**dict(raw))


@dataclass
class RunBundle(VersionedContract):
    contract_name: ClassVar[str] = "RunBundle"
    run_id: str
    task_id: str
    condition: str
    harness: Dict[str, Any]
    model: Dict[str, Any]
    events: List[Dict[str, Any]] = field(default_factory=list)
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    claims: List[ResearchClaim] = field(default_factory=list)
    checkpoints: List[Checkpoint] = field(default_factory=list)
    reviews: List[HumanReview] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    final_answer: str = ""
    usage: Dict[str, Any] = field(
        default_factory=lambda: {
            "input_tokens": None,
            "output_tokens": None,
            "cost": None,
            "elapsed_ms": None,
        }
    )
    interruption_markers: List[Dict[str, Any]] = field(default_factory=list)
    raw_artifact_refs: List[Dict[str, Any]] = field(default_factory=list)
    ra_core_version: str = SCHEMA_VERSION
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_version(self.schema_version)
        require_version(self.ra_core_version)
        for name in ("run_id", "task_id", "condition"):
            _required_text(getattr(self, name), name)
        if self.condition not in {"baseline", "ra"}:
            raise ContractError("condition must be 'baseline' or 'ra'")
        if not isinstance(self.harness, Mapping) or not self.harness.get("name"):
            raise ContractError("harness identity is required")
        if not isinstance(self.model, Mapping) or not self.model.get("provider") or not self.model.get("model"):
            raise ContractError("provider/model identity is required")
        self.evidence_refs = [
            item if isinstance(item, EvidenceRef) else EvidenceRef.from_dict(item)
            for item in self.evidence_refs
        ]
        self.claims = [
            item if isinstance(item, ResearchClaim) else ResearchClaim.from_dict(item)
            for item in self.claims
        ]
        self.checkpoints = [
            item if isinstance(item, Checkpoint) else Checkpoint.from_dict(item)
            for item in self.checkpoints
        ]
        self.reviews = [
            item if isinstance(item, HumanReview) else HumanReview.from_dict(item)
            for item in self.reviews
        ]
