#############################################################################
#
# Version 0.1.100 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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


import pandas as pd
import numpy  as np

def read_engine_csv(path, resolution):
    data = pd.read_csv(path, skiprows=[0])  # 1st row is a description row, irrelevant for the data processing
    quantiles = data.quantile(np.linspace(1/resolution,1,resolution-1,0))
    ranks     = data.rank()
