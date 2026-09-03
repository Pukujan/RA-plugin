"""Thin OpenCode-facing boundary for the deterministic RA core.

This module intentionally contains no source ranking, claim verification, or
benchmark scoring.  It translates stable commands and lifecycle events only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from .core import RAError, ReviewUnavailable, SessionCore


class AdapterError(RuntimeError):
    pass


@dataclass(frozen=True)
class RunIdentity:
    task_id: str
    condition: str
    harness_name: str
    harness_version: str
    adapter_sha: str
    provider: str
    model: str
    parameters: Dict[str, Any]


class OpenCodeAdapter:
    """Command/lifecycle adapter with a fail-open research boundary."""

    OPERATIONS = (
        "session.start",
        "session.resume",
        "session.status",
        "evidence.capture",
        "claim.propose",
        "checkpoint.create",
        "conclusion.review",
    )
    MODEL_ALLOWED = frozenset(OPERATIONS) - {"conclusion.review"}

    def __init__(
        self,
        core: SessionCore,
        *,
        harness_version: str = "unknown",
        adapter_sha: Optional[str] = None,
        provider: str = "unknown",
        model: str = "unknown",
        parameters: Optional[Mapping[str, Any]] = None,
    ):
        self.core = core
        self.harness_version = harness_version
        self.adapter_sha = adapter_sha or os.environ.get("RA_PLUGIN_ADAPTER_SHA", "working-tree")
        self.provider = provider
        self.model = model
        self.parameters = dict(parameters or {})
        self._run: Optional[RunIdentity] = None
        self._events: list[Dict[str, Any]] = []

    @classmethod
    def commands(cls) -> tuple[str, ...]:
        return cls.OPERATIONS

    def start_run(self, *, task_id: str, condition: str) -> RunIdentity:
        if condition not in {"baseline", "ra"}:
            raise AdapterError("condition must be 'baseline' or 'ra'")
        self._run = RunIdentity(
            task_id=task_id,
            condition=condition,
            harness_name="opencode",
            harness_version=self.harness_version,
            adapter_sha=self.adapter_sha,
            provider=self.provider,
            model=self.model,
            parameters=dict(self.parameters),
        )
        self._events.append({"type": "run.start", "task_id": task_id, "condition": condition})
        return self._run

    def lifecycle_event(self, event: str, *, details: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """Record stable lifecycle markers; unknown event details stay opaque."""
        if not event or not isinstance(event, str):
            raise AdapterError("lifecycle event must be a non-empty string")
        marker = {"type": "lifecycle", "event": event}
        if details:
            marker["details"] = dict(details)
        self._events.append(marker)
        return marker

    def _degraded(self, command: str, error: Exception) -> Dict[str, Any]:
        if command == "conclusion.review" or command == "conclusion.promote":
            return {
                "ok": False,
                "reviewed": False,
                "promoted": False,
                "error": "REVIEW_UNAVAILABLE",
            }
        return {"ok": False, "degraded": True, "error": "RA_UNAVAILABLE"}

    def handle(self, command: str, payload: Mapping[str, Any], *, trusted_review: bool = False) -> Dict[str, Any]:
        """Dispatch a canonical operation without granting model review authority."""
        if command not in self.OPERATIONS and command != "conclusion.promote":
            raise AdapterError(f"unsupported command: {command}")
        if command == "conclusion.review" and not trusted_review:
            return {"ok": False, "error": "PRIVILEGED_OPERATION", "reviewed": False}
        try:
            if command == "session.start":
                result = self.core.session_start(**dict(payload))
            elif command == "session.resume":
                result = self.core.session_resume()
            elif command == "session.status":
                result = self.core.session_status()
            elif command == "evidence.capture":
                result = self.core.evidence_capture(**dict(payload))
            elif command == "claim.propose":
                result = self.core.claim_propose(**dict(payload))
            elif command == "checkpoint.create":
                result = self.core.checkpoint_create(**dict(payload))
            elif command == "conclusion.review":
                result = self.core.conclusion_review(**dict(payload))
            else:
                if not trusted_review:
                    return {"ok": False, "reviewed": False, "promoted": False, "error": "PRIVILEGED_OPERATION"}
                result = self.core.promote_conclusion(**dict(payload))
            return {"ok": True, **result}
        except (RAError, OSError, ValueError) as exc:
            return self._degraded(command, exc)

    def export_run_bundle(self, *, final_answer: str = "", usage: Optional[Mapping[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        if self._run is None:
            raise AdapterError("start_run must be called before exporting a RunBundle")
        identity = self._run
        events = list(self._events)
        return self.core.export_run_bundle(
            task_id=identity.task_id,
            condition=identity.condition,
            harness={
                "name": identity.harness_name,
                "version": identity.harness_version,
                "adapter_sha": identity.adapter_sha,
            },
            model={
                "provider": identity.provider,
                "model": identity.model,
                "parameters": identity.parameters,
            },
            final_answer=final_answer,
            usage=usage,
            events=events,
            **kwargs,
        )

