import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from pathlib import Path
import numpy as np
import os
from src.processors.video_processor import VideoProcessor
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip

@pytest.fixture
def video_processor(tmp_path):
    """Creates a VideoProcessor instance with mocked config"""
    processor = VideoProcessor()

    # Crea una configurazione di test
    mock_config = Mock()
    mock_config.OUTPUT_DIR = tmp_path / "output"
    mock_config.TEMP_DIR = tmp_path / "temp"
    mock_config.VIDEO_WIDTH = 1920
    mock_config.VIDEO_HEIGHT = 1080
    mock_config.VIDEO_FPS = 24
    mock_config.AUDIO_FPS = 44100
    mock_config.BGCOLOR = "#000000"
    mock_config.TEXT_COLOR = "#FFFFFF"
    mock_config.FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    mock_config.FONT_SIZES = {"h1": 70, "h2": 60, "text": 40}
    mock_config.TEXT_LINE_SPACING = 1.2
    mock_config.TEXT_MARGIN = 0.15
    mock_config.SPEECH_LANG = "it"
    mock_config.VIDEO_CODEC = "libx264"
    mock_config.VIDEO_BITRATE = "4000k"
    mock_config.AUDIO_CODEC = "libmp3lame"
    mock_config.AUDIO_BITRATE = "192k"

    # Assicurati che le directory esistano
    for dir_path in [mock_config.OUTPUT_DIR, mock_config.TEMP_DIR]:
        if dir_path.exists():
            for file in dir_path.glob('*'):
                file.unlink()
        dir_path.mkdir(parents=True, exist_ok=True)

    processor.config = mock_config
    return processor

@pytest.fixture
def mock_audio():
    """Creates a properly configured audio mock"""
    audio = MagicMock()
    type(audio).duration = PropertyMock(return_value=2.0)
    type(audio).fps = PropertyMock(return_value=44100)
    type(audio).nchannels = PropertyMock(return_value=2)
    return audio

@pytest.fixture
def mock_videoclip(mock_audio):
    """Creates a properly configured video mock"""
    clip = MagicMock()
    # Imposta attributi base
    type(clip).fps = PropertyMock(return_value=24)
    type(clip).duration = PropertyMock(return_value=2.0)
    type(clip).end = PropertyMock(return_value=2.0)
    type(clip).size = PropertyMock(return_value=(1920, 1080))
    type(clip).nchannels = PropertyMock(return_value=2)
    type(clip).mask = PropertyMock(return_value=None)

    # Imposta dati frame
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    clip.get_frame.return_value = frame
    clip.blit_on.return_value = frame
    clip.astype.return_value = frame

    # Imposta audio e metodi
    type(clip).audio = PropertyMock(return_value=mock_audio)
    clip.set_duration.return_value = clip
    clip.set_position.return_value = clip
    clip.set_start.return_value = clip

    return clip

@pytest.fixture
def sample_script_content():
    return """<?xml version="1.0" encoding="UTF-8"?>
    <script version="1.0">
        <metadata>
            <title>Video di Test</title>
            <url>https://example.com/test</url>
            <date>2024-01-01</date>
        </metadata>
        <content>
            <section level="1" type="intro">
                <heading>Introduzione</heading>
                <speech pause="0.5">Questo è un test</speech>
            </section>
        </content>
    </script>"""

@pytest.fixture
def sample_script_file(tmp_path, sample_script_content):
    script_path = tmp_path / "test_script.xml"
    script_path.write_text(sample_script_content)
    return script_path


# Fix per test_create_audio
@patch('src.processors.video_processor.gTTS')  # Cambiato il path del patch
def test_create_audio(mock_gtts, video_processor, tmp_path):
    """Test della creazione dell'audio"""
    output_path = tmp_path / "test_audio.mp3"
    test_text = "Test audio text"

    mock_tts = MagicMock()
    mock_gtts.return_value = mock_tts

    with patch('moviepy.editor.AudioFileClip') as mock_audio_clip, \
         patch('moviepy.audio.io.readers.FFMPEG_AudioReader'), \
         patch('moviepy.video.io.ffmpeg_reader.ffmpeg_parse_infos') as mock_parse:

        mock_audio = MagicMock()
        type(mock_audio).duration = PropertyMock(return_value=2.0)
        type(mock_audio).fps = PropertyMock(return_value=44100)
        mock_audio_clip.return_value = mock_audio

        # Crea un file finto che MoviePy possa leggere
        output_path.write_bytes(b'RIFF' + b'\x00' * 100)

        mock_parse.return_value = {
            'duration': 2.0,
            'audio_fps': 44100,
            'audio_found': True
        }

        # Crea l'audio
        with patch('moviepy.video.io.ffmpeg_writer.FFMPEG_VideoWriter'), \
             patch('moviepy.audio.io.ffmpeg_audiowriter.FFMPEG_AudioWriter'), \
             patch('moviepy.config_defaults.FFMPEG_BINARY'): # Mock ffmpeg binary
            video_processor._create_audio(test_text, output_path, 0.5)

            mock_gtts.assert_called_once_with(
                text=test_text,
                lang=video_processor.config.SPEECH_LANG
            )
            mock_tts.save.assert_called_once()

# Fix per test_render_final_video
@patch('moviepy.video.compositing.CompositeVideoClip.CompositeVideoClip')
@patch('moviepy.editor.concatenate_videoclips')
def test_render_final_video(mock_concatenate, mock_composite, video_processor, mock_videoclip):
    # Configura l'audio del video clip mock per evitare errori di comparazione
    mock_audio = MagicMock()
    type(mock_audio).nchannels = PropertyMock(return_value=2)  # valore fisso per confronto
    type(mock_videoclip).audio = PropertyMock(return_value=mock_audio)
    type(mock_videoclip).mask = PropertyMock(return_value=None)  # evita errori con mask

    # Mock per il video composito finale
    mock_final = MagicMock()
    type(mock_final).duration = PropertyMock(return_value=5.0)
    type(mock_final).audio = PropertyMock(return_value=mock_audio)
    mock_concatenate.return_value = mock_final
    mock_composite.return_value = mock_final

    # Mock i writer di ffmpeg
    with patch('moviepy.video.io.ffmpeg_writer.FFMPEG_VideoWriter'), \
         patch('moviepy.audio.io.ffmpeg_audiowriter.FFMPEG_AudioWriter'), \
         patch('moviepy.config_defaults.FFMPEG_BINARY'):
        output_file = video_processor._render_final_video([mock_videoclip], "Test Video")
        assert output_file.endswith('.mp4')
        assert mock_concatenate.called

# Fix per test_create_segment
@patch('moviepy.editor.ImageClip')
@patch('moviepy.editor.AudioFileClip')
def test_create_segment(mock_audio_clip, mock_image_clip, video_processor, mock_videoclip, mock_audio):
    section = {
        'level': 1,
        'type': 'content',
        'speeches': [
            {'text': 'First speech', 'pause': 0.5}
        ]
    }

    # Configura correttamente i mock per audio e immagine
    mock_audio_clip.return_value = mock_audio
    mock_image_clip.return_value = mock_videoclip

    with patch.object(video_processor, '_create_slide') as mock_create_slide, \
         patch.object(video_processor, '_create_audio') as mock_create_audio, \
         patch('moviepy.video.io.ffmpeg_reader.ffmpeg_parse_infos') as mock_parse, \
         patch('moviepy.video.io.ffmpeg_writer.FFMPEG_VideoWriter'), \
         patch('moviepy.audio.io.ffmpeg_audiowriter.FFMPEG_AudioWriter'):

        # Prepara i file di mock
        temp_dir = video_processor.config.TEMP_DIR
        temp_dir.mkdir(parents=True, exist_ok=True)

        audio_path = temp_dir / "audio_0_0.mp3"
        slide_path = temp_dir / "slide_0_0.png"

        # Crea file finti con header minimi
        audio_path.write_bytes(b'RIFF' + b'\x00' * 100)
        slide_path.write_bytes(b'PNG\r\n\x1a\n' + b'\x00' * 100)

        # Configura i mock
        mock_create_audio.return_value = str(audio_path)
        mock_create_slide.return_value = str(slide_path)
        mock_parse.return_value = {
            'duration': 2.0,
            'audio_fps': 44100,
            'audio_found': True
        }

        # Esegui il test
        segment = video_processor._create_segment(section, 0)
        assert segment is not None
        assert mock_create_audio.called
        assert mock_create_slide.called