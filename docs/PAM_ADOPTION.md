# PAM second-adopter assessment

This branch exercises Project Assurance Modules as methodology/configuration/schema/evidence-state on `RA-plugin`. It does **not** add PAM as a runtime dependency and it does not modify the frozen RA retrospective benchmark.

## Live-state boundary

This adoption branch is stacked on the exact head of RA-plugin planning PR #2:

- repository: `Pukujan/RA-plugin`
- planning PR: `#2`
- planning head used for adoption: `7b47d80221cd2c5eaaed23a23ab2fff8d4189681`
- executable parent issue: `#1`

PR #2 is still an open proposal, not merged/default-branch truth. `HANDOFF_STATE.json` is current resumable adoption state; PR #2's planning commit and this document are historical/adoption checkpoints. A resumed worker must re-fetch live issue/PR/CI state before mutation.

The Research Assurance control plane was also re-fetched before adoption. Program methodology, benchmark interpretation, and program-level scope remain owned by `Pukujan/research-assurance`; RA-plugin owns only the bounded harness experiment.

## PAM identity

This adopter pins the exact bounded v0.2 development revision:

`Pukujan/project-assurance-modules@a10ad56b7088c1e101e80914a9e00357dbef9120`

That revision is the open PAM v0.2 PR #5 head, not a stable release. The adoption workflow fetches this exact commit, checks it out detached, verifies `HEAD`, installs its validator package only for CI, then validates the adopter-owned manifest/handoff/bootstrap files.

No PAM runtime code is imported by the RA-plugin product design.

## Profile selection

Declared RA-plugin facts select these profiles:

- `projectization.software@0.1.0`
- `continuity.material-work@0.1.0`
- `benchmark.empirical-work@0.1.0`
- `provenance.material-decisions@0.1.0`

The corresponding routed modules are all required for this project state:

- `projectization.build-vs-reuse@0.1.0`
- `projectization.scope-boundary@0.1.0`
- `continuity.structured-handoff@0.1.0`
- `planning.foundation@0.1.0`
- `engineering.swe-ci-foundation@0.1.0`
- `benchmark.integrity@0.1.0`
- `provenance.decision-lineage@0.1.0`

Profile selection does not itself close any requirement. Requirement states in `PROJECT_ASSURANCE.json` are backed by project-owned evidence or remain pending/N/A.

## What the existing RA-plugin plan already satisfies

The planning PR independently contains strong evidence for several PAM obligations without being rewritten to match PAM:

- product outcome, hypotheses, non-goals, and valid negative outcomes in `specs/PDD.md` and `docs/MVP_PLAN.md`;
- component, state, trust, persistence, adapter, and authority boundaries in `specs/SDD.md` and `AGENTS.md`;
- explicit system invariants in `specs/INVARIANTS.md`;
- an MVP-scoped failure register in `docs/FAILURE_MODES.md`;
- explicit validation layers in `docs/VALIDATION_STRATEGY.md`;
- a paired experimental protocol, public-development/hidden-confirmatory split, and contamination controls in `docs/EXPERIMENT_PROTOCOL.md`;
- strong scope admission/kill rules around second harnesses, MCP, source ranking, semantic verification, GraphRAG, and other attractive adjacent mechanisms;
- fresh-session instructions that re-fetch live RA-plugin and Research Assurance state instead of trusting chat memory.

This is useful second-adopter evidence because those artifacts existed before PAM v0.2 was applied to the repository.

## Honest gaps surfaced by PAM

### 1. Build-vs-reuse evidence is not yet closed

RA-plugin proposes a new deterministic RA core plus thin OpenCode adapter, but the planning branch does not yet contain an exact candidate register and cheap compatibility probes showing which existing maintained systems/libraries can or cannot satisfy portions of the proposed core.

Therefore `REUSE_002` through `REUSE_006` remain pending. The bespoke core must earn itself before large implementation begins; the existence of a plausible architecture is not the same as a completed reuse disposition.

### 2. Generic machine handoff validation is new adopter infrastructure

`AGENTS.md` already has strong continuity semantics, but the project did not have a generic machine-readable handoff state/schema validation lane. This adoption adds `HANDOFF_STATE.json` and exact-PAM validation without replacing the project's planning documents.

`HANDOFF-003` remains pending until the adoption workflow actually passes on the exact pinned PAM revision.

### 3. SWE/CI foundation is intentionally pending

The planning branch has a detailed validation strategy but no implementation package, local deterministic check command, test suite, or CI workflow for RA-plugin code yet. `SWE_CI_001` through `SWE_CI_005` remain pending rather than being falsely satisfied by planning prose.

The PAM adoption workflow validates methodology state only; it does not close the future RA-plugin implementation CI requirement.

### 4. Benchmark identity and leakage tooling are not yet executable

The experiment protocol has a good development/confirmatory boundary, but exact first-campaign task/data manifests and a deterministic blind/hidden packaging leakage validator do not yet exist. `BENCH_INT_002`, `BENCH_INT_004`, and `BENCH_INT_005` remain pending.

This matches the earlier retrospective lesson: prose saying material is hidden is not equivalent to fail-closed packaging validation.

### 5. Consequential decision lineage is only partially explicit

RA-plugin clearly separates local plugin authority from Research Assurance program authority, but exact source/outcome lineage and explicit accepted-versus-proposed status for consequential architecture/benchmark decisions are not yet frozen as a portable decision record. `PROV_LINEAGE_002` and `PROV_LINEAGE_003` remain pending.

`PROV_LINEAGE_005` is explicitly not applicable because this adopter claims no external FOSSIL/provenance-runtime ingest or promotion. Storage of project files is not relabeled as an ingest receipt.

## PAM defects / adopter-specific exceptions

At initial adoption there is **no known need for a bespoke PAM methodology edit**. The project can express its current state using the generic v0.2 profiles, modules, manifest, handoff, and bootstrap contracts.

If exact validation finds an incompatibility, it must be recorded as one of:

1. a PAM defect that should be fixed generically on the PAM branch;
2. a project/domain-specific not-applicable requirement with explicit rationale;
3. a real RA-plugin gap that remains pending/blocked.

Do not silently edit PAM solely to make this adopter appear complete.

## Next action

Validate this adoption against the exact pinned PAM revision. After validation, reconcile live PR/issue state and review the pending build-vs-reuse gaps before RA-001 implementation begins.

Do not run the OpenCode model benchmark as part of PAM adoption. The RA-plugin issue's deterministic contract/core/evaluator gates remain authoritative for when model spend is allowed.
