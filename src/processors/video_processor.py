from typing import Dict, List
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
from pathlib import Path
import os
import xml.etree.ElementTree as ET
from ..base_processor import BaseProcessor
import logging
from ..tts import EnhancedTTSFactory

class VideoEffect:
    """Strategy pattern for video effects"""
    @staticmethod
    def fade(clip):
        return clip.fadein(0.5).fadeout(0.5)

    @staticmethod
    def slide_left(clip, width):
        duration = clip.duration

        def position_function(t):
            progress = t / duration
            if progress <= 0.5:
                x = width - (width * (progress * 2))
                return (x, 'center')
            else:
                return ('center', 'center')

        animated_clip = clip.set_position(position_function)

        return animated_clip.fadein(0.3)

    @staticmethod
    def zoom_in(clip):
        return clip.resize(lambda t: 1 + 0.5 * t)

    @staticmethod
    def rotate_cw(clip):
        return clip.rotate(lambda t: 360 * t)

    @staticmethod
    def zoom(clip):
        duration = clip.duration
        def zoom_function(t):
            progress = t / duration
            # Parte da 0.8x, arriva a 1.2x
            return 0.8 + (0.4 * progress)
        return clip.resize(zoom_function).fadein(0.3)

    @staticmethod
    def zoom_in(clip):
        return clip.resize(lambda t: 1 + 0.5 * t)

    @staticmethod
    def rotate_cw(clip):
        return clip.rotate(lambda t: 360 * t)

class VideoProcessor(BaseProcessor):
    """Video generation processor"""

    def __init__(self):
        super().__init__()
        # Initialize the TTS provider through the factory
        self.tts_provider = EnhancedTTSFactory.create_provider()
        self.effects = {
            'fade': VideoEffect.fade,
            'slide_left': lambda clip: VideoEffect.slide_left(clip, self.config.VIDEO_WIDTH),
            'zoom_in': VideoEffect.zoom_in,
            'rotate': VideoEffect.rotate_cw
        }

    def process(self, script_path: str) -> str:
        """Main video generation process"""
        try:
            sections = self._parse_script(script_path)
            metadata = sections['metadata']

            self.callback.log_message(f"Creating video for: {metadata['title']}")
            clips = []

            for i, section in enumerate(sections['content']):
                segment_clip = self._create_segment(section, i)
                if segment_clip:
                    clips.append(segment_clip)

            if not clips:
                raise ValueError("No valid clips generated")

            return self._render_final_video(clips, metadata['title'])

        except Exception as e:
            self.logger.error(f"Error creating video: {str(e)}")
            raise

    def _render_final_video(self, clips: List[VideoFileClip], title: str) -> str:
        """Render final video"""
        output_file = os.path.join(
            self.config.OUTPUT_DIR,
            f"video_{title[:30].replace(' ', '_')}.mp4"
        )

        self.logger.info(f"Creating video for: {title}")

        try:
            final_video = concatenate_videoclips(clips, method="compose")
            final_video.write_videofile(
                output_file,
                fps=self.config.VIDEO_FPS,
                codec='libx264',
                audio_codec='aac',
                bitrate="4000k"
            )

            self.logger.info(f"Video saved to: {output_file}")
            return output_file

        except Exception as e:
            self.logger.error(f"Error creating video: {str(e)}")
            raise
        finally:
            temp_dir = Path(self.config.TEMP_DIR)
            if temp_dir.exists():
                for file in temp_dir.glob('*'):
                    file.unlink()
                temp_dir.rmdir()

    def _parse_script(self, script_path: str) -> Dict:
        """XML script parser"""
        tree = ET.parse(script_path)
        root = tree.getroot()

        metadata = root.find("metadata")
        return {
            'metadata': {
                'title': metadata.find("title").text,
                'url': metadata.find("url").text,
                'date': metadata.find("date").text
            },
            'content': self._parse_sections(root.find("content"))
        }

    def _parse_sections(self, content: ET.Element) -> List[Dict]:
        """Extract sections from script"""
        sections = []
        for section in content.findall("section"):
            sections.append({
                'level': int(section.get("level")),
                'type': section.get("type"),
                'background': section.get("background"),  # Aggiungiamo questa riga
                'animation': section.get("animation"),    # Aggiungiamo questa riga
                'heading': section.find("heading").text if section.find("heading") is not None else "",
                'speeches': [{
                    'text': speech.text,
                    'pause': float(speech.get("pause", 0.5))
                } for speech in section.findall("speech")]
            })
        return sections

    def _create_segment(self, section: Dict, segment_number: int) -> VideoFileClip:
        """Create video segment for section"""
        temp_path = Path(self.config.TEMP_DIR)
        temp_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Using temp directory: {temp_path}")

        clips = []
        total_speeches = len(section['speeches'])
        for i, speech in enumerate(section['speeches']):
            self.callback.update_progress(
                (i * 100) // total_speeches,
                f"Processing segment {segment_number}, speech {i+1}/{total_speeches}"
            )

            image_path = temp_path / f'slide_{segment_number}_{i}.png'
            audio_path = temp_path / f'audio_{segment_number}_{i}.mp3'

            try:
                # Gestione dello sfondo personalizzato
                if section.get('background'):
                    bg_path = Path(self.config.ASSETS_DIR) / section['background']
                    if bg_path.exists():
                        # Creiamo una copia dello sfondo
                        background = Image.open(bg_path)
                        if background.size != (self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT):
                            background = background.resize((self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT))

                        # Aggiungiamo il testo sullo sfondo
                        draw = ImageDraw.Draw(background)
                        font_size = self.config.FONT_SIZES.get(
                            f'h{section["level"]}' if section["level"] in [1,2,3] else 'text'
                        )
                        font = ImageFont.truetype(self.config.FONT_PATH, font_size)

                        # Calcoliamo il layout del testo
                        margin = int(self.config.VIDEO_WIDTH * self.config.TEXT_MARGIN)
                        max_width = self.config.VIDEO_WIDTH - (2 * margin)
                        lines = self._wrap_text(speech['text'], font, max_width)

                        # Disegniamo il testo con ombra
                        y = (self.config.VIDEO_HEIGHT - (len(lines) * font_size * self.config.TEXT_LINE_SPACING)) / 2
                        for line in lines:
                            x = (self.config.VIDEO_WIDTH - font.getlength(line)) / 2
                            # Ombra
                            draw.text((x + 2, y + 2), line, font=font, fill='black')
                            # Testo principale
                            draw.text((x, y), line, font=font, fill=self.config.TEXT_COLOR)
                            y += font_size * self.config.TEXT_LINE_SPACING

                        background.save(image_path)
                    else:
                        self.logger.warning(f"Background image not found: {bg_path}, using default")
                        self._create_slide(speech['text'], image_path, section['level'])
                else:
                    self._create_slide(speech['text'], image_path, section['level'])

                self._create_audio(speech['text'], audio_path, speech['pause'])

                audio = AudioFileClip(str(audio_path))
                video = ImageClip(str(image_path)).set_duration(audio.duration)

                # Applicazione dell'animazione specificata
                animation = section.get('animation')
                if animation and animation in self.effects:
                    video = self.effects[animation](video)
                else:
                    video = self.effects['fade'](video)

                video = video.set_audio(audio)
                clips.append(video)

            except Exception as e:
                self.logger.error(f"Error processing speech {i}: {str(e)}")
                continue

        if clips:
            try:
                final = concatenate_videoclips(clips, method="compose")
                self.logger.info(f"Created final segment with {len(clips)} clips")
                return final
            except Exception as e:
                self.logger.error(f"Error concatenating clips: {str(e)}")
                return clips[0] if clips else None
        return None

    def _create_slide(self, text: str, output_path: Path, heading_level: int):
        """Crea una slide con testo"""
        # Create background
        image = self._create_background()
        draw = ImageDraw.Draw(image)

        # Configure font
        font_size = self.config.FONT_SIZES.get(
            f'h{heading_level}' if heading_level in [1,2,3] else 'text'
        )
        try:
            font = ImageFont.truetype(self.config.FONT_PATH, font_size)
        except:
            self.logger.warning(f"Could not load font {self.config.FONT_PATH}, using default")
            font = ImageFont.load_default()

        # Calculate text layout
        margin = int(self.config.VIDEO_WIDTH * self.config.TEXT_MARGIN)
        max_width = self.config.VIDEO_WIDTH - (2 * margin)
        lines = self._wrap_text(text, font, max_width)

        # Draw text
        y = (self.config.VIDEO_HEIGHT - (len(lines) * font_size * self.config.TEXT_LINE_SPACING)) / 2

        for line in lines:
            x = (self.config.VIDEO_WIDTH - font.getlength(line)) / 2
            draw.text((x, y), line, font=font, fill=self.config.TEXT_COLOR)
            y += font_size * self.config.TEXT_LINE_SPACING

        image.save(output_path)

    def _create_audio(self, text: str, output_path: Path, pause: float):
            """Crea l'audio da testo"""
            try:
                # Temporary dir for audio files
                temp_path = str(output_path).replace('.mp3', '_temp.mp3')

                # Generate audio using the configured TTS provider
                success = self.tts_provider.synthesize(
                    text=text,
                    output_path=Path(temp_path),
                    language=self.config.SPEECH_LANG
                )

                if not success:
                    self.logger.error("TTS synthesis failed")
                    raise Exception("Speech synthesis failed")

                # Run generated audio
                audio = AudioFileClip(temp_path)

                if pause > 0:
                    # Create silence
                    silence = AudioClip(
                        lambda t: 0,
                        duration=pause
                    ).set_fps(self.config.AUDIO_FPS)

                    # Combine audio and silence
                    final_audio = CompositeAudioClip([
                        audio,
                        silence.set_start(audio.duration)
                    ])

                    # Get the total expected duration
                    expected_duration = audio.duration + pause

                    # Salve final audio
                    final_audio.write_audiofile(
                        str(output_path),
                        fps=self.config.AUDIO_FPS,
                        codec=self.config.AUDIO_CODEC,
                        bitrate=self.config.AUDIO_BITRATE,
                        write_logfile=False,
                        verbose=False
                    )

                    # Check the final duration
                    check_audio = AudioFileClip(str(output_path))
                    if abs(check_audio.duration - expected_duration) > 0.01:
                        self.logger.warning(
                            f"Audio duration mismatch. Expected: {expected_duration:.2f}s, "
                            f"Got: {check_audio.duration:.2f}s"
                        )
                    check_audio.close()

                else:
                    # If there is no pause, use the original audio directly
                    os.rename(temp_path, str(output_path))

            except Exception as e:
                self.logger.error(f"Error creating audio: {str(e)}")
                raise

            finally:
                # Clean
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass

                # Close audio clips
                if 'audio' in locals():
                    audio.close()
                if 'silence' in locals():
                    silence.close()
                if 'final_audio' in locals():
                    final_audio.close()

    def _create_background(self) -> Image:
        """Create the background for the slides"""
        image = Image.new('RGB', (self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT))
        draw = ImageDraw.Draw(image)

        ## Convert hex color to RGB
        bg_color = tuple(int(self.config.BGCOLOR[i:i+2], 16) for i in (1, 3, 5))

        # Create vertical gradient
        for y in range(self.config.VIDEO_HEIGHT):
            factor = 1 - y/self.config.VIDEO_HEIGHT * 0.2
            color = tuple(int(c * factor) for c in bg_color)
            draw.line([(0, y), (self.config.VIDEO_WIDTH, y)], fill=color)

        return image

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Divides text into lines that fit the maximum width"""
        words = text.split()
        lines = []
        current_line = []
        current_width = 0

        for word in words:
            word_width = font.getlength(word + " ")
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def cleanup(self):
        """Cleans temporary files"""
        temp_dir = Path(self.config.TEMP_DIR)
        if temp_dir.exists():
            for file in temp_dir.glob('*'):
                try:
                    file.unlink()
                except Exception as e:
                    self.logger.error(f"Error deleting temporary file {file}: {str(e)}")
