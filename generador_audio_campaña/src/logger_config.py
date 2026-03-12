"""
Configuración del sistema de logging para Audio Gran Campaña.

Este módulo configura el logging para todo el sistema, proporcionando
diferentes niveles de detalle para debugging y monitoreo.
"""

import logging
import sys
from pathlib import Path


def setup_logging(
    level: int = logging.INFO,
    log_file: Path = None,
    format_string: str = None
) -> logging.Logger:
    """
    Configura el sistema de logging para la aplicación.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path opcional para guardar logs en archivo
        format_string: Formato personalizado para los mensajes de log
    
    Returns:
        Logger configurado para la aplicación
    """
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configurar el logger raíz
    logger = logging.getLogger('audio_gran_campana')
    logger.setLevel(level)
    
    # Limpiar handlers existentes
    logger.handlers.clear()
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo (opcional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger hijo del logger principal de la aplicación.
    
    Args:
        name: Nombre del módulo o componente
    
    Returns:
        Logger configurado para el componente específico
    """
    return logging.getLogger(f'audio_gran_campana.{name}')
