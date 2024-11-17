from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from gtts import gTTS
from moviepy.editor import *
import textwrap
import logging
from dotenv import load_dotenv
import re

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
            1: int(os.getenv('VIDEO_H1_FONT_SIZE', '70')),  # h1
            2: int(os.getenv('VIDEO_H2_FONT_SIZE', '60')),  # h2
            3: int(os.getenv('VIDEO_H3_FONT_SIZE', '50')),  # h3
            0: int(os.getenv('VIDEO_TEXT_FONT_SIZE', '40'))  # testo normale
        }

        # Layout settings
        self.margin = int(self.width * 0.15)  # 15% margine
        self.line_spacing = 1.2
        self.max_text_width = int(self.width * 0.7)  # 70% larghezza massima testo

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def create_gradient_background(self) -> Image:
        """Crea uno sfondo con gradiente"""
        image = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        # Converti il colore di sfondo da hex a RGB
        def hex_to_rgb(hex_color):
            return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

        bg_color = hex_to_rgb(self.background_color)

        for y in range(self.height):
            # Gradiente sottile
            factor = 1 - y/self.height * 0.2
            color = tuple(int(c * factor) for c in bg_color)
            draw.line([(0, y), (self.width, y)], fill=color)

        return image

    def add_decorative_elements(self, image: Image) -> Image:
        """Aggiunge elementi decorativi """

        return image

    def get_wrapped_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
        """Calcola il wrapping del testo considerando la larghezza effettiva"""
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
        """Crea una slide con design migliorato e gestione testo ottimizzata"""
        try:
            # Crea l'immagine di base
            image = self.create_gradient_background()
            image = self.add_decorative_elements(image)

            # Prepara il font
            try:
                font_size = self.heading_sizes.get(heading_level, self.heading_sizes[0])
                font = ImageFont.truetype(self.font_path, font_size)
            except:
                self.logger.warning(f"Could not load font {self.font_path}, using default")
                font = ImageFont.load_default()

            draw = ImageDraw.Draw(image)

            # Calcola il wrapping del testo basato sulla larghezza effettiva
            max_width = self.width - (self.margin * 2)
            text_lines = self.get_wrapped_text(text, font, max_width)

            # Calcola l'altezza totale del testo
            line_height = font_size * self.line_spacing
            total_text_height = len(text_lines) * line_height

            # Limita il numero massimo di linee se necessario
            max_lines = int((self.height - (self.margin * 2)) / line_height)
            if len(text_lines) > max_lines:
                text_lines = text_lines[:max_lines-1]
                text_lines.append("...")
                total_text_height = len(text_lines) * line_height

            # Calcola la posizione iniziale y per centrare il testo verticalmente
            y = (self.height - total_text_height) / 2

            # Disegna il testo
            for line in text_lines:
                # Calcola la larghezza del testo per centrarlo
                line_width = font.getlength(line)
                x = (self.width - line_width) / 2

                if heading_level in [1, 2, 3]:
                    # Ombra più sottile per i titoli
                    shadow_offset = 2
                    draw.text((x + shadow_offset, y + shadow_offset), line,
                            font=font, fill='#000000', alpha=100)

                draw.text((x, y), line, font=font, fill=self.text_color)
                y += line_height

            # Salva l'immagine
            image.save(filename, quality=95)
            return filename

        except Exception as e:
            self.logger.error(f"Error creating slide: {str(e)}")
            raise

    def text_to_speech(self, text: str, filename: str, lang='it') -> str:
        """Converte testo in audio"""
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(filename)
            return filename
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {str(e)}")
            raise

    def create_video_segment(self, text: str, segment_number: int, heading_level: int = 0) -> VideoFileClip:
        """Crea un segmento video con transizioni"""
        temp_dir = Path(self.output_dir) / 'temp'
        temp_dir.mkdir(exist_ok=True)

        try:
            # Crea slide e audio
            image_file = str(temp_dir / f'slide_{segment_number}.png')
            audio_file = str(temp_dir / f'audio_{segment_number}.mp3')

            self.create_slide(text, image_file, heading_level)
            self.text_to_speech(text, audio_file)

            # Crea video con fade
            audio = AudioFileClip(audio_file)
            video = (ImageClip(image_file)
                    .set_duration(audio.duration)
                    .fadein(0.5)
                    .fadeout(0.5))

            # Aggiungi l'audio
            final_clip = video.set_audio(audio)

            return final_clip

        except Exception as e:
            self.logger.error(f"Error creating video segment: {str(e)}")
            raise

    def create_video(self, script_content: dict) -> str:
        """Crea un video completo da uno script strutturato"""
        try:
            self.logger.info(f"Creating video for: {script_content['title']}")
            clips = []

            # Intro con titolo principale
            intro_clip = self.create_video_segment(
                script_content['title'],
                0,
                heading_level=1
            )
            clips.append(intro_clip)

            # Processa le sezioni
            for i, section in enumerate(script_content['sections'], 1):
                # Crea una slide per il titolo della sezione se presente
                if section['title']:
                    clips.append(self.create_video_segment(
                        section['title'],
                        i,
                        heading_level=section['level']
                    ))

                # Crea slide per il contenuto
                if section['content']:
                    content_text = '\n'.join(section['content'])
                    clips.append(self.create_video_segment(
                        content_text,
                        i + 1000,  # offset per evitare conflitti
                        heading_level=0
                    ))

            # Concatena tutti i clip con transizioni
            final_video = concatenate_videoclips(clips, method="compose")

            # Salva il video
            output_file = os.path.join(
                self.output_dir,
                f"video_{script_content['title'][:30].replace(' ', '_')}.mp4"
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
            # Pulisci i file temporanei
            temp_dir = Path(self.output_dir) / 'temp'
            if temp_dir.exists():
                for file in temp_dir.glob('*'):
                    file.unlink()
                temp_dir.rmdir()