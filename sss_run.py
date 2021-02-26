#########################################################
# Version 220 - Author: Asaf Ravid <asaf.rvd@gmail.com> #
#########################################################


import sss
import numpy as np
import csv
import os
import pdf_generator
import sss_diff


EV_MILLIONS_STEP          = 100
PDF_NUM_ENTRIES_IN_REPORT = 28

SCAN_MODE_TASE = 0  # Tel Aviv Stock Exchange
SCAN_MODE_NSR  = 1  # Nasdaq100 + S&P500 + Russel1000
SCAN_MODE_ALL  = 2  # All Nasdaq Stocks

TITLES = ["_תוצאות_סריקה_עבור_בורסת_תל_אביב", "_Scan_Results_for_Nasdaq100_SNP500_Russel1000", "_Scan_Results_for_All_Nasdaq_Stocks"]

#
# TODO: ASAFR: 0. sss vs ssss/sssss list lengths (appearances) may differ because of the if on the price_to_book which is only for sss -FIX!
#              1. Compare SSS and SSSS and SSSSS recommendations, and formalize some merging between them
#              2. Find stocks with 0 values for trailing Price/Sales (or for instance 0 trailing Price / Earnings) which cancel the whole result and analyze what can be done (manual calculation for instance, etc)
#              3. Further narrow the auto-percentile scanning to not add to percentile_list those tickers whose sss values are illegal (exclusde them)
#              5. Export Results to the SSS excel automatically

# Reuse:
# sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=0, num_threads=1,  market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.17, ev_to_cfo_ratio_limit = 100.0, min_enterprise_value_millions_usd=100, best_n_select=50, enterprise_value_to_revenue_limit=15, favor_technology_sector=4.5, generate_result_folders=1)

# Run Build DB Only: TASE
# =============================
#sss.sss_run(sectors_list=[], sectors_filter_out=0, build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=1, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.01, ev_to_cfo_ratio_limit = 200.0, min_enterprise_value_millions_usd=5, best_n_select=3, enterprise_value_to_revenue_limit=100, favor_sectors=['Technology', 'Real Estate'], favor_sectors_by=[4.5, 0.5], generate_result_folders=1)

# Run Build DB Only: Nasdaq100+S&P500+Russel1000
# ==============================================
# sss.sss_run(sectors_list=[], sectors_filter_out=0, build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=0, tase_mode=0, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.01, ev_to_cfo_ratio_limit=200.0, min_enterprise_value_millions_usd=100, best_n_select=2, enterprise_value_to_revenue_limit=200, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[4.5, 0.5], generate_result_folders=1)

# Run Build DB Only: All/Others
# =============================
# sss.sss_run(sectors_list=[], sectors_filter_out=0, build_csv_db_only=1, build_csv_db=1, csv_db_path='None', read_united_states_input_symbols=1, tase_mode=0, num_threads=20, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.01, ev_to_cfo_ratio_limit = 200.0, min_enterprise_value_millions_usd=75, best_n_select=3, enterprise_value_to_revenue_limit=75, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[4.5, 0.33333], generate_result_folders=1)

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
def get_range(csv_db_path, column_name, num_sections, reverse):
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
    percentile_step = int(100.0/num_sections)
    percentile      = percentile_step
    percentile_range.insert(0, round(sorted_elements_list[0], sss.NUM_ROUND_DECIMALS))
    while percentile < 100:
        percentile_range.append(round(np.percentile(sorted_elements_list, percentile), sss.NUM_ROUND_DECIMALS))
        percentile += percentile_step
    percentile_range_sorted = sorted(percentile_range, reverse=reverse)
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
                    row_index += 1
                    continue
                else:
                    appearance_counter_dict_sss[  (row[0],row[1],row[2],float(row[3]),float(0 if row[28] == '' else row[28]))] = 0.0  # Symbol, Short Name, Sector, SSS   Value, previousClose
                    appearance_counter_dict_ssss[ (row[0],row[1],row[2],float(row[4]),float(0 if row[28] == '' else row[28]))] = 0.0  # Symbol, Short Name, Sector, SSSS  Value, previousClose
                    appearance_counter_dict_sssss[(row[0],row[1],row[2],float(row[5]),float(0 if row[28] == '' else row[28]))] = 0.0  # Symbol, Short Name, Sector, SSSSS Value, previousClose
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
def combine_multi_dim_to_table(multi_dim, dim3, rows,cols):
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


def research_db(sectors_list, sectors_filter_out, evr_range, pm_range, ev_millions_range, csv_db_path, read_united_states_input_symbols, scan_mode, generate_result_folders, appearance_counter_min, appearance_counter_max, favor_sectors, favor_sectors_by,
                newer_path, older_path, db_exists_in_both_folders, diff_only_recommendation, ticker_index, name_index, movement_threshold, newer_rec_ranges, older_rec_ranges, rec_length):
    if scan_mode == SCAN_MODE_TASE:
        tase_mode = 1
    else:
        tase_mode = 0

    appearance_counter_dict_sss   = {}
    appearance_counter_dict_ssss  = {}
    appearance_counter_dict_sssss = {}
    prepare_appearance_counters_dictionaries(csv_db_path, appearance_counter_dict_sss, appearance_counter_dict_ssss, appearance_counter_dict_sssss)
    ev_millions_range_len = len(ev_millions_range)
    evr_range_len         = len(evr_range)
    pm_range_len          = len(pm_range)
    research_rows_sss   = np.zeros( (ev_millions_range_len, evr_range_len, pm_range_len), dtype=int )
    research_rows_ssss  = np.zeros( (ev_millions_range_len, evr_range_len, pm_range_len), dtype=int )
    research_rows_sssss = np.zeros( (ev_millions_range_len, evr_range_len, pm_range_len), dtype=int )
    for ev_millions_index, ev_millions_limit             in enumerate(ev_millions_range):
        for evr_index, enterprise_value_to_revenue_limit in enumerate(evr_range):
            for pm_index, profit_margin_limit            in enumerate(pm_range):
                num_results_for_ev_evr_and_pm = sss.sss_run(sectors_list=sectors_list, sectors_filter_out=sectors_filter_out, build_csv_db_only=0, build_csv_db=0, csv_db_path=csv_db_path, read_united_states_input_symbols=read_united_states_input_symbols, tase_mode=tase_mode, num_threads=1, market_cap_included=1, use_investpy=0, research_mode=1, profit_margin_limit=float(profit_margin_limit)/100.0, min_enterprise_value_millions_usd=ev_millions_limit, ev_to_cfo_ratio_limit = 100.0, best_n_select=3, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_sectors=favor_sectors, favor_sectors_by=favor_sectors_by, generate_result_folders=generate_result_folders, appearance_counter_dict_sss=appearance_counter_dict_sss, appearance_counter_dict_ssss=appearance_counter_dict_ssss, appearance_counter_dict_sssss=appearance_counter_dict_sssss, appearance_counter_min=appearance_counter_min, appearance_counter_max=appearance_counter_max)
                # if num_results_for_ev_evr_and_pm > appearance_counter_max:
                #     break  # already appearance_counter_max results. With lower profit margin limit there will always be more results -> saves running time
                research_rows_sss  [ev_millions_index][evr_index][pm_index] = int(num_results_for_ev_evr_and_pm)
                research_rows_ssss [ev_millions_index][evr_index][pm_index] = int(num_results_for_ev_evr_and_pm)
                research_rows_sssss[ev_millions_index][evr_index][pm_index] = int(num_results_for_ev_evr_and_pm)
                print('ev_millions_limit {:6} | row {:3} -> (enterprise_value_to_revenue_limit {:8}) | col {:3} -> (profit_margin_limit {:7}%): num_results_for_ev_evr_and_pm = {}'.format(ev_millions_limit, evr_index, enterprise_value_to_revenue_limit, pm_index, profit_margin_limit, num_results_for_ev_evr_and_pm))
    results_filename    = 'results_evm{}-{}_evr{}-{}_pm{}-{}.csv'.format(ev_millions_range[0],ev_millions_range[-1],evr_range[0],evr_range[-1],pm_range[0],pm_range[-1])

    mesh_combined = combine_multi_dim_to_table(multi_dim=research_rows_sss, dim3=ev_millions_range, rows=evr_range,cols=pm_range)

    np.savetxt(csv_db_path+'/'+results_filename,  mesh_combined.astype(int), fmt='%d', delimiter=',')
    title_row = pm_range             # column 2 and onwards
    title_row.insert(0, 'evr / pm')  # column 1
    title_row.insert(0, 'ev')        # column 0
    ev_evr_rows_pm_cols_filenames_list = [csv_db_path+'/'+results_filename]
    # Read Results, and add row and col axis:
    for filename in ev_evr_rows_pm_cols_filenames_list:
        ev_evr_rows_pm_cols = [title_row]
        with open(filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0 # title + len(ev_millions_range)*len(evr_range)
            for row in reader:
                row.insert(0, evr_range[    row_index%len(evr_range) ])  # column 1 is evr repetitively cyclic
                row.insert(0, evr_range[int(row_index/len(evr_range))])  # column 0 is the ev, increasing every len(evr_range)
                ev_evr_rows_pm_cols.append(row)
                row_index += 1
    for index in range(len(ev_evr_rows_pm_cols_filenames_list)):
        row_col_csv_filename = ev_evr_rows_pm_cols_filenames_list[index].replace('.csv','_evr_row_pm_col.csv')
        os.makedirs(os.path.dirname(row_col_csv_filename), exist_ok=True)
        with open(row_col_csv_filename, mode='w', newline='') as engine:
            writer = csv.writer(engine)
            writer.writerows(ev_evr_rows_pm_cols)

    sorted_appearance_counter_dict_sss          = {k: v for k, v in sorted(appearance_counter_dict_sss.items(),   key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict_sss   = {k: v for k, v in sorted_appearance_counter_dict_sss.items()    if v > 0.0}

    sorted_appearance_counter_dict_ssss         = {k: v for k, v in sorted(appearance_counter_dict_ssss.items(),  key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict_ssss  = {k: v for k, v in sorted_appearance_counter_dict_ssss.items()   if v > 0.0}

    sorted_appearance_counter_dict_sssss        = {k: v for k, v in sorted(appearance_counter_dict_sssss.items(), key=lambda item: item[1], reverse=True)}
    result_sorted_appearance_counter_dict_sssss = {k: v for k, v in sorted_appearance_counter_dict_sssss.items()  if v > 0.0}

    recommendation_list_filename_sss   = csv_db_path+'/rec_sss_'  +results_filename.replace('results_','')
    recommendation_list_filename_ssss  = csv_db_path+'/rec_ssss_' +results_filename.replace('results_','')
    recommendation_list_filename_sssss = csv_db_path+'/rec_sssss_'+results_filename.replace('results_','')


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
        diff_lists = sss_diff.run(newer_path=newer_path, older_path=older_path, db_exists_in_both_folders=db_exists_in_both_folders, diff_only_recommendation=diff_only_recommendation, ticker_index=ticker_index, name_index=name_index, movement_threshold=movement_threshold, newer_rec_ranges=newer_rec_ranges, older_rec_ranges=older_rec_ranges, rec_length=rec_length, consider_as_new_from=PDF_NUM_ENTRIES_IN_REPORT)

        #                                                                                                  0:15 is date and time
        pdf_generator.csv_to_pdf(csv_filename=recommendation_list_filename_sss,   csv_db_path=csv_db_path, data_time_str=recommendation_list_filename_sss.replace('Results/','')[  0:15], title=TITLES[scan_mode].replace('_',' '),         limit_num_rows=PDF_NUM_ENTRIES_IN_REPORT, diff_list=diff_lists[0], tase_mode=tase_mode)
        pdf_generator.csv_to_pdf(csv_filename=recommendation_list_filename_ssss,  csv_db_path=None,        data_time_str=recommendation_list_filename_ssss.replace('Results/','')[ 0:15], title=TITLES[scan_mode].replace('_',' ')+'ssss' , limit_num_rows=PDF_NUM_ENTRIES_IN_REPORT, diff_list=diff_lists[0], tase_mode=tase_mode)
        pdf_generator.csv_to_pdf(csv_filename=recommendation_list_filename_sssss, csv_db_path=None,        data_time_str=recommendation_list_filename_sssss.replace('Results/','')[0:15], title=TITLES[scan_mode].replace('_',' ')+'sssss', limit_num_rows=PDF_NUM_ENTRIES_IN_REPORT, diff_list=diff_lists[0], tase_mode=tase_mode)



# TASE:
# =====
old_run = 'Results/20210219-171143_Tase_Technology4.5_RealEstate0.3333_MCap_pm0.0567_evr15.0_BuildDb_nResults259_Backup'
new_run = 'Results/20210226-100125_Tase_Technology4.5_RealEstate0.5_MCap_pm0.01_evr100_Bdb_nRes273'
evr_range_tase         = get_range(csv_db_path=new_run, column_name='evr_effective',            num_sections=10, reverse=1)
pm_ratios_range_tase   = get_range(csv_db_path=new_run, column_name='annualized_profit_margin', num_sections=10, reverse=0)
ev_range_tase          = get_range(csv_db_path=new_run, column_name='enterprise_value',         num_sections=4,  reverse=0)
pm_range_tase          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_tase]
ev_millions_range_tase = [int(  ev/1000000                       ) for ev in ev_range_tase       ]
research_db(sectors_list=[], sectors_filter_out=0, evr_range=evr_range_tase, pm_range=pm_range_tase, ev_millions_range=ev_millions_range_tase,   csv_db_path=new_run,   read_united_states_input_symbols=0, scan_mode=SCAN_MODE_TASE, generate_result_folders=0, appearance_counter_min=1, appearance_counter_max=400, favor_sectors=['Technology', 'Real Estate'], favor_sectors_by=[4.5, 0.5],
            newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, ticker_index=0, name_index=1, movement_threshold=0, newer_rec_ranges=[ev_millions_range_tase[0],ev_millions_range_tase[-1],evr_range_tase[0],evr_range_tase[-1],pm_range_tase[0],pm_range_tase[-1]], older_rec_ranges=[5,5000,1,54,1,50], rec_length=80)
#sss_diff.run(newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, ticker_index=0, name_index=1, movement_threshold=0, newer_rec_ranges=[5,1,54,1,50], older_rec_ranges=[5,1,45,5,45], rec_length=80)

# Generate TASE:
# research_db(evr_range=[8,8],  pm_range=[10,10], ev_millions_range=5, csv_db_path=new_run,   read_united_states_input_symbols=0, scan_mode=SCAN_MODE_TASE, generate_result_folders=1, appearance_counter_min=1, appearance_counter_max=250, favor_technology_sector=4.5,
#             newer_path=new_run, older_path=None, db_exists_in_both_folders=1, diff_only_recommendation=1, ticker_index=0, name_index=1, movement_threshold=0, newer_rec_ranges=[5,1,54,1,50], older_rec_ranges=[5,1,54,1,50], rec_length=80)



# NASDAQ100+S&P500+RUSSEL1000:
# ============================
# old_run = 'Results/20210213-011620_FTB4.5_MCap_pm0.17_evr17.5_BuildDb_nResults944'
# new_run = 'Results/20210224-114630_Technology4.5_FinancialServices0.5_MCap_pm0.01_evr200_BuildDb_nResults969'
# evr_range_n         = get_range(csv_db_path=new_run, column_name='evr_effective',            num_sections=6)
# pm_ratios_range_n   = get_range(csv_db_path=new_run, column_name='annualized_profit_margin', num_sections=6)
# ev_range_n          = get_range(csv_db_path=new_run, column_name='enterprise_value',         num_sections=4)
# pm_range_n          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_n]
# ev_millions_range_n = [int(  ev/1000000                       ) for ev in ev_range_n       ]
# research_db(sectors_list=[], sectors_filter_out=0, evr_range=evr_range_n, pm_range=pm_range_n, ev_millions_range=ev_millions_range_n,  csv_db_path=new_run,   read_united_states_input_symbols=0, scan_mode=SCAN_MODE_NSR, generate_result_folders=0, appearance_counter_min=1, appearance_counter_max=450, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[4.5, 0.33333],
#             newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, ticker_index=0, name_index=1, movement_threshold=0, newer_rec_ranges=[ev_millions_range_n[0],ev_millions_range_n[-1],evr_range_n[0],evr_range_n[-1],pm_range_n[0],pm_range_n[-1]], older_rec_ranges=[100,100,1,54,1,50], rec_length=80)
# sss_diff.run(newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, ticker_index=0, name_index=1, movement_threshold=3, newer_rec_ranges=[100,1,54,1,50], older_rec_ranges=[100,1,54,1,50], rec_length=80)

# Generate:
# research_db(evr_range=[24,24],  pm_range=[31,31], ev_millions_range=100, csv_db_path=new_run,   read_united_states_input_symbols=0, tase_mode=0, generate_result_folders=1, appearance_counter_min=15, appearance_counter_max=45, favor_technology_sector=4.5)

# ALL:
# ====
# old_run = 'Results/20210220-161246_Technology4.5_FinancialServices0.5_All_MCap_pm0.24_evr15.0_BuildDb_nResults4132'
# new_run = 'Results/20210224-102449_Technology4.5_FinancialServices0.3333_All_MCap_pm0.01_evr75_BuildDb_nResults3871'
# evr_range_all         = get_range(csv_db_path=new_run, column_name='evr_effective',            num_sections=6)
# pm_ratios_range_all   = get_range(csv_db_path=new_run, column_name='annualized_profit_margin', num_sections=6)
# ev_range_all          = get_range(csv_db_path=new_run, column_name='enterprise_value',         num_sections=4)
# pm_range_all          = [round(pm*100,    sss.NUM_ROUND_DECIMALS) for pm in pm_ratios_range_all]
# ev_millions_range_all = [int(  ev/1000000                       ) for ev in ev_range_all       ]
# research_db(sectors_list=[], sectors_filter_out=0, evr_range=evr_range_all, pm_range=pm_range_all, ev_millions_range=ev_millions_range_all, csv_db_path=new_run, read_united_states_input_symbols=1, scan_mode=SCAN_MODE_ALL, generate_result_folders=0, appearance_counter_min=1, appearance_counter_max=1000, favor_sectors=['Technology', 'Financial Services'], favor_sectors_by=[4.5, 0.33333],
#             newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, ticker_index=0, name_index=1, movement_threshold=0, newer_rec_ranges=[ev_millions_range_all[0],ev_millions_range_all[-1],evr_range_all[0],evr_range_all[-1],pm_range_all[0],pm_range_all[-1]], older_rec_ranges=[75,250000,1,45,1,50], rec_length=80)
#sss_diff.run(newer_path=new_run, older_path=old_run, db_exists_in_both_folders=1, diff_only_recommendation=1, ticker_index=0, name_index=1, movement_threshold=3, newer_rec_ranges=[100,1,54,1,50], older_rec_ranges=[100, 1, 54, 1, 50], rec_length=80)

# Generate ALL:
# research_db(evr_range=[30,30], pm_range=[40,40], ev_millions_range=100, csv_db_path=new_run,  read_united_states_input_symbols=1, tase_mode=0, generate_result_folders=1, appearance_counter_min=5, appearance_counter_max=75, favor_technology_sector=4.5)


