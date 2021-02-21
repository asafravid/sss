#########################################################
# Version 201 - Author: Asaf Ravid <asaf.rvd@gmail.com> #
#########################################################

# TODO: ASAF: 1. Finnacials, for instance. Also Favoring EVR is not enough, apply the favor over the PEtrailing (P/E) as well - research the DB prior to that.
#                - Add column: pe_effective...
#             2. What about that ev_to_cfo_ratio of 1000 - check that all is well in db.csv and in the results csvs... maybe increase it?
#             3. Check and multi dim and investigate earnings_quarterly_growth_min

import time
import random
import pandas   as pd
import yfinance as yf
import csv
import os
import itertools
import sss_filenames
import investpy
import math

from threading import Thread
from dataclasses import dataclass

NUM_ROUND_DECIMALS                        = 4
NUM_EMPLOYEES_UNKNOWN                     = 10000000   # This will make the company very inefficient in terms of number of employees
PROFIT_MARGIN_UNKNOWN                     = 0.001      # This will make the company almost not profitable terms of profit margins, thus less attractive
PERCENT_HELD_INSTITUTIONS_LOW             = 0.01       # low, to make less relevant
PEG_UNKNOWN                               = 1          # use a neutral value when PEG is unknown
SHARES_OUTSTANDING_UNKNOWN                = 100000000  # 100 Million Shares - just a value for calculation of a currently unused vaue
BAD_SSS                                   = 10.0 ** 15.0
BAD_SSSE                                  = 0
PROFIT_MARGIN_WEIGHTS                     = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]  # from oldest to newest
CASH_FLOW_WEIGHTS                         = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]  # from oldest to newest
REVENUES_WEIGHTS                          = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]  # from oldest to newest
EARNINGS_WEIGHTS                          = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]  # from oldest to newest
EARNINGS_QUARTERLY_GROWTH_UNKNOWN         = -0.75  # -75% TODO: ASAFR: 1. Scan (like pm and ever) values of earnings_quarterly_growth for big data research better recommendations
EARNINGS_QUARTERLY_GROWTH_POSITIVE_FACTOR = 10.0   # When profit margin is positive, it will have a 10x factor on the 1 + function
TRAILING_EPS_PERCENTAGE_DAMP_FACTOR       = 0.01   # When the trailing_eps_percentage is very low (units are ratio here), this damper shall limit the affect to x100 not more)
PROFIT_MARGIN_DAMPER                      = 0.001  # When the profit_margin           is very low (units are ratio here), this damper shall limit the affect to x1000 not more)

@dataclass
class StockData:
    ticker:                                         str   = 'None'
    short_name:                                     str   = 'None'
    quote_type:                                     str   = 'None'
    sector:                                         str   = 'None'
    sss_value:                                      float = BAD_SSS
    ssss_value:                                     float = BAD_SSS
    sssss_value:                                    float = BAD_SSS
    ssse_value:                                     float = BAD_SSSE
    sssse_value:                                    float = BAD_SSSE
    ssssse_value:                                   float = BAD_SSSE
    sssi_value:                                     float = BAD_SSS
    ssssi_value:                                    float = BAD_SSS
    sssssi_value:                                   float = BAD_SSS
    sssei_value:                                    float = BAD_SSSE
    ssssei_value:                                   float = BAD_SSSE
    sssssei_value:                                  float = BAD_SSSE
    annualized_revenue:                             float = 0.0
    annualized_earnings:                            float = 0.0
    enterprise_value_to_revenue:                    float = 0.0
    evr_effective:                                  float = 0.0
    trailing_price_to_earnings:                     float = 0.0
    trailing_12months_price_to_sales:               float = 0.0
    tpe_effective:                                  float = 0.0
    enterprise_value_to_ebitda:                     float = 0.0
    profit_margin:                                  float = 0.0
    annualized_profit_margin:                       float = 0.0
    held_percent_institutions:                      float = 0.0
    forward_eps:                                    float = 0.0
    trailing_eps:                                   float = 0.0
    previous_close:                                 float = 0.0
    trailing_eps_percentage:                        float = 0.0 # trailing_eps / previousClose
    price_to_book:                                  float = 0.0
    shares_outstanding:                             float = 0.0
    net_income_to_common_shareholders:              float = 0.0
    nitcsh_to_shares_outstanding:                   float = 0.0
    num_employees:                                  int   = 0
    enterprise_value:                               int   = 0
    nitcsh_to_num_employees:                        float = 0.0
    earnings_quarterly_growth:                      float = 0.0  # Value is a ratio, such that when multiplied by 100, yields percentage (%) units
    price_to_earnings_to_growth_ratio:              float = 0.0
    sqrt_peg_ratio:                                 float = 0.0
    annualized_cash_flow_from_operating_activities: float = 0.0
    ev_to_cfo_ratio:                                float = 0.0  # https://investinganswers.com/dictionary/e/enterprise-value-cash-flow-operations-evcfo
    last_4_dividends_0:                             float = 0.0
    last_4_dividends_1:                             float = 0.0
    last_4_dividends_2:                             float = 0.0
    last_4_dividends_3:                             float = 0.0

def check_quote_type(stock_data, research_mode):
    if stock_data.quote_type == 'MUTUALFUND' and not research_mode: # Definition of a mutual fund 'quoteType' field in base.py, those are not interesting
        print('Mutual Fund: Skip')
        return False  # Not interested in those and they lack all the below info[] properties so nothing to do with them anyways
    return True


def check_sector(stock_data, sectors_list):
    if len(sectors_list) and stock_data.sector not in sectors_list:
        print('              Skipping Sector {}'.format(stock_data.sector))
        return False
    return True


def text_to_num(text):
    d = {
        'K': 1000,
        'M': 1000000,
        'B': 1000000000,
        'T': 1000000000000
    }
    if not isinstance(text, str):
        # Non-strings are bad are missing data in poster's submission
        return 0

    text = text.replace(' ','')

    if text[-1] in d:  # separate out the K, M, B or T
        num, magnitude = text[:-1], text[-1]
        return int(float(num) * d[magnitude])
    else:
        return float(text)


def process_info(symbol, stock_data, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode):
    try:
        return_value = True
        info              = {}
        earnings          = {}
        stock_information = {}
        if build_csv_db:
            try:
                info                  = symbol.get_info()
                cash_flows            = symbol.get_cashflow(as_dict=True)
                # balance_sheet         = symbol.get_balance_sheet(as_dict=True)
                # balancesheet          = symbol.get_balancesheet(as_dict=True)
                earnings              = symbol.get_earnings(as_dict=True)  # TODO: ASAFR: There is supposed to be a quarterly_earnings() or earnings_quarterly() which will open up a whole new level of scanning: inner-year scanning
                # financials            = symbol.get_financials(as_dict=True)
                # institutional_holders = symbol.get_institutional_holders(as_dict=True)
                # sustainability        = symbol.get_sustainability(as_dict=True)
                # major_holders         = symbol.get_major_holders(as_dict=True)
                # mutualfund_holders    = symbol.get_mutualfund_holders(as_dict=True)
            except Exception as e:
                if not research_mode: print("              Exception in {} symbol.get_info(): {}".format(stock_data.ticker, e))
                pass

            if use_investpy:
                try:
                    if tase_mode:
                        stock_information = investpy.get_stock_information(stock=stock_data.ticker.replace('.TA',''), country='israel', as_json=True)
                    else:
                        stock_information = investpy.get_stock_information(stock=stock_data.ticker, country='united states', as_json=True)
                except Exception as e:
                    if not research_mode: print("              Exception in {} get_stock_information(): {}".format(stock_data.ticker, e))
                    pass

            if 'shortName' in info: stock_data.short_name = info['shortName']
            else:                   stock_data.short_name = 'None'

            weight_index    = 0
            cash_flows_list = []
            weights_sum     = 0
            try:
                for key in reversed(list(cash_flows)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Total Cash From Operating Activities' in cash_flows[key] and not math.isnan(cash_flows[key]['Total Cash From Operating Activities']):
                        cash_flows_list.append(cash_flows[key]['Total Cash From Operating Activities']*CASH_FLOW_WEIGHTS[weight_index])
                        weights_sum += CASH_FLOW_WEIGHTS[weight_index]
                        weight_index += 1
                if weights_sum > 0: stock_data.annualized_cash_flow_from_operating_activities = sum(cash_flows_list) / weights_sum
            except Exception as e:
                print("Exception in cash_flows: {}".format(e))
                stock_data.annualized_cash_flow_from_operating_activities = 0
                pass

        if stock_data.short_name is     None:                       stock_data.short_name = 'None'
        if stock_data.short_name is not None and not research_mode: print('              {:35}:'.format(stock_data.short_name))

        if build_csv_db and 'quoteType' in info: stock_data.quote_type = info['quoteType']
        if not check_quote_type(stock_data, research_mode):     return_value = False

        if build_csv_db and 'sector' in info:    stock_data.sector = info['sector']
        if len(sectors_list):
            if sectors_filter_out:
                if check_sector(stock_data, sectors_list):     return_value = False
            else:
                if not check_sector(stock_data, sectors_list): return_value = False
        if build_csv_db:
            if 'fullTimeEmployees' in info:      stock_data.num_employees = info['fullTimeEmployees']
            else:                                stock_data.num_employees = NUM_EMPLOYEES_UNKNOWN
            if stock_data.num_employees is None: stock_data.num_employees = NUM_EMPLOYEES_UNKNOWN

            if earnings is not None and 'Revenue' in earnings and 'Earnings'in earnings:
                len_revenue_list  = len(earnings['Revenue'])
                len_earnings_list = len(earnings['Earnings'])
                if len_earnings_list == len_revenue_list:
                    weight_index              = 0
                    earnings_to_revenues_list = []
                    weights_sum               = 0
                    try:
                        for key in earnings['Revenue']:
                            if float(earnings['Revenue'][key]) > 0:
                                earnings_to_revenues_list.append((float(earnings['Earnings'][key])/float(earnings['Revenue'][key]))*PROFIT_MARGIN_WEIGHTS[weight_index])
                                weights_sum  += PROFIT_MARGIN_WEIGHTS[weight_index]
                            weight_index += 1
                        if weights_sum > 0: stock_data.annualized_profit_margin = sum(earnings_to_revenues_list)/weights_sum
                    except Exception as e:
                        print("Exception in annualized_profit_margin: {}".format(e))
                        pass

            if earnings is not None and 'Revenue' in earnings:
                weight_index  = 0
                revenues_list = []
                weights_sum   = 0
                for key in earnings['Revenue']:
                    revenues_list.append((float(earnings['Revenue'][key])) * REVENUES_WEIGHTS[weight_index])
                    weights_sum += REVENUES_WEIGHTS[weight_index]
                    weight_index += 1
                stock_data.annualized_revenue = sum(revenues_list) / weights_sum

            if earnings is not None and 'Earnings' in earnings:
                weight_index  = 0
                earnings_list = []
                weights_sum   = 0
                for key in earnings['Earnings']:
                    earnings_list.append((float(earnings['Earnings'][key])) * EARNINGS_WEIGHTS[weight_index])
                    weights_sum += EARNINGS_WEIGHTS[weight_index]
                    weight_index += 1
                stock_data.annualized_earnings = sum(earnings_list) / weights_sum

            if 'profitMargins' in info:          stock_data.profit_margin = info['profitMargins']
            else:                                stock_data.profit_margin = PROFIT_MARGIN_UNKNOWN
            if stock_data.profit_margin is None: stock_data.profit_margin = PROFIT_MARGIN_UNKNOWN

            if 'heldPercentInstitutions' in info:                                                         stock_data.held_percent_institutions = info['heldPercentInstitutions']
            else:                                                                                         stock_data.held_percent_institutions = PERCENT_HELD_INSTITUTIONS_LOW
            if stock_data.held_percent_institutions is None or stock_data.held_percent_institutions == 0: stock_data.held_percent_institutions = PERCENT_HELD_INSTITUTIONS_LOW

            if 'enterpriseToRevenue' in info:                          stock_data.enterprise_value_to_revenue = info['enterpriseToRevenue']  # https://www.investopedia.com/terms/e/ev-revenue-multiple.asp
            else:                                                      stock_data.enterprise_value_to_revenue = None # Mark as None, so as to try and calculate manually. TODO: ASAFR: Do the same to the Price and to the Earnings and the Price/Earnings (Also to sales if possible)
            if isinstance(stock_data.enterprise_value_to_revenue,str): stock_data.enterprise_value_to_revenue = None # Mark as None, so as to try and calculate manually.

            if 'enterpriseToEbitda' in info:                           stock_data.enterprise_value_to_ebitda  = info['enterpriseToEbitda']  # The lower the better: https://www.investopedia.com/ask/answers/072715/what-considered-healthy-evebitda.asp
            else:                                                      stock_data.enterprise_value_to_ebitda  = None
            if isinstance(stock_data.enterprise_value_to_ebitda,str):  stock_data.enterprise_value_to_ebitda  = None

            if 'trailingPE' in info:
                stock_data.trailing_price_to_earnings  = info['trailingPE']  # https://www.investopedia.com/terms/t/trailingpe.asp
                if tase_mode: stock_data.trailing_price_to_earnings /= 100.0  # In TLV stocks, Yahoo multiplies trailingPE by a factor of 100, so compensate
            else:
                stock_data.trailing_price_to_earnings  = None # Mark as None, so as to try and calculate manually.
            if isinstance(stock_data.trailing_price_to_earnings,str):  stock_data.trailing_price_to_earnings  = None # Mark as None, so as to try and calculate manually.

            if 'priceToSalesTrailing12Months' in info:
                stock_data.trailing_12months_price_to_sales = info['priceToSalesTrailing12Months']  # https://www.investopedia.com/articles/fundamental/03/032603.asp#:~:text=The%20price%2Dto%2Dsales%20ratio%20(Price%2FSales%20or,the%20more%20attractive%20the%20investment.
            else:
                stock_data.trailing_12months_price_to_sales  = None # Mark as None, so as to try and calculate manually.
            if isinstance(stock_data.trailing_12months_price_to_sales,str):  stock_data.trailing_12months_price_to_sales  = None # Mark as None, so as to try and calculate manually.

        # if stock_data.enterprise_value_to_revenue is None and stock_data.enterprise_value_to_ebitda is None and stock_data.trailing_price_to_earnings is None:
        #     if use_investpy and 'P/E Ratio' in stock_information and stock_information['P/E Ratio'] is not None:
        #         stock_data.trailing_price_to_earnings = float(text_to_num(stock_information['P/E Ratio']))
        #     elif not build_csv_db_only:
        #         if return_value and not research_mode: print('                            Skipping since trailing_price_to_earnings, enterprise_value_to_ebitda and enterprise_value_to_revenue are unknown')
        #         return_value = False

        if build_csv_db:
            # if   stock_data.enterprise_value_to_revenue is None and stock_data.enterprise_value_to_ebitda  is not None: stock_data.enterprise_value_to_revenue = stock_data.enterprise_value_to_ebitda
            # elif stock_data.enterprise_value_to_revenue is None and stock_data.trailing_price_to_earnings  is not None: stock_data.enterprise_value_to_revenue = stock_data.trailing_price_to_earnings
            #
            # if   stock_data.enterprise_value_to_ebitda  is None and stock_data.enterprise_value_to_revenue is not None: stock_data.enterprise_value_to_ebitda  = stock_data.enterprise_value_to_revenue
            # elif stock_data.enterprise_value_to_ebitda  is None and stock_data.trailing_price_to_earnings  is not None: stock_data.enterprise_value_to_ebitda  = stock_data.trailing_price_to_earnings
            #
            # if   stock_data.trailing_price_to_earnings  is None and stock_data.enterprise_value_to_revenue is not None: stock_data.trailing_price_to_earnings  = stock_data.enterprise_value_to_revenue
            # elif stock_data.trailing_price_to_earnings  is None and stock_data.enterprise_value_to_ebitda  is not None: stock_data.trailing_price_to_earnings  = stock_data.enterprise_value_to_ebitda

            if 'forwardEps'                                 in info: stock_data.forward_eps                       = info['forwardEps']
            else:                                                    stock_data.forward_eps                       = None
            if isinstance(stock_data.forward_eps,str):               stock_data.forward_eps                       = None

            if 'trailingEps'                                in info: stock_data.trailing_eps                      = info['trailingEps']
            else:                                                    stock_data.trailing_eps                      = None
            if isinstance(stock_data.trailing_eps,str):              stock_data.trailing_eps                      = None

            if 'previousClose'                              in info: stock_data.previous_close                    = info['previousClose']
            else:                                                    stock_data.previous_close                    = None
            if isinstance(stock_data.previous_close,str):            stock_data.previous_close                    = None

            if stock_data.trailing_eps is not None and stock_data.previous_close is not None and stock_data.previous_close > 0:
                stock_data.trailing_eps_percentage = stock_data.trailing_eps / stock_data.previous_close

            if 'priceToBook'                                in info: stock_data.price_to_book                     = info['priceToBook']
            else:                                                    stock_data.price_to_book                     = None # Mark as None, so as to try and calculate manually.
            if isinstance(stock_data.price_to_book,str):             stock_data.price_to_book                     = None # Mark as None, so as to try and calculate manually.

            # Value is a ratio, such that when multiplied by 100, yields percentage (%) units:
            if 'earningsQuarterlyGrowth'                    in info: stock_data.earnings_quarterly_growth         = info['earningsQuarterlyGrowth']
            else:                                                    stock_data.earnings_quarterly_growth         = None
            if stock_data.earnings_quarterly_growth         is None: stock_data.earnings_quarterly_growth         = EARNINGS_QUARTERLY_GROWTH_UNKNOWN # TODO: ASAFR: Perhaps a variation is required for TASE (less information on stocks, etc)

            if 'pegRatio'                                   in info: stock_data.price_to_earnings_to_growth_ratio = info['pegRatio']
            else:                                                    stock_data.price_to_earnings_to_growth_ratio = PEG_UNKNOWN
            if stock_data.price_to_earnings_to_growth_ratio is None: stock_data.price_to_earnings_to_growth_ratio = PEG_UNKNOWN

            if 'sharesOutstanding'                          in info: stock_data.shares_outstanding                = info['sharesOutstanding']
            else:                                                    stock_data.shares_outstanding                = SHARES_OUTSTANDING_UNKNOWN
            if stock_data.shares_outstanding is None or stock_data.shares_outstanding == 0:
                if use_investpy and 'Shares Outstanding' in stock_information and stock_information['Shares Outstanding'] is not None:
                    stock_data.shares_outstanding = int(text_to_num(stock_information['Shares Outstanding']))
                else:
                    stock_data.shares_outstanding = SHARES_OUTSTANDING_UNKNOWN

            if 'netIncomeToCommon' in info: stock_data.net_income_to_common_shareholders = info['netIncomeToCommon']
            else:                           stock_data.net_income_to_common_shareholders = None # TODO: ASAFR: It may be possible to calculate this manually

            if 'enterpriseValue' in info and info['enterpriseValue'] is not None: stock_data.enterprise_value = info['enterpriseValue']
            if market_cap_included:
                if stock_data.enterprise_value is None or stock_data.enterprise_value <= 0:
                    if   'marketCap' in info and info['marketCap'] is not None:
                        stock_data.enterprise_value = int(info['marketCap'])
                    elif use_investpy and 'MarketCap' in stock_information and stock_information['MarketCap'] is not None:
                        stock_data.enterprise_value = int(text_to_num(stock_information['MarketCap']))

            # if no enterprise_value_to_ebitda, use earnings
            if stock_data.enterprise_value_to_ebitda is None and stock_data.annualized_earnings > 0:
                stock_data.enterprise_value_to_ebitda = float(stock_data.enterprise_value) / stock_data.annualized_earnings

            if stock_data.annualized_cash_flow_from_operating_activities > 0:
                stock_data.ev_to_cfo_ratio = float(stock_data.enterprise_value)/stock_data.annualized_cash_flow_from_operating_activities
            else:
                stock_data.ev_to_cfo_ratio = ev_to_cfo_ratio_limit*10  # Set a very high value to make stock unatractive

        if not build_csv_db_only and (stock_data.enterprise_value is None or stock_data.enterprise_value < min_enterprise_value_millions_usd*1000000):
            if return_value and not research_mode: print('                            Skipping enterprise_value: {}'.format(stock_data.enterprise_value))
            return_value = False

        if stock_data.enterprise_value_to_revenue is None and stock_data.enterprise_value is not None and use_investpy and 'Revenue' in stock_information and stock_information['Revenue'] is not None  and text_to_num(stock_information['Revenue']) > 0:
            stock_data.enterprise_value_to_revenue = float(stock_data.enterprise_value)/float(text_to_num(stock_information['Revenue']))

        if not build_csv_db_only and (stock_data.evr_effective is None or stock_data.evr_effective <= 0 or stock_data.evr_effective > enterprise_value_to_revenue_limit):
            if return_value and not research_mode: print('                            Skipping enterprise_value_to_revenue: {}'.format(stock_data.evr_effective))
            return_value = False

        if build_csv_db_only:
            if stock_data.enterprise_value_to_revenue is not None and stock_data.enterprise_value_to_revenue <= 0:
                stock_data.evr_effective = stock_data.enterprise_value/stock_data.annualized_revenue
            else:
                stock_data.evr_effective = stock_data.enterprise_value_to_revenue

        if not build_csv_db_only and (stock_data.enterprise_value_to_ebitda is None or stock_data.enterprise_value_to_ebitda <= 0):
            if return_value and not research_mode: print('                            Skipping enterprise_value_to_ebitda: {}'.format(stock_data.enterprise_value_to_ebitda))
            return_value = False

        if not build_csv_db_only and (stock_data.trailing_price_to_earnings is None or stock_data.trailing_price_to_earnings <= 0):
            if return_value and not research_mode: print('                            Skipping trailing_price_to_earnings: {}'.format(stock_data.trailing_price_to_earnings))
            return_value = False

        if not build_csv_db_only and (stock_data.trailing_12months_price_to_sales is None or stock_data.trailing_12months_price_to_sales <= 0):
            if return_value and not research_mode: print('                            Skipping trailing_12months_price_to_sales: {}'.format(stock_data.trailing_12months_price_to_sales))
            return_value = False

        if not build_csv_db_only and (stock_data.price_to_book is None or stock_data.price_to_book <= 0):
            if return_value and not research_mode: print('                            Skipping price_to_book: {}'.format(stock_data.price_to_book))
            return_value = False

        if build_csv_db_only and stock_data.trailing_price_to_earnings is not None:
            if stock_data.sector in favor_sectors:
                index = favor_sectors.index(stock_data.sector)
                stock_data.tpe_effective = stock_data.trailing_price_to_earnings / float(favor_sectors_by[index])  # ** 2
            else:
                stock_data.tpe_effective = stock_data.trailing_price_to_earnings

        if stock_data.profit_margin is None  or stock_data.profit_margin < profit_margin_limit:
            if stock_data.profit_margin is not None or stock_data.profit_margin <= 0:
                if not build_csv_db_only and stock_data.annualized_profit_margin < profit_margin_limit:
                    if return_value and not research_mode: print('                            Skipping profit_margin: {}'.format(stock_data.profit_margin))
                    return_value = False

        if stock_data.ev_to_cfo_ratio is None  or stock_data.ev_to_cfo_ratio > ev_to_cfo_ratio_limit or stock_data.ev_to_cfo_ratio <= 0:
            if return_value and not research_mode: print('                            Skipping ev_to_cfo_ratio: {}'.format(stock_data.ev_to_cfo_ratio))
            return_value = False

        if stock_data.trailing_eps is None:
            if not build_csv_db_only and use_investpy and 'EPS' in stock_information and stock_information['EPS'] is not None:
                stock_data.trailing_eps = float(text_to_num(stock_information['EPS']))

        if not build_csv_db_only and (stock_data.trailing_eps is None or stock_data.trailing_eps is not None and stock_data.trailing_eps <= 0):
            if return_value and not research_mode: print('                            Skipping trailing_eps: {}'.format(stock_data.trailing_eps))
            return_value = False

        #if not build_csv_db_only and stock_data.previous_close is None:
        #    if return_value and not research_mode: print('                            Skipping previous_close: {}'.format(stock_data.previous_close))
        #    return_value = False

        # in TASE, forward EPS is mostly not provided, so allow it to not appear in stock_data:
        if not build_csv_db_only and not tase_mode and (stock_data.forward_eps is None or stock_data.forward_eps is not None and stock_data.forward_eps <= 0):
            if return_value and not research_mode: print('                            Skipping forward_eps: {}'.format(stock_data.forward_eps))
            return_value = False

        if not build_csv_db_only and (stock_data.earnings_quarterly_growth is None or stock_data.earnings_quarterly_growth < earnings_quarterly_growth_min):
            if return_value and not research_mode: print('                            Skipping earnings_quarterly_growth: {}'.format(stock_data.earnings_quarterly_growth))
            return_value = False

        if not build_csv_db_only and (stock_data.price_to_earnings_to_growth_ratio is None or stock_data.price_to_earnings_to_growth_ratio < 0):
            if return_value and not research_mode: print('                            Skipping price_to_earnings_to_growth_ratio: {}'.format(stock_data.price_to_earnings_to_growth_ratio))
            if return_value: return_value = False

        if build_csv_db_only and stock_data.price_to_earnings_to_growth_ratio > 0: stock_data.sqrt_peg_ratio = math.sqrt(stock_data.price_to_earnings_to_growth_ratio)

        if not build_csv_db_only and (stock_data.net_income_to_common_shareholders is None or stock_data.net_income_to_common_shareholders < 0):
            if return_value and not research_mode: print('                            Skipping net_income_to_common_shareholders: {}'.format(stock_data.net_income_to_common_shareholders))
            if return_value: return_value = False

        if build_csv_db:
            if return_value:
                if stock_data.shares_outstanding and stock_data.net_income_to_common_shareholders is not None: stock_data.nitcsh_to_shares_outstanding = float(stock_data.net_income_to_common_shareholders) / float(stock_data.shares_outstanding)
                if stock_data.num_employees      and stock_data.net_income_to_common_shareholders is not None: stock_data.nitcsh_to_num_employees      = float(stock_data.net_income_to_common_shareholders) / float(stock_data.num_employees)

                max_profit_margin_effective       = PROFIT_MARGIN_DAMPER + max(stock_data.profit_margin, stock_data.annualized_profit_margin)
                if stock_data.earnings_quarterly_growth > 0:
                    earnings_qgrowth_factor_effective = (1    + EARNINGS_QUARTERLY_GROWTH_POSITIVE_FACTOR*stock_data.earnings_quarterly_growth)
                else:
                    earnings_qgrowth_factor_effective = (1    + stock_data.earnings_quarterly_growth)
                # trailing_eps_percentage_effective = (TRAILING_EPS_PERCENTAGE_DAMP_FACTOR + stock_data.trailing_eps_percentage)

                if max_profit_margin_effective is not None and max_profit_margin_effective > 0 and earnings_qgrowth_factor_effective is not None and earnings_qgrowth_factor_effective > 0 and stock_data.price_to_earnings_to_growth_ratio is not None and stock_data.price_to_earnings_to_growth_ratio > 0 and stock_data.tpe_effective is not None and stock_data.tpe_effective > 0 and stock_data.enterprise_value_to_ebitda is not None and stock_data.enterprise_value_to_ebitda > 0 and stock_data.ev_to_cfo_ratio is not None and stock_data.ev_to_cfo_ratio > 0 and stock_data.sqrt_peg_ratio is not None and stock_data.sqrt_peg_ratio > 0:
                    if stock_data.trailing_12months_price_to_sales is not None and stock_data.trailing_12months_price_to_sales and stock_data.trailing_12months_price_to_sales is not None and stock_data.trailing_12months_price_to_sales > 0:
                        if stock_data.price_to_book is not None and stock_data.price_to_book > 0:
                            stock_data.sss_value = float(((stock_data.evr_effective * stock_data.tpe_effective * stock_data.enterprise_value_to_ebitda * stock_data.trailing_12months_price_to_sales * stock_data.price_to_book) / (max_profit_margin_effective                                        )) * ((stock_data.sqrt_peg_ratio * stock_data.ev_to_cfo_ratio) / earnings_qgrowth_factor_effective))  # The lower  the better
                        stock_data.ssss_value    = float(((stock_data.evr_effective * stock_data.tpe_effective * stock_data.enterprise_value_to_ebitda * stock_data.trailing_12months_price_to_sales                           ) / (max_profit_margin_effective                                        )) * ((stock_data.sqrt_peg_ratio * stock_data.ev_to_cfo_ratio) / earnings_qgrowth_factor_effective))  # the lower  the better
                    stock_data.sssss_value       = float(((stock_data.evr_effective * stock_data.tpe_effective * stock_data.enterprise_value_to_ebitda                                                                         ) / (max_profit_margin_effective                                        )) * ((stock_data.sqrt_peg_ratio * stock_data.ev_to_cfo_ratio) / earnings_qgrowth_factor_effective))  # the lower  the better

                    if (stock_data.sss_value):    stock_data.ssse_value    = float(stock_data.nitcsh_to_num_employees / stock_data.sss_value  )                                                                                                                                                                                                                                                              # the higher the better
                    if (stock_data.ssss_value):   stock_data.sssse_value   = float(stock_data.nitcsh_to_num_employees / stock_data.ssss_value )                                                                                                                                                                                                                                                              # the higher the better
                    if (stock_data.sssss_value):  stock_data.ssssse_value  = float(stock_data.nitcsh_to_num_employees / stock_data.sssss_value)                                                                                                                                                                                                                                                              # the higher the better

                    if stock_data.trailing_12months_price_to_sales is not None and stock_data.trailing_12months_price_to_sales and stock_data.trailing_12months_price_to_sales is not None and stock_data.trailing_12months_price_to_sales > 0:
                        if stock_data.price_to_book is not None and stock_data.price_to_book > 0:
                            stock_data.sssi_value = float(((stock_data.evr_effective * stock_data.tpe_effective * stock_data.enterprise_value_to_ebitda * stock_data.trailing_12months_price_to_sales * stock_data.price_to_book) / (max_profit_margin_effective * stock_data.held_percent_institutions)) * ((stock_data.sqrt_peg_ratio * stock_data.ev_to_cfo_ratio) / earnings_qgrowth_factor_effective))  # The lower  the better
                        stock_data.ssssi_value    = float(((stock_data.evr_effective * stock_data.tpe_effective * stock_data.enterprise_value_to_ebitda * stock_data.trailing_12months_price_to_sales                           ) / (max_profit_margin_effective * stock_data.held_percent_institutions)) * ((stock_data.sqrt_peg_ratio * stock_data.ev_to_cfo_ratio) / earnings_qgrowth_factor_effective))  # the lower  the better
                    stock_data.sssssi_value       = float(((stock_data.evr_effective * stock_data.tpe_effective * stock_data.enterprise_value_to_ebitda                                                                         ) / (max_profit_margin_effective * stock_data.held_percent_institutions)) * ((stock_data.sqrt_peg_ratio * stock_data.ev_to_cfo_ratio) / earnings_qgrowth_factor_effective))  # the lower  the better

                    if (stock_data.sssi_value):   stock_data.sssei_value   = float(stock_data.nitcsh_to_num_employees / stock_data.sssi_value  )                                                                                                                                                                                                                                                             # the higher the better
                    if (stock_data.ssssi_value):  stock_data.ssssei_value  = float(stock_data.nitcsh_to_num_employees / stock_data.ssssi_value )                                                                                                                                                                                                                                                             # the higher the better
                    if (stock_data.sssssi_value): stock_data.sssssei_value = float(stock_data.nitcsh_to_num_employees / stock_data.sssssi_value)                                                                                                                                                                                                                                                             # the higher the better
                else:
                    stock_data.sss_value     = BAD_SSS
                    stock_data.ssss_value    = BAD_SSS
                    stock_data.sssss_value   = BAD_SSS
                    stock_data.ssse_value    = BAD_SSSE
                    stock_data.sssse_value   = BAD_SSSE
                    stock_data.ssssse_value  = BAD_SSSE
                    stock_data.sssi_value    = BAD_SSS
                    stock_data.ssssi_value   = BAD_SSS
                    stock_data.sssssi_value  = BAD_SSS
                    stock_data.sssei_value   = BAD_SSSE
                    stock_data.ssssei_value  = BAD_SSSE
                    stock_data.sssssei_value = BAD_SSSE

                # Rounding to non-None values + set None values to 0 for simplicity:
                if stock_data.sss_value                                      is not None: stock_data.sss_value                                      = round(stock_data.sss_value,                                      NUM_ROUND_DECIMALS)
                if stock_data.ssss_value                                     is not None: stock_data.ssss_value                                     = round(stock_data.ssss_value,                                     NUM_ROUND_DECIMALS)
                if stock_data.sssss_value                                    is not None: stock_data.sssss_value                                    = round(stock_data.sssss_value,                                    NUM_ROUND_DECIMALS)
                if stock_data.ssse_value                                     is not None: stock_data.ssse_value                                     = round(stock_data.ssse_value,                                     NUM_ROUND_DECIMALS)
                if stock_data.sssse_value                                    is not None: stock_data.sssse_value                                    = round(stock_data.sssse_value,                                    NUM_ROUND_DECIMALS)
                if stock_data.ssssse_value                                   is not None: stock_data.ssssse_value                                   = round(stock_data.ssssse_value,                                   NUM_ROUND_DECIMALS)
                if stock_data.sssi_value                                     is not None: stock_data.sssi_value                                     = round(stock_data.sssi_value,                                     NUM_ROUND_DECIMALS)
                if stock_data.ssssi_value                                    is not None: stock_data.ssssi_value                                    = round(stock_data.ssssi_value,                                    NUM_ROUND_DECIMALS)
                if stock_data.sssssi_value                                   is not None: stock_data.sssssi_value                                   = round(stock_data.sssssi_value,                                   NUM_ROUND_DECIMALS)
                if stock_data.sssei_value                                    is not None: stock_data.sssei_value                                    = round(stock_data.sssei_value,                                    NUM_ROUND_DECIMALS)
                if stock_data.ssssei_value                                   is not None: stock_data.ssssei_value                                   = round(stock_data.ssssei_value,                                   NUM_ROUND_DECIMALS)
                if stock_data.sssssei_value                                  is not None: stock_data.sssssei_value                                  = round(stock_data.sssssei_value,                                  NUM_ROUND_DECIMALS)
                if stock_data.annualized_revenue                             is not None: stock_data.annualized_revenue                             = round(stock_data.annualized_revenue,                             NUM_ROUND_DECIMALS)
                if stock_data.annualized_earnings                            is not None: stock_data.annualized_earnings                            = round(stock_data.annualized_earnings,                            NUM_ROUND_DECIMALS)
                if stock_data.enterprise_value_to_revenue                    is not None: stock_data.enterprise_value_to_revenue                    = round(stock_data.enterprise_value_to_revenue,                    NUM_ROUND_DECIMALS)
                if stock_data.evr_effective                                  is not None: stock_data.evr_effective                                  = round(stock_data.evr_effective,                                  NUM_ROUND_DECIMALS)
                if stock_data.trailing_price_to_earnings                     is not None: stock_data.trailing_price_to_earnings                     = round(stock_data.trailing_price_to_earnings,                     NUM_ROUND_DECIMALS)
                if stock_data.trailing_12months_price_to_sales               is not None: stock_data.trailing_12months_price_to_sales               = round(stock_data.trailing_12months_price_to_sales,               NUM_ROUND_DECIMALS)
                if stock_data.tpe_effective                                  is not None: stock_data.tpe_effective                                  = round(stock_data.tpe_effective,                                  NUM_ROUND_DECIMALS)
                if stock_data.enterprise_value_to_ebitda                     is not None: stock_data.enterprise_value_to_ebitda                     = round(stock_data.enterprise_value_to_ebitda,                     NUM_ROUND_DECIMALS)
                if stock_data.profit_margin                                  is not None: stock_data.profit_margin                                  = round(stock_data.profit_margin,                                  NUM_ROUND_DECIMALS)
                if stock_data.annualized_profit_margin                       is not None: stock_data.annualized_profit_margin                       = round(stock_data.annualized_profit_margin,                       NUM_ROUND_DECIMALS)
                if stock_data.ev_to_cfo_ratio                                is not None: stock_data.ev_to_cfo_ratio                                = round(stock_data.ev_to_cfo_ratio,                                NUM_ROUND_DECIMALS)
                if stock_data.held_percent_institutions                      is not None: stock_data.held_percent_institutions                      = round(stock_data.held_percent_institutions,                      NUM_ROUND_DECIMALS)
                if stock_data.forward_eps                                    is not None: stock_data.forward_eps                                    = round(stock_data.forward_eps,                                    NUM_ROUND_DECIMALS)
                if stock_data.trailing_eps                                   is not None: stock_data.trailing_eps                                   = round(stock_data.trailing_eps,                                   NUM_ROUND_DECIMALS)
                if stock_data.previous_close                                 is not None: stock_data.previous_close                                 = round(stock_data.previous_close,                                 NUM_ROUND_DECIMALS)
                if stock_data.trailing_eps_percentage                        is not None: stock_data.trailing_eps_percentage                        = round(stock_data.trailing_eps_percentage,                        NUM_ROUND_DECIMALS)
                if stock_data.price_to_book                                  is not None: stock_data.price_to_book                                  = round(stock_data.price_to_book,                                  NUM_ROUND_DECIMALS)
                if stock_data.shares_outstanding                             is not None: stock_data.shares_outstanding                             = round(stock_data.shares_outstanding,                             NUM_ROUND_DECIMALS)
                if stock_data.net_income_to_common_shareholders              is not None: stock_data.net_income_to_common_shareholders              = round(stock_data.net_income_to_common_shareholders,              NUM_ROUND_DECIMALS)
                if stock_data.nitcsh_to_shares_outstanding                   is not None: stock_data.nitcsh_to_shares_outstanding                   = round(stock_data.nitcsh_to_shares_outstanding,                   NUM_ROUND_DECIMALS)
                if stock_data.num_employees                                  is not None: stock_data.num_employees                                  = round(stock_data.num_employees,                                  NUM_ROUND_DECIMALS)
                if stock_data.nitcsh_to_num_employees                        is not None: stock_data.nitcsh_to_num_employees                        = round(stock_data.nitcsh_to_num_employees,                        NUM_ROUND_DECIMALS)
                if stock_data.earnings_quarterly_growth                      is not None: stock_data.earnings_quarterly_growth                      = round(stock_data.earnings_quarterly_growth,                      NUM_ROUND_DECIMALS)
                if stock_data.price_to_earnings_to_growth_ratio              is not None: stock_data.price_to_earnings_to_growth_ratio              = round(stock_data.price_to_earnings_to_growth_ratio,              NUM_ROUND_DECIMALS)
                if stock_data.sqrt_peg_ratio                                 is not None: stock_data.sqrt_peg_ratio                                 = round(stock_data.sqrt_peg_ratio,                                 NUM_ROUND_DECIMALS)
                if stock_data.annualized_cash_flow_from_operating_activities is not None: stock_data.annualized_cash_flow_from_operating_activities = round(stock_data.annualized_cash_flow_from_operating_activities, NUM_ROUND_DECIMALS)
                if stock_data.ev_to_cfo_ratio                                is not None: stock_data.ev_to_cfo_ratio                                = round(stock_data.ev_to_cfo_ratio,                                NUM_ROUND_DECIMALS)
            else:
                stock_data.sss_value     = BAD_SSSE
                stock_data.ssss_value    = BAD_SSSE
                stock_data.sssss_value   = BAD_SSSE
                stock_data.ssse_value    = BAD_SSSE
                stock_data.sssse_value   = BAD_SSSE
                stock_data.ssssse_value  = BAD_SSSE
                stock_data.sssi_value    = BAD_SSS
                stock_data.ssssi_value   = BAD_SSS
                stock_data.sssssi_value  = BAD_SSS
                stock_data.sssei_value   = BAD_SSS
                stock_data.ssssei_value  = BAD_SSS
                stock_data.sssssei_value = BAD_SSS


        if build_csv_db:
            if stock_data.sss_value                         is     None: stock_data.sss_value                         = BAD_SSS
            if stock_data.ssss_value                        is     None: stock_data.ssss_value                        = BAD_SSS
            if stock_data.sssss_value                       is     None: stock_data.sssss_value                       = BAD_SSS
            if stock_data.ssse_value                        is     None: stock_data.ssse_value                        = BAD_SSSE
            if stock_data.sssse_value                       is     None: stock_data.sssse_value                       = BAD_SSSE
            if stock_data.ssssse_value                      is     None: stock_data.ssssse_value                      = BAD_SSSE
            if stock_data.sssi_value                        is     None: stock_data.sssi_value                        = BAD_SSS
            if stock_data.ssssi_value                       is     None: stock_data.ssssi_value                       = BAD_SSS
            if stock_data.sssssi_value                      is     None: stock_data.sssssi_value                      = BAD_SSS
            if stock_data.sssei_value                       is     None: stock_data.sssei_value                       = BAD_SSSE
            if stock_data.ssssei_value                      is     None: stock_data.ssssei_value                      = BAD_SSSE
            if stock_data.sssssei_value                     is     None: stock_data.sssssei_value                     = BAD_SSSE
            if stock_data.annualized_revenue                is     None: stock_data.annualized_revenue                = 0
            if stock_data.annualized_earnings               is     None: stock_data.annualized_earnings               = 0
            if stock_data.enterprise_value_to_revenue       is     None: stock_data.enterprise_value_to_revenue       = 0
            if stock_data.evr_effective                     is     None: stock_data.evr_effective                     = 0
            if stock_data.trailing_price_to_earnings        is     None: stock_data.trailing_price_to_earnings        = 0
            if stock_data.trailing_12months_price_to_sales  is     None: stock_data.trailing_12months_price_to_sales  = 0
            if stock_data.tpe_effective                     is     None: stock_data.tpe_effective                     = 0
            if stock_data.enterprise_value_to_ebitda        is     None: stock_data.enterprise_value_to_ebitda        = 0
            if stock_data.profit_margin                     is     None: stock_data.profit_margin                     = 0
            if stock_data.annualized_profit_margin          is     None: stock_data.annualized_profit_margin          = 0
            if stock_data.ev_to_cfo_ratio                   is     None: stock_data.ev_to_cfo_ratio                   = 0
            if stock_data.held_percent_institutions         is     None: stock_data.held_percent_institutions         = 0
            if stock_data.forward_eps                       is     None: stock_data.forward_eps                       = 0
            if stock_data.trailing_eps                      is     None: stock_data.trailing_eps                      = 0
            if stock_data.previous_close                    is     None: stock_data.previous_close                    = 0
            if stock_data.trailing_eps_percentage           is     None: stock_data.trailing_eps_percentage           = 0
            if stock_data.price_to_book                     is     None: stock_data.price_to_book                     = 0
            if stock_data.shares_outstanding                is     None: stock_data.shares_outstanding                = 0
            if stock_data.net_income_to_common_shareholders is     None: stock_data.net_income_to_common_shareholders = 0
            if stock_data.nitcsh_to_shares_outstanding      is     None: stock_data.nitcsh_to_shares_outstanding      = 0
            if stock_data.num_employees                     is     None: stock_data.num_employees                     = 0
            if stock_data.nitcsh_to_num_employees           is     None: stock_data.nitcsh_to_num_employees           = 0
            if stock_data.earnings_quarterly_growth         is     None: stock_data.earnings_quarterly_growth         = 0
            if stock_data.price_to_earnings_to_growth_ratio is     None: stock_data.price_to_earnings_to_growth_ratio = 0
            if stock_data.sqrt_peg_ratio                    is     None: stock_data.sqrt_peg_ratio                    = 0

            stock_data.last_4_dividends_0 = 0
            stock_data.last_4_dividends_1 = 0
            stock_data.last_4_dividends_2 = 0
            stock_data.last_4_dividends_3 = 0

            # try: TODO: ASAFR: Complete this backup data to the yfinance dividends information
            #     if tase_mode:
            #         stock_dividends = investpy.get_stock_dividends(stock=stock_data.ticker.replace('.TA',''), country='israel')
            #     else:
            #         stock_dividends = investpy.get_stock_dividends(stock=stock_data.ticker, country='united states')
            #     # print("stock_dividends: {}".format(stock_dividends.values.tolist()))
            # except Exception as e:
            #     print("Exception in investpy symbol.dividends: {}".format(e))
            #     pass

            try:
                if len(symbol.dividends) > 0: stock_data.last_4_dividends_0 = symbol.dividends[0]
                if len(symbol.dividends) > 1: stock_data.last_4_dividends_1 = symbol.dividends[1]
                if len(symbol.dividends) > 2: stock_data.last_4_dividends_2 = symbol.dividends[2]
                if len(symbol.dividends) > 3: stock_data.last_4_dividends_3 = symbol.dividends[3]

            except Exception as e:
                if not research_mode: print("Exception in symbol.dividends: {}".format(e))
                pass

        if return_value and not research_mode: print('                                          sector: {:15}, sss_value: {:15}, ssss_value: {:15}, sssss_value: {:15}, ssse_value: {:15}, sssse_value: {:15}, ssssse_value: {:15}, sssi_value: {:15}, ssssi_value: {:15}, sssssi_value: {:15}, sssei_value: {:15}, ssssei_value: {:15}, sssssei_value: {:15}, annualized_revenue: {:15}, annualized_earnings: {:15}, enterprise_value_to_revenue: {:15}, evr_effective: {:15}, trailing_price_to_earnings: {:15}, trailing_12months_price_to_sales: {:15}, tpe_effective: {:15}, enterprise_value_to_ebitda: {:15}, profit_margin: {:15}, annualized_profit_margin: {:15}, held_percent_institutions: {:15}, forward_eps: {:15}, trailing_eps: {:15}, previous_close: {:15}, trailing_eps_percentage: {:15}, price_to_book: {:15}, shares_outstanding: {:15}, net_income_to_common_shareholders: {:15}, nitcsh_to_shares_outstanding: {:15}, num_employees: {:15}, enterprise_value: {:15}, nitcsh_to_num_employees: {:15}, earnings_quarterly_growth: {:15}, price_to_earnings_to_growth_ratio: {:15}, sqrt_peg_ratio: {:15}, annualized_cash_flow_from_operating_activities: {:15}, ev_to_cfo_ratio: {:15}'.format(stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.sssssei_value, stock_data.annualized_revenue, stock_data.annualized_earnings, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.tpe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.sqrt_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.ev_to_cfo_ratio))
        return return_value

    except Exception as e:  # More information is output when exception is used instead of Exception
        if not research_mode: print("              Exception in {} info: {}".format(stock_data.ticker, e))
        return False


def check_interval(thread_id, interval_threads, interval_secs_to_avoid_http_errors, research_mode):
    if thread_id > 0 and thread_id % interval_threads == 0 and not research_mode:
        print("\n===========================================================================")
        print(  "[thread_id {:2} is an interval {} point, going to sleep for {} seconds]".format(thread_id, interval_threads, interval_secs_to_avoid_http_errors))
        print(  "===========================================================================\n")
        time.sleep(interval_secs_to_avoid_http_errors)


def process_symbols(symbols, csv_db_data, rows, rows_no_div, rows_only_div, thread_id, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode):
    iteration = 0
    if build_csv_db:
        for symb in symbols:
            iteration += 1
            sleep_seconds = round(random.uniform(float(relaxed_access)/2, float(relaxed_access)*2), NUM_ROUND_DECIMALS)
            time.sleep(sleep_seconds)
            if not research_mode: print('[Building DB: thread_id {:2} Sleeping for {:10} sec] Checking {:9} ({:4}/{:4}/{:4}):'.format(thread_id, sleep_seconds, symb, len(rows), iteration, len(symbols)))
            if tase_mode:
                symbol = yf.Ticker(symb)
            else:
                symbol = yf.Ticker(symb.replace('.','-'))
            stock_data = StockData(ticker=symb)
            if not process_info(symbol=symbol, stock_data=stock_data, build_csv_db_only=build_csv_db_only, use_investpy=use_investpy, tase_mode=tase_mode, sectors_list=sectors_list, sectors_filter_out=sectors_filter_out, build_csv_db=build_csv_db, profit_margin_limit=profit_margin_limit, ev_to_cfo_ratio_limit=ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd=min_enterprise_value_millions_usd, earnings_quarterly_growth_min=earnings_quarterly_growth_min, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_sectors=favor_sectors, favor_sectors_by=favor_sectors_by, market_cap_included=market_cap_included, research_mode=research_mode):
                if tase_mode and 'TLV:' not in stock_data.ticker: stock_data.ticker = 'TLV:' + stock_data.ticker.replace('.TA', '').replace('.','-')
                #                              Ticker	          Name	                 Sector	            sss_value	          ssss_value	         sssss_value	         ssse_value	            sssse_value	            ssssse_value	         sssi_value	            ssssi_value	            sssssi_value	         sssei_value	         ssssei_value	          sssssei_value	 annualized_revenue             annualized_earnings,            enterprise_value_to_revenue	            evr_effective	          trailing_price_to_earnings  trailing_12months_price_to_sales                        tpe_effective	            enterprise_value_to_ebitda	           profit_margin	         annualized_profit_margin	          held_percent_institutions	            forward_eps	            trailing_eps	         previous_close             trailing_eps_percentage             price_to_book	          shares_outstanding	         net_income_to_common_shareholders	           nitcsh_to_shares_outstanding	            num_employees	          enterprise_value	            nitcsh_to_num_employees	           earnings_quarterly_growth	          price_to_earnings_to_growth_ratio            sqrt_peg_ratio	          annualized_cash_flow_from_operating_activities             ev_to_cfo_ratio             last_dividend_0	            last_dividend_1	               last_dividend_2	              last_dividend_3
                csv_db_data.append([stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.sssssei_value, stock_data.annualized_revenue, stock_data.annualized_earnings, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.tpe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.sqrt_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.ev_to_cfo_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
                continue

            if tase_mode and 'TLV:' not in stock_data.ticker: stock_data.ticker = 'TLV:' + stock_data.ticker.replace('.TA', '').replace('.','-')
            dividends_sum = stock_data.last_4_dividends_0+stock_data.last_4_dividends_1+stock_data.last_4_dividends_2+stock_data.last_4_dividends_3
            rows.append(                           [stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.sssssei_value, stock_data.annualized_revenue, stock_data.annualized_earnings, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.tpe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.sqrt_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.ev_to_cfo_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
            if dividends_sum: rows_only_div.append([stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.sssssei_value, stock_data.annualized_revenue, stock_data.annualized_earnings, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.tpe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.sqrt_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.ev_to_cfo_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
            else:             rows_no_div.append(  [stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.sssssei_value, stock_data.annualized_revenue, stock_data.annualized_earnings, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.tpe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.sqrt_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.ev_to_cfo_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
            csv_db_data.append(                    [stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.sssssei_value, stock_data.annualized_revenue, stock_data.annualized_earnings, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.tpe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.sqrt_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.ev_to_cfo_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
    else: # DB already present
        for row in csv_db_data:
            iteration += 1
            symbol = row[0]
            if not research_mode: print('[Existing DB: thread_id {}] Checking {:9} ({:4}/{:4}/{:4}):'.format(thread_id, symbol, len(rows), iteration, len(symbols)))

            for fix_row_index in range(3,len(row)):  # for empty strings - convert value to 0
                if row[fix_row_index] == '':
                    if fix_row_index == 1:  # Name == '' --> 'None'
                        row[fix_row_index] = 'None'
                    else:
                        row[fix_row_index] = 0
            stock_data = StockData(ticker=symbol, short_name=row[1], sector=row[2], sss_value=float(row[3]), ssss_value=float(row[4]), sssss_value=float(row[5]), ssse_value=float(row[6]), sssse_value=float(row[7]), ssssse_value=float(row[8]), sssi_value=float(row[9]), ssssi_value=float(row[10]), sssssi_value=float(row[11]), sssei_value=float(row[12]), ssssei_value=float(row[13]), sssssei_value=float(row[14]), annualized_revenue=float(row[15]), annualized_earnings=float(row[16]), enterprise_value_to_revenue=float(row[17]), evr_effective=float(row[18]), trailing_price_to_earnings=float(row[19]), trailing_12months_price_to_sales=float(row[20]), tpe_effective=float(row[21]), enterprise_value_to_ebitda=float(row[22]), profit_margin=float(row[23]), annualized_profit_margin=float(row[24]), held_percent_institutions=float(row[25]), forward_eps=float(row[26]), trailing_eps=float(row[27]), previous_close=float(row[28]), trailing_eps_percentage=float(row[29]), price_to_book=float(row[30]), shares_outstanding=float(row[31]), net_income_to_common_shareholders=float(row[32]), nitcsh_to_shares_outstanding=float(row[33]), num_employees=int(row[34]), enterprise_value=int(float(row[35])), nitcsh_to_num_employees=float(row[36]), earnings_quarterly_growth=float(row[37]), price_to_earnings_to_growth_ratio=float(row[38]), sqrt_peg_ratio=float(row[39]), annualized_cash_flow_from_operating_activities=float(row[40]), ev_to_cfo_ratio=float(row[41]), last_4_dividends_0=float(row[42]), last_4_dividends_1=float(row[43]), last_4_dividends_2=float(row[44]), last_4_dividends_3=float(row[45]))
            if not process_info(symbol=symbol, stock_data=stock_data, build_csv_db_only=build_csv_db_only, use_investpy=use_investpy, tase_mode=tase_mode, sectors_list=sectors_list, sectors_filter_out=sectors_filter_out, build_csv_db=build_csv_db, profit_margin_limit=profit_margin_limit, min_enterprise_value_millions_usd=min_enterprise_value_millions_usd, ev_to_cfo_ratio_limit=ev_to_cfo_ratio_limit, earnings_quarterly_growth_min=earnings_quarterly_growth_min, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_sectors=favor_sectors, favor_sectors_by=favor_sectors_by, market_cap_included=market_cap_included, research_mode=research_mode):
                continue

            if tase_mode and 'TLV:' not in stock_data.ticker: stock_data.ticker = 'TLV:' + stock_data.ticker.replace('.TA', '').replace('.','-')

            dividends_sum = stock_data.last_4_dividends_0 + stock_data.last_4_dividends_1 + stock_data.last_4_dividends_2 + stock_data.last_4_dividends_3
            rows.append(                           [stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.sssssei_value, stock_data.annualized_revenue, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.tpe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.sqrt_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.ev_to_cfo_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
            if dividends_sum: rows_only_div.append([stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.sssssei_value, stock_data.annualized_revenue, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.tpe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.sqrt_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.ev_to_cfo_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])
            else:             rows_no_div.append(  [stock_data.ticker, stock_data.short_name, stock_data.sector, stock_data.sss_value, stock_data.ssss_value, stock_data.sssss_value, stock_data.ssse_value, stock_data.sssse_value, stock_data.ssssse_value, stock_data.sssi_value, stock_data.ssssi_value, stock_data.sssssi_value, stock_data.sssei_value, stock_data.ssssei_value, stock_data.sssssei_value, stock_data.annualized_revenue, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.tpe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.num_employees, stock_data.enterprise_value, stock_data.nitcsh_to_num_employees, stock_data.earnings_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.sqrt_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.ev_to_cfo_ratio, stock_data.last_4_dividends_0, stock_data.last_4_dividends_1, stock_data.last_4_dividends_2, stock_data.last_4_dividends_3])


#     BEST_N_SELECT                     = 50                     # Select best N from each of the resulting sorted tables
#     USE_INVESTPY                      = 0
#     MARKET_CAP_INCLUDED               = 1
#     FORWARD_EPS_INCLUDED              = 0*(not tase_mode)
#     NUM_THREADS                       = 20           # 1..20 Threads are supported
#     TASE_MODE                         = 0            # Work on the Israeli Market only: https://info.tase.co.il/eng/MarketData/Stocks/MarketData/Pages/MarketData.aspx
#     READ_UNITED_STATES_INPUT_SYMBOLS  = 1            # when set, covers 7,000 stocks
#     CSV_DB_PATH                       = 'Results/20201112-195244_MARKETCAP'
#     BUILD_CSV_DB                      = 1
#     BUILD_CSV_DB_ONLY                 = 1
#     SECTORS_LIST                      = [] # ['Technology', 'Consumer Cyclical', 'Consumer Defensive', 'Industrials', 'Consumer Goods']  # Allows filtering by sector(s)
def sss_run(sectors_list, sectors_filter_out, build_csv_db_only, build_csv_db, csv_db_path, read_united_states_input_symbols, tase_mode, num_threads, market_cap_included, use_investpy, research_mode, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, best_n_select, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, generate_result_folders=1, appearance_counter_dict_sss={}, appearance_counter_dict_ssss={}, appearance_counter_dict_sssss={}, appearance_counter_min=25, appearance_counter_max=35):
    # Working Mode:
    relaxed_access                     = (num_threads-1)/10.0            # In seconds
    interval_threads                   = 4 +     1*tase_mode -  2*read_united_states_input_symbols
    interval_secs_to_avoid_http_errors = 60*(7 - 1*tase_mode + 30*read_united_states_input_symbols)         # Every interval_threads, a INTERVALS_TO_AVOID_HTTP_ERRORS sec sleep will take place

    # Working Parameters:
    if not research_mode: profit_margin_limit               = profit_margin_limit
    earnings_quarterly_growth_min                           = 0.01-0.25*tase_mode       # The earnings can decrease by 1/4, but there is still a requirement that price_to_earnings_to_growth_ratio > 0. TODO: ASAFR: Add to multi-dimention
    if not research_mode: enterprise_value_to_revenue_limit = enterprise_value_to_revenue_limit

    symbols                 = []
    symbols_tase            = []
    symbols_snp500          = []
    symbols_snp500_download = []
    symbols_nasdaq100       = []
    symbols_nasdaq_100_csv  = []
    symbols_russel1000      = []
    symbols_russel1000_csv  = []
    stocks_list_tase        = []

    if not tase_mode and not research_mode:
        payload            = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies') # There are 2 tables on the Wikipedia page, get the first table
        first_table        = payload[0]
        second_table       = payload[1]
        df                 = first_table
        symbols_snp500     = df['Symbol'].values.tolist()
        symbols_nasdaq100  = ['ATVI', 'ADBE', 'AMD', 'ALXN', 'ALGN', 'GOOG', 'GOOGL', 'AMZN', 'AMGN', 'ADI', 'ANSS', 'AAPL', 'AMAT', 'ASML', 'ADSK', 'ADP', 'BIDU', 'BIIB', 'BMRN', 'BKNG', 'AVGO', 'CDNS', 'CDW', 'CERN', 'CHTR', 'CHKP', 'CTAS', 'CSCO', 'CTXS', 'CTSH', 'CMCSA', 'CPRT', 'COST', 'CSX', 'DXCM', 'DOCU', 'DLTR', 'EBAY', 'EA', 'EXC', 'EXPE', 'FB', 'FAST', 'FISV', 'FOX', 'FOXA', 'GILD', 'IDXX', 'ILMN', 'INCY', 'INTC', 'INTU', 'ISRG', 'JD', 'KLAC', 'LRCX', 'LBTYA', 'LBTYK', 'LULU', 'MAR', 'MXIM', 'MELI', 'MCHP', 'MU', 'MSFT', 'MRNA', 'MDLZ', 'MNST', 'NTES', 'NFLX', 'NVDA', 'NXPI', 'ORLY', 'PCAR', 'PAYX', 'PYPL', 'PEP', 'PDD', 'QCOM', 'REGN', 'ROST', 'SGEN', 'SIRI', 'SWKS', 'SPLK', 'SBUX', 'SNPS', 'TMUS', 'TTWO', 'TSLA', 'TXN', 'KHC', 'TCOM', 'ULTA', 'VRSN', 'VRSK', 'VRTX', 'WBA', 'WDC', 'WDAY', 'XEL', 'XLNX', 'ZM']
        symbols_russel1000 = ['TWOU', 'MMM', 'ABT', 'ABBV', 'ABMD', 'ACHC', 'ACN', 'ATVI', 'AYI', 'ADNT', 'ADBE', 'ADT', 'AAP', 'AMD', 'ACM', 'AES', 'AMG', 'AFL', 'AGCO', 'A', 'AGIO', 'AGNC', 'AL', 'APD', 'AKAM', 'ALK', 'ALB', 'AA', 'ARE', 'ALXN', 'ALGN', 'ALKS', 'Y', 'ALLE', 'AGN', 'ADS', 'LNT', 'ALSN', 'ALL', 'ALLY', 'ALNY', 'GOOGL', 'GOOG', 'MO', 'AMZN', 'AMCX', 'DOX', 'UHAL', 'AEE', 'AAL', 'ACC', 'AEP', 'AXP', 'AFG', 'AMH', 'AIG', 'ANAT', 'AMT', 'AWK', 'AMP', 'ABC', 'AME', 'AMGN', 'APH', 'ADI', 'NLY', 'ANSS', 'AR', 'ANTM', 'AON', 'APA', 'AIV', 'APY', 'APLE', 'AAPL', 'AMAT', 'ATR', 'APTV', 'WTR', 'ARMK', 'ACGL', 'ADM', 'ARNC', 'ARD', 'ANET', 'AWI', 'ARW', 'ASH', 'AZPN', 'ASB', 'AIZ', 'AGO', 'T', 'ATH', 'TEAM', 'ATO', 'ADSK', 'ADP', 'AN', 'AZO', 'AVB', 'AGR', 'AVY', 'AVT', 'EQH', 'AXTA', 'AXS', 'BKR', 'BLL', 'BAC', 'BOH', 'BK', 'OZK', 'BKU', 'BAX', 'BDX', 'WRB', 'BRK.B', 'BERY', 'BBY', 'BYND', 'BGCP', 'BIIB', 'BMRN', 'BIO', 'TECH', 'BKI', 'BLK', 'HRB', 'BLUE', 'BA', 'BOKF', 'BKNG', 'BAH', 'BWA', 'BSX', 'BDN', 'BFAM', 'BHF', 'BMY', 'BRX', 'AVGO', 'BR', 'BPYU', 'BRO', 'BFA', 'BFB', 'BRKR', 'BC', 'BG', 'BURL', 'BWXT', 'CHRW', 'CABO', 'CBT', 'COG', 'CACI', 'CDNS', 'CZR', 'CPT', 'CPB', 'CMD', 'COF', 'CAH', 'CSL', 'KMX', 'CCL', 'CRI', 'CASY', 'CTLT', 'CAT', 'CBOE', 'CBRE', 'CBS', 'CDK', 'CDW', 'CE', 'CELG', 'CNC', 'CDEV', 'CNP', 'CTL', 'CDAY', 'BXP', 'CF', 'CRL', 'CHTR', 'CHE', 'LNG', 'CHK', 'CVX', 'CIM', 'CMG', 'CHH', 'CB', 'CHD', 'CI', 'XEC', 'CINF', 'CNK', 'CTAS', 'CSCO', 'CIT', 'C', 'CFG', 'CTXS', 'CLH', 'CLX', 'CME', 'CMS', 'CNA', 'CNX', 'KO', 'CGNX', 'CTSH', 'COHR', 'CFX', 'CL', 'CLNY', 'CXP', 'COLM', 'CMCSA', 'CMA', 'CBSH', 'COMM', 'CAG', 'CXO', 'CNDT', 'COP', 'ED', 'STZ', 'CERN', 'CPA', 'CPRT', 'CLGX', 'COR', 'GLW', 'OFC', 'CSGP', 'COST', 'COTY', 'CR', 'CACC', 'CCI', 'CCK', 'CSX', 'CUBE', 'CFR', 'CMI', 'CW', 'CVS', 'CY', 'CONE', 'DHI', 'DHR', 'DRI', 'DVA', 'SITC', 'DE', 'DELL', 'DAL', 'XRAY', 'DVN', 'DXCM', 'FANG', 'DKS', 'DLR', 'DFS', 'DISCA', 'DISCK', 'DISH', 'DIS', 'DHC', 'DOCU', 'DLB', 'DG', 'DLTR', 'D', 'DPZ', 'CLR', 'COO', 'DEI', 'DOV', 'DD', 'DPS', 'DTE', 'DUK', 'DRE', 'DNB', 'DNKN', 'DXC', 'ETFC', 'EXP', 'EWBC', 'EMN', 'ETN', 'EV', 'EBAY', 'SATS', 'ECL', 'EIX', 'EW', 'EA', 'EMR', 'ESRT', 'EHC', 'EGN', 'ENR', 'ETR', 'EVHC', 'EOG', 'EPAM', 'EPR', 'EQT', 'EFX', 'EQIX', 'EQC', 'ELS', 'EQR', 'ERIE', 'ESS', 'EL', 'EEFT', 'EVBG', 'EVR', 'RE', 'EVRG', 'ES', 'UFS', 'DCI', 'EXPE', 'EXPD', 'STAY', 'EXR', 'XOG', 'XOM', 'FFIV', 'FB', 'FDS', 'FICO', 'FAST', 'FRT', 'FDX', 'FIS', 'FITB', 'FEYE', 'FAF', 'FCNCA', 'FDC', 'FHB', 'FHN', 'FRC', 'FSLR', 'FE', 'FISV', 'FLT', 'FLIR', 'FND', 'FLO', 'FLS', 'FLR', 'FMC', 'FNB', 'FNF', 'FL', 'F', 'FTNT', 'FTV', 'FBHS', 'FOXA', 'FOX', 'BEN', 'FCX', 'AJG', 'GLPI', 'GPS', 'EXAS', 'EXEL', 'EXC', 'GTES', 'GLIBA', 'GD', 'GE', 'GIS', 'GM', 'GWR', 'G', 'GNTX', 'GPC', 'GILD', 'GPN', 'GL', 'GDDY', 'GS', 'GT', 'GRA', 'GGG', 'EAF', 'GHC', 'GWW', 'LOPE', 'GPK', 'GRUB', 'GWRE', 'HAIN', 'HAL', 'HBI', 'THG', 'HOG', 'HIG', 'HAS', 'HE', 'HCA', 'HDS', 'HTA', 'PEAK', 'HEI.A', 'HEI', 'HP', 'JKHY', 'HLF', 'HSY', 'HES', 'GDI', 'GRMN', 'IT', 'HGV', 'HLT', 'HFC', 'HOLX', 'HD', 'HON', 'HRL', 'HST', 'HHC', 'HPQ', 'HUBB', 'HPP', 'HUM', 'HBAN', 'HII', 'HUN', 'H', 'IAC', 'ICUI', 'IEX', 'IDXX', 'INFO', 'ITW', 'ILMN', 'INCY', 'IR', 'INGR', 'PODD', 'IART', 'INTC', 'IBKR', 'ICE', 'IGT', 'IP', 'IPG', 'IBM', 'IFF', 'INTU', 'ISRG', 'IVZ', 'INVH', 'IONS', 'IPGP', 'IQV', 'HPE', 'HXL', 'HIW', 'HRC', 'JAZZ', 'JBHT', 'JBGS', 'JEF', 'JBLU', 'JNJ', 'JCI', 'JLL', 'JPM', 'JNPR', 'KSU', 'KAR', 'K', 'KEY', 'KEYS', 'KRC', 'KMB', 'KIM', 'KMI', 'KEX', 'KLAC', 'KNX', 'KSS', 'KOS', 'KR', 'LB', 'LHX', 'LH', 'LRCX', 'LAMR', 'LW', 'LSTR', 'LVS', 'LAZ', 'LEA', 'LM', 'LEG', 'LDOS', 'LEN', 'LEN.B', 'LII', 'LBRDA', 'LBRDK', 'FWONA', 'IRM', 'ITT', 'JBL', 'JEC', 'LLY', 'LECO', 'LNC', 'LGF.A', 'LGF.B', 'LFUS', 'LYV', 'LKQ', 'LMT', 'L', 'LOGM', 'LOW', 'LPLA', 'LULU', 'LYFT', 'LYB', 'MTB', 'MAC', 'MIC', 'M', 'MSG', 'MANH', 'MAN', 'MRO', 'MPC', 'MKL', 'MKTX', 'MAR', 'MMC', 'MLM', 'MRVL', 'MAS', 'MASI', 'MA', 'MTCH', 'MAT', 'MXIM', 'MKC', 'MCD', 'MCK', 'MDU', 'MPW', 'MD', 'MDT', 'MRK', 'FWONK', 'LPT', 'LSXMA', 'LSXMK', 'LSI', 'CPRI', 'MIK', 'MCHP', 'MU', 'MSFT', 'MAA', 'MIDD', 'MKSI', 'MHK', 'MOH', 'TAP', 'MDLZ', 'MPWR', 'MNST', 'MCO', 'MS', 'MORN', 'MOS', 'MSI', 'MSM', 'MSCI', 'MUR', 'MYL', 'NBR', 'NDAQ', 'NFG', 'NATI', 'NOV', 'NNN', 'NAVI', 'NCR', 'NKTR', 'NTAP', 'NFLX', 'NBIX', 'NRZ', 'NYCB', 'NWL', 'NEU', 'NEM', 'NWSA', 'NWS', 'MCY', 'MET', 'MTD', 'MFA', 'MGM', 'JWN', 'NSC', 'NTRS', 'NOC', 'NLOK', 'NCLH', 'NRG', 'NUS', 'NUAN', 'NUE', 'NTNX', 'NVT', 'NVDA', 'NVR', 'NXPI', 'ORLY', 'OXY', 'OGE', 'OKTA', 'ODFL', 'ORI', 'OLN', 'OHI', 'OMC', 'ON', 'OMF', 'OKE', 'ORCL', 'OSK', 'OUT', 'OC', 'OI', 'PCAR', 'PKG', 'PACW', 'PANW', 'PGRE', 'PK', 'PH', 'PE', 'PTEN', 'PAYX', 'PAYC', 'PYPL', 'NEE', 'NLSN', 'NKE', 'NI', 'NBL', 'NDSN', 'PEP', 'PKI', 'PRGO', 'PFE', 'PCG', 'PM', 'PSX', 'PPC', 'PNFP', 'PF', 'PNW', 'PXD', 'ESI', 'PNC', 'PII', 'POOL', 'BPOP', 'POST', 'PPG', 'PPL', 'PRAH', 'PINC', 'TROW', 'PFG', 'PG', 'PGR', 'PLD', 'PFPT', 'PB', 'PRU', 'PTC', 'PSA', 'PEG', 'PHM', 'PSTG', 'PVH', 'QGEN', 'QRVO', 'QCOM', 'PWR', 'PBF', 'PEGA', 'PAG', 'PNR', 'PEN', 'PBCT', 'RLGY', 'RP', 'O', 'RBC', 'REG', 'REGN', 'RF', 'RGA', 'RS', 'RNR', 'RSG', 'RMD', 'RPAI', 'RNG', 'RHI', 'ROK', 'ROL', 'ROP', 'ROST', 'RCL', 'RGLD', 'RES', 'RPM', 'RSPP', 'R', 'SPGI', 'SABR', 'SAGE', 'CRM', 'SC', 'SRPT', 'SBAC', 'HSIC', 'SLB', 'SNDR', 'SCHW', 'SMG', 'SEB', 'SEE', 'DGX', 'QRTEA', 'RL', 'RRC', 'RJF', 'RYN', 'RTN', 'NOW', 'SVC', 'SHW', 'SBNY', 'SLGN', 'SPG', 'SIRI', 'SIX', 'SKX', 'SWKS', 'SLG', 'SLM', 'SM', 'AOS', 'SJM', 'SNA', 'SON', 'SO', 'SCCO', 'LUV', 'SPB', 'SPR', 'SRC', 'SPLK', 'S', 'SFM', 'SQ', 'SSNC', 'SWK', 'SBUX', 'STWD', 'STT', 'STLD', 'SRCL', 'STE', 'STL', 'STOR', 'SYK', 'SUI', 'STI', 'SIVB', 'SWCH', 'SGEN', 'SEIC', 'SRE', 'ST', 'SCI', 'SERV', 'TPR', 'TRGP', 'TGT', 'TCO', 'TCF', 'AMTD', 'TDY', 'TFX', 'TDS', 'TPX', 'TDC', 'TER', 'TEX', 'TSRO', 'TSLA', 'TCBI', 'TXN', 'TXT', 'TFSL', 'CC', 'KHC', 'WEN', 'TMO', 'THO', 'TIF', 'TKR', 'TJX', 'TOL', 'TTC', 'TSCO', 'TDG', 'RIG', 'TRU', 'TRV', 'THS', 'TPCO', 'TRMB', 'TRN', 'TRIP', 'SYF', 'SNPS', 'SNV', 'SYY', 'DATA', 'TTWO', 'TMUS', 'TFC', 'UBER', 'UGI', 'ULTA', 'ULTI', 'UMPQ', 'UAA', 'UA', 'UNP', 'UAL', 'UPS', 'URI', 'USM', 'X', 'UTX', 'UTHR', 'UNH', 'UNIT', 'UNVR', 'OLED', 'UHS', 'UNM', 'URBN', 'USB', 'USFD', 'VFC', 'MTN', 'VLO', 'VMI', 'VVV', 'VAR', 'VVC', 'VEEV', 'VTR', 'VER', 'VRSN', 'VRSK', 'VZ', 'VSM', 'VRTX', 'VIAC', 'TWLO', 'TWTR', 'TWO', 'TYL', 'TSN', 'USG', 'UI', 'UDR', 'VMC', 'WPC', 'WBC', 'WAB', 'WBA', 'WMT', 'WM', 'WAT', 'WSO', 'W', 'WFTLF', 'WBS', 'WEC', 'WRI', 'WBT', 'WCG', 'WFC', 'WELL', 'WCC', 'WST', 'WAL', 'WDC', 'WU', 'WLK', 'WRK', 'WEX', 'WY', 'WHR', 'WTM', 'WLL', 'JW.A', 'WMB', 'WSM', 'WLTW', 'WTFC', 'WDAY', 'WP', 'WPX', 'WYND', 'WH', 'VIAB', 'VICI', 'VIRT', 'V', 'VC', 'VST', 'VMW', 'VNO', 'VOYA', 'ZAYO', 'ZBRA', 'ZEN', 'ZG', 'Z', 'ZBH', 'ZION', 'ZTS', 'ZNGA', 'WYNN', 'XEL', 'XRX', 'XLNX', 'XPO', 'XYL', 'YUMC', 'YUM']

        # nasdaq100: https://www.barchart.com/stocks/quotes/$IUXX/components?viewName=main or https://www.nasdaq.com/market-activity/quotes/nasdaq-ndx-index
        symbols_nasdaq_100_csv = [] # nasdaq100-components.csv
        nasdq100_filenames_list = ['Indices/nasdaq100-components.csv'] # https://www.barchart.com/stocks/indices/russell/russell1000
        for filename in nasdq100_filenames_list:
            with open(filename, mode='r', newline='') as engine:
                reader = csv.reader(engine, delimiter=',')
                row_index = 0
                for row in reader:
                    if row_index == 0:
                        row_index += 1
                        continue
                    else:
                        symbols_nasdaq_100_csv.append(row[0])
                        row_index += 1

        # s&p500: https://www.barchart.com/stocks/quotes/$SPX/components
        symbols_snp500_download_csv = [] # snp500-components.csv
        symbols_snp500_download_filenames_list = ['Indices/snp500-components.csv']
        for filename in symbols_snp500_download_filenames_list:
            with open(filename, mode='r', newline='') as engine:
                reader = csv.reader(engine, delimiter=',')
                row_index = 0
                for row in reader:
                    if row_index == 0:
                        row_index += 1
                        continue
                    else:
                        symbols_snp500_download_csv.append(row[0])
                        row_index += 1

        symbols_russel1000_wiki = [] # https://en.wikipedia.org/wiki/Russell_1000_Index
        russel1000_filenames_wiki_list = ['Indices/Russel_1000_index_wiki.csv'] # https://www.barchart.com/stocks/indices/russell/russell1000
        for filename in russel1000_filenames_wiki_list:
            with open(filename, mode='r', newline='', encoding='cp1252') as engine:
                reader = csv.reader(engine, delimiter=',')
                for row in reader:
                    symbols_russel1000_wiki.append(row[1])


        symbols_russel1000_csv = []  # TODO: ASAFR: Make a general CSV reading function (with title row and withour, and which component in row to take, etc...
        russel1000_filenames_list = ['Indices/russell-1000-index.csv'] # https://www.barchart.com/stocks/indices/russell/russell1000
        for filename in russel1000_filenames_list:
            with open(filename, mode='r', newline='') as engine:
                reader = csv.reader(engine, delimiter=',')
                row_index = 0
                for row in reader:
                    if row_index == 0:
                        row_index += 1
                        continue
                    else:
                        symbols_russel1000_csv.append(row[0])
                        row_index += 1

        symbols_tase     = []  # symbols_tase       = ['ALD.TA', 'ABIL.TA', 'ACCL.TA', 'ADGR.TA', 'ADKA.TA', 'ARDM.TA', 'AFHL.TA', 'AFPR.TA', 'AFID.TA', 'AFRE.TA', 'AICS.TA', 'ARPT.TA', 'ALBA.TA', 'ALMD.TA', 'ALLT.TA', 'AMDA.L.TA', 'ALMA.TA', 'ALGS.TA', 'ALHE.TA', 'ALRPR.TA', 'ASPF.TA', 'AMAN.TA', 'AMRK.TA', 'AMOT.TA', 'ANLT.TA', 'ANGL.TA', 'APIO.M.TA', 'APLP.TA', 'ARD.TA', 'ARAD.TA', 'ARAN.TA', 'ARNA.TA', 'ARKO.TA', 'ARYT.TA', 'ASHO.TA', 'ASHG.TA', 'ASPR.TA', 'ASGR.TA', 'ATRY.TA', 'AUDC.TA', 'AUGN.TA', 'AURA.TA', 'SHVA.TA', 'AVER.TA', 'AVGL.TA', 'AVIA.TA', 'AVIV.TA', 'AVLN.TA', 'AVRT.TA', 'AYAL.TA', 'AZRM.TA', 'AZRG.TA', 'BCOM.TA', 'BYAR.TA', 'BBYL.TA', 'BRAN.TA', 'BVC.TA', 'BYSD.TA', 'ORL.TA', 'BSEN.TA', 'BEZQ.TA', 'BGI-M.TA', 'BIG.TA', 'BIOV.TA', 'BOLT.TA', 'BLRX.TA', 'PHGE.TA', 'BIRM.TA', 'BLSR.TA', 'BOTI.TA', 'BONS.TA', 'BCNV.TA', 'BWAY.TA', 'BRAM.TA', 'BRND.TA', 'BNRG.TA', 'BRIL.TA', 'BRMG.TA', 'CISY.TA', 'CAMT.TA', 'CANF.TA', 'CSURE.TA', 'CNMD.TA', 'CNZN.TA', 'CPTP.TA', 'CRSO.TA', 'CRMT.TA', 'CAST.TA', 'CEL.TA', 'CHAM.TA', 'CHR.TA', 'CMCT.TA', 'CMCTP.TA', 'CTPL5.TA', 'CTPL1.TA', 'CLBV.TA', 'CBI.TA', 'CLIS.TA', 'CFX.TA', 'CDEV.TA', 'CGEN.TA', 'CMDR.TA', 'DNA.TA', 'DANH.TA', 'DANE.TA', 'DCMA.TA', 'DLRL.TA', 'DLEA.TA', 'DEDR.L.TA', 'DLEKG.TA', 'DELT.TA', 'DIMRI.TA', 'DIFI.TA', 'DSCT.TA', 'DISI.TA', 'DRAL.TA', 'DORL.TA', 'DRSL.TA', 'DUNI.TA', 'EMCO.TA', 'EDRL.TA', 'ELAL.TA', 'EMITF.TA', 'EMTC.TA', 'ESLT.TA', 'ELCO.TA', 'ELDAV.TA', 'ELTR.TA', 'ECP.TA', 'ELCRE.TA', 'ELWS.TA', 'ELLO.TA', 'ELMR.TA', 'ELRN.TA', 'ELSPC.TA', 'EMDV.TA', 'ENDY.TA', 'ENOG.TA', 'ENRG.TA', 'ENLT.TA', 'ENLV.TA', 'EQTL.TA', 'EFNC.TA', 'EVGN.TA', 'EXPO.TA', 'FNTS.TA', 'FTAL.TA', 'FIBI.TA', 'FIBIH.TA', 'FGAS.TA', 'FBRT.TA', 'FRSX.TA', 'FORTY.TA', 'FOX.TA', 'FRSM.TA', 'FRDN.TA', 'GOSS.TA', 'GFC-L.TA', 'GPGB.TA', 'GADS.TA', 'GSFI.TA', 'GAON.TA', 'GAGR.TA', 'GZT.TA', 'GNRS.TA', 'GIBUI.TA', 'GILT.TA', 'GNGR.TA', 'GIVO.L.TA', 'GIX.TA', 'GLTC.TA', 'GLEX.L.TA', 'GKL.TA', 'GLRS.TA', 'GODM-M.TA', 'GLPL.TA', 'GOLD.TA', 'GOHO.TA', 'GOLF.TA', 'HDST.TA', 'HAP.TA', 'HGG.TA', 'HAIN.TA', 'HMAM.TA', 'MSBI.TA', 'HAMAT.TA', 'HAML.TA', 'HNMR.TA', 'HARL.TA', 'HLAN.TA', 'HRON.TA', 'HOD.TA', 'HLMS.TA', 'IBI.TA', 'IBITEC.F.TA', 'ICB.TA', 'ICCM.TA', 'ICL.TA', 'IDIN.TA', 'IES.TA', 'IFF.TA', 'ILDR.TA', 'ILX.TA', 'IMCO.TA', 'INBR.TA', 'INFR.TA', 'INRM.TA', 'INTL.TA', 'ININ.TA', 'INCR.TA', 'INTR.TA', 'IGLD-M.TA', 'ISCD.TA', 'ISCN.TA', 'ILCO.TA', 'ISOP.L.TA', 'ISHI.TA', 'ISRA.L.TA', 'ISRS.TA', 'ISRO.TA', 'ISTA.TA', 'ITMR.TA', 'JBNK.TA', 'KDST.TA', 'KAFR.TA', 'KMDA.TA', 'KRNV-L.TA', 'KARE.TA', 'KRDI.TA', 'KEN.TA', 'KRUR.TA', 'KTOV.TA', 'KLIL.TA', 'KMNK-M.TA', 'KNFM.TA', 'LHIS.TA', 'LAHAV.TA', 'ILDC.TA', 'LPHL.L.TA', 'LAPD.TA', 'LDER.TA', 'LSCO.TA', 'LUMI.TA', 'LEOF.TA', 'LEVI.TA', 'LVPR.TA', 'LBTL.TA', 'LCTX.TA', 'LPSN.TA', 'LODZ.TA', 'LUDN.TA', 'LUZN.TA', 'LZNR.TA', 'MGIC.TA', 'MLTM.TA', 'MMAN.TA', 'MSLA.TA', 'MTMY.TA', 'MTRX.TA', 'MAXO.TA', 'MTRN.TA', 'MEAT.TA', 'MDGS.TA', 'MDPR.TA', 'MDTR.TA', 'MDVI.TA', 'MGOR.TA', 'MEDN.TA', 'MTDS.TA', 'MLSR.TA', 'MNIN.TA', 'MNRT.TA', 'MMHD.TA', 'CMER.TA', 'MRHL.TA', 'MSKE.TA', 'MGRT.TA', 'MCRNT.TA', 'MGDL.TA', 'MIFT.TA', 'MNGN.TA', 'MNRV.TA', 'MLD.TA', 'MSHR.TA', 'MVNE.TA', 'MISH.TA', 'MZTF.TA', 'MBMX-M.TA', 'MDIN.L.TA', 'MRIN.TA', 'MYSZ.TA', 'MYDS.TA', 'NFTA.TA', 'NVPT.L.TA', 'NAWI.TA', 'NTGR.TA', 'NTO.TA', 'NTML.TA', 'NERZ-M.TA', 'NXTG.TA', 'NXTM.TA', 'NXGN-M.TA', 'NICE.TA', 'NISA.TA', 'NSTR.TA', 'NVMI.TA', 'NVLG.TA', 'ORTC.TA', 'ONE.TA', 'OPAL.TA', 'OPCE.TA', 'OPK.TA', 'OBAS.TA', 'ORAD.TA', 'ORMP.TA', 'ORBI.TA', 'ORIN.TA', 'ORA.TA', 'ORON.TA', 'OVRS.TA', 'PCBT.TA', 'PLTF.TA', 'PLRM.TA', 'PNAX.TA', 'PTNR.TA', 'PAYT.TA', 'PZOL.TA', 'PEN.TA', 'PFLT.TA', 'PERI.TA', 'PRGO.TA', 'PTCH.TA', 'PTX.TA', 'PMCN.TA', 'PHOE.TA', 'PLSN.TA', 'PLCR.TA', 'PPIL-M.TA', 'PLAZ-L.TA', 'PSTI.TA', 'POLI.TA', 'PIU.TA', 'POLY.TA', 'PWFL.TA', 'PRSK.TA', 'PRTC.TA', 'PTBL.TA', 'PLX.TA', 'QLTU.TA', 'QNCO.TA', 'RLCO.TA', 'RMN.TA', 'RMLI.TA', 'RANI.TA', 'RPAC.TA', 'RATI.L.TA', 'RTPT.L.TA', 'RAVD.TA', 'RVL.TA', 'RIT1.TA', 'AZRT.TA', 'REKA.TA', 'RIMO.TA', 'ROBO.TA', 'RTEN.L.TA', 'ROTS.TA', 'RSEL.TA', 'SRAC.TA', 'SFET.TA', 'SANO1.TA', 'SPNS.TA', 'SRFT.TA', 'STCM.TA', 'SAVR.TA', 'SHNP.TA', 'SCOP.TA', 'SEMG.TA', 'SLARL.TA', 'SHGR.TA', 'SALG.TA', 'SHAN.TA', 'SPEN.TA', 'SEFA.TA', 'SMNIN.TA', 'SKBN.TA', 'SHOM.TA', 'SAE.TA', 'SKLN.TA', 'SLGN.TA', 'SMTO.TA', 'SCC.TA', 'SPRG.TA', 'SPNTC.TA', 'STG.TA', 'STRS.TA', 'SMT.TA', 'SNFL.TA', 'SNCM.TA', 'SPGE.TA', 'SNEL.TA', 'TDGN-L.TA', 'TDRN.TA', 'TALD.TA', 'TMRP.TA', 'TASE.TA', 'TATT.TA', 'TAYA.TA', 'TNPV.TA', 'TEDE.TA', 'TFRLF.TA', 'TLRD.TA', 'TLSY.TA', 'TUZA.TA', 'TEVA.TA', 'TIGBUR.TA', 'TKUN.TA', 'TTAM.TA', 'TGTR.TA', 'TOPS.TA', 'TSEM.TA', 'TREN.TA', 'UNCR.TA', 'UNCT.L.TA', 'UNIT.TA', 'UNVO.TA', 'UTRN.TA', 'VCTR.TA', 'VILR.TA', 'VISN.TA', 'VTLC-M.TA', 'VTNA.TA', 'VNTZ-M.TA', 'WSMK.TA', 'WTS.TA', 'WILC.TA', 'WLFD.TA', 'XENA.TA', 'XTLB.TA', 'YAAC.TA', 'YBOX.TA', 'YHNF.TA', 'ZNKL.TA', 'ZMH.TA', 'ZUR.TA']
        stocks_list_tase = []  # https://info.tase.co.il/eng/MarketData/Stocks/MarketData/Pages/MarketData.aspx

    if tase_mode and not research_mode:
        tase_filenames_list = ['Indices/Data_TASE.csv']

        for filename in tase_filenames_list:
            with open(filename, mode='r', newline='') as engine:
                reader = csv.reader(engine, delimiter=',')
                row_index = 0
                for row in reader:
                    if row_index <= 3:
                        row_index += 1
                        continue
                    else:
                        symbols_tase.append(row[1].replace('.','-')+'.TA')
                        row_index += 1
        if use_investpy:
            stocks_list_tase = investpy.get_stocks_list(country='israel')
            for index, stock in enumerate(stocks_list_tase): stocks_list_tase[index] += '.TA'

    # All nasdaq and others: ftp://ftp.nasdaqtrader.com/symboldirectory/
    # ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt
    # ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt
    if not research_mode:
        symbols_united_states     = []
        stocks_list_united_states = []
        if read_united_states_input_symbols:
            nasdaq_filenames_list = ['Indices/nasdaqlisted.csv', 'Indices/otherlisted.csv', 'Indices/nasdaqtraded.csv']

            for filename in nasdaq_filenames_list:
                with open(filename, mode='r', newline='') as engine:
                    reader = csv.reader(engine, delimiter='|')
                    row_index = 0
                    for row in reader:
                        if row_index == 0 or 'ETF' in row[1]:
                            row_index += 1
                            continue
                        else:
                            symbols_united_states.append(row[0])
                            row_index += 1

            stocks_list_united_states = investpy.get_stocks_list(country='united states')

        symbols = symbols_snp500 + symbols_snp500_download + symbols_nasdaq100 + symbols_nasdaq_100_csv + symbols_russel1000 + symbols_russel1000_csv + symbols_united_states + stocks_list_united_states

    if not research_mode and tase_mode:
        symbols = symbols_tase + stocks_list_tase

    if not research_mode: symbols = list(set(symbols))


    # Temporary to test and debug: DEBUG MODE
    # =======================================
    # symbols     = ['LUMI.TA']
    # num_threads = 1
     
    if not research_mode: print('\n{} SSS Symbols to Scan using {} threads: {}\n'.format(len(symbols), num_threads, symbols))


    csv_db_data    = []
    rows           = []
    rows_no_div    = []
    rows_only_div  = []
    csv_db_data0   = []
    rows0          = []
    rows0_no_div   = []
    rows0_only_div = []
    csv_db_data1   = []
    rows1          = []
    rows1_no_div   = []
    rows1_only_div = []
    csv_db_data2   = []
    rows2          = []
    rows2_no_div   = []
    rows2_only_div = []
    csv_db_data3   = []
    rows3          = []
    rows3_no_div   = []
    rows3_only_div = []
    csv_db_data4   = []
    rows4          = []
    rows4_no_div   = []
    rows4_only_div = []
    csv_db_data5   = []
    rows5          = []
    rows5_no_div   = []
    rows5_only_div = []
    csv_db_data6   = []
    rows6          = []
    rows6_no_div   = []
    rows6_only_div = []
    csv_db_data7   = []
    rows7          = []
    rows7_no_div   = []
    rows7_only_div = []
    csv_db_data8   = []
    rows8          = []
    rows8_no_div   = []
    rows8_only_div = []
    csv_db_data9   = []
    rows9          = []
    rows9_no_div   = []
    rows9_only_div = []
    csv_db_data10   = []
    rows10          = []
    rows10_no_div   = []
    rows10_only_div = []
    csv_db_data11   = []
    rows11          = []
    rows11_no_div   = []
    rows11_only_div = []
    csv_db_data12   = []
    rows12          = []
    rows12_no_div   = []
    rows12_only_div = []
    csv_db_data13   = []
    rows13          = []
    rows13_no_div   = []
    rows13_only_div = []
    csv_db_data14   = []
    rows14          = []
    rows14_no_div   = []
    rows14_only_div = []
    csv_db_data15   = []
    rows15          = []
    rows15_no_div   = []
    rows15_only_div = []
    csv_db_data16   = []
    rows16          = []
    rows16_no_div   = []
    rows16_only_div = []
    csv_db_data17   = []
    rows17          = []
    rows17_no_div   = []
    rows17_only_div = []
    csv_db_data18   = []
    rows18          = []
    rows18_no_div   = []
    rows18_only_div = []
    csv_db_data19   = []
    rows19          = []
    rows19_no_div   = []
    rows19_only_div = []

    if build_csv_db == 0: # if DB is already present, read from it and prepare input to threads
        csv_db_filename = csv_db_path+'/db.csv'
        with open(csv_db_filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                if row_index <= 1: # first row is just a title of evr and pm, then a title of columns
                    row_index += 1
                    continue
                else:
                    symbols.append(row[0])
                    if   (row_index-2) % num_threads ==  0: csv_db_data0.append(row)
                    elif (row_index-2) % num_threads ==  1: csv_db_data1.append(row)
                    elif (row_index-2) % num_threads ==  2: csv_db_data2.append(row)
                    elif (row_index-2) % num_threads ==  3: csv_db_data3.append(row)
                    elif (row_index-2) % num_threads ==  4: csv_db_data4.append(row)
                    elif (row_index-2) % num_threads ==  5: csv_db_data5.append(row)
                    elif (row_index-2) % num_threads ==  6: csv_db_data6.append(row)
                    elif (row_index-2) % num_threads ==  7: csv_db_data7.append(row)
                    elif (row_index-2) % num_threads ==  8: csv_db_data8.append(row)
                    elif (row_index-2) % num_threads ==  9: csv_db_data9.append(row)
                    elif (row_index-2) % num_threads == 10: csv_db_data10.append(row)
                    elif (row_index-2) % num_threads == 11: csv_db_data11.append(row)
                    elif (row_index-2) % num_threads == 12: csv_db_data12.append(row)
                    elif (row_index-2) % num_threads == 13: csv_db_data13.append(row)
                    elif (row_index-2) % num_threads == 14: csv_db_data14.append(row)
                    elif (row_index-2) % num_threads == 15: csv_db_data15.append(row)
                    elif (row_index-2) % num_threads == 16: csv_db_data16.append(row)
                    elif (row_index-2) % num_threads == 17: csv_db_data17.append(row)
                    elif (row_index-2) % num_threads == 18: csv_db_data18.append(row)
                    elif (row_index-2) % num_threads == 19: csv_db_data19.append(row)
                    row_index += 1

    if num_threads >=  1: symbols0  = symbols[ 0:][::num_threads] #  0,    num_threads,    2*num_threads,    3*num_threads, ...
    if num_threads >=  2: symbols1  = symbols[ 1:][::num_threads] #  1,  1+num_threads,  2+2*num_threads,  2+3*num_threads, ...
    if num_threads >=  3: symbols2  = symbols[ 2:][::num_threads] #  2,  2+num_threads,  3+2*num_threads,  3+3*num_threads, ...
    if num_threads >=  4: symbols3  = symbols[ 3:][::num_threads] #  3,  3+num_threads,  4+2*num_threads,  4+3*num_threads, ...
    if num_threads >=  5: symbols4  = symbols[ 4:][::num_threads] #  4,  4+num_threads,  5+2*num_threads,  5+3*num_threads, ...
    if num_threads >=  6: symbols5  = symbols[ 5:][::num_threads] #  5,  5+num_threads,  6+2*num_threads,  6+3*num_threads, ...
    if num_threads >=  7: symbols6  = symbols[ 6:][::num_threads] #  6,  6+num_threads,  7+2*num_threads,  7+3*num_threads, ...
    if num_threads >=  8: symbols7  = symbols[ 7:][::num_threads] #  7,  7+num_threads,  8+2*num_threads,  8+3*num_threads, ...
    if num_threads >=  9: symbols8  = symbols[ 8:][::num_threads] #  8,  8+num_threads,  9+2*num_threads,  9+3*num_threads, ...
    if num_threads >= 10: symbols9  = symbols[ 9:][::num_threads] #  9,  9+num_threads, 10+2*num_threads, 10+3*num_threads, ...
    if num_threads >= 11: symbols10 = symbols[10:][::num_threads] # 10, 10+num_threads, 11+2*num_threads, 11+3*num_threads, ...
    if num_threads >= 12: symbols11 = symbols[11:][::num_threads] # 11, 11+num_threads, 12+2*num_threads, 12+3*num_threads, ...
    if num_threads >= 13: symbols12 = symbols[12:][::num_threads] # 12, 12+num_threads, 13+2*num_threads, 13+3*num_threads, ...
    if num_threads >= 14: symbols13 = symbols[13:][::num_threads] # 13, 13+num_threads, 14+2*num_threads, 14+3*num_threads, ...
    if num_threads >= 15: symbols14 = symbols[14:][::num_threads] # 14, 14+num_threads, 15+2*num_threads, 15+3*num_threads, ...
    if num_threads >= 16: symbols15 = symbols[15:][::num_threads] # 15, 15+num_threads, 16+2*num_threads, 16+3*num_threads, ...
    if num_threads >= 17: symbols16 = symbols[16:][::num_threads] # 16, 16+num_threads, 17+2*num_threads, 17+3*num_threads, ...
    if num_threads >= 18: symbols17 = symbols[17:][::num_threads] # 17, 17+num_threads, 18+2*num_threads, 18+3*num_threads, ...
    if num_threads >= 19: symbols18 = symbols[18:][::num_threads] # 18, 18+num_threads, 19+2*num_threads, 19+3*num_threads, ...
    if num_threads >= 20: symbols19 = symbols[19:][::num_threads] # 19, 19+num_threads, 20+2*num_threads, 20+3*num_threads, ...

    if num_threads >=  1:
        check_interval(0, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread0  = Thread(target=process_symbols, args=(symbols0,  csv_db_data0,  rows0,  rows0_no_div,  rows0_only_div,   0,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min,  enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode)) # process_symbols(symbols=symbols0, rows=rows0, rows_no_div=rows0_no_div, rows_only_div=rows0_only_div)
        thread0.start()                               # symbols,   csv_db_data,   rows,   rows_no_div,   rows_only_div,    thread_id, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min,  enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included
    if num_threads >=  2:
        check_interval(1, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread1  = Thread(target=process_symbols, args=(symbols1,  csv_db_data1,  rows1,  rows1_no_div,  rows1_only_div,   1,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode)) # process_symbols(symbols=symbols1, rows=rows1, rows_no_div=rows1_no_div, rows_only_div=rows1_only_div)
        thread1.start()
    if num_threads >=  3:
        check_interval(2, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread2  = Thread(target=process_symbols, args=(symbols2,  csv_db_data2,  rows2,  rows2_no_div,  rows2_only_div,   2,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread2.start()
    if num_threads >=  4:
        check_interval(3, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread3  = Thread(target=process_symbols, args=(symbols3,  csv_db_data3,  rows3,  rows3_no_div,  rows3_only_div,   3,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread3.start()
    if num_threads >=  5:
        check_interval(4, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread4  = Thread(target=process_symbols, args=(symbols4,  csv_db_data4,  rows4,  rows4_no_div,  rows4_only_div,   4,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread4.start()
    if num_threads >=  6:
        check_interval(5, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread5  = Thread(target=process_symbols, args=(symbols5,  csv_db_data5,  rows5,  rows5_no_div,  rows5_only_div,   5,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread5.start()
    if num_threads >=  7:
        check_interval(6, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread6  = Thread(target=process_symbols, args=(symbols6,  csv_db_data6,  rows6,  rows6_no_div,  rows6_only_div,   6,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread6.start()
    if num_threads >=  8:
        check_interval(7, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread7  = Thread(target=process_symbols, args=(symbols7,  csv_db_data7,  rows7,  rows7_no_div,  rows7_only_div,   7,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread7.start()
    if num_threads >=  9:
        check_interval(8, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread8  = Thread(target=process_symbols, args=(symbols8,  csv_db_data8,  rows8,  rows8_no_div,  rows8_only_div,   8,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread8.start()
    if num_threads >= 10:
        check_interval(9, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread9  = Thread(target=process_symbols, args=(symbols9,  csv_db_data9,  rows9,  rows9_no_div,  rows9_only_div,   9,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread9.start()
    if num_threads >= 11:
        check_interval(10, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread10 = Thread(target=process_symbols, args=(symbols10, csv_db_data10, rows10, rows10_no_div, rows10_only_div, 10,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread10.start()
    if num_threads >= 12:
        check_interval(11, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread11 = Thread(target=process_symbols, args=(symbols11, csv_db_data11, rows11, rows11_no_div, rows11_only_div, 11,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread11.start()
    if num_threads >= 13:
        check_interval(12, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread12 = Thread(target=process_symbols, args=(symbols12, csv_db_data12, rows12, rows12_no_div, rows12_only_div, 12,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread12.start()
    if num_threads >= 14:
        check_interval(13, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread13 = Thread(target=process_symbols, args=(symbols13, csv_db_data13, rows13, rows13_no_div, rows13_only_div, 13,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread13.start()
    if num_threads >= 15:
        check_interval(14, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread14 = Thread(target=process_symbols, args=(symbols14, csv_db_data14, rows14, rows14_no_div, rows14_only_div, 14,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread14.start()
    if num_threads >= 16:
        check_interval(15, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread15 = Thread(target=process_symbols, args=(symbols15, csv_db_data15, rows15, rows15_no_div, rows15_only_div, 15,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread15.start()
    if num_threads >= 17:
        check_interval(16, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread16 = Thread(target=process_symbols, args=(symbols16, csv_db_data16, rows16, rows16_no_div, rows16_only_div, 16,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread16.start()
    if num_threads >= 18:
        check_interval(17, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread17 = Thread(target=process_symbols, args=(symbols17, csv_db_data17, rows17, rows17_no_div, rows17_only_div, 17,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread17.start()
    if num_threads >= 19:
        check_interval(18, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread18 = Thread(target=process_symbols, args=(symbols18, csv_db_data18, rows18, rows18_no_div, rows18_only_div, 18,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread18.start()
    if num_threads >= 20:
        check_interval(19, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread19 = Thread(target=process_symbols, args=(symbols19, csv_db_data19, rows19, rows19_no_div, rows19_only_div, 19,         build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, min_enterprise_value_millions_usd, earnings_quarterly_growth_min, enterprise_value_to_revenue_limit,  favor_sectors, favor_sectors_by, market_cap_included, research_mode))
        thread19.start()

    if num_threads >=  1: thread0.join()
    if num_threads >=  2: thread1.join()
    if num_threads >=  3: thread2.join()
    if num_threads >=  4: thread3.join()
    if num_threads >=  5: thread4.join()
    if num_threads >=  6: thread5.join()
    if num_threads >=  7: thread6.join()
    if num_threads >=  8: thread7.join()
    if num_threads >=  9: thread8.join()
    if num_threads >= 10: thread9.join()
    if num_threads >= 11: thread10.join()
    if num_threads >= 12: thread11.join()
    if num_threads >= 13: thread12.join()
    if num_threads >= 14: thread13.join()
    if num_threads >= 15: thread14.join()
    if num_threads >= 16: thread15.join()
    if num_threads >= 17: thread16.join()
    if num_threads >= 18: thread17.join()
    if num_threads >= 19: thread18.join()
    if num_threads >= 20: thread19.join()

    csv_db_data.extend(  csv_db_data0   + csv_db_data1   + csv_db_data2   + csv_db_data3   + csv_db_data4   + csv_db_data5   + csv_db_data6   + csv_db_data7   + csv_db_data8   + csv_db_data9   + csv_db_data10   + csv_db_data11   + csv_db_data12   + csv_db_data13   + csv_db_data14   + csv_db_data15   + csv_db_data16   + csv_db_data17   + csv_db_data18   + csv_db_data19  )
    rows.extend(         rows0          + rows1          + rows2          + rows3          + rows4          + rows5          + rows6          + rows7          + rows8          + rows9          + rows10          + rows11          + rows12          + rows13          + rows14          + rows15          + rows16          + rows17          + rows18          + rows19         )
    rows_no_div.extend(  rows0_no_div   + rows1_no_div   + rows2_no_div   + rows3_no_div   + rows4_no_div   + rows5_no_div   + rows6_no_div   + rows7_no_div   + rows8_no_div   + rows9_no_div   + rows10_no_div   + rows11_no_div   + rows12_no_div   + rows13_no_div   + rows14_no_div   + rows15_no_div   + rows16_no_div   + rows17_no_div   + rows18_no_div   + rows19_no_div  )
    rows_only_div.extend(rows0_only_div + rows1_only_div + rows2_only_div + rows3_only_div + rows4_only_div + rows5_only_div + rows6_only_div + rows7_only_div + rows8_only_div + rows9_only_div + rows10_only_div + rows11_only_div + rows12_only_div + rows13_only_div + rows14_only_div + rows15_only_div + rows16_only_div + rows17_only_div + rows18_only_div + rows19_only_div)

    # Now, Sort the rows using the sss_value and ssse_value formulas: [1:] skips the 1st title row
    sorted_list_db               = sorted(csv_db_data,   key=lambda row:          row[0],           reverse=False)  # Sort by ticker symbol
    sorted_list_sss              = sorted(rows,          key=lambda row:          row[3],           reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
    sorted_list_ssss             = sorted(rows,          key=lambda row:          row[4],           reverse=False)  # Sort by ssss_value    -> The lower  - the more attractive
    sorted_list_sssss            = sorted(rows,          key=lambda row:          row[5],           reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
    sorted_list_ssse             = sorted(rows,          key=lambda row:          row[6],           reverse=True )  # Sort by ssse_value    -> The higher - the more attractive
    sorted_list_sssse            = sorted(rows,          key=lambda row:          row[7],           reverse=True )  # Sort by sssse_value   -> The higher - the more attractive
    sorted_list_ssssse           = sorted(rows,          key=lambda row:          row[8],           reverse=True )  # Sort by ssssse_value  -> The higher - the more attractive
    sorted_list_sss_no_div       = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[3],    reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
    sorted_list_ssss_no_div      = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[4],    reverse=False)  # Sort by ssss_value    -> The lower  - the more attractive
    sorted_list_sssss_no_div     = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[5],    reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
    sorted_list_ssse_no_div      = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[6],    reverse=True )  # Sort by ssse_value    -> The higher - the more attractive
    sorted_list_sssse_no_div     = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[7],    reverse=True )  # Sort by sssse_value   -> The higher - the more attractive
    sorted_list_ssssse_no_div    = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[8],    reverse=True )  # Sort by ssssse_value  -> The higher - the more attractive
    sorted_list_sss_only_div     = sorted(rows_only_div, key=lambda row_only_div: row_only_div[3],  reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
    sorted_list_ssss_only_div    = sorted(rows_only_div, key=lambda row_only_div: row_only_div[4],  reverse=False)  # Sort by ssss_value    -> The lower  - the more attractive
    sorted_list_sssss_only_div   = sorted(rows_only_div, key=lambda row_only_div: row_only_div[5],  reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
    sorted_list_ssse_only_div    = sorted(rows_only_div, key=lambda row_only_div: row_only_div[6],  reverse=True )  # Sort by ssse_value    -> The higher - the more attractive
    sorted_list_sssse_only_div   = sorted(rows_only_div, key=lambda row_only_div: row_only_div[7],  reverse=True )  # Sort by sssse_value   -> The higher - the more attractive
    sorted_list_ssssse_only_div  = sorted(rows_only_div, key=lambda row_only_div: row_only_div[8],  reverse=True )  # Sort by ssssse_value  -> The higher - the more attractive
    sorted_list_sssi             = sorted(rows,          key=lambda row:          row[9],           reverse=False)  # Sort by sssi_value    -> The lower  - the more attractive
    sorted_list_ssssi            = sorted(rows,          key=lambda row:          row[10],          reverse=False)  # Sort by ssssi_value   -> The lower  - the more attractive
    sorted_list_sssssi           = sorted(rows,          key=lambda row:          row[11],          reverse=False)  # Sort by sssssi_value  -> The lower  - the more attractive
    sorted_list_sssei            = sorted(rows,          key=lambda row:          row[12],          reverse=True )  # Sort by sssei_value   -> The higher - the more attractive
    sorted_list_ssssei           = sorted(rows,          key=lambda row:          row[13],          reverse=True )  # Sort by ssssei_value  -> The higher - the more attractive
    sorted_list_sssssei          = sorted(rows,          key=lambda row:          row[14],          reverse=True )  # Sort by sssssei_value -> The higher - the more attractive
    sorted_list_sssi_no_div      = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[9],    reverse=False)  # Sort by sssi_value    -> The lower  - the more attractive
    sorted_list_ssssi_no_div     = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[10],   reverse=False)  # Sort by ssssi_value   -> The lower  - the more attractive
    sorted_list_sssssi_no_div    = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[11],   reverse=False)  # Sort by sssssi_value  -> The lower  - the more attractive
    sorted_list_sssei_no_div     = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[12],   reverse=True )  # Sort by sssei_value   -> The higher - the more attractive
    sorted_list_ssssei_no_div    = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[13],   reverse=True )  # Sort by ssssei_value  -> The higher - the more attractive
    sorted_list_sssssei_no_div   = sorted(rows_no_div,   key=lambda row_no_div:   row_no_div[14],   reverse=True )  # Sort by sssssei_value -> The higher - the more attractive
    sorted_list_sssi_only_div    = sorted(rows_only_div, key=lambda row_only_div: row_only_div[9],  reverse=False)  # Sort by sssi_value    -> The lower  - the more attractive
    sorted_list_ssssi_only_div   = sorted(rows_only_div, key=lambda row_only_div: row_only_div[10], reverse=False)  # Sort by ssssi_value   -> The lower  - the more attractive
    sorted_list_sssssi_only_div  = sorted(rows_only_div, key=lambda row_only_div: row_only_div[11], reverse=False)  # Sort by sssssi_value  -> The lower  - the more attractive
    sorted_list_sssei_only_div   = sorted(rows_only_div, key=lambda row_only_div: row_only_div[12], reverse=True )  # Sort by sssei_value   -> The higher - the more attractive
    sorted_list_ssssei_only_div  = sorted(rows_only_div, key=lambda row_only_div: row_only_div[13], reverse=True )  # Sort by ssssei_value  -> The higher - the more attractive
    sorted_list_sssssei_only_div = sorted(rows_only_div, key=lambda row_only_div: row_only_div[14], reverse=True )  # Sort by sssssei_value -> The higher - the more attractive

    best_nrows = int(len(rows)/best_n_select)
    list_sss_best = []
    list_sss_best.extend(sorted_list_sss             [:best_nrows])
    list_sss_best.extend(sorted_list_ssss            [:best_nrows])
    list_sss_best.extend(sorted_list_sssss           [:best_nrows])
    list_sss_best.extend(sorted_list_ssse            [:best_nrows])
    list_sss_best.extend(sorted_list_sssse           [:best_nrows])
    list_sss_best.extend(sorted_list_ssssse          [:best_nrows])
    list_sss_best.extend(sorted_list_sssi            [:best_nrows])
    list_sss_best.extend(sorted_list_ssssi           [:best_nrows])
    list_sss_best.extend(sorted_list_sssssi          [:best_nrows])
    list_sss_best.extend(sorted_list_sssei           [:best_nrows])
    list_sss_best.extend(sorted_list_ssssei          [:best_nrows])
    list_sss_best.extend(sorted_list_sssssei         [:best_nrows])
    sorted_list_sssss_best_with_duplicates = sorted(list_sss_best, key=lambda row: row[5], reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
    sorted_list_sssss_best = list(k for k, _ in itertools.groupby(sorted_list_sssss_best_with_duplicates))

    list_sss_best_no_div = []
    list_sss_best_no_div.extend(sorted_list_sss_no_div    [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_ssss_no_div   [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_sssss_no_div  [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_ssse_no_div   [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_sssse_no_div  [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_ssssse_no_div [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_sssi_no_div   [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_ssssi_no_div  [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_sssssi_no_div [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_sssei_no_div  [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_ssssei_no_div [:best_nrows])
    list_sss_best_no_div.extend(sorted_list_sssssei_no_div[:best_nrows])
    sorted_list_sssss_best_no_div_with_duplicates = sorted(list_sss_best_no_div, key=lambda row: row[5], reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
    sorted_list_sssss_best_no_div = list(k for k, _ in itertools.groupby(sorted_list_sssss_best_no_div_with_duplicates))

    list_sss_best_only_div = []
    list_sss_best_only_div.extend(sorted_list_sss_only_div    [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_ssss_only_div   [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_sssss_only_div  [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_ssse_only_div   [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_sssse_only_div  [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_ssssse_only_div [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_sssi_only_div   [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_ssssi_only_div  [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_sssssi_only_div [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_sssei_only_div  [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_ssssei_only_div [:best_nrows])
    list_sss_best_only_div.extend(sorted_list_sssssei_only_div[:best_nrows])
    sorted_list_sssss_best_only_div_with_duplicates = sorted(list_sss_best_only_div, key=lambda row: row[5], reverse=False)  # Sort by sssss_value   -> The lower  - the more attractive
    sorted_list_sssss_best_only_div = list(k for k, _ in itertools.groupby(sorted_list_sssss_best_only_div_with_duplicates))
    #             0         1       2         3            4             5              6             7              8               9             10             11              12             13              14               15                    16,                    17                             18               19                            20                                  21               22                            23               24                          25                           26             27
    header_row = ["Ticker", "Name", "Sector", "sss_value", "ssss_value", "sssss_value", "ssse_value", "sssse_value", "ssssse_value", "sssi_value", "ssssi_value", "sssssi_value", "sssei_value", "ssssei_value", "sssssei_value", "annualized_revenue", "annualized_earnings", "enterprise_value_to_revenue", "evr_effective", "trailing_price_to_earnings", "trailing_12months_price_to_sales", "tpe_effective", "enterprise_value_to_ebitda", "profit_margin", "annualized_profit_margin", "held_percent_institutions", "forward_eps", "trailing_eps", "previous_close", "trailing_eps_percentage","price_to_book", "shares_outstanding", "net_income_to_common_shareholders", "nitcsh_to_shares_outstanding", "employees", "enterprise_value", "nitcsh_to_num_employees", "earnings_quarterly_growth", "price_to_earnings_to_growth_ratio", "sqrt_peg_ratio", "annualized_cash_flow_from_operating_activities", "ev_to_cfo_ratio", "last_dividend_0", "last_dividend_1", "last_dividend_2", "last_dividend_3" ]

    if research_mode: # Update the appearance counter using ssss and sssss
        list_len_ssss = len(sorted_list_sss)
        list_len_sss  = list_len_ssss
        if appearance_counter_min <= list_len_sss   <= appearance_counter_max:
            for index, row in enumerate(sorted_list_sss):
                appearance_counter_dict_sss[  (row[0],row[1],row[2],row[3],row[26])] = appearance_counter_dict_sss[  (row[0],row[1],row[2],row[3],row[26])]+math.sqrt(float(list_len_sss  -index))/float(list_len_sss  )
        if appearance_counter_min <= list_len_ssss  <= appearance_counter_max:
            for index, row in enumerate(sorted_list_ssss):
                appearance_counter_dict_ssss[ (row[0],row[1],row[2],row[4],row[26])] = appearance_counter_dict_ssss[ (row[0],row[1],row[2],row[4],row[26])]+math.sqrt(float(list_len_ssss -index))/float(list_len_ssss )
        list_len_sssss = len(sorted_list_sssss)
        if appearance_counter_min <= list_len_sssss <= appearance_counter_max:
            for index, row in enumerate(sorted_list_sssss):
                appearance_counter_dict_sssss[(row[0],row[1],row[2],row[5],row[26])] = appearance_counter_dict_sssss[(row[0],row[1],row[2],row[5],row[26])]+math.sqrt(float(list_len_sssss-index))/float(list_len_sssss)

    sorted_lists_list = [
        sorted_list_db,
        sorted_list_sss,                        sorted_list_ssss,                       sorted_list_sssss,                      sorted_list_ssse,
        sorted_list_sssse,                      sorted_list_ssssse,                     sorted_list_sss_no_div,                 sorted_list_ssss_no_div,
        sorted_list_sssss_no_div,               sorted_list_ssse_no_div,                sorted_list_sssse_no_div,               sorted_list_ssssse_no_div,
        sorted_list_sss_only_div,               sorted_list_ssss_only_div,              sorted_list_sssss_only_div,             sorted_list_ssse_only_div,
        sorted_list_sssse_only_div,             sorted_list_ssssse_only_div,            sorted_list_sssi,                       sorted_list_ssssi,
        sorted_list_sssssi,                     sorted_list_sssei,                      sorted_list_ssssei,                     sorted_list_sssssei,
        sorted_list_sssi_no_div,                sorted_list_ssssi_no_div,               sorted_list_sssssi_no_div,              sorted_list_sssei_no_div,
        sorted_list_ssssei_no_div,              sorted_list_sssssei_no_div,             sorted_list_sssi_only_div,              sorted_list_ssssi_only_div,
        sorted_list_sssssi_only_div,            sorted_list_sssei_only_div,             sorted_list_ssssei_only_div,            sorted_list_sssssei_only_div,
        sorted_list_sssss_best,                 sorted_list_sssss_best_no_div,          sorted_list_sssss_best_only_div
    ]

    for sorted_list in sorted_lists_list:
        sorted_list.insert(0, header_row)

    tase_str              = ""
    sectors_str           = ""
    all_str               = ""
    csv_db_str            = ""
    investpy_str          = ""
    marketcap_str         = ""
    pmargin_str           = "_pm{}".format(profit_margin_limit)
    evr_str               = "_evr{}".format(enterprise_value_to_revenue_limit)
    num_results_str       = "_nResults{}".format(len(rows))
    build_csv_db_only_str = ""
    if tase_mode:                        tase_str              = "_Tase"

    if len(sectors_list):
        if sectors_filter_out:
            sectors_list       += 'FO_'
        sectors_str            += '_'+'_'.join(sectors_list)
    else:
        for index, sector in enumerate(favor_sectors):
            sectors_str += '_{}{}'.format(sector.replace(' ',''),round(favor_sectors_by[index],NUM_ROUND_DECIMALS))

    if read_united_states_input_symbols: all_str               = '_All'
    if build_csv_db == 0:                csv_db_str            = '_DBR'
    if use_investpy:                     investpy_str          = '_Investpy'
    if market_cap_included:              marketcap_str         = '_MCap'
    if build_csv_db_only:                build_csv_db_only_str = '_BuildDb'
    date_and_time = time.strftime("Results/%Y%m%d-%H%M%S{}{}{}{}{}{}{}{}{}{}".format(tase_str, sectors_str, all_str, csv_db_str, marketcap_str, investpy_str, pmargin_str, evr_str, build_csv_db_only_str, num_results_str))

    filenames_list = sss_filenames.create_filenames_list(date_and_time)

    evr_pm_col_title_row = ['Maximal enterprise_value_to_revenue_limit: {}, Minimal profit_margin_limit: {}'.format(enterprise_value_to_revenue_limit, profit_margin_limit)]

    if generate_result_folders:
        for index in range(len(filenames_list)):
            os.makedirs(os.path.dirname(filenames_list[index]), exist_ok=True)
            with open(filenames_list[index], mode='w', newline='') as engine:
                writer = csv.writer(engine)
                sorted_lists_list[index].insert(0, evr_pm_col_title_row)
                writer.writerows(sorted_lists_list[index])

    return len(rows)
