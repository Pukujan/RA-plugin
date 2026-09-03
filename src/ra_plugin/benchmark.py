"""Public deterministic development microworlds and evaluator.

These fixtures validate the canonical bundle/evaluator wiring.  They are not a
model pilot and must never be reported as confirmatory evidence.
"""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

from .adapter import OpenCodeAdapter
from .core import SessionCore, canonical_json


@dataclass(frozen=True)
class Microworld:
    case_id: str
    description: str
    gold_decision: str
    required_evidence: tuple[str, ...] = ()
    expected_version: str | None = None
    required_contradictions: tuple[str, ...] = ()
    unsupported_claim_ids: tuple[str, ...] = ()
    interruption: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


PUBLIC_MICROWORLDS: tuple[Microworld, ...] = (
    Microworld("interruption-recovery", "recover after an interrupted evidence review", "SUPPORTED", ("e-current",), interruption=True),
    Microworld("temporal-cutoff", "respect the frozen 2024 cutoff", "SUPPORTED", ("e-2024",), expected_version="2024"),
    Microworld("contradictory-evidence", "retain and surface contradictory roots", "INCONCLUSIVE", ("e-a", "e-b"), required_contradictions=("conflict",)),
    Microworld("duplicated-root", "deduplicate equivalent evidence roots", "SUPPORTED", ("e-root",)),
    Microworld("reputation-distractor", "prefer relevant evidence over reputation distractors", "SUPPORTED", ("e-signal",)),
    Microworld("unsupported-conclusion", "reject a conclusion without support", "REJECT", (), unsupported_claim_ids=("c-unsupported",)),
    Microworld("explicit-no-answer", "return an explicit inconclusive answer", "INCONCLUSIVE", ()),
)


def public_microworlds() -> tuple[Microworld, ...]:
    return PUBLIC_MICROWORLDS


def _decision(final_answer: str) -> str | None:
    match = re.search(r"DECISION\s*[:=]\s*([A-Z_]+)", final_answer.upper())
    return match.group(1) if match else None


def score_bundle(bundle: Mapping[str, Any], case: Microworld) -> Dict[str, Any]:
    claims = list(bundle.get("claims", []))
    evidence_ids = [eid for claim in claims for eid in claim.get("evidence_ids", [])]
    retained_evidence = set(evidence_ids)
    required = set(case.required_evidence)
    recall = len(required & retained_evidence) / len(required) if required else 1.0
    unsupported_claims = [claim for claim in claims if claim.get("claim_id") in set(case.unsupported_claim_ids)]
    contradictions = set(bundle.get("contradictions", []))
    final_answer = str(bundle.get("final_answer", ""))
    decision = _decision(final_answer)
    temporal_error = bool(case.expected_version and case.expected_version not in final_answer)
    interruption_recovered = True
    if case.interruption:
        markers = list(bundle.get("interruption_markers", []))
        interruption_recovered = any(marker.get("event") == "resume" and marker.get("recovered") is True for marker in markers)
    events = list(bundle.get("events", []))
    protocol_failures = sum(1 for event in events if event.get("type") in {"adapter.error", "protocol.failure"})
    return {
        "task_id": case.case_id,
        "condition": bundle.get("condition"),
        "final_decision": decision,
        "final_decision_correct": decision == case.gold_decision,
        "supporting_evidence_recall": recall,
        "unsupported_claim_rate": len(unsupported_claims) / max(1, len(claims)),
        "temporal_version_error": temporal_error,
        "contradiction_retained": set(case.required_contradictions).issubset(contradictions),
        "interruption_recovery": interruption_recovered,
        "duplicate_work": max(0, len(evidence_ids) - len(set(evidence_ids))),
        "human_review_burden": len(bundle.get("reviews", [])),
        "protocol_failure": protocol_failures > 0,
    }


def _aggregate(scores: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    if not scores:
        return {}
    bool_fields = [
        "final_decision_correct",
        "temporal_version_error",
        "contradiction_retained",
        "interruption_recovery",
        "protocol_failure",
    ]
    result: Dict[str, Any] = {"tasks": len(scores)}
    for field_name in bool_fields:
        values = [bool(score[field_name]) for score in scores]
        result[field_name] = sum(values) / len(values)
    for field_name in ["supporting_evidence_recall", "unsupported_claim_rate", "duplicate_work", "human_review_burden"]:
        result[field_name] = sum(float(score[field_name]) for score in scores) / len(scores)
    return result


def evaluate_pairs(scores: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    by_condition: Dict[str, list[Mapping[str, Any]]] = {"baseline": [], "ra": []}
    for score in scores:
        by_condition.setdefault(str(score.get("condition")), []).append(score)
    baseline = _aggregate(by_condition.get("baseline", []))
    ra = _aggregate(by_condition.get("ra", []))
    paired = {}
    if baseline and ra:
        for field_name in (
            "final_decision_correct",
            "supporting_evidence_recall",
            "unsupported_claim_rate",
            "temporal_version_error",
            "contradiction_retained",
            "interruption_recovery",
            "duplicate_work",
            "human_review_burden",
            "protocol_failure",
        ):
            paired[field_name] = ra[field_name] - baseline[field_name]
    return {"baseline": baseline, "ra": ra, "paired_difference_ra_minus_baseline": paired}


def _fixture_bundle(case: Microworld, condition: str, state_root: Path) -> Dict[str, Any]:
    state_path = state_root / f"{case.case_id}-{condition}.json"
    core = SessionCore(state_path)
    adapter = OpenCodeAdapter(core, harness_version="fixture-public-1", adapter_sha="fixture", provider="fixture", model="scripted")
    adapter.start_run(task_id=case.case_id, condition=condition)
    adapter.handle("session.start", {"objective": case.description, "scope": "public development microworld", "session_id": f"s-{case.case_id}-{condition}", "idempotency_key": "start"})
    evidence_defs = {
        "e-current": ("https://fixture/current", "current source", "2025"),
        "e-2024": ("https://fixture/2024", "cutoff source", "2024"),
        "e-a": ("https://fixture/a", "first account", "2024"),
        "e-b": ("https://fixture/b", "contradicting account", "2024"),
        "e-root": ("https://fixture/root", "canonical root", "2024"),
        "e-signal": ("https://fixture/signal", "relevant signal", "2024"),
    }
    selected = set(case.required_evidence)
    for evidence_id, (uri, title, version) in evidence_defs.items():
        if evidence_id in selected:
            adapter.handle(
                "evidence.capture",
                {"evidence_id": evidence_id, "uri": uri, "title": title, "source_version": version, "content": f"{title} bytes", "idempotency_key": f"evidence-{evidence_id}"},
            )
    if case.required_contradictions:
        core.session.contradictions.extend(case.required_contradictions)
        core.store.save(core.session)
    if condition == "ra" and case.interruption:
        core.checkpoint_create(reason="before interruption", idempotency_key="checkpoint")
        interruption_markers = [{"event": "interrupt", "at_step": "evidence"}, {"event": "resume", "recovered": True}]
    else:
        interruption_markers = [{"event": "interrupt", "at_step": "evidence"}] if case.interruption else []
    claim_ids = list(case.unsupported_claim_ids) or [f"c-{case.case_id}"]
    claim_id = claim_ids[0]
    claim_evidence = list(case.required_evidence)
    if condition == "baseline" and case.case_id == "contradictory-evidence":
        claim_evidence = ["e-a"]
    statement = "fixture conclusion"
    adapter.handle("claim.propose", {"claim_id": claim_id, "statement": statement, "evidence_ids": claim_evidence, "conclusion": case.gold_decision, "idempotency_key": "claim"})
    decision = case.gold_decision if condition == "ra" else ("SUPPORTED" if case.gold_decision == "INCONCLUSIVE" else case.gold_decision)
    version_note = f" version={case.expected_version}" if case.expected_version else ""
    final_answer = f"DECISION={decision}; public fixture{version_note}"
    if condition == "ra" and case.gold_decision in {"SUPPORTED", "REJECT", "INCONCLUSIVE"}:
        adapter.handle("conclusion.review", {"claim_id": claim_id, "reviewer_id": "fixture-human", "decision": "ACCEPT_WITH_LIMITATIONS" if case.gold_decision == "INCONCLUSIVE" else case.gold_decision, "evidence_ids": claim_evidence, "idempotency_key": "review"}, trusted_review=True)
    return adapter.export_run_bundle(final_answer=final_answer, run_id=f"dev-{condition}-{case.case_id}", interruption_markers=interruption_markers)


def run_development_benchmark(output_dir: str | Path) -> Dict[str, Any]:
    """Run only visible scripted fixtures and preserve every raw RunBundle."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    raw_dir = output / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ra-dev-state-") as temp:
        state_root = Path(temp)
        scores = []
        manifest = {"kind": "public-development-only", "cases": [case.to_dict() for case in public_microworlds()]}
        for case in public_microworlds():
            for condition in ("baseline", "ra"):
                bundle = _fixture_bundle(case, condition, state_root)
                bundle_path = raw_dir / f"{condition}-{case.case_id}.runbundle.json"
                bundle_path.write_text(canonical_json(bundle) + "\n", encoding="utf-8")
                scores.append(score_bundle(bundle, case))
        report = {"manifest": manifest, "scores": scores, "summary": evaluate_pairs(scores), "note": "Development fixtures only; no model or confirmatory result."}
    (output / "report.json").write_text(canonical_json(report) + "\n", encoding="utf-8")
    return report
