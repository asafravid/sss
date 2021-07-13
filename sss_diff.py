#############################################################################
#
# Version 0.1.118 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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

import sss_filenames
import csv
import os


def get_row_index(symbol_index, symbol, rows):
    index = 0
    for row in rows:
        if symbol == row[symbol_index]:
            return index+1 # avoid row index 0
        index += 1
    return -1


def run(newer_path, older_path, db_filename, db_exists_in_both_folders, diff_only_result, movement_threshold, res_length, consider_as_new_from):
    newer_filenames_list = sss_filenames.create_filenames_list(newer_path)
    older_filenames_list = sss_filenames.create_filenames_list(older_path)
    diff_path = 'Results/Diff/'+'new'+newer_path.replace('Results','_').replace('/','').replace('nRes','')+'_old'+older_path.replace('Results','_').replace('/','').replace('Tase','').replace('Nsr','').replace('All','').replace('nRes','').replace('a','').replace('e','').replace('i','').replace('o','').replace('u','')
    compact_diff_path = diff_path.replace('FavorTechBy3','FTB3').replace('MCap_','').replace('BuildDb_','').replace('nResults','')
    diff_filenames_list  = sss_filenames.create_filenames_list(compact_diff_path)
    newer_filenames_list.insert(  0, newer_path +'/results_{}'.format(db_filename.replace('_engine','')))
    older_filenames_list.insert(  0, older_path +'/results_{}'.format(db_filename.replace('_engine','')))

    diff_filenames_list.insert(  0,'{}/res_{}'.format(  compact_diff_path, db_filename.replace('_engine','')))

    if len(older_filenames_list) != len(newer_filenames_list):
        raise Exception("Different Lengths of lists - Unacceptable")

    diff_lists = [[]]  # index 0: sss

    if diff_only_result: length_to_iterate = 1 # Only SSS 3  # SSS, SSSS and SSSSS
    else:                length_to_iterate = len(newer_filenames_list)
    for index in range(length_to_iterate):
        if db_exists_in_both_folders == 0 and index == 0: continue
        output_csv_rows = [['symbol','change','from','to']]
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
                    if row_index >= res_length: break
                    row_index += 1

        # 2nd, read the Newer File and check if (and where) each line appears in the Older file (if at all)
        newer_rows = []
        with open(newer_filenames_list[index], mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                if row_index == 0:
                    diff_lists[index].append('Diff')
                    symbol_index = row.index("Symbol")
                    name_index   = row.index("Name")
                    row_index   += 1
                    continue
                else:
                    newer_rows.append(row)
                    symbol            = row[symbol_index]
                    name              = row[name_index]
                    row_in_older_file = get_row_index(symbol_index, symbol, older_rows)
                    if row_in_older_file >= 0:  # This stock in the new list, appears in the old list as well
                        if abs(row_in_older_file - row_index) > movement_threshold:
                            print("{:5} ({:15}):  {:2} positions change from {:3} to {:3}".format(symbol, name, row_in_older_file-row_index, row_in_older_file, row_index))
                            output_csv_rows.append([symbol, row_in_older_file-row_index, row_in_older_file, row_index])

                        if row_in_older_file > consider_as_new_from >= row_index:
                            diff_lists[index].append('new+{}'.format(row_in_older_file-row_index))
                        elif row_in_older_file == row_index:
                            diff_lists[index].append('0')
                        elif row_in_older_file > row_index:
                            diff_lists[index].append('+{}'.format(row_in_older_file-row_index))  # old row - this row = row change (up+ or down-)
                        else:
                            diff_lists[index].append('{}'.format( row_in_older_file-row_index))  # old row - this row = row change (+up or -down)
                    else:
                        print("{:5}: appears at position {:2} (new)".format(symbol, row_index))
                        output_csv_rows.append([symbol, 'new', 'new', row_index])
                        diff_lists[index].append('new')

                    if row_index >= res_length: break
                    row_index += 1

        # 3rd, scan for Older File rows which do not appear in the Newer files anymore:
        row_index = 0
        for row in older_rows:
            symbol = row[symbol_index]
            row_index_in_newer_file = get_row_index(symbol_index, symbol, newer_rows)
            if row_index_in_newer_file < 0:
                print("{:5}: disappeared from position {:2} (removed)".format(symbol, row_index))
                output_csv_rows.append([symbol, 'removed', row_index, 'removed'])
            row_index += 1
        # Write results to CSV (if any changes detected):
        if len(output_csv_rows) > 1:
            os.makedirs(os.path.dirname(diff_filenames_list[index]), exist_ok=True)
            with open(diff_filenames_list[index], mode='w', newline='') as engine:
                writer = csv.writer(engine)
                writer.writerows(output_csv_rows)
    return diff_lists
