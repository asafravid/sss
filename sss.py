#############################################################################
#
# Version 0.2.97 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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


# TODO: ASAFR:  0. Auto-Update Nasdaq (NSR) Indices as done with TASE
#               0.1. Add All Swiss   Stocks to A dedicated scan: https://www.six-group.com/en/products-services/the-swiss-stock-exchange/market-data/shares/closing-prices.html, https://www.six-group.com/fqs/closing.csv?select=ShortName,ISIN,ValorSymbol,ValorNumber,ClosingPrice,DailyHighPrice,DailyLowPrice,LatestTradeDate,PreviousClosingPrice,OpeningPrice,OnMarketVolume,OffBookVolume,SwissAtMidVolume,TotalVolume,TradingBaseCurrency,YearlyHighDate,YearlyHighPrice,YearlyLowDate,YearlyLowPrice,FirstTradingDate,LastTradingDate,Exchange,SecTypeCode,GeographicalAreaCode,Tminus1Volume,VWAP60Price&where=ProductLine=BC&orderby=ShortName&page=1&pagesize=9999999
#               1.0. https://en.wikipedia.org/wiki/Piotroski_F-score
#               1.2. https://en.wikipedia.org/wiki/Magic_formula_investing
#               1.3. https://www.oldschoolvalue.com/investing-strategy/backtest-graham-nnwc-ncav-screen/
#               2. Back to Investpy to download all Japanese stocks and all swiss stocks (and all swedish stocks!)
#               3. Investigate and add: https://www.investopedia.com/terms/o/operatingmargin.asp - operating margin
#               4. Add Free Cash flow [FCF] (EV/FreeCashFlow): Inverse of the Free Cash Flow Yield (https://www.stockopedia.com/ratios/ev-free-cash-flow-336/
#               5. There is already an EV/CFO ratio.
#                    CFO - CapitalExpenditures = FCF
#                    EV/CFO * EV/FCF = EV^2 / (CFO * [CFO - CapitalExpenditures]) | EV/CFO + EV/FCF = EV*(1/CFO + 1/(CFO-CapitalExpenditures))
#                    Conclusion: EV/FCF is better as it provides moe information. But make this a lower priority for development
#                                Bonus: When there is no CFO, Use FCF, and Vice Versa - more information
#               6. Which are the most effective parameters? Correlate the sorting of sss_value to the results and each of the sorted-by-parameter list.
#               7. Important: https://www.oldschoolvalue.com/investing-strategy/walter-schloss-investing-strategy-producing-towering-returns/
#                  7.1.  3 years low, 5 years low
#                  7.2.  F-Score, M-Score
#                  7.3.  Multi-Dim scan over the distance from low, and over the Schloff Score - define a Walter-Schloss score
#                  7.4.  Remove the square root from DtoE ?
#                  7.5.  MktCapM is >= US$ 300 million (basis year 2000) adjusted yearly
#                  7.6.  Consider only stocks that are listed at least 10 years
#                  7.8.  Calculate share_price/52weekLow 0.1
#                  7.9.  Take the top 500 stocks with highest Current Dividend Yield %#            12. https://pyportfolioopt.readthedocs.io/en/latest/UserGuide.html -> Use
#                  7.10. Take the top 250 stocks with lowest Latest Filing P/E ratio#            13. Calculate the ROE - Return on equity
#                  7.11. Take the top 125 stocks with lowest Latest Filing P/B ratio#            14. Operating Cash Flow Growth - interesting: https://github.com/JerBouma/FundamentalAnalysis
#                  7.12. Take the top 75 stocks with lowest Latest Filing Long Term Debt#            15. Quick Ratio - https://github.com/JerBouma/FinanceDatabase - interesting


import time
import shutil
import urllib.request as request
import pandas         as pd
import yfinance       as yf
import csv
import os
import sss_filenames
import sss_indices
import sss_config
import sss_post_processing
import math
import json
import traceback

from contextlib             import closing
from dataclasses            import dataclass
from forex_python.converter import CurrencyRates
from currency_converter     import CurrencyConverter


VERBOSE_LOGS = 0

SKIP_5LETTER_Y_STOCK_LISTINGS                = False       # Skip ADRs - American Depositary receipts (5 Letter Stocks)
NUM_ROUND_DECIMALS                           = 7
NUM_EMPLOYEES_UNKNOWN                        = 10000000   # This will make the company very inefficient in terms of number of employees
PROFIT_MARGIN_UNKNOWN                        = 0.00001    # This will make the company almost not profitable terms of profit margins, thus less attractive
PRICE_TO_BOOK_UNKNOWN                        = 1000.0
PERCENT_HELD_INSTITUTIONS_LOW                = 0.01       # low, to make less relevant
PERCENT_HELD_INSIDERS_UNKNOWN                = 0.0000123  # Temporary check, TODO: ASAFR: Take some unknown value (low) instead for the actual usage in Schloss factor
PEG_UNKNOWN                                  = 10000      # Use a non-attractive value
QEG_MAX                                      = 10000
REG_MAX                                      = 10000
SHARES_OUTSTANDING_UNKNOWN                   = 100000000  # 100 Million Shares - just a value for calculation of a currently unused vaue
BAD_SSS                                      = 10.0 ** 50.0
PROFIT_MARGIN_WEIGHTS                        = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0,   512.0]  # from oldest to newest
PROFIT_MARGIN_YEARLY_WEIGHTS                 = [1.0, 4.0, 16,  64,  256,  1024, 4096, 16384, 4*16384, 16*16384]  # from oldest to newest
PROFIT_MARGIN_QUARTERLY_WEIGHTS              = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0,   512.0]  # from oldest to newest
CASH_FLOW_WEIGHTS                            = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0,   512.0]  # from oldest to newest
REVENUES_WEIGHTS                             = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0,   512.0]  # from oldest to newest
NO_WEIGHTS                                   = [1.0, 1.0, 1.0, 1.0,  1.0,  1.0,  1.0,   1.0,   1.0,     1.0]  # from oldest to newest
EARNINGS_WEIGHTS                             = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0,   512.0]  # from oldest to newest
BALANCE_SHEETS_WEIGHTS                       = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0,   512.0]  # from oldest to newest
EQG_UNKNOWN                                  = -0.9   # -90% TODO: ASAFR: 1. Scan (like pm and ever) values of eqg for big data research better recommendations
RQG_UNKNOWN                                  = -0.9   # -90% TODO: ASAFR: 1. Scan (like pm and ever) values of rqg for big data research better recommendations
EQG_POSITIVE_FACTOR                          = 10.0   # When positive, it will have a 5x factor on the 1 + function
RQG_POSITIVE_FACTOR                          = 10.0   # When positive, it will have a 5x factor on the 1 + function
EQG_WEIGHT_VS_YOY                            = 0.75   # the provided EQG is weighted more than the manually calculated one
RQG_WEIGHT_VS_YOY                            = 0.75   # the provided RQG (yfinance now provides it) is weighted more than the manually calculated one
EQG_DAMPER                                   = 0.25
RQG_DAMPER                                   = 0.25
TRAILING_EPS_PERCENTAGE_DAMP_FACTOR          = 0.01  # When the trailing_eps_percentage is very low (units are ratio here), this damper shall limit the affect to x100 not more)
PROFIT_MARGIN_DAMPER                         = 0.001 # When the profit_margin                   is very low (units are ratio here), this damper shall limit the affect to x100 not more)
RATIO_DAMPER                                 = 0.01  # When the total/current_other_other ratio is very low (units are ratio here), this damper shall limit the affect to x100 not more)
ROA_DAMPER                                   = 0.1   # When the ROA is very low (units are ratio here), this damper shall limit the affect to x50 not more)
ROA_NEG_FACTOR                               = 0.000001
ROE_DAMPER                                   = 0.1   # When the ROE is very low (units are ratio here), this damper shall limit the affect to x50 not more)
ROE_NEG_FACTOR                               = 0.000001
REFERENCE_DB_MAX_VALUE_DIFF_FACTOR_THRESHOLD = 0.9   # if there is a parameter difference from reference db, in which the difference of values is higher than 0.75*abs(max_value) then something went wrong with the fetch of values from yfinance. Compensate smartly from reference database
QUARTERLY_YEARLY_MISSING_FACTOR              = 0.25  # if either yearly or quarterly values are missing - compensate by other with bad factor (less information means less attractive)
NEGATIVE_ALTMAN_Z_FACTOR                     = 0.00001
MIN_REVENUE_FOR_0_REVENUE_DIV_BY_0_AVOIDANCE = 0.001
MAX_UNKNOWN_PE                               = 100000

# TODO: ASAFR: All below boosters should be calibrated by:
#              1. The rarety (statistically comapred to all the stocks in scan) - proportionaly to it (the rarest the case - the more boost)
#              2. The ascent (slope) of the increase and the positive value -> the higher - the more boost
#              3. Add similar boosters for other annual and quarterly weighted-averaged parameters
PROFIT_MARGIN_BOOST_FOR_PRESENCE_OF_ANNUAL_NEGATIVE_EARNINGS      = 0.025 if sss_config.custom_sss_value_equation else 0.1
PROFIT_MARGIN_BOOST_FOR_PRESENCE_OF_QUARTERLY_NEGATIVE_EARNINGS   = 0.025 if sss_config.custom_sss_value_equation else 0.1
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE                = 10.0  if sss_config.custom_sss_value_equation else 3.75   # Provide a "bonus" for companies whose profit margins have increased continuously annually
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE             = 10.0  if sss_config.custom_sss_value_equation else 2.25   # Provide a "bonus" for companies whose profit margins have increased continuously quarterly
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_POSITIVE                = 10.0  if sss_config.custom_sss_value_equation else 4.75   # Provide a "bonus" for companies whose profit margins have been continuously positive annually
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_POSITIVE             = 10.0  if sss_config.custom_sss_value_equation else 2.75   # Provide a "bonus" for companies whose profit margins have been continuously positive quarterly
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_EARNINGS    = 10.0  if sss_config.custom_sss_value_equation else 4.25   # Provide a "bonus" for companies whose earnings       have been continuously increasing annually
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_REVENUE     = 14.0  if sss_config.custom_sss_value_equation else 7.77   # Provide a "bonus" for companies whose revenue        has  been continuously increasing annually - TODO: ASAFR: This is a very good indicator for stock value growth
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_EARNINGS = 10.0  if sss_config.custom_sss_value_equation else 3.25   # Provide a "bonus" for companies whose earnings       have been continuously increasing quarterly
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_REVENUE  = 25.0  if sss_config.custom_sss_value_equation else 9.99   # Provide a "bonus" for companies whose revenue        has  been continuously increasing quarterly - TODO: ASAFR: This is a very good indicator for stock value growth
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE                = 0.05  if sss_config.custom_sss_value_equation else 0.25   # Provide a "bonus" for companies whose profit margins have decreased continuously annually
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE             = 0.05  if sss_config.custom_sss_value_equation else 0.25   # Provide a "bonus" for companies whose profit margins have decreased continuously quarterly
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE_IN_EARNINGS    = 0.05  if sss_config.custom_sss_value_equation else 0.25   # Provide a "bonus" for companies whose earnings       have been continuously decreasing annually
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE_IN_REVENUE     = 0.05  if sss_config.custom_sss_value_equation else 0.2    # Provide a "bonus" for companies whose revenue        has  been continuously decreasing annually - TODO: ASAFR: This is a very good indicator for stock value growth
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE_IN_EARNINGS = 0.05  if sss_config.custom_sss_value_equation else 0.25   # Provide a "bonus" for companies whose earnings       have been continuously decreasing quarterly
PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE_IN_REVENUE  = 0.05  if sss_config.custom_sss_value_equation else 0.1    # Provide a "bonus" for companies whose revenue        has  been continuously decreasing quarterly - TODO: ASAFR: This is a very good indicator for stock value growth
PROFIT_MARGIN_DUPLICATION_FACTOR                                  = 8.0    # When copying profit margin (if either quarterized/annualized/profit_margin is missing) - devide by this factor
NEGATIVE_CFO_FACTOR                                               = 100000.0   #
NEGATIVE_PEG_RATIO_FACTOR                                         = 100000.0
NEGATIVE_DEBT_TO_EQUITY_FACTOR                                    = 100.0   # -0.5 -> 50, and -0.001 -> 0.1
NEGATIVE_EARNINGS_FACTOR                                          = 100000.0
DEBT_TO_EQUITY_MIN_BASE                                           = 0.001  # Clearing from 0 values for companies without debt

FORWARD_PRICE_TO_EARNINGS_WEIGHT  = 0.125 # Give less weight to forward (estimation)
TRAILING_PRICE_TO_EARNINGS_WEIGHT = 1-FORWARD_PRICE_TO_EARNINGS_WEIGHT

DIST_FROM_LOW_FACTOR_DAMPER                = 0.001
DIST_FROM_LOW_FACTOR_HIGHER_THAN_ONE_POWER = 6

EV_TO_EBITDA_MAX_UNKNOWN = 100000

#
# TODO: ASAFR: (https://www.gurufocus.com/letter.php)
#              1. Add Free Cash Flow
#              2. Lower Market Cap - Give more weight (in multi-dimensional scan)
#              3. Start adjusting the normalized sss_value flow - those companies which are "deceiving" -> fix according to them

@dataclass
class StockData:
    symbol:                                               str   = 'None'
    short_name:                                           str   = 'None'
    quote_type:                                           str   = 'None'
    sector:                                               str   = 'None'
    country:                                              str   = 'Unknown'
    sss_value:                                            float = BAD_SSS
    annualized_revenue:                                   float = 0.0
    annualized_revenue_bonus:                             float = 0.0
    annualized_earnings:                                  float = 0.0  # TODO: ASAFR: Add the bonus calculations (pos, neg, mon_inc, mon_dec, etc)
    annualized_retained_earnings:                         float = 0.0
    annualized_retained_earnings_bonus:                   float = 0.0
    quarterized_revenue:                                  float = 0.0
    quarterized_revenue_bonus:                            float = 0.0
    quarterized_earnings:                                 float = 0.0
    quarterized_earnings_bonus:                           float = 0.0
    quarterized_retained_earnings:                        float = 0.0
    quarterized_retained_earnings_bonus:                  float = 0.0
    effective_earnings:                                   float = 0.0
    effective_retained_earnings:                          float = 0.0
    effective_revenue:                                    float = 0.0
    annualized_total_revenue:                             float = 0.0
    annualized_total_revenue_bonus:                       float = 0.0
    annualized_net_income:                                float = 0.0   # TODO: ASAFR: Add the bonus calculations (pos, neg, mon_inc, mon_dec, etc)
    quarterized_total_revenue:                            float = 0.0
    quarterized_total_revenue_bonus:                      float = 0.0
    quarterized_net_income:                               float = 0.0
    quarterized_net_income_bonus:                         float = 0.0
    effective_net_income:                                 float = 0.0
    effective_total_revenue:                              float = 0.0
    enterprise_value_to_revenue:                          float = 0.0
    evr_effective:                                        float = 0.0
    trailing_price_to_earnings:                           float = 0.0
    forward_price_to_earnings:                            float = 0.0
    effective_price_to_earnings:                          float = 0.0
    trailing_12months_price_to_sales:                     float = 0.0
    pe_effective:                                         float = 0.0
    enterprise_value_to_ebitda:                           float = 0.0
    effective_ev_to_ebitda:                               float = 0.0
    ebitda:                                               float = 0.0
    quarterized_ebitd:                                    float = 0.0
    annualized_ebitd:                                     float = 0.0
    ebitd:                                                float = 0.0
    profit_margin:                                        float = 0.0
    annualized_profit_margin:                             float = 0.0
    annualized_profit_margin_boost:                       float = 0.0
    quarterized_profit_margin:                            float = 0.0
    quarterized_profit_margin_boost:                      float = 0.0
    effective_profit_margin:                              float = 0.0
    held_percent_institutions:                            float = 0.0
    held_percent_insiders:                                float = 0.0
    forward_eps:                                          float = 0.0
    trailing_eps:                                         float = 0.0
    previous_close:                                       float = 0.0
    trailing_eps_percentage:                              float = 0.0 # trailing_eps / previousClose
    price_to_book:                                        float = 0.0
    shares_outstanding:                                   float = 0.0
    net_income_to_common_shareholders:                    float = 0.0
    nitcsh_to_shares_outstanding:                         float = 0.0
    employees:                                            int   = 0
    enterprise_value:                                     int   = 0
    market_cap:                                           int   = 0
    nitcsh_to_num_employees:                              float = 0.0
    eqg:                                                  float = 0.0  # Value is a ratio, such that when multiplied by 100, yields percentage (%) units
    rqg:                                                  float = 0.0  # Value is a ratio, such that when multiplied by 100, yields percentage (%) units
    eqg_yoy:                                              float = 0.0  # calculated from the yearly earnings - if available
    rqg_yoy:                                              float = 0.0  # calculated from the yearly Revenues - if available
    niqg_yoy:                                             float = 0.0  # Net Income Quarterly Growth: calculated from the yearly net income - if available
    trqg_yoy:                                             float = 0.0  # Total Revenue Quarterly Growth: calculated from the yearly net income - if available
    eqg_effective:                                        float = 0.0  # average of eqg_yoy and eqg
    eqg_factor_effective:                                 float = 0.0  # function with positive factor and damper
    rqg_effective:                                        float = 0.0  # average of rqg_yoy and rqg
    rqg_factor_effective:                                 float = 0.0  # function with positive factor and damper
    price_to_earnings_to_growth_ratio:                    float = 0.0
    effective_peg_ratio:                                  float = 0.0
    annualized_cash_flow_from_operating_activities:       float = 0.0
    annualized_cash_flow_from_operating_activities_bonus: float = 0.0
    quarterized_cash_flow_from_operating_activities:      float = 0.0
    quarterized_cash_flow_from_operating_activities_bonus:float = 0.0
    annualized_ev_to_cfo_ratio:                           float = 0.0  # https://investinganswers.com/dictionary/e/enterprise-value-cash-flow-operations-evcfo
    quarterized_ev_to_cfo_ratio:                          float = 0.0  # https://investinganswers.com/dictionary/e/enterprise-value-cash-flow-operations-evcfo
    ev_to_cfo_ratio_effective:                            float = 0.0
    annualized_debt_to_equity:                            float = 0.0
    annualized_debt_to_equity_bonus:                      float = 0.0
    quarterized_debt_to_equity:                           float = 0.0
    quarterized_debt_to_equity_bonus:                     float = 0.0
    debt_to_equity_effective:                             float = 0.0
    debt_to_equity_effective_used:                        float = 0.0
    financial_currency:                                   str   = 'None'
    summary_currency:                                     str   = 'None'
    financial_currency_conversion_rate_mult_to_usd:       float = 0.0
    summary_currency_conversion_rate_mult_to_usd:         float = 0.0
    last_dividend_0:                                      float = 0.0
    last_dividend_1:                                      float = 0.0
    last_dividend_2:                                      float = 0.0
    last_dividend_3:                                      float = 0.0
    fifty_two_week_change:                                float = 0.0
    fifty_two_week_low:                                   float = 0.0
    fifty_two_week_high:                                  float = 0.0
    two_hundred_day_average:                              float = 0.0
    previous_close_percentage_from_200d_ma:               float = 0.0
    previous_close_percentage_from_52w_low:               float = 0.0
    previous_close_percentage_from_52w_high:              float = 0.0
    dist_from_low_factor:                                 float = 0.0
    eff_dist_from_low_factor:                             float = 0.0
    annualized_total_ratio:                               float = 0.0
    annualized_total_ratio_bonus:                         float = 0.0
    quarterized_total_ratio:                              float = 0.0
    quarterized_total_ratio_bonus:                        float = 0.0
    annualized_other_current_ratio:                       float = 0.0
    annualized_other_current_ratio_bonus:                 float = 0.0
    quarterized_other_current_ratio:                      float = 0.0
    quarterized_other_current_ratio_bonus:                float = 0.0
    annualized_other_ratio:                               float = 0.0
    annualized_other_ratio_bonus:                         float = 0.0
    quarterized_other_ratio:                              float = 0.0
    quarterized_other_ratio_bonus:                        float = 0.0
    annualized_total_current_ratio:                       float = 0.0
    annualized_total_current_ratio_bonus:                 float = 0.0
    quarterized_total_current_ratio:                      float = 0.0
    quarterized_total_current_ratio_bonus:                float = 0.0
    total_ratio_effective:                                float = 0.0
    other_current_ratio_effective:                        float = 0.0
    other_ratio_effective:                                float = 0.0
    total_current_ratio_effective:                        float = 0.0
    effective_current_ratio:                              float = 0.0
    annualized_total_assets:                              float = 0.0
    annualized_total_assets_bonus:                        float = 0.0
    quarterized_total_assets:                             float = 0.0
    quarterized_total_assets_bonus:                       float = 0.0
    effective_total_assets:                               float = 0.0
    annualized_total_stockholder_equity:                  float = 0.0
    annualized_total_stockholder_equity_bonus:            float = 0.0
    quarterized_total_stockholder_equity:                 float = 0.0
    quarterized_total_stockholder_equity_bonus:           float = 0.0
    effective_total_stockholder_equity:                   float = 0.0
    calculated_roa:                                       float = 0.0
    calculated_roe:                                       float = 0.0
    annualized_working_capital:                           float = 0.0
    quarterized_working_capital:                          float = 0.0
    effective_working_capital:                            float = 0.0
    annualized_total_liabilities:                         float = 0.0
    annualized_total_liabilities_bonus:                   float = 0.0
    quarterized_total_liabilities:                        float = 0.0
    quarterized_total_liabilities_bonus:                  float = 0.0
    effective_total_liabilities:                          float = 0.0
    altman_z_score_factor:                                float = 0.0
    skip_reason:                                          str   = 'None'

@dataclass
class StockDataNormalized:
    symbol:                                               str   = 'None'
    short_name:                                           str   = 'None'
    quote_type:                                           str   = 'None'
    sector:                                               str   = 'None'
    country:                                              str   = 'Unknown'
    sss_value:                                            float = BAD_SSS
    sss_value_normalized:                                 float = BAD_SSS
    annualized_revenue:                                   float = 0.0
    annualized_revenue_bonus:                             float = 0.0
    annualized_earnings:                                  float = 0.0  # TODO: ASAFR: Add the bonus calculations (pos, neg, mon_inc, mon_dec, etc)
    annualized_retained_earnings:                         float = 0.0
    annualized_retained_earnings_bonus:                   float = 0.0
    quarterized_revenue:                                  float = 0.0
    quarterized_revenue_bonus:                            float = 0.0
    quarterized_earnings:                                 float = 0.0
    quarterized_earnings_bonus:                           float = 0.0
    quarterized_retained_earnings:                        float = 0.0
    quarterized_retained_earnings_bonus:                  float = 0.0
    effective_earnings:                                   float = 0.0
    effective_retained_earnings:                          float = 0.0
    effective_revenue:                                    float = 0.0
    annualized_total_revenue:                             float = 0.0
    annualized_total_revenue_bonus:                       float = 0.0
    annualized_net_income:                                float = 0.0   # TODO: ASAFR: Add the bonus calculations (pos, neg, mon_inc, mon_dec, etc)
    quarterized_total_revenue:                            float = 0.0
    quarterized_total_revenue_bonus:                      float = 0.0
    quarterized_net_income:                               float = 0.0
    quarterized_net_income_bonus:                         float = 0.0
    effective_net_income:                                 float = 0.0
    effective_total_revenue:                              float = 0.0
    enterprise_value_to_revenue:                          float = 0.0
    evr_effective:                                        float = 0.0
    evr_effective_normalized:                             float = 0.0
    trailing_price_to_earnings:                           float = 0.0
    forward_price_to_earnings:                            float = 0.0
    effective_price_to_earnings:                          float = 0.0
    trailing_12months_price_to_sales:                     float = 0.0
    trailing_12months_price_to_sales_normalized:          float = 0.0
    pe_effective:                                         float = 0.0
    pe_effective_normalized:                              float = 0.0
    enterprise_value_to_ebitda:                           float = 0.0
    effective_ev_to_ebitda:                               float = 0.0
    effective_ev_to_ebitda_normalized:                    float = 0.0
    ebitda:                                               float = 0.0
    quarterized_ebitd:                                    float = 0.0
    annualized_ebitd:                                     float = 0.0
    ebitd:                                                float = 0.0
    profit_margin:                                        float = 0.0
    annualized_profit_margin:                             float = 0.0
    annualized_profit_margin_boost:                       float = 0.0
    quarterized_profit_margin:                            float = 0.0
    quarterized_profit_margin_boost:                      float = 0.0
    effective_profit_margin:                              float = 0.0
    effective_profit_margin_normalized:                   float = 0.0
    held_percent_institutions:                            float = 0.0
    held_percent_insiders:                                float = 0.0
    held_percent_insiders_normalized:                     float = 0.0
    forward_eps:                                          float = 0.0
    trailing_eps:                                         float = 0.0
    previous_close:                                       float = 0.0
    trailing_eps_percentage:                              float = 0.0 # trailing_eps / previousClose
    price_to_book:                                        float = 0.0
    price_to_book_normalized:                             float = 0.0
    shares_outstanding:                                   float = 0.0
    net_income_to_common_shareholders:                    float = 0.0
    nitcsh_to_shares_outstanding:                         float = 0.0
    employees:                                            int   = 0
    enterprise_value:                                     int   = 0
    market_cap:                                           int   = 0
    nitcsh_to_num_employees:                              float = 0.0
    eqg:                                                  float = 0.0  # Value is a ratio, such that when multiplied by 100, yields percentage (%) units
    rqg:                                                  float = 0.0  # Value is a ratio, such that when multiplied by 100, yields percentage (%) units
    eqg_yoy:                                              float = 0.0  # calculated from the yearly earnings - if available
    rqg_yoy:                                              float = 0.0  # calculated from the yearly Revenues - if available
    niqg_yoy:                                             float = 0.0  # Net Income Quarterly Growth: calculated from the yearly net income - if available
    trqg_yoy:                                             float = 0.0  # Total Revenue Quarterly Growth: calculated from the yearly net income - if available
    eqg_effective:                                        float = 0.0  # average of eqg_yoy and eqg
    eqg_factor_effective:                                 float = 0.0  # function with positive factor and damper
    eqg_factor_effective_normalized:                      float = 0.0  # function with positive factor and damper
    rqg_effective:                                        float = 0.0  # average of rqg_yoy and rqg
    rqg_factor_effective:                                 float = 0.0  # function with positive factor and damper
    rqg_factor_effective_normalized:                      float = 0.0  # function with positive factor and damper
    price_to_earnings_to_growth_ratio:                    float = 0.0
    effective_peg_ratio:                                  float = 0.0
    effective_peg_ratio_normalized:                       float = 0.0
    annualized_cash_flow_from_operating_activities:       float = 0.0
    annualized_cash_flow_from_operating_activities_bonus: float = 0.0
    quarterized_cash_flow_from_operating_activities:      float = 0.0
    quarterized_cash_flow_from_operating_activities_bonus:float = 0.0
    annualized_ev_to_cfo_ratio:                           float = 0.0  # https://investinganswers.com/dictionary/e/enterprise-value-cash-flow-operations-evcfo
    quarterized_ev_to_cfo_ratio:                          float = 0.0  # https://investinganswers.com/dictionary/e/enterprise-value-cash-flow-operations-evcfo
    ev_to_cfo_ratio_effective:                            float = 0.0
    ev_to_cfo_ratio_effective_normalized:                 float = 0.0
    annualized_debt_to_equity:                            float = 0.0
    annualized_debt_to_equity_bonus:                      float = 0.0
    quarterized_debt_to_equity:                           float = 0.0
    quarterized_debt_to_equity_bonus:                     float = 0.0
    debt_to_equity_effective:                             float = 0.0
    debt_to_equity_effective_used:                        float = 0.0
    debt_to_equity_effective_used_normalized:             float = 0.0
    financial_currency:                                   str   = 'None'
    summary_currency:                                     str   = 'None'
    financial_currency_conversion_rate_mult_to_usd:       float = 0.0
    summary_currency_conversion_rate_mult_to_usd:         float = 0.0
    last_dividend_0:                                      float = 0.0
    last_dividend_1:                                      float = 0.0
    last_dividend_2:                                      float = 0.0
    last_dividend_3:                                      float = 0.0
    fifty_two_week_change:                                float = 0.0
    fifty_two_week_low:                                   float = 0.0
    fifty_two_week_high:                                  float = 0.0
    two_hundred_day_average:                              float = 0.0
    previous_close_percentage_from_200d_ma:               float = 0.0
    previous_close_percentage_from_52w_low:               float = 0.0
    previous_close_percentage_from_52w_high:              float = 0.0
    dist_from_low_factor:                                 float = 0.0
    eff_dist_from_low_factor:                             float = 0.0
    eff_dist_from_low_factor_normalized:                  float = 0.0
    annualized_total_ratio:                               float = 0.0
    annualized_total_ratio_bonus:                         float = 0.0
    quarterized_total_ratio:                              float = 0.0
    quarterized_total_ratio_bonus:                        float = 0.0
    annualized_other_current_ratio:                       float = 0.0
    annualized_other_current_ratio_bonus:                 float = 0.0
    quarterized_other_current_ratio:                      float = 0.0
    quarterized_other_current_ratio_bonus:                float = 0.0
    annualized_other_ratio:                               float = 0.0
    annualized_other_ratio_bonus:                         float = 0.0
    quarterized_other_ratio:                              float = 0.0
    quarterized_other_ratio_bonus:                        float = 0.0
    annualized_total_current_ratio:                       float = 0.0
    annualized_total_current_ratio_bonus:                 float = 0.0
    quarterized_total_current_ratio:                      float = 0.0
    quarterized_total_current_ratio_bonus:                float = 0.0
    total_ratio_effective:                                float = 0.0
    other_current_ratio_effective:                        float = 0.0
    other_ratio_effective:                                float = 0.0
    total_current_ratio_effective:                        float = 0.0
    effective_current_ratio:                              float = 0.0
    effective_current_ratio_normalized:                   float = 0.0
    annualized_total_assets:                              float = 0.0
    annualized_total_assets_bonus:                        float = 0.0
    quarterized_total_assets:                             float = 0.0
    quarterized_total_assets_bonus:                       float = 0.0
    effective_total_assets:                               float = 0.0
    annualized_total_stockholder_equity:                  float = 0.0
    annualized_total_stockholder_equity_bonus:            float = 0.0
    quarterized_total_stockholder_equity:                 float = 0.0
    quarterized_total_stockholder_equity_bonus:           float = 0.0
    effective_total_stockholder_equity:                   float = 0.0
    calculated_roa:                                       float = 0.0
    calculated_roa_normalized:                            float = 0.0
    calculated_roe:                                       float = 0.0
    calculated_roe_normalized:                            float = 0.0
    annualized_working_capital:                           float = 0.0
    quarterized_working_capital:                          float = 0.0
    effective_working_capital:                            float = 0.0
    annualized_total_liabilities:                         float = 0.0
    annualized_total_liabilities_bonus:                   float = 0.0
    quarterized_total_liabilities:                        float = 0.0
    quarterized_total_liabilities_bonus:                  float = 0.0
    effective_total_liabilities:                          float = 0.0
    altman_z_score_factor:                                float = 0.0
    altman_z_score_factor_normalized:                     float = 0.0
    skip_reason:                                          str   = 'None'

g_symbols_tase_duals = []

g_header_row            = ["Symbol", "Name", "Sector", "Country", "sss_value",                         "annualized_revenue", "annualized_revenue_bonus", "annualized_earnings", "annualized_retained_earnings", "annualized_retained_earnings_bonus", "quarterized_revenue", "quarterized_revenue_bonus", "quarterized_earnings", "quarterized_earnings_bonus", "quarterized_retained_earnings", "quarterized_retained_earnings_bonus", "effective_earnings", "effective_retained_earnings", "effective_revenue", "annualized_total_revenue", "annualized_total_revenue_bonus", "annualized_net_income", "quarterized_total_revenue", "quarterized_total_revenue_bonus", "quarterized_net_income", "quarterized_net_income_bonus", "effective_net_income", "effective_total_revenue", "enterprise_value_to_revenue", "evr_effective",                             "trailing_price_to_earnings", "forward_price_to_earnings", "effective_price_to_earnings", "trailing_12months_price_to_sales",                                                "pe_effective",                            "enterprise_value_to_ebitda", "effective_ev_to_ebitda",                                      "ebitda", "quarterized_ebitd", "annualized_ebitd", "ebitd", "profit_margin", "annualized_profit_margin", "annualized_profit_margin_boost", "quarterized_profit_margin", "quarterized_profit_margin_boost", "effective_profit_margin",                                       "held_percent_institutions", "held_percent_insiders",                                     "forward_eps", "trailing_eps", "previous_close", "trailing_eps_percentage", "price_to_book",                             "shares_outstanding", "net_income_to_common_shareholders", "nitcsh_to_shares_outstanding", "employees", "enterprise_value", "market_cap", "nitcsh_to_num_employees", "eqg", "rqg", "eqg_yoy", "rqg_yoy", "niqg_yoy", "trqg_yoy", "eqg_effective", "eqg_factor_effective",                                    "rqg_effective", "rqg_factor_effective",                                    "price_to_earnings_to_growth_ratio", "effective_peg_ratio",                                   "annualized_cash_flow_from_operating_activities", "annualized_cash_flow_from_operating_activities_bonus", "quarterized_cash_flow_from_operating_activities", "quarterized_cash_flow_from_operating_activities_bonus", "annualized_ev_to_cfo_ratio", "quarterized_ev_to_cfo_ratio", "ev_to_cfo_ratio_effective",                                         "annualized_debt_to_equity", "annualized_debt_to_equity_bonus", "quarterized_debt_to_equity", "quarterized_debt_to_equity_bonus", "debt_to_equity_effective", "debt_to_equity_effective_used",                                             "financial_currency", "summary_currency", "financial_currency_conversion_rate_mult_to_usd", "summary_currency_conversion_rate_mult_to_usd", "last_dividend_0", "last_dividend_1", "last_dividend_2", "last_dividend_3", "fifty_two_week_change", "fifty_two_week_low", "fifty_two_week_high", "two_hundred_day_average", "previous_close_percentage_from_200d_ma", "previous_close_percentage_from_52w_low", "previous_close_percentage_from_52w_high", "dist_from_low_factor", "eff_dist_from_low_factor",                                        "annualized_total_ratio", "annualized_total_ratio_bonus", "quarterized_total_ratio", "quarterized_total_ratio_bonus", "annualized_other_current_ratio", "annualized_other_current_ratio_bonus", "quarterized_other_current_ratio", "quarterized_other_current_ratio_bonus", "annualized_other_ratio", "annualized_other_ratio_bonus", "quarterized_other_ratio", "quarterized_other_ratio_bonus", "annualized_total_current_ratio", "annualized_total_current_ratio_bonus", "quarterized_total_current_ratio", "quarterized_total_current_ratio_bonus", "total_ratio_effective", "other_current_ratio_effective", "other_ratio_effective", "total_current_ratio_effective", "effective_current_ratio",                                       "annualized_total_assets", "annualized_total_assets_bonus", "quarterized_total_assets", "quarterized_total_assets_bonus", "effective_total_assets", "annualized_total_stockholder_equity", "annualized_total_stockholder_equity_bonus", "quarterized_total_stockholder_equity", "quarterized_total_stockholder_equity_bonus", "effective_total_stockholder_equity", "calculated_roa",                              "calculated_roe",                              "annualized_working_capital", "quarterized_working_capital", "effective_working_capital", "annualized_total_liabilities", "annualized_total_liabilities_bonus", "quarterized_total_liabilities", "quarterized_total_liabilities_bonus", "effective_total_liabilities", "altman_z_score_factor",                                     "skip_reason" ]
g_header_row_normalized = ["Symbol", "Name", "Sector", "Country", "sss_value", "sss_value_normalized", "annualized_revenue", "annualized_revenue_bonus", "annualized_earnings", "annualized_retained_earnings", "annualized_retained_earnings_bonus", "quarterized_revenue", "quarterized_revenue_bonus", "quarterized_earnings", "quarterized_earnings_bonus", "quarterized_retained_earnings", "quarterized_retained_earnings_bonus", "effective_earnings", "effective_retained_earnings", "effective_revenue", "annualized_total_revenue", "annualized_total_revenue_bonus", "annualized_net_income", "quarterized_total_revenue", "quarterized_total_revenue_bonus", "quarterized_net_income", "quarterized_net_income_bonus", "effective_net_income", "effective_total_revenue", "enterprise_value_to_revenue", "evr_effective", "evr_effective_normalized", "trailing_price_to_earnings", "forward_price_to_earnings", "effective_price_to_earnings", "trailing_12months_price_to_sales", "trailing_12months_price_to_sales_normalized", "pe_effective", "pe_effective_normalized", "enterprise_value_to_ebitda", "effective_ev_to_ebitda", "effective_ev_to_ebitda_normalized", "ebitda", "quarterized_ebitd", "annualized_ebitd", "ebitd", "profit_margin", "annualized_profit_margin", "annualized_profit_margin_boost", "quarterized_profit_margin", "quarterized_profit_margin_boost", "effective_profit_margin", "effective_profit_margin_normalized", "held_percent_institutions", "held_percent_insiders", "held_percent_insiders_normalized", "forward_eps", "trailing_eps", "previous_close", "trailing_eps_percentage", "price_to_book", "price_to_book_normalized", "shares_outstanding", "net_income_to_common_shareholders", "nitcsh_to_shares_outstanding", "employees", "enterprise_value", "market_cap", "nitcsh_to_num_employees", "eqg", "rqg", "eqg_yoy", "rqg_yoy", "niqg_yoy", "trqg_yoy", "eqg_effective", "eqg_factor_effective", "eqg_factor_effective_normalized", "rqg_effective", "rqg_factor_effective", "rqg_factor_effective_normalized", "price_to_earnings_to_growth_ratio", "effective_peg_ratio", "effective_peg_ratio_normalized", "annualized_cash_flow_from_operating_activities", "annualized_cash_flow_from_operating_activities_bonus", "quarterized_cash_flow_from_operating_activities", "quarterized_cash_flow_from_operating_activities_bonus", "annualized_ev_to_cfo_ratio", "quarterized_ev_to_cfo_ratio", "ev_to_cfo_ratio_effective", "ev_to_cfo_ratio_effective_normalized", "annualized_debt_to_equity", "annualized_debt_to_equity_bonus", "quarterized_debt_to_equity", "quarterized_debt_to_equity_bonus", "debt_to_equity_effective", "debt_to_equity_effective_used", "debt_to_equity_effective_used_normalized", "financial_currency", "summary_currency", "financial_currency_conversion_rate_mult_to_usd", "summary_currency_conversion_rate_mult_to_usd", "last_dividend_0", "last_dividend_1", "last_dividend_2", "last_dividend_3", "fifty_two_week_change", "fifty_two_week_low", "fifty_two_week_high", "two_hundred_day_average", "previous_close_percentage_from_200d_ma", "previous_close_percentage_from_52w_low", "previous_close_percentage_from_52w_high", "dist_from_low_factor", "eff_dist_from_low_factor", "eff_dist_from_low_factor_normalized", "annualized_total_ratio", "annualized_total_ratio_bonus", "quarterized_total_ratio", "quarterized_total_ratio_bonus", "annualized_other_current_ratio", "annualized_other_current_ratio_bonus", "quarterized_other_current_ratio", "quarterized_other_current_ratio_bonus", "annualized_other_ratio", "annualized_other_ratio_bonus", "quarterized_other_ratio", "quarterized_other_ratio_bonus", "annualized_total_current_ratio", "annualized_total_current_ratio_bonus", "quarterized_total_current_ratio", "quarterized_total_current_ratio_bonus", "total_ratio_effective", "other_current_ratio_effective", "other_ratio_effective", "total_current_ratio_effective", "effective_current_ratio", "effective_current_ratio_normalized", "annualized_total_assets", "annualized_total_assets_bonus", "quarterized_total_assets", "quarterized_total_assets_bonus", "effective_total_assets", "annualized_total_stockholder_equity", "annualized_total_stockholder_equity_bonus", "quarterized_total_stockholder_equity", "quarterized_total_stockholder_equity_bonus", "effective_total_stockholder_equity", "calculated_roa", "calculated_roa_normalized", "calculated_roe", "calculated_roe_normalized", "annualized_working_capital", "quarterized_working_capital", "effective_working_capital", "annualized_total_liabilities", "annualized_total_liabilities_bonus", "quarterized_total_liabilities", "quarterized_total_liabilities_bonus", "effective_total_liabilities", "altman_z_score_factor", "altman_z_score_factor_normalized", "skip_reason" ]


g_symbol_index                                                = g_header_row.index("Symbol")
g_name_index                                                  = g_header_row.index("Name")
g_sector_index                                                = g_header_row.index("Sector")
g_country_index                                               = g_header_row.index("Country")
g_sss_value_index                                             = g_header_row.index("sss_value")
g_annualized_revenue_index                                    = g_header_row.index("annualized_revenue")
g_annualized_revenue_bonus_index                              = g_header_row.index("annualized_revenue_bonus")
g_annualized_earnings_index                                   = g_header_row.index("annualized_earnings")
g_annualized_retained_earnings_index                          = g_header_row.index("annualized_retained_earnings")
g_annualized_retained_earnings_bonus_index                    = g_header_row.index("annualized_retained_earnings_bonus")
g_quarterized_revenue_index                                   = g_header_row.index("quarterized_revenue")
g_quarterized_revenue_bonus_index                             = g_header_row.index("quarterized_revenue_bonus")
g_quarterized_earnings_index                                  = g_header_row.index("quarterized_earnings")
g_quarterized_earnings_bonus_index                            = g_header_row.index("quarterized_earnings_bonus")
g_quarterized_retained_earnings_index                         = g_header_row.index("quarterized_retained_earnings")
g_quarterized_retained_earnings_bonus_index                   = g_header_row.index("quarterized_retained_earnings_bonus")
g_effective_earnings_index                                    = g_header_row.index("effective_earnings")
g_effective_retained_earnings_index                           = g_header_row.index("effective_retained_earnings")
g_effective_revenue_index                                     = g_header_row.index("effective_revenue")
g_annualized_total_revenue_index                              = g_header_row.index("annualized_total_revenue")
g_annualized_total_revenue_bonus_index                        = g_header_row.index("annualized_total_revenue_bonus")
g_annualized_net_income_index                                 = g_header_row.index("annualized_net_income")
g_quarterized_total_revenue_index                             = g_header_row.index("quarterized_total_revenue")
g_quarterized_total_revenue_bonus_index                       = g_header_row.index("quarterized_total_revenue_bonus")
g_quarterized_net_income_index                                = g_header_row.index("quarterized_net_income")
g_quarterized_net_income_bonus_index                          = g_header_row.index("quarterized_net_income_bonus")
g_effective_net_income_index                                  = g_header_row.index("effective_net_income")
g_effective_total_revenue_index                               = g_header_row.index("effective_total_revenue")
g_enterprise_value_to_revenue_index                           = g_header_row.index("enterprise_value_to_revenue")
g_evr_effective_index                                         = g_header_row.index("evr_effective")
g_trailing_price_to_earnings_index                            = g_header_row.index("trailing_price_to_earnings")
g_forward_price_to_earnings_index                             = g_header_row.index("forward_price_to_earnings")
g_effective_price_to_earnings_index                           = g_header_row.index("effective_price_to_earnings")
g_trailing_12months_price_to_sales_index                      = g_header_row.index("trailing_12months_price_to_sales")
g_pe_effective_index                                          = g_header_row.index("pe_effective")
g_enterprise_value_to_ebitda_index                            = g_header_row.index("enterprise_value_to_ebitda")
g_effective_ev_to_ebitda_index                                = g_header_row.index("effective_ev_to_ebitda")
g_ebitda_index                                                = g_header_row.index("ebitda")
g_quarterized_ebitd_index                                     = g_header_row.index("quarterized_ebitd")
g_annualized_ebitd_index                                      = g_header_row.index("annualized_ebitd")
g_ebitd_index                                                 = g_header_row.index("ebitd")
g_profit_margin_index                                         = g_header_row.index("profit_margin")
g_annualized_profit_margin_index                              = g_header_row.index("annualized_profit_margin")
g_annualized_profit_margin_boost_index                        = g_header_row.index("annualized_profit_margin_boost")
g_quarterized_profit_margin_index                             = g_header_row.index("quarterized_profit_margin")
g_quarterized_profit_margin_boost_index                       = g_header_row.index("quarterized_profit_margin_boost")
g_effective_profit_margin_index                               = g_header_row.index("effective_profit_margin")
g_held_percent_institutions_index                             = g_header_row.index("held_percent_institutions")
g_held_percent_insiders_index                                 = g_header_row.index("held_percent_insiders")
g_forward_eps_index                                           = g_header_row.index("forward_eps")
g_trailing_eps_index                                          = g_header_row.index("trailing_eps")
g_previous_close_index                                        = g_header_row.index("previous_close")
g_trailing_eps_percentage_index                               = g_header_row.index("trailing_eps_percentage")
g_price_to_book_index                                         = g_header_row.index("price_to_book")
g_shares_outstanding_index                                    = g_header_row.index("shares_outstanding")
g_net_income_to_common_shareholders_index                     = g_header_row.index("net_income_to_common_shareholders")
g_nitcsh_to_shares_outstanding_index                          = g_header_row.index("nitcsh_to_shares_outstanding")
g_employees_index                                             = g_header_row.index("employees")
g_enterprise_value_index                                      = g_header_row.index("enterprise_value")
g_market_cap_index                                            = g_header_row.index("market_cap")
g_nitcsh_to_num_employees_index                               = g_header_row.index("nitcsh_to_num_employees")
g_eqg_index                                                   = g_header_row.index("eqg")
g_rqg_index                                                   = g_header_row.index("rqg")
g_eqg_yoy_index                                               = g_header_row.index("eqg_yoy")
g_rqg_yoy_index                                               = g_header_row.index("rqg_yoy")
g_niqg_yoy_index                                              = g_header_row.index("niqg_yoy")
g_trqg_yoy_index                                              = g_header_row.index("trqg_yoy")
g_eqg_effective_index                                         = g_header_row.index("eqg_effective")
g_eqg_factor_effective_index                                  = g_header_row.index("eqg_factor_effective")
g_rqg_effective_index                                         = g_header_row.index("rqg_effective")
g_rqg_factor_effective_index                                  = g_header_row.index("rqg_factor_effective")
g_price_to_earnings_to_growth_ratio_index                     = g_header_row.index("price_to_earnings_to_growth_ratio")
g_effective_peg_ratio_index                                   = g_header_row.index("effective_peg_ratio")
g_annualized_cash_flow_from_operating_activities_index        = g_header_row.index("annualized_cash_flow_from_operating_activities")
g_annualized_cash_flow_from_operating_activities_bonus_index  = g_header_row.index("annualized_cash_flow_from_operating_activities_bonus")
g_quarterized_cash_flow_from_operating_activities_index       = g_header_row.index("quarterized_cash_flow_from_operating_activities")
g_quarterized_cash_flow_from_operating_activities_bonus_index = g_header_row.index("quarterized_cash_flow_from_operating_activities_bonus")
g_annualized_ev_to_cfo_ratio_index                            = g_header_row.index("annualized_ev_to_cfo_ratio")
g_quarterized_ev_to_cfo_ratio_index                           = g_header_row.index("quarterized_ev_to_cfo_ratio")
g_ev_to_cfo_ratio_effective_index                             = g_header_row.index("ev_to_cfo_ratio_effective")
g_annualized_debt_to_equity_index                             = g_header_row.index("annualized_debt_to_equity")
g_annualized_debt_to_equity_bonus_index                       = g_header_row.index("annualized_debt_to_equity_bonus")
g_quarterized_debt_to_equity_index                            = g_header_row.index("quarterized_debt_to_equity")
g_quarterized_debt_to_equity_bonus_index                      = g_header_row.index("quarterized_debt_to_equity_bonus")
g_debt_to_equity_effective_index                              = g_header_row.index("debt_to_equity_effective")
g_debt_to_equity_effective_used_index                         = g_header_row.index("debt_to_equity_effective_used")
g_financial_currency_index                                    = g_header_row.index("financial_currency")
g_summary_currency_index                                      = g_header_row.index("summary_currency")
g_financial_currency_conversion_rate_mult_to_usd_index        = g_header_row.index("financial_currency_conversion_rate_mult_to_usd")
g_summary_currency_conversion_rate_mult_to_usd_index          = g_header_row.index("summary_currency_conversion_rate_mult_to_usd")
g_last_dividend_0_index                                       = g_header_row.index("last_dividend_0")
g_last_dividend_1_index                                       = g_header_row.index("last_dividend_1")
g_last_dividend_2_index                                       = g_header_row.index("last_dividend_2")
g_last_dividend_3_index                                       = g_header_row.index("last_dividend_3")
g_fifty_two_week_change_index                                 = g_header_row.index("fifty_two_week_change")
g_fifty_two_week_low_index                                    = g_header_row.index("fifty_two_week_low")
g_fifty_two_week_high_index                                   = g_header_row.index("fifty_two_week_high")
g_two_hundred_day_average_index                               = g_header_row.index("two_hundred_day_average")
g_previous_close_percentage_from_200d_ma_index                = g_header_row.index("previous_close_percentage_from_200d_ma")
g_previous_close_percentage_from_52w_low_index                = g_header_row.index("previous_close_percentage_from_52w_low")
g_previous_close_percentage_from_52w_high_index               = g_header_row.index("previous_close_percentage_from_52w_high")
g_dist_from_low_factor_index                                  = g_header_row.index("dist_from_low_factor")
g_eff_dist_from_low_factor_index                              = g_header_row.index("eff_dist_from_low_factor")
g_annualized_total_ratio_index                                = g_header_row.index("annualized_total_ratio")
g_annualized_total_ratio_bonus_index                          = g_header_row.index("annualized_total_ratio_bonus")
g_quarterized_total_ratio_index                               = g_header_row.index("quarterized_total_ratio")
g_quarterized_total_ratio_bonus_index                         = g_header_row.index("quarterized_total_ratio_bonus")
g_annualized_other_current_ratio_index                        = g_header_row.index("annualized_other_current_ratio")
g_annualized_other_current_ratio_bonus_index                  = g_header_row.index("annualized_other_current_ratio_bonus")
g_quarterized_other_current_ratio_index                       = g_header_row.index("quarterized_other_current_ratio")
g_quarterized_other_current_ratio_bonus_index                 = g_header_row.index("quarterized_other_current_ratio_bonus")
g_annualized_other_ratio_index                                = g_header_row.index("annualized_other_ratio")
g_annualized_other_ratio_bonus_index                          = g_header_row.index("annualized_other_ratio_bonus")
g_quarterized_other_ratio_index                               = g_header_row.index("quarterized_other_ratio")
g_quarterized_other_ratio_bonus_index                         = g_header_row.index("quarterized_other_ratio_bonus")
g_annualized_total_current_ratio_index                        = g_header_row.index("annualized_total_current_ratio")
g_annualized_total_current_ratio_bonus_index                  = g_header_row.index("annualized_total_current_ratio_bonus")
g_quarterized_total_current_ratio_index                       = g_header_row.index("quarterized_total_current_ratio")
g_quarterized_total_current_ratio_bonus_index                 = g_header_row.index("quarterized_total_current_ratio_bonus")
g_total_ratio_effective_index                                 = g_header_row.index("total_ratio_effective")
g_other_current_ratio_effective_index                         = g_header_row.index("other_current_ratio_effective")
g_other_ratio_effective_index                                 = g_header_row.index("other_ratio_effective")
g_total_current_ratio_effective_index                         = g_header_row.index("total_current_ratio_effective")
g_effective_current_ratio_index                               = g_header_row.index("effective_current_ratio")
g_annualized_total_assets_index                               = g_header_row.index("annualized_total_assets")
g_annualized_total_assets_bonus_index                         = g_header_row.index("annualized_total_assets_bonus")
g_quarterized_total_assets_index                              = g_header_row.index("quarterized_total_assets")
g_quarterized_total_assets_bonus_index                        = g_header_row.index("quarterized_total_assets_bonus")
g_effective_total_assets_index                                = g_header_row.index("effective_total_assets")
g_annualized_total_stockholder_equity_index                   = g_header_row.index("annualized_total_stockholder_equity")
g_annualized_total_stockholder_equity_bonus_index             = g_header_row.index("annualized_total_stockholder_equity_bonus")
g_quarterized_total_stockholder_equity_index                  = g_header_row.index("quarterized_total_stockholder_equity")
g_quarterized_total_stockholder_equity_bonus_index            = g_header_row.index("quarterized_total_stockholder_equity_bonus")
g_effective_total_stockholder_equity_index                    = g_header_row.index("effective_total_stockholder_equity")
g_calculated_roa_index                                        = g_header_row.index("calculated_roa")
g_calculated_roe_index                                        = g_header_row.index("calculated_roe")
g_annualized_working_capital_index                            = g_header_row.index("annualized_working_capital")
g_quarterized_working_capital_index                           = g_header_row.index("quarterized_working_capital")
g_effective_working_capital_index                             = g_header_row.index("effective_working_capital")
g_annualized_total_liabilities_index                          = g_header_row.index("annualized_total_liabilities")
g_annualized_total_liabilities_bonus_index                    = g_header_row.index("annualized_total_liabilities_bonus")
g_quarterized_total_liabilities_index                         = g_header_row.index("quarterized_total_liabilities")
g_quarterized_total_liabilities_bonus_index                   = g_header_row.index("quarterized_total_liabilities_bonus")
g_effective_total_liabilities_index                           = g_header_row.index("effective_total_liabilities")
g_altman_z_score_factor_index                                 = g_header_row.index("altman_z_score_factor")
g_skip_reason_index                                           = g_header_row.index("skip_reason")

g_symbol_index_n                                                = g_header_row_normalized.index("Symbol")
g_name_index_n                                                  = g_header_row_normalized.index("Name")
g_sector_index_n                                                = g_header_row_normalized.index("Sector")
g_country_index_n                                               = g_header_row_normalized.index("Country")
g_sss_value_index_n                                             = g_header_row_normalized.index("sss_value")
g_sss_value_normalized_index_n                                  = g_header_row_normalized.index("sss_value_normalized")
g_annualized_revenue_index_n                                    = g_header_row_normalized.index("annualized_revenue")
g_annualized_revenue_bonus_index_n                              = g_header_row_normalized.index("annualized_revenue_bonus")
g_annualized_earnings_index_n                                   = g_header_row_normalized.index("annualized_earnings")
g_annualized_retained_earnings_index_n                          = g_header_row_normalized.index("annualized_retained_earnings")
g_annualized_retained_earnings_bonus_index_n                    = g_header_row_normalized.index("annualized_retained_earnings_bonus")
g_quarterized_revenue_index_n                                   = g_header_row_normalized.index("quarterized_revenue")
g_quarterized_revenue_bonus_index_n                             = g_header_row_normalized.index("quarterized_revenue_bonus")
g_quarterized_earnings_index_n                                  = g_header_row_normalized.index("quarterized_earnings")
g_quarterized_earnings_bonus_index_n                            = g_header_row_normalized.index("quarterized_earnings_bonus")
g_quarterized_retained_earnings_index_n                         = g_header_row_normalized.index("quarterized_retained_earnings")
g_quarterized_retained_earnings_bonus_index_n                   = g_header_row_normalized.index("quarterized_retained_earnings_bonus")
g_effective_earnings_index_n                                    = g_header_row_normalized.index("effective_earnings")
g_effective_retained_earnings_index_n                           = g_header_row_normalized.index("effective_retained_earnings")
g_effective_revenue_index_n                                     = g_header_row_normalized.index("effective_revenue")
g_annualized_total_revenue_index_n                              = g_header_row_normalized.index("annualized_total_revenue")
g_annualized_total_revenue_bonus_index_n                        = g_header_row_normalized.index("annualized_total_revenue_bonus")
g_annualized_net_income_index_n                                 = g_header_row_normalized.index("annualized_net_income")
g_quarterized_total_revenue_index_n                             = g_header_row_normalized.index("quarterized_total_revenue")
g_quarterized_total_revenue_bonus_index_n                       = g_header_row_normalized.index("quarterized_total_revenue_bonus")
g_quarterized_net_income_index_n                                = g_header_row_normalized.index("quarterized_net_income")
g_quarterized_net_income_bonus_index_n                          = g_header_row_normalized.index("quarterized_net_income_bonus")
g_effective_net_income_index_n                                  = g_header_row_normalized.index("effective_net_income")
g_effective_total_revenue_index_n                               = g_header_row_normalized.index("effective_total_revenue")
g_enterprise_value_to_revenue_index_n                           = g_header_row_normalized.index("enterprise_value_to_revenue")
g_evr_effective_index_n                                         = g_header_row_normalized.index("evr_effective")
g_evr_effective_normalized_index_n                              = g_header_row_normalized.index("evr_effective_normalized")
g_trailing_price_to_earnings_index_n                            = g_header_row_normalized.index("trailing_price_to_earnings")
g_forward_price_to_earnings_index_n                             = g_header_row_normalized.index("forward_price_to_earnings")
g_effective_price_to_earnings_index_n                           = g_header_row_normalized.index("effective_price_to_earnings")
g_trailing_12months_price_to_sales_index_n                      = g_header_row_normalized.index("trailing_12months_price_to_sales")
g_trailing_12months_price_to_sales_normalized_index_n           = g_header_row_normalized.index("trailing_12months_price_to_sales_normalized")
g_pe_effective_index_n                                          = g_header_row_normalized.index("pe_effective")
g_pe_effective_normalized_index_n                               = g_header_row_normalized.index("pe_effective_normalized")
g_enterprise_value_to_ebitda_index_n                            = g_header_row_normalized.index("enterprise_value_to_ebitda")
g_effective_ev_to_ebitda_index_n                                = g_header_row_normalized.index("effective_ev_to_ebitda")
g_effective_ev_to_ebitda_normalized_index_n                     = g_header_row_normalized.index("effective_ev_to_ebitda_normalized")
g_ebitda_index_n                                                = g_header_row_normalized.index("ebitda")
g_quarterized_ebitd_index_n                                     = g_header_row_normalized.index("quarterized_ebitd")
g_annualized_ebitd_index_n                                      = g_header_row_normalized.index("annualized_ebitd")
g_ebitd_index_n                                                 = g_header_row_normalized.index("ebitd")
g_profit_margin_index_n                                         = g_header_row_normalized.index("profit_margin")
g_annualized_profit_margin_index_n                              = g_header_row_normalized.index("annualized_profit_margin")
g_annualized_profit_margin_boost_index_n                        = g_header_row_normalized.index("annualized_profit_margin_boost")
g_quarterized_profit_margin_index_n                             = g_header_row_normalized.index("quarterized_profit_margin")
g_quarterized_profit_margin_boost_index_n                       = g_header_row_normalized.index("quarterized_profit_margin_boost")
g_effective_profit_margin_index_n                               = g_header_row_normalized.index("effective_profit_margin")
g_effective_profit_margin_normalized_index_n                    = g_header_row_normalized.index("effective_profit_margin_normalized")
g_held_percent_institutions_index_n                             = g_header_row_normalized.index("held_percent_institutions")
g_held_percent_insiders_index_n                                 = g_header_row_normalized.index("held_percent_insiders")
g_held_percent_insiders_normalized_index_n                      = g_header_row_normalized.index("held_percent_insiders_normalized")
g_forward_eps_index_n                                           = g_header_row_normalized.index("forward_eps")
g_trailing_eps_index_n                                          = g_header_row_normalized.index("trailing_eps")
g_previous_close_index_n                                        = g_header_row_normalized.index("previous_close")
g_trailing_eps_percentage_index_n                               = g_header_row_normalized.index("trailing_eps_percentage")
g_price_to_book_index_n                                         = g_header_row_normalized.index("price_to_book")
g_price_to_book_normalized_index_n                              = g_header_row_normalized.index("price_to_book_normalized")
g_shares_outstanding_index_n                                    = g_header_row_normalized.index("shares_outstanding")
g_net_income_to_common_shareholders_index_n                     = g_header_row_normalized.index("net_income_to_common_shareholders")
g_nitcsh_to_shares_outstanding_index_n                          = g_header_row_normalized.index("nitcsh_to_shares_outstanding")
g_employees_index_n                                             = g_header_row_normalized.index("employees")
g_enterprise_value_index_n                                      = g_header_row_normalized.index("enterprise_value")
g_market_cap_index_n                                            = g_header_row_normalized.index("market_cap")
g_nitcsh_to_num_employees_index_n                               = g_header_row_normalized.index("nitcsh_to_num_employees")
g_eqg_index_n                                                   = g_header_row_normalized.index("eqg")
g_rqg_index_n                                                   = g_header_row_normalized.index("rqg")
g_eqg_yoy_index_n                                               = g_header_row_normalized.index("eqg_yoy")
g_rqg_yoy_index_n                                               = g_header_row_normalized.index("rqg_yoy")
g_niqg_yoy_index_n                                              = g_header_row_normalized.index("niqg_yoy")
g_trqg_yoy_index_n                                              = g_header_row_normalized.index("trqg_yoy")
g_eqg_effective_index_n                                         = g_header_row_normalized.index("eqg_effective")
g_eqg_factor_effective_index_n                                  = g_header_row_normalized.index("eqg_factor_effective")
g_eqg_factor_effective_normalized_index_n                       = g_header_row_normalized.index("eqg_factor_effective_normalized")
g_rqg_effective_index_n                                         = g_header_row_normalized.index("rqg_effective")
g_rqg_factor_effective_index_n                                  = g_header_row_normalized.index("rqg_factor_effective")
g_rqg_factor_effective_normalized_index_n                       = g_header_row_normalized.index("rqg_factor_effective_normalized")
g_price_to_earnings_to_growth_ratio_index_n                     = g_header_row_normalized.index("price_to_earnings_to_growth_ratio")
g_effective_peg_ratio_index_n                                   = g_header_row_normalized.index("effective_peg_ratio")
g_effective_peg_ratio_normalized_index_n                        = g_header_row_normalized.index("effective_peg_ratio_normalized")
g_annualized_cash_flow_from_operating_activities_index_n        = g_header_row_normalized.index("annualized_cash_flow_from_operating_activities")
g_annualized_cash_flow_from_operating_activities_bonus_index_n  = g_header_row_normalized.index("annualized_cash_flow_from_operating_activities_bonus")
g_quarterized_cash_flow_from_operating_activities_index_n       = g_header_row_normalized.index("quarterized_cash_flow_from_operating_activities")
g_quarterized_cash_flow_from_operating_activities_bonus_index_n = g_header_row_normalized.index("quarterized_cash_flow_from_operating_activities_bonus")
g_annualized_ev_to_cfo_ratio_index_n                            = g_header_row_normalized.index("annualized_ev_to_cfo_ratio")
g_quarterized_ev_to_cfo_ratio_index_n                           = g_header_row_normalized.index("quarterized_ev_to_cfo_ratio")
g_ev_to_cfo_ratio_effective_index_n                             = g_header_row_normalized.index("ev_to_cfo_ratio_effective")
g_ev_to_cfo_ratio_effective_normalized_index_n                  = g_header_row_normalized.index("ev_to_cfo_ratio_effective_normalized")
g_annualized_debt_to_equity_index_n                             = g_header_row_normalized.index("annualized_debt_to_equity")
g_annualized_debt_to_equity_bonus_index_n                       = g_header_row_normalized.index("annualized_debt_to_equity_bonus")
g_quarterized_debt_to_equity_index_n                            = g_header_row_normalized.index("quarterized_debt_to_equity")
g_quarterized_debt_to_equity_bonus_index_n                      = g_header_row_normalized.index("quarterized_debt_to_equity_bonus")
g_debt_to_equity_effective_index_n                              = g_header_row_normalized.index("debt_to_equity_effective")
g_debt_to_equity_effective_used_index_n                         = g_header_row_normalized.index("debt_to_equity_effective_used")
g_debt_to_equity_effective_used_normalized_index_n              = g_header_row_normalized.index("debt_to_equity_effective_used_normalized")
g_financial_currency_index_n                                    = g_header_row_normalized.index("financial_currency")
g_summary_currency_index_n                                      = g_header_row_normalized.index("summary_currency")
g_financial_currency_conversion_rate_mult_to_usd_index_n        = g_header_row_normalized.index("financial_currency_conversion_rate_mult_to_usd")
g_summary_currency_conversion_rate_mult_to_usd_index_n          = g_header_row_normalized.index("summary_currency_conversion_rate_mult_to_usd")
g_last_dividend_0_index_n                                       = g_header_row_normalized.index("last_dividend_0")
g_last_dividend_1_index_n                                       = g_header_row_normalized.index("last_dividend_1")
g_last_dividend_2_index_n                                       = g_header_row_normalized.index("last_dividend_2")
g_last_dividend_3_index_n                                       = g_header_row_normalized.index("last_dividend_3")
g_fifty_two_week_change_index_n                                 = g_header_row_normalized.index("fifty_two_week_change")
g_fifty_two_week_low_index_n                                    = g_header_row_normalized.index("fifty_two_week_low")
g_fifty_two_week_high_index_n                                   = g_header_row_normalized.index("fifty_two_week_high")
g_two_hundred_day_average_index_n                               = g_header_row_normalized.index("two_hundred_day_average")
g_previous_close_percentage_from_200d_ma_index_n                = g_header_row_normalized.index("previous_close_percentage_from_200d_ma")
g_previous_close_percentage_from_52w_low_index_n                = g_header_row_normalized.index("previous_close_percentage_from_52w_low")
g_previous_close_percentage_from_52w_high_index_n               = g_header_row_normalized.index("previous_close_percentage_from_52w_high")
g_dist_from_low_factor_index_n                                  = g_header_row_normalized.index("dist_from_low_factor")
g_eff_dist_from_low_factor_index_n                              = g_header_row_normalized.index("eff_dist_from_low_factor")
g_eff_dist_from_low_factor_normalized_index_n                   = g_header_row_normalized.index("eff_dist_from_low_factor_normalized")
g_annualized_total_ratio_index_n                                = g_header_row_normalized.index("annualized_total_ratio")
g_annualized_total_ratio_bonus_index_n                          = g_header_row_normalized.index("annualized_total_ratio_bonus")
g_quarterized_total_ratio_index_n                               = g_header_row_normalized.index("quarterized_total_ratio")
g_quarterized_total_ratio_bonus_index_n                         = g_header_row_normalized.index("quarterized_total_ratio_bonus")
g_annualized_other_current_ratio_index_n                        = g_header_row_normalized.index("annualized_other_current_ratio")
g_annualized_other_current_ratio_bonus_index_n                  = g_header_row_normalized.index("annualized_other_current_ratio_bonus")
g_quarterized_other_current_ratio_index_n                       = g_header_row_normalized.index("quarterized_other_current_ratio")
g_quarterized_other_current_ratio_bonus_index_n                 = g_header_row_normalized.index("quarterized_other_current_ratio_bonus")
g_annualized_other_ratio_index_n                                = g_header_row_normalized.index("annualized_other_ratio")
g_annualized_other_ratio_bonus_index_n                          = g_header_row_normalized.index("annualized_other_ratio_bonus")
g_quarterized_other_ratio_index_n                               = g_header_row_normalized.index("quarterized_other_ratio")
g_quarterized_other_ratio_bonus_index_n                         = g_header_row_normalized.index("quarterized_other_ratio_bonus")
g_annualized_total_current_ratio_index_n                        = g_header_row_normalized.index("annualized_total_current_ratio")
g_annualized_total_current_ratio_bonus_index_n                  = g_header_row_normalized.index("annualized_total_current_ratio_bonus")
g_quarterized_total_current_ratio_index_n                       = g_header_row_normalized.index("quarterized_total_current_ratio")
g_quarterized_total_current_ratio_bonus_index_n                 = g_header_row_normalized.index("quarterized_total_current_ratio_bonus")
g_total_ratio_effective_index_n                                 = g_header_row_normalized.index("total_ratio_effective")
g_other_current_ratio_effective_index_n                         = g_header_row_normalized.index("other_current_ratio_effective")
g_other_ratio_effective_index_n                                 = g_header_row_normalized.index("other_ratio_effective")
g_total_current_ratio_effective_index_n                         = g_header_row_normalized.index("total_current_ratio_effective")
g_effective_current_ratio_index_n                               = g_header_row_normalized.index("effective_current_ratio")
g_effective_current_ratio_normalized_index_n                    = g_header_row_normalized.index("effective_current_ratio_normalized")
g_annualized_total_assets_index_n                               = g_header_row_normalized.index("annualized_total_assets")
g_annualized_total_assets_bonus_index_n                         = g_header_row_normalized.index("annualized_total_assets_bonus")
g_quarterized_total_assets_index_n                              = g_header_row_normalized.index("quarterized_total_assets")
g_quarterized_total_assets_bonus_index_n                        = g_header_row_normalized.index("quarterized_total_assets_bonus")
g_effective_total_assets_index_n                                = g_header_row_normalized.index("effective_total_assets")
g_annualized_total_stockholder_equity_index_n                   = g_header_row_normalized.index("annualized_total_stockholder_equity")
g_annualized_total_stockholder_equity_bonus_index_n             = g_header_row_normalized.index("annualized_total_stockholder_equity_bonus")
g_quarterized_total_stockholder_equity_index_n                  = g_header_row_normalized.index("quarterized_total_stockholder_equity")
g_quarterized_total_stockholder_equity_bonus_index_n            = g_header_row_normalized.index("quarterized_total_stockholder_equity_bonus")
g_effective_total_stockholder_equity_index_n                    = g_header_row_normalized.index("effective_total_stockholder_equity")
g_calculated_roa_index_n                                        = g_header_row_normalized.index("calculated_roa")
g_calculated_roa_normalized_index_n                             = g_header_row_normalized.index("calculated_roa_normalized")
g_calculated_roe_index_n                                        = g_header_row_normalized.index("calculated_roe")
g_calculated_roe_normalized_index_n                             = g_header_row_normalized.index("calculated_roe_normalized")
g_annualized_working_capital_index_n                            = g_header_row_normalized.index("annualized_working_capital")
g_quarterized_working_capital_index_n                           = g_header_row_normalized.index("quarterized_working_capital")
g_effective_working_capital_index_n                             = g_header_row_normalized.index("effective_working_capital")
g_annualized_total_liabilities_index_n                          = g_header_row_normalized.index("annualized_total_liabilities")
g_annualized_total_liabilities_bonus_index_n                    = g_header_row_normalized.index("annualized_total_liabilities_bonus")
g_quarterized_total_liabilities_index_n                         = g_header_row_normalized.index("quarterized_total_liabilities")
g_quarterized_total_liabilities_bonus_index_n                   = g_header_row_normalized.index("quarterized_total_liabilities_bonus")
g_effective_total_liabilities_index_n                           = g_header_row_normalized.index("effective_total_liabilities")
g_altman_z_score_factor_index_n                                 = g_header_row_normalized.index("altman_z_score_factor")
g_altman_z_score_factor_normalized_index_n                      = g_header_row_normalized.index("altman_z_score_factor_normalized")
g_skip_reason_index_n                                           = g_header_row_normalized.index("skip_reason")


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
    if VERBOSE_LOGS > 2: print("[{} weighted_average]".format(__name__), end='')
    return sum([float(values_list[i])*float(weights[i]) for i in range(len(values_list))])/float(sum(weights))


def set_skip_reason(stock_data):
    stock_data.skip_reason = ''

    if   stock_data.trailing_12months_price_to_sales is None: stock_data.skip_reason += 'trailing_12months_price_to_sales is None|'
    elif stock_data.trailing_12months_price_to_sales <= 0:    stock_data.skip_reason += 'trailing_12months_price_to_sales <= 0   |'
    if   stock_data.effective_profit_margin          is None: stock_data.skip_reason += 'effective_profit_margin          is None|'
    elif stock_data.effective_profit_margin          <= 0:    stock_data.skip_reason += 'effective_profit_margin          <= 0   |'
    if   stock_data.eqg_factor_effective             is None: stock_data.skip_reason += 'eqg_factor_effective             is None|'
    elif stock_data.eqg_factor_effective             <= 0:    stock_data.skip_reason += 'eqg_factor_effective             <= 0   |'
    if   stock_data.rqg_factor_effective             is None: stock_data.skip_reason += 'rqg_factor_effective             is None|'
    elif stock_data.rqg_factor_effective             <= 0:    stock_data.skip_reason += 'rqg_factor_effective             <= 0   |'
    if   stock_data.pe_effective                     is None: stock_data.skip_reason += 'pe_effective                     is None|'
    elif stock_data.pe_effective                     <= 0:    stock_data.skip_reason += 'pe_effective                     <= 0   |'
    if   stock_data.effective_ev_to_ebitda           is None: stock_data.skip_reason += 'effective_ev_to_ebitda           is None|'
    elif stock_data.effective_ev_to_ebitda           <= 0:    stock_data.skip_reason += 'effective_ev_to_ebitda           <= 0   |'
    if   stock_data.ev_to_cfo_ratio_effective        is None: stock_data.skip_reason += 'ev_to_cfo_ratio_effective        is None|'
    elif stock_data.ev_to_cfo_ratio_effective        <= 0:    stock_data.skip_reason += 'ev_to_cfo_ratio_effective        <= 0   |'
    if   stock_data.effective_peg_ratio              is None: stock_data.skip_reason += 'effective_peg_ratio              is None|'
    elif stock_data.effective_peg_ratio              <= 0:    stock_data.skip_reason += 'effective_peg_ratio              <= 0   |'
    if   stock_data.price_to_book                    is None: stock_data.skip_reason += 'price_to_book                    is None|'
    elif stock_data.price_to_book                    <= 0:    stock_data.skip_reason += 'price_to_book                    <= 0   |'
    if   stock_data.debt_to_equity_effective_used    is None: stock_data.skip_reason += 'debt_to_equity_effective_used    is None|'
    elif stock_data.debt_to_equity_effective_used    <= 0:    stock_data.skip_reason += 'debt_to_equity_effective_used    <= 0   |'
    if   stock_data.total_current_ratio_effective    is None: stock_data.skip_reason += 'total_current_ratio_effective    is None|'
    elif stock_data.total_current_ratio_effective    <= 0:    stock_data.skip_reason += 'total_current_ratio_effective    <= 0   |'
    if   stock_data.evr_effective                    is None: stock_data.skip_reason += 'evr_effective                    is None|'
    elif stock_data.evr_effective                    <= 0:    stock_data.skip_reason += 'evr_effective                    <= 0   |'
    if   stock_data.calculated_roa                   is None: stock_data.skip_reason += 'calculated_roa                   is None|'
    elif stock_data.calculated_roa                   <= 0:    stock_data.skip_reason += 'calculated_roa                   <= 0   |'
    if   stock_data.calculated_roe                   is None: stock_data.skip_reason += 'calculated_roe                   is None|'
    elif stock_data.calculated_roe                   <= 0:    stock_data.skip_reason += 'calculated_roe                   <= 0   |'
    if   stock_data.altman_z_score_factor            is None: stock_data.skip_reason += 'altman_z_score_factor            is None|'
    elif stock_data.altman_z_score_factor            <= 0:    stock_data.skip_reason += 'altman_z_score_factor            <= 0   |'
    if   stock_data.held_percent_insiders            is None: stock_data.skip_reason += 'held_percent_insiders            is None|'
    elif stock_data.held_percent_insiders            <= 0:    stock_data.skip_reason += 'held_percent_insiders            <= 0   |'


def get_list_of_csv_row_indices_which_affect_core_equation():
    return [g_eff_dist_from_low_factor_index, g_held_percent_insiders_index, g_evr_effective_index, g_pe_effective_index, g_effective_ev_to_ebitda_index, g_trailing_12months_price_to_sales_index, g_price_to_book_index, g_effective_profit_margin_index, g_effective_current_ratio_index, g_calculated_roa_index, g_calculated_roe_index, g_effective_peg_ratio_index, g_ev_to_cfo_ratio_effective_index, g_debt_to_equity_effective_used_index, g_eqg_factor_effective_index, g_rqg_factor_effective_index, g_altman_z_score_factor_index]


def sss_core_equation_value_set(stock_data):
    if VERBOSE_LOGS > 2: print("[{} sss_core_equation_value_set]".format(__name__), end='')
    if stock_data.shares_outstanding and stock_data.net_income_to_common_shareholders != None: stock_data.nitcsh_to_shares_outstanding = float(stock_data.net_income_to_common_shareholders) / float(stock_data.shares_outstanding)
    if stock_data.employees          and stock_data.net_income_to_common_shareholders != None: stock_data.nitcsh_to_num_employees      = float(stock_data.net_income_to_common_shareholders) / float(stock_data.employees)

    if sss_config.custom_sss_value_equation and stock_data.trailing_12months_price_to_sales != None and stock_data.trailing_12months_price_to_sales > 0 and stock_data.effective_profit_margin != None and stock_data.effective_profit_margin > 0 and stock_data.pe_effective != None and stock_data.pe_effective > 0 and stock_data.evr_effective != None and stock_data.evr_effective > 0.0:
        stock_data.sss_value = float(float(stock_data.evr_effective) * stock_data.pe_effective * stock_data.trailing_12months_price_to_sales / stock_data.effective_profit_margin)  # The lower  the better
        min_sss_value = round(10 ** (-NUM_ROUND_DECIMALS), NUM_ROUND_DECIMALS)
        stock_data.sss_value = max(stock_data.sss_value, min_sss_value)
    elif stock_data.trailing_12months_price_to_sales != None and stock_data.trailing_12months_price_to_sales > 0 and stock_data.effective_profit_margin != None and stock_data.effective_profit_margin > 0 and stock_data.eqg_factor_effective != None and stock_data.eqg_factor_effective > 0 and stock_data.rqg_factor_effective != None and stock_data.rqg_factor_effective > 0 and stock_data.pe_effective != None and stock_data.pe_effective > 0 and stock_data.effective_ev_to_ebitda != None and stock_data.effective_ev_to_ebitda > 0 and stock_data.ev_to_cfo_ratio_effective != None and stock_data.ev_to_cfo_ratio_effective > 0 and stock_data.effective_peg_ratio != None and stock_data.effective_peg_ratio > 0 and stock_data.price_to_book != None and stock_data.price_to_book > 0 and stock_data.debt_to_equity_effective_used != None and stock_data.debt_to_equity_effective_used > 0 and stock_data.effective_current_ratio != None and stock_data.effective_current_ratio > 0 and stock_data.evr_effective != None and stock_data.evr_effective > 0.0 and stock_data.calculated_roa != None and stock_data.calculated_roa > 0 and stock_data.calculated_roe != None and stock_data.calculated_roe > 0 and stock_data.altman_z_score_factor != None and stock_data.altman_z_score_factor > 0 and stock_data.held_percent_insiders != None and stock_data.held_percent_insiders > 0:
        stock_data.sss_value = float((stock_data.eff_dist_from_low_factor/stock_data.held_percent_insiders) * ((float(stock_data.evr_effective) * stock_data.pe_effective * stock_data.effective_ev_to_ebitda * stock_data.trailing_12months_price_to_sales * stock_data.price_to_book) / (stock_data.effective_profit_margin * stock_data.effective_current_ratio * stock_data.calculated_roa * stock_data.calculated_roe)) * ((stock_data.effective_peg_ratio * stock_data.ev_to_cfo_ratio_effective * stock_data.debt_to_equity_effective_used) / (stock_data.eqg_factor_effective * stock_data.rqg_factor_effective * stock_data.altman_z_score_factor)))  # The lower  the better
        min_sss_value        = round(10**(-NUM_ROUND_DECIMALS), NUM_ROUND_DECIMALS)
        stock_data.sss_value = max(stock_data.sss_value, min_sss_value)
    else:
        stock_data.sss_value = BAD_SSS
        set_skip_reason(stock_data)


def get_used_parameters_names_in_core_equation(custom_sss_value_equation):
    if custom_sss_value_equation:
        numerator_parameters_list   = ["evr_effective", "pe_effective", "trailing_12months_price_to_sales"]  # The lower  the better
        denominator_parameters_list = ["effective_profit_margin",                        ]  # The higher the better
    else:
        numerator_parameters_list   = ["eff_dist_from_low_factor", "evr_effective", "pe_effective", "effective_ev_to_ebitda", "trailing_12months_price_to_sales", "price_to_book",        "effective_peg_ratio",   "ev_to_cfo_ratio_effective", "debt_to_equity_effective_used"]  # The lower  the better
        denominator_parameters_list = ["effective_profit_margin",  "effective_current_ratio",       "calculated_roa",       "calculated_roe",         "eqg_factor_effective",             "rqg_factor_effective", "altman_z_score_factor", "held_percent_insiders"                                     ]  # The higher the better
    return [numerator_parameters_list, denominator_parameters_list]


# Rounding to non-None values + set None values to 0 for simplicity:
def round_and_avoid_none_values(stock_data):
    if stock_data.sss_value                                             != None: stock_data.sss_value                                             = round(stock_data.sss_value,                                             NUM_ROUND_DECIMALS)
    if stock_data.annualized_revenue                                    != None: stock_data.annualized_revenue                                    = round(stock_data.annualized_revenue,                                    NUM_ROUND_DECIMALS)
    if stock_data.annualized_revenue_bonus                              != None: stock_data.annualized_revenue_bonus                              = round(stock_data.annualized_revenue_bonus,                              NUM_ROUND_DECIMALS)
    if stock_data.annualized_earnings                                   != None: stock_data.annualized_earnings                                   = round(stock_data.annualized_earnings,                                   NUM_ROUND_DECIMALS)
    if stock_data.annualized_retained_earnings                          != None: stock_data.annualized_retained_earnings                          = round(stock_data.annualized_retained_earnings,                          NUM_ROUND_DECIMALS)
    if stock_data.annualized_retained_earnings_bonus                    != None: stock_data.annualized_retained_earnings_bonus                    = round(stock_data.annualized_retained_earnings_bonus,                    NUM_ROUND_DECIMALS)
    if stock_data.quarterized_revenue                                   != None: stock_data.quarterized_revenue                                   = round(stock_data.quarterized_revenue,                                   NUM_ROUND_DECIMALS)
    if stock_data.quarterized_revenue_bonus                             != None: stock_data.quarterized_revenue_bonus                             = round(stock_data.quarterized_revenue_bonus,                             NUM_ROUND_DECIMALS)
    if stock_data.quarterized_earnings                                  != None: stock_data.quarterized_earnings                                  = round(stock_data.quarterized_earnings,                                  NUM_ROUND_DECIMALS)
    if stock_data.quarterized_earnings_bonus                            != None: stock_data.quarterized_earnings_bonus                            = round(stock_data.quarterized_earnings_bonus,                            NUM_ROUND_DECIMALS)
    if stock_data.quarterized_retained_earnings                         != None: stock_data.quarterized_retained_earnings                         = round(stock_data.quarterized_retained_earnings,                         NUM_ROUND_DECIMALS)
    if stock_data.quarterized_retained_earnings_bonus                   != None: stock_data.quarterized_retained_earnings_bonus                   = round(stock_data.quarterized_retained_earnings_bonus,                   NUM_ROUND_DECIMALS)
    if stock_data.effective_earnings                                    != None: stock_data.effective_earnings                                    = round(stock_data.effective_earnings,                                    NUM_ROUND_DECIMALS)
    if stock_data.effective_retained_earnings                           != None: stock_data.effective_retained_earnings                           = round(stock_data.effective_retained_earnings,                           NUM_ROUND_DECIMALS)
    if stock_data.effective_revenue                                     != None: stock_data.effective_revenue                                     = round(stock_data.effective_revenue,                                     NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_revenue                              != None: stock_data.annualized_total_revenue                              = round(stock_data.annualized_total_revenue,                              NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_revenue_bonus                        != None: stock_data.annualized_total_revenue_bonus                        = round(stock_data.annualized_total_revenue_bonus,                        NUM_ROUND_DECIMALS)
    if stock_data.annualized_net_income                                 != None: stock_data.annualized_net_income                                 = round(stock_data.annualized_net_income,                                 NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_revenue                             != None: stock_data.quarterized_total_revenue                             = round(stock_data.quarterized_total_revenue,                             NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_revenue_bonus                       != None: stock_data.quarterized_total_revenue_bonus                       = round(stock_data.quarterized_total_revenue_bonus,                       NUM_ROUND_DECIMALS)
    if stock_data.quarterized_net_income                                != None: stock_data.quarterized_net_income                                = round(stock_data.quarterized_net_income,                                NUM_ROUND_DECIMALS)
    if stock_data.quarterized_net_income_bonus                          != None: stock_data.quarterized_net_income_bonus                          = round(stock_data.quarterized_net_income_bonus,                          NUM_ROUND_DECIMALS)
    if stock_data.effective_net_income                                  != None: stock_data.effective_net_income                                  = round(stock_data.effective_net_income,                                  NUM_ROUND_DECIMALS)
    if stock_data.effective_total_revenue                               != None: stock_data.effective_total_revenue                               = round(stock_data.effective_total_revenue,                               NUM_ROUND_DECIMALS)
    if stock_data.enterprise_value_to_revenue                           != None: stock_data.enterprise_value_to_revenue                           = round(stock_data.enterprise_value_to_revenue,                           NUM_ROUND_DECIMALS)
    if stock_data.evr_effective                                         != None: stock_data.evr_effective                                         = round(stock_data.evr_effective,                                         NUM_ROUND_DECIMALS)
    if stock_data.trailing_price_to_earnings                            != None: stock_data.trailing_price_to_earnings                            = round(stock_data.trailing_price_to_earnings,                            NUM_ROUND_DECIMALS)
    if stock_data.forward_price_to_earnings                             != None: stock_data.forward_price_to_earnings                             = round(stock_data.forward_price_to_earnings,                             NUM_ROUND_DECIMALS)
    if stock_data.effective_price_to_earnings                           != None: stock_data.effective_price_to_earnings                           = round(stock_data.effective_price_to_earnings,                           NUM_ROUND_DECIMALS)
    if stock_data.trailing_12months_price_to_sales                      != None: stock_data.trailing_12months_price_to_sales                      = round(stock_data.trailing_12months_price_to_sales,                      NUM_ROUND_DECIMALS)
    if stock_data.pe_effective                                          != None: stock_data.pe_effective                                          = round(stock_data.pe_effective,                                          NUM_ROUND_DECIMALS)
    if stock_data.enterprise_value_to_ebitda                            != None: stock_data.enterprise_value_to_ebitda                            = round(stock_data.enterprise_value_to_ebitda,                            NUM_ROUND_DECIMALS)
    if stock_data.effective_ev_to_ebitda                                != None: stock_data.effective_ev_to_ebitda                                = round(stock_data.effective_ev_to_ebitda,                                NUM_ROUND_DECIMALS)
    if stock_data.ebitda                                                != None: stock_data.ebitda                                                = round(stock_data.ebitda,                                                NUM_ROUND_DECIMALS)
    if stock_data.quarterized_ebitd                                     != None: stock_data.quarterized_ebitd                                     = round(stock_data.quarterized_ebitd,                                     NUM_ROUND_DECIMALS)
    if stock_data.annualized_ebitd                                      != None: stock_data.annualized_ebitd                                      = round(stock_data.annualized_ebitd,                                      NUM_ROUND_DECIMALS)
    if stock_data.ebitd                                                 != None: stock_data.ebitd                                                 = round(stock_data.ebitd,                                                 NUM_ROUND_DECIMALS)
    if stock_data.profit_margin                                         != None: stock_data.profit_margin                                         = round(stock_data.profit_margin,                                         NUM_ROUND_DECIMALS)
    if stock_data.annualized_profit_margin                              != None: stock_data.annualized_profit_margin                              = round(stock_data.annualized_profit_margin,                              NUM_ROUND_DECIMALS)
    if stock_data.annualized_profit_margin_boost                        != None: stock_data.annualized_profit_margin_boost                        = round(stock_data.annualized_profit_margin_boost,                        NUM_ROUND_DECIMALS)
    if stock_data.quarterized_profit_margin                             != None: stock_data.quarterized_profit_margin                             = round(stock_data.quarterized_profit_margin,                             NUM_ROUND_DECIMALS)
    if stock_data.quarterized_profit_margin_boost                       != None: stock_data.quarterized_profit_margin_boost                       = round(stock_data.quarterized_profit_margin_boost,                       NUM_ROUND_DECIMALS)
    if stock_data.effective_profit_margin                               != None: stock_data.effective_profit_margin                               = round(stock_data.effective_profit_margin,                               NUM_ROUND_DECIMALS)
    if stock_data.held_percent_institutions                             != None: stock_data.held_percent_institutions                             = round(stock_data.held_percent_institutions,                             NUM_ROUND_DECIMALS)
    if stock_data.held_percent_insiders                                 != None: stock_data.held_percent_insiders                                 = round(stock_data.held_percent_insiders,                                 NUM_ROUND_DECIMALS)
    if stock_data.forward_eps                                           != None: stock_data.forward_eps                                           = round(stock_data.forward_eps,                                           NUM_ROUND_DECIMALS)
    if stock_data.trailing_eps                                          != None: stock_data.trailing_eps                                          = round(stock_data.trailing_eps,                                          NUM_ROUND_DECIMALS)
    if stock_data.previous_close                                        != None: stock_data.previous_close                                        = round(stock_data.previous_close,                                        NUM_ROUND_DECIMALS)
    if stock_data.trailing_eps_percentage                               != None: stock_data.trailing_eps_percentage                               = round(stock_data.trailing_eps_percentage,                               NUM_ROUND_DECIMALS)
    if stock_data.price_to_book                                         != None: stock_data.price_to_book                                         = round(stock_data.price_to_book,                                         NUM_ROUND_DECIMALS)
    if stock_data.shares_outstanding                                    != None: stock_data.shares_outstanding                                    = round(stock_data.shares_outstanding,                                    NUM_ROUND_DECIMALS)
    if stock_data.net_income_to_common_shareholders                     != None: stock_data.net_income_to_common_shareholders                     = round(stock_data.net_income_to_common_shareholders,                     NUM_ROUND_DECIMALS)
    if stock_data.nitcsh_to_shares_outstanding                          != None: stock_data.nitcsh_to_shares_outstanding                          = round(stock_data.nitcsh_to_shares_outstanding,                          NUM_ROUND_DECIMALS)
    if stock_data.employees                                             != None: stock_data.employees                                             = int(  stock_data.employees                                                                )
    if stock_data.enterprise_value                                      != None: stock_data.enterprise_value                                      = int(  stock_data.enterprise_value                                                         )
    if stock_data.market_cap                                            != None: stock_data.market_cap                                            = int(  stock_data.market_cap                                                               )
    if stock_data.nitcsh_to_num_employees                               != None: stock_data.nitcsh_to_num_employees                               = round(stock_data.nitcsh_to_num_employees,                               NUM_ROUND_DECIMALS)
    if stock_data.eqg                                                   != None: stock_data.eqg                                                   = round(stock_data.eqg,                                                   NUM_ROUND_DECIMALS)
    if stock_data.rqg                                                   != None: stock_data.rqg                                                   = round(stock_data.rqg,                                                   NUM_ROUND_DECIMALS)
    if stock_data.eqg_yoy                                               != None: stock_data.eqg_yoy                                               = round(stock_data.eqg_yoy,                                               NUM_ROUND_DECIMALS)
    if stock_data.rqg_yoy                                               != None: stock_data.rqg_yoy                                               = round(stock_data.rqg_yoy,                                               NUM_ROUND_DECIMALS)
    if stock_data.niqg_yoy                                              != None: stock_data.niqg_yoy                                              = round(stock_data.niqg_yoy,                                              NUM_ROUND_DECIMALS)
    if stock_data.trqg_yoy                                              != None: stock_data.trqg_yoy                                              = round(stock_data.trqg_yoy,                                              NUM_ROUND_DECIMALS)
    if stock_data.eqg_effective                                         != None: stock_data.eqg_effective                                         = round(stock_data.eqg_effective,                                         NUM_ROUND_DECIMALS)
    if stock_data.eqg_factor_effective                                  != None: stock_data.eqg_factor_effective                                  = round(stock_data.eqg_factor_effective,                                  NUM_ROUND_DECIMALS)
    if stock_data.rqg_effective                                         != None: stock_data.rqg_effective                                         = round(stock_data.rqg_effective,                                         NUM_ROUND_DECIMALS)
    if stock_data.rqg_factor_effective                                  != None: stock_data.rqg_factor_effective                                  = round(stock_data.rqg_factor_effective,                                  NUM_ROUND_DECIMALS)
    if stock_data.price_to_earnings_to_growth_ratio                     != None: stock_data.price_to_earnings_to_growth_ratio                     = round(stock_data.price_to_earnings_to_growth_ratio,                     NUM_ROUND_DECIMALS)
    if stock_data.effective_peg_ratio                                   != None: stock_data.effective_peg_ratio                                   = round(stock_data.effective_peg_ratio,                                   NUM_ROUND_DECIMALS)
    if stock_data.annualized_cash_flow_from_operating_activities        != None: stock_data.annualized_cash_flow_from_operating_activities        = round(stock_data.annualized_cash_flow_from_operating_activities,        NUM_ROUND_DECIMALS)
    if stock_data.annualized_cash_flow_from_operating_activities_bonus  != None: stock_data.annualized_cash_flow_from_operating_activities_bonus  = round(stock_data.annualized_cash_flow_from_operating_activities_bonus,  NUM_ROUND_DECIMALS)
    if stock_data.quarterized_cash_flow_from_operating_activities       != None: stock_data.quarterized_cash_flow_from_operating_activities       = round(stock_data.quarterized_cash_flow_from_operating_activities,       NUM_ROUND_DECIMALS)
    if stock_data.quarterized_cash_flow_from_operating_activities_bonus != None: stock_data.quarterized_cash_flow_from_operating_activities_bonus = round(stock_data.quarterized_cash_flow_from_operating_activities_bonus, NUM_ROUND_DECIMALS)
    if stock_data.annualized_ev_to_cfo_ratio                            != None: stock_data.annualized_ev_to_cfo_ratio                            = round(stock_data.annualized_ev_to_cfo_ratio,                            NUM_ROUND_DECIMALS)
    if stock_data.quarterized_ev_to_cfo_ratio                           != None: stock_data.quarterized_ev_to_cfo_ratio                           = round(stock_data.quarterized_ev_to_cfo_ratio,                           NUM_ROUND_DECIMALS)
    if stock_data.ev_to_cfo_ratio_effective                             != None: stock_data.ev_to_cfo_ratio_effective                             = round(stock_data.ev_to_cfo_ratio_effective,                             NUM_ROUND_DECIMALS)
    if stock_data.annualized_debt_to_equity                             != None: stock_data.annualized_debt_to_equity                             = round(stock_data.annualized_debt_to_equity,                             NUM_ROUND_DECIMALS)
    if stock_data.annualized_debt_to_equity_bonus                       != None: stock_data.annualized_debt_to_equity_bonus                       = round(stock_data.annualized_debt_to_equity_bonus,                       NUM_ROUND_DECIMALS)
    if stock_data.quarterized_debt_to_equity                            != None: stock_data.quarterized_debt_to_equity                            = round(stock_data.quarterized_debt_to_equity,                            NUM_ROUND_DECIMALS)
    if stock_data.quarterized_debt_to_equity_bonus                      != None: stock_data.quarterized_debt_to_equity_bonus                      = round(stock_data.quarterized_debt_to_equity_bonus,                      NUM_ROUND_DECIMALS)
    if stock_data.debt_to_equity_effective                              != None: stock_data.debt_to_equity_effective                              = round(stock_data.debt_to_equity_effective,                              NUM_ROUND_DECIMALS)
    if stock_data.debt_to_equity_effective_used                         != None: stock_data.debt_to_equity_effective_used                         = round(stock_data.debt_to_equity_effective_used,                         NUM_ROUND_DECIMALS)
    if stock_data.financial_currency_conversion_rate_mult_to_usd        != None: stock_data.financial_currency_conversion_rate_mult_to_usd        = round(stock_data.financial_currency_conversion_rate_mult_to_usd,        NUM_ROUND_DECIMALS)
    if stock_data.summary_currency_conversion_rate_mult_to_usd          != None: stock_data.summary_currency_conversion_rate_mult_to_usd          = round(stock_data.summary_currency_conversion_rate_mult_to_usd,          NUM_ROUND_DECIMALS)
    if stock_data.last_dividend_0                                       != None: stock_data.last_dividend_0                                       = round(stock_data.last_dividend_0,                                       NUM_ROUND_DECIMALS)
    if stock_data.last_dividend_1                                       != None: stock_data.last_dividend_1                                       = round(stock_data.last_dividend_1,                                       NUM_ROUND_DECIMALS)
    if stock_data.last_dividend_2                                       != None: stock_data.last_dividend_2                                       = round(stock_data.last_dividend_2,                                       NUM_ROUND_DECIMALS)
    if stock_data.last_dividend_3                                       != None: stock_data.last_dividend_3                                       = round(stock_data.last_dividend_3,                                       NUM_ROUND_DECIMALS)
    if stock_data.fifty_two_week_change                                 != None: stock_data.fifty_two_week_change                                 = round(stock_data.fifty_two_week_change,                                 NUM_ROUND_DECIMALS)
    if stock_data.fifty_two_week_low                                    != None: stock_data.fifty_two_week_low                                    = round(stock_data.fifty_two_week_low,                                    NUM_ROUND_DECIMALS)
    if stock_data.fifty_two_week_high                                   != None: stock_data.fifty_two_week_high                                   = round(stock_data.fifty_two_week_high,                                   NUM_ROUND_DECIMALS)
    if stock_data.two_hundred_day_average                               != None: stock_data.two_hundred_day_average                               = round(stock_data.two_hundred_day_average,                               NUM_ROUND_DECIMALS)
    if stock_data.previous_close_percentage_from_200d_ma                != None: stock_data.previous_close_percentage_from_200d_ma                = round(stock_data.previous_close_percentage_from_200d_ma,                NUM_ROUND_DECIMALS)
    if stock_data.previous_close_percentage_from_52w_low                != None: stock_data.previous_close_percentage_from_52w_low                = round(stock_data.previous_close_percentage_from_52w_low,                NUM_ROUND_DECIMALS)
    if stock_data.previous_close_percentage_from_52w_high               != None: stock_data.previous_close_percentage_from_52w_high               = round(stock_data.previous_close_percentage_from_52w_high,               NUM_ROUND_DECIMALS)
    if stock_data.dist_from_low_factor                                  != None: stock_data.dist_from_low_factor                                  = round(stock_data.dist_from_low_factor,                                  NUM_ROUND_DECIMALS)
    if stock_data.eff_dist_from_low_factor                              != None: stock_data.eff_dist_from_low_factor                              = round(stock_data.eff_dist_from_low_factor,                              NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_ratio                                != None: stock_data.annualized_total_ratio                                = round(stock_data.annualized_total_ratio,                                NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_ratio_bonus                          != None: stock_data.annualized_total_ratio_bonus                          = round(stock_data.annualized_total_ratio_bonus,                          NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_ratio                               != None: stock_data.quarterized_total_ratio                               = round(stock_data.quarterized_total_ratio,                               NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_ratio_bonus                         != None: stock_data.quarterized_total_ratio_bonus                         = round(stock_data.quarterized_total_ratio_bonus,                         NUM_ROUND_DECIMALS)
    if stock_data.annualized_other_current_ratio                        != None: stock_data.annualized_other_current_ratio                        = round(stock_data.annualized_other_current_ratio,                        NUM_ROUND_DECIMALS)
    if stock_data.annualized_other_current_ratio_bonus                  != None: stock_data.annualized_other_current_ratio_bonus                  = round(stock_data.annualized_other_current_ratio_bonus,                  NUM_ROUND_DECIMALS)
    if stock_data.quarterized_other_current_ratio                       != None: stock_data.quarterized_other_current_ratio                       = round(stock_data.quarterized_other_current_ratio,                       NUM_ROUND_DECIMALS)
    if stock_data.quarterized_other_current_ratio_bonus                 != None: stock_data.quarterized_other_current_ratio_bonus                 = round(stock_data.quarterized_other_current_ratio_bonus,                 NUM_ROUND_DECIMALS)
    if stock_data.annualized_other_ratio                                != None: stock_data.annualized_other_ratio                                = round(stock_data.annualized_other_ratio,                                NUM_ROUND_DECIMALS)
    if stock_data.annualized_other_ratio_bonus                          != None: stock_data.annualized_other_ratio_bonus                          = round(stock_data.annualized_other_ratio_bonus,                          NUM_ROUND_DECIMALS)
    if stock_data.quarterized_other_ratio                               != None: stock_data.quarterized_other_ratio                               = round(stock_data.quarterized_other_ratio,                               NUM_ROUND_DECIMALS)
    if stock_data.quarterized_other_ratio_bonus                         != None: stock_data.quarterized_other_ratio_bonus                         = round(stock_data.quarterized_other_ratio_bonus,                         NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_current_ratio                        != None: stock_data.annualized_total_current_ratio                        = round(stock_data.annualized_total_current_ratio,                        NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_current_ratio_bonus                  != None: stock_data.annualized_total_current_ratio_bonus                  = round(stock_data.annualized_total_current_ratio_bonus,                  NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_current_ratio                       != None: stock_data.quarterized_total_current_ratio                       = round(stock_data.quarterized_total_current_ratio,                       NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_current_ratio_bonus                 != None: stock_data.quarterized_total_current_ratio_bonus                 = round(stock_data.quarterized_total_current_ratio_bonus,                 NUM_ROUND_DECIMALS)
    if stock_data.total_ratio_effective                                 != None: stock_data.total_ratio_effective                                 = round(stock_data.total_ratio_effective,                                 NUM_ROUND_DECIMALS)
    if stock_data.other_current_ratio_effective                         != None: stock_data.other_current_ratio_effective                         = round(stock_data.other_current_ratio_effective,                         NUM_ROUND_DECIMALS)
    if stock_data.other_ratio_effective                                 != None: stock_data.other_ratio_effective                                 = round(stock_data.other_ratio_effective,                                 NUM_ROUND_DECIMALS)
    if stock_data.total_current_ratio_effective                         != None: stock_data.total_current_ratio_effective                         = round(stock_data.total_current_ratio_effective,                         NUM_ROUND_DECIMALS)
    if stock_data.effective_current_ratio                               != None: stock_data.effective_current_ratio                               = round(stock_data.effective_current_ratio,                               NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_assets                               != None: stock_data.annualized_total_assets                               = round(stock_data.annualized_total_assets,                               NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_assets_bonus                         != None: stock_data.annualized_total_assets_bonus                         = round(stock_data.annualized_total_assets_bonus,                         NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_assets                              != None: stock_data.quarterized_total_assets                              = round(stock_data.quarterized_total_assets,                              NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_assets_bonus                        != None: stock_data.quarterized_total_assets_bonus                        = round(stock_data.quarterized_total_assets_bonus,                        NUM_ROUND_DECIMALS)
    if stock_data.effective_total_assets                                != None: stock_data.effective_total_assets                                = round(stock_data.effective_total_assets,                                NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_stockholder_equity                   != None: stock_data.annualized_total_stockholder_equity                   = round(stock_data.annualized_total_stockholder_equity,                   NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_stockholder_equity_bonus             != None: stock_data.annualized_total_stockholder_equity_bonus             = round(stock_data.annualized_total_stockholder_equity_bonus,             NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_stockholder_equity                  != None: stock_data.quarterized_total_stockholder_equity                  = round(stock_data.quarterized_total_stockholder_equity,                  NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_stockholder_equity_bonus            != None: stock_data.quarterized_total_stockholder_equity_bonus            = round(stock_data.quarterized_total_stockholder_equity_bonus,            NUM_ROUND_DECIMALS)
    if stock_data.effective_total_stockholder_equity                    != None: stock_data.effective_total_stockholder_equity                    = round(stock_data.effective_total_stockholder_equity,                    NUM_ROUND_DECIMALS)
    if stock_data.calculated_roa                                        != None: stock_data.calculated_roa                                        = round(stock_data.calculated_roa,                                        NUM_ROUND_DECIMALS)
    if stock_data.calculated_roe                                        != None: stock_data.calculated_roe                                        = round(stock_data.calculated_roe,                                        NUM_ROUND_DECIMALS)
    if stock_data.annualized_working_capital                            != None: stock_data.annualized_working_capital                            = round(stock_data.annualized_working_capital,                            NUM_ROUND_DECIMALS)
    if stock_data.quarterized_working_capital                           != None: stock_data.quarterized_working_capital                           = round(stock_data.quarterized_working_capital,                           NUM_ROUND_DECIMALS)
    if stock_data.effective_working_capital                             != None: stock_data.effective_working_capital                             = round(stock_data.effective_working_capital,                             NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_liabilities                          != None: stock_data.annualized_total_liabilities                          = round(stock_data.annualized_total_liabilities,                          NUM_ROUND_DECIMALS)
    if stock_data.annualized_total_liabilities_bonus                    != None: stock_data.annualized_total_liabilities_bonus                    = round(stock_data.annualized_total_liabilities_bonus,                    NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_liabilities                         != None: stock_data.quarterized_total_liabilities                         = round(stock_data.quarterized_total_liabilities,                         NUM_ROUND_DECIMALS)
    if stock_data.quarterized_total_liabilities_bonus                   != None: stock_data.quarterized_total_liabilities_bonus                   = round(stock_data.quarterized_total_liabilities_bonus,                   NUM_ROUND_DECIMALS)
    if stock_data.effective_total_liabilities                           != None: stock_data.effective_total_liabilities                           = round(stock_data.effective_total_liabilities,                           NUM_ROUND_DECIMALS)
    if stock_data.altman_z_score_factor                                 != None: stock_data.altman_z_score_factor                                 = round(stock_data.altman_z_score_factor,                                 NUM_ROUND_DECIMALS)

    # TODO: ASAFR: Unify below with above to single line for each parameter
    if stock_data.sss_value                                             is None: stock_data.sss_value                                             = BAD_SSS
    if stock_data.annualized_revenue                                    is None: stock_data.annualized_revenue                                    = 0
    if stock_data.annualized_revenue_bonus                              is None: stock_data.annualized_revenue_bonus                              = 0.0
    if stock_data.annualized_earnings                                   is None: stock_data.annualized_earnings                                   = 0
    if stock_data.annualized_retained_earnings                          is None: stock_data.annualized_retained_earnings                          = 0
    if stock_data.annualized_retained_earnings_bonus                    is None: stock_data.annualized_retained_earnings_bonus                    = 0.0
    if stock_data.quarterized_revenue                                   is None: stock_data.quarterized_revenue                                   = 0
    if stock_data.quarterized_revenue_bonus                             is None: stock_data.quarterized_revenue_bonus                             = 0.0
    if stock_data.quarterized_earnings                                  is None: stock_data.quarterized_earnings                                  = 0
    if stock_data.quarterized_earnings_bonus                            is None: stock_data.quarterized_earnings_bonus                            = 0.0
    if stock_data.quarterized_retained_earnings                         is None: stock_data.quarterized_retained_earnings                         = 0
    if stock_data.quarterized_retained_earnings_bonus                   is None: stock_data.quarterized_retained_earnings_bonus                   = 0.0
    if stock_data.effective_earnings                                    is None: stock_data.effective_earnings                                    = 0
    if stock_data.effective_retained_earnings                           is None: stock_data.effective_retained_earnings                           = 0
    if stock_data.effective_revenue                                     is None: stock_data.effective_revenue                                     = 0
    if stock_data.annualized_total_revenue                              is None: stock_data.annualized_total_revenue                              = 0
    if stock_data.annualized_total_revenue_bonus                        is None: stock_data.annualized_total_revenue_bonus                        = 0.0
    if stock_data.annualized_net_income                                 is None: stock_data.annualized_net_income                                 = 0
    if stock_data.quarterized_total_revenue                             is None: stock_data.quarterized_total_revenue                             = 0
    if stock_data.quarterized_total_revenue_bonus                       is None: stock_data.quarterized_total_revenue_bonus                       = 0.0
    if stock_data.quarterized_net_income                                is None: stock_data.quarterized_net_income                                = 0
    if stock_data.quarterized_net_income_bonus                          is None: stock_data.quarterized_net_income_bonus                          = 0.0
    if stock_data.effective_net_income                                  is None: stock_data.effective_net_income                                  = 0
    if stock_data.effective_total_revenue                               is None: stock_data.effective_total_revenue                               = 0
    if stock_data.enterprise_value_to_revenue                           is None: stock_data.enterprise_value_to_revenue                           = 0
    if stock_data.evr_effective                                         is None: stock_data.evr_effective                                         = 0.0
    if stock_data.trailing_price_to_earnings                            is None: stock_data.trailing_price_to_earnings                            = 0
    if stock_data.forward_price_to_earnings                             is None: stock_data.forward_price_to_earnings                             = 0
    if stock_data.effective_price_to_earnings                           is None: stock_data.effective_price_to_earnings                           = 0
    if stock_data.trailing_12months_price_to_sales                      is None: stock_data.trailing_12months_price_to_sales                      = 0
    if stock_data.pe_effective                                          is None: stock_data.pe_effective                                          = 0
    if stock_data.enterprise_value_to_ebitda                            is None: stock_data.enterprise_value_to_ebitda                            = 0
    if stock_data.effective_ev_to_ebitda                                is None: stock_data.effective_ev_to_ebitda                                = 0
    if stock_data.ebitda                                                is None: stock_data.ebitda                                                = 0
    if stock_data.quarterized_ebitd                                     is None: stock_data.quarterized_ebitd                                     = 0
    if stock_data.annualized_ebitd                                      is None: stock_data.annualized_ebitd                                      = 0
    if stock_data.ebitd                                                 is None: stock_data.ebitd                                                 = 0
    if stock_data.profit_margin                                         is None: stock_data.profit_margin                                         = 0
    if stock_data.annualized_profit_margin                              is None: stock_data.annualized_profit_margin                              = 0
    if stock_data.annualized_profit_margin_boost                        is None: stock_data.annualized_profit_margin_boost                        = 0
    if stock_data.quarterized_profit_margin                             is None: stock_data.quarterized_profit_margin                             = 0
    if stock_data.quarterized_profit_margin_boost                       is None: stock_data.quarterized_profit_margin_boost                       = 0
    if stock_data.effective_profit_margin                               is None: stock_data.effective_profit_margin                               = 0
    if stock_data.held_percent_institutions                             is None: stock_data.held_percent_institutions                             = 0
    if stock_data.held_percent_insiders                                 is None: stock_data.held_percent_insiders                                 = 0
    if stock_data.forward_eps                                           is None: stock_data.forward_eps                                           = 0
    if stock_data.trailing_eps                                          is None: stock_data.trailing_eps                                          = 0
    if stock_data.previous_close                                        is None: stock_data.previous_close                                        = 0
    if stock_data.trailing_eps_percentage                               is None: stock_data.trailing_eps_percentage                               = 0
    if stock_data.price_to_book                                         is None: stock_data.price_to_book                                         = 0
    if stock_data.shares_outstanding                                    is None: stock_data.shares_outstanding                                    = 0
    if stock_data.net_income_to_common_shareholders                     is None: stock_data.net_income_to_common_shareholders                     = 0
    if stock_data.nitcsh_to_shares_outstanding                          is None: stock_data.nitcsh_to_shares_outstanding                          = 0
    if stock_data.employees                                             is None: stock_data.employees                                             = 0
    if stock_data.enterprise_value                                      is None: stock_data.enterprise_value                                      = 0
    if stock_data.market_cap                                            is None: stock_data.market_cap                                            = 0
    if stock_data.nitcsh_to_num_employees                               is None: stock_data.nitcsh_to_num_employees                               = 0
    if stock_data.eqg                                                   is None: stock_data.eqg                                                   = 0
    if stock_data.rqg                                                   is None: stock_data.rqg                                                   = 0
    if stock_data.eqg_yoy                                               is None: stock_data.eqg_yoy                                               = 0
    if stock_data.rqg_yoy                                               is None: stock_data.rqg_yoy                                               = 0
    if stock_data.niqg_yoy                                              is None: stock_data.niqg_yoy                                              = 0
    if stock_data.trqg_yoy                                              is None: stock_data.trqg_yoy                                              = 0
    if stock_data.eqg_effective                                         is None: stock_data.eqg_effective                                         = 0
    if stock_data.eqg_factor_effective                                  is None: stock_data.eqg_factor_effective                                  = 0
    if stock_data.rqg_effective                                         is None: stock_data.rqg_effective                                         = 0
    if stock_data.rqg_factor_effective                                  is None: stock_data.rqg_factor_effective                                  = 0
    if stock_data.price_to_earnings_to_growth_ratio                     is None: stock_data.price_to_earnings_to_growth_ratio                     = 0
    if stock_data.effective_peg_ratio                                   is None: stock_data.effective_peg_ratio                                   = 0
    if stock_data.annualized_cash_flow_from_operating_activities        is None: stock_data.annualized_cash_flow_from_operating_activities        = 0
    if stock_data.annualized_cash_flow_from_operating_activities_bonus  is None: stock_data.annualized_cash_flow_from_operating_activities_bonus  = 0.0
    if stock_data.quarterized_cash_flow_from_operating_activities       is None: stock_data.quarterized_cash_flow_from_operating_activities       = 0
    if stock_data.quarterized_cash_flow_from_operating_activities_bonus is None: stock_data.quarterized_cash_flow_from_operating_activities_bonus = 0.0
    if stock_data.annualized_ev_to_cfo_ratio                            is None: stock_data.annualized_ev_to_cfo_ratio                            = 0
    if stock_data.quarterized_ev_to_cfo_ratio                           is None: stock_data.quarterized_ev_to_cfo_ratio                           = 0
    if stock_data.ev_to_cfo_ratio_effective                             is None: stock_data.ev_to_cfo_ratio_effective                             = 0
    if stock_data.annualized_debt_to_equity                             is None: stock_data.annualized_debt_to_equity                             = 0
    if stock_data.annualized_debt_to_equity_bonus                       is None: stock_data.annualized_debt_to_equity_bonus                       = 0.0
    if stock_data.quarterized_debt_to_equity                            is None: stock_data.quarterized_debt_to_equity                            = 0
    if stock_data.quarterized_debt_to_equity_bonus                      is None: stock_data.quarterized_debt_to_equity_bonus                      = 0.0
    if stock_data.debt_to_equity_effective                              is None: stock_data.debt_to_equity_effective                              = 0
    if stock_data.debt_to_equity_effective_used                         is None: stock_data.debt_to_equity_effective_used                         = 0
    if stock_data.financial_currency_conversion_rate_mult_to_usd        is None: stock_data.financial_currency_conversion_rate_mult_to_usd        = 0
    if stock_data.summary_currency_conversion_rate_mult_to_usd          is None: stock_data.summary_currency_conversion_rate_mult_to_usd          = 0
    if stock_data.last_dividend_0                                       is None: stock_data.last_dividend_0                                       = 0
    if stock_data.last_dividend_1                                       is None: stock_data.last_dividend_1                                       = 0
    if stock_data.last_dividend_2                                       is None: stock_data.last_dividend_2                                       = 0
    if stock_data.last_dividend_3                                       is None: stock_data.last_dividend_3                                       = 0
    if stock_data.fifty_two_week_change                                 is None: stock_data.fifty_two_week_change                                 = 0
    if stock_data.fifty_two_week_low                                    is None: stock_data.fifty_two_week_low                                    = 0
    if stock_data.fifty_two_week_high                                   is None: stock_data.fifty_two_week_high                                   = 0
    if stock_data.two_hundred_day_average                               is None: stock_data.two_hundred_day_average                               = 0
    if stock_data.previous_close_percentage_from_200d_ma                is None: stock_data.previous_close_percentage_from_200d_ma                = 0
    if stock_data.previous_close_percentage_from_52w_low                is None: stock_data.previous_close_percentage_from_52w_low                = 0
    if stock_data.previous_close_percentage_from_52w_high               is None: stock_data.previous_close_percentage_from_52w_high               = 0
    if stock_data.dist_from_low_factor                                  is None: stock_data.dist_from_low_factor                                  = 0
    if stock_data.eff_dist_from_low_factor                              is None: stock_data.eff_dist_from_low_factor                              = 0
    if stock_data.annualized_total_ratio                                is None: stock_data.annualized_total_ratio                                = 0
    if stock_data.annualized_total_ratio_bonus                          is None: stock_data.annualized_total_ratio_bonus                          = 0.0
    if stock_data.quarterized_total_ratio                               is None: stock_data.quarterized_total_ratio                               = 0
    if stock_data.quarterized_total_ratio_bonus                         is None: stock_data.quarterized_total_ratio_bonus                         = 0.0
    if stock_data.annualized_other_current_ratio                        is None: stock_data.annualized_other_current_ratio                        = 0
    if stock_data.annualized_other_current_ratio_bonus                  is None: stock_data.annualized_other_current_ratio_bonus                  = 0.0
    if stock_data.quarterized_other_current_ratio                       is None: stock_data.quarterized_other_current_ratio                       = 0
    if stock_data.quarterized_other_current_ratio_bonus                 is None: stock_data.quarterized_other_current_ratio_bonus                 = 0.0
    if stock_data.annualized_other_ratio                                is None: stock_data.annualized_other_ratio                                = 0
    if stock_data.annualized_other_ratio_bonus                          is None: stock_data.annualized_other_ratio_bonus                          = 0.0
    if stock_data.quarterized_other_ratio                               is None: stock_data.quarterized_other_ratio                               = 0
    if stock_data.quarterized_other_ratio_bonus                         is None: stock_data.quarterized_other_ratio_bonus                         = 0.0
    if stock_data.annualized_total_current_ratio                        is None: stock_data.annualized_total_current_ratio                        = 0
    if stock_data.annualized_total_current_ratio_bonus                  is None: stock_data.annualized_total_current_ratio_bonus                  = 0.0
    if stock_data.quarterized_total_current_ratio                       is None: stock_data.quarterized_total_current_ratio                       = 0
    if stock_data.quarterized_total_current_ratio_bonus                 is None: stock_data.quarterized_total_current_ratio_bonus                 = 0.0
    if stock_data.total_ratio_effective                                 is None: stock_data.total_ratio_effective                                 = 0
    if stock_data.other_current_ratio_effective                         is None: stock_data.other_current_ratio_effective                         = 0
    if stock_data.other_ratio_effective                                 is None: stock_data.other_ratio_effective                                 = 0
    if stock_data.total_current_ratio_effective                         is None: stock_data.total_current_ratio_effective                         = 0
    if stock_data.effective_current_ratio                               is None: stock_data.effective_current_ratio                               = 0
    if stock_data.annualized_total_assets                               is None: stock_data.annualized_total_assets                               = 0
    if stock_data.annualized_total_assets_bonus                         is None: stock_data.annualized_total_assets_bonus                         = 0.0
    if stock_data.quarterized_total_assets                              is None: stock_data.quarterized_total_assets                              = 0
    if stock_data.quarterized_total_assets_bonus                        is None: stock_data.quarterized_total_assets_bonus                        = 0.0
    if stock_data.effective_total_assets                                is None: stock_data.effective_total_assets                                = 0
    if stock_data.annualized_total_stockholder_equity                   is None: stock_data.annualized_total_stockholder_equity                   = 0
    if stock_data.annualized_total_stockholder_equity_bonus             is None: stock_data.annualized_total_stockholder_equity_bonus             = 0.0
    if stock_data.quarterized_total_stockholder_equity                  is None: stock_data.quarterized_total_stockholder_equity                  = 0
    if stock_data.quarterized_total_stockholder_equity_bonus            is None: stock_data.quarterized_total_stockholder_equity_bonus            = 0.0
    if stock_data.effective_total_stockholder_equity                    is None: stock_data.effective_total_stockholder_equity                    = 0
    if stock_data.calculated_roa                                        is None: stock_data.calculated_roa                                        = 0
    if stock_data.calculated_roe                                        is None: stock_data.calculated_roe                                        = 0
    if stock_data.annualized_working_capital                            is None: stock_data.annualized_working_capital                            = 0
    if stock_data.quarterized_working_capital                           is None: stock_data.quarterized_working_capital                           = 0
    if stock_data.effective_working_capital                             is None: stock_data.effective_working_capital                             = 0
    if stock_data.annualized_total_liabilities                          is None: stock_data.annualized_total_liabilities                          = 0
    if stock_data.annualized_total_liabilities_bonus                    is None: stock_data.annualized_total_liabilities_bonus                    = 0.0
    if stock_data.quarterized_total_liabilities                         is None: stock_data.quarterized_total_liabilities                         = 0
    if stock_data.quarterized_total_liabilities_bonus                   is None: stock_data.quarterized_total_liabilities_bonus                   = 0.0
    if stock_data.effective_total_liabilities                           is None: stock_data.effective_total_liabilities                           = 0
    if stock_data.altman_z_score_factor                                 is None: stock_data.altman_z_score_factor                                 = 0


def calculate_weighted_stock_data_on_dict(dict_input, dict_name, str_in_dict, weights, stock_data, reverse_required, force_only_sum=False, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=1.0, bonus_mon_dec=1.0, bonus_neg_pres=1.0):
    if VERBOSE_LOGS > 2: print("[{} calculate_weighted_stock_data_on_dict]".format(__name__), end='')
    weight_index  = 0
    weighted_list = []
    weights_sum   = 0
    all_pos       = True  # Values are all positive
    all_neg       = True  # Values are all negative
    mon_inc       = True  # Values are monotonically increasing
    mon_dec       = True  # Values are monotonically decreasing
    neg_pres      = False # Negative value presence
    bonus         = 1.0
    try:
        if str_in_dict is None:
            for key in (reversed(list(dict_input)) if reverse_required else list(dict_input)):
                current_value = float(dict_input[key])
                weighted_list.append(current_value * weights[weight_index])
                weights_sum  += weights[weight_index]
                weight_index += 1
                if weight_index > 1:
                    all_pos  = True if all_pos and current_value > 0          and prev_value > 0 else False
                    all_neg  = True if all_neg and current_value < 0          and prev_value < 0 else False
                    mon_inc  = True if mon_inc and current_value > prev_value                    else False
                    mon_dec  = True if mon_dec and current_value < prev_value                    else False
                neg_pres     = True if neg_pres or current_value < 0                             else False
                prev_value   = current_value
        else:
            for key in (reversed(list(dict_input)) if reverse_required else list(dict_input)):  # The 1st element will be the oldest, receiving the lowest weight
                if str_in_dict in dict_input[key] and not math.isnan(dict_input[key][str_in_dict]):
                    current_value = dict_input[key][str_in_dict]
                    weighted_list.append(current_value * weights[weight_index])
                    weights_sum  += weights[weight_index]
                    weight_index += 1
                    if weight_index > 1:  # 1st value: save previous
                        all_pos  = True if all_pos and current_value > 0          and prev_value > 0 else False
                        all_neg  = True if all_neg and current_value < 0          and prev_value < 0 else False
                        mon_inc  = True if mon_inc and current_value > prev_value                    else False
                        mon_dec  = True if mon_dec and current_value < prev_value                    else False
                    neg_pres     = True if neg_pres or current_value < 0                             else False
                    prev_value = current_value

        bonus = 1.0
        if weight_index > 1:
            if all_pos:  bonus *= bonus_all_pos
            if all_neg:  bonus *= bonus_all_neg
            if mon_inc:  bonus *= bonus_mon_inc
            if mon_dec:  bonus *= bonus_mon_dec
            if neg_pres: bonus *= bonus_neg_pres
        if weights_sum > 0:
            return_value = stock_data.financial_currency_conversion_rate_mult_to_usd * sum(weighted_list) / (1.0 if force_only_sum else float(weights_sum))  # Multiplying by the factor to get the valu in USD.
            if return_value  > 0: return_value *= bonus
            elif      bonus != 0: return_value /= float(bonus)
        else:
            return_value = None
    except Exception as e:
        print("Exception in {} {}: {} -> {}".format(stock_data.symbol, dict_name, e, traceback.format_exc()))
        return_value = None
        pass

    return [return_value, bonus]


def calculate_weighted_ratio_from_dict(dict_input, dict_name, str_in_dict_numerator, str_in_dict_denominator, weights, stock_data, default_return_value, reverse_required, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=1.0, bonus_mon_dec=1.0, bonus_neg_pres=1.0, bonus_mon_inc_num=1.0, bonus_mon_inc_den=1.0, bonus_mon_dec_num=1.0, bonus_mon_dec_den=1.0):
    if VERBOSE_LOGS > 2: print("[{} calculate_weighted_ratio_from_dict]".format(__name__), end='')
    return_value         = default_return_value
    weighted_ratios_list = []
    all_pos       = True  # Values are all positive
    all_neg       = True  # Values are all negative
    mon_inc       = True  # Values are monotonically increasing
    mon_dec       = True  # Values are monotonically decreasing
    mon_inc_num   = True  # Numerator   Values are monotonically increasing
    mon_inc_den   = True  # Numerator   Values are monotonically decreasing
    mon_dec_num   = True  # Denominator Values are monotonically increasing
    mon_dec_den   = True  # Denominator Values are monotonically decreasing
    neg_pres      = False # Negative value presence
    bonus         = 1.0
    try:
        for key in (reversed(list(dict_input)) if reverse_required else list(dict_input)):  # The 1st element will be the oldest, receiving the lowest weight
            if str_in_dict_denominator in dict_input[key] and not math.isnan(dict_input[key][str_in_dict_denominator]) and str_in_dict_numerator in dict_input[key] and not math.isnan(dict_input[key][str_in_dict_numerator]) and dict_input[key][str_in_dict_denominator] != 0:
                current_numerator    = float(dict_input[key][str_in_dict_numerator])
                current_denominator  = float(dict_input[key][str_in_dict_denominator])
                current_ratio        = (current_numerator / current_denominator)
                weighted_ratios_list.append(current_ratio)
                if len(weighted_ratios_list) > 1:  # 1st value: just save previous
                    all_pos          = True if all_pos     and current_ratio       > 0 and prev_ratio > 0 else False
                    all_neg          = True if all_neg     and current_ratio       < 0 and prev_ratio < 0 else False
                    mon_inc          = True if mon_inc     and current_ratio       > prev_ratio           else False
                    mon_dec          = True if mon_dec     and current_ratio       < prev_ratio           else False
                    mon_inc_num      = True if mon_inc_num and current_numerator   > prev_numerator       else False
                    mon_dec_num      = True if mon_dec_num and current_numerator   < prev_numerator       else False
                    mon_inc_den      = True if mon_inc_den and current_denominator > prev_denominator     else False
                    mon_dec_den      = True if mon_dec_den and current_denominator < prev_denominator     else False
                neg_pres             = True if neg_pres     or current_ratio       < 0                    else False
                prev_ratio           = current_ratio
                prev_numerator       = current_numerator
                prev_denominator     = current_denominator

    except Exception as e:
        print("Exception in {} {}: {} -> {}".format(stock_data.symbol, dict_name, e, traceback.format_exc()))
        pass
    if len(weighted_ratios_list):
        return_value = weighted_average(weighted_ratios_list, weights[:len(weighted_ratios_list)])
        if len(weighted_ratios_list) > 1:
            bonus = 1.0
            if all_pos:     bonus *= bonus_all_pos
            if all_neg:     bonus *= bonus_all_neg
            if mon_inc:     bonus *= bonus_mon_inc
            if mon_dec:     bonus *= bonus_mon_dec
            if neg_pres:    bonus *= bonus_neg_pres
            if mon_inc_num: bonus *= bonus_mon_inc_num
            if mon_inc_den: bonus *= bonus_mon_inc_den
            if mon_dec_num: bonus *= bonus_mon_dec_num
            if mon_dec_den: bonus *= bonus_mon_dec_den
            if return_value > 0: return_value *= bonus
            else               : return_value /= float(bonus)

    return [return_value, bonus]


def calculate_weighted_diff_from_dict(dict_input, dict_name, str_in_dict_left_term, str_in_dict_right_term, weights, stock_data, default_return_value, reverse_required, force_only_sum=False):
    if VERBOSE_LOGS > 2: print("[{} calculate_weighted_diff_from_dict]".format(__name__), end='')
    return_value         = default_return_value
    weighted_diffs_list = []
    try:
        for key in (reversed(list(dict_input)) if reverse_required else list(dict_input)):  # The 1st element will be the oldest, receiving the lowest weight
            if str_in_dict_right_term in dict_input[key] and not math.isnan(dict_input[key][str_in_dict_right_term]) and str_in_dict_left_term in dict_input[key] and not math.isnan(dict_input[key][str_in_dict_left_term]):
                weighted_diffs_list.append((dict_input[key][str_in_dict_left_term] - dict_input[key][str_in_dict_right_term]))
    except Exception as e:
        print("Exception in {} {}: {} -> {}".format(stock_data.symbol, dict_name, e, traceback.format_exc()))
        pass
    if len(weighted_diffs_list): return_value = sum(weighted_diffs_list) if force_only_sum else weighted_average(weighted_diffs_list, weights[:len(weighted_diffs_list)])

    return return_value


def calculate_weighted_sum_from_2_dicts(dict1_input, dict1_name, str_in_dict1, dict2_input, dict2_name, str_in_dict2, weights, stock_data, default_return_value, reverse_required1, reverse_required2, force_only_sum=False):
    if VERBOSE_LOGS > 2: print("[{} calculate_weighted_sum_from_2_dicts]".format(__name__), end='')
    return_value       = default_return_value
    weighted_sums_list = []
    try:
        for key in (reversed(list(dict1_input)) if reverse_required1 else list(dict1_input)):  # The 1st element will be the oldest, receiving the lowest weight
            if str_in_dict1 in dict1_input[key] and not math.isnan(dict1_input[key][str_in_dict1]) and str_in_dict2 in dict2_input[key] and not math.isnan(dict2_input[key][str_in_dict2]):
                weighted_sums_list.append((dict1_input[key][str_in_dict1] + dict2_input[key][str_in_dict2]))
    except Exception as e:
        print("Exception in {} {} {}: {} -> ".format(stock_data.symbol, dict1_name, dict2_name, e, traceback.format_exc()))
        pass
    if len(weighted_sums_list): return_value = sum(weighted_sums_list) if force_only_sum else weighted_average(weighted_sums_list, weights[:len(weighted_sums_list)])

    return return_value


def calculate_current_vs_previous_change_ratio(current_value, previous_value):
    if VERBOSE_LOGS > 2: print("[{} calculate_current_vs_previous_change_ratio]".format(__name__), end='')
    if   current_value >  0 and previous_value >  0: value_to_return = float(current_value) / float(previous_value) - 1.0  #  100/ 1000 - 1 = -0.9;  1000/ 100 - 1 = 9
    elif current_value == 0 and previous_value >  0: value_to_return = float(current_value) / float(previous_value) - 1.0  #  100/ 1000 - 1 = -0.9;  1000/ 100 - 1 = 9
    elif current_value >  0 and previous_value == 0: value_to_return =  1.0  #  100% Growth (from     0        to     positive)

    elif current_value <  0 and previous_value <  0: value_to_return = float(previous_value) / float(current_value) - 1.0  # -100/-1000 - 1 = -0.9; -1000/-100 - 1 = 9
    elif current_value == 0 and previous_value <  0: value_to_return =  1.0  #  100% Growth (from     negative to            0)
    elif current_value <  0 and previous_value == 0: value_to_return = -1.0  # -100% Growth (from     0        to     negative)

    elif current_value >  0 and previous_value <  0: value_to_return =  1.0  #  100% Growth (from     negative to     positive)
   #elif current_value == 0 and previous_value <  0: value_to_return =  1  #  Already handled above
   #elif current_value >  0 and previous_value == 0: value_to_return =  1  #  Already handled above

    elif current_value <  0 and previous_value >  0: value_to_return = -1.0  # -100% Growth (from     positive to     negative)
   #elif current_value == 0 and previous_value >  0: value_to_return = -1  #  Already handled above
   #elif current_value <  0 and previous_value == 0: value_to_return = -1  #  Already handled above
    else: # current_value == 0 and previous_value == 0:
        value_to_return = 0.0  # No change

    return float(value_to_return)


# Altman Z Score: The formula for Altman Z-Score is:
# Formula: 2 calculation methods: Simple is effective_<parameter1> / effective_<parameter2>. Complex (but better) is effective(parameter1/parameter2) and best (most complex) is effective((parameter1-parameter2)/(parameter3-parameter4))
#                 1.2*(working capital                       / total assets     ) +
#                 1.4*(retained earnings                     / total assets     ) +
#                 3.3*(earnings before interest and tax      / total assets     ) +
#                 0.6*(market value of equity [==market_cap] / total liabilities) +
#                 1.0*(sales                                 / total assets     )
# Instructions:
# How Should an Investor Interpret Altman Z-Score?
# - Investors can use Altman Z-score Plus to evaluate corporate credit risk. A score below 1.8 means it's likely the company is headed for bankruptcy, while companies with scores above 3 are not likely to go bankrupt. Investors may consider purchasing a stock if its Altman Z-Score value is closer to 3 and selling, or shorting, a stock if the value is closer to 1.8.
# Beneish M Score
def calculate_altman_z_score_factor(stock_data):
    stock_data.altman_z_score_factor = 0.0

    # TODO: ASAFR: Each of the elements can (and should) most probably be calculated by quarterized and annualized (and then effective) ratio prior
    if stock_data.effective_total_assets != None and stock_data.effective_total_assets != 0:
        stock_data.altman_z_score_factor += 1.2 * ((float(stock_data.effective_working_capital  ) if stock_data.effective_working_capital   != None else 0.0)/ float(stock_data.effective_total_assets))
        stock_data.altman_z_score_factor += 1.4 * ((float(stock_data.effective_retained_earnings) if stock_data.effective_retained_earnings != None else 0.0)/ float(stock_data.effective_total_assets))
        stock_data.altman_z_score_factor += 3.3 * ((float(stock_data.ebitda                     ) if stock_data.ebitda                      != None else 0.0)/ float(stock_data.effective_total_assets))
        stock_data.altman_z_score_factor += 1.0 * ((float(stock_data.effective_revenue          ) if stock_data.effective_revenue           != None else 0.0)/ float(stock_data.effective_total_assets))
    if stock_data.effective_total_liabilities != None and stock_data.effective_total_liabilities != 0:
        stock_data.altman_z_score_factor += 0.6 * ((float(stock_data.market_cap                 ) if stock_data.market_cap                  != None else 0.0)/ float(stock_data.effective_total_liabilities))

    # https://www.accountingtools.com/articles/the-altman-z-score-formula.html
    if    3.0 <= stock_data.altman_z_score_factor:         stock_data.altman_z_score_factor **= 0.5  # f(        x >= 3   ) = 1.71+...square root     growth
    elif 1.81 <= stock_data.altman_z_score_factor <  3.0:  stock_data.altman_z_score_factor  /= 2.0  # f(1.81 <= x <  3   ) = 1.5 -...         linear decay
    elif    0 <  stock_data.altman_z_score_factor <  1.81: stock_data.altman_z_score_factor  /= 4.0  # f(   0 <  x <  1.81) = 0.45-...stronger linear decay
    elif         stock_data.altman_z_score_factor <= 0:    stock_data.altman_z_score_factor   = NEGATIVE_ALTMAN_Z_FACTOR    # a very low value -> Much less attractive


def print_sss_value_results(stock_data):
    print('{:20}, ({:10}, {:10}), sss_value: {:.3e}, evr_effective: {:.3e}, trailing_12months_price_to_sales: {:.3e}, pe_effective: {:.3e}, effective_ev_to_ebitda: {:.3e}, effective_profit_margin: {:.3e}, held_percent_insiders: {:.3e}, price_to_book: {:.3e}, enterprise_value: {:.3e}, market_cap: {:.3e}, eqg_factor_effective: {:.3e}, rqg_factor_effective: {:.3e}, effective_peg_ratio: {:.3e}, ev_to_cfo_ratio_effective: {:.3e}, debt_to_equity_effective_used: {:.3e}, financial_currency: {:4}, summary_currency: {:4}, financial_currency_conversion_rate_mult_to_usd: {:.3e}, summary_currency_conversion_rate_mult_to_usd: {:.3e}, skip_reason: {}'.format(
           stock_data.short_name[0:19],
                  stock_data.sector[0:9],
                          stock_data.country[0:9],
                                  stock_data.sss_value, stock_data.evr_effective, stock_data.trailing_12months_price_to_sales,
                                                                                                                      stock_data.pe_effective,
                                                                                                                                            stock_data.effective_ev_to_ebitda, stock_data.effective_profit_margin, stock_data.held_percent_insiders,
                                                                                                                                                                                                                                            stock_data.price_to_book, stock_data.enterprise_value,
                                                                                                                                                                                                                                                                                             stock_data.market_cap, stock_data.eqg_factor_effective, stock_data.rqg_factor_effective,
                                                                                                                                                                                                                                                                                                                                                                             stock_data.effective_peg_ratio, stock_data.ev_to_cfo_ratio_effective, stock_data.debt_to_equity_effective_used,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    stock_data.financial_currency, stock_data.summary_currency,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     stock_data.financial_currency_conversion_rate_mult_to_usd,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             stock_data.summary_currency_conversion_rate_mult_to_usd, stock_data.skip_reason))

def stringify_keys(d, check_inner):
    """Convert a dict's keys to strings if they are not."""
    converted_dict = {}
    for key in d.keys():
        # check inner dict if required:
        if check_inner and isinstance(d[key], dict):
            value = stringify_keys(d[key], check_inner)
        else:
            value = d[key]

        # convert nonstring to string if needed:
        if not isinstance(key, str):
            key_str = '{}'.format(key)
            converted_dict[key_str] = value
        else:
            converted_dict[key]     = value

    return converted_dict


def process_info(json_db, symbol, stock_data, tase_mode, sectors_list, sectors_filter_out, countries_list, countries_filter_out, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, pb_limit, pi_limit, enterprise_value_millions_usd_limit, research_mode_max_ev, eqg_min, rqg_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, reference_db_title_row, db_filename):
    return_value = True
    if research_mode:
        if   stock_data.previous_close < 1.0:                                                                                                                         return_value = False  # Avoid Penny Stocks
        elif (not research_mode_max_ev and stock_data.enterprise_value < enterprise_value_millions_usd_limit * 1000000) or \
             (    research_mode_max_ev and stock_data.enterprise_value > enterprise_value_millions_usd_limit * 1000000):                                              return_value = False
        elif stock_data.price_to_book                    > pb_limit:                                                                                                  return_value = False
        elif stock_data.held_percent_insiders            < pi_limit:                                                                                                  return_value = False
        elif stock_data.evr_effective                    <= 0                     or stock_data.evr_effective             > enterprise_value_to_revenue_limit:        return_value = False
        elif stock_data.effective_ev_to_ebitda           <= 0:                                                                                                        return_value = False
        elif stock_data.effective_price_to_earnings      <= 0:                                                                                                        return_value = False
        elif stock_data.trailing_12months_price_to_sales <= 0:                                                                                                        return_value = False
        elif stock_data.price_to_book                    <= 0:                                                                                                        return_value = False
        elif stock_data.pe_effective                     <= 0                     or stock_data.pe_effective              >  price_to_earnings_limit:                 return_value = False
        elif stock_data.effective_profit_margin          <  profit_margin_limit:                                                                                      return_value = False
        elif stock_data.ev_to_cfo_ratio_effective        >  ev_to_cfo_ratio_limit or stock_data.ev_to_cfo_ratio_effective <= 0:                                       return_value = False
        elif stock_data.debt_to_equity_effective         >  debt_to_equity_limit  or stock_data.debt_to_equity_effective  <= 0:                                       return_value = False
        elif stock_data.eqg_factor_effective             <  eqg_min:                                                                                                  return_value = False
        elif stock_data.rqg_factor_effective             <  rqg_min:                                                                                                  return_value = False

        return return_value

    try:
        info                     = {}
        earnings_quarterly       = {}
        earnings_yearly          = {}
        balance_sheets_yearly    = {}
        balance_sheets_quarterly = {}
        cash_flows_yearly        = {}
        cash_flows_quarterly     = {}
        financials_yearly        = {}
        financials_quarterly     = {}
        # TODO: ASAFR: Here: id no previous_close, use market_high, low regular, or anything possible to avoid none!
        try:
            if isinstance(symbol, dict):
                info                     = symbol['info'                    ] if 'info'                     in symbol else None
                cash_flows_yearly        = symbol['cash_flows_yearly'       ] if 'cash_flows_yearly'        in symbol else None
                cash_flows_quarterly     = symbol['cash_flows_quarterly'    ] if 'cash_flows_quarterly'     in symbol else None
                balance_sheets_yearly    = symbol['balance_sheets_yearly'   ] if 'balance_sheets_yearly'    in symbol else None
                balance_sheets_quarterly = symbol['balance_sheets_quarterly'] if 'balance_sheets_quarterly' in symbol else None
                earnings_yearly          = symbol['earnings_yearly'         ] if 'earnings_yearly'          in symbol else None
                earnings_quarterly       = symbol['earnings_quarterly'      ] if 'earnings_quarterly'       in symbol else None
            else:
                info                     = symbol.get_info()
                cash_flows_yearly        = symbol.get_cashflow(     as_dict=True, freq="yearly")
                cash_flows_quarterly     = symbol.get_cashflow(     as_dict=True, freq="quarterly")
                balance_sheets_yearly    = symbol.get_balance_sheet(as_dict=True, freq="yearly")
                balance_sheets_quarterly = symbol.get_balance_sheet(as_dict=True, freq="quarterly")
                earnings_yearly          = symbol.get_earnings(     as_dict=True, freq="yearly")
                earnings_quarterly       = symbol.get_earnings(     as_dict=True, freq="quarterly")

                cash_flows_yearly        = stringify_keys(d=cash_flows_yearly,        check_inner=False)
                cash_flows_quarterly     = stringify_keys(d=cash_flows_quarterly,     check_inner=False)
                balance_sheets_yearly    = stringify_keys(d=balance_sheets_yearly,    check_inner=False)
                balance_sheets_quarterly = stringify_keys(d=balance_sheets_quarterly, check_inner=False)
                earnings_yearly          = stringify_keys(d=earnings_yearly,          check_inner=False)
                earnings_quarterly       = stringify_keys(d=earnings_quarterly,       check_inner=False)

            if   earnings_yearly    != None: stock_data.financial_currency = earnings_yearly[   'financialCurrency']
            elif earnings_quarterly != None: stock_data.financial_currency = earnings_quarterly['financialCurrency']

            stock_data.summary_currency = info['currency'] if 'currency' in info else stock_data.financial_currency  # Used for market_cap and enterprise_value conversions

            # Currency Conversion Rules, per yfinance Data Display Methods:
            #
            # +--------------------+-------------------+-------------------+
            # |       Mode         | earnings_ Exist   | earnings_ Missing |
            # +====================+===================+===================+
            # | All/Custom/Nsr     |                   |                   |
            # +--------------------| financialCurrency | info.currency     |
            # | TASE (<symbol>.TA) |                   |                   |
            # +--------------------+-------------------+-------------------+

            if stock_data.summary_currency == 'ILA':  # Sometimes (in TASE mode) in info['currency'] ILA may show instead of ILS so just substitute
                stock_data.summary_currency = 'ILS'
            if currency_conversion_tool:
                stock_data.financial_currency_conversion_rate_mult_to_usd = round(1.0/float(currency_conversion_tool[stock_data.financial_currency]), NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
                stock_data.summary_currency_conversion_rate_mult_to_usd   = round(1.0/float(currency_conversion_tool[stock_data.summary_currency  ]), NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
            elif currency_conversion_tool_alternative:
                try:
                    stock_data.financial_currency_conversion_rate_mult_to_usd = round(float(currency_conversion_tool_alternative.convert(1.0, stock_data.financial_currency, 'USD')), NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
                    stock_data.summary_currency_conversion_rate_mult_to_usd   = round(float(currency_conversion_tool_alternative.convert(1.0, stock_data.summary_currency,   'USD')), NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
                except Exception as e:
                    stock_data.financial_currency_conversion_rate_mult_to_usd = round(1.0 / float(currency_conversion_tool_manual[stock_data.financial_currency]), NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
                    stock_data.summary_currency_conversion_rate_mult_to_usd   = round(1.0 / float(currency_conversion_tool_manual[stock_data.summary_currency  ]), NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
                    print("Exception {} -> {}".format(e, traceback.format_exc()))
            else:
                stock_data.financial_currency_conversion_rate_mult_to_usd = round(1.0 / float(currency_conversion_tool_manual[stock_data.financial_currency]), NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3
                stock_data.summary_currency_conversion_rate_mult_to_usd   = round(1.0 / float(currency_conversion_tool_manual[stock_data.summary_currency  ]), NUM_ROUND_DECIMALS)  # conversion_rate is the value to multiply the foreign exchange (in which the stock's currency is) by to get the original value in USD. For instance if the currency is ILS, values should be divided by ~3.3

            if isinstance(symbol, dict):
                financials_yearly    = symbol['financials_yearly'   ] if 'financials_yearly'    in symbol else None
                financials_quarterly = symbol['financials_quarterly'] if 'financials_quarterly' in symbol else None
            else:
                financials_yearly    = symbol.get_financials(as_dict=True, freq="yearly")
                financials_quarterly = symbol.get_financials(as_dict=True, freq="quarterly")
                financials_yearly    = stringify_keys(d=financials_yearly,    check_inner=False)
                financials_quarterly = stringify_keys(d=financials_quarterly, check_inner=False)


            if VERBOSE_LOGS:
                print('[DB Debug] Symbol:                   {}'.format(stock_data.symbol))
                print('[DB Debug] info:                     {}'.format(info))
                print('[DB Debug] cash_flows_yearly:        {}'.format(cash_flows_yearly))
                print('[DB Debug] cash_flows_quarterly:     {}'.format(cash_flows_quarterly))
                print('[DB Debug] balance_sheets_yearly:    {}'.format(balance_sheets_yearly))
                print('[DB Debug] balance_sheets_quarterly: {}'.format(balance_sheets_quarterly))
                print('[DB Debug] earnings_yearly:          {}'.format(earnings_yearly))
                print('[DB Debug] earnings_quarterly:       {}'.format(earnings_quarterly))
                print('[DB Debug] financials_yearly:        {}'.format(financials_yearly))
                print('[DB Debug] financials_quarterly:     {}'.format(financials_quarterly))

            # Save raw json db:
            json_db[stock_data.symbol] = {}
            json_db[stock_data.symbol]["info"]                     = info
            json_db[stock_data.symbol]["cash_flows_yearly"]        = cash_flows_yearly
            json_db[stock_data.symbol]["cash_flows_quarterly"]     = cash_flows_quarterly
            json_db[stock_data.symbol]["balance_sheets_yearly"]    = balance_sheets_yearly
            json_db[stock_data.symbol]["balance_sheets_quarterly"] = balance_sheets_quarterly
            json_db[stock_data.symbol]["earnings_yearly"]          = earnings_yearly
            json_db[stock_data.symbol]["earnings_quarterly"]       = earnings_quarterly
            json_db[stock_data.symbol]["financials_yearly"]        = financials_yearly
            json_db[stock_data.symbol]["financials_quarterly"]     = financials_quarterly

            # institutional_holders                = symbol.get_institutional_holders(as_dict=True)
            # sustainability                       = symbol.get_sustainability(as_dict=True)
            # major_holders                        = symbol.get_major_holders(as_dict=True)
            # mutualfund_holders                   = symbol.get_mutualfund_holders(as_dict=True)
        except Exception as e:
            if not research_mode: print("              Exception in {} symbol.get_info(): {} -> {}".format(stock_data.symbol, e, traceback.format_exc()))
            pass

        if 'shortName' in info: stock_data.short_name = info['shortName']
        else:                   stock_data.short_name = 'None'

        # Balance sheets are listed from newest to oldest, so for the weights, must reverse the dictionary:
        [stock_data.annualized_total_ratio,          stock_data.annualized_total_ratio_bonus         ] = calculate_weighted_ratio_from_dict(balance_sheets_yearly,    'annualized_total_ratio',          'Total Assets',         'Total Liab',                BALANCE_SHEETS_WEIGHTS, stock_data, 0, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=3.0, bonus_mon_dec=1.0/3.0, bonus_neg_pres=1.0, bonus_mon_inc_num=2.0, bonus_mon_inc_den=0.5, bonus_mon_dec_num=0.5, bonus_mon_dec_den=2.0)
        [stock_data.annualized_other_current_ratio,  stock_data.annualized_other_current_ratio_bonus ] = calculate_weighted_ratio_from_dict(balance_sheets_yearly,    'annualized_other_current_ratio',  'Other Current Assets', 'Other Current Liab',        BALANCE_SHEETS_WEIGHTS, stock_data, 0, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=3.0, bonus_mon_dec=1.0/3.0, bonus_neg_pres=1.0, bonus_mon_inc_num=2.0, bonus_mon_inc_den=0.5, bonus_mon_dec_num=0.5, bonus_mon_dec_den=2.0)
        [stock_data.annualized_other_ratio,          stock_data.annualized_other_ratio_bonus         ] = calculate_weighted_ratio_from_dict(balance_sheets_yearly,    'annualized_other_ratio',          'Other Assets',         'Other Liab',                BALANCE_SHEETS_WEIGHTS, stock_data, 0, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=3.0, bonus_mon_dec=1.0/3.0, bonus_neg_pres=1.0, bonus_mon_inc_num=2.0, bonus_mon_inc_den=0.5, bonus_mon_dec_num=0.5, bonus_mon_dec_den=2.0)
        [stock_data.annualized_total_current_ratio,  stock_data.annualized_total_current_ratio_bonus ] = calculate_weighted_ratio_from_dict(balance_sheets_yearly,    'annualized_total_current_ratio',  'Total Current Assets', 'Total Current Liabilities', BALANCE_SHEETS_WEIGHTS, stock_data, 0, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=3.0, bonus_mon_dec=1.0/3.0, bonus_neg_pres=1.0, bonus_mon_inc_num=2.0, bonus_mon_inc_den=0.5, bonus_mon_dec_num=0.5, bonus_mon_dec_den=2.0)

        [stock_data.quarterized_total_ratio,         stock_data.quarterized_total_ratio_bonus        ] = calculate_weighted_ratio_from_dict(balance_sheets_quarterly, 'quarterized_total_ratio',         'Total Assets',         'Total Liab',                BALANCE_SHEETS_WEIGHTS, stock_data, 0, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,     bonus_neg_pres=1.0, bonus_mon_inc_num=2.0, bonus_mon_inc_den=0.5, bonus_mon_dec_num=0.5, bonus_mon_dec_den=2.0)
        [stock_data.quarterized_other_current_ratio, stock_data.quarterized_other_current_ratio_bonus] = calculate_weighted_ratio_from_dict(balance_sheets_quarterly, 'quarterized_other_current_ratio', 'Other Current Assets', 'Other Current Liab',        BALANCE_SHEETS_WEIGHTS, stock_data, 0, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,     bonus_neg_pres=1.0, bonus_mon_inc_num=2.0, bonus_mon_inc_den=0.5, bonus_mon_dec_num=0.5, bonus_mon_dec_den=2.0)
        [stock_data.quarterized_other_ratio,         stock_data.quarterized_other_ratio_bonus        ] = calculate_weighted_ratio_from_dict(balance_sheets_quarterly, 'quarterized_other_ratio',         'Other Assets',         'Other Liab',                BALANCE_SHEETS_WEIGHTS, stock_data, 0, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,     bonus_neg_pres=1.0, bonus_mon_inc_num=2.0, bonus_mon_inc_den=0.5, bonus_mon_dec_num=0.5, bonus_mon_dec_den=2.0)
        [stock_data.quarterized_total_current_ratio, stock_data.quarterized_total_current_ratio_bonus] = calculate_weighted_ratio_from_dict(balance_sheets_quarterly, 'quarterized_total_current_ratio', 'Total Current Assets', 'Total Current Liabilities', BALANCE_SHEETS_WEIGHTS, stock_data, 0, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,     bonus_neg_pres=1.0, bonus_mon_inc_num=2.0, bonus_mon_inc_den=0.5, bonus_mon_dec_num=0.5, bonus_mon_dec_den=2.0)

        stock_data.annualized_working_capital      = calculate_weighted_diff_from_dict( balance_sheets_yearly,    'annualized_working_capital',      'Total Current Assets', 'Total Current Liabilities', BALANCE_SHEETS_WEIGHTS, stock_data, 0, True)
        stock_data.quarterized_working_capital     = calculate_weighted_diff_from_dict( balance_sheets_quarterly, 'quarterized_working_capital',     'Total Current Assets', 'Total Current Liabilities', BALANCE_SHEETS_WEIGHTS, stock_data, 0, True)

        [stock_data.annualized_total_liabilities,  stock_data.annualized_total_liabilities_bonus ]  = calculate_weighted_stock_data_on_dict(balance_sheets_yearly,    'annualized_total_liabilities',  'Total Liab', BALANCE_SHEETS_WEIGHTS, stock_data, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,     bonus_neg_pres=1.0)
        [stock_data.quarterized_total_liabilities, stock_data.quarterized_total_liabilities_bonus]  = calculate_weighted_stock_data_on_dict(balance_sheets_quarterly, 'quarterized_total_liabilities', 'Total Liab', BALANCE_SHEETS_WEIGHTS, stock_data, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=1.5, bonus_mon_dec=1.0/1.5, bonus_neg_pres=1.0)

        if stock_data.annualized_total_ratio          == 0.0: stock_data.annualized_total_ratio          = stock_data.quarterized_total_ratio        *QUARTERLY_YEARLY_MISSING_FACTOR
        if stock_data.quarterized_total_ratio         == 0.0: stock_data.quarterized_total_ratio         = stock_data.annualized_total_ratio         *QUARTERLY_YEARLY_MISSING_FACTOR
        if stock_data.annualized_other_current_ratio  == 0.0: stock_data.annualized_other_current_ratio  = stock_data.quarterized_other_current_ratio*QUARTERLY_YEARLY_MISSING_FACTOR
        if stock_data.quarterized_other_current_ratio == 0.0: stock_data.quarterized_other_current_ratio = stock_data.annualized_other_current_ratio *QUARTERLY_YEARLY_MISSING_FACTOR
        if stock_data.annualized_other_ratio          == 0.0: stock_data.annualized_other_ratio          = stock_data.quarterized_other_ratio        *QUARTERLY_YEARLY_MISSING_FACTOR
        if stock_data.quarterized_other_ratio         == 0.0: stock_data.quarterized_other_ratio         = stock_data.annualized_other_ratio         *QUARTERLY_YEARLY_MISSING_FACTOR
        if stock_data.annualized_total_current_ratio  == 0.0: stock_data.annualized_total_current_ratio  = stock_data.quarterized_total_current_ratio*QUARTERLY_YEARLY_MISSING_FACTOR
        if stock_data.quarterized_total_current_ratio == 0.0: stock_data.quarterized_total_current_ratio = stock_data.annualized_total_current_ratio *QUARTERLY_YEARLY_MISSING_FACTOR

        if stock_data.annualized_working_capital      == 0.0: stock_data.annualized_working_capital  = stock_data.quarterized_working_capital*QUARTERLY_YEARLY_MISSING_FACTOR
        if stock_data.quarterized_working_capital     == 0.0: stock_data.quarterized_working_capital = stock_data.annualized_working_capital *QUARTERLY_YEARLY_MISSING_FACTOR

        if stock_data.annualized_total_liabilities    is None and stock_data.quarterized_total_liabilities != None: stock_data.annualized_total_liabilities  = stock_data.quarterized_total_liabilities*QUARTERLY_YEARLY_MISSING_FACTOR
        if stock_data.quarterized_total_liabilities   is None and stock_data.annualized_total_liabilities  != None: stock_data.quarterized_total_liabilities = stock_data.annualized_total_liabilities *QUARTERLY_YEARLY_MISSING_FACTOR

        if VERBOSE_LOGS > 2: print("[{} {}]".format(__name__, 3))

        # The correct methos is the TTM only: avoid (quareterly+annual)/2 - Keep it Simple -> Apply to all calculations
        # TODO: ASAFR: In the next stage - add the other current and other ratio to a sum of the ratios Investigate prior
        stock_data.total_ratio_effective         = RATIO_DAMPER+(stock_data.quarterized_total_ratio        ) # Prefer TTM only
        stock_data.other_current_ratio_effective = RATIO_DAMPER+(stock_data.quarterized_other_current_ratio) # Prefer TTM only
        stock_data.other_ratio_effective         = RATIO_DAMPER+(stock_data.quarterized_other_ratio        ) # Prefer TTM only
        stock_data.total_current_ratio_effective = RATIO_DAMPER+(stock_data.quarterized_total_current_ratio) # Prefer TTM only
        stock_data.effective_current_ratio       = (stock_data.total_ratio_effective + stock_data.total_current_ratio_effective) / 2.0  # TODO: ASAFR: In the next stage - add the other and current other ratios - more information -> more completeness

        stock_data.effective_working_capital     = (stock_data.quarterized_working_capital) # Prefer TTM only

        if stock_data.quarterized_total_liabilities != None:
            stock_data.effective_total_liabilities = (stock_data.quarterized_total_liabilities) # Prefer TTM only

        # TODO: ASAFR: Add Other Current Liab / Other Stockholder Equity
        # Balance Sheets are listed from newest to olders, so for proper weight: Reverse required
        [stock_data.annualized_debt_to_equity,  stock_data.annualized_debt_to_equity_bonus ] = calculate_weighted_ratio_from_dict(balance_sheets_yearly,    'annualized_debt_to_equity',  'Total Liab', 'Total Stockholder Equity', BALANCE_SHEETS_WEIGHTS, stock_data, None, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5, bonus_neg_pres=1.0, bonus_mon_inc_num=0.5, bonus_mon_inc_den=2.0, bonus_mon_dec_num=2.0, bonus_mon_dec_den=0.5)
        [stock_data.quarterized_debt_to_equity, stock_data.quarterized_debt_to_equity_bonus] = calculate_weighted_ratio_from_dict(balance_sheets_quarterly, 'quarterized_debt_to_equity', 'Total Liab', 'Total Stockholder Equity', BALANCE_SHEETS_WEIGHTS, stock_data, None, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5, bonus_neg_pres=1.0, bonus_mon_inc_num=0.5, bonus_mon_inc_den=2.0, bonus_mon_dec_num=2.0, bonus_mon_dec_den=0.5)

        if stock_data.annualized_debt_to_equity is None and stock_data.quarterized_debt_to_equity is None:
            stock_data.annualized_debt_to_equity = stock_data.quarterized_debt_to_equity = 1000.0*debt_to_equity_limit
        else:
            if   stock_data.annualized_debt_to_equity is None and stock_data.quarterized_debt_to_equity != None:
                stock_data.annualized_debt_to_equity = stock_data.quarterized_debt_to_equity*QUARTERLY_YEARLY_MISSING_FACTOR
            elif stock_data.annualized_debt_to_equity != None and stock_data.quarterized_debt_to_equity is None:
                stock_data.quarterized_debt_to_equity = stock_data.annualized_debt_to_equity * QUARTERLY_YEARLY_MISSING_FACTOR

            stock_data.debt_to_equity_effective = (stock_data.quarterized_debt_to_equity)  # Prefer TTM only

            if stock_data.debt_to_equity_effective < 0.0:
                stock_data.debt_to_equity_effective_used = (1.0-stock_data.debt_to_equity_effective * NEGATIVE_DEBT_TO_EQUITY_FACTOR)  # (https://www.investopedia.com/terms/d/debtequityratio.asp#:~:text=What%20does%20it%20mean%20for,has%20more%20liabilities%20than%20assets.) What does it mean for debt to equity to be negative? If a company has a negative D/E ratio, this means that the company has negative shareholder equity. In other words, it means that the company has more liabilities than assets
            else:
                stock_data.debt_to_equity_effective_used = DEBT_TO_EQUITY_MIN_BASE + math.sqrt(stock_data.debt_to_equity_effective)

        # Cash Flows are listed from newest to oldest, so reverse required for weights:
        [stock_data.annualized_cash_flow_from_operating_activities,  stock_data.annualized_cash_flow_from_operating_activities_bonus ] = calculate_weighted_stock_data_on_dict(cash_flows_yearly,    'cash_flows_yearly',    'Total Cash From Operating Activities', CASH_FLOW_WEIGHTS, stock_data, True,       bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,   bonus_neg_pres=0.5)
        [stock_data.quarterized_cash_flow_from_operating_activities, stock_data.quarterized_cash_flow_from_operating_activities_bonus] = calculate_weighted_stock_data_on_dict(cash_flows_quarterly, 'cash_flows_quarterly', 'Total Cash From Operating Activities', NO_WEIGHTS,        stock_data, True, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=1.5, bonus_mon_dec=1/1.5, bonus_neg_pres=0.5)

        # Balance Sheets are listed from newest to oldest, so reverse required for weights:
        [stock_data.annualized_total_assets,  stock_data.annualized_total_assets_bonus ]     = calculate_weighted_stock_data_on_dict(balance_sheets_yearly,    'balance_sheets_yearly',    'Total Assets', BALANCE_SHEETS_WEIGHTS, stock_data, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,   bonus_neg_pres=1.0)
        [stock_data.quarterized_total_assets, stock_data.quarterized_total_assets_bonus]     = calculate_weighted_stock_data_on_dict(balance_sheets_quarterly, 'balance_sheets_quarterly', 'Total Assets', BALANCE_SHEETS_WEIGHTS, stock_data, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=1.5, bonus_mon_dec=1/1.5, bonus_neg_pres=1.0)

        # Balance Sheets are listed from newest to oldest, so reverse required for weights:
        [stock_data.annualized_total_stockholder_equity,  stock_data.annualized_total_stockholder_equity_bonus ] = calculate_weighted_stock_data_on_dict(balance_sheets_yearly,    'balance_sheets_yearly',    'Total Stockholder Equity', BALANCE_SHEETS_WEIGHTS, stock_data, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,     bonus_neg_pres=1.0)
        [stock_data.quarterized_total_stockholder_equity, stock_data.quarterized_total_stockholder_equity_bonus] = calculate_weighted_stock_data_on_dict(balance_sheets_quarterly, 'balance_sheets_quarterly', 'Total Stockholder Equity', BALANCE_SHEETS_WEIGHTS, stock_data, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=1.5, bonus_mon_dec=1.0/1.5, bonus_neg_pres=1.0)

        # Balance Sheets are listed from newest to oldest, so reverse required for weights:
        [stock_data.annualized_retained_earnings,  stock_data.annualized_retained_earnings_bonus ] = calculate_weighted_stock_data_on_dict(balance_sheets_yearly,    'balance_sheets_yearly',    'Retained Earnings', BALANCE_SHEETS_WEIGHTS, stock_data, True,       bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,     bonus_neg_pres=0.25)
        [stock_data.quarterized_retained_earnings, stock_data.quarterized_retained_earnings_bonus] = calculate_weighted_stock_data_on_dict(balance_sheets_quarterly, 'balance_sheets_yearly',    'Retained Earnings', NO_WEIGHTS,             stock_data, True, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=1.5, bonus_mon_dec=1.0/1.5, bonus_neg_pres=0.25)

        if stock_data.short_name is     None:                       stock_data.short_name = 'None'
        # if stock_data.short_name != None and not research_mode: print('              {:35}:'.format(stock_data.short_name))

        if 'quoteType' in info: stock_data.quote_type = info['quoteType']
        if not check_quote_type(stock_data, research_mode):     return_value = False

        if 'sector'  in info:    stock_data.sector = info['sector']
        if sectors_filter_out:
            if     check_sector(stock_data, sectors_list):    return_value = False
        else:
            if not check_sector(stock_data, sectors_list):    return_value = False

        if 'country' in info:    stock_data.country = info['country']
        if len(countries_list):
            if countries_filter_out:
                if     check_country(stock_data, countries_list): return_value = False
            else:
                if not check_country(stock_data, countries_list): return_value = False

        if 'fullTimeEmployees' in info:      stock_data.employees = info['fullTimeEmployees']
        else:                                stock_data.employees = NUM_EMPLOYEES_UNKNOWN
        if stock_data.employees is None: stock_data.employees = NUM_EMPLOYEES_UNKNOWN

        # Oldest is the lower index
        alternative_annual_pm_required = True
        if earnings_yearly != None and 'Revenue' in earnings_yearly and 'Earnings' in earnings_yearly:
            len_revenue_list  = len(earnings_yearly['Revenue'])
            len_earnings_list = len(earnings_yearly['Earnings'])
            if len_earnings_list == len_revenue_list:
                weight_index              = 0
                used_weights              = 0
                earnings_to_revenues_list = []
                weights_sum               = 0
                last_ratio                = None
                last_earnings             = None
                last_revenue              = None
                boost_cont_inc_ratio      = True # Will be set to (a Final Value of) True if there is a continuous increase in the profit margin
                boost_cont_ratio_pos      = True # Will be set to (a Final Value of) True if there is a continuous positive in the profit margin
                boost_cont_inc_earnings   = True # Will be set to (a Final Value of) True if there is a continuous increase in the earnings
                boost_cont_inc_revenue    = True # Will be set to (a Final Value of) True if there is a continuous increase in the revenue
                boost_cont_dec_ratio      = True # Will be set to (a Final Value of) True if there is a continuous increase in the profit margin
                boost_cont_dec_earnings   = True # Will be set to (a Final Value of) True if there is a continuous increase in the earnings
                boost_cont_dec_revenue    = True # Will be set to (a Final Value of) True if there is a continuous increase in the revenue
                boost_neg_earnings        = False
                try:
                    for key in earnings_yearly['Revenue']:
                        if float(earnings_yearly['Revenue'][key]) >= 0:
                            earnings = float(          earnings_yearly['Earnings'][key])
                            revenue  = float(max(MIN_REVENUE_FOR_0_REVENUE_DIV_BY_0_AVOIDANCE,earnings_yearly['Revenue' ][key]))
                            earnings_to_revenues_list.append((earnings/revenue)*PROFIT_MARGIN_YEARLY_WEIGHTS[weight_index])
                            weights_sum  += PROFIT_MARGIN_YEARLY_WEIGHTS[weight_index]
                            used_weights += 1
                            current_ratio = earnings/revenue
                            if used_weights > 1:
                                boost_cont_inc_ratio    = True if boost_cont_inc_ratio    and current_ratio > last_ratio                                                               else False
                                boost_cont_inc_earnings = True if boost_cont_inc_earnings and earnings      > last_earnings                                                            else False
                                boost_cont_inc_revenue  = True if boost_cont_inc_revenue  and revenue       > last_revenue                                                             else False
                                boost_cont_dec_ratio    = True if boost_cont_dec_ratio    and current_ratio < last_ratio                                                               else False
                                boost_cont_dec_earnings = True if boost_cont_dec_earnings and earnings      < last_earnings                                                            else False
                                boost_cont_dec_revenue  = True if boost_cont_dec_revenue  and revenue       < last_revenue                                                             else False
                            boost_cont_ratio_pos        = True if boost_cont_ratio_pos    and current_ratio > 0             and revenue > MIN_REVENUE_FOR_0_REVENUE_DIV_BY_0_AVOIDANCE else False
                            boost_neg_earnings          = True if boost_neg_earnings      or  earnings      < 0                                                                        else False
                            last_ratio    = current_ratio
                            last_earnings = earnings
                            last_revenue  = revenue
                        weight_index += 1
                    if weights_sum > 0:
                        stock_data.annualized_profit_margin        = sum(earnings_to_revenues_list)/float(weights_sum)
                        if   stock_data.annualized_profit_margin > 0 and used_weights > 1:
                            stock_data.annualized_profit_margin_boost  = 1.0 if not boost_cont_inc_ratio    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_ratio_pos    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_POSITIVE
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_inc_earnings or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_EARNINGS
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_inc_revenue  or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_REVENUE
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_dec_ratio    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_dec_earnings or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE_IN_EARNINGS
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_dec_revenue  or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE_IN_REVENUE
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_neg_earnings      or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_PRESENCE_OF_ANNUAL_NEGATIVE_EARNINGS
                            stock_data.annualized_profit_margin       *= stock_data.annualized_profit_margin_boost
                        elif stock_data.annualized_profit_margin < 0 and used_weights > 1:
                            stock_data.annualized_profit_margin_boost  = 1.0 if not boost_cont_inc_ratio    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_ratio_pos    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_POSITIVE
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_inc_earnings or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_EARNINGS
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_inc_revenue  or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_INCREASE_IN_REVENUE
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_dec_ratio    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_dec_earnings or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE_IN_EARNINGS
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_cont_dec_revenue  or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_ANNUAL_DECREASE_IN_REVENUE
                            stock_data.annualized_profit_margin_boost *= 1.0 if not boost_neg_earnings      or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_PRESENCE_OF_ANNUAL_NEGATIVE_EARNINGS
                            stock_data.annualized_profit_margin       /= float(stock_data.annualized_profit_margin_boost)
                        alternative_annual_pm_required = False

                except Exception as e:
                    print("Exception in {} annualized_profit_margin: {} -> {}".format(stock_data.symbol, e, traceback.format_exc()))
                    stock_data.annualized_profit_margin = None
                    pass
        # TODO: ASAFR: This below can be duplicated for usage of total_revenue and net_income. Analyze and implement as/if required:
        alternative_quarterly_pm_required = True
        if earnings_quarterly != None and 'Revenue' in earnings_quarterly and 'Earnings' in earnings_quarterly:
            len_revenue_list  = len(earnings_quarterly['Revenue'])
            len_earnings_list = len(earnings_quarterly['Earnings'])
            if len_earnings_list == len_revenue_list:
                weight_index              = 0
                used_weights              = 0
                earnings_to_revenues_list = []
                weights_sum               = 0
                last_ratio                = None
                last_earnings             = None
                last_revenue              = None
                boost_cont_inc_ratio      = True # Will be set to (Final Value of) True if there is a continuous increase in the profit   margin  TODO: ASAFR: Do the same boosting for cash flows ev_to_cfo
                boost_cont_ratio_pos      = True # Will be set to (Final Value of) True if there is a continuous positive in the profit   margin
                boost_cont_inc_earnings   = True # Will be set to (Final Value of) True if there is a continuous increase in the earnings
                boost_cont_inc_revenue    = True # Will be set to (Final Value of) True if there is a continuous increase in the revenue
                boost_cont_dec_ratio      = True # Will be set to (Final Value of) True if there is a continuous increase in the profit   margin  TODO: ASAFR: Do the same boosting for cash flows ev_to_cfo
                boost_cont_dec_earnings   = True # Will be set to (Final Value of) True if there is a continuous increase in the earnings
                boost_cont_dec_revenue    = True # Will be set to (Final Value of) True if there is a continuous increase in the revenue
                boost_neg_earnings        = False
                try:
                    for key in earnings_quarterly['Revenue']:
                        if float(earnings_quarterly['Revenue'][key]) >= 0:
                            earnings = float(          earnings_quarterly['Earnings'][key])
                            revenue  = float(max(MIN_REVENUE_FOR_0_REVENUE_DIV_BY_0_AVOIDANCE,earnings_quarterly['Revenue' ][key]))

                            earnings_to_revenues_list.append((earnings/revenue)*PROFIT_MARGIN_QUARTERLY_WEIGHTS[weight_index])
                            weights_sum  += PROFIT_MARGIN_QUARTERLY_WEIGHTS[weight_index]
                            used_weights += 1
                            current_ratio = earnings/revenue
                            if used_weights > 1:
                                boost_cont_inc_ratio    = True if boost_cont_inc_ratio    and current_ratio > last_ratio                                                               else False
                                boost_cont_inc_earnings = True if boost_cont_inc_earnings and earnings      > last_earnings                                                            else False
                                boost_cont_inc_revenue  = True if boost_cont_inc_revenue  and revenue       > last_revenue                                                             else False
                                boost_cont_dec_ratio    = True if boost_cont_dec_ratio    and current_ratio < last_ratio                                                               else False
                                boost_cont_dec_earnings = True if boost_cont_dec_earnings and earnings      < last_earnings                                                            else False
                                boost_cont_dec_revenue  = True if boost_cont_dec_revenue  and revenue       < last_revenue                                                             else False
                            boost_cont_ratio_pos        = True if boost_cont_ratio_pos    and current_ratio > 0             and revenue > MIN_REVENUE_FOR_0_REVENUE_DIV_BY_0_AVOIDANCE else False
                            boost_neg_earnings          = True if boost_neg_earnings      or  earnings      < 0                                                                        else False
                            last_ratio    = current_ratio
                            last_earnings = earnings
                            last_revenue  = revenue
                        weight_index += 1
                    if weights_sum > 0:
                        alternative_quarterly_pm_required               = False
                        stock_data.quarterized_profit_margin            = sum(earnings_to_revenues_list)/float(weights_sum)
                        if   stock_data.quarterized_profit_margin > 0 and used_weights > 1:  # boosts irrelevant if only 1 weight used
                            stock_data.quarterized_profit_margin_boost  = 1.0 if not boost_cont_inc_ratio    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_ratio_pos    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_POSITIVE
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_inc_earnings or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_EARNINGS
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_inc_revenue  or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_REVENUE
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_dec_ratio    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_dec_earnings or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE_IN_EARNINGS
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_dec_revenue  or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE_IN_REVENUE
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_neg_earnings      or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_PRESENCE_OF_QUARTERLY_NEGATIVE_EARNINGS
                            stock_data.quarterized_profit_margin       *= stock_data.quarterized_profit_margin_boost
                        elif stock_data.quarterized_profit_margin < 0 and used_weights > 1:
                            stock_data.quarterized_profit_margin_boost  = 1.0 if not boost_cont_inc_ratio    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_ratio_pos    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_POSITIVE
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_inc_earnings or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_EARNINGS
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_inc_revenue  or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_INCREASE_IN_REVENUE
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_dec_ratio    or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_dec_earnings or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE_IN_EARNINGS
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_cont_dec_revenue  or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_CONTINUOUS_QUARTERLY_DECREASE_IN_REVENUE
                            stock_data.quarterized_profit_margin_boost *= 1.0 if not boost_neg_earnings      or used_weights <= 1 else PROFIT_MARGIN_BOOST_FOR_PRESENCE_OF_QUARTERLY_NEGATIVE_EARNINGS
                            stock_data.quarterized_profit_margin       /= float(stock_data.quarterized_profit_margin_boost)
                except Exception as e:
                    print("Exception in {} quarterized_profit_margin: {} -> {}".format(stock_data.symbol, e, traceback.format_exc()))
                    stock_data.quarterized_profit_margin = None
                    pass

        # TODO: ASAFR: 1. Apply the bonuses here (configure) and test + verify
        #              2. Add mon_dec and mon_inc bonuses here
        if alternative_quarterly_pm_required:   # TODO: ASAFR: replace the bonuses below with the existing quarterly bonuses CONSTANTS
            [stock_data.quarterized_profit_margin, stock_data.quarterized_profit_margin_boost] = calculate_weighted_ratio_from_dict(financials_quarterly, 'quarterized_profit_margin', 'Net Income', 'Total Revenue', PROFIT_MARGIN_WEIGHTS, stock_data, 0, True, bonus_all_pos=(10.0 if sss_config.custom_sss_value_equation else 1.0), bonus_all_neg=(0.1 if sss_config.custom_sss_value_equation else 1.0), bonus_mon_inc=(10.0 if sss_config.custom_sss_value_equation else 1.0), bonus_mon_dec=(0.1 if sss_config.custom_sss_value_equation else 1.0), bonus_neg_pres=(0.1 if sss_config.custom_sss_value_equation else 1.0), bonus_mon_inc_num=(10.0 if sss_config.custom_sss_value_equation else 4.0), bonus_mon_inc_den=(10.0 if sss_config.custom_sss_value_equation else 4.0), bonus_mon_dec_num=(0.1 if sss_config.custom_sss_value_equation else 0.25), bonus_mon_dec_den=(0.1 if sss_config.custom_sss_value_equation else 0.25))

        # Earnings are ordered from oldest to newest so no reversing required for weights:
        if earnings_yearly != None and 'Revenue' in earnings_yearly: [stock_data.annualized_revenue, stock_data.annualized_revenue_bonus] = calculate_weighted_stock_data_on_dict(earnings_yearly['Revenue'],    'earnings_yearly[Revenue]', None,            REVENUES_WEIGHTS, stock_data, False, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=4.0, bonus_mon_dec=0.25, bonus_neg_pres=1.0)
        else:                                                        stock_data.annualized_revenue = None

        # TODO: ASAFR: Add a calculation of net_income_to_total_revenue_list
        # Financials are ordered newest to oldest so reversing is required for weights:
        [stock_data.annualized_total_revenue, stock_data.annualized_total_revenue_bonus] = calculate_weighted_stock_data_on_dict(financials_yearly,             'financials_yearly',        'Total Revenue', REVENUES_WEIGHTS, stock_data, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=4.0, bonus_mon_dec=0.25, bonus_neg_pres=1.0)

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
                        value_to_append = calculate_current_vs_previous_change_ratio(current_earnings, previous_earnings)
                        qeg_list.append(value_to_append*EARNINGS_WEIGHTS[weight_index-1])
                    else:
                        qeg_list.append(0.0) # No change
                    qeg_weights_sum += EARNINGS_WEIGHTS[weight_index-1]
                previous_earnings = earnings_yearly['Earnings'][key]
                weight_index     += 1

            stock_data.annualized_earnings = stock_data.financial_currency_conversion_rate_mult_to_usd*float(sum(earnings_list)) / float(weights_sum)  # Multiplying by the factor to get the valu in USD.
            if len(qeg_list):
                stock_data.eqg_yoy         = float(sum(qeg_list)) / float(qeg_weights_sum)
            else:
                stock_data.eqg_yoy         = None
        else:
            stock_data.eqg_yoy             = None
            stock_data.annualized_earnings = None

        if earnings_yearly != None and 'Revenue' in earnings_yearly:
            weight_index      = 0
            qrg_list          = []
            qrg_weights_sum   = 0
            previous_revenue = None
            for key in earnings_yearly['Revenue']:
                if weight_index > 0:
                    current_revenue = earnings_yearly['Revenue'][key]
                    if float(previous_revenue) != 0.0 and float(current_revenue) != 0.0: # (this-prev)/(abs(this)+abs(prev))
                        value_to_append = calculate_current_vs_previous_change_ratio(current_revenue, previous_revenue)
                        qrg_list.append(value_to_append*REVENUES_WEIGHTS[weight_index-1])
                    else:
                        qrg_list.append(0.0) # No change
                    qrg_weights_sum += REVENUES_WEIGHTS[weight_index-1]
                previous_revenue = earnings_yearly['Revenue'][key]
                weight_index     += 1
            if len(qrg_list):
                stock_data.rqg_yoy = sum(qrg_list) / float(qrg_weights_sum)
            else:
                stock_data.rqg_yoy = None
        else:
            stock_data.rqg_yoy     = None

        # Net Income Quarterly Growth Year-Over-Year Calculation:
        if financials_yearly != None and len(financials_yearly):
            qnig_weight_index = 0
            qtrg_weight_index = 0
            net_income_list = []
            earnings_to_revenues_list = []
            qnig_list = []
            qtrg_list = [] # Quarterly Total Revenue Growth
            weights_sum = 0
            qnig_weights_sum = 0
            qtrg_weights_sum = 0
            previous_net_income = None
            previous_total_revenue = None
            weight_index = 0
            alternative_pm_weights_sum = 0

            for key in reversed(list(financials_yearly)):  # 1st will be oldest
                if 'Net Income' in financials_yearly[key]:
                    net_income_list.append((float(financials_yearly[key]['Net Income'])) * EARNINGS_WEIGHTS[qnig_weight_index])
                    weights_sum += EARNINGS_WEIGHTS[qnig_weight_index]
                    if qnig_weight_index > 0:
                        current_net_income = financials_yearly[key]['Net Income']
                        if float(previous_net_income) != 0.0 and float(current_net_income) != 0.0:  # (this-prev)/(abs(this)+abs(prev))
                            value_to_append = calculate_current_vs_previous_change_ratio(current_net_income, previous_net_income)
                            qnig_list.append(value_to_append * EARNINGS_WEIGHTS[qnig_weight_index - 1])
                        else:
                            qnig_list.append(0.0)  # No change
                        qnig_weights_sum += EARNINGS_WEIGHTS[qnig_weight_index - 1]
                    previous_net_income = financials_yearly[key]['Net Income']
                    qnig_weight_index += 1
                if 'Total Revenue' in financials_yearly[key]:
                    if qtrg_weight_index > 0:
                        current_total_revenue = financials_yearly[key]['Total Revenue']
                        if float(previous_total_revenue) != 0.0 and float(current_total_revenue) != 0.0:  # (this-prev)/(abs(this)+abs(prev))
                            value_to_append = calculate_current_vs_previous_change_ratio(current_total_revenue, previous_total_revenue)
                            qtrg_list.append(value_to_append * REVENUES_WEIGHTS[qtrg_weight_index - 1])
                        else:
                            qtrg_list.append(0.0)  # No change
                        qtrg_weights_sum += REVENUES_WEIGHTS[qtrg_weight_index - 1]
                    previous_total_revenue = financials_yearly[key]['Total Revenue']
                    qtrg_weight_index += 1
                # Calculate an alternative to the profit_margin calculation: TODO: ASAFR: Apply the bonuses and the previous comparison for slope bonus here as well!
                if 'Net Income' in financials_yearly[key] and 'Total Revenue' in financials_yearly[key]:
                    if float(financials_yearly[key]['Total Revenue']) > 0:
                        earnings_to_revenues_list.append((float(financials_yearly[key]['Net Income'])/float(financials_yearly[key]['Total Revenue']))*PROFIT_MARGIN_YEARLY_WEIGHTS[weight_index])
                        alternative_pm_weights_sum += PROFIT_MARGIN_YEARLY_WEIGHTS[weight_index]
                        weight_index += 1

            if alternative_annual_pm_required and alternative_pm_weights_sum > 0:
                stock_data.annualized_profit_margin = sum(earnings_to_revenues_list)/float(alternative_pm_weights_sum)

            if len(net_income_list):
                stock_data.annualized_net_income = stock_data.financial_currency_conversion_rate_mult_to_usd * sum(net_income_list) / float(weights_sum)  # Multiplying by the factor to get the valu in USD.
            else:
                stock_data.annualized_net_income = None

            if len(qnig_list):
                stock_data.niqg_yoy = sum(qnig_list) / float(qnig_weights_sum)
            else:
                stock_data.niqg_yoy = None
            if len(qtrg_list):
                stock_data.trqg_yoy = sum(qtrg_list) / float(qtrg_weights_sum)
            else:
                stock_data.trqg_yoy = None
        else:
            stock_data.niqg_yoy              = None
            stock_data.trqg_yoy              = None
            stock_data.annualized_net_income = None

        # Earnings are ordered from oldest to newest so no reversing required for weights:
        if earnings_quarterly != None and 'Revenue' in earnings_quarterly: [stock_data.quarterized_revenue, stock_data.quarterized_revenue_bonus]    = calculate_weighted_stock_data_on_dict(earnings_quarterly['Revenue'],   'earnings_quarterly[Revenue]',   None,            NO_WEIGHTS, stock_data, False, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=3.0, bonus_mon_dec=1.0/3.0, bonus_neg_pres=1.0)
        else:                                                              stock_data.quarterized_revenue = None

        # Financials are ordered newest to oldest so reversing is required for weights:
        [stock_data.quarterized_total_revenue, stock_data.quarterized_total_revenue_bonus]                                                           = calculate_weighted_stock_data_on_dict(financials_quarterly,            'financials_quarterly',          'Total Revenue', NO_WEIGHTS, stock_data, True,  True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=3.0, bonus_mon_dec=1.0/3.0, bonus_neg_pres=1.0)

        # Earnings are ordered from oldest to newest so no reversing required for weights:
        if earnings_quarterly != None and 'Earnings' in earnings_quarterly: [stock_data.quarterized_earnings, stock_data.quarterized_earnings_bonus] = calculate_weighted_stock_data_on_dict(earnings_quarterly['Earnings'],  'earnings_quarterly[Earnings]',  None,            NO_WEIGHTS, stock_data, False, True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,     bonus_neg_pres=0.25)
        else:                                                               stock_data.quarterized_earnings = None

        # TODO: ASAFR: Add a calculation of net_income_to_total_revenue_list
        # Financials are ordered newest to oldest so reversing is required for weights:
        [stock_data.quarterized_net_income, stock_data.quarterized_net_income_bonus]                                                                 = calculate_weighted_stock_data_on_dict(financials_quarterly,            'financials_quarterly',          'Net Income',    NO_WEIGHTS, stock_data, True,  True, bonus_all_pos=1.0, bonus_all_neg=1.0, bonus_mon_inc=2.0, bonus_mon_dec=0.5,     bonus_neg_pres=0.25)

        # At this stage, use the Total Revenue and Net Income as backups for revenues and earnings. TODO: ASAFR: Later on run comparisons and take them into account as well!
        if   stock_data.annualized_net_income  is None and stock_data.quarterized_net_income is None: stock_data.effective_net_income = None
        elif stock_data.annualized_net_income  is None and stock_data.quarterized_net_income != None: stock_data.effective_net_income = stock_data.quarterized_net_income
        elif stock_data.quarterized_net_income is None and stock_data.annualized_net_income  != None: stock_data.effective_net_income = stock_data.annualized_net_income
        else                                                                                        : stock_data.effective_net_income = (stock_data.quarterized_net_income) # Prefer TTM only

        if   stock_data.annualized_total_revenue   is None and stock_data.quarterized_total_revenue  is None: stock_data.effective_total_revenue  = None
        elif stock_data.annualized_total_revenue   is None and stock_data.quarterized_total_revenue  != None: stock_data.effective_total_revenue  = stock_data.quarterized_total_revenue
        elif stock_data.quarterized_total_revenue  is None and stock_data.annualized_total_revenue   != None: stock_data.effective_total_revenue  = stock_data.annualized_total_revenue
        else                                                                                                : stock_data.effective_total_revenue  = (stock_data.quarterized_total_revenue ) # Prefer TTM only

        if   stock_data.annualized_earnings  is None: stock_data.annualized_earnings  = stock_data.annualized_net_income
        if   stock_data.quarterized_earnings is None: stock_data.quarterized_earnings = stock_data.quarterized_net_income

        if   stock_data.annualized_earnings  is None and stock_data.quarterized_earnings is None: stock_data.effective_earnings = stock_data.effective_net_income
        elif stock_data.annualized_earnings  is None and stock_data.quarterized_earnings != None: stock_data.effective_earnings = stock_data.quarterized_earnings
        elif stock_data.quarterized_earnings is None and stock_data.annualized_earnings  != None: stock_data.effective_earnings = stock_data.annualized_earnings
        else                                                                                    : stock_data.effective_earnings = (stock_data.quarterized_earnings) # Prefer TTM only

        if   stock_data.annualized_revenue   is None: stock_data.annualized_revenue   = stock_data.annualized_total_revenue
        if   stock_data.quarterized_revenue  is None: stock_data.quarterized_revenue  = stock_data.quarterized_total_revenue

        if   stock_data.annualized_revenue   is None and stock_data.quarterized_revenue  is None: stock_data.effective_revenue  = stock_data.effective_total_revenue
        elif stock_data.annualized_revenue   is None and stock_data.quarterized_revenue  != None: stock_data.effective_revenue  = stock_data.quarterized_revenue
        elif stock_data.quarterized_revenue  is None and stock_data.annualized_revenue   != None: stock_data.effective_revenue  = stock_data.annualized_revenue
        else                                                                                    : stock_data.effective_revenue  = (stock_data.quarterized_revenue ) # Prefer TTM only

        if 'country' in info:                stock_data.country = info['country']
        else:                                stock_data.country = 'Unknown'
        if stock_data.country is None: stock_data.country       = 'Unknown'

        if 'profitMargins' in info:          stock_data.profit_margin = info['profitMargins']
        else:                                stock_data.profit_margin = None

        if 'heldPercentInstitutions' in info:                                                         stock_data.held_percent_institutions = info['heldPercentInstitutions']
        else:                                                                                         stock_data.held_percent_institutions = PERCENT_HELD_INSTITUTIONS_LOW
        if stock_data.held_percent_institutions is None or stock_data.held_percent_institutions == 0: stock_data.held_percent_institutions = PERCENT_HELD_INSTITUTIONS_LOW

        if 'heldPercentInsiders' in info:                                                             stock_data.held_percent_insiders     = info['heldPercentInsiders']
        else:                                                                                         stock_data.held_percent_insiders     = PERCENT_HELD_INSIDERS_UNKNOWN
        if stock_data.held_percent_insiders     is None or stock_data.held_percent_insiders == 0:     stock_data.held_percent_insiders     = PERCENT_HELD_INSIDERS_UNKNOWN

        if 'enterpriseToRevenue' in info:
            stock_data.enterprise_value_to_revenue = info['enterpriseToRevenue']
            if stock_data.enterprise_value_to_revenue != None: stock_data.enterprise_value_to_revenue *= stock_data.summary_currency_conversion_rate_mult_to_usd # https://www.investopedia.com/terms/e/ev-revenue-multiple.asp
        else:
            stock_data.enterprise_value_to_revenue = None # Mark as None, so as to try and calculate manually. TODO: ASAFR: Do the same to the Price and to the Earnings and the Price/Earnings (Also to sales if possible)
        if isinstance(stock_data.enterprise_value_to_revenue,str): stock_data.enterprise_value_to_revenue = None # Mark as None, so as to try and calculate manually.

        if 'marketCap' in info and info['marketCap'] != None:
            stock_data.market_cap = info['marketCap']*stock_data.summary_currency_conversion_rate_mult_to_usd
        else:
            stock_data.market_cap = None

        if 'enterpriseValue' in info and info['enterpriseValue'] != None: stock_data.enterprise_value = info['enterpriseValue']*stock_data.summary_currency_conversion_rate_mult_to_usd
        if stock_data.enterprise_value is None or stock_data.enterprise_value <= 0:
            if   'marketCap' in info and info['marketCap'] != None:
                stock_data.enterprise_value = int(info['marketCap']*stock_data.summary_currency_conversion_rate_mult_to_usd)
        elif stock_data.market_cap is None or stock_data.market_cap <= 0:
            stock_data.market_cap = stock_data.enterprise_value

        # in order to calculate eibtd, take ebit from finantials and add deprecations from cash_flows to it:
        # Financials and Cash Flows are ordered newest to oldest so reversing is required for weights:
        stock_data.quarterized_ebitd = calculate_weighted_sum_from_2_dicts(financials_quarterly, 'financials_quarterly', 'Ebit', cash_flows_quarterly, 'cash_flows_quarterly', 'Depreciation', NO_WEIGHTS,       stock_data, 0, True, True, True)
        stock_data.annualized_ebitd  = calculate_weighted_sum_from_2_dicts(financials_yearly,    'financials_yearly',    'Ebit', cash_flows_yearly,    'cash_flows_yearly',    'Depreciation', EARNINGS_WEIGHTS, stock_data, 0, True, True)
        stock_data.ebitd             = (stock_data.quarterized_ebitd) # Prefer TTM only

        # TODO: ASAFR: 1. ebit (within financials) can be used instead of simply taking the earnings
        #              1.1. is ebit available for all/most TASE stocks? ebitd
        #              1.2. There is a similar field (same value different name) besides ebit - see if it is always the same? Low priority
        #              1.3. If enterpriseToEbitda is available (for most stocks it is? Check), then EBITDA = EV/enterpriseToEbitda
        #              1.3.1. But if EV is negative for some stocks... then Market Capital might be used...
        #              1.4. Suggestion: take average such that EBITDA = (EV/enterpriseToEbitda + CalculatedEbitFromFinancialsAndCashFlows)/2
        if 'enterpriseToEbitda' in info:
            stock_data.enterprise_value_to_ebitda = info['enterpriseToEbitda']
            if stock_data.enterprise_value_to_ebitda != None:
                stock_data.enterprise_value_to_ebitda *= stock_data.summary_currency_conversion_rate_mult_to_usd  # The lower the better: https://www.investopedia.com/ask/answers/072715/what-considered-healthy-evebitda.asp

                # Calculate ebitda from enterprise_value_to_ebitda:
                if stock_data.enterprise_value_to_ebitda != 0: stock_data.ebitda = (float(stock_data.enterprise_value)/float(stock_data.enterprise_value_to_ebitda) + float(stock_data.ebitd))/2.0
        else:
            if stock_data.ebitd != 0:
                stock_data.enterprise_value_to_ebitda = float(stock_data.enterprise_value)/float(stock_data.ebitd)

        if stock_data.enterprise_value_to_ebitda != None and stock_data.enterprise_value_to_ebitda != 0:
            stock_data.effective_ev_to_ebitda = (stock_data.enterprise_value_to_ebitda + float(stock_data.enterprise_value)/float(stock_data.ebitda) if stock_data.ebitda != 0 else float(stock_data.enterprise_value_to_ebitda))/2.0
        else:
            stock_data.effective_ev_to_ebitda = EV_TO_EBITDA_MAX_UNKNOWN

        if 'trailingPE' in info:
            stock_data.trailing_price_to_earnings  = info['trailingPE']  # https://www.investopedia.com/terms/t/trailingpe.asp
            if tase_mode and stock_data.trailing_price_to_earnings != None:
                stock_data.trailing_price_to_earnings /= 100.0  # In TLV stocks, yfinance multiplies trailingPE by a factor of 100, so compensate
                if stock_data.symbol in g_symbols_tase_duals:  # TODO: ASAFR: Do research and add this condition to all relevant cases in other fundamental parameters
                    stock_data.trailing_price_to_earnings *= stock_data.summary_currency_conversion_rate_mult_to_usd # Additionally, in TLV DUAL stocks this ratio is mistakenly calculated using PriceInNis/EarningsInUSD -> so Compensate
        elif stock_data.effective_earnings != None and stock_data.effective_earnings != 0 and stock_data.market_cap != None:
            stock_data.trailing_price_to_earnings = float(stock_data.market_cap)       / float(stock_data.effective_earnings) # Calculate manually.
        elif stock_data.effective_net_income != None and stock_data.effective_net_income != 0 and stock_data.enterprise_value != None:
            stock_data.trailing_price_to_earnings = float(stock_data.enterprise_value) / float(stock_data.effective_net_income)  # Calculate manually.
        if isinstance(stock_data.trailing_price_to_earnings,str):  stock_data.trailing_price_to_earnings  = MAX_UNKNOWN_PE # Mark as None, so as to try and calculate manually.

        if 'forwardPE' in info:
            stock_data.forward_price_to_earnings  = info['forwardPE']  # https://www.investopedia.com/terms/t/trailingpe.asp
            if tase_mode and stock_data.forward_price_to_earnings != None:
                stock_data.forward_price_to_earnings /= 100.0 # In TLV stocks, yfinance multiplies forwardPE by a factor of 100, so compensate
                if stock_data.symbol in g_symbols_tase_duals:  # TODO: ASAFR: Do research and add this condition to all relevant cases in other fundamental parameters
                    stock_data.forward_price_to_earnings *= stock_data.summary_currency_conversion_rate_mult_to_usd # Additionally, in DUAL TLV stocks this ratio is mistakenly calculated using PriceInNis/EarningsInUSD -> so Compensate
        else:  stock_data.forward_price_to_earnings  = None # Mark as None, so as to try and calculate manually. TODO: ASAFR: Calcualte using the forward_eps?

        if   stock_data.trailing_price_to_earnings is None and stock_data.forward_price_to_earnings  is None: stock_data.effective_price_to_earnings = None
        elif stock_data.forward_price_to_earnings  is None and stock_data.trailing_price_to_earnings != None: stock_data.forward_price_to_earnings   = stock_data.trailing_price_to_earnings
        elif stock_data.trailing_price_to_earnings is None and stock_data.forward_price_to_earnings  != None: stock_data.trailing_price_to_earnings  = stock_data.forward_price_to_earnings

        # Handle Negative Values of P/E: Negative P/E handling (TODO: ASAFR: Research this, maybe a smiling parabola is preferred, or some different less harsh function than 1/-x, like some damper n/[e+X])
        # Sources: https://www.investopedia.com/ask/answers/05/negativeeps.asp

        if stock_data.trailing_price_to_earnings != None:
            if   stock_data.trailing_price_to_earnings  < 0: stock_data.trailing_price_to_earnings = -NEGATIVE_EARNINGS_FACTOR/float(stock_data.trailing_price_to_earnings)
            elif stock_data.trailing_price_to_earnings == 0: stock_data.trailing_price_to_earnings =  NEGATIVE_EARNINGS_FACTOR
        if stock_data.forward_price_to_earnings  != None:
            if   stock_data.forward_price_to_earnings   < 0: stock_data.forward_price_to_earnings  = -NEGATIVE_EARNINGS_FACTOR/float(stock_data.forward_price_to_earnings)
            elif stock_data.forward_price_to_earnings  == 0: stock_data.forward_price_to_earnings  =  NEGATIVE_EARNINGS_FACTOR

        # Calculate the weighted average of the forward and trailing P/E:
        if (stock_data.trailing_price_to_earnings != None and stock_data.forward_price_to_earnings != None):
            stock_data.effective_price_to_earnings = (stock_data.trailing_price_to_earnings*TRAILING_PRICE_TO_EARNINGS_WEIGHT+stock_data.forward_price_to_earnings*FORWARD_PRICE_TO_EARNINGS_WEIGHT)

        if 'forwardEps'                                 in info: stock_data.forward_eps                       = info['forwardEps']
        else:                                                    stock_data.forward_eps                       = None
        if isinstance(stock_data.forward_eps,str):               stock_data.forward_eps                       = None

        if 'trailingEps'                                in info: stock_data.trailing_eps                      = info['trailingEps']
        else:                                                    stock_data.trailing_eps                      = None
        if isinstance(stock_data.trailing_eps,str):              stock_data.trailing_eps                      = None

        if 'previousClose'                              in info: stock_data.previous_close                    = info['previousClose']
        else:                                                    stock_data.previous_close                    = None
        if isinstance(stock_data.previous_close,str):            stock_data.previous_close                    = None

        if '52WeekChange'         in info: stock_data.fifty_two_week_change   = info['52WeekChange']
        if 'fiftyTwoWeekLow'      in info: stock_data.fifty_two_week_low      = info['fiftyTwoWeekLow']
        if 'fiftyTwoWeekHigh'     in info: stock_data.fifty_two_week_high     = info['fiftyTwoWeekHigh']
        if 'twoHundredDayAverage' in info: stock_data.two_hundred_day_average = info['twoHundredDayAverage']

        if stock_data.fifty_two_week_change                                                        is None: stock_data.fifty_two_week_change   = stock_data.previous_close
        if stock_data.fifty_two_week_low                                                           is None: stock_data.fifty_two_week_low      = stock_data.previous_close
        if stock_data.fifty_two_week_high                                                          is None: stock_data.fifty_two_week_high     = stock_data.previous_close
        if stock_data.two_hundred_day_average                                                      is None: stock_data.two_hundred_day_average = stock_data.previous_close
        if stock_data.previous_close != None and stock_data.previous_close < stock_data.fifty_two_week_low: stock_data.previous_close          = stock_data.fifty_two_week_low

        if stock_data.two_hundred_day_average != None and stock_data.two_hundred_day_average > 0.0: stock_data.previous_close_percentage_from_200d_ma  = 100.0 * ((float(stock_data.previous_close) - float(stock_data.two_hundred_day_average)) / float(stock_data.two_hundred_day_average))
        if stock_data.fifty_two_week_low      != None and stock_data.fifty_two_week_low      > 0.0: stock_data.previous_close_percentage_from_52w_low  = 100.0 * ((float(stock_data.previous_close) - float(stock_data.fifty_two_week_low)     ) / float(stock_data.fifty_two_week_low)     )
        if stock_data.fifty_two_week_high     != None and stock_data.fifty_two_week_high     > 0.0: stock_data.previous_close_percentage_from_52w_high = 100.0 * ((float(stock_data.previous_close) - float(stock_data.fifty_two_week_high)    ) / float(stock_data.fifty_two_week_high)    )
        if stock_data.fifty_two_week_low      != None and stock_data.fifty_two_week_low      > 0.0 and stock_data.fifty_two_week_high > 0.0 and stock_data.previous_close > 0.0:
            if stock_data.fifty_two_week_high == stock_data.fifty_two_week_low or stock_data.previous_close == 0:  # TODO: ASAFR: Take these values from nasdaq_traded.csv when they are not available temporarily on yfinance
                stock_data.dist_from_low_factor = 1.0  # When there is no range or no previous_close_data, leave as neutral
            else:
                stock_data.dist_from_low_factor = float(stock_data.previous_close - stock_data.fifty_two_week_low)/(0.5*float(stock_data.fifty_two_week_high-stock_data.fifty_two_week_low))
            stock_data.eff_dist_from_low_factor = (DIST_FROM_LOW_FACTOR_DAMPER + stock_data.dist_from_low_factor) if stock_data.dist_from_low_factor < 1.0 else (stock_data.dist_from_low_factor**DIST_FROM_LOW_FACTOR_HIGHER_THAN_ONE_POWER)

        if stock_data.trailing_eps != None and stock_data.previous_close != None and stock_data.previous_close > 0:
            stock_data.trailing_eps_percentage = float(stock_data.trailing_eps) / float(stock_data.previous_close)

        if 'priceToBook'                                in info:
            stock_data.price_to_book = info['priceToBook']
            if tase_mode and stock_data.price_to_book != None: # yfinance mistakenly multiplies value by 100
                stock_data.price_to_book /= 100.0
                if stock_data.symbol in g_symbols_tase_duals:  # TODO: ASAFR: Do research and add this condition to all relevant cases in other fundamental parameters
                    stock_data.price_to_book *= stock_data.summary_currency_conversion_rate_mult_to_usd  # This is required only for the dual-listed companies on TASE and NASDAQ - for some reason
        else:
            stock_data.price_to_book      = None # Mark as None, so as to try and calculate manually.
        if isinstance(stock_data.price_to_book,str): stock_data.price_to_book = None # Mark as None, so as to try and calculate manually.
        if stock_data.price_to_book is None:
            stock_data.price_to_book = PRICE_TO_BOOK_UNKNOWN * (10 if tase_mode else 1) # TODO: ASAFR: Until calculated manually, do not allow N/A in price2book to ruin the whole value, just set a very unatractive one, and let the rest of the parameters cope

        # Value is a ratio, such that when multiplied by 100, yields percentage (%) units:
        if 'earningsQuarterlyGrowth'                    in info: stock_data.eqg         = info['earningsQuarterlyGrowth']
        else:                                                    stock_data.eqg         = None

        # Value is a ratio, such that when multiplied by 100, yields percentage (%) units:
        if 'revenueGrowth'                     in info: stock_data.rqg         = info['revenueGrowth']
        else:                                           stock_data.rqg         = None

        # TODO: ASAFR: Currently use the niqg_yoy and trqg_yoy as a simple backup. Later on - compare and add to calculations...
        if stock_data.eqg_yoy is None: stock_data.eqg_yoy = stock_data.niqg_yoy
        if stock_data.rqg_yoy is None: stock_data.rqg_yoy = stock_data.trqg_yoy

        # Now use above backup as required: TODO: ASAFR: One may use the yoy as direct backup... analyze this...
        if   stock_data.eqg is None and stock_data.eqg_yoy != None: stock_data.eqg     = stock_data.eqg_yoy
        elif stock_data.eqg != None and stock_data.eqg_yoy is None: stock_data.eqg_yoy = stock_data.eqg
        elif stock_data.eqg is None and stock_data.eqg_yoy is None: stock_data.eqg_yoy = stock_data.eqg = EQG_UNKNOWN

        if   stock_data.rqg is None and stock_data.rqg_yoy != None: stock_data.rqg     = stock_data.rqg_yoy
        elif stock_data.rqg != None and stock_data.rqg_yoy is None: stock_data.rqg_yoy = stock_data.rqg
        elif stock_data.rqg is None and stock_data.rqg_yoy is None: stock_data.rqg_yoy = stock_data.rqg = RQG_UNKNOWN

        stock_data.eqg_effective = EQG_WEIGHT_VS_YOY*stock_data.eqg + (1.0-EQG_WEIGHT_VS_YOY)*stock_data.eqg_yoy
        stock_data.rqg_effective = RQG_WEIGHT_VS_YOY*stock_data.rqg + (1.0-RQG_WEIGHT_VS_YOY)*stock_data.rqg_yoy

        if stock_data.eqg_effective > 0:
            stock_data.eqg_factor_effective = (EQG_DAMPER + EQG_POSITIVE_FACTOR * math.sqrt(stock_data.eqg_effective))
        else:
            stock_data.eqg_factor_effective = (EQG_DAMPER + float(stock_data.eqg_effective)/EQG_POSITIVE_FACTOR)

        if stock_data.rqg_effective >= 0:
            stock_data.rqg_factor_effective = (RQG_DAMPER + RQG_POSITIVE_FACTOR * math.sqrt(stock_data.rqg_effective))
        else:
            stock_data.rqg_factor_effective = (RQG_DAMPER + float(stock_data.rqg_effective)/RQG_POSITIVE_FACTOR)

        if 'sharesOutstanding'                          in info: stock_data.shares_outstanding                = info['sharesOutstanding']
        else:                                                    stock_data.shares_outstanding                = SHARES_OUTSTANDING_UNKNOWN
        if stock_data.shares_outstanding is None or stock_data.shares_outstanding == 0:
            stock_data.shares_outstanding = SHARES_OUTSTANDING_UNKNOWN

        if 'netIncomeToCommon' in info: stock_data.net_income_to_common_shareholders = info['netIncomeToCommon']
        else:                           stock_data.net_income_to_common_shareholders = None # TODO: ASAFR: It may be possible to calculate this manually

        # if no effective_ev_to_ebitda, use earnings.
        if stock_data.effective_ev_to_ebitda is None and stock_data.enterprise_value != None and stock_data.enterprise_value != 0 and stock_data.effective_earnings != None and stock_data.effective_earnings != 0:
            stock_data.effective_ev_to_ebitda = float(stock_data.enterprise_value) / float(stock_data.effective_earnings)  #  effective_earnings is already in USD

        if stock_data.effective_ev_to_ebitda != None:
            if   stock_data.effective_ev_to_ebitda  < 0: stock_data.effective_ev_to_ebitda = -NEGATIVE_EARNINGS_FACTOR/float(stock_data.effective_ev_to_ebitda)
            elif stock_data.effective_ev_to_ebitda == 0: stock_data.effective_ev_to_ebitda =  NEGATIVE_EARNINGS_FACTOR

        if stock_data.annualized_total_assets is None and stock_data.quarterized_total_assets is None:
            stock_data.effective_total_assets = None
        elif stock_data.annualized_total_assets is None and stock_data.quarterized_total_assets != None:
            stock_data.annualized_total_assets = stock_data.quarterized_total_assets*QUARTERLY_YEARLY_MISSING_FACTOR
        elif stock_data.annualized_total_assets != None and stock_data.quarterized_total_assets is None:
            stock_data.quarterized_total_assets = stock_data.annualized_total_assets*QUARTERLY_YEARLY_MISSING_FACTOR

        if stock_data.quarterized_total_assets != None:
            stock_data.effective_total_assets = (stock_data.quarterized_total_assets) # Prefer TTM only

        if stock_data.annualized_total_stockholder_equity is None and stock_data.quarterized_total_stockholder_equity is None:
            stock_data.effective_total_stockholder_equity = None
        elif stock_data.annualized_total_stockholder_equity is None and stock_data.quarterized_total_stockholder_equity != None:
            stock_data.annualized_total_stockholder_equity = stock_data.quarterized_total_stockholder_equity*QUARTERLY_YEARLY_MISSING_FACTOR
        elif stock_data.annualized_total_stockholder_equity != None and stock_data.quarterized_total_stockholder_equity is None:
            stock_data.quarterized_total_stockholder_equity = stock_data.annualized_total_stockholder_equity*QUARTERLY_YEARLY_MISSING_FACTOR

        if stock_data.quarterized_total_stockholder_equity != None:
            stock_data.effective_total_stockholder_equity = (stock_data.quarterized_total_stockholder_equity) # Prefer TTM only

        if stock_data.annualized_retained_earnings is None and stock_data.quarterized_retained_earnings is None:
            stock_data.effective_retained_earnings = None
        elif stock_data.annualized_retained_earnings is None and stock_data.quarterized_retained_earnings != None:
            stock_data.annualized_retained_earnings = stock_data.quarterized_retained_earnings*QUARTERLY_YEARLY_MISSING_FACTOR
        elif stock_data.annualized_retained_earnings != None and stock_data.quarterized_retained_earnings is None:
            stock_data.quarterized_retained_earnings = stock_data.annualized_retained_earnings*QUARTERLY_YEARLY_MISSING_FACTOR

        if stock_data.quarterized_retained_earnings != None:
            stock_data.effective_retained_earnings = (stock_data.quarterized_retained_earnings) # Prefer TTM only

        # TODO: ASAFR: This must be upgraded to the form of an ongoing ration calculations like done in Net Income / Total Revenue
        if stock_data.effective_total_assets != None and stock_data.effective_total_assets > 0 and stock_data.effective_net_income != None:
            stock_data.calculated_roa = ROA_DAMPER + float(stock_data.effective_net_income)/float(stock_data.effective_total_assets)
        if stock_data.calculated_roa != None and 0 < stock_data.calculated_roa < ROA_DAMPER:
            stock_data.calculated_roa /= 1000.0
        elif stock_data.calculated_roa != None and stock_data.calculated_roa <= 0:
            stock_data.calculated_roa = ROA_NEG_FACTOR

        if stock_data.effective_total_stockholder_equity != None and stock_data.effective_total_stockholder_equity > 0 and stock_data.effective_net_income != None:
            stock_data.calculated_roe = ROE_DAMPER + stock_data.effective_net_income/stock_data.effective_total_stockholder_equity
        if stock_data.calculated_roe != None and 0 < stock_data.calculated_roe < ROE_DAMPER:
            stock_data.calculated_roe /= 1000.0
        elif stock_data.calculated_roe != None and stock_data.calculated_roe <= 0:
            stock_data.calculated_roe = ROE_NEG_FACTOR

        if stock_data.annualized_cash_flow_from_operating_activities is None and stock_data.quarterized_cash_flow_from_operating_activities is None:
            if stock_data.effective_earnings != None:
                stock_data.annualized_cash_flow_from_operating_activities = stock_data.quarterized_cash_flow_from_operating_activities = stock_data.effective_earnings
        elif stock_data.annualized_cash_flow_from_operating_activities is None and stock_data.quarterized_cash_flow_from_operating_activities != None:
            if stock_data.quarterized_cash_flow_from_operating_activities >= 0:
                stock_data.annualized_cash_flow_from_operating_activities = stock_data.quarterized_cash_flow_from_operating_activities*QUARTERLY_YEARLY_MISSING_FACTOR
            else:
                stock_data.annualized_cash_flow_from_operating_activities = float(stock_data.quarterized_cash_flow_from_operating_activities)/float(QUARTERLY_YEARLY_MISSING_FACTOR)
        elif stock_data.annualized_cash_flow_from_operating_activities != None and stock_data.quarterized_cash_flow_from_operating_activities is None:
            if stock_data.annualized_cash_flow_from_operating_activities >= 0:
                stock_data.quarterized_cash_flow_from_operating_activities = stock_data.annualized_cash_flow_from_operating_activities*QUARTERLY_YEARLY_MISSING_FACTOR
            else:
                stock_data.quarterized_cash_flow_from_operating_activities = float(stock_data.annualized_cash_flow_from_operating_activities)/float(QUARTERLY_YEARLY_MISSING_FACTOR)


        if stock_data.annualized_cash_flow_from_operating_activities != None:
            if stock_data.annualized_cash_flow_from_operating_activities >= 0:
                if stock_data.enterprise_value == 0 or stock_data.annualized_cash_flow_from_operating_activities == 0: # When 0, it means either EV is 0 (strange!) or a very very good cash flow (strange as well)
                    stock_data.annualized_ev_to_cfo_ratio = ev_to_cfo_ratio_limit * 1000.0  # Set a very high value to make stock unatractive
                else:
                    stock_data.annualized_ev_to_cfo_ratio = float(stock_data.enterprise_value)/float(stock_data.annualized_cash_flow_from_operating_activities)  # annualized_cash_flow_from_operating_activities has been converted to USD earlier
            else:  # stock_data.annualized_cash_flow_from_operating_activities < 0
                if stock_data.enterprise_value == 0 or stock_data.annualized_cash_flow_from_operating_activities == 0: # When 0, it means either EV is 0 (strange!) or a very very good cash flow (strange as well)
                    stock_data.annualized_ev_to_cfo_ratio = ev_to_cfo_ratio_limit * 1000.0  # Set a very high value to make stock unatractive
                else:
                    stock_data.annualized_ev_to_cfo_ratio = -NEGATIVE_CFO_FACTOR/(float(stock_data.enterprise_value)/float(stock_data.annualized_cash_flow_from_operating_activities))
        else:
            stock_data.annualized_ev_to_cfo_ratio = ev_to_cfo_ratio_limit * 1000.0
        if stock_data.quarterized_cash_flow_from_operating_activities != None:
            if stock_data.quarterized_cash_flow_from_operating_activities >= 0:
                if stock_data.enterprise_value == 0 or stock_data.quarterized_cash_flow_from_operating_activities == 0: # When 0, it means either EV is 0 (strange!) or a very very good cash flow (strange as well)
                    stock_data.quarterized_ev_to_cfo_ratio = ev_to_cfo_ratio_limit * 1000.0  # Set a very high value to make stock unatractive
                else:
                    stock_data.quarterized_ev_to_cfo_ratio = float(stock_data.enterprise_value)/float(stock_data.quarterized_cash_flow_from_operating_activities)  # quarterized_cash_flow_from_operating_activities has been converted to USD earlier
            else:  # stock_data.quarterized_cash_flow_from_operating_activities < 0
                if stock_data.enterprise_value == 0 or stock_data.quarterized_cash_flow_from_operating_activities == 0: # When 0, it means either EV is 0 (strange!) or a very very good cash flow (strange as well)
                    stock_data.quarterized_ev_to_cfo_ratio = ev_to_cfo_ratio_limit * 1000.0  # Set a very high value to make stock unatractive
                else:
                    stock_data.quarterized_ev_to_cfo_ratio = -NEGATIVE_CFO_FACTOR*(float(stock_data.enterprise_value)/float(stock_data.quarterized_cash_flow_from_operating_activities))
        else:
            stock_data.quarterized_ev_to_cfo_ratio = ev_to_cfo_ratio_limit * 1000.0

        # Seems value is calculated relatively similarly in dual (TASE, NASDAQ) stocks so no compensation required
        stock_data.ev_to_cfo_ratio_effective = (stock_data.quarterized_ev_to_cfo_ratio) # Prefer TTM only
        if 'priceToSalesTrailing12Months' in info and info['priceToSalesTrailing12Months'] != None:
            stock_data.trailing_12months_price_to_sales = info['priceToSalesTrailing12Months'] # https://www.investopedia.com/articles/fundamental/03/032603.asp#:~:text=The%20price%2Dto%2Dsales%20ratio%20(Price%2FSales%20or,the%20more%20attractive%20the%20investment.
            if isinstance(stock_data.trailing_12months_price_to_sales, str):  stock_data.trailing_12months_price_to_sales = None
            if tase_mode and stock_data.trailing_12months_price_to_sales != None: stock_data.trailing_12months_price_to_sales *= (float(stock_data.summary_currency_conversion_rate_mult_to_usd)/100.0) # Wrongly calculated by yfinance for TASE
        else:
            if stock_data.effective_revenue != None and stock_data.effective_revenue > 0 and stock_data.market_cap != None and stock_data.market_cap > 0:
                stock_data.trailing_12months_price_to_sales  = float(stock_data.market_cap) / float(stock_data.effective_revenue)  # effective_revenue and_market_cap are already in USD (converted earlier)
            elif stock_data.ev_to_cfo_ratio_effective != None:
                stock_data.trailing_12months_price_to_sales  = stock_data.ev_to_cfo_ratio_effective
            else:
                stock_data.trailing_12months_price_to_sales  = None # Mark as None, so as to try and calculate manually.
        if isinstance(stock_data.trailing_12months_price_to_sales,str):  stock_data.trailing_12months_price_to_sales  = None # Mark as None, so as to try and calculate manually.

        calculate_altman_z_score_factor(stock_data)

        if (stock_data.enterprise_value_to_revenue != None and stock_data.enterprise_value_to_revenue <= 0 or stock_data.enterprise_value_to_revenue is None) and stock_data.effective_revenue != None and stock_data.effective_revenue > 0:
            stock_data.evr_effective = float(stock_data.enterprise_value)/float(stock_data.effective_revenue)
        else:
            stock_data.evr_effective = stock_data.enterprise_value_to_revenue

        if stock_data.effective_price_to_earnings != None:
            if stock_data.sector in favor_sectors:
                index = favor_sectors.index(stock_data.sector)
                stock_data.pe_effective = float(stock_data.effective_price_to_earnings) / float(favor_sectors_by[index])  # ** 2
            else:
                stock_data.pe_effective = stock_data.effective_price_to_earnings

            if   stock_data.profit_margin            is None and stock_data.annualized_profit_margin is None and stock_data.quarterized_profit_margin is None:
                 stock_data.profit_margin            = stock_data.annualized_profit_margin  = stock_data.quarterized_profit_margin = PROFIT_MARGIN_UNKNOWN
            elif stock_data.profit_margin            is None and stock_data.annualized_profit_margin is None                                                 :
                 stock_data.profit_margin            = stock_data.annualized_profit_margin  = float(stock_data.quarterized_profit_margin)/PROFIT_MARGIN_DUPLICATION_FACTOR
            elif stock_data.annualized_profit_margin is None and stock_data.quarterized_profit_margin is None:
                 stock_data.annualized_profit_margin = stock_data.quarterized_profit_margin = float(stock_data.profit_margin)/PROFIT_MARGIN_DUPLICATION_FACTOR
            elif stock_data.profit_margin            is None and stock_data.quarterized_profit_margin is None:
                 stock_data.profit_margin            = stock_data.quarterized_profit_margin = float(stock_data.annualized_profit_margin)/PROFIT_MARGIN_DUPLICATION_FACTOR
            elif stock_data.profit_margin             is None: stock_data.profit_margin             = float(stock_data.annualized_profit_margin+stock_data.quarterized_profit_margin)/(2.0*PROFIT_MARGIN_DUPLICATION_FACTOR)
            elif stock_data.annualized_profit_margin  is None: stock_data.annualized_profit_margin  = float(stock_data.profit_margin)/PROFIT_MARGIN_DUPLICATION_FACTOR
            elif stock_data.quarterized_profit_margin is None: stock_data.quarterized_profit_margin = float(stock_data.profit_margin)/PROFIT_MARGIN_DUPLICATION_FACTOR

            sorted_pms = sorted([stock_data.profit_margin, stock_data.annualized_profit_margin, stock_data.quarterized_profit_margin])
            weighted_average_pm = weighted_average(sorted_pms, NO_WEIGHTS[:len(sorted_pms)]) # Higher weight to the higher profit margin when averaging out
            stock_data.effective_profit_margin = PROFIT_MARGIN_DAMPER + weighted_average_pm

        # The PEG Ratio is equal to (share_price / earnings_per_share) / (earnings_per_share_growth_ratio [% units])
        if 'pegRatio' in info:
            stock_data.price_to_earnings_to_growth_ratio = info['pegRatio']
        else:
            stock_data.price_to_earnings_to_growth_ratio = PEG_UNKNOWN

        if stock_data.price_to_earnings_to_growth_ratio is None or stock_data.price_to_earnings_to_growth_ratio == PEG_UNKNOWN:
            if stock_data.eqg_effective != None and stock_data.eqg_effective != 0 and stock_data.effective_price_to_earnings != None and stock_data.effective_price_to_earnings > 0:
                stock_data.price_to_earnings_to_growth_ratio = float(stock_data.effective_price_to_earnings) / float(stock_data.eqg_effective)
            elif stock_data.effective_price_to_earnings != None:
                stock_data.price_to_earnings_to_growth_ratio = stock_data.effective_price_to_earnings * PEG_UNKNOWN # At this stage effective_price_to_earnings is always positive so this code will not be reached
        elif stock_data.price_to_earnings_to_growth_ratio != None:
            if   stock_data.price_to_earnings_to_growth_ratio > 0: stock_data.effective_peg_ratio =  stock_data.price_to_earnings_to_growth_ratio
            elif stock_data.price_to_earnings_to_growth_ratio < 0: stock_data.effective_peg_ratio = -NEGATIVE_PEG_RATIO_FACTOR/float(stock_data.price_to_earnings_to_growth_ratio)
            else                                                 : stock_data.effective_peg_ratio =  1.0  # Something must be wrong, so take a neutral value of 1.0
        else                                                     : stock_data.effective_peg_ratio =  1.0  # Something must be wrong, so take a neutral value of 1.0

        if return_value: sss_core_equation_value_set(stock_data)
        else:            stock_data.sss_value = BAD_SSS

        stock_data.last_dividend_0 = 0; stock_data.last_dividend_1 = 0
        stock_data.last_dividend_2 = 0; stock_data.last_dividend_3 = 0

        try:  # It is important to note that: 1. latest value is in index 0. 2. For the actual value in USD, need to translate the date of the dividend to the value of share at that time, because the dividends[] are pare share
            # if sss_config.custom_sss_value_equation:
            #     dividends =
            if isinstance(symbol, dict):
                dividends = symbol['dividends'] if 'dividends' in symbol else None
            else:
                dividends = symbol.get_dividends()

            last_dividends_list = []
            if len(dividends) > 0:
                last_4_dividends = dividends[-1:]
                stock_data.last_dividend_0 = last_4_dividends[-1] # Latest
                last_dividends_list.insert(0, stock_data.last_dividend_0)
            if len(dividends) > 1:
                last_4_dividends = dividends[-2:]
                stock_data.last_dividend_1 = last_4_dividends[-2] # One before latest
                last_dividends_list.insert(0, stock_data.last_dividend_1)
            if len(dividends) > 2:
                last_4_dividends = dividends[-3:]
                stock_data.last_dividend_2 = last_4_dividends[-3] # 2 before latest, etc
                last_dividends_list.insert(0, stock_data.last_dividend_2)
            if len(dividends) > 3:
                last_4_dividends = dividends[-4:]
                stock_data.last_dividend_3 = last_4_dividends[-4]
                last_dividends_list.insert(0, stock_data.last_dividend_3)

            json_db[stock_data.symbol]["dividends"] = last_dividends_list

        except Exception as e:
            # if not research_mode: print("Exception in symbol.dividends: {} -> {}".format(e, traceback.format_exc()))
            json_db[stock_data.symbol]["dividends"] = []
            pass

        round_and_avoid_none_values(stock_data)

        if return_value:
            print_sss_value_results(stock_data)
        else:
            print('Skipped - skip_reason: {}'.format(stock_data.skip_reason))
        if not return_value and (not research_mode or VERBOSE_LOGS > 2): print('                            ' + stock_data.skip_reason)

        return return_value

    except Exception as e:  # More information is output when exception is used instead of Exception
        if not research_mode: print("              Exception in {} info: {} -> {}".format(stock_data.symbol, e, traceback.format_exc()))
        return False


# Assumption is that reference_db is sorted by symbol name, but just find it, no need to optimize as of now
def find_symbol_in_reference_db(symbol, reference_db):
    for index in range(len(reference_db)):
        if symbol == reference_db[index][g_symbol_index]:
            return index
    return -1


def get_db_row_from_stock_data(stock_data):
    #                 "Symbol",                           "Name",                     "Sector",                     "Country",                     "sss_value",                                                                 "annualized_revenue",                           "annualized_revenue_bonus",                      "annualized_earnings",                     "annualized_retained_earnings",                           "annualized_retained_earnings_bonus",                      "quarterized_revenue",                           "quarterized_revenue_bonus",                      "quarterized_earnings",                           "quarterized_earnings_bonus",                      "quarterized_retained_earnings",                           "quarterized_retained_earnings_bonus",                      "effective_earnings",                     "effective_retained_earnings",                     "effective_revenue",                     "annualized_total_revenue",                           "annualized_total_revenue_bonus",                      "annualized_net_income",                     "quarterized_total_revenue",                           "quarterized_total_revenue_bonus",                      "quarterized_net_income",                           "quarterized_net_income_bonus",                      "effective_net_income",                     "effective_total_revenue",                     "enterprise_value_to_revenue",                           "evr_effective",                                                                      "trailing_price_to_earnings",                     "forward_price_to_earnings",                     "effective_price_to_earnings",                     "trailing_12months_price_to_sales",                                                                                        "pe_effective",                                                                    "enterprise_value_to_ebitda",                     "effective_ev_to_ebitda",                                                                              "ebitda",                     "quarterized_ebitd",                     "annualized_ebitd",                     "ebitd",                     "profit_margin",                     "annualized_profit_margin",                     "annualized_profit_margin_boost",                     "quarterized_profit_margin",                     "quarterized_profit_margin_boost",                     "effective_profit_margin",                                                                               "held_percent_institutions",                     "held_percent_insiders",                                                                             "forward_eps",                     "trailing_eps",                     "previous_close",                     "trailing_eps_percentage",                     "price_to_book",                                                                     "shares_outstanding",                     "net_income_to_common_shareholders",                     "nitcsh_to_shares_outstanding",                     "employees",                     "enterprise_value",                     "market_cap",                     "nitcsh_to_num_employees",                     "eqg",                     "rqg",                     "eqg_yoy",                     "rqg_yoy",                     "niqg_yoy",                     "trqg_yoy",                     "eqg_effective",                     "eqg_factor_effective",                                                                            "rqg_effective",                     "rqg_factor_effective",                                                                            "price_to_earnings_to_growth_ratio",                     "effective_peg_ratio",                                                                           "annualized_cash_flow_from_operating_activities",                           "annualized_cash_flow_from_operating_activities_bonus",                      "quarterized_cash_flow_from_operating_activities",                           "quarterized_cash_flow_from_operating_activities_bonus",                      "annualized_ev_to_cfo_ratio",                     "quarterized_ev_to_cfo_ratio",                     "ev_to_cfo_ratio_effective",                                                                                 "annualized_debt_to_equity",                           "annualized_debt_to_equity_bonus",                      "quarterized_debt_to_equity",                           "quarterized_debt_to_equity_bonus",                      "debt_to_equity_effective",                     "debt_to_equity_effective_used",                                                                                     "financial_currency",                     "summary_currency",                     "financial_currency_conversion_rate_mult_to_usd",                     "summary_currency_conversion_rate_mult_to_usd",                     "last_dividend_0",                     "last_dividend_1",                     "last_dividend_2",                     "last_dividend_3",                     "fifty_two_week_change",                     "fifty_two_week_low",                     "fifty_two_week_high",                     "two_hundred_day_average",                     "previous_close_percentage_from_200d_ma",                     "previous_close_percentage_from_52w_low",                     "previous_close_percentage_from_52w_high",                     "dist_from_low_factor",                     "eff_dist_from_low_factor",                                                                                "annualized_total_ratio",                           "annualized_total_ratio_bonus",                      "quarterized_total_ratio",                           "quarterized_total_ratio_bonus",                      "annualized_other_current_ratio",                           "annualized_other_current_ratio_bonus",                      "quarterized_other_current_ratio",                           "quarterized_other_current_ratio_bonus",                      "annualized_other_ratio",                           "annualized_other_ratio_bonus",                      "quarterized_other_ratio",                           "quarterized_other_ratio_bonus",                      "annualized_total_current_ratio",                           "annualized_total_current_ratio_bonus",                                 "quarterized_total_current_ratio",                                      "quarterized_total_current_ratio_bonus",                      "total_ratio_effective",                      "other_current_ratio_effective",                     "other_ratio_effective",                     "total_current_ratio_effective",                     "effective_current_ratio",                                                                               "annualized_total_assets",                           "annualized_total_assets_bonus",                      "quarterized_total_assets",                           "quarterized_total_assets_bonus",                      "effective_total_assets",                     "annualized_total_stockholder_equity      ",                     "annualized_total_stockholder_equity_bonus",                      "quarterized_total_stockholder_equity",                           "quarterized_total_stockholder_equity_bonus",                      "effective_total_stockholder_equity",                     "calculated_roa",                                                                      "calculated_roe",                                                                      "annualized_working_capital",                     "quarterized_working_capital",                     "effective_working_capital",                     "annualized_total_liabilities",                           "annualized_total_liabilities_bonus",                      "quarterized_total_liabilities",                           "quarterized_total_liabilities_bonus",                      "effective_total_liabilities",                     "altman_z_score_factor",                                                                             "skip_reason"
    return [stock_data.symbol,            stock_data.short_name,            stock_data.sector,            stock_data.country,            stock_data.sss_value,                                                        stock_data.annualized_revenue,            float(stock_data.annualized_revenue_bonus),            stock_data.annualized_earnings,            stock_data.annualized_retained_earnings,            float(stock_data.annualized_retained_earnings_bonus),            stock_data.quarterized_revenue,            float(stock_data.quarterized_revenue_bonus),            stock_data.quarterized_earnings,            float(stock_data.quarterized_earnings_bonus),            stock_data.quarterized_retained_earnings,            float(stock_data.quarterized_retained_earnings_bonus),            stock_data.effective_earnings,            stock_data.effective_retained_earnings,            stock_data.effective_revenue,            stock_data.annualized_total_revenue,            float(stock_data.annualized_total_revenue_bonus),            stock_data.annualized_net_income,            stock_data.quarterized_total_revenue,            float(stock_data.quarterized_total_revenue_bonus),            stock_data.quarterized_net_income,            float(stock_data.quarterized_net_income_bonus),            stock_data.effective_net_income,            stock_data.effective_total_revenue,            stock_data.enterprise_value_to_revenue,            float(stock_data.evr_effective),                                                            stock_data.trailing_price_to_earnings,            stock_data.forward_price_to_earnings,            stock_data.effective_price_to_earnings,            stock_data.trailing_12months_price_to_sales,                                                                               stock_data.pe_effective,                                                           stock_data.enterprise_value_to_ebitda,            stock_data.effective_ev_to_ebitda,                                                                     stock_data.ebitda,            stock_data.quarterized_ebitd,            stock_data.annualized_ebitd,            stock_data.ebitd,            stock_data.profit_margin,            stock_data.annualized_profit_margin,            stock_data.annualized_profit_margin_boost,            stock_data.quarterized_profit_margin,            stock_data.quarterized_profit_margin_boost,            stock_data.effective_profit_margin,                                                                      stock_data.held_percent_institutions,            stock_data.held_percent_insiders,                                                                    stock_data.forward_eps,            stock_data.trailing_eps,            stock_data.previous_close,            stock_data.trailing_eps_percentage,            stock_data.price_to_book,                                                            stock_data.shares_outstanding,            stock_data.net_income_to_common_shareholders,            stock_data.nitcsh_to_shares_outstanding,            stock_data.employees,            stock_data.enterprise_value,            stock_data.market_cap,            stock_data.nitcsh_to_num_employees,            stock_data.eqg,            stock_data.rqg,            stock_data.eqg_yoy,            stock_data.rqg_yoy,            stock_data.niqg_yoy,            stock_data.trqg_yoy,            stock_data.eqg_effective,            stock_data.eqg_factor_effective,                                                                   stock_data.rqg_effective,            stock_data.rqg_factor_effective,                                                                   stock_data.price_to_earnings_to_growth_ratio,            stock_data.effective_peg_ratio,                                                                  stock_data.annualized_cash_flow_from_operating_activities,            float(stock_data.annualized_cash_flow_from_operating_activities_bonus),            stock_data.quarterized_cash_flow_from_operating_activities,            float(stock_data.quarterized_cash_flow_from_operating_activities_bonus),            stock_data.annualized_ev_to_cfo_ratio,            stock_data.quarterized_ev_to_cfo_ratio,            stock_data.ev_to_cfo_ratio_effective,                                                                        stock_data.annualized_debt_to_equity,            float(stock_data.annualized_debt_to_equity_bonus),            stock_data.quarterized_debt_to_equity,            float(stock_data.quarterized_debt_to_equity_bonus),            stock_data.debt_to_equity_effective,            stock_data.debt_to_equity_effective_used,                                                                            stock_data.financial_currency,            stock_data.summary_currency,            stock_data.financial_currency_conversion_rate_mult_to_usd,            stock_data.summary_currency_conversion_rate_mult_to_usd,            stock_data.last_dividend_0,            stock_data.last_dividend_1,            stock_data.last_dividend_2,            stock_data.last_dividend_3,            stock_data.fifty_two_week_change,            stock_data.fifty_two_week_low,            stock_data.fifty_two_week_high,            stock_data.two_hundred_day_average,            stock_data.previous_close_percentage_from_200d_ma,            stock_data.previous_close_percentage_from_52w_low,            stock_data.previous_close_percentage_from_52w_high,            stock_data.dist_from_low_factor,            stock_data.eff_dist_from_low_factor,                                                                       stock_data.annualized_total_ratio,            float(stock_data.annualized_total_ratio_bonus),            stock_data.quarterized_total_ratio,            float(stock_data.quarterized_total_ratio_bonus),            stock_data.annualized_other_current_ratio,            float(stock_data.annualized_other_current_ratio_bonus),            stock_data.quarterized_other_current_ratio,            float(stock_data.quarterized_other_current_ratio_bonus),            stock_data.annualized_other_ratio,            float(stock_data.annualized_other_ratio_bonus),            stock_data.quarterized_other_ratio,            float(stock_data.quarterized_other_ratio_bonus),            stock_data.annualized_total_current_ratio,            float(stock_data.annualized_total_current_ratio_bonus),                       stock_data.quarterized_total_current_ratio,                       float(stock_data.quarterized_total_current_ratio_bonus),            stock_data.total_ratio_effective,             stock_data.other_current_ratio_effective,            stock_data.other_ratio_effective,            stock_data.total_current_ratio_effective,            stock_data.effective_current_ratio,                                                                      stock_data.annualized_total_assets,            float(stock_data.annualized_total_assets_bonus),            stock_data.quarterized_total_assets,            float(stock_data.quarterized_total_assets_bonus),            stock_data.effective_total_assets,            stock_data.annualized_total_stockholder_equity,            float(stock_data.annualized_total_stockholder_equity_bonus),            stock_data.quarterized_total_stockholder_equity,            float(stock_data.quarterized_total_stockholder_equity_bonus),            stock_data.effective_total_stockholder_equity,            stock_data.calculated_roa,                                                             stock_data.calculated_roe,                                                             stock_data.annualized_working_capital,            stock_data.quarterized_working_capital,            stock_data.effective_working_capital,            stock_data.annualized_total_liabilities,            float(stock_data.annualized_total_liabilities_bonus),            stock_data.quarterized_total_liabilities,            float(stock_data.quarterized_total_liabilities_bonus),            stock_data.effective_total_liabilities,            stock_data.altman_z_score_factor,                                                                    stock_data.skip_reason]


def get_db_row_from_stock_data_normalized(           stock_data_normalized):
    return [stock_data_normalized.symbol, stock_data_normalized.short_name, stock_data_normalized.sector, stock_data_normalized.country, stock_data_normalized.sss_value, stock_data_normalized.sss_value_normalized, stock_data_normalized.annualized_revenue, float(stock_data_normalized.annualized_revenue_bonus), stock_data_normalized.annualized_earnings, stock_data_normalized.annualized_retained_earnings, float(stock_data_normalized.annualized_retained_earnings_bonus), stock_data_normalized.quarterized_revenue, float(stock_data_normalized.quarterized_revenue_bonus), stock_data_normalized.quarterized_earnings, float(stock_data_normalized.quarterized_earnings_bonus), stock_data_normalized.quarterized_retained_earnings, float(stock_data_normalized.quarterized_retained_earnings_bonus), stock_data_normalized.effective_earnings, stock_data_normalized.effective_retained_earnings, stock_data_normalized.effective_revenue, stock_data_normalized.annualized_total_revenue, float(stock_data_normalized.annualized_total_revenue_bonus), stock_data_normalized.annualized_net_income, stock_data_normalized.quarterized_total_revenue, float(stock_data_normalized.quarterized_total_revenue_bonus), stock_data_normalized.quarterized_net_income, float(stock_data_normalized.quarterized_net_income_bonus), stock_data_normalized.effective_net_income, stock_data_normalized.effective_total_revenue, stock_data_normalized.enterprise_value_to_revenue, float(stock_data_normalized.evr_effective), stock_data_normalized.evr_effective_normalized, stock_data_normalized.trailing_price_to_earnings, stock_data_normalized.forward_price_to_earnings, stock_data_normalized.effective_price_to_earnings, stock_data_normalized.trailing_12months_price_to_sales, stock_data_normalized.trailing_12months_price_to_sales_normalized, stock_data_normalized.pe_effective, stock_data_normalized.pe_effective_normalized, stock_data_normalized.enterprise_value_to_ebitda, stock_data_normalized.effective_ev_to_ebitda, stock_data_normalized.effective_ev_to_ebitda_normalized, stock_data_normalized.ebitda, stock_data_normalized.quarterized_ebitd, stock_data_normalized.annualized_ebitd, stock_data_normalized.ebitd, stock_data_normalized.profit_margin, stock_data_normalized.annualized_profit_margin, stock_data_normalized.annualized_profit_margin_boost, stock_data_normalized.quarterized_profit_margin, stock_data_normalized.quarterized_profit_margin_boost, stock_data_normalized.effective_profit_margin, stock_data_normalized.effective_profit_margin_normalized, stock_data_normalized.held_percent_institutions, stock_data_normalized.held_percent_insiders, stock_data_normalized.held_percent_insiders_normalized, stock_data_normalized.forward_eps, stock_data_normalized.trailing_eps, stock_data_normalized.previous_close, stock_data_normalized.trailing_eps_percentage, stock_data_normalized.price_to_book, stock_data_normalized.price_to_book_normalized, stock_data_normalized.shares_outstanding, stock_data_normalized.net_income_to_common_shareholders, stock_data_normalized.nitcsh_to_shares_outstanding, stock_data_normalized.employees, stock_data_normalized.enterprise_value, stock_data_normalized.market_cap, stock_data_normalized.nitcsh_to_num_employees, stock_data_normalized.eqg, stock_data_normalized.rqg, stock_data_normalized.eqg_yoy, stock_data_normalized.rqg_yoy, stock_data_normalized.niqg_yoy, stock_data_normalized.trqg_yoy, stock_data_normalized.eqg_effective, stock_data_normalized.eqg_factor_effective, stock_data_normalized.eqg_factor_effective_normalized, stock_data_normalized.rqg_effective, stock_data_normalized.rqg_factor_effective, stock_data_normalized.rqg_factor_effective_normalized, stock_data_normalized.price_to_earnings_to_growth_ratio, stock_data_normalized.effective_peg_ratio, stock_data_normalized.effective_peg_ratio_normalized, stock_data_normalized.annualized_cash_flow_from_operating_activities, float(stock_data_normalized.annualized_cash_flow_from_operating_activities_bonus), stock_data_normalized.quarterized_cash_flow_from_operating_activities, float(stock_data_normalized.quarterized_cash_flow_from_operating_activities_bonus), stock_data_normalized.annualized_ev_to_cfo_ratio, stock_data_normalized.quarterized_ev_to_cfo_ratio, stock_data_normalized.ev_to_cfo_ratio_effective, stock_data_normalized.ev_to_cfo_ratio_effective_normalized, stock_data_normalized.annualized_debt_to_equity, float(stock_data_normalized.annualized_debt_to_equity_bonus), stock_data_normalized.quarterized_debt_to_equity, float(stock_data_normalized.quarterized_debt_to_equity_bonus), stock_data_normalized.debt_to_equity_effective, stock_data_normalized.debt_to_equity_effective_used, stock_data_normalized.debt_to_equity_effective_used_normalized, stock_data_normalized.financial_currency, stock_data_normalized.summary_currency, stock_data_normalized.financial_currency_conversion_rate_mult_to_usd, stock_data_normalized.summary_currency_conversion_rate_mult_to_usd, stock_data_normalized.last_dividend_0, stock_data_normalized.last_dividend_1, stock_data_normalized.last_dividend_2, stock_data_normalized.last_dividend_3, stock_data_normalized.fifty_two_week_change, stock_data_normalized.fifty_two_week_low, stock_data_normalized.fifty_two_week_high, stock_data_normalized.two_hundred_day_average, stock_data_normalized.previous_close_percentage_from_200d_ma, stock_data_normalized.previous_close_percentage_from_52w_low, stock_data_normalized.previous_close_percentage_from_52w_high, stock_data_normalized.dist_from_low_factor, stock_data_normalized.eff_dist_from_low_factor, stock_data_normalized.eff_dist_from_low_factor_normalized, stock_data_normalized.annualized_total_ratio, float(stock_data_normalized.annualized_total_ratio_bonus), stock_data_normalized.quarterized_total_ratio, float(stock_data_normalized.quarterized_total_ratio_bonus), stock_data_normalized.annualized_other_current_ratio, float(stock_data_normalized.annualized_other_current_ratio_bonus), stock_data_normalized.quarterized_other_current_ratio, float(stock_data_normalized.quarterized_other_current_ratio_bonus), stock_data_normalized.annualized_other_ratio, float(stock_data_normalized.annualized_other_ratio_bonus), stock_data_normalized.quarterized_other_ratio, float(stock_data_normalized.quarterized_other_ratio_bonus), stock_data_normalized.annualized_total_current_ratio, float(stock_data_normalized.annualized_total_current_ratio_bonus), stock_data_normalized.quarterized_total_current_ratio,            float(stock_data_normalized.quarterized_total_current_ratio_bonus), stock_data_normalized.total_ratio_effective,  stock_data_normalized.other_current_ratio_effective, stock_data_normalized.other_ratio_effective, stock_data_normalized.total_current_ratio_effective, stock_data_normalized.effective_current_ratio, stock_data_normalized.effective_current_ratio_normalized, stock_data_normalized.annualized_total_assets, float(stock_data_normalized.annualized_total_assets_bonus), stock_data_normalized.quarterized_total_assets, float(stock_data_normalized.quarterized_total_assets_bonus), stock_data_normalized.effective_total_assets, stock_data_normalized.annualized_total_stockholder_equity, float(stock_data_normalized.annualized_total_stockholder_equity_bonus), stock_data_normalized.quarterized_total_stockholder_equity, float(stock_data_normalized.quarterized_total_stockholder_equity_bonus), stock_data_normalized.effective_total_stockholder_equity, stock_data_normalized.calculated_roa, stock_data_normalized.calculated_roa_normalized, stock_data_normalized.calculated_roe, stock_data_normalized.calculated_roe_normalized, stock_data_normalized.annualized_working_capital, stock_data_normalized.quarterized_working_capital, stock_data_normalized.effective_working_capital, stock_data_normalized.annualized_total_liabilities, float(stock_data_normalized.annualized_total_liabilities_bonus), stock_data_normalized.quarterized_total_liabilities, float(stock_data_normalized.quarterized_total_liabilities_bonus), stock_data_normalized.effective_total_liabilities, stock_data_normalized.altman_z_score_factor, stock_data_normalized.altman_z_score_factor_normalized, stock_data_normalized.skip_reason]


def get_stock_data_from_db_row(row, symbol=None):
    if symbol:
        stock_symbol = symbol
    else:
        stock_symbol = row[g_symbol_index]
    return StockData(symbol=stock_symbol, short_name=row[g_name_index],   sector=row[g_sector_index],   country=row[g_country_index],   sss_value=float(row[g_sss_value_index]   if row[g_sss_value_index]   != None else 0), annualized_revenue=float(row[g_annualized_revenue_index] if row[g_annualized_revenue_index] != None else 0), annualized_revenue_bonus=float(row[g_annualized_revenue_bonus_index] if row[g_annualized_revenue_bonus_index] != None else 0), annualized_earnings=float(row[g_annualized_earnings_index] if row[g_annualized_earnings_index] != None else 0), annualized_retained_earnings=float(row[g_annualized_retained_earnings_index] if row[g_annualized_retained_earnings_index] != None else 0), annualized_retained_earnings_bonus=float(row[g_annualized_retained_earnings_bonus_index] if row[g_annualized_retained_earnings_bonus_index] != None else 0), quarterized_revenue=float(row[g_quarterized_revenue_index] if row[g_quarterized_revenue_index] != None else 0), quarterized_revenue_bonus=float(row[g_quarterized_revenue_bonus_index] if row[g_quarterized_revenue_bonus_index] != None else 0), quarterized_earnings=float(row[g_quarterized_earnings_index] if row[g_quarterized_earnings_index] != None else 0), quarterized_earnings_bonus=float(row[g_quarterized_earnings_bonus_index] if row[g_quarterized_earnings_bonus_index] != None else 0), quarterized_retained_earnings=float(row[g_quarterized_retained_earnings_index] if row[g_quarterized_retained_earnings_index] != None else 0), quarterized_retained_earnings_bonus=float(row[g_quarterized_retained_earnings_bonus_index] if row[g_quarterized_retained_earnings_bonus_index] != None else 0), effective_earnings=float(row[g_effective_earnings_index] if row[g_effective_earnings_index] != None else 0), effective_retained_earnings=float(row[g_effective_retained_earnings_index] if row[g_effective_retained_earnings_index] != None else 0), effective_revenue=float(row[g_effective_revenue_index] if row[g_effective_revenue_index] != None else 0), annualized_total_revenue=float(row[g_annualized_total_revenue_index] if row[g_annualized_total_revenue_index] != None else 0), annualized_total_revenue_bonus=float(row[g_annualized_total_revenue_bonus_index] if row[g_annualized_total_revenue_bonus_index] != None else 0), annualized_net_income=float(row[g_annualized_net_income_index] if row[g_annualized_net_income_index] != None else 0), quarterized_total_revenue=float(row[g_quarterized_total_revenue_index] if row[g_quarterized_total_revenue_index] != None else 0), quarterized_total_revenue_bonus=float(row[g_quarterized_total_revenue_bonus_index] if row[g_quarterized_total_revenue_bonus_index] != None else 0), quarterized_net_income=float(row[g_quarterized_net_income_index] if row[g_quarterized_net_income_index] != None else 0), quarterized_net_income_bonus=float(row[g_quarterized_net_income_bonus_index] if row[g_quarterized_net_income_bonus_index] != None else 0), effective_net_income=float(row[g_effective_net_income_index] if row[g_effective_net_income_index] != None else 0), effective_total_revenue=float(row[g_effective_total_revenue_index] if row[g_effective_total_revenue_index] != None else 0), enterprise_value_to_revenue=float(row[g_enterprise_value_to_revenue_index] if row[g_enterprise_value_to_revenue_index] != None else 0), evr_effective=float(row[g_evr_effective_index] if row[g_evr_effective_index] != None else 0), trailing_price_to_earnings=float(row[g_trailing_price_to_earnings_index] if row[g_trailing_price_to_earnings_index] != None else 0), forward_price_to_earnings=float(row[g_forward_price_to_earnings_index] if row[g_forward_price_to_earnings_index] != None else 0), effective_price_to_earnings=float(row[g_effective_price_to_earnings_index] if row[g_effective_price_to_earnings_index] != None else 0), trailing_12months_price_to_sales=float(row[g_trailing_12months_price_to_sales_index] if row[g_trailing_12months_price_to_sales_index] != None else 0), pe_effective=float(row[g_pe_effective_index] if row[g_pe_effective_index] != None else 0), enterprise_value_to_ebitda=float(row[g_enterprise_value_to_ebitda_index] if row[g_enterprise_value_to_ebitda_index] != None else 0), effective_ev_to_ebitda=float(row[g_effective_ev_to_ebitda_index] if row[g_effective_ev_to_ebitda_index] != None else 0), ebitda=float(row[g_ebitda_index] if row[g_ebitd_index] != None else 0), quarterized_ebitd=float(row[g_quarterized_ebitd_index] if row[g_quarterized_ebitd_index] != None else 0), annualized_ebitd=float(row[g_annualized_ebitd_index] if row[g_annualized_ebitd_index] != None else 0), ebitd=float(row[g_ebitd_index] if row[g_ebitd_index] != None else 0), profit_margin=float(row[g_profit_margin_index] if row[g_profit_margin_index] != None else 0), annualized_profit_margin=float(row[g_annualized_profit_margin_index] if row[g_annualized_profit_margin_index] != None else 0), annualized_profit_margin_boost=float(row[g_annualized_profit_margin_boost_index] if row[g_annualized_profit_margin_boost_index] != None else 0), quarterized_profit_margin=float(row[g_quarterized_profit_margin_index] if row[g_quarterized_profit_margin_index] != None else 0), quarterized_profit_margin_boost=float(row[g_quarterized_profit_margin_boost_index] if row[g_quarterized_profit_margin_boost_index] != None else 0), effective_profit_margin=float(row[g_effective_profit_margin_index] if row[g_effective_profit_margin_index] != None else 0), held_percent_institutions=float(row[g_held_percent_institutions_index] if row[g_held_percent_institutions_index] != None else 0), held_percent_insiders=float(row[g_held_percent_insiders_index] if row[g_held_percent_insiders_index] != None else 0), forward_eps=float(row[g_forward_eps_index] if row[g_forward_eps_index] != None else 0), trailing_eps=float(row[g_trailing_eps_index] if row[g_trailing_eps_index] != None else 0), previous_close=float(row[g_previous_close_index] if row[g_previous_close_index] != None else 0), trailing_eps_percentage=float(row[g_trailing_eps_percentage_index] if row[g_trailing_eps_percentage_index] != None else 0), price_to_book=float(row[g_price_to_book_index] if row[g_price_to_book_index] != None else 0), shares_outstanding=float(row[g_shares_outstanding_index] if row[g_shares_outstanding_index] != None else 0), net_income_to_common_shareholders=float(row[g_net_income_to_common_shareholders_index] if row[g_net_income_to_common_shareholders_index] != None else 0), nitcsh_to_shares_outstanding=float(row[g_nitcsh_to_shares_outstanding_index] if row[g_nitcsh_to_shares_outstanding_index] != None else 0), employees=int(float(row[g_employees_index] if row[g_employees_index] != None else 0)), enterprise_value=int(float(row[g_enterprise_value_index] if row[g_enterprise_value_index] != None else 0)), market_cap=int(float(row[g_market_cap_index] if row[g_market_cap_index] != None else 0)), nitcsh_to_num_employees=float(row[g_nitcsh_to_num_employees_index] if row[g_nitcsh_to_num_employees_index] != None else 0), eqg=float(row[g_eqg_index] if row[g_eqg_index] != None else 0), rqg=float(row[g_rqg_index] if row[g_rqg_index] != None else 0), eqg_yoy=float(row[g_eqg_yoy_index] if row[g_eqg_yoy_index] != None else 0), rqg_yoy=float(row[g_rqg_yoy_index] if row[g_rqg_yoy_index] != None else 0), niqg_yoy=float(row[g_niqg_yoy_index] if row[g_niqg_yoy_index] != None else 0), trqg_yoy=float(row[g_trqg_yoy_index] if row[g_trqg_yoy_index] != None else 0), eqg_effective=float(row[g_eqg_effective_index] if row[g_eqg_effective_index] != None else 0), eqg_factor_effective=float(row[g_eqg_factor_effective_index] if row[g_eqg_factor_effective_index] != None else 0), rqg_effective=float(row[g_rqg_effective_index] if row[g_rqg_effective_index] != None else 0), rqg_factor_effective=float(row[g_rqg_factor_effective_index] if row[g_rqg_factor_effective_index] != None else 0), price_to_earnings_to_growth_ratio=float(row[g_price_to_earnings_to_growth_ratio_index] if row[g_price_to_earnings_to_growth_ratio_index] != None else 0), effective_peg_ratio=float(row[g_effective_peg_ratio_index] if row[g_effective_peg_ratio_index] != None else 0), annualized_cash_flow_from_operating_activities=float(row[g_annualized_cash_flow_from_operating_activities_index] if row[g_annualized_cash_flow_from_operating_activities_index] != None else 0), annualized_cash_flow_from_operating_activities_bonus=float(row[g_annualized_cash_flow_from_operating_activities_bonus_index] if row[g_annualized_cash_flow_from_operating_activities_bonus_index] != None else 0), quarterized_cash_flow_from_operating_activities=float(row[g_quarterized_cash_flow_from_operating_activities_index] if row[g_quarterized_cash_flow_from_operating_activities_index] != None else 0), quarterized_cash_flow_from_operating_activities_bonus=float(row[g_quarterized_cash_flow_from_operating_activities_bonus_index] if row[g_quarterized_cash_flow_from_operating_activities_bonus_index] != None else 0), annualized_ev_to_cfo_ratio=float(row[g_annualized_ev_to_cfo_ratio_index] if row[g_annualized_ev_to_cfo_ratio_index] != None else 0), quarterized_ev_to_cfo_ratio=float(row[g_quarterized_ev_to_cfo_ratio_index] if row[g_quarterized_ev_to_cfo_ratio_index] != None else 0), ev_to_cfo_ratio_effective=float(row[g_ev_to_cfo_ratio_effective_index] if row[g_ev_to_cfo_ratio_effective_index] != None else 0), annualized_debt_to_equity=float(row[g_annualized_debt_to_equity_index] if row[g_annualized_debt_to_equity_index] != None else 0), annualized_debt_to_equity_bonus=float(row[g_annualized_debt_to_equity_bonus_index] if row[g_annualized_debt_to_equity_bonus_index] != None else 0), quarterized_debt_to_equity=float(row[g_quarterized_debt_to_equity_index] if row[g_quarterized_debt_to_equity_index] != None else 0), quarterized_debt_to_equity_bonus=float(row[g_quarterized_debt_to_equity_bonus_index] if row[g_quarterized_debt_to_equity_bonus_index] != None else 0), debt_to_equity_effective=float(row[g_debt_to_equity_effective_index] if row[g_debt_to_equity_effective_index] != None else 0), debt_to_equity_effective_used=float(row[g_debt_to_equity_effective_used_index] if row[g_debt_to_equity_effective_used_index] != None else 0), financial_currency=row[g_financial_currency_index], summary_currency=row[g_summary_currency_index], financial_currency_conversion_rate_mult_to_usd=float(row[g_financial_currency_conversion_rate_mult_to_usd_index] if row[g_financial_currency_conversion_rate_mult_to_usd_index] != None else 0), summary_currency_conversion_rate_mult_to_usd=float(row[g_summary_currency_conversion_rate_mult_to_usd_index] if row[g_summary_currency_conversion_rate_mult_to_usd_index] != None else 0), last_dividend_0=float(row[g_last_dividend_0_index] if row[g_last_dividend_0_index] != None else 0), last_dividend_1=float(row[g_last_dividend_1_index] if row[g_last_dividend_1_index] != None else 0), last_dividend_2=float(row[g_last_dividend_2_index] if row[g_last_dividend_2_index] != None else 0), last_dividend_3=float(row[g_last_dividend_3_index] if row[g_last_dividend_3_index] != None else 0), fifty_two_week_change=float(row[g_fifty_two_week_change_index] if row[g_fifty_two_week_change_index] != None else 0), fifty_two_week_low=float(row[g_fifty_two_week_low_index] if row[g_fifty_two_week_low_index] != None else 0), fifty_two_week_high=float(row[g_fifty_two_week_high_index] if row[g_fifty_two_week_high_index] != None else 0), two_hundred_day_average=float(row[g_two_hundred_day_average_index] if row[g_two_hundred_day_average_index] != None else 0), previous_close_percentage_from_200d_ma=float(row[g_previous_close_percentage_from_200d_ma_index] if row[g_previous_close_percentage_from_200d_ma_index] != None else 0), previous_close_percentage_from_52w_low=float(row[g_previous_close_percentage_from_52w_low_index] if row[g_previous_close_percentage_from_52w_low_index] != None else 0), previous_close_percentage_from_52w_high=float(row[g_previous_close_percentage_from_52w_high_index] if row[g_previous_close_percentage_from_52w_high_index] != None else 0), dist_from_low_factor=float(row[g_dist_from_low_factor_index] if row[g_dist_from_low_factor_index] != None else 0), eff_dist_from_low_factor=float(row[g_eff_dist_from_low_factor_index] if row[g_eff_dist_from_low_factor_index] != None else 0), annualized_total_ratio=float(row[g_annualized_total_ratio_index] if row[g_annualized_total_ratio_index] != None else 0), annualized_total_ratio_bonus=float(row[g_annualized_total_ratio_bonus_index] if row[g_annualized_total_ratio_bonus_index] != None else 0), quarterized_total_ratio=float(row[g_quarterized_total_ratio_index] if row[g_quarterized_total_ratio_index] != None else 0), quarterized_total_ratio_bonus=float(row[g_quarterized_total_ratio_bonus_index] if row[g_quarterized_total_ratio_bonus_index] != None else 0), annualized_other_current_ratio=float(row[g_annualized_other_current_ratio_index] if row[g_annualized_other_current_ratio_index] != None else 0), annualized_other_current_ratio_bonus=float(row[g_annualized_other_current_ratio_bonus_index] if row[g_annualized_other_current_ratio_bonus_index] != None else 0), quarterized_other_current_ratio=float(row[g_quarterized_other_current_ratio_index] if row[g_quarterized_other_current_ratio_index] != None else 0), quarterized_other_current_ratio_bonus=float(row[g_quarterized_other_current_ratio_bonus_index] if row[g_quarterized_other_current_ratio_bonus_index] != None else 0), annualized_other_ratio=float(row[g_annualized_other_ratio_index] if row[g_annualized_other_ratio_index] != None else 0), annualized_other_ratio_bonus=float(row[g_annualized_other_ratio_bonus_index] if row[g_annualized_other_ratio_bonus_index] != None else 0), quarterized_other_ratio=float(row[g_quarterized_other_ratio_index] if row[g_quarterized_other_ratio_index] != None else 0), quarterized_other_ratio_bonus=float(row[g_quarterized_other_ratio_bonus_index] if row[g_quarterized_other_ratio_bonus_index] != None else 0), annualized_total_current_ratio=float(row[g_annualized_total_current_ratio_index] if row[g_annualized_total_current_ratio_index] != None else 0), quarterized_total_current_ratio=float(row[g_quarterized_total_current_ratio_index] if row[g_quarterized_total_current_ratio_index] != None else 0), total_ratio_effective=float(row[g_total_ratio_effective_index] if row[g_total_ratio_effective_index] != None else 0), other_current_ratio_effective=float(row[g_other_current_ratio_effective_index] if row[g_other_current_ratio_effective_index] != None else 0), other_ratio_effective=float(row[g_other_ratio_effective_index] if row[g_other_ratio_effective_index] != None else 0), total_current_ratio_effective=float(row[g_total_current_ratio_effective_index] if row[g_total_current_ratio_effective_index] != None else 0), effective_current_ratio=float(row[g_effective_current_ratio_index] if row[g_effective_current_ratio_index] != None else 0), annualized_total_assets=float(row[g_annualized_total_assets_index] if row[g_annualized_total_assets_index] != None else 0), annualized_total_assets_bonus=float(row[g_annualized_total_assets_bonus_index] if row[g_annualized_total_assets_bonus_index] != None else 0), quarterized_total_assets=float(row[g_quarterized_total_assets_index] if row[g_quarterized_total_assets_index] != None else 0), quarterized_total_assets_bonus=float(row[g_quarterized_total_assets_bonus_index] if row[g_quarterized_total_assets_bonus_index] != None else 0), effective_total_assets=float(row[g_effective_total_assets_index] if row[g_effective_total_assets_index] != None else 0), annualized_total_stockholder_equity=float(row[g_annualized_total_stockholder_equity_index] if row[g_annualized_total_stockholder_equity_index] != None else 0), annualized_total_stockholder_equity_bonus=float(row[g_annualized_total_stockholder_equity_bonus_index] if row[g_annualized_total_stockholder_equity_bonus_index] != None else 0), quarterized_total_stockholder_equity=float(row[g_quarterized_total_stockholder_equity_index] if row[g_quarterized_total_stockholder_equity_index] != None else 0), quarterized_total_stockholder_equity_bonus=float(row[g_quarterized_total_stockholder_equity_bonus_index] if row[g_quarterized_total_stockholder_equity_bonus_index] != None else 0), effective_total_stockholder_equity=float(row[g_effective_total_stockholder_equity_index] if row[g_effective_total_stockholder_equity_index] != None else 0), calculated_roa=float(row[g_calculated_roa_index] if row[g_calculated_roa_index] != None else 0), calculated_roe=float(row[g_calculated_roe_index] if row[g_calculated_roe_index] != None else 0), annualized_working_capital=float(row[g_annualized_working_capital_index] if row[g_annualized_working_capital_index] != None else 0), quarterized_working_capital=float(row[g_quarterized_working_capital_index] if row[g_quarterized_working_capital_index] != None else 0), effective_working_capital=float(row[g_effective_working_capital_index] if row[g_effective_working_capital_index] != None else 0), annualized_total_liabilities=float(row[g_annualized_total_liabilities_index] if row[g_annualized_total_liabilities_index] != None else 0), annualized_total_liabilities_bonus=float(row[g_annualized_total_liabilities_bonus_index] if row[g_annualized_total_liabilities_bonus_index] != None else 0), quarterized_total_liabilities=float(row[g_quarterized_total_liabilities_index] if row[g_quarterized_total_liabilities_index] != None else 0), quarterized_total_liabilities_bonus=float(row[g_quarterized_total_liabilities_bonus_index] if row[g_quarterized_total_liabilities_bonus_index] != None else 0), effective_total_liabilities=float(row[g_effective_total_liabilities_index] if row[g_effective_total_liabilities_index] != None else 0), altman_z_score_factor=float(row[g_altman_z_score_factor_index] if row[g_altman_z_score_factor_index] != None else 0), skip_reason=row[g_skip_reason_index])


# Get only the required values necessary for the research mode (i.e. the core equation values)
def get_stock_data_from_db_row_compact(row, stock_symbol):
    return StockData(symbol=stock_symbol, short_name=row[g_name_index],   sector=row[g_sector_index],   country=row[g_country_index],   sss_value=float(row[g_sss_value_index]), evr_effective=float(row[g_evr_effective_index]), effective_price_to_earnings=float(row[g_effective_price_to_earnings_index]), trailing_12months_price_to_sales=float(row[g_trailing_12months_price_to_sales_index]), pe_effective=float(row[g_pe_effective_index]), effective_ev_to_ebitda=float(row[g_effective_ev_to_ebitda_index]), effective_profit_margin=float(row[g_effective_profit_margin_index]), held_percent_insiders=float(row[g_held_percent_insiders_index]), previous_close=float(row[g_previous_close_index]), price_to_book=float(row[g_price_to_book_index]), enterprise_value=int(float(row[g_enterprise_value_index])), eqg_factor_effective=float(row[g_eqg_factor_effective_index]), rqg_factor_effective=float(row[g_rqg_factor_effective_index]), effective_peg_ratio=float(row[g_effective_peg_ratio_index]), ev_to_cfo_ratio_effective=float(row[g_ev_to_cfo_ratio_effective_index]), debt_to_equity_effective=float(row[g_debt_to_equity_effective_index]), debt_to_equity_effective_used=float(row[g_debt_to_equity_effective_used_index]), eff_dist_from_low_factor=float(row[g_eff_dist_from_low_factor_index]), total_ratio_effective=float(row[g_total_ratio_effective_index]), total_current_ratio_effective=float(row[g_total_current_ratio_effective_index]), effective_current_ratio=float(row[g_effective_current_ratio_index]), calculated_roa=float(row[g_calculated_roa_index]), calculated_roe=float(row[g_calculated_roe_index]), altman_z_score_factor=float(row[g_altman_z_score_factor_index]))


def get_stock_data_normalized_from_db_row(row, symbol=None):
    if symbol:
        stock_symbol = symbol
    else:
        stock_symbol = row[g_symbol_index_n]
    return StockDataNormalized(symbol=stock_symbol, short_name=row[g_name_index_n], sector=row[g_sector_index_n], country=row[g_country_index_n], sss_value=float(row[g_sss_value_index_n] if row[g_sss_value_index_n] != None else 0), sss_value_normalized=float(row[g_sss_value_normalized_index_n] if row[g_sss_value_normalized_index_n] != None else 0), annualized_revenue=float(row[g_annualized_revenue_index_n] if row[g_annualized_revenue_index_n] != None else 0), annualized_revenue_bonus=float(row[g_annualized_revenue_bonus_index_n] if row[g_annualized_revenue_bonus_index_n] != None else 0), annualized_earnings=float(row[g_annualized_earnings_index_n] if row[g_annualized_earnings_index_n] != None else 0), annualized_retained_earnings=float(row[g_annualized_retained_earnings_index_n] if row[g_annualized_retained_earnings_index_n] != None else 0), annualized_retained_earnings_bonus=float(row[g_annualized_retained_earnings_bonus_index_n] if row[g_annualized_retained_earnings_bonus_index_n] != None else 0), quarterized_revenue=float(row[g_quarterized_revenue_index_n] if row[g_quarterized_revenue_index_n] != None else 0), quarterized_revenue_bonus=float(row[g_quarterized_revenue_bonus_index_n] if row[g_quarterized_revenue_bonus_index_n] != None else 0), quarterized_earnings=float(row[g_quarterized_earnings_index_n] if row[g_quarterized_earnings_index_n] != None else 0), quarterized_earnings_bonus=float(row[g_quarterized_earnings_bonus_index_n] if row[g_quarterized_earnings_bonus_index_n] != None else 0), quarterized_retained_earnings=float(row[g_quarterized_retained_earnings_index_n] if row[g_quarterized_retained_earnings_index_n] != None else 0), quarterized_retained_earnings_bonus=float(row[g_quarterized_retained_earnings_bonus_index_n] if row[g_quarterized_retained_earnings_bonus_index_n] != None else 0), effective_earnings=float(row[g_effective_earnings_index_n] if row[g_effective_earnings_index_n] != None else 0), effective_retained_earnings=float(row[g_effective_retained_earnings_index_n] if row[g_effective_retained_earnings_index_n] != None else 0), effective_revenue=float(row[g_effective_revenue_index_n] if row[g_effective_revenue_index_n] != None else 0), annualized_total_revenue=float(row[g_annualized_total_revenue_index_n] if row[g_annualized_total_revenue_index_n] != None else 0), annualized_total_revenue_bonus=float(row[g_annualized_total_revenue_bonus_index_n] if row[g_annualized_total_revenue_bonus_index_n] != None else 0), annualized_net_income=float(row[g_annualized_net_income_index_n] if row[g_annualized_net_income_index_n] != None else 0), quarterized_total_revenue=float(row[g_quarterized_total_revenue_index_n] if row[g_quarterized_total_revenue_index_n] != None else 0), quarterized_total_revenue_bonus=float(row[g_quarterized_total_revenue_bonus_index_n] if row[g_quarterized_total_revenue_bonus_index_n] != None else 0), quarterized_net_income=float(row[g_quarterized_net_income_index_n] if row[g_quarterized_net_income_index_n] != None else 0), quarterized_net_income_bonus=float(row[g_quarterized_net_income_bonus_index_n] if row[g_quarterized_net_income_bonus_index_n] != None else 0), effective_net_income=float(row[g_effective_net_income_index_n] if row[g_effective_net_income_index_n] != None else 0), effective_total_revenue=float(row[g_effective_total_revenue_index_n] if row[g_effective_total_revenue_index_n] != None else 0), enterprise_value_to_revenue=float(row[g_enterprise_value_to_revenue_index_n] if row[g_enterprise_value_to_revenue_index_n] != None else 0), evr_effective=float(row[g_evr_effective_index_n] if row[g_evr_effective_index_n] != None else 0), evr_effective_normalized=float(row[g_evr_effective_normalized_index_n] if row[g_evr_effective_normalized_index_n] != None else 0), trailing_price_to_earnings=float(row[g_trailing_price_to_earnings_index_n] if row[g_trailing_price_to_earnings_index_n] != None else 0), forward_price_to_earnings=float(row[g_forward_price_to_earnings_index_n] if row[g_forward_price_to_earnings_index_n] != None else 0), effective_price_to_earnings=float(row[g_effective_price_to_earnings_index_n] if row[g_effective_price_to_earnings_index_n] != None else 0), trailing_12months_price_to_sales=float(row[g_trailing_12months_price_to_sales_index_n] if row[g_trailing_12months_price_to_sales_index_n] != None else 0), trailing_12months_price_to_sales_normalized=float(row[g_trailing_12months_price_to_sales_normalized_index_n] if row[g_trailing_12months_price_to_sales_normalized_index_n] != None else 0), pe_effective=float(row[g_pe_effective_index_n] if row[g_pe_effective_index_n] != None else 0), pe_effective_normalized=float(row[g_pe_effective_normalized_index_n] if row[g_pe_effective_normalized_index_n] != None else 0), enterprise_value_to_ebitda=float(row[g_enterprise_value_to_ebitda_index_n] if row[g_enterprise_value_to_ebitda_index_n] != None else 0), effective_ev_to_ebitda=float(row[g_effective_ev_to_ebitda_index_n] if row[g_effective_ev_to_ebitda_index_n] != None else 0), effective_ev_to_ebitda_normalized=float(row[g_effective_ev_to_ebitda_normalized_index_n] if row[g_effective_ev_to_ebitda_normalized_index_n] != None else 0), ebitda=float(row[g_ebitda_index_n] if row[g_ebitd_index_n] != None else 0), quarterized_ebitd=float(row[g_quarterized_ebitd_index_n] if row[g_quarterized_ebitd_index_n] != None else 0), annualized_ebitd=float(row[g_annualized_ebitd_index_n] if row[g_annualized_ebitd_index_n] != None else 0), ebitd=float(row[g_ebitd_index_n] if row[g_ebitd_index_n] != None else 0), profit_margin=float(row[g_profit_margin_index_n] if row[g_profit_margin_index_n] != None else 0), annualized_profit_margin=float(row[g_annualized_profit_margin_index_n] if row[g_annualized_profit_margin_index_n] != None else 0), annualized_profit_margin_boost=float(row[g_annualized_profit_margin_boost_index_n] if row[g_annualized_profit_margin_boost_index_n] != None else 0), quarterized_profit_margin=float(row[g_quarterized_profit_margin_index_n] if row[g_quarterized_profit_margin_index_n] != None else 0), quarterized_profit_margin_boost=float(row[g_quarterized_profit_margin_boost_index_n] if row[g_quarterized_profit_margin_boost_index_n] != None else 0), effective_profit_margin=float(row[g_effective_profit_margin_index_n] if row[g_effective_profit_margin_index_n] != None else 0), effective_profit_margin_normalized=float(row[g_effective_profit_margin_normalized_index_n] if row[g_effective_profit_margin_normalized_index_n] != None else 0), held_percent_institutions=float(row[g_held_percent_institutions_index_n] if row[g_held_percent_institutions_index_n] != None else 0), held_percent_insiders=float(row[g_held_percent_insiders_index_n] if row[g_held_percent_insiders_index_n] != None else 0), held_percent_insiders_normalized=float(row[g_held_percent_insiders_normalized_index_n] if row[g_held_percent_insiders_normalized_index_n] != None else 0), forward_eps=float(row[g_forward_eps_index_n] if row[g_forward_eps_index_n] != None else 0), trailing_eps=float(row[g_trailing_eps_index_n] if row[g_trailing_eps_index_n] != None else 0), previous_close=float(row[g_previous_close_index_n] if row[g_previous_close_index_n] != None else 0), trailing_eps_percentage=float(row[g_trailing_eps_percentage_index_n] if row[g_trailing_eps_percentage_index_n] != None else 0), price_to_book=float(row[g_price_to_book_index_n] if row[g_price_to_book_index_n] != None else 0), price_to_book_normalized=float(row[g_price_to_book_normalized_index_n] if row[g_price_to_book_normalized_index_n] != None else 0), shares_outstanding=float(row[g_shares_outstanding_index_n] if row[g_shares_outstanding_index_n] != None else 0), net_income_to_common_shareholders=float(row[g_net_income_to_common_shareholders_index_n] if row[g_net_income_to_common_shareholders_index_n] != None else 0), nitcsh_to_shares_outstanding=float(row[g_nitcsh_to_shares_outstanding_index_n] if row[g_nitcsh_to_shares_outstanding_index_n] != None else 0), employees=int(float(row[g_employees_index_n] if row[g_employees_index_n] != None else 0)), enterprise_value=int(float(row[g_enterprise_value_index_n] if row[g_enterprise_value_index_n] != None else 0)), market_cap=int(float(row[g_market_cap_index_n] if row[g_market_cap_index_n] != None else 0)), nitcsh_to_num_employees=float(row[g_nitcsh_to_num_employees_index_n] if row[g_nitcsh_to_num_employees_index_n] != None else 0), eqg=float(row[g_eqg_index_n] if row[g_eqg_index_n] != None else 0), rqg=float(row[g_rqg_index_n] if row[g_rqg_index_n] != None else 0), eqg_yoy=float(row[g_eqg_yoy_index_n] if row[g_eqg_yoy_index_n] != None else 0), rqg_yoy=float(row[g_rqg_yoy_index_n] if row[g_rqg_yoy_index_n] != None else 0), niqg_yoy=float(row[g_niqg_yoy_index_n] if row[g_niqg_yoy_index_n] != None else 0), trqg_yoy=float(row[g_trqg_yoy_index_n] if row[g_trqg_yoy_index_n] != None else 0), eqg_effective=float(row[g_eqg_effective_index_n] if row[g_eqg_effective_index_n] != None else 0), eqg_factor_effective=float(row[g_eqg_factor_effective_index_n] if row[g_eqg_factor_effective_index_n] != None else 0), eqg_factor_effective_normalized=float(row[g_eqg_factor_effective_normalized_index_n] if row[g_eqg_factor_effective_normalized_index_n] != None else 0), rqg_effective=float(row[g_rqg_effective_index_n] if row[g_rqg_effective_index_n] != None else 0), rqg_factor_effective=float(row[g_rqg_factor_effective_index_n] if row[g_rqg_factor_effective_index_n] != None else 0), rqg_factor_effective_normalized=float(row[g_rqg_factor_effective_normalized_index_n] if row[g_rqg_factor_effective_normalized_index_n] != None else 0), price_to_earnings_to_growth_ratio=float(row[g_price_to_earnings_to_growth_ratio_index_n] if row[g_price_to_earnings_to_growth_ratio_index_n] != None else 0), effective_peg_ratio=float(row[g_effective_peg_ratio_index_n] if row[g_effective_peg_ratio_index_n] != None else 0), effective_peg_ratio_normalized=float(row[g_effective_peg_ratio_normalized_index_n] if row[g_effective_peg_ratio_normalized_index_n] != None else 0), annualized_cash_flow_from_operating_activities=float(row[g_annualized_cash_flow_from_operating_activities_index_n] if row[g_annualized_cash_flow_from_operating_activities_index_n] != None else 0), annualized_cash_flow_from_operating_activities_bonus=float(row[g_annualized_cash_flow_from_operating_activities_bonus_index_n] if row[g_annualized_cash_flow_from_operating_activities_bonus_index_n] != None else 0), quarterized_cash_flow_from_operating_activities=float(row[g_quarterized_cash_flow_from_operating_activities_index_n] if row[g_quarterized_cash_flow_from_operating_activities_index_n] != None else 0), quarterized_cash_flow_from_operating_activities_bonus=float(row[g_quarterized_cash_flow_from_operating_activities_bonus_index_n] if row[g_quarterized_cash_flow_from_operating_activities_bonus_index_n] != None else 0), annualized_ev_to_cfo_ratio=float(row[g_annualized_ev_to_cfo_ratio_index_n] if row[g_annualized_ev_to_cfo_ratio_index_n] != None else 0), quarterized_ev_to_cfo_ratio=float(row[g_quarterized_ev_to_cfo_ratio_index_n] if row[g_quarterized_ev_to_cfo_ratio_index_n] != None else 0), ev_to_cfo_ratio_effective=float(row[g_ev_to_cfo_ratio_effective_index_n] if row[g_ev_to_cfo_ratio_effective_index_n] != None else 0), ev_to_cfo_ratio_effective_normalized=float(row[g_ev_to_cfo_ratio_effective_normalized_index_n] if row[g_ev_to_cfo_ratio_effective_normalized_index_n] != None else 0), annualized_debt_to_equity=float(row[g_annualized_debt_to_equity_index_n] if row[g_annualized_debt_to_equity_index_n] != None else 0), annualized_debt_to_equity_bonus=float(row[g_annualized_debt_to_equity_bonus_index_n] if row[g_annualized_debt_to_equity_bonus_index_n] != None else 0), quarterized_debt_to_equity=float(row[g_quarterized_debt_to_equity_index_n] if row[g_quarterized_debt_to_equity_index_n] != None else 0), quarterized_debt_to_equity_bonus=float(row[g_quarterized_debt_to_equity_bonus_index_n] if row[g_quarterized_debt_to_equity_bonus_index_n] != None else 0), debt_to_equity_effective=float(row[g_debt_to_equity_effective_index_n] if row[g_debt_to_equity_effective_index_n] != None else 0), debt_to_equity_effective_used=float(row[g_debt_to_equity_effective_used_index_n] if row[g_debt_to_equity_effective_used_index_n] != None else 0), debt_to_equity_effective_used_normalized=float(row[g_debt_to_equity_effective_used_normalized_index_n] if row[g_debt_to_equity_effective_used_normalized_index_n] != None else 0), financial_currency=row[g_financial_currency_index_n], summary_currency=row[g_summary_currency_index_n], financial_currency_conversion_rate_mult_to_usd=float(row[g_financial_currency_conversion_rate_mult_to_usd_index_n] if row[g_financial_currency_conversion_rate_mult_to_usd_index_n] != None else 0), summary_currency_conversion_rate_mult_to_usd=float(row[g_summary_currency_conversion_rate_mult_to_usd_index_n] if row[g_summary_currency_conversion_rate_mult_to_usd_index_n] != None else 0), last_dividend_0=float(row[g_last_dividend_0_index_n] if row[g_last_dividend_0_index_n] != None else 0), last_dividend_1=float(row[g_last_dividend_1_index_n] if row[g_last_dividend_1_index_n] != None else 0), last_dividend_2=float(row[g_last_dividend_2_index_n] if row[g_last_dividend_2_index_n] != None else 0), last_dividend_3=float(row[g_last_dividend_3_index_n] if row[g_last_dividend_3_index_n] != None else 0), fifty_two_week_change=float(row[g_fifty_two_week_change_index_n] if row[g_fifty_two_week_change_index_n] != None else 0), fifty_two_week_low=float(row[g_fifty_two_week_low_index_n] if row[g_fifty_two_week_low_index_n] != None else 0), fifty_two_week_high=float(row[g_fifty_two_week_high_index_n] if row[g_fifty_two_week_high_index_n] != None else 0), two_hundred_day_average=float(row[g_two_hundred_day_average_index_n] if row[g_two_hundred_day_average_index_n] != None else 0), previous_close_percentage_from_200d_ma=float(row[g_previous_close_percentage_from_200d_ma_index_n] if row[g_previous_close_percentage_from_200d_ma_index_n] != None else 0), previous_close_percentage_from_52w_low=float(row[g_previous_close_percentage_from_52w_low_index_n] if row[g_previous_close_percentage_from_52w_low_index_n] != None else 0), previous_close_percentage_from_52w_high=float(row[g_previous_close_percentage_from_52w_high_index_n] if row[g_previous_close_percentage_from_52w_high_index_n] != None else 0), dist_from_low_factor=float(row[g_dist_from_low_factor_index_n] if row[g_dist_from_low_factor_index_n] != None else 0), eff_dist_from_low_factor=float(row[g_eff_dist_from_low_factor_index_n] if row[g_eff_dist_from_low_factor_index_n] != None else 0), eff_dist_from_low_factor_normalized=float(row[g_eff_dist_from_low_factor_normalized_index_n] if row[g_eff_dist_from_low_factor_normalized_index_n] != None else 0), annualized_total_ratio=float(row[g_annualized_total_ratio_index_n] if row[g_annualized_total_ratio_index_n] != None else 0), annualized_total_ratio_bonus=float(row[g_annualized_total_ratio_bonus_index_n] if row[g_annualized_total_ratio_bonus_index_n] != None else 0), quarterized_total_ratio=float(row[g_quarterized_total_ratio_index_n] if row[g_quarterized_total_ratio_index_n] != None else 0), quarterized_total_ratio_bonus=float(row[g_quarterized_total_ratio_bonus_index_n] if row[g_quarterized_total_ratio_bonus_index_n] != None else 0), annualized_other_current_ratio=float(row[g_annualized_other_current_ratio_index_n] if row[g_annualized_other_current_ratio_index_n] != None else 0), annualized_other_current_ratio_bonus=float(row[g_annualized_other_current_ratio_bonus_index_n] if row[g_annualized_other_current_ratio_bonus_index_n] != None else 0), quarterized_other_current_ratio=float(row[g_quarterized_other_current_ratio_index_n] if row[g_quarterized_other_current_ratio_index_n] != None else 0), quarterized_other_current_ratio_bonus=float(row[g_quarterized_other_current_ratio_bonus_index_n] if row[g_quarterized_other_current_ratio_bonus_index_n] != None else 0), annualized_other_ratio=float(row[g_annualized_other_ratio_index_n] if row[g_annualized_other_ratio_index_n] != None else 0), annualized_other_ratio_bonus=float(row[g_annualized_other_ratio_bonus_index_n] if row[g_annualized_other_ratio_bonus_index_n] != None else 0), quarterized_other_ratio=float(row[g_quarterized_other_ratio_index_n] if row[g_quarterized_other_ratio_index_n] != None else 0), quarterized_other_ratio_bonus=float(row[g_quarterized_other_ratio_bonus_index_n] if row[g_quarterized_other_ratio_bonus_index_n] != None else 0), annualized_total_current_ratio=float(row[g_annualized_total_current_ratio_index_n] if row[g_annualized_total_current_ratio_index_n] != None else 0), quarterized_total_current_ratio=float(row[g_quarterized_total_current_ratio_index_n] if row[g_quarterized_total_current_ratio_index_n] != None else 0), total_ratio_effective=float(row[g_total_ratio_effective_index_n] if row[g_total_ratio_effective_index_n] != None else 0), other_current_ratio_effective=float(row[g_other_current_ratio_effective_index_n] if row[g_other_current_ratio_effective_index_n] != None else 0), other_ratio_effective=float(row[g_other_ratio_effective_index_n] if row[g_other_ratio_effective_index_n] != None else 0), total_current_ratio_effective=float(row[g_total_current_ratio_effective_index_n] if row[g_total_current_ratio_effective_index_n] != None else 0), effective_current_ratio=float(row[g_effective_current_ratio_index_n] if row[g_effective_current_ratio_index_n] != None else 0), effective_current_ratio_normalized=float(row[g_effective_current_ratio_normalized_index_n] if row[g_effective_current_ratio_normalized_index_n] != None else 0), annualized_total_assets=float(row[g_annualized_total_assets_index_n] if row[g_annualized_total_assets_index_n] != None else 0), annualized_total_assets_bonus=float(row[g_annualized_total_assets_bonus_index_n] if row[g_annualized_total_assets_bonus_index_n] != None else 0), quarterized_total_assets=float(row[g_quarterized_total_assets_index_n] if row[g_quarterized_total_assets_index_n] != None else 0), quarterized_total_assets_bonus=float(row[g_quarterized_total_assets_bonus_index_n] if row[g_quarterized_total_assets_bonus_index_n] != None else 0), effective_total_assets=float(row[g_effective_total_assets_index_n] if row[g_effective_total_assets_index_n] != None else 0), annualized_total_stockholder_equity=float(row[g_annualized_total_stockholder_equity_index_n] if row[g_annualized_total_stockholder_equity_index_n] != None else 0), annualized_total_stockholder_equity_bonus=float(row[g_annualized_total_stockholder_equity_bonus_index_n] if row[g_annualized_total_stockholder_equity_bonus_index_n] != None else 0), quarterized_total_stockholder_equity=float(row[g_quarterized_total_stockholder_equity_index_n] if row[g_quarterized_total_stockholder_equity_index_n] != None else 0), quarterized_total_stockholder_equity_bonus=float(row[g_quarterized_total_stockholder_equity_bonus_index_n] if row[g_quarterized_total_stockholder_equity_bonus_index_n] != None else 0), effective_total_stockholder_equity=float(row[g_effective_total_stockholder_equity_index_n] if row[g_effective_total_stockholder_equity_index_n] != None else 0), calculated_roa=float(row[g_calculated_roa_index_n] if row[g_calculated_roa_index_n] != None else 0), calculated_roa_normalized=float(row[g_calculated_roa_normalized_index_n] if row[g_calculated_roa_normalized_index_n] != None else 0), calculated_roe=float(row[g_calculated_roe_index_n] if row[g_calculated_roe_index_n] != None else 0), calculated_roe_normalized=float(row[g_calculated_roe_normalized_index_n] if row[g_calculated_roe_normalized_index_n] != None else 0), annualized_working_capital=float(row[g_annualized_working_capital_index_n] if row[g_annualized_working_capital_index_n] != None else 0), quarterized_working_capital=float(row[g_quarterized_working_capital_index_n] if row[g_quarterized_working_capital_index_n] != None else 0), effective_working_capital=float(row[g_effective_working_capital_index_n] if row[g_effective_working_capital_index_n] != None else 0), annualized_total_liabilities=float(row[g_annualized_total_liabilities_index_n] if row[g_annualized_total_liabilities_index_n] != None else 0), annualized_total_liabilities_bonus=float(row[g_annualized_total_liabilities_bonus_index_n] if row[g_annualized_total_liabilities_bonus_index_n] != None else 0), quarterized_total_liabilities=float(row[g_quarterized_total_liabilities_index_n] if row[g_quarterized_total_liabilities_index_n] != None else 0), quarterized_total_liabilities_bonus=float(row[g_quarterized_total_liabilities_bonus_index_n] if row[g_quarterized_total_liabilities_bonus_index_n] != None else 0), effective_total_liabilities=float(row[g_effective_total_liabilities_index_n] if row[g_effective_total_liabilities_index_n] != None else 0), altman_z_score_factor=float(row[g_altman_z_score_factor_index_n] if row[g_altman_z_score_factor_index_n] != None else 0), altman_z_score_factor_normalized=float(row[g_altman_z_score_factor_normalized_index_n] if row[g_altman_z_score_factor_normalized_index_n] != None else 0), skip_reason=row[g_skip_reason_index_n])


def get_stock_data_normalized_from_db_row_compact(row, stock_symbol):
    return StockDataNormalized(symbol=stock_symbol, short_name=row[g_name_index_n], sector=row[g_sector_index_n], country=row[g_country_index_n], sss_value=float(row[g_sss_value_index_n]), sss_value_normalized=float(row[g_sss_value_normalized_index_n]), evr_effective=float(row[g_evr_effective_index_n]), evr_effective_normalized=float(row[g_evr_effective_normalized_index_n]), effective_price_to_earnings=float(row[g_effective_price_to_earnings_index_n]), trailing_12months_price_to_sales=float(row[g_trailing_12months_price_to_sales_index_n]), trailing_12months_price_to_sales_normalized=float(row[g_trailing_12months_price_to_sales_normalized_index_n]), pe_effective=float(row[g_pe_effective_index_n]), pe_effective_normalized=float(row[g_pe_effective_normalized_index_n]), effective_ev_to_ebitda=float(row[g_effective_ev_to_ebitda_index_n]), effective_ev_to_ebitda_normalized=float(row[g_effective_ev_to_ebitda_normalized_index_n]), effective_profit_margin=float(row[g_effective_profit_margin_index_n]), effective_profit_margin_normalized=float(row[g_effective_profit_margin_normalized_index_n]), held_percent_insiders=float(row[g_held_percent_insiders_index_n]), held_percent_insiders_normalized=float(row[g_held_percent_insiders_normalized_index_n]), previous_close=float(row[g_previous_close_index_n]), price_to_book=float(row[g_price_to_book_index_n]), price_to_book_normalized=float(row[g_price_to_book_normalized_index_n]), enterprise_value=int(float(row[g_enterprise_value_index_n])), eqg_factor_effective=float(row[g_eqg_factor_effective_index_n]), eqg_factor_effective_normalized=float(row[g_eqg_factor_effective_normalized_index_n]), rqg_factor_effective=float(row[g_rqg_factor_effective_index_n]), rqg_factor_effective_normalized=float(row[g_rqg_factor_effective_normalized_index_n]), effective_peg_ratio=float(row[g_effective_peg_ratio_index_n]), effective_peg_ratio_normalized=float(row[g_effective_peg_ratio_normalized_index_n]), ev_to_cfo_ratio_effective=float(row[g_ev_to_cfo_ratio_effective_index_n]), ev_to_cfo_ratio_effective_normalized=float(row[g_ev_to_cfo_ratio_effective_normalized_index_n]), debt_to_equity_effective=float(row[g_debt_to_equity_effective_index_n]), debt_to_equity_effective_used=float(row[g_debt_to_equity_effective_used_index_n]), debt_to_equity_effective_used_normalized=float(row[g_debt_to_equity_effective_used_normalized_index_n]), eff_dist_from_low_factor=float(row[g_eff_dist_from_low_factor_index_n]), eff_dist_from_low_factor_normalized=float(row[g_eff_dist_from_low_factor_normalized_index_n]), total_ratio_effective=float(row[g_total_ratio_effective_index_n]), total_current_ratio_effective=float(row[g_total_current_ratio_effective_index_n]), effective_current_ratio=float(row[g_effective_current_ratio_index_n]), effective_current_ratio_normalized=float(row[g_effective_current_ratio_normalized_index_n]), calculated_roa=float(row[g_calculated_roa_index_n]), calculated_roa_normalized=float(row[g_calculated_roa_normalized_index_n]), calculated_roe=float(row[g_calculated_roe_index_n]), calculated_roe_normalized=float(row[g_calculated_roe_normalized_index_n]), altman_z_score_factor=float(row[g_altman_z_score_factor_index_n]), altman_z_score_factor_normalized=float(row[g_altman_z_score_factor_normalized_index_n]))


def process_symbols(json_db, symbols, csv_db_data, rows, rows_no_div, rows_only_div, tase_mode, read_all_country_symbols, sectors_list, sectors_filter_out, countries_list, countries_filter_out, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, pb_limit, pi_limit, enterprise_value_millions_usd_limit, research_mode_max_ev, eqg_min, rqg_min, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, research_mode, currency_conversion_tool, currency_conversion_tool_alternative, currency_conversion_tool_manual, reference_db, reference_db_title_row, diff_rows, db_filename, reference_raw_data=None):
    iteration = 0
    if not research_mode:
        elapsed_time_start_sec = time.time()
        for symb in symbols:
            iteration += 1
            elapsed_time_sample_sec = time.time()
            elapsed_time_sec        = round(elapsed_time_sample_sec - elapsed_time_start_sec, 0)
            average_sec_per_symbol  = round(elapsed_time_sec/float(iteration), int(NUM_ROUND_DECIMALS/3.0))
            percentage_complete     = round(100.0*float(iteration)/float(len(symbols)), int(NUM_ROUND_DECIMALS/3.0))
            print('[DB] {:9} ({:04}/{:04}/{:04} [{:2.2f}%], Diff: {:04}), time/left/avg [sec]: {:5.0f}/{:5.0f}/{:2.2f} -> '.format(symb, len(rows), iteration, len(symbols), percentage_complete, len(diff_rows), elapsed_time_sec, average_sec_per_symbol*(len(symbols)-iteration), average_sec_per_symbol), end='')

            if reference_raw_data is None:
                if tase_mode:
                    symbol = yf.Ticker(symb)
                else:
                    if read_all_country_symbols not in [sss_config.ALL_COUNTRY_SYMBOLS_SIX, sss_config.ALL_COUNTRY_SYMBOLS_ST]:
                        symbol = yf.Ticker(symb.replace('.U','-UN').replace('.W','-WT').replace('.','-'))  # TODO: ASFAR: Sometimes the '.' Is needed, especially for non-US companies. See for instance 5205.kl. In this case the parameter is also case-sensitive! -> https://github.com/pydata/pandas-datareader/issues/810#issuecomment-789684354
                    else:
                        if read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_ST and '.ST' not in symb: symb = symb.replace('.S.DX', '.ST')
                        symbol = yf.Ticker(symb)
            else:
                if symb in reference_raw_data:
                    symbol = reference_raw_data[symb]
                else:
                    print('[DB] symbol {} not in reference_raw_data {}'.format(symb, reference_raw_data))
                    continue

            stock_data = StockData(symbol=symb)
            process_info_result = process_info(json_db=json_db, symbol=symbol, stock_data=stock_data, tase_mode=tase_mode, sectors_list=sectors_list, sectors_filter_out=sectors_filter_out, countries_list=countries_list, countries_filter_out=countries_filter_out, profit_margin_limit=profit_margin_limit, ev_to_cfo_ratio_limit=ev_to_cfo_ratio_limit, debt_to_equity_limit=debt_to_equity_limit, pb_limit=pb_limit, pi_limit=pi_limit, enterprise_value_millions_usd_limit=enterprise_value_millions_usd_limit, research_mode_max_ev=research_mode_max_ev, eqg_min=eqg_min, rqg_min=rqg_min, price_to_earnings_limit=price_to_earnings_limit, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_sectors=favor_sectors, favor_sectors_by=favor_sectors_by, research_mode=research_mode, currency_conversion_tool=currency_conversion_tool, currency_conversion_tool_alternative=currency_conversion_tool_alternative, currency_conversion_tool_manual=currency_conversion_tool_manual, reference_db=reference_db, reference_db_title_row=reference_db_title_row, db_filename=None)
            if   tase_mode                                                      and 'TLV:' not in stock_data.symbol: stock_data.symbol = 'TLV:' + stock_data.symbol.replace('.TA', '').replace('-', '.')
            elif read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_SIX and 'SWX:' not in stock_data.symbol: stock_data.symbol = 'SWX:' + stock_data.symbol.replace('.SW', '')  # .replace('.', '-')
            elif read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_ST  and 'STO:' not in stock_data.symbol: stock_data.symbol = 'STO:' + stock_data.symbol.replace('.ST', '')  # .replace('.', '-')

            row_to_append = get_db_row_from_stock_data(stock_data)
            # Find symbol in reference_db:
            if len(reference_db):
                # for reference db, use only the values which affect the core equation
                indices_list_to_check_changes_in = get_list_of_csv_row_indices_which_affect_core_equation()

                symbol_index_in_reference_db = find_symbol_in_reference_db(stock_data.symbol, reference_db)
                if symbol_index_in_reference_db >= 0:
                    found_differences = False
                    for index in indices_list_to_check_changes_in:
                        if (VERBOSE_LOGS > 3): print('      comparing column {}'.format(g_header_row[index]))
                        if type(row_to_append[index]) == int or type(row_to_append[index]) == float:
                            try:
                                if g_header_row[index] in reference_db_title_row:
                                    column_index_in_reference_db = reference_db_title_row.index(g_header_row[index])
                                    if len(reference_db[symbol_index_in_reference_db][column_index_in_reference_db]):
                                        min_val = min(float(row_to_append[index]), float(reference_db[symbol_index_in_reference_db][column_index_in_reference_db]))
                                        max_val = max(float(row_to_append[index]), float(reference_db[symbol_index_in_reference_db][column_index_in_reference_db]))
                                    else:
                                        min_val = max_val = float(row_to_append[index])
                                    diff = abs(max_val-min_val)

                                    if diff > abs(max_val)*REFERENCE_DB_MAX_VALUE_DIFF_FACTOR_THRESHOLD:
                                        if 0.0 < float(reference_db[symbol_index_in_reference_db][g_sss_value_index]) < float(row_to_append[g_sss_value_index]):
                                            found_differences = True
                                            compensated_value = round(REFERENCE_DB_MAX_VALUE_DIFF_FACTOR_THRESHOLD*float(reference_db[symbol_index_in_reference_db][column_index_in_reference_db]) + (1-REFERENCE_DB_MAX_VALUE_DIFF_FACTOR_THRESHOLD)*float(row_to_append[index]), NUM_ROUND_DECIMALS)
                                            if type(row_to_append[index]) == int:
                                                compensated_value = int(round(compensated_value))
                                            print('                                                                           Diff (Taking [{} < {}]): ref[{:25}]={:6}, db[{:25}]={:6} -> comp -> {:6}'.format((reference_db[symbol_index_in_reference_db][g_sss_value_index]), (row_to_append[g_sss_value_index]), g_header_row[index], reference_db[symbol_index_in_reference_db][column_index_in_reference_db], g_header_row[index], row_to_append[index], compensated_value))
                                            row_to_append[index] = compensated_value  # Overwrite specific index value with compensated value from reference db
                            except Exception as e:
                                print("Exception {} in comparison of {}: row_to_append is {} while reference_db is {} -> {}".format(e, g_header_row[index], row_to_append[index], reference_db[symbol_index_in_reference_db][column_index_in_reference_db], traceback.format_exc()))
                                pass

                    if found_differences:
                        stock_data = get_stock_data_from_db_row(row_to_append)
                        if stock_data.sector             in ['None', '', 'Unknown']: stock_data.sector             = reference_db[symbol_index_in_reference_db][g_sector_index]
                        if stock_data.country            in ['None', '', 'Unknown']: stock_data.country            = reference_db[symbol_index_in_reference_db][g_country_index]
                        if stock_data.short_name         in ['None', '', 'Unknown']: stock_data.short_name         = reference_db[symbol_index_in_reference_db][g_name_index]
                        if stock_data.financial_currency in ['None', '', 'Unknown']: stock_data.financial_currency = reference_db[symbol_index_in_reference_db][g_financial_currency_index]
                        if stock_data.summary_currency   in ['None', '', 'Unknown']: stock_data.summary_currency   = reference_db[symbol_index_in_reference_db][g_summary_currency_index]

                        # stock_data = get_stock_data_from_db_row(reference_db[symbol_index_in_reference_db])
                        # Re-process with more correct information:
                        sss_core_equation_value_set(stock_data)
                        diff_rows.append(reference_db[symbol_index_in_reference_db])
                        print('[DB] Difference Found, recalculating sss_value: ', end='')
                        print_sss_value_results(stock_data)

            dividends_sum = stock_data.last_dividend_0+stock_data.last_dividend_1+stock_data.last_dividend_2+stock_data.last_dividend_3

            if process_info_result:
                rows.append(                           row_to_append)
                if dividends_sum:
                    rows_only_div.append(row_to_append)
                else:
                    rows_no_div.append(  row_to_append)
            csv_db_data.append(                        row_to_append)
    else: # DB already present
        for row_index, row in enumerate(csv_db_data):
            iteration += 1

            symbol = row[g_symbol_index_n if "normalized" in db_filename else g_symbol_index]
            # Below: 4 represents 1st index in row after "Country" which is index 3 (counting from 0 of course)
            # TODO: ASAFR: The loop below can probably be skipped (optimization) - check and verify
            for fix_row_index in range((g_country_index_n if "normalized" in db_filename else g_country_index)+1,len(row)):  # for empty strings - convert value to 0
                if row[fix_row_index] == '':
                    if fix_row_index == (g_name_index_n if "normalized" in db_filename else g_name_index):  # Name == '' --> 'None'
                        row[fix_row_index] = 'None'
                    else:
                        row[fix_row_index] = 0
            stock_data = get_stock_data_normalized_from_db_row_compact(row, symbol) if "normalized" in db_filename else get_stock_data_from_db_row_compact(row, symbol)
            if not process_info(json_db=None, symbol=symbol, stock_data=stock_data, tase_mode=tase_mode, sectors_list=sectors_list, sectors_filter_out=sectors_filter_out, countries_list=countries_list, countries_filter_out=countries_filter_out, profit_margin_limit=profit_margin_limit, pb_limit=pb_limit, pi_limit=pi_limit, enterprise_value_millions_usd_limit=enterprise_value_millions_usd_limit, research_mode_max_ev=research_mode_max_ev, ev_to_cfo_ratio_limit=ev_to_cfo_ratio_limit, debt_to_equity_limit=debt_to_equity_limit, eqg_min=eqg_min, rqg_min=rqg_min, price_to_earnings_limit=price_to_earnings_limit, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_sectors=favor_sectors, favor_sectors_by=favor_sectors_by, research_mode=research_mode, currency_conversion_tool=currency_conversion_tool, currency_conversion_tool_alternative=currency_conversion_tool_alternative, currency_conversion_tool_manual=currency_conversion_tool_manual, reference_db=reference_db, reference_db_title_row=reference_db_title_row, db_filename=db_filename):
                if research_mode: continue

            dividends_sum = stock_data.last_dividend_0 + stock_data.last_dividend_1 + stock_data.last_dividend_2 + stock_data.last_dividend_3

            row_to_append = get_db_row_from_stock_data_normalized(stock_data) if "normalized" in db_filename else get_db_row_from_stock_data(stock_data)
            rows.append(                           row_to_append)
            if dividends_sum: rows_only_div.append(row_to_append)
            else:             rows_no_div.append(  row_to_append)

            # Probing:
            for symbol in sss_config.research_mode_probe_list:
                if symbol in stock_data.symbol:
                    print('[Probe] {:5}: {:5} pb {:6.3f} | pi {:6.6f} | evm {:6.0f} | pe {:8.3f} | evr {:8.3f} | pm {:7.3f}% :'.format(symbol, len(rows), stock_data.price_to_book, stock_data.held_percent_insiders, stock_data.enterprise_value, stock_data.effective_price_to_earnings, stock_data.evr_effective, stock_data.effective_profit_margin*100), end='')


def download_ftp_files(filenames_list, ftp_path):
    for filename in filenames_list:
        filename_to_download = filename
        if '/' in filename_to_download:
            filename_to_download = filename[filename.index('/')+1:]
        with closing(request.urlopen(ftp_path+filename_to_download.replace('.csv','.txt'))) as read_file:
            with open(filename, 'wb') as file_write:
                shutil.copyfileobj(read_file, file_write)

# reference_run : Used for identifying anomalies in which some symbol information is completely different from last run. It can be different but only in new quartely reports
#                 It is sometimes observed that stocks information is wrongly fetched. Is such cases, the last run's reference point shall be used, with a forgetting factor
def sss_run(reference_run, sectors_list, sectors_filter_out, countries_list, countries_filter_out, csv_db_path, db_filename, read_all_country_symbols, tase_mode, research_mode, profit_margin_limit, ev_to_cfo_ratio_limit, debt_to_equity_limit, pb_limit, pi_limit, enterprise_value_millions_usd_limit, research_mode_max_ev, price_to_earnings_limit, enterprise_value_to_revenue_limit, favor_sectors, favor_sectors_by, appearance_counter_dict_sss={}, appearance_counter_min=25, appearance_counter_max=35, custom_portfolio=[], num_results_list=[], num_results_list_index=0):
    # Working Parameters:
    eqg_min = EQG_UNKNOWN     # The earnings can decrease but there is still a requirement that price_to_earnings_to_growth_ratio > 0. TODO: ASAFR: Add to multi-dimension
    rqg_min = RQG_UNKNOWN     # The revenue  can decrease there is still a requirement that price_to_earnings_to_growth_ratio > 0. TODO: ASAFR: Add to multi-dimension

    symbols                 = []
    symbols_tase            = []
    symbols_snp500          = []
    symbols_nasdaq_100_csv  = []
    symbols_russel1000_csv  = []

    if not research_mode:
        # https://en.wikipedia.org/wiki/ISO_4217
        currency_filename = 'Indices/currencies.json'
        with open(currency_filename, 'r') as file:
            currency_rates_raw_dict = json.loads(file.read())
        currency_conversion_tool_manual = {k: round(float(v), NUM_ROUND_DECIMALS) for k, v in currency_rates_raw_dict.items()}
        # print(currency_conversion_tool_manual)

        json_db = dict()

        currency_conversion_tool = None
        currency_conversion_tool_alternative = None

        try:
            currency_conversion_tool = CurrencyRates().get_rates('USD')
        except Exception as e:
            pass

        try:
            currency_conversion_tool_alternative = CurrencyConverter()
        except Exception as e:
            pass

        for item in currency_conversion_tool_manual:
            if currency_conversion_tool != None and item not in currency_conversion_tool:
                try:
                    currency_conversion_tool[item] = 1.0/float(currency_conversion_tool_alternative.convert(1.0, item, 'USD'))
                except:
                    currency_conversion_tool[item] = 1.0/float(currency_conversion_tool_manual[item])

        reference_db           = []
        reference_db_title_row = []
        if reference_run != None and len(reference_run):  # in non-research mode, compare to reference run
            reference_csv_db_filename = reference_run+'/db.csv'
            with open(reference_csv_db_filename, mode='r', newline='') as engine:
                reader = csv.reader(engine, delimiter=',')
                row_index = 0
                for row in reader:
                    if row_index <= 1: # first row is just a title of evr and pm, then a title of columns
                        if row_index == 1: reference_db_title_row = row
                        row_index += 1
                        continue
                    else:
                        reference_db.append(row)
                        row_index += 1

        if not tase_mode and read_all_country_symbols not in [sss_config.ALL_COUNTRY_SYMBOLS_SIX, sss_config.ALL_COUNTRY_SYMBOLS_ST]:
            payload            = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies') # There are 2 tables on the Wikipedia page, get the first table
            first_table        = payload[0]
            second_table       = payload[1]
            df                 = first_table
            symbols_snp500     = df['Symbol'].values.tolist()

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

            symbols_tase     = []
        elif tase_mode:
            try:
                sss_indices.update_tase_indices()
            except Exception as e:
                print("Error updating Indices/Data_TASE.csv: {} -> {}".format(e, traceback.format_exc()))

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

            tase_filenames_list = ['Indices/Data_Duals_TASE.csv']
            for filename in tase_filenames_list:
                with open(filename, mode='r', newline='') as engine:
                    reader = csv.reader(engine, delimiter=',')
                    row_index = 0
                    for row in reader:
                        if row_index <= 3:
                            row_index += 1
                            continue
                        else:
                            g_symbols_tase_duals.append(row[1].replace('.','-')+'.TA')
                            row_index += 1

        # All nasdaq and others: ftp://ftp.nasdaqtrader.com/symboldirectory/ -> Downloaded automatically
        # Legend: http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs
        # ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt
        # ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt
        # ftp.nasdaqtrader.com/SymbolDirectory/nasdaqtraded.txt
        symbols_united_states               = []
        symbols_six                         = []
        symbols_st                          = []
        etf_and_nextshares_list             = []
        if read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_SIX:
            filenames_list     = ['Indices/six_closing.csv']  # https://www.six-group.com/en/products-services/the-swiss-stock-exchange/market-data/shares/closing-prices.html -> https://www.six-group.com/fqs/closing.csv?select=ShortName,ISIN,ValorSymbol,ValorNumber,ClosingPrice,DailyHighPrice,DailyLowPrice,LatestTradeDate,PreviousClosingPrice,OpeningPrice,OnMarketVolume,OffBookVolume,SwissAtMidVolume,TotalVolume,TradingBaseCurrency,YearlyHighDate,YearlyHighPrice,YearlyLowDate,YearlyLowPrice,FirstTradingDate,LastTradingDate,Exchange,SecTypeCode,GeographicalAreaCode,Tminus1Volume,VWAP60Price&where=ProductLine=BC&orderby=ShortName&page=1&pagesize=9999999
            ticker_column_list = [2                        ]  # six_closing.csv - Column 2 is ValorSymbol
            for index, filename in enumerate(filenames_list):
                with open(filename, mode='r', newline='') as engine:
                    reader = csv.reader(engine, delimiter=';')
                    row_index = 0
                    for row in reader:
                        if row_index == 0:
                            row_index += 1
                            continue
                        else:
                            row_index += 1
                            stock_symbol = row[ticker_column_list[index]]
                            symbols_six.append(stock_symbol+'.SW')

        elif read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_ST:
            filenames_list     = ['Indices/swedish_stocks_list_filtered.csv']
            ticker_column_list = [0                                         ]  # Column 0 is Symbol
            for index, filename in enumerate(filenames_list):
                with open(filename, mode='r', newline='') as engine:
                    reader = csv.reader(engine, delimiter=',')
                    row_index = 0
                    for row in reader:
                        if row_index == 0:
                            row_index += 1
                            continue
                        else:
                            row_index += 1
                            if VERBOSE_LOGS > 2: print('[sss_run] ticker_column_list[index={}] = {}, row = {}'.format(index, ticker_column_list[index], row))
                            stock_symbol = row[ticker_column_list[index]]
                            if '.S.DX' not in stock_symbol: continue
                            symbols_st.append(stock_symbol)

        elif read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_US:
            nasdaq_filenames_list = ['Indices/nasdaqlisted.csv', 'Indices/otherlisted.csv', 'Indices/nasdaqtraded.csv']  # Checkout http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs for all symbol definitions (for instance - `$` in stock names, 5-letter stocks ending with `Y`)
            ticker_column_list    = [0,                          0,                         1                         ]  # nasdaqtraded.csv - 1st column is Y/N (traded or not) - so take row[1] instead!!!
            download_ftp_files(nasdaq_filenames_list, 'ftp://ftp.nasdaqtrader.com/SymbolDirectory/')
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
                            if 'File Creation Time' in row[0]:
                                continue
                            if next_shares_column and row[next_shares_column] == 'Y':
                                etf_and_nextshares_list.append(row[ticker_column_list[index]])
                                continue
                            if etf_column         and row[etf_column]         == 'Y':
                                etf_and_nextshares_list.append(row[ticker_column_list[index]])
                                continue
                            if '$' in row[ticker_column_list[index]]: # AAIC$B -> <stock_symbol>$<letter> --> keep just the stock_Symbol
                                stock_symbol = row[ticker_column_list[index]].split('$')[0]
                            else:
                                stock_symbol = row[ticker_column_list[index]]
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

        symbols = symbols_snp500 + symbols_nasdaq_100_csv + symbols_russel1000_csv + symbols_united_states + symbols_six + symbols_st

        if tase_mode:
            symbols = symbols_tase

        symbols = sorted(list(set(symbols)))

        # Temporary to test and debug: DEBUG MODE
        # =======================================
        if len(custom_portfolio):
            symbols = []
            if tase_mode:
                for symbol in custom_portfolio:
                    symbols.append(symbol.replace('.', '-') + '.TA')
            else:
                symbols = custom_portfolio

        print('\n{} Symbols to Scan: {}'.format(len(symbols), symbols))

        # After printing: shuffle (better content from Yahoo Finance):
        # random.shuffle(symbols)
        print('\n{} Symbols order to Scan: {}\n'.format(len(symbols), symbols))

    csv_db_data   = []
    rows          = []
    rows_no_div   = []
    rows_only_div = []
    rows_diff     = []

    if research_mode: # if DB is already present, read from it and prepare input
        symbols = []
        csv_db_filename = csv_db_path+'/'+db_filename
        num_title_rows = 1 if "normalized" in db_filename else 2
        with open(csv_db_filename, mode='r', newline='') as engine:
            reader = csv.reader(engine, delimiter=',')
            row_index = 0
            for row in reader:
                if row_index < num_title_rows:  # first row (only in non-normalized sss_engine.csv) is just a title of evr and pm, then a title of columns
                    row_index += 1
                    continue
                else:
                    symbols.append(row[0])
                    csv_db_data.append(row)
                    row_index += 1

    reference_raw_data = None
    if sss_config.use_reference_as_raw_data:
        json_db_filename = open(reference_run + '/db.json')
        reference_raw_data = json.load(json_db_filename)

    process_symbols(json_db=json_db if not research_mode else None, symbols=symbols, csv_db_data=csv_db_data, rows=rows, rows_no_div=rows_no_div, rows_only_div=rows_only_div, tase_mode=tase_mode, read_all_country_symbols=read_all_country_symbols, sectors_list=sectors_list, sectors_filter_out=sectors_filter_out, countries_list=countries_list, countries_filter_out=countries_filter_out, profit_margin_limit=profit_margin_limit, ev_to_cfo_ratio_limit=ev_to_cfo_ratio_limit, debt_to_equity_limit=debt_to_equity_limit, pb_limit=pb_limit, pi_limit=pi_limit, enterprise_value_millions_usd_limit=enterprise_value_millions_usd_limit, research_mode_max_ev=research_mode_max_ev, eqg_min=eqg_min, rqg_min=rqg_min, price_to_earnings_limit=price_to_earnings_limit, enterprise_value_to_revenue_limit=enterprise_value_to_revenue_limit, favor_sectors=favor_sectors, favor_sectors_by=favor_sectors_by, research_mode=research_mode, currency_conversion_tool=currency_conversion_tool if not research_mode else None, currency_conversion_tool_alternative=currency_conversion_tool_alternative if not research_mode else None, currency_conversion_tool_manual=currency_conversion_tool_manual if not research_mode else None, reference_db=reference_db if not research_mode else None, reference_db_title_row=reference_db_title_row if not research_mode else None, diff_rows=rows_diff, db_filename=db_filename, reference_raw_data=reference_raw_data)

    # remove (from rows, not from db or diff) rows whose sss_value is irrelevant:
    compact_rows          = []
    compact_rows_no_div   = []
    compact_rows_only_div = []
    if not research_mode:
        for row in rows:
            if row[         g_sss_value_index_n if "normalized" in db_filename else g_sss_value_index] != BAD_SSS: compact_rows.append(row)
        for row_no_div in rows_no_div:
            if row_no_div[  g_sss_value_index_n if "normalized" in db_filename else g_sss_value_index] != BAD_SSS: compact_rows_no_div.append(row_no_div)
        for row_only_div in rows_only_div:
            if row_only_div[g_sss_value_index_n if "normalized" in db_filename else g_sss_value_index] != BAD_SSS: compact_rows_only_div.append(row_only_div)

        # Now, Sort the compact_rows using the sss_value formula: [1:] skips the 1st title row
        sorted_list_db               = sorted(csv_db_data,           key=lambda row:          row[         g_symbol_index_n               if "normalized" in db_filename else g_symbol_index   ],  reverse=False)  # Sort by symbol
        sorted_list_sss              = sorted(compact_rows,          key=lambda row:          row[         g_sss_value_normalized_index_n if "normalized" in db_filename else g_sss_value_index],  reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
        sorted_list_sss_no_div       = sorted(compact_rows_no_div,   key=lambda row_no_div:   row_no_div[  g_sss_value_normalized_index_n if "normalized" in db_filename else g_sss_value_index],  reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
        sorted_list_sss_only_div     = sorted(compact_rows_only_div, key=lambda row_only_div: row_only_div[g_sss_value_normalized_index_n if "normalized" in db_filename else g_sss_value_index],  reverse=False)  # Sort by sss_value     -> The lower  - the more attractive
        sorted_list_diff             = sorted(rows_diff,             key=lambda row_diff:     row_diff[    g_symbol_index_n               if "normalized" in db_filename else g_symbol_index   ],  reverse=False)  # Sort by symbol
        sorted_lists_list = [
            sorted_list_db,
            sorted_list_sss,
            sorted_list_sss_no_div,
            sorted_list_sss_only_div,
            sorted_list_diff
        ]

        for sorted_list in sorted_lists_list:
            sorted_list.insert(0, (g_header_row_normalized if "normalized" in db_filename else g_header_row))

        custom_sss_value_str  = "_CustSssV" if sss_config.custom_sss_value_equation else ""
        tase_str              = ""
        sectors_str           = ""
        countries_str         = ""
        all_str               = ""
        csv_db_str            = ""
        custom_portfolio_str  = ""
        num_results_str       = "_nRes{}".format(len(compact_rows))
        build_csv_db_str      = ""
        if tase_mode:         tase_str       = "_Tase"

        if len(sectors_list):
            if sectors_filter_out: sectors_list += 'FO_'
            sectors_str += '_' + '_'.join(sectors_list)
        else:
            for index, sector in enumerate(favor_sectors):
                sectors_str += '_{}{}'.format(sector.replace(' ', ''), round(favor_sectors_by[index], NUM_ROUND_DECIMALS))

        if len(countries_list):
            if countries_filter_out: countries_list += 'FO_'
            countries_str += '_' + '_'.join(countries_list).replace(' ', '')

        mode_str = 'Nsr' # Default is Nasdaq100+S&P500+Russel1000
        if   read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_US:  mode_str = 'All'
        elif read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_SIX: mode_str = 'Six'
        elif read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_ST:  mode_str = 'St'
        elif tase_mode:                                                      mode_str = 'Tase'
        elif len(custom_portfolio):                                          mode_str = 'Custom'

        if   read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_US:  all_str  = '_A'
        elif read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_SIX: all_str  = '_S'
        elif read_all_country_symbols == sss_config.ALL_COUNTRY_SYMBOLS_ST:  all_str  = '_St'

        if not research_mode:     build_csv_db_str     = '_Bdb'
        if len(custom_portfolio): custom_portfolio_str = '_Custom'

        date_and_time = time.strftime("Results/{}/%Y%m%d-%H%M%S{}{}{}{}{}{}{}{}{}".format(mode_str, tase_str, sectors_str.replace(' ','').replace('a','').replace('e','').replace('i','').replace('o','').replace('u',''), countries_str, all_str, csv_db_str, build_csv_db_str, num_results_str, custom_portfolio_str, custom_sss_value_str))
        print('\n[DV] Scan Results placed in {}'.format(date_and_time))

        filenames_list = sss_filenames.create_filenames_list(date_and_time)

        evr_pm_col_title_row = ['Maximal price_to_earnings_limit: {}, Maximal enterprise_value_to_revenue_limit: {}, Minimal profit_margin_limit: {}'.format(price_to_earnings_limit, enterprise_value_to_revenue_limit, profit_margin_limit)]

        for index in range(len(filenames_list)):
            os.makedirs(os.path.dirname(filenames_list[index]), exist_ok=True)
            with open(filenames_list[index], mode='w', newline='') as engine:
                writer = csv.writer(engine)
                sorted_lists_list[index].insert(0, evr_pm_col_title_row)
                writer.writerows(sorted_lists_list[index])
        # Save raw database as json:
        json_db_file = open(date_and_time+'/db.json', "w")
        json.dump(json_db, json_db_file, indent=1)
        json_db_file.close()

        sss_post_processing.process_engine_csv(date_and_time)
    else:
        sorted_list_sss = compact_rows = rows

        # Update the appearance counter:
        list_len_sss = len(sorted_list_sss)
        if appearance_counter_min <= list_len_sss   <= appearance_counter_max:
            for index, row in enumerate(sorted_list_sss):
                # Debug mode:
                # if 'ISRA-L' in row[g_symbol_index]:
                #     print('ISRA-L - index is {}'.format(index))
                if "normalized" in db_filename:
                    appearance_counter_dict_sss[(row[g_symbol_index_n], row[g_name_index_n], row[g_sector_index_n], row[g_sss_value_normalized_index_n], row[g_previous_close_index_n])] = appearance_counter_dict_sss[(row[g_symbol_index_n], row[g_name_index_n], row[g_sector_index_n], row[g_sss_value_normalized_index_n], row[g_previous_close_index_n])] + math.sqrt(float(list_len_sss - index)) / float(list_len_sss)
                else:
                    appearance_counter_dict_sss[(row[g_symbol_index],   row[g_name_index],   row[g_sector_index],   row[g_sss_value_index],              row[g_previous_close_index])]   = appearance_counter_dict_sss[(row[g_symbol_index],   row[g_name_index],   row[g_sector_index],   row[g_sss_value_index],              row[g_previous_close_index])]   + math.sqrt(float(list_len_sss - index)) / float(list_len_sss)


    if num_results_list != None and num_results_list_index < len(num_results_list): num_results_list[num_results_list_index] = len(compact_rows)
    return len(compact_rows)
