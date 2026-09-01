# RA Plugin MVP plan

## Research question

Does a small, model-independent research-state substrate with bounded human review improve research continuity, evidence discipline, and conclusion quality in BYOK agent harnesses compared with the native harness alone?

The MVP is an experiment, not a commitment to a production subsystem.

## Scope

The MVP implements only enough behavior to test persistent research state and early human-in-the-loop conclusion review.

Semantic operations:

- `session.start` / `session.resume`
- `session.status`
- `evidence.capture`
- `claim.propose`
- `checkpoint.create`
- `conclusion.review`

The first adapter is an OpenCode plugin.

## Non-scope

Do not implement in the MVP:

- automatic extraction/verification of every model claim;
- universal stamps or response-level proof requirements;
- source-ranker integration;
- semantic claim verifier;
- GraphRAG or an assurance knowledge graph;
- general coding-task governance;
- mandatory human review for ordinary exploration;
- MCP as the canonical core boundary;
- multiple harnesses before OpenCode shows empirical signal.

## Core model

A minimal state object should be sufficient:

```text
ResearchSession
├── objective
├── scope
├── evidence_refs[]
├── hypotheses[]
├── claims[]
├── contradictions[]
├── unresolved_questions[]
├── experiments[]
└── decisions[]
```

Do not turn this into a universal ontology.

## HITL boundary

Human review occurs only when a candidate conclusion is being promoted from exploration into a reviewed research conclusion.

```text
exploration
   ↓
claim.propose
   ↓
conclusion.review
   ↓
ACCEPT
REJECT
NEEDS_MORE_EVIDENCE
ACCEPT_WITH_LIMITATIONS
```

A review binds to the exact normalized conclusion digest and exact evidence-set digest. If either changes, review state becomes `STALE`.

The model may propose a conclusion, but it cannot manufacture a human-review receipt.

## Availability boundary

RA must not block ordinary research because the substrate fails.

```text
RA unavailable -> research continues
RA unavailable -> reviewed/accepted promotion unavailable
```

This explicitly avoids recreating prior stamp systems where protocol failure prevented useful work.

## Trusted vs model-owned fields

The model may propose:

- objective/scope updates;
- evidence references;
- hypotheses;
- claims;
- unresolved questions;
- candidate conclusions.

Trusted deterministic code owns:

- IDs/digests;
- timestamps where required;
- idempotency;
- state versioning;
- evidence byte hashes when bytes are captured;
- review/conclusion binding;
- adapter/harness/model identity in run records.

The model must not self-declare integrity/review PASS states.

## Storage

Use the simplest deterministic local store that satisfies restart/replay tests. SQLite or an equivalent small local store is acceptable.

Do not make FOSSIL a runtime dependency for the MVP. Add a FOSSIL export/integration adapter only after the core experiment demonstrates value or if exact evidence preservation is cheaper to reuse directly than duplicate.

## Adapter architecture

```text
RA core/library
     |
semantic operation boundary
     |
  OpenCode plugin
```

Later adapters reuse the same core:

```text
RA core
├── OpenCode plugin
├── Oh My Pi extension   [only after signal]
└── MCP adapter          [later / optional]
```

Harness-specific lifecycle behavior must remain in adapters.

## OpenCode plugin responsibilities

The first plugin may:

- expose the six semantic operations as tools/commands;
- load current RA session state at explicit research-session start/resume;
- persist checkpoints at explicit command and stable lifecycle boundaries that OpenCode actually supports;
- record harness/model/version identity;
- export a canonical `RunBundle` for evaluation.

It must not initially:

- block every model response;
- force evidence capture for every source/tool call;
- automatically promote claims;
- hide errors behind synthetic PASS states;
- modify benchmark scoring.

## Canonical RunBundle

Every future adapter must emit the same experiment artifact:

```json
{
  "run_id": "...",
  "task_id": "...",
  "condition": "baseline|ra",
  "harness": {
    "name": "...",
    "version": "...",
    "adapter_sha": "..."
  },
  "model": {
    "provider": "...",
    "model": "...",
    "parameters": {}
  },
  "events": [],
  "evidence_refs": [],
  "claims": [],
  "checkpoints": [],
  "reviews": [],
  "final_answer": "...",
  "usage": {
    "input_tokens": null,
    "output_tokens": null,
    "cost": null,
    "elapsed_ms": null
  }
}
```

The evaluator consumes `RunBundle`; it should not depend on arbitrary native harness logs when a canonical field can represent the needed observation.

## Build gates

### Gate A — deterministic core

No model calls. Required tests include:

- state/schema version validation;
- idempotent retries;
- conflicting-id/content refusal;
- checkpoint/restart determinism;
- changed claim invalidates existing review;
- changed evidence set invalidates existing review;
- corrupt persisted state fails loudly;
- unknown future schema version fails safely;
- adapter/model identity recorded in run bundle;
- model-facing API cannot forge a human review.

Do not spend model tokens before this gate passes.

### Gate B — OpenCode-only experiment

Use 2–3 affordable cross-vendor models available through the user's normal BYOK/subscription paths.

For each model run paired conditions:

```text
OpenCode native baseline
OpenCode + RA MVP
```

Use frozen research-microworld tasks from `docs/EXPERIMENT_PROTOCOL.md`.

### Gate C — second harness

Only if Gate B shows enough positive signal to justify portability work, add an Oh My Pi (or another selected harness) adapter and rerun shared models where available.

### Gate D — MCP / ChatGPT

MCP is a transport/interoperability experiment after core semantics and local plugin value are stable. It must not become a prerequisite for the OpenCode experiment.

## Provisional MVP success criteria

Freeze exact thresholds before confirmatory evaluation. Initial planning targets:

- state-recovery accuracy: >=25% relative improvement over native baseline on interruption tasks;
- final-decision accuracy: positive paired improvement with uncertainty reported;
- unsupported-conclusion rate: no regression and preferably meaningful decrease;
- protocol-induced failure rate: <5%;
- median token/time overhead: <30% unless quality improvement clearly justifies more;
- human-review burden: low enough that review is exception-focused rather than continuous work.

These are provisional preregistration targets, not external standards.

## Valid negative outcome

The experiment may conclude:

- `NO_MEASURABLE_BENEFIT`;
- `BENEFIT_TOO_SMALL_FOR_COMPLEXITY`;
- `HARNESS_SPECIFIC`;
- `MODEL_SPECIFIC`;
- `REDESIGN_REQUIRED`;
- `REJECT`.

A negative result is useful and must not be converted into a success claim by adding more features mid-benchmark.
