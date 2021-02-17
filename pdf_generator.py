#########################################################
# Version 173 - Author: Asaf Ravid <asaf.rvd@gmail.com> #
#########################################################

#!/usr/bin/env python
# -*- coding: utf8 -*-

from fpdf import FPDF, HTMLMixin

import csv
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np


def csv_to_pdf(csv_filename, csv_db_path, data_time_str, title, limit_num_rows, diff_list, tase_mode):
    title_for_figures = data_time_str + ' ' + (title[::-1] if tase_mode else title)

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
    pdf.set_font('DejaVu', '', 8)

    # pdf.set_font("Arial", size=8, style='B')
    pdf.cell(200, 10, txt=title_for_figures, ln=1, align="C")  # http://fpdf.org/en/doc/cell.htm

    names       = []
    appearances = []
    for row_index, row in enumerate(csv_rows):
        if row_index >= limit_num_rows: break
        if row_index > 0:  # row 0 is title
            names.append(row[1])
            appearances.append(float(row[4]))
        if row_index == 0 and tase_mode: # overrwrite to hebrew
            row = ['סימבול'[::-1],'שם החברה'[::-1],'ענף'[::-1],'ערך'[::-1],'ציון'[::-1]]
        for col_index, col in enumerate(row):
            w_diff                =0
            if   col_index == 0: w=18 # Ticker
            elif col_index == 1: w=50 # Name
            elif col_index == 2: w=33 # Sector
            elif col_index == 3: w=25 # S value
            elif col_index == 4:
                w                = 22 # appearance[_counter]
                w_diff           = 8  # Diff

            if col_index < len(row)-1:
                pdf.cell(w=w, h=5, txt=col, border=1, ln=0, align="C" if row_index == 0 else "L")
            else:
                # last col is added with the diff col:
                pdf.cell(w=w, h=5, txt=col.replace('_counter',''), border=1, ln=0, align="C" if row_index == 0 else "L")
                if w_diff:
                    if diff_list is not None and row_index < len(diff_list):
                        pdf.cell(w=w, h=5, txt='שינוי'[::-1] if tase_mode and row_index == 0 else str(diff_list[row_index]), border=1, ln=1, align="C" if row_index == 0 else "L")

    pdf.cell(200, 5, txt='', ln=1, align="L")
    fig, ax = plt.subplots(figsize=(15, 5))
    y_pos = np.arange(len(names))

    # plt.plot(names, appearances)
    # plt.xlabel('Names')
    # plt.ylabel('Appearances')
    # plt.title(csv_filename[csv_filename.find('recommendation'):])
    # plt.invert_yaxis()
    # plt.bar(y_pos, appearances, align='center', alpha=0.5)
    # plt.xticks(y_pos, names)

    ax.barh(y_pos, appearances, align='center')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel('שינוי'[::-1] if tase_mode else 'Appearances')
    ax.set_title(title_for_figures)

    # plt.show()
    plt.savefig(csv_filename+"_fig.png")

    if tase_mode:  # TODO: ASAFR: Resolve Hebrew PDF issues
        telegram_channel_description          = 'ערוץ ערך מוסף בטלגרם'[::-1]
        telegram_discussion_group_description = 'עדכונים )כולל תמיכה ושאלות על הסורק( ודיונים בטלגרם'[::-1]
        open_source_description               = 'קוד פתוח'[::-1]
        lecture_description                   = 'הרצאה )בעברית( על הסורק'[::-1]

        pdf.cell(30, 5, txt=telegram_channel_description,          ln=0, align="R", border=1)
        pdf.cell(70, 5, txt=telegram_discussion_group_description, ln=0, align="R", border=1)
        pdf.cell(60, 5, txt=open_source_description,               ln=0, align="R", border=1)
        pdf.cell(35, 5, txt=lecture_description,                   ln=1, align="R", border=1)


        html_telegram_channel_description          = "<A HREF=""https://t.me/investorsIL"">t.me/investorsIL</A><"
        pdf.write_html(text=html_telegram_channel_description)

        html_telegram_discussion_group_description = "                                <A HREF=""http://t.me/StockScannerIL"">t.me/StockScannerIL</A>"
        pdf.write_html(text=html_telegram_discussion_group_description)

        html_open_source_description               = "                  <A HREF=""https://github.com/asafravid/sss"">github.com/asafravid/sss</A>"
        pdf.write_html(text=html_open_source_description)

        html_lecture_description                   = "     <A HREF=""http://bit.ly/SssLecture"">bit.ly/SssLecture</A>"
        pdf.write_html(text=html_lecture_description)

        pdf.cell(200, 5, txt='', ln=1, align="R")
        html_telegram_channel_description     = "<p><img src=""{}"" width=""600"" height=""250""></p>".format(csv_filename+"_fig.png")
        
        pdf.write_html(text=html_telegram_channel_description)
    else:
        html="<p>Deeper Value Channel Telegram: <A HREF=""https://t.me/investorsIL"">https://t.me/investorsIL</A></p>" \
             "<p>Updates, Discussions and Technical Support on Telegram: <A HREF=""https://t.me/StockScannerIL"">https://t.me/StockScannerIL</A></p>" \
             "<p>This Scanner is Open Source. fork() here: <A HREF=""https://github.com/asafravid/sss"">https://github.com/asafravid/sss</A></p>" \
             "<p>Lecture (in Hebrew): <A HREF=""http://bit.ly/SssLecture"">http://bit.ly/SssLecture</A></p>" \
             "<p><img src=""{}"" width=""600"" height=""250""></p>".format(csv_filename+"_fig.png")
        pdf.write_html(text=html)

    if csv_db_path is not None:
        output_filename = csv_db_path+'/'+data_time_str+title+'.pdf'
    else:
        output_filename = csv_filename+'.pdf'
    pdf.output(output_filename, 'F')

