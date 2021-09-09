#############################################################################
#
# Version 0.2.40 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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

ALL_COUNTRY_SYMBOLS_OFF = 0
ALL_COUNTRY_SYMBOLS_US  = 1  # Nasdaq
ALL_COUNTRY_SYMBOLS_SIX = 2  # Swiss Stock Exchange

run_custom_tase      = False   # Custom Portfolio
run_custom           = True
run_tase             = False    # Tel Aviv Stock Exchange
run_nsr              = False   # NASDAQ100+S&P500+RUSSEL1000
run_all              = False   # All Nasdaq Stocks
run_six              = False    # All Swiss Stocks
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
reference_run_custom = 'Results/Custom/20210816-014004_Bdb_nRes289_Custom'
reference_run_tase   = 'Results/Tase/20210903-130138_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes328'
reference_run_nsr    = 'Results/Nsr/20210828-230028_Tchnlgy3.0_FnnclSrvcs0.5_Bdb_nRes800'
reference_run_all    = 'Results/All/220210829-114414_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes3318'
reference_run_six    = 'Results/Six/20210909-143511_S_Bdb_nRes30'

new_run_custom = 'Results/Custom/20210909-154648_Bdb_nRes309_Custom'
new_run_tase   = 'Results/Tase/20210903-130138_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes328'
new_run_nsr    = 'Results/Nsr/20210828-230028_Tchnlgy3.0_FnnclSrvcs0.5_Bdb_nRes800'
new_run_all    = 'Results/All/20210829-114414_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes3318'
new_run_six    = 'Results/Six/20210909-143511_S_Bdb_nRes30'

# TODO: ASAFR: Why is normalized AGIO giving a Good low value?? this is deceiving! Check this
custom_portfolio      = ['GIS', 'RE', 'STZ', 'COG', 'SWK', 'INVA', 'ACGL', 'ES', 'ATVI', 'RNR', 'ETR', 'ALGN', 'VST', 'EXEL', 'PEG', 'OHI', 'NGG', 'DGX', 'ESGR', 'COO', 'TGT', 'BDN', 'MDLZ', 'SCI', 'SRE', 'AVB', 'CRUS', 'MMM', 'WSM', 'LDOS', 'CDK', 'ABBV', 'UTHR', 'HOLX', 'LH', 'APT', 'DG', 'VRSN', 'BIO', 'NBIX', 'MBT', 'ZIM', 'ALL', 'DOX', 'GD', 'LOPE', 'TROW', 'ARE', 'ADM', 'CHKP', 'AZPN', 'ORCL', 'ICE', 'GLPI', 'HUN', 'AMCR', 'VEDL', 'HD', 'EXR', 'TRP', 'NEU', 'PG', 'WPC', 'TSCO', 'LMT', 'CUZ', 'HIW', 'TMO', 'AKAM', 'TRV', 'DRE', 'MCY', 'VICI', 'FTV', 'GM', 'GHC', 'GPP', 'QDEL', 'GNTX', 'NOC', 'RGLD', 'CB', 'FDUS', 'BTI', 'CDNS', 'AMG', 'WPM', 'CPB', 'LPX', 'CACC', 'LITE', 'KIM', 'COOP', 'BRK.B', 'BXP', 'OLP', 'VZ', 'SMFG', 'SKM', 'WMT', 'LAKE', 'AGO', 'SSNC', 'PRIM', 'VMW', 'REGN', 'SEB', 'MCO', 'PGR', 'JEF', 'MSFT', 'JAZZ', 'PNFP', 'SLM', 'HAPP', 'DLB', 'BLK', 'FCPT', 'AEF', 'TRNO', 'AFL', 'OMF', 'INTC', 'TDS', 'ORAN', 'AMGN', 'DISH', 'FAST', 'PNC', 'CMCSA', 'HTH', 'PCAR', 'BPOP', 'NEM', 'FLGT', 'OLLI', 'ACN', 'CSCO', 'TXN', 'BLDR', 'MFC', 'KNOP', 'BTG', 'GIB', 'CDW', 'VRTX', 'KMI', 'AVGO', 'JPM', 'BBY', 'SONY', 'PKX', 'WTFC', 'FRC', 'PBFX', 'GTLS', 'MS', 'APH', 'HZNP', 'NVO', 'RS', 'ALLY', 'BWXT', 'SCHW', 'LEJU', 'PBCT', 'FCNCA', 'GRMN', 'KNX', 'ATH', 'MRK', 'COLM', 'RKT', 'SNDR', 'PB', 'KGC', 'ARW', 'QCOM', 'USB', 'TM', 'STLD', 'PHI', 'CE', 'SUPN', 'MX', 'CE', 'RF', 'NVR', 'FDX', 'NVEC', 'AAPL', 'OPRA', 'USM', 'EBAY', 'C', 'TER', 'DD', 'WFC', 'TEL', 'TX', 'FB', 'MT', 'HMY', 'GFI', 'BAC', 'GS', 'OZK', 'VIACA', 'EPD', 'RIO', 'MRCY', 'BOKF', 'CI', 'UNH', 'MAS', 'MRVL', 'BMRN', 'NVDA', 'CNC', 'TSN', 'SBSW', 'MPLX', 'KLAC', 'COF', 'CGNX', 'FKWL', 'TPC', 'AL', 'THO', 'HPQ', 'LRCX', 'TLK', 'TKC', 'NUS', 'VIAC', 'UI', 'BIIB', 'ZION', 'ANTM', 'JD', 'ZTO', 'MU', 'FRO', 'MDC', 'WAL', 'DAC', 'ZUMZ', 'FF', 'SWKS', 'TTEC', 'LEN.B', 'ZM', 'SYF', 'AMAT', 'QRVO', 'FOXA', 'WY', 'DFS', 'FOX', 'MKSI', 'PM', 'NUE', 'TSM', 'MTH', 'WLK', 'MGM', 'LYB', 'LOGI', 'STT', 'ASX', 'BIDU', 'ENVA', 'BABA', 'SBNY', 'CPRX', 'DHI', 'BMA', 'FHN', 'UWMC', 'AMD', 'GTN', 'MRNA', 'MOS', 'SNX', 'LEN', 'MHO', 'CCS', 'TROX', 'TOL', 'YY', 'SCCO', 'VALE', 'RILY', 'TRQ', 'SID', 'STX', 'UHS', 'CIG', 'HIMX', 'VIV', 'NTES', 'ABEV', 'ONEW', 'MARA', 'IMOS', 'ACTG', 'CEPU', 'GGB', 'PHM', 'GRVY', 'ELP', 'HMLP', 'IRCP']
custom_portfolio_tase = ['FORTY.TA']

# TODO: ASAFR: Check these warnings:
# [DB] AAP       (0015/0016/7427 [0.22%], Diff: 0001), time/left/avg [sec]:    56/25938/3.50 -> /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:542: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()
# /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:532: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()
# /home/asaf/.local/lib/python3.8/site-packages/yfinance/base.py:525: UserWarning: DataFrame columns are not unique, some columns will be omitted.
#   return data.to_dict()