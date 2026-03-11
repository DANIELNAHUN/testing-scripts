# Hypothesis Configuration for Audio Gran Campaña

This document explains how to use the centralized Hypothesis configuration for property-based testing in the Audio Gran Campaña project.

## Overview

The project uses a centralized Hypothesis configuration to ensure consistent testing across all property-based tests. This configuration is designed specifically for audio processing tests with appropriate timeouts and iteration counts.

## Configuration Files

### `tests/hypothesis_config.py`
Contains centralized Hypothesis settings and decorators:
- **Default profile**: 100 iterations, 10-second timeout
- **Fast profile**: 50 iterations, 5-second timeout  
- **Integration profile**: 20 iterations, 30-second timeout
- **Debug profile**: 10 iterations, no timeout, verbose output

### `tests/hypothesis_strategies.py`
Contains custom strategies for audio testing:
- `audio_segment_with_duration()`: Generate AudioSegments with random durations
- `audio_properties()`: Generate random audio properties (sample rate, channels, etc.)
- `file_existence_pattern()`: Generate patterns of existing/missing files
- `duration_list()`: Generate lists of durations
- `processing_durations()`: Generate durations for complete processing scenarios

### `tests/conftest.py`
Global pytest configuration:
- Activates default Hypothesis profile
- Provides common fixtures for temporary directories
- Automatically marks property tests and integration tests

## Usage

### Writing Property Tests

Use the `@audio_property_test()` decorator for standard property tests:

```python
from hypothesis import given, strategies as st
from tests.hypothesis_config import audio_property_test
from tests.hypothesis_strategies import audio_segment_with_duration

@audio_property_test()
@given(
    duration_ms=st.integers(min_value=1000, max_value=60000),
    audio=audio_segment_with_duration(1000, 60000)
)
def test_property_example(duration_ms, audio):
    """
    Property Example: Description of what this property validates
    Feature: audio-gran-campana, Property X: Property Name
    
    Validates: Requirements X.Y, Z.A
    """
    # Test implementation
    assert len(audio) == duration_ms
```

### Using Custom Strategies

Import and use custom strategies for consistent test data:

```python
from tests.hypothesis_strategies import (
    audio_segment_with_duration,
    file_existence_pattern,
    processing_durations
)

@audio_property_test()
@given(
    pattern=file_existence_pattern(5),  # 5 files
    durations=processing_durations()
)
def test_my_property(pattern, durations):
    # Test implementation
    pass
```

### Alternative Decorators

For specific test types, use specialized decorators:

```python
from tests.hypothesis_config import fast_audio_test, integration_audio_test, debug_audio_test

@fast_audio_test()  # 50 iterations, 5s timeout
@given(...)
def test_fast_property(...):
    pass

@integration_audio_test()  # 20 iterations, 30s timeout  
@given(...)
def test_integration_property(...):
    pass

@debug_audio_test()  # 10 iterations, no timeout, verbose
@given(...)
def test_debug_property(...):
    pass
```

## Property Test Requirements

All property tests must follow these conventions:

1. **Naming**: Use `test_property_N_description` format where N is the property number
2. **Documentation**: Include property description and requirements validation
3. **Feature tag**: Include `# Feature: audio-gran-campana, Property N: Name` comment
4. **Decorators**: Use `@audio_property_test()` and `@given(...)`
5. **Iterations**: Default 100 iterations (configured automatically)

## Running Tests

### Run all property tests:
```bash
pytest -m property_test
```

### Run with different profiles:
```bash
# Fast profile (50 iterations)
HYPOTHESIS_PROFILE=audio_fast pytest -m property_test

# Debug profile (10 iterations, verbose)
HYPOTHESIS_PROFILE=debug pytest -m property_test -v
```

### Run specific property test:
```bash
pytest tests/test_file_loader.py::test_property_1_multi_format_audio_loading -v
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure `tests/` is in Python path
2. **Timeout errors**: Use `@integration_audio_test()` for slow tests
3. **Memory issues**: Reduce max_examples in custom settings

### Debugging Property Tests

Use the debug decorator for troubleshooting:

```python
@debug_audio_test()  # Verbose output, no timeout
@given(...)
def test_property_debug(data):
    print(f"Generated data: {data}")  # Will be shown in verbose mode
    # Test implementation
```

### Performance Tips

1. Use `@fast_audio_test()` for simple property tests
2. Use `@integration_audio_test()` only for complex end-to-end tests
3. Generate smaller audio segments when possible (shorter durations)
4. Use `assume()` to filter invalid test cases early

## Configuration Profiles

The system supports multiple Hypothesis profiles:

- **default**: Standard testing (100 examples, 10s timeout)
- **audio_fast**: Quick testing (50 examples, 5s timeout)
- **audio_integration**: Integration testing (20 examples, 30s timeout)
- **debug**: Debugging (10 examples, no timeout, verbose)

Switch profiles using environment variable:
```bash
export HYPOTHESIS_PROFILE=audio_fast
pytest tests/
```

## Verification

To verify all property tests are properly configured:

```bash
python verify_property_tests.py
```

This script checks:
- All property tests have proper decorators
- Hypothesis imports are correct
- Custom strategies are imported
- Configuration is consistent across files