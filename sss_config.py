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
reference_run_tase   = 'Results/Tase/20210813-001618_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes329'
reference_run_nsr    = 'Results/Nsr/20210815-042855_Tchnlgy3.0_FnnclSrvcs0.5_Bdb_nRes881'
reference_run_all    = 'Results/All/20210815-173943_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes3409'

new_run_custom = 'Results/Custom/20210816-014004_Bdb_nRes289_Custom'
new_run_tase   = 'Results/Tase/20210813-001618_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes329'
new_run_nsr    = 'Results/Nsr/20210815-042855_Tchnlgy3.0_FnnclSrvcs0.5_Bdb_nRes881'
new_run_all    = 'Results/All/20210815-173943_Tchnlgy3.0_FnnclSrvcs0.5_A_Bdb_nRes3409'

custom_portfolio      = ['DAC', 'AGO', 'WAL', 'DFS', 'AMAT', 'PNFP', 'LRCX', 'SLM', 'MGM', 'BPOP', 'CACC', 'OZK', 'KIM', 'AFL', 'KLAC', 'TROW', 'UI', 'CPRX', 'FRC', 'SBNY', 'BLK', 'SCHW', 'NUE', 'OMF', 'FHN', 'TROX', 'MRVL', 'HIW', 'FCNCA', 'HZNP', 'TER', 'EXR', 'ORCL', 'UTHR', 'OLP', 'MSFT', 'BIO', 'GS', 'TGT', 'CSCO', 'WTFC', 'TX', 'SCI', 'COF', 'DLB', 'BXP', 'BOKF', 'MU', 'PBCT', 'NVO', 'EBAY', 'BDN', 'ABBV', 'PM', 'FDUS', 'FB', 'GPP', 'INVA', 'QRVO', 'COOP', 'PB', 'MS', 'CE', 'GRMN', 'MCO', 'AL', 'ALGN', 'ALL', 'REGN', 'BIIB', 'CGNX', 'ATH', 'DGX', 'AVB', 'ESGR', 'LEN', 'DRE', 'DHI', 'CEPU', 'AAPL', 'DG', 'ALLY', 'ACN', 'GTLS', 'TMO', 'FAST', 'VEDL', 'GTN', 'VICI', 'ARE', 'ACGL', 'CDW', 'AKAM', 'LH', 'BAC', 'DISH', 'MMM', 'MTH', 'GLPI', 'GNTX', 'MT', 'MDLZ', 'FRO', 'CUZ', 'BLDR', 'STT', 'CDNS', 'BRK.B', 'NGG', 'ICE', 'TEL', 'IMOS', 'CMCSA', 'OHI', 'COO', 'JEF', 'CCS', 'SYF', 'STLD', 'HOLX', 'WPC', 'ABEV', 'TRNO', 'PEG', 'USB', 'WPM', 'PBFX', 'NVR', 'PG', 'MAS', 'PHM', 'TRQ', 'NVEC', 'WFC', 'VMW', 'THO', 'KNOP', 'LEN.B', 'UHS', 'WMT', 'TSCO', 'ETR', 'CE', 'C', 'KNX', 'APH', 'FTV', 'RGLD', 'TOL', 'RKT', 'NOC', 'CRUS', 'CB', 'MHO', 'ZIM', 'AMG', 'TSN', 'JPM', 'PNC', 'TXN', 'UNH', 'GD', 'CNC', 'SEB', 'GHC', 'MX', 'SRE', 'HD', 'TRV', 'ATVI', 'TRP', 'AVGO', 'VST', 'GFI', 'SNDR', 'BTI', 'VIV', 'TTEC', 'DOX', 'QCOM', 'STZ', 'GGB', 'ZION', 'ADM', 'CHKP', 'FDX', 'PGR', 'SWK', 'SONY', 'GIB', 'VZ', 'FCPT', 'MARA', 'TKC', 'WY', 'RILY', 'LMT', 'TM', 'AMGN', 'TSM', 'ASX', 'VALE', 'ES', 'RE', 'SNX', 'CIG', 'AMCR', 'VRSN', 'ONEW', 'ANTM', 'BMRN', 'TLK', 'ELP', 'MBT', 'NUS', 'LITE', 'MDC', 'ARW', 'GIS', 'VIACA', 'FOXA', 'LDOS', 'SWKS', 'BWXT', 'ORAN', 'NEM', 'AZPN', 'MFC', 'FLGT', 'BBY', 'HTH', 'MKSI', 'PHI', 'UWMC', 'RS', 'MRK', 'RNR', 'CDK', 'LYB', 'LPX', 'ZUMZ', 'FKWL', 'ZM', 'BMA', 'DD', 'HPQ', 'OPRA', 'CPB', 'FOX', 'HUN', 'INTC', 'RF', 'SKM', 'WSM', 'SMFG', 'PCAR', 'RIO', 'ENVA', 'LOGI', 'JD', 'CI', 'KGC', 'JAZZ', 'TDS', 'NTES', 'PRIM', 'TPC', 'PKX', 'SID', 'MRCY', 'SBSW', 'ZTO', 'SUPN', 'ACTG', 'LOPE', 'BABA', 'BTG', 'NBIX', 'HMY', 'BIDU', 'VRTX', 'LEJU', 'GRVY', 'LAKE', 'HAPP', 'QDEL', 'EXEL', 'FF', 'APT', 'YY', 'HIMX', 'HMLP', 'IRCP']
custom_portfolio_tase = ['FORTY.TA']
