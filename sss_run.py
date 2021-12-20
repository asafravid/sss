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

import time
import numpy as np
import csv
import os
import pdf_generator
from glob import glob

import sss
import sss_config # This is the configuration file for the run modes
import sss_diff
import cProfile

DB_FILENAMES = ['sss_engine.csv', 'sss_engine_normalized.csv']  # 'db.csv' -> but faster with 9so hence use) sss_engine.csv

# TODO: ASAFR: 1. read_csv in pandas, and then .describe() and .quantiles() will provide mean, std and percentiles for all the columns (sss_engine.csv and/or db.csv)
#              2. Calculate the angle (dericative) of the Profit margin change over years and quarters and apply a bonus relative to the slope
#              3. Add a column with position number or just #. Symbol
#              4. Add a a Removed Column reports!
PDF_NUM_ENTRIES_IN_REPORT       = 49
RESEARCH_MODE_MIN_ENTRIES_LIMIT = 7

SCAN_MODE_TASE   = 0  # Tel Aviv Stock Exchange
SCAN_MODE_NSR    = 1  # Nasdaq100 + S&P500 + Russel1000
SCAN_MODE_ALL    = 2  # All Nasdaq Stocks
SCAN_MODE_SIX    = 3  # All Swiss Stocks
SCAN_MODE_ST     = 4  # All Swedish (Stockholm) Stocks
SCAN_MODE_CUSTOM = 5  # All Swedish (Stockholm) Stocks

TITLES = ["_תוצאות_סריקה_עבור_בורסת_תל_אביב", "_Scan_Results_for_Nasdaq100_SNP500_Russel1000", "_Scan_Results_for_All_Nasdaq_Stocks", "_Scan_Results_for_All_Swiss_Stocks", "_Scan_Results_for_All_Swedish_Stocks", "_Scan_Results_for_Custom_Nasdaq_Stocks"]

# TODO: ASAFR: Add dimension to multi-dim-scan: held_percent_insiders (analyze 1st)

# automatic_folder_selection()
#
# Description:
# This function is called by retrieve_path_settings() when when automatic_folder_selection is True.
# If run is not in research mode, then the reference folder is identified as the most recent results folder from a
# previous run.
# If run is in research mode, then the the new_run folder is identified as the most recent results folder and
# the reference folder is the folder before the most recent one (if such exists, otherwise a warning message
# is printed and both set to the most recent).
#
# Results are returned via the path_dict1 dictionary
def automatic_folder_selection(research_mode_flag, results_input_folder, path_dict1, ref_key, new_run_key):
    results_input_paths = glob(results_input_folder + '/*/')
    if research_mode_flag:
        path_dict1[new_run_key] = results_input_paths[-1]
        if len(results_input_paths) > 1:
            path_dict1[ref_key] = results_input_paths[-2]
        else:
            print('Warning: only one folder in result folder {}, using the same for reference and new_run'.format(
                results_input_folder))
            path_dict1[ref_key] = results_input_paths[-1]
    else:
        path_dict1[new_run_key] = None
        path_dict1[ref_key] = results_input_paths[-1]


# retrieve_path_settings()
#
# Parameters:
#   automatic_results_folder_selection_flag: boolean flag, by default is False.
#   research_mode_flag - boolean flag, identifies if 'research mode' is applied
# Description:
#      When automatic_results_folder_selection_flag is set to False, paths are taken from sss_config.py
#      otherwise paths are automatically derived  by taking the most recent folders.
#
# Results are returned using a dictionary
def retrieve_path_settings(automatic_results_folder_selection_flag, research_mode_flag):
    path_dict1 = {}
    if automatic_results_folder_selection_flag:

        results_input_folder = 'Results/Custom'
        automatic_folder_selection(research_mode_flag, results_input_folder, path_dict1, 'reference_run_custom', 'new_run_custom')
        results_input_folder = 'Results/Tase'
        automatic_folder_selection(research_mode_flag, results_input_folder, path_dict1, 'reference_run_tase',   'new_run_tase')
        results_input_folder = 'Results/Nsr'
        automatic_folder_selection(research_mode_flag, results_input_folder, path_dict1, 'reference_run_nsr',    'new_run_nsr')
        results_input_folder = 'Results/All'
        automatic_folder_selection(research_mode_flag, results_input_folder, path_dict1, 'reference_run_all',    'new_run_all')
        results_input_folder = 'Results/Six'
        automatic_folder_selection(research_mode_flag, results_input_folder, path_dict1, 'reference_run_six',    'new_run_six')
        results_input_folder = 'Results/St'
        automatic_folder_selection(research_mode_flag, results_input_folder, path_dict1, 'reference_run_st',     'new_run_st')
    else:
        path_dict1['reference_run_custom'] = sss_config.reference_run_custom
        path_dict1['reference_run_tase'  ] = sss_config.reference_run_tase
        path_dict1['reference_run_nsr'   ] = sss_config.reference_run_nsr
        path_dict1['reference_run_all'   ] = sss_config.reference_run_all
        path_dict1['reference_run_six'   ] = sss_config.reference_run_six
        path_dict1['reference_run_st'    ] = sss_config.reference_run_st

        path_dict1['new_run_custom'] = sss_config.new_run_custom
        path_dict1['new_run_tase'  ] = sss_config.new_run_tase
        path_dict1['new_run_nsr'   ] = sss_config.new_run_nsr
        path_dict1['new_run_all'   ] = sss_config.new_run_all
        path_dict1['new_run_six'   ] = sss_config.new_run_six
        path_dict1['new_run_st'    ] = sss_config.new_run_st

    return path_dict1


#
# Percentiles:
# index   x        1         2        3  ...  n-1
# +----------------------------------------------------+
# |       x        |         |        |        |       |
# +----------------------------------------------------+
#
# In order to give a chance to all stocks fairly, always take the 1st element in the sorted list
def get_range(csv_db_path, db_filename, column_name, num_sections, reverse, pop_1st_percentile_range=True):
    csv_db_filename = csv_db_path+'/'+db_filename
    num_title_rows = 1 if "normalized" in db_filename else 2
    with open(csv_db_filename, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter=',')
        row_index = 0
        elements_list    = []
        percentile_range = []
        for row in reader:
            if row_index < num_title_rows:  # first row (only in non-normalized sss_engine.csv) is just a title of evr and pm, then a title of columns
                if row_index == num_title_rows-1:
                    if column_name in row:
                        column_index = row.index(column_name)
                        sss_index    = row.index("sss_value_normalized") if "normalized" in db_filename else row.index("sss_value")
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


def prepare_appearance_counters_dictionaries(csv_db_path, db_filename, appearance_counter_dict_sss):
    csv_db_filename = csv_db_path + '/' + db_filename
    num_title_rows = 1 if "normalized" in db_filename else 2
    try:
        with open(csv_db_filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                if row_index < num_title_rows:  # first row (only in non-normalized sss_engine.csv) is just a title of evr and pm, then a title of columns
                    if row_index == num_title_rows-1:
                        ticker_index         = row.index("Symbol")
                        name_index           = row.index("Name")
                        sector_index         = row.index("Sector")
                        sss_index            = row.index("sss_value_normalized") if "normalized" in db_filename else row.index("sss_value")
                        previous_close_index = row.index("previous_close")
                    row_index += 1
                    continue
                else:
                    appearance_counter_dict_sss[  (row[ticker_index],row[name_index],row[sector_index],float(row[sss_index  ]),float(0 if row[previous_close_index] == '' else row[previous_close_index]))] = 0.0  # Symbol, Short Name, Sector, SSS   Value, previousClose
    except Exception as e:
        if print("              Exception in {}: {}".format(row, e)):
            pass


# now introduce the 5th dim:  |dim5 [pi %, %`]| = 2, |dim4 [evm a,b]| = 2, |dim3 [pe 1,10,50]| = 3, |dim2_rows [evr x,y]| = 2, |dim1_cols [num results for 3 pm values]| = 3
# ==========================
#
#  pi (percent_insiders): %
#                                                                                           |cols'''| = 1+|cols''|
#     |cols''| = 1+|cols'|
#   evm  pe   evr / pm                                                             d5  d4   d3 d2    <---- d1 ------->
#    a,   1,  x,    19.,   18.,   17.                                              pi  evm  pe evr / pm
#    a,   1,  y,    14.,   13.,   12.                                              %,  a,   1,  x,   19.,   18.,   17.
#    a,  10,  x,   119.,  118.,  117.                                        \     %,  a,   1,  y,   14.,   13.,   12.
#    a,  10,  y,   114.,  113.,  112.                           ==============\    %,  a,  10,  x,  119.,  118.,  117.
#    a,  50,  x,     b.,    c.,    d.   |rows''=|dim4|*|rows'|| ==============/    %,  a,  10,  y,  114.,  113.,  112.
#    a,  50,  y,     g.,    h.,    i.                                        /     %,  a,  50,  x,    b.,    c.,    d.
#    b,   1,  x,    19_,   18_,   17_                                              %,  a,  50,  y,    g.,    h.,    i.
#    b,   1,  y,    14_,   13_,   12_                                              %,  b,   1,  x,   19_,   18_,   17_
#    b,  10,  x,   119_,  118_,  117_                                              %,  b,   1,  y,   14_,   13_,   12_
#    b,  10,  y,   114_,  113_,  112_                                              %,  b,  10,  x,  119_,  118_,  117_
#    b,  50,  x,     b_,    c_,    d_                                              %,  b,  10,  y,  114_,  113_,  112_
#    b,  50,  y,     g_,    h_,    i_                                              %,  b,  50,  x,    b_,    c_,    d_
#                                                                                  %,  b,  50,  y,    g_,    h_,    i_      |rows'''=|dim5|*|rows''||
#                                                                                  %`, a,   1,  x,   19.`,  18.`,  17.`
#  pi (percent_insiders): %`                                                       %`, a,   1,  y,   14.`,  13.`,  12.`
#                                                                                  %`, a,  10,  x,  119.`, 118.`, 117.`
#                                                                                  %`, a,  10,  y,  114.`, 113.`, 112.`
#     |cols''| = 1+|cols'|                                                         %`, a,  50,  x,    b.`,   c.`,   d.`
#   evm  pe   evr / pm                                                             %`, a,  50,  y,    g.`,   h.`,   i.`
#    a,   1,  x,    19.`,  18.`,  17.`                                         \   %`, b,   1,  x,   19_`,  18_`,  17_`
#    a,   1,  y,    14.`,  13.`,  12.`                            ==============\  %`, b,   1,  y,   14_`,  13_`,  12_`
#    a,  10,  x,   119.`, 118.`, 117.`   |rows''=|dim4|*|rows'||  ==============/  %`, b,  10,  x,  119_`, 118_`, 117_`
#    a,  10,  y,   114.`, 113.`, 112.`                                         /   %`, b,  10,  y,  114_`, 113_`, 112_`
#    a,  50,  x,     b.`,   c.`,   d.`                                             %`, b,  50,  x,    b_`,   c_`,   d_`
#    a,  50,  y,     g.`,   h.`,   i.`                                             %`, b,  50,  y,    g_`,   h_`,   i_`
#    b,   1,  x,    19_`,  18_`,  17_`
#    b,   1,  y,    14_`,  13_`,  12_`
#    b,  10,  x,   119_`, 118_`, 117_`
#    b,  10,  y,   114_`, 113_`, 112_`
#    b,  50,  x,     b_`,   c_`,   d_`
#    b,  50,  y,     g_`,   h_`,   i_`
#                                                 pi    evm   pe    evr        pm
#                                 5dim data       range range range range      range
def combine_multi_dim_to_table_5d(multi_dim_data, dim5, dim4, dim3, dim2_rows, dim1_cols):
    # dim1
    dim1_combined_num_rows = 1                                #                                               1 row for dim 1 (pm range)
    dim1_combined_num_cols = len(dim1_cols)                   #                                               pm range

    # dim2
    dim2_combined_num_rows = len(dim2_rows)                   #                                   evr range
    dim2_combined_num_cols = 1+dim1_combined_num_cols         #                                   evr index + pm range

    # dim3
    dim3_combined_num_rows = len(dim3)*dim2_combined_num_rows #                        pe range * evr range
    dim3_combined_num_cols = 1+dim2_combined_num_cols         #                        pe index + evr index + pm range

    # dim4:
    dim4_combined_num_rows = len(dim4)*dim3_combined_num_rows #            evm range * pe range * evr range
    dim4_combined_num_cols = 1+dim3_combined_num_cols         #            evm index + pe index + evr index + pm range

    # dim5:
    dim5_combined_num_rows = len(dim5)*dim4_combined_num_rows # pi range * evm range * pe range * evr range
    dim5_combined_num_cols = 1+dim4_combined_num_cols         # pi index + evm index + pe index + evr index + pm range

    combined5_rows_cols = np.zeros( (dim5_combined_num_rows, dim5_combined_num_cols), dtype=float )
    for row in range(dim5_combined_num_rows):
        for col in range(dim5_combined_num_cols):
            if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_5d] row = {}, col = {}'.format(row,col))
            if   col == 0:
                dim5_index = int(row / dim4_combined_num_rows) % len(dim5)
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_5d] Access dim5[{}]'.format(dim5_index))
                combined5_rows_cols[row][col] = dim5[dim5_index] # dim5 - pi
            elif col == 1:
                dim4_index = (int(row / dim3_combined_num_rows)) % len(dim4)
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_5d] Access dim4[{}]'.format(dim4_index))
                combined5_rows_cols[row][col] = dim4[dim4_index] # dim4 - evm
            elif col == 2:
                dim3_index = (int(row / dim2_combined_num_rows)) % len(dim3)
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_5d] Access dim3[{}]'.format(dim3_index))
                combined5_rows_cols[row][col] = dim3[dim3_index] # dim3 - pe
            elif col == 3:
                dim2_index = (int(row / dim1_combined_num_rows)) % len(dim2_rows)
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_5d] Access dim2_rows[{}]'.format(dim2_index))
                combined5_rows_cols[row][col] = dim2_rows[dim2_index] # dim2 - evr
            #                                                             pi                              evm                             pe                              evr                      pm
            else:
                dim5_index = int(row / dim4_combined_num_rows) % len(dim5)      # Increase after every dim4_combined_num_rows rows, and cyclic on dim5
                dim4_index = int(row / dim3_combined_num_rows) % len(dim4)      # Increase after every dim3_combined_num_rows rows, and cyclic on dim4
                dim3_index = int(row / dim2_combined_num_rows) % len(dim3)      # Increase after every dim2_combined_num_rows rows, and cyclic on dim3
                dim2_index = row                               % len(dim2_rows) # Increase after every           row,  and cyclic on dim2
                dim1_index = col - 4                                            # Increase after every           col,  and offset of -4 dims
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_5d] Access multi_dim_data[{}][{}][{}][{}][{}]'.format(dim5_index,dim4_index,dim3_index,dim2_index,dim1_index))
                combined5_rows_cols[row][col] = multi_dim_data[dim5_index][dim4_index][dim3_index][dim2_index][dim1_index]  # dim2+dim1

    return combined5_rows_cols


#                                                 pb    pi    evm   pe    evr        pm
#                                 6dim data       range range range range range      range
def combine_multi_dim_to_table_6d(multi_dim_data, dim6, dim5, dim4, dim3, dim2_rows, dim1_cols):
    # dim1
    dim1_combined_num_rows = 1                                #                                               1 row for dim 1 (pm range)
    dim1_combined_num_cols = len(dim1_cols)                   #                                               pm range

    # dim2
    dim2_combined_num_rows = len(dim2_rows)                   #                                   evr range
    dim2_combined_num_cols = 1+dim1_combined_num_cols         #                                   evr index + pm range

    # dim3
    dim3_combined_num_rows = len(dim3)*dim2_combined_num_rows #                        pe range * evr range
    dim3_combined_num_cols = 1+dim2_combined_num_cols         #                        pe index + evr index + pm range

    # dim4:
    dim4_combined_num_rows = len(dim4)*dim3_combined_num_rows #            evm range * pe range * evr range
    dim4_combined_num_cols = 1+dim3_combined_num_cols         #            evm index + pe index + evr index + pm range

    # dim5:
    dim5_combined_num_rows = len(dim5)*dim4_combined_num_rows # pi range * evm range * pe range * evr range
    dim5_combined_num_cols = 1+dim4_combined_num_cols         # pi index + evm index + pe index + evr index + pm range

    # dim6:
    dim6_combined_num_rows = len(dim6)*dim5_combined_num_rows # pb range * pi range * evm range * pe range * evr range
    dim6_combined_num_cols = 1+dim5_combined_num_cols         # pb index + pi index + evm index + pe index + evr index + pm range

    combined6_rows_cols = np.zeros( (dim6_combined_num_rows, dim6_combined_num_cols), dtype=float )
    for row in range(dim6_combined_num_rows):
        for col in range(dim6_combined_num_cols):
            if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_6d] row = {}, col = {}'.format(row,col))
            if   col == 0:
                dim6_index = (int(row / dim5_combined_num_rows)) % len(dim6)
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_6d] Access dim6[{}]'.format(dim6_index))
                combined6_rows_cols[row][col] = dim6[dim6_index] # dim6 - pb
            elif col == 1:
                dim5_index = (int(row / dim4_combined_num_rows)) % len(dim5)
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_6d] Access dim5[{}]'.format(dim5_index))
                combined6_rows_cols[row][col] = dim5[dim5_index] # dim5 - pi
            elif col == 2:
                dim4_index = (int(row / dim3_combined_num_rows)) % len(dim4)
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_6d] Access dim4[{}]'.format(dim4_index))
                combined6_rows_cols[row][col] = dim4[dim4_index] # dim4 - evm
            elif col == 3:
                dim3_index = (int(row / dim2_combined_num_rows)) % len(dim3)
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_6d] Access dim3[{}]'.format(dim3_index))
                combined6_rows_cols[row][col] = dim3[dim3_index] # dim3 - pe
            elif col == 4:
                dim2_index = (int(row / dim1_combined_num_rows)) % len(dim2_rows)
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_6d] Access dim2_rows[{}]'.format(dim2_index))
                combined6_rows_cols[row][col] = dim2_rows[dim2_index] # dim2 - evr
            #                                                             pi                              evm                             pe                              evr                      pm
            else:
                dim6_index = int(row / dim5_combined_num_rows) % len(dim6)      # Increase after every dim5_combined_num_rows rows, and cyclic on dim6
                dim5_index = int(row / dim4_combined_num_rows) % len(dim5)      # Increase after every dim4_combined_num_rows rows, and cyclic on dim5
                dim4_index = int(row / dim3_combined_num_rows) % len(dim4)      # Increase after every dim3_combined_num_rows rows, and cyclic on dim4
                dim3_index = int(row / dim2_combined_num_rows) % len(dim3)      # Increase after every dim2_combined_num_rows rows, and cyclic on dim3
                dim2_index = row                               % len(dim2_rows) # Increase after every           row,  and cyclic on dim2
                dim1_index = col - 5                                            # Increase after every           col,  and offset of -5 dims
                if sss.VERBOSE_LOGS: print('[combine_multi_dim_to_table_6d] Access multi_dim_data[{}][{}][{}][{}][{}][{}]'.format(dim6_index,dim5_index,dim4_index,dim3_index,dim2_index,dim1_index))
                combined6_rows_cols[row][col] = multi_dim_data[dim6_index][dim5_index][dim4_index][dim3_index][dim2_index][dim1_index]  # dim2+dim1

    return combined6_rows_cols


# TODO: ASAFR: 1. Must add the EQG to the multi-dimensional scan - the TH is now -50% but it must be scanned
#              2. Like the EQG - see other places where there are filterings out (around that area in sss.py) and handle properly - EV/CFO and D/E
#              3. Move to Pandas in CSV readings!
def research_db(sectors_list, sectors_filter_out, countries_list, countries_filter_out, pb_range, pi_range, research_mode_max_ev, ev_millions_range, evr_range, pe_range, pm_range, csv_db_path, db_filename, read_all_country_symbols, scan_mode, appearance_counter_min, appearance_counter_max, favor_sectors, favor_sectors_by,
                newer_path, older_path, movement_threshold, res_length):
    if scan_mode == SCAN_MODE_TASE:
        tase_mode = 1
    else:
        tase_mode = 0

    if research_mode_max_ev:
        ev_millions_range = list(reversed(ev_millions_range)) # Flip order to have stocks with higher EV first (as limit shall be Max and not Min)

    appearance_counter_dict_sss   = {}
    prepare_appearance_counters_dictionaries(csv_db_path, db_filename, appearance_counter_dict_sss)
    pb_range_len          = len(pb_range)
    pi_range_len          = len(pi_range)
    ev_millions_range_len = len(ev_millions_range)
    pe_range_len          = len(pe_range)
    evr_range_len         = len(evr_range)
    pm_range_len          = len(pm_range)
    research_num_results_multi_dim_data = np.zeros( (pb_range_len, pi_range_len, ev_millions_range_len, pe_range_len, evr_range_len, pm_range_len), dtype=int )
    elapsed_time_start_sec = time.time()
    iteration              = 0
    estimated_iterations_left = pb_range_len*pi_range_len*ev_millions_range_len*pe_range_len*evr_range_len*pm_range_len
    for pb_index, pb_limit                                           in enumerate(pb_range):
        print('\n')
        for pi_index, pi_limit                                       in enumerate(pi_range):
            print('\n')
            for ev_millions_index, ev_millions_limit                 in enumerate(ev_millions_range):
                print('\n')
                for pe_index, price_to_earnings_limit                in enumerate(pe_range):
                    print('\n')
                    for evr_index, enterprise_value_to_revenue_limit in enumerate(evr_range):
                        print('\n')
                        for pm_index, profit_margin_limit            in enumerate(pm_range):  # TODO: ASAFR: Below 1. Ambiguity of parameters - narrow down. 2. Some magic numbers on ev_to_cfo_ration etc 100.0 and 1000.0 - make order and defines/constants/multi_dim here
                            num_results_for_pb_pi_ev_pe_evr_and_pm = sss.sss_run(reference_run=[], sectors_list=sectors_list, sectors_filter_out=sectors_filter_out, countries_list=countries_list, countries_filter_out=countries_filter_out, csv_db_path=csv_db_path, db_filename=db_filename, read_all_country_symbols=read_all_country_symbols, tase_mode=tase_mode, research_mode=1, profit_margin_limit=float(profit_margin_limit)/100.0, pb_limit=pb_limit, pi_limit=pi_limit, enterprise_value_millions_usd_limit=ev_millions_limit, research_mode_max_ev=research_mode_max_ev, ev_to_cfo_ratio_limit=10e9, debt_to_equity_limit=10e9, price_to_earnings_limit=price_to_earnings_limit, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_sectors=favor_sectors, favor_sectors_by=favor_sectors_by, appearance_counter_dict_sss=appearance_counter_dict_sss, appearance_counter_min=appearance_counter_min, appearance_counter_max=appearance_counter_max)
                            if num_results_for_pb_pi_ev_pe_evr_and_pm < appearance_counter_min:
                                estimated_iterations_left -= (pm_range_len-pm_index)
                                iteration                 += (pm_range_len-pm_index)
                                break  # Already lower than appearance_counter_min results. With higher profit margin limit there will always be less results -> save running time by breaking
                            research_num_results_multi_dim_data[pb_index][pi_index][ev_millions_index][pe_index][evr_index][pm_index] = int(num_results_for_pb_pi_ev_pe_evr_and_pm)

                            estimated_iterations_left -= 1
                            iteration                 += 1
                            elapsed_time_sample_sec   = time.time()
                            elapsed_time_sec          = round(elapsed_time_sample_sec - elapsed_time_start_sec, 0)
                            average_sec_per_iteration = round(elapsed_time_sec / iteration, int(sss.NUM_ROUND_DECIMALS / 3))
                            percentage_complete       = round(100 * iteration / (estimated_iterations_left+iteration), int(sss.NUM_ROUND_DECIMALS / 3))
                            estimated_time_left_sec   = int(round(average_sec_per_iteration*estimated_iterations_left, 0))
                            print('time [sec] tot/avg/%/left {:3.0f}/{:1.2f}/{:2.2f}/{:5} : pb {:6.3f} | pi {:6.6f} | evm {:6.0f} | pe {:8.3f} | evr {:8.3f} | pm {:7.3f}% -> num_results = {}'.format(elapsed_time_sec, average_sec_per_iteration, percentage_complete, estimated_time_left_sec, pb_limit, pi_limit, ev_millions_limit, price_to_earnings_limit, enterprise_value_to_revenue_limit, profit_margin_limit, num_results_for_pb_pi_ev_pe_evr_and_pm))
    results_filename    = 'results_without_labels_{}'.format(db_filename)

    mesh_combined = combine_multi_dim_to_table_6d(multi_dim_data=research_num_results_multi_dim_data, dim6=pb_range, dim5=pi_range, dim4=ev_millions_range, dim3=pe_range, dim2_rows=evr_range, dim1_cols=pm_range)

    np.savetxt(csv_db_path+'/'+results_filename,  mesh_combined, fmt='%f', delimiter=',')
    title_row = pm_range             # column 5 and onwards
    title_row.insert(0, 'evr / pm')  # column 4
    title_row.insert(0, 'pe')        # column 3
    title_row.insert(0, 'ev')        # column 2
    title_row.insert(0, 'pi')        # column 1
    title_row.insert(0, 'pb')        # column 0
    pb_pi_ev_pe_evr_rows_pm_cols_filenames_list = [csv_db_path+'/'+results_filename]
    # Read Results, and add row and col axis:
    for filename in pb_pi_ev_pe_evr_rows_pm_cols_filenames_list:
        pb_pi_ev_pe_evr_rows_pm_cols = [title_row]
        with open(filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0  # Title
            for row in reader:
                pb_pi_ev_pe_evr_rows_pm_cols.append(row)
                row_index += 1
    for index in range(len(pb_pi_ev_pe_evr_rows_pm_cols_filenames_list)):
        row_col_csv_filename = pb_pi_ev_pe_evr_rows_pm_cols_filenames_list[index].replace('.csv','_with_labels.csv')
        os.makedirs(os.path.dirname(row_col_csv_filename), exist_ok=True)
        with open(row_col_csv_filename, mode='w', newline='') as engine:
            writer = csv.writer(engine)
            writer.writerows(pb_pi_ev_pe_evr_rows_pm_cols)

    sorted_appearance_counter_dict_sss          = {k: v for k, v in sorted(appearance_counter_dict_sss.items(),   key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict_sss   = {k: v for k, v in sorted_appearance_counter_dict_sss.items()    if v > 0.0}

    result_list_filename_sss              = csv_db_path+'/results_{}'.format(    db_filename.replace('_engine',''))
    result_list_filename_sss_ref_to_read  = older_path +'/results_{}'.format(    db_filename.replace('_engine',''))
    result_list_filename_sss_ref_to_write = csv_db_path+'/results_ref_{}'.format(db_filename.replace('_engine',''))

    # Create the new results file without yet adding the Diff column
    with open(result_list_filename_sss, 'w') as f:
        f.write("Symbol,Name,Sector,Value,Close,Grade\n")
        for key in result_sorted_appearance_counter_dict_sss.keys():
            #                              Symbol,    Name,                    Sector Value           Close        Grade
            f.write("%s,%s,%s,%s,%s,%s\n"%(key[0],str(key[1]).replace(',',' '),key[2],round(key[3],5),key[4],round(result_sorted_appearance_counter_dict_sss[  key],4)))

    # Read the reference results file without the Diff column
    ref_rows_no_diff = []
    with open(result_list_filename_sss_ref_to_read, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter=',')
        row_index = 0
        for row in reader:
            ref_rows_no_diff.append(row)
            if row_index >= res_length: break
            row_index += 1

    # Create the removed results file without yet adding the Diff column
    with open(result_list_filename_sss_ref_to_write, 'w') as f:
        for row in ref_rows_no_diff:
            #                                    Symbol, Name,   Sector  Value   Close   Grade
            f.write("{},{},{},{},{},{}\n".format(row[0], row[1], row[2], row[3], row[4], row[5]))

    if older_path is not None:
        [diff_list_new, diff_list_removed] = sss_diff.run(newer_path=newer_path, older_path=older_path, db_filename=db_filename, movement_threshold=movement_threshold, res_length=res_length, consider_as_new_from=PDF_NUM_ENTRIES_IN_REPORT)

        pdf_to_append = pdf_generator.csv_to_pdf(csv_filename=result_list_filename_sss,              output_path=csv_db_path, data_time_str=result_list_filename_sss.replace(             'Results','').replace('Tase','').replace('Nsr','').replace('All','').replace('Six','').replace('St','').replace('Custom','').replace('/','')[0:15], title=TITLES[scan_mode].replace('_',' '), limit_num_rows=PDF_NUM_ENTRIES_IN_REPORT, diff_list_new=diff_list_new,     tase_mode=tase_mode, db_filename=db_filename, append_to_pdf=None,          output=False)
        pdf_generator.csv_to_pdf(                csv_filename=result_list_filename_sss_ref_to_write, output_path=csv_db_path, data_time_str=result_list_filename_sss_ref_to_write.replace('Results','').replace('Tase','').replace('Nsr','').replace('All','').replace('Six','').replace('St','').replace('Custom','').replace('/','')[0:15], title=TITLES[scan_mode].replace('_',' '), limit_num_rows=PDF_NUM_ENTRIES_IN_REPORT, diff_list_new=diff_list_removed, tase_mode=tase_mode, db_filename=db_filename, append_to_pdf=pdf_to_append, output=True )


def find_symbol_in_aggregated_results(symbol, aggregated_results):
    for index, row in enumerate(aggregated_results):
        if row[0] == symbol: return index

    return -1


def aggregate_results(newer_path, older_path, res_length, scan_mode):
    aggregated_results = []
    for db_filename_to_aggregate in DB_FILENAMES:
        result_list_filename_sss = newer_path + '/results_{}'.format(db_filename_to_aggregate.replace('_engine', ''))

        with open(result_list_filename_sss, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                if row_index < 1:  # first row title
                    row_index += 1
                    continue
                else:
                    position = find_symbol_in_aggregated_results(row[0], aggregated_results)
                    if position >= 0:  # Existing Entry:
                        aggregated_results[position][3] += '/' + row[3]
                        aggregated_results[position][5] += float(row[5])
                    else:  # New Entry:            Symbol  Name    Sector  sss_value/sss_value_normalized Close   Grade
                        aggregated_results.append([row[0], row[1], row[2], row[3],                        row[4], float(row[5])])

    # Sort the aggregated results by their aggregated Grade:
    sorted_aggregated_results = sorted(aggregated_results, key=lambda row: row[5], reverse=True)  # Sort by Grade

    # Save aggregated_results:
    result_list_filename_sss = newer_path + '/results_sss_aggregated.csv'
    with open(result_list_filename_sss, 'w') as f:
        f.write("Symbol,Name,Sector,Value,Close,Grade\n")
        for row in sorted_aggregated_results:
            #                                    Symbol, Name,   Sector  Value   Close   Grade
            f.write("{},{},{},{},{},{}\n".format(row[0], row[1], row[2], row[3], row[4], round(row[5],4)))

    # Read reference aggregated_results less the diff column:
    result_list_filename_sss_ref = older_path + '/results_sss_aggregated.csv'
    ref_rows_no_diff = []
    with open(result_list_filename_sss_ref, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter=',')
        row_index = 0
        for row in reader:
            ref_rows_no_diff.append(row)
            if row_index >= res_length: break
            row_index += 1

    # Create the removed results file without yet adding the Diff column
    result_list_filename_sss_ref_to_write = newer_path + '/results_ref_sss_aggregated.csv'
    with open(result_list_filename_sss_ref_to_write, 'w') as f:
        for row in ref_rows_no_diff:
            #                                    Symbol, Name,   Sector  Value   Close   Grade
            f.write("{},{},{},{},{},{}\n".format(row[0], row[1], row[2], row[3], row[4], row[5]))


    if older_path is not None:
        [aggregated_diff_list_new, aggregated_diff_list_removed] = sss_diff.run(newer_path=newer_path, older_path=older_path, db_filename='sss_aggregated.csv', movement_threshold=0, res_length=res_length, consider_as_new_from=PDF_NUM_ENTRIES_IN_REPORT)

        pdf_to_append = pdf_generator.csv_to_pdf(csv_filename=result_list_filename_sss,              output_path=newer_path, data_time_str=result_list_filename_sss.replace(             'Results', '').replace('Tase', '').replace('Nsr', '').replace('All', '').replace('Six','').replace('St','').replace('Custom', '').replace('/', '')[0:15], title=TITLES[scan_mode].replace('_', ' ') + ' ' + ('aggregated'[::-1] if scan_mode==SCAN_MODE_TASE else 'aggregated'), limit_num_rows=PDF_NUM_ENTRIES_IN_REPORT, diff_list_new=aggregated_diff_list_new,     tase_mode=(1 if scan_mode == SCAN_MODE_TASE else 0), db_filename="", append_to_pdf=None,          output=False)
        pdf_generator.csv_to_pdf(                csv_filename=result_list_filename_sss_ref_to_write, output_path=newer_path, data_time_str=result_list_filename_sss_ref_to_write.replace('Results', '').replace('Tase', '').replace('Nsr', '').replace('All', '').replace('Six','').replace('St','').replace('Custom', '').replace('/', '')[0:15], title=TITLES[scan_mode].replace('_', ' ') + ' ' + ('aggregated'[::-1] if scan_mode==SCAN_MODE_TASE else 'aggregated'), limit_num_rows=PDF_NUM_ENTRIES_IN_REPORT, diff_list_new=aggregated_diff_list_removed, tase_mode=(1 if scan_mode == SCAN_MODE_TASE else 0), db_filename="", append_to_pdf=pdf_to_append, output=True )


def execute():
    ############################
    # main ()
    ###########################
    # TODO: ASAFR: 1. Export Results to the SSS Google Sheet automatically

    run_custom_tase      = sss_config.run_custom_tase       # Custom Portfolio
    run_custom           = sss_config.run_custom
    run_tase             = sss_config.run_tase              # Tel Aviv Stock Exchange
    run_nsr              = sss_config.run_nsr               # NASDAQ100+S&P500+RUSSEL1000
    run_all              = sss_config.run_all               # All Nasdaq Stocks
    run_six              = sss_config.run_six               # All SIX Stocks
    run_st               = sss_config.run_st                # All (Stockholm) Swedish Stocks
    research_mode        = sss_config.research_mode         # Research Mode
    research_mode_max_ev = sss_config.research_mode_max_ev
    automatic_results_folder_selection = sss_config.automatic_results_folder_selection

    path_setting_dict = retrieve_path_settings(automatic_results_folder_selection, research_mode)
    print(path_setting_dict)

    reference_run_custom = path_setting_dict['reference_run_custom']
    reference_run_tase   = path_setting_dict['reference_run_tase']
    reference_run_nsr    = path_setting_dict['reference_run_nsr']
    reference_run_all    = path_setting_dict['reference_run_all']
    reference_run_six    = path_setting_dict['reference_run_six']
    reference_run_st     = path_setting_dict['reference_run_st']

    new_run_custom = path_setting_dict['new_run_custom']
    new_run_tase   = path_setting_dict['new_run_tase']
    new_run_nsr    = path_setting_dict['new_run_nsr']
    new_run_all    = path_setting_dict['new_run_all']
    new_run_six    = path_setting_dict['new_run_six']
    new_run_st     = path_setting_dict['new_run_st']

    if not research_mode:   # Run Build DB Only:
        if run_custom_tase: sss.sss_run(reference_run=reference_run_custom, sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, csv_db_path='None', db_filename='None', read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_OFF, tase_mode=1, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=10e9, debt_to_equity_limit=10e9, pb_limit=0, pi_limit=0, enterprise_value_millions_usd_limit=1, research_mode_max_ev=False, price_to_earnings_limit=10e9, enterprise_value_to_revenue_limit=10e9, favor_sectors=[],                                   favor_sectors_by=[],         custom_portfolio=sss_config.custom_portfolio_tase)
        if run_custom:      sss.sss_run(reference_run=reference_run_custom, sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, csv_db_path='None', db_filename='None', read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_OFF, tase_mode=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=10e9, debt_to_equity_limit=10e9, pb_limit=0, pi_limit=0, enterprise_value_millions_usd_limit=5, research_mode_max_ev=False, price_to_earnings_limit=10e9, enterprise_value_to_revenue_limit=10e9, favor_sectors=[],                                   favor_sectors_by=[],         custom_portfolio=sss_config.custom_portfolio)
        if run_tase:        sss.sss_run(reference_run=reference_run_tase,   sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, csv_db_path='None', db_filename='None', read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_OFF, tase_mode=1, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=10e9, debt_to_equity_limit=10e9, pb_limit=0, pi_limit=0, enterprise_value_millions_usd_limit=1, research_mode_max_ev=False, price_to_earnings_limit=10e9, enterprise_value_to_revenue_limit=10e9, favor_sectors=['Technology', 'Real Estate'       ], favor_sectors_by=[3.0,  1.0],)
        if run_nsr:         sss.sss_run(reference_run=reference_run_nsr,    sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, csv_db_path='None', db_filename='None', read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_OFF, tase_mode=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=10e9, debt_to_equity_limit=10e9, pb_limit=0, pi_limit=0, enterprise_value_millions_usd_limit=5, research_mode_max_ev=False, price_to_earnings_limit=10e9, enterprise_value_to_revenue_limit=10e9, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[3.0,  0.75])
        if run_all:         sss.sss_run(reference_run=reference_run_all,    sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, csv_db_path='None', db_filename='None', read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_US,  tase_mode=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=10e9, debt_to_equity_limit=10e9, pb_limit=0, pi_limit=0, enterprise_value_millions_usd_limit=5, research_mode_max_ev=False, price_to_earnings_limit=10e9, enterprise_value_to_revenue_limit=10e9, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[3.0,  0.75])
        if run_six:         sss.sss_run(reference_run=reference_run_six,    sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, csv_db_path='None', db_filename='None', read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_SIX, tase_mode=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=10e9, debt_to_equity_limit=10e9, pb_limit=0, pi_limit=0, enterprise_value_millions_usd_limit=5, research_mode_max_ev=False, price_to_earnings_limit=10e9, enterprise_value_to_revenue_limit=10e9, favor_sectors=[],                                   favor_sectors_by=[],         )
        if run_st:          sss.sss_run(reference_run=reference_run_st,     sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, csv_db_path='None', db_filename='None', read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_ST,  tase_mode=0, research_mode=0, profit_margin_limit=0.0001, ev_to_cfo_ratio_limit=10e9, debt_to_equity_limit=10e9, pb_limit=0, pi_limit=0, enterprise_value_millions_usd_limit=5, research_mode_max_ev=False, price_to_earnings_limit=10e9, enterprise_value_to_revenue_limit=10e9, favor_sectors=[],                                   favor_sectors_by=[],         )
    else:                   # Research Mode:
        if run_tase:
            if not sss_config.aggregate_only:
                for db_filename in DB_FILENAMES:
                    pb_range_tase         = get_range(csv_db_path=new_run_tase, db_filename=db_filename, column_name='price_to_book',           num_sections=1 if sss_config.custom_sss_value_equation else 5, reverse=1, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else False)  # TODO: ASAFR: Revisit this - perhaps no popping required for non-TASE as well?
                    pi_range_tase         = get_range(csv_db_path=new_run_tase, db_filename=db_filename, column_name='held_percent_insiders',   num_sections=1 if sss_config.custom_sss_value_equation else 3, reverse=0, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else False)
                    ev_range_tase         = get_range(csv_db_path=new_run_tase, db_filename=db_filename, column_name='enterprise_value',        num_sections=2 if sss_config.custom_sss_value_equation else 3, reverse=0, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else False)
                    pe_range_tase         = get_range(csv_db_path=new_run_tase, db_filename=db_filename, column_name='pe_effective',            num_sections=2 if sss_config.custom_sss_value_equation else 5, reverse=1, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else False)
                    evr_range_tase        = get_range(csv_db_path=new_run_tase, db_filename=db_filename, column_name='evr_effective',           num_sections=2 if sss_config.custom_sss_value_equation else 6, reverse=1, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else False)
                    pm_ratios_range_tase  = get_range(csv_db_path=new_run_tase, db_filename=db_filename, column_name='effective_profit_margin', num_sections=2 if sss_config.custom_sss_value_equation else 7, reverse=0, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else False)

                    ev_millions_range_tase= [int(  ev/1000000                       ) for ev in ev_range_tase       ]
                    pm_range_tase         = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_tase]

                    research_db(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, pb_range=pb_range_tase, pi_range=pi_range_tase, research_mode_max_ev=research_mode_max_ev, ev_millions_range=ev_millions_range_tase, pe_range=pe_range_tase, evr_range=evr_range_tase, pm_range=pm_range_tase,   csv_db_path=new_run_tase, db_filename=db_filename,   read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_OFF, scan_mode=SCAN_MODE_TASE, appearance_counter_min=RESEARCH_MODE_MIN_ENTRIES_LIMIT, appearance_counter_max=1000, favor_sectors=['Technology', 'Real Estate'], favor_sectors_by=[3.0, 1.0],
                                newer_path=new_run_tase, older_path=reference_run_tase, movement_threshold=0, res_length=400)
            aggregate_results(newer_path=new_run_tase, older_path=reference_run_tase, res_length=400, scan_mode=SCAN_MODE_TASE)

        if run_nsr:
            if not sss_config.aggregate_only:
                for db_filename in DB_FILENAMES:
                    pb_range_nsr          = get_range(csv_db_path=new_run_nsr,  db_filename=db_filename, column_name='price_to_book',           num_sections=1 if sss_config.custom_sss_value_equation else 6, reverse=1, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)
                    pi_range_nsr          = get_range(csv_db_path=new_run_nsr,  db_filename=db_filename, column_name='held_percent_insiders',   num_sections=1 if sss_config.custom_sss_value_equation else 4, reverse=0, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)
                    ev_range_nsr          = get_range(csv_db_path=new_run_nsr,  db_filename=db_filename, column_name='enterprise_value',        num_sections=3 if sss_config.custom_sss_value_equation else 4, reverse=0, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)
                    pe_range_nsr          = get_range(csv_db_path=new_run_nsr,  db_filename=db_filename, column_name='pe_effective',            num_sections=3 if sss_config.custom_sss_value_equation else 6, reverse=1, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)
                    evr_range_nsr         = get_range(csv_db_path=new_run_nsr,  db_filename=db_filename, column_name='evr_effective',           num_sections=3 if sss_config.custom_sss_value_equation else 7, reverse=1, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)
                    pm_ratios_range_nsr   = get_range(csv_db_path=new_run_nsr,  db_filename=db_filename, column_name='effective_profit_margin', num_sections=3 if sss_config.custom_sss_value_equation else 8, reverse=0, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)

                    ev_millions_range_nsr = [int(  ev/1000000                       ) for ev in ev_range_nsr       ]
                    pm_range_nsr          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_nsr]

                    research_db(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, pb_range=pb_range_nsr, pi_range=pi_range_nsr, research_mode_max_ev=research_mode_max_ev, ev_millions_range=ev_millions_range_nsr, pe_range=pe_range_nsr, evr_range=evr_range_nsr, pm_range=pm_range_nsr,  csv_db_path=new_run_nsr, db_filename=db_filename,   read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_OFF, scan_mode=SCAN_MODE_NSR, appearance_counter_min=RESEARCH_MODE_MIN_ENTRIES_LIMIT, appearance_counter_max=5000, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[3.5, 1.0],
                                newer_path=new_run_nsr, older_path=reference_run_nsr, movement_threshold=0, res_length=800)
            aggregate_results(newer_path=new_run_nsr, older_path=reference_run_nsr, res_length=800, scan_mode=SCAN_MODE_NSR)

        if run_all:
            if not sss_config.aggregate_only:
                for db_filename in DB_FILENAMES:
                    pb_range_all          = get_range(csv_db_path=new_run_all, db_filename=db_filename, column_name='price_to_book',            num_sections=1 if sss_config.custom_sss_value_equation else  7, reverse=1, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)
                    pi_range_all          = get_range(csv_db_path=new_run_all, db_filename=db_filename, column_name='held_percent_insiders',    num_sections=1 if sss_config.custom_sss_value_equation else  5, reverse=0, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)
                    ev_range_all          = get_range(csv_db_path=new_run_all, db_filename=db_filename, column_name='enterprise_value',         num_sections=4 if sss_config.custom_sss_value_equation else  5, reverse=0, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)
                    pe_range_all          = get_range(csv_db_path=new_run_all, db_filename=db_filename, column_name='pe_effective',             num_sections=4 if sss_config.custom_sss_value_equation else  7, reverse=1, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)
                    evr_range_all         = get_range(csv_db_path=new_run_all, db_filename=db_filename, column_name='evr_effective',            num_sections=7 if sss_config.custom_sss_value_equation else 14, reverse=1, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)
                    pm_ratios_range_all   = get_range(csv_db_path=new_run_all, db_filename=db_filename, column_name='effective_profit_margin',  num_sections=4 if sss_config.custom_sss_value_equation else  9, reverse=0, pop_1st_percentile_range=False if sss_config.custom_sss_value_equation else True)

                    ev_millions_range_all = [int(  ev/1000000                       ) for ev in ev_range_all       ]
                    pm_range_all          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_all]

                    research_db(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, pb_range=pb_range_all, pi_range=pi_range_all, research_mode_max_ev=research_mode_max_ev, ev_millions_range=ev_millions_range_all, pe_range=pe_range_all, evr_range=evr_range_all, pm_range=pm_range_all, csv_db_path=new_run_all, db_filename=db_filename, read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_US, scan_mode=SCAN_MODE_ALL, appearance_counter_min=RESEARCH_MODE_MIN_ENTRIES_LIMIT, appearance_counter_max=50000, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[3.5, 1.0],
                                newer_path=new_run_all, older_path=reference_run_all, movement_threshold=0, res_length=1000)
            aggregate_results(newer_path=new_run_all, older_path=reference_run_all, res_length=1000, scan_mode=SCAN_MODE_ALL)

        if run_six:
            if not sss_config.aggregate_only:
                for db_filename in DB_FILENAMES:
                    pb_range_six          = get_range(csv_db_path=new_run_six, db_filename=db_filename, column_name='price_to_book',            num_sections=1, reverse=1, pop_1st_percentile_range=False)
                    pi_range_six          = get_range(csv_db_path=new_run_six, db_filename=db_filename, column_name='held_percent_insiders',    num_sections=1, reverse=0, pop_1st_percentile_range=False)
                    ev_range_six          = get_range(csv_db_path=new_run_six, db_filename=db_filename, column_name='enterprise_value',         num_sections=1, reverse=0, pop_1st_percentile_range=False)
                    pe_range_six          = get_range(csv_db_path=new_run_six, db_filename=db_filename, column_name='pe_effective',             num_sections=1, reverse=1, pop_1st_percentile_range=False)
                    evr_range_six         = get_range(csv_db_path=new_run_six, db_filename=db_filename, column_name='evr_effective',            num_sections=1, reverse=1, pop_1st_percentile_range=False)
                    pm_ratios_range_six   = get_range(csv_db_path=new_run_six, db_filename=db_filename, column_name='effective_profit_margin',  num_sections=1, reverse=0, pop_1st_percentile_range=False)

                    ev_millions_range_six = [int(  ev/1000000                       ) for ev in ev_range_six       ]
                    pm_range_six          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_six]

                    research_db(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, pb_range=pb_range_six, pi_range=pi_range_six, research_mode_max_ev=research_mode_max_ev, ev_millions_range=ev_millions_range_six, pe_range=pe_range_six, evr_range=evr_range_six, pm_range=pm_range_six, csv_db_path=new_run_six, db_filename=db_filename, read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_SIX, scan_mode=SCAN_MODE_SIX, appearance_counter_min=RESEARCH_MODE_MIN_ENTRIES_LIMIT/2, appearance_counter_max=50000, favor_sectors=[], favor_sectors_by=[],
                                newer_path=new_run_six, older_path=reference_run_six, movement_threshold=0, res_length=100)
            aggregate_results(newer_path=new_run_six, older_path=reference_run_six, res_length=1000, scan_mode=SCAN_MODE_SIX)

        if run_st:
            if not sss_config.aggregate_only:
                for db_filename in DB_FILENAMES:
                    pb_range_st          = get_range(csv_db_path=new_run_st, db_filename=db_filename, column_name='price_to_book',            num_sections=5, reverse=1)
                    pi_range_st          = get_range(csv_db_path=new_run_st, db_filename=db_filename, column_name='held_percent_insiders',    num_sections=3, reverse=0)
                    ev_range_st          = get_range(csv_db_path=new_run_st, db_filename=db_filename, column_name='enterprise_value',         num_sections=3, reverse=0)
                    pe_range_st          = get_range(csv_db_path=new_run_st, db_filename=db_filename, column_name='pe_effective',             num_sections=4, reverse=1)
                    evr_range_st         = get_range(csv_db_path=new_run_st, db_filename=db_filename, column_name='evr_effective',            num_sections=5, reverse=1)
                    pm_ratios_range_st   = get_range(csv_db_path=new_run_st, db_filename=db_filename, column_name='effective_profit_margin',  num_sections=6, reverse=0)

                    ev_millions_range_st = [int(  ev/1000000                       ) for ev in ev_range_st       ]
                    pm_range_st          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_st]

                    research_db(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, pb_range=pb_range_st, pi_range=pi_range_st, research_mode_max_ev=research_mode_max_ev, ev_millions_range=ev_millions_range_st, pe_range=pe_range_st, evr_range=evr_range_st, pm_range=pm_range_st, csv_db_path=new_run_st, db_filename=db_filename, read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_ST, scan_mode=SCAN_MODE_ST, appearance_counter_min=RESEARCH_MODE_MIN_ENTRIES_LIMIT, appearance_counter_max=50000, favor_sectors=[], favor_sectors_by=[],
                                newer_path=new_run_st, older_path=reference_run_st, movement_threshold=0, res_length=1000)
            aggregate_results(newer_path=new_run_st, older_path=reference_run_st, res_length=1000, scan_mode=SCAN_MODE_ST)

        if run_custom:
            if not sss_config.aggregate_only:
                for db_filename in DB_FILENAMES:
                    pb_range_custom          = get_range(csv_db_path=new_run_custom, db_filename=db_filename, column_name='price_to_book',            num_sections=5, reverse=1)
                    pi_range_custom          = get_range(csv_db_path=new_run_custom, db_filename=db_filename, column_name='held_percent_insiders',    num_sections=3, reverse=0)
                    ev_range_custom          = get_range(csv_db_path=new_run_custom, db_filename=db_filename, column_name='enterprise_value',         num_sections=3, reverse=0)
                    pe_range_custom          = get_range(csv_db_path=new_run_custom, db_filename=db_filename, column_name='pe_effective',             num_sections=4, reverse=1)
                    evr_range_custom         = get_range(csv_db_path=new_run_custom, db_filename=db_filename, column_name='evr_effective',            num_sections=5, reverse=1)
                    pm_ratios_range_custom   = get_range(csv_db_path=new_run_custom, db_filename=db_filename, column_name='effective_profit_margin',  num_sections=6, reverse=0)

                    ev_millions_range_custom = [int(  ev/1000000                       ) for ev in ev_range_custom       ]
                    pm_range_custom          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_custom]

                    research_db(sectors_list=[], sectors_filter_out=0, countries_list=[], countries_filter_out=0, pb_range=pb_range_custom, pi_range=pi_range_custom, research_mode_max_ev=research_mode_max_ev, ev_millions_range=ev_millions_range_custom, pe_range=pe_range_custom, evr_range=evr_range_custom, pm_range=pm_range_custom, csv_db_path=new_run_custom, db_filename=db_filename, read_all_country_symbols=sss_config.ALL_COUNTRY_SYMBOLS_US, scan_mode=SCAN_MODE_CUSTOM, appearance_counter_min=RESEARCH_MODE_MIN_ENTRIES_LIMIT, appearance_counter_max=50000, favor_sectors=[], favor_sectors_by=[],
                                newer_path=new_run_custom, older_path=reference_run_custom, movement_threshold=0, res_length=1000)
            aggregate_results(newer_path=new_run_custom, older_path=reference_run_custom, res_length=1000, scan_mode=SCAN_MODE_CUSTOM)

if sss_config.PROFILE:
    cProfile.run('execute()')
else:
    execute()
