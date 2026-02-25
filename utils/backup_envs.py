import os
import shutil
import argparse
from pathlib import Path

def backup_env_files(root_dir):
    # Convertimos la ruta a un objeto Path y la resolvemos (ruta absoluta)
    root_path = Path(root_dir).resolve()
    
    # Validamos que la ruta exista
    if not root_path.exists() or not root_path.is_dir():
        print(f"❌ Error: La ruta '{root_dir}' no existe o no es un directorio válido.")
        return

    # Creamos la carpeta principal de backup
    backup_dir = root_path / "envs-files"
    backup_dir.mkdir(exist_ok=True)
    
    print(f"🔍 Iniciando escaneo en: {root_path}")
    print("-" * 40)

    # Buscamos todos los archivos .env recursivamente
    # Usamos .rglob() para que busque en todos los subniveles
    env_files = list(root_path.rglob('.env'))
    
    if not env_files:
        print("⚠️ No se encontraron archivos .env en la ruta especificada.")
        return

    archivos_copiados = 0

    for env_path in env_files:
        # Evitamos escanear la propia carpeta de backup si ejecutas el script varias veces
        if backup_dir in env_path.parents:
            continue
            
        # Obtenemos el nombre de la carpeta padre inmediata para mostrar en consola
        parent_folder_name = env_path.parent.name
        
        # Mostramos en consola según el formato solicitado: nombre_carpeta, archivo .env
        print(f"📁 {parent_folder_name}, {env_path.name}")
        
        # Calculamos la ruta relativa para replicar la estructura de carpetas
        # y evitar que .env de distintas carpetas se sobreescriban
        relative_parent = env_path.relative_to(root_path).parent
        dest_folder = backup_dir / relative_parent
        
        # Creamos la ruta de carpetas de destino
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        # Ruta final donde se pegará el archivo
        dest_file = dest_folder / env_path.name
        
        # Copiamos el archivo .env (copy2 preserva los metadatos como fecha de creación)
        shutil.copy2(env_path, dest_file)
        archivos_copiados += 1

    print("-" * 40)
    print(f"✅ Backup completado con éxito. Se copiaron {archivos_copiados} archivos.")
    print(f"📂 Tus .env respaldados están en: {backup_dir}")

if __name__ == "__main__":
    # Configuramos el paso de parámetros por consola
    parser = argparse.ArgumentParser(description="Script para hacer un backup de todos los archivos .env locales.")
    parser.add_argument(
        "ruta", 
        help="La ruta absoluta o relativa de tu carpeta principal (ej: C:/Usuarios/TuNombre/Documentos/github)"
    )
    
    args = parser.parse_args()
    backup_env_files(args.ruta)