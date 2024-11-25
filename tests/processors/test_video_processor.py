import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.processors.video_processor import VideoProcessor

# Note: We don't test the video/audio processing methods directly as they heavily rely on MoviePy,
# which is difficult to mock reliably. These methods are tested manually through integration tests.

@pytest.fixture
def video_processor(tmp_path):
    """Creates a VideoProcessor instance with mocked config"""
    processor = VideoProcessor()
    mock_config = Mock()
    mock_config.OUTPUT_DIR = tmp_path / "output"
    mock_config.TEMP_DIR = tmp_path / "temp"
    mock_config.SPEECH_LANG = "it"

    for dir_path in [mock_config.OUTPUT_DIR, mock_config.TEMP_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

    processor.config = mock_config
    return processor

# Test only configuration and directory setup
def test_processor_initialization(video_processor):
    """Test that processor is correctly configured"""
    assert video_processor.config.TEMP_DIR.exists()
    assert video_processor.config.OUTPUT_DIR.exists()
    assert video_processor.config.SPEECH_LANG == "it"