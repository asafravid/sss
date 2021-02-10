#########################################################
# Version 135 - Author: Asaf Ravid <asaf.rvd@gmail.com> #
#########################################################

from fpdf import FPDF, HTMLMixin

import csv


def csv_to_pdf(csv_filename, title, limit_num_rows):
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

    for row_index, row in enumerate(csv_rows):
        if row_index >= limit_num_rows: break
        for col_index, col in enumerate(row):
            if   col_index == 0: w=15 # Ticker
            elif col_index == 1: w=62 # Name
            elif col_index == 2: w=37 # Sector
            elif col_index == 3: w=30 # S value
            else               : w=30 # appearance[_counter]

            if col_index < len(row)-1:
                pdf.cell(w=w, h=5, txt=col, border=1, ln=0, align="l")
            else:
                pdf.cell(w=w, h=5, txt=col.replace('_counter',''), border=1, ln=1, align="l")

    # pdf.cell(200, 10, txt='https://t.me/SssWeeklyUpdates',    ln=1, align="L")
    # pdf.cell(200, 10, txt='https://github.com/asafravid/sss', ln=1, align="L")
    # pdf.cell(200, 10, txt='http://bit.ly/SssLecture',         ln=1, align="L")
    # pdf.cell(200, 10, txt='For Weekly Updates and Support on Telegram:', ln=0, align="L")
    # pdf.write_html(text='<A HREF="https://t.me/SssWeeklyUpdates">https://t.me/SssWeeklyUpdates</A>')
    # pdf.cell(200, 5, txt='', ln=1, align="L")
    #
    # pdf.cell(200, 10, txt='SSS is open source. fork() here:', ln=0, align="L")
    # pdf.write_html(text='<A HREF="https://github.com/asafravid/sss">https://github.com/asafravid/sss</A>')
    # pdf.cell(200, 5, txt='', ln=1, align="L")
    #
    # pdf.cell(200, 10, txt='Lecture (Hebrew):', ln=0, align="L")
    # pdf.write_html(text='<A HREF="http://bit.ly/SssLecture">http://bit.ly/SssLecture</A>')
    pdf.cell(200, 5, txt='', ln=1, align="L")

    html="<p>For Weekly Updates and Support on Telegram: <A HREF=""https://t.me/SssWeeklyUpdates"">https://t.me/SssWeeklyUpdates</A></p>" \
         "<p>SSS is open source. fork() here: <A HREF=""https://github.com/asafravid/sss"">https://github.com/asafravid/sss</A></p>" \
         "<p>Lecture (Hebrew): <A HREF=""http://bit.ly/SssLecture"">http://bit.ly/SssLecture</A></p>"
    pdf.write_html(text=html)


    pdf.output(csv_filename+'.pdf')
