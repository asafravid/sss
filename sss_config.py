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

run_custom_tase           = False  # Custom Portfolio
run_custom                = False
run_tase                  = False  # Tel Aviv Stock Exchange
run_nsr                   = True   # NASDAQ100+S&P500+RUSSEL1000
run_all                   = False  # All Nasdaq Stocks
run_six                   = False  # All Swiss Stocks
run_st                    = False  # All (Stockholm) Swedish Stocks
research_mode             = True   # Research Mode
aggregate_only            = False
research_mode_max_ev      = False  # @JustLearning's suggestion in Telegram: Multi-Dimensional Scan by Max EV Limit rather than Min EV Limit
use_reference_as_raw_data = False
custom_sss_value_equation = True

scan_close_values_interval = '1d'

# When automatic_results_folder_selection is False, the explicitly specified paths below are used for the
# reference and new_run folder locations.
# When automatic_results_folder_selection is True, the program will automatically use the most recently created
# folder(s).
automatic_results_folder_selection = False

# Upon 1st ever run: reference must be set to None
# After 1st ever Run: Recommended to use reference (filter and damper)
# The research mode shall run on new_run as input (new_run >= reference_run) where > means newer
reference_run_custom = None  # 'Results/Custom/20211109-235448_Bdb_nRes271_Custom'
reference_run_tase   = 'Results/Tase/20220121-134155_Tase_Tchnlgy7.0_RlEstt1.0_nRes273_CustSssV'  # 20220128-102620_Tase_Tchnlgy7.0_RlEstt1.0_nRes274'
reference_run_nsr    = 'Results/Nsr/20220116-122157_Tchnlgy7.0_FnnclSrvcs1.0_nRes790_CustSssV'  # 20220129-202905_Tchnlgy7.0_FnnclSrvcs1.0_nRes793'
reference_run_all    = 'Results/All/20220102-190905_Tchnlgy7.0_FnnclSrvcs1.0_A_nRes2942_CustSssV'  # 20220118-084334_Tchnlgy7.0_FnnclSrvcs1.0_A_nRes3019'
reference_run_six    = 'Results/Six/20220111-002719_S_nRes196'                                        # '20211216-002301_S_nRes27_CustSssV'
reference_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

new_run_custom       = 'Results/Custom/20210917-201728_Bdb_nRes312_Custom'
new_run_tase         = 'Results/Tase/20220128-113807_Tase_Tchnlgy7.0_RlEstt1.0_nRes273_CustSssV'  # 20220128-102620_Tase_Tchnlgy7.0_RlEstt1.0_nRes274'
new_run_nsr          = 'Results/Nsr/20220129-230539_Tchnlgy7.0_FnnclSrvcs1.0_nRes792_CustSssV'  # 20220129-202905_Tchnlgy7.0_FnnclSrvcs1.0_nRes793'
new_run_all          = 'Results/All/20220118-160553_Tchnlgy7.0_FnnclSrvcs1.0_A_nRes3008_CustSssV'  # 20220118-084334_Tchnlgy7.0_FnnclSrvcs1.0_A_nRes3019'
new_run_six          = 'Results/Six/20220111-002719_S_nRes196'                                        # '20211216-002301_S_nRes27_CustSssV'
new_run_st           = 'Results/St/20210915-023602_St_Bdb_nRes130'

crash_and_continue_path = None # 'Results/Nsr/20211207-215612_Tchnlgy3.0_FnnclSrvcs0.75_cc'

custom_portfolio      = ['AAPL', 'AB', 'ABBV', 'ABC', 'ABEV', 'ACGL', 'ACN', 'ADM', 'AEF', 'AFL', 'AGIO', 'AGO', 'AKAM', 'AL', 'ALGN', 'ALL', 'ALLY', 'AM', 'AMAT', 'AMCR', 'AMD']
custom_portfolio_tase = ['AFRE', 'ITMR']

research_mode_probe_list = []  # ['TLV:MISH']  # ['MTDS']

