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


run_custom_tase      = False   # Custom Portfolio
run_custom           = False
run_tase             = True   # Tel Aviv Stock Exchange
run_nsr              = False   # NASDAQ100+S&P500+RUSSEL1000
run_all              = False   # All Nasdaq Stocks
research_mode        = False  # Research Mode
research_mode_max_ev = False  # @JustLearning's suggestion in Telegram: Multi-Dimentional Scan by Max EV Limit rather than Min EV Limit

# when automatic_results_folder_selection is False, the explicitly specified paths below are used for the
# reference and new_run folder locations.
# When automatic_results_folder_selection is True, the program will automatically use the most recently created
# folder(s).
automatic_results_folder_selection = False

# Upon 1st ever run: reference must be set to None
# After 1st ever Run: Recommended to use reference (filter and damper)
# The research mode shall run on new_run as input (new_run >= reference_run) where > means newer
reference_run_custom = 'Results/All/20210606-011608_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes3195'
reference_run_tase   = 'Results/Tase/20210611-132439_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes306'
reference_run_nsr    = 'Results/Nsr/20210619-173839_Tchnlgy3.0_FnnclSrvcs0.5_Bdb_nRes870'
reference_run_all    = 'Results/All/20210606-011608_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes3195'

new_run_tase   = 'Results/Tase/20210611-132439_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes306'
new_run_nsr    = 'Results/Nsr/20210619-173839_Tchnlgy3.0_FnnclSrvcs0.5_Bdb_nRes870'
new_run_all    = 'Results/All/20210606-011608_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes3195'
new_run_custom = 'Results/Custom/20210607-002552_Bdb_nRes3_Custom'

custom_portfolio      = ['AAPL']
custom_portfolio_tase = ['FORTY.TA']
