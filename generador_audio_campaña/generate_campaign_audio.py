#!/usr/bin/env python3
"""
Campaign Audio Generator using ElevenLabs

This script generates campaign audio announcements using ElevenLabs text-to-speech API.
It creates both "ESTE" and "HOY" versions of the announcement.
"""
import os
import argparse
import sys
from pathlib import Path

from src.elevenlabs_generator import ElevenLabsGenerator, CampaignParams
from src.exceptions import AudioProcessingError
from src.logger_config import get_logger
from load_dotenv import load_dotenv

load_dotenv()


logger = get_logger('campaign_generator')


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate campaign audio using ElevenLabs TTS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_campaign_audio.py --fecha "DOMINGO 15 DE MARZO" --hora "5:30 PM" --lugar "PLAZA DE LA BANDERA" --referencia "CERCA AL OVALO"
  
  python generate_campaign_audio.py -f "LUNES 20 DE ABRIL" -t "6:00 PM" -l "PARQUE CENTRAL" -r "FRENTE AL MUNICIPIO" -o output/
        """
    )
    
    parser.add_argument(
        '-f', '--fecha',
        type=str,
        required=True,
        help='Fecha del evento (ej: "DOMINGO 15 DE MARZO")'
    )
    
    parser.add_argument(
        '-t', '--hora',
        type=str,
        required=True,
        help='Hora del evento (ej: "5:30 PM (cinco y treinta de la tarde)")'
    )
    
    parser.add_argument(
        '-l', '--lugar',
        type=str,
        required=True,
        help='Lugar del evento (ej: "PLAZA DE LA BANDERA")'
    )
    
    parser.add_argument(
        '-r', '--referencia',
        type=str,
        required=True,
        help='Referencia del lugar (ej: "CERCA AL OVALO")'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='files/campaign_audio',
        help='Carpeta de salida para los audios generados (default: files/campaign_audio)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='ElevenLabs API key (si no se proporciona, se usa la variable de entorno ELEVEN_API_KEY)'
    )
    
    parser.add_argument(
        '--voice-id',
        type=str,
        default='JBFqnCBsd6RMkjVDRZzb',
        help='ID de la voz a usar (default: Free voice)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='eleven_multilingual_v2',
        help='Modelo de ElevenLabs a usar (default: eleven_multilingual_v2)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        default='mp3_44100_128',
        help='Formato de salida del audio (default: mp3_44100_128)'
    )
    
    parser.add_argument(
        '--version',
        choices=['este', 'hoy', 'both'],
        default='both',
        help='Versión a generar: "este", "hoy" o "both" (default: both)'
    )
    
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Solo probar la conexión con la API de ElevenLabs'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Habilitar logging detallado'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Get API key
        api_key = args.api_key
        if not api_key:
            import os
            api_key = os.getenv('ELEVEN_API_KEY')
            if not api_key:
                print("❌ Error: API key requerida. Usa --api-key o configura ELEVEN_API_KEY")
                print("💡 Ejemplo: export ELEVEN_API_KEY='sk_4b6af8e14011994fcd5e9e6488e387525ec0098b5d7c6489'")
                sys.exit(1)
        
        # Initialize generator
        generator = ElevenLabsGenerator(api_key, args.voice_id)
        
        # Test connection if requested
        if args.test_connection:
            print("🔄 Probando conexión con ElevenLabs API...")
            if generator.test_connection():
                print("✅ Conexión exitosa con ElevenLabs API")
                sys.exit(0)
            else:
                print("❌ Error: No se pudo conectar con ElevenLabs API")
                sys.exit(1)
        
        # Create campaign parameters
        params = CampaignParams(
            fecha=args.fecha,
            hora=args.hora,
            lugar=args.lugar,
            referencia=args.referencia
        )
        
        # Create output folder
        output_folder = Path(args.output).resolve()
        output_folder.mkdir(parents=True, exist_ok=True)
        
        print("🎵 Generador de Audio de Campaña - ElevenLabs")
        print("="*50)
        print(f"📅 Fecha: {params.fecha}")
        print(f"🕐 Hora: {params.hora}")
        print(f"📍 Lugar: {params.lugar}")
        print(f"🗺️  Referencia: {params.referencia}")
        print(f"📁 Carpeta de salida: {output_folder}")
        print(f"🎤 Voz ID: {args.voice_id}")
        print(f"🤖 Modelo: {args.model}")
        print("="*50)
        
        # Generate audio based on version selection
        if args.version == 'both':
            print("\n🔄 Generando ambas versiones (ESTE y HOY)...")
            results = generator.generate_both_versions(
                params, output_folder, args.model, args.format
            )
            
            print("\n✅ Generación completada:")
            print(f"📄 Versión ESTE: {results['este']}")
            print(f"📄 Versión HOY: {results['hoy']}")
            
        else:
            use_today = args.version == 'hoy'
            version_name = "HOY" if use_today else "ESTE"
            
            print(f"\n🔄 Generando versión {version_name}...")
            result_path = generator.generate_campaign_audio(
                params, output_folder, use_today, args.model, args.format
            )
            
            print(f"\n✅ Generación completada:")
            print(f"📄 Archivo: {result_path}")
        
        print("\n🎉 ¡Audio de campaña generado exitosamente!")
        
    except AudioProcessingError as e:
        logger.error(f"Error de procesamiento de audio: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Generación interrumpida por el usuario")
        print("\n⏹️  Generación interrumpida por el usuario")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        print(f"\n💥 Error inesperado: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()