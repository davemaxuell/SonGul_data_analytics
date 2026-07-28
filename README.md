# Generated Injection Dataset — Report & Explorer

Public-facing analytics for the finalized SonGul Phase 5B–F paragraph release,
measured against the real NIKL Korean learner corpus.

Current release: `20260728_phase5bf_error_word_zero_coverage`, finalized
2026-07-28.

- 612,029 records
- 1,186,269 sentences, including 944,175 errored sentences
- 1,436,790 error annotations
- 43,784 independently judged 오류 어절 replacements, covering every
  semantically qualified zero-coverage pair
- 149 non-realizable source annotations and one independently rejected
  annotation fail closed
- SHA-256:
  `8b02878e2a358a6ed3b87dda37e1a773c6bdcd877268241ca16d6e5b09a82d11`
- 83.51625% eight-axis replication score (displayed as 83.5%), up 0.78125
  percentage points from the immutable parent
- 99.9% NIKL exact-combination **mass** coverage; 101 very rare NIKL
  combinations remain absent
- 48/48 actionable NIKL top-50 canonical error-morpheme pairs covered; the
  two same-surface rows are annotation artifacts, not injectable errors

| Page | Contents |
|---|---|
| `PHASE2_VS_PHASE5_ERROR_EDA_20260714.html` | Main report, scorecard, charts, bilingual explanations, and finalized artifact provenance |
| `PHASE2_VS_PHASE5_ERROR_EDA_20260714_EXPLORER.html` | Searchable full location, level, exact-combination, and word-pair tables, plus the complete score derivation |

The filenames retain `20260714` for stable public links; the embedded release
metadata and displayed evidence are from the finalized `20260728` zero-pair
coverage release.

## Rebuild and verify

From this directory:

```bash
python -B build_report_data.py \
  --release-dir generated-dataset-records/phase5_errors/releases/20260728_phase5bf_error_word_zero_coverage

python -B score_release.py \
  --jsonl ../../generated-dataset-records/phase5_errors/releases/20260728_phase5bf_error_word_zero_coverage/'[FINAL]_PHASE5BF_PARAGRAPH_ERRORS_20260728.jsonl' \
  --out /tmp/songul-final-score.json

python -m pytest -q test_report_scoring.py
```

`build_report_data.py` streams the final JSONL and replaces the embedded data
and provenance blocks in both pages. Density is calculated per **errored
sentence**, not per paragraph record; L1 shares are sentence-weighted. The
오류 어절 axis uses `phase2_pair_key` attribution so Phase 5 surface edits are
compared with NIKL's morpheme-level pairs. The overall score is the unweighted
mean of the eight axes documented on the math tab.

`NIKL_ONLY_ERROR_COMBINATIONS_REPORT.html` and its CSV/append-plan companions
are retained as the historical pre-gap-fill planning snapshot. They are not
the current post-gap-fill coverage report.

The finalized private artifact is at
`generated-dataset-records/phase5_errors/releases/20260728_phase5bf_error_word_zero_coverage/`.
The two public pages are copied to the separate
`SonGul_data_analytics` GitHub/Vercel repository by `publish_to_github.sh`.
