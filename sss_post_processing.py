#############################################################################
#
# Version 0.1.102 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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

import sss
import sss_filenames

SSS_VALUE_NORMALIZED_COLUMN_NAME = "sss_value_normalized"


def process_engine_csv(path) -> object:
    filename_path = path+"/"+sss_filenames.ENGINE_FILENAME
    data = pd.read_csv(filename_path+".csv", skiprows=[0])  # 1st row is a description row, irrelevant for the data processing
    max_values = data.max()
    [numerator_parameters_list, denominator_parameters_list] = sss.get_used_parameters_names_in_core_equation()
    for parameter in numerator_parameters_list:
        data[parameter+"_normalized"] = data[parameter] / max_values[parameter]
        if SSS_VALUE_NORMALIZED_COLUMN_NAME in data:
            data[SSS_VALUE_NORMALIZED_COLUMN_NAME] = data[SSS_VALUE_NORMALIZED_COLUMN_NAME] + data[parameter+"_normalized"]
        else:
            data[SSS_VALUE_NORMALIZED_COLUMN_NAME] =                                          data[parameter+"_normalized"]
    for parameter in denominator_parameters_list:
        data[parameter+"_normalized"] = data[parameter] / max_values[parameter]
        data[SSS_VALUE_NORMALIZED_COLUMN_NAME]     = data[SSS_VALUE_NORMALIZED_COLUMN_NAME] - data[parameter+"_normalized"]

    data.sort_values(by=SSS_VALUE_NORMALIZED_COLUMN_NAME)
    data.to_csv(filename_path+"_normalized.csv")