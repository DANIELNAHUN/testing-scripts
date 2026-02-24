import os
import pymysql
from load_dotenv import load_dotenv
import pandas as pd
import pandas_cases.utils as ut

load_dotenv()



def connect_to_db():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE")
    )
    return connection


if __name__ == "__main__":
    connection = connect_to_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT correo FROM ficha_inscripcion LIMIT 10")
            result = cursor.fetchall()
            ut.save_to_excel(dfs={'Correos': pd.DataFrame(result)}, filename='files/results/correos.xlsx')
    finally:
        connection.close()


# SELECT DISTINCT estado_os FROM orden_servicio;
# SELECT DISTINCT tipo_os FROM orden_servicio;
