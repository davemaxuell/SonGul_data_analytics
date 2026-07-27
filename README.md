# SonGul — Generated Injection Dataset Analytics

Public transparency report for the finalized **SonGul Phase 5B–F Korean
learner-error dataset**, measured against the real NIKL learner corpus.

- **`index.html`** — main report, eight-axis fidelity scorecard, charts, and
  finalized artifact provenance.
- **`explorer.html`** — searchable full data tables and the complete score
  derivation.

Current release: `20260721_phase5bf_paragraph_merged`, finalized 2026-07-25.

- 612,029 paragraph records
- 1,188,356 sentences (944,175 errored)
- 1,436,790 error annotations
- 82.70% replication score
- 99.7% NIKL exact-combination mass coverage
- SHA-256:
  `eeccd1df8c9e6f831adfeb28f5b0265dcd947959fa54f7b84123c7c45fe4cba7`

The pages are fully static and self-contained. They are rebuilt from the
private final JSONL with `tools/build_report_data.py`; Vercel deploys this
repository automatically after a push to `main`.

The published build script documents the calculation. It cannot run from this
repository alone because the source dataset and frozen NIKL reference tables
remain in the private Kor_AI pipeline repository. Density is measured per
errored sentence, while L1 distributions are sentence-weighted.
