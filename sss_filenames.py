#############################################################################
#
# Version 0.1.35 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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

def create_filenames_list(date_and_time):
    filename_csv_db                     = "{}/db.csv".format(date_and_time)
    filename_sss_engine                 = "{}/sss_engine.csv".format(date_and_time)
    filename_sss_engine_no_div          = "{}/sss_engine_no_div.csv".format(date_and_time)
    filename_sss_engine_only_div        = "{}/sss_engine_only_div.csv".format(date_and_time)
    filename_diff_from_ref              = "{}/db_diff_from_ref.csv".format(date_and_time)
    filenames_list = [
        filename_csv_db,
        filename_sss_engine,
        filename_sss_engine_no_div,
        filename_sss_engine_only_div,
        filename_diff_from_ref
    ]
    return filenames_list
