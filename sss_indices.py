#############################################################################
#
# Version 0.1.61 - Author: Asaf Ravid <asaf.rvd@gmail.com>
#
#    Stock Screener and Scanner - based on yfinance
#    Copyright (C) 2021 Asaf Ravid
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

# Downloads the current TASE share universe into Indices/Data_TASE.csv and
# Indices/Data_Duals_TASE.csv.
#
# HISTORY: this used to GET
#   https://info.tase.co.il/_layouts/Tase/ManagementPages/Export.aspx?...&GridId=33&CurGuid={8560...}
# That was TASE's old SharePoint export. The host no longer exists -- info.tase.co.il
# is NXDOMAIN as of 2026 -- so the call raised, sss.py swallowed the exception in a
# bare try/except, and every TASE scan silently screened whatever stale CSV was on
# disk. The committed file was dated 21/01/2024.
#
# The live site (market.tase.co.il) is an Angular app backed by a JSON API. This
# module calls the same endpoint the site's own front end calls:
#   POST https://api.tase.co.il/api/security/securitiesmarketdata
#   body {"dType":1,"TotalRec":1,"pageNum":N,"cl1":"1","lang":"1"}
# cl1="1" selects Shares (cl1="0" would return bonds, warrants and T-bills too).
# The endpoint requires the Origin/Referer/User-Agent headers below; without them
# Imperva answers 403.
#
# The CSV layout is preserved exactly, including the four header lines and the
# trailing space in "Symbol ", because sss.py skips rows 0-3 and then reads
# row[0] as the name and row[1] as the symbol (sss.py:3468).

import csv
import json
import time

import requests

API_URL = "https://api.tase.co.il/api/security/securitiesmarketdata"
PAGE_SIZE = 30  # fixed server side

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://market.tase.co.il",
    "Referer": "https://market.tase.co.il/",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"),
}

COLUMNS = ["Name", "Symbol ", "ISIN", "Index Membership", "Last closing",
           "Change (%)", "Turnover(NIS thousands)", "Last transaction"]


def _post(body, retries=3, timeout=30):
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(API_URL, headers=HEADERS, data=json.dumps(body), timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last = "HTTP {}: {}".format(r.status_code, r.text[:200])
        except Exception as e:
            last = "{}: {}".format(type(e).__name__, e)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError("TASE API call failed after {} attempts -- {}".format(retries, last))


def fetch_shares(sleep=0.4):
    """Every share on TASE. Returns (items, trade_date)."""
    first = _post({"dType": 1, "TotalRec": 1, "pageNum": 1, "cl1": "1", "lang": "1"})
    total = int(first.get("TotalRec") or 0)
    trade_date = first.get("TradeDateEOD") or first.get("TradeDate") or ""
    items = list(first.get("Items") or [])
    if total <= 0:
        raise RuntimeError("TASE API returned TotalRec={} -- schema may have changed".format(total))

    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    for page in range(2, pages + 1):
        time.sleep(sleep)
        j = _post({"dType": 1, "TotalRec": 1, "pageNum": page, "cl1": "1", "lang": "1"})
        items.extend(j.get("Items") or [])

    seen, uniq = set(), []
    for it in items:
        sym = (it.get("Symbol") or "").strip()
        if sym and sym not in seen:
            seen.add(sym)
            uniq.append(it)
    if len(uniq) < 0.8 * total:
        raise RuntimeError("TASE API returned {} unique shares but claimed {} -- "
                           "refusing to overwrite the symbol list".format(len(uniq), total))
    return uniq, trade_date


def _is_dual(item):
    """Dual-listed by Securities Law: the security also trades on a foreign exchange."""
    if (item.get("ForeignMarket") or "").strip():
        return True
    ex = item.get("StockExchanges")
    if isinstance(ex, list) and ex:
        return True
    if isinstance(ex, str) and ex.strip():
        return True
    return False


def _row(item, dual):
    row = [
        item.get("Name") or "",
        (item.get("Symbol") or "").strip(),
        item.get("ISIN_ID") or "",
        "",  # Index Membership: not returned by this endpoint; sss.py does not read it
        item.get("LastRate") if item.get("LastRate") is not None else "",
        item.get("Change") if item.get("Change") is not None else "",
        item.get("TurnOverValueShekel") if item.get("TurnOverValueShekel") is not None else "",
        item.get("DealTime") or "",
    ]
    if dual:
        row.append((item.get("ForeignMarket") or "").strip())
    return row


def _write(path, title, trade_date, items, dual):
    columns = COLUMNS + (["Foreign Stock Exchange"] if dual else [])
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([title])
        w.writerow(["As of (date and time) {} ".format(trade_date)])
        w.writerow([])
        w.writerow(columns)
        for it in items:
            w.writerow(_row(it, dual))


def update_tase_indices(verbose=True):
    """Refresh both TASE symbol files. Raises on failure -- do not swallow this.

    A silent failure here means the whole scan runs against a stale universe, which
    is far worse than not running at all.
    """
    shares, trade_date = fetch_shares()
    duals = [it for it in shares if _is_dual(it)]

    _write("Indices/Data_TASE.csv", "Market Data - All shares", trade_date, shares, dual=False)
    _write("Indices/Data_Duals_TASE.csv", "Market Data - Dual Listed by Securities Law",
           trade_date, duals, dual=True)

    if verbose:
        print("TASE symbol lists updated (trade date {}): {} shares, {} dual-listed".format(
            trade_date, len(shares), len(duals)))
    return len(shares), len(duals), trade_date


if __name__ == "__main__":
    update_tase_indices()
