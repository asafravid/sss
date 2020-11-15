######
# V2 #
######


import sss
import numpy as np

# Reuse:
# sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path='Results/20201115-001203_MARKETCAP_FORWARDEPS', read_united_states_input_symbols=0, tase_mode=0, num_threads=1, forward_eps_included=0, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.17, best_n_select=50, enterprise_value_to_revenue_limit=15)

# Run Build DB Only:
# sss.sss_run(sectors_list=[], build_csv_db_only=1, build_csv_db=1, csv_db_path='Results/20201112-195244_MARKETCAP', read_united_states_input_symbols=0, tase_mode=0, num_threads=20, forward_eps_included=1, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.17, best_n_select=50, enterprise_value_to_revenue_limit=15)


# Research Mode:
MIN_EVR = 1
MAX_EVR = 10
PM_MIN  = 5
PM_MAX  = 100
research_rows = np.zeros( (MAX_EVR-MIN_EVR+1, PM_MAX-PM_MIN+1), dtype=int )
for enterprise_value_to_revenue_limit in range(MIN_EVR,MAX_EVR+1):
    for profit_margin_limit in range(PM_MIN,PM_MAX+1):
        num_results = sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path='Results/20201115-001203_MARKETCAP_FORWARDEPS', read_united_states_input_symbols=0, tase_mode=0, num_threads=1, forward_eps_included=0, market_cap_included=1, use_investpy=0, research_mode=1, profit_margin_limit=float(profit_margin_limit)/100.0, best_n_select=50, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit)
        if num_results == 0: break  # already 0 results. With higher profit margin limit there will still be 0
        research_rows[enterprise_value_to_revenue_limit-MIN_EVR][profit_margin_limit-PM_MIN] = int(num_results)
        print('row {:3} -> (enterprise_value_to_revenue_limit {:3}) | col {:3} -> (profit_margin_limit {:3}%): num_results = {}'.format(enterprise_value_to_revenue_limit-MIN_EVR, enterprise_value_to_revenue_limit, profit_margin_limit-PM_MIN, profit_margin_limit, num_results))
np.savetxt('Results/research_results.csv', research_rows.astype(int), fmt='%d', delimiter=',')
