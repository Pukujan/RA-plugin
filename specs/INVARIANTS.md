# RA Plugin MVP — System Invariants

- RA-INV-001: A model-facing operation cannot create, overwrite, or forge a human-review receipt.
- RA-INV-002: A review is valid only for the exact normalized conclusion digest and exact evidence-set digest it reviewed.
- RA-INV-003: Any material conclusion change or evidence-set change makes the prior review `STALE`; stale review cannot authorize reviewed/accepted state.
- RA-INV-004: Ordinary research remains possible when the RA substrate is unavailable; RA failure cannot silently convert ordinary work into reviewed/accepted work.
- RA-INV-005: Same idempotency identity plus same normalized content converges to the same durable result; same identity plus conflicting content fails loudly.
- RA-INV-006: A completed checkpoint is replayable after process restart to the same normalized research state; partial/incomplete checkpoint state cannot masquerade as complete.
- RA-INV-007: Unknown future schema/contract versions are refused rather than silently interpreted as a known version.
- RA-INV-008: Evidence-byte digests are computed by trusted deterministic code when bytes are captured; model-supplied hashes are never treated as integrity proof.
- RA-INV-009: Adapter-specific behavior cannot alter canonical core semantics or benchmark scoring.
- RA-INV-010: Every experimental run records exact harness, adapter, model/provider, RA core/schema, and benchmark identities needed to interpret the result.
- RA-INV-011: Hidden confirmatory gold is not available to evaluated models, harness adapters, or implementation agents before the corresponding implementation/evaluator identities are frozen.
- RA-INV-012: A canonical `RunBundle` cannot claim events/reviews/checkpoints that are absent from the underlying canonical RA state or raw run evidence.
- RA-INV-013: Duplicate evidence identity must not become independent corroboration merely because it was recorded twice.
- RA-INV-014: No single boolean `verified=true` collapses evidence integrity, human review, semantic support, or research correctness.
- RA-INV-015: The MVP cannot silently expand into source ranking, semantic claim verification, GraphRAG, general coding governance, or a second harness without an explicit issue and new empirical entry criterion.

These invariants are normative for MVP implementation. Each invariant must map to one or more deterministic, metamorphic, fault, adapter-conformance, or benchmark checks before the corresponding capability is considered complete.
