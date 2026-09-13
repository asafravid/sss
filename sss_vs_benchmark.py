#!/usr/bin/env python3
"""Does an sss top-N basket beat simply owning an index ETF?

Every backtest in this project so far is CROSS-SECTIONAL: it asks whether the names
sss ranks highly beat the other names in the same scan, with the period mean removed.
That question is silent on the one an investor actually cares about -- whether the
whole exercise beats buying QQQ.

This holds the top N names by Grade for each period's window and compares the
equal-weighted total return against a benchmark over the exact same dates.
Benchmarks are matched by currency: US markets against QQQ/SPY/IWM, TASE against
TA35.TA (shekel-denominated, so no FX confound).

    python sss_vs_benchmark.py --top 10
"""
import argparse
import glob
import os
import re
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

PRICE_CACHE = os.path.join("price_cache", "adjusted_close.pkl")
BENCH_CACHE = os.path.join("price_cache", "benchmarks.pkl")
BENCH = {"Nsr": ["QQQ", "SPY", "IWM"], "All": ["QQQ", "SPY", "IWM"], "Tase": ["TA35.TA", "EIS"]}


def load_benchmarks(start, end):
    if os.path.exists(BENCH_CACHE):
        return pd.read_pickle(BENCH_CACHE)
    tick = sorted({t for v in BENCH.values() for t in v})
    df = yf.download(tick, start=start, end=end, auto_adjust=True, progress=False,
                     threads=False, group_by="column")
    if isinstance(df.columns, pd.MultiIndex):
        df = df["Close"]
    df.index = pd.to_datetime(df.index)
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)
    df.to_pickle(BENCH_CACHE)
    return df


def folders(market):
    out = []
    for res in sorted(glob.glob(os.path.join("Results", market, "*", "results_sss.csv"))):
        f = os.path.dirname(res)
        m = re.search(r"(\d{8})-", f)
        if m and os.path.exists(os.path.join(f, "sss_engine.csv")):
            out.append((pd.to_datetime(m.group(1), format="%Y%m%d"), res))
    out.sort()
    seen, uniq = set(), []
    for d, r in out:
        if d not in seen:
            seen.add(d); uniq.append((d, r))
    return uniq


def ret(series, d0, d1):
    """Total return between the last quote on/before d0 and on/before d1."""
    s = series.dropna()
    a, b = s.loc[:d0], s.loc[:d1]
    if a.empty or b.empty:
        return np.nan
    p0, p1 = a.iloc[-1], b.iloc[-1]
    if not (p0 > 0 and p1 > 0) or a.index[-1] == b.index[-1]:
        return np.nan
    return p1 / p0 - 1.0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--markets", nargs="+", default=["Tase", "Nsr", "All"])
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--tolerance", type=int, default=10)
    a = ap.parse_args()

    px = pd.read_pickle(PRICE_CACHE)
    px.index = pd.to_datetime(px.index)
    bm = load_benchmarks("2021-05-01", "2024-03-01")

    print("sss top-{} basket vs index ETF -- absolute total returns, {}d windows".format(
        a.top, a.horizon))
    print("=" * 78)

    rows = []
    for mkt in a.markets:
        items = folders(mkt)
        free = None
        for i, (d0, res) in enumerate(items):
            if free is not None and d0 < free:
                continue
            d1 = None
            for j in range(i + 1, len(items)):
                gap = (items[j][0] - d0).days
                if abs(gap - a.horizon) <= a.tolerance:
                    d1 = items[j][0]
                    break
                if gap > a.horizon + a.tolerance:
                    break
            if d1 is None:
                continue
            free = d1

            g = pd.read_csv(res)
            if "Grade" not in g.columns:
                continue
            g["Grade"] = pd.to_numeric(g["Grade"], errors="coerce")
            g = g.dropna(subset=["Grade"]).drop_duplicates("Symbol")
            top = g.nlargest(a.top, "Grade").Symbol.tolist()

            rs = [ret(px[s], d0, d1) for s in top if s in px.columns]
            rs = [r for r in rs if r == r]
            if len(rs) < max(3, a.top // 2):
                continue
            basket = float(np.mean(rs))

            rec = {"market": mkt, "date": d0.date(), "held": len(rs), "basket": basket}
            for b in BENCH[mkt]:
                if b in bm.columns:
                    rec[b] = ret(bm[b], d0, d1)
            rows.append(rec)

    if not rows:
        print("no periods"); return
    t = pd.DataFrame(rows)

    for mkt in a.markets:
        s = t[t.market == mkt]
        if s.empty:
            continue
        print("\n{}  ({} periods, mean {:.0f} of top {} names priced)".format(
            mkt, len(s), s.held.mean(), a.top))
        print("  {:12s} mean {:+7.2%}   median {:+7.2%}   cumulative {:+8.2%}   sd {:6.2%}   "
              "return/sd {:+6.2f}".format(
                  "sss top-N", s.basket.mean(), s.basket.median(),
                  (1 + s.basket).prod() - 1, s.basket.std(ddof=1),
                  s.basket.mean() / s.basket.std(ddof=1) if s.basket.std(ddof=1) else np.nan))
        for b in BENCH[mkt]:
            if b not in s.columns:
                continue
            v = s[[b, "basket"]].dropna()
            if v.empty:
                continue
            d = v.basket - v[b]
            se = d.std(ddof=1) / np.sqrt(len(d))
            print("  {:12s} mean {:+7.2%}   median {:+7.2%}   cumulative {:+8.2%}   sd {:6.2%}   "
                  "return/sd {:+6.2f}".format(
                      b, v[b].mean(), v[b].median(), (1 + v[b]).prod() - 1, v[b].std(ddof=1),
                      v[b].mean() / v[b].std(ddof=1) if v[b].std(ddof=1) else np.nan))
            print("     -> sss minus {}: {:+.2%} per window, t = {:+.2f}, sss wins {}/{}".format(
                b, d.mean(), d.mean() / se if se else np.nan, int((d > 0).sum()), len(d)))

    print("\n  Equal-weighted, no costs, no spread, no slippage, no taxes. TASE names are")
    print("  compared against TA35.TA so both sides are in shekels. Delisted names are")
    print("  absent from the price file, so the basket is survivor-biased in its own favour.")


if __name__ == "__main__":
    main()
