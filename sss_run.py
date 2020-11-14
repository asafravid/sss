import sss

# Reuse:
# sss.sss_run(sectors_list=[], build_csv_db_only=0, build_csv_db=0, csv_db_path='Results/20201112-195244_MARKETCAP', read_united_states_input_symbols=0, tase_mode=0, num_threads=1, forward_eps_included=0, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.17, best_n_select=50, enterprise_value_to_revenue_limit=15)

# Run Build DB Only:
sss.sss_run(sectors_list=[], build_csv_db_only=1, build_csv_db=1, csv_db_path='Results/20201112-195244_MARKETCAP', read_united_states_input_symbols=0, tase_mode=0, num_threads=20, forward_eps_included=1, market_cap_included=1, use_investpy=0, research_mode=0, profit_margin_limit=0.17, best_n_select=50, enterprise_value_to_revenue_limit=15)