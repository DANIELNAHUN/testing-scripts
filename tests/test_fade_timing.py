#!/usr/bin/env python3
"""
Script de prueba para verificar el timing correcto del fade del fondo musical.
"""

from pathlib import Path
from pydub import AudioSegment
from src.audio_combiner import AudioCombiner
from src.logger_config import get_logger

logger = get_logger('test_fade_timing')

def create_test_audio():
    """Crea audios de prueba para verificar el timing del fade."""
    
    # Crear un locutor de prueba de 10 segundos
    locutor_test = AudioSegment.silent(duration=10000)  # 10 segundos
    
    # Crear un fondo de prueba de 20 segundos (locutor + 10s)
    background_test = AudioSegment.silent(duration=20000)  # 20 segundos
    
    return locutor_test, background_test

def test_fade_timing():
    """Prueba el timing del fade del fondo musical."""
    
    logger.info("=== PRUEBA DE TIMING DEL FADE ===")
    
    # Crear audios de prueba
    locutor, background = create_test_audio()
    
    logger.info(f"Locutor de prueba: {len(locutor)}ms")
    logger.info(f"Fondo de prueba: {len(background)}ms")
    
    # Inicializar el combiner
    combiner = AudioCombiner()
    
    # Calcular posiciones esperadas
    locutor_start = combiner.LOCUTOR_START_OFFSET  # 5000ms
    locutor_end = locutor_start + len(locutor)     # 5000 + 10000 = 15000ms
    fade_start_expected = locutor_end - 1000       # 15000 - 1000 = 14000ms
    
    logger.info(f"Posiciones esperadas:")
    logger.info(f"  - Locutor inicia en: {locutor_start}ms")
    logger.info(f"  - Locutor termina en: {locutor_end}ms")
    logger.info(f"  - Fade debe iniciar en: {fade_start_expected}ms (1s antes del final del locutor)")
    
    # Combinar audios
    combined = combiner.combine(locutor, background)
    
    logger.info(f"Audio combinado: {len(combined)}ms")
    
    # Verificar que el timing sea correcto
    expected_final_duration = len(background)  # Debe ser igual al fondo
    
    if len(combined) == expected_final_duration:
        logger.info("✓ Duración final correcta")
    else:
        logger.warning(f"✗ Duración final incorrecta: esperada {expected_final_duration}ms, obtenida {len(combined)}ms")
    
    return combined

def test_with_real_scenario():
    """Prueba con un escenario más realista."""
    
    logger.info("\n=== PRUEBA CON ESCENARIO REALISTA ===")
    
    # Simular un locutor de 45 segundos
    locutor_real = AudioSegment.silent(duration=45000)  # 45 segundos
    
    # Simular un fondo de 55 segundos (45 + 10)
    background_real = AudioSegment.silent(duration=55000)  # 55 segundos
    
    logger.info(f"Locutor realista: {len(locutor_real)}ms ({len(locutor_real)/1000:.1f}s)")
    logger.info(f"Fondo realista: {len(background_real)}ms ({len(background_real)/1000:.1f}s)")
    
    combiner = AudioCombiner()
    
    # Calcular posiciones
    locutor_start = combiner.LOCUTOR_START_OFFSET  # 5000ms
    locutor_end = locutor_start + len(locutor_real)  # 5000 + 45000 = 50000ms
    fade_start_expected = locutor_end - 1000         # 50000 - 1000 = 49000ms
    
    logger.info(f"Timing del escenario realista:")
    logger.info(f"  - Locutor: {locutor_start/1000:.1f}s a {locutor_end/1000:.1f}s")
    logger.info(f"  - Fade del fondo inicia en: {fade_start_expected/1000:.1f}s")
    logger.info(f"  - Fade del fondo termina en: {locutor_end/1000:.1f}s")
    logger.info(f"  - Volumen alto del fondo: {locutor_end/1000:.1f}s hasta {len(background_real)/1000:.1f}s")
    
    # Combinar
    combined_real = combiner.combine(locutor_real, background_real)
    
    logger.info(f"Resultado: {len(combined_real)}ms ({len(combined_real)/1000:.1f}s)")
    
    return combined_real

def export_test_results():
    """Exporta los resultados de prueba para análisis en Audacity."""
    
    output_folder = Path('files/output')
    output_folder.mkdir(parents=True, exist_ok=True)
    
    logger.info("\n=== EXPORTANDO RESULTADOS PARA ANÁLISIS ===")
    
    # Prueba básica
    combined_basic = test_fade_timing()
    combined_basic.export(output_folder / "test_fade_timing_basic.mp3", format="mp3")
    logger.info(f"Exportado: {output_folder}/test_fade_timing_basic.mp3")
    
    # Prueba realista
    combined_real = test_with_real_scenario()
    combined_real.export(output_folder / "test_fade_timing_realistic.mp3", format="mp3")
    logger.info(f"Exportado: {output_folder}/test_fade_timing_realistic.mp3")
    
    logger.info(f"\nArchivos exportados en: {output_folder}")
    logger.info("Puedes abrir estos archivos en Audacity para verificar visualmente el timing del fade")

if __name__ == "__main__":
    logger.info("Iniciando pruebas de timing del fade")
    export_test_results()
    logger.info("Pruebas completadas")