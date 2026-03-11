"""
Unit tests for LocutorProcessor.

Tests the locutor audio unification functionality including:
- Concatenation in correct order
- Handling of missing files
- Duration calculation
- Metadata tracking
"""

import pytest
from pathlib import Path
from pydub import AudioSegment
from hypothesis import given, strategies as st
from tests.hypothesis_config import audio_property_test
from tests.hypothesis_strategies import (
    file_existence_pattern, 
    duration_list, 
    audio_properties,
    audio_segment_with_duration
)

from src.file_loader import FileLoader
from src.locutor_processor import LocutorProcessor
from src.models import LocutorResult


@pytest.fixture
def test_audio_dir(tmp_path):
    """Create a temporary directory with test audio files."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    
    # Create test audio files with different durations
    # Using silent audio for testing
    intro = AudioSegment.silent(duration=1000)  # 1 second
    hora_lugar = AudioSegment.silent(duration=2000)  # 2 seconds
    cuerpo = AudioSegment.silent(duration=3000)  # 3 seconds
    cierre = AudioSegment.silent(duration=1500)  # 1.5 seconds
    
    # Export test files
    intro.export(audio_dir / "Gran Campaña - Introduccion.wav", format="wav")
    hora_lugar.export(audio_dir / "Gran Campaña - Hora y lugar del evento.mp3", format="mp3")
    cuerpo.export(audio_dir / "Gran Campaña - Cuerpo.wav", format="wav")
    cierre.export(audio_dir / "Gran Campaña - Cierre.wav", format="wav")
    
    return audio_dir


@pytest.fixture
def file_loader(test_audio_dir):
    """Create a FileLoader instance with test audio directory."""
    return FileLoader(test_audio_dir)


@pytest.fixture
def locutor_processor(file_loader):
    """Create a LocutorProcessor instance."""
    return LocutorProcessor(file_loader)


def test_locutor_sequence_constant():
    """Test that LOCUTOR_SEQUENCE constant is defined correctly."""
    expected_sequence = [
        'Gran Campaña - Introduccion.wav',
        'Gran Campaña - Hora y lugar del evento.mp3',
        'Gran Campaña - Cuerpo.wav',
        'Gran Campaña - Hora y lugar del evento.mp3',
        'Gran Campaña - Cierre.wav'
    ]
    assert LocutorProcessor.LOCUTOR_SEQUENCE == expected_sequence


def test_unify_locutor_audio_all_files_present(locutor_processor):
    """Test unification when all files are present."""
    result = locutor_processor.unify_locutor_audio()
    
    # Verify result type
    assert isinstance(result, LocutorResult)
    assert isinstance(result.audio, AudioSegment)
    
    # Verify files loaded (4 unique files, one repeated)
    assert len(result.files_loaded) == 5  # All 5 positions in sequence
    assert len(result.files_skipped) == 0
    
    # Verify duration (1000 + 2000 + 3000 + 2000 + 1500 = 9500ms)
    # Note: Second file appears twice in sequence
    assert result.duration_ms == 9500
    
    # Verify metadata
    assert 'Gran Campaña - Introduccion.wav' in result.files_loaded
    assert 'Gran Campaña - Cuerpo.wav' in result.files_loaded
    assert 'Gran Campaña - Cierre.wav' in result.files_loaded


def test_unify_locutor_audio_with_missing_files(test_audio_dir):
    """Test unification when some files are missing."""
    # Only create intro and cierre files
    intro = AudioSegment.silent(duration=1000)
    cierre = AudioSegment.silent(duration=1500)
    
    intro.export(test_audio_dir / "Gran Campaña - Introduccion.wav", format="wav")
    cierre.export(test_audio_dir / "Gran Campaña - Cierre.wav", format="wav")
    
    # Remove other files if they exist
    for file in test_audio_dir.glob("*.mp3"):
        file.unlink()
    cuerpo_file = test_audio_dir / "Gran Campaña - Cuerpo.wav"
    if cuerpo_file.exists():
        cuerpo_file.unlink()
    
    file_loader = FileLoader(test_audio_dir)
    processor = LocutorProcessor(file_loader)
    result = processor.unify_locutor_audio()
    
    # Verify some files were loaded
    assert len(result.files_loaded) == 2
    assert len(result.files_skipped) == 3
    
    # Verify duration (1000 + 1500 = 2500ms)
    assert result.duration_ms == 2500
    
    # Verify correct files in metadata
    assert 'Gran Campaña - Introduccion.wav' in result.files_loaded
    assert 'Gran Campaña - Cierre.wav' in result.files_loaded
    assert 'Gran Campaña - Hora y lugar del evento.mp3' in result.files_skipped
    assert 'Gran Campaña - Cuerpo.wav' in result.files_skipped


def test_unify_locutor_audio_no_files(tmp_path):
    """Test unification when no files exist."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    file_loader = FileLoader(empty_dir)
    processor = LocutorProcessor(file_loader)
    result = processor.unify_locutor_audio()
    
    # Should return empty result
    assert len(result.files_loaded) == 0
    assert len(result.files_skipped) == 5
    assert result.duration_ms == 0


def test_concatenation_order_preservation(test_audio_dir):
    """Test that files are concatenated in the correct order."""
    # Create files with distinct characteristics
    # We'll use different frequencies or amplitudes to verify order
    intro = AudioSegment.silent(duration=1000)
    hora_lugar = AudioSegment.silent(duration=2000)
    cuerpo = AudioSegment.silent(duration=3000)
    cierre = AudioSegment.silent(duration=1500)
    
    intro.export(test_audio_dir / "Gran Campaña - Introduccion.wav", format="wav")
    hora_lugar.export(test_audio_dir / "Gran Campaña - Hora y lugar del evento.mp3", format="mp3")
    cuerpo.export(test_audio_dir / "Gran Campaña - Cuerpo.wav", format="wav")
    cierre.export(test_audio_dir / "Gran Campaña - Cierre.wav", format="wav")
    
    file_loader = FileLoader(test_audio_dir)
    processor = LocutorProcessor(file_loader)
    result = processor.unify_locutor_audio()
    
    # Verify order by checking files_loaded list
    expected_order = [
        'Gran Campaña - Introduccion.wav',
        'Gran Campaña - Hora y lugar del evento.mp3',
        'Gran Campaña - Cuerpo.wav',
        'Gran Campaña - Hora y lugar del evento.mp3',
        'Gran Campaña - Cierre.wav'
    ]
    assert result.files_loaded == expected_order


def test_duration_calculation(test_audio_dir):
    """Test that total duration equals sum of individual durations."""
    # Create files with known durations
    durations = [1000, 2000, 3000, 1500]  # milliseconds
    files = [
        "Gran Campaña - Introduccion.wav",
        "Gran Campaña - Hora y lugar del evento.mp3",
        "Gran Campaña - Cuerpo.wav",
        "Gran Campaña - Cierre.wav"
    ]
    
    for duration, filename in zip(durations, files):
        audio = AudioSegment.silent(duration=duration)
        format_type = "mp3" if filename.endswith(".mp3") else "wav"
        audio.export(test_audio_dir / filename, format=format_type)
    
    file_loader = FileLoader(test_audio_dir)
    processor = LocutorProcessor(file_loader)
    result = processor.unify_locutor_audio()
    
    # Expected: 1000 + 2000 + 3000 + 2000 (repeated) + 1500 = 9500
    expected_duration = 1000 + 2000 + 3000 + 2000 + 1500
    assert result.duration_ms == expected_duration


# Unit Tests for Task 4.5

def test_all_files_present(test_audio_dir):
    """
    Test con todos los archivos presentes.
    
    Validates: Requirements 2.1, 2.2
    """
    file_loader = FileLoader(test_audio_dir)
    processor = LocutorProcessor(file_loader)
    result = processor.unify_locutor_audio()
    
    # Verify all files were loaded
    assert len(result.files_loaded) == 5, "All 5 positions in sequence should be loaded"
    assert len(result.files_skipped) == 0, "No files should be skipped"
    
    # Verify correct files are in the loaded list
    assert 'Gran Campaña - Introduccion.wav' in result.files_loaded
    assert 'Gran Campaña - Hora y lugar del evento.mp3' in result.files_loaded
    assert 'Gran Campaña - Cuerpo.wav' in result.files_loaded
    assert 'Gran Campaña - Cierre.wav' in result.files_loaded
    
    # Verify duration is positive
    assert result.duration_ms > 0, "Duration should be positive when files are loaded"
    
    # Verify audio segment exists
    assert isinstance(result.audio, AudioSegment)
    assert len(result.audio) == result.duration_ms


def test_first_file_missing(tmp_path):
    """
    Test con primer archivo faltante.
    
    Validates: Requirements 2.2
    """
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    
    # Create all files EXCEPT the first one (Introduccion.wav)
    hora_lugar = AudioSegment.silent(duration=2000)
    cuerpo = AudioSegment.silent(duration=3000)
    cierre = AudioSegment.silent(duration=1500)
    
    hora_lugar.export(audio_dir / "Gran Campaña - Hora y lugar del evento.mp3", format="mp3")
    cuerpo.export(audio_dir / "Gran Campaña - Cuerpo.wav", format="wav")
    cierre.export(audio_dir / "Gran Campaña - Cierre.wav", format="wav")
    
    file_loader = FileLoader(audio_dir)
    processor = LocutorProcessor(file_loader)
    result = processor.unify_locutor_audio()
    
    # Verify first file was skipped
    assert 'Gran Campaña - Introduccion.wav' in result.files_skipped
    assert 'Gran Campaña - Introduccion.wav' not in result.files_loaded
    
    # Verify other files were loaded
    assert len(result.files_loaded) == 4, "4 files should be loaded (one repeated)"
    assert len(result.files_skipped) == 1, "1 file should be skipped"
    
    # Verify the processor continued with remaining files
    assert 'Gran Campaña - Hora y lugar del evento.mp3' in result.files_loaded
    assert 'Gran Campaña - Cuerpo.wav' in result.files_loaded
    assert 'Gran Campaña - Cierre.wav' in result.files_loaded
    
    # Verify duration (2000 + 3000 + 2000 + 1500 = 8500ms)
    # Allow tolerance for MP3 encoding
    tolerance = 80  # 20ms per file * 4 files
    assert abs(result.duration_ms - 8500) <= tolerance


def test_all_files_missing_should_return_empty_result(tmp_path):
    """
    Test con todos los archivos faltantes.
    
    According to the current implementation, when all files are missing,
    the processor returns an empty result with 0 duration rather than
    raising MissingFileError. This is consistent with the graceful handling
    of missing files (Requirement 1.3, 2.2).
    
    Note: MissingFileError is raised by AudioProcessor (the orchestrator)
    when validating that at least one locutor file exists (Requirement 10.2).
    
    Validates: Requirements 2.2, 10.2
    """
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    file_loader = FileLoader(empty_dir)
    processor = LocutorProcessor(file_loader)
    
    # Should not raise exception, but return empty result
    result = processor.unify_locutor_audio()
    
    # Verify all files were skipped
    assert len(result.files_loaded) == 0, "No files should be loaded"
    assert len(result.files_skipped) == 5, "All 5 positions should be skipped"
    
    # Verify duration is 0
    assert result.duration_ms == 0, "Duration should be 0 when no files are loaded"
    
    # Verify all expected files are in skipped list
    assert 'Gran Campaña - Introduccion.wav' in result.files_skipped
    assert 'Gran Campaña - Hora y lugar del evento.mp3' in result.files_skipped
    assert 'Gran Campaña - Cuerpo.wav' in result.files_skipped
    assert 'Gran Campaña - Cierre.wav' in result.files_skipped


def test_specific_file_order_verification(test_audio_dir):
    """
    Test verificación de orden específico de archivos.
    
    Verifies that files are concatenated in the exact order specified
    in LOCUTOR_SEQUENCE, including the repeated file.
    
    Validates: Requirements 2.1
    """
    file_loader = FileLoader(test_audio_dir)
    processor = LocutorProcessor(file_loader)
    result = processor.unify_locutor_audio()
    
    # Verify the exact order matches LOCUTOR_SEQUENCE
    expected_order = [
        'Gran Campaña - Introduccion.wav',
        'Gran Campaña - Hora y lugar del evento.mp3',
        'Gran Campaña - Cuerpo.wav',
        'Gran Campaña - Hora y lugar del evento.mp3',  # Repeated
        'Gran Campaña - Cierre.wav'
    ]
    
    assert result.files_loaded == expected_order, \
        f"Files should be loaded in exact sequence order: expected {expected_order}, got {result.files_loaded}"
    
    # Verify that the repeated file appears twice in the loaded list
    hora_lugar_count = result.files_loaded.count('Gran Campaña - Hora y lugar del evento.mp3')
    assert hora_lugar_count == 2, \
        f"'Gran Campaña - Hora y lugar del evento.mp3' should appear twice in sequence, appeared {hora_lugar_count} times"
    
    # Verify the positions of the repeated file
    first_occurrence = result.files_loaded.index('Gran Campaña - Hora y lugar del evento.mp3')
    last_occurrence = len(result.files_loaded) - 1 - result.files_loaded[::-1].index('Gran Campaña - Hora y lugar del evento.mp3')
    
    assert first_occurrence == 1, "First occurrence should be at position 1"
    assert last_occurrence == 3, "Second occurrence should be at position 3"


# Property-Based Tests


@audio_property_test()
@given(
    file_existence_pattern=file_existence_pattern(5)
)
def test_property_2_graceful_handling_of_missing_files(file_existence_pattern):
    """
    Property 2: Graceful Handling of Missing Files
    Feature: audio-gran-campana, Property 2: Graceful Handling of Missing Files
    
    For any file in the locutor sequence that does not exist, the processor 
    should skip it and continue processing with the remaining files without 
    throwing an exception.
    
    Validates: Requirements 1.3, 2.2, 10.3
    """
    import tempfile
    import shutil
    
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Obtener la secuencia de archivos de locutor
        sequence = LocutorProcessor.LOCUTOR_SEQUENCE
        
        # Crear archivos solo para las posiciones donde file_existence_pattern es True
        # Nota: algunos archivos pueden repetirse en la secuencia
        created_files_set = set()
        for i, should_exist in enumerate(file_existence_pattern):
            if should_exist:
                filename = sequence[i]
                # Solo crear el archivo si no existe ya (evitar sobrescribir)
                if filename not in created_files_set:
                    # Crear audio con duración determinística basada en posición
                    duration = 1000 + (i * 500)
                    audio = AudioSegment.silent(duration=duration)
                    
                    # Determinar formato basado en extensión
                    format_type = "mp3" if filename.endswith(".mp3") else "wav"
                    file_path = audio_dir / filename
                    audio.export(str(file_path), format=format_type)
                    created_files_set.add(filename)
        
        # Crear FileLoader y LocutorProcessor
        file_loader = FileLoader(audio_dir)
        processor = LocutorProcessor(file_loader)
        
        # Ejecutar unificación - NO debe lanzar excepciones
        result = processor.unify_locutor_audio()
        
        # Verificar que no se lanzó excepción (si llegamos aquí, pasó)
        assert result is not None, "Processor should return a result even with missing files"
        assert isinstance(result, LocutorResult), "Result should be a LocutorResult instance"
        
        # Calcular cuántos archivos se esperan cargar y omitir
        # Nota: la secuencia tiene 5 posiciones, pero algunos archivos pueden repetirse
        expected_loaded_positions = []
        expected_skipped_positions = []
        
        for i, should_exist in enumerate(file_existence_pattern):
            filename = sequence[i]
            # Un archivo se carga si existe en el filesystem
            if filename in created_files_set:
                expected_loaded_positions.append(i)
            else:
                expected_skipped_positions.append(i)
        
        expected_loaded_count = len(expected_loaded_positions)
        expected_skipped_count = len(expected_skipped_positions)
        
        assert len(result.files_loaded) == expected_loaded_count, \
            f"Should load {expected_loaded_count} files, loaded {len(result.files_loaded)}"
        assert len(result.files_skipped) == expected_skipped_count, \
            f"Should skip {expected_skipped_count} files, skipped {len(result.files_skipped)}"
        
        # Verificar que los archivos cargados son los que existen
        for filename in result.files_loaded:
            assert filename in created_files_set, \
                f"Loaded file {filename} should be in created files"
        
        # Verificar que los archivos omitidos son los que no existen
        for filename in result.files_skipped:
            assert filename not in created_files_set, \
                f"Skipped file {filename} should not be in created files"
        
        # Verificar que la duración es correcta
        if expected_loaded_count > 0:
            assert result.duration_ms > 0, \
                "Duration should be positive when files are loaded"
            assert isinstance(result.audio, AudioSegment), \
                "Audio should be an AudioSegment when files are loaded"
        else:
            # Caso especial: sin archivos cargados
            assert result.duration_ms == 0, \
                "Duration should be 0 when no files are loaded"
        
        # Verificar que el orden se preserva en files_loaded
        for i, filename in enumerate(result.files_loaded):
            expected_filename = sequence[expected_loaded_positions[i]]
            assert filename == expected_filename, \
                f"File order should be preserved: expected {expected_filename}, got {filename}"
    
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


@audio_property_test()
@given(
    file_existence_pattern=file_existence_pattern(5),
    durations=duration_list(min_count=5, max_count=5, min_duration=100, max_duration=5000)
)
def test_property_3_concatenation_order_preservation(file_existence_pattern, durations):
    """
    Property 3: Concatenation Order Preservation
    Feature: audio-gran-campana, Property 3: Concatenation Order Preservation
    
    For any set of audio files loaded in the specified locutor sequence, 
    the concatenated output should contain the audio segments in the exact 
    order specified, with each segment starting immediately after the 
    previous one ends.
    
    Validates: Requirements 2.1
    """
    import tempfile
    import shutil
    
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Obtener la secuencia completa de archivos de locutor
        sequence = LocutorProcessor.LOCUTOR_SEQUENCE
        
        # Crear archivos de audio con duraciones específicas solo para los que deben existir
        # Cada archivo tendrá una duración única para poder verificar el orden
        created_files = {}
        for i, (filename, should_exist, duration) in enumerate(zip(sequence, file_existence_pattern, durations)):
            # Solo crear el archivo si debe existir y no existe ya (algunos pueden repetirse)
            if should_exist and filename not in created_files:
                audio = AudioSegment.silent(duration=duration)
                format_type = "mp3" if filename.endswith(".mp3") else "wav"
                file_path = audio_dir / filename
                audio.export(str(file_path), format=format_type)
                created_files[filename] = duration
        
        # Si no hay archivos creados, saltar el test (caso trivial)
        if not created_files:
            return
        
        # Crear FileLoader y LocutorProcessor
        file_loader = FileLoader(audio_dir)
        processor = LocutorProcessor(file_loader)
        
        # Ejecutar unificación
        result = processor.unify_locutor_audio()
        
        # Verificar que el resultado existe
        assert result is not None, "Processor should return a result"
        assert isinstance(result, LocutorResult), "Result should be a LocutorResult instance"
        
        # Verificar que el orden de files_loaded coincide con la secuencia
        # Los archivos deben aparecer en el mismo orden que en la secuencia
        expected_loaded = []
        for filename in sequence:
            if filename in created_files:
                expected_loaded.append(filename)
        
        assert result.files_loaded == expected_loaded, \
            f"Order should be preserved: expected {expected_loaded}, got {result.files_loaded}"
        
        # Verificar que la duración total es la suma de las duraciones individuales
        # Nota: si un archivo aparece múltiples veces en la secuencia, su duración
        # se cuenta cada vez que aparece
        expected_duration = 0
        for filename in sequence:
            if filename in created_files:
                expected_duration += created_files[filename]
        
        # Allow tolerance for MP3 encoding artifacts (±20ms per file)
        # MP3 compression can introduce small duration variations
        tolerance = 20 * len(result.files_loaded)
        assert abs(result.duration_ms - expected_duration) <= tolerance, \
            f"Total duration should equal sum of individual durations (±{tolerance}ms tolerance): expected {expected_duration}, got {result.duration_ms}"
        
        # Verificar que el audio resultante tiene la duración correcta
        if len(result.files_loaded) > 0:
            actual_audio_duration = len(result.audio)  # pydub AudioSegment length in ms
            # Allow small tolerance for audio processing (±10ms)
            assert abs(actual_audio_duration - expected_duration) <= 10, \
                f"Audio duration should match expected: expected {expected_duration}, got {actual_audio_duration}"
        
        # Verificar que cada segmento comienza inmediatamente después del anterior
        # Esto se verifica implícitamente por la duración total, pero también
        # podemos verificar que no hay gaps o overlaps
        if len(result.files_loaded) > 1:
            # La duración total debe ser exactamente la suma (sin gaps ni overlaps)
            # Allow tolerance for MP3 encoding artifacts
            cumulative_duration = 0
            for filename in sequence:
                if filename in created_files:
                    cumulative_duration += created_files[filename]
            
            tolerance = 20 * len(result.files_loaded)
            assert abs(result.duration_ms - cumulative_duration) <= tolerance, \
                "Segments should be concatenated without gaps or overlaps (within MP3 encoding tolerance)"
    
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


@audio_property_test()
@given(
    durations=duration_list(min_count=1, max_count=5, min_duration=100, max_duration=5000)
)
def test_property_4_duration_summation_in_concatenation(durations):
    """
    Property 4: Duration Summation in Concatenation
    Feature: audio-gran-campana, Property 4: Duration Summation in Concatenation
    
    For any set of audio segments concatenated together, the total duration 
    of the unified audio should equal the sum of the individual segment durations.
    
    Validates: Requirements 2.5
    """
    import tempfile
    import shutil
    
    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()
    
    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()
        
        # Obtener la secuencia de archivos de locutor
        sequence = LocutorProcessor.LOCUTOR_SEQUENCE
        
        # Crear archivos de audio con las duraciones generadas aleatoriamente
        # Usaremos solo los primeros N archivos de la secuencia según la cantidad de duraciones
        created_files = {}
        for i, duration in enumerate(durations):
            if i >= len(sequence):
                break
            
            filename = sequence[i]
            
            # Solo crear el archivo si no existe ya (algunos pueden repetirse en la secuencia)
            if filename not in created_files:
                audio = AudioSegment.silent(duration=duration)
                format_type = "mp3" if filename.endswith(".mp3") else "wav"
                file_path = audio_dir / filename
                audio.export(str(file_path), format=format_type)
                created_files[filename] = duration
        
        # Crear FileLoader y LocutorProcessor
        file_loader = FileLoader(audio_dir)
        processor = LocutorProcessor(file_loader)
        
        # Ejecutar unificación
        result = processor.unify_locutor_audio()
        
        # Verificar que el resultado existe
        assert result is not None, "Processor should return a result"
        assert isinstance(result, LocutorResult), "Result should be a LocutorResult instance"
        
        # Calcular la duración esperada sumando las duraciones individuales
        # Nota: si un archivo aparece múltiples veces en la secuencia, 
        # su duración se cuenta cada vez que aparece
        expected_duration = 0
        for filename in result.files_loaded:
            if filename in created_files:
                expected_duration += created_files[filename]
        
        # Verificar que la duración total reportada coincide con la suma esperada
        # Allow tolerance for MP3 encoding artifacts (±20ms per file)
        # MP3 compression can introduce small duration variations due to frame padding
        tolerance = 20 * len(result.files_loaded)
        assert abs(result.duration_ms - expected_duration) <= tolerance, \
            f"Total duration should equal sum of individual durations (±{tolerance}ms tolerance for MP3 encoding): expected {expected_duration}ms, got {result.duration_ms}ms"
        
        # Verificar que el audio resultante también tiene la duración correcta
        if len(result.files_loaded) > 0:
            actual_audio_duration = len(result.audio)  # pydub AudioSegment length in ms
            # Allow tolerance for audio processing artifacts
            assert abs(actual_audio_duration - expected_duration) <= tolerance, \
                f"Audio segment duration should match expected (±{tolerance}ms tolerance): expected {expected_duration}ms, got {actual_audio_duration}ms"
        
        # Verificar que la duración reportada en el resultado coincide con la duración del audio
        assert abs(result.duration_ms - len(result.audio)) <= 1, \
            f"Reported duration should match audio segment duration: reported {result.duration_ms}ms, audio {len(result.audio)}ms"
        
        # Verificar que no hay gaps ni overlaps en la concatenación
        # La duración total debe ser exactamente la suma de las partes (dentro de la tolerancia)
        cumulative_duration = sum(created_files[filename] for filename in result.files_loaded if filename in created_files)
        assert abs(result.duration_ms - cumulative_duration) <= tolerance, \
            f"Concatenation should not introduce gaps or overlaps (±{tolerance}ms tolerance): expected {cumulative_duration}ms, got {result.duration_ms}ms"
    
    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)



@audio_property_test()
@given(
    num_segments=st.integers(min_value=1, max_value=5),
    sample_rates=st.lists(
        st.sampled_from([8000, 16000, 22050, 44100, 48000]),
        min_size=1,
        max_size=5
    ),
    channels=st.lists(
        st.sampled_from([1, 2]),  # 1=mono, 2=stereo
        min_size=1,
        max_size=5
    ),
    sample_widths=st.lists(
        st.sampled_from([1, 2, 4]),  # 1=8bit, 2=16bit, 4=32bit
        min_size=1,
        max_size=5
    )
)
def test_property_5_audio_quality_preservation_in_concatenation(num_segments, sample_rates, channels, sample_widths):
    """
    Property 5: Audio Quality Preservation in Concatenation
    Feature: audio-gran-campana, Property 5: Audio Quality Preservation in Concatenation

    For any set of audio segments concatenated together, the output should
    preserve the sample rate and bit depth of the input segments.

    Validates: Requirements 2.4
    """
    import tempfile
    import shutil

    # Crear directorio temporal para audio
    temp_dir = tempfile.mkdtemp()

    try:
        audio_dir = Path(temp_dir) / "audio"
        audio_dir.mkdir()

        # Obtener la secuencia de archivos de locutor
        sequence = LocutorProcessor.LOCUTOR_SEQUENCE

        # Limitar el número de segmentos a la longitud de la secuencia
        num_segments = min(num_segments, len(sequence))

        # Crear archivos de audio con diferentes propiedades de calidad
        created_files = {}
        file_properties = {}

        for i in range(num_segments):
            filename = sequence[i]

            # Solo crear el archivo si no existe ya (algunos pueden repetirse en la secuencia)
            if filename not in created_files:
                # Obtener propiedades de audio para este archivo
                sample_rate = sample_rates[i % len(sample_rates)]
                channel_count = channels[i % len(channels)]
                sample_width = sample_widths[i % len(sample_widths)]

                # Crear audio silencioso con propiedades específicas
                duration = 1000  # 1 segundo
                audio = AudioSegment.silent(
                    duration=duration,
                    frame_rate=sample_rate
                )

                # Configurar canales y sample width
                audio = audio.set_channels(channel_count)
                audio = audio.set_sample_width(sample_width)

                # Exportar archivo
                format_type = "mp3" if filename.endswith(".mp3") else "wav"
                file_path = audio_dir / filename

                # Nota: MP3 puede cambiar las propiedades de audio durante la codificación
                # WAV preserva las propiedades exactas
                audio.export(str(file_path), format=format_type)

                created_files[filename] = audio
                file_properties[filename] = {
                    'sample_rate': sample_rate,
                    'channels': channel_count,
                    'sample_width': sample_width,
                    'format': format_type
                }

        # Si no hay archivos creados, saltar el test (caso trivial)
        if not created_files:
            return

        # Crear FileLoader y LocutorProcessor
        file_loader = FileLoader(audio_dir)
        processor = LocutorProcessor(file_loader)

        # Ejecutar unificación
        result = processor.unify_locutor_audio()

        # Verificar que el resultado existe
        assert result is not None, "Processor should return a result"
        assert isinstance(result, LocutorResult), "Result should be a LocutorResult instance"
        assert len(result.files_loaded) > 0, "At least one file should be loaded"

        # Verificar que el audio resultante tiene propiedades de calidad válidas
        unified_audio = result.audio
        assert isinstance(unified_audio, AudioSegment), "Result should contain an AudioSegment"

        # Obtener propiedades del audio unificado
        unified_sample_rate = unified_audio.frame_rate
        unified_channels = unified_audio.channels
        unified_sample_width = unified_audio.sample_width

        # Verificar que las propiedades de audio son válidas (no nulas o cero)
        assert unified_sample_rate > 0, f"Sample rate should be positive: {unified_sample_rate}"
        assert unified_channels > 0, f"Channels should be positive: {unified_channels}"
        assert unified_sample_width > 0, f"Sample width should be positive: {unified_sample_width}"

        # Verificar que las propiedades están dentro de rangos válidos
        assert unified_sample_rate in [8000, 11025, 16000, 22050, 44100, 48000, 96000], \
            f"Sample rate should be a standard value: {unified_sample_rate}"
        assert unified_channels in [1, 2], \
            f"Channels should be 1 (mono) or 2 (stereo): {unified_channels}"
        assert unified_sample_width in [1, 2, 4], \
            f"Sample width should be 1, 2, or 4 bytes: {unified_sample_width}"

        # Verificar que las propiedades se preservan de los archivos de entrada
        # pydub normaliza las propiedades cuando concatena archivos con diferentes características
        # El audio resultante debe tener propiedades consistentes con al menos uno de los archivos de entrada

        # Recopilar todas las propiedades únicas de los archivos cargados
        input_sample_rates = set()
        input_channels = set()
        input_sample_widths = set()

        for filename in result.files_loaded:
            if filename in file_properties:
                props = file_properties[filename]
                input_sample_rates.add(props['sample_rate'])
                input_channels.add(props['channels'])
                input_sample_widths.add(props['sample_width'])

        # Si todos los archivos de entrada tienen las mismas propiedades, el output debe preservarlas
        # (excepto para MP3 que puede normalizar)
        has_mp3 = any(file_properties[f]['format'] == 'mp3' for f in result.files_loaded if f in file_properties)

        if len(input_sample_rates) == 1 and not has_mp3:
            # Todos los archivos WAV tienen el mismo sample rate
            expected_sample_rate = list(input_sample_rates)[0]
            assert unified_sample_rate == expected_sample_rate, \
                f"Sample rate should be preserved when all inputs match: expected {expected_sample_rate}, got {unified_sample_rate}"

        if len(input_channels) == 1 and not has_mp3:
            # Todos los archivos WAV tienen el mismo número de canales
            expected_channels = list(input_channels)[0]
            assert unified_channels == expected_channels, \
                f"Channels should be preserved when all inputs match: expected {expected_channels}, got {unified_channels}"

        if len(input_sample_widths) == 1 and not has_mp3:
            # Todos los archivos WAV tienen el mismo sample width
            expected_sample_width = list(input_sample_widths)[0]
            assert unified_sample_width == expected_sample_width, \
                f"Sample width should be preserved when all inputs match: expected {expected_sample_width}, got {unified_sample_width}"

        # Verificar que el audio no está corrupto (tiene datos)
        assert len(unified_audio) > 0, "Unified audio should have non-zero duration"
        assert unified_audio.raw_data is not None, "Unified audio should have raw data"
        assert len(unified_audio.raw_data) > 0, "Unified audio raw data should not be empty"

        # Verificar que la duración es razonable (al menos la duración de un segmento)
        min_expected_duration = 100  # Al menos 100ms
        assert len(unified_audio) >= min_expected_duration, \
            f"Unified audio duration should be at least {min_expected_duration}ms: got {len(unified_audio)}ms"

    finally:
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True)

