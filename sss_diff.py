#############################################################################
#
# Version 0.2.1 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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


def get_row_and_index(symbol_index, symbol, rows):
    index = 0
    for row in rows:
        if symbol == row[symbol_index]:
            return [row, index+1] # avoid row index 0
        index += 1
    return [[], -1]


def run(newer_path, older_path, db_filename, movement_threshold, res_length, consider_as_new_from):
    diff_path = 'Results/Diff/'+'new'+newer_path.replace('Results','_').replace('/','').replace('nRes','')+'_old'+older_path.replace('Results','_').replace('/','').replace('Tase','').replace('Nsr','').replace('All','').replace('nRes','').replace('a','').replace('e','').replace('i','').replace('o','').replace('u','')
    compact_diff_path = diff_path.replace('FavorTechBy3','FTB3').replace('MCap_','').replace('BuildDb_','').replace('nResults','')

    newer_filename = newer_path +'/results_{}'.format(db_filename.replace('_engine',''))
    older_filename = older_path +'/results_{}'.format(db_filename.replace('_engine',''))

    diff_filename_new     = '{}/res_new_{}'.format(      compact_diff_path, db_filename.replace('_engine',''))
    diff_filename_removed = '{}/res_removed_{}'.format(  compact_diff_path, db_filename.replace('_engine',''))

    diff_list_new     = [] # A Column Header 'Diff' and then the changes
    diff_list_removed = [] # A Column Header 'Diff' and then the changes

    output_csv_rows_new     = [['symbol','change','from','to']]
    output_csv_rows_removed = [['symbol', 'change', 'from', 'to']]
    print("\n{:20}:\n======================================".format(newer_filename))

    # 1st, Read the Older File, which will be the reference:
    older_rows = []
    with open(older_filename, mode='r', newline='') as engine:
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
    with open(newer_filename, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter=',')
        row_index = 0
        for row in reader:
            if row_index == 0:
                diff_list_new.append(    'Diff')
                diff_list_removed.append('Diff')
                symbol_index = row.index("Symbol")
                name_index   = row.index("Name")
                ma_index     = row.index("MA")
                row_index   += 1
                continue
            else:
                newer_rows.append(row)
                symbol            = row[symbol_index]
                name              = row[name_index]
                ma                = row[ma_index]
                [row_in_older_file, row_index_in_older_file] = get_row_and_index(symbol_index, symbol, older_rows)
                if row_index_in_older_file >= 0:  # This stock in the new list, appears in the old list as well
                    # Diff the MA columns:
                    ma_diff = ''
                    if len(row_in_older_file):
                        if   ma == row_in_older_file[ma_index]:
                            ma_diff = ''
                        elif 'r+' in     ma and 'r+' not in row_in_older_file[ma_index]:  # Started the r+? indicate
                            ma_diff = ' !r+'
                        elif 'r+' not in ma and 'r+'     in row_in_older_file[ma_index]:  # Stopped the r+? indicate
                            ma_diff = ' ?r+'

                    if abs(row_index_in_older_file - row_index) > movement_threshold:
                        print("{:5} ({:15}):  {:2} positions change from {:3} to {:3}".format(symbol, name, row_index_in_older_file-row_index, row_index_in_older_file, row_index))
                        output_csv_rows_new.append([symbol, row_index_in_older_file-row_index, row_index_in_older_file, row_index])

                    if row_index_in_older_file > consider_as_new_from >= row_index:
                        diff_list_new.append('new+{}{}'.format(row_index_in_older_file-row_index, ma_diff))
                    elif row_index_in_older_file == row_index:
                        diff_list_new.append('0{}'.format(ma_diff))
                    elif row_index_in_older_file > row_index:
                        diff_list_new.append('+{}{}'.format(row_index_in_older_file-row_index, ma_diff))  # old row - this row = row change (up+ or down-)
                    else:
                        diff_list_new.append('{}{}'.format( row_index_in_older_file-row_index, ma_diff))  # old row - this row = row change (+up or -down)
                else:
                    print("{:5}: appears at position {:2} (new)".format(symbol, row_index))
                    output_csv_rows_new.append([symbol, 'new', 'new', row_index])
                    diff_list_new.append('new')

                if row_index >= res_length: break
                row_index += 1

    # 3rd, scan for Older File rows which do not appear in the Newer files anymore:
    row_index = 1  # start from 1 as get_row_and_index() used for reference, skips title row
    for row in older_rows:  # Those do not contain the title row hence added offset 1 to row_index above to start off with
        symbol = row[symbol_index]
        ma     = row[ma_index]
        [row_in_newer_file, row_index_in_newer_file] = get_row_and_index(symbol_index, symbol, newer_rows)
        # Diff the MA columns:
        ma_diff = ''
        if len(row_in_newer_file):
            if ma == row_in_newer_file[ma_index]:
                ma_diff = ''
            elif 'r+' in     ma and 'r+' not in row_in_newer_file[ma_index]:  # Stopped the r+? indicate
                ma_diff = ' ?r+'
            elif 'r+' not in ma and 'r+'     in row_in_newer_file[ma_index]:  # Started the r+? indicate
                ma_diff = ' !r+'

        if row_index_in_newer_file < 0:  # symbol disappeared completely
            print("{:5}: disappeared from position {:2} (removed)".format(symbol, row_index))
            output_csv_rows_removed.append([symbol, 'removed', row_index, 'removed'])
            diff_list_removed.append('removed')
        elif row_index_in_newer_file > consider_as_new_from >= row_index:  # symbol disappeared above the threshold
            print("{:5}: disappeared from position {:2} (removed above threshold {}) to {:2}".format(symbol, row_index, consider_as_new_from, row_index_in_newer_file))
            output_csv_rows_removed.append([symbol, 'removed{}', row_index, row_index_in_newer_file, ma_diff])
            diff_list_removed.append('removed{}'.format(row_index-row_index_in_newer_file))
        elif row_index > row_index_in_newer_file:  # just moved UP[better] a few places in newer file
            print("{:5} ({:15}):  +{:2} positions change from {:3} to {:3}".format(symbol, name, row_index - row_index_in_newer_file, row_index, row_index_in_newer_file))
            output_csv_rows_removed.append([symbol, row_index - row_index_in_newer_file, row_index, row_index_in_newer_file])
            diff_list_removed.append('+{}{}'.format(row_index-row_index_in_newer_file, ma_diff))  # this old row - newer row = row change (+up or -down)
        else:                                      # moved DOWN[worse] (or remained)
            print("{:5} ({:15}):  {:2} positions change from {:3} to {:3}".format(symbol, name, row_index - row_index_in_newer_file, row_index, row_index_in_newer_file))
            output_csv_rows_removed.append(
                [symbol, row_index - row_index_in_newer_file, row_index, row_index_in_newer_file])
            diff_list_removed.append('{}{}'.format( row_index-row_index_in_newer_file, ma_diff))  # this old row - newer row = row change (+up or -down)

        row_index += 1

    # Write results to CSVs (if any changes detected):
    if len(output_csv_rows_new) > 1:
        os.makedirs(os.path.dirname(diff_filename_new), exist_ok=True)
        with open(diff_filename_new, mode='w', newline='') as engine:
            writer = csv.writer(engine)
            writer.writerows(output_csv_rows_new)

    if len(output_csv_rows_removed) > 1:
        os.makedirs(os.path.dirname(diff_filename_removed), exist_ok=True)
        with open(diff_filename_removed, mode='w', newline='') as engine:
            writer = csv.writer(engine)
            writer.writerows(output_csv_rows_removed)

    return [diff_list_new, diff_list_removed]
