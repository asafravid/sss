#############################################################################
#
# Version 0.2.52 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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

run_custom_tase      = False   # Custom Portfolio
run_custom           = False
run_tase             = False    # Tel Aviv Stock Exchange
run_nsr              = True   # NASDAQ100+S&P500+RUSSEL1000
run_all              = False   # All Nasdaq Stocks
run_six              = False    # All Swiss Stocks
run_st               = False    # All (Stockholm) Swedish Stocks
research_mode        = True    # Research Mode
aggregate_only       = False
research_mode_max_ev = False   # @JustLearning's suggestion in Telegram: Multi-Dimensional Scan by Max EV Limit rather than Min EV Limit

# When automatic_results_folder_selection is False, the explicitly specified paths below are used for the
# reference and new_run folder locations.
# When automatic_results_folder_selection is True, the program will automatically use the most recently created
# folder(s).
automatic_results_folder_selection = False

# Upon 1st ever run: reference must be set to None
# After 1st ever Run: Recommended to use reference (filter and damper)
# The research mode shall run on new_run as input (new_run >= reference_run) where > means newer
reference_run_custom = 'Results/Custom/20210909-154648_Bdb_nRes309_Custom'
reference_run_tase   = 'Results/Tase/20210924-100244_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes332'
reference_run_nsr    = 'Results/Nsr/20210926-093332_Tchnlgy3.0_FnnclSrvcs0.75_Bdb_nRes898'
reference_run_all    = 'Results/All/20210926-043839_Tchnlgy3.0_FnnclSrvcs0.75_A_Bdb_nRes3441'
reference_run_six    = 'Results/Six/20210919-072727_S_Bdb_nRes30'
reference_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

new_run_custom = 'Results/Custom/20210917-201728_Bdb_nRes312_Custom'
new_run_tase   = 'Results/Tase/20210924-100244_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes332'
new_run_nsr    = 'Results/Nsr/20210926-093332_Tchnlgy3.0_FnnclSrvcs0.75_Bdb_nRes898'
new_run_all    = 'Results/All/20210926-043839_Tchnlgy3.0_FnnclSrvcs0.75_A_Bdb_nRes3441'
new_run_six    = 'Results/Six/20210920-174034_S_Bdb_nRes30'
new_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

# TODO: ASAFR: Why is normalized AGIO giving a Good low value?? this is deceiving! Check this
custom_portfolio      = ['AAPL', 'ABBV', 'ABEV', 'ACGL', 'ACN', 'ACTG', 'ADM', 'AEF', 'AFL', 'AGIO', 'AGO', 'AKAM', 'AL', 'ALGN', 'ALL', 'ALLY', 'AMAT', 'AMCR', 'AMD', 'AMG', 'AMGN', 'ANTM', 'APH', 'APT', 'ARE', 'ARW', 'ASX', 'ATH', 'ATVI', 'AVB', 'AVGO', 'AZPN', 'BABA', 'BAC', 'BBY', 'BDN', 'BEN', 'BIDU', 'BIIB', 'BIO', 'BLDR', 'BLK', 'BMA', 'BMRN', 'BOKF', 'BPOP', 'BRK.B', 'BTG', 'BTI', 'BWXT', 'BXP', 'C', 'CACC', 'CB', 'CCS', 'CDK', 'CDNS', 'CDW', 'CE', 'CE', 'CEPU', 'CGNX', 'CHKP', 'CI', 'CIG', 'CMCSA', 'CNC', 'COF', 'COG', 'COLM', 'COO', 'COOP', 'CPB', 'CPRX', 'CRUS', 'CSCO', 'CUZ', 'DAC', 'DD', 'DFS', 'DG', 'DGX', 'DHI', 'DISH', 'DLB', 'DOX', 'DRE', 'DVA', 'EBAY', 'ELP', 'ENVA', 'EPD', 'ES', 'ESGR', 'ETR', 'EXEL', 'EXR', 'FAST', 'FB', 'FCNCA', 'FCPT', 'FDUS', 'FDX', 'FF', 'FHN', 'FKWL', 'FLGT', 'FOX', 'FOXA', 'FRC', 'FRO', 'FTV', 'GD', 'GFI', 'GGB', 'GHC', 'GIB', 'GIS', 'GLPI', 'GM', 'GNTX', 'GPP', 'GRMN', 'GRVY', 'GS', 'GTLS', 'GTN', 'HAPP', 'HD', 'HIMX', 'HIW', 'HMLP', 'HMY', 'HOLX', 'HPQ', 'HTH', 'HUN', 'HZNP', 'ICE', 'IMOS', 'INTC', 'INVA', 'IRCP', 'JAZZ', 'JD', 'JEF', 'JPM', 'KGC', 'KIM', 'KLAC', 'KMI', 'KNOP', 'KNX', 'LAKE', 'LDOS', 'LEJU', 'LEN', 'LEN.B', 'LH', 'LITE', 'LMT', 'LOGI', 'LOPE', 'LPX', 'LRCX', 'LYB', 'MARA', 'MAS', 'MBT', 'MCO', 'MCY', 'MDC', 'MDLZ', 'MFC', 'MGM', 'MHO', 'MKSI', 'MMM', 'MOS', 'MPLX', 'MRCY', 'MRK', 'MRNA', 'MRVL', 'MS', 'MSFT', 'MT', 'MTH', 'MU', 'MX', 'NBIX', 'NEM', 'NEU', 'NGG', 'NOC', 'NTES', 'NUE', 'NUS', 'NVDA', 'NVEC', 'NVO', 'NVR', 'OHI', 'OLLI', 'OLP', 'OMF', 'ONEW', 'OPRA', 'ORAN', 'ORCL', 'OZK', 'PB', 'PBCT', 'PBFX', 'PCAR', 'PEG', 'PG', 'PGR', 'PHI', 'PHM', 'PKX', 'PM', 'PNC', 'PNFP', 'PRIM', 'QCOM', 'QDEL', 'QRVO', 'RE', 'REGN', 'RF', 'RGLD', 'RILY', 'RIO', 'RKT', 'RNR', 'RS', 'SBNY', 'SBSW', 'SCCO', 'SCHW', 'SCI', 'SEB', 'SID', 'SKM', 'SLM', 'SMFG', 'SNDR', 'SNX', 'SONY', 'SRE', 'SSNC', 'STLD', 'STT', 'STX', 'STZ', 'SUPN', 'SWK', 'SWKS', 'SYF', 'TDS', 'TEL', 'TER', 'TGT', 'THO', 'TKC', 'TLK', 'TM', 'TMO', 'TOL', 'TPC', 'TRNO', 'TROW', 'TROX', 'TRP', 'TRQ', 'TRV', 'TSCO', 'TSM', 'TSN', 'TTEC', 'TX', 'TXN', 'UHS', 'UI', 'UNH', 'USB', 'USM', 'UTHR', 'UWMC', 'VALE', 'VEDL', 'VIAC', 'VIACA', 'VICI', 'VIV', 'VMW', 'VRSN', 'VRTX', 'VST', 'VZ', 'WAL', 'WFC', 'WLK', 'WMT', 'WPC', 'WPM', 'WSM', 'WTFC', 'WY', 'YY', 'ZIM', 'ZION', 'ZM', 'ZTO', 'ZUMZ']
custom_portfolio_tase = ['DEDR.L']

# TODO: ASAFR: Check these warnings:
# [DB] AAP       (0015/0016/7427 [0.22%], Diff: 0001), time/left/avg [sec]:    56/25938/3.50 -> /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:542: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()
# /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:532: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()
# /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:525: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()

# TODO: ASAFR: DB] G107.TA   (0184/0186/0535 [34.77%], Diff: 0016), time/left/avg [sec]:  1152/ 2160/6.19 ->               Exception in G107.TA symbol.get_info(): None
#               Exception in G107.TA info: local variable 'financials_yearly' referenced before assignment
