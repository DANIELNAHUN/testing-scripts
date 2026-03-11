"""
Pytest configuration and fixtures for audio processing tests.

This file configures Hypothesis settings globally and provides common fixtures.
"""

import pytest
from hypothesis import settings, Verbosity
import tempfile
import shutil
from pathlib import Path


# Configure Hypothesis globally
settings.register_profile(
    "default",
    max_examples=100,  # Minimum 100 iterations as specified in design
    deadline=10000,    # 10 seconds timeout for audio processing
    verbosity=Verbosity.normal,
    suppress_health_check=[],
    print_blob=False
)

settings.register_profile(
    "ci", 
    max_examples=50,   # Fewer examples for CI to speed up tests
    deadline=15000,    # Longer deadline for CI environments
    verbosity=Verbosity.normal
)

settings.register_profile(
    "debug",
    max_examples=10,
    deadline=None,
    verbosity=Verbosity.verbose,
    print_blob=True
)

# Load default profile
settings.load_profile("default")


@pytest.fixture(scope="session")
def temp_audio_workspace():
    """
    Create a temporary workspace for audio tests.
    
    This fixture creates a temporary directory structure that mimics
    the expected audio file organization.
    """
    temp_dir = tempfile.mkdtemp(prefix="audio_test_")
    workspace = Path(temp_dir)
    
    # Create expected directory structure
    source_dir = workspace / "files" / "source"
    output_dir = workspace / "files" / "output"
    source_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    
    yield {
        'workspace': workspace,
        'source': source_dir,
        'output': output_dir
    }
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def clean_temp_dir():
    """
    Provide a clean temporary directory for each test.
    
    Automatically cleans up after the test completes.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "property_test: mark test as a property-based test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark property tests
        if "property" in item.name.lower() and "test_property_" in item.name:
            item.add_marker(pytest.mark.property_test)
        
        # Mark integration tests
        if "integration" in item.name.lower() or "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests (property tests and integration tests)
        if any(marker.name in ["property_test", "integration"] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.slow)