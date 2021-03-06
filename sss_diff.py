#########################################################
# Version 240 - Author: Asaf Ravid <asaf.rvd@gmail.com> #
#########################################################



import sss_filenames
import csv
import os
# import pdf_generator


def get_row_index(ticker_index, ticker, rows):
    index = 0
    for row in rows:
        if ticker == row[ticker_index]:
            return index+1 # avoid row index 0
        index += 1
    return -1


def run(newer_path, older_path, db_exists_in_both_folders, diff_only_recommendation, movement_threshold, newer_rec_ranges, older_rec_ranges, rec_length, consider_as_new_from):
    newer_filenames_list = sss_filenames.create_filenames_list(newer_path)
    older_filenames_list = sss_filenames.create_filenames_list(older_path)
    diff_path = 'Results/diff'+'_new'+newer_path.replace('Results/','_')+'_old'+older_path.replace('Results/','_')
    compact_diff_path = diff_path.replace('FavorTechBy3','FTB3').replace('MCap_','').replace('BuildDb_','').replace('nResults','')
    diff_filenames_list  = sss_filenames.create_filenames_list(compact_diff_path)
    # The order is important: sss, then ssss, then sssss                                                    evm_min              evm_max              evr_min,             evr_max,             pm_min,              pm_max
    newer_filenames_list.insert(0, newer_path +'/rec_sssss_evm{}-{}_evr{}-{}_pm{}-{}.csv'.format(newer_rec_ranges[0], newer_rec_ranges[1], newer_rec_ranges[2], newer_rec_ranges[3], newer_rec_ranges[4], newer_rec_ranges[5]))
    newer_filenames_list.insert(0, newer_path +'/rec_ssss_evm{}-{}_evr{}-{}_pm{}-{}.csv'.format( newer_rec_ranges[0], newer_rec_ranges[1], newer_rec_ranges[2], newer_rec_ranges[3], newer_rec_ranges[4], newer_rec_ranges[5]))
    newer_filenames_list.insert(0, newer_path +'/rec_sss_evm{}-{}_evr{}-{}_pm{}-{}.csv'.format(  newer_rec_ranges[0], newer_rec_ranges[1], newer_rec_ranges[2], newer_rec_ranges[3], newer_rec_ranges[4], newer_rec_ranges[5]))
    older_filenames_list.insert(0, older_path +'/rec_sssss_evm{}-{}_evr{}-{}_pm{}-{}.csv'.format(older_rec_ranges[0], older_rec_ranges[1], older_rec_ranges[2], older_rec_ranges[3], older_rec_ranges[4], older_rec_ranges[5]))
    older_filenames_list.insert(0, older_path +'/rec_ssss_evm{}-{}_evr{}-{}_pm{}-{}.csv'.format( older_rec_ranges[0], older_rec_ranges[1], older_rec_ranges[2], older_rec_ranges[3], older_rec_ranges[4], older_rec_ranges[5]))
    older_filenames_list.insert(0, older_path +'/rec_sss_evm{}-{}_evr{}-{}_pm{}-{}.csv'.format(  older_rec_ranges[0], older_rec_ranges[1], older_rec_ranges[2], older_rec_ranges[3], older_rec_ranges[4], older_rec_ranges[5]))

    diff_filenames_list.insert(0,'{}/rec_sssss.csv'.format(compact_diff_path))
    diff_filenames_list.insert(0,'{}/rec_ssss.csv'.format( compact_diff_path))
    diff_filenames_list.insert(0,'{}/rec_sss.csv'.format( compact_diff_path))

    if len(older_filenames_list) != len(newer_filenames_list):
        raise Exception("Different Lengths of lists - Unacceptable")

    diff_lists = [[],[],[]]  # index 0: sss, 1: ssss, 2: sssss

    if diff_only_recommendation: length_to_iterate = 3  # SSS, SSSS and SSSSS
    else:                        length_to_iterate = len(newer_filenames_list)
    for index in range(length_to_iterate):
        if db_exists_in_both_folders == 0 and index == 0: continue
        output_csv_rows = [['ticker','change','from','to']]
        print("\n{:20}:\n======================================".format(newer_filenames_list[index]))

        # 1st, Read the Older File, which will be the reference:
        older_rows = []
        with open(older_filenames_list[index], mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                if row_index == 0:
                    row_index += 1
                    continue
                else:
                    older_rows.append(row)
                    if row_index >= rec_length: break
                    row_index += 1

        # 2nd, read the Newer File and check if (and where) each line appears in the Older file (if at all)
        newer_rows = []
        with open(newer_filenames_list[index], mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                if row_index == 0:
                    diff_lists[index].append('Diff')
                    ticker_index = row.index("Ticker")
                    name_index   = row.index("Name")
                    if   "sss_index"   in row: sss_index = row.index("sss_value")
                    elif "ssss_index"  in row: sss_index = row.index("ssss_value")
                    elif "sssss_index" in row: sss_index = row.index("sssss_value") # 3 different comparisons
                    row_index += 1
                    continue
                else:
                    newer_rows.append(row)
                    ticker = row[ticker_index]
                    name   = row[name_index]
                    row_in_older_file = get_row_index(ticker_index, ticker, older_rows)
                    oldr = older_rows[row_in_older_file-1]  # -1 converts from row to row_index
                    if row_in_older_file >= 0:  # This stock in the new list, appears in the old list as well
                        if abs(row_in_older_file - row_index) > movement_threshold:
                            print("{:5} ({:15}):  {:2} positions change from {:3} to {:3}".format(ticker, name, row_in_older_file-row_index, row_in_older_file, row_index))
                            if not diff_only_recommendation: #                                                                             sss_value=row[3], ssss_value=row[4], sssss_value=row[5], ssse_value=row[6], sssse_value=row[7], ssssse_value=row[8], sssi_value=row[9], ssssi_value=row[10],sssssi_value=row[11],sssei_value=row[12],ssssei_value=row[13],sssssei_value=row[14],annualized_revenue=row[15],annualized_earnings=row[16],enterprise_value_to_revenue=row[17],evr_effective=row[18],trailing_price_to_earnings=row[19],trailing_12months_price_to_sales=row[20],tpe_effective=row[21],enterprise_value_to_ebitda=row[22],profit_margin=row[23],annualized_profit_margin=row[24],held_percent_institutions=row[25],forward_eps=row[26],trailing_eps=row[27],previous_close=row[28],trailing_eps_percentage=row[29],price_to_book=row[30],shares_outstanding=row[31],net_income_to_common_shareholders=row[32],nitcsh_to_shares_outstanding=row[33],num_employees=row[34],enterprise_value=row[35],market_cap=row[36],nitcsh_to_num_employees=row[37],earnings_quarterly_growth=row[38],revenue_quarterly_growth=row[39],price_to_earnings_to_growth_ratio=row[40],sqrt_peg_ratio=row[41],annualized_cash_flow_from_operating_activities=row[42],ev_to_cfo_ratio=row[43],last_4_dividends_0=row[44],last_4_dividends_1=row[45],last_4_dividends_2=row[46],last_4_dividends_3=row[47]

                                print('                                                                                    From            sss_value: {:15}, ssss_value: {:15}, sssss_value: {:15}, ssse_value: {:15}, sssse_value: {:15}, ssssse_value: {:15}, sssi_value: {:15}, ssssi_value: {:15}, sssssi_value: {:15}, sssei_value: {:15}, ssssei_value: {:15}, sssssei_value: {:15}, annualized_revenue: {:15}, annualized_earnings: {:15}, enterprise_value_to_revenue: {:15}, evr_effective: {:15}, trailing_price_to_earnings: {:15}, trailing_12months_price_to_sales: {15:}, tpe_effective: {:15}, enterprise_value_to_ebitda: {:15}, profit_margin: {:15}, annualized_profit_margin: {:15}, held_percent_institutions: {:15}, forward_eps: {:15}, trailing_eps: {:15}, previous_close: {:15}, trailing_eps_percentage: {:15}, price_to_book: {:15}, shares_outstanding: {:15}, net_income_to_common_shareholders: {:15}, nitcsh_to_shares_outstanding: {:15}, num_employees: {:15}, enterprise_value: {:15}, market_cap: {:15}, nitcsh_to_num_employees: {:15}, earnings_quarterly_growth: {:15}, revenue_quarterly_growth: {:15}, price_to_earnings_to_growth_ratio: {:15}, sqrt_peg_ratio: {:15}, annualized_cash_flow_from_operating_activities: {:15}, ev_to_cfo_ratio: {:15}'.format(
                                                                                                                                           oldr[sss_index+0],oldr[sss_index+1], oldr[sss_index+2],  oldr[sss_index+3], oldr[sss_index+4],  oldr[sss_index+5],   oldr[sss_index+6], oldr[sss_index+7],  oldr[sss_index+8],   oldr[sss_index+9],  oldr[sss_index+10],  oldr[sss_index+11],   oldr[sss_index+12],        oldr[sss_index+13],         oldr[sss_index+14],                 oldr[sss_index+15],   older[sss_index+16],               oldr[sss_index+17],                      oldr[sss_index+18],   oldr[sss_index+19],                oldr[sss_index+20],   oldr[sss_index+21],              oldr[sss_index+22],               oldr[sss_index+23], oldr[sss_index+24],  oldr[sss_index+25],    oldr[sss_index+26],             oldr[sss_index+27],   oldr[sss_index+28],        oldr[sss_index+29],                       oldr[sss_index+30],                  oldr[sss_index+31],   oldr[sss_index+32],      oldr[sss_index+33],oldr[sss_index+34],             oldr[sss_index+35],               oldr[sss_index+36],              oldr[sss_index+37],                       oldr[sss_index+38],    oldr[sss_index+39],                                    oldr[sss_index+40]))
                                print('                                                                                    To              sss_value: {:15}, ssss_value: {:15}, sssss_value: {:15}, ssse_value: {:15}, sssse_value: {:15}, ssssse_value: {:15}, sssi_value: {:15}, ssssi_value: {:15}, sssssi_value: {:15}, sssei_value: {:15}, ssssei_value: {:15}, sssssei_value: {:15}, annualized_revenue: {:15}, annualized_earnings: {:15}, enterprise_value_to_revenue: {:15}, evr_effective: {:15}, trailing_price_to_earnings: {:15}, trailing_12months_price_to_sales: {15:}, tpe_effective: {:15}, enterprise_value_to_ebitda: {:15}, profit_margin: {:15}, annualized_profit_margin: {:15}, held_percent_institutions: {:15}, forward_eps: {:15}, trailing_eps: {:15}, previous_close: {:15}, trailing_eps_percentage: {:15}, price_to_book: {:15}, shares_outstanding: {:15}, net_income_to_common_shareholders: {:15}, nitcsh_to_shares_outstanding: {:15}, num_employees: {:15}, enterprise_value: {:15}, market_cap: {:15}, nitcsh_to_num_employees: {:15}, earnings_quarterly_growth: {:15}, revenue_quarterly_growth: {:15}, price_to_earnings_to_growth_ratio: {:15}, sqrt_peg_ratio: {:15}, annualized_cash_flow_from_operating_activities: {:15}, ev_to_cfo_ratio: {:15}'.format(
                                                                                                                                           row[sss_index+0], row[sss_index+1],  row[sss_index+2],   row[sss_index+3],  row[sss_index+4],   row[sss_index+5],    row[sss_index+6],  row[sss_index+7],   row[sss_index+8],    row[sss_index+9],   row[sss_index+10],   row[sss_index+11],    row[sss_index+12],         row[sss_index+13],          row[sss_index+14],                  row[sss_index+15],    row[sss_index+16],                 row[sss_index+17],                       row[sss_index+18],    row[sss_index+19],                 row[sss_index+20],    row[sss_index+21],               row[sss_index+22],                row[sss_index+23],  row[sss_index+24],   row[sss_index+25],     row[sss_index+26],              row[sss_index+27],    row[sss_index+28],         row[sss_index+29],                        row[sss_index+30],                   row[sss_index+31],    row[sss_index+32],       row[sss_index+33], row[sss_index+34],              row[sss_index+35],                row[sss_index+36],               row[sss_index+37],                        row[sss_index+38],     row[sss_index+39],                                     row[sss_index+40] ))

                            output_csv_rows.append([ticker, row_in_older_file-row_index, row_in_older_file, row_index])

                        if row_in_older_file > consider_as_new_from >= row_index:
                            diff_lists[index].append('new+{}'.format(row_in_older_file-row_index))
                        elif row_in_older_file == row_index:
                            diff_lists[index].append('0')
                        elif row_in_older_file > row_index:
                            diff_lists[index].append('+{}'.format(row_in_older_file-row_index))  # old row - this row = row change (up+ or down-)
                        else:
                            diff_lists[index].append('{}'.format( row_in_older_file-row_index))  # old row - this row = row change (+up or -down)
                    else:
                        print("{:5}: appears at position {:2} (new)".format(ticker, row_index))
                        if not diff_only_recommendation:
                            print('                                                                                                        sss_value: {:15}, ssss_value: {:15}, sssss_value: {:15}, ssse_value: {:15}, sssse_value: {:15}, ssssse_value: {:15}, sssi_value: {:15}, ssssi_value: {:15}, sssssi_value: {:15}, sssei_value: {:15}, ssssei_value: {:15}, sssssei_value: {:15}, annualized_revenue: {:15}, annualized_earnings: {:15}, enterprise_value_to_revenue: {:15}, evr_effective: {:15}, trailing_price_to_earnings: {:15}, trailing_12months_price_to_sales: {15:}, tpe_effective: {:15}, enterprise_value_to_ebitda: {:15}, profit_margin: {:15}, annualized_profit_margin: {:15}, held_percent_institutions: {:15}, forward_eps: {:15}, trailing_eps: {:15}, previous_close: {:15}, trailing_eps_percentage: {:15}, price_to_book: {:15}, shares_outstanding: {:15}, net_income_to_common_shareholders: {:15}, nitcsh_to_shares_outstanding: {:15}, num_employees: {:15}, enterprise_value: {:15}, market_cap: {:15}, nitcsh_to_num_employees: {:15}, earnings_quarterly_growth: {:15}, revenue_quarterly_growth: {:15}, price_to_earnings_to_growth_ratio: {:15}, sqrt_peg_ratio: {:15}, annualized_cash_flow_from_operating_activities: {:15}, ev_to_cfo_ratio: {:15}'.format(
                                                                                                                                           row[sss_index+0], row[sss_index+1],  row[sss_index+2],   row[sss_index+3],  row[sss_index+4],   row[sss_index+5],    row[sss_index+6],  row[sss_index+7],   row[sss_index+8],    row[sss_index+9],   row[sss_index+10],   row[sss_index+11],    row[sss_index+12],         row[sss_index+13],          row[sss_index+14],                  row[sss_index+15],    row[sss_index+16],                 row[sss_index+17],                       row[sss_index+18],    row[sss_index+19],                 row[sss_index+20],    row[sss_index+21],               row[sss_index+22],                row[sss_index+23],  row[sss_index+24],   row[sss_index+25],     row[sss_index+26],              row[sss_index+27],    row[sss_index+28],         row[sss_index+29],                        row[sss_index+30],                   row[sss_index+31],    row[sss_index+32],       row[sss_index+33], row[sss_index+34],              row[sss_index+35],                row[sss_index+36],               row[sss_index+37],                        row[sss_index+38],     row[sss_index+39],                                     row[sss_index+40] ))
                        output_csv_rows.append([ticker, 'new', 'new', row_index])
                        diff_lists[index].append('new')

                    if row_index >= rec_length: break
                    row_index += 1

        # 3rd, scan for Older File rows which do not appear in the Newer files anymore:
        row_index = 0
        for row in older_rows:
            ticker = row[ticker_index]
            row_index_in_newer_file = get_row_index(ticker_index, ticker, newer_rows)
            if row_index_in_newer_file < 0:
                print("{:5}: disappeared from position {:2} (removed)".format(ticker, row_index))
                if not diff_only_recommendation:
                    print(            '                                                                                                    sss_value: {:15}, ssss_value: {:15}, sssss_value: {:15}, ssse_value: {:15}, sssse_value: {:15}, ssssse_value: {:15}, sssi_value: {:15}, ssssi_value: {:15}, sssssi_value: {:15}, sssei_value: {:15}, ssssei_value: {:15}, sssssei_value: {:15}, annualized_revenue: {:15}, annualized_earnings: {:15}, enterprise_value_to_revenue: {:15}, evr_effective: {:15}, trailing_price_to_earnings: {:15}, trailing_12months_price_to_sales: {15:}, tpe_effective: {:15}, enterprise_value_to_ebitda: {:15}, profit_margin: {:15}, annualized_profit_margin: {:15}, held_percent_institutions: {:15}, forward_eps: {:15}, trailing_eps: {:15}, previous_close: {:15}, trailing_eps_percentage: {:15}, price_to_book: {:15}, shares_outstanding: {:15}, net_income_to_common_shareholders: {:15}, nitcsh_to_shares_outstanding: {:15}, num_employees: {:15}, enterprise_value: {:15}, market_cap: {:15}, nitcsh_to_num_employees: {:15}, earnings_quarterly_growth: {:15}, revenue_quarterly_growth: {:15}, price_to_earnings_to_growth_ratio: {:15}, sqrt_peg_ratio: {:15}, annualized_cash_flow_from_operating_activities: {:15}, ev_to_cfo_ratio: {:15}'.format(
                                                                                                                                           row[sss_index+0], row[sss_index+1],  row[sss_index+2],   row[sss_index+3],  row[sss_index+4],   row[sss_index+5],    row[sss_index+6],  row[sss_index+7],   row[sss_index+8],    row[sss_index+9],   row[sss_index+10],   row[sss_index+11],    row[sss_index+12],         row[sss_index+13],          row[sss_index+14],                  row[sss_index+15],    row[sss_index+16],                 row[sss_index+17],                       row[sss_index+18],    row[sss_index+19],                 row[sss_index+20],    row[sss_index+21],               row[sss_index+22],                row[sss_index+23],  row[sss_index+24],   row[sss_index+25],     row[sss_index+26],              row[sss_index+27],    row[sss_index+28],         row[sss_index+29],                        row[sss_index+30],                   row[sss_index+31],    row[sss_index+32],       row[sss_index+33], row[sss_index+34],              row[sss_index+35],                row[sss_index+36],               row[sss_index+37],                        row[sss_index+38],     row[sss_index+39],                                     row[sss_index+40] ))
                output_csv_rows.append([ticker, 'removed', row_index, 'removed'])
            row_index += 1
        # Write results to CSV (if any changes detected):
        if len(output_csv_rows) > 1:
            os.makedirs(os.path.dirname(diff_filenames_list[index]), exist_ok=True)
            with open(diff_filenames_list[index], mode='w', newline='') as engine:
                writer = csv.writer(engine)
                writer.writerows(output_csv_rows)
            # pdf_generator.csv_to_pdf(csv_filename=diff_filenames_list[index],   title='Diff: '+diff_filenames_list[index].replace( '/',  '-'), limit_num_rows=28)
    return diff_lists
