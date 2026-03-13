"""
ElevenLabs Text-to-Speech Generator

This module provides functionality to generate audio using the ElevenLabs API
for campaign announcements with customizable parameters.
"""

import os
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass

from .logger_config import get_logger
from .exceptions import AudioProcessingError

from elevenlabs.client import ElevenLabs
from load_dotenv import load_dotenv

load_dotenv()


logger = get_logger('elevenlabs_generator')


@dataclass
class CampaignParams:
    """Parameters for campaign audio generation."""
    fecha: str
    hora: str
    lugar: str
    referencia: str


class ElevenLabsGenerator:
    """Generator for ElevenLabs text-to-speech audio."""
    
    def __init__(self, api_key: str, voice_id: str):
        """
        Initialize the ElevenLabs generator.
        
        Args:
            api_key: ElevenLabs API key
            voice_id: Voice ID to use for generation
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.client = ElevenLabs(api_key=api_key)
    
    def generate_campaign_audio(
        self,
        params: CampaignParams,
        output_folder: Path,
        use_today: bool = False,
        model_id: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128"
    ) -> Path:
        """
        Generate campaign audio with the specified parameters.
        
        Args:
            params: Campaign parameters (fecha, hora, lugar, referencia)
            output_folder: Folder to save the generated audio
            use_today: If True, uses "HOY" instead of "ESTE"
            model_id: ElevenLabs model to use
            output_format: Audio output format
            
        Returns:
            Path to the generated audio file
            
        Raises:
            AudioProcessingError: If generation fails
        """
        try:
            # Create the text based on parameters
            prefix = "HOY" if use_today else "ESTE"
            text = f"{prefix} {params.fecha}, DESDE LAS {params.hora} EN {params.lugar}. {params.referencia}..."
            
            logger.info(f"Generating audio for text: {text}")
            
            # Generate audio using SDK
            logger.info("Making request to ElevenLabs API using SDK")
            print(f"Text: {text}, voice: {self.voice_id}")
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=model_id,
                output_format=output_format
            )
            
            # Save the audio file
            filename = f"campaign_{'today' if use_today else 'este'}_{params.fecha.replace(' ', '_').lower()}.mp3"
            output_path = output_folder / filename
            
            # Ensure output folder exists
            output_folder.mkdir(parents=True, exist_ok=True)
            
            # Write audio content to file
            with open(output_path, 'wb') as f:
                for chunk in audio:
                    f.write(chunk)
            
            logger.info(f"Audio generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Error during audio generation: {e}"
            logger.error(error_msg, exc_info=True)
            raise AudioProcessingError(error_msg)
    
    def generate_both_versions(
        self,
        params: CampaignParams,
        output_folder: Path,
        model_id: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128"
    ) -> Dict[str, Path]:
        """
        Generate both versions of the campaign audio (ESTE and HOY).
        
        Args:
            params: Campaign parameters
            output_folder: Folder to save the generated audio files
            model_id: ElevenLabs model to use
            output_format: Audio output format
            
        Returns:
            Dictionary with 'este' and 'hoy' keys mapping to file paths
            
        Raises:
            AudioProcessingError: If generation fails
        """
        results = {}
        
        try:
            # Generate "ESTE" version
            logger.info("Generating 'ESTE' version")
            results['este'] = self.generate_campaign_audio(
                params, output_folder, use_today=False, 
                model_id=model_id, output_format=output_format
            )
            
            # Generate "HOY" version
            logger.info("Generating 'HOY' version")
            results['hoy'] = self.generate_campaign_audio(
                params, output_folder, use_today=True,
                model_id=model_id, output_format=output_format
            )
            
            logger.info("Both versions generated successfully")
            return results
            
        except Exception as e:
            # Clean up any partially created files
            for path in results.values():
                if path.exists():
                    try:
                        path.unlink()
                        logger.info(f"Cleaned up partial file: {path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Could not clean up file {path}: {cleanup_error}")
            
            raise e
    
    def test_connection(self) -> bool:
        """
        Test the connection to ElevenLabs API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test connection by fetching voices
            voices = self.client.voices.get_all()
            logger.info("ElevenLabs API connection test successful")
            return True
                
        except Exception as e:
            logger.error(f"ElevenLabs API connection test failed: {e}")
            return False


def create_generator_from_env() -> Optional[ElevenLabsGenerator]:
    """
    Create an ElevenLabsGenerator from environment variables.
    
    Expected environment variables:
    - ELEVEN_API_KEY: ElevenLabs API key
    - ELEVEN_VOICE_ID: Voice ID (defaults to provided Cesar Rodriguez ID)
    
    Returns:
        ElevenLabsGenerator instance or None if env vars are missing
    """
    api_key = os.getenv('ELEVEN_API_KEY')
    voice_id = os.getenv('ELEVEN_VOICE_ID', 'JBFqnCBsd6RMkjVDRZzb')  # Default to Cesar Rodriguez
    
    if not api_key:
        logger.warning("ELEVEN_API_KEY environment variable not found")
        return None
    
    return ElevenLabsGenerator(api_key, voice_id)