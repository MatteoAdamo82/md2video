from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import *
import textwrap
import logging

class VideoMaker:
    def __init__(self, output_dir: str = 'video_output'):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def create_slide(self, text: str, filename: str,
                    size=(1920, 1080),
                    bg_color='white',
                    text_color='black'):
        """Crea una slide con testo"""
        # Crea immagine
        image = Image.new('RGB', size, bg_color)
        draw = ImageDraw.Draw(image)

        # Usa un font di sistema
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
        except:
            font = ImageFont.load_default()

        # Wrap del testo
        wrapper = textwrap.TextWrapper(width=50)
        text_lines = wrapper.wrap(text)

        # Posiziona il testo
        y = 100
        for line in text_lines:
            width = draw.textlength(line, font=font)
            draw.text(((size[0] - width) / 2, y), line, font=font, fill=text_color)
            y += 70

        image.save(filename)
        return filename

    def text_to_speech(self, text: str, filename: str, lang='it'):
        """Converte testo in audio"""
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
        return filename

    def create_video_segment(self, text: str, segment_number: int) -> VideoFileClip:
        """Crea un segmento di video da testo"""
        temp_dir = Path(self.output_dir) / 'temp'
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

            # Crea i segmenti del video
            clips = []

            # Intro
            intro_text = f"Ciao a tutti e bentornati sul canale!\nOggi parleremo di {script_content['title']}"
            clips.append(self.create_video_segment(intro_text, 0))

            # Contenuto principale
            paragraphs = script_content['content'].split('\n\n')
            for i, para in enumerate(paragraphs, 1):
                if para.strip():
                    clips.append(self.create_video_segment(para, i))

            # Outro
            outro_text = "Grazie per aver guardato questo video!\nNon dimenticare di iscriverti al canale!"
            clips.append(self.create_video_segment(outro_text, len(paragraphs) + 1))

            # Concatena tutti i clip
            final_video = concatenate_videoclips(clips)

            # Salva il video
            output_file = os.path.join(
                self.output_dir,
                f"video_{script_content['title'][:30].replace(' ', '_')}.mp4"
            )

            final_video.write_videofile(
                output_file,
                fps=24,
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
            temp_dir = Path(self.output_dir) / 'temp'
            if temp_dir.exists():
                for file in temp_dir.glob('*'):
                    file.unlink()
                temp_dir.rmdir()
