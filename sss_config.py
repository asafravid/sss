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

run_custom_tase           = False    # Custom Portfolio
run_custom                = False
run_tase                  = False   # Tel Aviv Stock Exchange
run_nsr                   = False   # NASDAQ100+S&P500+RUSSEL1000
run_all                   = True   # All Nasdaq Stocks
run_six                   = False   # All Swiss Stocks
run_st                    = False   # All (Stockholm) Swedish Stocks
research_mode             = False   # Research Mode
aggregate_only            = False
research_mode_max_ev      = False   # @JustLearning's suggestion in Telegram: Multi-Dimensional Scan by Max EV Limit rather than Min EV Limit
use_reference_as_raw_data = False
custom_sss_value_equation = False

# When automatic_results_folder_selection is False, the explicitly specified paths below are used for the
# reference and new_run folder locations.
# When automatic_results_folder_selection is True, the program will automatically use the most recently created
# folder(s).
automatic_results_folder_selection = False

# Upon 1st ever run: reference must be set to None
# After 1st ever Run: Recommended to use reference (filter and damper)
# The research mode shall run on new_run as input (new_run >= reference_run) where > means newer
reference_run_custom = None  # 'Results/Custom/20211109-235448_Bdb_nRes271_Custom'
reference_run_tase   = 'Results/Tase/20211217-103246_Tase_Tchnlgy3.0_RlEstt1.0_nRes273' #  '20211211-182250_Tase_Tchnlgy3.0_RlEstt1.0_nRes280_CustSssV'  # '20211204-190025_Tase_Tchnlgy3.0_RlEstt1.0_Bdb_nRes280_CustSssV'
reference_run_nsr    = 'Results/Nsr/20211205-011557_Tchnlgy3.0_FnnclSrvcs0.75_Bdb_nRes775_CustSssV'
reference_run_all    = None  # 'Results/All/20211206-202021_Tchnlgy3.0_FnnclSrvcs0.75_A_Bdb_nRes2958_CustSssV'
reference_run_six    = 'Results/Six/20211216-001037_S_nRes28'                                        # '20211216-002301_S_nRes27_CustSssV'
reference_run_st     = 'Results/St/20210915-023602_St_Bdb_nRes130'

new_run_custom       = 'Results/Custom/20210917-201728_Bdb_nRes312_Custom'
new_run_tase         = 'Results/Tase/20211217-103246_Tase_Tchnlgy3.0_RlEstt1.0_nRes273'
new_run_nsr          = 'Results/Nsr/20211220-002530_Tchnlgy3.0_FnnclSrvcs0.75_nRes781_CustSssV'
new_run_all          = 'Results/All/20211206-202021_Tchnlgy3.0_FnnclSrvcs0.75_A_Bdb_nRes2958_CustSssV'
new_run_six          = 'Results/Six/20211216-001037_S_nRes28'                                        # '20211216-002301_S_nRes27_CustSssV'
new_run_st           = 'Results/St/20210915-023602_St_Bdb_nRes130'

crash_and_continue_path = None # 'Results/Nsr/20211207-215612_Tchnlgy3.0_FnnclSrvcs0.75_cc'

custom_portfolio      = ['AAPL', 'AB', 'ABBV', 'ABC', 'ABEV', 'ACGL', 'ACN', 'ADM', 'AEF', 'AFL', 'AGIO', 'AGO', 'AKAM', 'AL', 'ALGN', 'ALL', 'ALLY', 'AM', 'AMAT', 'AMCR', 'AMD', 'AMG', 'APH', 'ARE', 'ARW', 'ASX', 'ATH', 'ATVI', 'AVB', 'AVGO', 'AVT', 'AZPN', 'BABA', 'BAC', 'BBY', 'BCH', 'BDN', 'BEN', 'BIDU', 'BIO', 'BLDR', 'BLK', 'BMA', 'BMRN', 'BOKF', 'BPOP', 'BRK.B', 'BTG', 'BTI', 'BWXT', 'BXP', 'C', 'CACC', 'CACI', 'CAH', 'CB', 'CCS', 'CCU', 'CDK', 'CDNS', 'CDW', 'CE', 'CE', 'CFG', 'CGNX', 'CHKP', 'CI', 'CIG', 'CINF', 'CMCSA', 'CNC', 'COF', 'COLM', 'COO', 'COOP', 'CPB', 'CPRX', 'CRUS', 'CSCO', 'CTRA', 'CUZ', 'DAC', 'DD', 'DFS', 'DG', 'DGX', 'DHI', 'DISH', 'DLB', 'DOX', 'DRE', 'DVA', 'EBAY', 'EHC', 'ELP', 'EPD', 'ESGR', 'EXEL', 'EXR', 'FAST', 'FB', 'FCNCA', 'FCPT', 'FDUS', 'FDX', 'FF', 'FHN', 'FKWL', 'FLGT', 'FOX', 'FOXA', 'FRC', 'FRO', 'FTV', 'GD', 'GFI', 'GGB', 'GHC', 'GHLD', 'GLPI', 'GM', 'GNTX', 'GPP', 'GRMN', 'GRVY', 'GS', 'GTLS', 'GTN', 'HAPP', 'HD', 'HIMX', 'HIW', 'HMLP', 'HMY', 'HPE', 'HPQ', 'HTH', 'HUN', 'HZNP', 'ICE', 'IMOS', 'INTC', 'INVA', 'IP', 'IPGP', 'IRBT', 'JD', 'JEF', 'JPM', 'KIM', 'KLAC', 'KMI', 'KNOP', 'KNX', 'LAD', 'LAKE', 'LDI', 'LDOS', 'LEN', 'LEN.B', 'LH', 'LITE', 'LMT', 'LOGI', 'LOPE', 'LPX', 'LRCX', 'LSTR', 'LYB', 'MAN', 'MAS', 'MBT', 'MCO', 'MCY', 'MDC', 'MDLZ', 'MFC', 'MGM', 'MHK', 'MHO', 'MIN', 'MKSI', 'MMM', 'MOS', 'MPLX', 'MRCY', 'MRK', 'MRNA', 'MS', 'MSFT', 'MT', 'MTH', 'MU', 'MX', 'NBIX', 'NEU', 'NGG', 'NOC', 'NTES', 'NUE', 'NUS', 'NVDA', 'NVEC', 'NVO', 'NVR', 'NYMT', 'OLLI', 'OLP', 'OMF', 'ONEW', 'OPRA', 'OPY', 'ORAN', 'ORCL', 'OZK', 'PB', 'PBCT', 'PBFX', 'PCAR', 'PG', 'PGR', 'PHI', 'PHM', 'PKX', 'PM', 'PNC', 'PNFP', 'PRIM', 'QCOM', 'QDEL', 'RE', 'REGN', 'RF', 'RGLD', 'RILY', 'RIO', 'RJF', 'RKT', 'ROL', 'RS', 'RTX', 'SAIC', 'SBNY', 'SBR', 'SBSW', 'SCCO', 'SCHW', 'SCI', 'SEB', 'SENEA', 'SID', 'SJT', 'SKM', 'SLM', 'SMFG', 'SNDR', 'SNX', 'SONY', 'SRAD', 'SRE', 'SSNC', 'STLD', 'STT', 'STX', 'SUPN', 'SWKS', 'SYF', 'TDS', 'TEL', 'TER', 'TGT', 'THO', 'TKC', 'TLK', 'TM', 'TMO', 'TOL', 'TRNO', 'TROW', 'TROX', 'TRP', 'TRV', 'TSCO', 'TSM', 'TSN', 'TTEC', 'TX', 'TXN', 'UHS', 'UI', 'UMC', 'UNH', 'UNM', 'USB', 'USM', 'UTHR', 'UWMC', 'VALE', 'VEDL', 'VIAC', 'VIACA', 'VICI', 'VIV', 'VMW', 'VRSN', 'VRTX', 'VZ', 'WAL', 'WFC', 'WLK', 'WMT', 'WPC', 'WPM', 'WSM', 'WTFC', 'WY', 'WYY', 'XBIT', 'ZIM', 'ZION', 'ZM', 'ZUMZ']
custom_portfolio_tase = ['APLP', 'ITMR']

research_mode_probe_list = []  # ['TLV:MISH']  # ['MTDS']

