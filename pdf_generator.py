#########################################################
# Version 153 - Author: Asaf Ravid <asaf.rvd@gmail.com> #
#########################################################

from fpdf import FPDF, HTMLMixin

import csv
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np



def csv_to_pdf(csv_filename, title, limit_num_rows, diff_list):
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
    pdf.set_font("Arial", size=8, style='B')
    pdf.cell(200, 10, txt=title, ln=1, align="C")  # http://fpdf.org/en/doc/cell.htm

    names       = []
    appearances = []
    for row_index, row in enumerate(csv_rows):
        if row_index >= limit_num_rows: break
        if row_index > 0:  # row 0 is title
            names.append(row[1])
            appearances.append(float(row[4]))
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
                pdf.cell(w=w, h=5, txt=col, border=1, ln=0, align="l")
            else:
                # last col is added with the diff col:
                pdf.cell(w=w, h=5, txt=col.replace('_counter',''), border=1, ln=0, align="l")
                if w_diff:
                    if diff_list is not None and row_index < len(diff_list):
                        pdf.cell(w=w, h=5, txt=str(diff_list[row_index]), border=1, ln=1, align="l")

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
    ax.set_xlabel('Appearances')
    ax.set_title(csv_filename[csv_filename.find('recommendation'):])

    # plt.show()
    plt.savefig(csv_filename+"_fig.png")

    html="<p>For Weekly Updates and Support on Telegram: <A HREF=""https://t.me/SssWeeklyUpdates"">https://t.me/SssWeeklyUpdates</A></p>" \
         "<p>SSS is open source. fork() here: <A HREF=""https://github.com/asafravid/sss"">https://github.com/asafravid/sss</A></p>" \
         "<p>Lecture (Hebrew): <A HREF=""http://bit.ly/SssLecture"">http://bit.ly/SssLecture</A></p>" \
         "<p><img src=""{}"" width=""600"" height=""250""></p>".format(csv_filename+"_fig.png")
    pdf.write_html(text=html)

    pdf.output(csv_filename+'.pdf')

