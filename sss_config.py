#############################################################################
#
# Version 0.2.56 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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

run_custom_tase           = False   # Custom Portfolio
run_custom                = False
run_tase                  = True    # Tel Aviv Stock Exchange
run_nsr                   = False   # NASDAQ100+S&P500+RUSSEL1000
run_all                   = False   # All Nasdaq Stocks
run_six                   = False    # All Swiss Stocks
run_st                    = False    # All (Stockholm) Swedish Stocks
research_mode             = False     # Research Mode
aggregate_only            = False
research_mode_max_ev      = False   # @JustLearning's suggestion in Telegram: Multi-Dimensional Scan by Max EV Limit rather than Min EV Limit
use_reference_as_raw_data = False

# When automatic_results_folder_selection is False, the explicitly specified paths below are used for the
# reference and new_run folder locations.
# When automatic_results_folder_selection is True, the program will automatically use the most recently created
# folder(s).
automatic_results_folder_selection = False

# Upon 1st ever run: reference must be set to None
# After 1st ever Run: Recommended to use reference (filter and damper)
# The research mode shall run on new_run as input (new_run >= reference_run) where > means newer
reference_run_custom = 'Results/Custom/20211108-002201_Bdb_nRes18_Custom'
reference_run_tase   = 'Results/Tase/20211108-145501_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes279'
reference_run_nsr    = 'Results/Nsr/20211106-170744_Tchnlgy3.0_FnnclSrvcs0.75_Bdb_nRes788'
reference_run_all    = 'Results/All/20211107-151952_Tchnlgy3.0_FnnclSrvcs0.75_A_Bdb_nRes3004'
reference_run_six    = 'Results/Six/20211012-141034_S_Bdb_nRes30'
reference_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

new_run_custom = 'Results/Custom/20210917-201728_Bdb_nRes312_Custom'
new_run_tase   = 'Results/Tase/20211108-145501_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes279'
new_run_nsr    = 'Results/Nsr/20211106-170744_Tchnlgy3.0_FnnclSrvcs0.75_Bdb_nRes788'
new_run_all    = 'Results/All/20211107-151952_Tchnlgy3.0_FnnclSrvcs0.75_A_Bdb_nRes3004'
new_run_six    = 'Results/Six/20211012-141034_S_Bdb_nRes30'
new_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

# TODO: ASAFR: Why is normalized AGIO giving a Good low value?? this is deceiving! Check this
custom_portfolio      = ['NVDA', 'BLK', 'DAC', 'X', 'TEVA', 'NICE', 'A', 'T', 'TSLA', 'AAPL', 'MSFT', 'BBBY', 'COST', 'ZM', 'CHKP', 'AMZN', 'SEDG', 'FB', 'NFLX', 'Y', 'C']
custom_portfolio_tase = ['SPNTC']

research_mode_probe_list = []  # ['MTDS']

# TODO: ASAFR: Check these warnings:
# [DB] AAP       (0015/0016/7427 [0.22%], Diff: 0001), time/left/avg [sec]:    56/25938/3.50 -> /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:542: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()
# /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:532: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()
# /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:525: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()

# TODO: ASAFR: DB] G107.TA   (0184/0186/0535 [34.77%], Diff: 0016), time/left/avg [sec]:  1152/ 2160/6.19 ->               Exception in G107.TA symbol.get_info(): None
#               Exception in G107.TA info: local variable 'financials_yearly' referenced before assignment
