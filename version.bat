REM #########################################################
REM # Version 275 - Author: Asaf Ravid <asaf.rvd@gmail.com> #
REM #########################################################

mkdir Backup\%1
copy sss.py           Backup\%1\sss.py
copy sss_run.py       Backup\%1\sss_run.py
copy sss_diff.py      Backup\%1\sss_diff.py
copy sss_filenames.py Backup\%1\sss_filenames.py
copy sss_filenames.py Backup\%1\sss_filenames.py
copy pdf_generator.py Backup\%1\pdf_generator.py 
copy version.bat Backup\%1\version.bat 