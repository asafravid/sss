#############################################################################
#
# Version 0.1.24 - Author: Asaf Ravid <asaf.rvd@gmail.com>
#
#    Stock Screener and Scanner - based on yfinance and investpy
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


# TODO: ASAF: 0. Remove non-required columns from the indices input CSVs - faster load and down to the point
#                0.1. Investigate average and ranges of all parameters in the SSS Core Equation - summarise in the document itself (Test Case)
#             1. Check and multi dim and investigate eqg_min and revenue_quarterly_growth_min: Check why Yahoo Finance always gives QRG values of 0? Unusable if that is always so
#             3. Take latest yfinance base.py (and other - compare the whole folder) and updates - maybe not required - but just stay up to date
#             5. Investigate and add: https://www.investopedia.com/terms/o/operatingmargin.asp - operating margin
#             6. Add Free Cash flow [FCF] (EV/FreeCashFlow): Inverse of the Free Cash Flow Yield (https://www.stockopedia.com/ratios/ev-free-cash-flow-336/#:~:text=What%20is%20the%20definition%20of,the%20Free%20Cash%20Flow%20Yield.)
#             7. There is already an EV/CFO ratio.
#                  CFO - CapitalExpenditures = FCF
#                  EV/CFO * EV/FCF = EV^2 / (CFO * [CFO - CapitalExpenditures]) | EV/CFO + EV/FCF = EV*(1/CFO + 1/(CFO-CapitalExpenditures))
#                  Conclusion: EV/FCF is better as it provides moe information. But make this a lower priority for development
#                              Bonus: When there is no CFO, Use FCF, and Vice Versa - more information
#             9. Which are the most effective parameters? Correlate the sorting of sss_value to the results and each of the sorted-by-parameter list.
#            10. Important: https://www.oldschoolvalue.com/investing-strategy/walter-schloss-investing-strategy-producing-towering-returns/#:~:text=Walter%20Schloss%20ran%20with%20the,to%20perform%20complex%20valuations%20either.
#                10.1.  3 years low, 5 years low
#                10.2.  F-Score, M-Score, Z-Score
#                10.3.  Multi-Dim scan over the distance from low, and over the Schloff Score - define a Walter-Schloss score
#                10.4.  Remove the square root from DtoE ?
#                10.5.  MktCapM is >= US$ 300 million (basis year 2000) adjusted yearly
#                10.6.  Consider only stocks that are listed at least 10 years
#                10.7.  Price 1 Day ago within 15% of the 52 week low
#                10.8.  Take the top 1000 stocks with highest Number of Insiders owning shares#            11. Calculate share_price/52weekLow 0.1
#                10.9.  Take the top 500 stocks with highest Current Dividend Yield %#            12. https://pyportfolioopt.readthedocs.io/en/latest/UserGuide.html -> Use
#                10.10. Take the top 250 stocks with lowest Latest Filing P/E ratio#            13. Calculate the ROE - Return on equity
#                10.11. Take the top 125 stocks with lowest Latest Filing P/B ratio#            14. Operating Cash Flow Growth - interesting: https://github.com/JerBouma/FundamentalAnalysis
#                10.12. Take the top 75 stocks with lowest Latest Filing Long Term Debt#            15. Quick Ratio - https://github.com/JerBouma/FinanceDatabase - interesting
#


import time
import random                                                                                                          
import pandas   as pd
import yfinance as yf
import csv
import os
import sss_filenames
import investpy
import math

from threading import Thread
from dataclasses import dataclass
# TODO: ASAFR: Try again the CurrencyConverter and check it on venv as well
from forex_python.converter import CurrencyRates
from currency_converter import CurrencyConverter

VERBOSE_LOGS = 0

SKIP_5LETTER_Y_STOCK_LISTINGS                = True       # Skip ADRs - American Depositary receipts (5 Letter Stocks)
NUM_ROUND_DECIMALS                           = 5
NUM_EMPLOYEES_UNKNOWN                        = 10000000   # This will make the company very inefficient in terms of number of employees
PROFIT_MARGIN_UNKNOWN                        = 0.00001    # This will make the company almost not profitable terms of profit margins, thus less attractive
PRICE_TO_BOOK_UNKNOWN                        = 1000.0
PERCENT_HELD_INSTITUTIONS_LOW                = 0.01       # low, to make less relevant
PEG_UNKNOWN                                  = 1          # use a neutral value when PEG is unknown
SHARES_OUTSTANDING_UNKNOWN                   = 100000000  # 100 Million Shares - just a value for calculation of a currently unused vaue
BAD_SSS                                      = 10.0 ** 50.0
PROFIT_MARGIN_WEIGHTS                        = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]  # from oldest to newest
CASH_FLOW_WEIGHTS                            = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]  # from oldest to newest
REVENUES_WEIGHTS                             = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]  # from oldest to newest
EARNINGS_WEIGHTS                             = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]  # from oldest to newest
BALANCE_SHEETS_WEIGHTS                       = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]  # from oldest to newest
EQG_UNKNOWN                                  = -0.9   # -90% TODO: ASAFR: 1. Scan (like pm and ever) values of eqg for big data research better recommendations
EQG_POSITIVE_FACTOR                          = 5.0   # When positive, it will have a 5x factor on the 1 + function
EQG_MAX_VALUE                                = 100
EQG_WEIGHT_VS_YOY                            = 0.75   # the provided EQG is weighted more than the manually calculated one
EQG_DAMPER                                   = 0.05
REVENUE_QUARTERLY_GROWTH_UNKNOWN             = -0.75  # -75% TODO: ASAFR: 1. Scan (like pm and ever) values of revenue_quarterly_growth  for big data research better recommendations
REVENUE_QUARTERLY_GROWTH_POSITIVE_FACTOR     = 10.0   # When positive, it will have a 10x factor on the 1 + function
TRAILING_EPS_PERCENTAGE_DAMP_FACTOR          = 0.01   # When the trailing_eps_percentage is very low (units are ratio here), this damper shall limit the affect to x100 not more)
PROFIT_MARGIN_DAMPER                         = 0.01   # When the profit_margin                   is very low (units are ratio here), this damper shall limit the affect to x100 not more)
RATIO_DAMPER                                 = 0.01   # When the total/current_other_other ratio is very low (units are ratio here), this damper shall limit the affect to x100 not more)
REFERENCE_DB_MAX_VALUE_DIFF_FACTOR_THRESHOLD = 0.9   # if there is a parameter difference from reference db, in which the difference of values is higher than 0.75*abs(max_value) then something went wrong with the fetch of values from yfinance. Compensate smartly from reference database
QUARTERLY_YEARLY_MISSING_FACTOR              = 0.25  # if either yearly or quarterly values are missing - compensate by other with bad factor (less information means less attractive)

# TODO: ASAFR: All below boosters should be calibrated by:
#              1. The rarety (statistically comapred to all the stocks in scan) - proportionaly to it (the rarest the case - the more boost)
#              2. The ascent (slope) of the increase and the positive value -> the higher - the more boost
#              3. Add similar boosters for other annual and quarterly weighted-averaged parameters
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE                = 2.25   # Provide a "bonus" for companies whose profit margins have increased continuously annually
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE             = 1.75   # Provide a "bonus" for companies whose profit margins have increased continuously quarterly
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_POSITIVE                = 2.5    # Provide a "bonus" for companies whose profit margins have been continuously positive annually
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_POSITIVE             = 2.5    # Provide a "bonus" for companies whose profit margins have been continuously positive quarterly
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_EARNINGS    = 2.75   # Provide a "bonus" for companies whose earnings       have been continuously increasing annually
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_REVENUE     = 2.25   # Provide a "bonus" for companies whose revenue        has  been continuously increasing annually
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_EARNINGS = 2.75   # Provide a "bonus" for companies whose earnings       have been continuously increasing quarterly
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_REVENUE  = 2.5    # Provide a "bonus" for companies whose revenue        has  been continuously increasing quarterly
PROFIT_MARGIN_DUPLICATION_FACTOR                                  = 8.0    # When copying profit margin (if either quarterized/annualized/profit_margin is missing) - devide by this factor
NEGATIVE_CFO_FACTOR                                               = 10.0   #
NEGATIVE_PEG_RATIO_FACTOR                                         = 10.0   # -0.5 -> 5, and -0.001 -> 0.01
NEGATIVE_DEBT_TO_EQUITY_FACTOR                                    = 10.0   # -0.5 -> 5, and -0.001 -> 0.01
NEGATIVE_PRICE_TO_EARNINGS_FACTOR                                 = 10.0

TRAILING_PRICE_TO_EARNINGS_WEIGHT = 0.75
FORWARD_PRICE_TO_EARNINGS_WEIGHT  = 0.25

DIST_FROM_LOW_FACTOR_DAMPER                = 0.001
DIST_FROM_LOW_FACTOR_HIGHER_THAN_ONE_POWER = 6

#
# TODO: ASAFR: Mati Alon (https://www.gurufocus.com/letter.php)
#              1. Add Free Cash Flow
#              2. Lower Market Cap - Give more weight (in multi-dimensional scan)

@dataclass
class StockData:
    symbol:                                         str   = 'None'
    short_name:                                     str   = 'None'
    quote_type:                                     str   = 'None'
    sector:                                         str   = 'None'
    country:                                        str   = 'Unknown'
    sss_value:                                      float = BAD_SSS
    annualized_revenue:                             float = 0.0
    annualized_earnings:                            float = 0.0
    quarterized_revenue:                            float = 0.0
    quarterized_earnings:                           float = 0.0
    effective_earnings:                             float = 0.0
    effective_revenue:                              float = 0.0
    annualized_total_revenue:                       float = 0.0
    annualized_net_income:                          float = 0.0
    quarterized_total_revenue:                      float = 0.0
    quarterized_net_income:                         float = 0.0
    effective_net_income:                           float = 0.0
    effective_total_revenue:                        float = 0.0
    enterprise_value_to_revenue:                    float = 0.0
    evr_effective:                                  float = 0.0
    trailing_price_to_earnings:                     float = 0.0
    forward_price_to_earnings:                      float = 0.0
    effective_price_to_earnings:                    float = 0.0
    trailing_12months_price_to_sales:               float = 0.0
    pe_effective:                                   float = 0.0
    enterprise_value_to_ebitda:                     float = 0.0
    profit_margin:                                  float = 0.0
    annualized_profit_margin:                       float = 0.0
    annualized_profit_margin_boost:                 float = 0.0
    quarterized_profit_margin:                      float = 0.0
    quarterized_profit_margin_boost:                float = 0.0
    effective_profit_margin:                        float = 0.0
    held_percent_institutions:                      float = 0.0
    forward_eps:                                    float = 0.0
    trailing_eps:                                   float = 0.0
    previous_close:                                 float = 0.0
    trailing_eps_percentage:                        float = 0.0 # trailing_eps / previousClose
    price_to_book:                                  float = 0.0
    shares_outstanding:                             float = 0.0
    net_income_to_common_shareholders:              float = 0.0
    nitcsh_to_shares_outstanding:                   float = 0.0
    employees:                                      int   = 0
    enterprise_value:                               int   = 0
    market_cap:                                     int   = 0
    nitcsh_to_num_employees:                        float = 0.0
    eqg:                                            float = 0.0  # Value is a ratio, such that when multiplied by 100, yields percentage (%) units
    eqg_yoy:                                        float = 0.0  # calculated from the yearly earnings - if available
    niqg_yoy:                                       float = 0.0  # Net Income Quarterly Growth: calculated from the yearly net income - if available
    eqg_effective:                                  float = 0.0  # average of eqg_yoy and eqg
    eqg_factor_effective:                           float = 0.0  # function with positive factor and damper
    revenue_quarterly_growth:                       float = 0.0  # Value is a ratio, such that when multiplied by 100, yields percentage (%) units --> TODO: ASAFR: Now with the financials_yearly and financials_quarterly, this value can finally be calculated!
    price_to_earnings_to_growth_ratio:              float = 0.0
    effective_peg_ratio:                            float = 0.0
    annualized_cash_flow_from_operating_activities: float = 0.0
    quarterized_cash_flow_from_operating_activities:float = 0.0
    annualized_ev_to_cfo_ratio:                     float = 0.0  # https://investinganswers.com/dictionary/e/enterprise-value-cash-flow-operations-evcfo
    quarterized_ev_to_cfo_ratio:                    float = 0.0  # https://investinganswers.com/dictionary/e/enterprise-value-cash-flow-operations-evcfo
    ev_to_cfo_ratio_effective:                      float = 0.0
    annualized_debt_to_equity:                      float = 0.0
    quarterized_debt_to_equity:                     float = 0.0
    debt_to_equity_effective:                       float = 0.0
    financial_currency:                             str   = 'None'
    conversion_rate_mult_to_usd:                    float = 0.0
    last_dividend_0:                                float = 0.0
    last_dividend_1:                                float = 0.0
    last_dividend_2:                                float = 0.0
    last_dividend_3:                                float = 0.0
    fifty_two_week_change:                          float = 0.0
    fifty_two_week_low:                             float = 0.0
    fifty_two_week_high:                            float = 0.0
    two_hundred_day_average:                        float = 0.0
    previous_close_percentage_from_200d_ma:         float = 0.0
    previous_close_percentage_from_52w_low:         float = 0.0
    previous_close_percentage_from_52w_high:        float = 0.0
    dist_from_low_factor:                           float = 0.0
    eff_dist_from_low_factor:                       float = 0.0
    annualized_total_ratio:                         float = 0.0
    quarterized_total_ratio:                        float = 0.0
    annualized_other_current_ratio:                 float = 0.0
    quarterized_other_current_ratio:                float = 0.0
    annualized_other_ratio:                         float = 0.0
    quarterized_other_ratio:                        float = 0.0
    annualized_total_current_ratio:                 float = 0.0
    quarterized_total_current_ratio:                float = 0.0
    total_ratio_effective:                          float = 0.0
    other_current_ratio_effective:                  float = 0.0
    other_ratio_effective:                          float = 0.0
    total_current_ratio_effective:                  float = 0.0
    skip_reason:                                    str   = 'None'


g_header_row = ["Symbol", "Name", "Sector", "Country", "sss_value", "annualized_revenue", "annualized_earnings", "quarterized_revenue", "quarterized_earnings", "effective_earnings", "effective_revenue", "annualized_total_revenue", "annualized_net_income", "quarterized_total_revenue", "quarterized_net_income", "effective_net_income", "effective_total_revenue", "enterprise_value_to_revenue", "evr_effective", "trailing_price_to_earnings", "forward_price_to_earnings", "effective_price_to_earnings", "trailing_12months_price_to_sales", "pe_effective", "enterprise_value_to_ebitda", "profit_margin", "annualized_profit_margin", "annualized_profit_margin_boost", "quarterized_profit_margin", "quarterized_profit_margin_boost", "effective_profit_margin", "held_percent_institutions", "forward_eps", "trailing_eps", "previous_close", "trailing_eps_percentage","price_to_book", "shares_outstanding", "net_income_to_common_shareholders", "nitcsh_to_shares_outstanding", "employees", "enterprise_value", "market_cap", "nitcsh_to_num_employees", "eqg", "eqg_yoy", "niqg_yoy", "eqg_effective", "eqg_factor_effective", "revenue_quarterly_growth", "price_to_earnings_to_growth_ratio", "effective_peg_ratio", "annualized_cash_flow_from_operating_activities", "quarterized_cash_flow_from_operating_activities", "annualized_ev_to_cfo_ratio", "quarterized_ev_to_cfo_ratio", "ev_to_cfo_ratio_effective", "annualized_debt_to_equity", "quarterized_debt_to_equity", "debt_to_equity_effective", "financial_currency", "conversion_rate_mult_to_usd", "last_dividend_0", "last_dividend_1", "last_dividend_2", "last_dividend_3", "fifty_two_week_change", "fifty_two_week_low", "fifty_two_week_high", "two_hundred_day_average", "previous_close_percentage_from_200d_ma", "previous_close_percentage_from_52w_low", "previous_close_percentage_from_52w_high", "dist_from_low_factor", "eff_dist_from_low_factor", "annualized_total_ratio", "quarterized_total_ratio", "annualized_other_current_ratio", "quarterized_other_current_ratio", "annualized_other_ratio", "quarterized_other_ratio", "annualized_total_current_ratio", "quarterized_total_current_ratio", "total_ratio_effective", "other_current_ratio_effective", "other_ratio_effective", "total_current_ratio_effective", "skip_reason" ]
g_symbol_index                                          = g_header_row.index("Symbol")
g_name_index                                            = g_header_row.index("Name")
g_sector_index                                          = g_header_row.index("Sector")
g_country_index                                         = g_header_row.index("Country")
g_sss_value_index                                       = g_header_row.index("sss_value")
g_annualized_revenue_index                              = g_header_row.index("annualized_revenue")
g_annualized_earnings_index                             = g_header_row.index("annualized_earnings")
g_quarterized_revenue_index                             = g_header_row.index("quarterized_revenue")
g_quarterized_earnings_index                            = g_header_row.index("quarterized_earnings")
g_effective_earnings_index                              = g_header_row.index("effective_earnings")
g_effective_revenue_index                               = g_header_row.index("effective_revenue")
g_annualized_total_revenue_index                        = g_header_row.index("annualized_total_revenue")
g_annualized_net_income_index                           = g_header_row.index("annualized_net_income")
g_quarterized_total_revenue_index                       = g_header_row.index("quarterized_total_revenue")
g_quarterized_net_income_index                          = g_header_row.index("quarterized_net_income")
g_effective_net_income_index                            = g_header_row.index("effective_net_income")
g_effective_total_revenue_index                         = g_header_row.index("effective_total_revenue")
g_enterprise_value_to_revenue_index                     = g_header_row.index("enterprise_value_to_revenue")
g_evr_effective_index                                   = g_header_row.index("evr_effective")
g_trailing_price_to_earnings_index                      = g_header_row.index("trailing_price_to_earnings")
g_forward_price_to_earnings_index                       = g_header_row.index("forward_price_to_earnings")
g_effective_price_to_earnings_index                     = g_header_row.index("effective_price_to_earnings")
g_trailing_12months_price_to_sales_index                = g_header_row.index("trailing_12months_price_to_sales")
g_pe_effective_index                                    = g_header_row.index("pe_effective")
g_enterprise_value_to_ebitda_index                      = g_header_row.index("enterprise_value_to_ebitda")
g_profit_margin_index                                   = g_header_row.index("profit_margin")
g_annualized_profit_margin_index                        = g_header_row.index("annualized_profit_margin")
g_annualized_profit_margin_boost_index                  = g_header_row.index("annualized_profit_margin_boost")
g_quarterized_profit_margin_index                       = g_header_row.index("quarterized_profit_margin")
g_quarterized_profit_margin_boost_index                 = g_header_row.index("quarterized_profit_margin_boost")
g_effective_profit_margin_index                         = g_header_row.index("effective_profit_margin")
g_held_percent_institutions_index                       = g_header_row.index("held_percent_institutions")
g_forward_eps_index                                     = g_header_row.index("forward_eps")
g_trailing_eps_index                                    = g_header_row.index("trailing_eps")
g_previous_close_index                                  = g_header_row.index("previous_close")
g_trailing_eps_percentage_index                         = g_header_row.index("trailing_eps_percentage")
g_price_to_book_index                                   = g_header_row.index("price_to_book")
g_shares_outstanding_index                              = g_header_row.index("shares_outstanding")
g_net_income_to_common_shareholders_index               = g_header_row.index("net_income_to_common_shareholders")
g_nitcsh_to_shares_outstanding_index                    = g_header_row.index("nitcsh_to_shares_outstanding")
g_employees_index                                       = g_header_row.index("employees")
g_enterprise_value_index                                = g_header_row.index("enterprise_value")
g_market_cap_index                                      = g_header_row.index("market_cap")
g_nitcsh_to_num_employees_index                         = g_header_row.index("nitcsh_to_num_employees")
g_eqg_index                                             = g_header_row.index("eqg")
g_eqg_yoy_index                                         = g_header_row.index("eqg_yoy")
g_niqg_yoy_index                                        = g_header_row.index("niqg_yoy")
g_eqg_effective_index                                   = g_header_row.index("eqg_effective")
g_eqg_factor_effective_index                            = g_header_row.index("eqg_factor_effective")
g_revenue_quarterly_growth_index                        = g_header_row.index("revenue_quarterly_growth")
g_price_to_earnings_to_growth_ratio_index               = g_header_row.index("price_to_earnings_to_growth_ratio")
g_effective_peg_ratio_index                             = g_header_row.index("effective_peg_ratio")
g_annualized_cash_flow_from_operating_activities_index  = g_header_row.index("annualized_cash_flow_from_operating_activities")
g_quarterized_cash_flow_from_operating_activities_index = g_header_row.index("quarterized_cash_flow_from_operating_activities")
g_annualized_ev_to_cfo_ratio_index                      = g_header_row.index("annualized_ev_to_cfo_ratio")
g_quarterized_ev_to_cfo_ratio_index                     = g_header_row.index("quarterized_ev_to_cfo_ratio")
g_ev_to_cfo_ratio_effective_index                       = g_header_row.index("ev_to_cfo_ratio_effective")
g_annualized_debt_to_equity_index                       = g_header_row.index("annualized_debt_to_equity")
g_quarterized_debt_to_equity_index                      = g_header_row.index("quarterized_debt_to_equity")
g_debt_to_equity_effective_index                        = g_header_row.index("debt_to_equity_effective")
g_financial_currency_index                              = g_header_row.index("financial_currency")
g_conversion_rate_mult_to_usd_index                     = g_header_row.index("conversion_rate_mult_to_usd")
g_last_dividend_0_index                                 = g_header_row.index("last_dividend_0")
g_last_dividend_1_index                                 = g_header_row.index("last_dividend_1")
g_last_dividend_2_index                                 = g_header_row.index("last_dividend_2")
g_last_dividend_3_index                                 = g_header_row.index("last_dividend_3")
g_fifty_two_week_change_index                           = g_header_row.index("fifty_two_week_change")
g_fifty_two_week_low_index                              = g_header_row.index("fifty_two_week_low")
g_fifty_two_week_high_index                             = g_header_row.index("fifty_two_week_high")
g_two_hundred_day_average_index                         = g_header_row.index("two_hundred_day_average")
g_previous_close_percentage_from_200d_ma_index          = g_header_row.index("previous_close_percentage_from_200d_ma")
g_previous_close_percentage_from_52w_low_index          = g_header_row.index("previous_close_percentage_from_52w_low")
g_previous_close_percentage_from_52w_high_index         = g_header_row.index("previous_close_percentage_from_52w_high")
g_dist_from_low_factor_index                            = g_header_row.index("dist_from_low_factor")
g_eff_dist_from_low_factor_index                        = g_header_row.index("eff_dist_from_low_factor")
g_annualized_total_ratio_index                          = g_header_row.index("annualized_total_ratio")
g_quarterized_total_ratio_index                         = g_header_row.index("quarterized_total_ratio")
g_annualized_other_current_ratio_index                  = g_header_row.index("annualized_other_current_ratio")
g_quarterized_other_current_ratio_index                 = g_header_row.index("quarterized_other_current_ratio")
g_annualized_other_ratio_index                          = g_header_row.index("annualized_other_ratio")
g_quarterized_other_ratio_index                         = g_header_row.index("quarterized_other_ratio")
g_annualized_total_current_ratio_index                  = g_header_row.index("annualized_total_current_ratio")
g_quarterized_total_current_ratio_index                 = g_header_row.index("quarterized_total_current_ratio")
g_total_ratio_effective_index                           = g_header_row.index("total_ratio_effective")
g_other_current_ratio_effective_index                   = g_header_row.index("other_current_ratio_effective")
g_other_ratio_effective_index                           = g_header_row.index("other_ratio_effective")
g_total_current_ratio_effective_index                   = g_header_row.index("total_current_ratio_effective")
g_skip_reason_index                                     = g_header_row.index("skip_reason")


def check_quote_type(stock_data, research_mode):
    if stock_data.quote_type == 'MUTUALFUND' and not research_mode: # Definition of a mutual fund 'quoteType' field in base.py, those are not interesting
        print('Mutual Fund: Skip')
        return False  # Not interested in those and they lack all the below info[] properties so nothing to do with them anyways
    if stock_data.quote_type == 'ETF' and not research_mode: # Definition of a mutual fund 'quoteType' field in base.py, those are not interesting
        print('ETF: Skip')
        return False  # Not interested in those and they lack all the below info[] properties so nothing to do with them anyways
    return True


def check_sector(stock_data, sectors_list):
    # Fix stocks' Sectors to Correct Sector. yfinance sometimes has those mistaken
    if   stock_data.symbol in ['BRMG.TA',   'RLCO.TA',   'DELT.TA',  'TDRN.TA',   'ECP.TA'      ]: stock_data.sector = 'Consumer Cyclical'
    elif stock_data.symbol in ['EFNC.TA',   'GIBUI.TA',  'KMNK-M.TA'                            ]: stock_data.sector = 'Financial Services'
    elif stock_data.symbol in ['DEDR-L.TA', 'GLEX-L',    'RPAC.TA',  'CDEV.TA',   'GNRS.TA'     ]: stock_data.sector = 'Energy'
    elif stock_data.symbol in ['GLRS.TA',   'WILC.TA',   'MEDN.TA'                              ]: stock_data.sector = 'Consumer Defensive'
    elif stock_data.symbol in ['POLY.TA',   'WTS.TA',    'YBOX.TA',  'PLAZ-L.TA', 'TIGBUR.TA',
                               'ROTS.TA',   'AZRT.TA',   'SKBN.TA',  'DUNI.TA',   'DNYA.TA',
                               'HGG.TA',    'YAAC.TA',   'LZNR.TA',  'LSCO.TA',   'MGRT.TA',
                               'ALMA.TA',   'RTSN.TA',   'AVIV.TA',  'KRNV.TA',   'LAHAV.TA',
                               'NERZ.TA',   'SNEL.TA'                                           ]: stock_data.sector = 'Real Estate'
    elif stock_data.symbol in ['XTLB.TA',   'UNVO.TA',   'BONS.TA',  'CSURE.TA',  'GODM-M.TA',
                               'ILX.TA',    'LCTX.TA',   'ORMP.TA'                              ]: stock_data.sector = 'Healthcare'
    elif stock_data.symbol in ['BIRM.TA'                                                        ]: stock_data.sector = 'Industrials'
    elif stock_data.symbol in ['IGLD-M.TA'                                                      ]: stock_data.sector = 'Communication Services'
    elif stock_data.symbol in ['UNCT-L.TA', 'ROBO.TA',   'SONO.TA',  'SMAG-L.TA', 'STG.TA',
                               'BIGT-L.TA', 'BIMT-L.TA', 'BVC.TA',   'ECPA.TA',   'ELLO.TA',
                               'FLYS.TA',   'FORTY.TA',  'GFC-L.TA', 'IARG-L.TA', 'IBITEC-F.TA',
                               'MBMX-M.TA', 'MITC.TA',   'SMAG-L.TA','ORBI.TA',   'ARYT.TA',
                               'ORTC.TA',   'PERI.TA',   'PAYT.TA',  'TUZA.TA',   'ENLT.TA',
                               'ESLT.TA',   'ORA.TA',    'ENRG.TA',  'RADA.TA',   'DORL.TA',
                               'AUGN.TA',   'FRSX.TA',   'SLGN.TA',  'AQUA.TA',   'PNRG.TA',
                               'BMLK.TA',   'MSKE.TA',   'HMGS.TA',  'HICN.TA',   'ARDM.TA',
                               'ENOG.TA',   'BLND.TA',   'ARTS.TA',  'BNRG.TA',   'MIFT.TA',
                               'SNFL.TA',   'KVSR.TA',   'SNEL.TA',  'SVRT.TA',   'GIX.TA',
                               'NXFR.TA',   'FEAT-L.TA'                                         ]: stock_data.sector = 'Technology'

    if len(sectors_list) and stock_data.sector not in sectors_list:
        return False
    return True

def check_country(stock_data, countries_list):
    if len(countries_list) and stock_data.country not in countries_list:
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


def weighted_average(values_list, weights):
    return sum([values_list[i]*weights[i] for i in range(len(values_list))])/sum(weights)

# TODO: ASAFR: Investigate NSR stocks who have sss value of 0...: AMG, HPP, RPRX, SQ, FAST, HAE, DVA, FBHS
def sss_core_equation_value_set(stock_data):
    if stock_data.shares_outstanding and stock_data.net_income_to_common_shareholders != None: stock_data.nitcsh_to_shares_outstanding = float(stock_data.net_income_to_common_shareholders) / float(stock_data.shares_outstanding)
    if stock_data.employees          and stock_data.net_income_to_common_shareholders != None: stock_data.nitcsh_to_num_employees = float(stock_data.net_income_to_common_shareholders) / float(stock_data.employees)

    if stock_data.trailing_12months_price_to_sales != None and stock_data.trailing_12months_price_to_sales > 0 and stock_data.effective_profit_margin != None and stock_data.effective_profit_margin > 0 and stock_data.eqg_factor_effective and stock_data.eqg_factor_effective > 0 != None and stock_data.pe_effective != None and stock_data.pe_effective > 0 and stock_data.enterprise_value_to_ebitda != None and stock_data.enterprise_value_to_ebitda > 0 and stock_data.ev_to_cfo_ratio_effective != None and stock_data.ev_to_cfo_ratio_effective > 0 and stock_data.effective_peg_ratio != None and stock_data.effective_peg_ratio > 0 and stock_data.price_to_book != None and stock_data.price_to_book > 0 and stock_data.debt_to_equity_effective > 0 and stock_data.total_ratio_effective > 0 and stock_data.total_current_ratio_effective > 0 and stock_data.evr_effective != None and stock_data.evr_effective > 0.0:
        effective_debt_to_equity_effective = math.sqrt(stock_data.debt_to_equity_effective)
        effective_current_ratio            = (stock_data.total_ratio_effective + stock_data.total_current_ratio_effective) / 2.0  # TODO: ASAFR: In the next stage - add the other and current other ratios - more information -> more completeness
        stock_data.sss_value               = float(stock_data.eff_dist_from_low_factor * ((stock_data.evr_effective * stock_data.pe_effective * stock_data.enterprise_value_to_ebitda * stock_data.trailing_12months_price_to_sales * stock_data.price_to_book) / (stock_data.effective_profit_margin * effective_current_ratio)) * ((stock_data.effective_peg_ratio * stock_data.ev_to_cfo_ratio_effective * effective_debt_to_equity_effective) / stock_data.eqg_factor_effective))  # The lower  the better
    else:
        stock_data.sss_value = BAD_SSS


# Rounding to non-None values + set None values to 0 for simplicity:
def round_and_avoid_none_values(stock_data):
    if stock_data.sss_value                                       != None: stock_data.sss_value                                       = round(stock_data.sss_value,                                       NUM_ROUND_DECIMALS)
    if stock_data.annualized_revenue                              != None: stock_data.annualized_revenue                              = round(stock_data.annualized_revenue,                              NUM_ROUND_DECIMALS)
    if stock_data.annualized_earnings                             != None: stock_data.annualized_earnings                             = round(stock_data.annualized_earnings,                             NUM_ROUND_DECIMALS)
    if stock_data.quarterized_revenue                             != None: stock_data.quarterized_revenue                             = round(stock_data.quarterized_revenue,                             NUM_ROUND_DECIMALS)
    if stock_data.quarterized_earnings                            != None: stock_data.quarterized_earnings                            = round(stock_data.quarterized_earnings,                            NUM_ROUND_DECIMALS)
    if stock_data.effective_earnings                              != None: stock_data.effective_earnings                              = round(stock_data.effective_earnings,                              NUM_ROUND_DECIMALS)
    if stock_data.effective_revenue                               != None: stock_data.effective_revenue                               = round(stock_data.effective_revenue,                               NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_revenue                        != None: stock_data.annualized_total_revenue                        = round(stock_data.annualized_total_revenue,                              NUM_ROUND_DECIMALS)
    if stock_data.annualized_net_income                           != None: stock_data.annualized_net_income                           = round(stock_data.annualized_net_income,                             NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_revenue                       != None: stock_data.quarterized_total_revenue                       = round(stock_data.quarterized_total_revenue,                             NUM_ROUND_DECIMALS)
    if stock_data.quarterized_net_income                          != None: stock_data.quarterized_net_income                          = round(stock_data.quarterized_net_income,                            NUM_ROUND_DECIMALS)
    if stock_data.effective_net_income                            != None: stock_data.effective_net_income                            = round(stock_data.effective_net_income,                              NUM_ROUND_DECIMALS)
    if stock_data.effective_total_revenue                         != None: stock_data.effective_total_revenue                         = round(stock_data.effective_total_revenue,                               NUM_ROUND_DECIMALS)
    if stock_data.enterprise_value_to_revenue                     != None: stock_data.enterprise_value_to_revenue                     = round(stock_data.enterprise_value_to_revenue,                     NUM_ROUND_DECIMALS)
    if stock_data.evr_effective                                   != None: stock_data.evr_effective                                   = round(stock_data.evr_effective,                                   NUM_ROUND_DECIMALS)
    if stock_data.trailing_price_to_earnings                      != None: stock_data.trailing_price_to_earnings                      = round(stock_data.trailing_price_to_earnings,                      NUM_ROUND_DECIMALS)
    if stock_data.forward_price_to_earnings                       != None: stock_data.forward_price_to_earnings                       = round(stock_data.forward_price_to_earnings,                       NUM_ROUND_DECIMALS)
    if stock_data.effective_price_to_earnings                     != None: stock_data.effective_price_to_earnings                     = round(stock_data.effective_price_to_earnings,                     NUM_ROUND_DECIMALS)
    if stock_data.trailing_12months_price_to_sales                != None: stock_data.trailing_12months_price_to_sales                = round(stock_data.trailing_12months_price_to_sales,                NUM_ROUND_DECIMALS)
    if stock_data.pe_effective                                    != None: stock_data.pe_effective                                    = round(stock_data.pe_effective,                                    NUM_ROUND_DECIMALS)
    if stock_data.enterprise_value_to_ebitda                      != None: stock_data.enterprise_value_to_ebitda                      = round(stock_data.enterprise_value_to_ebitda,                      NUM_ROUND_DECIMALS)
    if stock_data.profit_margin                                   != None: stock_data.profit_margin                                   = round(stock_data.profit_margin,                                   NUM_ROUND_DECIMALS)
    if stock_data.annualized_profit_margin                        != None: stock_data.annualized_profit_margin                        = round(stock_data.annualized_profit_margin,                        NUM_ROUND_DECIMALS)
    if stock_data.annualized_profit_margin_boost                  != None: stock_data.annualized_profit_margin_boost                  = round(stock_data.annualized_profit_margin_boost,                  NUM_ROUND_DECIMALS)
    if stock_data.quarterized_profit_margin                       != None: stock_data.quarterized_profit_margin                       = round(stock_data.quarterized_profit_margin,                       NUM_ROUND_DECIMALS)
    if stock_data.quarterized_profit_margin_boost                 != None: stock_data.quarterized_profit_margin_boost                 = round(stock_data.quarterized_profit_margin_boost,                 NUM_ROUND_DECIMALS)
    if stock_data.effective_profit_margin                         != None: stock_data.effective_profit_margin                         = round(stock_data.effective_profit_margin,                         NUM_ROUND_DECIMALS)
    if stock_data.held_percent_institutions                       != None: stock_data.held_percent_institutions                       = round(stock_data.held_percent_institutions,                       NUM_ROUND_DECIMALS)
    if stock_data.forward_eps                                     != None: stock_data.forward_eps                                     = round(stock_data.forward_eps,                                     NUM_ROUND_DECIMALS)
    if stock_data.trailing_eps                                    != None: stock_data.trailing_eps                                    = round(stock_data.trailing_eps,                                    NUM_ROUND_DECIMALS)
    if stock_data.previous_close                                  != None: stock_data.previous_close                                  = round(stock_data.previous_close,                                  NUM_ROUND_DECIMALS)
    if stock_data.trailing_eps_percentage                         != None: stock_data.trailing_eps_percentage                         = round(stock_data.trailing_eps_percentage,                         NUM_ROUND_DECIMALS)
    if stock_data.price_to_book                                   != None: stock_data.price_to_book                                   = round(stock_data.price_to_book,                                   NUM_ROUND_DECIMALS)
    if stock_data.shares_outstanding                              != None: stock_data.shares_outstanding                              = round(stock_data.shares_outstanding,                              NUM_ROUND_DECIMALS)
    if stock_data.net_income_to_common_shareholders               != None: stock_data.net_income_to_common_shareholders               = round(stock_data.net_income_to_common_shareholders,               NUM_ROUND_DECIMALS)
    if stock_data.nitcsh_to_shares_outstanding                    != None: stock_data.nitcsh_to_shares_outstanding                    = round(stock_data.nitcsh_to_shares_outstanding,                    NUM_ROUND_DECIMALS)
    if stock_data.employees                                       != None: stock_data.employees                                       = int(  stock_data.employees                                                          )
    if stock_data.enterprise_value                                != None: stock_data.enterprise_value                                = int(  stock_data.enterprise_value                                                   )
    if stock_data.market_cap                                      != None: stock_data.market_cap                                      = int(  stock_data.market_cap                                                         )
    if stock_data.nitcsh_to_num_employees                         != None: stock_data.nitcsh_to_num_employees                         = round(stock_data.nitcsh_to_num_employees,                         NUM_ROUND_DECIMALS)
    if stock_data.eqg                                             != None: stock_data.eqg                                             = round(stock_data.eqg,                                             NUM_ROUND_DECIMALS)
    if stock_data.eqg_yoy                                         != None: stock_data.eqg_yoy                                         = round(stock_data.eqg_yoy,                                         NUM_ROUND_DECIMALS)
    if stock_data.niqg_yoy                                        != None: stock_data.niqg_yoy                                        = round(stock_data.niqg_yoy,                                        NUM_ROUND_DECIMALS)
    if stock_data.eqg_effective                                   != None: stock_data.eqg_effective                                   = round(stock_data.eqg_effective,                                   NUM_ROUND_DECIMALS)
    if stock_data.eqg_factor_effective                            != None: stock_data.eqg_factor_effective                            = round(stock_data.eqg_factor_effective,                            NUM_ROUND_DECIMALS)
    if stock_data.revenue_quarterly_growth                        != None: stock_data.revenue_quarterly_growth                        = round(stock_data.revenue_quarterly_growth,                        NUM_ROUND_DECIMALS)
    if stock_data.price_to_earnings_to_growth_ratio               != None: stock_data.price_to_earnings_to_growth_ratio               = round(stock_data.price_to_earnings_to_growth_ratio,               NUM_ROUND_DECIMALS)
    if stock_data.effective_peg_ratio                             != None: stock_data.effective_peg_ratio                             = round(stock_data.effective_peg_ratio,                             NUM_ROUND_DECIMALS)
    if stock_data.annualized_cash_flow_from_operating_activities  != None: stock_data.annualized_cash_flow_from_operating_activities  = round(stock_data.annualized_cash_flow_from_operating_activities,  NUM_ROUND_DECIMALS)
    if stock_data.quarterized_cash_flow_from_operating_activities != None: stock_data.quarterized_cash_flow_from_operating_activities = round(stock_data.quarterized_cash_flow_from_operating_activities, NUM_ROUND_DECIMALS)
    if stock_data.annualized_ev_to_cfo_ratio                      != None: stock_data.annualized_ev_to_cfo_ratio                      = round(stock_data.annualized_ev_to_cfo_ratio,                      NUM_ROUND_DECIMALS)
    if stock_data.quarterized_ev_to_cfo_ratio                     != None: stock_data.quarterized_ev_to_cfo_ratio                     = round(stock_data.quarterized_ev_to_cfo_ratio,                     NUM_ROUND_DECIMALS)
    if stock_data.ev_to_cfo_ratio_effective                       != None: stock_data.ev_to_cfo_ratio_effective                       = round(stock_data.ev_to_cfo_ratio_effective,                       NUM_ROUND_DECIMALS)
    if stock_data.annualized_debt_to_equity                       != None: stock_data.annualized_debt_to_equity                       = round(stock_data.annualized_debt_to_equity,                       NUM_ROUND_DECIMALS)
    if stock_data.quarterized_debt_to_equity                      != None: stock_data.quarterized_debt_to_equity                      = round(stock_data.quarterized_debt_to_equity,                      NUM_ROUND_DECIMALS)
    if stock_data.debt_to_equity_effective                        != None: stock_data.debt_to_equity_effective                        = round(stock_data.debt_to_equity_effective,                        NUM_ROUND_DECIMALS)
    if stock_data.conversion_rate_mult_to_usd                     != None: stock_data.conversion_rate_mult_to_usd                     = round(stock_data.conversion_rate_mult_to_usd,                     NUM_ROUND_DECIMALS)
    if stock_data.last_dividend_0                                 != None: stock_data.last_dividend_0                                 = round(stock_data.last_dividend_0,                                 NUM_ROUND_DECIMALS)
    if stock_data.last_dividend_1                                 != None: stock_data.last_dividend_1                                 = round(stock_data.last_dividend_1,                                 NUM_ROUND_DECIMALS)
    if stock_data.last_dividend_2                                 != None: stock_data.last_dividend_2                                 = round(stock_data.last_dividend_2,                                 NUM_ROUND_DECIMALS)
    if stock_data.last_dividend_3                                 != None: stock_data.last_dividend_3                                 = round(stock_data.last_dividend_3,                                 NUM_ROUND_DECIMALS)
    if stock_data.fifty_two_week_change                           != None: stock_data.fifty_two_week_change                           = round(stock_data.fifty_two_week_change,                           NUM_ROUND_DECIMALS)
    if stock_data.fifty_two_week_low                              != None: stock_data.fifty_two_week_low                              = round(stock_data.fifty_two_week_low,                              NUM_ROUND_DECIMALS)
    if stock_data.fifty_two_week_high                             != None: stock_data.fifty_two_week_high                             = round(stock_data.fifty_two_week_high,                             NUM_ROUND_DECIMALS)
    if stock_data.two_hundred_day_average                         != None: stock_data.two_hundred_day_average                         = round(stock_data.two_hundred_day_average,                         NUM_ROUND_DECIMALS)
    if stock_data.previous_close_percentage_from_200d_ma          != None: stock_data.previous_close_percentage_from_200d_ma          = round(stock_data.previous_close_percentage_from_200d_ma,          NUM_ROUND_DECIMALS)
    if stock_data.previous_close_percentage_from_52w_low          != None: stock_data.previous_close_percentage_from_52w_low          = round(stock_data.previous_close_percentage_from_52w_low,          NUM_ROUND_DECIMALS)
    if stock_data.previous_close_percentage_from_52w_high         != None: stock_data.previous_close_percentage_from_52w_high         = round(stock_data.previous_close_percentage_from_52w_high,         NUM_ROUND_DECIMALS)
    if stock_data.dist_from_low_factor                            != None: stock_data.dist_from_low_factor                            = round(stock_data.dist_from_low_factor,                            NUM_ROUND_DECIMALS)
    if stock_data.eff_dist_from_low_factor                        != None: stock_data.eff_dist_from_low_factor                        = round(stock_data.eff_dist_from_low_factor,                        NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_ratio                          != None: stock_data.annualized_total_ratio                          = round(stock_data.annualized_total_ratio,                          NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_ratio                         != None: stock_data.quarterized_total_ratio                         = round(stock_data.quarterized_total_ratio,                         NUM_ROUND_DECIMALS)
    if stock_data.annualized_other_current_ratio                  != None: stock_data.annualized_other_current_ratio                  = round(stock_data.annualized_other_current_ratio,                  NUM_ROUND_DECIMALS)
    if stock_data.quarterized_other_current_ratio                 != None: stock_data.quarterized_other_current_ratio                 = round(stock_data.quarterized_other_current_ratio,                 NUM_ROUND_DECIMALS)
    if stock_data.annualized_other_ratio                          != None: stock_data.annualized_other_ratio                          = round(stock_data.annualized_other_ratio,                          NUM_ROUND_DECIMALS)
    if stock_data.quarterized_other_ratio                         != None: stock_data.quarterized_other_ratio                         = round(stock_data.quarterized_other_ratio,                         NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_current_ratio                  != None: stock_data.annualized_total_current_ratio                  = round(stock_data.annualized_total_current_ratio,                  NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_current_ratio                 != None: stock_data.quarterized_total_current_ratio                 = round(stock_data.quarterized_total_current_ratio,                 NUM_ROUND_DECIMALS)
    if stock_data.total_ratio_effective                           != None: stock_data.total_ratio_effective                           = round(stock_data.total_ratio_effective,                           NUM_ROUND_DECIMALS)
    if stock_data.other_current_ratio_effective                   != None: stock_data.other_current_ratio_effective                   = round(stock_data.other_current_ratio_effective,                   NUM_ROUND_DECIMALS)
    if stock_data.other_ratio_effective                           != None: stock_data.other_ratio_effective                           = round(stock_data.other_ratio_effective,                           NUM_ROUND_DECIMALS)
    if stock_data.total_current_ratio_effective                   != None: stock_data.total_current_ratio_effective                   = round(stock_data.total_current_ratio_effective,                   NUM_ROUND_DECIMALS)

    # TODO: ASAFR: Unify below with above to single line for each parameter
    if stock_data.sss_value                                       is None: stock_data.sss_value                                       = BAD_SSS
    if stock_data.annualized_revenue                              is None: stock_data.annualized_revenue                              = 0
    if stock_data.annualized_earnings                             is None: stock_data.annualized_earnings                             = 0
    if stock_data.quarterized_revenue                             is None: stock_data.quarterized_revenue                             = 0
    if stock_data.quarterized_earnings                            is None: stock_data.quarterized_earnings                            = 0
    if stock_data.effective_earnings                              is None: stock_data.effective_earnings                              = 0
    if stock_data.effective_revenue                               is None: stock_data.effective_revenue                               = 0
    if stock_data.annualized_total_revenue                        is None: stock_data.annualized_total_revenue                        = 0
    if stock_data.annualized_net_income                           is None: stock_data.annualized_net_income                           = 0
    if stock_data.quarterized_total_revenue                       is None: stock_data.quarterized_total_revenue                       = 0
    if stock_data.quarterized_net_income                          is None: stock_data.quarterized_net_income                          = 0
    if stock_data.effective_net_income                            is None: stock_data.effective_net_income                            = 0
    if stock_data.effective_total_revenue                         is None: stock_data.effective_total_revenue                         = 0
    if stock_data.enterprise_value_to_revenue                     is None: stock_data.enterprise_value_to_revenue                     = 0
    if stock_data.evr_effective                                   is None: stock_data.evr_effective                                   = 0
    if stock_data.trailing_price_to_earnings                      is None: stock_data.trailing_price_to_earnings                      = 0
    if stock_data.forward_price_to_earnings                       is None: stock_data.forward_price_to_earnings                       = 0
    if stock_data.effective_price_to_earnings                     is None: stock_data.effective_price_to_earnings                     = 0
    if stock_data.trailing_12months_price_to_sales                is None: stock_data.trailing_12months_price_to_sales                = 0
    if stock_data.pe_effective                                    is None: stock_data.pe_effective                                    = 0
    if stock_data.enterprise_value_to_ebitda                      is None: stock_data.enterprise_value_to_ebitda                      = 0
    if stock_data.profit_margin                                   is None: stock_data.profit_margin                                   = 0
    if stock_data.annualized_profit_margin                        is None: stock_data.annualized_profit_margin                        = 0
    if stock_data.annualized_profit_margin_boost                  is None: stock_data.annualized_profit_margin_boost                  = 0
    if stock_data.quarterized_profit_margin                       is None: stock_data.quarterized_profit_margin                       = 0
    if stock_data.quarterized_profit_margin_boost                 is None: stock_data.quarterized_profit_margin_boost                 = 0
    if stock_data.effective_profit_margin                         is None: stock_data.effective_profit_margin                         = 0
    if stock_data.held_percent_institutions                       is None: stock_data.held_percent_institutions                       = 0
    if stock_data.forward_eps                                     is None: stock_data.forward_eps                                     = 0
    if stock_data.trailing_eps                                    is None: stock_data.trailing_eps                                    = 0
    if stock_data.previous_close                                  is None: stock_data.previous_close                                  = 0
    if stock_data.trailing_eps_percentage                         is None: stock_data.trailing_eps_percentage                         = 0
    if stock_data.price_to_book                                   is None: stock_data.price_to_book                                   = 0
    if stock_data.shares_outstanding                              is None: stock_data.shares_outstanding                              = 0
    if stock_data.net_income_to_common_shareholders               is None: stock_data.net_income_to_common_shareholders               = 0
    if stock_data.nitcsh_to_shares_outstanding                    is None: stock_data.nitcsh_to_shares_outstanding                    = 0
    if stock_data.employees                                       is None: stock_data.employees                                       = 0
    if stock_data.enterprise_value                                is None: stock_data.enterprise_value                                = 0
    if stock_data.market_cap                                      is None: stock_data.market_cap                                      = 0
    if stock_data.nitcsh_to_num_employees                         is None: stock_data.nitcsh_to_num_employees                         = 0
    if stock_data.eqg                                             is None: stock_data.eqg                                             = 0
    if stock_data.eqg_yoy                                         is None: stock_data.eqg_yoy                                         = 0
    if stock_data.niqg_yoy                                        is None: stock_data.niqg_yoy                                        = 0
    if stock_data.eqg_effective                                   is None: stock_data.eqg_effective                                   = 0
    if stock_data.eqg_factor_effective                            is None: stock_data.eqg_factor_effective                            = 0
    if stock_data.revenue_quarterly_growth                        is None: stock_data.revenue_quarterly_growth                        = 0
    if stock_data.price_to_earnings_to_growth_ratio               is None: stock_data.price_to_earnings_to_growth_ratio               = 0
    if stock_data.effective_peg_ratio                             is None: stock_data.effective_peg_ratio                             = 0
    if stock_data.annualized_cash_flow_from_operating_activities  is None: stock_data.annualized_cash_flow_from_operating_activities  = 0
    if stock_data.quarterized_cash_flow_from_operating_activities is None: stock_data.quarterized_cash_flow_from_operating_activities = 0
    if stock_data.annualized_ev_to_cfo_ratio                      is None: stock_data.annualized_ev_to_cfo_ratio                      = 0
    if stock_data.quarterized_ev_to_cfo_ratio                     is None: stock_data.quarterized_ev_to_cfo_ratio                     = 0
    if stock_data.ev_to_cfo_ratio_effective                       is None: stock_data.ev_to_cfo_ratio_effective                       = 0
    if stock_data.annualized_debt_to_equity                       is None: stock_data.annualized_debt_to_equity                       = 0
    if stock_data.quarterized_debt_to_equity                      is None: stock_data.quarterized_debt_to_equity                      = 0
    if stock_data.debt_to_equity_effective                        is None: stock_data.debt_to_equity_effective                        = 0
    if stock_data.conversion_rate_mult_to_usd                     is None: stock_data.conversion_rate_mult_to_usd                     = 0
    if stock_data.last_dividend_0                                 is None: stock_data.last_dividend_0                                 = 0
    if stock_data.last_dividend_1                                 is None: stock_data.last_dividend_1                                 = 0
    if stock_data.last_dividend_2                                 is None: stock_data.last_dividend_2                                 = 0
    if stock_data.last_dividend_3                                 is None: stock_data.last_dividend_3                                 = 0
    if stock_data.fifty_two_week_change                           is None: stock_data.fifty_two_week_change                           = 0
    if stock_data.fifty_two_week_low                              is None: stock_data.fifty_two_week_low                              = 0
    if stock_data.fifty_two_week_high                             is None: stock_data.fifty_two_week_high                             = 0
    if stock_data.two_hundred_day_average                         is None: stock_data.two_hundred_day_average                         = 0
    if stock_data.previous_close_percentage_from_200d_ma          is None: stock_data.previous_close_percentage_from_200d_ma          = 0
    if stock_data.previous_close_percentage_from_52w_low          is None: stock_data.previous_close_percentage_from_52w_low          = 0
    if stock_data.previous_close_percentage_from_52w_high         is None: stock_data.previous_close_percentage_from_52w_high         = 0
    if stock_data.dist_from_low_factor                            is None: stock_data.dist_from_low_factor                            = 0
    if stock_data.eff_dist_from_low_factor                        is None: stock_data.eff_dist_from_low_factor                        = 0
    if stock_data.annualized_total_ratio                          is None: stock_data.annualized_total_ratio                          = 0
    if stock_data.quarterized_total_ratio                         is None: stock_data.quarterized_total_ratio                         = 0
    if stock_data.annualized_other_current_ratio                  is None: stock_data.annualized_other_current_ratio                  = 0
    if stock_data.quarterized_other_current_ratio                 is None: stock_data.quarterized_other_current_ratio                 = 0
    if stock_data.annualized_other_ratio                          is None: stock_data.annualized_other_ratio                          = 0
    if stock_data.quarterized_other_ratio                         is None: stock_data.quarterized_other_ratio                         = 0
    if stock_data.annualized_total_current_ratio                  is None: stock_data.annualized_total_current_ratio                  = 0
    if stock_data.quarterized_total_current_ratio                 is None: stock_data.quarterized_total_current_ratio                 = 0
    if stock_data.total_ratio_effective                           is None: stock_data.total_ratio_effective                           = 0
    if stock_data.other_current_ratio_effective                   is None: stock_data.other_current_ratio_effective                   = 0
    if stock_data.other_ratio_effective                           is None: stock_data.other_ratio_effective                           = 0
    if stock_data.total_current_ratio_effective                   is None: stock_data.total_current_ratio_effective                   = 0


def process_info(symbol, stock_data, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db):
    try:
        return_value = True
        info               = {}
        earnings_quarterly = {}
        earnings_yearly    = {}
        stock_information  = {}
        if build_csv_db:
            try:
                info                                   = symbol.get_info()
                cash_flows_yearly                             = symbol.get_cashflow(     as_dict=True, freq="yearly")
                cash_flows_quarterly                   = symbol.get_cashflow(     as_dict=True, freq="quarterly")
                balance_sheets_yearly                  = symbol.get_balance_sheet(as_dict=True, freq="yearly")
                balance_sheets_quarterly               = symbol.get_balance_sheet(as_dict=True, freq="quarterly")
                earnings_yearly                        = symbol.get_earnings(     as_dict=True, freq="yearly")
                earnings_quarterly                     = symbol.get_earnings(     as_dict=True, freq="quarterly")
                stock_data.financial_currency          = earnings_yearly['financialCurrency']
                if currency_conversion_tool:
                    stock_data.conversion_rate_mult_to_usd = round(1.0/currency_conversion_tool[stock_data.financial_currency], NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
                elif currency_conversion_tool_alternative:
                    try:
                        stock_data.conversion_rate_mult_to_usd = round(currency_conversion_tool_alternative.convert(1.0, stock_data.financial_currency, 'USD'), NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
                    except Exception as e:
                        stock_data.conversion_rate_mult_to_usd = round(1.0 / currency_conversion_tool_manual[stock_data.financial_currency], NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
                else:
                    stock_data.conversion_rate_mult_to_usd = round(1.0 / currency_conversion_tool_manual[stock_data.financial_currency], NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
                financials_yearly                           = symbol.get_financials(as_dict=True, freq="yearly")
                financials_quarterly                        = symbol.get_financials(as_dict=True, freq="quarterly")
                # institutional_holders                = symbol.get_institutional_holders(as_dict=True)
                # sustainability                       = symbol.get_sustainability(as_dict=True)
                # major_holders                        = symbol.get_major_holders(as_dict=True)
                # mutualfund_holders                   = symbol.get_mutualfund_holders(as_dict=True)
            except Exception as e:
                if not research_mode: print("              Exception in {} symbol.get_info(): {}".format(stock_data.symbol, e))
                pass

            if use_investpy:
                try:
                    if tase_mode:
                        stock_information = investpy.get_stock_information(stock=stock_data.symbol.replace('.TA',''), country='israel', as_json=True)
                    else:
                        stock_information = investpy.get_stock_information(stock=stock_data.symbol, country='united states', as_json=True)
                except Exception as e:
                    if not research_mode: print("              Exception in {} get_stock_information(): {}".format(stock_data.symbol, e))
                    pass

            if 'shortName' in info: stock_data.short_name = info['shortName']
            else:                   stock_data.short_name = 'None'

            total_ratios_list         = []
            try:
                for key in reversed(list(balance_sheets_yearly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Total Liab' in balance_sheets_yearly[key] and not math.isnan(balance_sheets_yearly[key]['Total Liab']) and 'Total Assets' in balance_sheets_yearly[key] and not math.isnan(balance_sheets_yearly[key]['Total Assets']):
                        total_ratios_list.append((balance_sheets_yearly[key]['Total Assets']/balance_sheets_yearly[key]['Total Liab']))
            except Exception as e:
                print("Exception in {} annualized_total_ratio: {}".format(stock_data.symbol, e))
                stock_data.annualized_total_ratio              = 0
                pass
            if len(total_ratios_list): stock_data.annualized_total_ratio = weighted_average(total_ratios_list, BALANCE_SHEETS_WEIGHTS[:len(total_ratios_list)])

            other_current_ratios_list = []
            try:
                for key in reversed(list(balance_sheets_yearly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Other Current Liab' in balance_sheets_yearly[key] and not math.isnan(balance_sheets_yearly[key]['Other Current Liab']) and 'Other Current Assets' in balance_sheets_yearly[key] and not math.isnan(balance_sheets_yearly[key]['Other Current Assets']):
                        other_current_ratios_list.append((balance_sheets_yearly[key]['Other Current Assets']/balance_sheets_yearly[key]['Other Current Liab']))
            except Exception as e:
                print("Exception in {} annualized_other_current_ratio: {}".format(stock_data.symbol, e))
                stock_data.annualized_other_current_ratio       = 0
                pass
            if len(other_current_ratios_list): stock_data.annualized_other_current_ratio = weighted_average(other_current_ratios_list, BALANCE_SHEETS_WEIGHTS[:len(other_current_ratios_list)])

            other_ratios_list         = []
            try:
                for key in reversed(list(balance_sheets_yearly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Other Liab' in balance_sheets_yearly[key] and not math.isnan(balance_sheets_yearly[key]['Other Liab']) and 'Other Assets' in balance_sheets_yearly[key] and not math.isnan(balance_sheets_yearly[key]['Other Assets']):
                        other_ratios_list.append((balance_sheets_yearly[key]['Other Assets']/balance_sheets_yearly[key]['Other Liab']))
            except Exception as e:
                print("Exception in {} annualized_other_ratio: {}".format(stock_data.symbol, e))
                stock_data.annualized_other_ratio              = 0
                pass
            if len(other_ratios_list): stock_data.annualized_other_ratio = weighted_average(other_ratios_list, BALANCE_SHEETS_WEIGHTS[:len(other_ratios_list)])

            total_current_ratios_list         = []
            try:
                for key in reversed(list(balance_sheets_yearly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Total Current Liabilities' in balance_sheets_yearly[key] and not math.isnan(balance_sheets_yearly[key]['Total Current Liabilities']) and 'Total Current Assets' in balance_sheets_yearly[key] and not math.isnan(balance_sheets_yearly[key]['Total Current Assets']):
                        total_current_ratios_list.append((balance_sheets_yearly[key]['Total Current Assets']/balance_sheets_yearly[key]['Total Current Liabilities']))
            except Exception as e:
                print("Exception in {} annualized_total_current_ratio: {}".format(stock_data.symbol, e))
                stock_data.annualized_total_current_ratio              = 0
                pass
            if len(total_current_ratios_list): stock_data.annualized_total_current_ratio = weighted_average(total_current_ratios_list, BALANCE_SHEETS_WEIGHTS[:len(total_current_ratios_list)])


            total_ratios_list         = []
            try:
                for key in reversed(list(balance_sheets_quarterly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Total Liab' in balance_sheets_quarterly[key] and not math.isnan(balance_sheets_quarterly[key]['Total Liab']) and 'Total Assets' in balance_sheets_quarterly[key] and not math.isnan(balance_sheets_quarterly[key]['Total Assets']):
                        total_ratios_list.append((balance_sheets_quarterly[key]['Total Assets']/balance_sheets_quarterly[key]['Total Liab']))
            except Exception as e:
                print("Exception in {} quarterized_total_ratio: {}".format(stock_data.symbol, e))
                stock_data.quarterized_total_ratio              = 0
                pass
            if len(total_ratios_list): stock_data.quarterized_total_ratio = weighted_average(total_ratios_list, BALANCE_SHEETS_WEIGHTS[:len(total_ratios_list)])

            other_current_ratios_list = []
            try:
                for key in reversed(list(balance_sheets_quarterly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Other Current Liab' in balance_sheets_quarterly[key] and not math.isnan(balance_sheets_quarterly[key]['Other Current Liab']) and 'Other Current Assets' in balance_sheets_quarterly[key] and not math.isnan(balance_sheets_quarterly[key]['Other Current Assets']):
                        other_current_ratios_list.append((balance_sheets_quarterly[key]['Other Current Assets']/balance_sheets_quarterly[key]['Other Current Liab']))
            except Exception as e:
                print("Exception in {} quarterized_other_current_ratio: {}".format(stock_data.symbol, e))
                stock_data.quarterized_other_current_ratio       = 0
                pass
            if len(other_current_ratios_list): stock_data.quarterized_other_current_ratio = weighted_average(other_current_ratios_list, BALANCE_SHEETS_WEIGHTS[:len(other_current_ratios_list)])

            other_ratios_list         = []
            try:
                for key in reversed(list(balance_sheets_quarterly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Other Liab' in balance_sheets_quarterly[key] and not math.isnan(balance_sheets_quarterly[key]['Other Liab']) and 'Other Assets' in balance_sheets_quarterly[key] and not math.isnan(balance_sheets_quarterly[key]['Other Assets']):
                        other_ratios_list.append((balance_sheets_quarterly[key]['Other Assets']/balance_sheets_quarterly[key]['Other Liab']))
            except Exception as e:
                print("Exception in {} quarterized_other_ratio: {}".format(stock_data.symbol, e))
                stock_data.quarterized_other_ratio              = 0
                pass
            if len(other_ratios_list): stock_data.quarterized_other_ratio = weighted_average(other_ratios_list, BALANCE_SHEETS_WEIGHTS[:len(other_ratios_list)])

            total_current_ratios_list         = []
            try:
                for key in reversed(list(balance_sheets_quarterly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Total Current Liabilities' in balance_sheets_quarterly[key] and not math.isnan(balance_sheets_quarterly[key]['Total Current Liabilities']) and 'Total Current Assets' in balance_sheets_quarterly[key] and not math.isnan(balance_sheets_quarterly[key]['Total Current Assets']):
                        total_current_ratios_list.append((balance_sheets_quarterly[key]['Total Current Assets']/balance_sheets_quarterly[key]['Total Current Liabilities']))
            except Exception as e:
                print("Exception in {} quarterized_total_current_ratio: {}".format(stock_data.symbol, e))
                stock_data.quarterized_total_current_ratio              = 0
                pass
            if len(total_current_ratios_list): stock_data.quarterized_total_current_ratio = weighted_average(total_current_ratios_list, BALANCE_SHEETS_WEIGHTS[:len(total_current_ratios_list)])

            if stock_data.annualized_total_ratio          == 0.0: stock_data.annualized_total_ratio          = stock_data.quarterized_total_ratio        *QUARTERLY_YEARLY_MISSING_FACTOR
            if stock_data.quarterized_total_ratio         == 0.0: stock_data.quarterized_total_ratio         = stock_data.annualized_total_ratio         *QUARTERLY_YEARLY_MISSING_FACTOR
            if stock_data.annualized_other_current_ratio  == 0.0: stock_data.annualized_other_current_ratio  = stock_data.quarterized_other_current_ratio*QUARTERLY_YEARLY_MISSING_FACTOR
            if stock_data.quarterized_other_current_ratio == 0.0: stock_data.quarterized_other_current_ratio = stock_data.annualized_other_current_ratio *QUARTERLY_YEARLY_MISSING_FACTOR
            if stock_data.annualized_other_ratio          == 0.0: stock_data.annualized_other_ratio          = stock_data.quarterized_other_ratio        *QUARTERLY_YEARLY_MISSING_FACTOR
            if stock_data.quarterized_other_ratio         == 0.0: stock_data.quarterized_other_ratio         = stock_data.annualized_other_ratio         *QUARTERLY_YEARLY_MISSING_FACTOR
            if stock_data.annualized_total_current_ratio  == 0.0: stock_data.annualized_total_current_ratio  = stock_data.quarterized_total_current_ratio*QUARTERLY_YEARLY_MISSING_FACTOR
            if stock_data.quarterized_total_current_ratio == 0.0: stock_data.quarterized_total_current_ratio = stock_data.annualized_total_current_ratio *QUARTERLY_YEARLY_MISSING_FACTOR

            # TODO: ASAFR: In the next stage - add the other current and other ratio to a sum of the ratios Investigate prior
            stock_data.total_ratio_effective         = RATIO_DAMPER+(stock_data.annualized_total_ratio         + stock_data.quarterized_total_ratio        )/2.0
            stock_data.other_current_ratio_effective = RATIO_DAMPER+(stock_data.annualized_other_current_ratio + stock_data.quarterized_other_current_ratio)/2.0
            stock_data.other_ratio_effective         = RATIO_DAMPER+(stock_data.annualized_other_ratio         + stock_data.quarterized_other_ratio        )/2.0
            stock_data.total_current_ratio_effective = RATIO_DAMPER+(stock_data.annualized_total_current_ratio + stock_data.quarterized_total_current_ratio)/2.0

            total_debt_to_equity_list     = []
            try:
                for key in reversed(list(balance_sheets_yearly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Total Liab' in balance_sheets_yearly[key] and not math.isnan(balance_sheets_yearly[key]['Total Liab']) and 'Total Stockholder Equity' in balance_sheets_yearly[key] and not math.isnan(balance_sheets_yearly[key]['Total Stockholder Equity']):
                        total_debt_to_equity_list.append(balance_sheets_yearly[key]['Total Liab']/balance_sheets_yearly[key]['Total Stockholder Equity'])
            except Exception as e:
                print("Exception in {} annualized_debt_to_equity: {}".format(stock_data.symbol, e))
                stock_data.annualized_debt_to_equity           = None
                pass
            if len(total_debt_to_equity_list): stock_data.annualized_debt_to_equity = weighted_average(total_debt_to_equity_list, BALANCE_SHEETS_WEIGHTS[:len(total_debt_to_equity_list)])
            else:                              stock_data.annualized_debt_to_equity = None

            # TODO: ASAFR: Add Other Current Liab / Other Stockholder Equity
            total_debt_to_equity_list     = []
            try:
                for key in reversed(list(balance_sheets_quarterly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Total Liab' in balance_sheets_quarterly[key] and not math.isnan(balance_sheets_quarterly[key]['Total Liab']) and 'Total Stockholder Equity' in balance_sheets_quarterly[key] and not math.isnan(balance_sheets_quarterly[key]['Total Stockholder Equity']):
                        total_debt_to_equity_list.append(balance_sheets_quarterly[key]['Total Liab']/balance_sheets_quarterly[key]['Total Stockholder Equity'])
            except Exception as e:
                print("Exception in {} quarterized_debt_to_equity: {}".format(stock_data.symbol, e))
                stock_data.quarterized_debt_to_equity = None
                pass
            if len(total_debt_to_equity_list): stock_data.quarterized_debt_to_equity = weighted_average(total_debt_to_equity_list, BALANCE_SHEETS_WEIGHTS[:len(total_debt_to_equity_list)])
            else:                              stock_data.quarterized_debt_to_equity = None

            if stock_data.annualized_debt_to_equity is None and stock_data.quarterized_debt_to_equity is None:
                stock_data.annualized_debt_to_equity = stock_data.quarterized_debt_to_equity = 1000.0*debt_to_equity_limit
            else:
                if   stock_data.annualized_debt_to_equity is None and stock_data.quarterized_debt_to_equity != None:
                    stock_data.annualized_debt_to_equity = stock_data.quarterized_debt_to_equity*QUARTERLY_YEARLY_MISSING_FACTOR
                elif stock_data.annualized_debt_to_equity != None and stock_data.quarterized_debt_to_equity is None:
                    stock_data.quarterized_debt_to_equity = stock_data.annualized_debt_to_equity * QUARTERLY_YEARLY_MISSING_FACTOR

                # A mixed sign (one negative, the other positive) quarterized and annualized values cannot simply be averaged, because the may lead to a low D/E value
                if stock_data.annualized_debt_to_equity > 0.0 and stock_data.quarterized_debt_to_equity > 0.0 or stock_data.annualized_debt_to_equity < 0.0 and stock_data.quarterized_debt_to_equity < 0.0:
                    stock_data.debt_to_equity_effective = (stock_data.annualized_debt_to_equity+stock_data.quarterized_debt_to_equity)/2.0
                elif stock_data.annualized_debt_to_equity > 0.0 and stock_data.quarterized_debt_to_equity < 0.0:
                    stock_data.debt_to_equity_effective = (                                stock_data.annualized_debt_to_equity - NEGATIVE_DEBT_TO_EQUITY_FACTOR*stock_data.quarterized_debt_to_equity)**2
                else:
                    stock_data.debt_to_equity_effective = (-NEGATIVE_DEBT_TO_EQUITY_FACTOR*stock_data.annualized_debt_to_equity +                                stock_data.quarterized_debt_to_equity)**2

                if stock_data.debt_to_equity_effective < 0.0:
                    stock_data.debt_to_equity_effective = (1.0-stock_data.debt_to_equity_effective * NEGATIVE_DEBT_TO_EQUITY_FACTOR)  # (https://www.investopedia.com/terms/d/debtequityratio.asp#:~:text=What%20does%20it%20mean%20for,has%20more%20liabilities%20than%20assets.) What does it mean for debt to equity to be negative? If a company has a negative D/E ratio, this means that the company has negative shareholder equity. In other words, it means that the company has more liabilities than assets

            weight_index    = 0
            cash_flows_list = []
            weights_sum     = 0
            try:
                for key in reversed(list(cash_flows_yearly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Total Cash From Operating Activities' in cash_flows_yearly[key] and not math.isnan(cash_flows_yearly[key]['Total Cash From Operating Activities']):
                        cash_flows_list.append(cash_flows_yearly[key]['Total Cash From Operating Activities']*CASH_FLOW_WEIGHTS[weight_index])
                        weights_sum += CASH_FLOW_WEIGHTS[weight_index]
                        weight_index += 1
                if weights_sum > 0: stock_data.annualized_cash_flow_from_operating_activities = stock_data.conversion_rate_mult_to_usd*sum(cash_flows_list) / weights_sum  # Multiplying by the factor to get the valu in USD.
                else:               stock_data.annualized_cash_flow_from_operating_activities = None
            except Exception as e:
                print("Exception in {} cash_flows_yearly: {}".format(stock_data.symbol, e))
                stock_data.annualized_cash_flow_from_operating_activities = None
                pass

            weight_index    = 0
            cash_flows_list = []
            weights_sum     = 0
            try:
                for key in reversed(list(cash_flows_quarterly)):  # The 1st element will be the oldest, receiving the lowest weight
                    if 'Total Cash From Operating Activities' in cash_flows_quarterly[key] and not math.isnan(cash_flows_quarterly[key]['Total Cash From Operating Activities']):
                        cash_flows_list.append(cash_flows_quarterly[key]['Total Cash From Operating Activities']*CASH_FLOW_WEIGHTS[weight_index])
                        weights_sum += CASH_FLOW_WEIGHTS[weight_index]
                        weight_index += 1
                if weights_sum > 0: stock_data.quarterized_cash_flow_from_operating_activities = stock_data.conversion_rate_mult_to_usd*sum(cash_flows_list) / weights_sum  # Multiplying by the factor to get the valu in USD.
                else:               stock_data.quarterized_cash_flow_from_operating_activities = None
            except Exception as e:
                print("Exception in {} cash_flows_quarterly: {}".format(stock_data.symbol, e))
                stock_data.quarterized_cash_flow_from_operating_activities = None
                pass

        if stock_data.short_name is     None:                       stock_data.short_name = 'None'
        if stock_data.short_name != None and not research_mode: print('              {:35}:'.format(stock_data.short_name))

        if build_csv_db and 'quoteType' in info: stock_data.quote_type = info['quoteType']
        if not check_quote_type(stock_data, research_mode):     return_value = False

        if build_csv_db and 'sector'  in info:    stock_data.sector = info['sector']
        if sectors_filter_out:
            if     check_sector(stock_data, sectors_list):    return_value = False
        else:
            if not check_sector(stock_data, sectors_list):    return_value = False

        if build_csv_db and 'country' in info:    stock_data.country = info['country']
        if len(countries_list):
            if countries_filter_out:
                if     check_country(stock_data, countries_list): return_value = False
            else:
                if not check_country(stock_data, countries_list): return_value = False

        if build_csv_db:
            if 'fullTimeEmployees' in info:      stock_data.employees = info['fullTimeEmployees']
            else:                                stock_data.employees = NUM_EMPLOYEES_UNKNOWN
            if stock_data.employees is None: stock_data.employees = NUM_EMPLOYEES_UNKNOWN

            # Oldest is the lower index
            if earnings_yearly != None and 'Revenue' in earnings_yearly and 'Earnings'in earnings_yearly:
                len_revenue_list  = len(earnings_yearly['Revenue'])
                len_earnings_list = len(earnings_yearly['Earnings'])
                if len_earnings_list == len_revenue_list:
                    weight_index              = 0
                    used_weights              = 0
                    earnings_to_revenues_list = []
                    weights_sum               = 0
                    boost_cont_inc_ratio    = True # Will be set to True if there is a continuous increase in the profit margin
                    boost_cont_inc_pos      = True # Will be set to True if there is a continuous positive in the profit margin
                    boost_cont_inc_earnings = True # Will be set to True if there is a continuous increase in the earnings
                    boost_cont_inc_revenue  = True # Will be set to True if there is a continuous increase in the revenue
                    try:
                        for key in earnings_yearly['Revenue']:
                            if float(earnings_yearly['Revenue'][key]) > 0:
                                earnings_to_revenues_list.append((float(earnings_yearly['Earnings'][key])/float(earnings_yearly['Revenue'][key]))*PROFIT_MARGIN_WEIGHTS[weight_index])
                                weights_sum  += PROFIT_MARGIN_WEIGHTS[weight_index]
                                used_weights += 1
                                current_ratio = float(earnings_yearly['Earnings'][key])/float(earnings_yearly['Revenue'][key])
                                if used_weights > 1:
                                    boost_cont_inc_ratio    = True if boost_cont_inc_ratio    and current_ratio                    > last_ratio                    else False
                                    boost_cont_inc_pos      = True if boost_cont_inc_pos      and current_ratio                    > 0          and last_ratio > 0 else False
                                    boost_cont_inc_earnings = True if boost_cont_inc_earnings and float(earnings_yearly['Earnings'][key]) > last_earnings                 else False
                                    boost_cont_inc_revenue  = True if boost_cont_inc_revenue  and float(earnings_yearly['Revenue' ][key]) > last_revenue                  else False
                                last_ratio    = current_ratio
                                last_earnings = float(earnings_yearly['Earnings'][key])
                                last_revenue  = float(earnings_yearly['Revenue' ][key])
                            weight_index += 1
                        if weights_sum > 0:
                            stock_data.annualized_profit_margin        = sum(earnings_to_revenues_list)/weights_sum
                            if stock_data.annualized_profit_margin > 0:
                                stock_data.annualized_profit_margin_boost  = 1.0 if not boost_cont_inc_ratio    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE
                                stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_inc_pos      or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_POSITIVE
                                stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_inc_earnings or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_EARNINGS
                                stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_inc_revenue  or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_REVENUE
                                stock_data.annualized_profit_margin       *= stock_data.annualized_profit_margin_boost
                    except Exception as e:
                        print("Exception in {} annualized_profit_margin: {}".format(stock_data.symbol, e))
                        stock_data.annualized_profit_margin = None
                        pass
            # TODO: ASAFR: This below can be duplicated for usage of total_revenue and net_income. Analyze and implement as/if required:
            if earnings_quarterly != None and 'Revenue' in earnings_quarterly and 'Earnings'in earnings_quarterly:
                len_revenue_list  = len(earnings_quarterly['Revenue'])
                len_earnings_list = len(earnings_quarterly['Earnings'])
                if len_earnings_list == len_revenue_list:
                    weight_index              = 0
                    used_weights              = 0
                    earnings_to_revenues_list = []
                    weights_sum               = 0
                    boost_cont_inc_ratio    = True # Will be set to True if there is a continuous increase in the profit   margin  TODO: ASAFR: Do the same boosting for cash flows ev_to_cfo
                    boost_cont_inc_pos      = True # Will be set to True if there is a continuous positive in the profit   margin
                    boost_cont_inc_earnings = True # Will be set to True if there is a continuous increase in the earnings
                    boost_cont_inc_revenue  = True # Will be set to True if there is a continuous increase in the revenue
                    try:
                        for key in earnings_quarterly['Revenue']:
                            if float(earnings_quarterly['Revenue'][key]) > 0:
                                earnings_to_revenues_list.append((float(earnings_quarterly['Earnings'][key])/float(earnings_quarterly['Revenue'][key]))*PROFIT_MARGIN_WEIGHTS[weight_index])
                                weights_sum  += PROFIT_MARGIN_WEIGHTS[weight_index]
                                used_weights += 1
                                current_ratio = float(earnings_quarterly['Earnings'][key])/float(earnings_quarterly['Revenue'][key])
                                if used_weights > 1:
                                    boost_cont_inc_ratio    = True if boost_cont_inc_ratio    and current_ratio                              > last_ratio                    else False
                                    boost_cont_inc_pos      = True if boost_cont_inc_pos      and current_ratio                              > 0          and last_ratio > 0 else False
                                    boost_cont_inc_earnings = True if boost_cont_inc_earnings and float(earnings_quarterly['Earnings'][key]) > last_earnings                 else False
                                    boost_cont_inc_revenue  = True if boost_cont_inc_revenue  and float(earnings_quarterly['Revenue' ][key]) > last_revenue                  else False
                                last_ratio    = current_ratio
                                last_earnings = float(earnings_quarterly['Earnings'][key])
                                last_revenue  = float(earnings_quarterly['Revenue' ][key])
                            weight_index += 1
                        if weights_sum > 0:
                            stock_data.quarterized_profit_margin            = sum(earnings_to_revenues_list)/weights_sum
                            if stock_data.quarterized_profit_margin > 0:
                                stock_data.quarterized_profit_margin_boost  = 1.0 if not boost_cont_inc_ratio    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE
                                stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_inc_pos      or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_POSITIVE
                                stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_inc_earnings or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_EARNINGS
                                stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_inc_revenue  or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_REVENUE
                                stock_data.quarterized_profit_margin       *= stock_data.quarterized_profit_margin_boost
                    except Exception as e:
                        print("Exception in {} quarterized_profit_margin: {}".format(stock_data.symbol, e))
                        stock_data.quarterized_profit_margin = None
                        pass

            if earnings_yearly != None and 'Revenue' in earnings_yearly:
                weight_index  = 0
                revenues_list = []
                weights_sum   = 0
                for key in earnings_yearly['Revenue']:
                    revenues_list.append((float(earnings_yearly['Revenue'][key])) * REVENUES_WEIGHTS[weight_index])
                    weights_sum += REVENUES_WEIGHTS[weight_index]
                    weight_index += 1
                stock_data.annualized_revenue = stock_data.conversion_rate_mult_to_usd*sum(revenues_list) / weights_sum  # Multiplying by the factor to get the valu in USD.
            else:
                stock_data.annualized_revenue = None

            if financials_yearly != None and len(financials_yearly):
                weight_index  = 0
                weights_sum   = 0
                total_revenue_list               = []
                for key in reversed(list(financials_yearly)):  # 1st will be oldest - TODO: ASAFR: verify
                    if 'Total Revenue' in financials_yearly[key]:
                        total_revenue_list.append(float(financials_yearly[key]['Total Revenue']) * REVENUES_WEIGHTS[weight_index])
                        weights_sum  += REVENUES_WEIGHTS[weight_index]
                        weight_index += 1
                        # TODO: ASAFR: Add a calculation of net_income_to_total_revenue_list
                if len(total_revenue_list):
                    stock_data.annualized_total_revenue = stock_data.conversion_rate_mult_to_usd * sum(total_revenue_list) / weights_sum  # Multiplying by the factor to get the value in USD.
                else:
                    stock_data.annualized_total_revenue = None

            if earnings_yearly != None and 'Earnings' in earnings_yearly:
                weight_index      = 0
                earnings_list     = []
                qeg_list          = []
                weights_sum       = 0
                qeg_weights_sum   = 0
                previous_earnings = None
                for key in earnings_yearly['Earnings']:
                    earnings_list.append((float(earnings_yearly['Earnings'][key])) * EARNINGS_WEIGHTS[weight_index])
                    weights_sum  += EARNINGS_WEIGHTS[weight_index]
                    if weight_index > 0:
                        current_earnings = earnings_yearly['Earnings'][key]
                        if float(previous_earnings) != 0.0 and float(current_earnings) != 0.0: # (this-prev)/(abs(this)+abs(prev))
                            value_to_append = (float(current_earnings)-float(previous_earnings))/(abs(current_earnings)+abs(previous_earnings))
                            qeg_list.append(value_to_append*EARNINGS_WEIGHTS[weight_index-1])
                        else:
                            qeg_list.append(0.0) # No change
                        qeg_weights_sum += EARNINGS_WEIGHTS[weight_index-1]
                    previous_earnings = earnings_yearly['Earnings'][key]
                    weight_index     += 1
                stock_data.annualized_earnings = stock_data.conversion_rate_mult_to_usd*sum(earnings_list) / weights_sum  # Multiplying by the factor to get the valu in USD.
                if len(qeg_list):
                    stock_data.eqg_yoy         =                                        sum(qeg_list)      / qeg_weights_sum
                else:
                    stock_data.eqg_yoy         =                                        None
            else:
                stock_data.eqg_yoy             = None
                stock_data.annualized_earnings = None

            if financials_yearly != None and len(financials_yearly):
                weight_index = 0
                net_income_list = []
                qnig_list = []
                weights_sum = 0
                qnig_weights_sum = 0
                previous_net_income = None
                for key in reversed(list(financials_yearly)):  # 1st will be oldest - TODO: ASAFR: verify
                    if 'Net Income' in financials_yearly[key]:
                        net_income_list.append((float(financials_yearly[key]['Net Income'])) * EARNINGS_WEIGHTS[weight_index])
                        weights_sum += EARNINGS_WEIGHTS[weight_index]
                        if weight_index > 0:
                            current_net_income = financials_yearly[key]['Net Income']
                            if float(previous_net_income) != 0.0 and float(current_net_income) != 0.0:  # (this-prev)/(abs(this)+abs(prev))
                                value_to_append = (float(current_net_income) - float(previous_net_income)) / (abs(current_net_income) + abs(previous_net_income))
                                qnig_list.append(value_to_append * EARNINGS_WEIGHTS[weight_index - 1])
                            else:
                                qnig_list.append(0.0)  # No change
                            qnig_weights_sum += EARNINGS_WEIGHTS[weight_index - 1]
                        previous_net_income = financials_yearly[key]['Net Income']
                        weight_index += 1
                if len(net_income_list):
                    stock_data.annualized_net_income = stock_data.conversion_rate_mult_to_usd * sum(net_income_list) / weights_sum  # Multiplying by the factor to get the valu in USD.
                else:
                    stock_data.annualized_net_income = None
                if len(qnig_list):
                    stock_data.niqg_yoy = sum(qnig_list) / qnig_weights_sum
                else:
                    stock_data.niqg_yoy = None
            else:
                stock_data.niqg_yoy              = None
                stock_data.annualized_net_income = None

            if earnings_quarterly != None and 'Revenue' in earnings_quarterly:
                weight_index  = 0
                revenues_list = []
                weights_sum   = 0
                for key in earnings_quarterly['Revenue']:
                    revenues_list.append((float(earnings_quarterly['Revenue'][key])) * REVENUES_WEIGHTS[weight_index])
                    weights_sum += REVENUES_WEIGHTS[weight_index]
                    weight_index += 1
                stock_data.quarterized_revenue = stock_data.conversion_rate_mult_to_usd*sum(revenues_list) / weights_sum  # Multiplying by the factor to get the valu in USD.
            else:
                stock_data.quarterized_revenue = None

            if financials_quarterly != None and len(financials_quarterly):
                weight_index  = 0
                weights_sum   = 0
                total_revenue_list               = []
                for key in reversed(list(financials_quarterly)):  # 1st will be oldest - TODO: ASAFR: verify
                    if 'Total Revenue' in financials_quarterly[key]:
                        total_revenue_list.append(float(financials_quarterly[key]['Total Revenue']) * REVENUES_WEIGHTS[weight_index])
                        weights_sum  += REVENUES_WEIGHTS[weight_index]
                        weight_index += 1
                        # TODO: ASAFR: Add a calculation of net_income_to_total_revenue_list
                if len(total_revenue_list):
                    stock_data.quarterized_total_revenue = stock_data.conversion_rate_mult_to_usd * sum(total_revenue_list) / weights_sum  # Multiplying by the factor to get the value in USD.
                else:
                    stock_data.quarterized_total_revenue = None
            else:
                stock_data.quarterized_total_revenue = None

            if earnings_quarterly != None and 'Earnings' in earnings_quarterly:
                weight_index  = 0
                earnings_list = []
                weights_sum   = 0
                for key in earnings_quarterly['Earnings']:
                    earnings_list.append((float(earnings_quarterly['Earnings'][key])) * EARNINGS_WEIGHTS[weight_index])
                    weights_sum += EARNINGS_WEIGHTS[weight_index]
                    weight_index += 1
                stock_data.quarterized_earnings = stock_data.conversion_rate_mult_to_usd*sum(earnings_list) / weights_sum  # Multiplying by the factor to get the valu in USD.
            else:
                stock_data.quarterized_earnings = None

            if financials_quarterly != None and len(financials_quarterly):
                weight_index  = 0
                net_income_list = []
                weights_sum   = 0
                for key in reversed(list(financials_quarterly)):  # 1st will be oldest - TODO: ASAFR: verify
                    if 'Net Income' in financials_quarterly[key]:
                        net_income_list.append(float(financials_quarterly[key]['Net Income']) * REVENUES_WEIGHTS[weight_index])
                        weights_sum  += REVENUES_WEIGHTS[weight_index]
                        weight_index += 1
                        # TODO: ASAFR: Add a calculation of net_income_to_total_revenue_list
                if len(net_income_list):
                    stock_data.quarterized_net_income = stock_data.conversion_rate_mult_to_usd * sum(net_income_list) / weights_sum  # Multiplying by the factor to get the value in USD.
                else:
                    stock_data.quarterized_net_income = None
            else:
                stock_data.quarterized_net_income = None

            # At this stage, use the Total Revenue and Net Income as backups for revenues and earnings. TODO: ASAFR: Later on run comparisons and take them into account as well!
            if   stock_data.annualized_net_income  is None and stock_data.quarterized_net_income is None: stock_data.effective_net_income = None
            elif stock_data.annualized_net_income  is None and stock_data.quarterized_net_income != None: stock_data.effective_net_income = stock_data.quarterized_net_income
            elif stock_data.quarterized_net_income is None and stock_data.annualized_net_income  != None: stock_data.effective_net_income = stock_data.annualized_net_income
            else                                                                                        : stock_data.effective_net_income = (stock_data.annualized_net_income+stock_data.quarterized_net_income)/2.0

            if   stock_data.annualized_total_revenue   is None and stock_data.quarterized_total_revenue  is None: stock_data.effective_total_revenue  = None
            elif stock_data.annualized_total_revenue   is None and stock_data.quarterized_total_revenue  != None: stock_data.effective_total_revenue  = stock_data.quarterized_total_revenue
            elif stock_data.quarterized_total_revenue  is None and stock_data.annualized_total_revenue   != None: stock_data.effective_total_revenue  = stock_data.annualized_total_revenue
            else                                                                                                : stock_data.effective_total_revenue  = (stock_data.annualized_total_revenue +stock_data.quarterized_total_revenue )/2.0

            if   stock_data.annualized_earnings  is None: stock_data.annualized_earnings  = stock_data.annualized_net_income
            if   stock_data.quarterized_earnings is None: stock_data.quarterized_earnings = stock_data.quarterized_net_income

            if   stock_data.annualized_earnings  is None and stock_data.quarterized_earnings is None: stock_data.effective_earnings = stock_data.effective_net_income
            elif stock_data.annualized_earnings  is None and stock_data.quarterized_earnings != None: stock_data.effective_earnings = stock_data.quarterized_earnings
            elif stock_data.quarterized_earnings is None and stock_data.annualized_earnings  != None: stock_data.effective_earnings = stock_data.annualized_earnings
            else                                                                                    : stock_data.effective_earnings = (stock_data.annualized_earnings+stock_data.quarterized_earnings)/2.0

            if   stock_data.annualized_revenue   is None: stock_data.annualized_revenue   = stock_data.annualized_total_revenue
            if   stock_data.quarterized_revenue  is None: stock_data.quarterized_revenue  = stock_data.quarterized_total_revenue

            if   stock_data.annualized_revenue   is None and stock_data.quarterized_revenue  is None: stock_data.effective_revenue  = stock_data.effective_total_revenue
            elif stock_data.annualized_revenue   is None and stock_data.quarterized_revenue  != None: stock_data.effective_revenue  = stock_data.quarterized_revenue
            elif stock_data.quarterized_revenue  is None and stock_data.annualized_revenue   != None: stock_data.effective_revenue  = stock_data.annualized_revenue
            else                                                                                    : stock_data.effective_revenue  = (stock_data.annualized_revenue +stock_data.quarterized_revenue )/2.0

            if 'country' in info:                stock_data.country = info['country']
            else:                                stock_data.country = 'Unknown'
            if stock_data.country is None: stock_data.country       = 'Unknown'

            if 'profitMargins' in info:          stock_data.profit_margin = info['profitMargins']
            else:                                stock_data.profit_margin = None

            if 'heldPercentInstitutions' in info:                                                         stock_data.held_percent_institutions = info['heldPercentInstitutions']
            else:                                                                                         stock_data.held_percent_institutions = PERCENT_HELD_INSTITUTIONS_LOW
            if stock_data.held_percent_institutions is None or stock_data.held_percent_institutions == 0: stock_data.held_percent_institutions = PERCENT_HELD_INSTITUTIONS_LOW

            if 'enterpriseToRevenue' in info:                          stock_data.enterprise_value_to_revenue = info['enterpriseToRevenue']  # https://www.investopedia.com/terms/e/ev-revenue-multiple.asp
            else:                                                      stock_data.enterprise_value_to_revenue = None # Mark as None, so as to try and calculate manually. TODO: ASAFR: Do the same to the Price and to the Earnings and the Price/Earnings (Also to sales if possible)
            if isinstance(stock_data.enterprise_value_to_revenue,str): stock_data.enterprise_value_to_revenue = None # Mark as None, so as to try and calculate manually.

            if 'enterpriseToEbitda' in info:                           stock_data.enterprise_value_to_ebitda  = info['enterpriseToEbitda']  # The lower the better: https://www.investopedia.com/ask/answers/072715/what-considered-healthy-evebitda.asp
            else:                                                      stock_data.enterprise_value_to_ebitda  = None
            if isinstance(stock_data.enterprise_value_to_ebitda,str):  stock_data.enterprise_value_to_ebitda  = None

            if 'marketCap' in info and info['marketCap'] != None:
                stock_data.market_cap = info['marketCap'] # For Nasdaq - these values are already in USD, no conversion required
            else:
                stock_data.market_cap = None

            if 'enterpriseValue' in info and info['enterpriseValue'] != None: stock_data.enterprise_value = info['enterpriseValue']  # Value is always in USD, no need to convert
            if market_cap_included:
                if stock_data.enterprise_value is None or stock_data.enterprise_value <= 0:
                    if   'marketCap' in info and info['marketCap'] != None:
                        stock_data.enterprise_value = int(info['marketCap'])
                    elif use_investpy and 'MarketCap' in stock_information and stock_information['MarketCap'] != None:
                        stock_data.enterprise_value = int(text_to_num(stock_information['MarketCap']))
                elif stock_data.market_cap is None or stock_data.market_cap <= 0:
                    stock_data.market_cap = stock_data.enterprise_value

            if 'trailingPE' in info:
                stock_data.trailing_price_to_earnings  = info['trailingPE']  # https://www.investopedia.com/terms/t/trailingpe.asp
                if tase_mode and stock_data.trailing_price_to_earnings != None: stock_data.trailing_price_to_earnings /= 100.0  # In TLV stocks, Yahoo multiplies trailingPE by a factor of 100, so compensate
            elif stock_data.effective_earnings != None and stock_data.effective_earnings != 0:
                stock_data.trailing_price_to_earnings  = stock_data.market_cap / stock_data.effective_earnings # Calculate manually.
            if isinstance(stock_data.trailing_price_to_earnings,str):  stock_data.trailing_price_to_earnings  = None # Mark as None, so as to try and calculate manually.

            if 'forwardPE' in info:
                stock_data.forward_price_to_earnings  = info['forwardPE']  # https://www.investopedia.com/terms/t/trailingpe.asp
                if tase_mode and stock_data.forward_price_to_earnings != None:
                    stock_data.forward_price_to_earnings /= 100.0
            else:  stock_data.forward_price_to_earnings  = None # Mark as None, so as to try and calculate manually. TODO: ASAFR: Calcualte using the forward_eps?

            if   stock_data.trailing_price_to_earnings is None and stock_data.forward_price_to_earnings  is     None: stock_data.effective_price_to_earnings = None
            elif stock_data.forward_price_to_earnings  is None and stock_data.trailing_price_to_earnings != None: stock_data.effective_price_to_earnings = stock_data.trailing_price_to_earnings
            elif stock_data.trailing_price_to_earnings is None and stock_data.forward_price_to_earnings  != None: stock_data.effective_price_to_earnings = stock_data.forward_price_to_earnings
            else:  # mixed sign (one negative, one positive) values of forward and trailing, cannot be simply averaged, as they may yield to a totally wrong result. Need special handling in such cases
                if stock_data.trailing_price_to_earnings > 0.0 and stock_data.forward_price_to_earnings > 0.0 or stock_data.trailing_price_to_earnings < 0.0 and stock_data.forward_price_to_earnings < 0.0:
                    stock_data.effective_price_to_earnings = (stock_data.trailing_price_to_earnings*TRAILING_PRICE_TO_EARNINGS_WEIGHT+stock_data.forward_price_to_earnings*FORWARD_PRICE_TO_EARNINGS_WEIGHT)
                elif stock_data.trailing_price_to_earnings > 0.0 and stock_data.forward_price_to_earnings < 0.0:
                    stock_data.effective_price_to_earnings = (                                   stock_data.trailing_price_to_earnings                                   - NEGATIVE_PRICE_TO_EARNINGS_FACTOR*stock_data.forward_price_to_earnings)**2
                else:
                    stock_data.effective_price_to_earnings = (-NEGATIVE_PRICE_TO_EARNINGS_FACTOR*stock_data.trailing_price_to_earnings*TRAILING_PRICE_TO_EARNINGS_WEIGHT + stock_data.forward_price_to_earnings*FORWARD_PRICE_TO_EARNINGS_WEIGHT )**2

            if 'forwardEps'                                 in info: stock_data.forward_eps                       = info['forwardEps']
            else:                                                    stock_data.forward_eps                       = None
            if isinstance(stock_data.forward_eps,str):               stock_data.forward_eps                       = None

            if 'trailingEps'                                in info: stock_data.trailing_eps                      = info['trailingEps']
            else:                                                    stock_data.trailing_eps                      = None
            if isinstance(stock_data.trailing_eps,str):              stock_data.trailing_eps                      = None

            if 'previousClose'                              in info: stock_data.previous_close                    = info['previousClose']
            else:                                                    stock_data.previous_close                    = None
            if isinstance(stock_data.previous_close,str):            stock_data.previous_close                    = None

            if build_csv_db and '52WeekChange'         in info: stock_data.fifty_two_week_change   = info['52WeekChange']
            if build_csv_db and 'fiftyTwoWeekLow'      in info: stock_data.fifty_two_week_low      = info['fiftyTwoWeekLow']
            if build_csv_db and 'fiftyTwoWeekHigh'     in info: stock_data.fifty_two_week_high     = info['fiftyTwoWeekHigh']
            if build_csv_db and 'twoHundredDayAverage' in info: stock_data.two_hundred_day_average = info['twoHundredDayAverage']

            if build_csv_db and stock_data.fifty_two_week_change                                                            is None: stock_data.fifty_two_week_change   = stock_data.previous_close
            if build_csv_db and stock_data.fifty_two_week_low                                                               is None: stock_data.fifty_two_week_low      = stock_data.previous_close
            if build_csv_db and stock_data.fifty_two_week_high                                                              is None: stock_data.fifty_two_week_high     = stock_data.previous_close
            if build_csv_db and stock_data.two_hundred_day_average                                                          is None: stock_data.two_hundred_day_average = stock_data.previous_close
            if build_csv_db and stock_data.previous_close != None and stock_data.previous_close < stock_data.fifty_two_week_low: stock_data.previous_close          = stock_data.fifty_two_week_low

            if build_csv_db:
                if stock_data.two_hundred_day_average > 0.0: stock_data.previous_close_percentage_from_200d_ma  = 100.0 * ((stock_data.previous_close - stock_data.two_hundred_day_average) / stock_data.two_hundred_day_average)
                if stock_data.fifty_two_week_low      > 0.0: stock_data.previous_close_percentage_from_52w_low  = 100.0 * ((stock_data.previous_close - stock_data.fifty_two_week_low     ) / stock_data.fifty_two_week_low     )
                if stock_data.fifty_two_week_high     > 0.0: stock_data.previous_close_percentage_from_52w_high = 100.0 * ((stock_data.previous_close - stock_data.fifty_two_week_high    ) / stock_data.fifty_two_week_high    )
                if stock_data.fifty_two_week_low      > 0.0 and stock_data.fifty_two_week_high > 0.0 and stock_data.previous_close > 0.0:
                    if stock_data.fifty_two_week_high == stock_data.fifty_two_week_low:
                        stock_data.dist_from_low_factor = 1.0  # When there is no range, leave as neutral
                    else:
                        stock_data.dist_from_low_factor = (stock_data.previous_close - stock_data.fifty_two_week_low)/(0.5*(stock_data.fifty_two_week_high-stock_data.fifty_two_week_low))
                    stock_data.eff_dist_from_low_factor = (DIST_FROM_LOW_FACTOR_DAMPER + stock_data.dist_from_low_factor) if stock_data.dist_from_low_factor < 1.0 else (stock_data.dist_from_low_factor**DIST_FROM_LOW_FACTOR_HIGHER_THAN_ONE_POWER)

            if stock_data.trailing_eps != None and stock_data.previous_close != None and stock_data.previous_close > 0:
                stock_data.trailing_eps_percentage = stock_data.trailing_eps / stock_data.previous_close

            if 'priceToBook'                                in info: stock_data.price_to_book                     = info['priceToBook']
            else:                                                    stock_data.price_to_book                     = None # Mark as None, so as to try and calculate manually.
            if isinstance(stock_data.price_to_book,str):             stock_data.price_to_book                     = None # Mark as None, so as to try and calculate manually.
            if stock_data.price_to_book is None:
                stock_data.price_to_book = PRICE_TO_BOOK_UNKNOWN * (10 if tase_mode else 1) # TODO: ASAFR: Until calculated manually, do not allow N/A in price2book to ruin the whole value, just set a very unatractive one, and let the rest of the parameters cope

            # Value is a ratio, such that when multiplied by 100, yields percentage (%) units:
            if 'earningsQuarterlyGrowth'                    in info:
                stock_data.eqg         = info['earningsQuarterlyGrowth']
            else:
                stock_data.eqg         = None

            # TODO: ASAFR: Currently use the niqg_yoy as a simple backup. Later on - compare and add to calculations...
            if stock_data.eqg_yoy is None: stock_data.eqg_yoy = stock_data.niqg_yoy

            # Now use above backup as required: TODO: ASAFR: One may use the yoy as direct backup... analyze this...
            if   stock_data.eqg is None and stock_data.eqg_yoy != None: stock_data.eqg     = stock_data.eqg_yoy
            elif stock_data.eqg != None and stock_data.eqg_yoy is None: stock_data.eqg_yoy = stock_data.eqg
            elif stock_data.eqg is None and stock_data.eqg_yoy is None: stock_data.eqg_yoy = stock_data.eqg = EQG_UNKNOWN

            stock_data.eqg_effective = EQG_WEIGHT_VS_YOY*stock_data.eqg + (1.0-EQG_WEIGHT_VS_YOY)*stock_data.eqg_yoy

            if stock_data.eqg_effective > 0:
                stock_data.eqg_factor_effective = (EQG_DAMPER + 1 + EQG_POSITIVE_FACTOR * stock_data.eqg_effective)
            else:
                stock_data.eqg_factor_effective = (EQG_DAMPER + 1 + stock_data.eqg_effective)

            # Value is a ratio, such that when multiplied by 100, yields percentage (%) units:
            if 'revenueQuarterlyGrowth'                     in info: stock_data.revenue_quarterly_growth         = info['revenueQuarterlyGrowth']
            else:                                                    stock_data.revenue_quarterly_growth         = None
            if stock_data.revenue_quarterly_growth          is None: stock_data.revenue_quarterly_growth         = REVENUE_QUARTERLY_GROWTH_UNKNOWN # TODO: ASAFR: Perhaps a variation is required for TASE (less information on stocks, etc)

            # TODO: ASAFR: Can actually really calculate the growth ratio - if it is the earnings growth ration than the data is known!!
            if 'pegRatio'                                   in info: stock_data.price_to_earnings_to_growth_ratio = info['pegRatio']
            else:                                                    stock_data.price_to_earnings_to_growth_ratio = PEG_UNKNOWN
            if stock_data.price_to_earnings_to_growth_ratio is None: stock_data.price_to_earnings_to_growth_ratio = PEG_UNKNOWN

            if 'sharesOutstanding'                          in info: stock_data.shares_outstanding                = info['sharesOutstanding']
            else:                                                    stock_data.shares_outstanding                = SHARES_OUTSTANDING_UNKNOWN
            if stock_data.shares_outstanding is None or stock_data.shares_outstanding == 0:
                if use_investpy and 'Shares Outstanding' in stock_information and stock_information['Shares Outstanding'] != None:
                    stock_data.shares_outstanding = int(text_to_num(stock_information['Shares Outstanding']))
                else:
                    stock_data.shares_outstanding = SHARES_OUTSTANDING_UNKNOWN

            if 'netIncomeToCommon' in info: stock_data.net_income_to_common_shareholders = info['netIncomeToCommon']
            else:                           stock_data.net_income_to_common_shareholders = None # TODO: ASAFR: It may be possible to calculate this manually

            # if no enterprise_value_to_ebitda, use earnings.
            if (stock_data.enterprise_value_to_ebitda is None or stock_data.enterprise_value_to_ebitda < 0) and stock_data.effective_earnings != None and stock_data.effective_earnings != 0:
                stock_data.enterprise_value_to_ebitda = float(stock_data.enterprise_value) / stock_data.effective_earnings  #  effective_earnings is already in USD

            if stock_data.annualized_cash_flow_from_operating_activities is None and stock_data.quarterized_cash_flow_from_operating_activities is None:
                if stock_data.effective_earnings != None:
                    stock_data.annualized_cash_flow_from_operating_activities = stock_data.quarterized_cash_flow_from_operating_activities = stock_data.effective_earnings
            elif stock_data.annualized_cash_flow_from_operating_activities is None and stock_data.quarterized_cash_flow_from_operating_activities != None:
                stock_data.annualized_cash_flow_from_operating_activities = stock_data.quarterized_cash_flow_from_operating_activities*QUARTERLY_YEARLY_MISSING_FACTOR
            elif stock_data.annualized_cash_flow_from_operating_activities != None and stock_data.quarterized_cash_flow_from_operating_activities is None:
                stock_data.quarterized_cash_flow_from_operating_activities = stock_data.annualized_cash_flow_from_operating_activities*QUARTERLY_YEARLY_MISSING_FACTOR

            if stock_data.annualized_cash_flow_from_operating_activities != None:
                if stock_data.annualized_cash_flow_from_operating_activities >= 0:
                    if stock_data.enterprise_value == 0 or stock_data.annualized_cash_flow_from_operating_activities == 0: # When 0, it means either EV is 0 (strange!) or a very very good cash flow (strange as well)
                        stock_data.annualized_ev_to_cfo_ratio = ev_to_cfo_ratio_limit * 1000  # Set a very high value to make stock unatractive
                    else:
                        stock_data.annualized_ev_to_cfo_ratio = float(stock_data.enterprise_value)/stock_data.annualized_cash_flow_from_operating_activities  # annualized_cash_flow_from_operating_activities has been converted to USD earlier
                else:  # stock_data.annualized_cash_flow_from_operating_activities < 0
                    stock_data.annualized_ev_to_cfo_ratio = (1.0-NEGATIVE_CFO_FACTOR*float(stock_data.enterprise_value)/stock_data.annualized_cash_flow_from_operating_activities)**3
            else:
                stock_data.annualized_ev_to_cfo_ratio = ev_to_cfo_ratio_limit * 1000

            if stock_data.quarterized_cash_flow_from_operating_activities != None:
                if stock_data.quarterized_cash_flow_from_operating_activities >= 0:
                    if stock_data.enterprise_value == 0 or stock_data.quarterized_cash_flow_from_operating_activities == 0: # When 0, it means either EV is 0 (strange!) or a very very good cash flow (strange as well)
                        stock_data.quarterized_ev_to_cfo_ratio = ev_to_cfo_ratio_limit * 1000  # Set a very high value to make stock unatractive
                    else:
                        stock_data.quarterized_ev_to_cfo_ratio = float(stock_data.enterprise_value)/stock_data.quarterized_cash_flow_from_operating_activities  # quarterized_cash_flow_from_operating_activities has been converted to USD earlier
                else:  # stock_data.quarterized_cash_flow_from_operating_activities < 0
                    stock_data.quarterized_ev_to_cfo_ratio = (1.0-NEGATIVE_CFO_FACTOR*float(stock_data.enterprise_value)/stock_data.quarterized_cash_flow_from_operating_activities)**3
            else:
                stock_data.quarterized_cash_flow_from_operating_activities = ev_to_cfo_ratio_limit * 1000

            stock_data.ev_to_cfo_ratio_effective = (stock_data.annualized_ev_to_cfo_ratio+stock_data.quarterized_ev_to_cfo_ratio)/2.0

            if 'priceToSalesTrailing12Months' in info and info['priceToSalesTrailing12Months'] != None:
                stock_data.trailing_12months_price_to_sales = info['priceToSalesTrailing12Months']  # https://www.investopedia.com/articles/fundamental/03/032603.asp#:~:text=The%20price%2Dto%2Dsales%20ratio%20(Price%2FSales%20or,the%20more%20attractive%20the%20investment.
            else:
                if stock_data.effective_revenue != None and stock_data.effective_revenue > 0:
                    stock_data.trailing_12months_price_to_sales  = stock_data.market_cap / stock_data.effective_revenue  # effective_revenue is already in USD (converted earlier)
                elif stock_data.ev_to_cfo_ratio_effective != None:
                    stock_data.trailing_12months_price_to_sales  = stock_data.ev_to_cfo_ratio_effective
                else:
                    stock_data.trailing_12months_price_to_sales  = None # Mark as None, so as to try and calculate manually.
            if isinstance(stock_data.trailing_12months_price_to_sales,str):  stock_data.trailing_12months_price_to_sales  = None # Mark as None, so as to try and calculate manually.
        # TODO: ASAFR: Here: id no previous_close, use market_high, low regular, or anything possible to avoid none!
        if not build_csv_db_only and (stock_data.previous_close is None or stock_data.previous_close < 1.0): # Avoid Penny Stocks
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} previous_close: {}'.format(stock_data.symbol, stock_data.previous_close)
            return_value = False

        if not build_csv_db_only and (stock_data.enterprise_value is None or stock_data.enterprise_value < min_enterprise_value_millions_usd*1000000):
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} enterprise_value: {}'.format(stock_data.symbol, stock_data.enterprise_value)
            return_value = False

        # Checkout http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs for all symbol definitions (for instance - `$` in stock names, 5-letter stocks ending with `Y`)
        if not tase_mode and SKIP_5LETTER_Y_STOCK_LISTINGS and stock_data.symbol[-1] == 'Y' and len(stock_data.symbol) == 5 and '.' not in stock_data.symbol and '-' not in stock_data.symbol and '$' not in stock_data.symbol:
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} 5 letter stock listing'.format(stock_data.symbol)
            return_value = False

        if build_csv_db_only and stock_data.enterprise_value_to_revenue is None and use_investpy and 'Revenue' in stock_information and stock_information['Revenue'] != None  and text_to_num(stock_information['Revenue']) > 0:
            stock_data.enterprise_value_to_revenue = float(stock_data.enterprise_value)/float(text_to_num(stock_information['Revenue']))

        if build_csv_db_only:
            if (stock_data.enterprise_value_to_revenue != None and stock_data.enterprise_value_to_revenue <= 0 or stock_data.enterprise_value_to_revenue is None) and stock_data.effective_revenue != None and stock_data.effective_revenue > 0:
                stock_data.evr_effective = stock_data.enterprise_value/stock_data.effective_revenue
            else:
                stock_data.evr_effective = stock_data.enterprise_value_to_revenue

        if not build_csv_db_only and (stock_data.evr_effective is None or stock_data.evr_effective <= 0 or stock_data.evr_effective > enterprise_value_to_revenue_limit):
            if return_value and (not research_mode or VERBOSE_LOGS):
                stock_data.skip_reason = 'Skipping {} enterprise_value_to_revenue: {}'.format(stock_data.symbol, stock_data.evr_effective)
            return_value = False

        if not build_csv_db_only and (stock_data.enterprise_value_to_ebitda is None or stock_data.enterprise_value_to_ebitda <= 0):
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} enterprise_value_to_ebitda: {}'.format(stock_data.symbol, stock_data.enterprise_value_to_ebitda)
            return_value = False

        if not build_csv_db_only and (stock_data.effective_price_to_earnings is None or stock_data.effective_price_to_earnings <= 0):
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} effective_price_to_earnings: {}'.format(stock_data.symbol, stock_data.effective_price_to_earnings)
            return_value = False

        if not build_csv_db_only and (stock_data.trailing_12months_price_to_sales is None or stock_data.trailing_12months_price_to_sales <= 0):
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} trailing_12months_price_to_sales: {}'.format(stock_data.symbol, stock_data.trailing_12months_price_to_sales)
            return_value = False

        if not build_csv_db_only and (stock_data.price_to_book is None or stock_data.price_to_book <= 0):
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} price_to_book: {}'.format(stock_data.symbol, stock_data.price_to_book)
            return_value = False

        if build_csv_db_only and stock_data.effective_price_to_earnings != None:
            if stock_data.sector in favor_sectors:
                index = favor_sectors.index(stock_data.sector)
                stock_data.pe_effective = stock_data.effective_price_to_earnings / float(favor_sectors_by[index])  # ** 2
            else:
                stock_data.pe_effective = stock_data.effective_price_to_earnings

        if not build_csv_db_only and (stock_data.pe_effective is None or stock_data.pe_effective <= 0 or stock_data.pe_effective > price_to_earnings_limit):
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} pe_effective: {}'.format(stock_data.symbol, stock_data.pe_effective)
            return_value = False

        if build_csv_db_only:
            if   stock_data.profit_margin            is None and stock_data.annualized_profit_margin is None and stock_data.quarterized_profit_margin is None:
                stock_data.profit_margin             = stock_data.annualized_profit_margin  = stock_data.quarterized_profit_margin = PROFIT_MARGIN_UNKNOWN
            elif stock_data.profit_margin            is None and stock_data.annualized_profit_margin is None                                                 :
                 stock_data.profit_margin            = stock_data.annualized_profit_margin  = stock_data.quarterized_profit_margin/PROFIT_MARGIN_DUPLICATION_FACTOR
            elif stock_data.annualized_profit_margin is None and stock_data.quarterized_profit_margin is None:
                 stock_data.annualized_profit_margin = stock_data.quarterized_profit_margin = stock_data.profit_margin/PROFIT_MARGIN_DUPLICATION_FACTOR
            elif stock_data.profit_margin            is None and stock_data.quarterized_profit_margin is None:
                 stock_data.profit_margin            = stock_data.quarterized_profit_margin = stock_data.annualized_profit_margin/PROFIT_MARGIN_DUPLICATION_FACTOR
            elif stock_data.profit_margin             is None: stock_data.profit_margin             = stock_data.annualized_profit_margin/PROFIT_MARGIN_DUPLICATION_FACTOR
            elif stock_data.annualized_profit_margin  is None: stock_data.annualized_profit_margin  = stock_data.profit_margin/PROFIT_MARGIN_DUPLICATION_FACTOR
            elif stock_data.quarterized_profit_margin is None: stock_data.quarterized_profit_margin = max(stock_data.profit_margin, stock_data.annualized_profit_margin)/PROFIT_MARGIN_DUPLICATION_FACTOR

            sorted_pms = sorted([stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.quarterized_profit_margin])
            weighted_average_pm = weighted_average(sorted_pms, PROFIT_MARGIN_WEIGHTS[:len(sorted_pms)]) # Do provide higher weight to the higher profit margin when averaging out
            stock_data.effective_profit_margin = PROFIT_MARGIN_DAMPER + weighted_average_pm
            
        if not build_csv_db_only and stock_data.effective_profit_margin < profit_margin_limit:
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} effective_profit_margin: {}'.format(stock_data.symbol, stock_data.effective_profit_margin)
            return_value = False

        if not build_csv_db_only and (stock_data.ev_to_cfo_ratio_effective is None  or stock_data.ev_to_cfo_ratio_effective > ev_to_cfo_ratio_limit or stock_data.ev_to_cfo_ratio_effective <= 0):
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} ev_to_cfo_ratio_effective: {}'.format(stock_data.symbol, stock_data.ev_to_cfo_ratio_effective)
            return_value = False

        if not build_csv_db_only and (stock_data.debt_to_equity_effective is None  or stock_data.debt_to_equity_effective > debt_to_equity_limit or stock_data.debt_to_equity_effective <= 0):
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} debt_to_equity_effective: {}'.format(stock_data.symbol, stock_data.debt_to_equity_effective)
            return_value = False

        if stock_data.trailing_eps is None:
            if not build_csv_db_only and use_investpy and 'EPS' in stock_information and stock_information['EPS'] != None:
                stock_data.trailing_eps = float(text_to_num(stock_information['EPS']))

        if not build_csv_db_only and (stock_data.eqg_factor_effective is None or stock_data.eqg_factor_effective < eqg_min):
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} eqg_factor_effective: {}'.format(stock_data.symbol, stock_data.eqg_factor_effective)
            return_value = False

        if not build_csv_db_only and stock_data.price_to_earnings_to_growth_ratio is None:
            if return_value and (not research_mode or VERBOSE_LOGS): stock_data.skip_reason = 'Skipping {} price_to_earnings_to_growth_ratio: {}'.format(stock_data.symbol, stock_data.price_to_earnings_to_growth_ratio)
            return_value = False

        if build_csv_db_only:
            if   stock_data.price_to_earnings_to_growth_ratio > 0: stock_data.effective_peg_ratio =  stock_data.price_to_earnings_to_growth_ratio
            elif stock_data.price_to_earnings_to_growth_ratio < 0: stock_data.effective_peg_ratio = -stock_data.price_to_earnings_to_growth_ratio*NEGATIVE_PEG_RATIO_FACTOR
            else                                                 : stock_data.effective_peg_ratio =  1.0  # Something must be wrong, so take a neutral value of 1.0

        if build_csv_db:
            if return_value: sss_core_equation_value_set(stock_data)
            else:            stock_data.sss_value = BAD_SSS

            stock_data.last_dividend_0 = 0; stock_data.last_dividend_1 = 0
            stock_data.last_dividend_2 = 0; stock_data.last_dividend_3 = 0

            # try: TODO: ASAFR: Complete this backup data to the yfinance dividends information
            #     if tase_mode: stock_dividends = investpy.get_stock_dividends(stock=stock_data.symbol.replace('.TA',''), country='israel')
            #     else:         stock_dividends = investpy.get_stock_dividends(stock=stock_data.symbol, country='united states')
            # except Exception as e:
            #     pass

            try:  # It is important to note that: 1. latest value is in index 0. 2. For the actual value in USD, need to translate the date of the dividend to the value of share at that time, because the dividends[] are pare share
                dividends = symbol.get_dividends()
                if len(dividends) > 0:
                    last_4_dividends = dividends[-1:]
                    stock_data.last_dividend_0 = last_4_dividends[-1] # Latest
                if len(dividends) > 1:
                    last_4_dividends = dividends[-2:]
                    stock_data.last_dividend_1 = last_4_dividends[-2] # One before latest
                if len(dividends) > 2:
                    last_4_dividends = dividends[-3:]
                    stock_data.last_dividend_2 = last_4_dividends[-3] # 2 before latest, etc
                if len(dividends) > 3:
                    last_4_dividends = dividends[-4:]
                    stock_data.last_dividend_3 = last_4_dividends[-4]

            except Exception as e:
                #if not research_mode: print("Exception in symbol.dividends: {}".format(e))
                pass

            round_and_avoid_none_values(stock_data)

        if return_value and not research_mode: print('                                          sector: {:10},     country: {:10},    sss_value: {:10},     annualized_revenue: {:10},     annualized_earnings: {:10},     quarterized_revenue: {:10},     quarterized_earnings: {:10},     effective_earnings: {:10},     effective_revenue: {:10},     annualized_total_revenue: {:10},     annualized_net_income: {:10},     quarterized_total_revenue: {:10},     quarterized_net_income: {:10},     effective_net_income: {:10},     effective_total_revenue: {:10},     enterprise_value_to_revenue: {:10},     evr_effective: {:10},     trailing_price_to_earnings: {:10},     forward_price_to_earnings: {:10},     effective_price_to_earnings: {:10},     trailing_12months_price_to_sales: {:10},     pe_effective: {:10},     enterprise_value_to_ebitda: {:10},     profit_margin: {:10},     annualized_profit_margin: {:10},       annualized_profit_margin_boost: {:10},     quarterized_profit_margin: {:10},     quarterized_profit_margin_boost: {:10},     effective_profit_margin_boost: {:10}, held_percent_institutions: {:10},     forward_eps: {:10},     trailing_eps: {:10},     previous_close: {:10},     trailing_eps_percentage: {:10},     price_to_book: {:10},     shares_outstanding: {:10},     net_income_to_common_shareholders: {:10},     nitcsh_to_shares_outstanding: {:10},     employees: {:10},     enterprise_value: {:10},     market_cap: {:10},     nitcsh_to_num_employees: {:10},     eqg_factor_effective: {:10},     revenue_quarterly_growth: {:10},     price_to_earnings_to_growth_ratio: {:10},     effective_peg_ratio: {:10},     annualized_cash_flow_from_operating_activities: {:10},     quarterized_cash_flow_from_operating_activities: {:10},     annualized_ev_to_cfo_ratio: {:10},     quarterized_ev_to_cfo_ratio: {:10},     ev_to_cfo_ratio_effective: {:10},     annualized_debt_to_equity: {:10},     quarterized_debt_to_equity: {:10},     debt_to_equity_effective: {:10},     financial_currency: {:10},     conversion_rate_mult_to_usd: {:10}'.format(
                                                                                                stock_data.sector, stock_data.country,stock_data.sss_value, stock_data.annualized_revenue, stock_data.annualized_earnings, stock_data.quarterized_revenue, stock_data.quarterized_earnings, stock_data.effective_earnings, stock_data.effective_revenue, stock_data.annualized_total_revenue, stock_data.annualized_net_income, stock_data.quarterized_total_revenue, stock_data.quarterized_net_income, stock_data.effective_net_income, stock_data.effective_total_revenue, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.forward_price_to_earnings, stock_data.effective_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.pe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin,   stock_data.annualized_profit_margin_boost, stock_data.quarterized_profit_margin, stock_data.quarterized_profit_margin_boost, stock_data.effective_profit_margin,   stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.employees, stock_data.enterprise_value, stock_data.market_cap, stock_data.nitcsh_to_num_employees, stock_data.eqg_factor_effective, stock_data.revenue_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.effective_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.quarterized_cash_flow_from_operating_activities, stock_data.annualized_ev_to_cfo_ratio, stock_data.quarterized_ev_to_cfo_ratio, stock_data.ev_to_cfo_ratio_effective, stock_data.annualized_debt_to_equity, stock_data.quarterized_debt_to_equity, stock_data.debt_to_equity_effective, stock_data.financial_currency, stock_data.conversion_rate_mult_to_usd))
        if not return_value and (not research_mode or VERBOSE_LOGS): print('                            ' + stock_data.skip_reason)

        return return_value

    except Exception as e:  # More information is output when exception is used instead of Exception
        if not research_mode: print("              Exception in {} info: {}".format(stock_data.symbol, e))
        return False


def check_interval(thread_id, interval_threads, interval_secs_to_avoid_http_errors, research_mode):
    if thread_id > 0 and thread_id % interval_threads == 0 and not research_mode:
        print("\n===========================================================================")
        print(  "[thread_id {:2} is an interval {} point, going to sleep for {} seconds]".format(thread_id, interval_threads, interval_secs_to_avoid_http_errors))
        print(  "===========================================================================\n")
        time.sleep(interval_secs_to_avoid_http_errors)


# Assumption is that reference_db is sorted by symbol name, but just find it, no need to optimize as of now
def find_symbol_in_reference_db(symbol, reference_db):
    for index in range(len(reference_db)):
        if symbol == reference_db[index][g_symbol_index]:
            return index
    return -1


def get_db_row_from_stock_data(stock_data):
    return [stock_data.symbol, stock_data.short_name, stock_data.sector, stock_data.country, stock_data.sss_value, stock_data.annualized_revenue, stock_data.annualized_earnings, stock_data.quarterized_revenue, stock_data.quarterized_earnings, stock_data.effective_earnings, stock_data.effective_revenue, stock_data.annualized_total_revenue, stock_data.annualized_net_income, stock_data.quarterized_total_revenue, stock_data.quarterized_net_income, stock_data.effective_net_income, stock_data.effective_total_revenue, stock_data.enterprise_value_to_revenue, stock_data.evr_effective, stock_data.trailing_price_to_earnings, stock_data.forward_price_to_earnings, stock_data.effective_price_to_earnings, stock_data.trailing_12months_price_to_sales, stock_data.pe_effective, stock_data.enterprise_value_to_ebitda, stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.annualized_profit_margin_boost, stock_data.quarterized_profit_margin, stock_data.quarterized_profit_margin_boost, stock_data.effective_profit_margin, stock_data.held_percent_institutions, stock_data.forward_eps, stock_data.trailing_eps, stock_data.previous_close, stock_data.trailing_eps_percentage, stock_data.price_to_book, stock_data.shares_outstanding, stock_data.net_income_to_common_shareholders, stock_data.nitcsh_to_shares_outstanding, stock_data.employees, stock_data.enterprise_value, stock_data.market_cap, stock_data.nitcsh_to_num_employees, stock_data.eqg, stock_data.eqg_yoy, stock_data.niqg_yoy, stock_data.eqg_effective, stock_data.eqg_factor_effective, stock_data.revenue_quarterly_growth, stock_data.price_to_earnings_to_growth_ratio, stock_data.effective_peg_ratio, stock_data.annualized_cash_flow_from_operating_activities, stock_data.quarterized_cash_flow_from_operating_activities, stock_data.annualized_ev_to_cfo_ratio, stock_data.quarterized_ev_to_cfo_ratio, stock_data.ev_to_cfo_ratio_effective, stock_data.annualized_debt_to_equity, stock_data.quarterized_debt_to_equity, stock_data.debt_to_equity_effective, stock_data.financial_currency, stock_data.conversion_rate_mult_to_usd, stock_data.last_dividend_0, stock_data.last_dividend_1, stock_data.last_dividend_2, stock_data.last_dividend_3, stock_data.fifty_two_week_change, stock_data.fifty_two_week_low, stock_data.fifty_two_week_high, stock_data.two_hundred_day_average, stock_data.previous_close_percentage_from_200d_ma, stock_data.previous_close_percentage_from_52w_low, stock_data.previous_close_percentage_from_52w_high, stock_data.dist_from_low_factor, stock_data.eff_dist_from_low_factor, stock_data.annualized_total_ratio, stock_data.quarterized_total_ratio, stock_data.annualized_other_current_ratio, stock_data.quarterized_other_current_ratio, stock_data.annualized_other_ratio, stock_data.quarterized_other_ratio, stock_data.annualized_total_current_ratio, stock_data.quarterized_total_current_ratio, stock_data.total_ratio_effective, stock_data.other_current_ratio_effective, stock_data.other_ratio_effective, stock_data.total_current_ratio_effective, stock_data.skip_reason]


def get_stock_data_from_db_row(row, symbol=None):
    if symbol:
        stock_symbol = symbol
    else:
        stock_symbol = row[g_symbol_index]
    return StockData(symbol=stock_symbol, short_name=row[g_name_index], sector=row[g_sector_index], country=row[g_country_index], sss_value=float(row[g_sss_value_index] if row[g_sss_value_index] != None else 0), annualized_revenue=float(row[g_annualized_revenue_index] if row[g_annualized_revenue_index] != None else 0), annualized_earnings=float(row[g_annualized_earnings_index] if row[g_annualized_earnings_index] != None else 0), quarterized_revenue=float(row[g_quarterized_revenue_index] if row[g_quarterized_revenue_index] != None else 0), quarterized_earnings=float(row[g_quarterized_earnings_index] if row[g_quarterized_earnings_index] != None else 0), effective_earnings=float(row[g_effective_earnings_index] if row[g_effective_earnings_index] != None else 0), effective_revenue=float(row[g_effective_revenue_index] if row[g_effective_revenue_index] != None else 0), annualized_total_revenue=float(row[g_annualized_total_revenue_index] if row[g_annualized_total_revenue_index] != None else 0), annualized_net_income=float(row[g_annualized_net_income_index] if row[g_annualized_net_income_index] != None else 0), quarterized_total_revenue=float(row[g_quarterized_total_revenue_index] if row[g_quarterized_total_revenue_index] != None else 0), quarterized_net_income=float(row[g_quarterized_net_income_index] if row[g_quarterized_net_income_index] != None else 0), effective_net_income=float(row[g_effective_net_income_index] if row[g_effective_net_income_index] != None else 0), effective_total_revenue=float(row[g_effective_total_revenue_index] if row[g_effective_total_revenue_index] != None else 0), enterprise_value_to_revenue=float(row[g_enterprise_value_to_revenue_index] if row[g_enterprise_value_to_revenue_index] != None else 0), evr_effective=float(row[g_evr_effective_index] if row[g_evr_effective_index] != None else 0), trailing_price_to_earnings=float(row[g_trailing_price_to_earnings_index] if row[g_trailing_price_to_earnings_index] != None else 0), forward_price_to_earnings=float(row[g_forward_price_to_earnings_index] if row[g_forward_price_to_earnings_index] != None else 0), effective_price_to_earnings=float(row[g_effective_price_to_earnings_index] if row[g_effective_price_to_earnings_index] != None else 0), trailing_12months_price_to_sales=float(row[g_trailing_12months_price_to_sales_index] if row[g_trailing_12months_price_to_sales_index] != None else 0), pe_effective=float(row[g_pe_effective_index] if row[g_pe_effective_index] != None else 0), enterprise_value_to_ebitda=float(row[g_enterprise_value_to_ebitda_index] if row[g_enterprise_value_to_ebitda_index] != None else 0), profit_margin=float(row[g_profit_margin_index] if row[g_profit_margin_index] != None else 0), annualized_profit_margin=float(row[g_annualized_profit_margin_index] if row[g_annualized_profit_margin_index] != None else 0), annualized_profit_margin_boost=float(row[g_annualized_profit_margin_boost_index] if row[g_annualized_profit_margin_boost_index] != None else 0), quarterized_profit_margin=float(row[g_quarterized_profit_margin_index] if row[g_quarterized_profit_margin_index] != None else 0), quarterized_profit_margin_boost=float(row[g_quarterized_profit_margin_boost_index] if row[g_quarterized_profit_margin_boost_index] != None else 0), effective_profit_margin=float(row[g_effective_profit_margin_index] if row[g_effective_profit_margin_index] != None else 0), held_percent_institutions=float(row[g_held_percent_institutions_index] if row[g_held_percent_institutions_index] != None else 0), forward_eps=float(row[g_forward_eps_index] if row[g_forward_eps_index] != None else 0), trailing_eps=float(row[g_trailing_eps_index] if row[g_trailing_eps_index] != None else 0), previous_close=float(row[g_previous_close_index] if row[g_previous_close_index] != None else 0), trailing_eps_percentage=float(row[g_trailing_eps_percentage_index] if row[g_trailing_eps_percentage_index] != None else 0), price_to_book=float(row[g_price_to_book_index] if row[g_price_to_book_index] != None else 0), shares_outstanding=float(row[g_shares_outstanding_index] if row[g_shares_outstanding_index] != None else 0), net_income_to_common_shareholders=float(row[g_net_income_to_common_shareholders_index] if row[g_net_income_to_common_shareholders_index] != None else 0), nitcsh_to_shares_outstanding=float(row[g_nitcsh_to_shares_outstanding_index] if row[g_nitcsh_to_shares_outstanding_index] != None else 0), employees=int(float(row[g_employees_index] if row[g_employees_index] != None else 0)), enterprise_value=int(float(row[g_enterprise_value_index] if row[g_enterprise_value_index] != None else 0)), market_cap=int(float(row[g_market_cap_index] if row[g_market_cap_index] != None else 0)), nitcsh_to_num_employees=float(row[g_nitcsh_to_num_employees_index] if row[g_nitcsh_to_num_employees_index] != None else 0), eqg=float(row[g_eqg_index] if row[g_eqg_index] != None else 0), eqg_yoy=float(row[g_eqg_yoy_index] if row[g_eqg_yoy_index] != None else 0), niqg_yoy=float(row[g_niqg_yoy_index] if row[g_niqg_yoy_index] != None else 0), eqg_effective=float(row[g_eqg_effective_index] if row[g_eqg_effective_index] != None else 0), eqg_factor_effective=float(row[g_eqg_factor_effective_index] if row[g_eqg_factor_effective_index] != None else 0), revenue_quarterly_growth=float(row[g_revenue_quarterly_growth_index] if row[g_revenue_quarterly_growth_index] != None else 0), price_to_earnings_to_growth_ratio=float(row[g_price_to_earnings_to_growth_ratio_index] if row[g_price_to_earnings_to_growth_ratio_index] != None else 0), effective_peg_ratio=float(row[g_effective_peg_ratio_index] if row[g_effective_peg_ratio_index] != None else 0), annualized_cash_flow_from_operating_activities=float(row[g_annualized_cash_flow_from_operating_activities_index] if row[g_annualized_cash_flow_from_operating_activities_index] != None else 0), quarterized_cash_flow_from_operating_activities=float(row[g_quarterized_cash_flow_from_operating_activities_index] if row[g_quarterized_cash_flow_from_operating_activities_index] != None else 0), annualized_ev_to_cfo_ratio=float(row[g_annualized_ev_to_cfo_ratio_index] if row[g_annualized_ev_to_cfo_ratio_index] != None else 0), quarterized_ev_to_cfo_ratio=float(row[g_quarterized_ev_to_cfo_ratio_index] if row[g_quarterized_ev_to_cfo_ratio_index] != None else 0), ev_to_cfo_ratio_effective=float(row[g_ev_to_cfo_ratio_effective_index] if row[g_ev_to_cfo_ratio_effective_index] != None else 0), annualized_debt_to_equity=float(row[g_annualized_debt_to_equity_index] if row[g_annualized_debt_to_equity_index] != None else 0), quarterized_debt_to_equity=float(row[g_quarterized_debt_to_equity_index] if row[g_quarterized_debt_to_equity_index] != None else 0), debt_to_equity_effective=float(row[g_debt_to_equity_effective_index] if row[g_debt_to_equity_effective_index] != None else 0), financial_currency=row[g_financial_currency_index], conversion_rate_mult_to_usd=float(row[g_conversion_rate_mult_to_usd_index] if row[g_conversion_rate_mult_to_usd_index] != None else 0), last_dividend_0=float(row[g_last_dividend_0_index] if row[g_last_dividend_0_index] != None else 0), last_dividend_1=float(row[g_last_dividend_1_index] if row[g_last_dividend_1_index] != None else 0), last_dividend_2=float(row[g_last_dividend_2_index] if row[g_last_dividend_2_index] != None else 0), last_dividend_3=float(row[g_last_dividend_3_index] if row[g_last_dividend_3_index] != None else 0), fifty_two_week_change=float(row[g_fifty_two_week_change_index] if row[g_fifty_two_week_change_index] != None else 0), fifty_two_week_low=float(row[g_fifty_two_week_low_index] if row[g_fifty_two_week_low_index] != None else 0), fifty_two_week_high=float(row[g_fifty_two_week_high_index] if row[g_fifty_two_week_high_index] != None else 0), two_hundred_day_average=float(row[g_two_hundred_day_average_index] if row[g_two_hundred_day_average_index] != None else 0), previous_close_percentage_from_200d_ma=float(row[g_previous_close_percentage_from_200d_ma_index] if row[g_previous_close_percentage_from_200d_ma_index] != None else 0), previous_close_percentage_from_52w_low=float(row[g_previous_close_percentage_from_52w_low_index] if row[g_previous_close_percentage_from_52w_low_index] != None else 0), previous_close_percentage_from_52w_high=float(row[g_previous_close_percentage_from_52w_high_index] if row[g_previous_close_percentage_from_52w_high_index] != None else 0), dist_from_low_factor=float(row[g_dist_from_low_factor_index] if row[g_dist_from_low_factor_index] != None else 0), eff_dist_from_low_factor=float(row[g_eff_dist_from_low_factor_index] if row[g_eff_dist_from_low_factor_index] != None else 0), annualized_total_ratio=float(row[g_annualized_total_ratio_index] if row[g_annualized_total_ratio_index] != None else 0), quarterized_total_ratio=float(row[g_quarterized_total_ratio_index] if row[g_quarterized_total_ratio_index] != None else 0), annualized_other_current_ratio=float(row[g_annualized_other_current_ratio_index] if row[g_annualized_other_current_ratio_index] != None else 0), quarterized_other_current_ratio=float(row[g_quarterized_other_current_ratio_index] if row[g_quarterized_other_current_ratio_index] != None else 0), annualized_other_ratio=float(row[g_annualized_other_ratio_index] if row[g_annualized_other_ratio_index] != None else 0), quarterized_other_ratio=float(row[g_quarterized_other_ratio_index] if row[g_quarterized_other_ratio_index] != None else 0), annualized_total_current_ratio=float(row[g_annualized_total_current_ratio_index] if row[g_annualized_total_current_ratio_index] != None else 0), quarterized_total_current_ratio=float(row[g_quarterized_total_current_ratio_index] if row[g_quarterized_total_current_ratio_index] != None else 0), total_ratio_effective=float(row[g_total_ratio_effective_index] if row[g_total_ratio_effective_index] != None else 0), other_current_ratio_effective=float(row[g_other_current_ratio_effective_index] if row[g_other_current_ratio_effective_index] != None else 0), other_ratio_effective=float(row[g_other_ratio_effective_index] if row[g_other_ratio_effective_index] != None else 0), total_current_ratio_effective=float(row[g_total_current_ratio_effective_index] if row[g_total_current_ratio_effective_index] != None else 0), skip_reason=row[g_skip_reason_index])

def process_symbols(symbols, csv_db_data, rows, rows_no_div, rows_only_div, thread_id, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, diff_rows):
    iteration = 0
    if build_csv_db:
        for symb in symbols:
            iteration += 1
            sleep_seconds = round(random.uniform(float(relaxed_access)/2.0, float(relaxed_access)*2), NUM_ROUND_DECIMALS)
            time.sleep(sleep_seconds)
            if not research_mode: print('[Building DB: thread_id {:2} Sleeping for {:10} sec] Checking {:9} ({:4}/{:4}/{:4} [Diff: {:4}]):'.format(thread_id, sleep_seconds, symb, len(rows), iteration, len(symbols), len(diff_rows)))
            if tase_mode:
                symbol = yf.Ticker(symb)
            else:
                symbol = yf.Ticker(symb.replace('.','-'))  # TODO: ASFAR: Sometimes the '.' Is needed, especially for non-US companies. See for instance 5205.kl. In this case the parameter is also case-sensitive! -> https://github.com/pydata/pandas-datareader/issues/810#issuecomment-789684354
            stock_data = StockData(symbol=symb)
            process_info_result = process_info(symbol=symbol, stock_data=stock_data, build_csv_db_only=build_csv_db_only, use_investpy=use_investpy, tase_mode=tase_mode, sectors_list=sectors_list, sectors_filter_out=sectors_filter_out, countries_list=countries_list, countries_filter_out=countries_filter_out, build_csv_db=build_csv_db, profit_margin_limit=profit_margin_limit, ev_to_cfo_ratio_limit=ev_to_cfo_ratio_limit, debt_to_equity_limit=debt_to_equity_limit, min_enterprise_value_millions_usd=min_enterprise_value_millions_usd, eqg_min=eqg_min, revenue_quarterly_growth_min=revenue_quarterly_growth_min, price_to_earnings_limit=price_to_earnings_limit, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_sectors=favor_sectors, favor_sectors_by=favor_sectors_by, market_cap_included=market_cap_included, research_mode=research_mode, currency_conversion_tool=currency_conversion_tool, currency_conversion_tool_alternative=currency_conversion_tool_alternative, currency_conversion_tool_manual=currency_conversion_tool_manual, reference_db=reference_db)
            if tase_mode and 'TLV:' not in stock_data.symbol: stock_data.symbol = 'TLV:' + stock_data.symbol.replace('.TA', '').replace('.', '-')

            row_to_append = get_db_row_from_stock_data(stock_data)
            # Find symbol in reference_db:
            if len(reference_db):
                symbol_index_in_reference_db = find_symbol_in_reference_db(stock_data.symbol, reference_db)
                if symbol_index_in_reference_db >= 0:
                    found_differences = False
                    for index in range(len(g_header_row)):
                        if (VERBOSE_LOGS): print('      comparing column {}'.format(g_header_row[index]))
                        if type(row_to_append[index]) == int or type(row_to_append[index]) == float:
                            try:
                                if len(reference_db[symbol_index_in_reference_db][index]):
                                    min_val = min(float(row_to_append[index]), float(reference_db[symbol_index_in_reference_db][index]))
                                    max_val = max(float(row_to_append[index]), float(reference_db[symbol_index_in_reference_db][index]))
                                    diff    = abs(max_val-min_val)
                                    # TODO: ASAFR: 52-week change is not really working and not really needed - fix or eliminate
                                    indices_list_to_ignore_changes_in = [g_sss_value_index] # [g_fifty_two_week_change_index, g_sss_value_index, g_two_hundred_day_average_index, g_previous_close_percentage_from_200d_ma_index]
                                    if diff > abs(max_val)*REFERENCE_DB_MAX_VALUE_DIFF_FACTOR_THRESHOLD and index not in indices_list_to_ignore_changes_in:
                                        if 0.0 < float(reference_db[symbol_index_in_reference_db][g_sss_value_index]) < float(row_to_append[g_sss_value_index]):
                                            found_differences = True
                                            compensated_value = round(REFERENCE_DB_MAX_VALUE_DIFF_FACTOR_THRESHOLD*float(reference_db[symbol_index_in_reference_db][index]) + (1-REFERENCE_DB_MAX_VALUE_DIFF_FACTOR_THRESHOLD)*float(row_to_append[index]), NUM_ROUND_DECIMALS)
                                            if type(row_to_append[index]) == int:
                                                compensated_value = int(round(compensated_value))
                                            print('                            {:5} - Suspicious Difference detected (taking lower sss_value [{} < {}] row as correct row): reference_db[{:25}]={:6}, db[{:25}]={:6} -> compensated_value = {:6}'.format(row_to_append[g_symbol_index], (reference_db[symbol_index_in_reference_db][g_sss_value_index]), (row_to_append[g_sss_value_index]), g_header_row[index], reference_db[symbol_index_in_reference_db][index], g_header_row[index], row_to_append[index], compensated_value))
                                            row_to_append[index] = compensated_value  # Overwrite specific index value with compensated value from reference db
                            except Exception as e:
                                print("Exception {} in comparison of {}: row_to_append is {} while reference_db is {}".format(e, g_header_row[index], row_to_append[index], reference_db[symbol_index_in_reference_db][index]))
                                pass

                    if found_differences:
                        get_stock_data_from_db_row(row_to_append)
                        if stock_data.sector             in ['None', '', 'Unknown']: stock_data.sector             = reference_db[symbol_index_in_reference_db][g_sector_index]
                        if stock_data.country            in ['None', '', 'Unknown']: stock_data.country            = reference_db[symbol_index_in_reference_db][g_country_index]
                        if stock_data.short_name         in ['None', '', 'Unknown']: stock_data.short_name         = reference_db[symbol_index_in_reference_db][g_name_index]
                        if stock_data.financial_currency in ['None', '', 'Unknown']: stock_data.financial_currency = reference_db[symbol_index_in_reference_db][g_financial_currency_index]

                        # stock_data = get_stock_data_from_db_row(reference_db[symbol_index_in_reference_db])
                        # Re-process with more correct information:
                        sss_core_equation_value_set(stock_data)
                        diff_rows.append(reference_db[symbol_index_in_reference_db])

            dividends_sum = stock_data.last_dividend_0+stock_data.last_dividend_1+stock_data.last_dividend_2+stock_data.last_dividend_3

            if process_info_result:
                rows.append(                           row_to_append)
                if dividends_sum: rows_only_div.append(row_to_append)
                else:             rows_no_div.append(  row_to_append)
            csv_db_data.append(                    row_to_append)
    else: # DB already present
        for row_index, row in enumerate(csv_db_data):
            iteration += 1

            symbol = row[g_symbol_index]
            # Below: 4 represents 1st index in row after "Country" which is index 3 (counting from 0 of course)
            for fix_row_index in range(g_country_index+1,len(row)):  # for empty strings - convert value to 0
                if row[fix_row_index] == '':
                    if fix_row_index == g_name_index:  # Name == '' --> 'None'
                        row[fix_row_index] = 'None'
                    else:
                        row[fix_row_index] = 0
            stock_data = get_stock_data_from_db_row(row, symbol)
            if not process_info(symbol=symbol, stock_data=stock_data, build_csv_db_only=build_csv_db_only, use_investpy=use_investpy, tase_mode=tase_mode, sectors_list=sectors_list, sectors_filter_out=sectors_filter_out, countries_list=countries_list, countries_filter_out=countries_filter_out, build_csv_db=build_csv_db, profit_margin_limit=profit_margin_limit, min_enterprise_value_millions_usd=min_enterprise_value_millions_usd, ev_to_cfo_ratio_limit=ev_to_cfo_ratio_limit, debt_to_equity_limit=debt_to_equity_limit, eqg_min=eqg_min, revenue_quarterly_growth_min=revenue_quarterly_growth_min, price_to_earnings_limit=price_to_earnings_limit, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_sectors=favor_sectors, favor_sectors_by=favor_sectors_by, market_cap_included=market_cap_included, research_mode=research_mode, currency_conversion_tool=currency_conversion_tool, currency_conversion_tool_alternative=currency_conversion_tool_alternative, currency_conversion_tool_manual=currency_conversion_tool_manual, reference_db=reference_db):
                if research_mode: continue

            if tase_mode and 'TLV:' not in stock_data.symbol: stock_data.symbol = 'TLV:' + stock_data.symbol.replace('.TA', '').replace('.','-')

            dividends_sum = stock_data.last_dividend_0 + stock_data.last_dividend_1 + stock_data.last_dividend_2 + stock_data.last_dividend_3

            row_to_append = get_db_row_from_stock_data(stock_data)
            rows.append(                           row_to_append)
            if dividends_sum: rows_only_div.append(row_to_append)
            else:             rows_no_div.append(  row_to_append)


# reference_run : Used for identifying anomalies in which some symbol information is completely different from last run. It can be different but only in new quartely reports
#                 It is sometimes observed that stocks information is wrongly fetched. Is such cases, the last run's reference point shall be used, with a forgetting factor
def sss_run(reference_run, sectors_list, sectors_filter_out, countries_list, countries_filter_out,build_csv_db_only, build_csv_db, csv_db_path, db_filename, read_united_states_input_symbols, tase_mode, num_threads, market_cap_included, use_investpy, research_mode, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, generate_result_folders=1, appearance_counter_dict_sss={}, appearance_counter_min=25, appearance_counter_max=35, custom_portfolio=[]):
    currency_conversion_tool = currency_conversion_tool_alternative = None
    currency_conversion_tool_manual = {  # https://en.wikipedia.org/wiki/ISO_4217
        "ARS": 94.2,  # Argentine Peso
        "AUD": 1.29,
        "BMD": 1.0,
        "BRL": 5.32,
        "CAD": 1.21,
        "CHF": 0.9,
        "CLP": 715.1,
        "CNY": 6.44,
        "COP": 3684.95,
        "DKK": 6.1,  # Danish Krone
        "EUR": 0.82,
        "GBP": 0.71,
        "HKD": 7.76,  # Hong Kong Dollar
        "IDR": 14394.70,
        "ILS": 3.27,
        "INR": 73.13,  # Indian Rupee
        "JPY": 108.97,  # Japanese Yen
        "KRW": 1131.24,
        "MXN": 19.9,
        "PEN": 3.74,
        "PHP": 3.74,  # Philippine Peso
        "RUB": 73.78,
        "SEK": 1.33,  # Swedish Krona
        "SGD": 1.33,
        "TRY": 8.41,
        "TWD": 27.98,
        "USD": 1.0,
        "ZAR": 14.1  # South African Rand
    }

    try:
        currency_conversion_tool = CurrencyRates().get_rates('USD') if build_csv_db else None
    except Exception as e:
        try:
            currency_conversion_tool_alternative = CurrencyConverter() if build_csv_db else None
        except Exception as e:
            print('Exchange Rates down, some countries shall be filtered out unless exchange rate provided manualy')

    reference_db = []
    if not research_mode and reference_run != None and len(reference_run):  # in non-research mode, compare to reference run
        reference_csv_db_filename = reference_run+'/db.csv'
        with open(reference_csv_db_filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                if row_index <= 1: # first row is just a title of evr and pm, then a title of columns
                    row_index += 1
                    continue
                else:
                    reference_db.append(row)
                    row_index += 1

    # Working Mode:
    relaxed_access                     = (num_threads-1)/10.0                                       if build_csv_db else 0  # In seconds
    interval_threads                   = 4 +     1*tase_mode -    read_united_states_input_symbols  if build_csv_db else 0
    interval_secs_to_avoid_http_errors = num_threads*(num_threads - 1*tase_mode + num_threads*read_united_states_input_symbols) if build_csv_db else 0  # Every interval_threads, a INTERVALS_TO_AVOID_HTTP_ERRORS sec sleep will take place

    # Working Parameters:
    eqg_min                      = EQG_UNKNOWN                          # The earnings can decrease but there is still a requirement that price_to_earnings_to_growth_ratio > 0. TODO: ASAFR: Add to multi-dimension
    revenue_quarterly_growth_min = REVENUE_QUARTERLY_GROWTH_UNKNOWN     # The revenue  can decrease there is still a requirement that price_to_earnings_to_growth_ratio > 0. TODO: ASAFR: Add to multi-dimension

    symbols                 = []
    symbols_tase            = []
    symbols_snp500          = []
    symbols_snp500_download = []
    symbols_nasdaq100       = []
    symbols_nasdaq_100_csv  = []
    symbols_russel1000      = []
    symbols_russel1000_csv  = []
    stocks_list_tase        = []

    if not tase_mode and not research_mode and build_csv_db:
        payload            = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies') # There are 2 tables on the Wikipedia page, get the first table
        first_table        = payload[0]
        second_table       = payload[1]
        df                 = first_table
        symbols_snp500     = df['Symbol'].values.tolist()
        symbols_nasdaq100  = ['ATVI', 'ADBE', 'AMD', 'ALXN', 'ALGN', 'GOOG', 'GOOGL', 'AMZN', 'AMGN', 'ADI', 'ANSS', 'AAPL', 'AMAT', 'ASML', 'ADSK', 'ADP', 'BIDU', 'BIIB', 'BMRN', 'BKNG', 'AVGO', 'CDNS', 'CDW', 'CERN', 'CHTR', 'CHKP', 'CTAS', 'CSCO', 'CTXS', 'CTSH', 'CMCSA', 'CPRT', 'COST', 'CSX', 'DXCM', 'DOCU', 'DLTR', 'EBAY', 'EA', 'EXC', 'EXPE', 'FB', 'FAST', 'FISV', 'FOX', 'FOXA', 'GILD', 'IDXX', 'ILMN', 'INCY', 'INTC', 'INTU', 'ISRG', 'JD', 'KLAC', 'LRCX', 'LBTYA', 'LBTYK', 'LULU', 'MAR', 'MXIM', 'MELI', 'MCHP', 'MU', 'MSFT', 'MRNA', 'MDLZ', 'MNST', 'NTES', 'NFLX', 'NVDA', 'NXPI', 'ORLY', 'PCAR', 'PAYX', 'PYPL', 'PEP', 'PDD', 'QCOM', 'REGN', 'ROST', 'SGEN', 'SIRI', 'SWKS', 'SPLK', 'SBUX', 'SNPS', 'TMUS', 'TTWO', 'TSLA', 'TXN', 'KHC', 'TCOM', 'ULTA', 'VRSN', 'VRSK', 'VRTX', 'WBA', 'WDC', 'WDAY', 'XEL', 'XLNX', 'ZM']
        symbols_russel1000 = ['TWOU', 'MMM', 'ABT', 'ABBV', 'ABMD', 'ACHC', 'ACN', 'ATVI', 'AYI', 'ADNT', 'ADBE', 'ADT', 'AAP', 'AMD', 'ACM', 'AES', 'AMG', 'AFL', 'AGCO', 'A', 'AGIO', 'AGNC', 'AL', 'APD', 'AKAM', 'ALK', 'ALB', 'AA', 'ARE', 'ALXN', 'ALGN', 'ALKS', 'Y', 'ALLE', 'AGN', 'ADS', 'LNT', 'ALSN', 'ALL', 'ALLY', 'ALNY', 'GOOGL', 'GOOG', 'MO', 'AMZN', 'AMCX', 'DOX', 'UHAL', 'AEE', 'AAL', 'ACC', 'AEP', 'AXP', 'AFG', 'AMH', 'AIG', 'ANAT', 'AMT', 'AWK', 'AMP', 'ABC', 'AME', 'AMGN', 'APH', 'ADI', 'NLY', 'ANSS', 'AR', 'ANTM', 'AON', 'APA', 'AIV', 'APY', 'APLE', 'AAPL', 'AMAT', 'ATR', 'APTV', 'WTR', 'ARMK', 'ACGL', 'ADM', 'ARNC', 'ARD', 'ANET', 'AWI', 'ARW', 'ASH', 'AZPN', 'ASB', 'AIZ', 'AGO', 'T', 'ATH', 'TEAM', 'ATO', 'ADSK', 'ADP', 'AN', 'AZO', 'AVB', 'AGR', 'AVY', 'AVT', 'EQH', 'AXTA', 'AXS', 'BKR', 'BLL', 'BAC', 'BOH', 'BK', 'OZK', 'BKU', 'BAX', 'BDX', 'WRB', 'BRK.B', 'BERY', 'BBY', 'BYND', 'BGCP', 'BIIB', 'BMRN', 'BIO', 'TECH', 'BKI', 'BLK', 'HRB', 'BLUE', 'BA', 'BOKF', 'BKNG', 'BAH', 'BWA', 'BSX', 'BDN', 'BFAM', 'BHF', 'BMY', 'BRX', 'AVGO', 'BR', 'BPYU', 'BRO', 'BFA', 'BFB', 'BRKR', 'BC', 'BG', 'BURL', 'BWXT', 'CHRW', 'CABO', 'CBT', 'COG', 'CACI', 'CDNS', 'CZR', 'CPT', 'CPB', 'CMD', 'COF', 'CAH', 'CSL', 'KMX', 'CCL', 'CRI', 'CASY', 'CTLT', 'CAT', 'CBOE', 'CBRE', 'CBS', 'CDK', 'CDW', 'CE', 'CELG', 'CNC', 'CDEV', 'CNP', 'CTL', 'CDAY', 'BXP', 'CF', 'CRL', 'CHTR', 'CHE', 'LNG', 'CHK', 'CVX', 'CIM', 'CMG', 'CHH', 'CB', 'CHD', 'CI', 'XEC', 'CINF', 'CNK', 'CTAS', 'CSCO', 'CIT', 'C', 'CFG', 'CTXS', 'CLH', 'CLX', 'CME', 'CMS', 'CNA', 'CNX', 'KO', 'CGNX', 'CTSH', 'COHR', 'CFX', 'CL', 'CLNY', 'CXP', 'COLM', 'CMCSA', 'CMA', 'CBSH', 'COMM', 'CAG', 'CXO', 'CNDT', 'COP', 'ED', 'STZ', 'CERN', 'CPA', 'CPRT', 'CLGX', 'COR', 'GLW', 'OFC', 'CSGP', 'COST', 'COTY', 'CR', 'CACC', 'CCI', 'CCK', 'CSX', 'CUBE', 'CFR', 'CMI', 'CW', 'CVS', 'CY', 'CONE', 'DHI', 'DHR', 'DRI', 'DVA', 'SITC', 'DE', 'DELL', 'DAL', 'XRAY', 'DVN', 'DXCM', 'FANG', 'DKS', 'DLR', 'DFS', 'DISCA', 'DISCK', 'DISH', 'DIS', 'DHC', 'DOCU', 'DLB', 'DG', 'DLTR', 'D', 'DPZ', 'CLR', 'COO', 'DEI', 'DOV', 'DD', 'DPS', 'DTE', 'DUK', 'DRE', 'DNB', 'DNKN', 'DXC', 'ETFC', 'EXP', 'EWBC', 'EMN', 'ETN', 'EV', 'EBAY', 'SATS', 'ECL', 'EIX', 'EW', 'EA', 'EMR', 'ESRT', 'EHC', 'EGN', 'ENR', 'ETR', 'EVHC', 'EOG', 'EPAM', 'EPR', 'EQT', 'EFX', 'EQIX', 'EQC', 'ELS', 'EQR', 'ERIE', 'ESS', 'EL', 'EEFT', 'EVBG', 'EVR', 'RE', 'EVRG', 'ES', 'UFS', 'DCI', 'EXPE', 'EXPD', 'STAY', 'EXR', 'XOG', 'XOM', 'FFIV', 'FB', 'FDS', 'FICO', 'FAST', 'FRT', 'FDX', 'FIS', 'FITB', 'FEYE', 'FAF', 'FCNCA', 'FDC', 'FHB', 'FHN', 'FRC', 'FSLR', 'FE', 'FISV', 'FLT', 'FLIR', 'FND', 'FLO', 'FLS', 'FLR', 'FMC', 'FNB', 'FNF', 'FL', 'F', 'FTNT', 'FTV', 'FBHS', 'FOXA', 'FOX', 'BEN', 'FCX', 'AJG', 'GLPI', 'GPS', 'EXAS', 'EXEL', 'EXC', 'GTES', 'GLIBA', 'GD', 'GE', 'GIS', 'GM', 'GWR', 'G', 'GNTX', 'GPC', 'GILD', 'GPN', 'GL', 'GDDY', 'GS', 'GT', 'GRA', 'GGG', 'EAF', 'GHC', 'GWW', 'LOPE', 'GPK', 'GRUB', 'GWRE', 'HAIN', 'HAL', 'HBI', 'THG', 'HOG', 'HIG', 'HAS', 'HE', 'HCA', 'HDS', 'HTA', 'PEAK', 'HEI.A', 'HEI', 'HP', 'JKHY', 'HLF', 'HSY', 'HES', 'GDI', 'GRMN', 'IT', 'HGV', 'HLT', 'HFC', 'HOLX', 'HD', 'HON', 'HRL', 'HST', 'HHC', 'HPQ', 'HUBB', 'HPP', 'HUM', 'HBAN', 'HII', 'HUN', 'H', 'IAC', 'ICUI', 'IEX', 'IDXX', 'INFO', 'ITW', 'ILMN', 'INCY', 'IR', 'INGR', 'PODD', 'IART', 'INTC', 'IBKR', 'ICE', 'IGT', 'IP', 'IPG', 'IBM', 'IFF', 'INTU', 'ISRG', 'IVZ', 'INVH', 'IONS', 'IPGP', 'IQV', 'HPE', 'HXL', 'HIW', 'HRC', 'JAZZ', 'JBHT', 'JBGS', 'JEF', 'JBLU', 'JNJ', 'JCI', 'JLL', 'JPM', 'JNPR', 'KSU', 'KAR', 'K', 'KEY', 'KEYS', 'KRC', 'KMB', 'KIM', 'KMI', 'KEX', 'KLAC', 'KNX', 'KSS', 'KOS', 'KR', 'LB', 'LHX', 'LH', 'LRCX', 'LAMR', 'LW', 'LSTR', 'LVS', 'LAZ', 'LEA', 'LM', 'LEG', 'LDOS', 'LEN', 'LEN.B', 'LII', 'LBRDA', 'LBRDK', 'FWONA', 'IRM', 'ITT', 'JBL', 'JEC', 'LLY', 'LECO', 'LNC', 'LGF.A', 'LGF.B', 'LFUS', 'LYV', 'LKQ', 'LMT', 'L', 'LOGM', 'LOW', 'LPLA', 'LULU', 'LYFT', 'LYB', 'MTB', 'MAC', 'MIC', 'M', 'MSG', 'MANH', 'MAN', 'MRO', 'MPC', 'MKL', 'MKTX', 'MAR', 'MMC', 'MLM', 'MRVL', 'MAS', 'MASI', 'MA', 'MTCH', 'MAT', 'MXIM', 'MKC', 'MCD', 'MCK', 'MDU', 'MPW', 'MD', 'MDT', 'MRK', 'FWONK', 'LPT', 'LSXMA', 'LSXMK', 'LSI', 'CPRI', 'MIK', 'MCHP', 'MU', 'MSFT', 'MAA', 'MIDD', 'MKSI', 'MHK', 'MOH', 'TAP', 'MDLZ', 'MPWR', 'MNST', 'MCO', 'MS', 'MORN', 'MOS', 'MSI', 'MSM', 'MSCI', 'MUR', 'MYL', 'NBR', 'NDAQ', 'NFG', 'NATI', 'NOV', 'NNN', 'NAVI', 'NCR', 'NKTR', 'NTAP', 'NFLX', 'NBIX', 'NRZ', 'NYCB', 'NWL', 'NEU', 'NEM', 'NWSA', 'NWS', 'MCY', 'MET', 'MTD', 'MFA', 'MGM', 'JWN', 'NSC', 'NTRS', 'NOC', 'NLOK', 'NCLH', 'NRG', 'NUS', 'NUAN', 'NUE', 'NTNX', 'NVT', 'NVDA', 'NVR', 'NXPI', 'ORLY', 'OXY', 'OGE', 'OKTA', 'ODFL', 'ORI', 'OLN', 'OHI', 'OMC', 'ON', 'OMF', 'OKE', 'ORCL', 'OSK', 'OUT', 'OC', 'OI', 'PCAR', 'PKG', 'PACW', 'PANW', 'PGRE', 'PK', 'PH', 'PE', 'PTEN', 'PAYX', 'PAYC', 'PYPL', 'NEE', 'NLSN', 'NKE', 'NI', 'NBL', 'NDSN', 'PEP', 'PKI', 'PRGO', 'PFE', 'PCG', 'PM', 'PSX', 'PPC', 'PNFP', 'PF', 'PNW', 'PXD', 'ESI', 'PNC', 'PII', 'POOL', 'BPOP', 'POST', 'PPG', 'PPL', 'PRAH', 'PINC', 'TROW', 'PFG', 'PG', 'PGR', 'PLD', 'PFPT', 'PB', 'PRU', 'PTC', 'PSA', 'PEG', 'PHM', 'PSTG', 'PVH', 'QGEN', 'QRVO', 'QCOM', 'PWR', 'PBF', 'PEGA', 'PAG', 'PNR', 'PEN', 'PBCT', 'RLGY', 'RP', 'O', 'RBC', 'REG', 'REGN', 'RF', 'RGA', 'RS', 'RNR', 'RSG', 'RMD', 'RPAI', 'RNG', 'RHI', 'ROK', 'ROL', 'ROP', 'ROST', 'RCL', 'RGLD', 'RES', 'RPM', 'RSPP', 'R', 'SPGI', 'SABR', 'SAGE', 'CRM', 'SC', 'SRPT', 'SBAC', 'HSIC', 'SLB', 'SNDR', 'SCHW', 'SMG', 'SEB', 'SEE', 'DGX', 'QRTEA', 'RL', 'RRC', 'RJF', 'RYN', 'RTN', 'NOW', 'SVC', 'SHW', 'SBNY', 'SLGN', 'SPG', 'SIRI', 'SIX', 'SKX', 'SWKS', 'SLG', 'SLM', 'SM', 'AOS', 'SJM', 'SNA', 'SON', 'SO', 'SCCO', 'LUV', 'SPB', 'SPR', 'SRC', 'SPLK', 'S', 'SFM', 'SQ', 'SSNC', 'SWK', 'SBUX', 'STWD', 'STT', 'STLD', 'SRCL', 'STE', 'STL', 'STOR', 'SYK', 'SUI', 'STI', 'SIVB', 'SWCH', 'SGEN', 'SEIC', 'SRE', 'ST', 'SCI', 'SERV', 'TPR', 'TRGP', 'TGT', 'TCO', 'TCF', 'AMTD', 'TDY', 'TFX', 'TDS', 'TPX', 'TDC', 'TER', 'TEX', 'TSRO', 'TSLA', 'TCBI', 'TXN', 'TXT', 'TFSL', 'CC', 'KHC', 'WEN', 'TMO', 'THO', 'TIF', 'TKR', 'TJX', 'TOL', 'TTC', 'TSCO', 'TDG', 'RIG', 'TRU', 'TRV', 'THS', 'TPCO', 'TRMB', 'TRN', 'TRIP', 'SYF', 'SNPS', 'SNV', 'SYY', 'DATA', 'TTWO', 'TMUS', 'TFC', 'UBER', 'UGI', 'ULTA', 'ULTI', 'UMPQ', 'UAA', 'UA', 'UNP', 'UAL', 'UPS', 'URI', 'USM', 'X', 'UTX', 'UTHR', 'UNH', 'UNIT', 'UNVR', 'OLED', 'UHS', 'UNM', 'URBN', 'USB', 'USFD', 'VFC', 'MTN', 'VLO', 'VMI', 'VVV', 'VAR', 'VVC', 'VEEV', 'VTR', 'VER', 'VRSN', 'VRSK', 'VZ', 'VSM', 'VRTX', 'VIAC', 'TWLO', 'TWTR', 'TWO', 'TYL', 'TSN', 'USG', 'UI', 'UDR', 'VMC', 'WPC', 'WBC', 'WAB', 'WBA', 'WMT', 'WM', 'WAT', 'WSO', 'W', 'WFTLF', 'WBS', 'WEC', 'WRI', 'WBT', 'WCG', 'WFC', 'WELL', 'WCC', 'WST', 'WAL', 'WDC', 'WU', 'WLK', 'WRK', 'WEX', 'WY', 'WHR', 'WTM', 'WLL', 'JW.A', 'WMB', 'WSM', 'WLTW', 'WTFC', 'WDAY', 'WP', 'WPX', 'WYND', 'WH', 'VIAB', 'VICI', 'VIRT', 'V', 'VC', 'VST', 'VMW', 'VNO', 'VOYA', 'ZAYO', 'ZBRA', 'ZEN', 'ZG', 'Z', 'ZBH', 'ZION', 'ZTS', 'ZNGA', 'WYNN', 'XEL', 'XRX', 'XLNX', 'XPO', 'XYL', 'YUMC', 'YUM']

        # nasdaq100: https://www.nasdaq.com/market-activity/quotes/nasdaq-ndx-index
        symbols_nasdaq_100_csv = [] # nasdaq100.csv
        nasdq100_filenames_list = ['Indices/nasdaq100.csv']
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

        # s&p500:
        symbols_snp500_download_csv = [] # snp500.csv
        symbols_snp500_download_filenames_list = ['Indices/snp500.csv']
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
        russel1000_filenames_wiki_list = ['Indices/Russel_1000_index_wiki.csv']
        for filename in russel1000_filenames_wiki_list:
            with open(filename, mode='r', newline='', encoding='cp1252') as engine:
                reader = csv.reader(engine, delimiter=',')
                for row in reader:
                    symbols_russel1000_wiki.append(row[1])


        symbols_russel1000_csv = []  # TODO: ASAFR: Make a general CSV reading function (with title row and withour, and which component in row to take, etc...
        russel1000_filenames_list = ['Indices/russell1000.csv']
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

    if tase_mode and not research_mode and build_csv_db:
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
    # Legend: http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs
    # ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt
    # ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt
    # ftp.nasdaqtrader.com/SymbolDirectory/nasdaqtraded.txt
    if not research_mode and build_csv_db:
        symbols_united_states               = []
        stocks_list_united_states_effective = []
        etf_and_nextshares_list             = []
        if read_united_states_input_symbols:
            nasdaq_filenames_list = ['Indices/nasdaqlisted.csv', 'Indices/otherlisted.csv', 'Indices/nasdaqtraded.csv']  # Checkout http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs for all symbol definitions (for instance - `$` in stock names, 5-letter stocks ending with `Y`)
            ticker_clumn_list     = [0,                          0,                         1                         ]  # nasdaqtraded.csv - 1st column is Y/N (traded or not) - so take row[1] instead!!!
            for index, filename in enumerate(nasdaq_filenames_list):
                with open(filename, mode='r', newline='') as engine:
                    reader = csv.reader(engine, delimiter='|')
                    next_shares_column = None
                    etf_column         = None
                    row_index = 0
                    for row in reader:
                        if row_index == 0:
                            row_index += 1
                            # Find ETF and next shares Column:
                            for column_index, column in enumerate(row):
                                if   column == 'ETF':        etf_column         = column_index
                                elif column == 'NextShares': next_shares_column = column_index
                            continue
                        else:
                            row_index += 1
                            if next_shares_column and row[next_shares_column] == 'Y':
                                etf_and_nextshares_list.append(row[ticker_clumn_list[index]])
                                continue
                            if etf_column         and row[etf_column]         == 'Y':
                                etf_and_nextshares_list.append(row[ticker_clumn_list[index]])
                                continue
                            if '$' in row[ticker_clumn_list[index]]: # AAIC$B -> <stock_symbol>$<letter> --> keep just the stock_Symbol
                                stock_symbol = row[ticker_clumn_list[index]].split('$')[0]
                            else:
                                stock_symbol = row[ticker_clumn_list[index]]
                            if len(stock_symbol) == 5: # https://www.investopedia.com/ask/answers/06/nasdaqfifthletter.asp
                                if stock_symbol[4] in ['Q', 'W', 'C']: # Q: Bankruptcy, W: Warrant, C: Nextshares (Example: https://funds.eatonvance.com/includes/loadDocument.php?fn=20939.pdf&dt=fundPDFs)
                                    continue
                                if stock_symbol[4] in ['Y'] and SKIP_5LETTER_Y_STOCK_LISTINGS: # Configurable - harder to buy (from Israel, at least), but not impossible of coure
                                    continue
                            elif len(stock_symbol) == 6: # https://www.investopedia.com/ask/answers/06/nasdaqfifthletter.asp
                                if stock_symbol[5] in ['Q', 'W', 'C']: # Q: Bankruptcy, W: Warrant, C: Nextshares (Example: https://funds.eatonvance.com/includes/loadDocument.php?fn=20939.pdf&dt=fundPDFs)
                                    continue
                                if stock_symbol[5] in ['Y'] and SKIP_5LETTER_Y_STOCK_LISTINGS: # Configurable - harder to buy (from Israel, at least), but not impossible of coure
                                    continue
                            symbols_united_states.append(stock_symbol)

            if use_investpy:
                stocks_list_united_states = investpy.get_stocks_list(country='united states')
                for stock_symbol in stocks_list_united_states:
                    if stock_symbol in etf_and_nextshares_list: continue
                    if len(stock_symbol) == 5:  # https://www.investopedia.com/ask/answers/06/nasdaqfifthletter.asp
                        if stock_symbol[4] in ['Q', 'W', 'C']:  # Q: Bankruptcy, W: Warrant, C: Nextshares (Example: https://funds.eatonvance.com/includes/loadDocument.php?fn=20939.pdf&dt=fundPDFs)
                            continue
                        if stock_symbol[4] in [ 'Y'] and SKIP_5LETTER_Y_STOCK_LISTINGS:  # Configurable - harder to buy (from Israel, at least), but not impossible of coure
                            continue
                    elif len(stock_symbol) == 6:  # https://www.investopedia.com/ask/answers/06/nasdaqfifthletter.asp
                        if stock_symbol[5] in ['Q', 'W', 'C']:  # Q: Bankruptcy, W: Warrant, C: Nextshares (Example: https://funds.eatonvance.com/includes/loadDocument.php?fn=20939.pdf&dt=fundPDFs)
                            continue
                        if stock_symbol[5] in ['Y'] and SKIP_5LETTER_Y_STOCK_LISTINGS:  # Configurable - harder to buy (from Israel, at least), but not impossible of coure
                            continue
                    stocks_list_united_states_effective.append(stock_symbol)
        symbols = symbols_snp500 + symbols_snp500_download + symbols_nasdaq100 + symbols_nasdaq_100_csv + symbols_russel1000 + symbols_russel1000_csv + symbols_united_states + stocks_list_united_states_effective

    if not research_mode and tase_mode and build_csv_db:
        symbols = symbols_tase + stocks_list_tase

    if not research_mode and build_csv_db: symbols = sorted(list(set(symbols)))

    # Temporary to test and debug: DEBUG MODE
    # =======================================
    if len(custom_portfolio):
        symbols = custom_portfolio

    if not research_mode: print('\n{} Symbols for SSS to Scan (Using {} threads): {}\n'.format(len(symbols), num_threads, symbols))

    csv_db_data   = [];	rows   = []; rows_no_div   = []; rows_only_div   = []; rows_diff   = []
    csv_db_data0  = []; rows0  = []; rows0_no_div  = []; rows0_only_div  = []; rows0_diff  = []; csv_db_data1  = []; rows1  = []; rows1_no_div  = []; rows1_only_div  = []; rows1_diff  = []
    csv_db_data2  = []; rows2  = []; rows2_no_div  = []; rows2_only_div  = []; rows2_diff  = []; csv_db_data3  = []; rows3  = []; rows3_no_div  = []; rows3_only_div  = []; rows3_diff  = []
    csv_db_data4  = []; rows4  = []; rows4_no_div  = []; rows4_only_div  = []; rows4_diff  = []; csv_db_data5  = []; rows5  = []; rows5_no_div  = []; rows5_only_div  = []; rows5_diff  = []
    csv_db_data6  = []; rows6  = []; rows6_no_div  = []; rows6_only_div  = []; rows6_diff  = []; csv_db_data7  = []; rows7  = []; rows7_no_div  = []; rows7_only_div  = []; rows7_diff  = []
    csv_db_data8  = []; rows8  = []; rows8_no_div  = []; rows8_only_div  = []; rows8_diff  = []; csv_db_data9  = []; rows9  = []; rows9_no_div  = []; rows9_only_div  = []; rows9_diff  = []
    csv_db_data10 = []; rows10 = []; rows10_no_div = []; rows10_only_div = []; rows10_diff = []; csv_db_data11 = []; rows11 = []; rows11_no_div = []; rows11_only_div = []; rows11_diff = []
    csv_db_data12 = []; rows12 = []; rows12_no_div = []; rows12_only_div = []; rows12_diff = []; csv_db_data13 = []; rows13 = []; rows13_no_div = []; rows13_only_div = []; rows13_diff = []
    csv_db_data14 = []; rows14 = []; rows14_no_div = []; rows14_only_div = []; rows14_diff = []; csv_db_data15 = []; rows15 = []; rows15_no_div = []; rows15_only_div = []; rows15_diff = []
    csv_db_data16 = []; rows16 = []; rows16_no_div = []; rows16_only_div = []; rows16_diff = []; csv_db_data17 = []; rows17 = []; rows17_no_div = []; rows17_only_div = []; rows17_diff = []
    csv_db_data18 = []; rows18 = []; rows18_no_div = []; rows18_only_div = []; rows18_diff = []; csv_db_data19 = []; rows19 = []; rows19_no_div = []; rows19_only_div = []; rows19_diff = []

    if build_csv_db == 0: # if DB is already present, read from it and prepare input to threads
        symbols = []
        csv_db_filename = csv_db_path+'/'+db_filename
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

    if num_threads ==  1:
        process_symbols(symbols0, csv_db_data0, rows0, rows0_no_div, rows0_only_div, 0, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows0_diff)
    elif num_threads >= 1:
        check_interval(0, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread0  = Thread(target=process_symbols, args=(symbols0,  csv_db_data0,  rows0,  rows0_no_div,  rows0_only_div,   0, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows0_diff))
        thread0.start()
    if num_threads >=  2:
        check_interval(1, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread1  = Thread(target=process_symbols, args=(symbols1,  csv_db_data1,  rows1,  rows1_no_div,  rows1_only_div,   1, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows1_diff))
        thread1.start()
    if num_threads >=  3:
        check_interval(2, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread2  = Thread(target=process_symbols, args=(symbols2,  csv_db_data2,  rows2,  rows2_no_div,  rows2_only_div,   2, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows2_diff))
        thread2.start()
    if num_threads >=  4:
        check_interval(3, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread3  = Thread(target=process_symbols, args=(symbols3,  csv_db_data3,  rows3,  rows3_no_div,  rows3_only_div,   3, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows3_diff))
        thread3.start()
    if num_threads >=  5:
        check_interval(4, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread4  = Thread(target=process_symbols, args=(symbols4,  csv_db_data4,  rows4,  rows4_no_div,  rows4_only_div,   4, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows4_diff))
        thread4.start()
    if num_threads >=  6:
        check_interval(5, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread5  = Thread(target=process_symbols, args=(symbols5,  csv_db_data5,  rows5,  rows5_no_div,  rows5_only_div,   5, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows5_diff))
        thread5.start()
    if num_threads >=  7:
        check_interval(6, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread6  = Thread(target=process_symbols, args=(symbols6,  csv_db_data6,  rows6,  rows6_no_div,  rows6_only_div,   6, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows6_diff))
        thread6.start()
    if num_threads >=  8:
        check_interval(7, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread7  = Thread(target=process_symbols, args=(symbols7,  csv_db_data7,  rows7,  rows7_no_div,  rows7_only_div,   7, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows7_diff))
        thread7.start()
    if num_threads >=  9:
        check_interval(8, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread8  = Thread(target=process_symbols, args=(symbols8,  csv_db_data8,  rows8,  rows8_no_div,  rows8_only_div,   8, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows8_diff))
        thread8.start()
    if num_threads >= 10:
        check_interval(9, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread9  = Thread(target=process_symbols, args=(symbols9,  csv_db_data9,  rows9,  rows9_no_div,  rows9_only_div,   9, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows9_diff))
        thread9.start()
    if num_threads >= 11:
        check_interval(10, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread10 = Thread(target=process_symbols, args=(symbols10, csv_db_data10, rows10, rows10_no_div, rows10_only_div, 10, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows10_diff))
        thread10.start()
    if num_threads >= 12:
        check_interval(11, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread11 = Thread(target=process_symbols, args=(symbols11, csv_db_data11, rows11, rows11_no_div, rows11_only_div, 11, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows11_diff))
        thread11.start()
    if num_threads >= 13:
        check_interval(12, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread12 = Thread(target=process_symbols, args=(symbols12, csv_db_data12, rows12, rows12_no_div, rows12_only_div, 12, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows12_diff))
        thread12.start()
    if num_threads >= 14:
        check_interval(13, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread13 = Thread(target=process_symbols, args=(symbols13, csv_db_data13, rows13, rows13_no_div, rows13_only_div, 13, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows13_diff))
        thread13.start()
    if num_threads >= 15:
        check_interval(14, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread14 = Thread(target=process_symbols, args=(symbols14, csv_db_data14, rows14, rows14_no_div, rows14_only_div, 14, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows14_diff))
        thread14.start()
    if num_threads >= 16:
        check_interval(15, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread15 = Thread(target=process_symbols, args=(symbols15, csv_db_data15, rows15, rows15_no_div, rows15_only_div, 15, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows15_diff))
        thread15.start()
    if num_threads >= 17:
        check_interval(16, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread16 = Thread(target=process_symbols, args=(symbols16, csv_db_data16, rows16, rows16_no_div, rows16_only_div, 16, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows16_diff))
        thread16.start()
    if num_threads >= 18:
        check_interval(17, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread17 = Thread(target=process_symbols, args=(symbols17, csv_db_data17, rows17, rows17_no_div, rows17_only_div, 17, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows17_diff))
        thread17.start()
    if num_threads >= 19:
        check_interval(18, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread18 = Thread(target=process_symbols, args=(symbols18, csv_db_data18, rows18, rows18_no_div, rows18_only_div, 18, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows18_diff))
        thread18.start()
    if num_threads >= 20:
        check_interval(19, interval_threads, interval_secs_to_avoid_http_errors, research_mode)
        thread19 = Thread(target=process_symbols, args=(symbols19, csv_db_data19, rows19, rows19_no_div, rows19_only_div, 19, build_csv_db_only, use_investpy, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, build_csv_db, relaxed_access, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, min_enterprise_value_millions_usd, eqg_min, revenue_quarterly_growth_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, market_cap_included, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, rows19_diff))
        thread19.start()

    if num_threads == 1:
        pass
    elif num_threads >=  1: thread0.join()
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
    rows_diff.extend(    rows0_diff     + rows1_diff     + rows2_diff     + rows3_diff     + rows4_diff     + rows5_diff     + rows6_diff     + rows7_diff     + rows8_diff     + rows9_diff     + rows10_diff     + rows11_diff     + rows12_diff     + rows13_diff     + rows14_diff     + rows15_diff     + rows16_diff     + rows17_diff     + rows18_diff     + rows19_diff    )

    # remove (from rows, not from db or diff) rows whose sss[s[s]]_value is a bad one - irrelevant:
    compact_rows          = []
    compact_rows_no_div   = []
    compact_rows_only_div = []
    for row in rows:
        if row[g_sss_value_index] != BAD_SSS: compact_rows.append(row)
    for row_no_div in rows_no_div:
        if row_no_div[g_sss_value_index] != BAD_SSS: compact_rows_no_div.append(row_no_div)
    for row_only_div in rows_only_div:
        if row_only_div[g_sss_value_index] != BAD_SSS: compact_rows_only_div.append(row_only_div)

    # Now, Sort the compact_rows using the sss_value formula: [1:] skips the 1st title row
    sorted_list_db               = sorted(csv_db_data,           key=lambda row:          row[g_symbol_index],                 reverse=False)  # Sort by symbol
    sorted_list_sss              = sorted(compact_rows,          key=lambda row:          row[g_sss_value_index   ],           reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
    sorted_list_sss_no_div       = sorted(compact_rows_no_div,   key=lambda row_no_div:   row_no_div[g_sss_value_index   ],    reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
    sorted_list_sss_only_div     = sorted(compact_rows_only_div, key=lambda row_only_div: row_only_div[g_sss_value_index   ],  reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
    sorted_list_diff             = sorted(rows_diff,             key=lambda row_diff:     row_diff[g_symbol_index   ],         reverse=False)  # Sort by symbol

    if research_mode: # Update the appearance counter
        list_len_sss = len(sorted_list_sss)
        if appearance_counter_min <= list_len_sss   <= appearance_counter_max:
            for index, row in enumerate(sorted_list_sss):
                # Debug mode:
                # if 'ISRA-L' in row[g_symbol_index]:
                #     print('ISRA-L - index is {}'.format(index))
                appearance_counter_dict_sss[  (row[g_symbol_index],row[g_name_index],row[g_sector_index],row[g_sss_value_index],  row[g_previous_close_index])] = appearance_counter_dict_sss[  (row[g_symbol_index],row[g_name_index],row[g_sector_index],row[g_sss_value_index],  row[g_previous_close_index])]+math.sqrt(float(list_len_sss  -index))/float(list_len_sss  )

    sorted_lists_list = [
        sorted_list_db,
        sorted_list_sss,
        sorted_list_sss_no_div,
        sorted_list_sss_only_div,
        sorted_list_diff
    ]

    for sorted_list in sorted_lists_list:
        sorted_list.insert(0, g_header_row)

    tase_str              = ""
    sectors_str           = ""
    countries_str         = ""
    all_str               = ""
    csv_db_str            = ""
    investpy_str          = ""
    custom_portfolio_str  = ""
    num_results_str       = "_nRes{}".format(len(compact_rows))
    build_csv_db_only_str = ""
    if tase_mode:         tase_str       = "_Tase"

    if len(sectors_list):
        if sectors_filter_out:
            sectors_list       += 'FO_'
        sectors_str            += '_'+'_'.join(sectors_list)
    else:
        for index, sector in enumerate(favor_sectors):
            sectors_str += '_{}{}'.format(sector.replace(' ',''),round(favor_sectors_by[index],NUM_ROUND_DECIMALS))

    if len(countries_list):
        if countries_filter_out:
            countries_list       += 'FO_'
        countries_str            += '_'+'_'.join(countries_list).replace(' ','')

    mode_str = 'Nsr' # Default is Nasdaq100+S&P500+Russel1000
    if read_united_states_input_symbols: mode_str              = 'All'
    elif tase_mode:                      mode_str              = 'Tase'
    if   len(custom_portfolio):          mode_str              = 'Custom'
    if read_united_states_input_symbols: all_str               = '_A'
    if build_csv_db == 0:                csv_db_str            = '_DBR'
    if use_investpy:                     investpy_str          = '_Investpy'
    if build_csv_db_only:                build_csv_db_only_str = '_Bdb'
    if len(custom_portfolio):            custom_portfolio_str  = '_Custom'
    date_and_time = time.strftime("Results/{}/%Y%m%d-%H%M%S{}{}{}{}{}{}{}{}{}".format(mode_str, tase_str, sectors_str.replace(' ','').replace('a','').replace('e','').replace('i','').replace('o','').replace('u',''), countries_str, all_str, csv_db_str, investpy_str, build_csv_db_only_str, num_results_str, custom_portfolio_str))

    filenames_list = sss_filenames.create_filenames_list(date_and_time)

    evr_pm_col_title_row = ['Maximal price_to_earnings_limit: {}, Maximal enterprise_value_to_revenue_limit: {}, Minimal profit_margin_limit: {}'.format(price_to_earnings_limit, enterprise_value_to_revenue_limit, profit_margin_limit)]

    if generate_result_folders:
        for index in range(len(filenames_list)):
            os.makedirs(os.path.dirname(filenames_list[index]), exist_ok=True)
            with open(filenames_list[index], mode='w', newline='') as engine:
                writer = csv.writer(engine)
                sorted_lists_list[index].insert(0, evr_pm_col_title_row)
                writer.writerows(sorted_lists_list[index])

    return len(compact_rows)
