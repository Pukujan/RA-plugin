# RA Plugin MVP — Validation Strategy

## Pre-implementation gate

Before substantive implementation begins, the MVP must have reviewed and internally consistent:

- `specs/PDD.md`;
- `specs/SDD.md`;
- `specs/INVARIANTS.md`;
- `docs/FAILURE_MODES.md`;
- `docs/MVP_PLAN.md`;
- `docs/EXPERIMENT_PROTOCOL.md`;
- versioned schemas/contracts for the canonical objects and operations.

Implementation work should begin from failing tests/checks derived from these artifacts, not from agent-invented behavior.

## Deterministic test layers

### Unit and schema tests

Cover canonicalization, IDs/digests, set normalization, review binding, version parsing, idempotency, conflict detection, serialization, RunBundle generation, and privilege separation.

### Property/state-machine tests

Use property-based state-machine tests over sequences such as start -> propose -> checkpoint -> review -> mutate -> resume. Generate valid and invalid operation sequences and assert invariants continuously.

At minimum exercise:

- repeated retries;
- conflicting retries;
- multiple checkpoints;
- review before/after claim mutation;
- review before/after evidence mutation;
- restart at arbitrary legal states;
- unknown version input;
- malformed/untrusted model payloads.

## Metamorphic tests

Metamorphic relations are versioned and mapped to invariants.

Required MVP relations include:

1. Reordering an evidence set without changing membership must not change its canonical evidence-set digest.
2. Adding the same evidence identity twice must not create independent corroboration or a different set identity.
3. Removing or adding a material evidence identity after review must make the review stale.
4. A material qualifier/conclusion change must change the conclusion digest and stale review.
5. Canonically equivalent formatting/whitespace changes, as defined by the frozen normalizer, must not create a new semantic review target.
6. Replaying the same idempotent request must converge to the same durable identity/result.
7. Replacing an idempotent request's content while retaining identity must change outcome from success/replay to explicit conflict.
8. Serialize -> restart -> resume -> serialize without intervening mutation must preserve normalized state.
9. Changing harness/model identity for a new run must not rewrite prior run identity or prior research state.
10. Making the RA adapter unavailable must not prevent the harness from continuing ordinary research, while reviewed promotion must remain unavailable.
11. Corrupting captured evidence bytes must change the trusted digest or fail integrity checks; a model-supplied unchanged hash must not override that result.
12. Removing an unresolved contradiction from a checkpoint without a resolving event must be detected by state-transition/benchmark checks rather than silently treated as resolved.

## Fault-injection tests

Inject failures at durable boundaries:

- process kill before/during/after checkpoint commit;
- locked/unavailable database;
- truncated/corrupted state record;
- disk/write failure where reproducible;
- plugin exception around a semantic operation;
- duplicate/concurrent retry;
- adapter receiving malformed tool arguments;
- unsupported harness/version metadata.

Required property: failure is either atomically absent or explicitly detectable as incomplete/error; it must not become a successful reviewed state accidentally.

## Mutation testing

Run targeted mutation testing on high-value deterministic policy code. The suite should kill mutants equivalent to:

- removing review-staleness checks;
- allowing model-facing review writes;
- ignoring evidence-set changes;
- disabling idempotency conflicts;
- treating unknown schema versions as current;
- converting adapter exceptions into successful review/promotion;
- changing fail-open research / fail-closed review behavior;
- permitting duplicate evidence to count as independent identity.

Surviving mutants are reviewed individually; raw mutation score is not itself an assurance claim.

## Adapter conformance

The OpenCode adapter has a harness-independent conformance suite using a fake/stub harness boundary where feasible. It must prove:

- canonical operation names/inputs/outputs are preserved;
- adapter cannot manufacture privileged review state;
- adapter errors do not alter core semantics;
- benchmark scoring is absent from adapter code paths;
- exact harness/model/adapter version identity is emitted;
- canonical RunBundle is reproducible from the same canonical run evidence.

A future second harness must pass the same core conformance suite before cross-harness comparison.

## Benchmark/evaluation tests

Public development microworlds validate evaluator correctness before model experiments. Scorer unit tests use hand-checkable fixtures for required evidence, temporal cutoffs, evidence roots, contradictions, unsupported claims, expected inconclusive outcomes, interruption markers, and protocol-induced failures.

The evaluator itself receives mutation/golden tests so a scoring bug cannot make RA appear better by construction.

## Model-use gate

No paid/model benchmark run is part of proof until the deterministic core, invariant mapping, adapter conformance, scorer golden tests, and public development fixtures are green.

The initial OpenCode pilot is then a research experiment, not a substitute for deterministic correctness testing.

## CI lanes

Fast PR CI: format/lint/type/schema/unit/contract/property-smoke tests and deterministic adapter conformance.

Deep/manual CI: larger property campaigns, fault injection, targeted mutation testing, repeated restart/replay, benchmark evaluator golden suite.

Confirmatory model benchmark: frozen separately with exact core/adapter/evaluator/benchmark identities and hidden material outside the public repo.

## Formal methods boundary

TLA+ is not required for the MVP unless concurrency/distribution makes state-space exploration materially useful. Property-based state-machine validation is mandatory from the start.

## Definition of deterministic-core done

The deterministic core is not done because examples work. It is done when every `RA-INV-*` has mapped executable evidence, required metamorphic/fault cases pass, targeted high-value mutants are killed or explicitly reviewed, and the core can be restarted/replayed without ambiguous reviewed state.
