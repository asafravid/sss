#!/usr/bin/env python3
"""
sss_scan_vs_ranksum.py -- is the multi-dimensional scan worth 42,875 screening passes?

HANDOFF.md 4(d): the six scan axes are already six of the seventeen core-equation
factors, so the scan re-weights variables the score has already used. This compares
the scan's output (Grade, in results_sss.csv) against a six-line alternative: the
unweighted mean percentile rank of those same six columns, taken straight from the
sibling sss_engine.csv.

If rho is high, the scan is an expensive approximation of an average.

    python sss_scan_vs_ranksum.py
    python sss_scan_vs_ranksum.py --markets Tase --variant results_sss_normalized.csv
"""

import argparse
import glob
import os
import re
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

# (column, higher_is_better) -- the six axes sss_run.py iterates over via get_range()
SCAN_AXES = [
    ("price_to_book", False),
    ("held_percent_insiders", True),
    ("enterprise_value", True),
    ("pe_effective", False),
    ("evr_effective", False),
    ("effective_profit_margin", True),
]


def rank_sum(engine, axes):
    """Unweighted mean percentile rank over the six axes. Higher = better, to match Grade."""
    parts = []
    used = []
    for col, higher_is_better in axes:
        if col not in engine.columns:
            continue
        s = pd.to_numeric(engine[col], errors="coerce")
        if s.notna().sum() < 0.5 * len(s) or s.nunique() < 3:
            continue
        r = s.rank(pct=True)
        parts.append(r if higher_is_better else 1.0 - r)
        used.append(col)
    if not parts:
        return None, []
    return pd.concat(parts, axis=1).mean(axis=1), used


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--markets", nargs="+", default=["Tase", "Nsr", "All"])
    ap.add_argument("--variant", default="results_sss.csv",
                    choices=["results_sss.csv", "results_sss_normalized.csv"])
    ap.add_argument("--min-names", type=int, default=30)
    a = ap.parse_args()

    print("scan Grade vs unweighted 6-axis rank sum")
    print("=" * 74)
    print("variant : " + a.variant)

    rows = []
    for mkt in a.markets:
        for res in sorted(glob.glob(os.path.join("Results", mkt, "*", a.variant))):
            folder = os.path.dirname(res)
            eng = os.path.join(folder, "sss_engine.csv")
            if not os.path.exists(eng):
                continue
            try:
                g = pd.read_csv(res, low_memory=False)
                e = pd.read_csv(eng, skiprows=[0], low_memory=False)
            except Exception:
                continue
            if "Grade" not in g.columns or "Symbol" not in g.columns:
                continue
            g = g[["Symbol", "Grade"]].dropna().drop_duplicates("Symbol").set_index("Symbol")
            g["Grade"] = pd.to_numeric(g["Grade"], errors="coerce")

            e = e.dropna(subset=["Symbol"]).drop_duplicates("Symbol").set_index("Symbol")
            rs, used = rank_sum(e, SCAN_AXES)
            if rs is None:
                continue
            e = e.assign(_rs=rs)

            m = g.join(e[["_rs"]], how="inner").dropna()
            if len(m) < a.min_names:
                continue

            rho = m.Grade.rank().corr(m._rs.rank())
            # how much of the scan's ordering survives if you only keep the top decile
            k = max(5, int(0.1 * len(m)))
            top_scan = set(m.nlargest(k, "Grade").index)
            top_rs = set(m.nlargest(k, "_rs").index)
            rows.append({
                "market": mkt,
                "date": re.search(r"(\d{8})-", res).group(1),
                "n": len(m),
                "rho": rho,
                "top10_overlap": len(top_scan & top_rs) / k,
                "axes_used": len(used),
            })

    if not rows:
        print("\n  no folder had both a Grade file and a usable sss_engine.csv")
        return

    t = pd.DataFrame(rows)
    print("periods : {}".format(len(t)))
    print("\nper market")
    print("-" * 74)
    summ = t.groupby("market").agg(
        periods=("rho", "size"), median_n=("n", "median"),
        mean_rho=("rho", "mean"), median_rho=("rho", "median"),
        min_rho=("rho", "min"), max_rho=("rho", "max"),
        mean_top10_overlap=("top10_overlap", "mean"))
    print(summ.to_string(float_format=lambda v: "{:+.4f}".format(v)))

    print("\npooled")
    print("-" * 74)
    print("  mean   Spearman(Grade, 6-axis rank sum) : {:+.4f}".format(t.rho.mean()))
    print("  median Spearman                         : {:+.4f}".format(t.rho.median()))
    print("  periods with rho > 0.90                 : {}/{}".format(int((t.rho > 0.90).sum()), len(t)))
    print("  periods with rho > 0.80                 : {}/{}".format(int((t.rho > 0.80).sum()), len(t)))
    print("  mean top-decile overlap                 : {:.1%}".format(t.top10_overlap.mean()))
    print("\n  HANDOFF 4(d) threshold: rho > 0.9 means the scan grid approximates a")
    print("  six-line function. Top-decile overlap is the practical version of the same")
    print("  question -- it is the fraction of actual recommendations you would still get.")


if __name__ == "__main__":
    main()
