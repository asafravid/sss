######
# V4 #
######


import sss
import numpy as np
import time
import csv
import os



# Reuse:
# sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path='Results/20201115-001203_MARKETCAP_FORWARDEPS', read_united_states_input_symbols=0, tase_mode=0, num_threads=1, forward_eps_included=0, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.17, best_n_select=50, enterprise_value_to_revenue_limit=15)

# Run Build DB Only: Nasdaq100/S&P500
# ===================================
# sss.sss_run(sectors_list=[], build_csv_db_only=1, build_csv_db=1, csv_db_path='Results/20201112-195244_MARKETCAP', read_united_states_input_symbols=0, tase_mode=0, num_threads=20, forward_eps_included=1, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.17, best_n_select=50, enterprise_value_to_revenue_limit=15)

# Run Build DB Only: All/Others
# =============================
# sss.sss_run(sectors_list=[], build_csv_db_only=1, build_csv_db=1, csv_db_path='Results/20201112-195244_MARKETCAP', read_united_states_input_symbols=1, tase_mode=0, num_threads=20, forward_eps_included=1, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.1, best_n_select=50, enterprise_value_to_revenue_limit=20)


# Research Mode for Nasdaq100/S&P500:
# ===================================
MIN_EVR = 5
MAX_EVR = 8
PM_MIN  = 18
PM_MAX  = 20
research_rows = np.zeros( (MAX_EVR-MIN_EVR+1, PM_MAX-PM_MIN+1), dtype=int )
for enterprise_value_to_revenue_limit in range(MIN_EVR,MAX_EVR+1):
    for profit_margin_limit in range(PM_MIN,PM_MAX+1):
        num_results = sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path='Results/20201115-043117_FAVOUR_TECH_BY3_MARKETCAP_FORWARDEPS_PMARGIN0.17_EVR17.5_BUILD_DB_ONLY_NUM_RESULTS_1115', read_united_states_input_symbols=0, tase_mode=0, num_threads=1, forward_eps_included=0, market_cap_included=1, use_investpy=0, research_mode=1, profit_margin_limit=float(profit_margin_limit)/100.0, best_n_select=3, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit)
        if num_results < 20: break  # already 0 results. With higher profit margin limit there will still be 0
        research_rows[enterprise_value_to_revenue_limit-MIN_EVR][profit_margin_limit-PM_MIN] = int(num_results)
        print('row {:3} -> (enterprise_value_to_revenue_limit {:3}) | col {:3} -> (profit_margin_limit {:3}%): num_results = {}'.format(enterprise_value_to_revenue_limit-MIN_EVR, enterprise_value_to_revenue_limit, profit_margin_limit-PM_MIN, profit_margin_limit, num_results))
date_and_time_str = time.strftime("%Y%m%d-%H%M%S_")
results_filename  = 'Results/research_results_{}_evr{}to{}_pm{}to{}.csv'.format(date_and_time_str, MIN_EVR,MAX_EVR,PM_MIN,PM_MAX)
np.savetxt(results_filename, research_rows.astype(int), fmt='%d', delimiter=',')
title_row = list(range(PM_MIN,PM_MAX+1))
title_row.insert(0, 'evr / pm')
evr_rows_pm_cols = [title_row]
evr_rows_pm_cols_filenames_list = [results_filename]
# Read Results, and add row and col axis:
for filename in evr_rows_pm_cols_filenames_list:
    with open(filename, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter=',')
        row_index = 0
        for row in reader:
            row.insert(0, MIN_EVR+row_index)
            evr_rows_pm_cols.append(row)
            row_index += 1
for index in range(len(evr_rows_pm_cols_filenames_list)):
    row_col_csv_filename = evr_rows_pm_cols_filenames_list[index].replace('.csv','_evr_row_pm_col.csv')
    os.makedirs(os.path.dirname(row_col_csv_filename), exist_ok=True)
    with open(row_col_csv_filename, mode='w', newline='') as engine:
        writer = csv.writer(engine)
        writer.writerows(evr_rows_pm_cols)
