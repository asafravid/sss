#############################################################################
#
# Version 300 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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

import sss_filenames
import csv
import os


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
                output_csv_rows.append([ticker, 'removed', row_index, 'removed'])
            row_index += 1
        # Write results to CSV (if any changes detected):
        if len(output_csv_rows) > 1:
            os.makedirs(os.path.dirname(diff_filenames_list[index]), exist_ok=True)
            with open(diff_filenames_list[index], mode='w', newline='') as engine:
                writer = csv.writer(engine)
                writer.writerows(output_csv_rows)
    return diff_lists
