from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import *
import logging
from dotenv import load_dotenv
from math import sin, pi
from .script_generator import ScriptParser

class VideoMaker:
    def __init__(self, output_dir: str = 'video_output'):
        load_dotenv()
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Impostazioni base
        self.width = int(os.getenv('VIDEO_WIDTH', '1920'))
        self.height = int(os.getenv('VIDEO_HEIGHT', '1080'))
        self.default_bg = os.getenv('VIDEO_BGCOLOR', '#291d38')
        self.text_color = os.getenv('VIDEO_TEXT_COLOR', '#ffffff')
        self.accent_color = os.getenv('VIDEO_ACCENT_COLOR', '#f22bb3')

        # Directory assets
        self.assets_dir = Path(output_dir) / 'assets'
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        # Configurazioni animazioni
        self.animations = {
            # Transizioni base
            'fade': lambda clip: clip.fadein(0.5).fadeout(0.5),
            'slide_left': lambda clip: clip.set_position(lambda t: ('center', 'center') if t > 0.5 else (self.width * (1-2*t), 'center')),
            'slide_right': lambda clip: clip.set_position(lambda t: ('center', 'center') if t > 0.5 else (-self.width * (1-2*t), 'center')),
            'slide_up': lambda clip: clip.set_position(lambda t: ('center', 'center') if t > 0.5 else ('center', self.height * (1-2*t))),
            'slide_down': lambda clip: clip.set_position(lambda t: ('center', 'center') if t > 0.5 else ('center', -self.height * (1-2*t))),

            # Zoom
            'zoom_in': lambda clip: clip.resize(lambda t: 1 + 0.5 * t),
            'zoom_out': lambda clip: clip.resize(lambda t: 1.5 - 0.5 * t),
            'zoom_pulse': lambda clip: clip.resize(lambda t: 1 + 0.1 * sin(t * 2 * pi)),

            # Rotazioni
            'rotate_cw': lambda clip: clip.rotate(lambda t: 360 * t),
            'rotate_ccw': lambda clip: clip.rotate(lambda t: -360 * t),

            # Combinazioni
            'zoom_fade': lambda clip: clip.fadein(0.5).fadeout(0.5).resize(lambda t: 1 + 0.1 * t),
            'rotate_fade': lambda clip: clip.fadein(0.5).fadeout(0.5).rotate(lambda t: 360 * t)
        }

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

    def create_gradient_background(self, bg_name: str = None) -> Image:
        """Crea uno sfondo con gradiente o carica un'immagine custom"""
        if bg_name and (self.assets_dir / bg_name).exists():
            bg_image = Image.open(self.assets_dir / bg_name)
            return bg_image.resize((self.width, self.height))

        # Sfondo default con gradiente
        image = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        def hex_to_rgb(hex_color):
            return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

        bg_color = hex_to_rgb(self.default_bg)

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

    def create_slide(self, text: str, filename: str, heading_level: int = 0, bg_name: str = None) -> str:
        try:
            image = self.create_gradient_background(bg_name)
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
            tts.save(filename)

            # Se è richiesta una pausa, aggiungiamola in modo più sicuro
            if pause > 0:
                # Carica l'audio originale
                audio = AudioFileClip(filename)

                # Crea un array di zeri per il silenzio
                sample_rate = 44100  # standard sample rate
                silence_duration = int(pause * sample_rate)
                silence = AudioClip(lambda t: 0, duration=pause)

                # Concatena con un crossfade minimo per evitare glitch
                final_audio = concatenate_audioclips([audio, silence],
                                                   method="compose",
                                                   crossfadein=0.1,
                                                   crossfadeout=0.1)

                # Salva l'audio finale
                final_audio.write_audiofile(filename,
                                          fps=sample_rate,
                                          nbytes=2,
                                          codec='libmp3lame',
                                          bitrate='192k',
                                          ffmpeg_params=["-ac", "2"])  # forza output stereo

                # Chiudi i clips per liberare memoria
                audio.close()
                final_audio.close()

            return filename
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {str(e)}")
            raise

    def create_video_segment(self, section: dict, segment_number: int) -> VideoFileClip:
        temp_dir = Path(self.output_dir) / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            clips = []

            # Per ogni speech, crea una nuova slide
            for i, speech in enumerate(section['speeches']):
                image_file = str(temp_dir / f'slide_{segment_number}_{i}.png')
                audio_file = str(temp_dir / f'audio_{segment_number}_{i}.mp3')

                # Usa background custom se specificato nella sezione
                bg_name = section.get('background')

                # Crea slide per ogni speech
                self.create_slide(speech['text'], image_file, section['level'], bg_name)
                self.text_to_speech(speech['text'], audio_file, speech['pause'])

                audio = AudioFileClip(audio_file)
                video = ImageClip(image_file).set_duration(audio.duration)

                # Applica animazione se specificata
                animation = section.get('animation', 'fade')
                if animation in self.animations:
                    video = self.animations[animation](video)

                clips.append(video.set_audio(audio))

            return concatenate_videoclips(clips, method="compose") if clips else None

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
                segment_clip = self.create_video_segment(section, i)
                if segment_clip is not None:
                    clips.append(segment_clip)

            if not clips:
                raise ValueError("No valid clips generated")

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