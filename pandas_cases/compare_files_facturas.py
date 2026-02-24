import pandas as pd
import os


id_from_zoho = pd.read_excel('files/IDFROMZOHO.xlsx')
id_from_bd = pd.read_excel('files/IDFROMBD.xlsx')

def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, keys: list) -> tuple:
    merged = df1.merge(df2, on=keys, how='outer', indicator=True)
    only_in_df1 = merged[merged['_merge'] == 'left_only']
    only_in_df2 = merged[merged['_merge'] == 'right_only']
    in_both = merged[merged['_merge'] == 'both']
    return only_in_df1, only_in_df2, in_both

# El campo ID debe ser texto
id_from_zoho['ID'] = id_from_zoho['ID'].astype(str)
id_from_bd['ID'] = id_from_bd['ID'].astype(str)

only_in_zoho, only_in_bd, in_both = compare_dataframes(id_from_zoho, id_from_bd, ['ID'])
with pd.ExcelWriter('files/results/comparison_results.xlsx') as writer:
    only_in_zoho.to_excel(writer, sheet_name='Only in Zoho', index=False)
    only_in_bd.to_excel(writer, sheet_name='Only in BD', index=False)
    in_both.to_excel(writer, sheet_name='In Both', index=False)