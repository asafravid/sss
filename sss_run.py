#######
# V15 #
#######


import sss
import numpy as np
import time
import csv
import os



# Reuse:
# sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=0, num_threads=1, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.17, best_n_select=50, enterprise_value_to_revenue_limit=15, generate_result_folders=1)

# Run Build DB Only: Nasdaq100/S&P500
# ===================================
# sss.sss_run(sectors_list=[], build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=0, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.12, best_n_select=3, enterprise_value_to_revenue_limit=20, generate_result_folders=1)

# Run Build DB Only: All/Others
# =============================
# sss.sss_run(sectors_list=[], build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=1, tase_mode=0, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.10, best_n_select=3, enterprise_value_to_revenue_limit=20, generate_result_folders=1)

# Run Build DB Only: TASE
# =============================
# sss.sss_run(sectors_list=[], build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=1, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.10, best_n_select=3, enterprise_value_to_revenue_limit=25, generate_result_folders=1)


# Research Mode:
# ==============
def prepare_appearance_counters_dictionary(csv_db_path, appearance_counter_dict):
    csv_db_filename = csv_db_path + '/db.csv'
    with open(csv_db_filename, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter=',')
        row_index = 0
        for row in reader:
            if row_index <= 1:  # first row is just a title of evr and pm, then a title of columns
                row_index += 1
                continue
            else:
                appearance_counter_dict[(row[0],row[1],row[2],float(row[5]))] = 0.0  # Symbol, Short Name, Sector, SSSSS Value


def research_db(min_evr, max_evr, pm_min, pm_max, csv_db_path, read_united_states_input_symbols, tase_mode, generate_result_folders, appearance_counter_min, appearance_counter_max):
    appearance_counter_dict = {}
    prepare_appearance_counters_dictionary(csv_db_path, appearance_counter_dict)
    research_rows = np.zeros( (max_evr-min_evr+1, pm_max-pm_min+1), dtype=int )
    for enterprise_value_to_revenue_limit in range(min_evr,max_evr+1):
        for profit_margin_limit in range(pm_min,pm_max+1):
            num_results = sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path=csv_db_path, read_united_states_input_symbols=read_united_states_input_symbols, tase_mode=tase_mode, num_threads=1, market_cap_included=1, use_investpy=0, research_mode=1, profit_margin_limit=float(profit_margin_limit)/100.0, best_n_select=3, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, generate_result_folders=generate_result_folders, appearance_counter_dict=appearance_counter_dict, appearance_counter_min=appearance_counter_min, appearance_counter_max=appearance_counter_max)
            if num_results < 1: break  # already 0 results. With higher profit margin limit there will still be 0
            research_rows[enterprise_value_to_revenue_limit-min_evr][profit_margin_limit-pm_min] = int(num_results)
            print('row {:3} -> (enterprise_value_to_revenue_limit {:3}) | col {:3} -> (profit_margin_limit {:3}%): num_results = {}'.format(enterprise_value_to_revenue_limit-min_evr, enterprise_value_to_revenue_limit, profit_margin_limit-pm_min, profit_margin_limit, num_results))
    results_filename   = 'results_evr{}-{}_pm{}-{}.csv'.format(min_evr,max_evr,pm_min,pm_max)
    np.savetxt(csv_db_path+'/'+results_filename, research_rows.astype(int), fmt='%d', delimiter=',')
    title_row = list(range(pm_min,pm_max+1))
    title_row.insert(0, 'evr / pm')
    evr_rows_pm_cols = [title_row]
    evr_rows_pm_cols_filenames_list = [csv_db_path+'/'+results_filename]
    # Read Results, and add row and col axis:
    for filename in evr_rows_pm_cols_filenames_list:
        with open(filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                row.insert(0, min_evr+row_index)
                evr_rows_pm_cols.append(row)
                row_index += 1
    for index in range(len(evr_rows_pm_cols_filenames_list)):
        row_col_csv_filename = evr_rows_pm_cols_filenames_list[index].replace('.csv','_evr_row_pm_col.csv')
        os.makedirs(os.path.dirname(row_col_csv_filename), exist_ok=True)
        with open(row_col_csv_filename, mode='w', newline='') as engine:
            writer = csv.writer(engine)
            writer.writerows(evr_rows_pm_cols)
    sorted_appearance_counter_dict = {k: v for k, v in sorted(appearance_counter_dict.items(), key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict = {k: v for k, v in sorted_appearance_counter_dict.items() if v > 0.0}

    reccomendation_list_filename = csv_db_path+'/reccomendation_sssss_'+results_filename.replace('results_','')
    with open(reccomendation_list_filename, 'w') as f:
        f.write("Ticker,Name,Sector,sssss_value,appearance_counter\n")
        for key in result_sorted_appearance_counter_dict.keys():
            f.write("%s,%s,%s,%s,%s\n"%(key[0],str(key[1]).replace(',',' '),key[2],key[3],result_sorted_appearance_counter_dict[key]))

# TASE:
# =====
# research_db(min_evr=1, max_evr=25, pm_min=5,  pm_max=45, csv_db_path='Results/20201222-140521_Tase_FavorTechBy3_MCap_pm0.0567_evr15.0_BuildDb_nResults455',   read_united_states_input_symbols=0, tase_mode=1, generate_result_folders=0, appearance_counter_min=20, appearance_counter_max=40)

# NASDAQ100+S&P500+RUSSEL1000:
# ============================
research_db(min_evr=1, max_evr=45, pm_min=5, pm_max=45, csv_db_path='Results/20201222-132710_FavorTechBy3_MCap_pm0.17_evr17.5_BuildDb_nResults1119',         read_united_states_input_symbols=0, tase_mode=0, generate_result_folders=0, appearance_counter_min=20, appearance_counter_max=40)

# Generate SSSSS:
# research_db(min_evr=5, max_evr=5,  pm_min=17, pm_max=17, csv_db_path='Results/20201222-132710_FavorTechBy3_MCap_pm0.17_evr17.5_BuildDb_nResults1119',         read_united_states_input_symbols=0, tase_mode=0, generate_result_folders=1, appearance_counter_min=20, appearance_counter_max=40)

# ALL:
# ====
# research_db(min_evr=1, max_evr=45, pm_min=5, pm_max=45, csv_db_path='Results/20201222-235543_FavorTechBy3_All_MCap_pm0.24_evr15.0_BuildDb_nResults8669',  read_united_states_input_symbols=1, tase_mode=0, generate_result_folders=0, appearance_counter_min=20, appearance_counter_max=40)

# Generate SSSSS ALL:
# research_db(min_evr=5, max_evr=5, pm_min=27, pm_max=27, csv_db_path='Results/20201222-235543_FavorTechBy3_All_MCap_pm0.24_evr15.0_BuildDb_nResults8669',  read_united_states_input_symbols=1, tase_mode=0, generate_result_folders=1, appearance_counter_min=20, appearance_counter_max=40)
