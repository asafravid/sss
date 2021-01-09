# sss
Sure Stock Scanner: A yfinance+investpy combined-based Stock Scanner for the Israeli and US Stock Markets

# SSS Core Equation
http://bit.ly/SssCoreEquation

# Setup
- No steps requried apart from pip-installing relevant libraries
- Note that for yfinance - I'm providing updated sources since they take time to update by the developers, 
  and my forks are, well - mine, and I prefer one to pip install yfinance from the origin, and then update 
  (using comparison SW) the necessary changes I made (not too many) to run the SSS smoothly and gracefuly.
  
# Run Step-By-Step Instructions
- 1: Run the scanning mode by uncommenting the `Run Build DB Only` lines in `sss_run.py`
- 2: A result folder shall be created under `Results` Folder
- 3: Run research mode, selecting profit margin (`pm`) Enterprise value to Revenue Ratio ('evr') scanning parameters (just use the defaults - they are fine)
- 4: Reccomendation list shall appear in the result folder fed to the Research Mode

# Make your analysis before buying the reccommended stocks
- This Stock Screener/Scanner shall only provide reccomendations
- Buying the reccommended stocks is at your own risk
- Study the companies reccommended - read their financial reports, and only then decide if and how much to buy
- Good luck and you are welcome to contribute to this project:
  - Add other contries stocks, for instance
  - Past reccomendations and present results - for proving that the model works

# yfinance.7z Usage
- `yfinance` is a known library which this scanner uses
- Several Bugs were found upon examining the code of `yfinance`, and I have created pull requests for those.
- For simplicity, unzip `yfinance.7z` and beyond[or other comparison software]-compare it with the official [`pip3` it] one, and take the changes provided within this library's `yfinance.7z`.
