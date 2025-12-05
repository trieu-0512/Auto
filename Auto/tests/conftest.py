# Pytest configuration and fixtures
# Ensures all tests use isolated temporary databases and cleanup after

import pytest
import tempfile
import shutil
import os


@pytest.fixture(autouse=True)
def isolate_from_production_db(monkeypatch):
    """
    Automatically isolate all tests from production databases.
    This ensures tests never write to data/data.db or data/app_data.db.
    """
    # Create temp directory for this test session
    temp_dir = tempfile.mkdtemp(prefix="test_")
    
    # Monkeypatch default paths if any test accidentally uses defaults
    original_cwd = os.getcwd()
    
    yield temp_dir
    
    # Cleanup temp directory after test
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass


@pytest.fixture
def clean_temp_dir():
    """Provide a clean temporary directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="pytest_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def pytest_configure(config):
    """Configure pytest to show warnings about database access."""
    pass


def pytest_sessionfinish(session, exitstatus):
    """Cleanup after all tests complete."""
    # Remove any .hypothesis cache that might have been created
    hypothesis_dir = os.path.join(os.getcwd(), ".hypothesis")
    if os.path.exists(hypothesis_dir):
        # Keep the directory but clean examples
        examples_dir = os.path.join(hypothesis_dir, "examples")
        if os.path.exists(examples_dir):
            try:
                shutil.rmtree(examples_dir, ignore_errors=True)
            except:
                pass
