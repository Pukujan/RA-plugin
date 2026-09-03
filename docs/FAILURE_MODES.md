# RA Plugin MVP — Failure Modes

This register is intentionally MVP-scoped. Discovering a future failure mode does not automatically expand implementation scope.

| Failure mode | Current mitigation / validation | MVP disposition |
| --- | --- | --- |
| Agent games schema/stamps without doing useful research | No generic stamps; trusted fields server/core-owned; compare outcome metrics | MITIGATE_NOW |
| Protocol blocks otherwise solvable research | fail-open ordinary research; protocol-induced failure metric | MITIGATE_NOW |
| Model forges human approval | privileged review surface; negative API/authorization tests | MITIGATE_NOW |
| Reviewed conclusion changes after approval | claim/evidence digest binding; metamorphic staleness tests | MITIGATE_NOW |
| Evidence set changes after approval | exact evidence-set binding; staleness tests | MITIGATE_NOW |
| Duplicate evidence counted as independent corroboration | canonical evidence identity/dedup semantics | MITIGATE_NOW |
| Retry creates duplicate state | idempotency key + deterministic conflict behavior | MITIGATE_NOW |
| Same operation identity used with different content | conflict/refusal test | MITIGATE_NOW |
| Crash leaves ambiguous checkpoint | transaction or explicit incomplete marker; kill/fault injection | MITIGATE_NOW |
| Corrupt local state silently loads | integrity/schema validation; corruption fixtures | MITIGATE_NOW |
| Unknown schema interpreted incorrectly | fail-safe version refusal | MITIGATE_NOW |
| Adapter adds hidden semantics/scoring | adapter conformance + code boundary; benchmark scorer separate | MITIGATE_NOW |
| Harness event missing or changes across versions | explicit supported-event matrix; fallback to explicit commands; adapter version pin | MEASURE |
| Context compaction loses unresolved contradiction | checkpoint state + interruption benchmark | MEASURE |
| RA checkpoint anchors model to a wrong early hypothesis | contradiction/unresolved state kept separate; final outcome benchmark | MEASURE |
| Human review becomes rubber-stamp labor | review burden/correction metrics | MEASURE |
| Human reviewer is wrong | gold evaluates accepted conclusions independently; review is not semantic truth oracle | MEASURE |
| Model-specific protocol overfit | cross-vendor paired OpenCode runs | MEASURE |
| Harness-specific protocol overfit | second harness only after OpenCode signal | DEFER until portability gate |
| MCP transport failure | MCP is not MVP core | DEFER |
| Remote hostile multi-tenant caller | not an MVP deployment claim | NOT_APPLICABLE |
| Source suitability error | source-ranker absent from MVP | DEFER |
| Semantic claim verifier bias | verifier absent from MVP | DEFER |
| Hidden holdout leakage | implementation/holdout separation and freeze protocol | MITIGATE_NOW |
| Benchmark-specific shortcuts in adapter | hidden confirmatory corpus + adapter conformance | MITIGATE_NOW |

Every newly reproduced failure must record impact, reachability, evidence level, current-scope relevance, and one of `MITIGATE_NOW`, `MEASURE`, `ACCEPT_RESIDUAL_RISK`, `DEFER`, or `NOT_APPLICABLE`.
