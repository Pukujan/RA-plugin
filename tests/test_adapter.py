from pathlib import Path

from ra_plugin import SessionCore
from ra_plugin.adapter import OpenCodeAdapter


def test_adapter_exposes_only_canonical_operations(tmp_path: Path) -> None:
    adapter = OpenCodeAdapter(SessionCore(tmp_path / "state.json"), harness_version="1.2", provider="fixture", model="m")
    assert adapter.commands() == (
        "session.start",
        "session.resume",
        "session.status",
        "evidence.capture",
        "claim.propose",
        "checkpoint.create",
        "conclusion.review",
    )


def test_model_cannot_manufacture_review(tmp_path: Path) -> None:
    core = SessionCore(tmp_path / "state.json")
    adapter = OpenCodeAdapter(core)
    adapter.handle("session.start", {"objective": "o", "scope": "s", "session_id": "s", "idempotency_key": "start"})
    response = adapter.handle(
        "conclusion.review",
        {"claim_id": "c", "reviewer_id": "model", "decision": "ACCEPT", "idempotency_key": "r"},
    )
    assert response == {"ok": False, "error": "PRIVILEGED_OPERATION", "reviewed": False}


def test_adapter_records_identity_in_reproducible_bundle(tmp_path: Path) -> None:
    core = SessionCore(tmp_path / "state.json")
    adapter = OpenCodeAdapter(core, harness_version="1.2", adapter_sha="a" * 40, provider="fixture", model="m")
    adapter.handle("session.start", {"objective": "o", "scope": "s", "session_id": "s", "idempotency_key": "start"})
    adapter.start_run(task_id="task-1", condition="ra")
    adapter.lifecycle_event("checkpoint")
    bundle = adapter.export_run_bundle(final_answer="done", run_id="run-1")
    assert bundle["harness"] == {"name": "opencode", "version": "1.2", "adapter_sha": "a" * 40}
    assert bundle["model"]["provider"] == "fixture"
    assert any(event.get("type") == "lifecycle" for event in bundle["events"])


class BrokenCore:
    def session_status(self):
        raise OSError("unavailable")

    def promote_conclusion(self, **kwargs):
        raise OSError("unavailable")


def test_fail_open_ordinary_research_and_fail_closed_promotion(tmp_path: Path) -> None:
    adapter = OpenCodeAdapter(BrokenCore())  # type: ignore[arg-type]
    ordinary = adapter.handle("session.status", {})
    assert ordinary == {"ok": False, "degraded": True, "error": "RA_UNAVAILABLE"}
    promotion = adapter.handle("conclusion.promote", {"claim_id": "c"}, trusted_review=True)
    assert promotion["promoted"] is False
    assert promotion["error"] == "REVIEW_UNAVAILABLE"

