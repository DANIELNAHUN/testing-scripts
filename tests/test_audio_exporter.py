"""
Tests for AudioExporter component.

Tests verifican la exportación a MP3 con bitrate correcto, preservación de calidad,
y logging de información de exportación.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine
from hypothesis import given, strategies as st
from tests.hypothesis_config import audio_property_test
from tests.hypothesis_strategies import audio_segment_with_duration, audio_properties
import mutagen
from mutagen.mp3 import MP3

from src.audio_exporter import AudioExporter


@pytest.fixture
def temp_output_dir():
    """Crea un directorio temporal para archivos de salida."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_export_basic_functionality(temp_output_dir):
    """Test exportación básica a MP3."""
    exporter = AudioExporter(temp_output_dir)
    
    # Crear audio de prueba (1 segundo de tono)
    audio = Sine(440).to_audio_segment(duration=1000)
    
    # Exportar
    output_path = exporter.export(audio, "test_output")
    
    # Verificar que el archivo se creó
    assert output_path.exists()
    assert output_path.suffix == ".mp3"
    assert output_path.name == "test_output.mp3"


def test_export_with_mp3_extension(temp_output_dir):
    """Test exportación cuando el filename ya incluye extensión .mp3."""
    exporter = AudioExporter(temp_output_dir)
    
    # Crear audio de prueba
    audio = AudioSegment.silent(duration=500)
    
    # Exportar con extensión incluida
    output_path = exporter.export(audio, "test_output.mp3")
    
    # Verificar que no se duplica la extensión
    assert output_path.name == "test_output.mp3"
    assert output_path.exists()


def test_export_creates_output_directory(tmp_path):
    """Test que el exporter crea el directorio de salida si no existe."""
    non_existent_dir = tmp_path / "new_output_dir"
    assert not non_existent_dir.exists()
    
    exporter = AudioExporter(non_existent_dir)
    
    # El directorio debe haberse creado
    assert non_existent_dir.exists()
    assert non_existent_dir.is_dir()


def test_export_bitrate_verification(temp_output_dir):
    """Test verificación de bitrate mínimo de 192 kbps."""
    exporter = AudioExporter(temp_output_dir)
    
    # Crear audio de prueba con propiedades específicas
    audio = Sine(440).to_audio_segment(duration=2000)
    
    # Exportar
    output_path = exporter.export(audio, "bitrate_test")
    
    # Verificar bitrate usando mutagen
    mp3_file = MP3(str(output_path))
    bitrate = mp3_file.info.bitrate
    
    # Verificar que el bitrate es al menos 192 kbps
    assert bitrate >= 192, f"Bitrate should be at least 192 kbps, got {bitrate} kbps"


def test_export_format_verification(temp_output_dir):
    """Test verificación de formato MP3."""
    exporter = AudioExporter(temp_output_dir)
    
    # Crear audio de prueba
    audio = AudioSegment.silent(duration=1000)
    
    # Exportar
    output_path = exporter.export(audio, "format_test")
    
    # Verificar que es un archivo MP3 válido
    mp3_file = MP3(str(output_path))
    assert mp3_file.info is not None
    assert mp3_file.info.length > 0


# Property-Based Tests

@settings(max_examples=20, deadline=5000)  # 5 second deadline for export operations
@given(
    duration_ms=st.integers(min_value=500, max_value=10000),
    sample_rate=st.sampled_from([22050, 44100, 48000]),
    channels=st.sampled_from([1, 2])
)
def test_property_18_mp3_export_format_and_quality(duration_ms, sample_rate, channels):
    """
    Property 18: MP3 Export Format and Quality
    Feature: audio-gran-campana, Property 18: MP3 Export Format and Quality
    
    For any audio exported to MP3 format, the output file should have MP3 format 
    with a bitrate of at least 192 kbps.
    
    Validates: Requirements 9.1, 9.3
    """
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    try:
        output_dir = Path(temp_dir)
        exporter = AudioExporter(output_dir)
        
        # Generar archivo de audio aleatorio con propiedades específicas
        audio = Sine(440).to_audio_segment(duration=duration_ms)
        audio = audio.set_frame_rate(sample_rate)
        audio = audio.set_channels(channels)
        
        # Exportar a MP3
        output_path = exporter.export(audio, f"test_export_{duration_ms}")
        
        # Verificar que el archivo existe y es MP3
        assert output_path.exists(), "Exported file should exist"
        assert output_path.suffix == ".mp3", "Exported file should have .mp3 extension"
        
        # Verificar formato MP3 y bitrate usando mutagen
        mp3_file = MP3(str(output_path))
        assert mp3_file.info is not None, "File should be a valid MP3"
        
        # Verificar bitrate mínimo de 192 kbps
        bitrate = mp3_file.info.bitrate
        assert bitrate >= 192, f"Bitrate should be at least 192 kbps, got {bitrate} kbps"
        
        # Verificar que el archivo tiene contenido de audio válido
        assert mp3_file.info.length > 0, "MP3 should have positive duration"
        
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


@settings(max_examples=20, deadline=5000)  # 5 second deadline for export operations
@given(
    duration_ms=st.integers(min_value=1000, max_value=8000),
    sample_rate=st.sampled_from([22050, 44100, 48000]),
    channels=st.sampled_from([1, 2]),
    sample_width=st.sampled_from([1, 2])  # 1 = 8-bit, 2 = 16-bit
)
def test_property_19_export_quality_preservation(duration_ms, sample_rate, channels, sample_width):
    """
    Property 19: Export Quality Preservation
    Feature: audio-gran-campana, Property 19: Export Quality Preservation
    
    For any audio exported to file, the output should preserve the audio properties 
    (sample rate, channels) of the input audio.
    
    Validates: Requirements 9.4
    """
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    try:
        output_dir = Path(temp_dir)
        exporter = AudioExporter(output_dir)
        
        # Generar archivo de audio con propiedades específicas
        audio = Sine(440).to_audio_segment(duration=duration_ms)
        audio = audio.set_frame_rate(sample_rate)
        audio = audio.set_channels(channels)
        audio = audio.set_sample_width(sample_width)
        
        # Guardar propiedades originales
        original_sample_rate = audio.frame_rate
        original_channels = audio.channels
        original_sample_width = audio.sample_width
        
        # Exportar a MP3
        output_path = exporter.export(audio, f"quality_test_{sample_rate}_{channels}")
        
        # Cargar el archivo exportado para verificar propiedades
        exported_audio = AudioSegment.from_mp3(str(output_path))
        
        # Verificar preservación de propiedades de audio
        # Nota: MP3 puede cambiar sample_width debido a la compresión, pero sample_rate y channels deben preservarse
        assert exported_audio.frame_rate == original_sample_rate, \
            f"Sample rate should be preserved (expected {original_sample_rate}, got {exported_audio.frame_rate})"
        
        assert exported_audio.channels == original_channels, \
            f"Channels should be preserved (expected {original_channels}, got {exported_audio.channels})"
        
        # Verificar que la duración se preserva aproximadamente (tolerancia para compresión MP3)
        duration_diff = abs(len(exported_audio) - duration_ms)
        assert duration_diff <= 100, \
            f"Duration should be approximately preserved (expected ~{duration_ms}ms, got {len(exported_audio)}ms, diff: {duration_diff}ms)"
        
        # Verificar que el audio exportado tiene contenido válido
        assert len(exported_audio) > 0, "Exported audio should have positive duration"
        assert exported_audio.frame_rate > 0, "Exported audio should have positive frame rate"
        assert exported_audio.channels > 0, "Exported audio should have positive channel count"
        
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_export_logging_information(temp_output_dir, caplog):
    """Test logging de información de exportación."""
    import logging
    
    # Configurar logging para capturar mensajes
    caplog.set_level(logging.INFO)
    
    exporter = AudioExporter(temp_output_dir)
    
    # Crear audio de prueba con propiedades conocidas
    audio = Sine(440).to_audio_segment(duration=2000)  # 2 segundos
    audio = audio.set_frame_rate(44100)
    audio = audio.set_channels(2)
    
    # Exportar
    output_path = exporter.export(audio, "logging_test")
    
    # Verificar que se registraron los logs esperados
    log_messages = [record.message for record in caplog.records]
    
    # Verificar log de inicio de exportación
    assert any("Starting export to MP3" in msg for msg in log_messages), \
        "Should log export start"
    
    # Verificar log de éxito con path y duración
    assert any("Successfully exported audio to" in msg and str(output_path) in msg for msg in log_messages), \
        "Should log successful export with path"
    
    # Verificar log de detalles de exportación (duración, bitrate, etc.)
    assert any("Export details" in msg and "Duration: 2.00s" in msg for msg in log_messages), \
        "Should log export details with duration"
    
    assert any("Bitrate: 192k" in msg for msg in log_messages), \
        "Should log bitrate information"


def test_export_error_handling(temp_output_dir):
    """Test manejo de errores durante exportación."""
    from src.exceptions import AudioProcessingError
    
    exporter = AudioExporter(temp_output_dir)
    
    # Intentar exportar audio None (debería fallar)
    with pytest.raises(AudioProcessingError) as exc_info:
        exporter.export(None, "error_test")
    
    # Verificar que el error contiene información útil
    assert "Cannot export None audio segment" in str(exc_info.value)


def test_export_invalid_output_path():
    """Test manejo de path de salida inválido."""
    from src.exceptions import AudioProcessingError
    
    # Intentar crear exporter con path inválido (archivo en lugar de directorio)
    invalid_path = Path("/dev/null")  # Este es un archivo especial, no un directorio
    
    # El constructor debería fallar con path inválido
    with pytest.raises(AudioProcessingError) as exc_info:
        AudioExporter(invalid_path)
    
    # Verificar que el error contiene información útil
    assert "not a directory" in str(exc_info.value) or "Failed to create output directory" in str(exc_info.value)


def test_export_preserves_filename_without_extension(temp_output_dir):
    """Test que el export preserva nombres de archivo sin extensión."""
    exporter = AudioExporter(temp_output_dir)
    
    # Crear audio de prueba
    audio = AudioSegment.silent(duration=500)
    
    # Exportar con nombre sin extensión
    output_path = exporter.export(audio, "test_file_name")
    
    # Verificar que se agregó la extensión .mp3
    assert output_path.name == "test_file_name.mp3"
    assert output_path.exists()


def test_export_different_audio_properties(temp_output_dir):
    """Test exportación con diferentes propiedades de audio."""
    exporter = AudioExporter(temp_output_dir)
    
    # Test con audio mono
    mono_audio = Sine(440).to_audio_segment(duration=1000).set_channels(1)
    mono_path = exporter.export(mono_audio, "mono_test")
    assert mono_path.exists()
    
    # Test con audio estéreo
    stereo_audio = Sine(440).to_audio_segment(duration=1000).set_channels(2)
    stereo_path = exporter.export(stereo_audio, "stereo_test")
    assert stereo_path.exists()
    
    # Test con diferentes sample rates
    low_rate_audio = Sine(440).to_audio_segment(duration=1000).set_frame_rate(22050)
    low_rate_path = exporter.export(low_rate_audio, "low_rate_test")
    assert low_rate_path.exists()
    
    high_rate_audio = Sine(440).to_audio_segment(duration=1000).set_frame_rate(48000)
    high_rate_path = exporter.export(high_rate_audio, "high_rate_test")
    assert high_rate_path.exists()