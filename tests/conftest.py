import pytest
from pathlib import Path
import os
import sys

# Aggiungi la directory src al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(scope="session")
def test_dir():
    """Directory base per i file temporanei dei test"""
    return Path(__file__).parent / "test_files"

@pytest.fixture(autouse=True)
def setup_test_env(test_dir):
    """Setup dell'ambiente di test"""
    # Crea directory temporanea per i test
    test_dir.mkdir(exist_ok=True)

    # Setup variabili d'ambiente per i test
    os.environ['CONTENT_DIR'] = str(test_dir / 'content')
    os.environ['SCRIPT_DIR'] = str(test_dir / 'scripts')
    os.environ['OUTPUT_DIR'] = str(test_dir / 'output')

    yield

    # Cleanup dopo i test
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)
