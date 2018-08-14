# Import pandas
import pandas as pd

def pyExlDict(filexl):
    """
    process a two column .xlsx file
    input: filexl: file name in <str>
    output: dictout: a dict with column 1 as key, column 2 as value
    """
    dtfr = pd.read_excel(filexl, dtype = str)
    key_list = list(dtfr.keys())
    dictout = {}
    col1 = dtfr.get(key_list[0])
    col2 = dtfr.get(key_list[1])
    for i in range(len(col1)):
        dictout[col1[i]] = col2[i]

    return dictout