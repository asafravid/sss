#############################################################################
#
# Version 0.2.0 - Author: Asaf Ravid <asaf.rvd@gmail.com>
#
#    Credit to the PEG Ratio fetching source code: https://github.com/rickturner2001
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

#
# Declare the tickers to check in the symbols list as strings or even better use a csv file.
# If you decide to use a .csv file remember to change the for loop (e.g. for symbol in symbols['Symbol'])
import csv
import yfinance as yf
import sss
import requests
from bs4 import BeautifulSoup


symbols_united_states   = []
etf_and_nextshares_list = []

nasdaq_filenames_list = ['Indices/nasdaqlisted.csv', 'Indices/otherlisted.csv', 'Indices/nasdaqtraded.csv']  # Checkout http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs for all symbol definitions (for instance - `$` in stock names, 5-letter stocks ending with `Y`)
ticker_column_list = [0, 0, 1]  # nasdaqtraded.csv - 1st column is Y/N (traded or not) - so take row[1] instead!!!
sss.download_ftp_files(nasdaq_filenames_list, 'ftp://ftp.nasdaqtrader.com/SymbolDirectory/')
for index, filename in enumerate(nasdaq_filenames_list):
    with open(filename, mode='r', newline='') as engine:
        reader = csv.reader(engine, delimiter='|')
        next_shares_column = None
        etf_column = None
        row_index = 0
        for row in reader:
            if row_index == 0:
                row_index += 1
                # Find ETF and next shares Column:
                for column_index, column in enumerate(row):
                    if column == 'ETF':
                        etf_column = column_index
                    elif column == 'NextShares':
                        next_shares_column = column_index
                continue
            else:
                row_index += 1
                if 'File Creation Time' in row[0]:
                    continue
                if next_shares_column and row[next_shares_column] == 'Y':
                    etf_and_nextshares_list.append(row[ticker_column_list[index]])
                    continue
                if etf_column and row[etf_column] == 'Y':
                    etf_and_nextshares_list.append(row[ticker_column_list[index]])
                    continue
                if '$' in row[
                    ticker_column_list[index]]:  # AAIC$B -> <stock_symbol>$<letter> --> keep just the stock_Symbol
                    stock_symbol = row[ticker_column_list[index]].split('$')[0]
                else:
                    stock_symbol = row[ticker_column_list[index]]
                symbols_united_states.append(stock_symbol)

symbols = symbols_united_states

for symbol in symbols:
    eff_symbol = symbol.replace(".","-")  # Dot notation on symbols (BRK.B) will return null values if used with yfinance
    info = yf.Ticker(eff_symbol).get_info()
    if "pegRatio" not in info:
        continue
    api_peg = info['pegRatio']  # Getting the yfinance PEG Ratio
    URL = f'https://stockanalysis.com/stocks/{symbol}/statistics/'
    r = requests.get(URL)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, 'html.parser')
        my_table = soup.findAll('table', {'class': 'text-sm xs:text-base StatsWidget_statstable__9KlU0'})

        for i in my_table:
            if 'PEG' in str(i):
                ratio_iloc = str(i).find('PEG Ratio')
                peg_ratio = str(i)[ratio_iloc + 39:ratio_iloc + 43]
                try:
                    peg_ratio = float(peg_ratio)
                    print(f"{symbol}, {api_peg}, {peg_ratio}")
                except:
                    # First exception: double digits and negative values.
                    try:
                        peg_ratio = str(i)[ratio_iloc + 40:ratio_iloc + 45]
                        peg_ratio = float(peg_ratio)
                        print(f"{symbol}, {api_peg}, {peg_ratio}")
                    except Exception as e:
                        # Empty td tag in the page means N/A value
                        if str(peg_ratio) == '</td>':
                            peg_ratio = 'N/A'
                            print(f"{symbol}, {api_peg}, {peg_ratio}")
                        else:
                            print('Something went wrong trying to convert the PEG Ratio: ',symbol,  peg_ratio)