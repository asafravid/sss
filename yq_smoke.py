#!/usr/bin/env python3
"""
yq_smoke.py — live health check for the YAHOOQUERY path.

smoke_test.py --live exercises yfinance. But sss_config.yq_mode defaults to True,
so sss_run.py actually fetches through yahooquery. Different endpoints, different
failure modes. This checks the ones sss.py reads in the yq branch (sss.py:1651+).

    python yq_smoke.py AAPL
    python yq_smoke.py TEVA.TA --tase
"""
import argparse
import sys

import pandas as pd
from yahooquery import Ticker

# Exactly the keys sss.py reads out of each quoteSummary module.
DKS_KEYS = ['52WeekChange', 'bookValue', 'earningsQuarterlyGrowth', 'enterpriseToEbitda',
            'enterpriseToRevenue', 'enterpriseValue', 'forwardEps', 'heldPercentInsiders',
            'heldPercentInstitutions', 'pegRatio', 'priceToBook', 'profitMargins',
            'sharesOutstanding', 'trailingEps']
SD_KEYS = ['fiftyTwoWeekHigh', 'fiftyTwoWeekLow', 'forwardPE', 'marketCap', 'previousClose',
           'priceToSalesTrailing12Months', 'trailingPE', 'twoHundredDayAverage']
FD_KEYS = ['revenueGrowth']
STATEMENT_FIELDS = {
    'income_statement': ['TotalRevenue', 'NetIncome'],
    'balance_sheet': ['RetainedEarnings'],
    'cash_flow': [],
}

n_fail = 0


def rec(stage, ok, detail=""):
    global n_fail
    tag = "PASS" if ok else "FAIL"
    if not ok:
        n_fail += 1
    print(f"  [{tag}] {stage}" + (f" — {detail}" if detail else ""))


def is_dead(obj):
    """yahooquery returns a plain str error message instead of raising."""
    return obj is None or isinstance(obj, str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--tase", action="store_true",
                    help="skip the '.'->'-' rewrite sss.py applies to non-TASE symbols")
    a = ap.parse_args()

    sym = a.symbol
    key = sym if a.tase else sym.replace('.', '-')
    t = Ticker(sym)
    print(f"yahooquery path — {sym}  (module key: {key})")
    print("=" * 64)

    # ---- all_modules: the umbrella call sss.py makes 8 times
    print("\nall_modules (quoteSummary)")
    try:
        am = t.all_modules
        blob = am.get(key) if isinstance(am, dict) else None
        if is_dead(blob):
            rec("all_modules[symbol]", False, f"{type(blob).__name__}: {str(blob)[:80]}")
            blob = {}
        else:
            rec("all_modules[symbol]", True, f"{len(blob)} modules")
    except Exception as e:
        rec("all_modules", False, f"{type(e).__name__}: {e}")
        blob = {}

    for mod, keys in (("defaultKeyStatistics", DKS_KEYS), ("summaryDetail", SD_KEYS)):
        sub = blob.get(mod)
        if not isinstance(sub, dict):
            rec(f"  {mod}", False, "module absent — every key below falls back to a sentinel")
            continue
        rec(f"  {mod}", True, f"{len(sub)} keys")
        missing = [k for k in keys if sub.get(k) is None]
        for k in keys:
            v = sub.get(k)
            rec(f"    {mod}['{k}']", v is not None, "" if v is None else str(v)[:40])
        if missing:
            rec(f"  {mod} coverage", False, f"missing: {', '.join(missing)}")

    for mod in ("assetProfile", "quoteType"):
        rec(f"  {mod}", isinstance(blob.get(mod), dict), "" if isinstance(blob.get(mod), dict) else "absent")

    # ---- price / financial_data
    print("\nprice / financial_data")
    try:
        p = t.price.get(key)
        rec("price[symbol]['currency']", isinstance(p, dict) and p.get('currency') is not None,
            p.get('currency') if isinstance(p, dict) else str(p)[:60])
    except Exception as e:
        rec("price", False, f"{type(e).__name__}: {e}")
    try:
        fd = t.financial_data.get(key)
        if not isinstance(fd, dict):
            rec("financial_data[symbol]", False, str(fd)[:80])
        else:
            rec("financial_data[symbol]", True, f"{len(fd)} keys")
            for k in FD_KEYS + ['financialCurrency']:
                rec(f"  financial_data['{k}']", fd.get(k) is not None,
                    "" if fd.get(k) is None else str(fd.get(k))[:40])
    except Exception as e:
        rec("financial_data", False, f"{type(e).__name__}: {e}")

    # ---- earnings.financialsChart: drives annualized_revenue / annualized_earnings
    print("\nearnings.financialsChart  (sss.py:1670 — feeds annualized revenue/earnings)")
    try:
        e = t.earnings.get(key)
        if not isinstance(e, dict):
            rec("earnings[symbol]", False, str(e)[:80])
        elif 'financialsChart' not in e:
            rec("earnings[symbol]['financialsChart']", False,
                f"absent; earnings keys = {list(e.keys())[:6]}")
        else:
            fc = e['financialsChart']
            for freq in ('yearly', 'quarterly'):
                rows = fc.get(freq)
                rec(f"  financialsChart['{freq}']", bool(rows), f"{len(rows)} periods" if rows else "empty")
                if rows:
                    rec(f"    has revenue+earnings", all(k in rows[0] for k in ('revenue', 'earnings')),
                        str(rows[0])[:70])
    except Exception as e:
        rec("earnings", False, f"{type(e).__name__}: {e}")

    # ---- statements
    print("\nstatements")
    for meth, fields in STATEMENT_FIELDS.items():
        for freq in ('a', 'q'):
            try:
                df = getattr(t, meth)(frequency=freq)
                if is_dead(df) or not isinstance(df, pd.DataFrame) or df.empty:
                    rec(f"{meth}(frequency='{freq}')", False,
                        "empty/str — sss falls back to sentinels")
                    continue
                rec(f"{meth}(frequency='{freq}')", True, f"shape {df.shape}")
                for f in fields:
                    rec(f"  column '{f}'", f in df.columns,
                        "" if f in df.columns else "absent — sss.py reads this by name")
            except Exception as ex:
                rec(f"{meth}(frequency='{freq}')", False, f"{type(ex).__name__}: {ex}")

    print("\n" + "=" * 64)
    print(f"  {n_fail} failure(s)")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
