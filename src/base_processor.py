from abc import ABC, abstractmethod
import logging
from typing import Optional, Callable
from .config import Config

class ProcessorCallback:
    def __init__(self, message_callback: Optional[Callable] = None,
                 progress_callback: Optional[Callable] = None):
        self.message_callback = message_callback
        self.progress_callback = progress_callback

    def log_message(self, message: str):
        """Log a message using the callback if available"""
        if self.message_callback:
            try:
                self.message_callback(message)
            except Exception as e:
                logging.error(f"Error in message callback: {str(e)}")

    def update_progress(self, progress: float, status: str):
        """Update progress using the callback if available"""
        if self.progress_callback:
            try:
                self.progress_callback({
                    "value": progress,
                    "status": status
                })
            except Exception as e:
                logging.error(f"Error in progress callback: {str(e)}")

class BaseProcessor(ABC):
    """Base class for all processors implementing Template Method pattern"""
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.callback = ProcessorCallback()

    def set_callbacks(self, message_callback: Optional[Callable] = None,
                     progress_callback: Optional[Callable] = None):
        """Set the callbacks for message and progress updates"""
        self.callback = ProcessorCallback(message_callback, progress_callback)

    @abstractmethod
    def process(self, *args, **kwargs):
        """Template method to be implemented by concrete processors"""
        pass

    def cleanup(self):
        """Template method for cleanup operations"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()