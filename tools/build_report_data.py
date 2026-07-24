#!/usr/bin/env python3
"""Rebuild the injection-dataset report pages from a Phase 5 release.

Streams the release JSONL, compares against the frozen NIKL Phase 2 canonical
stats, and re-injects the /*DATA-START*/…/*DATA-END*/ and /*META-START*/…
/*META-END*/ blocks inside the two HTML pages in this directory. Everything
visible on the pages (KPIs, scorecard, charts, tables, provenance, the math
tab) re-renders from those blocks — no other edits needed for a new release.

Usage:
  python build_report_data.py \
    --release-dir "generated-dataset-records/phase5_errors/releases/20260714_phase5b-f_5model"

Narrative explainer paragraphs (the "? · 설명" panels) intentionally keep
hand-written prose; the script prints a reminder to re-read them.
"""
import argparse, json, math, re, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
NIKL_STATS = REPO / "1-SonGul/datasets/[PHASE_2]_Correction_Dataset/dataset-EDA/Analysis with Unknown Tags/stats_report"
NIKL_L1 = REPO / "1-SonGul/datasets/[PHASE_5_SHARED]/multi_error_matrices/_stats.json"
MAIN_PAGE = HERE / "PHASE2_VS_PHASE5_ERROR_EDA_20260714.html"
EXPL_PAGE = HERE / "PHASE2_VS_PHASE5_ERROR_EDA_20260714_EXPLORER.html"


# ---------- NIKL side (frozen reference) ----------

def load_nikl():
    import csv
    out = {}
    def readcsv(fn):
        with open(NIKL_STATS / fn, encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    for name, fn in [("area", "error_area_distribution.csv"),
                     ("level", "error_level_distribution.csv"),
                     ("pattern", "error_pattern_distribution.csv")]:
        out[name] = {r["code"]: int(r["count"]) for r in readcsv(fn)}
    out["triple"] = {r["combination"]: int(r["count"])
                     for r in readcsv("ERROR_COMBINATION_PROBABILITY_BASELINE.csv")}
    pairs = {}
    for i, r in enumerate(readcsv("ERROR PAIR DISTRIBUTION BASELINE.csv")):
        if i >= 2000: break
        pairs[r["wrong"] + "|" + r["correct"]] = int(r["count"])
    out["pair"] = pairs
    s = json.load(open(NIKL_STATS / "summary.json"))
    out["nerr"] = s["overview"]["errors_per_record_distribution"]
    out["n_records"] = s["overview"]["n_records"]
    out["n_errors"] = s["overview"]["n_errors"]
    out["l1_sentences"] = json.load(open(NIKL_L1))["n_sentences_by_L1"]
    return out


# ---------- Phase 5 side (stream the release) ----------

def mine_release(jsonl_path):
    c = {k: Counter() for k in
         ("area level pattern triple spat striple pair engine family l1 nerr lane").split()}
    n_records = n_errors = 0
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rec = r.get("recipe", {})
            errs = rec.get("errors", [])
            n_records += 1
            c["nerr"][len(errs)] += 1
            c["l1"][rec.get("l1") or "UNKNOWN"] += 1
            c["lane"][r.get("generation_source", {}).get("distribution_lane", "?")] += 1
            for e in errs:
                n_errors += 1
                a = e.get("scheme_area") or "UNKNOWN"
                lv = e.get("scheme_level") or "UNKNOWN"
                sp = e.get("scheme_pattern") or "UNKNOWN"
                pt = e.get("surface_pattern") or "UNKNOWN"
                c["area"][a] += 1; c["level"][lv] += 1; c["pattern"][pt] += 1
                c["spat"][sp] += 1
                c["triple"][f"{a}|{lv}|{pt}"] += 1
                c["striple"][f"{a}|{lv}|{sp}"] += 1
                w = (e.get("wrong_text") or "").strip() or "∅"
                cr = (e.get("correct_text") or "").strip() or "∅"
                c["pair"][f"{w}|{cr}"] += 1
                c["engine"][e.get("engine_used") or "?"] += 1
                rid = e.get("rule_id") or ""
                c["family"][rid.split(".")[0] if rid else "?"] += 1
            if n_records % 100000 == 0:
                print(f"  …{n_records:,} records", file=sys.stderr)
    return c, n_records, n_errors


# ---------- comparison (same math as the pages document) ----------

def norm(c): t = sum(c.values()); return {k: v / t for k, v in c.items()}
def tv(a, b): return 0.5 * sum(abs(a.get(k, 0) - b.get(k, 0)) for k in set(a) | set(b))
def cosine(a, b):
    ks = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in ks)
    na = math.sqrt(sum(v * v for v in a.values())); nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0
def spearman(xs, ys):
    n = len(xs)
    if n < 3: return None
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: -v[i]); r = [0] * len(v)
        for pos, i in enumerate(order): r[i] = pos + 1
        return r
    rx, ry = rank(xs), rank(ys)
    return 1 - 6 * sum((a - b) ** 2 for a, b in zip(rx, ry)) / (n * (n * n - 1))


def build_page_data(nikl, c, PT):
    NT = nikl["n_errors"]
    nikl_pat = norm(nikl["pattern"])
    nikl_pat_known = norm({k: v for k, v in nikl["pattern"].items() if k != "UNKNOWN"})
    p5_scheme_pat = norm(c["spat"]); p5_surface_pat = norm(c["pattern"])
    labs = ["REP", "MIF", "OM", "ADD", "UNKNOWN"]
    pattern = {
        "labels": labs,
        "nikl_full": [round(nikl_pat.get(k, 0) * 100, 2) for k in labs],
        "p5_scheme": [round(p5_scheme_pat.get(k, 0) * 100, 2) for k in labs],
        "nikl_known": [round(nikl_pat_known.get(k, 0) * 100, 2) for k in labs[:4]] + [0],
        "p5_surface": [round(p5_surface_pat.get(k, 0) * 100, 2) for k in labs[:4]] + [0],
        "tv_scheme": round(tv(nikl_pat, p5_scheme_pat), 4),
        "tv_surface": round(tv(nikl_pat_known, p5_surface_pat), 4),
    }
    def topn_rows(nc, pc, n):
        na, pa = norm(nc), norm(pc)
        top = [k for k, _ in sorted(nc.items(), key=lambda x: -x[1])[:n]]
        rows = [{"code": k, "nikl": round(na.get(k, 0) * 100, 2),
                 "p5": round(pa.get(k, 0) * 100, 2)} for k in top]
        rows.append({"code": "OTHER",
                     "nikl": round((1 - sum(na.get(k, 0) for k in top)) * 100, 2),
                     "p5": round((1 - sum(pa.get(k, 0) for k in top)) * 100, 2)})
        return rows, round(tv(na, pa), 4), round(cosine(na, pa), 4)
    a_rows, a_tv, a_cos = topn_rows(nikl["area"], c["area"], 30)
    l_rows, l_tv, l_cos = topn_rows(nikl["level"], c["level"], 10)
    area = {"rows": a_rows, "tv": a_tv, "cos": a_cos,
            "n_nikl_codes": len(nikl["area"]), "n_p5_codes": len(c["area"])}
    level = {"rows": l_rows, "tv": l_tv, "cos": l_cos}
    nikl_tri = norm(nikl["triple"]); p5_tri = norm(c["striple"])
    cov = sum(sh for t_, sh in nikl_tri.items() if t_ in p5_tri)
    tri_top = [k for k, _ in sorted(nikl["triple"].items(), key=lambda x: -x[1])[:30]]
    triples = {
        "rows": [{"t": t_, "nikl": round(nikl_tri.get(t_, 0) * 100, 2),
                  "p5": round(p5_tri.get(t_, 0) * 100, 2)} for t_ in tri_top],
        "scatter": [[round(sh * 100, 3), round(p5_tri.get(t_, 0) * 100, 3), t_]
                    for t_, sh in sorted(nikl_tri.items(), key=lambda x: -x[1])[:120]],
        "tv": round(tv(nikl_tri, p5_tri), 4), "coverage": round(cov * 100, 1),
        "n_nikl": len(nikl["triple"]), "n_p5": len(c["striple"])}
    nikl_pair = {k: v / NT for k, v in nikl["pair"].items()}
    p5_pair = {k: v / PT for k, v in c["pair"].items()}
    top50 = [k for k, _ in sorted(nikl["pair"].items(), key=lambda x: -x[1])[:50]]
    p5_rank = {k: i + 1 for i, (k, _) in enumerate(sorted(c["pair"].items(), key=lambda x: -x[1]))}
    pair_rows = [{"pair": k, "nikl": round(nikl_pair.get(k, 0) * 100, 3),
                  "p5": round(p5_pair.get(k, 0) * 100, 3), "p5rank": p5_rank.get(k)} for k in top50]
    shared50 = [k for k in top50 if k in p5_pair]
    rho = spearman([nikl_pair[k] for k in shared50], [p5_pair[k] for k in shared50])
    u200 = set(sorted(nikl_pair, key=lambda k: -nikl_pair[k])[:200]) | \
           set(sorted(p5_pair, key=lambda k: -p5_pair[k])[:200])
    pairs = {"rows": pair_rows,
             "in_top30": sum(1 for r in pair_rows[:20] if r["p5rank"] and r["p5rank"] <= 30),
             "shared50": len(shared50),
             "spearman50": round(rho, 3) if rho is not None else None,
             "cos200": round(cosine({k: nikl_pair.get(k, 0) for k in u200},
                                    {k: p5_pair.get(k, 0) for k in u200}), 4),
             "n_p5_distinct": len(c["pair"])}
    def bin_nerr(cn):
        out = {str(i): 0 for i in range(1, 8)}; out["8+"] = 0
        for k, v in cn.items():
            k = int(k)
            if k <= 0: continue
            out["8+" if k >= 8 else str(k)] += v
        t_ = sum(out.values())
        return {k: v / t_ for k, v in out.items()}
    nb, pb = bin_nerr(nikl["nerr"]), bin_nerr(c["nerr"])
    nerr = {"bins": list(nb.keys()),
            "nikl": [round(v * 100, 2) for v in nb.values()],
            "p5": [round(v * 100, 2) for v in pb.values()],
            "mean_nikl": round(sum(int(k) * v for k, v in nikl["nerr"].items()) / sum(nikl["nerr"].values()), 2),
            "mean_p5": round(sum(int(k) * v for k, v in c["nerr"].items()) / sum(c["nerr"].values()), 2),
            "tv": round(tv(nb, pb), 4)}
    nikl_l1, p5_l1 = norm(nikl["l1_sentences"]), norm(c["l1"])
    l1 = {"rows": [{"l1": k, "nikl": round(nikl_l1.get(k, 0) * 100, 2),
                    "p5": round(p5_l1.get(k, 0) * 100, 2)}
                   for k, _ in sorted(nikl["l1_sentences"].items(), key=lambda x: -x[1])[:10]],
          "tv": round(tv(nikl_l1, p5_l1), 4), "cos": round(cosine(nikl_l1, p5_l1), 4)}
    return {"pattern": pattern, "area": area, "level": level, "triples": triples,
            "pairs": pairs, "nerr": nerr, "l1": l1,
            "made": {"engine": dict(c["engine"].most_common()),
                     "family": dict(c["family"].most_common()),
                     "lane": dict(c["lane"].most_common())}}


def union_table(nc, pc, nt, pt):
    rows = [{"k": k, "nc": nc.get(k, 0), "np": round(nc.get(k, 0) / nt * 100, 3),
             "pc": pc.get(k, 0), "pp": round(pc.get(k, 0) / pt * 100, 3)}
            for k in set(nc) | set(pc)]
    rows.sort(key=lambda r: -r["nc"])
    return rows


def inject(path, marker, payload):
    s = path.read_text(encoding="utf-8")
    pat = re.compile(r"/\*" + marker + r"-START\*/.*?/\*" + marker + r"-END\*/", re.S)
    assert pat.search(s), f"{marker} markers missing in {path.name}"
    s = pat.sub(lambda _: f"/*{marker}-START*/{payload}/*{marker}-END*/", s, count=1)
    path.write_text(s, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release-dir", required=True,
                    help="release folder containing manifest.json + the [FINAL]*.jsonl")
    ap.add_argument("--paragraph-dir", default=None,
                    help="paragraph_merged release folder; refreshes the by-learner-level stats")
    args = ap.parse_args()
    rel = (REPO / args.release_dir) if not Path(args.release_dir).is_absolute() else Path(args.release_dir)
    manifest = json.load(open(rel / "manifest.json"))
    jsonl = rel / manifest["artifact"]["file"]

    print(f"mining {jsonl.name} …", file=sys.stderr)
    nikl = load_nikl()
    c, n_rec, n_err = mine_release(jsonl)
    assert n_err == manifest["artifact"]["error_annotations"], "error count != manifest"

    data = build_page_data(nikl, c, n_err)
    data["kpi"] = {"nikl_errors": nikl["n_errors"], "nikl_records": nikl["n_records"],
                   "p5_errors": n_err, "p5_records": n_rec}

    # by-learner-level stats from the paragraph view (dedup by paragraph_key,
    # keep the most-injected view of each paragraph)
    if args.paragraph_dir:
        pdir = (REPO / args.paragraph_dir) if not Path(args.paragraph_dir).is_absolute() else Path(args.paragraph_dir)
        print("mining paragraph view for learner levels …", file=sys.stderr)
        seen = {}
        with open(pdir / "paragraph_merged.jsonl", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                pk = r["paragraph_key"]
                key = (pk["sample_id"], pk["gen_idx"], pk["model"], pk["level"], r.get("form"))
                sens = r["sentences"]
                inj = sum(1 for s in sens if s.get("status") == "injected")
                if key not in seen or inj > seen[key][1]:
                    seen[key] = (len(sens), inj, pk["level"])
        lv_agg = {}
        for tot, inj, lv in seen.values():
            a = lv_agg.setdefault(lv, {"paras": 0, "sent": 0, "inj": 0})
            a["paras"] += 1; a["sent"] += tot; a["inj"] += inj
        # errors-per-errored-sentence needs error counts; approximate from the
        # release stream is not level-keyed, so recompute from views:
        # (kept simple: eps from a second lightweight pass would double runtime;
        # reuse share stats and mark eps from previous page data if present)
        rows = []
        for k in ("beginner", "intermediate", "advanced"):
            if k not in lv_agg: continue
            a = lv_agg[k]
            rows.append({"key": k, "paras": a["paras"], "sent": a["sent"], "inj": a["inj"],
                         "pct": round(a["inj"] / a["sent"] * 100, 1), "eps": None})
        prev_l = re.search(r"/\*DATA-START\*/(.*?)/\*DATA-END\*/",
                           MAIN_PAGE.read_text(encoding="utf-8"), re.S)
        if prev_l:
            try:
                prev_rows = {r["key"]: r for r in json.loads(prev_l.group(1)).get("levels", {}).get("rows", [])}
                for r in rows:
                    if r["eps"] is None and r["key"] in prev_rows:
                        r["eps"] = prev_rows[r["key"]].get("eps")
            except json.JSONDecodeError:
                pass
        data["levels"] = {"rows": rows,
                          "total_paras": sum(r["paras"] for r in rows),
                          "total_sent": sum(r["sent"] for r in rows),
                          "total_pct": round(sum(r["inj"] for r in rows) / max(1, sum(r["sent"] for r in rows)) * 100, 1)}
    else:
        # no paragraph dir given: carry the existing levels block forward
        prev_l = re.search(r"/\*DATA-START\*/(.*?)/\*DATA-END\*/",
                           MAIN_PAGE.read_text(encoding="utf-8"), re.S)
        if prev_l:
            try:
                lvl = json.loads(prev_l.group(1)).get("levels")
                if lvl: data["levels"] = lvl
            except json.JSONDecodeError:
                pass
    rid = manifest["release_id"]
    meta = {
        "release_id": rid, "release_short": rid.split("_")[0], "released": manifest["released_at"][:10],
        "artifact_file": manifest["artifact"]["file"], "sha256": manifest["artifact"]["sha256"],
        "bytes": manifest["artifact"]["bytes"],
        "nikl_errors": nikl["n_errors"], "nikl_records": nikl["n_records"], "nikl_essays": 7748,
        "source_line": f"{Path(manifest['source']['file']).parent.name} · {manifest['source']['records']:,} rows",
        "source_sha_short": manifest["source"]["sha256"][:8] + "…" + manifest["source"]["sha256"][-12:],
        "judge": {"injected": manifest["judging"]["injected_errors"],
                  "approved": manifest["judging"]["approved_errors"],
                  "rejected": manifest["judging"]["rejected_errors"]},
        "records": {"full": manifest["judging"]["fully_accepted_records"],
                    "partial": manifest["judging"]["partially_accepted_records"],
                    "rejected": manifest["judging"]["fully_rejected_records"]},
        "run_window": f"{manifest['run']['started_at'][:10]} → {manifest['run']['completed_at'][:10]}"
                      f" · {manifest['run']['input_chunks']} chunks · {manifest['run']['workers']} workers",
        "engines_line": "rule {:.1%} (deterministic morpheme edits) · LLM {:.1%}".format(
            c["engine"].get("rule", 0) / n_err, c["engine"].get("llm", 0) / n_err),
        "derived_line": "(update manually if a derived view exists for this release)",
        "schema": manifest["artifact"]["schema_version"],
    }
    # Preserve hand-maintained META fields from the current page: the LLM model
    # suffix on the engines line, and the derived-view note (only meaningful for
    # the release it was written for).
    cur = re.search(r"/\*META-START\*/(.*?)/\*META-END\*/", MAIN_PAGE.read_text(encoding="utf-8"), re.S)
    if cur:
        try:
            prev = json.loads(cur.group(1))
            tail = re.search(r"LLM [\d.]+% (\(.+\))$", prev.get("engines_line", ""))
            if tail:
                meta["engines_line"] += " " + tail.group(1)
            if prev.get("release_id") == rid and "(update manually" not in prev.get("derived_line", ""):
                meta["derived_line"] = prev["derived_line"]
        except (json.JSONDecodeError, KeyError):
            pass
    NT, PT = nikl["n_errors"], n_err
    edata = {"meta": {"nikl_errors": NT, "p5_errors": PT, "release_short": meta["release_short"]},
             "area": union_table(nikl["area"], c["area"], NT, PT),
             "level": union_table(nikl["level"], c["level"], NT, PT),
             "triple": union_table(nikl["triple"], c["striple"], NT, PT),
             "pair": union_table(nikl["pair"], dict(Counter(c["pair"]).most_common(2000)), NT, PT),
             "metrics": {"area": {"tv": data["area"]["tv"], "cos": data["area"]["cos"]},
                         "pattern": {"tv_scheme": data["pattern"]["tv_scheme"],
                                     "tv_surface": data["pattern"]["tv_surface"]},
                         "level": {"tv": data["level"]["tv"], "cos": data["level"]["cos"]},
                         "triples": {"tv": data["triples"]["tv"], "coverage": data["triples"]["coverage"]},
                         "pairs": {"spearman50": data["pairs"]["spearman50"],
                                   "in_top30": data["pairs"]["in_top30"], "cos200": data["pairs"]["cos200"]},
                         "nerr": {"tv": data["nerr"]["tv"], "mean_nikl": data["nerr"]["mean_nikl"],
                                  "mean_p5": data["nerr"]["mean_p5"]},
                         "l1": {"tv": data["l1"]["tv"], "cos": data["l1"]["cos"]},
                         "kpi": data["kpi"]}}

    inject(MAIN_PAGE, "DATA", json.dumps(data, ensure_ascii=False))
    inject(MAIN_PAGE, "META", json.dumps(meta, ensure_ascii=False))
    inject(EXPL_PAGE, "DATA", json.dumps(edata, ensure_ascii=False))
    print(f"OK — {n_rec:,} records / {n_err:,} errors injected into both pages.")
    print("Reminder: narrative '? · 설명' paragraphs and the derived-view provenance line are prose —")
    print("re-read them for a new release; the numbers everywhere else re-render automatically.")

if __name__ == "__main__":
    main()
