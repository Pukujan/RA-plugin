"""Small JSON CLI for local OpenCode/plugin smoke runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapter import OpenCodeAdapter
from .benchmark import run_development_benchmark
from .core import SessionCore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ra-plugin")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("dev-benchmark", help="run visible deterministic development fixtures")
    demo.add_argument("output", type=Path)
    op = sub.add_parser("op", help="dispatch one canonical operation from JSON")
    op.add_argument("state", type=Path)
    op.add_argument("operation")
    op.add_argument("payload", help="JSON object")
    op.add_argument("--trusted-review", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "dev-benchmark":
        print(json.dumps(run_development_benchmark(args.output), indent=2, ensure_ascii=False))
        return 0
    adapter = OpenCodeAdapter(SessionCore(args.state))
    try:
        payload = json.loads(args.payload)
        result = adapter.handle(args.operation, payload, trusted_review=args.trusted_review)
    except (ValueError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

