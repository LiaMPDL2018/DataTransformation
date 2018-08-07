# Import pandas
import pandas as pd
from openpyxl import load_workbook

def pyExlDict(filexl):
    """
    process a two column .xlsx file
    input: filexl: file name in <str>
    output: dictout: a dict with column 1 as key, column 2 as value
    """

    xl = pd.ExcelFile(filexl)

    # Print the sheet names
    sheetName = xl.sheet_names[0]

    # Load a sheet into a DataFrame by name: df1
    df = xl.parse(sheetName)
    # print(df)
    dfdict = df.to_dict()
    keys = list(dfdict.keys())
    col1 = dfdict[keys[0]]
    col2 = dfdict[keys[1]]

    dictout = {}
    for i in range(len(col1)):
        dictout[col1[i]] = str(col2[i])

    return dictout
# # Load csv
# df = pd.read_csv(filecsv) 