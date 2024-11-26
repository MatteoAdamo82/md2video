import pytest
from unittest.mock import Mock, patch
import logging
from src.base_processor import BaseProcessor, ProcessorCallback

def test_processor_callback_creation():
    # Test creating callback with None parameters
    callback = ProcessorCallback()
    assert callback.message_callback is None
    assert callback.progress_callback is None

    # Test creating callbacks with mock functions
    message_mock = Mock()
    progress_mock = Mock()
    callback = ProcessorCallback(message_mock, progress_mock)
    assert callback.message_callback == message_mock
    assert callback.progress_callback == progress_mock

def test_processor_callback_log_message():
    # Test logging with defined callback
    message_mock = Mock()
    callback = ProcessorCallback(message_callback=message_mock)
    callback.log_message("Test message")
    message_mock.assert_called_once_with("Test message")

    # Test logging without callback (should not throw exceptions)
    callback = ProcessorCallback()
    callback.log_message("Test message")

def test_processor_callback_update_progress():
    # Test progress with callback defined
    progress_mock = Mock()
    callback = ProcessorCallback(progress_callback=progress_mock)
    callback.update_progress(50.0, "Half done")
    progress_mock.assert_called_once_with({
        "value": 50.0,
        "status": "Half done"
    })

    # Test progress without callback (should not throw exceptions)
    callback = ProcessorCallback()
    callback.update_progress(50.0, "Half done")

def test_processor_callback_error_handling():
    # Test error handling in message callback
    def failing_callback(msg):
        raise Exception("Test error")

    callback = ProcessorCallback(message_callback=failing_callback)
    with patch.object(logging, 'error') as mock_error:
        callback.log_message("Test")
        mock_error.assert_called_once()

    # Test error handling in progress callback
    def failing_progress(progress):
        raise Exception("Test error")

    callback = ProcessorCallback(progress_callback=failing_progress)
    with patch.object(logging, 'error') as mock_error:
        callback.update_progress(50.0, "Test")
        mock_error.assert_called_once()

class TestProcessor(BaseProcessor):
    """Concrete processor for testing"""
    def process(self, *args, **kwargs):
        return "processed"

def test_base_processor_initialization():
    processor = TestProcessor()
    assert processor.logger is not None
    assert processor.callback is not None
    assert isinstance(processor.callback, ProcessorCallback)

def test_base_processor_set_callbacks():
    processor = TestProcessor()
    message_mock = Mock()
    progress_mock = Mock()

    processor.set_callbacks(message_mock, progress_mock)
    assert processor.callback.message_callback == message_mock
    assert processor.callback.progress_callback == progress_mock

def test_base_processor_context_manager():
    with TestProcessor() as processor:
        assert isinstance(processor, TestProcessor)
        result = processor.process()
        assert result == "processed"

@pytest.fixture
def processor():
    return TestProcessor()
