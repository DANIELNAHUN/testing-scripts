import sys
import os

# Añadir la raíz del proyecto al path para que las importaciones funcionen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from mysql.db import connect_to_db
import pandas_cases.utils as ut

table = 'email_envios_sorteo'

def main():
    # 1. Establecer conexión a la base de datos
    print("Conectando a la base de datos...")
    connection = connect_to_db()
    
    try:
        # 2. Definir el query y leer los datos en un DataFrame
        # Ajusta este query según tus necesidades
        query = f"SELECT * FROM {table}"
        print(f"Ejecutando query: {query}")
        
        # Usamos pd.read_sql para obtener el DataFrame directamente
        df = pd.read_sql(query, connection)
        
        # 3. Configurar la ruta de salida en files/output
        output_dir = 'files/output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_file = os.path.join(output_dir, f'{table}.xlsx')
        
        # 4. Usar la utilidad para guardar en Excel
        # La función ut.save_to_excel espera un diccionario de DataFrames
        print(f"Guardando datos en {output_file}...")
        ut.save_to_excel(dfs={'DatosDB': df}, filename=output_file)
        
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        # 5. Cerrar la conexión
        connection.close()
        print("Conexión cerrada.")

if __name__ == "__main__":
    main()
