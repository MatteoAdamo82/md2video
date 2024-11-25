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
    # Crea un mock di un clip video
    mock_clip = MagicMock()
    mock_clip.duration = 5
    mock_clip.size = (1920, 1080)

    # Test fade effect
    fade_clip = VideoEffect.fade(mock_clip)
    mock_clip.fadein.assert_called_once_with(0.5)
    mock_clip.fadein.return_value.fadeout.assert_called_once_with(0.5)

    # Test slide effect
    slide_clip = VideoEffect.slide_left(mock_clip, 1920)
    assert callable(slide_clip.get_position())

    # Test zoom effect
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

def test_create_slide(video_processor, tmp_path):
    """Test della creazione delle slide"""
    output_path = tmp_path / "test_slide.png"
    test_text = "Test slide text"

    with patch('PIL.ImageFont.truetype') as mock_font:
        # Mock del font per evitare problemi con il sistema
        mock_font.return_value = MagicMock()
        mock_font.return_value.getlength.return_value = 100

        video_processor._create_slide(test_text, output_path, 1)

        assert output_path.exists()
        # Verifica che l'immagine sia stata creata con le dimensioni corrette
        with Image.open(output_path) as img:
            assert img.size == (video_processor.config.VIDEO_WIDTH,
                              video_processor.config.VIDEO_HEIGHT)

@patch('moviepy.editor.AudioFileClip')
@patch('gtts.gTTS')
def test_create_audio(mock_gtts, mock_audio_clip, video_processor, tmp_path):
    output_path = tmp_path / "test_audio.mp3"
    test_text = "Test audio text"

    # Mock completo di gTTS
    mock_tts = Mock()
    mock_gtts.return_value = mock_tts

    # Mock completo dell'AudioClip
    mock_audio = Mock()
    mock_audio.duration = 2.0
    mock_audio_clip.return_value = mock_audio
    mock_audio.write_audiofile = Mock()  # Aggiungi mock per write_audiofile

    video_processor._create_audio(test_text, output_path, 0.5)

    mock_gtts.assert_called_once()
    mock_tts.save.assert_called_once()

    video_processor._create_audio(test_text, output_path, 0.5)

    mock_gtts.assert_called_once_with(text=test_text, lang=video_processor.config.SPEECH_LANG)
    mock_tts.save.assert_called_once()

@patch('moviepy.editor.concatenate_videoclips')
@patch('moviepy.editor.VideoFileClip')
def test_render_final_video(mock_video_clip, mock_concatenate, video_processor, tmp_path):
    """Test del rendering del video finale"""
    # Mock dei clip video
    mock_clip1 = Mock()
    mock_clip2 = Mock()
    clips = [mock_clip1, mock_clip2]

    # Mock del clip concatenato
    mock_final = Mock()
    mock_concatenate.return_value = mock_final

    output_file = video_processor._render_final_video(clips, "Test Video")

    mock_concatenate.assert_called_once_with(clips, method="compose")
    mock_final.write_videofile.assert_called_once()
    assert isinstance(output_file, str)
    assert output_file.endswith('.mp4')

@patch('src.processors.video_processor.VideoProcessor._create_segment')
def test_process_complete(mock_create_segment, video_processor, sample_script_file):
    """Test del processo completo di generazione video"""
    # Mock del segmento video
    mock_segment = Mock()
    mock_create_segment.return_value = mock_segment

    with patch('moviepy.editor.concatenate_videoclips') as mock_concatenate:
        # Mock del video finale
        mock_final = Mock()
        mock_concatenate.return_value = mock_final

        output_file = video_processor.process(sample_script_file)

        assert mock_create_segment.called
        assert mock_concatenate.called
        assert isinstance(output_file, str)
        assert output_file.endswith('.mp4')

def test_cleanup(video_processor, tmp_path):
    """Test della pulizia dei file temporanei"""
    # Crea alcuni file temporanei
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()

    test_files = ["temp1.mp3", "temp2.png", "temp3.mp4"]
    for file in test_files:
        (temp_dir / file).touch()

    with patch('src.processors.video_processor.Config') as mock_config:
        mock_config.return_value.TEMP_DIR = temp_dir
        video_processor.cleanup()

        # Verifica che i file siano stati rimossi
        remaining_files = list(temp_dir.glob('*'))
        assert len(remaining_files) == 0

def test_wrap_text(video_processor):
    """Test della funzione di wrapping del testo"""
    mock_font = MagicMock()
    mock_font.getlength.side_effect = lambda text: len(text) * 10  # Simula larghezza del testo

    text = "This is a long text that should be wrapped into multiple lines"
    max_width = 200  # Larghezza massima che dovrebbe contenere circa 20 caratteri

    lines = video_processor._wrap_text(text, mock_font, max_width)

    assert len(lines) > 1  # Il testo dovrebbe essere diviso in più linee
    for line in lines:
        # Verifica che ogni linea rispetti la larghezza massima
        assert mock_font.getlength(line) <= max_width

@patch('moviepy.editor.ImageClip')
@patch('moviepy.editor.AudioFileClip')
def test_create_segment(mock_audio_clip, mock_image_clip, video_processor):
    """Test della creazione di un segmento video"""
    section = {
        'level': 1,
        'type': 'content',
        'speeches': [
            {'text': 'First speech', 'pause': 0.5},
            {'text': 'Second speech', 'pause': 0.3}
        ]
    }

    # Mock dell'audio clip
    mock_audio = Mock()
    mock_audio.duration = 2.0
    mock_audio_clip.return_value = mock_audio

    # Mock dell'image clip
    mock_image = Mock()
    mock_image_clip.return_value = mock_image

    segment = video_processor._create_segment(section, 0)

    assert mock_audio_clip.called
    assert mock_image_clip.called
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
