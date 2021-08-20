#############################################################################
#
# Version 0.2.20 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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
research_mode        = False    # Research Mode
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
reference_run_tase   = 'Results/Tase/20210820-030153_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes324'
reference_run_nsr    = 'Results/Nsr/20210815-042855_Tchnlgy3.0_FnnclSrvcs0.5_Bdb_nRes881'
reference_run_all    = 'Results/All/20210815-173943_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes3409'

new_run_custom = 'Results/Custom/20210816-014004_Bdb_nRes289_Custom'
new_run_tase   = 'Results/Tase/20210820-030153_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes324'
new_run_nsr    = 'Results/Nsr/20210815-042855_Tchnlgy3.0_FnnclSrvcs0.5_Bdb_nRes881'
new_run_all    = 'Results/All/20210817-144654_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes3414'

custom_portfolio      = ['DAC', 'AGO', 'WAL', 'AMAT', 'DFS', 'PNFP', 'LRCX', 'CACC', 'SLM', 'BPOP', 'MGM', 'OZK', 'KIM', 'KLAC', 'AFL', 'TROW', 'UI', 'FRC', 'BLK', 'SCHW', 'HIW', 'EXR', 'TROX', 'MRVL', 'FHN', 'SBNY', 'OMF', 'CPRX', 'MSFT', 'FCNCA', 'HZNP', 'UTHR', 'NUE', 'CSCO', 'TER', 'OLP', 'BIO', 'ORCL', 'NVO', 'SCI', 'MU', 'DLB', 'ABBV', 'GS', 'WTFC', 'EBAY', 'PM', 'BOKF', 'BXP', 'REGN', 'TGT', 'BDN', 'PBCT', 'COF', 'FB', 'GPP', 'TX', 'INVA', 'FDUS', 'GRMN', 'COOP', 'PB', 'ALL', 'MCO', 'QRVO', 'DGX', 'CGNX', 'ALGN', 'MS', 'ACN', 'BIIB', 'AVB', 'DRE', 'CE', 'TMO', 'AAPL', 'DG', 'FAST', 'AL', 'GTLS', 'ARE', 'ESGR', 'ACGL', 'LEN', 'LH', 'DHI', 'CDW', 'VICI', 'MDLZ', 'GTN', 'DISH', 'AKAM', 'ALLY', 'MMM', 'NGG', 'BAC', 'CDNS', 'COO', 'GNTX', 'GLPI', 'CEPU', 'ICE', 'FRO', 'ATH', 'BRK.B', 'CMCSA', 'PG', 'CUZ', 'ABEV', 'HOLX', 'MTH', 'PEG', 'WPC', 'TRNO', 'TEL', 'JEF', 'ETR', 'IMOS', 'UHS', 'UNH', 'WMT', 'TSCO', 'STT', 'NVR', 'CB', 'BLDR', 'APH', 'ZIM', 'WPM', 'SYF', 'USB', 'MAS', 'OHI', 'NOC', 'MT', 'PHM', 'VMW', 'VEDL', 'TRV', 'CCS', 'CNC', 'KNX', 'LEN.B', 'FTV', 'LITE', 'CRUS', 'STLD', 'KNOP', 'TSN', 'WFC', 'C', 'TXN', 'GD', 'GFI', 'TKC', 'NVEC', 'ATVI', 'TOL', 'SRE', 'THO', 'PNC', 'RGLD', 'MHO', 'JPM', 'STZ', 'CE', 'PBFX', 'VIV', 'DOX', 'HD', 'MX', 'PGR', 'AVGO', 'CIG', 'FCPT', 'SEB', 'AMCR', 'AMG', 'BTI', 'SNDR', 'ANTM', 'VZ', 'ES', 'VST', 'GHC', 'LMT', 'VRSN', 'CHKP', 'TRP', 'SSNC', 'GIB', 'TTEC', 'TLK', 'RKT', 'FDX', 'RE', 'WY', 'ZION', 'SCCO', 'MBT', 'AMGN', 'MARA', 'BMRN', 'SNX', 'WLK', 'GIS', 'VIACA', 'LDOS', 'ADM', 'QCOM', 'ELP', 'ARW', 'SWK', 'TRQ', 'SONY', 'MRK', 'TSM', 'ASX', 'RNR', 'ORAN', 'AZPN', 'MDC', 'FOXA', 'TM', 'BWXT', 'OPRA', 'RILY', 'SWKS', 'HTH', 'KMI', 'NUS', 'NEM', 'ONEW', 'BBY', 'PHI', 'CPB', 'MKSI', 'BMA', 'ZUMZ', 'LPX', 'MFC', 'WSM', 'RS', 'FOX', 'INTC', 'PCAR', 'HPQ', 'FLGT', 'GGB', 'VALE', 'FKWL', 'DD', 'RF', 'LYB', 'ZM', 'HUN', 'SMFG', 'CI', 'SKM', 'UWMC', 'LOGI', 'ENVA', 'TDS', 'CDK', 'RIO', 'KGC', 'JAZZ', 'TPC', 'SUPN', 'PRIM', 'MRCY', 'PKX', 'NBIX', 'ZTO', 'LOPE', 'ACTG', 'JD', 'NTES', 'SBSW', 'BTG', 'HMY', 'VRTX', 'SID', 'BIDU', 'BABA', 'LAKE', 'EXEL', 'LEJU', 'HAPP', 'FF', 'QDEL', 'GRVY', 'APT', 'YY', 'HMLP', 'HIMX', 'IRCP']
custom_portfolio_tase = ['FORTY.TA']
