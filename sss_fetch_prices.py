#!/usr/bin/env python3
"""
sss_fetch_prices.py -- download split- and dividend-adjusted price history once.

Every backtest number in this repo otherwise comes from joining `previous_close`
across two snapshots. That is a raw price: no dividend, no split adjustment, and a
delisted name simply vanishes from the later snapshot instead of counting as a loss.
All three flatter the model.

    python sss_fetch_prices.py --markets Tase      # ~27 requests, start here
    python sss_fetch_prices.py                     # all 4,975 symbols

RATE LIMITING IS THE BINDING CONSTRAINT, not bandwidth. Yahoo throttles hard: once
it starts answering "Crumb fetch rate-limited (HTTP 429)" a single-ticker download
returns zero rows and every batch comes back mostly empty. Critically it does NOT
raise -- you get a DataFrame of NaNs, which looks exactly like "this stock has no
history". Defaults here are deliberately slow. If you see the backoff notices start
firing, stop and come back in a few hours; pushing through only extends the block.

Everything is resumable. The batch cache is keyed by a hash of the batch's ticker
list plus the date window, so a partial run costs nothing to resume and changing
--markets does not silently serve you a previous run's data.
"""

import argparse
import glob
import hashlib
import json
import os
import time

import pandas as pd
import yfinance as yf

CACHE_DIR = "price_cache"
OUT = os.path.join(CACHE_DIR, "adjusted_close.pkl")
DEAD = os.path.join(CACHE_DIR, "no_data_symbols.json")


def engine_symbols(markets):
    syms = set()
    for mkt in markets:
        for p in sorted(glob.glob(os.path.join("Results", mkt, "*", "sss_engine.csv"))):
            try:
                d = pd.read_csv(p, skiprows=[0], low_memory=False, usecols=["Symbol"])
            except Exception:
                continue
            syms |= set(d.Symbol.dropna().astype(str))
    return sorted(syms)


def to_yahoo(sym):
    """Engine symbol -> Yahoo ticker.

    sss.py builds TASE lookups as symbol.replace('.', '-') + '.TA' (sss.py:3596) and
    rewrites them for display as 'TLV:' + x.replace('.TA','').replace('-','.')
    (sss.py:3212). This inverts that.
    """
    if sym.startswith("TLV:"):
        return sym[4:].replace(".", "-") + ".TA"
    return sym.replace(".U", "-UN").replace(".W", "-WT").replace(".", "-")


def _close_frame(df, batch):
    if df is None or len(df) == 0:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        lvl0 = df.columns.get_level_values(0)
        if "Close" in lvl0:
            df = df["Close"]
        elif len(batch) == 1 and "Close" in df.columns.get_level_values(-1):
            df = df.xs("Close", axis=1, level=-1)
        else:
            return None
    elif "Close" in df.columns:
        df = df[["Close"]]
        if len(batch) == 1:
            df.columns = [batch[0]]
    if isinstance(df, pd.Series):
        df = df.to_frame(batch[0])
    return df.dropna(axis=1, how="all")


def download(batch, start, end):
    try:
        raw = yf.download(batch, start=start, end=end, auto_adjust=True,
                          progress=False, threads=False, group_by="column")
    except Exception as e:
        print("      download raised: {}: {}".format(type(e).__name__, str(e)[:100]))
        return None
    return _close_frame(raw, batch)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--markets", nargs="+", default=["Tase", "Nsr", "All"])
    ap.add_argument("--start", default="2021-05-01")
    ap.add_argument("--end", default="2024-03-01")
    ap.add_argument("--batch-size", type=int, default=20)
    ap.add_argument("--sleep", type=float, default=6.0, help="seconds between batches")
    ap.add_argument("--retry-missing", action="store_true", default=True,
                    help="re-request tickers a batch returned nothing for, in a small group")
    ap.add_argument("--max-consecutive-empty", type=int, default=4,
                    help="give up after this many all-empty batches in a row (throttled)")
    ap.add_argument("--skip-known-dead", action="store_true", default=True,
                    help="skip symbols a previous run confirmed have no history")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    os.makedirs(CACHE_DIR, exist_ok=True)
    syms = engine_symbols(a.markets)
    dead = set()
    if a.skip_known_dead and os.path.exists(DEAD) and not a.force:
        try:
            dead = set(json.load(open(DEAD)))
        except Exception:
            dead = set()

    mapping = {to_yahoo(s): s for s in syms}
    tickers = sorted(t for t in mapping if t not in dead)
    batches = [tickers[i:i + a.batch_size] for i in range(0, len(tickers), a.batch_size)]

    est = len(batches) * (a.sleep + 2) / 60.0
    print("symbols  : {} ({} skipped as known-dead)".format(len(tickers), len(dead)))
    print("batches  : {} of {}   spacing {:.0f}s   est ~{:.0f} min".format(
        len(batches), a.batch_size, a.sleep, est))
    print("window   : {} .. {}".format(a.start, a.end))

    frames, consecutive_empty, newly_dead = [], 0, []
    for bi, batch in enumerate(batches, 1):
        key = hashlib.sha1("|".join(batch).encode()).hexdigest()[:12]
        cache = os.path.join(CACHE_DIR, "b_{}_{}_{}.pkl".format(a.start, a.end, key))
        if os.path.exists(cache) and not a.force:
            frames.append(pd.read_pickle(cache))
            continue

        df = download(batch, a.start, a.end)
        got = set(df.columns) if df is not None else set()
        missing = [t for t in batch if t not in got]

        # A partial miss is ambiguous: genuinely no history, or throttled mid-batch.
        # Re-ask for just the missing ones; if they come back now, it was throttling.
        if missing and a.retry_missing and got:
            time.sleep(a.sleep)
            again = download(missing, a.start, a.end)
            if again is not None and len(again.columns):
                df = again if df is None else pd.concat([df, again], axis=1)
                got |= set(again.columns)
                missing = [t for t in batch if t not in got]

        if not got:
            consecutive_empty += 1
            print("  [{:3d}/{}] EMPTY  ({} consecutive)".format(bi, len(batches), consecutive_empty))
            if consecutive_empty >= a.max_consecutive_empty:
                print("\n  STOPPING: {} all-empty batches in a row. This is rate limiting,"
                      " not missing data.".format(consecutive_empty))
                print("  Everything fetched so far is cached. Re-run this exact command later"
                      " to resume.")
                break
            time.sleep(a.sleep * 4)
            continue

        consecutive_empty = 0
        df.to_pickle(cache)
        frames.append(df)
        newly_dead.extend(missing)
        print("  [{:3d}/{}] {:3d}/{} tickers{}".format(
            bi, len(batches), len(got), len(batch),
            "   no data: " + ",".join(missing[:4]) + ("..." if len(missing) > 4 else "")
            if missing else ""))
        time.sleep(a.sleep)

    if newly_dead:
        json.dump(sorted(dead | set(newly_dead)), open(DEAD, "w"), indent=0)

    if not frames:
        print("\nnothing fetched")
        return

    px = pd.concat(frames, axis=1)
    px = px.loc[:, ~px.columns.duplicated()]
    px = px.rename(columns={c: mapping[c] for c in px.columns if c in mapping})
    px = px.loc[:, [c for c in px.columns if c in set(syms)]]
    px.index = pd.to_datetime(px.index)
    if getattr(px.index, "tz", None) is not None:
        px.index = px.index.tz_localize(None)
    px.sort_index(inplace=True)
    px.to_pickle(OUT)

    covered = int(px.notna().any().sum())
    print("\nwrote {}".format(OUT))
    print("  {} dates x {} symbols".format(px.shape[0], px.shape[1]))
    print("  coverage: {}/{} engine symbols ({:.1%})".format(covered, len(syms), covered / len(syms)))
    if covered < 0.6 * len(syms):
        print("\n  COVERAGE IS LOW. Before treating these as real gaps, check whether you were")
        print("  throttled: run   python -c \"import yfinance as yf;"
              " print(yf.download('AAPL', period='5d', progress=False).shape)\"")
        print("  If that returns (0, ...) you are rate limited and this run is not trustworthy.")


if __name__ == "__main__":
    main()
