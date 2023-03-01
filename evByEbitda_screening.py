'''Filters stock trading with attractive Ev/Editda financial ratio'''

import csv
import traceback
from itertools import zip_longest
from yahoofinancials import YahooFinancials
from more_itertools import unique_everseen

tickers_name=list()
tickers_PTS=list()
tickers_EV=list()
tickers_bookval=list()
tickers_close=list()

#--------------------------------------------------------------------------------------------------------
#Filters stocks with EV/EBITDA ratio in range 0-10, stores the resultant dataset in EVToEbitda_Output.csv

def ev_ebitda_filter():
    with open("Financials.csv",'r') as mf:
        data=csv.DictReader(mf)

        for row in data:

            try:
                hold2=float(row['EVToEBITDA'])
                hold2=round(hold2,3)
                #print(hold2<1)

            except Exception as e:
                print(row['Ticker'])
                print(traceback.format_exc())

            if(hold2<11 and hold2>0):
                    tickers_name.append(row['Ticker'])
                    tickers_EV.append(row['EVToEBITDA'])
                    tickers_PTS.append(row['PToSales'])
                    tickers_close.append(row['Close'])
                    tickers_bookval.append(row['Book Value'])


    list_clubber=[tickers_name,tickers_EV,tickers_PTS,tickers_close,tickers_bookval]
    export_data_complete=zip_longest(*list_clubber,fillvalue='')

    with open("EVToEbitda_Output.csv",'w',encoding="ISO-8859-1",newline="") as myfile:
        wr=csv.writer(myfile)
        wr.writerow(("Ticker","EVToEBITDA","P/S","LTP","Book Value"))
        wr.writerows(export_data_complete)
        print("Execution Success!")
