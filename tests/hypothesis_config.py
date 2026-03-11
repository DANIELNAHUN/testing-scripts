"""
Configuración centralizada de Hypothesis para tests de audio.

Este módulo define la configuración global de Hypothesis para todos los
property-based tests del sistema Audio Gran Campaña.
"""

from hypothesis import settings, Verbosity
from functools import wraps


# Configuración global de Hypothesis
settings.register_profile(
    "audio_processing",
    max_examples=100,  # Mínimo 100 iteraciones por test como especifica el diseño
    deadline=10000,    # 10 segundos de timeout para operaciones de audio
    verbosity=Verbosity.normal,
    suppress_health_check=[],
    print_blob=False
)

# Configuración para tests rápidos (sin procesamiento de audio pesado)
settings.register_profile(
    "audio_fast",
    max_examples=50,
    deadline=5000,     # 5 segundos para tests más rápidos
    verbosity=Verbosity.normal
)

# Configuración para tests de integración (más tiempo)
settings.register_profile(
    "audio_integration",
    max_examples=20,
    deadline=30000,    # 30 segundos para tests de integración
    verbosity=Verbosity.normal
)

# Configuración para debugging
settings.register_profile(
    "debug",
    max_examples=10,
    deadline=None,     # Sin timeout para debugging
    verbosity=Verbosity.verbose,
    print_blob=True
)

# Activar perfil por defecto
settings.load_profile("audio_processing")


def audio_property_test(profile="audio_processing"):
    """
    Decorador para property tests de audio con configuración estándar.
    
    Args:
        profile: Perfil de configuración a usar
        
    Usage:
        @audio_property_test()
        @given(...)
        def test_my_property(...):
            pass
    """
    def decorator(test_func):
        @wraps(test_func)
        @settings(
            max_examples=100 if profile == "audio_processing" else 50,
            deadline=10000 if profile == "audio_processing" else 5000
        )
        def wrapper(*args, **kwargs):
            return test_func(*args, **kwargs)
        return wrapper
    return decorator


def fast_audio_test():
    """
    Decorador para tests de audio rápidos.
    
    Usage:
        @fast_audio_test()
        @given(...)
        def test_my_property(...):
            pass
    """
    def decorator(test_func):
        @wraps(test_func)
        @settings(max_examples=50, deadline=5000)
        def wrapper(*args, **kwargs):
            return test_func(*args, **kwargs)
        return wrapper
    return decorator


def integration_audio_test():
    """
    Decorador para tests de integración de audio.
    
    Usage:
        @integration_audio_test()
        @given(...)
        def test_my_property(...):
            pass
    """
    def decorator(test_func):
        @wraps(test_func)
        @settings(max_examples=20, deadline=30000)
        def wrapper(*args, **kwargs):
            return test_func(*args, **kwargs)
        return wrapper
    return decorator


def debug_audio_test():
    """
    Decorador para debugging de tests de audio.
    
    Usage:
        @debug_audio_test()
        @given(...)
        def test_my_property(...):
            pass
    """
    def decorator(test_func):
        @wraps(test_func)
        @settings(max_examples=10, deadline=None, verbosity=Verbosity.verbose)
        def wrapper(*args, **kwargs):
            return test_func(*args, **kwargs)
        return wrapper
    return decorator


# Configuraciones específicas por tipo de test

PROPERTY_TEST_SETTINGS = {
    "file_loading": settings(max_examples=100, deadline=5000),
    "audio_processing": settings(max_examples=100, deadline=10000),
    "audio_combination": settings(max_examples=100, deadline=15000),
    "export_operations": settings(max_examples=50, deadline=20000),
    "integration": settings(max_examples=20, deadline=30000)
}


def get_test_settings(test_type: str):
    """
    Obtiene configuración de Hypothesis para un tipo específico de test.
    
    Args:
        test_type: Tipo de test ("file_loading", "audio_processing", etc.)
        
    Returns:
        Settings de Hypothesis configurados para el tipo de test
    """
    return PROPERTY_TEST_SETTINGS.get(test_type, PROPERTY_TEST_SETTINGS["audio_processing"])