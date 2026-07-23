# SonGul — Generated Injection Dataset Analytics

Public transparency report for the **SonGul Phase 5B–F generated Korean
learner-error dataset**, measured against the real NIKL 학습자 말뭉치.

- **`index.html`** — main report: EDA, 8-axis fidelity scorecard with overall
  replication score, dataset provenance (release SHA-256, judge audit).
- **`explorer.html`** — full data explorer: every error location code, level,
  tag combination and word pair (search / sort / filter), plus the score derivation.

Pages are fully static and self-contained. They are **pre-built** from each
dataset release by `build_report_data.py` in the (private) Kor_AI pipeline
repo — every number on both pages renders from embedded data blocks, so a new
release only replaces those blocks.

Current release: `20260714_phase5b-f_5model` — 610,416 sentences ·
952,819 judge-approved error annotations.
