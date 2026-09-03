# RA-plugin implementation status

This file records the bounded experiment state; program-level phase decisions
remain owned by `Pukujan/research-assurance`.

## Durable commits

- Design freeze PR #2 merged at `6a6f30677e5502b72d2d3fef4052879614b8a020`.
- Core/adapter/development benchmark PR #4 merged at `8bac8bd37d13cbfdba1179acc34a41606d8bb3f6`.
- OpenCode pilot runner PR #5 merged at `0eb533689a4be889c43658585c5910de4025f4e7`.

## Implemented gates

- RA-001: versioned contracts for `ResearchSession`, `EvidenceRef`,
  `ResearchClaim`, `Checkpoint`, `HumanReview`, and `RunBundle`; unknown
  versions refuse; canonical digest and evidence-set normalization are tested.
- RA-002: deterministic JSON state core with atomic replacement, integrity
  envelope, trusted evidence-byte hashes, idempotent retries, loud conflicts,
  restart/checkpoint behavior, review staleness, and fail-closed promotion.
- RA-003: thin OpenCode command/lifecycle adapter.  Model-facing calls cannot
  issue reviews; ordinary research degrades open when RA is unavailable.
- RA-004: seven visible development microworlds and a paired evaluator with
  raw RunBundles preserved before summary generation.

## Validation evidence

`python -m pytest -q` passes 21 tests locally and in GitHub Actions.  The
development runner produced 14 fixture RunBundles (seven cases × baseline/RA)
under `artifacts/dev-benchmark/`; these are scripted validation fixtures, not
model evidence.

## RA-005 public pilot

The frozen public pilot used OpenCode `1.18.21`,
`openrouter/minimax/minimax-m3`, and `openrouter/xiaomi/mimo-v2.5-pro` over
seven atomic public microworlds, paired baseline/RA (28 runs).  Raw OpenCode
event responses and canonical RunBundles are under
`artifacts/opencode-pilot-minimax-mimo/`; `freeze.json` records the exact
identities and matrix.

The pilot report is explicitly `public-microworlds-only`.  It contains no
hidden-holdout or confirmatory claim.  No human-review receipts were
fabricated; all RA promotion remains review-pending and fail-closed until a
real reviewer acts.

## Remaining gate

Before any confirmatory campaign or M2 work, the owner must provide a real
review surface/decision process and freeze a non-public holdout manifest under
the control plane.  Public pilot results alone are insufficient to claim that
the plugin wins; `NO_MEASURABLE_BENEFIT` remains a valid outcome.

