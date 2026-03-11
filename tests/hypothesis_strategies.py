"""
Custom Hypothesis strategies for audio processing tests.

Este módulo define estrategias personalizadas de Hypothesis para generar
datos de prueba consistentes para el sistema Audio Gran Campaña.
"""

import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from pydub import AudioSegment
from pydub.generators import Sine
import hypothesis.strategies as st
from hypothesis import assume


# Audio property strategies
@st.composite
def audio_properties(draw):
    """
    Strategy para generar propiedades de audio aleatorias.
    
    Returns:
        Dict con sample_rate, channels, sample_width
    """
    sample_rate = draw(st.sampled_from([8000, 16000, 22050, 44100, 48000]))
    channels = draw(st.integers(min_value=1, max_value=2))  # mono o stereo
    sample_width = draw(st.sampled_from([1, 2, 4]))  # 8, 16, 32 bits
    
    return {
        'sample_rate': sample_rate,
        'channels': channels,
        'sample_width': sample_width
    }


@st.composite
def audio_segment_with_duration(draw, min_duration_ms=100, max_duration_ms=60000):
    """
    Strategy para generar AudioSegments con duraciones aleatorias.
    
    Args:
        min_duration_ms: Duración mínima en milisegundos
        max_duration_ms: Duración máxima en milisegundos
        
    Returns:
        AudioSegment con duración aleatoria
    """
    duration_ms = draw(st.integers(min_value=min_duration_ms, max_value=max_duration_ms))
    properties = draw(audio_properties())
    
    # Generar audio silencioso con propiedades específicas
    audio = AudioSegment.silent(
        duration=duration_ms,
        frame_rate=properties['sample_rate']
    )
    
    # Ajustar canales y sample width
    if properties['channels'] == 2:
        audio = audio.set_channels(2)
    else:
        audio = audio.set_channels(1)
        
    audio = audio.set_sample_width(properties['sample_width'])
    
    return audio


@st.composite
def audio_segment_with_tone(draw, min_duration_ms=100, max_duration_ms=60000):
    """
    Strategy para generar AudioSegments con tono aleatorio.
    
    Args:
        min_duration_ms: Duración mínima en milisegundos
        max_duration_ms: Duración máxima en milisegundos
        
    Returns:
        AudioSegment con tono aleatorio
    """
    duration_ms = draw(st.integers(min_value=min_duration_ms, max_value=max_duration_ms))
    frequency = draw(st.integers(min_value=200, max_value=2000))
    properties = draw(audio_properties())
    
    # Generar tono con propiedades específicas
    tone = Sine(frequency).to_audio_segment(
        duration=duration_ms,
        frame_rate=properties['sample_rate']
    )
    
    # Ajustar canales y sample width
    if properties['channels'] == 2:
        tone = tone.set_channels(2)
    else:
        tone = tone.set_channels(1)
        
    tone = tone.set_sample_width(properties['sample_width'])
    
    return tone


@st.composite
def file_existence_pattern(draw, sequence_length=5):
    """
    Strategy para generar patrones de archivos existentes/faltantes.
    
    Args:
        sequence_length: Longitud de la secuencia de archivos
        
    Returns:
        Lista de booleanos indicando si cada archivo existe
    """
    # Asegurar que al menos un archivo existe para evitar casos vacíos
    pattern = draw(st.lists(
        st.booleans(), 
        min_size=sequence_length, 
        max_size=sequence_length
    ))
    
    # Si todos son False, hacer que al menos uno sea True
    if not any(pattern):
        index = draw(st.integers(min_value=0, max_value=sequence_length-1))
        pattern[index] = True
    
    return pattern


@st.composite
def audio_file_set(draw, filenames: List[str], temp_dir: Path):
    """
    Strategy para generar un conjunto de archivos de audio en disco.
    
    Args:
        filenames: Lista de nombres de archivos a crear
        temp_dir: Directorio temporal donde crear los archivos
        
    Returns:
        Dict con filename -> AudioSegment (o None si no existe)
    """
    existence_pattern = draw(file_existence_pattern(len(filenames)))
    created_files = {}
    
    for i, (filename, should_exist) in enumerate(zip(filenames, existence_pattern)):
        if should_exist:
            # Generar audio con duración determinística basada en posición
            duration = draw(st.integers(min_value=1000, max_value=10000))
            audio = draw(audio_segment_with_duration(duration, duration))
            
            # Determinar formato basado en extensión
            format_type = "mp3" if filename.endswith(".mp3") else "wav"
            file_path = temp_dir / filename
            
            try:
                audio.export(str(file_path), format=format_type)
                created_files[filename] = audio
            except Exception:
                # Si falla la exportación, marcar como no existente
                created_files[filename] = None
        else:
            created_files[filename] = None
    
    return created_files


@st.composite
def duration_list(draw, min_count=1, max_count=5, min_duration=1000, max_duration=60000):
    """
    Strategy para generar listas de duraciones aleatorias.
    
    Args:
        min_count: Número mínimo de duraciones
        max_count: Número máximo de duraciones
        min_duration: Duración mínima en milisegundos
        max_duration: Duración máxima en milisegundos
        
    Returns:
        Lista de duraciones en milisegundos
    """
    count = draw(st.integers(min_value=min_count, max_value=max_count))
    durations = []
    
    for _ in range(count):
        duration = draw(st.integers(min_value=min_duration, max_value=max_duration))
        durations.append(duration)
    
    return durations


@st.composite
def volume_level(draw):
    """
    Strategy para generar niveles de volumen válidos.
    
    Returns:
        Float entre 0.0 y 1.0 representando el nivel de volumen
    """
    return draw(st.floats(min_value=0.0, max_value=1.0))


@st.composite
def crossfade_parameters(draw):
    """
    Strategy para generar parámetros de crossfade.
    
    Returns:
        Dict con duration_ms y position
    """
    duration_ms = draw(st.integers(min_value=1000, max_value=5000))
    
    return {
        'duration_ms': duration_ms
    }


@st.composite
def audio_format_choice(draw):
    """
    Strategy para elegir formato de audio aleatorio.
    
    Returns:
        String con formato ("wav" o "mp3")
    """
    return draw(st.sampled_from(["wav", "mp3"]))


# Strategies específicas para el dominio del problema

@st.composite
def locutor_sequence_pattern(draw):
    """
    Strategy para generar patrones de existencia de archivos de locutor.
    
    Returns:
        Lista de 5 booleanos para la secuencia de locutor
    """
    return draw(file_existence_pattern(5))


@st.composite
def background_music_durations(draw):
    """
    Strategy para generar duraciones de fondos musicales.
    
    Returns:
        Tuple con (first_bg_duration, second_bg_duration)
    """
    first_duration = draw(st.integers(min_value=6000, max_value=300000))  # 6s a 5min
    second_duration = draw(st.integers(min_value=6000, max_value=300000))  # 6s a 5min
    
    return (first_duration, second_duration)


@st.composite
def processing_durations(draw):
    """
    Strategy para generar duraciones relacionadas con el procesamiento completo.
    
    Returns:
        Dict con locutor_duration, first_bg_duration, calculated_second_duration
    """
    locutor_duration = draw(st.integers(min_value=5000, max_value=300000))  # 5s a 5min
    first_bg_duration = draw(st.integers(min_value=6000, max_value=300000))  # 6s a 5min
    
    # Calcular duración del segundo fondo según la fórmula
    calculated_second_duration = locutor_duration + 10000 - first_bg_duration + 3000
    
    # Asegurar que la duración calculada sea positiva
    assume(calculated_second_duration > 1000)
    
    return {
        'locutor_duration': locutor_duration,
        'first_bg_duration': first_bg_duration,
        'calculated_second_duration': calculated_second_duration
    }


# Utility functions para crear archivos temporales

def create_temp_audio_dir():
    """
    Crea un directorio temporal para archivos de audio.
    
    Returns:
        Path del directorio temporal
    """
    return Path(tempfile.mkdtemp())


def cleanup_temp_dir(temp_dir: Path):
    """
    Limpia un directorio temporal.
    
    Args:
        temp_dir: Path del directorio a limpiar
    """
    if temp_dir.exists():
        shutil.rmtree(str(temp_dir), ignore_errors=True)