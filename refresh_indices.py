#!/usr/bin/env python3
"""Refresh Indices/{snp500,nasdaq100,russell1000}.csv — the NSR universe.

sss.py reads these three as plain `Symbol,Name` CSVs and never downloads them, so the
NSR universe was frozen at the 2024-01-21 commit. (S&P 500 is *also* fetched live at
sss.py:3641, but that call 403s because Wikipedia now rejects pandas' default urllib
User-Agent — which is why the NSR run died after 3 seconds.)

Each index has a list of candidate sources, tried in order; the first that yields a
plausible table wins. A file is only overwritten when the fetched list passes a
minimum-row sanity check, so a dead source leaves the previous universe intact rather
than silently emptying it. The added/removed diff is printed so a change in the
universe is visible.

    python refresh_indices.py
"""
import io
import os
import re
import sys

import pandas as pd
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"}

SYM_COLS = ("Symbol", "Ticker", "Ticker symbol")
NAME_COLS = ("Security", "Company", "Company Name", "Name", "Security Name")

SOURCES = {
    "snp500": (450, [
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "https://stockanalysis.com/list/sp-500-stocks/",
        "https://www.slickcharts.com/sp500",
    ]),
    "nasdaq100": (90, [
        "https://www.slickcharts.com/nasdaq100",
        "https://stockanalysis.com/list/nasdaq-100-stocks/",
        "https://en.wikipedia.org/wiki/Nasdaq-100",
    ]),
    "russell1000": (800, [
        "https://stockanalysis.com/list/russell-1000-index/",
        "https://stockanalysis.com/list/russell-1000-stocks/",
        "https://en.wikipedia.org/wiki/Russell_1000_Index",
    ]),
}


def pick_table(text, min_rows):
    try:
        tables = pd.read_html(io.StringIO(text))
    except Exception:
        return None
    best = None
    for t in tables:
        cols = {str(c).strip(): c for c in t.columns}
        sym = next((cols[c] for c in SYM_COLS if c in cols), None)
        if sym is None:
            continue
        nam = next((cols[c] for c in NAME_COLS if c in cols), None)
        sub = t[[sym] + ([nam] if nam is not None else [])].dropna()
        if len(sub) < min_rows:
            continue
        if best is None or len(sub) > len(best[0]):
            best = (sub, sym, nam)
    return best


def clean_symbol(s):
    s = re.sub(r"\[.*?\]", "", str(s)).strip().upper()
    return s.replace(".", "-")          # Yahoo uses BRK-B, not BRK.B


def refresh(key, min_rows, urls):
    path = os.path.join("Indices", key + ".csv")
    print("\n=== {} ===".format(key))
    got = None
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=45)
        except Exception as e:
            print("  {:52s} {}".format(url[:52], type(e).__name__)); continue
        if r.status_code != 200:
            print("  {:52s} HTTP {}".format(url[:52], r.status_code)); continue
        got = pick_table(r.text, min_rows)
        print("  {:52s} {}".format(url[:52], "OK {} rows".format(len(got[0])) if got else "no usable table"))
        if got:
            break
    if not got:
        print("  ALL SOURCES FAILED -- leaving the existing file untouched")
        return False

    sub, sym, nam = got
    rows, seen = [], set()
    for _, r_ in sub.iterrows():
        s = clean_symbol(r_[sym])
        if not re.fullmatch(r"[A-Z0-9\-]{1,8}", s) or s in seen:
            continue
        seen.add(s)
        n = re.sub(r"\[.*?\]", "", str(r_[nam])).strip().replace(",", " ") if nam is not None else ""
        rows.append((s, n))
    if len(rows) < min_rows:
        print("  only {} usable rows (< {}) -- leaving file untouched".format(len(rows), min_rows))
        return False

    old = set()
    if os.path.exists(path):
        try:
            old = set(pd.read_csv(path).iloc[:, 0].astype(str))
        except Exception:
            pass
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("Symbol,Name\n")
        for s, n in rows:
            f.write("{},{}\n".format(s, n))

    new = {s for s, _ in rows}
    added, gone = sorted(new - old), sorted(old - new)
    print("  wrote {} rows (was {})".format(len(rows), len(old)))
    print("    added {}: {}".format(len(added), ", ".join(added[:10]) + ("..." if len(added) > 10 else "")))
    print("    gone  {}: {}".format(len(gone), ", ".join(gone[:10]) + ("..." if len(gone) > 10 else "")))
    return True


def main():
    os.makedirs("Indices", exist_ok=True)
    ok = {k: refresh(k, mn, urls) for k, (mn, urls) in SOURCES.items()}
    print("\n=== summary ===")
    for k, v in ok.items():
        n = sum(1 for _ in open(os.path.join("Indices", k + ".csv"), encoding="utf-8")) - 1
        print("  {:12s} {:4d} rows   {}".format(k, n, "refreshed" if v else "STALE (refresh failed)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
