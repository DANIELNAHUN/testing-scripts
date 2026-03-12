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
                           reduce_silences: bool = True, max_silence_duration: float = 0.7,
                           normalize_volume: bool = False, target_dbfs: float = -20.0,
                           apply_soft_echo: bool = True, echo_delay_ms: int = 150, echo_decay: float = 0.3,
                           increase_volume: bool = True, volume_increase_db: float = 3.0) -> LocutorResult:
        """
        Unifica los archivos de locutor en el orden especificado.

        Carga cada archivo en la secuencia LOCUTOR_SEQUENCE, omite los archivos
        que no existen, y concatena los archivos disponibles en orden.
        Opcionalmente reduce silencios largos para mejorar el flujo del audio,
        normaliza el volumen para mantener consistencia, aplica eco suave y
        aumenta el volumen general.

        Args:
            export_path: Ruta opcional donde exportar el audio unificado como MP3
            export_filename: Nombre del archivo de exportación (sin extensión)
            reduce_silences: Si True, reduce silencios largos a max_silence_duration
            max_silence_duration: Duración máxima permitida para silencios en segundos
            normalize_volume: Si True, normaliza el volumen de todos los archivos
            target_dbfs: Nivel de volumen objetivo en dBFS para la normalización
            apply_soft_echo: Si True, aplica un filtro de eco suave al audio final
            echo_delay_ms: Retraso del eco en milisegundos (default: 150ms)
            echo_decay: Factor de decaimiento del eco (0.0-1.0, default: 0.3)
            increase_volume: Si True, aumenta el volumen general del audio final
            volume_increase_db: Incremento de volumen en dB (default: 3.0dB)

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
                # Normalizar volumen si está habilitado
                if normalize_volume:
                    original_dbfs = audio.dBFS
                    audio = self._normalize_volume(audio, target_dbfs)
                    logger.debug(f"Volume normalized for {filename}: {original_dbfs:.1f}dBFS → {audio.dBFS:.1f}dBFS")

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

        # Aplicar eco suave si está habilitado
        if apply_soft_echo:
            logger.info(f"Applying soft echo (delay: {echo_delay_ms}ms, decay: {echo_decay})")
            unified_audio = self._apply_soft_echo(unified_audio, echo_delay_ms, echo_decay)

        # Aumentar volumen general si está habilitado
        if increase_volume:
            logger.info(f"Increasing overall volume by {volume_increase_db}dB")
            unified_audio = self._increase_overall_volume(unified_audio, volume_increase_db)

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

    def _normalize_volume(self, audio: AudioSegment, target_dbfs: float = -20.0) -> AudioSegment:
        """
        Normaliza el volumen del audio a un nivel objetivo específico.
        
        Ajusta el volumen del audio para que tenga un nivel de dBFS consistente,
        lo que ayuda a mantener un volumen uniforme entre diferentes archivos.
        
        Args:
            audio: AudioSegment a normalizar
            target_dbfs: Nivel objetivo en dBFS (valores típicos: -20.0 a -12.0)
        
        Returns:
            AudioSegment con volumen normalizado
        """
        if len(audio) == 0:
            return audio
        
        # Calcular el cambio necesario en dB
        current_dbfs = audio.dBFS
        
        # Si el audio está completamente silencioso, no se puede normalizar
        if current_dbfs == float('-inf'):
            logger.warning("Cannot normalize silent audio segment")
            return audio
        
        # Calcular el ajuste necesario
        db_change = target_dbfs - current_dbfs
        
        # Aplicar el cambio de volumen
        normalized_audio = audio + db_change
        
        logger.debug(f"Volume normalization: {current_dbfs:.1f}dBFS → {normalized_audio.dBFS:.1f}dBFS (change: {db_change:+.1f}dB)")
        
        return normalized_audio
    def _apply_soft_echo(self, audio: AudioSegment, delay_ms: int = 150, decay: float = 0.3) -> AudioSegment:
        """
        Aplica un filtro de eco suave al audio.

        Args:
            audio: AudioSegment al que aplicar el eco
            delay_ms: Retraso del eco en milisegundos (default: 150ms)
            decay: Factor de decaimiento del eco (0.0-1.0, default: 0.3)

        Returns:
            AudioSegment con eco suave aplicado
        """
        logger.debug(f"Applying soft echo: delay={delay_ms}ms, decay={decay}")

        # Crear el eco reduciendo el volumen del audio original
        echo = audio - (20 * (1 - decay))  # Reducir volumen según el decay

        # Crear silencio para el delay
        silence = AudioSegment.silent(duration=delay_ms)

        # Combinar silencio + eco para crear el retraso
        delayed_echo = silence + echo

        # Superponer el audio original con el eco retrasado
        # Asegurar que ambos tengan la misma duración
        max_length = max(len(audio), len(delayed_echo))

        # Extender el audio original si es necesario
        if len(audio) < max_length:
            audio = audio + AudioSegment.silent(duration=max_length - len(audio))

        # Truncar el eco si es más largo
        if len(delayed_echo) > max_length:
            delayed_echo = delayed_echo[:max_length]

        # Combinar audio original con eco
        result = audio.overlay(delayed_echo)

        logger.debug(f"Soft echo applied: original={len(audio)}ms, result={len(result)}ms")
        return result

    def _increase_overall_volume(self, audio: AudioSegment, volume_increase_db: float = 3.0) -> AudioSegment:
        """
        Aumenta el volumen general del audio.

        Args:
            audio: AudioSegment al que aumentar el volumen
            volume_increase_db: Incremento de volumen en dB (default: 3.0dB)

        Returns:
            AudioSegment con volumen aumentado
        """
        logger.debug(f"Increasing overall volume by {volume_increase_db}dB")

        original_dbfs = audio.dBFS
        result = audio + volume_increase_db
        new_dbfs = result.dBFS

        logger.debug(f"Volume increased: {original_dbfs:.1f}dBFS → {new_dbfs:.1f}dBFS")
        return result


    def calculate_optimal_target_volume(self, filenames: Optional[List[str]] = None) -> float:
        """
        Calcula el nivel de volumen objetivo óptimo basado en los archivos disponibles.
        
        Analiza todos los archivos de locutor disponibles y calcula un nivel de volumen
        que represente un punto medio entre todos ellos, evitando tanto archivos muy
        silenciosos como muy fuertes.
        
        Args:
            filenames: Lista opcional de archivos a analizar. Si es None, usa LOCUTOR_SEQUENCE
        
        Returns:
            Nivel objetivo en dBFS calculado como punto medio
        """
        if filenames is None:
            filenames = self.LOCUTOR_SEQUENCE
        
        logger.info("Calculating optimal target volume from available files")
        
        volume_levels = []
        analyzed_files = []
        
        # Analizar cada archivo disponible
        for filename in filenames:
            audio = self.file_loader.load_audio(filename)
            if audio is not None and len(audio) > 0:
                dbfs = audio.dBFS
                if dbfs != float('-inf'):  # Ignorar archivos completamente silenciosos
                    volume_levels.append(dbfs)
                    analyzed_files.append(filename)
                    logger.debug(f"Analyzed {filename}: {dbfs:.1f}dBFS")
        
        if not volume_levels:
            logger.warning("No valid audio files found for volume analysis, using default target")
            return -20.0
        
        # Calcular estadísticas
        min_volume = min(volume_levels)
        max_volume = max(volume_levels)
        avg_volume = sum(volume_levels) / len(volume_levels)
        
        # Usar el promedio como punto medio, pero limitado a un rango razonable
        target_volume = max(-25.0, min(-12.0, avg_volume))
        
        logger.info(f"Volume analysis complete:")
        logger.info(f"  Files analyzed: {len(analyzed_files)}")
        logger.info(f"  Volume range: {min_volume:.1f}dBFS to {max_volume:.1f}dBFS")
        logger.info(f"  Average volume: {avg_volume:.1f}dBFS")
        logger.info(f"  Calculated target: {target_volume:.1f}dBFS")
        logger.info(f"  Files: {analyzed_files}")
        
        return target_volume

    def unify_locutor_audio_with_auto_volume(self, export_path: Optional[Path] = None, 
                                           export_filename: str = "locutor_unificado",
                                           reduce_silences: bool = True, 
                                           max_silence_duration: float = 0.7,
                                           apply_soft_echo: bool = True, echo_delay_ms: int = 150, echo_decay: float = 0.3,
                                           increase_volume: bool = True, volume_increase_db: float = 3.0) -> LocutorResult:
        """
        Unifica archivos de locutor con normalización automática de volumen.

        Esta es una versión conveniente que calcula automáticamente el nivel de volumen
        óptimo basado en todos los archivos disponibles y luego los normaliza a ese nivel.
        También aplica eco suave y aumento de volumen general.

        Args:
            export_path: Ruta opcional donde exportar el audio unificado como MP3
            export_filename: Nombre del archivo de exportación (sin extensión)
            reduce_silences: Si True, reduce silencios largos a max_silence_duration
            max_silence_duration: Duración máxima permitida para silencios en segundos
            apply_soft_echo: Si True, aplica un filtro de eco suave al audio final
            echo_delay_ms: Retraso del eco en milisegundos (default: 150ms)
            echo_decay: Factor de decaimiento del eco (0.0-1.0, default: 0.3)
            increase_volume: Si True, aumenta el volumen general del audio final
            volume_increase_db: Incremento de volumen en dB (default: 3.0dB)

        Returns:
            LocutorResult con el audio unificado y volumen normalizado automáticamente
        """
        logger.info("Starting locutor unification with automatic volume normalization")

        # Calcular el nivel de volumen óptimo
        optimal_target = self.calculate_optimal_target_volume()

        # Procesar con el nivel calculado
        return self.unify_locutor_audio(
            export_path=export_path,
            export_filename=export_filename,
            reduce_silences=reduce_silences,
            max_silence_duration=max_silence_duration,
            normalize_volume=True,
            target_dbfs=optimal_target,
            apply_soft_echo=apply_soft_echo,
            echo_delay_ms=echo_delay_ms,
            echo_decay=echo_decay,
            increase_volume=increase_volume,
            volume_increase_db=volume_increase_db
        )
