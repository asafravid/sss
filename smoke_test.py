#!/usr/bin/env python3
"""
sss smoke test — answers "does this still run?" without launching a multi-hour scan.

    python smoke_test.py           offline only: imports, API surface, post-processing
    python smoke_test.py --live    also fetches one ticker and reports field health

Exit code 0 = all checks passed, 1 = at least one FAIL.
"""

import argparse
import glob
import os
import shutil
import sys
import tempfile
import traceback

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results = []


def record(stage, status, detail=""):
    results.append((stage, status, detail))
    colour = {"PASS": "\033[32m", "FAIL": "\033[31m", "WARN": "\033[33m"}.get(status, "")
    reset = "\033[0m" if colour else ""
    print(f"  [{colour}{status}{reset}] {stage}" + (f" — {detail}" if detail else ""))


def section(title):
    print(f"\n{title}\n" + "-" * len(title))


# ---------------------------------------------------------------- 1. interpreter
def check_python():
    section("1. Interpreter")
    v = sys.version_info
    if v >= (3, 9):
        record("Python version", PASS, f"{v.major}.{v.minor}.{v.micro}")
    else:
        record("Python version", FAIL, f"{v.major}.{v.minor} — sss needs 3.9+")
    in_venv = sys.prefix != sys.base_prefix
    record("Running inside a venv", PASS if in_venv else WARN,
           sys.prefix if in_venv else "not in a venv — you may be polluting system Python")


# ---------------------------------------------------------------- 2. dependencies
def check_deps():
    section("2. Third-party dependencies")
    import importlib.metadata as md
    wanted = ["yfinance", "yahooquery", "fpdf2", "pandas", "numpy", "requests",
              "beautifulsoup4", "psutil", "CurrencyConverter", "matplotlib"]
    for pkg in wanted:
        try:
            record(pkg, PASS, md.version(pkg))
        except Exception:
            record(pkg, FAIL, "not installed")

    # pyfpdf/fpdf2 collision is silent and breaks PDF generation at the last step
    try:
        md.version("fpdf")
        record("fpdf/fpdf2 collision", FAIL,
               "legacy 'fpdf' is installed alongside fpdf2 — run: pip uninstall -y fpdf")
    except Exception:
        record("fpdf/fpdf2 collision", PASS, "clean")

    try:
        from fpdf import FPDF, HTMLMixin  # noqa: F401
        record("from fpdf import FPDF, HTMLMixin", PASS)
    except Exception as e:
        record("from fpdf import FPDF, HTMLMixin", FAIL, f"{type(e).__name__}: {e}")

    try:
        from forex_python.converter import CurrencyRates  # noqa: F401
        record("forex_python import", PASS, "imports (rate API may still be down at runtime)")
    except Exception as e:
        record("forex_python import", FAIL, f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------- 3. sss modules
def check_sss_imports():
    section("3. sss modules")
    for mod in ["sss_config", "sss_filenames", "sss", "sss_post_processing",
                "sss_indices", "sss_diff", "pdf_generator"]:
        try:
            __import__(mod)
            record(f"import {mod}", PASS)
        except Exception as e:
            record(f"import {mod}", FAIL, f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------- 4. yfinance API
def check_yf_api():
    section("4. yfinance API surface used by sss.py")
    try:
        import yfinance as yf
    except Exception as e:
        record("import yfinance", FAIL, str(e))
        return
    t = yf.Ticker("AAPL")
    needed = ["get_info", "get_financials", "get_earnings", "get_cashflow",
              "get_balance_sheet", "get_sustainability", "get_major_holders",
              "get_institutional_holders", "get_mutualfund_holders", "get_dividends"]
    missing = [n for n in needed if not hasattr(t, n)]
    for n in needed:
        record(f"Ticker.{n}", PASS if hasattr(t, n) else FAIL,
               "" if hasattr(t, n) else "removed upstream — sss.py will AttributeError")
    record("yf.download", PASS if hasattr(yf, "download") else FAIL)
    if missing:
        record("API surface summary", FAIL, f"{len(missing)} method(s) gone: {', '.join(missing)}")


# ------------------------------------------------------- 5. offline post-processing
def check_postprocessing():
    section("5. Offline pipeline stage (post-processing, no network)")
    candidates = sorted(glob.glob("Results/*/*/sss_engine.csv"))
    if not candidates:
        record("find a results folder", WARN, "no Results/*/*/sss_engine.csv found — skipping")
        return
    src = os.path.dirname(candidates[-1])
    tmp = tempfile.mkdtemp(prefix="sss_smoke_")
    dst = os.path.join(tmp, "run")
    try:
        shutil.copytree(src, dst)
        import sss_post_processing
        sss_post_processing.process_engine_csv(dst)
        import pandas as pd
        out = os.path.join(dst, "sss_engine_normalized.csv")
        d = pd.read_csv(out)
        record("process_engine_csv()", PASS,
               f"{len(d)} rows x {len(d.columns)} cols from {os.path.basename(src)}")
        if "sss_value_normalized" not in d.columns:
            record("sss_value_normalized column", FAIL, "missing from output")
        else:
            n_bad = int(d["sss_value_normalized"].isna().sum())
            record("sss_value_normalized column", PASS if n_bad == 0 else WARN,
                   f"{n_bad} NaN values" if n_bad else "no NaNs")
    except Exception as e:
        record("process_engine_csv()", FAIL, f"{type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- 6. live fetch
# These are the exact info keys sss.py reads. If Yahoo drops one, the corresponding
# factor silently falls back to a sentinel (often 1e5) and distorts every ranking.
INFO_KEYS = [
    "shortName", "sector", "country", "currency", "financialCurrency",
    "enterpriseValue", "marketCap", "sharesOutstanding", "fullTimeEmployees",
    "trailingPE", "forwardPE", "priceToBook", "priceToSalesTrailing12Months",
    "enterpriseToRevenue", "enterpriseToEbitda", "profitMargins",
    "heldPercentInsiders", "heldPercentInstitutions",
    "earningsQuarterlyGrowth", "pegRatio",
    "previousClose", "fiftyTwoWeekLow", "fiftyTwoWeekHigh", "twoHundredDayAverage",
]


def check_live(symbol):
    section(f"6. Live fetch — {symbol} (requires network access to Yahoo)")
    try:
        import yfinance as yf
        info = yf.Ticker(symbol).get_info()
    except Exception as e:
        record("get_info()", FAIL, f"{type(e).__name__}: {e}")
        return
    if not info:
        record("get_info()", FAIL, "returned empty")
        return
    record("get_info()", PASS, f"{len(info)} keys returned")

    present = [k for k in INFO_KEYS if info.get(k) is not None]
    absent = [k for k in INFO_KEYS if info.get(k) is None]
    for k in INFO_KEYS:
        v = info.get(k)
        record(f"info['{k}']", PASS if v is not None else FAIL,
               ("" if v is None else str(v)[:48]))
    record("field coverage", PASS if not absent else WARN,
           f"{len(present)}/{len(INFO_KEYS)} present" +
           (f"; missing: {', '.join(absent)}" if absent else ""))

    section("   Statement endpoints")
    t = yf.Ticker(symbol)
    for name in ["get_financials", "get_balance_sheet", "get_cashflow", "get_earnings"]:
        try:
            df = getattr(t, name)()
            empty = df is None or (hasattr(df, "empty") and df.empty)
            record(name + "()", FAIL if empty else PASS,
                   "empty/None — sss will fall back to sentinels" if empty
                   else f"shape {getattr(df, 'shape', '?')}")
        except Exception as e:
            record(name + "()", FAIL, f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="also hit Yahoo Finance")
    ap.add_argument("--symbol", default="AAPL", help="ticker for the live test")
    args = ap.parse_args()

    print("sss smoke test")
    print("=" * 60)
    check_python()
    check_deps()
    check_sss_imports()
    check_yf_api()
    check_postprocessing()
    if args.live:
        check_live(args.symbol)
    else:
        section("6. Live fetch")
        print("  skipped — re-run with --live to test the Yahoo data path")

    section("Summary")
    n_fail = sum(1 for _, s, _ in results if s == FAIL)
    n_warn = sum(1 for _, s, _ in results if s == WARN)
    n_pass = sum(1 for _, s, _ in results if s == PASS)
    print(f"  {n_pass} passed, {n_warn} warnings, {n_fail} failures")
    if n_fail:
        print("\n  Failures:")
        for stage, s, detail in results:
            if s == FAIL:
                print(f"    - {stage}: {detail}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
