# Cross-harness experiment protocol

## Objective

Measure the incremental effect of the RA state/HITL substrate independently of model and harness choice.

Primary causal contrast:

```text
same task + same harness + same model
native baseline
vs
native harness + RA
```

Only after an OpenCode signal exists do we test portability across harnesses.

## Why not start with live-web research

Live search introduces uncontrolled variance:

- search rankings change;
- pages change/disappear;
- provider search tools differ;
- network timing/access differs;
- models may receive different source pools.

The confirmatory MVP therefore begins with frozen **research microworlds** that preserve real research structure while keeping objective gold.

Live-web tasks may be exploratory/secondary evidence later.

## Research microworld case

Each case contains a frozen corpus of approximately 20–50 documents/artifacts with known relationships such as:

- direct primary source;
- secondary summary;
- stale and current versions;
- duplicated/syndicated sources sharing one evidence root;
- contradictory evidence;
- irrelevant but high-reputation distractors;
- benchmark/method result;
- methodological limitation;
- temporal cutoff;
- explicit no-answer/inconclusive cases.

The hidden case manifest defines:

```text
eligible evidence under cutoff/version
required supporting evidence
known evidence roots
contradictions that must remain unresolved unless resolved by evidence
forbidden/unsupported claims
correct conclusion OR expected INCONCLUSIVE state
```

The evaluated model/harness does not receive the hidden manifest.

## Example task shape

Question:

> As of cutoff T, should implementation X or Y be preferred for workload W, and what evidence supports the conclusion?

Corpus may include:

```text
report_A_v1: X = 420 ms
report_A_v2: X = 190 ms, released after/before chosen cutoff depending case
vendor_blog: X = 100 ms on a different workload
independent_test: X = 205 ms on target workload
news_1 -> vendor_blog
news_2 -> news_1
Y_test: Y = 240 ms on target workload
```

Gold can detect:

- future evidence leakage;
- stale-version use;
- workload qualifier loss;
- duplicate corroboration;
- contradiction loss;
- unsupported overgeneralization.

## Conditions

### Phase 1 — OpenCode

For each selected affordable model:

```text
A: OpenCode native baseline
B: OpenCode + RA
```

Use paired tasks and randomize/counterbalance task order where feasible.

Do not require GPT-5.6 Sol as a routine experimental model. Expensive/high-capability models may be used as reference ceilings, not independent proof of an architecture they helped design.

### Phase 2 — interruption/recovery

At deterministic task points (for example approximately 25%, 50%, or 75% through the research budget), force interruption:

- fresh session with same model;
- fresh session after context/state reset;
- optionally different model in the RA condition for cross-model handoff.

Baseline receives only the state normally available through the native harness/protocol. RA receives its structured checkpoint.

### Phase 3 — second harness

Only after Phase 1/2 demonstrates signal, port the exact semantic core to a second harness such as Oh My Pi.

Where models overlap, compare:

```text
OpenCode baseline
OpenCode + RA
second-harness baseline
second-harness + RA
```

This permits analysis of:

- model effect;
- harness effect;
- RA effect;
- RA × harness interaction;
- RA × model interaction.

## Canonical run artifact

Every adapter exports the same versioned `RunBundle`. Harness-native logs may be retained as raw evidence, but scoring operates on the canonical bundle plus frozen task gold.

At minimum record:

- task ID/version;
- condition;
- harness name/version;
- adapter SHA;
- provider/model identity and parameters where observable;
- RA core/schema version;
- event/evidence/claim/checkpoint/review records;
- final answer/conclusion;
- interruption/resume markers;
- token/cost/elapsed-time data where available;
- raw artifact references/digests.

## Primary metrics

### Research quality

- final decision/conclusion accuracy;
- supporting-evidence recall;
- unsupported-claim/conclusion rate;
- temporal/version error rate;
- expected-inconclusive/abstention accuracy.

### State quality

- objective/scope recovery accuracy;
- required evidence retained after interruption;
- unresolved contradiction retention;
- unresolved-question retention;
- stale/invalid evidence reintroduced;
- duplicate-work rate;
- time/actions required to regain productive state.

### HITL burden

- number of review actions per task;
- accept/reject/needs-more-evidence distribution;
- fraction of accepted conclusions later found incorrect by gold;
- human correction time if measured.

### Protocol harm

**Protocol-induced failure rate** is first-class:

> Fraction of tasks where the RA protocol causes looping, blocking, unusable tool behavior, corrupted state, or failure that the baseline did not exhibit.

Also record:

- adapter/tool errors;
- retries caused by RA;
- tokens/time/cost overhead;
- cases where the model attempts to game or bypass the RA semantics.

## Sample strategy

### Development

Use a small visible set to implement the protocol and expose adapter bugs. Do not treat it as confirmatory evidence.

### Initial OpenCode pilot

Approximately 20–30 substantial tasks across 2–3 affordable models may be enough to determine whether there is obvious signal/noise and protocol breakage.

### Confirmatory expansion

If the pilot passes entry criteria, freeze a larger hidden set. Exact sample size should be chosen from expected effect size/variance and available budget rather than copied mechanically from the pilot.

## Contamination controls

Implementation agents may see:

- schemas/contracts;
- metric definitions;
- public development cases;
- task generator code that does not reveal held-out seeds/gold;
- adapter conformance fixtures.

They do not see:

- confirmatory tasks before the implementation SHA is frozen;
- hidden labels/oracles;
- hidden perturbation seeds;
- per-model holdout failure details during the same confirmatory campaign.

At confirmatory start, freeze:

```text
RA core SHA
adapter SHA
harness version
model/provider identifiers
benchmark manifest/digest
evaluator SHA
```

A holdout failure becomes evidence for the next version; do not mutate the frozen benchmark to make the current implementation pass.

## Model independence

No majority vote across models is treated as technical truth. The gold/oracle determines task correctness.

Cross-provider models are useful for answering a different question:

> Is the RA effect robust across model families, or is the protocol overfit to one model's behavior?

A result that only benefits one model family is reported as model-specific rather than generalized.

## Harness independence

Adapters must remain thin. A harness adapter may translate lifecycle events/tools into canonical RA operations but must not add hidden scoring, source-quality logic, semantic verification, or benchmark-specific shortcuts.

Adapter conformance tests use the same RA core semantics.

## Analysis

Report raw per-task paired results, not only aggregate means. For proportions use confidence intervals; for paired outcomes use appropriate paired tests/intervals when sample size supports them.

Always report quality alongside cost/friction. A system that improves correctness by making many solvable tasks fail is not an acceptable win.

## Stop rules

Stop before second-harness work if:

- protocol-induced failure is unacceptably high;
- no meaningful state/quality signal appears;
- RA overhead dominates benefit;
- the adapter requires harness-specific semantics that cannot be expressed through the frozen core;
- human review becomes continuous rather than exception-focused.

Valid outcome: `NO_MEASURABLE_BENEFIT`.
