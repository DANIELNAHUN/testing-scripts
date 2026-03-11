"""
Unit tests for BackgroundMusicProcessor.

Tests the processing of background music files with volume effects.
"""

import pytest
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine
from hypothesis import given, strategies as st
from tests.hypothesis_config import audio_property_test
from tests.hypothesis_strategies import (
    audio_segment_with_duration,
    processing_durations,
    background_music_durations
)

from src.background_music_processor import BackgroundMusicProcessor
from src.file_loader import FileLoader


@pytest.fixture
def test_audio_folder(tmp_path):
    """Create a temporary folder with test audio files."""
    audio_folder = tmp_path / "audio"
    audio_folder.mkdir()
    
    # Generate a test audio file (10 seconds of sine wave at 440Hz)
    test_audio = Sine(440).to_audio_segment(duration=10000)
    
    # Save as MP3
    first_bg_path = audio_folder / "Yo tengo un amigo que me ama.mp3"
    test_audio.export(str(first_bg_path), format="mp3")
    
    return audio_folder


@pytest.fixture
def file_loader(test_audio_folder):
    """Create a FileLoader instance with test audio folder."""
    return FileLoader(test_audio_folder)


@pytest.fixture
def processor(file_loader):
    """Create a BackgroundMusicProcessor instance."""
    return BackgroundMusicProcessor(file_loader)


def test_process_first_background_success(processor):
    """Test successful processing of first background music."""
    result = processor.process_first_background()
    
    # Verify result is an AudioSegment
    assert isinstance(result, AudioSegment)
    
    # Verify duration is preserved (10 seconds = 10000ms)
    assert len(result) == 10000
    
    # Verify the audio is not empty
    assert result.frame_count() > 0


def test_process_first_background_duration_preservation(processor):
    """Test that processing preserves the original duration."""
    result = processor.process_first_background()
    
    # Original test audio is 10 seconds
    expected_duration = 10000
    assert len(result) == expected_duration


def test_process_first_background_file_not_found(file_loader):
    """Test error handling when first background file is missing."""
    # Create processor with empty folder
    empty_folder = Path("/tmp/nonexistent_folder_for_test")
    empty_loader = FileLoader(empty_folder)
    processor = BackgroundMusicProcessor(empty_loader)
    
    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError) as exc_info:
        processor.process_first_background()
    
    assert "First background file not found" in str(exc_info.value)


def test_process_first_background_has_three_sections(processor):
    """Test that the processed audio conceptually has three sections."""
    result = processor.process_first_background()
    
    # Section 1: 0-4000ms (100% volume)
    section_1 = result[:4000]
    assert len(section_1) == 4000
    
    # Section 2: 4000-5000ms (fade from 100% to 25%)
    section_2 = result[4000:5000]
    assert len(section_2) == 1000
    
    # Section 3: 5000-10000ms (25% volume)
    section_3 = result[5000:]
    assert len(section_3) == 5000


def test_constants_defined(processor):
    """Test that required constants are defined."""
    assert processor.FIRST_BACKGROUND == 'Yo tengo un amigo que me ama.mp3'
    assert processor.SECOND_BACKGROUND == 'Eres todo poderoso.mp3'
    assert processor.CROSSFADE_DURATION == 3000


def test_calculate_second_background_duration(processor):
    """Test calculation of second background duration."""
    locutor_duration = 30000  # 30 seconds
    first_bg_duration = 10000  # 10 seconds
    
    # Formula: locutor + 10s - first_bg + 3s
    # 30000 + 10000 - 10000 + 3000 = 33000
    expected = 33000
    
    result = processor.calculate_second_background_duration(
        locutor_duration, first_bg_duration
    )
    
    assert result == expected


def test_process_second_background_success(test_audio_folder, file_loader):
    """Test successful processing of second background music."""
    # Create second background file (15 seconds)
    test_audio = Sine(440).to_audio_segment(duration=15000)
    second_bg_path = test_audio_folder / "Eres todo poderoso.mp3"
    test_audio.export(str(second_bg_path), format="mp3")
    
    processor = BackgroundMusicProcessor(file_loader)
    
    # Process with required duration of 10 seconds
    result = processor.process_second_background(10000)
    
    # Verify result is an AudioSegment
    assert isinstance(result, AudioSegment)
    
    # Verify duration is trimmed to required duration
    assert len(result) == 10000
    
    # Verify the audio is not empty
    assert result.frame_count() > 0


def test_process_second_background_shorter_than_required(test_audio_folder, file_loader):
    """Test processing when second background is shorter than required."""
    # Create second background file (8 seconds)
    test_audio = Sine(440).to_audio_segment(duration=8000)
    second_bg_path = test_audio_folder / "Eres todo poderoso.mp3"
    test_audio.export(str(second_bg_path), format="mp3")
    
    processor = BackgroundMusicProcessor(file_loader)
    
    # Process with required duration of 10 seconds (longer than available)
    result = processor.process_second_background(10000)
    
    # Should use complete available duration (8 seconds)
    assert len(result) == 8000


def test_process_second_background_file_not_found(file_loader):
    """Test error handling when second background file is missing."""
    # Create processor with folder that doesn't have second background
    processor = BackgroundMusicProcessor(file_loader)
    
    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError) as exc_info:
        processor.process_second_background(10000)
    
    assert "Second background file not found" in str(exc_info.value)


def test_process_second_background_has_three_sections(test_audio_folder, file_loader):
    """Test that the processed second background has three sections."""
    # Create second background file (15 seconds)
    test_audio = Sine(440).to_audio_segment(duration=15000)
    second_bg_path = test_audio_folder / "Eres todo poderoso.mp3"
    test_audio.export(str(second_bg_path), format="mp3")
    
    processor = BackgroundMusicProcessor(file_loader)
    result = processor.process_second_background(10000)
    
    # Section 1: 0 to (10000-5000)ms = 0-5000ms (20% volume)
    section_1 = result[:5000]
    assert len(section_1) == 5000
    
    # Section 2: (10000-5000) to (10000-1000)ms = 5000-9000ms (fade 20% to 100%)
    section_2 = result[5000:9000]
    assert len(section_2) == 4000
    
    # Section 3: (10000-1000) to 10000ms = 9000-10000ms (100% volume)
    section_3 = result[9000:]
    assert len(section_3) == 1000


# Property-Based Tests

from pydub.generators import Sine
import tempfile
import shutil


@audio_property_test()
@given(
    duration_ms=st.integers(min_value=6000, max_value=30000)  # At least 6s to have all sections
)
def test_property_6_first_background_volume_profile(duration_ms):
    """
    Property 6: First Background Volume Profile
    Feature: audio-gran-campana, Property 6: First Background Volume Profile
    
    For any first background music file processed, the output should have: 
    100% volume for the first 4 seconds, a smooth fade from 100% to 25% 
    between seconds 4 and 5, and 25% volume for all remaining time.
    
    Validates: Requirements 3.2, 3.3, 3.4
    """
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Generar archivo de audio sintético con duración aleatoria
        # Usamos un tono constante para poder medir cambios de volumen
        audio_segment = Sine(440).to_audio_segment(duration=duration_ms)
        filename = "Yo tengo un amigo que me ama.mp3"
        file_path = audio_dir / filename
        
        # Exportar como MP3
        audio_segment.export(str(file_path), format="mp3")
        
        # Procesar el archivo usando BackgroundMusicProcessor
        loader = FileLoader(audio_dir)
        processor = BackgroundMusicProcessor(loader)
        processed_audio = processor.process_first_background()
        
        # Verificar que la duración se preserva
        assert abs(len(processed_audio) - duration_ms) <= 100, \
            f"Duration should be preserved (expected ~{duration_ms}ms, got {len(processed_audio)}ms)"
        
        # Extraer secciones para verificar el perfil de volumen
        # Sección 1: Primeros 4 segundos (0-4000ms) - debe estar a 100% volumen
        section_1 = processed_audio[:4000]
        
        # Sección 2: Entre segundo 4 y 5 (4000-5000ms) - debe tener fade de 100% a 25%
        section_2 = processed_audio[4000:5000]
        
        # Sección 3: Después del segundo 5 (5000ms en adelante) - debe estar a 25% volumen
        section_3 = processed_audio[5000:6000]  # Tomamos 1 segundo de muestra
        
        # Verificar volumen relativo usando dBFS (decibeles relativos a escala completa)
        # dBFS más alto = más volumen (menos negativo)
        # 100% volumen ≈ 0 dBFS (o cerca)
        # 25% volumen ≈ -12 dBFS (20 * log10(0.25) ≈ -12)
        
        section_1_dbfs = section_1.dBFS
        section_3_dbfs = section_3.dBFS
        
        # Verificar que sección 1 tiene mayor volumen que sección 3
        # La diferencia debería ser aproximadamente 12 dB (100% vs 25%)
        volume_difference = section_1_dbfs - section_3_dbfs
        
        # Permitir un margen de error debido a la compresión MP3 y procesamiento
        assert volume_difference >= 10.0, \
            f"Section 1 (100%) should be ~12dB louder than Section 3 (25%), got {volume_difference:.2f}dB difference"
        
        assert volume_difference <= 14.0, \
            f"Volume difference should be around 12dB, got {volume_difference:.2f}dB"
        
        # Verificar que la sección 2 (fade) tiene volumen intermedio
        section_2_start = processed_audio[4000:4100]  # Inicio del fade
        section_2_end = processed_audio[4900:5000]    # Final del fade
        
        section_2_start_dbfs = section_2_start.dBFS
        section_2_end_dbfs = section_2_end.dBFS
        
        # El inicio del fade debe estar cerca del volumen de sección 1
        assert abs(section_2_start_dbfs - section_1_dbfs) <= 2.0, \
            f"Fade start should be close to 100% volume"
        
        # El final del fade debe estar cerca del volumen de sección 3
        assert abs(section_2_end_dbfs - section_3_dbfs) <= 2.0, \
            f"Fade end should be close to 25% volume"
        
        # Verificar que hay una transición suave (el volumen disminuye gradualmente)
        assert section_2_start_dbfs > section_2_end_dbfs, \
            f"Volume should decrease during fade section"
            
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


@audio_property_test()
@given(
    duration_ms=st.integers(min_value=6000, max_value=60000)  # 6s to 60s
)
def test_property_7_first_background_duration_preservation(duration_ms):
    """
    Property 7: First Background Duration Preservation
    Feature: audio-gran-campana, Property 7: First Background Duration Preservation
    
    For any first background music file, the processed output duration 
    should equal the input file duration.
    
    Validates: Requirements 3.1, 3.5
    """
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Generar archivo de audio sintético con duración aleatoria
        audio_segment = Sine(440).to_audio_segment(duration=duration_ms)
        filename = "Yo tengo un amigo que me ama.mp3"
        file_path = audio_dir / filename
        
        # Exportar como MP3
        audio_segment.export(str(file_path), format="mp3")
        
        # Procesar el archivo usando BackgroundMusicProcessor
        loader = FileLoader(audio_dir)
        processor = BackgroundMusicProcessor(loader)
        processed_audio = processor.process_first_background()
        
        # Verificar que la duración de salida es igual a la duración de entrada
        # Permitir un pequeño margen de error debido a la compresión MP3
        # y el procesamiento de audio (típicamente < 100ms)
        output_duration = len(processed_audio)
        duration_difference = abs(output_duration - duration_ms)
        
        assert duration_difference <= 100, \
            f"Output duration ({output_duration}ms) should equal input duration ({duration_ms}ms), " \
            f"difference: {duration_difference}ms"
            
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


@audio_property_test()
@given(
    locutor_duration_ms=st.integers(min_value=1000, max_value=300000),  # 1s to 5 minutes
    first_bg_duration_ms=st.integers(min_value=1000, max_value=300000)  # 1s to 5 minutes
)
def test_property_8_second_background_duration_calculation(locutor_duration_ms, first_bg_duration_ms):
    """
    Property 8: Second Background Duration Calculation
    Feature: audio-gran-campana, Property 8: Second Background Duration Calculation
    
    For any valid locutor duration L and first background duration F, 
    the calculated second background duration should equal 
    L + 10000ms - F + 3000ms.
    
    Validates: Requirements 4.1
    """
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Crear un FileLoader (no necesitamos archivos reales para este test)
        loader = FileLoader(audio_dir)
        processor = BackgroundMusicProcessor(loader)
        
        # Calcular la duración del segundo fondo usando el método
        calculated_duration = processor.calculate_second_background_duration(
            locutor_duration_ms, 
            first_bg_duration_ms
        )
        
        # Verificar que la fórmula se aplica correctamente
        # Fórmula: L + 10000ms - F + 3000ms
        expected_duration = locutor_duration_ms + 10000 - first_bg_duration_ms + 3000
        
        assert calculated_duration == expected_duration, \
            f"Calculated duration ({calculated_duration}ms) should equal " \
            f"L + 10000 - F + 3000 = {locutor_duration_ms} + 10000 - {first_bg_duration_ms} + 3000 = {expected_duration}ms"
            
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


@audio_property_test()
@given(
    available_duration_ms=st.integers(min_value=6000, max_value=30000),  # 6s to 30s available
    required_duration_ms=st.integers(min_value=10000, max_value=60000)  # 10s to 60s required
)
def test_property_9_second_background_duration_fallback(available_duration_ms, required_duration_ms):
    """
    Property 9: Second Background Duration Fallback
    Feature: audio-gran-campana, Property 9: Second Background Duration Fallback
    
    For any second background music file that is shorter than the calculated 
    required duration, the processor should use the complete available duration 
    without error.
    
    Validates: Requirements 4.4
    """
    # Filtrar casos donde el archivo disponible es más corto que lo requerido
    # (esto es lo que queremos probar)
    if available_duration_ms >= required_duration_ms:
        # Si el archivo es suficientemente largo, el test no es relevante
        # para esta propiedad, así que lo saltamos
        return
    
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Generar archivo de audio sintético con duración disponible (más corta que la requerida)
        audio_segment = Sine(440).to_audio_segment(duration=available_duration_ms)
        filename = "Eres todo poderoso.mp3"
        file_path = audio_dir / filename
        
        # Exportar como MP3
        audio_segment.export(str(file_path), format="mp3")
        
        # Procesar el archivo usando BackgroundMusicProcessor
        loader = FileLoader(audio_dir)
        processor = BackgroundMusicProcessor(loader)
        
        # Procesar con duración requerida mayor que la disponible
        # Esto NO debe lanzar error, debe usar la duración completa disponible
        processed_audio = processor.process_second_background(required_duration_ms)
        
        # Verificar que el procesamiento fue exitoso (no lanzó excepción)
        assert processed_audio is not None, \
            "Processing should succeed even when file is shorter than required"
        
        # Verificar que usa la duración completa disponible
        # Permitir un pequeño margen de error debido a la compresión MP3
        output_duration = len(processed_audio)
        duration_difference = abs(output_duration - available_duration_ms)
        
        assert duration_difference <= 100, \
            f"Should use complete available duration ({available_duration_ms}ms), " \
            f"got {output_duration}ms, difference: {duration_difference}ms"
        
        # Verificar que NO usa la duración requerida (que es mayor)
        assert output_duration < required_duration_ms, \
            f"Output duration ({output_duration}ms) should be less than required duration ({required_duration_ms}ms)"
        
        # Verificar que el audio procesado tiene contenido válido
        assert processed_audio.frame_count() > 0, \
            "Processed audio should have valid audio content"
        
        # Verificar que el audio tiene las secciones de volumen correctas
        # incluso cuando es más corto que lo requerido
        if available_duration_ms >= 6000:  # Solo si hay suficiente duración para las 3 secciones
            fade_start = available_duration_ms - 5000
            fade_end = available_duration_ms - 1000
            
            # Verificar que las secciones existen
            section_1 = processed_audio[:fade_start]
            section_2 = processed_audio[fade_start:fade_end]
            section_3 = processed_audio[fade_end:]
            
            assert len(section_1) > 0, "Section 1 should exist"
            assert len(section_2) > 0, "Section 2 (fade) should exist"
            assert len(section_3) > 0, "Section 3 should exist"
            
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


@audio_property_test()
@given(
    duration_ms=st.integers(min_value=6000, max_value=60000)  # 6s to 60s
)
def test_property_10_second_background_volume_profile(duration_ms):
    """
    Property 10: Second Background Volume Profile
    Feature: audio-gran-campana, Property 10: Second Background Volume Profile
    
    For any second background music file processed to a specific duration, 
    the output should have: 20% volume for all time except the last 5 seconds, 
    a smooth fade from 20% to 100% starting 4 seconds before the end, 
    and 100% volume for the last second.
    
    Validates: Requirements 5.2, 5.3, 5.4
    """
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Generar archivo de audio sintético con duración mayor que la requerida
        # para asegurar que el procesamiento recorta correctamente
        available_duration = duration_ms + 5000  # 5 segundos extra
        audio_segment = Sine(440).to_audio_segment(duration=available_duration)
        filename = "Eres todo poderoso.mp3"
        file_path = audio_dir / filename
        
        # Exportar como MP3
        audio_segment.export(str(file_path), format="mp3")
        
        # Procesar el archivo usando BackgroundMusicProcessor
        loader = FileLoader(audio_dir)
        processor = BackgroundMusicProcessor(loader)
        processed_audio = processor.process_second_background(duration_ms)
        
        # Verificar que la duración es la requerida
        output_duration = len(processed_audio)
        duration_difference = abs(output_duration - duration_ms)
        
        assert duration_difference <= 100, \
            f"Output duration ({output_duration}ms) should equal required duration ({duration_ms}ms), " \
            f"difference: {duration_difference}ms"
        
        # Definir puntos de tiempo para las secciones
        fade_start = duration_ms - 5000  # 5 segundos antes del final
        fade_end = duration_ms - 1000    # 1 segundo antes del final
        
        # Extraer secciones para verificar el perfil de volumen
        # Sección 1: Desde inicio hasta 5 segundos antes del final (20% volumen)
        section_1 = processed_audio[:fade_start]
        
        # Sección 2: Últimos 4 segundos antes del último segundo (fade 20% a 100%)
        section_2 = processed_audio[fade_start:fade_end]
        
        # Sección 3: Último segundo (100% volumen)
        section_3 = processed_audio[fade_end:]
        
        # Verificar que las secciones tienen las duraciones correctas
        assert abs(len(section_1) - fade_start) <= 10, \
            f"Section 1 should be {fade_start}ms, got {len(section_1)}ms"
        
        assert abs(len(section_2) - 4000) <= 10, \
            f"Section 2 (fade) should be 4000ms, got {len(section_2)}ms"
        
        assert abs(len(section_3) - 1000) <= 10, \
            f"Section 3 should be 1000ms, got {len(section_3)}ms"
        
        # Verificar volumen relativo usando dBFS
        # 20% volumen ≈ -14 dBFS (20 * log10(0.20) ≈ -14)
        # 100% volumen ≈ 0 dBFS (o cerca)
        
        section_1_dbfs = section_1.dBFS
        section_3_dbfs = section_3.dBFS
        
        # Verificar que sección 3 tiene mayor volumen que sección 1
        # La diferencia debería ser aproximadamente 14 dB (100% vs 20%)
        volume_difference = section_3_dbfs - section_1_dbfs
        
        # Permitir un margen de error debido a la compresión MP3 y procesamiento
        assert volume_difference >= 12.0, \
            f"Section 3 (100%) should be ~14dB louder than Section 1 (20%), got {volume_difference:.2f}dB difference"
        
        assert volume_difference <= 16.0, \
            f"Volume difference should be around 14dB, got {volume_difference:.2f}dB"
        
        # Verificar que la sección 2 (fade) tiene volumen intermedio
        section_2_start = processed_audio[fade_start:fade_start+100]  # Inicio del fade
        section_2_end = processed_audio[fade_end-100:fade_end]        # Final del fade
        
        section_2_start_dbfs = section_2_start.dBFS
        section_2_end_dbfs = section_2_end.dBFS
        
        # El inicio del fade debe estar cerca del volumen de sección 1 (20%)
        assert abs(section_2_start_dbfs - section_1_dbfs) <= 2.0, \
            f"Fade start should be close to 20% volume"
        
        # El final del fade debe estar cerca del volumen de sección 3 (100%)
        assert abs(section_2_end_dbfs - section_3_dbfs) <= 2.0, \
            f"Fade end should be close to 100% volume"
        
        # Verificar que hay una transición suave (el volumen aumenta gradualmente)
        assert section_2_end_dbfs > section_2_start_dbfs, \
            f"Volume should increase during fade section"
        
        # Verificar que el fade es gradual (no abrupto)
        # Tomamos muestras en el medio del fade
        section_2_mid = processed_audio[fade_start+2000:fade_start+2100]
        section_2_mid_dbfs = section_2_mid.dBFS
        
        # El volumen en el medio debe estar entre el inicio y el final
        assert section_2_start_dbfs < section_2_mid_dbfs < section_2_end_dbfs, \
            f"Fade should be gradual: start ({section_2_start_dbfs:.2f}dB) < " \
            f"mid ({section_2_mid_dbfs:.2f}dB) < end ({section_2_end_dbfs:.2f}dB)"
            
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


@audio_property_test()
@given(
    available_duration_ms=st.integers(min_value=6000, max_value=60000),  # 6s to 60s available
    calculated_duration_ms=st.integers(min_value=6000, max_value=60000)  # 6s to 60s calculated
)
def test_property_11_second_background_trimming(available_duration_ms, calculated_duration_ms):
    """
    Property 11: Second Background Trimming
    Feature: audio-gran-campana, Property 11: Second Background Trimming
    
    For any second background music file and calculated duration D, 
    the processed output should have duration exactly equal to D 
    (or the file's full duration if shorter than D).
    
    Validates: Requirements 5.1
    """
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Generar archivo de audio sintético con duración disponible
        audio_segment = Sine(440).to_audio_segment(duration=available_duration_ms)
        filename = "Eres todo poderoso.mp3"
        file_path = audio_dir / filename
        
        # Exportar como MP3
        audio_segment.export(str(file_path), format="mp3")
        
        # Procesar el archivo usando BackgroundMusicProcessor
        loader = FileLoader(audio_dir)
        processor = BackgroundMusicProcessor(loader)
        processed_audio = processor.process_second_background(calculated_duration_ms)
        
        # Determinar la duración esperada según la lógica:
        # - Si el archivo disponible es más largo o igual que lo calculado: usar duración calculada
        # - Si el archivo disponible es más corto que lo calculado: usar duración disponible completa
        expected_duration = min(available_duration_ms, calculated_duration_ms)
        
        # Verificar que la duración de salida es exactamente la esperada
        # Permitir un pequeño margen de error debido a la compresión MP3 (típicamente < 100ms)
        output_duration = len(processed_audio)
        duration_difference = abs(output_duration - expected_duration)
        
        assert duration_difference <= 100, \
            f"Output duration ({output_duration}ms) should equal expected duration ({expected_duration}ms), " \
            f"difference: {duration_difference}ms. " \
            f"Available: {available_duration_ms}ms, Calculated: {calculated_duration_ms}ms"
        
        # Verificar que el audio procesado tiene contenido válido
        assert processed_audio.frame_count() > 0, \
            "Processed audio should have valid audio content"
        
        # Verificar casos específicos:
        if available_duration_ms >= calculated_duration_ms:
            # Caso 1: Archivo suficientemente largo - debe recortar a duración calculada
            assert output_duration <= calculated_duration_ms + 100, \
                f"When file is long enough, output should be trimmed to calculated duration. " \
                f"Output: {output_duration}ms, Calculated: {calculated_duration_ms}ms"
        else:
            # Caso 2: Archivo más corto - debe usar duración completa disponible
            assert output_duration <= available_duration_ms + 100, \
                f"When file is shorter, output should use complete available duration. " \
                f"Output: {output_duration}ms, Available: {available_duration_ms}ms"
            
            # Verificar que NO se extiende más allá de lo disponible
            assert output_duration < calculated_duration_ms, \
                f"Output should not exceed available duration when file is shorter. " \
                f"Output: {output_duration}ms, Calculated: {calculated_duration_ms}ms"
        
        # Verificar que el procesamiento no lanza excepciones en ningún caso
        # (esto ya se verifica implícitamente al llegar aquí sin errores)
        
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)
def test_unify_backgrounds_success(test_audio_folder, file_loader):
    """Test successful unification of two background music segments."""
    # Create both background files
    first_audio = Sine(440).to_audio_segment(duration=10000)  # 10 seconds
    first_bg_path = test_audio_folder / "Yo tengo un amigo que me ama.mp3"
    first_audio.export(str(first_bg_path), format="mp3")

    second_audio = Sine(880).to_audio_segment(duration=8000)  # 8 seconds
    second_bg_path = test_audio_folder / "Eres todo poderoso.mp3"
    second_audio.export(str(second_bg_path), format="mp3")

    processor = BackgroundMusicProcessor(file_loader)

    # Process both backgrounds
    first_bg = processor.process_first_background()
    second_bg = processor.process_second_background(8000)

    # Unify backgrounds
    result = processor.unify_backgrounds(first_bg, second_bg)

    # Verify result is a BackgroundResult
    from src.models import BackgroundResult
    assert isinstance(result, BackgroundResult)

    # Verify audio is an AudioSegment
    assert isinstance(result.audio, AudioSegment)

    # Verify crossfade was applied
    assert result.crossfade_applied is True

    # Verify durations are stored correctly
    assert result.first_bg_duration_ms == len(first_bg)
    assert result.second_bg_duration_ms == len(second_bg)

    # Verify total duration is correct (first + second - crossfade)
    expected_duration = len(first_bg) + len(second_bg) - 3000
    assert abs(result.duration_ms - expected_duration) <= 100

    # Verify the unified audio has the expected duration
    assert abs(len(result.audio) - expected_duration) <= 100


def test_unify_backgrounds_duration_calculation(test_audio_folder, file_loader):
    """Test that unified background duration follows the crossfade formula."""
    # Create both background files with specific durations
    first_audio = Sine(440).to_audio_segment(duration=15000)  # 15 seconds
    first_bg_path = test_audio_folder / "Yo tengo un amigo que me ama.mp3"
    first_audio.export(str(first_bg_path), format="mp3")

    second_audio = Sine(880).to_audio_segment(duration=12000)  # 12 seconds
    second_bg_path = test_audio_folder / "Eres todo poderoso.mp3"
    second_audio.export(str(second_bg_path), format="mp3")

    processor = BackgroundMusicProcessor(file_loader)

    # Process both backgrounds
    first_bg = processor.process_first_background()
    second_bg = processor.process_second_background(12000)

    # Unify backgrounds
    result = processor.unify_backgrounds(first_bg, second_bg)

    # Calculate expected duration: first + second - crossfade (3000ms)
    first_duration = len(first_bg)
    second_duration = len(second_bg)
    expected_duration = first_duration + second_duration - 3000

    # Verify the duration matches the formula
    assert abs(result.duration_ms - expected_duration) <= 100, \
        f"Expected duration {expected_duration}ms, got {result.duration_ms}ms"

    # Verify the audio segment duration matches
    assert abs(len(result.audio) - expected_duration) <= 100


def test_unify_backgrounds_crossfade_applied(test_audio_folder, file_loader):
    """Test that crossfade is marked as applied in the result."""
    # Create both background files
    first_audio = Sine(440).to_audio_segment(duration=10000)
    first_bg_path = test_audio_folder / "Yo tengo un amigo que me ama.mp3"
    first_audio.export(str(first_bg_path), format="mp3")

    second_audio = Sine(880).to_audio_segment(duration=8000)
    second_bg_path = test_audio_folder / "Eres todo poderoso.mp3"
    second_audio.export(str(second_bg_path), format="mp3")

    processor = BackgroundMusicProcessor(file_loader)

    # Process both backgrounds
    first_bg = processor.process_first_background()
    second_bg = processor.process_second_background(8000)

    # Unify backgrounds
    result = processor.unify_backgrounds(first_bg, second_bg)

    # Verify crossfade was applied
    assert result.crossfade_applied is True


def test_calculate_second_background_duration_formula(processor):
    """Test the duration calculation formula with specific values."""
    # Test case 1: Standard case
    locutor_duration = 30000  # 30 seconds
    first_bg_duration = 10000  # 10 seconds
    
    # Formula: locutor + 10s - first_bg + 3s
    # 30000 + 10000 - 10000 + 3000 = 33000
    result = processor.calculate_second_background_duration(
        locutor_duration, first_bg_duration
    )
    assert result == 33000

    # Test case 2: Different values
    locutor_duration = 45000  # 45 seconds
    first_bg_duration = 15000  # 15 seconds
    
    # 45000 + 10000 - 15000 + 3000 = 43000
    result = processor.calculate_second_background_duration(
        locutor_duration, first_bg_duration
    )
    assert result == 43000

    # Test case 3: Edge case with short durations
    locutor_duration = 5000   # 5 seconds
    first_bg_duration = 8000  # 8 seconds
    
    # 5000 + 10000 - 8000 + 3000 = 10000
    result = processor.calculate_second_background_duration(
        locutor_duration, first_bg_duration
    )
    assert result == 10000


@settings(max_examples=20, deadline=None)  # No deadline for audio processing
@given(
    first_duration_ms=st.integers(min_value=6000, max_value=60000),  # At least 6s to avoid edge cases with fade sections
    second_duration_ms=st.integers(min_value=6000, max_value=60000)  # At least 6s to avoid edge cases with fade sections
)
def test_property_12_crossfade_duration_and_position(first_duration_ms, second_duration_ms):
    """
    Property 12: Crossfade Duration and Position
    Feature: audio-gran-campana, Property 12: Crossfade Duration and Position
    
    For any two background music segments unified with crossfade, the transition 
    should overlap the last 3 seconds of the first segment with the first 3 seconds 
    of the second segment, resulting in a total duration of 
    (first_duration + second_duration - 3000ms).
    
    Validates: Requirements 6.2, 6.6
    """
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Generar dos segmentos de audio sintéticos con duraciones aleatorias
        # Usamos diferentes frecuencias para poder distinguir los segmentos
        first_audio = Sine(440).to_audio_segment(duration=first_duration_ms)
        second_audio = Sine(880).to_audio_segment(duration=second_duration_ms)
        
        # Guardar archivos temporales
        first_bg_path = audio_dir / "Yo tengo un amigo que me ama.mp3"
        second_bg_path = audio_dir / "Eres todo poderoso.mp3"
        
        first_audio.export(str(first_bg_path), format="mp3")
        second_audio.export(str(second_bg_path), format="mp3")
        
        # Procesar ambos fondos usando BackgroundMusicProcessor
        loader = FileLoader(audio_dir)
        processor = BackgroundMusicProcessor(loader)
        
        # Procesar primer fondo (aplica efectos de volumen)
        first_bg_processed = processor.process_first_background()
        
        # Procesar segundo fondo (aplica efectos de volumen)
        second_bg_processed = processor.process_second_background(second_duration_ms)
        
        # Obtener duraciones reales después del procesamiento
        # (puede haber pequeñas diferencias debido a compresión MP3)
        actual_first_duration = len(first_bg_processed)
        actual_second_duration = len(second_bg_processed)
        
        # Unificar ambos fondos con crossfade
        result = processor.unify_backgrounds(first_bg_processed, second_bg_processed)
        
        # Verificar que el crossfade fue aplicado
        assert result.crossfade_applied is True, \
            "Crossfade should be marked as applied"
        
        # Verificar que las duraciones individuales se almacenan correctamente
        assert abs(result.first_bg_duration_ms - actual_first_duration) <= 10, \
            f"First background duration should be stored correctly"
        
        assert abs(result.second_bg_duration_ms - actual_second_duration) <= 10, \
            f"Second background duration should be stored correctly"
        
        # Verificar la fórmula de duración total: first + second - 3000ms
        # La duración total debe ser la suma de ambas duraciones menos el crossfade de 3 segundos
        expected_total_duration = actual_first_duration + actual_second_duration - 3000
        actual_total_duration = len(result.audio)
        
        # Permitir un margen de error debido a la compresión MP3 y procesamiento
        duration_difference = abs(actual_total_duration - expected_total_duration)
        
        assert duration_difference <= 100, \
            f"Total duration should equal first + second - 3000ms. " \
            f"Expected: {expected_total_duration}ms, Got: {actual_total_duration}ms, " \
            f"Difference: {duration_difference}ms. " \
            f"First: {actual_first_duration}ms, Second: {actual_second_duration}ms"
        
        # Verificar que result.duration_ms coincide con la duración real del audio
        assert abs(result.duration_ms - actual_total_duration) <= 10, \
            f"Stored duration should match actual audio duration"
        
        # Verificar que el overlap es exactamente de 3 segundos
        # El overlap significa que los últimos 3 segundos del primer segmento
        # se superponen con los primeros 3 segundos del segundo segmento
        crossfade_duration = 3000
        
        # La reducción en duración total debe ser exactamente el crossfade
        duration_reduction = (actual_first_duration + actual_second_duration) - actual_total_duration
        
        assert abs(duration_reduction - crossfade_duration) <= 100, \
            f"Duration reduction should equal crossfade duration (3000ms). " \
            f"Expected reduction: {crossfade_duration}ms, Actual reduction: {duration_reduction}ms"
        
        # Verificar que el audio unificado tiene contenido válido
        assert result.audio.frame_count() > 0, \
            "Unified audio should have valid audio content"
        
        # Verificar que la duración del audio unificado es menor que la suma simple
        # (esto confirma que hay overlap, no concatenación simple)
        simple_concatenation_duration = actual_first_duration + actual_second_duration
        
        assert actual_total_duration < simple_concatenation_duration, \
            f"Unified duration ({actual_total_duration}ms) should be less than " \
            f"simple concatenation ({simple_concatenation_duration}ms) due to crossfade overlap"
        
        # Verificar que la diferencia es aproximadamente el crossfade
        overlap_amount = simple_concatenation_duration - actual_total_duration
        
        assert abs(overlap_amount - crossfade_duration) <= 100, \
            f"Overlap amount should be approximately {crossfade_duration}ms, got {overlap_amount}ms"
        
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)





@settings(max_examples=20, deadline=None)  # No deadline for audio processing
@given(
    first_duration_ms=st.integers(min_value=6000, max_value=60000),  # At least 6s to avoid edge cases
    second_duration_ms=st.integers(min_value=6000, max_value=60000)  # At least 6s to avoid edge cases
)
def test_property_13_background_unification_completeness(first_duration_ms, second_duration_ms):
    """
    Property 13: Background Unification Completeness
    Feature: audio-gran-campana, Property 13: Background Unification Completeness
    
    For any two processed background music segments, the unified output should 
    contain audio content from both segments with a smooth volume transition 
    at the crossfade point.
    
    Validates: Requirements 6.1, 6.5
    """
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Generar dos segmentos de audio sintéticos con duraciones aleatorias
        # Usamos diferentes frecuencias para poder distinguir los segmentos
        # Primer segmento: 440Hz (La4)
        # Segundo segmento: 880Hz (La5, una octava más alta)
        first_audio = Sine(440).to_audio_segment(duration=first_duration_ms)
        second_audio = Sine(880).to_audio_segment(duration=second_duration_ms)
        
        # Guardar archivos temporales
        first_bg_path = audio_dir / "Yo tengo un amigo que me ama.mp3"
        second_bg_path = audio_dir / "Eres todo poderoso.mp3"
        
        first_audio.export(str(first_bg_path), format="mp3")
        second_audio.export(str(second_bg_path), format="mp3")
        
        # Procesar ambos fondos usando BackgroundMusicProcessor
        loader = FileLoader(audio_dir)
        processor = BackgroundMusicProcessor(loader)
        
        # Procesar primer fondo (aplica efectos de volumen)
        first_bg_processed = processor.process_first_background()
        
        # Procesar segundo fondo (aplica efectos de volumen)
        second_bg_processed = processor.process_second_background(second_duration_ms)
        
        # Obtener duraciones reales después del procesamiento
        actual_first_duration = len(first_bg_processed)
        actual_second_duration = len(second_bg_processed)
        
        # Unificar ambos fondos con crossfade
        result = processor.unify_backgrounds(first_bg_processed, second_bg_processed)
        
        # Verificar que el resultado contiene audio válido
        assert result.audio is not None, \
            "Unified audio should not be None"
        
        assert isinstance(result.audio, AudioSegment), \
            "Unified audio should be an AudioSegment"
        
        assert result.audio.frame_count() > 0, \
            "Unified audio should have valid audio content (frame_count > 0)"
        
        # Verificar que el audio unificado tiene una duración razonable
        unified_duration = len(result.audio)
        assert unified_duration > 0, \
            "Unified audio should have positive duration"
        
        # Verificar que contiene contenido de ambos segmentos
        # La duración unificada debe ser mayor que cualquiera de los segmentos individuales
        # (pero menor que la suma debido al crossfade)
        assert unified_duration > max(actual_first_duration, actual_second_duration), \
            f"Unified audio ({unified_duration}ms) should be longer than either individual segment " \
            f"(first: {actual_first_duration}ms, second: {actual_second_duration}ms)"
        
        # Verificar que la duración es menor que la suma simple (confirma que hay crossfade)
        simple_sum = actual_first_duration + actual_second_duration
        assert unified_duration < simple_sum, \
            f"Unified audio ({unified_duration}ms) should be shorter than simple concatenation " \
            f"({simple_sum}ms) due to crossfade overlap"
        
        # Verificar que el crossfade fue aplicado (transición suave)
        assert result.crossfade_applied is True, \
            "Crossfade should be marked as applied"
        
        # Verificar que hay contenido de audio en diferentes secciones del audio unificado
        # Esto confirma que ambos segmentos están presentes
        
        # Sección del primer segmento (antes del crossfade)
        # Tomamos una muestra del medio del primer segmento
        first_segment_sample_start = actual_first_duration // 2
        first_segment_sample_end = first_segment_sample_start + 1000  # 1 segundo de muestra
        first_segment_sample = result.audio[first_segment_sample_start:first_segment_sample_end]
        
        # Sección del segundo segmento (después del crossfade)
        # Tomamos una muestra del final del audio unificado
        second_segment_sample_start = unified_duration - (actual_second_duration // 2)
        second_segment_sample_end = second_segment_sample_start + 1000  # 1 segundo de muestra
        second_segment_sample = result.audio[second_segment_sample_start:second_segment_sample_end]
        
        # Verificar que ambas muestras tienen contenido de audio válido
        assert first_segment_sample.frame_count() > 0, \
            "First segment section should have audio content"
        
        assert second_segment_sample.frame_count() > 0, \
            "Second segment section should have audio content"
        
        # Verificar que ambas muestras tienen volumen audible (no están en silencio)
        # dBFS de -infinity significa silencio completo
        first_segment_dbfs = first_segment_sample.dBFS
        second_segment_dbfs = second_segment_sample.dBFS
        
        assert first_segment_dbfs > -60.0, \
            f"First segment should have audible content (dBFS: {first_segment_dbfs:.2f})"
        
        assert second_segment_dbfs > -60.0, \
            f"Second segment should have audible content (dBFS: {second_segment_dbfs:.2f})"
        
        # Verificar la transición suave en el punto de crossfade
        # El crossfade ocurre entre (actual_first_duration - 3000) y actual_first_duration
        crossfade_start = actual_first_duration - 3000
        crossfade_end = actual_first_duration
        
        # Tomar muestras antes, durante y después del crossfade
        before_crossfade = result.audio[crossfade_start - 500:crossfade_start - 400]  # 100ms antes
        during_crossfade = result.audio[crossfade_start + 1400:crossfade_start + 1600]  # 200ms en medio
        after_crossfade = result.audio[crossfade_end + 400:crossfade_end + 500]  # 100ms después
        
        # Verificar que todas las secciones tienen contenido de audio
        assert before_crossfade.frame_count() > 0, \
            "Audio before crossfade should have content"
        
        assert during_crossfade.frame_count() > 0, \
            "Audio during crossfade should have content"
        
        assert after_crossfade.frame_count() > 0, \
            "Audio after crossfade should have content"
        
        # Verificar que no hay silencio en el crossfade (transición suave)
        before_dbfs = before_crossfade.dBFS
        during_dbfs = during_crossfade.dBFS
        after_dbfs = after_crossfade.dBFS
        
        assert before_dbfs > -60.0, \
            f"Audio before crossfade should be audible (dBFS: {before_dbfs:.2f})"
        
        assert during_dbfs > -60.0, \
            f"Audio during crossfade should be audible (dBFS: {during_dbfs:.2f})"
        
        assert after_dbfs > -60.0, \
            f"Audio after crossfade should be audible (dBFS: {after_dbfs:.2f})"
        
        # Verificar que no hay cambios abruptos de volumen (transición suave)
        # La diferencia de volumen entre secciones consecutivas no debe ser muy grande
        before_to_during_diff = abs(before_dbfs - during_dbfs)
        during_to_after_diff = abs(during_dbfs - after_dbfs)
        
        # Permitir hasta 13dB de diferencia entre secciones consecutivas
        # (más de 13dB sería un cambio abrupto)
        # El crossfade puede crear diferencias de hasta ~12dB debido a los efectos de volumen
        # aplicados a cada segmento (25% en primer fondo, 20% en segundo fondo)
        # Usamos 13dB para dar margen a errores de redondeo de punto flotante y compresión MP3
        assert before_to_during_diff <= 13.0, \
            f"Volume transition should be smooth (before to during: {before_to_during_diff:.2f}dB)"
        
        assert during_to_after_diff <= 13.0, \
            f"Volume transition should be smooth (during to after: {during_to_after_diff:.2f}dB)"
        
        # Verificar que el audio unificado preserva las propiedades de audio básicas
        assert result.audio.frame_rate > 0, \
            "Unified audio should have valid frame rate"
        
        assert result.audio.channels > 0, \
            "Unified audio should have valid channel count"
        
        assert result.audio.sample_width > 0, \
            "Unified audio should have valid sample width"
        
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)
