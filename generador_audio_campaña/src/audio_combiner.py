"""
AudioCombiner component for Audio Gran Campaña.

Este módulo combina el locutor unificado con el fondo musical unificado,
aplicando overlay y efectos de volumen para crear el audio final.
"""

from pydub import AudioSegment

from src.logger_config import get_logger


logger = get_logger('audio_combiner')


class AudioCombiner:
    """
    Combina el locutor unificado con el fondo musical unificado.
    
    Maneja el overlay del locutor sobre el fondo musical con timing específico
    y aplica efectos de volumen al fondo cuando termina el locutor.
    """
    
    # Constante de configuración
    LOCUTOR_START_OFFSET = 5000  # milliseconds
    
    def __init__(self):
        """Inicializa el combiner."""
        logger.info("AudioCombiner initialized")
    
    def combine(
        self,
        locutor: AudioSegment,
        background: AudioSegment
    ) -> AudioSegment:
        """
        Combina el locutor con el fondo musical.
        
        Aplica los siguientes efectos:
        - Locutor inicia a los 5 segundos del fondo
        - Locutor mantiene 100% volumen
        - Fondo musical hace fade a 100% UN SEGUNDO ANTES de que termine el locutor
        - El volumen máximo del fondo se mantiene hasta el final del audio
        
        Args:
            locutor: AudioSegment del locutor unificado
            background: AudioSegment del fondo musical unificado
        
        Returns:
            AudioSegment con el audio final combinado
        """
        logger.info("Combining locutor with background music")
        
        locutor_duration_ms = len(locutor)
        background_duration_ms = len(background)
        
        logger.info(f"Locutor duration: {locutor_duration_ms}ms")
        logger.info(f"Background duration: {background_duration_ms}ms")
        logger.info(f"Locutor will start at: {self.LOCUTOR_START_OFFSET}ms")
        
        # Calcular cuándo termina el locutor en el timeline del fondo
        locutor_end_position = self.LOCUTOR_START_OFFSET + locutor_duration_ms
        logger.info(f"Locutor will end at: {locutor_end_position}ms")
        
        # Calcular cuándo debe empezar el fade (1 segundo antes de que termine el locutor)
        fade_start_advance_ms = 1000  # 1 segundo antes
        fade_start_position = locutor_end_position - fade_start_advance_ms
        
        # Asegurar que el fade no empiece antes del inicio del locutor
        if fade_start_position < self.LOCUTOR_START_OFFSET:
            fade_start_position = self.LOCUTOR_START_OFFSET
            logger.warning(f"Fade start adjusted to locutor start position: {fade_start_position}ms")
        
        logger.info(f"Background volume fade will start at: {fade_start_position}ms (1s before locutor ends)")
        
        # Aplicar incremento gradual de volumen al fondo musical
        if fade_start_position < background_duration_ms:
            # Dividir el fondo en tres partes: antes del fade, fade, y después del fade
            background_before_fade = background[:fade_start_position]
            background_fade_and_after = background[fade_start_position:]
            
            # Calcular duración del fade (desde 1s antes del final del locutor hasta el final del locutor)
            fade_duration_ms = min(locutor_end_position - fade_start_position, len(background_fade_and_after))
            
            if fade_duration_ms > 0 and len(background_fade_and_after) > 0:
                # Dividir el segmento de fade y después en dos partes
                if len(background_fade_and_after) > fade_duration_ms:
                    fade_segment = background_fade_and_after[:fade_duration_ms]
                    remaining_segment = background_fade_and_after[fade_duration_ms:]
                else:
                    fade_segment = background_fade_and_after
                    remaining_segment = AudioSegment.silent(duration=0)
                
                # Aplicar fade in gradual al segmento de fade (de volumen actual a +3dB)
                fade_segment = fade_segment.fade_in(len(fade_segment))
                
                # Aumentar el volumen del resto del segmento en +3dB para mayor presencia
                # Este segmento se mantiene con volumen alto hasta el final
                if len(remaining_segment) > 0:
                    remaining_segment = remaining_segment + 3.0  # +3dB de incremento
                
                # Reconstruir el segmento de fade y después
                background_fade_and_after = fade_segment + remaining_segment
            
            # Reconstruir el fondo completo con el fade aplicado
            background_with_fade = background_before_fade + background_fade_and_after
            
            logger.info(f"Applied volume fade to background from {fade_start_position}ms to {fade_start_position + fade_duration_ms}ms")
            logger.info(f"High volume maintained from {fade_start_position + fade_duration_ms}ms to end of audio")
        else:
            background_with_fade = background
            logger.warning(
                f"Fade start position is at or after background ends "
                f"({fade_start_position}ms >= {background_duration_ms}ms). "
                f"No fade applied to background."
            )
        
        # Overlay del locutor sobre el fondo musical
        # El locutor inicia a los 5 segundos (LOCUTOR_START_OFFSET)
        # El locutor mantiene 100% volumen (no se modifica)
        combined_audio = background_with_fade.overlay(
            locutor,
            position=self.LOCUTOR_START_OFFSET
        )
        
        final_duration_ms = len(combined_audio)
        logger.info(f"Audio combination completed: final duration={final_duration_ms}ms")
        
        return combined_audio

    def validate_durations(
        self,
        locutor_duration_ms: int,
        background_duration_ms: int,
        final_duration_ms: int
    ) -> bool:
        """
        Valida que las duraciones sean correctas según los requisitos.

        Verifica:
        - Background debe ser locutor + 10s (con tolerancia de ±100ms)
        - Locutor debe terminar al menos 5s antes del final

        Args:
            locutor_duration_ms: Duración del locutor unificado en milisegundos
            background_duration_ms: Duración del fondo musical unificado en milisegundos
            final_duration_ms: Duración del audio final en milisegundos

        Returns:
            bool: True si todas las validaciones pasan, False si alguna falla
        """
        logger.info("Validating durations")
        logger.info(f"Locutor duration: {locutor_duration_ms}ms")
        logger.info(f"Background duration: {background_duration_ms}ms")
        logger.info(f"Final duration: {final_duration_ms}ms")

        validation_passed = True

        # Validación 1: Background debe ser locutor + 10000ms (con tolerancia de ±100ms)
        expected_background_duration = locutor_duration_ms + 10000
        duration_difference = abs(background_duration_ms - expected_background_duration)
        tolerance_ms = 100

        if duration_difference > tolerance_ms:
            logger.warning(
                f"Background duration validation failed: "
                f"expected {expected_background_duration}ms (locutor + 10s), "
                f"got {background_duration_ms}ms, "
                f"difference: {duration_difference}ms (tolerance: ±{tolerance_ms}ms)"
            )
            validation_passed = False
        else:
            logger.info(
                f"Background duration validation passed: "
                f"{background_duration_ms}ms ≈ {expected_background_duration}ms "
                f"(difference: {duration_difference}ms)"
            )

        # Validación 2: Locutor debe terminar al menos 5000ms antes del final
        # El locutor inicia a los 5000ms (LOCUTOR_START_OFFSET)
        # Por lo tanto, termina en: LOCUTOR_START_OFFSET + locutor_duration_ms
        locutor_end_position = self.LOCUTOR_START_OFFSET + locutor_duration_ms
        time_after_locutor = final_duration_ms - locutor_end_position
        min_time_after_locutor = 5000

        if time_after_locutor < min_time_after_locutor:
            logger.warning(
                f"Locutor end position validation failed: "
                f"locutor ends at {locutor_end_position}ms, "
                f"final audio ends at {final_duration_ms}ms, "
                f"time after locutor: {time_after_locutor}ms "
                f"(minimum required: {min_time_after_locutor}ms)"
            )
            validation_passed = False
        else:
            logger.info(
                f"Locutor end position validation passed: "
                f"locutor ends at {locutor_end_position}ms, "
                f"time after locutor: {time_after_locutor}ms "
                f"(minimum: {min_time_after_locutor}ms)"
            )

        if validation_passed:
            logger.info("All duration validations passed")
        else:
            logger.warning("Duration validation failed - see warnings above")

        return validation_passed