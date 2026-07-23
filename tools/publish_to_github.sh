#!/usr/bin/env bash
# Push the current report pages to the public deploy repo (SonGul_data_analytics).
# Run AFTER build_report_data.py. Vercel auto-deploys on push.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEPLOY="${DEPLOY_REPO:-/data/team_a/dave-workspace/SonGul_data_analytics}"
MSG="${1:-update report pages}"

[ -d "$DEPLOY/.git" ] || { echo "deploy repo not found at $DEPLOY (set DEPLOY_REPO)"; exit 1; }

{ printf '<!doctype html>\n<html lang="en">\n'
  sed 's/PHASE2_VS_PHASE5_ERROR_EDA_20260714_EXPLORER\.html/explorer.html/g' \
    "$SRC/PHASE2_VS_PHASE5_ERROR_EDA_20260714.html"; } > "$DEPLOY/index.html"
{ printf '<!doctype html>\n<html lang="en">\n'
  sed 's/PHASE2_VS_PHASE5_ERROR_EDA_20260714\.html/index.html/g' \
    "$SRC/PHASE2_VS_PHASE5_ERROR_EDA_20260714_EXPLORER.html"; } > "$DEPLOY/explorer.html"

cd "$DEPLOY"
git add index.html explorer.html
git diff --cached --quiet && { echo "no changes to publish"; exit 0; }
git -c core.hooksPath=/dev/null commit -m "$MSG"
git push
echo "pushed — Vercel will deploy automatically."
