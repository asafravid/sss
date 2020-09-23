import time
import pandas   as pd
import yfinance as yf
import csv
import os

TASE_MODE                    = 1            # Work on the Israeli Market only
CONTINUE_UPON_INFO_EXCEPTION = 1            # Instead of filling with zeros, continue
NUM_EMPLOYEES_UNKNOWN        = 10000000     # This will make the company very inefficient in terms of number of employees
EVR_UNKNOWN                  = 10000000     # This will make the company very expensive in terms of number of EVR
MUTUALFUND                   = 'MUTUALFUND' # Definition of a mutual fund 'quoteType' field in base.py, those are not interesting
PROFIT_MARGIN_UNKNOWN        = 0.01         # This will make the company not profitable terms of profit margins
SHARES_OUTSTANDING_UNKNOWN   = 1000000      # one million shares, jsut a number
UNKNOWN_PEG2R                = 10000000     # unknown so high will yield uninteresting company
TASE_PROFIT_MARGIN           = 0.13
PROFIT_MARGIN_LIMIT          = 0.15

# There are 2 tables on the Wikipedia page
# we want the first table

payload            = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
first_table        = payload[0]
second_table       = payload[1]
df                 = first_table
symbols_snp500     = df['Symbol'].values.tolist()
symbols_nasdaq100  = ['ADBE', 'AMD', 'ALXN', 'ALGN', 'GOOGL', 'GOOG', 'AMZN', 'AMGN', 'ADI', 'ANSS', 'AAPL', 'AMAT', 'ASML', 'ADSK', 'ADP', 'BIDU', 'BIIB', 'BMRN', 'BKNG', 'AVGO', 'CDNS', 'CDW', 'CERN', 'CHTR', 'CHKP', 'CTAS', 'CSCO', 'CTXS', 'CTSH', 'CMCSA', 'CPRT', 'COST', 'CSX', 'DXCM', 'DOCU', 'DLTR', 'EBAY', 'EA', 'EXC', 'EXPE', 'FB', 'FAST', 'FISV', 'FOXA', 'FOX', 'GILD', 'IDXX', 'ILMN', 'INCY', 'INTC', 'INTU', 'ISRG', 'JD', 'KLAC', 'KHC', 'LRCX', 'LBTYA', 'LBTYK', 'LULU', 'MAR', 'MXIM', 'MELI', 'MCHP', 'MU', 'MSFT', 'MRNA', 'MDLZ', 'MNST', 'NTES', 'NFLX', 'NVDA', 'NXPI', 'ORLY', 'PCAR', 'PAYX', 'PYPL', 'PEP', 'PDD', 'QCOM', 'REGN', 'ROST', 'SGEN', 'SIRI', 'SWKS', 'SPLK', 'SBUX', 'SNPS', 'TMUS', 'TTWO', 'TSLA', 'TXN', 'TCOM', 'ULTA', 'VRSN', 'VRSK', 'VRTX', 'WBA', 'WDAY', 'WDC', 'XEL', 'XLNX', 'ZM']
symbols_russel1000 = ['TWOU', 'MMM', 'ABT', 'ABBV', 'ABMD', 'ACHC', 'ACN', 'ATVI', 'AYI', 'ADNT', 'ADBE', 'ADT', 'AAP', 'AMD', 'ACM', 'AES', 'AMG', 'AFL', 'AGCO', 'A', 'AGIO', 'AGNC', 'AL', 'APD', 'AKAM', 'ALK', 'ALB', 'AA', 'ARE', 'ALXN', 'ALGN', 'ALKS', 'Y', 'ALLE', 'AGN', 'ADS', 'LNT', 'ALSN', 'ALL', 'ALLY', 'ALNY', 'GOOGL', 'GOOG', 'MO', 'AMZN', 'AMCX', 'DOX', 'UHAL', 'AEE', 'AAL', 'ACC', 'AEP', 'AXP', 'AFG', 'AMH', 'AIG', 'ANAT', 'AMT', 'AWK', 'AMP', 'ABC', 'AME', 'AMGN', 'APH', 'ADI', 'NLY', 'ANSS', 'AR', 'ANTM', 'AON', 'APA', 'AIV', 'APY', 'APLE', 'AAPL', 'AMAT', 'ATR', 'APTV', 'WTR', 'ARMK', 'ACGL', 'ADM', 'ARNC', 'ARD', 'ANET', 'AWI', 'ARW', 'ASH', 'AZPN', 'ASB', 'AIZ', 'AGO', 'T', 'ATH', 'TEAM', 'ATO', 'ADSK', 'ADP', 'AN', 'AZO', 'AVB', 'AGR', 'AVY', 'AVT', 'EQH', 'AXTA', 'AXS', 'BKR', 'BLL', 'BAC', 'BOH', 'BK', 'OZK', 'BKU', 'BAX', 'BDX', 'WRB', 'BRK.B', 'BERY', 'BBY', 'BYND', 'BGCP', 'BIIB', 'BMRN', 'BIO', 'TECH', 'BKI', 'BLK', 'HRB', 'BLUE', 'BA', 'BOKF', 'BKNG', 'BAH', 'BWA', 'BSX', 'BDN', 'BFAM', 'BHF', 'BMY', 'BRX', 'AVGO', 'BR', 'BPYU', 'BRO', 'BFA', 'BFB', 'BRKR', 'BC', 'BG', 'BURL', 'BWXT', 'CHRW', 'CABO', 'CBT', 'COG', 'CACI', 'CDNS', 'CZR', 'CPT', 'CPB', 'CMD', 'COF', 'CAH', 'CSL', 'KMX', 'CCL', 'CRI', 'CASY', 'CTLT', 'CAT', 'CBOE', 'CBRE', 'CBS', 'CDK', 'CDW', 'CE', 'CELG', 'CNC', 'CDEV', 'CNP', 'CTL', 'CDAY', 'BXP', 'CF', 'CRL', 'CHTR', 'CHE', 'LNG', 'CHK', 'CVX', 'CIM', 'CMG', 'CHH', 'CB', 'CHD', 'CI', 'XEC', 'CINF', 'CNK', 'CTAS', 'CSCO', 'CIT', 'C', 'CFG', 'CTXS', 'CLH', 'CLX', 'CME', 'CMS', 'CNA', 'CNX', 'KO', 'CGNX', 'CTSH', 'COHR', 'CFX', 'CL', 'CLNY', 'CXP', 'COLM', 'CMCSA', 'CMA', 'CBSH', 'COMM', 'CAG', 'CXO', 'CNDT', 'COP', 'ED', 'STZ', 'CERN', 'CPA', 'CPRT', 'CLGX', 'COR', 'GLW', 'OFC', 'CSGP', 'COST', 'COTY', 'CR', 'CACC', 'CCI', 'CCK', 'CSX', 'CUBE', 'CFR', 'CMI', 'CW', 'CVS', 'CY', 'CONE', 'DHI', 'DHR', 'DRI', 'DVA', 'SITC', 'DE', 'DELL', 'DAL', 'XRAY', 'DVN', 'DXCM', 'FANG', 'DKS', 'DLR', 'DFS', 'DISCA', 'DISCK', 'DISH', 'DIS', 'DHC', 'DOCU', 'DLB', 'DG', 'DLTR', 'D', 'DPZ', 'CLR', 'COO', 'DEI', 'DOV', 'DD', 'DPS', 'DTE', 'DUK', 'DRE', 'DNB', 'DNKN', 'DXC', 'ETFC', 'EXP', 'EWBC', 'EMN', 'ETN', 'EV', 'EBAY', 'SATS', 'ECL', 'EIX', 'EW', 'EA', 'EMR', 'ESRT', 'EHC', 'EGN', 'ENR', 'ETR', 'EVHC', 'EOG', 'EPAM', 'EPR', 'EQT', 'EFX', 'EQIX', 'EQC', 'ELS', 'EQR', 'ERIE', 'ESS', 'EL', 'EEFT', 'EVBG', 'EVR', 'RE', 'EVRG', 'ES', 'UFS', 'DCI', 'EXPE', 'EXPD', 'STAY', 'EXR', 'XOG', 'XOM', 'FFIV', 'FB', 'FDS', 'FICO', 'FAST', 'FRT', 'FDX', 'FIS', 'FITB', 'FEYE', 'FAF', 'FCNCA', 'FDC', 'FHB', 'FHN', 'FRC', 'FSLR', 'FE', 'FISV', 'FLT', 'FLIR', 'FND', 'FLO', 'FLS', 'FLR', 'FMC', 'FNB', 'FNF', 'FL', 'F', 'FTNT', 'FTV', 'FBHS', 'FOXA', 'FOX', 'BEN', 'FCX', 'AJG', 'GLPI', 'GPS', 'EXAS', 'EXEL', 'EXC', 'GTES', 'GLIBA', 'GD', 'GE', 'GIS', 'GM', 'GWR', 'G', 'GNTX', 'GPC', 'GILD', 'GPN', 'GL', 'GDDY', 'GS', 'GT', 'GRA', 'GGG', 'EAF', 'GHC', 'GWW', 'LOPE', 'GPK', 'GRUB', 'GWRE', 'HAIN', 'HAL', 'HBI', 'THG', 'HOG', 'HIG', 'HAS', 'HE', 'HCA', 'HDS', 'HTA', 'PEAK', 'HEI.A', 'HEI', 'HP', 'JKHY', 'HLF', 'HSY', 'HES', 'GDI', 'GRMN', 'IT', 'HGV', 'HLT', 'HFC', 'HOLX', 'HD', 'HON', 'HRL', 'HST', 'HHC', 'HPQ', 'HUBB', 'HPP', 'HUM', 'HBAN', 'HII', 'HUN', 'H', 'IAC', 'ICUI', 'IEX', 'IDXX', 'INFO', 'ITW', 'ILMN', 'INCY', 'IR', 'INGR', 'PODD', 'IART', 'INTC', 'IBKR', 'ICE', 'IGT', 'IP', 'IPG', 'IBM', 'IFF', 'INTU', 'ISRG', 'IVZ', 'INVH', 'IONS', 'IPGP', 'IQV', 'HPE', 'HXL', 'HIW', 'HRC', 'JAZZ', 'JBHT', 'JBGS', 'JEF', 'JBLU', 'JNJ', 'JCI', 'JLL', 'JPM', 'JNPR', 'KSU', 'KAR', 'K', 'KEY', 'KEYS', 'KRC', 'KMB', 'KIM', 'KMI', 'KEX', 'KLAC', 'KNX', 'KSS', 'KOS', 'KR', 'LB', 'LHX', 'LH', 'LRCX', 'LAMR', 'LW', 'LSTR', 'LVS', 'LAZ', 'LEA', 'LM', 'LEG', 'LDOS', 'LEN', 'LEN.B', 'LII', 'LBRDA', 'LBRDK', 'FWONA', 'IRM', 'ITT', 'JBL', 'JEC', 'LLY', 'LECO', 'LNC', 'LGF.A', 'LGF.B', 'LFUS', 'LYV', 'LKQ', 'LMT', 'L', 'LOGM', 'LOW', 'LPLA', 'LULU', 'LYFT', 'LYB', 'MTB', 'MAC', 'MIC', 'M', 'MSG', 'MANH', 'MAN', 'MRO', 'MPC', 'MKL', 'MKTX', 'MAR', 'MMC', 'MLM', 'MRVL', 'MAS', 'MASI', 'MA', 'MTCH', 'MAT', 'MXIM', 'MKC', 'MCD', 'MCK', 'MDU', 'MPW', 'MD', 'MDT', 'MRK', 'FWONK', 'LPT', 'LSXMA', 'LSXMK', 'LSI', 'CPRI', 'MIK', 'MCHP', 'MU', 'MSFT', 'MAA', 'MIDD', 'MKSI', 'MHK', 'MOH', 'TAP', 'MDLZ', 'MPWR', 'MNST', 'MCO', 'MS', 'MORN', 'MOS', 'MSI', 'MSM', 'MSCI', 'MUR', 'MYL', 'NBR', 'NDAQ', 'NFG', 'NATI', 'NOV', 'NNN', 'NAVI', 'NCR', 'NKTR', 'NTAP', 'NFLX', 'NBIX', 'NRZ', 'NYCB', 'NWL', 'NEU', 'NEM', 'NWSA', 'NWS', 'MCY', 'MET', 'MTD', 'MFA', 'MGM', 'JWN', 'NSC', 'NTRS', 'NOC', 'NLOK', 'NCLH', 'NRG', 'NUS', 'NUAN', 'NUE', 'NTNX', 'NVT', 'NVDA', 'NVR', 'NXPI', 'ORLY', 'OXY', 'OGE', 'OKTA', 'ODFL', 'ORI', 'OLN', 'OHI', 'OMC', 'ON', 'OMF', 'OKE', 'ORCL', 'OSK', 'OUT', 'OC', 'OI', 'PCAR', 'PKG', 'PACW', 'PANW', 'PGRE', 'PK', 'PH', 'PE', 'PTEN', 'PAYX', 'PAYC', 'PYPL', 'NEE', 'NLSN', 'NKE', 'NI', 'NBL', 'NDSN', 'PEP', 'PKI', 'PRGO', 'PFE', 'PCG', 'PM', 'PSX', 'PPC', 'PNFP', 'PF', 'PNW', 'PXD', 'ESI', 'PNC', 'PII', 'POOL', 'BPOP', 'POST', 'PPG', 'PPL', 'PRAH', 'PINC', 'TROW', 'PFG', 'PG', 'PGR', 'PLD', 'PFPT', 'PB', 'PRU', 'PTC', 'PSA', 'PEG', 'PHM', 'PSTG', 'PVH', 'QGEN', 'QRVO', 'QCOM', 'PWR', 'PBF', 'PEGA', 'PAG', 'PNR', 'PEN', 'PBCT', 'RLGY', 'RP', 'O', 'RBC', 'REG', 'REGN', 'RF', 'RGA', 'RS', 'RNR', 'RSG', 'RMD', 'RPAI', 'RNG', 'RHI', 'ROK', 'ROL', 'ROP', 'ROST', 'RCL', 'RGLD', 'RES', 'RPM', 'RSPP', 'R', 'SPGI', 'SABR', 'SAGE', 'CRM', 'SC', 'SRPT', 'SBAC', 'HSIC', 'SLB', 'SNDR', 'SCHW', 'SMG', 'SEB', 'SEE', 'DGX', 'QRTEA', 'RL', 'RRC', 'RJF', 'RYN', 'RTN', 'NOW', 'SVC', 'SHW', 'SBNY', 'SLGN', 'SPG', 'SIRI', 'SIX', 'SKX', 'SWKS', 'SLG', 'SLM', 'SM', 'AOS', 'SJM', 'SNA', 'SON', 'SO', 'SCCO', 'LUV', 'SPB', 'SPR', 'SRC', 'SPLK', 'S', 'SFM', 'SQ', 'SSNC', 'SWK', 'SBUX', 'STWD', 'STT', 'STLD', 'SRCL', 'STE', 'STL', 'STOR', 'SYK', 'SUI', 'STI', 'SIVB', 'SWCH', 'SGEN', 'SEIC', 'SRE', 'ST', 'SCI', 'SERV', 'TPR', 'TRGP', 'TGT', 'TCO', 'TCF', 'AMTD', 'TDY', 'TFX', 'TDS', 'TPX', 'TDC', 'TER', 'TEX', 'TSRO', 'TSLA', 'TCBI', 'TXN', 'TXT', 'TFSL', 'CC', 'KHC', 'WEN', 'TMO', 'THO', 'TIF', 'TKR', 'TJX', 'TOL', 'TTC', 'TSCO', 'TDG', 'RIG', 'TRU', 'TRV', 'THS', 'TPCO', 'TRMB', 'TRN', 'TRIP', 'SYF', 'SNPS', 'SNV', 'SYY', 'DATA', 'TTWO', 'TMUS', 'TFC', 'UBER', 'UGI', 'ULTA', 'ULTI', 'UMPQ', 'UAA', 'UA', 'UNP', 'UAL', 'UPS', 'URI', 'USM', 'X', 'UTX', 'UTHR', 'UNH', 'UNIT', 'UNVR', 'OLED', 'UHS', 'UNM', 'URBN', 'USB', 'USFD', 'VFC', 'MTN', 'VLO', 'VMI', 'VVV', 'VAR', 'VVC', 'VEEV', 'VTR', 'VER', 'VRSN', 'VRSK', 'VZ', 'VSM', 'VRTX', 'VIAC', 'TWLO', 'TWTR', 'TWO', 'TYL', 'TSN', 'USG', 'UI', 'UDR', 'VMC', 'WPC', 'WBC', 'WAB', 'WBA', 'WMT', 'WM', 'WAT', 'WSO', 'W', 'WFTLF', 'WBS', 'WEC', 'WRI', 'WBT', 'WCG', 'WFC', 'WELL', 'WCC', 'WST', 'WAL', 'WDC', 'WU', 'WLK', 'WRK', 'WEX', 'WY', 'WHR', 'WTM', 'WLL', 'JW.A', 'WMB', 'WSM', 'WLTW', 'WTFC', 'WDAY', 'WP', 'WPX', 'WYND', 'WH', 'VIAB', 'VICI', 'VIRT', 'V', 'VC', 'VST', 'VMW', 'VNO', 'VOYA', 'ZAYO', 'ZBRA', 'ZEN', 'ZG', 'Z', 'ZBH', 'ZION', 'ZTS', 'ZNGA', 'WYNN', 'XEL', 'XRX', 'XLNX', 'XPO', 'XYL', 'YUMC', 'YUM']
symbols_tase       = ['ALD.TA', 'ABIL.TA', 'ACCL.TA', 'ADGR.TA', 'ADKA.TA', 'ARDM.TA', 'AFHL.TA', 'AFPR.TA', 'AFID.TA', 'AFRE.TA', 'AICS.TA', 'ARPT.TA', 'ALBA.TA', 'ALMD.TA', 'ALLT.TA', 'ALMA.TA', 'ALGS.TA', 'ALHE.TA', 'ALRPR.TA', 'ASPF.TA', 'AMAN.TA', 'AMRK.TA', 'AMOT.TA', 'ANLT.TA', 'ANGL.TA', 'APIO.M.TA', 'APLP.TA', 'ARD.TA', 'ARAD.TA', 'ARAN.TA', 'ARNA.TA', 'ARKO.TA', 'ARYT.TA', 'ASHO.TA', 'ASHG.TA', 'ASPR.TA', 'ASGR.TA', 'ATRY.TA', 'AUDC.TA', 'AUGN.TA', 'AURA.TA', 'SHVA.TA', 'AVER.TA', 'AVGL.TA', 'AVIA.TA', 'AVIV.TA', 'AVLN.TA', 'AVRT.TA', 'AYAL.TA', 'AZRM.TA', 'AZRG.TA', 'BCOM.TA', 'BYAR.TA', 'BBYL.TA', 'BRAN.TA', 'BVC.TA', 'BYSD.TA', 'ORL.TA', 'BSEN.TA', 'BEZQ.TA', 'BGI-M.TA', 'BIG.TA', 'BIOV.TA', 'BOLT.TA', 'BLRX.TA', 'PHGE.TA', 'BIRM.TA', 'BLSR.TA', 'BOTI.TA', 'BONS.TA', 'BCNV.TA', 'BWAY.TA', 'BRAM.TA', 'BRND.TA', 'BNRG.TA', 'BRIL.TA', 'BRMG.TA', 'CISY.TA', 'CAMT.TA', 'CANF.TA', 'CSURE.TA', 'CNMD.TA', 'CNZN.TA', 'CPTP.TA', 'CRSO.TA', 'CRMT.TA', 'CAST.TA', 'CEL.TA', 'CHAM.TA', 'CHR.TA', 'CMCT.TA', 'CMCTP.TA', 'CTPL5.TA', 'CTPL1.TA', 'CLBV.TA', 'CBI.TA', 'CLIS.TA', 'CFX.TA', 'CDEV.TA', 'CGEN.TA', 'CMDR.TA', 'DNA.TA', 'DANH.TA', 'DANE.TA', 'DCMA.TA', 'DLRL.TA', 'DLEA.TA', 'DEDR.L.TA', 'DLEKG.TA', 'DELT.TA', 'DIMRI.TA', 'DIFI.TA', 'DSCT.TA', 'DISI.TA', 'DRAL.TA', 'DORL.TA', 'DRSL.TA', 'DUNI.TA', 'EMCO.TA', 'EDRL.TA', 'ELAL.TA', 'EMITF.TA', 'EMTC.TA', 'ESLT.TA', 'ELCO.TA', 'ELDAV.TA', 'ELTR.TA', 'ECP.TA', 'ELCRE.TA', 'ELWS.TA', 'ELLO.TA', 'ELMR.TA', 'ELRN.TA', 'ELSPC.TA', 'EMDV.TA', 'ENDY.TA', 'ENOG.TA', 'ENRG.TA', 'ENLT.TA', 'ENLV.TA', 'EQTL.TA', 'EFNC.TA', 'EVGN.TA', 'EXPO.TA', 'FNTS.TA', 'FTAL.TA', 'FIBI.TA', 'FIBIH.TA', 'FGAS.TA', 'FBRT.TA', 'FRSX.TA', 'FORTY.TA', 'FOX.TA', 'FRSM.TA', 'FRDN.TA', 'GOSS.TA', 'GFC-L.TA', 'GPGB.TA', 'GADS.TA', 'GSFI.TA', 'GAON.TA', 'GAGR.TA', 'GZT.TA', 'GNRS.TA', 'GIBUI.TA', 'GILT.TA', 'GNGR.TA', 'GIVO.L.TA', 'GIX.TA', 'GLTC.TA', 'GLEX.L.TA', 'GKL.TA', 'GLRS.TA', 'GODM-M.TA', 'GLPL.TA', 'GOLD.TA', 'GOHO.TA', 'GOLF.TA', 'HDST.TA', 'HAP.TA', 'HGG.TA', 'HAIN.TA', 'HMAM.TA', 'MSBI.TA', 'HAMAT.TA', 'HAML.TA', 'HNMR.TA', 'HARL.TA', 'HLAN.TA', 'HRON.TA', 'HOD.TA', 'HLMS.TA', 'IBI.TA', 'IBITEC.F.TA', 'ICB.TA', 'ICCM.TA', 'ICL.TA', 'IDIN.TA', 'IES.TA', 'IFF.TA', 'ILDR.TA', 'ILX.TA', 'IMCO.TA', 'INBR.TA', 'INFR.TA', 'INRM.TA', 'INTL.TA', 'ININ.TA', 'INCR.TA', 'INTR.TA', 'IGLD-M.TA', 'ISCD.TA', 'ISCN.TA', 'ILCO.TA', 'ISOP.L.TA', 'ISHI.TA', 'ISRA.L.TA', 'ISRS.TA', 'ISRO.TA', 'ISTA.TA', 'ITMR.TA', 'JBNK.TA', 'KDST.TA', 'KAFR.TA', 'KMDA.TA', 'KRNV-L.TA', 'KARE.TA', 'KRDI.TA', 'KEN.TA', 'KRUR.TA', 'KTOV.TA', 'KLIL.TA', 'KMNK-M.TA', 'KNFM.TA', 'LHIS.TA', 'LAHAV.TA', 'ILDC.TA', 'LPHL.L.TA', 'LAPD.TA', 'LDER.TA', 'LSCO.TA', 'LUMI.TA', 'LEOF.TA', 'LEVI.TA', 'LVPR.TA', 'LBTL.TA', 'LCTX.TA', 'LPSN.TA', 'LODZ.TA', 'LUDN.TA', 'LUZN.TA', 'LZNR.TA', 'MGIC.TA', 'MLTM.TA', 'MMAN.TA', 'MSLA.TA', 'MTMY.TA', 'MTRX.TA', 'MAXO.TA', 'MTRN.TA', 'MEAT.TA', 'MDGS.TA', 'MDPR.TA', 'MDTR.TA', 'MDVI.TA', 'MGOR.TA', 'MEDN.TA', 'MTDS.TA', 'MLSR.TA', 'MNIN.TA', 'MNRT.TA', 'MMHD.TA', 'CMER.TA', 'MRHL.TA', 'MSKE.TA', 'MGRT.TA', 'MCRNT.TA', 'MGDL.TA', 'MIFT.TA', 'MNGN.TA', 'MNRV.TA', 'MLD.TA', 'MSHR.TA', 'MVNE.TA', 'MISH.TA', 'MZTF.TA', 'MBMX-M.TA', 'MDIN.L.TA', 'MRIN.TA', 'MYSZ.TA', 'MYDS.TA', 'NFTA.TA', 'NVPT.L.TA', 'NAWI.TA', 'NTGR.TA', 'NTO.TA', 'NTML.TA', 'NERZ-M.TA', 'NXTG.TA', 'NXTM.TA', 'NXGN-M.TA', 'NICE.TA', 'NISA.TA', 'NSTR.TA', 'NVMI.TA', 'NVLG.TA', 'ORTC.TA', 'ONE.TA', 'OPAL.TA', 'OPCE.TA', 'OPK.TA', 'OBAS.TA', 'ORAD.TA', 'ORMP.TA', 'ORBI.TA', 'ORIN.TA', 'ORA.TA', 'ORON.TA', 'OVRS.TA', 'PCBT.TA', 'PLTF.TA', 'PLRM.TA', 'PNAX.TA', 'PTNR.TA', 'PAYT.TA', 'PZOL.TA', 'PEN.TA', 'PFLT.TA', 'PERI.TA', 'PRGO.TA', 'PTCH.TA', 'PTX.TA', 'PMCN.TA', 'PHOE.TA', 'PLSN.TA', 'PLCR.TA', 'PPIL-M.TA', 'PLAZ-L.TA', 'PSTI.TA', 'POLI.TA', 'PIU.TA', 'POLY.TA', 'PWFL.TA', 'PRSK.TA', 'PRTC.TA', 'PTBL.TA', 'PLX.TA', 'QLTU.TA', 'QNCO.TA', 'RLCO.TA', 'RMN.TA', 'RMLI.TA', 'RANI.TA', 'RPAC.TA', 'RATI.L.TA', 'RTPT.L.TA', 'RAVD.TA', 'RVL.TA', 'RIT1.TA', 'AZRT.TA', 'REKA.TA', 'RIMO.TA', 'ROBO.TA', 'RTEN.L.TA', 'ROTS.TA', 'RSEL.TA', 'SRAC.TA', 'SFET.TA', 'SANO1.TA', 'SPNS.TA', 'SRFT.TA', 'STCM.TA', 'SAVR.TA', 'SHNP.TA', 'SCOP.TA', 'SEMG.TA', 'SLARL.TA', 'SHGR.TA', 'SALG.TA', 'SHAN.TA', 'SPEN.TA', 'SEFA.TA', 'SMNIN.TA', 'SKBN.TA', 'SHOM.TA', 'SAE.TA', 'SKLN.TA', 'SLGN.TA', 'SMTO.TA', 'SCC.TA', 'SPRG.TA', 'SPNTC.TA', 'STG.TA', 'STRS.TA', 'SMT.TA', 'SNFL.TA', 'SNCM.TA', 'SPGE.TA', 'SNEL.TA', 'TDGN-L.TA', 'TDRN.TA', 'TALD.TA', 'TMRP.TA', 'TASE.TA', 'TATT.TA', 'TAYA.TA', 'TNPV.TA', 'TEDE.TA', 'TFRLF.TA', 'TLRD.TA', 'TLSY.TA', 'TUZA.TA', 'TEVA.TA', 'TIGBUR.TA', 'TKUN.TA', 'TTAM.TA', 'TGTR.TA', 'TOPS.TA', 'TSEM.TA', 'TREN.TA', 'UNCR.TA', 'UNCT.L.TA', 'UNON.TA', 'UNIT.TA', 'UNVO.TA', 'UTRN.TA', 'VCTR.TA', 'VILR.TA', 'VISN.TA', 'VTLC-M.TA', 'VTNA.TA', 'VNTZ-M.TA', 'WSMK.TA', 'WTS.TA', 'WILC.TA', 'WLFD.TA', 'XENA.TA', 'XTLB.TA', 'YAAC.TA', 'YBOX.TA', 'YHNF.TA', 'ZNKL.TA', 'ZMH.TA', 'ZUR.TA']

symbols = symbols_snp500 + symbols_nasdaq100 + symbols_russel1000
symbols = list(set(symbols))

if TASE_MODE: symbols = symbols_tase
print('SSS Symbols to Scan: {}'.format(symbols))

# Temporary for test:
# symbols = ['ALMA.TA', 'SHOM.TA', 'BR', 'GDI', 'LOGM', 'WRK', 'EBAY', 'RSPP', 'FB', 'AL', 'INTC', 'AES', 'MMM', 'ADBE', 'MS']

rows          = []
rows_no_div   = []
rows_only_div = []

rows.append(         ["Ticker", "Name", "sss_value", "ssss_value", "ssse_value", "EV/R", "profit_margin", "forward_eps", "trailing_eps", "price_to_book", "shares_outstanding", "net_income_to_common_shareholders", "nitcsh_div_shares_outstanding", "employees", "nitcsh_div_num_employees", "earnings_quarterly_growth", "price_to_earnings_to_growth_ratio", "last_dividend_0", "last_dividend_1", "last_dividend_2", "last_dividend_3" ])
rows_no_div.append(  ["Ticker", "Name", "sss_value", "ssss_value", "ssse_value", "EV/R", "profit_margin", "forward_eps", "trailing_eps", "price_to_book", "shares_outstanding", "net_income_to_common_shareholders", "nitcsh_div_shares_outstanding", "employees", "nitcsh_div_num_employees", "earnings_quarterly_growth", "price_to_earnings_to_growth_ratio", "last_dividend_0", "last_dividend_1", "last_dividend_2", "last_dividend_3" ])
rows_only_div.append(["Ticker", "Name", "sss_value", "ssss_value", "ssse_value", "EV/R", "profit_margin", "forward_eps", "trailing_eps", "price_to_book", "shares_outstanding", "net_income_to_common_shareholders", "nitcsh_div_shares_outstanding", "employees", "nitcsh_div_num_employees", "earnings_quarterly_growth", "price_to_earnings_to_growth_ratio", "last_dividend_0", "last_dividend_1", "last_dividend_2", "last_dividend_3" ])
iteration = 0
for symb in symbols:
    iteration += 1
    print('Checking {:6} ({:4}/{:4}): '.format(symb,iteration,len(symbols)), end='')
    symbol = yf.Ticker(symb)
    try:
        info = symbol.get_info()

        if 'quoteType' in info and info['quoteType'] == MUTUALFUND:
            print('Mutual Fund: Skip')
            continue  # Not interested in those and they lack all the below info[] properties so nothing to do with them anyways

        if 'fullTimeEmployees' in info: num_employees = info['fullTimeEmployees']
        else                          : num_employees = NUM_EMPLOYEES_UNKNOWN

        # Special exception for Intel (INTC) - Bug in Yahoo Finance:
        if symb == 'INTC' and num_employees < 1000:
            num_employees *= 1000

        if 'shortName' in info: short_name = info['shortName']
        else:                   short_name = 'None'

        # https://www.investopedia.com/terms/e/ev-revenue-multiple.asp
        if 'enterpriseToRevenue' in info:
            evr = info['enterpriseToRevenue']
        else:
            evr = EVR_UNKNOWN

        if 'profitMargins'       in info: profit_margin = info['profitMargins']
        else                            : profit_margin = PROFIT_MARGIN_UNKNOWN

        if 'forwardEps' in info:
            forward_eps = info['forwardEps']
        else:
            forward_eps = 0

        if 'trailingEps' in info:
            trailing_eps = info['trailingEps']
        else:
            trailing_eps = 0

        if 'trailingPE' in info: trailing_pe = info['trailingPE'] # https://www.investopedia.com/terms/t/trailingpe.asp
        else:
            if evr == EVR_UNKNOWN:
                print('skipping since trailing_peand evr are unknown')
                continue

        if evr == EVR_UNKNOWN:
            evr = trailing_pe

        price_to_book                     = info['priceToBook']
        earnings_quarterly_growth         = info['earningsQuarterlyGrowth']
        price_to_earnings_to_growth_ratio = info['pegRatio']
        shares_outstanding                = info['sharesOutstanding']

        if shares_outstanding is None: shares_outstanding = SHARES_OUTSTANDING_UNKNOWN

        net_income_to_common_shareholders = info['netIncomeToCommon']

        if evr is None: evr = EVR_UNKNOWN
        if evr != EVR_UNKNOWN and (evr < 0 or evr > 15 + 25*TASE_MODE):
            print('skipping evr: {}'.format(evr))
            continue

        if profit_margin is None: profit_margin = PROFIT_MARGIN_UNKNOWN
        if profit_margin < PROFIT_MARGIN_LIMIT-TASE_PROFIT_MARGIN*TASE_MODE or profit_margin <= 0:
            if not TASE_MODE:
                print('skipping profit_margin: {}'.format(profit_margin))
                continue

        if trailing_eps is None: trailing_eps = 0

        if trailing_eps                      <    0               :
            print('skipping trailing_eps: {}'.format(trailing_eps))
            continue

        if price_to_book is None: price_to_book = 0

        if earnings_quarterly_growth is None: earnings_quarterly_growth = 0
        if earnings_quarterly_growth         <    0               :
            print('skipping earnings_quarterly_growth: {}'.format(earnings_quarterly_growth))
            continue

        if price_to_earnings_to_growth_ratio is None: price_to_earnings_to_growth_ratio = UNKNOWN_PEG2R
        if price_to_earnings_to_growth_ratio <    0               :
            print('skipping price_to_earnings_to_growth_ratio: {}'.format(price_to_earnings_to_growth_ratio))
            continue

        if net_income_to_common_shareholders is None: net_income_to_common_shareholders = 0
        if net_income_to_common_shareholders <    0               :
            print('skipping net_income_to_common_shareholders: {}'.format(net_income_to_common_shareholders))
            continue

        nitcsh_div_shares_outstanding     = round(float(net_income_to_common_shareholders)/float(shares_outstanding),2)
        nitcsh_div_num_employees          = round(float(net_income_to_common_shareholders)/float(num_employees),     2)

        sss_value  = evr
        ssss_value = price_to_earnings_to_growth_ratio
        ssse_value = profit_margin

        print('Name: {}, sss_value: {}, ssss_value: {}, ssse_value: {}, EV/R: {}, profit_margin: {}, forward_eps: {}, trailing_eps: {}, price_to_book: {}, shares_outstanding: {}, net_income_to_common_shareholders: {}, nitcsh_div_shares_outstanding: {}, # employees: {}, nitcsh_div_num_employees: {}, earnings_quarterly_growth: {}, price_to_earnings_to_growth_ratio: {}'.format(short_name, sss_value, ssss_value, ssse_value, evr, profit_margin, forward_eps, trailing_eps, price_to_book, shares_outstanding, net_income_to_common_shareholders, nitcsh_div_shares_outstanding, num_employees, nitcsh_div_num_employees, earnings_quarterly_growth, price_to_earnings_to_growth_ratio))

    except Exception as e: # More information is output when exception is used instead of Exception
        print("Exception in info: {}".format(e))
        if CONTINUE_UPON_INFO_EXCEPTION:
            continue
        num_employees                          = 0
        short_name                             = 0
        evr                                    = 0
        profit_margin                          = 0
        forward_eps                            = 0
        trailing_eps                           = 0
        price_to_book                          = 0
        earnings_quarterly_growth              = 0
        price_to_earnings_to_growth_ratio      = 0
        shares_outstanding                     = 0
        net_income_to_common_shareholders      = 0
        nitcsh_div_shares_outstanding          = 0
        nitcsh_div_num_employees               = 0
        sss_value                              = 0
        ssss_value                             = 0
        ssse_value                             = 0
        trailing_pe                            = 0
    try:
        last_4_dividends = symbol.dividends[-4:]
        print('last_4_dividends list: {}, {}, {}, {}'.format(last_4_dividends[0],last_4_dividends[1],last_4_dividends[2],last_4_dividends[3]))
        dividends_exist = True
    except:
        last_4_dividends = [0,0,0,0]
        print("Added to No Dividends Lists")
        dividends_exist = False
    rows.append([             symb, short_name, sss_value, ssss_value, ssse_value, evr, profit_margin, forward_eps, trailing_eps, price_to_book, shares_outstanding, net_income_to_common_shareholders, nitcsh_div_shares_outstanding, num_employees, nitcsh_div_num_employees, earnings_quarterly_growth, price_to_earnings_to_growth_ratio, last_4_dividends[0], last_4_dividends[1], last_4_dividends[2], last_4_dividends[3]])

    if dividends_exist:
        rows_only_div.append([symb, short_name, sss_value, ssss_value, ssse_value, evr, profit_margin, forward_eps, trailing_eps, price_to_book, shares_outstanding, net_income_to_common_shareholders, nitcsh_div_shares_outstanding, num_employees, nitcsh_div_num_employees, earnings_quarterly_growth, price_to_earnings_to_growth_ratio, last_4_dividends[0], last_4_dividends[1], last_4_dividends[2], last_4_dividends[3]])
    else:
        rows_no_div.append(  [symb, short_name, sss_value, ssss_value, ssse_value, evr, profit_margin, forward_eps, trailing_eps, price_to_book, shares_outstanding, net_income_to_common_shareholders, nitcsh_div_shares_outstanding, num_employees, nitcsh_div_num_employees, earnings_quarterly_growth, price_to_earnings_to_growth_ratio, last_4_dividends[0], last_4_dividends[1], last_4_dividends[2], last_4_dividends[3]])

    print('\n')

# Now, Sort the rows using the sss_value and ssse_value formulas: [1:] skips the 1st title row
sorted_list_sss           = sorted(rows[1:],          key=lambda row:          row[2],          reverse=False)  # Sort by sss_value  -> The lower  - the more attractive
sorted_list_ssss          = sorted(rows[1:],          key=lambda row:          row[3],          reverse=False)  # Sort by ssss_value -> The lower  - the more attractive
sorted_list_ssse          = sorted(rows[1:],          key=lambda row:          row[4],          reverse=True )  # Sort by ssse_value -> The higher - the more attractive
sorted_list_sss_no_div    = sorted(rows_no_div[1:],   key=lambda row_no_div:   row_no_div[2],   reverse=False)  # Sort by sss_value  -> The lower  - the more attractive
sorted_list_ssss_no_div   = sorted(rows_no_div[1:],   key=lambda row_no_div:   row_no_div[3],   reverse=False)  # Sort by ssss_value -> The lower  - the more attractive
sorted_list_ssse_no_div   = sorted(rows_no_div[1:],   key=lambda row_no_div:   row_no_div[4],   reverse=True )  # Sort by ssse_value -> The higher - the more attractive
sorted_list_sss_only_div  = sorted(rows_only_div[1:], key=lambda row_only_div: row_only_div[2], reverse=False)  # Sort by sss_value  -> The lower  - the more attractive
sorted_list_ssss_only_div = sorted(rows_only_div[1:], key=lambda row_only_div: row_only_div[3], reverse=False)  # Sort by ssss_value -> The lower  - the more attractive
sorted_list_ssse_only_div = sorted(rows_only_div[1:], key=lambda row_only_div: row_only_div[4], reverse=True )  # Sort by ssse_value -> The higher - the more attractive

sorted_list_sss.insert(          0, rows[0])
sorted_list_ssss.insert(         0, rows[0])
sorted_list_ssse.insert(         0, rows[0])
sorted_list_sss_no_div.insert(   0, rows_no_div[0])
sorted_list_ssss_no_div.insert(  0, rows_no_div[0])
sorted_list_ssse_no_div.insert(  0, rows_no_div[0])
sorted_list_sss_only_div.insert( 0, rows_only_div[0])
sorted_list_ssss_only_div.insert(0, rows_only_div[0])
sorted_list_ssse_only_div.insert(0, rows_only_div[0])

tase_str = ""
if TASE_MODE: tase_str = "_TASE"
date_and_time = time.strftime("%Y%m%d-%H%M%S{}".format(tase_str))

filename_sss_engine           = "{}/sss_engine.csv".format(date_and_time)
filename_ssss_engine          = "{}/ssss_engine.csv".format(date_and_time)
filename_ssse_engine          = "{}/ssse_engine.csv".format(date_and_time)
filename_sss_engine_no_div    = "{}/sss_engine_no_div.csv".format(date_and_time)
filename_ssss_engine_no_div   = "{}/ssss_engine_no_div.csv".format(date_and_time)
filename_ssse_engine_no_div   = "{}/ssse_engine_no_div.csv".format(date_and_time)
filename_sss_engine_only_div  = "{}/sss_engine_only_div.csv".format(date_and_time)
filename_ssss_engine_only_div = "{}/ssss_engine_only_div.csv".format(date_and_time)
filename_ssse_engine_only_div = "{}/ssse_engine_only_div.csv".format(date_and_time)

os.makedirs(os.path.dirname(filename_sss_engine),           exist_ok=True)
with open(filename_sss_engine,           mode='w', newline='') as sss_engine:
    writer_sss = csv.writer(sss_engine)
    writer_sss.writerows(sorted_list_sss)

os.makedirs(os.path.dirname(filename_ssss_engine),           exist_ok=True)
with open(filename_ssss_engine,          mode='w', newline='') as ssss_engine:
    writer_ssss = csv.writer(ssss_engine)
    writer_ssss.writerows(sorted_list_ssss)

os.makedirs(os.path.dirname(filename_ssse_engine),          exist_ok=True)
with open(filename_ssse_engine,          mode='w', newline='') as ssse_engine:
    writer_ssse = csv.writer(ssse_engine)
    writer_ssse.writerows(sorted_list_ssse)

os.makedirs(os.path.dirname(filename_sss_engine_no_div),    exist_ok=True)
with open(filename_sss_engine_no_div,    mode='w', newline='') as sss_engine:
    writer_sss = csv.writer(sss_engine)
    writer_sss.writerows(sorted_list_sss_no_div)

os.makedirs(os.path.dirname(filename_ssss_engine_no_div),    exist_ok=True)
with open(filename_ssss_engine_no_div,   mode='w', newline='') as ssss_engine:
    writer_ssss = csv.writer(ssss_engine)
    writer_ssss.writerows(sorted_list_ssss_no_div)

os.makedirs(os.path.dirname(filename_ssse_engine_no_div),   exist_ok=True)
with open(filename_ssse_engine_no_div,   mode='w', newline='') as ssse_engine:
    writer_ssse = csv.writer(ssse_engine)
    writer_ssse.writerows(sorted_list_ssse_no_div)

os.makedirs(os.path.dirname(filename_sss_engine_only_div),  exist_ok=True)
with open(filename_sss_engine_only_div,  mode='w', newline='') as sss_engine:
    writer_sss = csv.writer(sss_engine)
    writer_sss.writerows(sorted_list_sss_only_div)

os.makedirs(os.path.dirname(filename_ssss_engine_only_div),  exist_ok=True)
with open(filename_ssss_engine_only_div, mode='w', newline='') as ssss_engine:
    writer_ssss = csv.writer(ssss_engine)
    writer_ssss.writerows(sorted_list_ssss_only_div)

os.makedirs(os.path.dirname(filename_ssse_engine_only_div), exist_ok=True)
with open(filename_ssse_engine_only_div, mode='w', newline='') as ssse_engine:
    writer_ssse = csv.writer(ssse_engine)
    writer_ssse.writerows(sorted_list_ssse_only_div)
