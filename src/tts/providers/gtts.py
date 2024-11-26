from pathlib import Path
from gtts import gTTS
from .base import TTSProvider

class GttsTTSProvider(TTSProvider):
    """Google TTS implementation"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def synthesize(self, text: str, output_path: Path, language: str = 'it-IT') -> bool:
        try:
            # Convert language code format if needed
            lang = language.split('-')[0]  # Convert 'it-IT' to 'it'

            self.logger.info(f"Synthesizing text with GTTS (lang: {lang})")
            tts = gTTS(text=text, lang=lang)
            tts.save(str(output_path))

            return True

        except Exception as e:
            self.logger.error(f"Error in GTTS synthesis: {str(e)}")
            return False