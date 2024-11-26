from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import logging

class TTSProvider(ABC):
    """Base abstract class for TTS providers"""

    def __init__(self, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def synthesize(self, text: str, output_path: Path, language: str = 'it-IT') -> bool:
        """
        Synthesize speech from text and save to file

        Args:
            text: Text to synthesize
            output_path: Where to save the audio file
            language: Language code

        Returns:
            bool: True if successful, False otherwise
        """
        pass