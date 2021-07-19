#############################################################################
#
# Version 0.1.129 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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
run_custom           = True
run_tase             = False    # Tel Aviv Stock Exchange
run_nsr              = False   # NASDAQ100+S&P500+RUSSEL1000
run_all              = False   # All Nasdaq Stocks
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
reference_run_custom = 'Results/All/20210704-014737_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes2752' # 'Results/All/20210606-011608_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes3195'
reference_run_tase   = 'Results/Tase/20210716-070702_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes288'
reference_run_nsr    = 'Results/Nsr/20210703-141918_Tchnlgy3.0_FnnclSrvcs0.5_Bdb_nRes825'
reference_run_all    = 'Results/All/20210704-014737_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes2752'

new_run_tase   = 'Results/Tase/20210718-230916_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes287'
new_run_nsr    = 'Results/Nsr/20210717-205110_Tchnlgy3.0_FnnclSrvcs0.5_Bdb_nRes702'
new_run_all    = 'Results/All/20210715-051935_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes2553'
new_run_custom = 'Results/Custom/20210719-065911_Bdb_nRes236_Custom'

custom_portfolio      = ['DAC', 'WAL', 'AGO', 'AMAT', 'DFS', 'SLM', 'LRCX', 'PNFP', 'MGM', 'BPOP', 'KIM', 'OZK', 'OMF', 'FRC', 'HIW', 'AFL', 'UI', 'TROW', 'TROX', 'BLK', 'TER', 'KLAC', 'CPRX', 'FHN', 'SCHW', 'MU', 'SBNY', 'EXR', 'CACC', 'ORCL', 'ALXN', 'BDN', 'OLP', 'BXP', 'WTFC', 'DLB', 'MSFT', 'TGT', 'ABBV', 'PBCT', 'MRVL', 'FCNCA', 'CSCO', 'UTHR', 'QRVO', 'PM', 'HZNP', 'BOKF', 'PB', 'MCO', 'GS', 'EBAY', 'FDUS', 'FB', 'CGNX', 'COF', 'BIO', 'ESGR', 'AVB', 'ALL', 'VICI', 'PBFX', 'CE', 'FRO', 'SCI', 'DRE', 'MX', 'AAPL', 'ABEV', 'REGN', 'NVO', 'GPP', 'OHI', 'AL', 'AKAM', 'BIIB', 'ATH', 'ACN', 'CNC', 'MDLZ', 'FAST', 'MMM', 'GRMN', 'GTN', 'ALGN', 'DG', 'TMO', 'MS', 'COOP', 'ICE', 'NUE', 'DGX', 'GNTX', 'CUZ', 'KNOP', 'ALLY', 'NVEC', 'ARE', 'GLPI', 'WPC', 'ATVI', 'NGG', 'CEPU', 'TX', 'CRUS', 'TRNO', 'WPM', 'LEN', 'BRK.B', 'CMCSA', 'USB', 'ACGL', 'DHI', 'UHS', 'DISH', 'LH', 'HMLP', 'PG', 'BAC', 'GFI', 'GHC', 'INVA', 'JEF', 'IMOS', 'UNH', 'PEG', 'NTES', 'NOC', 'AMGN', 'RGLD', 'VRSN', 'STT', 'AZPN', 'BTI', 'STZ', 'CDW', 'JAZZ', 'LDOS', 'VALE', 'MAS', 'FCPT', 'LMT', 'COO', 'VST', 'TRP', 'GTLS', 'PHM', 'AMG', 'KNX', 'CIG', 'ANTM', 'IRCP', 'VMW', 'SRE', 'MRCY', 'TXN', 'CDNS', 'TRV', 'ETR', 'WMT', 'NVR', 'VIV', 'DOX', 'BMRN', 'SYF', 'HOLX', 'SWK', 'GIB', 'CE', 'VZ', 'PNC', 'TEL', 'PGR', 'OPRA', 'HD', 'TKC', 'SONY', 'JPM', 'CHKP', 'GD', 'VEDL', 'TSM', 'NEM', 'FTV', 'APH', 'AVGO', 'C', 'LITE', 'BWXT', 'TM', 'SWKS', 'GGB', 'CB', 'CDK', 'SNDR', 'THO', 'WFC', 'MBT', 'GIS', 'NUS', 'CI', 'TRQ', 'PCAR', 'MT', 'LEN.B', 'LOGI', 'QCOM', 'SKM', 'ES', 'CPB', 'PHI', 'HTH', 'MRK', 'ONEW', 'CCS', 'ELP', 'ORAN', 'JD', 'ZUMZ', 'ASX', 'PRIM', 'MTH', 'TDS', 'INTC', 'RIO', 'TSN', 'UWMC', 'BBY', 'TLK', 'FOXA', 'HUN', 'ZION', 'ARW', 'SID', 'MHO', 'DD', 'ZTO', 'BABA', 'RE', 'BMA', 'SUPN', 'FKWL', 'FOX', 'ENVA', 'BIDU', 'RNR', 'KGC', 'RS', 'MFC', 'PKX', 'HPQ', 'WSM', 'LYB', 'HMY', 'SMFG', 'RF', 'NBIX', 'LPX', 'LOPE', 'EXEL', 'SBSW', 'LEJU', 'ACTG', 'HAPP', 'BTG', 'TPC', 'VRTX', 'GRVY', 'FF', 'QDEL', 'LAKE', 'YY', 'APT']
custom_portfolio_tase = ['FORTY.TA']
