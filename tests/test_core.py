import json
from pathlib import Path

import pytest

from ra_plugin import (
    ConflictError,
    IntegrityError,
    ModelFacingAPI,
    ReviewUnavailable,
    SessionCore,
    UnknownVersionError,
    ValidationError,
    evidence_set_digest,
    normalize_text,
)


def started(tmp_path: Path, *, session_id: str = "s-1") -> SessionCore:
    core = SessionCore(tmp_path / "state.json")
    core.session_start("  Determine\nanswer  ", " public scope ", session_id=session_id, idempotency_key="start-1")
    return core


def with_evidence_and_claim(core: SessionCore) -> None:
    core.evidence_capture(
        evidence_id="e-1",
        uri="https://example.test/source",
        title=" Source ",
        excerpt="A  useful excerpt",
        content=b"canonical bytes",
        idempotency_key="evidence-1",
    )
    core.claim_propose(
        claim_id="c-1",
        statement="The answer is supported",
        evidence_ids=["e-1"],
        conclusion="SUPPORTED",
        idempotency_key="claim-1",
    )


def test_contract_unknown_version_refuses() -> None:
    from ra_plugin import EvidenceRef

    with pytest.raises(UnknownVersionError):
        EvidenceRef.from_dict({"schema_version": "99.0", "evidence_id": "e", "uri": "u"})


def test_normalization_and_set_digest_are_order_independent() -> None:
    assert normalize_text("  A\n\tB  ") == "A B"
    assert evidence_set_digest(["e2", "e1", "e1"]) == evidence_set_digest(["e1", "e2"])


def test_idempotent_retry_converges_and_conflict_is_loud(tmp_path: Path) -> None:
    core = started(tmp_path)
    first = core.evidence_capture(evidence_id="e", uri="u", content=b"x", idempotency_key="req")
    replay = core.evidence_capture(evidence_id="e", uri="u", content=b"x", idempotency_key="req")
    assert first["evidence_id"] == replay["evidence_id"]
    assert replay["replayed"] is True
    with pytest.raises(ConflictError):
        core.evidence_capture(evidence_id="e", uri="u", content=b"different", idempotency_key="req")


def test_conflicting_evidence_identity_fails_even_with_new_request(tmp_path: Path) -> None:
    core = started(tmp_path)
    core.evidence_capture(evidence_id="e", uri="u", content=b"x", idempotency_key="one")
    with pytest.raises(ConflictError):
        core.evidence_capture(evidence_id="e", uri="u", content=b"y", idempotency_key="two")


def test_checkpoint_restart_is_deterministic(tmp_path: Path) -> None:
    core = started(tmp_path)
    with_evidence_and_claim(core)
    before = core.session_resume()["state_digest"]
    result = core.checkpoint_create(reason="pause", idempotency_key="cp-1")
    restarted = SessionCore(tmp_path / "state.json")
    assert restarted.session_resume()["session"]["checkpoints"][0]["checkpoint_id"] == result["checkpoint_id"]
    assert restarted.session_resume()["session"]["checkpoints"][0]["state_digest"] == before


def test_review_binds_claim_and_evidence_and_stales_on_claim_change(tmp_path: Path) -> None:
    core = started(tmp_path)
    with_evidence_and_claim(core)
    review = core.conclusion_review(
        claim_id="c-1", reviewer_id="human@example.test", decision="ACCEPT", evidence_ids=["e-1"], idempotency_key="review-1"
    )
    assert review["status"] == "VALID"
    assert core.promote_conclusion(claim_id="c-1")["promoted"] is True
    core.claim_propose(
        claim_id="c-1", statement="The answer is not supported", evidence_ids=["e-1"], conclusion="UNSUPPORTED", idempotency_key="claim-2"
    )
    assert core.session.reviews[0].status == "STALE"
    with pytest.raises(ReviewUnavailable):
        core.promote_conclusion(claim_id="c-1")


def test_changed_evidence_set_stales_review(tmp_path: Path) -> None:
    core = started(tmp_path)
    with_evidence_and_claim(core)
    core.evidence_capture(evidence_id="e-2", uri="https://example.test/2", content=b"two", idempotency_key="evidence-2")
    core.conclusion_review(claim_id="c-1", reviewer_id="human", decision="ACCEPT", evidence_ids=["e-1"], idempotency_key="review-1")
    core.claim_propose(claim_id="c-1", statement="The answer is supported", evidence_ids=["e-1", "e-2"], conclusion="SUPPORTED", idempotency_key="claim-2")
    assert core.session.reviews[0].status == "STALE"


def test_corrupt_state_fails_loudly(tmp_path: Path) -> None:
    core = started(tmp_path)
    state_path = tmp_path / "state.json"
    raw = json.loads(state_path.read_text())
    raw["session"]["objective"] = "tampered"
    state_path.write_text(json.dumps(raw))
    with pytest.raises(IntegrityError):
        SessionCore(state_path).session_status()


def test_incomplete_state_is_detectable(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({"format": "ra-plugin-state", "complete": False}))
    with pytest.raises(IntegrityError):
        SessionCore(state_path).session_status()


def test_trusted_digest_wins_over_declared_hash(tmp_path: Path) -> None:
    core = started(tmp_path)
    result = core.evidence_capture(
        evidence_id="e", uri="u", content=b"actual", content_digest="0" * 64, idempotency_key="e-1"
    )
    assert result["content_digest"] != "0" * 64
    assert len(result["content_digest"]) == 64


def test_model_facing_facade_has_no_review_writer_and_review_fails_closed(tmp_path: Path) -> None:
    core = started(tmp_path)
    api = ModelFacingAPI(core)
    assert not hasattr(api, "conclusion_review")
    with pytest.raises(ReviewUnavailable):
        core.promote_conclusion(claim_id="missing")


def test_run_bundle_records_identity_and_is_json_serializable(tmp_path: Path) -> None:
    core = started(tmp_path)
    with_evidence_and_claim(core)
    raw = core.export_run_bundle(
        task_id="dev-1",
        condition="ra",
        harness={"name": "opencode", "version": "0.1", "adapter_sha": "a" * 40},
        model={"provider": "test", "model": "fixture", "parameters": {}},
        final_answer="answer",
        run_id="run-1",
    )
    assert raw["task_id"] == "dev-1"
    assert raw["harness"]["name"] == "opencode"
    assert raw["model"]["model"] == "fixture"
    json.dumps(raw)


def test_unknown_persisted_version_fails_safely(tmp_path: Path) -> None:
    core = started(tmp_path)
    state_path = tmp_path / "state.json"
    raw = json.loads(state_path.read_text())
    raw["session"]["schema_version"] = "2.0"
    raw["integrity_digest"] = __import__("hashlib").sha256(
        __import__("ra_plugin").canonical_json(raw["session"]).encode()
    ).hexdigest()
    state_path.write_text(json.dumps(raw))
    with pytest.raises(IntegrityError):
        SessionCore(state_path).session_status()

