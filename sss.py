import os
import yfinance as yf

CONTINUE_UPON_INFO_EXCEPTION = 1 # Instead of filling with zeros, continue
CONTINUE_UPON_NONE_FIELD     = 1 # Ignore stocks with None fields which are important for scanning

import pandas as pd
import yfinance as yf
import csv

# There are 2 tables on the Wikipedia page
# we want the first table

payload = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
first_table = payload[0]
second_table = payload[1]

df = first_table

symbols_snp500    = df['Symbol'].values.tolist()
symbols_nasdaq100 = ['ADBE', 'AMD', 'ALXN', 'ALGN', 'GOOGL', 'GOOG', 'AMZN', 'AMGN', 'ADI', 'ANSS', 'AAPL', 'AMAT', 'ASML', 'ADSK', 'ADP', 'BIDU', 'BIIB', 'BMRN', 'BKNG', 'AVGO', 'CDNS', 'CDW', 'CERN', 'CHTR', 'CHKP', 'CTAS', 'CSCO', 'CTXS', 'CTSH', 'CMCSA', 'CPRT', 'COST', 'CSX', 'DXCM', 'DOCU', 'DLTR', 'EBAY', 'EA', 'EXC', 'EXPE', 'FB', 'FAST', 'FISV', 'FOXA', 'FOX', 'GILD', 'IDXX', 'ILMN', 'INCY', 'INTC', 'INTU', 'ISRG', 'JD', 'KLAC', 'KHC', 'LRCX', 'LBTYA', 'LBTYK', 'LULU', 'MAR', 'MXIM', 'MELI', 'MCHP', 'MU', 'MSFT', 'MRNA', 'MDLZ', 'MNST', 'NTES', 'NFLX', 'NVDA', 'NXPI', 'ORLY', 'PCAR', 'PAYX', 'PYPL', 'PEP', 'PDD', 'QCOM', 'REGN', 'ROST', 'SGEN', 'SIRI', 'SWKS', 'SPLK', 'SBUX', 'SNPS', 'TMUS', 'TTWO', 'TSLA', 'TXN', 'TCOM', 'ULTA', 'VRSN', 'VRSK', 'VRTX', 'WBA', 'WDAY', 'WDC', 'XEL', 'XLNX', 'ZM']

symbols = symbols_snp500 + symbols_nasdaq100
symbols = list(set(symbols))
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

            if evr                               is None and CONTINUE_UPON_NONE_FIELD or evr                               > 20 : continue
            if profit_margin                     is None and CONTINUE_UPON_NONE_FIELD                                           : continue
            if forward_eps                       is None and CONTINUE_UPON_NONE_FIELD                                           : continue
            if trailing_eps                      is None and CONTINUE_UPON_NONE_FIELD or trailing_eps                      <  0 : continue
            if price_to_book                     is None and CONTINUE_UPON_NONE_FIELD                                           : continue
            if earnings_quarterly_growth         is None and CONTINUE_UPON_NONE_FIELD or earnings_quarterly_growth         <  0 : continue
            if price_to_earnings_to_growth_ratio is None and CONTINUE_UPON_NONE_FIELD or price_to_earnings_to_growth_ratio <  0 : continue
            if shares_outstanding                is None and CONTINUE_UPON_NONE_FIELD                                           : continue
            if net_income_to_common_shareholders is None and CONTINUE_UPON_NONE_FIELD or net_income_to_common_shareholders <  0 : continue

            nitcsh_div_shares_outstanding     = round(float(net_income_to_common_shareholders)/float(shares_outstanding),2)
            nitcsh_div_num_employees          = round(float(net_income_to_common_shareholders)/float(num_employees),2)
            print('Name: {}, EV/R: {}, profit_margin: {}, forward_eps: {}, trailing_eps: {}, price_to_book: {}, shares_outstanding: {}, net_income_to_common_shareholders: {}, nitcsh_div_shares_outstanding: {}, # employees: {}, nitcsh_div_num_employees: {}, earnings_quarterly_growth: {}, price_to_earnings_to_growth_ratio: {}'.format(short_name, evr, profit_margin, forward_eps, trailing_eps, price_to_book, shares_outstanding, net_income_to_common_shareholders, nitcsh_div_shares_outstanding, num_employees, nitcsh_div_num_employees, earnings_quarterly_growth, price_to_earnings_to_growth_ratio))

        except:
            print("Exception in info")
            if CONTINUE_UPON_INFO_EXCEPTION:
                continue
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
        try:
            last_4_dividends = symbol.dividends[-4:]
            print('last_4_dividends list: {}, {}, {}, {}'.format(last_4_dividends[0],last_4_dividends[1],last_4_dividends[2],last_4_dividends[3]))
        except:
            last_4_dividends = [0,0,0,0]
            print("Exception in dividends")
        writer.writerow([symb, short_name, evr, profit_margin, forward_eps, trailing_eps, price_to_book, shares_outstanding, net_income_to_common_shareholders, nitcsh_div_shares_outstanding, num_employees, nitcsh_div_num_employees, earnings_quarterly_growth, price_to_earnings_to_growth_ratio, last_4_dividends[0], last_4_dividends[1], last_4_dividends[2], last_4_dividends[3]])
        print('\n')

