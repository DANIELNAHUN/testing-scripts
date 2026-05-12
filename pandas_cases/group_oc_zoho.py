import os
import pandas as pd

def process(file):

    df = pd.read_csv(file)

    # Prueba limitar a 200 filas
    df = df.head(200)

    # leer columnas
    columns = df.columns
    print(columns)
    df.rename(columns={
        'oc.ID Oportunidad/ID Pago (comisiones)': 'oc_id_oportunidad', 
        'oc.Correlativo de orden': 'oc_correlativo',
        'oc.Hasta': 'oc_fecha_hasta',
        'oc.Fecha renovada': 'oc_fecha_renovada'
        }, inplace=True)

    # Encontrar el numero maximo de oc_correlativo para cada oc.ID Oportunidad, necesito mantener el campo oc_fecha_hasta de los maximos encontrados
    max_correlativos = df.groupby('oc_id_oportunidad').max()['oc_correlativo'].reset_index()
    # Agregar el campo oc_fecha_hasta que ya tiene mi dataframe original, hacer merge por id oportunidad y correlativo maximo
    max_correlativos = pd.merge(max_correlativos, df[['oc_id_oportunidad', 'oc_correlativo', 'oc_fecha_hasta']], on=['oc_id_oportunidad', 'oc_correlativo'], how='left')

    # print(max_correlativos)

    # Llenar todos los campos de oc.Fecha renovada con la fecha maxima de oc_fecha_hasta dependiendo de cada oc_id_oportunidad
    # Merge max correlativos back to df to know the max correlativo per opportunity
    df = pd.merge(df, max_correlativos.rename(columns={'oc_correlativo': 'max_correlativo', 'oc_fecha_hasta': 'max_hasta'}), 
                  on='oc_id_oportunidad', how='left')
    
    # Set oc_fecha_renovada in all cases except when oc_correlativo matches the max for that opportunity or when oc_correlativo is 1
    df['oc_fecha_renovada'] = df['max_hasta'].where(
        (df['oc_correlativo'] != df['max_correlativo']) & (df['oc_correlativo'] != 1), pd.NA
    )

    # Delete rows when oc_correlativo matches the max for that opportunity
    df = df[df['oc_correlativo'] != df['max_correlativo']]
    
    # # Drop the helper column
    # df = df.drop(columns=['max_correlativo', 'max_hasta'])
    print(df[['oc_id_oportunidad', 'oc_correlativo', 'oc_fecha_hasta', 'max_hasta', 'oc_fecha_renovada']])

    # Guardar el resultado en un nuevo archivo CSV
    df.to_csv('files/output/OC_para_marcar_como_renovadas.csv', index=False)

        

if __name__ == "__main__":
    file = "files/source/revisar.csv"
    process(file)