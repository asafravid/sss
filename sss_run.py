#########################################################
# Version 121 - Author: Asaf Ravid <asaf.rvd@gmail.com> #
#########################################################


import sss
import numpy as np
import csv
import os
import sss_diff


EV_MILLIONS_STEP = 100

# TODO: ASAFR: EVR Steps should be 1, 2, 3, 4, 5, 7,10,14,19,24,30,37,45,54 since in the high values the results remain the same and are biasing the appearnces counters ...
#              PM Steps should be  1,10,18,25,31,36,40,43,45,46,47,48,49,50 since the changes are delicate towards high PMs

# Reuse:
# sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=0, num_threads=1,  market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.17, ev_to_cfo_ratio_limit = 100.0, min_enterprise_value_millions_usd=100, best_n_select=50, enterprise_value_to_revenue_limit=15, favor_technology_sector=4.5, generate_result_folders=1)

# Run Build DB Only: Nasdaq100+S&P500+Russel1000
# ==============================================
# sss.sss_run(sectors_list=[], build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=0, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.12, ev_to_cfo_ratio_limit = 100.0, min_enterprise_value_millions_usd=100, best_n_select=3, enterprise_value_to_revenue_limit=20, favor_technology_sector=4.5, generate_result_folders=1)

# Run Build DB Only: All/Others
# =============================
# sss.sss_run(sectors_list=[], build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=1, tase_mode=0, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.10, ev_to_cfo_ratio_limit = 100.0, min_enterprise_value_millions_usd=100, best_n_select=3, enterprise_value_to_revenue_limit=20, favor_technology_sector=4.5, generate_result_folders=1)

# Run Build DB Only: TASE
# =============================
# sss.sss_run(sectors_list=[], build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=1, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.10, ev_to_cfo_ratio_limit = 100.0, min_enterprise_value_millions_usd=10, best_n_select=3, enterprise_value_to_revenue_limit=25, favor_technology_sector=4.5, generate_result_folders=1)


# Research Mode:
# ==============

def prepare_appearance_counters_dictionaries(csv_db_path, appearance_counter_dict_sss, appearance_counter_dict_ssss, appearance_counter_dict_sssss):
    csv_db_filename = csv_db_path + '/db.csv'
    with open(csv_db_filename, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter=',')
        row_index = 0
        for row in reader:
            if row_index <= 1:  # first row is just a title of evr and pm, then a title of columns
                row_index += 1
                continue
            else:
                appearance_counter_dict_sss[  (row[0],row[1],row[2],float(row[3]))] = 0.0  # Symbol, Short Name, Sector, SSS   Value
                appearance_counter_dict_ssss[ (row[0],row[1],row[2],float(row[4]))] = 0.0  # Symbol, Short Name, Sector, SSSS  Value
                appearance_counter_dict_sssss[(row[0],row[1],row[2],float(row[5]))] = 0.0  # Symbol, Short Name, Sector, SSSSS Value


def research_db(evr_range, pm_range, ev_millions_range, csv_db_path, read_united_states_input_symbols, tase_mode, generate_result_folders, appearance_counter_min, appearance_counter_max, favor_technology_sector):
    appearance_counter_dict_sss   = {}
    appearance_counter_dict_ssss  = {}
    appearance_counter_dict_sssss = {}
    prepare_appearance_counters_dictionaries(csv_db_path, appearance_counter_dict_sss, appearance_counter_dict_ssss, appearance_counter_dict_sssss)
    research_rows_sss   = np.zeros( (evr_range[1]-evr_range[0]+1, pm_range[1]-pm_range[0]+1), dtype=int )
    research_rows_ssss  = np.zeros( (evr_range[1]-evr_range[0]+1, pm_range[1]-pm_range[0]+1), dtype=int )
    research_rows_sssss = np.zeros( (evr_range[1]-evr_range[0]+1, pm_range[1]-pm_range[0]+1), dtype=int )
    for enterprise_value_to_revenue_limit in range(evr_range[0],evr_range[1]+1):
        for profit_margin_limit in range(pm_range[1],pm_range[0]-1,-1):
            min_enterprise_value_millions_usd = ev_millions_range  # ev_millions_range[0]+EV_MILLIONS_STEP*(ev_millions_limit_index-1)
            num_results_for_evr_and_pm = sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path=csv_db_path, read_united_states_input_symbols=read_united_states_input_symbols, tase_mode=tase_mode, num_threads=1, market_cap_included=1, use_investpy=0, research_mode=1, profit_margin_limit=float(profit_margin_limit)/100.0, min_enterprise_value_millions_usd=min_enterprise_value_millions_usd, ev_to_cfo_ratio_limit = 100.0, best_n_select=3, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_technology_sector=favor_technology_sector, generate_result_folders=generate_result_folders, appearance_counter_dict_sss=appearance_counter_dict_sss, appearance_counter_dict_ssss=appearance_counter_dict_ssss, appearance_counter_dict_sssss=appearance_counter_dict_sssss, appearance_counter_min=appearance_counter_min, appearance_counter_max=appearance_counter_max)
            if num_results_for_evr_and_pm > appearance_counter_max: break  # already appearance_counter_max results. With lower profit margin limit there will always be more results -> saves running time
            research_rows_sss [ enterprise_value_to_revenue_limit-evr_range[0]][profit_margin_limit-pm_range[0]] = int(num_results_for_evr_and_pm)
            research_rows_ssss[ enterprise_value_to_revenue_limit-evr_range[0]][profit_margin_limit-pm_range[0]] = int(num_results_for_evr_and_pm)
            research_rows_sssss[enterprise_value_to_revenue_limit-evr_range[0]][profit_margin_limit-pm_range[0]] = int(num_results_for_evr_and_pm)
            print('min_enterprise_value_millions_usd {:5} | row {:3} -> (enterprise_value_to_revenue_limit {:3}) | col {:3} -> (profit_margin_limit {:3}%): num_results_for_evr_and_pm = {}'.format(min_enterprise_value_millions_usd, enterprise_value_to_revenue_limit-evr_range[0], enterprise_value_to_revenue_limit, profit_margin_limit-pm_range[0], profit_margin_limit, num_results_for_evr_and_pm))
    results_filename    = 'results_evm{}_evr{}-{}_pm{}-{}.csv'.format(min_enterprise_value_millions_usd,evr_range[0],evr_range[1],pm_range[0],pm_range[1])
    np.savetxt(csv_db_path+'/'+results_filename,  research_rows_ssss.astype(int), fmt='%d', delimiter=',')
    title_row = list(range(pm_range[0],pm_range[1]+1))
    title_row.insert(0, 'evr / pm')
    evr_rows_pm_cols_filenames_list = [csv_db_path+'/'+results_filename]
    # Read Results, and add row and col axis:
    for filename in evr_rows_pm_cols_filenames_list:
        evr_rows_pm_cols = [title_row]
        with open(filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                row.insert(0, evr_range[0]+row_index)
                evr_rows_pm_cols.append(row)
                row_index += 1
    for index in range(len(evr_rows_pm_cols_filenames_list)):
        row_col_csv_filename = evr_rows_pm_cols_filenames_list[index].replace('.csv','_evr_row_pm_col.csv')
        os.makedirs(os.path.dirname(row_col_csv_filename), exist_ok=True)
        with open(row_col_csv_filename, mode='w', newline='') as engine:
            writer = csv.writer(engine)
            writer.writerows(evr_rows_pm_cols)

    sorted_appearance_counter_dict_sss          = {k: v for k, v in sorted(appearance_counter_dict_sss.items(),   key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict_sss   = {k: v for k, v in sorted_appearance_counter_dict_sss.items()    if v > 0.0}

    sorted_appearance_counter_dict_ssss         = {k: v for k, v in sorted(appearance_counter_dict_ssss.items(),  key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict_ssss  = {k: v for k, v in sorted_appearance_counter_dict_ssss.items()   if v > 0.0}

    sorted_appearance_counter_dict_sssss        = {k: v for k, v in sorted(appearance_counter_dict_sssss.items(), key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict_sssss = {k: v for k, v in sorted_appearance_counter_dict_sssss.items()  if v > 0.0}

    recommendation_list_filename_sss = csv_db_path+'/recommendation_sss_'+results_filename.replace('results_','')
    with open(recommendation_list_filename_sss, 'w') as f:
        f.write("Ticker,Name,Sector,sss_value,appearance_counter\n")
        for key in result_sorted_appearance_counter_dict_sss.keys():
            f.write("%s,%s,%s,%s,%s\n"%(key[0],str(key[1]).replace(',',' '),key[2],key[3],round(result_sorted_appearance_counter_dict_sss[  key],4)))

    recommendation_list_filename_ssss = csv_db_path+'/recommendation_ssss_'+results_filename.replace('results_','')
    with open(recommendation_list_filename_ssss, 'w') as f:
        f.write("Ticker,Name,Sector,ssss_value,appearance_counter\n")
        for key in result_sorted_appearance_counter_dict_ssss.keys():
            f.write("%s,%s,%s,%s,%s\n"%(key[0],str(key[1]).replace(',',' '),key[2],key[3],round(result_sorted_appearance_counter_dict_ssss[ key],4)))

    recommendation_list_filename_sssss = csv_db_path+'/recommendation_sssss_'+results_filename.replace('results_','')
    with open(recommendation_list_filename_sssss, 'w') as f:
        f.write("Ticker,Name,Sector,sssss_value,appearance_counter\n")
        for key in result_sorted_appearance_counter_dict_sssss.keys():
            f.write("%s,%s,%s,%s,%s\n"%(key[0],str(key[1]).replace(',',' '),key[2],key[3],round(result_sorted_appearance_counter_dict_sssss[key],4)))

# TASE:
# =====
# old_run = 'Results/20210131-161653_Tase_FTB4_MCap_pm0.0567_evr15.0_BuildDb_nResults457'
# new_run = 'Results/20210204-231709_Tase_FTB4_MCap_pm0.0567_evr15.0_BuildDb_nResults457'
# research_db(evr_range=[1,45], pm_range=[5,45], ev_millions_range=5,   csv_db_path=new_run,   read_united_states_input_symbols=0, tase_mode=1, generate_result_folders=0, appearance_counter_min=3, appearance_counter_max=75, favor_technology_sector=4.5)
# sss_diff.run(newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, ticker_index=0, name_index=1, movement_threshold=2, newer_rec_ranges=[5,1,45,5,45], older_rec_ranges=[10,1,45,5,45], rec_length=80)

# NASDAQ100+S&P500+RUSSEL1000:
# ============================
old_run = 'Results/20210131-112103_FTB4_MCap_pm0.17_evr17.5_BuildDb_nResults1126'
new_run = 'Results/20210205-002145_FTB4.5_MCap_pm0.17_evr17.5_BuildDb_nResults1126'
research_db(evr_range=[1,50], pm_range=[5,60], ev_millions_range=100,  csv_db_path=new_run,   read_united_states_input_symbols=0, tase_mode=0, generate_result_folders=0, appearance_counter_min=4, appearance_counter_max=75, favor_technology_sector=4.5)
sss_diff.run(newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, ticker_index=0, name_index=1, movement_threshold=3, newer_rec_ranges=[100,1,50,5,60], older_rec_ranges=[100,1,50,5,60], rec_length=80)

# Generate:
# research_db(evr_range=[11,11],  pm_range=[29,29], ev_millions_range=100, csv_db_path=new_run,   read_united_states_input_symbols=0, tase_mode=0, generate_result_folders=1, appearance_counter_min=15, appearance_counter_max=45, favor_technology_sector=4.5)

# ALL:
# ====
#old_run = 'Results/20210126-064649_FTB4_All_MCap_pm0.24_evr15.0_BuildDb_nResults8780'
#new_run = 'Results/20210201-033253_FTB4_All_MCap_pm0.24_evr15.0_BuildDb_nResults8780'
# research_db(evr_range=[1,55], pm_range=[5,65], ev_millions_range=100, csv_db_path=new_run,  read_united_states_input_symbols=1, tase_mode=0, generate_result_folders=0, appearance_counter_min=3, appearance_counter_max=70, favor_technology_sector=4.5)
# sss_diff.run(newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, ticker_index=0, name_index=1, movement_threshold=3, newer_rec_ranges=[100, 1, 55, 5, 65], older_rec_ranges=[100, 1, 55, 5, 55], rec_length=75)

# Generate ALL:
#research_db(evr_range=[12,12], pm_range=[42,42], ev_millions_range=100, csv_db_path=new_run,  read_united_states_input_symbols=1, tase_mode=0, generate_result_folders=1, appearance_counter_min=5, appearance_counter_max=75, favor_technology_sector=4.5)


