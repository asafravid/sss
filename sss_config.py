#############################################################################
#
# Version 0.2.59 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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

PROFILE = False

ALL_COUNTRY_SYMBOLS_OFF = 0
ALL_COUNTRY_SYMBOLS_US  = 1  # Nasdaq
ALL_COUNTRY_SYMBOLS_SIX = 2  # Swiss Stock Exchange
ALL_COUNTRY_SYMBOLS_ST  = 3  # Swedish (Stockholm) Stock Exchange

run_custom_tase           = False  # Custom Portfolio
run_custom                = False
run_tase             = True
run_nsr              = False
run_all              = False
run_six                   = False  # All Swiss Stocks
run_st                    = False  # All (Stockholm) Swedish Stocks
multi_dim_scan_mode       = True   # research mode
aggregate_only            = False
research_mode_max_ev      = False
use_reference_as_raw_data = False
custom_sss_value_equation = False

scan_close_values_interval      = '1d'
crash_and_continue_refresh_freq = 25  # was: 10 if custom else 100. Lowered so a rate-limit block costs at most 24 symbols of re-fetch.

# When automatic_results_folder_selection is False, the explicitly specified paths below are used for the
# reference and new_run folder locations.
# When automatic_results_folder_selection is True, the program will automatically use the most recently created
# folder(s).
automatic_results_folder_selection = False

# Upon 1st ever run: reference must be set to None
# After 1st ever Run: Recommended to use reference (filter and damper)
# The research mode shall run on new_run as input (new_run >= reference_run) where > means newer
reference_run_custom = 'Results/All/20220419-020633_A_nRes112_Custom_CustSssV'
reference_run_tase   = 'Results/Tase/20260913-150325_Tase_Tchnlgy3.0_RlEstt1.0_nRes300'
reference_run_nsr    = 'Results/Nsr/20260913-123506_Tchnlgy3.0_FnnclSrvcs1.0_nRes476'
reference_run_all    = 'Results/All/20221208-004305_Tchnlgy3.0_FnnclSrvcs1.0_A_nRes2543'
reference_run_six    = 'Results/Six/20220111-002719_S_nRes196'                                        # '20211216-002301_S_nRes27_CustSssV'
reference_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

new_run_custom       = 'Results/Custom/20210917-201728_Bdb_nRes312_Custom'
new_run_tase         = 'Results/Tase/20260913-150938_Tase_Tchnlgy3.0_RlEstt1.0_nRes300'
new_run_nsr          = 'Results/Nsr/20260913-131610_Tchnlgy3.0_FnnclSrvcs1.0_nRes481'
new_run_all          = 'Results/All/20230620-045317_Tchnlgy3.0_FnnclSrvcs1.0_A_nRes2786' #
new_run_six          = 'Results/Six/20220111-002719_S_nRes196'                                        # '20211216-002301_S_nRes27_CustSssV'
new_run_st           = 'Results/St/20210915-023602_St_Bdb_nRes130'

crash_and_continue_path = None

custom_portfolio      = ['XLE', 'AAPL', 'ABB', 'ABBV', 'ABMD', 'ADBE', 'ADSK', 'AFL', 'AGO', 'AKAM', 'AL', 'ALLE', 'AMAT', 'AMD', 'AMZN', 'APH', 'AZN', 'BAH', 'BIO', 'BLK', 'BMBL', 'BMRN', 'BP', 'BPOP', 'BRK B', 'BTI', 'BYND', 'CARR', 'CAT', 'CDNS', 'CHKP', 'CNC', 'COST', 'CPRX', 'CRNT', 'CROX', 'CSCO', 'CTRM', 'CUZ', 'DAC', 'DE', 'DFS', 'DG', 'DHI', 'DOX', 'EL', 'ESGR', 'EXC', 'FAST', 'FB', 'FDX', 'FFIV', 'FISV', 'FROG', 'GFI', 'GILD', 'GLBS', 'GM', 'GOOG', 'GPRO', 'HD', 'HIW', 'HUN', 'HZNP', 'ICE', 'INMD', 'INVA', 'JPM', 'KIM', 'KLAC', 'KO', 'LEVI', 'LMT', 'LOGI', 'LPX', 'LRCX', 'MCD', 'MRNA', 'MS', 'MSFT', 'MSTR', 'MTB', 'MU', 'NFLX', 'NOC', 'NOW', 'NUE', 'NVDA', 'NVO', 'ORCL', 'OZK', 'PEP', 'PFE', 'PLTR', 'PM', 'PNFP', 'PYPL', 'QCOM', 'QRVO', 'RADA', 'RBLX', 'RHP', 'RQI', 'SCHW', 'SCI', 'SEDG', 'SNAP', 'SNDR', 'SNPS', 'SONO', 'SONY', 'TER', 'TGT', 'TM', 'TNDM', 'TROW', 'TRTX', 'TSCO', 'TSLA', 'TWTR', 'UAL', 'UHAL', 'UI', 'UPST', 'V', 'WDC', 'WIX', 'WLK', 'WM', 'ZI', 'ZIM', 'ZM']
custom_portfolio_tase = ['MTRX', 'ELAL', 'RLCO', 'FORTY', 'HLAN', 'ESLT', 'NVMI', 'CAMT', 'POLI', 'LUMI', 'ICL', 'TEVA', 'ABRA', 'ACCL', 'PHOE']

research_mode_probe_list = []  # ['TLV:MMAN']  # ['TLV:MISH']  # ['MTDS']

yq_mode = True


#############################################################################
# Experimental model knobs
#
# Every setting below defaults to upstream behaviour. Changing one changes the
# ranking, so pair each change with a run of sss_backtest.py to find out whether
# it actually helps rather than assuming it does.
#############################################################################

# --- 1. Sentinel clamping -------------------------------------------------
# Missing/negative PEG, CFO, EV/EBITDA, P/E and EV/R are replaced by 100000 upstream.
# Measured on a real TASE scan, this makes effective_peg_ratio span 2.0e7 between the
# 5th and 95th percentile and ev_to_cfo_ratio_effective 4.0e5, while every genuine
# valuation multiple spans only 14x-50x. The score therefore ranks mostly on data
# availability rather than on economics. Set clamp_sentinels = True to cap the
# penalty at sentinel_clamp_value instead.
clamp_sentinels      = True
sentinel_clamp_value = 100.0

# --- 2. Per-factor floors -------------------------------------------------
# held_percent_insiders sits in the denominator with no floor, so a widely-held
# company at 0.012% insiders takes a ~8000x penalty against a founder-controlled one.
# That is an accidental size/ownership bet. Example: {'held_percent_insiders': 0.005}
factor_floors = {}

# --- 3. Per-factor exponents ----------------------------------------------
# The core equation multiplies 17 factors at exponent 1. Five of them (evr_effective,
# pe_effective, effective_ev_to_ebitda, trailing_12months_price_to_sales,
# price_to_book) are near-collinear valuation multiples, so "cheapness" is implicitly
# raised to ~5 against "quality"'s ~4 without anyone choosing that.
# Example: {'evr_effective': 0.2, 'pe_effective': 0.2, 'effective_ev_to_ebitda': 0.2,
#           'trailing_12months_price_to_sales': 0.2, 'price_to_book': 0.2}
factor_exponents = {}

# --- 4. Which score the multi-dimensional scan ranks on -------------------
# 'sss_value' (multiplicative) and 'sss_value_normalized' (additive, max-normalized)
# are not monotone transforms of each other. Measured Spearman between them on the
# Jan-2024 TASE run is 0.516, so they are close to half-independent rankings.
# Valid values: 'sss_value', 'sss_value_normalized'
ranking_score = 'sss_value'


# --- 5. Multi-dimensional scan sub-rank formula ---------------------------
# How much a stock at index i (0 = best) in a surviving screen of length N adds to
# its Grade. The SSS Multi-Dimensional-Scan document and the code disagree here:
#
#   'linear' : r = (N - i) / N**2          <- what sss.py has always implemented
#              Sums over a screen to (N+1)/2N ~ 0.5 for ANY N, so every screen is an
#              equal-weight voter and topping a tight screen beats topping a loose one.
#
#   'sqrt'   : r = sqrt(N - i) / N         <- what the document specifies, and calls
#              "currently the preferred equation" (its table gives 1/sqrt(10)=0.3162
#              for N=10 index 0, 1/sqrt(7)=0.3780 for N=7, 1/sqrt(20)=0.2236 for N=20).
#              Sums to ~(2/3)*sqrt(N), so a 1000-name screen carries ~12x the total
#              weight of a 7-name screen.
#
# These encode opposite philosophies about whether screen size means conviction.
# Default 'linear' preserves upstream behaviour bit-for-bit; set 'sqrt' to A/B the
# documented variant against sss_grade_backtest.py.
subrank_formula = 'linear'


# --- 6. TASE ratio scaling ------------------------------------------------
# TASE quotes prices in agorot (1/100 ILS) while fundamentals are in ILS: Yahoo
# reports price.currency = 'ILA' but financialCurrency = 'ILS'. sss.py carries four
# compensations written in 2021. Measured against live Yahoo data in Sept 2026,
# only one of them is still correct:
#
#   trailingPE            /= 100        -> WRONG today. Yahoo's trailingPE is already
#                                          correct in ILS (MTRX.TA: 20.97 = 106.30/5.07),
#                                          so this leaves pe_effective 100x too low.
#   forwardPE             /= 100        -> moot: forwardPE is absent for TASE names now.
#   priceToBook           /= 100        -> STILL CORRECT. Yahoo really does compute this
#                                          as price-in-agorot / bookValue-in-ILS
#                                          (ELAL.TA: 1640/1.885 = 870.0, reported 870.03).
#   priceToSales   *= rate_to_usd/100   -> WRONG twice over. Yahoo's value is correct in
#                                          ILS, and a price-to-sales ratio is
#                                          dimensionless, so neither the /100 nor the
#                                          currency conversion belongs.
#
# The same dimensionless-ratio argument applies to enterpriseToRevenue and
# enterpriseToEbitda, which are multiplied by the summary currency rate for every
# market. On USD markets the rate is 1.0 so it is a no-op, but on TASE it scales both
# by ~0.276. (Six/CHF and St/SEK have the same latent issue; not addressed here.)
#
# 'upstream'  : keep all four compensations exactly as they are (default, reproduces
#               every committed snapshot).
# 'corrected' : drop the PE /100, drop the price-to-sales scaling entirely, drop the
#               EV/R and EV/EBITDA currency conversion for TASE, and KEEP the
#               price-to-book /100. Dual-listed adjustments are kept in both modes,
#               since those genuinely do mix NIS prices with USD earnings.
#
# Changing this makes new TASE runs incomparable with the 71 committed TASE snapshots.
tase_ratio_scaling = 'corrected'


# --- 7. NSR universe composition ------------------------------------------
# NSR is the union of S&P 500, Nasdaq-100 and Russell 1000. The first two are now
# refreshed by refresh_indices.py (Wikipedia / slickcharts). Russell 1000 has no
# free machine-readable source that still works: Wikipedia dropped its component
# table, stockanalysis.com and slickcharts 404 on every URL form tried, and the
# iShares IWB holdings CSV endpoint returns an HTML page. Indices/russell1000.csv
# is therefore frozen at 2024-01-21, and it is ~1000 of the ~1013 union -- so a
# stale Russell effectively means a stale NSR universe.
#
# Set False to screen only the two lists that are actually current. That is ~530
# verified symbols instead of ~1013 mostly-stale ones, halves the request cost, and
# loses mid-cap coverage. Snapshots taken with this False are NOT comparable with
# the committed Nsr history, which all included Russell 1000.
nsr_include_russell1000 = False

# --- multi-dim scan breadth (added 2026-09-13) --------------------------------
# get_range() builds each axis range from percentiles, then pops the loosest rung
# ("the 1st percentile and the 1st element usually give the same result").
# Upstream pops a different number of rungs per market, and they disagree:
#
#     TASE : pop=0   -> graded 302/302 (100%) on the 2026-09-13 run
#     NS   : pop=1   -> graded  39/476 (8.2%)
#     ALL  : pop=2   -> (untested, would be worse still)
#
# For NS, held_percent_insiders and enterprise_value are both built with
# num_sections=2, so the range is [min, p50] and popping the loosest rung leaves
# ONE value -- the median. Every screen then demands top-half enterprise_value AND
# top-half held_percent_insiders simultaneously. Measured on the 2026-09-13 NS
# snapshot the loosest screen returned 39 of 476, and since screens are nested
# that is the ceiling: the scan graded exactly those 39.
#
# That is defensible as a shortlist, but it makes Grade unfalsifiable as a ranking
# -- 92% of the universe never receives one, so there is nothing to score rank
# quality against. It is also inconsistent with TASE, which already behaves as if
# this knob were 0.
#
#   0    -> keep the loosest rung on every axis, so the first screen admits the
#           whole universe and every symbol accumulates a Grade. DEFAULT as of
#           2026-09-13. No-op for TASE (already 0). NS: 39 -> 444 of 476.
#   None -> upstream per-market values (TASE 0 / NS 1 / ALL 2). Set this to
#           reproduce pre-2026-09-13 output exactly, or to A/B the change.
#
# Costs and caveats of the 0 default:
#   * Grade is a SUM of sub-ranks over surviving screens, so admitting more
#     screens rescales it. NS PDD went 18.13 -> 196.14. Grades are therefore only
#     comparable across runs that used the SAME value of this knob -- record it
#     alongside any stored run.
#   * Screens executed grow: NS 189 -> 5,137 (10s -> ~2min). The ALL grid goes
#     18,375 -> 138,915 combinations over 8,264 rows instead of 476. This is pure
#     local CSV work -- no Yahoo requests, so no rate-limit exposure -- but budget
#     hours, not minutes, for the ALL scan.
#   * It does NOT fix the other coverage gap: 32 of 476 NS symbols are still
#     ungraded because process_info() rejects debt_to_equity_effective <= 0, i.e.
#     every company with negative book equity from buybacks (MCD, MO, PM, ABBV,
#     BKNG, LOW, SBUX, HPQ, DELL, AZO, ORLY, YUM, HCA, TDG, ...). That is a
#     separate, unresolved modelling decision -- see STATUS.md 12.4.
scan_pop_1st_percentiles = 0

# --- zero-revenue years in the profit-margin average (added 2026-09-13) --------
# sss.py computes the weighted profit margin as earnings/revenue per reporting
# period, guarding division by zero with
#     revenue = max(MIN_REVENUE_FOR_0_REVENUE_DIV_BY_0_AVOIDANCE, revenue)   # 0.001
# Yahoo returns revenue == 0.00 with non-zero earnings for some periods, e.g. on
# the 2026-09-13 NS snapshot:
#     VMRK 2025  revenue 0.00  earnings 1,051,301,000  -> ratio 1.051e+12
#     SOLV 2023  revenue 0.00  earnings 1,346,000,000  -> ratio 1.346e+12
#     TPL  2024  revenue 0.00  earnings   453,960,000  -> ratio 4.540e+11
# The guard therefore converts "revenue unknown" into "infinite margin" -- the
# most attractive possible value on a higher-is-better axis. 13 of 476 NS rows
# carried effective_profit_margin > 100 (i.e. >10,000%) because of this, and
# effective_profit_margin is both a core-equation factor and one of the six scan
# axes.
#
#   True  -> skip any period whose revenue is not above the guard, so the margin
#            is averaged over the periods where revenue is actually known.
#            DEFAULT as of 2026-09-13.
#   False -> upstream behaviour (substitute 0.001 and keep the period).
#
# The skip is implemented by raising the loop's entry condition, NOT by
# `continue` -- `weight_index += 1` lives outside the `if`, so a `continue` would
# desynchronise the recency weights.
profit_margin_skip_zero_revenue = True

# --- which debt/equity column the research screen tests (added 2026-09-13) -----
# sss.py computes TWO debt/equity values:
#   debt_to_equity_effective        raw; NEGATIVE when book equity is negative
#   debt_to_equity_effective_used   the modelled value, always positive:
#       raw <  0 -> 1.0 - raw*NEGATIVE_DEBT_TO_EQUITY_FACTOR   (negative equity is
#                                                               re-expressed as very
#                                                               high leverage)
#       raw >= 0 -> DEBT_TO_EQUITY_MIN_BASE + sqrt(raw)
# The core equation consumes `_used` (it is in the core-equation index list, and
# sss_value requires `_used > 0`). The skip_reason logic also tests `_used`.
#
# But process_info()'s research-mode screen tested the RAW column and rejected
# `raw <= 0`, which threw out every company with negative book equity from
# buybacks -- 32 of 481 on the 2026-09-13 NS snapshot: ABBV, AZO, BKNG, CLX, DELL,
# DPZ, HCA, HLT, HPQ, LOW, MAR, MCD, MCK, MO, MSCI, MTD, ORLY, OTIS, PM, SBAC,
# SBUX, STX, TDG, WYNN, YUM and others. Their `_used` values are 43.1 .. 4.08e4,
# i.e. perfectly usable, and the equation was happy to score them -- only the
# screen refused to let them in. That is an internal inconsistency, not a
# modelling decision: the decision about negative equity was already taken at
# sss.py:2263 with an investopedia citation, and the screen contradicted it.
#
#   'used'     -> screen on debt_to_equity_effective_used, consistent with the
#                 core equation. DEFAULT as of 2026-09-13.
#   'upstream' -> screen on the raw column (rejects negative book equity).
debt_to_equity_screen_column = 'used'
