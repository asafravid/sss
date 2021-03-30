#############################################################################
#
# Version 0.0.350 - Author: Asaf Ravid <asaf.rvd@gmail.com>
#
#    Stock Screener and Scanner - based on yfinance and investpy
#    Copyright (C) 2021  Asaf Ravid
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

import sss
import numpy as np
import csv
import os
import pdf_generator
import sss_diff


PDF_NUM_ENTRIES_IN_REPORT = 28

SCAN_MODE_TASE = 0  # Tel Aviv Stock Exchange
SCAN_MODE_NSR  = 1  # Nasdaq100 + S&P500 + Russel1000
SCAN_MODE_ALL  = 2  # All Nasdaq Stocks

TITLES = ["_תוצאות_סריקה_עבור_בורסת_תל_אביב", "_Scan_Results_for_Nasdaq100_SNP500_Russel1000", "_Scan_Results_for_All_Nasdaq_Stocks"]

#
# TODO: ASAFR: 1. Export Results to the SSS Google Sheet automatically

# Reuse:
# sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=0, num_threads=1,  market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit = 100.0, debt_to_equity_limit = 1000.0, min_enterprise_value_millions_usd=100, enterprise_value_to_revenue_limit=15, favor_technology_sector=4.5, generate_result_folders=1)

# Run Build DB Only: TASE
# =============================
# sss.sss_run(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=1, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=100000.0, debt_to_equity_limit=1000.0, min_enterprise_value_millions_usd=1, price_to_earnings_limit=4500, enterprise_value_to_revenue_limit=1500,  favor_sectors=['Technology', 'Real Estate'],        favor_sectors_by=[4.0, 0.75], generate_result_folders=1)

# Run Build DB Only: Nasdaq100+S&P500+Russel1000
# ==============================================
# sss.sss_run(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=0, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=2000.0,   debt_to_equity_limit=1000.0, min_enterprise_value_millions_usd=75, price_to_earnings_limit=6500, enterprise_value_to_revenue_limit=2500,  favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[3.5,  0.75], generate_result_folders=1)

# Run Build DB Only: All/Others
# =============================
# sss.sss_run(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=1, tase_mode=0, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=20000.0,  debt_to_equity_limit=1000.0, min_enterprise_value_millions_usd=5, price_to_earnings_limit=9000, enterprise_value_to_revenue_limit=3000, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[3.5, 0.75], generate_result_folders=1)

# Reuse Existing Already-Built DB All/Others:
# sss.sss_run(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, build_csv_db_only=0, build_csv_db=0, csv_db_path='Results/All/20210315-185230_Technology3.5_FinancialServices0.75_A_Bdb_nRes8877', read_united_states_input_symbols=1, tase_mode=0, num_threads=1,  market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit = 20000.0, debt_to_equity_limit = 1000.0, min_enterprise_value_millions_usd=5, enterprise_value_to_revenue_limit=1000, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[4.0, 0.75], generate_result_folders=1)


# Run Build DB Only: Custom Portfolio
# ===================================
# TASE:
# sss.sss_run(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=1, num_threads=1, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=20000.0, debt_to_equity_limit = 1000.0, min_enterprise_value_millions_usd=5, price_to_earnings_limit=9000, enterprise_value_to_revenue_limit=200, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[4.0, 0.75], generate_result_folders=1, custom_portfolio=['SONO.TA'])
# Nasdaq: TODO: ASAFR: Continue investigating the custom portfolio
# sss.sss_run(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=0, num_threads=5, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=20000.0, debt_to_equity_limit = 1000.0, min_enterprise_value_millions_usd=5, price_to_earnings_limit=9000, enterprise_value_to_revenue_limit=200, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[3.5, 0.75], generate_result_folders=1, custom_portfolio=['AAPL','ABBV','ACGL','ACN','ADBE','AFL','AGO','AKAM','AL','ALGN','ALL','ALLY','ALXN','AMAT','AMGN','APT','ARE','ATH','ATVI','AVB','AVGO','AZPN','BAC','BBY','BDN','BIO','BLK','BMRN','BOKF','BPOP','BRK.B','BTG','BTI','BWXT','BXP','CACC','CB','CDNS','CE','CGNX','CHKP','CI','CMCSA','COF','COO','COOP','CPB','CPRX','CROX','CSCO','CUZ','DAC','DFS','DG','DGX','DHI','DISH','DLB','DOX','DRE','EBAY','ELP','ES','ESGR','EXEL','EXR','FAST','FB','FCNCA','FCPT','FDUS','FF','FHN','FRC','FRO','FTV','GFI','GILD','GIS','GLPI','GNTX','GOOG','GOOGL','GPP','GRMN','GS','GTLS','HIW','HMLP','HOLX','HTH','HUN','HZNP','ICE','INTC','INVA','IRCP','JAZZ','JEF','JPM','KGC','KIM','KLAC','KNOP','LAKE','LEN','LH','LMT','LNG','LOPE','LRCX','MAS','MCO','MDLZ','MGM','MMM','MRK','MRVL','MS','MSFT','MU','MX','NBIX','NEM','NGG','NVEC','NVR','OHI','OLP','OMF','OPRA','ORAN','ORCL','OZK','PB','PBCT','PBFX','PEG','PG','PGR','PHM','PM','PNFP','QCOM','QDEL','QRVO','REGN','RGLD','RIO','SBNY','SCHW','SCI','SLM','SMFG','SNE','SRE','STT','STZ','SUPN','SWKS','TER','TGT','TLK','TMO','TRNO','TROW','TROX','TRP','TRQ','TRV','TXN','UHS','UI','USB','UTHR','VICI','VMW','VRSN','VRTX','VST','VZ','WAL','WMT','WPC','WPM','WTFC','YY'])


# Research Mode:
# ==============

# Ranges:
# EV:  the lower  the EV,  the more stocks in the result
# EVR: the Higher the EVR, the more stocks in the result
# PM:  the lower  the PM,  the more stocks in the result
#
# Percentiles:
# index   x        1         2        3  ...  n-1
# +----------------------------------------------------+
# |       x        |         |        |        |       |
# +----------------------------------------------------+
#
# In order to give a chance to all stocks fairly, always take the 1st element in the sorted list
def get_range(csv_db_path, column_name, num_sections, reverse, pop_1st_percentile_range=True):
    csv_db_filename = csv_db_path + '/db.csv'
    with open(csv_db_filename, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter=',')
        row_index = 0
        elements_list    = []
        percentile_range = []
        for row in reader:
            if row_index <= 1:  # first row is just a title of evr and pm, then a title of columns
                if row_index == 1:
                    if column_name in row:
                        column_index = row.index(column_name)
                        sss_index    = row.index('sss_value')
                row_index += 1
                continue
            else:
                if len(row[column_index]) > 0 and float(row[column_index]) > 0.0 and len(row[sss_index]) > 0 and float(row[sss_index]) < sss.BAD_SSS:
                    elements_list.append(float(row[column_index]))
    sorted_elements_list = sorted(list(set(elements_list)), reverse=reverse)
    percentile_step = (100.0/num_sections)
    percentile      = percentile_step
    percentile_range.insert(0, round(sorted_elements_list[0], sss.NUM_ROUND_DECIMALS))
    while percentile < 100:
        percentile_range.append(round(np.percentile(sorted_elements_list, percentile), sss.NUM_ROUND_DECIMALS))
        percentile += percentile_step
    percentile_range_sorted = sorted(percentile_range, reverse=reverse)
    if pop_1st_percentile_range:
        percentile_range_sorted.pop(1) # Since the 1st percentile and the 1st element usually give the same result, remove the 1st percentile step
    return percentile_range_sorted


def prepare_appearance_counters_dictionaries(csv_db_path, appearance_counter_dict_sss, appearance_counter_dict_ssss, appearance_counter_dict_sssss):
    csv_db_filename = csv_db_path + '/db.csv'
    try:
        with open(csv_db_filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                if row_index <= 1:  # first row is just a title of evr and pm, then a title of columns
                    if row_index == 1:
                        ticker_index         = row.index("Ticker")
                        name_index           = row.index("Name")
                        sector_index         = row.index("Sector")
                        sss_index            = row.index("sss_value")
                        ssss_index           = row.index("ssss_value")
                        sssss_index          = row.index("sssss_value")
                        previous_close_index = row.index("previous_close")
                    row_index += 1
                    continue
                else:
                    appearance_counter_dict_sss[  (row[ticker_index],row[name_index],row[sector_index],float(row[sss_index  ]),float(0 if row[previous_close_index] == '' else row[previous_close_index]))] = 0.0  # Symbol, Short Name, Sector, SSS   Value, previousClose
                    appearance_counter_dict_ssss[ (row[ticker_index],row[name_index],row[sector_index],float(row[ssss_index ]),float(0 if row[previous_close_index] == '' else row[previous_close_index]))] = 0.0  # Symbol, Short Name, Sector, SSSS  Value, previousClose
                    appearance_counter_dict_sssss[(row[ticker_index],row[name_index],row[sector_index],float(row[sssss_index]),float(0 if row[previous_close_index] == '' else row[previous_close_index]))] = 0.0  # Symbol, Short Name, Sector, SSSSS Value, previousClose
    except Exception as e:
        if print("              Exception in {}: {}".format(row, e)):
            pass


# |dim3 [ev 1,10,50,100,500]| = 5, |rows [evr 5,50]| = 2, |cols [pm 3,10,25,45]| = 4
#
# Contents are the number of results, per ev,evr,pm:
#
# [[9, 8, 7, 6],                     1,   9, 8, 7, 6                   |cols' = 1+|cols||
#  [5, 4, 3, 2]],                    1,   5, 4, 3, 2
#                                                                        1,   9, 8, 7, 6
# [[!, @, #, $],                     10,  !, @, #, $                     1,   5, 4, 3, 2
#  [%, ^, &, *]],                    10,  %, ^, &, *                     10,  !, @, #, $
#                                 \                                 \    10,  %, ^, &, *
# [[u, v, w, x],     ==============\ 50,  u, v, w, x   ==============\   50,  u, v, w, x |rows'=|dim3|*|rows||
#  [q, r, s, t]],    ==============/ 50,  q, r, s, t   ==============/   50,  q, r, s, t
#                                 /                                 /    100, a, b, c, d
# [[a, b, c, d],                     100, a, b, c, d                     100, e, f, g, h
#  [e, f, g, h]],                    100, e, f, g, h                     500, i, j, k, l
#                                                                        500, m, n, o, p
# [[i, j, k, l],                     500, i, j, k, l
#  [m, n, o, p]]                     500, m, n, o, p
#
def combine_multi_dim_to_table_3d(multi_dim, dim3, rows,cols):
    len_new_rows = len(dim3)*len(rows)
    len_new_cols = 1+len(cols)
    combined_rows_cols = np.zeros( (len_new_rows, len_new_cols), dtype=int )
    for new_row in range(len_new_rows):
        for new_col in range(len_new_cols):
            if new_col == 0:
                combined_rows_cols[new_row][new_col] = dim3[int(new_row/len(rows))]
            else:
                combined_rows_cols[new_row][new_col] = multi_dim[int(new_row/len(rows))][new_row%len(rows)][new_col-1]
    return combined_rows_cols


# now introduce the 4th dim:  |dim4 [evm a,b]| = 2, |dim3 [pe 1,10,50]| = 3, |rows| = 4, |cols| = 5
# ==========================
#
#  evm: a
#
#  |cols' = 1+|cols||
#
#    pe
#     1,  20.,  19.,  18.,  17.,  16.
#     1,  15.,  14.,  13.,  12.,  11.                                              |cols''| = 1+|cols'|
#     1,  10.,   9.,   8.,   7.,   6.
#     1,   5.,   4.,   3.,   2.,   1.                                       a,  1,  20.,  19.,  18.,  17.,  16.
#    10, 120., 119., 118., 117., 116.                                    \  a,  1,  15.,  14.,  13.,  12.,  11.
#    10, 115., 114., 113., 112., 111.                       ==============\ a,  1,  10.,   9.,   8.,   7.,   6.
#    10, 110., 109., 108., 107., 106. |rows'=|dim3|*|rows|| ==============/ a,  1,   5.,   4.,   3.,   2.,   1.
#    10, 105., 104., 103., 102., 101.                                    /  a, 10, 120., 119., 118., 117., 116.
#    50,   a.,   b.,   c.,   d.,   e.                                       a, 10, 115., 114., 113., 112., 111.
#    50,   f.,   g.,   h.,   i.,   j.                                       a, 10, 110., 109., 108., 107., 106.
#    50,   k.,   l.,   m.,   n.,   o.                                       a, 10, 105., 104., 103., 102., 101.
#    50,   p.,   q.,   r.,   s.,   t.                                       a, 50,   a.,   b.,   c.,   d.,   e.
#                                                                           a, 50,   f.,   g.,   h.,   i.,   j.
#                                                                           a, 50,   k.,   l.,   m.,   n.,   o.      |rows''=|dim4|*|rows'||
#  evm: b                                                                   a, 50,   p.,   q.,   r.,   s.,   t.
#                                                                           b,  1,  20_,  19_,  18_,  17_,  16_
#  |cols' = 1+|cols||                                                       b,  1,  15_,  14_,  13_,  12_,  11_
#                                                                           b,  1,  10_,   9_,   8_,   7_,   6_
#    pe                                                                     b,  1,   5_,   4_,   3_,   2_,   1_
#     1,  20_,  19_,  18_,  17_,  16_                                       b, 10, 120_, 119_, 118_, 117_, 116_
#     1,  15_,  14_,  13_,  12_,  11_                                       b, 10, 115_, 114_, 113_, 112_, 111_
#     1,  10_,   9_,   8_,   7_,   6_                                    \  b, 10, 110_, 109_, 108_, 107_, 106_
#     1,   5_,   4_,   3_,   2_,   1_                       ==============\ b, 10, 105_, 104_, 103_, 102_, 101_
#    10, 120_, 119_, 118_, 117_, 116_ |rows'=|dim3|*|rows|| ==============/ b, 50,   a_,   b_,   c_,   d_,   e_
#    10, 115_, 114_, 113_, 112_, 111_                                    /  b, 50,   f_,   g_,   h_,   i_,   j_
#    10, 110_, 109_, 108_, 107_, 106_                                       b, 50,   k_,   l_,   m_,   n_,   o_
#    10, 105_, 104_, 103_, 102_, 101_                                       b, 50,   p_,   q_,   r_,   s_,   t_
#    50,   a_,   b_,   c_,   d_,   e_
#    50,   f_,   g_,   h_,   i_,   j_
#    50,   k_,   l_,   m_,   n_,   o_
#    50,   p_,   q_,   r_,   s_,   t_
def combine_multi_dim_to_table_4d(multi_dim, dim4, dim3, rows,cols):
    len_new_rows = len(dim3)*len(rows)
    len_new_cols = 1+len(cols)

    # Now 4th Dim:            
    len_new4_rows = len(dim4)*len_new_rows
    len_new4_cols = 1+len_new_cols
    combined4_rows_cols = np.zeros( (len_new4_rows, len_new4_cols), dtype=float )
    for new_row in range(len_new4_rows):
        for new_col in range(len_new4_cols):
            if   new_col == 0:  # dim4
                combined4_rows_cols[new_row][new_col] =      dim4[int(new_row/len_new_rows)]
            elif new_col == 1:  # dim3
                combined4_rows_cols[new_row][new_col] =                                 dim3[(int(new_row/len(rows))) % len(dim3)] # dim2 (rows)
            else:
                combined4_rows_cols[new_row][new_col] = multi_dim[int(new_row/len_new_rows)][(int(new_row/len(rows))) % len(dim3)][new_row%len(rows)][new_col-2]

    return combined4_rows_cols


def research_db(sectors_list, sectors_filter_out, countries_list, countries_filter_out, evr_range, pe_range, pm_range, ev_millions_range, csv_db_path, read_united_states_input_symbols, scan_mode, generate_result_folders, appearance_counter_min, appearance_counter_max, favor_sectors, favor_sectors_by,
                newer_path, older_path, db_exists_in_both_folders, diff_only_recommendation, movement_threshold, newer_res_ranges, older_res_ranges, res_length):
    if scan_mode == SCAN_MODE_TASE:
        tase_mode = 1
    else:
        tase_mode = 0

    appearance_counter_dict_sss   = {}
    appearance_counter_dict_ssss  = {}
    appearance_counter_dict_sssss = {}
    prepare_appearance_counters_dictionaries(csv_db_path, appearance_counter_dict_sss, appearance_counter_dict_ssss, appearance_counter_dict_sssss)
    ev_millions_range_len = len(ev_millions_range)
    pe_range_len          = len(pe_range)
    evr_range_len         = len(evr_range)
    pm_range_len          = len(pm_range)
    research_rows_sss   = np.zeros( (ev_millions_range_len, pe_range_len, evr_range_len, pm_range_len), dtype=int )
    research_rows_ssss  = np.zeros( (ev_millions_range_len, pe_range_len, evr_range_len, pm_range_len), dtype=int )
    research_rows_sssss = np.zeros( (ev_millions_range_len, pe_range_len, evr_range_len, pm_range_len), dtype=int )
    for ev_millions_index, ev_millions_limit                 in enumerate(ev_millions_range):
        for pe_index, price_to_earnings_limit                in enumerate(pe_range):
            for evr_index, enterprise_value_to_revenue_limit in enumerate(evr_range):
                for pm_index, profit_margin_limit            in enumerate(pm_range):                                                            # TODO: ASAFR: Below - some magic numbers on ev_to_cfo_ration etc 100.0 and 1000.0 - make order and defines/constants/multi_dim here
                    num_results_for_ev_pe_evr_and_pm = sss.sss_run(sectors_list=sectors_list, sectors_filter_out=sectors_filter_out, countries_list=countries_list, countries_filter_out=countries_filter_out, build_csv_db_only=0, build_csv_db=0, csv_db_path=csv_db_path, read_united_states_input_symbols=read_united_states_input_symbols, tase_mode=tase_mode, num_threads=1, market_cap_included=1, use_investpy=0, research_mode=1, profit_margin_limit=float(profit_margin_limit)/100.0, min_enterprise_value_millions_usd=ev_millions_limit, ev_to_cfo_ratio_limit = 100.0, debt_to_equity_limit = 1000.0, price_to_earnings_limit=price_to_earnings_limit, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_sectors=favor_sectors, favor_sectors_by=favor_sectors_by, generate_result_folders=generate_result_folders, appearance_counter_dict_sss=appearance_counter_dict_sss, appearance_counter_dict_ssss=appearance_counter_dict_ssss, appearance_counter_dict_sssss=appearance_counter_dict_sssss, appearance_counter_min=appearance_counter_min, appearance_counter_max=appearance_counter_max)
                    if num_results_for_ev_pe_evr_and_pm < appearance_counter_min:
                        break  # already lower than appearance_counter_min results. With higher profit margin limit there will always be less results -> save running time by breaking
                    research_rows_sss  [ev_millions_index][pe_index][evr_index][pm_index] = int(num_results_for_ev_pe_evr_and_pm)
                    research_rows_ssss [ev_millions_index][pe_index][evr_index][pm_index] = int(num_results_for_ev_pe_evr_and_pm)
                    research_rows_sssss[ev_millions_index][pe_index][evr_index][pm_index] = int(num_results_for_ev_pe_evr_and_pm)
                    print('ev_millions_limit {:6} | price_to_earnings_limit {:8} | row {:3} -> (enterprise_value_to_revenue_limit {:8}) | col {:3} -> (profit_margin_limit {:7}%): num_results_for_ev_pe_evr_and_pm = {}'.format(ev_millions_limit, price_to_earnings_limit, evr_index, enterprise_value_to_revenue_limit, pm_index, profit_margin_limit, num_results_for_ev_pe_evr_and_pm))
    results_filename    = 'results_evm{}-{}_pe{}-{}_evr{}-{}_pm{}-{}.csv'.format(ev_millions_range[0],ev_millions_range[-1],pe_range[0],pe_range[-1],evr_range[0],evr_range[-1],pm_range[0],pm_range[-1])

    mesh_combined = combine_multi_dim_to_table_4d(multi_dim=research_rows_sss, dim4=ev_millions_range, dim3=pe_range, rows=evr_range,cols=pm_range)

    np.savetxt(csv_db_path+'/'+results_filename,  mesh_combined, fmt='%f', delimiter=',')
    title_row = pm_range             # column 3 and onwards
    title_row.insert(0, 'evr / pm')  # column 2
    title_row.insert(0, 'pe')        # column 1
    title_row.insert(0, 'ev')        # column 0
    ev_pe_evr_rows_pm_cols_filenames_list = [csv_db_path+'/'+results_filename]
    # Read Results, and add row and col axis:
    for filename in ev_pe_evr_rows_pm_cols_filenames_list:
        ev_pe_evr_rows_pm_cols = [title_row]
        with open(filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0 # title + len(ev_millions_range)*len(evr_range)
            for row in reader:
                ev_pe_evr_rows_pm_cols.append(row)
                row.insert(2, evr_range[ int(row_index)%len(evr_range) ])  # column 2 is evr repetitively cyclic
                row_index += 1
    for index in range(len(ev_pe_evr_rows_pm_cols_filenames_list)):
        row_col_csv_filename = ev_pe_evr_rows_pm_cols_filenames_list[index].replace('.csv','_with_labels.csv')
        os.makedirs(os.path.dirname(row_col_csv_filename), exist_ok=True)
        with open(row_col_csv_filename, mode='w', newline='') as engine:
            writer = csv.writer(engine)
            writer.writerows(ev_pe_evr_rows_pm_cols)

    sorted_appearance_counter_dict_sss          = {k: v for k, v in sorted(appearance_counter_dict_sss.items(),   key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict_sss   = {k: v for k, v in sorted_appearance_counter_dict_sss.items()    if v > 0.0}

    sorted_appearance_counter_dict_ssss         = {k: v for k, v in sorted(appearance_counter_dict_ssss.items(),  key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict_ssss  = {k: v for k, v in sorted_appearance_counter_dict_ssss.items()   if v > 0.0}

    sorted_appearance_counter_dict_sssss        = {k: v for k, v in sorted(appearance_counter_dict_sssss.items(), key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict_sssss = {k: v for k, v in sorted_appearance_counter_dict_sssss.items()  if v > 0.0}

    recommendation_list_filename_sss   = csv_db_path+'/res_sss_'  +results_filename.replace('results_','')
    recommendation_list_filename_ssss  = csv_db_path+'/res_ssss_' +results_filename.replace('results_','')
    recommendation_list_filename_sssss = csv_db_path+'/res_sssss_'+results_filename.replace('results_','')


    with open(recommendation_list_filename_sss, 'w') as f:
        f.write("Ticker,Name,Sector,sss_value,close,appearance_counter\n")
        for key in result_sorted_appearance_counter_dict_sss.keys():
            #                              Ticker,    Name,                    Sector S      Close        appearance_counter
            f.write("%s,%s,%s,%s,%s,%s\n"%(key[0],str(key[1]).replace(',',' '),key[2],key[3],key[4],round(result_sorted_appearance_counter_dict_sss[  key],4)))

    with open(recommendation_list_filename_ssss, 'w') as f:
        f.write("Ticker,Name,Sector,ssss_value,close,appearance_counter\n")
        for key in result_sorted_appearance_counter_dict_ssss.keys():
            f.write("%s,%s,%s,%s,%s,%s\n"%(key[0],str(key[1]).replace(',',' '),key[2],key[3],key[4],round(result_sorted_appearance_counter_dict_ssss[ key],4)))

    with open(recommendation_list_filename_sssss, 'w') as f:
        f.write("Ticker,Name,Sector,sssss_value,close,appearance_counter\n")
        for key in result_sorted_appearance_counter_dict_sssss.keys():
            f.write("%s,%s,%s,%s,%s,%s\n"%(key[0],str(key[1]).replace(',',' '),key[2],key[3],key[4],round(result_sorted_appearance_counter_dict_sssss[key],4)))

    if older_path is not None:
        diff_lists = sss_diff.run(newer_path=newer_path, older_path=older_path, db_exists_in_both_folders=db_exists_in_both_folders, diff_only_recommendation=diff_only_recommendation, movement_threshold=movement_threshold, newer_res_ranges=newer_res_ranges, older_res_ranges=older_res_ranges, res_length=res_length, consider_as_new_from=PDF_NUM_ENTRIES_IN_REPORT)

        #                                                                                                  0:15 is date and time
        pdf_generator.csv_to_pdf(csv_filename=recommendation_list_filename_sss,   csv_db_path=csv_db_path, data_time_str=recommendation_list_filename_sss.replace(  'Results','').replace('Tase','').replace('All','').replace('Custom','').replace('/','')[0:15], title=TITLES[scan_mode].replace('_',' '),         limit_num_rows=PDF_NUM_ENTRIES_IN_REPORT, diff_list=diff_lists[0], tase_mode=tase_mode)
        pdf_generator.csv_to_pdf(csv_filename=recommendation_list_filename_ssss,  csv_db_path=None,        data_time_str=recommendation_list_filename_ssss.replace( 'Results','').replace('Tase','').replace('All','').replace('Custom','').replace('/','')[0:15], title=TITLES[scan_mode].replace('_',' ')+'ssss' , limit_num_rows=PDF_NUM_ENTRIES_IN_REPORT, diff_list=diff_lists[0], tase_mode=tase_mode)
        pdf_generator.csv_to_pdf(csv_filename=recommendation_list_filename_sssss, csv_db_path=None,        data_time_str=recommendation_list_filename_sssss.replace('Results','').replace('Tase','').replace('All','').replace('Custom','').replace('/','')[0:15], title=TITLES[scan_mode].replace('_',' ')+'sssss', limit_num_rows=PDF_NUM_ENTRIES_IN_REPORT, diff_list=diff_lists[0], tase_mode=tase_mode)


# TASE:
# =====
# old_run = 'Results/Tase/20210326-005808_Tase_Technology4.0_RealEstate0.75_Bdb_nRes468'
# new_run = 'Results/Tase/20210330-140034_Tase_Technology4.0_RealEstate0.75_Bdb_nRes248'
# ev_range_tase          = get_range(csv_db_path=new_run, column_name='enterprise_value',        num_sections=4, reverse=0, pop_1st_percentile_range=True)
# pe_range_tase          = get_range(csv_db_path=new_run, column_name='pe_effective',            num_sections=7, reverse=1, pop_1st_percentile_range=True)
# evr_range_tase         = get_range(csv_db_path=new_run, column_name='evr_effective',           num_sections=7, reverse=1, pop_1st_percentile_range=True)
# pm_ratios_range_tase   = get_range(csv_db_path=new_run, column_name='effective_profit_margin', num_sections=7, reverse=0, pop_1st_percentile_range=True)
#
# ev_millions_range_tase = [int(  ev/1000000                       ) for ev in ev_range_tase       ]
# pm_range_tase          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_tase]
#
# research_db(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, ev_millions_range=ev_millions_range_tase, pe_range=pe_range_tase, evr_range=evr_range_tase, pm_range=pm_range_tase,   csv_db_path=new_run,   read_united_states_input_symbols=0, scan_mode=SCAN_MODE_TASE, generate_result_folders=0, appearance_counter_min=PDF_NUM_ENTRIES_IN_REPORT/4, appearance_counter_max=400, favor_sectors=['Technology', 'Real Estate'], favor_sectors_by=[4.0, 0.75],
#             newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, movement_threshold=0, newer_res_ranges=[ev_millions_range_tase[0],ev_millions_range_tase[-1],pe_range_tase[0],pe_range_tase[-1],evr_range_tase[0],evr_range_tase[-1],pm_range_tase[0],pm_range_tase[-1]], older_res_ranges=[30,4003, 2468.5,8.04714, 105.218,0.869,0.431,45.688], res_length=80)

# Generate TASE:
# research_db(evr_range=[8,8],  pm_range=[10,10], ev_millions_range=[5,5], csv_db_path=new_run,   read_united_states_input_symbols=0, scan_mode=SCAN_MODE_TASE, generate_result_folders=1, appearance_counter_min=1, appearance_counter_max=250, favor_technology_sector=4.5,
#             newer_path=new_run, older_path=None, db_exists_in_both_folders=1, diff_only_recommendation=1, movement_threshold=0, newer_res_ranges=[5,1,54,1,50], older_res_ranges=[5,1,54,1,50], res_length=80)



# NASDAQ100+S&P500+RUSSEL1000:
# ============================
old_run = 'Results/Nsr/20210328-112509_Technology3.5_FinancialServices0.75_Bdb_nRes1084'
new_run = 'Results/Nsr/20210330-143820_Technology3.5_FinancialServices0.75_Bdb_nRes773'
ev_range_nsr          = get_range(csv_db_path=new_run, column_name='enterprise_value',        num_sections=5, reverse=0)
pe_range_nsr          = get_range(csv_db_path=new_run, column_name='pe_effective',            num_sections=8, reverse=1)
evr_range_nsr         = get_range(csv_db_path=new_run, column_name='evr_effective',           num_sections=8, reverse=1)
pm_ratios_range_nsr   = get_range(csv_db_path=new_run, column_name='effective_profit_margin', num_sections=8, reverse=0)

ev_millions_range_nsr = [int(  ev/1000000                       ) for ev in ev_range_nsr       ]
pm_range_nsr          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_nsr]

research_db(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, ev_millions_range=ev_millions_range_nsr, pe_range=pe_range_nsr, evr_range=evr_range_nsr, pm_range=pm_range_nsr,  csv_db_path=new_run,   read_united_states_input_symbols=0, scan_mode=SCAN_MODE_NSR, generate_result_folders=0, appearance_counter_min=PDF_NUM_ENTRIES_IN_REPORT/4, appearance_counter_max=850, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[3.5, 0.75],
            newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, movement_threshold=0, newer_res_ranges=[ev_millions_range_nsr[0],ev_millions_range_nsr[-1],pe_range_nsr[0],pe_range_nsr[-1],evr_range_nsr[0],evr_range_nsr[-1],pm_range_nsr[0],pm_range_nsr[-1]], older_res_ranges=[175,50892,7034.32895,11.92977,667.445,1.33512,0.051,72.834], res_length=80)

# Generate:
# research_db(evr_range=[24,24],  pm_range=[31,31], ev_millions_range=[100,100], csv_db_path=new_run,   read_united_states_input_symbols=0, tase_mode=0, generate_result_folders=1, appearance_counter_min=15, appearance_counter_max=45, favor_technology_sector=4.5)

# ALL:
# ====
# old_run = 'Results/All/20210328-182949_Technology3.5_FinancialServices0.75_A_Bdb_nRes8891'
# new_run = 'Results/All/20210330-064940_Technology3.5_FinancialServices0.75_A_Bdb_nRes8898'
# ev_range_all          = get_range(csv_db_path=new_run, column_name='enterprise_value',         num_sections=5, reverse=0)
# pe_range_all          = get_range(csv_db_path=new_run, column_name='pe_effective',             num_sections=9, reverse=1)
# evr_range_all         = get_range(csv_db_path=new_run, column_name='evr_effective',            num_sections=9, reverse=1)
# pm_ratios_range_all   = get_range(csv_db_path=new_run, column_name='effective_profit_margin',  num_sections=9, reverse=0)
#
# ev_millions_range_all = [int(  ev/1000000                       ) for ev in ev_range_all       ]
# pm_range_all          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_all]
#
# research_db(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, ev_millions_range=ev_millions_range_all, pe_range=pe_range_all, evr_range=evr_range_all, pm_range=pm_range_all, csv_db_path=new_run, read_united_states_input_symbols=1, scan_mode=SCAN_MODE_ALL, generate_result_folders=0, appearance_counter_min=PDF_NUM_ENTRIES_IN_REPORT/4, appearance_counter_max=1500, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[3.5, 0.75],
#             newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, movement_threshold=0, newer_res_ranges=[ev_millions_range_all[0],ev_millions_range_all[-1],pe_range_all[0],pe_range_all[-1],evr_range_all[0],evr_range_all[-1],pm_range_all[0],pm_range_all[-1]], older_res_ranges=[2,17537, 14429.61818,9.39113, 10571.204,0.91944, 0.008,113.362], res_length=80)

# Generate ALL:
# research_db(sectors_list=[], sectors_filter_out=0, evr_range=[30,30], pm_range=[40,40], ev_millions_range=[100,100], csv_db_path=new_run,  read_united_states_input_symbols=1, tase_mode=0, generate_result_folders=1, appearance_counter_min=5, appearance_counter_max=75, favor_technology_sector=4.5)


# Custom:
# =======
# old_run = 'Results/All/20210320-160910_Technology3.5_FinancialServices0.5_A_Bdb_nRes8908'
# new_run = 'Results/All/20210325-210925_Technology4.0_FinancialServices0.5_Bdb_nRes181_Custom'
# ev_range_all          = get_range(csv_db_path=new_run, column_name='enterprise_value',         num_sections=2, reverse=0, pop_1st_percentile_range=False)
# pe_range_all          = get_range(csv_db_path=new_run, column_name='pe_effective',             num_sections=3, reverse=1)
# evr_range_all         = get_range(csv_db_path=new_run, column_name='evr_effective',            num_sections=3, reverse=1)
# pm_ratios_range_all   = get_range(csv_db_path=new_run, column_name='effective_profit_margin',  num_sections=3, reverse=0)
#
# ev_millions_range_all = [int(  ev/1000000                       ) for ev in ev_range_all       ]
# pm_range_all          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_all]
#
# research_db(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, ev_millions_range=ev_millions_range_all, pe_range=pe_range_all, evr_range=evr_range_all, pm_range=pm_range_all, csv_db_path=new_run, read_united_states_input_symbols=1, scan_mode=SCAN_MODE_ALL, generate_result_folders=0, appearance_counter_min=PDF_NUM_ENTRIES_IN_REPORT/4, appearance_counter_max=1500, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[4.0, 0.5],
#             newer_path=new_run, older_path=None, db_exists_in_both_folders=1, diff_only_recommendation=1, movement_threshold=0, newer_res_ranges=[ev_millions_range_all[0],ev_millions_range_all[-1],pe_range_all[0],pe_range_all[-1],evr_range_all[0],evr_range_all[-1],pm_range_all[0],pm_range_all[-1]], older_res_ranges=[0,17170, 100,1, 8260.35271,0.92414, 0.047,1224.42], res_length=80)
