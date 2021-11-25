#############################################################################
#
# Version 0.2.9 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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
import sss_config
import sss_filenames

SSS_VALUE_NORMALIZED_COLUMN_NAME = "sss_value_normalized"
SSS_VALUE_COLUMN_NAME            = "sss_value"


def process_engine_csv(path) -> object:
    filename_path = path+"/"+sss_filenames.ENGINE_FILENAME
    data          = pd.read_csv(filename_path+".csv", skiprows=[0])  # 1st row is a description row, irrelevant for the data processing
    max_values    = data.max()
    # max_2_nlargest = data.nlargest(2,numerator_parameters_list+denominator_parameters_list)
    [numerator_parameters_list,              denominator_parameters_list             ] = sss.get_used_parameters_names_in_core_equation(False)                                 # Take all values
    [numerator_parameters_list_to_calcualte, denominator_parameters_list_to_calcualte] = sss.get_used_parameters_names_in_core_equation(sss_config.custom_sss_value_equation)  # Take all values for calculation of the sss_value

    for parameter in numerator_parameters_list:
        new_column       = data[parameter] / max_values[parameter]
        new_column_index = data.columns.get_loc(parameter)
        data.insert(new_column_index+1, parameter+"_normalized",new_column)
        if SSS_VALUE_NORMALIZED_COLUMN_NAME in data:
            if parameter in numerator_parameters_list_to_calcualte:
                data[SSS_VALUE_NORMALIZED_COLUMN_NAME] = data[SSS_VALUE_NORMALIZED_COLUMN_NAME] + data[parameter+"_normalized"]
        else:
            new_column_index = data.columns.get_loc(SSS_VALUE_COLUMN_NAME)
            data.insert(new_column_index + 1, SSS_VALUE_NORMALIZED_COLUMN_NAME, new_column)

    for parameter in denominator_parameters_list:
        new_column       = data[parameter] / max_values[parameter]
        new_column_index = data.columns.get_loc(parameter)
        data.insert(new_column_index+1, parameter+"_normalized",new_column)
        if parameter in denominator_parameters_list_to_calcualte:
            data[SSS_VALUE_NORMALIZED_COLUMN_NAME]     = data[SSS_VALUE_NORMALIZED_COLUMN_NAME] - data[parameter+"_normalized"]

    sorted_Data = data.sort_values(by=[SSS_VALUE_NORMALIZED_COLUMN_NAME])
    sorted_Data.to_csv(filename_path+"_normalized.csv", index = False)