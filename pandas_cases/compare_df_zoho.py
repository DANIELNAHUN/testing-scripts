import pandas as pd
import numpy as np


df_from_zoho = pd.read_excel('files/DealsZohoVsBDNawiki.xlsx', sheet_name='FromZoho')
df_from_bd = pd.read_excel('files/DealsZohoVsBDNawiki.xlsx', sheet_name='FromBD')

RELATION_BD_ZOHO = {
    'ID_Oportunidad': 'id',
    'KD': 'KD_Red_es',
    'Renueva': 'Oportunidad_Renovada',
    # 'ID_Nueva_Oportunidad': '',
    'Producto': 'Producto_temporal',
    'Tipo_Renovacion': 'Tipo_de_Renovaci_n',
    'SKU_Temporal': 'SKU_Temporal_6',
    'Fecha_Renovacion_Servicio':'Fecha_renovaci_n_Servicio',
    'Fecha_Subscripcion': 'Fecha_de_compra',
    'Estado_Provision_SKU_Temporal': 'Estado_provisi_n_SKU_temporal',
    'Recibido_Pago_Suscripcion': 'Recibido_pago_suscripci_n',
    'Zoho_ID_Registro': 'Zoho_ID_Registro', # Siempre sumar columnas adicionales antes de estos dos
    'KIT_Contratado': 'Categor_a_de_Producto',
}

def fill_na_values(df: pd.DataFrame):
    df.replace(pd.NaT, '', inplace=True)
    df.replace('NaT', 'N/A', inplace=True)
    df.replace('',"N/A", inplace=True)
    df.replace(np.nan,'N/A', inplace=True)
    df.fillna("N/A", inplace=True)
    return df

def transform_df_in_set(df: pd.DataFrame) -> set:
    return set(tuple(row) for row in df.to_numpy())

def compare_bd_with_zoho_records(df_from_bd: pd.DataFrame, df_from_zoho: pd.DataFrame):
    relation_without_zoho_id = RELATION_BD_ZOHO.copy()
    relation_without_zoho_id.pop('Zoho_ID_Registro')
    relation_without_zoho_id.pop('KIT_Contratado') # Se quita la columna por que siempre viene desde Zoho como Kit Digital, pero mas adelante se clasifica en PCS/OFV
    df_nuevos = pd.DataFrame()
    df_actualizar = pd.DataFrame()
    df_differences = pd.DataFrame()
    try:
        for col in ['SKU_Temporal_6.id', 'Producto_temporal.name']:
            if col in df_from_zoho.columns:
                df_from_zoho.drop(col, axis='columns', inplace=True)
        rename_dict = {}
        if 'Producto_temporal.name' in df_from_zoho.columns:
            rename_dict['Producto_temporal.id'] = 'Producto_temporal'
        if 'SKU_Temporal_6.name' in df_from_zoho.columns:
            rename_dict['SKU_Temporal_6.name'] = 'SKU_Temporal'
        if rename_dict:
            df_from_zoho.rename(columns=rename_dict, inplace=True)

        df_from_zoho = df_from_zoho[relation_without_zoho_id.values()]
        df_from_bd = df_from_bd[relation_without_zoho_id.keys()]
        df_from_zoho = df_from_zoho.rename(columns={v: k for k, v in relation_without_zoho_id.items()})

        df_from_bd['Renueva'] = np.where(df_from_bd['Renueva'].isin([1, '1', True, 'true', 'True']), True, False)
        df_from_bd['Recibido_Pago_Suscripcion'] = np.where(df_from_bd['Recibido_Pago_Suscripcion'].isin([1, '1', True, 'true', 'True']), True, False)
        df_from_zoho['Renueva'] = np.where(df_from_zoho['Renueva'].isin([1, '1', True, 'true', 'True']), True, False)
        df_from_zoho['Recibido_Pago_Suscripcion'] = np.where(df_from_zoho['Recibido_Pago_Suscripcion'].isin([1, '1', True, 'true', 'True']), True, False)
        df_from_bd[['Fecha_Renovacion_Servicio', 'Fecha_Subscripcion']] = df_from_bd[['Fecha_Renovacion_Servicio', 'Fecha_Subscripcion']].apply(pd.to_datetime, errors='coerce').fillna(pd.NaT)
        df_from_zoho[['Fecha_Renovacion_Servicio', 'Fecha_Subscripcion']] = df_from_zoho[['Fecha_Renovacion_Servicio', 'Fecha_Subscripcion']].apply(pd.to_datetime, errors='coerce').fillna(pd.NaT)
        df_from_zoho['Fecha_Renovacion_Servicio'] = pd.to_datetime(df_from_zoho['Fecha_Renovacion_Servicio']).dt.strftime('%Y-%m-%d')
        df_from_zoho['Fecha_Subscripcion'] = pd.to_datetime(df_from_zoho['Fecha_Subscripcion']).dt.strftime('%Y-%m-%d')
        
        # if df_from_bd['Fecha_Renovacion_Servicio'].dtype == 'datetime64[ns]':
        #     df_from_bd['Fecha_Renovacion_Servicio'] = df_from_bd['Fecha_Renovacion_Servicio'].dt.date.astype(str)
        # if df_from_zoho['Fecha_Subscripcion'].dtype == 'datetime64[ns]':
        #     df_from_zoho['Fecha_Subscripcion'] = df_from_zoho['Fecha_Subscripcion'].dt.date.astype(str)
        df_from_bd_clean = fill_na_values(df_from_bd)
        df_from_zoho_clean = fill_na_values(df_from_zoho)

        df_from_zoho_set = transform_df_in_set(df_from_zoho_clean)
        df_from_bd_set = transform_df_in_set(df_from_bd_clean)

        differences = df_from_zoho_set - df_from_bd_set
        df_differences = pd.DataFrame(list(differences), columns=df_from_bd.columns)

        nuevos = list(set(df_differences['ID_Oportunidad']) - set(df_from_bd['ID_Oportunidad']))
        actualizar = list(set(df_differences['ID_Oportunidad']) & set(df_from_bd['ID_Oportunidad']))

        df_nuevos = df_from_zoho.loc[df_from_zoho['ID_Oportunidad'].isin(nuevos)]
        df_actualizar = df_from_zoho.loc[df_from_zoho['ID_Oportunidad'].isin(actualizar)]

        print(f"Nuevos registros: {len(df_nuevos)}, por actualizar: {len(df_actualizar)}")
        save_to_excel(dfs={'FromBD': df_from_bd, 'FromZoho': df_from_zoho}, filename='files/results/ComparacionDeals.xlsx')

    except Exception as e:
        print(f"Error comparing records: {e}")
        return df_nuevos, df_actualizar, df_differences

    return df_nuevos, df_actualizar, df_differences

def save_to_excel(dfs: dict, filename: str):
    with pd.ExcelWriter(filename) as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name)

df_nuevos, df_actualizar, df_differences = compare_bd_with_zoho_records(df_from_bd, df_from_zoho)
# save_to_excel(dfs={'Nuevos': df_nuevos, 'Actualizar': df_actualizar, 'Diferencias': df_differences}, filename='files/results/comparison_results.xlsx')