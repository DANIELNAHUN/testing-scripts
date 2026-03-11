"""
AudioExporter module for exporting processed audio to MP3 format.

This module provides the AudioExporter class responsible for exporting
the final processed audio to MP3 format with high quality settings.
"""

from pathlib import Path
from typing import Union

from pydub import AudioSegment

from .logger_config import get_logger


class AudioExporter:
    """
    Exports processed audio to MP3 format with high quality settings.
    
    The AudioExporter handles the final step of the audio processing pipeline,
    converting the processed audio to MP3 format with a minimum bitrate of 192 kbps
    while preserving audio properties like sample rate and channels.
    """
    
    MIN_BITRATE = "192k"
    
    def __init__(self, output_folder: Path):
        """
        Initialize the AudioExporter with output folder.
        
        Args:
            output_folder: Path to the directory where exported files will be saved
        """
        self.output_folder = Path(output_folder)
        self.logger = get_logger('audio_exporter')
        
        # Ensure output folder exists and is a directory
        try:
            if self.output_folder.exists() and not self.output_folder.is_dir():
                error_msg = f"Output path exists but is not a directory: {self.output_folder}"
                self.logger.error(error_msg)
                from .exceptions import AudioProcessingError
                raise AudioProcessingError(error_msg)
            
            self.output_folder.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"AudioExporter initialized with output folder: {self.output_folder}")
        except Exception as e:
            error_msg = f"Failed to create output directory {self.output_folder}: {str(e)}"
            self.logger.error(error_msg)
            from .exceptions import AudioProcessingError
            raise AudioProcessingError(error_msg) from e
    
    def export(self, audio: AudioSegment, filename: str) -> Path:
        """
        Export audio to MP3 format with high quality settings.
        
        Exports the provided audio segment to MP3 format with a minimum bitrate
        of 192 kbps, preserving the original audio properties (sample rate, channels).
        
        Args:
            audio: The AudioSegment to export
            filename: Name of the output file (without extension)
        
        Returns:
            Path to the exported MP3 file
        
        Raises:
            AudioProcessingError: If export fails
        """
        # Validate input
        if audio is None:
            error_msg = "Cannot export None audio segment"
            self.logger.error(error_msg)
            from .exceptions import AudioProcessingError
            raise AudioProcessingError(error_msg)
        
        # Ensure filename has .mp3 extension
        if not filename.endswith('.mp3'):
            filename = f"{filename}.mp3"
        
        output_path = self.output_folder / filename
        
        self.logger.info(f"Starting export to MP3: {output_path}")
        self.logger.debug(f"Audio properties - Duration: {audio.duration_seconds:.2f}s, "
                         f"Sample rate: {audio.frame_rate}Hz, Channels: {audio.channels}")
        
        try:
            # Export to MP3 with high quality settings
            audio.export(
                str(output_path),
                format="mp3",
                bitrate=self.MIN_BITRATE,
                parameters=["-q:a", "0"]  # Highest quality VBR encoding
            )
            
            # Log successful export with details
            self.logger.info(f"Successfully exported audio to: {output_path}")
            self.logger.info(f"Export details - Duration: {audio.duration_seconds:.2f}s, "
                           f"Bitrate: {self.MIN_BITRATE}, "
                           f"Sample rate: {audio.frame_rate}Hz, "
                           f"Channels: {audio.channels}")
            
            return output_path
            
        except Exception as e:
            error_msg = f"Failed to export audio to {output_path}: {str(e)}"
            self.logger.error(error_msg)
            from .exceptions import AudioProcessingError
            raise AudioProcessingError(error_msg) from e