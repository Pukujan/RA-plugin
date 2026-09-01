# Adapter and transport plan

## Decision

The MVP is **plugin-first and transport-neutral**.

The Research Assurance semantics belong in a small local core. OpenCode is the first integration because its plugin lifecycle can participate in research state/checkpointing directly. MCP is a later interoperability adapter and must not become the core architecture.

```text
                 RA core
                   |
         canonical semantic API
           /        |        \
          /         |         \
 OpenCode plugin  Oh My Pi   MCP adapter
      first        later       later
                              |
                         ChatGPT/App
```

## Why plugin first

The experiment is about harness/state-management quality, not only tool availability. A plugin can potentially:

- expose semantic RA tools;
- observe stable session/lifecycle boundaries;
- restore/checkpoint state around context changes;
- record exact harness/model identity;
- integrate review UX without asking the model to remember every protocol step.

The plugin must stay thin: no hidden source ranking, semantic verification, benchmark scoring, or benchmark-specific shortcuts.

## OpenCode MVP adapter

Initial capabilities:

- explicit start/resume/status commands/tools;
- evidence capture through canonical core API;
- claim proposal and conclusion-review surfaces;
- explicit checkpoint plus only stable documented lifecycle hooks that are useful and testable;
- canonical `RunBundle` export;
- clear degraded mode when RA core is unavailable.

Do not initially auto-capture every source or intercept every assistant response.

## Second-harness adapter

A second adapter (candidate: Oh My Pi) is admitted only after the OpenCode experiment shows enough benefit to justify portability testing.

Its conformance target is the exact same semantic operation contracts and `RunBundle` schema. Harness-specific events are translated at the edge.

## MCP adapter

MCP is useful for clients that cannot load a native plugin/extension, especially ChatGPT Apps/custom integrations.

MCP phase begins only when:

1. the core semantic contracts are stable enough to avoid transport-driven churn;
2. OpenCode data shows the RA mechanism itself is useful;
3. a concrete MCP client need exists;
4. transport/authentication complexity is scoped separately from research semantics.

The MCP surface should expose the same semantic operations, not generic SQL/filesystem/shell access.

Candidate mapping:

```text
ra_session_start_or_resume
ra_session_status
ra_evidence_capture
ra_claim_propose
ra_checkpoint_create
ra_conclusion_review
ra_runbundle_export
```

Exact names are not frozen by this planning document; semantic behavior is.

## ChatGPT integration

ChatGPT integration, if used, is an adapter over the same core and may require a remotely reachable/private authenticated MCP endpoint depending on current product capabilities.

The architectural precedent is the user's Study OS design:

```text
ChatGPT
  -> custom app
  -> remote/private MCP
  -> local canonical runtime
```

RA-plugin must still function locally without ChatGPT or MCP.

## Trust boundary

Adapters may submit proposals and observed harness metadata. Trusted core code issues deterministic IDs/digests and enforces review binding/idempotency/state version rules.

No adapter may self-issue a human review or integrity PASS.

## Failure behavior

- ordinary research remains available when an adapter/core operation fails;
- reviewed/accepted promotion fails closed when its required receipt cannot be created;
- adapter errors are recorded as protocol errors in experiment output;
- no silent fallback may transform missing assurance evidence into PASS.

## Evaluation consequence

Adapters are judged by conformance and protocol-induced failure in addition to end research quality. An adapter that produces better benchmark answers through harness-specific hidden logic is invalid for the portability experiment.
