#!/usr/bin/env python3
"""
sss_factor_attribution.py -- per-factor attribution for the sss core equation.

The existing harness (sss_backtest.py) scores the *aggregate* on ~11 market-periods.
That answers "does the score work?" but never "which of the 17 factors carries the
signal?". This pools every stock-period in Results/ into one panel and regresses the
forward-return rank on all 17 core-equation factor ranks at once.

    python sss_factor_attribution.py                       # Tase+Nsr+All, 30d
    python sss_factor_attribution.py --markets Nsr         # tune on one market
    python sss_factor_attribution.py --horizon 180

Design, and why:

  * Ranks, not levels. The factors span 1e-6 to 1e5 and the sentinels are arbitrary
    magnitudes, so a level regression would be a regression on sentinel placement.
    Percentile rank within (market, period) is the only scale the sentinels do not
    dominate -- a sentinel just means "worst", which is what it was meant to mean.

  * Both sides demeaned within (market, period). That is algebraically period fixed
    effects, and it removes any market-wide return in the window. What is left is
    purely cross-sectional: did the cheap names beat the expensive ones that month.

  * SEs clustered by (market, period). Stocks inside one month share a common shock;
    treating 33,000 stock-periods as independent would understate SEs by roughly
    sqrt(cluster size) ~ 30x. The honest n here is the ~35 clusters, not the 33,000 rows.

  * Sign convention. Every coefficient is reported against what the model ASSUMES.
    Numerator factors are "lower is better", so the model predicts a NEGATIVE
    coefficient on their rank. Denominator factors predict POSITIVE. The "agrees"
    column is the only one worth reading first.

KNOWN LIMITATIONS inherited from the snapshot join (all of these flatter the model):
  price returns only, no dividends, no split adjustment, delistings silently dropped.
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

# The 17 factors of the default core equation, as declared in
# sss.get_used_parameters_names_in_core_equation(False).
NUMERATOR = ["eff_dist_from_low_factor", "evr_effective", "pe_effective",
             "effective_ev_to_ebitda", "trailing_12months_price_to_sales", "price_to_book",
             "effective_peg_ratio", "ev_to_cfo_ratio_effective", "debt_to_equity_effective_used"]
DENOMINATOR = ["held_percent_insiders", "effective_profit_margin", "effective_current_ratio",
               "calculated_roa", "calculated_roe", "eqg_factor_effective",
               "rqg_factor_effective", "altman_z_score_factor"]
FACTORS = NUMERATOR + DENOMINATOR

# Snapshots where the trailing-P/E fetch failed almost completely: 94-99% of rows sit
# at the 1e5 sentinel, so pe_effective is a near-constant ~87500 and the column is
# degenerate for that period. Measured, not assumed -- see --keep-pe-outage.
PE_OUTAGE = {("Nsr", "20230411"), ("Nsr", "20230606"), ("All", "20230620")}


# ------------------------------------------------------------------ panel construction
def snapshot_paths(market):
    out = []
    for p in sorted(glob.glob(os.path.join("Results", market, "*", "sss_engine.csv"))):
        m = re.search(r"(\d{8})-(\d{6})", p)
        if m:
            out.append((pd.to_datetime(m.group(1), format="%Y%m%d"), m.group(1), p))
    out.sort(key=lambda t: t[0])
    seen, uniq = set(), []
    for d, s, p in out:
        if d not in seen:
            seen.add(d)
            uniq.append((d, s, p))
    return uniq


def build_pairs(snaps, horizon, tolerance, non_overlapping):
    pairs, next_free = [], None
    for i, (d0, _, _) in enumerate(snaps):
        if non_overlapping and next_free is not None and d0 < next_free:
            continue
        best = None
        for j in range(i + 1, len(snaps)):
            gap = (snaps[j][0] - d0).days
            if abs(gap - horizon) <= tolerance:
                if best is None or abs(gap - horizon) < abs(best[2] - horizon):
                    best = (i, j, gap)
            elif gap > horizon + tolerance:
                break
        if best:
            pairs.append(best)
            next_free = snaps[best[1]][0]
    return pairs


def load(path, columns):
    d = pd.read_csv(path, skiprows=[0], low_memory=False)
    keep = ["Symbol"] + [c for c in columns if c in d.columns]
    d = d[keep].copy()
    for c in keep[1:]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna(subset=["Symbol"]).drop_duplicates("Symbol").set_index("Symbol")


def build_panel(markets, horizon, tolerance, non_overlapping, max_abs_return, drop_pe_outage):
    frames, skipped = [], []
    for mkt in markets:
        snaps = snapshot_paths(mkt)
        if len(snaps) < 2:
            continue
        for i, j, gap in build_pairs(snaps, horizon, tolerance, non_overlapping):
            stamp = snaps[i][1]
            if drop_pe_outage and (mkt, stamp) in PE_OUTAGE:
                skipped.append(mkt + "/" + stamp)
                continue
            a = load(snaps[i][2], FACTORS + ["previous_close"])
            b = load(snaps[j][2], ["previous_close"])
            if [c for c in FACTORS if c not in a.columns]:
                continue
            m = a.join(b[["previous_close"]], how="inner", rsuffix="_fwd")
            m = m[(m.previous_close > 0) & (m.previous_close_fwd > 0)]
            m["fwd"] = m.previous_close_fwd / m.previous_close - 1.0
            m = m[m.fwd.abs() <= max_abs_return]
            m = m.dropna(subset=FACTORS + ["fwd"])
            if len(m) < 50:
                continue
            m["cluster"] = mkt + ":" + stamp
            m["market"] = mkt
            m["days"] = gap
            frames.append(m.reset_index())
    if skipped:
        print("  excluded " + str(len(skipped)) + " PE-outage period(s): " + ", ".join(skipped))
    if not frames:
        sys.exit("No usable periods. Widen --tolerance or check --markets.")
    return pd.concat(frames, ignore_index=True)


# ------------------------------------------------------------------------- econometrics
def cluster_ols(y, X, clusters):
    """OLS with cluster-robust (CR1) covariance. Returns beta, se, t, dof."""
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    u = y - X @ beta

    meat = np.zeros((k, k))
    codes = pd.factorize(clusters)[0]
    G = int(codes.max()) + 1
    for gi in range(G):
        idx = codes == gi
        s = X[idx].T @ u[idx]
        meat += np.outer(s, s)

    c = (G / (G - 1.0)) * ((n - 1.0) / (n - k))
    V = XtX_inv @ meat @ XtX_inv * c
    se = np.sqrt(np.clip(np.diag(V), 0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(se > 0, beta / se, np.nan)
    return beta, se, t, G - 1


def two_sided_p(t, dof):
    """Student-t tail without scipy (scipy is not in requirements.txt)."""
    try:
        from scipy import stats
        return 2 * stats.t.sf(np.abs(t), dof)
    except Exception:
        from math import erfc, sqrt
        return np.array([erfc(abs(v) / sqrt(2)) if np.isfinite(v) else np.nan for v in t])


# ------------------------------------------------------------------------------ reporting
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--markets", nargs="+", default=["Tase", "Nsr", "All"])
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--tolerance", type=int, default=10)
    ap.add_argument("--overlapping", action="store_true",
                    help="allow overlapping windows (more rows, fewer independent clusters)")
    ap.add_argument("--max-abs-return", type=float, default=3.0)
    ap.add_argument("--keep-pe-outage", action="store_true",
                    help="keep the 2023 snapshots where the trailing P/E fetch failed wholesale")
    ap.add_argument("--csv", default="", help="write the coefficient table here")
    a = ap.parse_args()

    print("sss factor attribution")
    print("=" * 78)
    print("markets   : " + ", ".join(a.markets))
    print("horizon   : {} +/- {} days".format(a.horizon, a.tolerance))
    print("overlap   : " + ("ALLOWED" if a.overlapping else "disallowed"))

    panel = build_panel(a.markets, a.horizon, a.tolerance, not a.overlapping,
                        a.max_abs_return, not a.keep_pe_outage)

    n_clusters = panel.cluster.nunique()
    print("periods   : {} (market x date)".format(n_clusters))
    print("rows      : {:,} stock-periods".format(len(panel)))
    print("per period: median {:.0f} names".format(panel.groupby("cluster").size().median()))

    # ---- degenerate-factor guard: a factor with no within-period spread cannot inform
    print("\nfactor health -- share of periods where the factor is effectively constant")
    print("-" * 78)
    dead = {}
    for c in FACTORS:
        dead[c] = panel.groupby("cluster")[c].apply(
            lambda s: float(s.nunique() <= max(2, 0.02 * len(s)))).mean()
    health = pd.Series(dead).sort_values(ascending=False)
    printed = False
    for c, v in health.items():
        if v > 0.0:
            print("  {:36s} {:6.1%}{}".format(c, v, "  <-- DEGENERATE" if v > 0.25 else ""))
            printed = True
    if not printed:
        print("  all 17 factors vary within every period")

    # ---- ranks, demeaned within period (algebraically period fixed effects)
    g = panel.groupby("cluster", observed=True)
    R = pd.DataFrame(index=panel.index)
    for c in FACTORS + ["fwd"]:
        r = g[c].rank(pct=True)
        R[c] = r - r.groupby(panel.cluster.values).transform("mean")

    y = R["fwd"].to_numpy(float)
    X = R[FACTORS].to_numpy(float)
    beta, se, t, dof = cluster_ols(y, X, panel.cluster.values)
    p = two_sided_p(t, dof)

    # ---- univariate rank correlation, for contrast with the multivariate fit
    uni = {}
    for c in FACTORS:
        rows = []
        for _, grp in panel.groupby("cluster"):
            if grp[c].nunique() > 2:
                # Pearson on ranks IS Spearman, and avoids pandas' scipy dependency
                # for method="spearman" -- scipy is not in the repo's requirements.txt.
                rows.append(grp[c].rank().corr(grp.fwd.rank()))
        uni[c] = float(np.nanmean(rows)) if rows else np.nan

    expected = {c: -1.0 for c in NUMERATOR}
    expected.update({c: +1.0 for c in DENOMINATOR})

    out = pd.DataFrame({
        "side": ["num" if c in NUMERATOR else "den" for c in FACTORS],
        "expects": ["neg" if expected[c] < 0 else "pos" for c in FACTORS],
        "beta": beta, "cluster_se": se, "t": t, "p": p,
        "uni_rho": [uni[c] for c in FACTORS],
    }, index=FACTORS)
    out["agrees"] = np.where(np.sign(out.beta) == np.sign([expected[c] for c in FACTORS]),
                             "yes", "NO")

    print("\nPOOLED PANEL REGRESSION -- forward-return rank on 17 factor ranks")
    print("(within-period demeaned; SEs clustered on {} periods, dof={})".format(n_clusters, dof))
    print("-" * 78)
    print(out.reindex(out.t.abs().sort_values(ascending=False).index)
             .to_string(float_format=lambda v: "{:+.4f}".format(v)))

    ss_res = float(((y - X @ beta) ** 2).sum())
    ss_tot = float((y ** 2).sum())
    print("\n  within-period R^2 : {:.5f}".format(1 - ss_res / ss_tot))
    print("  factors agreeing with the model's assumed direction : {}/{}".format(
        int((out.agrees == "yes").sum()), len(out)))
    print("  significant at p<0.05 (clustered)                   : {}/{}".format(
        int((out.p < 0.05).sum()), len(out)))

    print("\n  Read 'agrees' first: NO means the factor points the opposite way to the")
    print("  core equation's assumption. Read 't' second -- with ~{} clusters, |t|<2 is noise.".format(n_clusters))
    print("  An R^2 of this size is normal for one-month cross-sectional return prediction;")
    print("  it is not evidence the model is useful after costs.")

    if a.csv:
        out.to_csv(a.csv)
        print("\n  wrote " + a.csv)
    return out


if __name__ == "__main__":
    main()
