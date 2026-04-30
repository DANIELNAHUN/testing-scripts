import os
import pymysql
from load_dotenv import load_dotenv
import pandas as pd

load_dotenv()

columns_to_extract = ''
table_name = 'notificaciones_avisos_cobranza'


def connect_to_db():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE")
    )
    return connection

def connect_to_db_2():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST_2"),
        user=os.getenv("DB_USER_2"),
        password=os.getenv("DB_PASSWORD_2"),
        database=os.getenv("DB_DATABASE_2")
    )
    return connection

def query_generator():
    if not columns_to_extract:
        cols = '*'
    else:
        cols = columns_to_extract
    query = f"SELECT {cols} from {table_name}"
    # query = """
    #     SELECT ac.id_sede, ac.nom_sede, ac.abonado, ac.nom_abonado, ac.estado, ac.celular1, ac.celular2, ac.celular3, ac.deuda, ac.link, n.correo as correo_electronico, n.fecha_install_internet as fecha_instalacion_internet, n.fecha_install_cable as fecha_instalacion_cable
    #     FROM avisos_cobranza ac
    #     INNER JOIN nomina n ON ac.id_sede = n.id_sede AND ac.abonado = n.abonado
    #     """
    print(query)
    return query

import pandas as pd

def save_to_excel(dfs: dict, filename: str):
    with pd.ExcelWriter(filename) as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name)
    print(f"Se guardó el archivo {filename}")

if __name__ == "__main__":
    connection = connect_to_db_2()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query_generator())
            result = [{cursor.description[index][0]: column for index, column in enumerate(value)} for value in cursor.fetchall()]
            print("Generando Excel")
            save_to_excel(dfs={'Correos': pd.DataFrame(result)}, filename=f'files/output/{table_name}.xlsx')
    finally:
        connection.close()


# SELECT DISTINCT estado_os FROM orden_servicio;
# SELECT DISTINCT tipo_os FROM orden_servicio;
