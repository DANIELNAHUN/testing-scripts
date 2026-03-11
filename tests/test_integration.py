"""
Integration tests for Audio Gran Campaña end-to-end processing.

These tests verify the complete pipeline functionality using real audio files
and test various scenarios including missing files, different combinations,
and output verification.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from src.audio_processor import AudioProcessor
from src.exceptions import MissingFileError, AudioProcessingError
from src.models import ProcessingResult
from pydub import AudioSegment


class TestIntegrationEndToEnd:
    """End-to-end integration tests for the complete audio processing pipeline."""
    
    @pytest.fixture
    def fixtures_dir(self):
        """Get the path to test fixtures directory."""
        return Path(__file__).parent / 'fixtures' / 'audio'
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_input_dir(self):
        """Create a temporary input directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def copy_test_files(self, source_dir: Path, dest_dir: Path, files: list):
        """Copy specific test files to destination directory."""
        for filename in files:
            source_file = source_dir / filename
            if source_file.exists():
                shutil.copy2(source_file, dest_dir / filename)
    
    def test_complete_pipeline_all_files_present(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test complete pipeline with all required files present."""
        # Copy all required files
        required_files = [
            'Gran Campaña - Introduccion.wav',
            'Gran Campaña - Hora y lugar del evento.mp3',
            'Gran Campaña - Cuerpo.wav',
            'Gran Campaña - Cierre.wav',
            'Yo tengo un amigo que me ama.mp3',
            'Eres todo poderoso.mp3'
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, required_files)
        
        # Run processing
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        # Verify success
        assert result.success is True
        assert result.error_message is None
        assert result.output_path is not None
        assert result.output_path.exists()
        
        # Verify output file properties
        output_audio = AudioSegment.from_mp3(result.output_path)
        assert len(output_audio) > 0  # Has duration
        assert output_audio.frame_rate >= 22050  # Reasonable sample rate
        assert output_audio.channels in [1, 2]  # Mono or stereo
        
        # Verify processing results
        assert result.locutor_result is not None
        assert len(result.locutor_result.files_loaded) >= 1
        assert result.background_result is not None
        assert result.background_result.crossfade_applied is True
        
        # Verify final duration is reasonable (should be > 30 seconds for our test files)
        assert result.final_duration_ms > 30000
        
        # Verify output file format and quality
        # MP3 files should have reasonable bitrate
        assert result.output_path.suffix == '.mp3'
    
    def test_pipeline_with_missing_locutor_files(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test pipeline with some locutor files missing."""
        # Copy only some locutor files and all background files
        files_to_copy = [
            'Gran Campaña - Introduccion.wav',  # Present
            'Gran Campaña - Cuerpo.wav',        # Present
            # Skip 'Gran Campaña - Hora y lugar del evento.mp3' and 'Gran Campaña - Cierre.wav'
            'Yo tengo un amigo que me ama.mp3',
            'Eres todo poderoso.mp3'
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, files_to_copy)
        
        # Run processing
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        # Should succeed with partial files
        assert result.success is True
        assert result.output_path is not None
        assert result.output_path.exists()
        
        # Verify some files were loaded and some were skipped
        assert result.locutor_result is not None
        assert len(result.locutor_result.files_loaded) == 2  # Only 2 files present
        assert len(result.locutor_result.files_skipped) == 3  # 3 files missing (including duplicate)
        
        # Output should still be valid
        output_audio = AudioSegment.from_mp3(result.output_path)
        assert len(output_audio) > 0
    
    def test_pipeline_with_missing_background_files(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test pipeline failure when required background files are missing."""
        # Copy only locutor files, skip background files
        locutor_files = [
            'Gran Campaña - Introduccion.wav',
            'Gran Campaña - Hora y lugar del evento.mp3',
            'Gran Campaña - Cuerpo.wav',
            'Gran Campaña - Cierre.wav'
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, locutor_files)
        
        # Run processing - should fail
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        # Should fail due to missing background files
        assert result.success is False
        assert result.error_message is not None
        assert "missing" in result.error_message.lower()
        assert result.output_path is None
    
    def test_pipeline_with_all_locutor_files_missing(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test pipeline failure when all locutor files are missing."""
        # Copy only background files
        background_files = [
            'Yo tengo un amigo que me ama.mp3',
            'Eres todo poderoso.mp3'
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, background_files)
        
        # Run processing - should fail
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        # Should fail due to no locutor files
        assert result.success is False
        assert result.error_message is not None
        assert "locutor" in result.error_message.lower()
        assert result.output_path is None
    
    def test_pipeline_with_minimal_files(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test pipeline with minimum viable files (one locutor + both backgrounds)."""
        # Copy minimal required files
        minimal_files = [
            'Gran Campaña - Introduccion.wav',  # Only one locutor file
            'Yo tengo un amigo que me ama.mp3',
            'Eres todo poderoso.mp3'
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, minimal_files)
        
        # Run processing
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        # Should succeed with minimal files
        assert result.success is True
        assert result.output_path is not None
        assert result.output_path.exists()
        
        # Verify processing results
        assert result.locutor_result is not None
        assert len(result.locutor_result.files_loaded) == 1
        assert len(result.locutor_result.files_skipped) == 4  # 4 files in sequence were missing
        
        # Output should be valid
        output_audio = AudioSegment.from_mp3(result.output_path)
        assert len(output_audio) > 0
    
    def test_pipeline_with_different_audio_formats(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test pipeline with mixed audio formats (WAV and MP3)."""
        # Copy files with different formats
        mixed_format_files = [
            'Gran Campaña - Introduccion.wav',      # WAV
            'Gran Campaña - Hora y lugar del evento.mp3',  # MP3
            'different_format.wav',                 # Additional WAV (will be ignored in sequence)
            'Yo tengo un amigo que me ama.mp3',
            'Eres todo poderoso.mp3'
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, mixed_format_files)
        
        # Run processing
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        # Should succeed with mixed formats
        assert result.success is True
        assert result.output_path is not None
        assert result.output_path.exists()
        
        # Verify output quality
        output_audio = AudioSegment.from_mp3(result.output_path)
        assert len(output_audio) > 0
        assert output_audio.frame_rate >= 22050
    
    def test_pipeline_with_edge_case_durations(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test pipeline with edge case file durations."""
        # Copy edge case files - use a file from the actual locutor sequence
        edge_case_files = [
            'Gran Campaña - Introduccion.wav',  # Use a real locutor file from sequence
            'long_background.mp3',              # Very long background (will be used as second background)
            'Yo tengo un amigo que me ama.mp3'  # Normal first background
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, edge_case_files)
        
        # Rename long_background.mp3 to the expected second background name
        (temp_input_dir / 'long_background.mp3').rename(
            temp_input_dir / 'Eres todo poderoso.mp3'
        )
        
        # Run processing
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        # Should succeed even with edge case durations
        assert result.success is True
        assert result.output_path is not None
        assert result.output_path.exists()
        
        # Verify the locutor was processed
        assert result.locutor_result is not None
        assert result.locutor_result.duration_ms > 0
        assert len(result.locutor_result.files_loaded) >= 1
    
    def test_output_file_format_and_quality(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test that output file has correct format and quality specifications."""
        # Copy required files
        required_files = [
            'Gran Campaña - Introduccion.wav',
            'Yo tengo un amigo que me ama.mp3',
            'Eres todo poderoso.mp3'
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, required_files)
        
        # Run processing
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        assert result.success is True
        assert result.output_path is not None
        
        # Load and verify output file properties
        output_audio = AudioSegment.from_mp3(result.output_path)
        
        # Verify format
        assert result.output_path.suffix == '.mp3'
        
        # Verify quality properties
        assert output_audio.frame_rate >= 22050  # Reasonable sample rate
        assert output_audio.sample_width >= 2    # At least 16-bit
        assert output_audio.channels in [1, 2]   # Mono or stereo
        
        # Verify file size is reasonable (not too small, indicating quality loss)
        file_size = result.output_path.stat().st_size
        assert file_size > 10000  # At least 10KB for a reasonable audio file
        
        # Verify duration matches expected result
        expected_min_duration = 10000  # At least 10 seconds for our test setup
        assert len(output_audio) >= expected_min_duration
    
    def test_validation_warnings_logged(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test that validation warnings are properly captured and reported."""
        # Use files that might cause validation warnings
        # (e.g., very short files that might not meet duration expectations)
        files_with_potential_warnings = [
            'short_locutor.wav',
            'short_background.mp3',  # Will be renamed to first background
            'Eres todo poderoso.mp3'
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, files_with_potential_warnings)
        
        # Rename short_background to expected first background name
        (temp_input_dir / 'short_background.mp3').rename(
            temp_input_dir / 'Yo tengo un amigo que me ama.mp3'
        )
        
        # Run processing
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        # Processing might succeed but with warnings
        if result.success:
            # Check if validation warnings were captured
            # (This depends on the specific duration relationships of our test files)
            assert isinstance(result.validation_warnings, list)
        else:
            # If it fails, it should be due to duration issues, not file loading
            assert result.error_message is not None
    
    def test_error_handling_with_corrupted_files(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test error handling when encountering corrupted audio files."""
        # Copy some good files and some corrupted files
        files_to_copy = [
            'Gran Campaña - Introduccion.wav',  # Good file
            'corrupted.mp3',                    # Corrupted file
            'empty.wav',                        # Empty file
            'Yo tengo un amigo que me ama.mp3',
            'Eres todo poderoso.mp3'
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, files_to_copy)
        
        # Run processing
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        # Should handle corrupted files gracefully
        # The system should either succeed (if it can skip corrupted files)
        # or fail with a clear error message
        if not result.success:
            assert result.error_message is not None
            # Error message should be informative
            assert len(result.error_message) > 10
        else:
            # If it succeeds, it should have loaded at least some files
            assert result.locutor_result is not None
            assert len(result.locutor_result.files_loaded) >= 1
    
    def test_processing_result_completeness(self, fixtures_dir, temp_input_dir, temp_output_dir):
        """Test that ProcessingResult contains complete and accurate metadata."""
        # Copy required files
        required_files = [
            'Gran Campaña - Introduccion.wav',
            'Gran Campaña - Cuerpo.wav',
            'Yo tengo un amigo que me ama.mp3',
            'Eres todo poderoso.mp3'
        ]
        
        self.copy_test_files(fixtures_dir, temp_input_dir, required_files)
        
        # Run processing
        processor = AudioProcessor(temp_input_dir, temp_output_dir)
        result = processor.process()
        
        assert result.success is True
        
        # Verify all required fields are present and valid
        assert result.output_path is not None
        assert result.final_duration_ms > 0
        assert result.locutor_result is not None
        assert result.background_result is not None
        assert result.error_message is None
        assert isinstance(result.validation_warnings, list)
        
        # Verify locutor result completeness
        locutor = result.locutor_result
        assert locutor.audio is not None
        assert locutor.duration_ms > 0
        assert isinstance(locutor.files_loaded, list)
        assert isinstance(locutor.files_skipped, list)
        assert len(locutor.files_loaded) >= 1
        
        # Verify background result completeness
        background = result.background_result
        assert background.audio is not None
        assert background.duration_ms > 0
        assert background.first_bg_duration_ms > 0
        assert background.second_bg_duration_ms > 0
        assert isinstance(background.crossfade_applied, bool)
        
        # Verify duration consistency - the final audio should be the background duration
        # since the background is longer and contains the overlaid locutor
        assert result.final_duration_ms == result.background_result.duration_ms


class TestIntegrationErrorScenarios:
    """Integration tests for error scenarios and edge cases."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary input and output directories."""
        input_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()
        yield Path(input_dir), Path(output_dir)
        shutil.rmtree(input_dir)
        shutil.rmtree(output_dir)
    
    def test_nonexistent_input_directory(self):
        """Test error handling when input directory doesn't exist."""
        nonexistent_input = Path("/nonexistent/path")
        temp_output = Path(tempfile.mkdtemp())
        
        try:
            # Should not raise exception during initialization
            processor = AudioProcessor(nonexistent_input, temp_output)
            
            # Should fail during processing
            result = processor.process()
            assert result.success is False
            assert result.error_message is not None
        finally:
            shutil.rmtree(temp_output)
    
    def test_readonly_output_directory(self, temp_dirs):
        """Test error handling when output directory is read-only."""
        input_dir, output_dir = temp_dirs
        
        # Create a basic input file
        test_file = input_dir / "test.wav"
        AudioSegment.silent(duration=1000).export(test_file, format="wav")
        
        # Make output directory read-only
        output_dir.chmod(0o444)
        
        try:
            processor = AudioProcessor(input_dir, output_dir)
            result = processor.process()
            
            # Should fail due to permission issues
            assert result.success is False
            assert result.error_message is not None
        finally:
            # Restore permissions for cleanup
            output_dir.chmod(0o755)
    
    def test_empty_input_directory(self, temp_dirs):
        """Test processing with completely empty input directory."""
        input_dir, output_dir = temp_dirs
        
        processor = AudioProcessor(input_dir, output_dir)
        result = processor.process()
        
        # Should fail due to missing required files
        assert result.success is False
        assert result.error_message is not None
        assert "missing" in result.error_message.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])