"""Custom exceptions for audio processing."""


class AudioProcessingError(Exception):
    """Base exception for all audio processing errors.
    
    This is the parent exception class for all audio processing-related errors.
    Catching this exception will catch all specific audio processing errors.
    """
    pass


class MissingFileError(AudioProcessingError):
    """Exception raised when required audio files are missing.
    
    This exception is raised when:
    - Required background music files do not exist
    - All locutor audio files are missing
    
    Args:
        message: Description of which files are missing
        missing_files: Optional list of missing file names
    """
    def __init__(self, message: str, missing_files: list = None):
        super().__init__(message)
        self.missing_files = missing_files or []


class ValidationError(AudioProcessingError):
    """Exception raised when audio validation fails.
    
    This exception is raised when:
    - Duration synchronization validation fails
    - Audio quality validation fails
    - Other validation checks fail
    
    Args:
        message: Description of the validation failure
        details: Optional dictionary with validation details
    """
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}
