import json
from pathlib import Path

from ra_plugin.benchmark import evaluate_pairs, public_microworlds, run_development_benchmark, score_bundle


def test_public_microworlds_cover_required_failure_modes() -> None:
    cases = {case.case_id: case for case in public_microworlds()}
    assert "interruption-recovery" in cases and cases["interruption-recovery"].interruption
    assert cases["temporal-cutoff"].expected_version == "2024"
    assert cases["contradictory-evidence"].required_contradictions == ("conflict",)
    assert cases["unsupported-conclusion"].unsupported_claim_ids == ("c-unsupported",)
    assert "explicit-no-answer" in cases


def test_evaluator_scores_hand_checkable_bundle() -> None:
    case = next(case for case in public_microworlds() if case.case_id == "temporal-cutoff")
    bundle = {
        "condition": "ra",
        "final_answer": "DECISION=SUPPORTED; version=2024",
        "claims": [{"claim_id": "c", "evidence_ids": ["e-2024"]}],
        "contradictions": [],
        "reviews": [],
        "events": [],
        "interruption_markers": [],
    }
    score = score_bundle(bundle, case)
    assert score["final_decision_correct"] is True
    assert score["supporting_evidence_recall"] == 1.0
    assert score["temporal_version_error"] is False


def test_development_runner_preserves_raw_bundles_and_report(tmp_path: Path) -> None:
    report = run_development_benchmark(tmp_path)
    assert report["manifest"]["kind"] == "public-development-only"
    assert len(report["scores"]) == len(public_microworlds()) * 2
    assert (tmp_path / "report.json").exists()
    raw = list((tmp_path / "raw").glob("*.runbundle.json"))
    assert len(raw) == len(public_microworlds()) * 2
    json.loads(raw[0].read_text())
    assert report["summary"]["paired_difference_ra_minus_baseline"]["final_decision_correct"] > 0


def test_pair_aggregation_is_explicit() -> None:
    summary = evaluate_pairs(
        [
            {"condition": "baseline", "final_decision_correct": False, "supporting_evidence_recall": 0.0, "unsupported_claim_rate": 0.0, "temporal_version_error": True, "contradiction_retained": False, "interruption_recovery": False, "duplicate_work": 1, "human_review_burden": 0, "protocol_failure": False},
            {"condition": "ra", "final_decision_correct": True, "supporting_evidence_recall": 1.0, "unsupported_claim_rate": 0.0, "temporal_version_error": False, "contradiction_retained": True, "interruption_recovery": True, "duplicate_work": 0, "human_review_burden": 1, "protocol_failure": False},
        ]
    )
    assert summary["paired_difference_ra_minus_baseline"]["final_decision_correct"] == 1.0

