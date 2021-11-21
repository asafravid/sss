#############################################################################
#
# Version 0.2.58 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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
run_tase                  = False    # Tel Aviv Stock Exchange
run_nsr                   = False   # NASDAQ100+S&P500+RUSSEL1000
run_all                   = True   # All Nasdaq Stocks
run_six                   = False    # All Swiss Stocks
run_st                    = False    # All (Stockholm) Swedish Stocks
research_mode             = False     # Research Mode
aggregate_only            = False
research_mode_max_ev      = False   # @JustLearning's suggestion in Telegram: Multi-Dimensional Scan by Max EV Limit rather than Min EV Limit
use_reference_as_raw_data = True
custom_sss_value_equation = True

# When automatic_results_folder_selection is False, the explicitly specified paths below are used for the
# reference and new_run folder locations.
# When automatic_results_folder_selection is True, the program will automatically use the most recently created
# folder(s).
automatic_results_folder_selection = False

# Upon 1st ever run: reference must be set to None
# After 1st ever Run: Recommended to use reference (filter and damper)
# The research mode shall run on new_run as input (new_run >= reference_run) where > means newer
reference_run_custom = None  # 'Results/Custom/20211109-235448_Bdb_nRes271_Custom'
reference_run_tase   = None  # 'Results/Tase/20211112-081706_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes280'
reference_run_nsr    = 'Results/Nsr/20211120-224642_Tchnlgy3.0_FnnclSrvcs0.75_Bdb_nRes773'
reference_run_all    = 'Results/All/20211121-225822_Tchnlgy3.0_FnnclSrvcs0.75_A_Bdb_nRes2968'
reference_run_six    = 'Results/Six/20211113-124102_S_Bdb_nRes26'
reference_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

new_run_custom = 'Results/Custom/20210917-201728_Bdb_nRes312_Custom'
new_run_tase   = 'Results/Tase/20211119-090628_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes275'
new_run_nsr    = 'Results/Nsr/20211120-224642_Tchnlgy3.0_FnnclSrvcs0.75_Bdb_nRes773'
new_run_all    = 'Results/All/20211121-225822_Tchnlgy3.0_FnnclSrvcs0.75_A_Bdb_nRes2968'
new_run_six    = 'Results/Six/20211114-124713_S_Bdb_nRes28'
new_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

custom_portfolio      = ['SKM']
custom_portfolio_tase = ['APLP', 'ITMR']

research_mode_probe_list = []  # ['MTDS']

# TODO: ASAFR: Check & Fix these warnings:
# [DB] AAP       (0015/0016/7427 [0.22%], Diff: 0001), time/left/avg [sec]:    56/25938/3.50 -> /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:542: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()
# /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:532: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()
# /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:525: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()

# TODO: ASAFR: DB] G107.TA   (0184/0186/0535 [34.77%], Diff: 0016), time/left/avg [sec]:  1152/ 2160/6.19 ->               Exception in G107.TA symbol.get_info(): None
#               Exception in G107.TA info: local variable 'financials_yearly' referenced before assignment

# TODO: ASAFR: [DB] GGMC      (2869/2930/7628 [38.41%], Diff: 0000), time/left/avg [sec]: 29715/47638/10.14 ->               Exception in GGMC info: unsupported operand type(s) for *: 'NoneType' and 'float' -> Traceback (most recent call last):
#               File "/root/PycharmProjects/sss/sss.py", line 2115, in process_info
#                 stock_data.effective_price_to_earnings = (stock_data.trailing_price_to_earnings*TRAILING_PRICE_TO_EARNINGS_WEIGHT+stock_data.forward_price_to_earnings*FORWARD_PRICE_TO_EARNINGS_WEIGHT)
#              TypeError: unsupported operand type(s) for *: 'NoneType' and 'float'
#              And:
#              [DB] DTST      (2073/2105/7628 [27.60%], Diff: 0000), time/left/avg [sec]: 21074/55285/10.01 ->               Exception in DTST info: unsupported operand type(s) for *: 'NoneType' and 'float' -> Traceback (most recent call last):
#                File "/root/PycharmProjects/sss/sss.py", line 2115, in process_info
#                  stock_data.effective_price_to_earnings = (stock_data.trailing_price_to_earnings*TRAILING_PRICE_TO_EARNINGS_WEIGHT+stock_data.forward_price_to_earnings*FORWARD_PRICE_TO_EARNINGS_WEIGHT)
#              TypeError: unsupported operand type(s) for *: 'NoneType' and 'float'
#              And:
#              [DB] IGZ       (3463/3532/7628 [46.30%], Diff: 0000), time/left/avg [sec]: 36259/42066/10.27 ->               Exception in IGZ info: '>' not supported between instances of 'NoneType' and 'float' -> Traceback (most recent call last):
#                File "/root/PycharmProjects/sss/sss.py", line 2140, in process_info
#              And:
#              [DB] ZVV       (7491/7616/7628 [99.84%], Diff: 0000), time/left/avg [sec]: 79005/  124/10.37 ->               Exception in ZVV info: '>' not supported between instances of 'NoneType' and 'float' -> Traceback (most recent call last):
#                File "/root/PycharmProjects/sss/sss.py", line 2140, in process_info
#                  if stock_data.two_hundred_day_average > 0.0: stock_data.previous_close_percentage_from_200d_ma  = 100.0 * ((float(stock_data.previous_close) - float(stock_data.two_hundred_day_average)) / float(stock_data.two_hundred_day_average))
#              TypeError: '>' not supported between instances of 'NoneType' and 'float'
