"""
Tests for volume normalization functionality in LocutorProcessor.

Este módulo contiene tests específicos para la funcionalidad de normalización
de volumen agregada al LocutorProcessor.
"""

import pytest
from pathlib import Path
from pydub import AudioSegment
from unittest.mock import Mock, patch

from src.locutor_processor import LocutorProcessor
from src.file_loader import FileLoader


@pytest.fixture
def test_audio_segments():
    """Crear segmentos de audio de prueba con diferentes volúmenes."""
    # Crear audio de prueba con diferentes niveles de volumen
    quiet_audio = AudioSegment.silent(duration=1000).apply_gain(-30)  # Muy silencioso
    normal_audio = AudioSegment.silent(duration=1000).apply_gain(-20)  # Normal
    loud_audio = AudioSegment.silent(duration=1000).apply_gain(-10)   # Fuerte
    
    # Agregar algo de contenido para que no sean completamente silenciosos
    # Generar un tono simple para cada uno
    from pydub.generators import Sine
    
    tone_quiet = Sine(440).to_audio_segment(duration=1000).apply_gain(-35)
    tone_normal = Sine(440).to_audio_segment(duration=1000).apply_gain(-25)
    tone_loud = Sine(440).to_audio_segment(duration=1000).apply_gain(-15)
    
    return {
        'quiet': tone_quiet,
        'normal': tone_normal,
        'loud': tone_loud
    }


@pytest.fixture
def mock_file_loader(test_audio_segments):
    """Mock FileLoader que retorna archivos con diferentes volúmenes."""
    mock_loader = Mock(spec=FileLoader)
    
    # Mapear archivos a diferentes niveles de volumen
    file_mapping = {
        'Gran Campaña - Introduccion.wav': test_audio_segments['normal'],
        'Gran Campaña - Hora y lugar del evento.mp3': test_audio_segments['loud'],  # Este es el problemático
        'Gran Campaña - Cuerpo.mp3': test_audio_segments['normal'],
        'Gran Campaña - Cierre.mp3': test_audio_segments['quiet']
    }
    
    def mock_load_audio(filename):
        return file_mapping.get(filename)
    
    mock_loader.load_audio.side_effect = mock_load_audio
    return mock_loader


def test_normalize_volume_basic(mock_file_loader, test_audio_segments):
    """Test básico de normalización de volumen."""
    processor = LocutorProcessor(mock_file_loader)
    
    # Tomar el audio fuerte y normalizarlo
    loud_audio = test_audio_segments['loud']
    original_dbfs = loud_audio.dBFS
    
    # Normalizar a -20dBFS
    normalized = processor._normalize_volume(loud_audio, target_dbfs=-20.0)
    
    # Verificar que el volumen cambió hacia el objetivo
    assert abs(normalized.dBFS - (-20.0)) < 1.0  # Tolerancia de 1dB
    assert normalized.dBFS != original_dbfs


def test_calculate_optimal_target_volume(mock_file_loader):
    """Test del cálculo automático del volumen objetivo."""
    processor = LocutorProcessor(mock_file_loader)
    
    # Calcular el volumen objetivo óptimo
    target_volume = processor.calculate_optimal_target_volume()
    
    # Debería estar en un rango razonable
    assert -25.0 <= target_volume <= -12.0
    
    # Debería ser un valor numérico válido
    assert isinstance(target_volume, float)
    assert target_volume != float('-inf')
    assert target_volume != float('inf')


def test_unify_with_volume_normalization(mock_file_loader):
    """Test de unificación con normalización de volumen habilitada."""
    processor = LocutorProcessor(mock_file_loader)
    
    # Procesar con normalización habilitada
    result = processor.unify_locutor_audio(normalize_volume=True, target_dbfs=-18.0)
    
    # Verificar que se procesaron archivos
    assert len(result.files_loaded) > 0
    assert result.audio is not None
    assert result.duration_ms > 0
    
    # El audio final debería tener un volumen más consistente
    # (esto es difícil de verificar exactamente, pero al menos no debería fallar)
    assert result.audio.dBFS != float('-inf')


def test_unify_with_auto_volume_normalization(mock_file_loader):
    """Test de unificación con normalización automática."""
    processor = LocutorProcessor(mock_file_loader)
    
    # Procesar con normalización automática
    result = processor.unify_locutor_audio_with_auto_volume()
    
    # Verificar que se procesaron archivos
    assert len(result.files_loaded) > 0
    assert result.audio is not None
    assert result.duration_ms > 0
    
    # Verificar que se cargaron los archivos esperados
    expected_files = [
        'Gran Campaña - Introduccion.wav',
        'Gran Campaña - Hora y lugar del evento.mp3',
        'Gran Campaña - Cuerpo.mp3',
        'Gran Campaña - Cierre.mp3'
    ]
    
    # Al menos algunos archivos deberían haberse cargado
    assert any(f in result.files_loaded for f in expected_files)


def test_normalize_silent_audio(mock_file_loader):
    """Test de normalización con audio completamente silencioso."""
    processor = LocutorProcessor(mock_file_loader)
    
    # Crear audio completamente silencioso
    silent_audio = AudioSegment.silent(duration=1000)
    
    # Intentar normalizar (debería manejar el caso graciosamente)
    normalized = processor._normalize_volume(silent_audio, target_dbfs=-20.0)
    
    # Debería retornar el audio original sin cambios
    assert len(normalized) == len(silent_audio)
    assert normalized.dBFS == float('-inf')  # Sigue siendo silencioso


def test_volume_normalization_preserves_duration(mock_file_loader, test_audio_segments):
    """Test que la normalización preserve la duración del audio."""
    processor = LocutorProcessor(mock_file_loader)
    
    original_audio = test_audio_segments['loud']
    original_duration = len(original_audio)
    
    # Normalizar
    normalized = processor._normalize_volume(original_audio, target_dbfs=-20.0)
    
    # La duración debería ser la misma
    assert len(normalized) == original_duration


def test_volume_analysis_with_missing_files():
    """Test del análisis de volumen cuando algunos archivos faltan."""
    # Crear un mock que solo retorna algunos archivos
    mock_loader = Mock(spec=FileLoader)
    
    def mock_load_audio(filename):
        from pydub.generators import Sine
        if filename == 'Gran Campaña - Introduccion.wav':
            return Sine(440).to_audio_segment(duration=1000).apply_gain(-25)
        elif filename == 'Gran Campaña - Cuerpo.mp3':
            return Sine(440).to_audio_segment(duration=1000).apply_gain(-15)
        else:
            return None  # Archivo faltante
    
    mock_loader.load_audio.side_effect = mock_load_audio
    
    processor = LocutorProcessor(mock_loader)
    
    # Calcular volumen objetivo con archivos faltantes
    target_volume = processor.calculate_optimal_target_volume()
    
    # Debería funcionar y retornar un valor razonable
    assert -25.0 <= target_volume <= -12.0
    assert isinstance(target_volume, float)


if __name__ == '__main__':
    pytest.main([__file__])