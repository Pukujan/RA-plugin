# RA Plugin

`RA-plugin` is the model- and harness-facing experiment for the broader Research Assurance program.

Its purpose is narrow:

> Test whether a small, model-independent research-state and human-review substrate improves research continuity, evidence discipline, and conclusion quality in BYOK agent harnesses.

The repository is **not** the Research Assurance control plane, not a universal agent-governance system, and not a replacement for FOSSIL, source-ranker, retrieval-benchmarker, or domain applications.

## Read first

- [`docs/MVP_PLAN.md`](docs/MVP_PLAN.md) — frozen MVP scope, semantic operations, HITL boundary, build gates, provisional success/kill criteria.
- [`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md) — cross-model/harness benchmark design, research microworlds, interruption tests, metrics, contamination controls.
- [`docs/ADAPTER_PLAN.md`](docs/ADAPTER_PLAN.md) — OpenCode plugin first; second harness and MCP/ChatGPT adapters only after evidence justifies them.
- [`AGENTS.md`](AGENTS.md) — Terra/Luna implementation ownership and rules.
- GitHub issue `#1` — executable MVP parent issue and acceptance sequence.

## Initial architecture

```text
research-assurance (program/control plane)
             |
             v
          RA-plugin
      model-independent core
             |
      adapter / plugin layer
       /       |        \
 OpenCode   Oh My Pi    MCP later
    |           |          |
 multi-vendor models    ChatGPT/app
```

The first implementation target is an **OpenCode plugin**. MCP is a later transport adapter, not the core architecture.

## MVP hypothesis

The first experiment asks:

> Does persistent, structured research state plus bounded human review at consequential conclusion transitions improve research performance compared with the native harness alone?

The MVP does **not** require source ranking, semantic claim verification, automatic claim extraction, GraphRAG, or mandatory proof for every model statement.

## Planned semantic operations

- `session.start` / `session.resume`
- `session.status`
- `evidence.capture`
- `claim.propose`
- `checkpoint.create`
- `conclusion.review`

A human review binds to the exact proposed conclusion and evidence set. If either changes, that review becomes stale.

## Fail-open / fail-closed boundary

Research work must continue if the RA substrate is unavailable. Promotion to an accepted/reviewed conclusion must not silently succeed without the required receipt.

```text
RA unavailable -> research can continue
RA unavailable -> accepted conclusion unavailable
```

## Cross-harness evaluation

Every supported adapter must emit one canonical `RunBundle` so evaluation is independent of harness-specific logs. OpenCode is the first adapter; a second harness is added only after the OpenCode experiment shows enough signal to justify portability testing.

## Relationship to Research Assurance

Program methodology, benchmark policy, scope control, adversarial-review rules, and layer-level empirical claims remain owned by `Pukujan/research-assurance`.

This repository owns only the bounded agent-harness experiment and its adapters.
