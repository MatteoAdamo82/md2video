from enum import Enum
from typing import Optional, Dict, Any
import os
from dataclasses import dataclass
import logging
from .providers import TTSProvider, GttsTTSProvider, AzureTTSProvider

class TTSProviderType(Enum):
    """Enumeration of available TTS providers"""
    GTTS = "gtts"
    AZURE = "azure"

@dataclass
class TTSConfig:
    """Configuration for TTS providers"""
    provider_type: TTSProviderType
    config: Dict[str, Any]

class TTSConfiguration:
    """Configuration manager for TTS services"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._load_config()

    def _load_config(self):
        """Load TTS configuration based on environment"""
        self.environment = os.getenv('APP_ENV', 'dev').lower()
        self.logger.info(f"Loading TTS configuration for environment: {self.environment}")

        # Default configurations per environment
        self.configs = {
            'dev': {
                'default': TTSConfig(
                    provider_type=TTSProviderType(os.getenv('DEV_TTS_PROVIDER', 'gtts')),
                    config={}
                ),
                'fallback': TTSConfig(
                    provider_type=TTSProviderType.GTTS,
                    config={}
                )
            },
            'prod': {
                'default': TTSConfig(
                    provider_type=TTSProviderType(os.getenv('PROD_TTS_PROVIDER', 'azure')),
                    config={
                        'subscription_key': os.getenv('AZURE_SPEECH_KEY'),
                        'region': os.getenv('AZURE_SPEECH_REGION'),
                        'voice_name': os.getenv('AZURE_VOICE_NAME', 'it-IT-IsabellaNeural')
                    }
                ),
                'fallback': TTSConfig(
                    provider_type=TTSProviderType.GTTS,
                    config={}
                )
            },
            'test': {
                'default': TTSConfig(
                    provider_type=TTSProviderType.GTTS,
                    config={}
                ),
                'fallback': None  # No fallback in test environment
            }
        }

    def get_provider_config(self) -> TTSConfig:
        """Get the appropriate TTS configuration for current environment"""
        env_config = self.configs.get(self.environment, self.configs['dev'])
        provider_config = env_config['default']

        # Validate provider configuration
        if provider_config.provider_type == TTSProviderType.AZURE:
            if not all([
                provider_config.config.get('subscription_key'),
                provider_config.config.get('region')
            ]):
                self.logger.warning("Invalid Azure configuration, falling back to default provider")
                return env_config['fallback']

        self.logger.info(f"Using TTS provider: {provider_config.provider_type.value}")
        return provider_config

class EnhancedTTSFactory:
    """Enhanced factory for creating TTS providers"""

    _providers = {}  # Cache for provider instances
    logger = logging.getLogger("EnhancedTTSFactory")

    @classmethod
    def register_provider(cls, provider_type: TTSProviderType, provider_class: type):
        """Register a new provider class"""
        cls._providers[provider_type] = provider_class
        cls.logger.info(f"Registered TTS provider: {provider_type.value}")

    @classmethod
    def create_provider(cls, config: Optional[TTSConfig] = None) -> TTSProvider:
        """Create TTS provider based on configuration"""
        if config is None:
            config = TTSConfiguration().get_provider_config()

        provider_class = cls._providers.get(config.provider_type)
        if provider_class is None:
            raise ValueError(f"No provider registered for type {config.provider_type}")

        cls.logger.info(f"Creating TTS provider instance: {config.provider_type.value}")
        return provider_class(**config.config)

# Register available providers
EnhancedTTSFactory.register_provider(TTSProviderType.GTTS, GttsTTSProvider)
EnhancedTTSFactory.register_provider(TTSProviderType.AZURE, AzureTTSProvider)