# Terra + Luna operating contract for RA Plugin

## Authority and scope

This repository is an experimental adapter/runtime for the Research Assurance program. Program methodology, benchmark policy, scope control, milestone claims, and architecture decisions remain owned by `Pukujan/research-assurance`.

Agents implement the frozen experiment; they do not redefine what counts as success.

If the requested work is broader than this repository's issue scope, **stop and return to the master control plane** rather than silently expanding this repo.

## Fresh-session protocol

A fresh agent with no previous conversation must not infer program state from this repository alone.

Before material work:

1. fetch current `RA-plugin` main, open issues/PRs, and CI;
2. read this file, `specs/PDD.md`, `specs/SDD.md`, `specs/INVARIANTS.md`, `docs/FAILURE_MODES.md`, `docs/VALIDATION_STRATEGY.md`, and the active issue;
3. fetch `Pukujan/research-assurance` and read its `AGENTS.md`, current status/next state, and `docs/governance/ORCHESTRATION_PLAYBOOK.md` when program coordination, benchmark interpretation, or scope decisions are involved;
4. distinguish merged/default-branch truth from open PR proposals;
5. state the exact active issue, current branch/PR, evidence already available, and smallest next implementation/test step before changing code.

The plugin repository may continue local implementation independently once the program contract and issue are clear. Program scope changes return to `research-assurance`.

## Shared rules

1. Work from one GitHub issue at a time.
2. Do not broaden scope without an explicit issue update/architecture decision.
3. Do not add source ranking, semantic verification, GraphRAG, MCP-first architecture, or generic coding governance to the MVP unless a new issue explicitly admits it.
4. Preserve raw experiment artifacts; summaries never replace `RunBundle` or source evidence.
5. Do not inspect hidden/confirmatory task labels or seeds.
6. Do not tune implementation against confirmatory failures within the same frozen campaign.
7. Every implementation claim must be backed by code/test/fixture/benchmark evidence.
8. Prefer deterministic validation for IDs, digests, state transitions, review binding, idempotency, corruption detection, and evaluator logic.
9. Model output is not proof of integrity, review, or benchmark success.
10. Keep harness-specific behavior behind adapters; the core must not depend on OpenCode semantics.

## Terra

Primary responsibility: deterministic substrate.

Terra owns:

- versioned schemas/contracts;
- local state model/storage;
- deterministic IDs/hashes/receipts;
- idempotency/conflict behavior;
- checkpoint/restart semantics;
- review/conclusion/evidence binding and staleness;
- canonical `RunBundle` schema/serialization;
- deterministic evaluator and metrics;
- fault/property tests and CI;
- later FOSSIL adapter only if explicitly admitted.

Terra must not:

- invent semantic research conclusions;
- alter benchmark gold to obtain a pass;
- add harness-specific shortcuts to the core;
- treat model self-report as trusted review/integrity evidence.

## Luna

Primary responsibility: model/harness-facing boundary.

Luna owns:

- OpenCode plugin/adapter;
- semantic tool/command UX;
- mapping stable OpenCode lifecycle events into canonical RA operations;
- harness/model/version identity capture;
- raw harness evidence capture where supported;
- user-facing status/review rendering;
- later second-harness/MCP adapters only after explicit entry gates.

Luna must not:

- change core state semantics because an adapter is inconvenient;
- add hidden benchmark-specific logic;
- auto-extract/verify every claim in the MVP;
- promote a conclusion without the required review semantics;
- make RA failure block ordinary research unless the operation is specifically a reviewed/accepted promotion.

## Build order

1. Freeze schemas/contracts and deterministic tests.
2. Implement core with no model calls.
3. Pass fault/property/metamorphic tests.
4. Implement thin OpenCode adapter.
5. Pass adapter conformance tests.
6. Implement benchmark runner/evaluator against public development microworlds.
7. Freeze SHAs before confirmatory evaluation.
8. Do not start second harness or MCP work until the OpenCode experiment is reviewed by the program control plane.

## Definition of done

An issue is complete only when its acceptance criteria are mechanically demonstrated or explicitly human-reviewed where judgment is inherent.

A handoff must state:

- exact commit/PR;
- files/contracts changed;
- tests actually run and exact result;
- artifacts produced;
- benchmark/holdout impact;
- unresolved uncertainty;
- next unblocked issue.

No `done`, `verified`, `passed`, or equivalent state may be inferred solely from an agent statement.
