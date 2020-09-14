import os
import yfinance as yf

import pandas as pd
import yfinance as yf
import csv

payload = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
first_table = payload[0]
second_table = payload[1]

df = first_table

symbols = df['Symbol'].values.tolist()
print(symbols)

with open('stocks_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Ticker", "Name", "EV/R", "profit_margin", "forward_eps", "trailing_eps", "price_to_book", "shares_outstanding", "net_income_to_common_shareholders", "nitcsh_div_shares_outstanding", "employees", "nitcsh_div_num_employees", "earnings_quarterly_growth", "price_to_earnings_to_growth_ratio", "last_dividend_0", "last_dividend_1", "last_dividend_2", "last_dividend_3" ])
    iteration = 0
    for symb in symbols:
        iteration += 1
        print('Checking {} ({}/{})'.format(symb,iteration,len(symbols)))
        symbol = yf.Ticker(symb)
        #     calendar = symbol.get_calendar(as_dict=True)
        #     earnings = symbol.get_earnings(as_dict=True)
        try:
            info = symbol.get_info()
            num_employees                     = info['fullTimeEmployees']
            short_name                        = info['shortName']
            website                           = info['website']
            evr                               = info['enterpriseToRevenue']
            profit_margin                     = info['profitMargins']
            forward_eps                       = info['forwardEps']
            trailing_eps                      = info['trailingEps']
            price_to_book                     = info['priceToBook']
            earnings_quarterly_growth         = info['earningsQuarterlyGrowth']
            price_to_earnings_to_growth_ratio = info['pegRatio']
            shares_outstanding                = info['sharesOutstanding']
            net_income_to_common_shareholders = info['netIncomeToCommon']
            nitcsh_div_shares_outstanding     = round(float(net_income_to_common_shareholders)/float(shares_outstanding),2)
            nitcsh_div_num_employees          = round(float(net_income_to_common_shareholders)/float(num_employees),2)
         #  print('info: {}'.format(info))
            print('Name: {}, EV/R: {}, profit_margin: {}, forward_eps: {}, trailing_eps: {}, price_to_book: {}, shares_outstanding: {}, net_income_to_common_shareholders: {}, nitcsh_div_shares_outstanding: {}, # employees: {}, nitcsh_div_num_employees: {}, earnings_quarterly_growth: {}, price_to_earnings_to_growth_ratio: {}'.format(short_name, evr, profit_margin, forward_eps, trailing_eps, price_to_book, shares_outstanding, net_income_to_common_shareholders, nitcsh_div_shares_outstanding, num_employees, nitcsh_div_num_employees, earnings_quarterly_growth, price_to_earnings_to_growth_ratio))
        except:
            num_employees                     = 0
            short_name                        = 0
            website                           = 0
            evr                               = 0
            profit_margin                     = 0
            forward_eps                       = 0
            trailing_eps                      = 0
            price_to_book                     = 0
            earnings_quarterly_growth         = 0
            price_to_earnings_to_growth_ratio = 0
            shares_outstanding                = 0
            net_income_to_common_shareholders = 0
            nitcsh_div_shares_outstanding     = 0
            nitcsh_div_num_employees          = 0
            print("Exception in info")
        try:
            last_4_dividends = symbol.dividends[-4:]
            print('last_4_dividends list: {}, {}, {}, {}'.format(last_4_dividends[0],last_4_dividends[1],last_4_dividends[2],last_4_dividends[3]))
        except:
            last_4_dividends = [0,0,0,0]
            print("Exception in dividends")
        writer.writerow([symb, short_name, evr, profit_margin, forward_eps, trailing_eps, price_to_book, shares_outstanding, net_income_to_common_shareholders, nitcsh_div_shares_outstanding, num_employees, nitcsh_div_num_employees, earnings_quarterly_growth, price_to_earnings_to_growth_ratio, last_4_dividends[0], last_4_dividends[1], last_4_dividends[2], last_4_dividends[3]])
        print('\n')

