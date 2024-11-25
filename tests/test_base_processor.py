import pytest
from unittest.mock import Mock, patch
import logging
from src.base_processor import BaseProcessor, ProcessorCallback

def test_processor_callback_creation():
    # Test creazione callback con parametri None
    callback = ProcessorCallback()
    assert callback.message_callback is None
    assert callback.progress_callback is None

    # Test creazione callback con funzioni mock
    message_mock = Mock()
    progress_mock = Mock()
    callback = ProcessorCallback(message_mock, progress_mock)
    assert callback.message_callback == message_mock
    assert callback.progress_callback == progress_mock

def test_processor_callback_log_message():
    # Test logging con callback definito
    message_mock = Mock()
    callback = ProcessorCallback(message_callback=message_mock)
    callback.log_message("Test message")
    message_mock.assert_called_once_with("Test message")

    # Test logging senza callback (non dovrebbe sollevare eccezioni)
    callback = ProcessorCallback()
    callback.log_message("Test message")  # Non dovrebbe fare nulla

def test_processor_callback_update_progress():
    # Test progress con callback definito
    progress_mock = Mock()
    callback = ProcessorCallback(progress_callback=progress_mock)
    callback.update_progress(50.0, "Half done")
    progress_mock.assert_called_once_with({
        "value": 50.0,
        "status": "Half done"
    })

    # Test progress senza callback (non dovrebbe sollevare eccezioni)
    callback = ProcessorCallback()
    callback.update_progress(50.0, "Half done")  # Non dovrebbe fare nulla

def test_processor_callback_error_handling():
    # Test gestione errori nel message callback
    def failing_callback(msg):
        raise Exception("Test error")

    callback = ProcessorCallback(message_callback=failing_callback)
    with patch.object(logging, 'error') as mock_error:
        callback.log_message("Test")
        mock_error.assert_called_once()

    # Test gestione errori nel progress callback
    def failing_progress(progress):
        raise Exception("Test error")

    callback = ProcessorCallback(progress_callback=failing_progress)
    with patch.object(logging, 'error') as mock_error:
        callback.update_progress(50.0, "Test")
        mock_error.assert_called_once()

class TestProcessor(BaseProcessor):
    """Processor concreto per testing"""
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
