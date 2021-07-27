##############################################################################
#
# Version 0.2.5 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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
##############################################################################

mkdir                         Backup/$1
cp sss.py                     Backup/$1/sss.py
cp sss_run.py                 Backup/$1/sss_run.py
cp sss_diff.py                Backup/$1/sss_diff.py
cp sss_filenames.py           Backup/$1/sss_filenames.py
cp sss_filenames.py           Backup/$1/sss_filenames.py
cp pdf_generator.py           Backup/$1/pdf_generator.py
cp Math.xlsx                  Backup/$1/Math.xlsx
cp sss_results_performance.py Backup/$1/sss_results_performance.py
cp sss_config.py              Backup/$1/sss_config.py
cp sss_indices.py             Backup/$1/sss_indices.py
cp sss_post_processing.py     Backup/$1/sss_post_processing.py

cp version.sh                 Backup/$1/version.sh
