from pathlib import Path
from typing import Dict, Any
import os
import logging
from dotenv import load_dotenv

class Config:
    """Singleton pattern per la gestione della configurazione"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Inizializza la configurazione dal file .env"""
        load_dotenv()

        # Directory paths - FIRST
        self.CONTENT_DIR = Path(os.getenv('CONTENT_DIR', './content'))
        self.SCRIPT_DIR = Path(os.getenv('SCRIPT_DIR', './video_scripts'))
        self.OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', './video_output'))

        # Directory interne a OUTPUT_DIR
        self.TEMP_DIR = self.OUTPUT_DIR / 'temp'
        self.ASSETS_DIR = self.OUTPUT_DIR / 'assets'

        # Log dei path - AFTER directories are initialized
        logging.info(f"=== Config Debug Info ===")
        logging.info(f"CONTENT_DIR from env: {os.getenv('CONTENT_DIR')}")
        logging.info(f"SCRIPT_DIR from env: {os.getenv('SCRIPT_DIR')}")
        logging.info(f"OUTPUT_DIR from env: {os.getenv('OUTPUT_DIR')}")
        logging.info(f"Resolved CONTENT_DIR: {self.CONTENT_DIR}")
        logging.info(f"Resolved SCRIPT_DIR: {self.SCRIPT_DIR}")
        logging.info(f"Resolved OUTPUT_DIR: {self.OUTPUT_DIR}")

        # Video settings
        self.VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', '1920'))
        self.VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', '1080'))
        self.VIDEO_FPS = int(os.getenv('VIDEO_FPS', '24'))
        self.VIDEO_BITRATE = os.getenv('VIDEO_BITRATE', '4000k')
        self.VIDEO_CODEC = os.getenv('VIDEO_CODEC', 'libx264')

        # Audio settings
        self.AUDIO_FPS = int(os.getenv('AUDIO_FPS', '44100'))
        self.AUDIO_NBYTES = int(os.getenv('AUDIO_NBYTES', '2'))
        self.AUDIO_CODEC = os.getenv('AUDIO_CODEC', 'libmp3lame')
        self.AUDIO_BITRATE = os.getenv('AUDIO_BITRATE', '192k')
        self.AUDIO_CHANNELS = int(os.getenv('AUDIO_CHANNELS', '2'))
        self.AUDIO_SAMPLE_FORMAT = os.getenv('AUDIO_SAMPLE_FORMAT', 's16le')

        # Styling
        self.BGCOLOR = os.getenv('VIDEO_BGCOLOR', '#291d38')
        self.TEXT_COLOR = os.getenv('VIDEO_TEXT_COLOR', '#ffffff')
        self.ACCENT_COLOR = os.getenv('VIDEO_ACCENT_COLOR', '#f22bb3')

        # Font settings
        self.FONT_PATH = os.getenv('FONT_PATH', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        self.FONT_SIZES = {
            'h1': int(os.getenv('FONT_SIZE_H1', '70')),
            'h2': int(os.getenv('FONT_SIZE_H2', '60')),
            'h3': int(os.getenv('FONT_SIZE_H3', '50')),
            'text': int(os.getenv('FONT_SIZE_TEXT', '40'))
        }

        # Text settings
        self.TEXT_LINE_SPACING = float(os.getenv('TEXT_LINE_SPACING', '1.2'))
        self.TEXT_MARGIN = float(os.getenv('TEXT_MARGIN', '0.15'))

        # Video content
        self.INTRO_TEXT = os.getenv('INTRO_TEXT', 'Ciao a tutti e bentornati sul canale!')
        self.OUTRO_TEXT = os.getenv('OUTRO_TEXT', 'Grazie per aver guardato questo video!')

        # Processing
        self.NUM_POSTS = int(os.getenv('NUM_POSTS', '5'))

        # Effects
        self.DEFAULT_EFFECT = os.getenv('DEFAULT_EFFECT', 'fade')
        self.TRANSITION_DURATION = float(os.getenv('TRANSITION_DURATION', '0.5'))
        self.PAUSE_DURATION = float(os.getenv('PAUSE_DURATION', '0.3'))

        # TTS Configuration
        self.APP_ENV = os.getenv('APP_ENV', 'dev')
        if self.APP_ENV == 'prod':
            self.TTS_PROVIDER = os.getenv('PROD_TTS_PROVIDER', 'azure')
            self.SPEECH_LANG = os.getenv('PROD_TTS_LANG', 'it-IT')

            # Azure specific settings
            self.AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
            self.AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION')
            self.AZURE_VOICE_NAME = os.getenv('AZURE_VOICE_NAME', 'it-IT-IsabellaNeural')
        else:
            self.TTS_PROVIDER = os.getenv('DEV_TTS_PROVIDER', 'gtts')
            self.SPEECH_LANG = os.getenv('DEV_TTS_LANG', 'it')

        self._create_directories()

    def _create_directories(self):
        """Crea le directory necessarie"""
        for dir_path in [self.CONTENT_DIR, self.SCRIPT_DIR, self.OUTPUT_DIR,
                        self.TEMP_DIR, self.ASSETS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @property
    def video_config(self) -> Dict[str, Any]:
        """Restituisce la configurazione specifica per il video"""
        return {
            'width': self.VIDEO_WIDTH,
            'height': self.VIDEO_HEIGHT,
            'fps': self.VIDEO_FPS,
            'bitrate': self.VIDEO_BITRATE
        }

    @property
    def style_config(self) -> Dict[str, Any]:
        """Restituisce la configurazione dello stile"""
        return {
            'bgcolor': self.BGCOLOR,
            'text_color': self.TEXT_COLOR,
            'accent_color': self.ACCENT_COLOR,
            'font_path': self.FONT_PATH,
            'font_sizes': self.FONT_SIZES,
            'line_spacing': self.TEXT_LINE_SPACING,
            'margin': self.TEXT_MARGIN
        }