"""Data models for audio processing results."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from pydub import AudioSegment


@dataclass
class LocutorResult:
    """Result of processing locutor audio files.
    
    Attributes:
        audio: The unified audio segment containing all concatenated locutor files
        duration_ms: Total duration of the unified audio in milliseconds
        files_loaded: List of filenames that were successfully loaded
        files_skipped: List of filenames that were skipped (not found)
    """
    audio: AudioSegment
    duration_ms: int
    files_loaded: List[str]
    files_skipped: List[str]


@dataclass
class BackgroundResult:
    """Result of processing background music files.
    
    Attributes:
        audio: The unified background music audio segment
        duration_ms: Total duration of the unified background in milliseconds
        first_bg_duration_ms: Duration of the first background music in milliseconds
        second_bg_duration_ms: Duration of the second background music in milliseconds
        crossfade_applied: Whether crossfade transition was successfully applied
    """
    audio: AudioSegment
    duration_ms: int
    first_bg_duration_ms: int
    second_bg_duration_ms: int
    crossfade_applied: bool


@dataclass
class ProcessingResult:
    """Complete result of audio processing pipeline.
    
    Attributes:
        success: Whether the processing completed successfully
        output_path: Path to the exported output file (None if processing failed)
        final_duration_ms: Duration of the final audio in milliseconds
        locutor_result: Result from locutor processing (None if processing failed)
        background_result: Result from background processing (None if processing failed)
        error_message: Error message if processing failed (None if successful)
        validation_warnings: List of validation warnings encountered during processing
    """
    success: bool
    output_path: Optional[Path]
    final_duration_ms: int
    locutor_result: Optional[LocutorResult]
    background_result: Optional[BackgroundResult]
    error_message: Optional[str]
    validation_warnings: List[str]
