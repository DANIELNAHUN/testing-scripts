#!/usr/bin/env python3
"""
Script de prueba para exportar audio de locutor usando tu configuración actual.
"""

from pathlib import Path
from src.file_loader import FileLoader
from src.locutor_processor import LocutorProcessor
from src.logger_config import setup_logging


def test_export_locutor():
    """Prueba la exportación del audio de locutor."""
    # Configurar logging
    setup_logging()
    
    # Usar las mismas rutas que probablemente uses en tu proyecto
    # Ajusta estas rutas según tu estructura de archivos
    source_folder = Path("files/source")
    output_folder = Path("files/output")  # Exportar en el directorio actual
    
    print(f"🔍 Buscando archivos en: {source_folder.absolute()}")
    print(f"💾 Exportando a: {output_folder.absolute()}")
    
    try:
        # Crear instancias
        file_loader = FileLoader(source_folder)
        locutor_processor = LocutorProcessor(file_loader)
        
        print("\n🎵 Iniciando unificación de archivos de locutor...")
        
        # Mostrar la secuencia que se va a procesar
        print("📋 Secuencia de archivos a procesar:")
        for i, filename in enumerate(locutor_processor.LOCUTOR_SEQUENCE, 1):
            print(f"   {i}. {filename}")
        
        # Unificar y exportar
        result = locutor_processor.unify_locutor_audio(
            export_path=output_folder,
            export_filename="locutor_unificado_test",
            reduce_silences=True,  # Activar reducción de silencios
            max_silence_duration=0.7  # Máximo 0.7 segundos de silencio
        )
        
        # Mostrar resultados detallados
        print(f"\n✅ ¡Unificación completada!")
        print(f"📊 Resumen:")
        print(f"   • Archivos procesados: {len(result.files_loaded)}/{len(locutor_processor.LOCUTOR_SEQUENCE)}")
        print(f"   • Duración total: {result.duration_ms / 1000:.2f} segundos ({result.duration_ms / 60000:.2f} minutos)")
        
        if result.files_loaded:
            print(f"\n✓ Archivos incluidos en la unificación:")
            for file in result.files_loaded:
                print(f"   ✓ {file}")
        
        if result.files_skipped:
            print(f"\n⚠️  Archivos no encontrados (omitidos):")
            for file in result.files_skipped:
                print(f"   ⚠️  {file}")
        
        output_file = output_folder / "locutor_unificado_test.mp3"
        if output_file.exists():
            print(f"\n🎧 Audio exportado exitosamente:")
            print(f"   📁 Archivo: {output_file.absolute()}")
            print(f"   📏 Tamaño: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_export_locutor()