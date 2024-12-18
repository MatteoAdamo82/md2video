import pytest
from unittest.mock import Mock, patch
from src.video_generator import VideoGenerator

@pytest.fixture
def video_generator():
    return VideoGenerator()

@pytest.fixture
def sample_post():
    return {
        'title': 'Test Post',
        'url': 'https://example.com/test',
        'content': 'Test content',
        'date': '2024-01-01'
    }

def test_video_generator_initialization():
    """Testing VideoGenerator Initialization"""
    generator = VideoGenerator()
    assert generator.blog_processor is not None
    assert generator.script_processor is not None
    assert generator.video_processor is not None

def test_set_callbacks():
    """Testing the callback setting"""
    generator = VideoGenerator()
    message_mock = Mock()
    progress_mock = Mock()

    generator.set_callbacks(message_mock, progress_mock)

    # Verify that callbacks have been set for all processors
    assert generator.blog_processor.callback.message_callback == message_mock
    assert generator.blog_processor.callback.progress_callback == progress_mock
    assert generator.script_processor.callback.message_callback == message_mock
    assert generator.script_processor.callback.progress_callback == progress_mock
    assert generator.video_processor.callback.message_callback == message_mock
    assert generator.video_processor.callback.progress_callback == progress_mock

@patch('src.processors.blog_processor.BlogProcessor.process')
@patch('src.processors.script_processor.ScriptProcessor.process')
def test_generate_scripts(mock_script_process, mock_blog_process, video_generator):
    """Test della generazione degli script"""
    # Blog Processor Results Mock
    mock_blog_process.return_value = [{'title': 'Post 1', 'url': 'http://example.com/1'}]

    # Mock of the script processor results
    mock_script_process.return_value = ('script1.xml', '<xml>content</xml>')

    results = video_generator.generate_scripts(num_posts=1)

    assert len(results) == 1
    assert results[0]['title'] == 'Post 1'
    assert results[0]['script_file'] == 'script1.xml'
    assert results[0]['url'] == 'http://example.com/1'

def test_generate_scripts_with_error(video_generator):
    """Testing error handling during script generation"""
    with patch('src.processors.blog_processor.BlogProcessor.process') as mock_blog_process:
        mock_blog_process.side_effect = Exception("Blog processing error")

        with pytest.raises(Exception) as exc_info:
            video_generator.generate_scripts()

        assert "Error generating scripts" in str(exc_info.value)

@patch('src.processors.video_processor.VideoProcessor.process')
def test_generate_video(mock_video_process, video_generator):
    """Video Generation Test"""
    mock_video_process.return_value = 'output.mp4'

    result = video_generator.generate_video('script.xml')

    assert result == 'output.mp4'
    mock_video_process.assert_called_once_with('script.xml')

def test_generate_video_with_error(video_generator):
    """Testing error handling during video generation"""
    with patch('src.processors.video_processor.VideoProcessor.process') as mock_video_process:
        mock_video_process.side_effect = Exception("Video processing error")

        with pytest.raises(Exception) as exc_info:
            video_generator.generate_video('script.xml')

        assert "Error generating video" in str(exc_info.value)

@patch('src.video_generator.VideoGenerator.generate_scripts')
@patch('src.video_generator.VideoGenerator.generate_video')
def test_process_recent_posts(mock_generate_video, mock_generate_scripts, video_generator):
    """Testing the complete generation process"""
    # Mock dei risultati degli script
    mock_generate_scripts.return_value = [
        {
            'title': 'Post 1',
            'script_file': 'script1.xml',
            'url': 'http://example.com/1'
        }
    ]

    # Mock del risultato del video
    mock_generate_video.return_value = 'video1.mp4'

    results = video_generator.process_recent_posts(num_posts=1)

    assert len(results) == 1
    assert results[0]['title'] == 'Post 1'
    assert results[0]['script_file'] == 'script1.xml'
    assert results[0]['video_file'] == 'video1.mp4'
    assert results[0]['url'] == 'http://example.com/1'

def test_process_recent_posts_with_script_error(video_generator):
    """Testing error handling during script generation in the complete process"""
    with patch('src.video_generator.VideoGenerator.generate_scripts') as mock_generate_scripts:
        mock_generate_scripts.side_effect = Exception("Script generation error")

        with pytest.raises(Exception) as exc_info:
            video_generator.process_recent_posts()

        assert "Error processing posts" in str(exc_info.value)

def test_process_recent_posts_with_video_error(video_generator):
    """Testing error handling during video generation in the complete process"""
    with patch('src.video_generator.VideoGenerator.generate_scripts') as mock_generate_scripts:
        mock_generate_scripts.return_value = [
            {
                'title': 'Post 1',
                'script_file': 'script1.xml',
                'url': 'http://example.com/1'
            }
        ]

        with patch('src.video_generator.VideoGenerator.generate_video') as mock_generate_video:
            mock_generate_video.side_effect = Exception("Video generation error")

            with pytest.raises(Exception) as exc_info:
                video_generator.process_recent_posts()

            assert "Error processing posts" in str(exc_info.value)

def test_process_recent_posts_empty_result(video_generator):
    """Test del processo completo quando non ci sono post da processare"""
    with patch('src.video_generator.VideoGenerator.generate_scripts') as mock_generate_scripts:
        mock_generate_scripts.return_value = []

        results = video_generator.process_recent_posts()
        assert results == []

def test_cleanup(video_generator):
    """Resource Cleanup Test"""
    # Mock of processors
    video_generator.blog_processor.cleanup = Mock()
    video_generator.script_processor.cleanup = Mock()
    video_generator.video_processor.cleanup = Mock()

    video_generator.cleanup()

    # Verify that cleanup has been called for all processors
    video_generator.blog_processor.cleanup.assert_called_once()
    video_generator.script_processor.cleanup.assert_called_once()
    video_generator.video_processor.cleanup.assert_called_once()

def test_cleanup_with_error(video_generator):
    """Testing error handling during cleanup"""
    video_generator.blog_processor.cleanup = Mock(side_effect=Exception("Cleanup error"))
    video_generator.script_processor.cleanup = Mock()
    video_generator.video_processor.cleanup = Mock()

    # Cleanup should not propagate the error
    video_generator.cleanup()

    # Verify that all cleanups were called despite the error
    video_generator.blog_processor.cleanup.assert_called_once()
    video_generator.script_processor.cleanup.assert_called_once()
    video_generator.video_processor.cleanup.assert_called_once()

@patch('src.processors.blog_processor.BlogProcessor.process')
def test_generate_scripts_with_custom_num_posts(mock_blog_process, video_generator):
    """Testing script generation with custom number of posts"""
    mock_blog_process.return_value = []

    video_generator.generate_scripts(num_posts=5)
    mock_blog_process.assert_called_once_with(5)

@patch('src.video_generator.VideoGenerator.generate_scripts')
def test_process_recent_posts_with_custom_num_posts(mock_generate_scripts, video_generator):
    """TFull process test with custom number of posts"""
    mock_generate_scripts.return_value = []

    video_generator.process_recent_posts(num_posts=5)
    mock_generate_scripts.assert_called_once_with(5)
