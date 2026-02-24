import pandas as pd

def save_to_excel(dfs: dict, filename: str):
    with pd.ExcelWriter(filename) as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name)
    print(f"Se guardó el archivo {filename}")