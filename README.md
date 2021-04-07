# SSS Overview
 Stock Scanner & Screener: A `yfinance`+`investpy` combined-based Stock Scanner & Screener for the Israeli and US Stock Markets (Extendable to other stock markets as well). Within the code, the following libraries and fonts are used:
 - https://pypi.org/project/yfinance/
 - https://pypi.org/project/investpy/
 - https://pypi.org/project/fpdf/
 - https://fonts2u.com/dejavu-sans-condensed.font

The stocks scan and sorting is done according to the below documentation (Core Equation and Multi-Dimensional scan) written using Google Documents (https://www.google.com/docs/about/):

# SSS Core Equation
http://bit.ly/SssCoreEquation

# SSS Muti-Dimentional Scan and Ranking Equation
http://bit.ly/SssBigDataAnalysis

# Setup
- Install `Python 3.7` or higher from https://www.python.org/downloads/
- Install `Pycharm Community Edition` from https://www.jetbrains.com/pycharm/download/
- Download the `SSS` source code as a Zip file from this page (https://github.com/asafravid/sss/archive/master.zip) or clone/fork the repository directly
- Open Project from folder (to which you unzipped the `sss` source code)
- No further steps required apart from `pip3` installing relevant libraries:
  - `cd <[path to]Python 3.7>`
  - `pip3 install pandas`
  - `pip3 install yfinance`
  - `pip3 install investpy`
  - `pip3 install fpdf`
- Note that for `yfinance` - I'm providing updated sources since they take time to update by the developers, 
  and my forks are, well - mine, and I prefer one to `pip3` install `yfinance` from the origin, and then update 
  (using comparison SW) the necessary changes I made (not too many) to run the `SSS` most efficiently and informatively.
  
# Run Step-By-Step Instructions
- 1: Run the scanning mode by uncommenting the `Run Build DB Only` lines in `sss_run.py`
- 2: A result folder shall be created under `Results` Folder
- 3: Results list shall appear in the result folder fed to the Research Mode

# Track Your Investments - Reference Sheet
http://bit.ly/SssResultsInvestmentTracking

# Indices Maintenance (Once per month)
- Download `TASE` latest components via https://info.tase.co.il/eng/MarketData/Stocks/MarketData/Pages/MarketData.aspx into `Indices/Data_TASE.csv`
- Download `NASDAQ100` latest components via https://www.barchart.com/stocks/quotes/$IUXX/components?viewName=main  (Remove last line indicating creation date) or https://www.nasdaq.com/market-activity/quotes/nasdaq-ndx-index into `Indices/nasdaq100-components.csv`
- Download `Russel1000` latest components via https://www.barchart.com/stocks/indices/russell/russell1000 (Remove last line indicating creation date) or https://en.wikipedia.org/wiki/Russell_1000_Index into `russell-1000-index.csv` 
- Download `S&P500` latest components via https://www.barchart.com/stocks/quotes/$SPX/components into `Indices/snp500-components.csv`  (Remove last line indicating creation date)
- Download `NASDAQ` latest components via `ftp://ftp.nasdaqtrader.com/symboldirectory/` into `Indices/nasdaqlisted.csv` (Convert `.txt` to `.csv` and remove last line indicating creation date) using an FTP Client (such as https://filezilla-project.org/)
- Download `NASDAQ` Other Listed components via `ftp://ftp.nasdaqtrader.com/symboldirectory/` into `Indices/otherlisted.csv` (Convert `.txt` to `.csv` and remove last line indicating creation date) using an FTP Client (such as https://filezilla-project.org/)
- Download `NASDAQ` Traded components via `ftp://ftp.nasdaqtrader.com/symboldirectory/` into `Indices/nasdaqtraded.csv` (Convert `.txt` to `.csv` and remove last line indicating creation date) using an FTP Client (such as https://filezilla-project.org/)
- You can also create your own indice/group of stocks by either overriding the above files' contents or simply adding your own indice to the code support. Use Custom Mode, and example in `sss_run.py`
- Checkout http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs for all symbol definitions (for instance - `$` in stock names, 5-letter stocks ending with `Y`)

# Disclaimer
- Make your analysis before buying any of the Results stocks
- Buying the Results stocks is at your own risk
- Study the Results companies - read their financial reports, and only then decide if and how much to buy

# yfinance.7z Usage
- `yfinance` is a known library which this scanner uses
- Several Bugs were found upon examining the code of `yfinance`, and I have created pull requests for those.
- For simplicity, unzip `yfinance.7z` and beyond[or other comparison software]-compare it with the official [`pip3` it] one, and take the changes provided within this library's `yfinance.7z`.

# Understanding and Verifying Units of yfinance parameters
- Units can compared to https://www.macroaxis.com/stock-analysis/CMRE/Costamare (i.e. CMRE can be replaced for any stock ticker/symbol)
- Use case: `CMRE`'s `yfinance` `earningsQuarterlyGrowth` is `-0.298`, and website shows `-29.80%` so the match yields that `yfinance` reports in direct ratio (not `%`)

# Looking Forward for Contributions
- Good luck and you are welcome to contribute to this project:
  - Add other contries' stocks
  - Past reccomendations and present results - for proving that the model works
  - Multi-Dimentional Big Data research mode (scan over `EQG`s, etc)
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
