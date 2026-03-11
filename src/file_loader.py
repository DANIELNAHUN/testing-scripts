"""
FileLoader component for Audio Gran Campaña.

Este módulo maneja la carga de archivos de audio desde el sistema de archivos,
soportando formatos WAV y MP3.
"""

from pathlib import Path
from typing import Optional, Dict, List
from pydub import AudioSegment

from src.logger_config import get_logger


logger = get_logger('file_loader')


class FileLoader:
    """
    Carga archivos de audio desde una carpeta de origen.
    
    Soporta formatos WAV y MP3. Maneja archivos faltantes de manera
    elegante retornando None en lugar de lanzar excepciones.
    """
    
    def __init__(self, source_folder: Path):
        """
        Inicializa el loader con la carpeta de origen.
        
        Args:
            source_folder: Path a la carpeta que contiene los archivos de audio
        """
        self.source_folder = Path(source_folder)
        logger.info(f"FileLoader initialized with source folder: {self.source_folder}")
    
    def load_audio(self, filename: str) -> Optional[AudioSegment]:
        """
        Carga un archivo de audio desde la carpeta de origen.
        
        Soporta formatos WAV y MP3. Si el archivo no existe, retorna None
        en lugar de lanzar una excepción.
        
        Args:
            filename: Nombre del archivo a cargar (con extensión)
        
        Returns:
            AudioSegment si el archivo existe y se carga correctamente, None en caso contrario
        """
        file_path = self.source_folder / filename
        
        if not file_path.exists():
            logger.warning(f"File not found, skipping: {filename}")
            return None
        
        try:
            # Determinar formato basado en extensión
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.wav':
                audio = AudioSegment.from_wav(str(file_path))
            elif file_extension == '.mp3':
                audio = AudioSegment.from_mp3(str(file_path))
            else:
                logger.warning(f"Unsupported format for file: {filename}")
                return None
            
            logger.info(f"Successfully loaded: {filename} (duration: {len(audio)}ms)")
            return audio
            
        except Exception as e:
            logger.error(f"Error loading file {filename}: {str(e)}")
            return None
    
    def load_multiple(self, filenames: List[str]) -> Dict[str, Optional[AudioSegment]]:
        """
        Carga múltiples archivos de audio.
        
        Args:
            filenames: Lista de nombres de archivos a cargar
        
        Returns:
            Diccionario con filename como key y AudioSegment o None como value
        """
        logger.info(f"Loading {len(filenames)} audio files...")
        
        results = {}
        loaded_count = 0
        skipped_count = 0
        
        for filename in filenames:
            audio = self.load_audio(filename)
            results[filename] = audio
            
            if audio is not None:
                loaded_count += 1
            else:
                skipped_count += 1
        
        logger.info(f"Loading complete: {loaded_count} loaded, {skipped_count} skipped")
        
        return results
