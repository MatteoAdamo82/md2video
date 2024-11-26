from pathlib import Path
import azure.cognitiveservices.speech as speechsdk
from .base import TTSProvider

class AzureTTSProvider(TTSProvider):
    """Azure Speech Services implementation"""

    def __init__(self, subscription_key: str, region: str,
                 voice_name: str = 'it-IT-IsabellaNeural', **kwargs):
        super().__init__(**kwargs)
        self.subscription_key = subscription_key
        self.region = region
        self.voice_name = voice_name

    def synthesize(self, text: str, output_path: Path, language: str = 'it-IT') -> bool:
        try:
            self.logger.info(f"Synthesizing text with Azure (voice: {self.voice_name})")

            # Configure speech service
            speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key,
                region=self.region
            )

            # Set speech synthesis voice
            speech_config.speech_synthesis_voice_name = self.voice_name

            # Configure audio output
            audio_config = speechsdk.AudioConfig(filename=str(output_path))

            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config
            )

            # Perform synthesis
            result = synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                self.logger.info("Azure synthesis completed successfully")
                return True
            else:
                self.logger.error(
                    f"Azure synthesis failed: {result.reason} {result.error_details}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error in Azure synthesis: {str(e)}")
            return False