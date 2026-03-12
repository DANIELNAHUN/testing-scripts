#!/usr/bin/env python3
"""
Script de prueba para verificar los nuevos efectos de eco suave y aumento de volumen.
"""

from pathlib import Path
from src.file_loader import FileLoader
from src.locutor_processor import LocutorProcessor
from src.logger_config import get_logger

logger = get_logger('test_echo_volume')

def test_echo_and_volume_effects():
    """Prueba los nuevos efectos de eco suave y aumento de volumen."""
    
    # Configurar rutas
    source_folder = Path('files/input')
    output_folder = Path('files/output')
    
    # Crear carpeta de salida si no existe
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Inicializar componentes
    file_loader = FileLoader(source_folder)
    locutor_processor = LocutorProcessor(file_loader)
    
    logger.info("=== Prueba 1: Audio sin efectos ===")
    result_no_effects = locutor_processor.unify_locutor_audio(
        export_path=output_folder,
        export_filename="locutor_sin_efectos",
        apply_soft_echo=False,
        increase_volume=False
    )
    
    logger.info("=== Prueba 2: Audio con eco suave solamente ===")
    result_echo_only = locutor_processor.unify_locutor_audio(
        export_path=output_folder,
        export_filename="locutor_con_eco",
        apply_soft_echo=True,
        echo_delay_ms=150,
        echo_decay=0.3,
        increase_volume=False
    )
    
    logger.info("=== Prueba 3: Audio con aumento de volumen solamente ===")
    result_volume_only = locutor_processor.unify_locutor_audio(
        export_path=output_folder,
        export_filename="locutor_con_volumen",
        apply_soft_echo=False,
        increase_volume=True,
        volume_increase_db=3.0
    )
    
    logger.info("=== Prueba 4: Audio con ambos efectos (configuración por defecto) ===")
    result_both_effects = locutor_processor.unify_locutor_audio(
        export_path=output_folder,
        export_filename="locutor_con_ambos_efectos",
        apply_soft_echo=True,
        increase_volume=True
    )
    
    logger.info("=== Prueba 5: Audio con eco más pronunciado ===")
    result_strong_echo = locutor_processor.unify_locutor_audio(
        export_path=output_folder,
        export_filename="locutor_eco_fuerte",
        apply_soft_echo=True,
        echo_delay_ms=200,
        echo_decay=0.5,
        increase_volume=True,
        volume_increase_db=4.0
    )
    
    # Mostrar resultados
    logger.info("\n=== RESUMEN DE RESULTADOS ===")
    logger.info(f"Sin efectos: {result_no_effects.duration_ms}ms, archivos: {len(result_no_effects.files_loaded)}")
    logger.info(f"Solo eco: {result_echo_only.duration_ms}ms, archivos: {len(result_echo_only.files_loaded)}")
    logger.info(f"Solo volumen: {result_volume_only.duration_ms}ms, archivos: {len(result_volume_only.files_loaded)}")
    logger.info(f"Ambos efectos: {result_both_effects.duration_ms}ms, archivos: {len(result_both_effects.files_loaded)}")
    logger.info(f"Eco fuerte: {result_strong_echo.duration_ms}ms, archivos: {len(result_strong_echo.files_loaded)}")
    
    logger.info(f"\nArchivos exportados en: {output_folder}")
    
    return {
        'no_effects': result_no_effects,
        'echo_only': result_echo_only,
        'volume_only': result_volume_only,
        'both_effects': result_both_effects,
        'strong_echo': result_strong_echo
    }

if __name__ == "__main__":
    logger.info("Iniciando pruebas de efectos de eco y volumen")
    results = test_echo_and_volume_effects()
    logger.info("Pruebas completadas")