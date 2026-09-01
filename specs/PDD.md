# RA Plugin MVP — Product/Program Design Document

## Problem

BYOK coding-agent harnesses can expose strong models yet still perform weakly on sustained research because research state, evidence identity, contradictions, unresolved questions, and cross-session continuity are often represented only in conversational context or harness-specific logs.

Previous generic stamp/compliance approaches are a negative design precedent: agents could game them, become blocked by them, fail to understand the required workflow, or satisfy form without satisfying intent. The MVP therefore tests a much narrower hypothesis instead of building universal agent governance.

## Goal

Determine whether a small, model-independent research-state substrate with bounded human review at consequential conclusion transitions improves research continuity, evidence discipline, and conclusion quality compared with the native harness alone.

The MVP is an experiment. It is not presumed to become a production subsystem.

## First integration target

OpenCode is the first adapter because it provides a multi-vendor BYOK environment and a plugin surface suitable for testing whether the effect is attributable to the RA substrate rather than one model provider.

A second harness is conditional on positive OpenCode evidence. MCP/ChatGPT is an interoperability adapter later, not the core architecture.

## User-visible capability

The user or agent can start/resume a research session, capture evidence references, propose claims, create checkpoints, inspect current research state, and request human review of a candidate conclusion.

Ordinary exploration must remain possible if the RA substrate is unavailable. Reviewed/accepted conclusion promotion must fail closed when its required receipt cannot be produced.

## Primary hypotheses

H1. Structured RA checkpoints improve state recovery after interruption relative to native harness state.

H2. Structured evidence/claim/contradiction state reduces unsupported conclusions and loss of unresolved contradictions without materially increasing task failure.

H3. Bounded HITL at conclusion promotion provides useful correction with substantially lower burden than per-response/per-claim verification.

H4. Any benefit is not limited to one model family; portability to a second harness is a later test, not assumed.

## Non-goals

- universal agent governance;
- coding-task completion certification;
- automatic extraction or proof of every model claim;
- generic `verified=true` or stamp semantics;
- source ranking or semantic claim verification in the MVP;
- GraphRAG, ontology, or universal research graph;
- FOSSIL as a mandatory runtime dependency;
- MCP as the canonical internal protocol;
- autonomous human-review simulation;
- proving that stronger models are unnecessary.

## Success measures

The experiment reports at minimum:

- state-recovery accuracy after interruption;
- final-decision accuracy;
- supporting-evidence recall;
- unsupported-conclusion rate;
- temporal/version error rate;
- contradiction retention;
- duplicate-work rate;
- human-review burden;
- protocol-induced failure rate;
- token/time/cost overhead.

Exact confirmatory thresholds are preregistered before the frozen pilot.

## Valid outcomes

The project may conclude `ADOPT_FOR_FURTHER_TEST`, `HARNESS_SPECIFIC`, `MODEL_SPECIFIC`, `NO_MEASURABLE_BENEFIT`, `BENEFIT_TOO_SMALL_FOR_COMPLEXITY`, `REDESIGN_REQUIRED`, or `REJECT`.

A negative result must not be converted into success by adding unplanned features during the same benchmark campaign.
