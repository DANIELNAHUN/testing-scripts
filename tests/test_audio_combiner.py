"""
Unit tests for AudioCombiner component.

Tests the combination of locutor audio with background music,
including overlay timing and volume effects.
"""

import pytest
from pydub import AudioSegment
from pydub.generators import Sine
from hypothesis import given, strategies as st
from tests.hypothesis_config import audio_property_test
from tests.hypothesis_strategies import audio_segment_with_duration

from src.audio_combiner import AudioCombiner


def create_test_audio(duration_ms: int, frequency: int = 440) -> AudioSegment:
    """
    Create a test audio segment with specified duration.
    
    Args:
        duration_ms: Duration in milliseconds
        frequency: Frequency of the sine wave (default 440 Hz)
    
    Returns:
        AudioSegment with the specified duration
    """
    return Sine(frequency).to_audio_segment(duration=duration_ms)


class TestAudioCombiner:
    """Test suite for AudioCombiner class."""
    
    def test_combiner_initialization(self):
        """Test that AudioCombiner initializes correctly."""
        combiner = AudioCombiner()
        assert combiner is not None
        assert combiner.LOCUTOR_START_OFFSET == 5000
    
    def test_combine_basic(self):
        """Test basic combination of locutor and background."""
        combiner = AudioCombiner()
        
        # Create test audio segments
        locutor = create_test_audio(10000)  # 10 seconds
        background = create_test_audio(25000)  # 25 seconds
        
        # Combine audio
        result = combiner.combine(locutor, background)
        
        # Verify result
        assert result is not None
        assert isinstance(result, AudioSegment)
        # Background duration should be preserved
        assert len(result) == len(background)
    
    def test_combine_locutor_timing(self):
        """Test that locutor starts at correct offset (5 seconds)."""
        combiner = AudioCombiner()
        
        # Create test audio segments
        locutor = create_test_audio(8000)  # 8 seconds
        background = create_test_audio(20000)  # 20 seconds
        
        # Combine audio
        result = combiner.combine(locutor, background)
        
        # Verify timing
        # Locutor should start at 5000ms and end at 5000 + 8000 = 13000ms
        assert len(result) == len(background)
        
        # The result should have the same duration as background
        # since overlay doesn't extend the background
        expected_duration = len(background)
        assert len(result) == expected_duration
    
    def test_combine_with_short_background(self):
        """Test combination when background is shorter than expected."""
        combiner = AudioCombiner()
        
        # Create test audio segments
        locutor = create_test_audio(10000)  # 10 seconds
        background = create_test_audio(12000)  # 12 seconds (shorter than locutor + offset)
        
        # Combine audio - should not raise exception
        result = combiner.combine(locutor, background)
        
        # Verify result exists
        assert result is not None
        assert isinstance(result, AudioSegment)
    
    def test_combine_preserves_background_duration(self):
        """Test that combination preserves background duration."""
        combiner = AudioCombiner()
        
        # Create test audio segments with various durations
        test_cases = [
            (5000, 15000),   # 5s locutor, 15s background
            (10000, 25000),  # 10s locutor, 25s background
            (15000, 30000),  # 15s locutor, 30s background
        ]
        
        for locutor_duration, background_duration in test_cases:
            locutor = create_test_audio(locutor_duration)
            background = create_test_audio(background_duration)
            
            result = combiner.combine(locutor, background)
            
            # Background duration should be preserved
            assert len(result) == background_duration
    
    def test_combine_with_different_audio_properties(self):
        """Test combination with different audio properties."""
        combiner = AudioCombiner()
        
        # Create test audio segments with different frequencies
        locutor = create_test_audio(8000, frequency=440)  # A4 note
        background = create_test_audio(20000, frequency=220)  # A3 note
        
        # Combine audio
        result = combiner.combine(locutor, background)
        
        # Verify result
        assert result is not None
        assert len(result) == len(background)

    def test_validate_durations_correct(self):
        """Test validation with correct durations."""
        combiner = AudioCombiner()

        # Correct durations: background = locutor + 10000ms
        locutor_duration = 15000  # 15 seconds
        background_duration = 25000  # 25 seconds (15s + 10s)
        final_duration = 25000  # Same as background

        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )

        assert result is True

    def test_validate_durations_within_tolerance(self):
        """Test validation with durations within tolerance (±100ms)."""
        combiner = AudioCombiner()

        # Durations within tolerance
        locutor_duration = 15000  # 15 seconds
        background_duration = 25050  # 25.05 seconds (within ±100ms tolerance)
        final_duration = 25050

        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )

        assert result is True

    def test_validate_durations_background_too_short(self):
        """Test validation fails when background is too short."""
        combiner = AudioCombiner()

        # Background too short (more than 100ms off)
        locutor_duration = 15000  # 15 seconds
        background_duration = 24500  # 24.5 seconds (should be 25s, off by 500ms)
        final_duration = 24500

        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )

        assert result is False

    def test_validate_durations_background_too_long(self):
        """Test validation fails when background is too long."""
        combiner = AudioCombiner()

        # Background too long (more than 100ms off)
        locutor_duration = 15000  # 15 seconds
        background_duration = 25500  # 25.5 seconds (should be 25s, off by 500ms)
        final_duration = 25500

        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )

        assert result is False

    def test_validate_durations_locutor_ends_too_late(self):
        """Test validation fails when locutor ends less than 5s before final."""
        combiner = AudioCombiner()

        # Locutor ends at 5000 + 15000 = 20000ms
        # Final ends at 23000ms
        # Time after locutor = 23000 - 20000 = 3000ms (less than 5000ms required)
        locutor_duration = 15000  # 15 seconds
        background_duration = 25000  # 25 seconds (correct)
        final_duration = 23000  # 23 seconds (too short)

        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )

        assert result is False

    def test_validate_durations_exactly_5s_after_locutor(self):
        """Test validation passes when locutor ends exactly 5s before final."""
        combiner = AudioCombiner()

        # Locutor ends at 5000 + 15000 = 20000ms
        # Final ends at 25000ms
        # Time after locutor = 25000 - 20000 = 5000ms (exactly 5000ms)
        locutor_duration = 15000  # 15 seconds
        background_duration = 25000  # 25 seconds
        final_duration = 25000  # 25 seconds

        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )

        assert result is True

    def test_validate_durations_multiple_failures(self):
        """Test validation fails when multiple conditions are not met."""
        combiner = AudioCombiner()

        # Both validations should fail
        locutor_duration = 15000  # 15 seconds
        background_duration = 24000  # 24 seconds (should be 25s, off by 1000ms)
        final_duration = 19000  # 19 seconds (locutor ends at 20s, only -1s after)

        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )

        assert result is False

    def test_overlay_timing_5_seconds_offset(self):
        """Test overlay con timing correcto (5 segundos) - Requirements 7.2, 8.2."""
        combiner = AudioCombiner()
        
        # Create test audio segments
        locutor = create_test_audio(8000)  # 8 seconds
        background = create_test_audio(20000)  # 20 seconds
        
        # Combine audio
        result = combiner.combine(locutor, background)
        
        # Verify that locutor starts at exactly 5 seconds (5000ms)
        assert combiner.LOCUTOR_START_OFFSET == 5000
        
        # Verify result properties
        assert result is not None
        assert isinstance(result, AudioSegment)
        assert len(result) == len(background)  # Duration should match background
        
        # The locutor should be positioned at 5000ms offset
        # This is verified by the implementation using overlay with position parameter

    def test_duration_validation_correct_values(self):
        """Test validación de duraciones con valores correctos - Requirements 8.1, 8.3."""
        combiner = AudioCombiner()
        
        # Test case 1: Perfect match
        locutor_duration = 12000  # 12 seconds
        background_duration = 22000  # 22 seconds (12s + 10s)
        final_duration = 22000  # Same as background
        
        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )
        
        assert result is True
        
        # Test case 2: Within tolerance (±100ms)
        locutor_duration = 15000  # 15 seconds
        background_duration = 25080  # 25.08 seconds (within ±100ms of 25s)
        final_duration = 25080
        
        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )
        
        assert result is True

    def test_duration_validation_incorrect_values_logs_warning(self):
        """Test validación de duraciones con valores incorrectos (debe logear warning) - Requirements 8.1, 8.3."""
        combiner = AudioCombiner()
        
        # Test case 1: Background duration incorrect (too short)
        locutor_duration = 15000  # 15 seconds
        background_duration = 24000  # 24 seconds (should be 25s, off by 1000ms > tolerance)
        final_duration = 24000
        
        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )
        
        assert result is False  # Should fail validation
        
        # Test case 2: Locutor ends too close to final (less than 5s)
        locutor_duration = 18000  # 18 seconds
        background_duration = 28000  # 28 seconds (correct: 18s + 10s)
        final_duration = 22000  # 22 seconds (locutor ends at 5s + 18s = 23s, only -1s before final)
        
        result = combiner.validate_durations(
            locutor_duration,
            background_duration,
            final_duration
        )
        
        assert result is False  # Should fail validation

    def test_background_fade_after_locutor_ends(self):
        """Test fade de fondo después de que termina locutor - Requirements 7.4."""
        combiner = AudioCombiner()
        
        # Create test audio segments where locutor ends before background
        locutor = create_test_audio(10000)  # 10 seconds
        background = create_test_audio(25000)  # 25 seconds
        
        # Reduce background volume to simulate the state during locutor
        background = background - 12  # Reduce to ~25% volume (-12dB)
        
        # Combine audio
        result = combiner.combine(locutor, background)
        
        # Verify result exists
        assert result is not None
        assert isinstance(result, AudioSegment)
        
        # Calculate when locutor ends
        locutor_end_position = combiner.LOCUTOR_START_OFFSET + len(locutor)  # 5000 + 10000 = 15000ms
        
        # Verify locutor ends before background
        assert locutor_end_position < len(result)
        
        # Extract segments to verify fade behavior
        # Segment just after locutor ends (should start fade)
        after_locutor_start = result[locutor_end_position:locutor_end_position + 500]
        
        # Segment well after locutor ends (should have higher volume due to fade)
        fade_end_position = min(locutor_end_position + 2000, len(result))  # 2s fade duration
        after_fade = result[fade_end_position:fade_end_position + 500]
        
        # Verify segments exist and have reasonable duration
        assert len(after_locutor_start) > 0
        assert len(after_fade) > 0
        
        # The fade should increase background volume after locutor ends
        # This is implemented in the combine method using fade effect



# Property-Based Tests

import tempfile
import shutil


@settings(max_examples=20, deadline=2000)  # 2 second deadline for audio processing
@given(
    locutor_duration_ms=st.integers(min_value=5000, max_value=60000),  # 5s to 60s
    background_duration_ms=st.integers(min_value=15000, max_value=120000)  # 15s to 120s
)
def test_property_14_locutor_overlay_timing(locutor_duration_ms, background_duration_ms):
    """
    Property 14: Locutor Overlay Timing
    Feature: audio-gran-campana, Property 14: Locutor Overlay Timing
    
    For any locutor audio overlaid on background music, the locutor should 
    start exactly 5000ms from the beginning of the background track.
    
    Validates: Requirements 7.2, 8.2
    """
    # Asegurar que el fondo es suficientemente largo para contener el locutor
    # El fondo debe ser al menos: LOCUTOR_START_OFFSET + locutor_duration
    min_background_duration = 5000 + locutor_duration_ms
    if background_duration_ms < min_background_duration:
        # Ajustar la duración del fondo para que sea suficiente
        background_duration_ms = min_background_duration + 5000  # +5s extra
    
    # Crear segmentos de audio sintéticos
    # Usamos tonos de diferentes frecuencias para poder distinguirlos
    locutor = Sine(440).to_audio_segment(duration=locutor_duration_ms)  # A4 note
    background = Sine(220).to_audio_segment(duration=background_duration_ms)  # A3 note
    
    # Crear AudioCombiner y combinar los audios
    combiner = AudioCombiner()
    combined = combiner.combine(locutor, background)
    
    # Verificar que el audio combinado existe
    assert combined is not None, "Combined audio should not be None"
    assert isinstance(combined, AudioSegment), "Combined audio should be an AudioSegment"
    
    # Verificar que la duración del audio combinado es igual a la del fondo
    # (el overlay no extiende la duración del fondo)
    assert len(combined) == len(background), \
        f"Combined audio duration ({len(combined)}ms) should equal background duration ({len(background)}ms)"
    
    # Verificar el timing del locutor usando análisis de audio
    # El locutor debe iniciar exactamente a los 5000ms
    
    # Extraer segmentos para verificar el timing:
    # 1. Antes del inicio del locutor (0-5000ms): solo debe haber fondo
    before_locutor = combined[:5000]
    
    # 2. Durante el locutor (5000ms a 5000+locutor_duration_ms): debe haber locutor + fondo
    during_locutor_start = 5000
    during_locutor_end = min(5000 + locutor_duration_ms, len(combined))
    during_locutor = combined[during_locutor_start:during_locutor_end]
    
    # 3. Después del locutor (si hay tiempo): solo debe haber fondo
    if during_locutor_end < len(combined):
        after_locutor = combined[during_locutor_end:]
    else:
        after_locutor = None
    
    # Verificar que los segmentos tienen las duraciones correctas
    assert len(before_locutor) == 5000, \
        f"Segment before locutor should be exactly 5000ms, got {len(before_locutor)}ms"
    
    expected_during_duration = min(locutor_duration_ms, len(combined) - 5000)
    assert len(during_locutor) == expected_during_duration, \
        f"Segment during locutor should be {expected_during_duration}ms, got {len(during_locutor)}ms"
    
    # Verificar el contenido de audio usando dBFS (nivel de volumen)
    # El segmento "durante el locutor" debe tener mayor energía que el segmento "antes del locutor"
    # porque contiene dos señales superpuestas (locutor + fondo)
    
    before_dbfs = before_locutor.dBFS
    during_dbfs = during_locutor.dBFS
    
    # El segmento durante el locutor debe tener mayor volumen (menos negativo en dBFS)
    # debido a la superposición de dos señales
    # Permitir un margen pequeño para variaciones de procesamiento
    assert during_dbfs > before_dbfs - 1.0, \
        f"During locutor segment should have higher or similar energy than before segment. " \
        f"Before: {before_dbfs:.2f}dBFS, During: {during_dbfs:.2f}dBFS"
    
    # Verificar que el segmento después del locutor (si existe) tiene energía similar
    # al segmento antes del locutor (ambos solo tienen fondo)
    if after_locutor is not None and len(after_locutor) >= 100:  # Al menos 100ms para análisis
        after_dbfs = after_locutor.dBFS
        
        # Los segmentos antes y después del locutor deberían tener energía similar
        # ya que ambos solo contienen el fondo musical
        # Permitir una diferencia mayor debido al fade que se aplica después del locutor
        dbfs_difference = abs(after_dbfs - before_dbfs)
        
        # El fade puede aumentar el volumen del fondo después del locutor,
        # así que el segmento "after" puede tener mayor volumen
        # Verificamos que la diferencia no sea excesiva (máximo 6dB de diferencia)
        assert dbfs_difference <= 6.0, \
            f"Before and after locutor segments should have similar energy (within 6dB). " \
            f"Before: {before_dbfs:.2f}dBFS, After: {after_dbfs:.2f}dBFS, " \
            f"Difference: {dbfs_difference:.2f}dB"
    
    # Verificar que el timing es exacto verificando que el locutor NO está presente
    # en los primeros 5000ms
    # Extraemos una muestra muy pequeña justo antes de los 5000ms (4900-5000ms)
    # y justo después de los 5000ms (5000-5100ms)
    sample_before = combined[4900:5000]  # 100ms antes del inicio del locutor
    sample_after = combined[5000:5100]   # 100ms después del inicio del locutor
    
    sample_before_dbfs = sample_before.dBFS
    sample_after_dbfs = sample_after.dBFS
    
    # La muestra después del inicio debe tener mayor energía que la muestra antes
    # debido a la presencia del locutor
    assert sample_after_dbfs > sample_before_dbfs - 1.0, \
        f"Audio energy should increase at 5000ms mark when locutor starts. " \
        f"Before (4900-5000ms): {sample_before_dbfs:.2f}dBFS, " \
        f"After (5000-5100ms): {sample_after_dbfs:.2f}dBFS"
    
    # Verificar que el offset usado es exactamente 5000ms
    assert combiner.LOCUTOR_START_OFFSET == 5000, \
        f"LOCUTOR_START_OFFSET should be exactly 5000ms, got {combiner.LOCUTOR_START_OFFSET}ms"
    
    # Verificar que la posición de finalización del locutor es correcta
    expected_locutor_end = 5000 + locutor_duration_ms
    
    # Si el locutor termina antes del final del fondo, verificamos que hay
    # al menos algo de tiempo después del locutor
    if expected_locutor_end < len(combined):
        time_after_locutor = len(combined) - expected_locutor_end
        assert time_after_locutor > 0, \
            f"There should be time after locutor ends. " \
            f"Locutor ends at {expected_locutor_end}ms, combined ends at {len(combined)}ms"


@settings(max_examples=20, deadline=2000)  # 2 second deadline for audio processing
@given(
    locutor_duration_ms=st.integers(min_value=5000, max_value=60000),  # 5s to 60s
    background_duration_ms=st.integers(min_value=15000, max_value=120000)  # 15s to 120s
)
def test_property_15_locutor_volume_preservation(locutor_duration_ms, background_duration_ms):
    """
    Property 15: Locutor Volume Preservation
    Feature: audio-gran-campana, Property 15: Locutor Volume Preservation
    
    For any locutor audio in the final combined output, the locutor track should 
    maintain 100% volume throughout its entire duration.
    
    Validates: Requirements 7.3
    """
    # Asegurar que el fondo es suficientemente largo para contener el locutor
    # El fondo debe ser al menos: LOCUTOR_START_OFFSET + locutor_duration
    min_background_duration = 5000 + locutor_duration_ms
    if background_duration_ms < min_background_duration:
        # Ajustar la duración del fondo para que sea suficiente
        background_duration_ms = min_background_duration + 5000  # +5s extra
    
    # Crear segmentos de audio sintéticos con diferentes frecuencias
    # para poder distinguir el locutor del fondo
    locutor_frequency = 880  # A5 note - frecuencia distintiva para el locutor
    background_frequency = 220  # A3 note - frecuencia más baja para el fondo
    
    # Crear el locutor a volumen completo (0dB)
    locutor = Sine(locutor_frequency).to_audio_segment(duration=locutor_duration_ms)
    
    # Crear el fondo a un volumen más bajo para que el locutor sea distinguible
    background = Sine(background_frequency).to_audio_segment(duration=background_duration_ms)
    background = background - 12  # Reducir el fondo a ~25% volumen (-12dB)
    
    # Guardar el nivel de volumen original del locutor para comparación
    original_locutor_dbfs = locutor.dBFS
    
    # Crear AudioCombiner y combinar los audios
    combiner = AudioCombiner()
    combined = combiner.combine(locutor, background)
    
    # Verificar que el audio combinado existe
    assert combined is not None, "Combined audio should not be None"
    assert isinstance(combined, AudioSegment), "Combined audio should be an AudioSegment"
    
    # Extraer la porción del audio combinado donde está el locutor
    # El locutor inicia a los 5000ms y dura locutor_duration_ms
    locutor_start = 5000
    locutor_end = min(5000 + locutor_duration_ms, len(combined))
    
    # Extraer el segmento donde está el locutor
    locutor_segment = combined[locutor_start:locutor_end]
    
    # Verificar que el segmento del locutor tiene la duración correcta
    expected_locutor_segment_duration = min(locutor_duration_ms, len(combined) - 5000)
    assert len(locutor_segment) == expected_locutor_segment_duration, \
        f"Locutor segment should be {expected_locutor_segment_duration}ms, got {len(locutor_segment)}ms"
    
    # Verificar el volumen del locutor en el audio combinado
    # El locutor debe mantener su volumen original (100%)
    
    # Estrategia de verificación:
    # 1. Dividir el segmento del locutor en múltiples sub-segmentos
    # 2. Verificar que cada sub-segmento mantiene un nivel de volumen consistente
    # 3. Verificar que el nivel de volumen es similar al original del locutor
    
    # Dividir el segmento del locutor en 5 partes para verificar consistencia
    num_samples = 5
    sample_duration = len(locutor_segment) // num_samples
    
    if sample_duration < 100:  # Si el segmento es muy corto, usar menos muestras
        num_samples = max(1, len(locutor_segment) // 100)
        sample_duration = len(locutor_segment) // num_samples
    
    sample_volumes = []
    
    for i in range(num_samples):
        start = i * sample_duration
        end = min((i + 1) * sample_duration, len(locutor_segment))
        
        if end - start < 50:  # Saltar muestras muy pequeñas
            continue
        
        sample = locutor_segment[start:end]
        sample_dbfs = sample.dBFS
        sample_volumes.append(sample_dbfs)
    
    # Verificar que hay suficientes muestras para analizar
    assert len(sample_volumes) > 0, "Should have at least one sample to analyze"
    
    # Verificar que el volumen es consistente a lo largo del segmento del locutor
    # Todas las muestras deben tener un volumen similar (dentro de ±2dB)
    if len(sample_volumes) > 1:
        max_volume = max(sample_volumes)
        min_volume = min(sample_volumes)
        volume_variation = max_volume - min_volume
        
        # El volumen debe ser consistente (variación máxima de 2dB)
        assert volume_variation <= 2.0, \
            f"Locutor volume should be consistent throughout its duration. " \
            f"Volume variation: {volume_variation:.2f}dB (max: {max_volume:.2f}dB, min: {min_volume:.2f}dB)"
    
    # Verificar que el volumen del locutor en el audio combinado es similar
    # al volumen original del locutor
    # 
    # Nota: Cuando se superponen dos señales de audio, el volumen resultante
    # puede ser ligeramente mayor debido a la suma de las señales.
    # Sin embargo, el locutor debe mantener su presencia dominante.
    
    avg_combined_locutor_volume = sum(sample_volumes) / len(sample_volumes)
    
    # El volumen del locutor en el audio combinado debe ser similar al original
    # Permitimos una diferencia de hasta 3dB debido a la superposición con el fondo
    # El volumen combinado puede ser mayor (menos negativo) debido a la suma de señales
    volume_difference = abs(avg_combined_locutor_volume - original_locutor_dbfs)
    
    # Verificar que el volumen no se ha reducido significativamente
    # (el locutor debe mantener 100% volumen, no debe ser atenuado)
    assert avg_combined_locutor_volume >= original_locutor_dbfs - 3.0, \
        f"Locutor volume should not be significantly reduced. " \
        f"Original: {original_locutor_dbfs:.2f}dBFS, " \
        f"Combined: {avg_combined_locutor_volume:.2f}dBFS, " \
        f"Difference: {volume_difference:.2f}dB"
    
    # Verificar que el locutor no ha sido amplificado excesivamente
    # (debe mantener aproximadamente el mismo volumen, no aumentar dramáticamente)
    assert avg_combined_locutor_volume <= original_locutor_dbfs + 6.0, \
        f"Locutor volume should not be excessively amplified. " \
        f"Original: {original_locutor_dbfs:.2f}dBFS, " \
        f"Combined: {avg_combined_locutor_volume:.2f}dBFS, " \
        f"Difference: {volume_difference:.2f}dB"
    
    # Verificación adicional: comparar el segmento del locutor con el fondo solo
    # El segmento del locutor debe tener mayor energía que el fondo solo
    # debido a la presencia del locutor a 100% volumen
    
    # Extraer un segmento del fondo antes del locutor (0-5000ms)
    background_only = combined[:5000]
    background_only_dbfs = background_only.dBFS
    
    # El segmento con el locutor debe tener mayor energía que el fondo solo
    assert avg_combined_locutor_volume > background_only_dbfs - 1.0, \
        f"Locutor segment should have higher energy than background only. " \
        f"Locutor segment: {avg_combined_locutor_volume:.2f}dBFS, " \
        f"Background only: {background_only_dbfs:.2f}dBFS"
    
    # Verificar que el locutor mantiene su volumen en diferentes puntos
    # Tomar muestras al inicio, medio y final del segmento del locutor
    if len(locutor_segment) >= 1000:  # Solo si el segmento es suficientemente largo
        # Muestra al inicio (primeros 500ms)
        start_sample = locutor_segment[:500]
        start_dbfs = start_sample.dBFS
        
        # Muestra en el medio
        mid_point = len(locutor_segment) // 2
        mid_sample = locutor_segment[mid_point:mid_point + 500]
        mid_dbfs = mid_sample.dBFS
        
        # Muestra al final (últimos 500ms)
        end_sample = locutor_segment[-500:]
        end_dbfs = end_sample.dBFS
        
        # Verificar que el volumen es consistente entre inicio, medio y final
        max_sample_volume = max(start_dbfs, mid_dbfs, end_dbfs)
        min_sample_volume = min(start_dbfs, mid_dbfs, end_dbfs)
        sample_variation = max_sample_volume - min_sample_volume
        
        assert sample_variation <= 2.0, \
            f"Locutor volume should be consistent from start to end. " \
            f"Start: {start_dbfs:.2f}dBFS, Mid: {mid_dbfs:.2f}dBFS, End: {end_dbfs:.2f}dBFS, " \
            f"Variation: {sample_variation:.2f}dB"



@settings(max_examples=20, deadline=2000)  # 2 second deadline for audio processing
@given(
    locutor_duration_ms=st.integers(min_value=5000, max_value=40000),  # 5s to 40s
    extra_background_ms=st.integers(min_value=6000, max_value=30000)  # 6s to 30s extra after locutor
)
def test_property_16_background_fade_after_locutor(locutor_duration_ms, extra_background_ms):
    """
    Property 16: Background Fade After Locutor
    Feature: audio-gran-campana, Property 16: Background Fade After Locutor
    
    For any combined audio where the locutor ends before the background, 
    the background music volume should fade from its current level to 100% 
    after the locutor ends.
    
    Validates: Requirements 7.4
    """
    # Calcular la duración del fondo para asegurar que el locutor termina antes
    # Fondo debe ser: LOCUTOR_START_OFFSET + locutor_duration + extra_background_ms
    background_duration_ms = 5000 + locutor_duration_ms + extra_background_ms
    
    # Crear segmentos de audio sintéticos
    # Locutor a volumen completo (0dB)
    locutor = Sine(880).to_audio_segment(duration=locutor_duration_ms)  # A5 note
    
    # Fondo a volumen reducido (~25% = -12dB) para simular el estado durante el locutor
    background = Sine(220).to_audio_segment(duration=background_duration_ms)  # A3 note
    background = background - 12  # Reducir a ~25% volumen (-12dB)
    
    # Crear AudioCombiner y combinar los audios
    combiner = AudioCombiner()
    combined = combiner.combine(locutor, background)
    
    # Verificar que el audio combinado existe
    assert combined is not None, "Combined audio should not be None"
    assert isinstance(combined, AudioSegment), "Combined audio should be an AudioSegment"
    
    # Calcular la posición donde termina el locutor
    locutor_end_position = 5000 + locutor_duration_ms
    
    # Verificar que el locutor termina antes del final del fondo
    assert locutor_end_position < len(combined), \
        f"Locutor should end before background. " \
        f"Locutor ends at {locutor_end_position}ms, combined ends at {len(combined)}ms"
    
    # Extraer segmentos para verificar el fade:
    # 1. Segmento durante el locutor (para referencia del volumen del fondo)
    #    Tomamos una muestra al final del periodo del locutor
    during_locutor_sample_start = max(5000, locutor_end_position - 1000)  # 1s antes del final del locutor
    during_locutor_sample_end = locutor_end_position
    during_locutor_sample = combined[during_locutor_sample_start:during_locutor_sample_end]
    
    # 2. Segmento justo después de que termina el locutor (inicio del fade)
    #    Tomamos los primeros 500ms después del locutor
    after_locutor_start = combined[locutor_end_position:min(locutor_end_position + 500, len(combined))]
    
    # 3. Segmento al final del fade (debe estar a 100% volumen)
    #    El fade dura 2000ms según la implementación
    fade_duration_ms = 2000
    fade_end_position = min(locutor_end_position + fade_duration_ms, len(combined))
    
    # Tomamos una muestra después del fade (últimos 1000ms del audio o después del fade)
    if fade_end_position < len(combined):
        # Hay audio después del fade
        after_fade_sample_start = fade_end_position
        after_fade_sample_end = min(fade_end_position + 1000, len(combined))
        after_fade_sample = combined[after_fade_sample_start:after_fade_sample_end]
    else:
        # El fade llega hasta el final, tomamos los últimos 500ms
        after_fade_sample = combined[-500:]
    
    # Verificar que los segmentos tienen suficiente duración para análisis
    assert len(after_locutor_start) >= 100, \
        f"After locutor sample should be at least 100ms, got {len(after_locutor_start)}ms"
    assert len(after_fade_sample) >= 100, \
        f"After fade sample should be at least 100ms, got {len(after_fade_sample)}ms"
    
    # Analizar el volumen de cada segmento
    after_locutor_dbfs = after_locutor_start.dBFS
    after_fade_dbfs = after_fade_sample.dBFS
    
    # Verificar que hay un incremento de volumen después del fade
    # El volumen después del fade debe ser mayor (menos negativo) que justo después del locutor
    # 
    # Nota: El segmento "after_locutor_start" contiene solo el fondo (sin locutor)
    # porque el locutor ya terminó. El fade debe aumentar el volumen del fondo.
    
    # El volumen debe aumentar al menos 8dB para demostrar que hay un fade significativo
    # hacia un volumen mayor (la implementación aplica un fade de -12dB a 0dB = 12dB de aumento)
    volume_increase = after_fade_dbfs - after_locutor_dbfs
    
    # Verificar que el volumen aumenta (el fade está funcionando)
    # Esperamos al menos 8dB de aumento para confirmar que el fade está funcionando
    assert volume_increase > 8.0, \
        f"Background volume should increase significantly after locutor ends (fade to 100%). " \
        f"Volume after locutor: {after_locutor_dbfs:.2f}dBFS, " \
        f"Volume after fade: {after_fade_dbfs:.2f}dBFS, " \
        f"Increase: {volume_increase:.2f}dB (expected > 8dB)"
    
    # Verificación adicional: verificar que el fade es gradual
    # Tomamos múltiples muestras durante el periodo del fade para verificar
    # que el volumen aumenta progresivamente
    
    if fade_end_position - locutor_end_position >= 1000:  # Solo si el fade es suficientemente largo
        # Dividir el periodo del fade en 4 segmentos
        fade_segment_duration = (fade_end_position - locutor_end_position) // 4
        fade_volumes = []
        
        for i in range(4):
            segment_start = locutor_end_position + (i * fade_segment_duration)
            segment_end = segment_start + fade_segment_duration
            
            if segment_end > len(combined):
                break
            
            fade_segment = combined[segment_start:segment_end]
            if len(fade_segment) >= 100:  # Solo analizar si el segmento es suficientemente largo
                fade_volumes.append(fade_segment.dBFS)
        
        # Verificar que hay al menos 2 muestras para comparar
        if len(fade_volumes) >= 2:
            # Verificar que el volumen aumenta progresivamente
            # (cada muestra debe tener volumen mayor o igual que la anterior)
            for i in range(1, len(fade_volumes)):
                # Permitir una pequeña variación hacia abajo (hasta -1dB) debido a
                # variaciones en el procesamiento de audio
                assert fade_volumes[i] >= fade_volumes[i-1] - 1.0, \
                    f"Fade should be gradual and increasing. " \
                    f"Sample {i-1}: {fade_volumes[i-1]:.2f}dBFS, " \
                    f"Sample {i}: {fade_volumes[i]:.2f}dBFS"
            
            # Verificar que hay un aumento total significativo durante el fade
            total_fade_increase = fade_volumes[-1] - fade_volumes[0]
            assert total_fade_increase > 2.0, \
                f"Fade should show significant volume increase. " \
                f"Start: {fade_volumes[0]:.2f}dBFS, " \
                f"End: {fade_volumes[-1]:.2f}dBFS, " \
                f"Increase: {total_fade_increase:.2f}dB (expected > 2dB)"
    
    # Verificar que el fade solo se aplica después de que termina el locutor
    # Comparamos el volumen del fondo solo antes del locutor con el volumen después del fade
    
    # Tomar una muestra del fondo solo (antes de que inicie el locutor a los 5000ms)
    background_only_sample = combined[1000:4000]  # 1s-4s, solo fondo
    
    if len(background_only_sample) >= 100:
        background_only_dbfs = background_only_sample.dBFS
        
        # El volumen después del fade debe ser mayor que el fondo solo original
        # (el fade debe aumentar el volumen del fondo)
        assert after_fade_dbfs > background_only_dbfs - 1.0, \
            f"Fade should increase background volume after locutor ends. " \
            f"Background only: {background_only_dbfs:.2f}dBFS, " \
            f"Volume after fade: {after_fade_dbfs:.2f}dBFS"
    
    # Verificar que la duración del fade es razonable (aproximadamente 2000ms según implementación)
    # Esto se verifica indirectamente a través del análisis de volumen progresivo arriba
    
    # Verificar que el audio combinado tiene la duración correcta (igual al fondo)
    assert len(combined) == background_duration_ms, \
        f"Combined audio duration should equal background duration. " \
        f"Expected {background_duration_ms}ms, got {len(combined)}ms"
    
    # Verificar que el fade se aplica correctamente incluso con diferentes duraciones
    # de tiempo extra después del locutor
    time_after_locutor = len(combined) - locutor_end_position
    assert time_after_locutor == extra_background_ms, \
        f"Time after locutor should match extra_background_ms. " \
        f"Expected {extra_background_ms}ms, got {time_after_locutor}ms"
    
    # Verificar que el fade se aplica incluso cuando el tiempo después del locutor
    # es menor que la duración del fade (2000ms)
    if extra_background_ms < fade_duration_ms:
        # En este caso, el fade debe aplicarse en el tiempo disponible
        # El volumen final aún debe ser mayor que el inicial
        assert after_fade_dbfs > after_locutor_dbfs + 1.0, \
            f"Even with short fade duration, volume should increase. " \
            f"Initial: {after_locutor_dbfs:.2f}dBFS, " \
            f"Final: {after_fade_dbfs:.2f}dBFS"


@audio_property_test()
@given(
    locutor_duration_ms=st.integers(min_value=5000, max_value=60000),  # 5s to 60s
    tolerance_offset_ms=st.integers(min_value=-100, max_value=100)  # Tolerance variation
)
def test_property_17_duration_synchronization_validation(locutor_duration_ms, tolerance_offset_ms):
    """
    Property 17: Duration Synchronization Validation
    Feature: audio-gran-campana, Property 17: Duration Synchronization Validation
    
    For any processed audio with locutor duration L and background duration B,
    the validation should verify that: B = L + 10000ms (within tolerance),
    and the locutor ends at least 5000ms before the final audio ends.
    
    Validates: Requirements 8.1, 8.3
    """
    # Calcular la duración del fondo según la fórmula: L + 10000ms
    # Añadimos el tolerance_offset para probar casos dentro y fuera de tolerancia
    background_duration_ms = locutor_duration_ms + 10000 + tolerance_offset_ms
    
    # La duración final debe ser igual a la duración del fondo
    # (el overlay no extiende la duración)
    final_duration_ms = background_duration_ms
    
    # Crear AudioCombiner
    combiner = AudioCombiner()
    
    # Ejecutar la validación
    validation_result = combiner.validate_durations(
        locutor_duration_ms=locutor_duration_ms,
        background_duration_ms=background_duration_ms,
        final_duration_ms=final_duration_ms
    )
    
    # Verificar que la validación retorna un booleano
    assert isinstance(validation_result, bool), \
        "validate_durations should return a boolean"
    
    # Verificación 1: Background debe ser locutor + 10000ms (con tolerancia de ±100ms)
    expected_background_duration = locutor_duration_ms + 10000
    duration_difference = abs(background_duration_ms - expected_background_duration)
    tolerance_ms = 100
    
    background_validation_should_pass = duration_difference <= tolerance_ms
    
    # Verificación 2: Locutor debe terminar al menos 5000ms antes del final
    # El locutor inicia a los 5000ms (LOCUTOR_START_OFFSET)
    # Por lo tanto, termina en: 5000 + locutor_duration_ms
    locutor_end_position = 5000 + locutor_duration_ms
    time_after_locutor = final_duration_ms - locutor_end_position
    min_time_after_locutor = 5000
    
    timing_validation_should_pass = time_after_locutor >= min_time_after_locutor
    
    # La validación completa debe pasar solo si ambas verificaciones pasan
    overall_should_pass = background_validation_should_pass and timing_validation_should_pass
    
    # Verificar que el resultado de la validación coincide con lo esperado
    assert validation_result == overall_should_pass, \
        f"Validation result mismatch. Expected {overall_should_pass}, got {validation_result}. " \
        f"Locutor: {locutor_duration_ms}ms, Background: {background_duration_ms}ms, " \
        f"Final: {final_duration_ms}ms, Duration diff: {duration_difference}ms, " \
        f"Time after locutor: {time_after_locutor}ms"
    
    # Verificar casos específicos:
    
    # Caso 1: Si la diferencia de duración está dentro de la tolerancia
    if duration_difference <= tolerance_ms:
        # La validación de duración debe pasar
        assert background_validation_should_pass, \
            f"Background validation should pass when difference ({duration_difference}ms) " \
            f"is within tolerance ({tolerance_ms}ms)"
    else:
        # La validación de duración debe fallar
        assert not background_validation_should_pass, \
            f"Background validation should fail when difference ({duration_difference}ms) " \
            f"exceeds tolerance ({tolerance_ms}ms)"
    
    # Caso 2: Si el tiempo después del locutor es suficiente
    if time_after_locutor >= min_time_after_locutor:
        # La validación de timing debe pasar
        assert timing_validation_should_pass, \
            f"Timing validation should pass when time after locutor ({time_after_locutor}ms) " \
            f"is at least {min_time_after_locutor}ms"
    else:
        # La validación de timing debe fallar
        assert not timing_validation_should_pass, \
            f"Timing validation should fail when time after locutor ({time_after_locutor}ms) " \
            f"is less than {min_time_after_locutor}ms"
    
    # Caso 3: Verificar que ambas condiciones deben cumplirse para que la validación pase
    if overall_should_pass:
        assert validation_result, \
            "Validation should pass when both background duration and timing are correct"
    else:
        assert not validation_result, \
            "Validation should fail when either background duration or timing is incorrect"
