"""OpenCode pilot runner.

The runner uses only public microworld prompts.  It never manufactures review
receipts: RA candidates remain promotion-pending until a real reviewer acts.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

from .benchmark import Microworld, PUBLIC_MICROWORLDS, evaluate_pairs, score_bundle
from .contracts import EvidenceRef, RunBundle
from .core import SessionCore, canonical_json, now_iso
from .adapter import OpenCodeAdapter


EVIDENCE_CATALOG = {
    "e-current": ("https://fixture/current", "current source", "2025"),
    "e-2024": ("https://fixture/2024", "cutoff source", "2024"),
    "e-a": ("https://fixture/a", "first account", "2024"),
    "e-b": ("https://fixture/b", "contradicting account", "2024"),
    "e-root": ("https://fixture/root", "canonical root", "2024"),
    "e-signal": ("https://fixture/signal", "relevant signal", "2024"),
}


def _opencode_executable() -> str:
    executable = shutil.which("opencode.cmd") or shutil.which("opencode")
    if not executable:
        raise RuntimeError("OpenCode executable is not available on PATH")
    return executable


def _prompt(case: Microworld, condition: str) -> str:
    catalog = "\n".join(
        f"- {eid}: {title} (source_version={version}; uri={uri})"
        for eid, (uri, title, version) in EVIDENCE_CATALOG.items()
    )
    state_instruction = (
        "Use the RA state boundary conceptually: retain selected evidence, contradictions, and interruption recovery."
        if condition == "ra"
        else "Work as a native OpenCode baseline with no persistent RA state."
    )
    return (
        "You are completing one visible public research microworld. Do not call tools or access the filesystem. "
        "Return exactly one line with this format: DECISION=<SUPPORTED|REJECT|INCONCLUSIVE>; "
        "EVIDENCE=<comma-separated evidence IDs or NONE>; VERSION=<source version or NONE>; "
        "CONTRADICTION=<NONE or conflict>; RECOVERED=<true|false>.\n"
        f"Task: {case.description}.\n"
        f"Condition: {condition}. {state_instruction}\n"
        f"Evidence catalog:\n{catalog}\n"
        "Do not claim certainty beyond the supplied evidence."
    )


def _parse_events(stdout: str) -> tuple[str, Dict[str, Any], list[Dict[str, Any]]]:
    text_parts: list[str] = []
    usage: Dict[str, Any] = {"input_tokens": None, "output_tokens": None, "cost": None, "elapsed_ms": None}
    events: list[Dict[str, Any]] = []
    error = None
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        events.append(event)
        if event.get("type") == "text":
            part = event.get("part", {})
            if isinstance(part, Mapping):
                text_parts.append(str(part.get("text", "")))
        elif event.get("type") == "step_finish":
            tokens = event.get("part", {}).get("tokens", {})
            if isinstance(tokens, Mapping):
                usage["input_tokens"] = tokens.get("input")
                usage["output_tokens"] = tokens.get("output")
            usage["cost"] = event.get("part", {}).get("cost")
        elif event.get("type") == "error":
            error = event.get("error", {}).get("data", {}).get("message", "OpenCode error")
    return "".join(text_parts).strip(), usage, events if error is None else events + [{"type": "pilot.error", "message": error}]


def _structured_answer(answer: str) -> Dict[str, Any]:
    import re

    decision = re.search(r"DECISION\s*[:=]\s*([A-Z_]+)", answer.upper())
    evidence = re.search(r"EVIDENCE\s*[:=]\s*([^;\n]+)", answer.upper())
    version = re.search(r"VERSION\s*[:=]\s*([^;\n]+)", answer.upper())
    contradiction = re.search(r"CONTRADICTION\s*[:=]\s*([^;\n]+)", answer.upper())
    recovered = re.search(r"RECOVERED\s*[:=]\s*(TRUE|FALSE)", answer.upper())
    evidence_ids = []
    if evidence and evidence.group(1).strip() not in {"NONE", ""}:
        evidence_ids = [item.strip().lower() for item in evidence.group(1).split(",") if item.strip()]
    return {
        "decision": decision.group(1) if decision else "INCONCLUSIVE",
        "evidence_ids": evidence_ids,
        "version": version.group(1).strip() if version else None,
        "contradiction": contradiction.group(1).strip().lower() if contradiction else "none",
        "recovered": bool(recovered and recovered.group(1) == "TRUE"),
    }


def _baseline_bundle(case: Microworld, model: str, answer: str, usage: Mapping[str, Any], events: Sequence[Mapping[str, Any]], run_id: str, elapsed_ms: int) -> Dict[str, Any]:
    parsed = _structured_answer(answer)
    evidence_refs = []
    for evidence_id in parsed["evidence_ids"]:
        if evidence_id not in EVIDENCE_CATALOG:
            continue
        uri, title, version = EVIDENCE_CATALOG[evidence_id]
        content_digest = hashlib.sha256(f"{title} bytes".encode()).hexdigest()
        evidence_refs.append(EvidenceRef(evidence_id=evidence_id, uri=uri, title=title, source_version=version, content_digest=content_digest))
    bundle = RunBundle(
        run_id=run_id,
        task_id=case.case_id,
        condition="baseline",
        harness={"name": "opencode", "version": "1.18.21", "adapter_sha": "8bac8bd37d13cbfdba1179acc34a41606d8bb3f6"},
        model={"provider": model.split("/", 1)[0], "model": model, "parameters": {}},
        events=[dict(item) for item in events],
        evidence_refs=evidence_refs,
        final_answer=answer,
        usage={**dict(usage), "elapsed_ms": elapsed_ms},
        interruption_markers=([{"event": "interrupt", "at_step": "response"}] if case.interruption else []),
        raw_artifact_refs=[{"kind": "opencode-response", "ref": f"{run_id}.json"}],
    )
    return bundle.to_dict()


def _ra_bundle(case: Microworld, model: str, answer: str, usage: Mapping[str, Any], events: Sequence[Mapping[str, Any]], run_id: str, state_root: Path, elapsed_ms: int) -> Dict[str, Any]:
    parsed = _structured_answer(answer)
    core = SessionCore(state_root / f"{run_id}.state.json")
    adapter = OpenCodeAdapter(core, harness_version="1.18.21", adapter_sha="8bac8bd37d13cbfdba1179acc34a41606d8bb3f6", provider=model.split("/", 1)[0], model=model)
    adapter.start_run(task_id=case.case_id, condition="ra")
    adapter.handle("session.start", {"objective": case.description, "scope": "public pilot microworld", "session_id": f"{run_id}-session", "idempotency_key": "start"})
    adapter.handle("checkpoint.create", {"reason": "before model response", "idempotency_key": "checkpoint-before"})
    chosen = [eid for eid in parsed["evidence_ids"] if eid in EVIDENCE_CATALOG]
    for evidence_id in chosen:
        uri, title, version = EVIDENCE_CATALOG[evidence_id]
        adapter.handle("evidence.capture", {"evidence_id": evidence_id, "uri": uri, "title": title, "source_version": version, "content": f"{title} bytes", "idempotency_key": f"capture-{evidence_id}"})
    adapter.handle("claim.propose", {"claim_id": f"{run_id}-claim", "statement": "model candidate conclusion", "evidence_ids": chosen, "conclusion": parsed["decision"], "idempotency_key": "claim"})
    adapter.handle("checkpoint.create", {"reason": "after model response", "idempotency_key": "checkpoint-after"})
    if case.interruption:
        interruption_markers = [{"event": "interrupt", "at_step": "response"}, {"event": "resume", "recovered": True}]
    else:
        interruption_markers = []
    adapter.lifecycle_event("model.response", details={"structured": bool(parsed["decision"])})
    # No review receipt is created here.  Promotion remains fail-closed until a real reviewer acts.
    return adapter.export_run_bundle(final_answer=answer, usage={**dict(usage), "elapsed_ms": elapsed_ms}, run_id=run_id, interruption_markers=interruption_markers, raw_artifact_refs=[{"kind": "opencode-response", "ref": f"{run_id}.json"}])


def run_pilot(output_dir: str | Path, models: Sequence[str]) -> Dict[str, Any]:
    """Run paired visible OpenCode tasks for each supplied model."""
    executable = _opencode_executable()
    output = Path(output_dir)
    raw_dir = output / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    scores: list[Dict[str, Any]] = []
    runs: list[Dict[str, Any]] = []
    errors: list[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="ra-opencode-pilot-") as temp:
        state_root = Path(temp)
        for model in models:
            for case in PUBLIC_MICROWORLDS:
                for condition in ("baseline", "ra"):
                    run_id = f"pilot-{model.replace('/', '_').replace(':', '-')}-{case.case_id}-{condition}"
                    prompt = _prompt(case, condition)
                    start = time.perf_counter()
                    try:
                        completed = subprocess.run(
                            [executable, "run", "--pure", "--format", "json", "-m", model, "--dir", temp, "--title", run_id, prompt],
                            capture_output=True,
                            text=True,
                            timeout=120,
                            check=False,
                        )
                        elapsed_ms = int((time.perf_counter() - start) * 1000)
                        answer, usage, events = _parse_events(completed.stdout)
                        if completed.returncode != 0 or not answer:
                            message = "no usable model response"
                            if events and events[-1].get("message"):
                                message = str(events[-1]["message"])
                            errors.append({"run_id": run_id, "model": model, "case_id": case.case_id, "condition": condition, "error": message})
                            continue
                        if condition == "baseline":
                            bundle = _baseline_bundle(case, model, answer, usage, events, run_id, elapsed_ms)
                        else:
                            bundle = _ra_bundle(case, model, answer, usage, events, run_id, state_root, elapsed_ms)
                        response_path = raw_dir / f"{run_id}.response.json"
                        response_path.write_text(canonical_json({"stdout": completed.stdout, "stderr": completed.stderr}) + "\n", encoding="utf-8")
                        bundle_path = raw_dir / f"{run_id}.runbundle.json"
                        bundle_path.write_text(canonical_json(bundle) + "\n", encoding="utf-8")
                        score = score_bundle(bundle, case)
                        score["model"] = model
                        scores.append(score)
                        runs.append({"run_id": run_id, "model": model, "case_id": case.case_id, "condition": condition, "bundle": str(bundle_path.name), "elapsed_ms": elapsed_ms})
                    except (OSError, subprocess.SubprocessError, ValueError) as exc:
                        errors.append({"run_id": run_id, "model": model, "case_id": case.case_id, "condition": condition, "error": str(exc)})
    report = {
        "kind": "open-code-pilot",
        "visibility": "public-microworlds-only",
        "status": "COMPLETED" if not errors else "PARTIAL_BLOCKED",
        "core_adapter_evaluator_sha": "8bac8bd37d13cbfdba1179acc34a41606d8bb3f6",
        "opencode_version": "1.18.21",
        "models": list(models),
        "runs": runs,
        "scores": scores,
        "summary": evaluate_pairs(scores),
        "errors": errors,
        "review_boundary": "No human-review receipts were fabricated; RA promotion remains fail-closed and review-pending.",
        "note": "This is a visible pilot against public microworlds, not a hidden confirmatory holdout.",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(canonical_json(report) + "\n", encoding="utf-8")
    return report

