from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import *
import logging
from dotenv import load_dotenv
from .script_generator import ScriptParser
import time

class VideoMaker:
    def __init__(self, output_dir: str = 'video_output'):
        load_dotenv()
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Slide settings
        self.width = int(os.getenv('VIDEO_WIDTH', '1920'))
        self.height = int(os.getenv('VIDEO_HEIGHT', '1080'))
        self.background_color = os.getenv('VIDEO_BGCOLOR', '#291d38')
        self.text_color = os.getenv('VIDEO_TEXT_COLOR', '#ffffff')
        self.accent_color = os.getenv('VIDEO_ACCENT_COLOR', '#f22bb3')

        # Font settings
        self.font_path = os.getenv('VIDEO_FONT_PATH', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        self.heading_sizes = {
            1: int(os.getenv('VIDEO_H1_FONT_SIZE', '70')),
            2: int(os.getenv('VIDEO_H2_FONT_SIZE', '60')),
            3: int(os.getenv('VIDEO_H3_FONT_SIZE', '50')),
            0: int(os.getenv('VIDEO_TEXT_FONT_SIZE', '40'))
        }

        # Layout settings
        self.margin = int(self.width * 0.15)
        self.line_spacing = 1.2
        self.max_text_width = int(self.width * 0.7)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def create_gradient_background(self) -> Image:
        """Crea uno sfondo con gradiente"""
        image = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        def hex_to_rgb(hex_color):
            return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

        bg_color = hex_to_rgb(self.background_color)

        for y in range(self.height):
            factor = 1 - y/self.height * 0.2
            color = tuple(int(c * factor) for c in bg_color)
            draw.line([(0, y), (self.width, y)], fill=color)

        return image

    def get_wrapped_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
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

    def create_slide(self, text: str, filename: str, heading_level: int = 0) -> str:
        try:
            image = self.create_gradient_background()
            try:
                font_size = self.heading_sizes.get(heading_level, self.heading_sizes[0])
                font = ImageFont.truetype(self.font_path, font_size)
            except:
                self.logger.warning(f"Could not load font {self.font_path}, using default")
                font = ImageFont.load_default()

            draw = ImageDraw.Draw(image)
            max_width = self.width - (self.margin * 2)
            text_lines = self.get_wrapped_text(text, font, max_width)
            line_height = font_size * self.line_spacing
            total_text_height = len(text_lines) * line_height

            max_lines = int((self.height - (self.margin * 2)) / line_height)
            if len(text_lines) > max_lines:
                text_lines = text_lines[:max_lines-1]
                text_lines.append("...")
                total_text_height = len(text_lines) * line_height

            y = (self.height - total_text_height) / 2

            for line in text_lines:
                line_width = font.getlength(line)
                x = (self.width - line_width) / 2

                if heading_level in [1, 2, 3]:
                    shadow_offset = 2
                    draw.text((x + shadow_offset, y + shadow_offset), line,
                            font=font, fill='#000000', alpha=100)

                draw.text((x, y), line, font=font, fill=self.text_color)
                y += line_height

            image.save(filename, quality=95)
            return filename

        except Exception as e:
            self.logger.error(f"Error creating slide: {str(e)}")
            raise

    def text_to_speech(self, text: str, filename: str, pause: float = 0.5, lang='it') -> str:
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            temp_speech = filename.replace('.mp3', '_temp.mp3')
            tts.save(temp_speech)

            # Aggiungi pausa alla fine dell'audio
            if pause > 0:
                speech_audio = AudioFileClip(temp_speech)
                silence = AudioClip(lambda t: 0, duration=pause)  # Crea silenzio di durata specificata
                final_audio = concatenate_audioclips([speech_audio, silence])
                final_audio.write_audiofile(filename)

                # Pulisci il file temporaneo
                os.remove(temp_speech)

            return filename
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {str(e)}")
            raise

    def create_video_segment(self, section: dict, segment_number: int) -> VideoFileClip:
        temp_dir = Path(self.output_dir) / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            image_file = str(temp_dir / f'slide_{segment_number}.png')

            # Crea la slide con l'heading o con il primo speech se non c'è heading
            if section['heading']:
                display_text = section['heading']
            elif section['speeches']:
                display_text = section['speeches'][0]['text']
            else:
                display_text = ""

            self.create_slide(display_text, image_file, section['level'])

            clips = []
            for i, speech in enumerate(section['speeches']):
                audio_file = str(temp_dir / f'audio_{segment_number}_{i}.mp3')
                self.text_to_speech(speech['text'], audio_file, speech['pause'])

                audio = AudioFileClip(audio_file)
                video = (ImageClip(image_file)
                        .set_duration(audio.duration)
                        .fadein(0.5)
                        .fadeout(0.5))

                clips.append(video.set_audio(audio))

            return concatenate_videoclips(clips, method="compose") if clips else None

        except Exception as e:
            self.logger.error(f"Error creating video segment: {str(e)}")
            raise

        except Exception as e:
            self.logger.error(f"Error creating video segment: {str(e)}")
            raise

    def create_video(self, script_path: str) -> str:
        try:
            parser = ScriptParser()
            parser.load_script(script_path)

            metadata = parser.get_metadata()
            sections = parser.get_sections()

            self.logger.info(f"Creating video for: {metadata['title']}")
            clips = []

            for i, section in enumerate(sections):
                clips.append(self.create_video_segment(section, i))

            final_video = concatenate_videoclips(clips, method="compose")

            output_file = os.path.join(
                self.output_dir,
                f"video_{metadata['title'][:30].replace(' ', '_')}.mp4"
            )

            final_video.write_videofile(
                output_file,
                fps=int(os.getenv('VIDEO_FPS', '24')),
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
            temp_dir = Path(self.output_dir) / 'temp'
            if temp_dir.exists():
                for file in temp_dir.glob('*'):
                    file.unlink()
                temp_dir.rmdir()