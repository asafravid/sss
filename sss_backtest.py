#!/usr/bin/env python3
"""
sss_backtest.py — evaluate the scanner against forward returns, entirely offline.

The repo contains 160 dated scan snapshots from 2021-06 to 2024-01. Joining a snapshot
at time t to one at t+horizon on Symbol, using previous_close, yields forward returns
with no network access. That turns "is the core equation any good?" into a measurable
question instead of an argument.

    python sss_backtest.py --market Tase
    python sss_backtest.py --market Tase --baselines
    python sss_backtest.py --market Tase --score sss_value_normalized

KNOWN LIMITATIONS, read before trusting any number this prints:

  1. previous_close is a raw price. No dividend adjustment and no split adjustment.
     --max-abs-return crudely drops |return| beyond a threshold to suppress split
     artifacts; that is a filter, not a correction. Numbers are price returns only.
  2. Symbols absent from the later snapshot are dropped, so delistings disappear.
     That is survivorship bias and it flatters the model. --report-attrition shows
     how many names vanish per period so you can size the effect.
  3. Overlapping windows are NOT independent observations. --non-overlapping is the
     default for exactly this reason; the effective sample is small either way.
  4. Any currency-scale problem upstream (pe_effective and P/S show implausible
     magnitudes on TASE) propagates straight into these results.

Nothing here is investment advice or a performance claim. It is a falsification tool.
"""

import argparse
import glob
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

SCORE_COLUMNS = ("sss_value", "sss_value_normalized")

# The six axes the multi-dimensional scan iterates over. Used by the rank-sum baseline,
# which exists to test whether 42875 screening passes beat a six-column average.
SCAN_AXES = [
    ("price_to_book", False),            # (column, higher_is_better)
    ("held_percent_insiders", True),
    ("enterprise_value", True),
    ("pe_effective", False),
    ("evr_effective", False),
    ("effective_profit_margin", True),
]


# --------------------------------------------------------------------------- loading
def snapshot_paths(market, engine="sss_engine.csv"):
    paths = sorted(glob.glob(os.path.join("Results", market, "*", engine)))
    out = []
    for p in paths:
        m = re.search(r"(\d{8})-(\d{6})", p)
        if m:
            out.append((pd.to_datetime(m.group(1), format="%Y%m%d"), p))
    out.sort(key=lambda t: t[0])
    # Some timestamps repeat across folders; keep the first per calendar date.
    seen, uniq = set(), []
    for d, p in out:
        if d not in seen:
            seen.add(d)
            uniq.append((d, p))
    return uniq


def load_snapshot(path, score, extra_columns=()):
    skip = [0] if "normalized" not in os.path.basename(path) else None
    d = pd.read_csv(path, skiprows=skip, low_memory=False)
    wanted = ["Symbol", score, "previous_close"] + [c for c in extra_columns if c in d.columns]
    missing = [c for c in ["Symbol", score, "previous_close"] if c not in d.columns]
    if missing:
        raise KeyError(f"{path}: missing {missing}")
    d = d[wanted].copy()
    for c in wanted:
        if c != "Symbol":
            d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["Symbol", score, "previous_close"])
    return d.drop_duplicates("Symbol").set_index("Symbol")


# ------------------------------------------------------------------------ pair build
def build_pairs(snaps, horizon_days, tolerance, non_overlapping):
    pairs, next_free = [], None
    for i, (d0, p0) in enumerate(snaps):
        if non_overlapping and next_free is not None and d0 < next_free:
            continue
        best = None
        for j in range(i + 1, len(snaps)):
            gap = (snaps[j][0] - d0).days
            if abs(gap - horizon_days) <= tolerance:
                if best is None or abs(gap - horizon_days) < abs(best[2] - horizon_days):
                    best = (i, j, gap)
            elif gap > horizon_days + tolerance:
                break
        if best:
            pairs.append(best)
            next_free = snaps[best[1]][0]
    return pairs


# -------------------------------------------------------------------------- baselines
def add_baselines(m, rng):
    """Attach baseline scores. Convention throughout: LOWER is better, matching sss_value."""
    out = {}
    out["random"] = pd.Series(rng.permutation(len(m)), index=m.index, dtype=float)

    have = [(c, hib) for c, hib in SCAN_AXES if c in m.columns and m[c].notna().sum() > len(m) * 0.5]
    if have:
        ranks = []
        for c, higher_is_better in have:
            r = m[c].rank(pct=True, na_option="keep")
            ranks.append(1.0 - r if higher_is_better else r)  # low = good
        out["rank_sum_6axis"] = pd.concat(ranks, axis=1).mean(axis=1)
        out["_rank_sum_axes"] = [c for c, _ in have]
    return out


# ------------------------------------------------------------------------- evaluation
def evaluate(market, score, horizon, tolerance, non_overlapping, max_abs_return,
             quantile, baselines, report_attrition, seed):
    engine = "sss_engine_normalized.csv" if score == "sss_value_normalized" else "sss_engine.csv"
    snaps = snapshot_paths(market, engine)
    if len(snaps) < 2:
        sys.exit(f"Not enough snapshots for market '{market}' with {engine} "
                 f"(found {len(snaps)}). For sss_value_normalized you must run "
                 f"postprocess_only.py over the snapshots first.")

    extra = [c for c, _ in SCAN_AXES] if baselines else ()
    pairs = build_pairs(snaps, horizon, tolerance, non_overlapping)

    print(f"market            : {market}")
    print(f"score             : {score}  (lower is better)")
    print(f"snapshots         : {len(snaps)}  ({snaps[0][0]:%Y-%m-%d} .. {snaps[-1][0]:%Y-%m-%d})")
    print(f"horizon           : {horizon} +/- {tolerance} days")
    print(f"window overlap    : {'disallowed' if non_overlapping else 'ALLOWED (rho values are not independent)'}")
    print(f"usable periods    : {len(pairs)}")
    if not pairs:
        sys.exit("No usable snapshot pairs. Widen --tolerance or allow overlap.")

    rng = np.random.default_rng(seed)
    rows, per_period_baseline = [], {}

    for i, j, gap in pairs:
        try:
            a = load_snapshot(snaps[i][1], score, extra)
            b = load_snapshot(snaps[j][1], score)
        except Exception as e:
            print(f"  skipped {snaps[i][0]:%Y-%m-%d}: {e}")
            continue

        n_start = len(a)
        m = a.join(b[["previous_close"]], how="inner", rsuffix="_fwd")
        attrition = n_start - len(m)
        m = m[(m.previous_close > 0) & (m.previous_close_fwd > 0)]
        m = m[(m[score] > 0) & (m[score] < 1e12)]
        m["fwd"] = m.previous_close_fwd / m.previous_close - 1.0
        m = m[m.fwd.abs() <= max_abs_return]
        if len(m) < 30:
            continue

        k = max(10, int(len(m) * quantile))
        sel = m.nsmallest(k, score)
        rest = m.drop(sel.index)

        row = {
            "from": snaps[i][0].date(), "to": snaps[j][0].date(), "days": gap,
            "n": len(m), "dropped": attrition,
            "rho": m[score].rank().corr(m.fwd.rank(), method="spearman"),
            "sel_med": sel.fwd.median(), "rest_med": rest.fwd.median(),
            "universe_med": m.fwd.median(),
        }
        row["excess"] = row["sel_med"] - row["universe_med"]
        rows.append(row)

        if baselines:
            bl = add_baselines(m, rng)
            per_period_baseline.setdefault("_axes", bl.get("_rank_sum_axes"))
            for name, series in bl.items():
                if name.startswith("_"):
                    continue
                ksel = m.loc[series.nsmallest(k).index]
                per_period_baseline.setdefault(name, []).append({
                    "rho": series.rank().corr(m.fwd.rank(), method="spearman"),
                    "excess": ksel.fwd.median() - m.fwd.median(),
                })

    if not rows:
        sys.exit("No period produced enough overlapping symbols to evaluate.")

    r = pd.DataFrame(rows)
    print()
    show = r[["from", "to", "days", "n", "dropped", "rho", "sel_med", "rest_med", "universe_med", "excess"]] \
        if report_attrition else r[["from", "to", "days", "n", "rho", "sel_med", "universe_med", "excess"]]
    print(show.to_string(index=False, float_format=lambda x: f"{x:+.4f}"))

    print("\n" + "=" * 74)
    print("RESULT")
    print("=" * 74)
    mean_rho = r.rho.mean()
    print(f"  mean Spearman(score rank, forward return rank) : {mean_rho:+.4f}")
    print(f"    lower score = better, so the model works only if this is NEGATIVE")
    print(f"  periods with negative rho (model directionally right) : {(r.rho < 0).sum()}/{len(r)}")
    print(f"  mean excess median return of top {quantile:.0%} vs universe : {r.excess.mean():+.4f}")
    print(f"  periods with positive excess : {(r.excess > 0).sum()}/{len(r)}")

    # A sign test is about the weakest defensible statistic here, which is the point:
    # with a handful of non-overlapping periods, nothing stronger is warranted.
    n_pos = int((r.excess > 0).sum())
    n = len(r)
    try:
        from scipy import stats
        p = stats.binomtest(n_pos, n, 0.5).pvalue
        print(f"  sign test on excess (H0: coin flip) : p = {p:.3f}"
              f"{'  -- not significant' if p > 0.05 else ''}")
    except Exception:
        pass
    print(f"\n  n = {n} periods. Treat this as a smoke test of direction, not a performance estimate.")
    print(f"  Price returns only: no dividends, no split adjustment, delistings dropped.")

    if baselines and per_period_baseline:
        print("\n" + "=" * 74)
        print("BASELINE COMPARISON — does the model beat trivial alternatives?")
        print("=" * 74)
        axes = per_period_baseline.get("_axes")
        comp = [{"model": score, "mean_rho": mean_rho, "mean_excess": r.excess.mean(),
                 "periods_positive_excess": f"{(r.excess > 0).sum()}/{len(r)}"}]
        for name, recs in per_period_baseline.items():
            if name.startswith("_"):
                continue
            b = pd.DataFrame(recs)
            comp.append({"model": name, "mean_rho": b.rho.mean(), "mean_excess": b.excess.mean(),
                         "periods_positive_excess": f"{(b.excess > 0).sum()}/{len(b)}"})
        print(pd.DataFrame(comp).to_string(index=False, float_format=lambda x: f"{x:+.4f}"))
        if axes:
            print(f"\n  rank_sum_6axis = unweighted mean percentile rank over: {', '.join(axes)}")
            print("  These are the same six columns the multi-dimensional scan iterates over.")
            print("  If it matches or beats the core equation, the 17-factor product is not")
            print("  earning its complexity, and the scan is approximating a six-line function.")
        print("\n  'random' is the floor. Any model that does not clearly beat it is noise.")

    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--market", default="Tase", help="Results/<market>/ — Tase, Nsr, All, Six, St, Custom")
    ap.add_argument("--score", default="sss_value", choices=list(SCORE_COLUMNS))
    ap.add_argument("--horizon", type=int, default=180, help="forward horizon in days")
    ap.add_argument("--tolerance", type=int, default=30, help="acceptable deviation from horizon")
    ap.add_argument("--overlapping", action="store_true",
                    help="allow overlapping windows (inflates apparent n; off by default)")
    ap.add_argument("--max-abs-return", type=float, default=3.0,
                    help="drop |return| above this as a likely split artifact")
    ap.add_argument("--quantile", type=float, default=0.2, help="top fraction treated as the selection")
    ap.add_argument("--baselines", action="store_true",
                    help="also score a random ranking and a 6-axis rank-sum")
    ap.add_argument("--report-attrition", action="store_true",
                    help="show how many symbols vanish between snapshots (survivorship)")
    ap.add_argument("--seed", type=int, default=20260912)
    args = ap.parse_args()

    evaluate(args.market, args.score, args.horizon, args.tolerance,
             not args.overlapping, args.max_abs_return, args.quantile,
             args.baselines, args.report_attrition, args.seed)


if __name__ == "__main__":
    main()
