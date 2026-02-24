import pandas as pd
import utils as ut

list_invalid_pre_correos = [
    'NOTIENE',
    'NOTIIEN',
    'NOTIEME',
    'NOTIEEN',
    'NOTIEN',
    'NOTINE',
    'NTIENE',
    'NOSABE',
    'NORECUERDA',
    'NOSE',
    'NOSEACUERDA',
    'ADULTOMAYO',
    'NOCUENTA',
    'NOCUETA'
    'NO.TIENE',
    'NO10',
    'NOTENGO',
    'NOESTADISPONIBLE',
    '-',
    'NODESEA',
    'NOIENECORREO',
    'NOIIENE',
    'NOITIENE',
    'NORECEURDA',
    'NOTIEJECORREO',
    'NOCUETACONCORREO',
]
list_invalid_exact_correos = [
    'NO',
    'NONO',
    'NONONON',
    'NOOTIENE',
    'NT',
    'NTG',
    'NO.TIENE'
]


def validar_correos(row: pd.Series) -> pd.DataFrame:
    if pd.isna(row['prefijo']) or row['prefijo'] == '':
        return False
    for palabra in list_invalid_pre_correos:
        if palabra in row['prefijo']:
            return False
    for palabra in list_invalid_exact_correos:
        if palabra == row['prefijo']:
            return False
    return True

df_correos = pd.read_excel('files/results/correos.xlsx', sheet_name='Correos')
df_correos.columns = ['idx','correo']
df_correos['prefijo'] = df_correos['correo'].str.split('@').str[0]
df_correos['prefijo'] = df_correos['prefijo'].str.upper()
df_correos['prefijo'] = df_correos['prefijo'].str.replace(' ', '')
df_correos['es_valido'] = df_correos.apply(validar_correos, axis=1)
ut.save_to_excel(dfs={'Correos Clasificados': df_correos},
                 filename='files/results/correos_validos.xlsx')
print("Proceso terminado")