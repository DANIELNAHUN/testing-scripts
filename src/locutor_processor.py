"""
LocutorProcessor component for Audio Gran Campaña.

Este módulo procesa y unifica archivos de audio de locutor en un orden específico,
manejando archivos faltantes de manera elegante.
"""

from typing import List, Optional
from pathlib import Path
from pydub import AudioSegment

from src.file_loader import FileLoader
from src.models import LocutorResult
from src.logger_config import get_logger
from src.audio_exporter import AudioExporter


logger = get_logger('locutor_processor')


class LocutorProcessor:
    """
    Procesa y unifica archivos de audio de locutor.
    
    Concatena múltiples archivos de locutor en un orden específico,
    omitiendo archivos faltantes y continuando con los siguientes.
    """
    
    # Secuencia específica de archivos de locutor en orden
    LOCUTOR_SEQUENCE = [
        'Gran Campaña - Introduccion.wav',
        'Gran Campaña - Hora y lugar del evento.mp3',
        'Gran Campaña - Cuerpo.mp3',
        'Gran Campaña - Hora y lugar del evento.mp3',
        'Gran Campaña - Cierre.mp3'
    ]
    
    def __init__(self, file_loader: FileLoader):
        """
        Inicializa el processor con un FileLoader.
        
        Args:
            file_loader: Instancia de FileLoader para cargar archivos de audio
        """
        self.file_loader = file_loader
        logger.info("LocutorProcessor initialized")
    
    def unify_locutor_audio(self, export_path: Optional[Path] = None, export_filename: str = "locutor_unificado", 
                           reduce_silences: bool = True, max_silence_duration: float = 0.7) -> LocutorResult:
        """
        Unifica los archivos de locutor en el orden especificado.
        
        Carga cada archivo en la secuencia LOCUTOR_SEQUENCE, omite los archivos
        que no existen, y concatena los archivos disponibles en orden.
        Opcionalmente reduce silencios largos para mejorar el flujo del audio.
        
        Args:
            export_path: Ruta opcional donde exportar el audio unificado como MP3
            export_filename: Nombre del archivo de exportación (sin extensión)
            reduce_silences: Si True, reduce silencios largos a max_silence_duration
            max_silence_duration: Duración máxima permitida para silencios en segundos
        
        Returns:
            LocutorResult con el audio unificado y metadata completa
        """
        logger.info(f"Starting locutor unification with {len(self.LOCUTOR_SEQUENCE)} files in sequence")
        
        files_loaded: List[str] = []
        files_skipped: List[str] = []
        audio_segments: List[AudioSegment] = []
        
        # Cargar archivos en orden
        for filename in self.LOCUTOR_SEQUENCE:
            audio = self.file_loader.load_audio(filename)
            
            if audio is not None:
                audio_segments.append(audio)
                files_loaded.append(filename)
                logger.debug(f"Added to sequence: {filename}")
            else:
                files_skipped.append(filename)
                logger.debug(f"Skipped (not found): {filename}")
        
        # Concatenar todos los segmentos de audio
        if not audio_segments:
            logger.error("No locutor files were loaded")
            # Retornar un resultado vacío con audio silencioso de 0ms
            empty_audio = AudioSegment.silent(duration=0)
            return LocutorResult(
                audio=empty_audio,
                duration_ms=0,
                files_loaded=files_loaded,
                files_skipped=files_skipped
            )
        
        # Concatenar segmentos
        unified_audio = audio_segments[0]
        for segment in audio_segments[1:]:
            unified_audio += segment
        
        # Reducir silencios largos si está habilitado
        if reduce_silences:
            logger.info(f"Applying silence reduction (max duration: {max_silence_duration}s)")
            original_duration = len(unified_audio)
            unified_audio = self._reduce_long_silences(unified_audio, max_silence_duration)
            new_duration = len(unified_audio)
            
            if new_duration != original_duration:
                logger.info(f"Silence reduction applied: {original_duration}ms → {new_duration}ms "
                           f"(reduced by {original_duration - new_duration}ms)")
        
        duration_ms = len(unified_audio)
        
        logger.info(f"Locutor unification complete: {len(files_loaded)} files loaded, "
                   f"{len(files_skipped)} files skipped, total duration: {duration_ms}ms")
        logger.info(f"Files loaded: {files_loaded}")
        logger.info(f"Files skipped: {files_skipped}")
        
        # Exportar a MP3 si se especifica una ruta
        if export_path is not None:
            try:
                exporter = AudioExporter(export_path)
                exported_file = exporter.export(unified_audio, export_filename)
                logger.info(f"Audio unificado exportado a: {exported_file}")
            except Exception as e:
                logger.error(f"Error al exportar audio unificado: {str(e)}")
                # No interrumpir el proceso, solo registrar el error
        
        return LocutorResult(
            audio=unified_audio,
            duration_ms=duration_ms,
            files_loaded=files_loaded,
            files_skipped=files_skipped
        )

    def _reduce_long_silences(self, audio: AudioSegment, max_silence_duration: float = 0.7,
                             silence_threshold: int = -40) -> AudioSegment:
        """
        Reduce silencios largos en el audio a una duración máxima especificada.

        Detecta segmentos de silencio que excedan max_silence_duration y los reduce
        a esa duración máxima, manteniendo una transición natural.

        Args:
            audio: AudioSegment a procesar
            max_silence_duration: Duración máxima permitida para silencios en segundos
            silence_threshold: Umbral de silencio en dBFS (valores más negativos = más silencioso)

        Returns:
            AudioSegment con silencios largos reducidos
        """
        if len(audio) == 0:
            return audio

        logger.info(f"Reducing long silences (max: {max_silence_duration}s, threshold: {silence_threshold}dBFS)")

        # Convertir duración máxima a milisegundos
        max_silence_ms = int(max_silence_duration * 1000)

        # Detectar segmentos de silencio
        silence_ranges = []
        chunk_size = 10  # Analizar en chunks de 10ms para mayor precisión

        i = 0
        while i < len(audio):
            chunk_end = min(i + chunk_size, len(audio))
            chunk = audio[i:chunk_end]

            # Verificar si el chunk está en silencio
            if chunk.dBFS < silence_threshold:
                # Inicio de un posible silencio
                silence_start = i

                # Continuar hasta encontrar el final del silencio
                while i < len(audio):
                    chunk_end = min(i + chunk_size, len(audio))
                    chunk = audio[i:chunk_end]

                    if chunk.dBFS >= silence_threshold:
                        # Final del silencio encontrado
                        break
                    i += chunk_size

                silence_end = i
                silence_duration = silence_end - silence_start

                # Solo procesar silencios que excedan la duración máxima
                if silence_duration > max_silence_ms:
                    silence_ranges.append((silence_start, silence_end, silence_duration))
                    logger.debug(f"Long silence detected: {silence_duration}ms at {silence_start}-{silence_end}ms")

            i += chunk_size

        if not silence_ranges:
            logger.info("No long silences detected")
            return audio

        logger.info(f"Found {len(silence_ranges)} long silences to reduce")

        # Construir nuevo audio reduciendo silencios largos
        result_audio = AudioSegment.empty()
        last_end = 0

        for silence_start, silence_end, silence_duration in silence_ranges:
            # Agregar audio antes del silencio
            result_audio += audio[last_end:silence_start]

            # Agregar silencio reducido
            reduced_silence = AudioSegment.silent(duration=max_silence_ms)
            result_audio += reduced_silence

            logger.debug(f"Reduced silence from {silence_duration}ms to {max_silence_ms}ms")
            last_end = silence_end

        # Agregar el resto del audio después del último silencio
        result_audio += audio[last_end:]

        original_duration = len(audio) / 1000
        new_duration = len(result_audio) / 1000
        time_saved = original_duration - new_duration

        logger.info(f"Silence reduction complete: {original_duration:.2f}s → {new_duration:.2f}s "
                   f"(saved {time_saved:.2f}s)")

        return result_audio
