"""
Unit tests for FileLoader component.

Tests verifican la carga de archivos WAV y MP3, manejo de archivos faltantes,
y carga múltiple de archivos.
"""

import pytest
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine
from hypothesis import given, strategies as st
from tests.hypothesis_config import audio_property_test
from tests.hypothesis_strategies import audio_format_choice

from src.file_loader import FileLoader


@pytest.fixture
def temp_audio_dir(tmp_path):
    """Crea un directorio temporal con archivos de audio de prueba."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    
    # Crear archivo WAV de prueba (1 segundo de silencio)
    silent_audio = AudioSegment.silent(duration=1000)
    wav_path = audio_dir / "test_file.wav"
    silent_audio.export(str(wav_path), format="wav")
    
    # Crear archivo MP3 de prueba (1 segundo de tono)
    tone = Sine(440).to_audio_segment(duration=1000)
    mp3_path = audio_dir / "test_file.mp3"
    tone.export(str(mp3_path), format="mp3")
    
    return audio_dir


def test_load_wav_file(temp_audio_dir):
    """Test carga de archivo WAV específico."""
    loader = FileLoader(temp_audio_dir)
    audio = loader.load_audio("test_file.wav")
    
    assert audio is not None
    assert isinstance(audio, AudioSegment)
    assert len(audio) == 1000  # 1 segundo


def test_load_mp3_file(temp_audio_dir):
    """Test carga de archivo MP3 específico."""
    loader = FileLoader(temp_audio_dir)
    audio = loader.load_audio("test_file.mp3")
    
    assert audio is not None
    assert isinstance(audio, AudioSegment)
    assert len(audio) == 1000  # 1 segundo


def test_load_nonexistent_file(temp_audio_dir):
    """Test manejo de archivo inexistente."""
    loader = FileLoader(temp_audio_dir)
    audio = loader.load_audio("nonexistent.wav")
    
    assert audio is None


def test_load_multiple_mixed_formats(temp_audio_dir):
    """Test carga múltiple con mix de formatos."""
    loader = FileLoader(temp_audio_dir)
    
    filenames = ["test_file.wav", "test_file.mp3", "missing.wav"]
    results = loader.load_multiple(filenames)
    
    assert len(results) == 3
    assert results["test_file.wav"] is not None
    assert results["test_file.mp3"] is not None
    assert results["missing.wav"] is None


def test_load_multiple_all_present(temp_audio_dir):
    """Test carga múltiple con todos los archivos presentes."""
    loader = FileLoader(temp_audio_dir)
    
    filenames = ["test_file.wav", "test_file.mp3"]
    results = loader.load_multiple(filenames)
    
    assert len(results) == 2
    assert all(audio is not None for audio in results.values())


def test_load_multiple_all_missing(temp_audio_dir):
    """Test carga múltiple con todos los archivos faltantes."""
    loader = FileLoader(temp_audio_dir)
    
    filenames = ["missing1.wav", "missing2.mp3"]
    results = loader.load_multiple(filenames)
    
    assert len(results) == 2
    assert all(audio is None for audio in results.values())


# Property-Based Tests

@audio_property_test()
@given(
    duration_ms=st.integers(min_value=100, max_value=5000),
    format_choice=audio_format_choice()
)
def test_property_1_multi_format_audio_loading(duration_ms, format_choice):
    """
    Property 1: Multi-format Audio Loading
    Feature: audio-gran-campana, Property 1: Multi-format Audio Loading
    
    For any audio file in WAV or MP3 format, the FileLoader should successfully 
    load it into an AudioSegment object with preserved audio properties.
    
    Validates: Requirements 1.4, 1.5
    """
    import tempfile
    import shutil
    
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Generar archivo de audio sintético con duración aleatoria
        audio_segment = AudioSegment.silent(duration=duration_ms)
        filename = f"test_audio.{format_choice}"
        file_path = audio_dir / filename
        
        # Exportar en el formato especificado
        audio_segment.export(str(file_path), format=format_choice)
        
        # Cargar el archivo usando FileLoader
        loader = FileLoader(audio_dir)
        loaded_audio = loader.load_audio(filename)
        
        # Verificar que se cargó correctamente
        assert loaded_audio is not None, f"FileLoader should load {format_choice.upper()} files"
        assert isinstance(loaded_audio, AudioSegment), "Loaded audio should be an AudioSegment"
        
        # Verificar que las propiedades de audio se preservan
        assert abs(len(loaded_audio) - duration_ms) <= 50, \
            f"Duration should be preserved (expected ~{duration_ms}ms, got {len(loaded_audio)}ms)"
        assert loaded_audio.frame_rate > 0, "Frame rate should be positive"
        assert loaded_audio.channels > 0, "Channels should be positive"
        assert loaded_audio.sample_width > 0, "Sample width should be positive"
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


