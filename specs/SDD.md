# RA Plugin MVP — System Design Document

## Composition

The MVP has four layers:

1. a deterministic RA core/library;
2. a simple local persistent store;
3. a versioned semantic operation boundary;
4. a thin harness adapter, initially OpenCode.

The benchmark/evaluator is separate from the runtime and consumes canonical `RunBundle` artifacts.

## Canonical operations

- `session.start` / `session.resume`
- `session.status`
- `evidence.capture`
- `claim.propose`
- `checkpoint.create`
- `conclusion.review`

No adapter may add hidden semantic judgment or benchmark-specific behavior to these operations.

## Canonical state

`ResearchSession` contains only the minimum experiment state: objective, scope, evidence references, hypotheses, claims, contradictions, unresolved questions, experiments, decisions, and version metadata.

This is not a universal ontology.

## Authority boundaries

The model may propose research content and references. Deterministic code owns IDs, normalized digests, idempotency, state versioning, persisted integrity metadata, review/conclusion binding, and harness/model/run identity.

A human-review receipt is privileged state. Model-facing APIs cannot create or mutate it directly.

## Review binding

A review binds to:

- normalized conclusion digest;
- exact evidence-set digest;
- review decision;
- review identity/actor as supplied by the trusted review surface;
- schema/policy version.

Any semantically material conclusion change or evidence-set change makes the prior review `STALE`. Canonicalization rules must be deterministic and versioned.

## Availability boundary

The runtime is fail-open for ordinary research and fail-closed for reviewed promotion:

```text
RA runtime unavailable -> research may continue outside reviewed state
required review/receipt unavailable -> reviewed/accepted promotion unavailable
```

No plugin exception may make the underlying harness unusable for ordinary research unless the harness itself requires the failed operation.

## Persistence

Use the smallest local store that can satisfy crash/restart/replay tests. SQLite is the default candidate. Durable writes use transactions or an explicit incomplete-state protocol; partial state must never masquerade as complete state.

Unknown future schema versions are refused rather than guessed or silently downgraded.

## Idempotency and conflicts

Mutating operations carry stable request/idempotency identity. Repeating the same operation with the same identity and same normalized content converges to the same result. Same identity with conflicting content fails loudly.

## RunBundle

All adapters emit the same versioned `RunBundle` containing task/condition, harness and adapter identity, model/provider identity, RA core/schema version, events, evidence refs, claims, checkpoints, reviews, final answer, interruption markers, usage metadata, and raw artifact references/digests.

The evaluator scores the canonical bundle plus frozen task gold, not adapter-specific convenience fields.

## Adapter boundary

The OpenCode plugin translates supported lifecycle/tool events into canonical RA operations. It may expose commands/tools and capture stable lifecycle events, but it must not own source-quality judgment, semantic verification, benchmark scoring, or human-review authority.

A second harness must reuse the same core and pass the same adapter conformance suite before cross-harness claims are permitted.

## Security / trust assumptions for MVP

The MVP is a local single-user research experiment. It is not a hostile multi-tenant service. The model is untrusted with respect to privileged review/integrity fields. Local filesystem/database corruption, retries, plugin exceptions, malformed model/tool payloads, and version skew are in scope. Byzantine local administrators and remote hostile tenants are not MVP claims.

## Formal-method boundary

Do not add TLA+ merely because the system has states. Property-based state-machine tests are the initial formalized mechanism. TLA+ becomes a candidate only if concurrent/distributed writers or more complex promotion state make reachable-state reasoning materially valuable.
