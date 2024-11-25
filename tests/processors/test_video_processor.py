import pytest
from unittest.mock import Mock, patch, MagicMock
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
import os
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip
from src.processors.video_processor import VideoProcessor, VideoEffect

@pytest.fixture
def sample_script_content():
    return """<?xml version="1.0" encoding="UTF-8"?>
    <script version="1.0">
        <metadata>
            <title>Test Video</title>
            <url>https://example.com/test</url>
            <date>2024-01-01</date>
        </metadata>
        <content>
            <section level="1" type="intro">
                <heading>Introduction</heading>
                <speech pause="0.5">Welcome to the test video</speech>
            </section>
            <section level="2" type="content">
                <heading>First Section</heading>
                <speech pause="0.3">This is the first section</speech>
                <speech pause="0.5">With multiple speeches</speech>
            </section>
        </content>
    </script>"""

@pytest.fixture
def sample_script_file(tmp_path, sample_script_content):
    script_file = tmp_path / "test_script.xml"
    script_file.write_text(sample_script_content)
    return str(script_file)

@pytest.fixture
def video_processor(tmp_path):
    with patch('src.base_processor.Config') as mock_config:
        config = mock_config.return_value
        config.OUTPUT_DIR = tmp_path / "output"
        config.TEMP_DIR = tmp_path / "temp"
        config.VIDEO_WIDTH = 1920
        config.VIDEO_HEIGHT = 1080
        config.VIDEO_FPS = 24
        config.AUDIO_FPS = 44100
        config.BGCOLOR = "#000000"
        config.TEXT_COLOR = "#FFFFFF"
        config.FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        config.FONT_SIZES = {"h1": 70, "h2": 60, "text": 40}
        config.TEXT_LINE_SPACING = 1.2
        config.TEXT_MARGIN = 0.15
        config.SPEECH_LANG = "en"
        config.AUDIO_CODEC = "libmp3lame"
        config.VIDEO_CODEC = "libx264"

        processor = VideoProcessor()
        # Crea le directory necessarie
        for dir_path in [config.OUTPUT_DIR, config.TEMP_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        return processor

def test_video_effects():
    """Test degli effetti video"""
    mock_clip = MagicMock()
    mock_clip.duration = 5
    mock_clip.size = (1920, 1080)

    fade_clip = VideoEffect.fade(mock_clip)
    mock_clip.fadein.assert_called_once_with(0.5)
    mock_clip.fadein.return_value.fadeout.assert_called_once_with(0.5)

    slide_clip = VideoEffect.slide_left(mock_clip, 1920)
    assert callable(slide_clip.get_position())

    zoom_clip = VideoEffect.zoom_in(mock_clip)
    assert callable(zoom_clip.resize)

def test_parse_script(video_processor, sample_script_file):
    """Test del parsing dello script XML"""
    result = video_processor._parse_script(sample_script_file)

    assert 'metadata' in result
    assert result['metadata']['title'] == 'Test Video'
    assert result['metadata']['url'] == 'https://example.com/test'
    assert result['metadata']['date'] == '2024-01-01'

    assert 'content' in result
    assert len(result['content']) == 2
    assert result['content'][0]['type'] == 'intro'
    assert result['content'][1]['type'] == 'content'

@patch('PIL.ImageFont.truetype')
def test_create_slide(mock_font, video_processor, tmp_path):
    """Test della creazione delle slide"""
    output_path = tmp_path / "test_slide.png"
    test_text = "Test slide text"

    # Mock del font con getmask2
    font_mock = MagicMock()
    font_mock.getlength.return_value = 100
    font_mock.getmask2.return_value = (MagicMock(), (0, 0))
    mock_font.return_value = font_mock

    video_processor._create_slide(test_text, output_path, 1)

    assert output_path.exists()
    with Image.open(output_path) as img:
        assert img.size == (video_processor.config.VIDEO_WIDTH,
                          video_processor.config.VIDEO_HEIGHT)

@patch('moviepy.editor.AudioFileClip')
@patch('gtts.gTTS')
def test_create_audio(mock_gtts, mock_audio_clip, video_processor, tmp_path):
    """Test della creazione dell'audio"""
    output_path = tmp_path / "test_audio.mp3"
    test_text = "Test audio text"

    # Mock dell'oggetto gTTS
    mock_tts = Mock()
    mock_gtts.return_value = mock_tts

    # Mock completo dell'AudioClip
    mock_audio = Mock()
    mock_audio.duration = 2.0
    mock_audio.write_audiofile = Mock()
    mock_audio_clip.return_value = mock_audio

    video_processor._create_audio(test_text, output_path, 0.5)

    mock_gtts.assert_called_once_with(text=test_text, lang=video_processor.config.SPEECH_LANG)
    mock_tts.save.assert_called_once()

@patch('moviepy.editor.concatenate_videoclips')
def test_render_final_video(mock_concatenate, video_processor):
    """Test del rendering del video finale"""
    mock_clip1 = Mock(duration=2.0)
    mock_clip2 = Mock(duration=3.0)
    clips = [mock_clip1, mock_clip2]

    mock_final = Mock()
    mock_final.write_videofile = Mock()
    mock_concatenate.return_value = mock_final

    output_file = video_processor._render_final_video(clips, "Test Video")

    mock_concatenate.assert_called_once_with(clips, method="compose")
    assert isinstance(output_file, str)
    assert output_file.endswith('.mp4')

@patch('moviepy.editor.concatenate_videoclips')
def test_process_complete(mock_concatenate, video_processor, sample_script_file):
    """Test del processo completo di generazione video"""
    with patch('src.processors.video_processor.VideoProcessor._create_segment') as mock_create_segment:
        mock_segment = Mock(duration=2.5)
        mock_create_segment.return_value = mock_segment

        mock_final = Mock()
        mock_final.write_videofile = Mock()
        mock_concatenate.return_value = mock_final

        output_file = video_processor.process(sample_script_file)

        assert mock_create_segment.called
        assert isinstance(output_file, str)
        assert output_file.endswith('.mp4')

def test_cleanup(video_processor):
    """Test della pulizia dei file temporanei"""
    temp_dir = video_processor.config.TEMP_DIR

    # Crea alcuni file temporanei
    test_files = ["temp1.mp3", "temp2.png", "temp3.mp4"]
    for file in test_files:
        (temp_dir / file).touch()

    video_processor.cleanup()

    # Verifica che i file siano stati rimossi
    remaining_files = list(temp_dir.glob('*'))
    assert len(remaining_files) == 0

@patch('moviepy.editor.ImageClip')
@patch('moviepy.editor.AudioFileClip')
def test_create_segment(mock_audio_clip, mock_image_clip, video_processor):
    """Test della creazione di un segmento video"""
    section = {
        'level': 1,
        'type': 'content',
        'speeches': [
            {'text': 'First speech', 'pause': 0.5}
        ]
    }

    # Mock degli oggetti necessari
    mock_audio = Mock(duration=2.0)
    mock_audio.write_audiofile = Mock()
    mock_audio_clip.return_value = mock_audio

    mock_image = Mock()
    mock_image_clip.return_value = mock_image

    # Patch di metodi interni
    with patch.object(video_processor, '_create_slide'), \
         patch.object(video_processor, '_create_audio'):
        segment = video_processor._create_segment(section, 0)
        assert segment is not None

def test_error_handling(video_processor, tmp_path):
    """Test della gestione degli errori"""
    # Test con file script non esistente
    with pytest.raises(Exception):
        video_processor.process(str(tmp_path / "nonexistent.xml"))

    # Test con XML malformato
    invalid_script = tmp_path / "invalid.xml"
    invalid_script.write_text("Invalid XML content")

    with pytest.raises(Exception):
        video_processor.process(str(invalid_script))