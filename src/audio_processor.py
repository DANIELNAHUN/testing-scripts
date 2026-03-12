"""
AudioProcessor - Main orchestrator for Audio Gran Campaña.

Este módulo implementa el orquestador principal que coordina todo el pipeline
de procesamiento de audio, desde la carga de archivos hasta la exportación final.
"""

from pathlib import Path
from typing import Optional

from src.file_loader import FileLoader
from src.locutor_processor import LocutorProcessor
from src.background_music_processor import BackgroundMusicProcessor
from src.audio_combiner import AudioCombiner
from src.audio_exporter import AudioExporter
from src.models import ProcessingResult
from src.exceptions import AudioProcessingError, MissingFileError
from src.logger_config import get_logger


logger = get_logger('audio_processor')


class AudioProcessor:
    """
    Orquestador principal del pipeline de procesamiento de audio.
    
    Coordina todos los componentes del sistema para procesar archivos de locutor
    y fondos musicales, aplicar efectos, combinarlos y exportar el resultado final.
    """
    
    def __init__(self, source_folder: Path, output_folder: Path):
        """
        Inicializa el AudioProcessor con carpetas de origen y destino.
        
        Args:
            source_folder: Path a la carpeta que contiene los archivos de audio de origen
            output_folder: Path a la carpeta donde se guardará el archivo final
        """
        self.source_folder = Path(source_folder)
        self.output_folder = Path(output_folder)
        
        # Inicializar todos los componentes
        self.file_loader = FileLoader(self.source_folder)
        self.locutor_processor = LocutorProcessor(self.file_loader)
        self.background_processor = BackgroundMusicProcessor(self.file_loader)
        self.audio_combiner = AudioCombiner()
        self.audio_exporter = AudioExporter(self.output_folder)
        
        logger.info(f"AudioProcessor initialized")
        logger.info(f"Source folder: {self.source_folder}")
        logger.info(f"Output folder: {self.output_folder}")
    
    def process(self) -> ProcessingResult:
        """
        Ejecuta el pipeline completo de procesamiento de audio.
        
        Pipeline de procesamiento:
        1. Validar archivos requeridos
        2. Procesar locutor (LocutorProcessor.unify_locutor_audio)
        3. Procesar primer fondo (BackgroundMusicProcessor.process_first_background)
        4. Calcular duración segundo fondo
        5. Procesar segundo fondo
        6. Unificar fondos
        7. Combinar locutor con fondo
        8. Validar duraciones
        9. Exportar audio final
        
        Returns:
            ProcessingResult con el resultado completo y metadata
        """
        logger.info("Starting audio processing pipeline")
        
        try:
            # Etapa 1: Validar archivos requeridos
            logger.info("Stage 1: Validating required files")
            self._validate_required_files()
            
            # Etapa 2: Procesar locutor
            logger.info("Stage 2: Processing locutor audio")
            locutor_result = self.locutor_processor.unify_locutor_audio(
                export_path=Path('files/output'),
                export_filename='locutor_unido'
            )
            
            # Validar que al menos un archivo de locutor fue cargado
            if not locutor_result.files_loaded:
                error_msg = "No locutor files were loaded - all locutor files are missing"
                logger.error(error_msg)
                raise MissingFileError(error_msg, self.locutor_processor.LOCUTOR_SEQUENCE)
            
            logger.info(f"Locutor processing completed: {len(locutor_result.files_loaded)} files loaded, "
                       f"duration: {locutor_result.duration_ms}ms")
            
            # Etapa 3: Procesar primer fondo musical
            logger.info("Stage 3: Processing first background music")
            first_background = self.background_processor.process_first_background()
            first_bg_duration_ms = len(first_background)
            logger.info(f"First background processed: duration={first_bg_duration_ms}ms")
            
            # Etapa 4: Calcular duración del segundo fondo
            logger.info("Stage 4: Calculating second background duration")
            second_bg_duration = self.background_processor.calculate_second_background_duration(
                locutor_result.duration_ms,
                first_bg_duration_ms
            )
            
            # Etapa 5: Procesar segundo fondo musical
            logger.info("Stage 5: Processing second background music")
            second_background = self.background_processor.process_second_background(second_bg_duration)
            second_bg_duration_ms = len(second_background)
            logger.info(f"Second background processed: duration={second_bg_duration_ms}ms")
            
            # Etapa 6: Unificar fondos musicales
            logger.info("Stage 6: Unifying background music")
            background_result = self.background_processor.unify_backgrounds(
                first_background,
                second_background
            )
            logger.info(f"Background unification completed: duration={background_result.duration_ms}ms")
            
            # Etapa 7: Combinar locutor con fondo
            logger.info("Stage 7: Combining locutor with background")
            combined_audio = self.audio_combiner.combine(
                locutor_result.audio,
                background_result.audio
            )
            final_duration_ms = len(combined_audio)
            logger.info(f"Audio combination completed: duration={final_duration_ms}ms")
            
            # Etapa 8: Validar duraciones
            logger.info("Stage 8: Validating durations")
            validation_warnings = []
            validation_passed = self.audio_combiner.validate_durations(
                locutor_result.duration_ms,
                background_result.duration_ms,
                final_duration_ms
            )
            
            if not validation_passed:
                warning_msg = "Duration validation failed - see logs for details"
                validation_warnings.append(warning_msg)
                logger.warning(warning_msg)
            
            # Etapa 9: Exportar audio final
            logger.info("Stage 9: Exporting final audio")
            output_filename = "Gran_Campana_Final"
            output_path = self.audio_exporter.export(combined_audio, output_filename)
            logger.info(f"Audio export completed: {output_path}")
            
            # Crear resultado exitoso
            result = ProcessingResult(
                success=True,
                output_path=output_path,
                final_duration_ms=final_duration_ms,
                locutor_result=locutor_result,
                background_result=background_result,
                error_message=None,
                validation_warnings=validation_warnings
            )
            
            logger.info("Audio processing pipeline completed successfully")
            logger.info(f"Final output: {output_path}")
            logger.info(f"Final duration: {final_duration_ms}ms ({final_duration_ms/1000:.2f}s)")
            
            return result
            
        except Exception as e:
            error_msg = f"Audio processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Crear resultado de error
            result = ProcessingResult(
                success=False,
                output_path=None,
                final_duration_ms=0,
                locutor_result=None,
                background_result=None,
                error_message=error_msg,
                validation_warnings=[]
            )
            
            return result
    
    def _validate_required_files(self) -> None:
        """
        Valida que los archivos de fondo requeridos existan.
        
        Verifica que ambos archivos de fondo musical estén presentes antes
        de iniciar el procesamiento.
        
        Raises:
            MissingFileError: Si algún archivo de fondo requerido falta
        """
        logger.info("Validating required background music files")
        
        required_files = [
            self.background_processor.FIRST_BACKGROUND,
            self.background_processor.SECOND_BACKGROUND
        ]
        
        missing_files = []
        
        for filename in required_files:
            file_path = self.source_folder / filename
            if not file_path.exists():
                missing_files.append(filename)
                logger.error(f"Required file not found: {filename}")
            else:
                logger.info(f"Required file found: {filename}")
        
        if missing_files:
            error_msg = f"Required background music files are missing: {missing_files}"
            logger.error(error_msg)
            raise MissingFileError(error_msg, missing_files)
        
        logger.info("All required files validation passed")