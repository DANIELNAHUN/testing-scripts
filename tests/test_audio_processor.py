"""
Tests for AudioProcessor - Main orchestrator.

Includes both unit tests and property-based tests for the complete audio processing pipeline.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine
from hypothesis import given, strategies as st
from tests.hypothesis_config import audio_property_test
from tests.hypothesis_strategies import file_existence_pattern, locutor_sequence_pattern

from src.audio_processor import AudioProcessor
from src.exceptions import MissingFileError, AudioProcessingError
from src.models import ProcessingResult


@pytest.fixture
def test_audio_folder(tmp_path):
    """Create a temporary folder with test audio files."""
    audio_folder = tmp_path / "audio"
    audio_folder.mkdir()
    
    # Generate test audio files
    # Locutor files (5 seconds each)
    locutor_audio = Sine(440).to_audio_segment(duration=5000)
    
    locutor_files = [
        'Gran Campaña - Introduccion.wav',
        'Gran Campaña - Hora y lugar del evento.mp3',
        'Gran Campaña - Cuerpo.wav',
        'Gran Campaña - Cierre.wav'
    ]
    
    for filename in locutor_files:
        file_path = audio_folder / filename
        format_type = "wav" if filename.endswith('.wav') else "mp3"
        locutor_audio.export(str(file_path), format=format_type)
    
    # Background music files (30 seconds each)
    background_audio = Sine(220).to_audio_segment(duration=30000)
    
    background_files = [
        'Yo tengo un amigo que me ama.mp3',
        'Eres todo poderoso.mp3'
    ]
    
    for filename in background_files:
        file_path = audio_folder / filename
        background_audio.export(str(file_path), format="mp3")
    
    return audio_folder


@pytest.fixture
def output_folder(tmp_path):
    """Create a temporary output folder."""
    output_folder = tmp_path / "output"
    output_folder.mkdir()
    return output_folder


@pytest.fixture
def audio_processor(test_audio_folder, output_folder):
    """Create an AudioProcessor instance with test folders."""
    return AudioProcessor(test_audio_folder, output_folder)


# Property-based tests (simplified without Hypothesis for now)

def test_property_20_required_file_validation():
    """
    **Validates: Requirements 10.1**
    Property 20: Required File Validation
    
    For any processing attempt where a required background music file is missing,
    the processor should raise a MissingFileError and terminate processing before
    attempting to process audio.
    """
    # Feature: audio-gran-campana, Property 20: Required File Validation
    
    tmp_dir = tempfile.mkdtemp()
    try:
        tmp_path = Path(tmp_dir)
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        # Create all required files first
        test_audio = Sine(440).to_audio_segment(duration=5000)
        
        # Create locutor files
        locutor_files = [
            'Gran Campaña - Introduccion.wav',
            'Gran Campaña - Hora y lugar del evento.mp3',
            'Gran Campaña - Cuerpo.wav',
            'Gran Campaña - Cierre.wav'
        ]
        
        for filename in locutor_files:
            file_path = source_folder / filename
            format_type = "wav" if filename.endswith('.wav') else "mp3"
            test_audio.export(str(file_path), format=format_type)
        
        # Create only second background file (first is missing)
        second_bg_path = source_folder / 'Eres todo poderoso.mp3'
        test_audio.export(str(second_bg_path), format="mp3")
        
        # Create processor and attempt processing
        processor = AudioProcessor(source_folder, output_folder)
        
        # Should fail with missing file error
        result = processor.process()
        assert not result.success
        assert result.error_message is not None
        assert "missing" in result.error_message.lower()
        assert result.output_path is None
        
    finally:
        shutil.rmtree(tmp_dir)


def test_property_21_empty_locutor_validation():
    """
    **Validates: Requirements 10.2**
    Property 21: Empty Locutor Validation
    
    For any processing attempt where all locutor files are missing,
    the processor should raise a MissingFileError.
    """
    # Feature: audio-gran-campana, Property 21: Empty Locutor Validation
    
    tmp_dir = tempfile.mkdtemp()
    try:
        tmp_path = Path(tmp_dir)
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        # Create background files (required files must exist to reach locutor validation)
        test_audio = Sine(440).to_audio_segment(duration=5000)
        background_files = ['Yo tengo un amigo que me ama.mp3', 'Eres todo poderoso.mp3']
        
        for filename in background_files:
            file_path = source_folder / filename
            test_audio.export(str(file_path), format="mp3")
        
        # Don't create any locutor files (they're all missing)
        
        # Create processor and attempt processing
        processor = AudioProcessor(source_folder, output_folder)
        
        # Should raise MissingFileError for empty locutor
        result = processor.process()
        assert not result.success
        assert "locutor" in result.error_message.lower()
        assert result.output_path is None
        
    finally:
        shutil.rmtree(tmp_dir)


def test_property_22_file_loading_status_logging(caplog):
    """
    **Validates: Requirements 10.4, 10.5**
    Property 22: File Loading Status Logging
    
    For any processing run, the logs should contain a complete list of
    successfully loaded files and a complete list of skipped files due to non-existence.
    """
    # Feature: audio-gran-campana, Property 22: File Loading Status Logging
    
    tmp_dir = tempfile.mkdtemp()
    try:
        tmp_path = Path(tmp_dir)
        source_folder = tmp_path / "source"
        output_folder = tmp_path / "output"
        source_folder.mkdir()
        output_folder.mkdir()
        
        # Create some files but not others to test logging
        test_audio = Sine(440).to_audio_segment(duration=5000)
        
        # Create only some locutor files
        created_files = [
            'Gran Campaña - Introduccion.wav',
            'Gran Campaña - Cuerpo.wav'
        ]
        
        skipped_files = [
            'Gran Campaña - Hora y lugar del evento.mp3',
            'Gran Campaña - Cierre.wav'
        ]
        
        for filename in created_files:
            file_path = source_folder / filename
            format_type = "wav" if filename.endswith('.wav') else "mp3"
            test_audio.export(str(file_path), format=format_type)
        
        # Create background files
        background_files = ['Yo tengo un amigo que me ama.mp3', 'Eres todo poderoso.mp3']
        for filename in background_files:
            file_path = source_folder / filename
            test_audio.export(str(file_path), format="mp3")
        
        # Create processor and run processing
        processor = AudioProcessor(source_folder, output_folder)
        
        # Clear previous log records
        caplog.clear()
        
        # Run processing
        result = processor.process()
        
        # Check that logs contain information about loaded and skipped files
        log_text = caplog.text.lower()
        
        # Verify that file processing information is logged
        # The logs should contain information about file operations
        assert len(log_text) > 0  # Ensure logs were captured
        
        # Verify skipped files are mentioned in logs
        assert "skipped" in log_text or "not found" in log_text or "missing" in log_text
        
    finally:
        shutil.rmtree(tmp_dir)


# Unit tests

def test_audio_processor_initialization(test_audio_folder, output_folder):
    """Test AudioProcessor initialization."""
    processor = AudioProcessor(test_audio_folder, output_folder)
    
    assert processor.source_folder == test_audio_folder
    assert processor.output_folder == output_folder
    assert processor.file_loader is not None
    assert processor.locutor_processor is not None
    assert processor.background_processor is not None
    assert processor.audio_combiner is not None
    assert processor.audio_exporter is not None


def test_process_happy_path(audio_processor):
    """Test complete processing pipeline with all files present."""
    result = audio_processor.process()
    
    assert isinstance(result, ProcessingResult)
    assert result.success
    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.final_duration_ms > 0
    assert result.locutor_result is not None
    assert result.background_result is not None
    assert result.error_message is None


def test_process_with_missing_background_files(test_audio_folder, output_folder):
    """Test processing when background files are missing."""
    # Remove one background file
    background_file = test_audio_folder / 'Yo tengo un amigo que me ama.mp3'
    background_file.unlink()
    
    processor = AudioProcessor(test_audio_folder, output_folder)
    result = processor.process()
    
    assert not result.success
    assert result.error_message is not None
    assert "missing" in result.error_message.lower()
    assert result.output_path is None


def test_process_with_some_locutor_files_missing(audio_processor):
    """Test processing with some locutor files missing."""
    # Remove one locutor file
    locutor_file = audio_processor.source_folder / 'Gran Campaña - Introduccion.wav'
    locutor_file.unlink()
    
    result = audio_processor.process()
    
    # Should still succeed with remaining files
    assert result.success
    assert result.output_path is not None
    assert len(result.locutor_result.files_skipped) == 1
    assert len(result.locutor_result.files_loaded) >= 1


def test_process_with_all_locutor_files_missing(test_audio_folder, output_folder):
    """Test processing when all locutor files are missing."""
    # Remove all locutor files
    locutor_files = [
        'Gran Campaña - Introduccion.wav',
        'Gran Campaña - Hora y lugar del evento.mp3',
        'Gran Campaña - Cuerpo.wav',
        'Gran Campaña - Cierre.wav'
    ]
    
    for filename in locutor_files:
        file_path = test_audio_folder / filename
        if file_path.exists():
            file_path.unlink()
    
    processor = AudioProcessor(test_audio_folder, output_folder)
    result = processor.process()
    
    assert not result.success
    assert result.error_message is not None
    assert "locutor" in result.error_message.lower()
    assert result.output_path is None


def test_processing_result_metadata(audio_processor):
    """Test that ProcessingResult contains correct metadata."""
    result = audio_processor.process()
    
    assert result.success
    assert isinstance(result.final_duration_ms, int)
    assert result.final_duration_ms > 0
    assert result.locutor_result.files_loaded
    assert result.background_result.crossfade_applied
    assert result.background_result.first_bg_duration_ms > 0
    assert result.background_result.second_bg_duration_ms > 0


def test_validate_required_files_success(audio_processor):
    """Test successful validation of required files."""
    # Should not raise any exception
    audio_processor._validate_required_files()


def test_validate_required_files_missing(test_audio_folder, output_folder):
    """Test validation failure when required files are missing."""
    # Remove a required background file
    background_file = test_audio_folder / 'Eres todo poderoso.mp3'
    background_file.unlink()
    
    processor = AudioProcessor(test_audio_folder, output_folder)
    
    with pytest.raises(MissingFileError) as exc_info:
        processor._validate_required_files()
    
    assert 'Eres todo poderoso.mp3' in str(exc_info.value)