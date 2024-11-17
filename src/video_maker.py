from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import *
import textwrap
import logging
from dotenv import load_dotenv

class VideoMaker:
    def __init__(self, output_dir: str = 'video_output'):
        load_dotenv()

        self.output_dir = output_dir
        self.temp_dir = os.getenv('TEMP_DIR', 'temp')
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Video settings
        self.video_width = int(os.getenv('VIDEO_WIDTH', '1920'))
        self.video_height = int(os.getenv('VIDEO_HEIGHT', '1080'))
        self.video_fps = int(os.getenv('VIDEO_FPS', '24'))
        self.bg_color = os.getenv('VIDEO_BGCOLOR', 'white')
        self.text_color = os.getenv('VIDEO_TEXT_COLOR', 'black')
        self.font_size = int(os.getenv('VIDEO_FONT_SIZE', '60'))
        self.font_path = os.getenv('VIDEO_FONT_PATH', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')

        # Text settings
        self.text_wrap_width = int(os.getenv('TEXT_WRAP_WIDTH', '50'))
        self.text_line_height = int(os.getenv('TEXT_LINE_HEIGHT', '70'))
        self.text_start_y = int(os.getenv('TEXT_START_Y', '100'))

        # Audio settings
        self.tts_language = os.getenv('TTS_LANGUAGE', 'it')

        # Logging setup
        logging.basicConfig(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            format=os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger = logging.getLogger(__name__)

    def create_slide(self, text: str, filename: str) -> str:
        """Crea una slide con testo"""
        # Crea immagine
        image = Image.new('RGB', (self.video_width, self.video_height), self.bg_color)
        draw = ImageDraw.Draw(image)

        # Usa il font configurato
        try:
            font = ImageFont.truetype(self.font_path, self.font_size)
        except:
            self.logger.warning(f"Could not load font {self.font_path}, using default")
            font = ImageFont.load_default()

        # Wrap del testo
        wrapper = textwrap.TextWrapper(width=self.text_wrap_width)
        text_lines = wrapper.wrap(text)

        # Posiziona il testo
        y = self.text_start_y
        for line in text_lines:
            width = draw.textlength(line, font=font)
            draw.text(
                ((self.video_width - width) / 2, y),
                line,
                font=font,
                fill=self.text_color
            )
            y += self.text_line_height

        image.save(filename)
        return filename

    def text_to_speech(self, text: str, filename: str) -> str:
        """Converte testo in audio"""
        tts = gTTS(text=text, lang=self.tts_language)
        tts.save(filename)
        return filename

    def create_video_segment(self, text: str, segment_number: int) -> VideoFileClip:
        """Crea un segmento di video da testo"""
        temp_dir = Path(self.output_dir) / self.temp_dir
        temp_dir.mkdir(exist_ok=True)

        # Crea slide e audio
        image_file = str(temp_dir / f'slide_{segment_number}.png')
        audio_file = str(temp_dir / f'audio_{segment_number}.mp3')

        self.create_slide(text, image_file)
        self.text_to_speech(text, audio_file)

        # Crea video
        audio = AudioFileClip(audio_file)
        video = ImageClip(image_file).set_duration(audio.duration)

        return video.set_audio(audio)

    def create_video(self, script_content: dict) -> str:
        """Crea un video completo da uno script"""
        try:
            self.logger.info(f"Creating video for: {script_content['title']}")
            clips = []

            # Intro
            intro_text = f"{os.getenv('VIDEO_INTRO_TEXT')}\nOggi parleremo di {script_content['title']}"
            clips.append(self.create_video_segment(intro_text, 0))

            # Contenuto principale
            paragraphs = script_content['content'].split('\n\n')
            for i, para in enumerate(paragraphs, 1):
                if para.strip():
                    clips.append(self.create_video_segment(para, i))

            # Outro
            clips.append(self.create_video_segment(os.getenv('VIDEO_OUTRO_TEXT'), len(paragraphs) + 1))

            # Concatena tutti i clip
            final_video = concatenate_videoclips(clips)

            # Salva il video
            output_file = os.path.join(
                self.output_dir,
                f"video_{script_content['title'][:30].replace(' ', '_')}.mp4"
            )

            final_video.write_videofile(
                output_file,
                fps=self.video_fps,
                codec='libx264',
                audio_codec='aac'
            )

            self.logger.info(f"Video saved to: {output_file}")
            return output_file

        except Exception as e:
            self.logger.error(f"Error creating video: {str(e)}")
            raise
        finally:
            # Pulisci i file temporanei
            temp_dir = Path(self.output_dir) / self.temp_dir
            if temp_dir.exists():
                for file in temp_dir.glob('*'):
                    file.unlink()
                temp_dir.rmdir()