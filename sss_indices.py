#############################################################################
#
# Version 0.1.61 - Author: Asaf Ravid <asaf.rvd@gmail.com>
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

# Prototype for downloading the latest TASE indices directly.
# TODO: ASAFR: Add output directly to CSV (currently printed on screen)

import urllib3
import certifi

def update_tase_indices():
    url_tase_indices = 'https://info.tase.co.il/_layouts/Tase/ManagementPages/Export.aspx?sn=none&action=1&SubAction=0&GridId=33&CurGuid={85603D39-703A-4619-97D9-CE9F16E27615}&ExportType=3'
    http             = urllib3.PoolManager(ca_certs=certifi.where())
    headers          = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    req       = http.request('GET', url_tase_indices, headers=headers)
    data_tase = req.data.decode('utf-8')
    data_tase_no_extra_lines = "\n".join(data_tase.splitlines())
    f = open('Indices/Data_TASE.csv','w')
    f.write(data_tase_no_extra_lines)
    f.close()