import pytest
from pathlib import Path
import os
import sys

# Add the src directory to the PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(scope="session")
def test_dir():
    """Base directory for temporary test files"""
    return Path(__file__).parent / "test_files"

@pytest.fixture(autouse=True)
def setup_test_env(test_dir):
    """Test Environment Setup"""
    # Create temporary directory for tests
    test_dir.mkdir(exist_ok=True)

    # Setup environment variables for testing
    os.environ['CONTENT_DIR'] = str(test_dir / 'content')
    os.environ['SCRIPT_DIR'] = str(test_dir / 'scripts')
    os.environ['OUTPUT_DIR'] = str(test_dir / 'output')

    yield

    # Cleanup after testing
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)
