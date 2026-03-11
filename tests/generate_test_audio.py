#!/usr/bin/env python3
"""
Generate synthetic audio files for testing Audio Gran Campaña.

This script creates test audio files with different durations, formats,
and characteristics to support comprehensive testing of the audio processing pipeline.
"""

from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine, Square, Sawtooth
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_fixtures_directory():
    """Create the fixtures directory structure."""
    fixtures_dir = Path(__file__).parent / 'fixtures' / 'audio'
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    return fixtures_dir


def generate_tone_audio(frequency: int, duration_ms: int, volume: float = 0.5) -> AudioSegment:
    """
    Generate a sine wave audio segment.
    
    Args:
        frequency: Frequency in Hz
        duration_ms: Duration in milliseconds
        volume: Volume level (0.0 to 1.0)
    
    Returns:
        AudioSegment with the generated tone
    """
    # Generate sine wave
    audio = Sine(frequency).to_audio_segment(duration=duration_ms)
    
    # Adjust volume (pydub uses dB, so convert from linear scale)
    if volume != 1.0:
        # Convert linear volume to dB (approximate)
        db_change = 20 * (volume - 1) if volume < 1 else 0
        audio = audio + db_change
    
    return audio


def generate_complex_audio(duration_ms: int, base_freq: int = 440) -> AudioSegment:
    """
    Generate a more complex audio segment with multiple frequencies.
    
    Args:
        duration_ms: Duration in milliseconds
        base_freq: Base frequency in Hz
    
    Returns:
        AudioSegment with complex audio content
    """
    # Create multiple tones and mix them
    tone1 = Sine(base_freq).to_audio_segment(duration=duration_ms)
    tone2 = Sine(base_freq * 1.5).to_audio_segment(duration=duration_ms) - 6  # Lower volume
    tone3 = Square(base_freq * 0.5).to_audio_segment(duration=duration_ms) - 12  # Even lower
    
    # Mix the tones
    mixed = tone1.overlay(tone2).overlay(tone3)
    
    # Add some fade in/out for more realistic audio
    mixed = mixed.fade_in(100).fade_out(100)
    
    return mixed


def generate_locutor_files(fixtures_dir: Path):
    """Generate synthetic locutor audio files."""
    logger.info("Generating locutor audio files...")
    
    locutor_files = [
        ('Gran Campaña - Introduccion.wav', 8000, 220),  # 8 seconds, low frequency
        ('Gran Campaña - Hora y lugar del evento.mp3', 5000, 330),  # 5 seconds, mid frequency
        ('Gran Campaña - Cuerpo.wav', 15000, 440),  # 15 seconds, standard frequency
        ('Gran Campaña - Cierre.wav', 6000, 550),  # 6 seconds, higher frequency
    ]
    
    for filename, duration_ms, frequency in locutor_files:
        logger.info(f"Creating {filename} ({duration_ms}ms, {frequency}Hz)")
        
        # Generate complex audio for more realistic testing
        audio = generate_complex_audio(duration_ms, frequency)
        
        # Export in the appropriate format
        file_path = fixtures_dir / filename
        if filename.endswith('.wav'):
            audio.export(file_path, format='wav')
        else:
            audio.export(file_path, format='mp3', bitrate='192k')


def generate_background_files(fixtures_dir: Path):
    """Generate synthetic background music files."""
    logger.info("Generating background music files...")
    
    background_files = [
        ('Yo tengo un amigo que me ama.mp3', 45000, 110),  # 45 seconds, low bass-like frequency
        ('Eres todo poderoso.mp3', 60000, 165),  # 60 seconds, slightly higher
    ]
    
    for filename, duration_ms, base_frequency in background_files:
        logger.info(f"Creating {filename} ({duration_ms}ms, base {base_frequency}Hz)")
        
        # Generate more complex background music-like audio
        # Use multiple harmonics to simulate music
        audio = AudioSegment.silent(duration=0)
        
        # Add multiple frequency components
        for i, harmonic in enumerate([1, 1.5, 2, 2.5, 3]):
            freq = int(base_frequency * harmonic)
            volume_reduction = i * 3  # Each harmonic gets quieter
            
            tone = Sine(freq).to_audio_segment(duration=duration_ms) - volume_reduction
            
            if i == 0:
                audio = tone
            else:
                audio = audio.overlay(tone)
        
        # Add some variation in volume to simulate music dynamics
        # Create a gentle volume envelope
        segments = []
        segment_duration = duration_ms // 10  # Divide into 10 segments
        
        for i in range(10):
            start = i * segment_duration
            end = min((i + 1) * segment_duration, duration_ms)
            segment = audio[start:end]
            
            # Vary volume slightly (simulate music dynamics)
            volume_variation = -2 + (i % 3)  # Vary between -2 and +1 dB
            segment = segment + volume_variation
            segments.append(segment)
        
        # Recombine segments
        audio = sum(segments)
        
        # Add fade in/out
        audio = audio.fade_in(500).fade_out(500)
        
        # Export as MP3
        file_path = fixtures_dir / filename
        audio.export(file_path, format='mp3', bitrate='192k')


def generate_edge_case_files(fixtures_dir: Path):
    """Generate additional files for edge case testing."""
    logger.info("Generating edge case test files...")
    
    edge_cases = [
        # Very short files
        ('short_locutor.wav', 500, 440),  # 0.5 seconds
        ('short_background.mp3', 1000, 220),  # 1 second
        
        # Very long files
        ('long_background.mp3', 120000, 110),  # 2 minutes
        
        # Different sample rates (pydub will handle conversion)
        ('different_format.wav', 10000, 880),  # 10 seconds, high frequency
        
        # Silent file for testing
        ('silent.wav', 5000, 0),  # 5 seconds of silence
    ]
    
    for filename, duration_ms, frequency in edge_cases:
        logger.info(f"Creating edge case file {filename}")
        
        if frequency == 0:
            # Create silent audio
            audio = AudioSegment.silent(duration=duration_ms)
        else:
            # Create tone audio
            audio = generate_tone_audio(frequency, duration_ms)
        
        file_path = fixtures_dir / filename
        if filename.endswith('.wav'):
            audio.export(file_path, format='wav')
        else:
            audio.export(file_path, format='mp3', bitrate='192k')


def generate_corrupted_files(fixtures_dir: Path):
    """Generate files for error testing."""
    logger.info("Generating files for error testing...")
    
    # Create a text file with audio extension (should cause loading error)
    corrupted_file = fixtures_dir / 'corrupted.mp3'
    with open(corrupted_file, 'w') as f:
        f.write("This is not an audio file")
    
    # Create an empty file
    empty_file = fixtures_dir / 'empty.wav'
    empty_file.touch()
    
    logger.info("Created corrupted and empty files for error testing")


def main():
    """Generate all test audio files."""
    logger.info("Starting test audio file generation...")
    
    try:
        # Create fixtures directory
        fixtures_dir = create_fixtures_directory()
        logger.info(f"Created fixtures directory: {fixtures_dir}")
        
        # Generate all types of test files
        generate_locutor_files(fixtures_dir)
        generate_background_files(fixtures_dir)
        generate_edge_case_files(fixtures_dir)
        generate_corrupted_files(fixtures_dir)
        
        logger.info("Test audio file generation completed successfully!")
        logger.info(f"Files created in: {fixtures_dir}")
        
        # List all created files
        created_files = list(fixtures_dir.glob('*'))
        logger.info(f"Total files created: {len(created_files)}")
        for file_path in sorted(created_files):
            size_kb = file_path.stat().st_size / 1024
            logger.info(f"  - {file_path.name} ({size_kb:.1f} KB)")
            
    except Exception as e:
        logger.error(f"Error generating test files: {e}")
        raise


if __name__ == '__main__':
    main()