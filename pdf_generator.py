#############################################################################
#
# Version 0.1.112 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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

#!/usr/bin/env python
# -*- coding: utf8 -*-

from fpdf import FPDF, HTMLMixin

import csv
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np


def csv_to_pdf(csv_filename, csv_db_path, data_time_str, title, limit_num_rows, diff_list, tase_mode, db_filename):
    title_for_figures = data_time_str + ' ' + (title[::-1] if tase_mode else title) + ']כתב ויתור: תוצאות הסריקה אינן המלצה בשום צורה, אלא אך ורק בסיס למחקר.['[::-1]

    # Read CSV file:
    csv_rows = []
    with open(csv_filename, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter=',')
        for row in reader:
            csv_rows.append(row)

    class MyFPDF(FPDF, HTMLMixin):
        pass

    pdf = MyFPDF(format='letter')
    pdf.add_page()
    # Access DejaVuSansCondensed.ttf on the machine. This font supports practically all languages.
    # Install it via https://fonts2u.com/dejavu-sans-condensed.font
    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
    pdf.set_font('DejaVu', '', 7)

    # pdf.set_font("Arial", size=8, style='B')
    pdf.set_text_color(0, 0, 200)  # blue
    pdf.cell(200, 8, txt=title_for_figures, ln=1, align="C")  # http://fpdf.org/en/doc/cell.htm

    names       = []
    appearances = []
    for row_index, row in enumerate(csv_rows):
        if row_index > limit_num_rows: break
        if row_index > 0:  # row 0 is title
            names.append(row[1][0:28])
            appearances.append(float(row[5]))
        if row_index == 0:
            if tase_mode: # overrwrite to hebrew
                row = ['סימבול'[::-1],'שם החברה'[::-1],'ענף'[::-1],'ערך'[::-1],'סגירה'[::-1],'ציון'[::-1]]
            else:
                row = ['Symbol', 'Name', 'Sector', 'Value', 'Close', 'Grade']
        for col_index, col in enumerate(row):
            w_diff                =0
            if   col_index == 0: w=14 # Symbol
            elif col_index == 1: w=42 # Name
            elif col_index == 2: w=33 # Sector
            elif col_index == 3: w=30 # Value
            elif col_index == 4: w=20 # Close
            elif col_index == 5:
                w                = 18 # Grade
                w_diff           = 5  # Diff

            if col_index < len(row)-1:
                pdf.set_text_color(0, 0, 200 if row_index == 0 else 0)  # blue for title and black otherwise
                pdf.cell(w=w, h=4, txt=col, border=1, ln=0, align="C" if row_index == 0 else "L")
            else:
                # last col is added with the diff col:
                pdf.set_text_color(0, 0, 200 if row_index == 0 else 0)  # blue for title and black otherwise
                pdf.cell(w=w, h=4, txt=col.replace('appearance_counter','Grade'), border=1, ln=0, align="C" if row_index == 0 else "L")
                if w_diff:
                    if diff_list is not None and row_index < len(diff_list):
                        if row_index == 0:
                            pdf.set_text_color(0, 0, 200 if row_index == 0 else 0)  # blue for title and black otherwise
                            pdf.cell(w=w, h=4, txt='שינוי'[::-1] if tase_mode else 'Change', border=1, ln=1, align="C")
                        else:
                            if 'new' in str(diff_list[row_index]):
                                pdf.set_text_color(0, 0, 200)  # blue
                            elif '-' in str(diff_list[row_index]):
                                pdf.set_text_color(200,0,0)   # red
                            elif '+' in str(diff_list[row_index]):
                                pdf.set_text_color(0,200,0)   # green
                            else:
                                pdf.set_text_color(0, 0, 0)   # black
                            pdf.cell(w=w, h=4, txt=str(diff_list[row_index]), border=1, ln=1, align="L")
    pdf.cell(200, 4, txt='', ln=1, align="L")
    fig, ax = plt.subplots(figsize=(15, 10))
    y_pos = np.arange(len(names))

    ax.barh(y_pos, appearances, align='center')
    ax.set_yticks(y_pos)
    ax.tick_params(axis='y', labelsize=8)
    ax.set_yticklabels(names)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel('ציון'[::-1] if tase_mode else 'Rank')
    ax.set_title(title_for_figures, color='blue')

    # plt.show()
    plt.savefig(csv_filename+"_fig.png")

    if tase_mode:
        telegram_channel_description          = 'ערוץ ערך מוסף'[::-1]
        telegram_discussion_group_description = 'עדכונים, תמיכה טכנית ודיונים'[::-1]
        open_source_description               = 'קוד פתוח'[::-1]
        the_engine_begind_description         = 'מנוע הסריקה'[::-1]
        lecture_description                   = 'הרצאה על הסורק'[::-1]

        pdf.set_text_color(0, 0, 200)  # blue
        pdf.cell(30, 4, txt=telegram_channel_description,          ln=0, align="C", border=1)
        pdf.cell(39, 4, txt=telegram_discussion_group_description, ln=0, align="C", border=1)
        pdf.cell(55, 4, txt=open_source_description,               ln=0, align="C", border=1)
        pdf.cell(40, 4, txt=the_engine_begind_description,         ln=0, align="C", border=1)
        pdf.cell(32, 4, txt=lecture_description,                   ln=1, align="C", border=1)


        html_telegram_channel_description          = "<A HREF=""https://t.me/investorsIL"">t.me/investorsIL</A><"
        pdf.write_html(text=html_telegram_channel_description)

        html_telegram_discussion_group_description = "   <A HREF=""http://t.me/StockScannerIL"">t.me/StockScannerIL</A>"
        pdf.write_html(text=html_telegram_discussion_group_description)

        html_open_source_description               = " <A HREF=""http://bit.ly/OpenSourceStockScanner"">bit.ly/OpenSourceStockScanner</A>"
        pdf.write_html(text=html_open_source_description)

        html_the_engine_begind_description         = " <A HREF=""http://bit.ly/SssCoreEquation"">bit.ly/SssCoreEquation</A>"
        pdf.write_html(text=html_the_engine_begind_description)

        html_lecture_description                   = "  <A HREF=""http://bit.ly/SssLecture"">bit.ly/SssLecture</A>"
        pdf.write_html(text=html_lecture_description)

        pdf.cell(200, 4, txt='', ln=1, align="R")
        html_telegram_channel_description     = "<p><img src=""{}"" width=""600"" height=""250""></p>".format(csv_filename+"_fig.png")
        
        pdf.write_html(text=html_telegram_channel_description)
    else:
        html="<p>Added-Value Channel in Telegram: <A HREF=""https://t.me/investorsIL"">https://t.me/investorsIL</A></p>" \
             "<p>Updates, Discussions and Technical Support on Telegram: <A HREF=""https://t.me/StockScannerIL"">https://t.me/StockScannerIL</A></p>" \
             "<p>This Scanner is Open Source. fork() here: <A HREF=""http://bit.ly/OpenSourceStockScanner"">http://bit.ly/OpenSourceStockScanner</A></p>" \
             "<p>Lecture: <A HREF=""http://bit.ly/SssLecture"">http://bit.ly/SssLecture</A>, One-Pagers: <A HREF=""http://bit.ly/SssCoreEquation"">http://bit.ly/SssCoreEquation</A>, <A HREF=""http://bit.ly/MultiDimensionalScan"">http://bit.ly/MultiDimensionalScan</A></p>" \
             "<p>Disclaimer: Scan Results are not recommendations! They only represent a basis for Research and Analysis.</p>" \
             "<p><img src=""{}"" width=""600"" height=""250""></p>".format(csv_filename+"_fig.png")
        pdf.write_html(text=html)

    if csv_db_path is not None:
        output_filename = csv_db_path+'/'+data_time_str+title+("_n" if "normalized" in db_filename else "")+'.pdf'
    else:
        output_filename = csv_filename+'.pdf'
    pdf.output(output_filename, 'F')

