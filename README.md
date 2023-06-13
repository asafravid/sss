# Overview 
* Utilizing `yfinance` [non-API based] +`yahooquery` [API-based] - Stock Scanner & Screener Based on a Core Equation of Fundamental Financial Properties, followed by a Multi-dimensional Scan Ranking process.
* Supports Custom Portfolio and the Israeli, US, Swedish and Swiss Stock Markets (Extendable to other stock markets as well).
* The stocks scan and sorting is done according to the below documentation (Core Equation and Multi-Dimensional scan) written using Google Documents (https://www.google.com/docs/about/):

# Core Equation
http://bit.ly/SssCoreEquation

# Muti-Dimensional Scan and Ranking Equation
https://bit.ly/MultiDimensionalScan

# Setup
 Within the code, the following libraries and fonts are used:
 - Mandatory Python Libraries:
   - https://pypi.org/project/yfinance/
   - https://pypi.org/project/fpdf/
   - https://pypi.org/project/pandas/
 - Reccomended Python Libraries (Backup Internal independent Forex Tables are partially maintained):
   - https://pypi.org/project/forex-python/
   - https://pypi.org/project/CurrencyConverter/
   - https://pypi.org/project/py-currency-converter/
   - https://pypi.org/project/PyCurrency-Converter/
   - https://pypi.org/project/currency.converter/
 - Fonts:
   - https://fonts2u.com/dejavu-sans-condensed.font

- Install `Python 3.6` or higher from https://www.python.org/downloads/
- (Reccomended but Optional) Install `Pycharm Community Edition` from https://www.jetbrains.com/pycharm/download/
- Download the source code as a Zip file from this page (https://github.com/asafravid/sss/archive/master.zip) or clone/fork the repository directly
- Open Project from folder (to which you unzipped the `sss` source code)
- No further steps required apart from `pip[3]` installing relevant libraries:
  - Mandatory
    - `pip[3] install pandas`
    - `pip[3] install yfinance`
    - `pip[3] install yahooquery`
    - `pip[3] install fpdf`
    - `pip[3] install pyPdf`
    - `pip[3] install numpy`
    - `pip[3] install forex_python` and/or `pip[3] install forex-python`
    - `pip[3] install CurrencyConverter`
    - `pip[3] install PyCurrency-Converter`
    - `pip[3] install currency.converter`
  
# Run Step-By-Step Instructions
- 1: Set `multi_dim_scan_mode` to `False` and for 1st time run, you may set `reference_run_<mode>` to `None` (or to latest relevant directory in results)
- 2: Set the required scanning mode(s) (`custom`/`tase`/`nsr`/`all`) in `sss_config.py` and run `sss_run.py`
- 3: A (New) `Results/<scan_mode>/<date_and_time>_..._<num_results>` directory shall be created under `Results/<mode>/` directory
- 4: Feed the `Results` path into the `multi_dim_scan_mode = True` (Multi-Dimensional Scan). A `PDF` and `results_sss_*.csv` files shall be created in the same directory
- 5: Crash and Continue from crash point - Supported for efficiency.

# Indices Maintenance
- Download `TASE` latest components via https://info.tase.co.il/eng/MarketData/Stocks/MarketData/Pages/MarketData.aspx into `Indices/Data_TASE.csv` -> This operation is done automatically upon each scan (with `research_mode = False`) via `sss_indices.py`
- Download `NASDAQ100` latest components via https://www.nasdaq.com/market-activity/quotes/nasdaq-ndx-index into `Indices/nasdaq100-components.csv`
- Download `Russel1000` latest components via https://en.wikipedia.org/wiki/Russell_1000_Index into `russell-1000-index.csv` 
- Download `S&P500` latest components into `Indices/snp500-components.csv`  (Remove last line indicating creation date)
- Download `NASDAQ` latest components (`otherlisted.txt`, `nasdaqlisted.txt`, `otherlisted.txt`) via `ftp://ftp.nasdaqtrader.com/symboldirectory/` into the `Indices/` directory (Convert `.txt` to `.csv`) using an FTP Client (such as https://filezilla-project.org/) -> This operation is done automatically upon each scan (with `research_mode = False`)
- You can also create your own indice/group of stocks by either overriding the above files' contents or simply adding your own indice to the code support. Use Custom Mode, and example in `sss_config.py`
- Checkout http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs for all symbol definitions (for instance - `$` in stock names, 5-letter stocks ending with `Y`, etc)

# Disclaimer
- The Scan Results are __By No Neans__ to be interpreted as reccomendations.
- The Results are merely a basis for Research and Analysis.

# Understanding and Verifying Units of yfinance parameters
- Units can be compared to https://www.macroaxis.com/stock-analysis/CMRE/Costamare (i.e. CMRE can be replaced for any stock ticker/symbol)
- Use case: `CMRE`'s `yfinance` `earningsQuarterlyGrowth` is `-0.298`, and website shows `-29.80%` so the match yields that `yfinance` reports in direct ratio (not `%`)

# Looking Forward for Contributions
- You are encouraged to contribute to this project:
  - Add other contries' stock markets
  - Past reccomendations and present results - for proving that the model works (a prototype is ready `sss_results_performance.py`)
  - Multi-Dimensional Scan enhancements (scan over `EQG`s, etc)
  - For any questions / issues / suggestions: You can reach me here: asaf.rvd@gmail.com

# License
          Copyright (C) 2021  Asaf Ravid <asaf.rvd@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
