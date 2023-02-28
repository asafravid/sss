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
run_tase                  = True   # Tel Aviv Stock Exchange
run_nsr                   = False  # NASDAQ100+S&P500+RUSSEL1000
run_all                   = False  # All Nasdaq Stocks
run_six                   = False  # All Swiss Stocks
run_st                    = False  # All (Stockholm) Swedish Stocks
multi_dim_scan_mode       = False  # Mult-dimentional scan Mode
aggregate_only            = False
research_mode_max_ev      = False
use_reference_as_raw_data = False
custom_sss_value_equation = False

scan_close_values_interval      = '1d'
crash_and_continue_refresh_freq = 10 if run_custom or run_custom_tase else 100 # Flush every 100 symbols (or less for custom)

# When automatic_results_folder_selection is False, the explicitly specified paths below are used for the
# reference and new_run folder locations.
# When automatic_results_folder_selection is True, the program will automatically use the most recently created
# folder(s).
automatic_results_folder_selection = False

# Upon 1st ever run: reference must be set to None
# After 1st ever Run: Recommended to use reference (filter and damper)
# The research mode shall run on new_run as input (new_run >= reference_run) where > means newer
reference_run_custom = 'Results/All/20220419-020633_A_nRes112_Custom_CustSssV'
reference_run_tase   = None  # 'Results/Tase/20221010-022443_Tase_Tchnlgy3.0_RlEstt1.0_nRes297'
reference_run_nsr    = None  #'Results/Nsr/20221010-132855_Tchnlgy3.0_FnnclSrvcs1.0_nRes831'
reference_run_all    = 'Results/All/20220827-133324_Tchnlgy3.0_FnnclSrvcs1.0_A_nRes2980'
reference_run_six    = 'Results/Six/20220111-002719_S_nRes196'                                        # '20211216-002301_S_nRes27_CustSssV'
reference_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

new_run_custom       = 'Results/Custom/20210917-201728_Bdb_nRes312_Custom'
new_run_tase         = 'Results/Tase/20221205-213437_Tase_Tchnlgy3.0_RlEstt1.0_nRes303'
new_run_nsr          = 'Results/Nsr/20221206-040620_Tchnlgy3.0_FnnclSrvcs1.0_nRes834'
new_run_all          = 'Results/All/20221208-004305_Tchnlgy3.0_FnnclSrvcs1.0_A_nRes2543'
new_run_six          = 'Results/Six/20220111-002719_S_nRes196'                                        # '20211216-002301_S_nRes27_CustSssV'
new_run_st           = 'Results/St/20210915-023602_St_Bdb_nRes130'

crash_and_continue_path = None  # 'Results/All/20221206-080038_Tchnlgy3.0_FnnclSrvcs1.0_A_cc'

custom_portfolio      = ['XLE', 'AAPL', 'ABB', 'ABBV', 'ABMD', 'ADBE', 'ADSK', 'AFL', 'AGO', 'AKAM', 'AL', 'ALLE', 'AMAT', 'AMD', 'AMZN', 'APH', 'AZN', 'BAH', 'BIO', 'BLK', 'BMBL', 'BMRN', 'BP', 'BPOP', 'BRK B', 'BTI', 'BYND', 'CARR', 'CAT', 'CDNS', 'CHKP', 'CNC', 'COST', 'CPRX', 'CRNT', 'CROX', 'CSCO', 'CTRM', 'CUZ', 'DAC', 'DE', 'DFS', 'DG', 'DHI', 'DOX', 'EL', 'ESGR', 'EXC', 'FAST', 'FB', 'FDX', 'FFIV', 'FISV', 'FROG', 'GFI', 'GILD', 'GLBS', 'GM', 'GOOG', 'GPRO', 'HD', 'HIW', 'HUN', 'HZNP', 'ICE', 'INMD', 'INVA', 'JPM', 'KIM', 'KLAC', 'KO', 'LEVI', 'LMT', 'LOGI', 'LPX', 'LRCX', 'MCD', 'MRNA', 'MS', 'MSFT', 'MSTR', 'MTB', 'MU', 'NFLX', 'NOC', 'NOW', 'NUE', 'NVDA', 'NVO', 'ORCL', 'OZK', 'PEP', 'PFE', 'PLTR', 'PM', 'PNFP', 'PYPL', 'QCOM', 'QRVO', 'RADA', 'RBLX', 'RHP', 'RQI', 'SCHW', 'SCI', 'SEDG', 'SNAP', 'SNDR', 'SNPS', 'SONO', 'SONY', 'TER', 'TGT', 'TM', 'TNDM', 'TROW', 'TRTX', 'TSCO', 'TSLA', 'TWTR', 'UAL', 'UHAL', 'UI', 'UPST', 'V', 'WDC', 'WIX', 'WLK', 'WM', 'ZI', 'ZIM', 'ZM']
custom_portfolio_tase = ['AFRE', 'ITMR']

research_mode_probe_list = []  # ['TLV:MMAN']  # ['TLV:MISH']  # ['MTDS']

yq_mode = True

