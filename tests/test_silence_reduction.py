#!/usr/bin/env python3
"""
Script para probar la funcionalidad de reducción de silencios en el audio de locutor.
"""

from pathlib import Path
from src.file_loader import FileLoader
from src.locutor_processor import LocutorProcessor
from src.logger_config import setup_logging


def test_silence_reduction():
    """Prueba la reducción de silencios con diferentes configuraciones."""
    # Configurar logging
    setup_logging()
    
    source_folder = Path("audio_files")
    output_folder = Path(".")
    
    print(f"🔍 Procesando archivos desde: {source_folder.absolute()}")
    print(f"💾 Exportando resultados a: {output_folder.absolute()}")
    
    try:
        # Crear instancias
        file_loader = FileLoader(source_folder)
        locutor_processor = LocutorProcessor(file_loader)
        
        print("\n🎵 Probando diferentes configuraciones de reducción de silencios...\n")
        
        # Configuraciones de prueba
        test_configs = [
            {
                "name": "Sin reducción de silencios",
                "filename": "locutor_sin_reduccion",
                "reduce_silences": False,
                "max_silence": 0.7
            },
            {
                "name": "Reducción a 0.7 segundos",
                "filename": "locutor_reducido_0.7s",
                "reduce_silences": True,
                "max_silence": 0.7
            },
            {
                "name": "Reducción a 0.5 segundos",
                "filename": "locutor_reducido_0.5s",
                "reduce_silences": True,
                "max_silence": 0.5
            },
            {
                "name": "Reducción a 1.0 segundo",
                "filename": "locutor_reducido_1.0s",
                "reduce_silences": True,
                "max_silence": 1.0
            }
        ]
        
        results = []
        
        for config in test_configs:
            print(f"🔧 Procesando: {config['name']}")
            
            result = locutor_processor.unify_locutor_audio(
                export_path=output_folder,
                export_filename=config['filename'],
                reduce_silences=config['reduce_silences'],
                max_silence_duration=config['max_silence']
            )
            
            duration_seconds = result.duration_ms / 1000
            results.append({
                'name': config['name'],
                'filename': f"{config['filename']}.mp3",
                'duration': duration_seconds,
                'files_loaded': len(result.files_loaded),
                'files_skipped': len(result.files_skipped)
            })
            
            print(f"   ✓ Duración: {duration_seconds:.2f}s")
            print(f"   ✓ Archivos: {len(result.files_loaded)} cargados, {len(result.files_skipped)} omitidos")
            print()
        
        # Mostrar comparación de resultados
        print("📊 COMPARACIÓN DE RESULTADOS:")
        print("=" * 80)
        print(f"{'Configuración':<30} {'Archivo':<25} {'Duración':<12} {'Archivos'}")
        print("-" * 80)
        
        for result in results:
            print(f"{result['name']:<30} {result['filename']:<25} "
                  f"{result['duration']:>8.2f}s    {result['files_loaded']}/{result['files_loaded'] + result['files_skipped']}")
        
        # Calcular tiempo ahorrado
        if len(results) >= 2:
            original_duration = results[0]['duration']  # Sin reducción
            reduced_duration = results[1]['duration']   # Con reducción a 0.7s
            time_saved = original_duration - reduced_duration
            percentage_saved = (time_saved / original_duration) * 100 if original_duration > 0 else 0
            
            print(f"\n💡 ANÁLISIS:")
            print(f"   • Tiempo original: {original_duration:.2f}s")
            print(f"   • Tiempo con reducción (0.7s): {reduced_duration:.2f}s")
            print(f"   • Tiempo ahorrado: {time_saved:.2f}s ({percentage_saved:.1f}%)")
        
        print(f"\n🎧 Archivos generados para análisis:")
        for result in results:
            output_file = output_folder / result['filename']
            if output_file.exists():
                size_mb = output_file.stat().st_size / 1024 / 1024
                print(f"   📁 {result['filename']} ({size_mb:.2f} MB)")
        
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_silence_reduction()