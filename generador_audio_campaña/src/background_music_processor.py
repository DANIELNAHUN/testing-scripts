"""
BackgroundMusicProcessor component for Audio Gran Campaña.

Este módulo procesa fondos musicales con efectos de volumen y transiciones,
incluyendo fade effects y crossfade entre múltiples fondos.
"""

from pydub import AudioSegment

from src.file_loader import FileLoader
from src.logger_config import get_logger


logger = get_logger('background_music_processor')


class BackgroundMusicProcessor:
    """
    Procesa fondos musicales con efectos de volumen y transiciones.
    
    Maneja el procesamiento de dos fondos musicales con efectos específicos
    de volumen y los unifica con una transición crossfade suave.
    """
    
    # Constantes de archivos y configuración
    FIRST_BACKGROUND = 'Yo tengo un amigo que me ama.mp3'
    SECOND_BACKGROUND = 'Eres todo Poderoso.mp3'
    CROSSFADE_DURATION = 3000  # milliseconds
    
    def __init__(self, file_loader: FileLoader):
        """
        Inicializa el processor con un FileLoader.
        
        Args:
            file_loader: Instancia de FileLoader para cargar archivos de audio
        """
        self.file_loader = file_loader
        logger.info("BackgroundMusicProcessor initialized")
    
    def process_first_background(self) -> AudioSegment:
        """
        Procesa el primer fondo musical con efectos de volumen específicos.
        
        Aplica los siguientes efectos:
        - 100% volumen a los primeros 4 segundos
        - Fade de 100% a 25% entre segundo 4 y 5
        - 25% volumen al resto del audio
        
        Returns:
            AudioSegment con el primer fondo musical procesado
        
        Raises:
            Exception si el archivo no existe o no se puede cargar
        """
        logger.info(f"Processing first background: {self.FIRST_BACKGROUND}")
        
        # Cargar el archivo de audio
        audio = self.file_loader.load_audio(self.FIRST_BACKGROUND)
        
        if audio is None:
            error_msg = f"First background file not found: {self.FIRST_BACKGROUND}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        duration_ms = len(audio)
        logger.info(f"First background loaded: duration={duration_ms}ms")
        
        # Definir puntos de tiempo en milisegundos
        first_section_end = 4000  # 4 segundos
        fade_end = 5000  # 5 segundos
        
        # Sección 1: Primeros 4 segundos a 100% volumen
        section_1 = audio[:first_section_end]
        
        # Sección 2: Fade de 100% a 25% entre segundo 4 y 5
        section_2 = audio[first_section_end:fade_end]
        # Aplicar fade out de 0dB (100%) a -12dB (aproximadamente 25%)
        # -12dB = 25% de volumen (20 * log10(0.25) ≈ -12dB)
        section_2_faded = section_2.fade(to_gain=-12.0, start=0, end=len(section_2))
        
        # Sección 3: Resto del audio a 25% volumen
        section_3 = audio[fade_end:]
        # Aplicar -12dB para mantener 25% volumen
        section_3_reduced = section_3 - 12.0
        
        # Concatenar todas las secciones
        processed_audio = section_1 + section_2_faded + section_3_reduced
        
        logger.info(f"First background processed: duration={len(processed_audio)}ms")
        logger.debug(f"Section 1 (100%): 0-{first_section_end}ms")
        logger.debug(f"Section 2 (fade 100%-25%): {first_section_end}-{fade_end}ms")
        logger.debug(f"Section 3 (25%): {fade_end}-{duration_ms}ms")
        
        return processed_audio

    def calculate_second_background_duration(
        self,
        locutor_duration_ms: int,
        first_bg_duration_ms: int
    ) -> int:
        """
        Calcula la duración requerida del segundo fondo musical.

        Implementa la fórmula: locutor_duration + 10s - first_bg_duration + 3s
        Los 3 segundos adicionales compensan el crossfade que se aplicará.

        Args:
            locutor_duration_ms: Duración del locutor unificado en milisegundos
            first_bg_duration_ms: Duración del primer fondo musical en milisegundos

        Returns:
            Duración calculada en milisegundos para el segundo fondo musical
        """
        # Fórmula: locutor_duration + 10000ms - first_bg_duration + 3000ms
        calculated_duration = (
            locutor_duration_ms + 10000 - first_bg_duration_ms + 3000
        )

        logger.info(
            f"Calculated second background duration: {calculated_duration}ms "
            f"(locutor={locutor_duration_ms}ms + 10000ms - "
            f"first_bg={first_bg_duration_ms}ms + 3000ms)"
        )

        return calculated_duration

    def process_second_background(self, required_duration_ms: int) -> AudioSegment:
        """
        Procesa el segundo fondo musical con efectos de volumen específicos.
        
        Aplica los siguientes efectos:
        - Recorta a la duración calculada (o usa duración completa si es menor)
        - 20% volumen hasta 5 segundos antes del final
        - Fade in de 20% a 100% en 1 segundo (de -5s a -4s)
        - 100% volumen en los últimos 4 segundos
        
        Args:
            required_duration_ms: Duración requerida en milisegundos
        
        Returns:
            AudioSegment con el segundo fondo musical procesado
        
        Raises:
            FileNotFoundError si el archivo no existe o no se puede cargar
        """
        logger.info(f"Processing second background: {self.SECOND_BACKGROUND}")
        logger.info(f"Required duration: {required_duration_ms}ms")
        
        # Cargar el archivo de audio
        audio = self.file_loader.load_audio(self.SECOND_BACKGROUND)
        
        if audio is None:
            error_msg = f"Second background file not found: {self.SECOND_BACKGROUND}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        original_duration_ms = len(audio)
        logger.info(f"Second background loaded: duration={original_duration_ms}ms")
        
        # Verificar si el archivo tiene duración suficiente
        if original_duration_ms < required_duration_ms:
            logger.warning(
                f"Second background is shorter than required "
                f"({original_duration_ms}ms < {required_duration_ms}ms). "
                f"Using complete available duration."
            )
            actual_duration_ms = original_duration_ms
        else:
            actual_duration_ms = required_duration_ms
        
        # Recortar a la duración calculada
        audio = audio[:actual_duration_ms]
        logger.info(f"Second background trimmed to: {actual_duration_ms}ms")
        
        # Definir puntos de tiempo en milisegundos
        fade_start = actual_duration_ms - 5000  # 5 segundos antes del final
        fade_end = actual_duration_ms - 4000    # 4 segundos antes del final (1 segundo de fade)
        
        # Sección 1: Desde el inicio hasta 5 segundos antes del final a 20% volumen
        # 20% volumen = -14dB (20 * log10(0.20) ≈ -14dB)
        section_1 = audio[:fade_start]
        section_1_reduced = section_1 - 14.0
        
        # Sección 2: Fade in de 20% a 100% en 1 segundo + últimos 4 segundos a 100%
        section_2 = audio[fade_start:]
        # Aplicar fade de -14dB (20%) a 0dB (100%) solo en el primer segundo
        fade_duration = 1000  # 1 segundo
        section_2_faded = section_2.fade(from_gain=-14.0, to_gain=0.0, start=0, end=fade_duration)
        
        # Concatenar ambas secciones
        processed_audio = section_1_reduced + section_2_faded
        
        logger.info(f"Second background processed: duration={len(processed_audio)}ms")
        logger.debug(f"Section 1 (20%): 0-{fade_start}ms")
        logger.debug(f"Section 2 (fade in 1s + 100%): {fade_start}-{actual_duration_ms}ms")
        
        return processed_audio

    def unify_backgrounds(
        self,
        first_bg: AudioSegment,
        second_bg: AudioSegment
    ) -> 'BackgroundResult':
        """
        Unifica ambos fondos musicales con crossfade de 3 segundos.

        Aplica una transición crossfade suave entre el primer y segundo fondo musical,
        donde los últimos 3 segundos del primer fondo se superponen con los primeros
        3 segundos del segundo fondo.

        Args:
            first_bg: Primer fondo musical procesado
            second_bg: Segundo fondo musical procesado

        Returns:
            BackgroundResult con el audio unificado y metadata completa
        """
        logger.info("Unifying background music with crossfade")

        # Obtener duraciones de ambos fondos
        first_duration_ms = len(first_bg)
        second_duration_ms = len(second_bg)

        logger.info(f"First background duration: {first_duration_ms}ms")
        logger.info(f"Second background duration: {second_duration_ms}ms")
        logger.info(f"Applying crossfade of {self.CROSSFADE_DURATION}ms")

        # Aplicar crossfade usando pydub.append con crossfade parameter
        # El crossfade superpone los últimos N ms del primer audio con los primeros N ms del segundo
        unified_audio = first_bg.append(second_bg, crossfade=self.CROSSFADE_DURATION)

        # Calcular duración total del fondo unificado
        # Duración = first_duration + second_duration - crossfade_duration
        unified_duration_ms = len(unified_audio)

        logger.info(f"Unified background duration: {unified_duration_ms}ms")
        logger.info(
            f"Expected duration: {first_duration_ms + second_duration_ms - self.CROSSFADE_DURATION}ms"
        )

        # Importar BackgroundResult aquí para evitar import circular
        from src.models import BackgroundResult

        # Crear y retornar BackgroundResult con metadata completa
        result = BackgroundResult(
            audio=unified_audio,
            duration_ms=unified_duration_ms,
            first_bg_duration_ms=first_duration_ms,
            second_bg_duration_ms=second_duration_ms,
            crossfade_applied=True
        )

        logger.info("Background music unification completed successfully")

        return result


