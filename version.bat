REM #############################################################################
REM #
REM # Version 0.1.35 - Author: Asaf Ravid <asaf.rvd@gmail.com>
REM #
REM #    Stock Screener and Scanner - based on yfinance
REM #    Copyright (C) 2021 Asaf Ravid
REM #
REM #    This program is free software: you can redistribute it and/or modify
REM #    it under the terms of the GNU General Public License as published by
REM #    the Free Software Foundation, either version 3 of the License, or
REM #    (at your option) any later version.
REM #
REM #    This program is distributed in the hope that it will be useful,
REM #    but WITHOUT ANY WARRANTY; without even the implied warranty of
REM #    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
REM #    GNU General Public License for more details.
REM #
REM #    You should have received a copy of the GNU General Public License
REM #    along with this program.  If not, see <https://www.gnu.org/licenses/>.
REM #
REM #############################################################################

mkdir                           Backup\%1
copy sss.py                     Backup\%1\sss.py
copy sss_run.py                 Backup\%1\sss_run.py
copy sss_diff.py                Backup\%1\sss_diff.py
copy sss_filenames.py           Backup\%1\sss_filenames.py
copy sss_filenames.py           Backup\%1\sss_filenames.py
copy pdf_generator.py           Backup\%1\pdf_generator.py
copy Math.xlsx                  Backup\%1\Math.xlsx
copy sss_results_performance.py Backup\%1\sss_results_performance.py

copy version.bat                Backup\%1\version.bat