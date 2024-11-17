from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from gtts import gTTS
from moviepy.editor import *
import textwrap
import logging
from dotenv import load_dotenv
import re
from pydub import AudioSegment
import tempfile
from typing import Optional, Tuple

class VideoMaker:
    def __init__(self, output_dir: str = 'video_output'):
        """Inizializza il VideoMaker con le configurazioni necessarie."""
        load_dotenv()
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Video settings
        self.width = int(os.getenv('VIDEO_WIDTH', '1920'))
        self.height = int(os.getenv('VIDEO_HEIGHT', '1080'))
        self.fps = int(os.getenv('VIDEO_FPS', '24'))
        self.bitrate = os.getenv('VIDEO_BITRATE', '4000k')

        # Design settings
        self.background_color = os.getenv('VIDEO_BGCOLOR', '#291d38')
        self.text_color = os.getenv('VIDEO_TEXT_COLOR', '#ffffff')
        self.accent_color = os.getenv('VIDEO_ACCENT_COLOR', '#f22bb3')

        # Font configuration
        self.font_path = os.getenv('VIDEO_FONT_PATH', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        self.heading_sizes = {
            1: int(os.getenv('VIDEO_H1_FONT_SIZE', '70')),  # Titoli principali
            2: int(os.getenv('VIDEO_H2_FONT_SIZE', '60')),  # Sottotitoli
            3: int(os.getenv('VIDEO_H3_FONT_SIZE', '50')),  # Sezioni
            0: int(os.getenv('VIDEO_TEXT_FONT_SIZE', '40'))  # Testo normale
        }

        # Layout settings
        self.margin = int(self.width * 0.15)
        self.line_spacing = 1.2
        self.max_text_width = int(self.width * 0.7)

        # Audio settings
        self.speech_rate = os.getenv('SPEECH_RATE', 'normal')
        self.pause_threshold = float(os.getenv('PAUSE_THRESHOLD', '0.3'))
        self.silence_threshold = int(os.getenv('SILENCE_THRESHOLD', '-40'))  # dB
        self.normalize_volume = bool(os.getenv('NORMALIZE_VOLUME', 'True'))

        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Converte un colore hex in RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def create_gradient_background(self) -> Image:
        """Crea uno sfondo con gradiente sfumato."""
        image = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        bg_color = self.hex_to_rgb(self.background_color)
        accent_color = self.hex_to_rgb(self.accent_color)

        # Gradiente principale
        for y in range(self.height):
            factor = 1 - (y / self.height * 0.3)  # Sfumatura più sottile
            color = tuple(int(c * factor) for c in bg_color)
            draw.line([(0, y), (self.width, y)], fill=color)

        # Aggiungi effetto vignette
        gradient = Image.new('L', (self.width, self.height))
        gradient_draw = ImageDraw.Draw(gradient)
        for i in range(50):
            alpha = int(255 * (1 - i/50))
            box = [(i, i), (self.width-i, self.height-i)]
            gradient_draw.rectangle(box, outline=alpha)

        # Applica la vignette
        image.putalpha(gradient)
        image = Image.alpha_composite(Image.new('RGBA', image.size), image)
        return image.convert('RGB')

    def clean_text_for_tts(self, text: str) -> str:
            """Prepara il testo per una migliore sintesi vocale."""
            # Rimuove spazi multipli e caratteri non necessari
            text = re.sub(r'\s+', ' ', text.strip())

            # Migliora la pronuncia delle abbreviazioni e dei simboli comuni
            replacements = {
                'es.': 'per esempio',
                'es:': 'per esempio',
                'ecc.': 'eccetera',
                'dr.': 'dottor',
                'dott.': 'dottor',
                'sig.': 'signor',
                'sig.ra': 'signora',
                'vs.': 'verso',
                'etc.': 'eccetera',
                'mr.': 'mister',
                'mrs.': 'signora',
                'prof.': 'professor',
                'n.': 'numero',
                'tel.': 'telefono',
                'p.s.': 'post scriptum',
                'pag.': 'pagina',
                '%': 'per cento',
                '€': 'euro',
                '$': 'dollari',
                '&': 'e',
                '+': 'più',
                '=': 'uguale a',
                '<': 'minore di',
                '>': 'maggiore di',
                '...': '.',  # Evita pause lunghe
                '!!': '!',   # Normalizza esclamazioni multiple
                '??': '?',   # Normalizza domande multiple
            }

            for old, new in replacements.items():
                text = text.replace(old, new)

            # Gestisce i numeri per una pronuncia migliore
            def format_number(match):
                num = match.group(0)
                if '.' in num or ',' in num:
                    # Gestisce i decimali
                    int_part, dec_part = re.split(r'[.,]', num)
                    return f"{int_part} virgola {dec_part}"
                return ' '.join(num)

            text = re.sub(r'\d+(?:[.,]\d+)?', format_number, text)

            # Migliora la punteggiatura per un ritmo più naturale
            text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\2', text)  # Aggiunge line breaks dopo la punteggiatura forte
            text = re.sub(r',\s+', ', ', text)  # Normalizza le virgole
            text = re.sub(r';\s+', '. ', text)  # Converte punto e virgola in punto
            text = re.sub(r':\s+', ', ', text)  # Converte i due punti in virgola

            # Gestisce le parentesi
            text = re.sub(r'\(([^)]+)\)', r', \1,', text)

            # Rimuove caratteri speciali rimanenti
            text = re.sub(r'[^\w\s,.!?-]', ' ', text)

            # Normalizza spazi dopo la pulizia
            text = re.sub(r'\s+', ' ', text).strip()

            return text

    def split_text_into_chunks(self, text: str, max_chars: int = 300) -> list:
        """Divide il testo in chunk gestibili preservando il senso delle frasi."""
        chunks = []
        sentences = re.split(r'([.!?]\n)', text)
        current_chunk = ""

        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""

            if len(current_chunk) + len(sentence) + len(punctuation) <= max_chars:
                current_chunk += sentence + punctuation
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + punctuation

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def process_audio_segment(self, audio: AudioSegment) -> AudioSegment:
        """Applica post-processing all'audio per migliorare la naturalezza."""
        try:
            # Normalizza il volume
            audio = audio.normalize()

            # Applica compressione dinamica per migliorare la chiarezza
            audio = audio.compress_dynamic_range(
                threshold=-20.0,
                ratio=4.0,
                attack=5.0,
                release=50.0
            )

            # Migliora le frequenze per una voce più chiara
            audio = audio.high_pass_filter(80)  # Rimuove le basse frequenze non necessarie
            audio = audio.low_pass_filter(10000)  # Limita le alte frequenze

            return audio

        except Exception as e:
            self.logger.error(f"Error processing audio: {str(e)}")
            return audio

    def text_to_speech(self, text: str, filename: str, lang='it') -> str:
            """Converte il testo in audio con miglioramenti alla qualità."""
            try:
                # Prepara il testo
                cleaned_text = self.clean_text_for_tts(text)

                # Divide in frasi più brevi per una migliore gestione
                sentences = re.split(r'([.!?]\n|[.!?]\s)', cleaned_text)
                chunks = []
                current_chunk = ""

                for i in range(0, len(sentences)-1, 2):
                    sentence = sentences[i]
                    punctuation = sentences[i+1] if i+1 < len(sentences) else ""

                    if len(current_chunk) + len(sentence) < 100:  # Chunk più piccoli
                        current_chunk += sentence + punctuation
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence + punctuation

                if current_chunk:
                    chunks.append(current_chunk)

                # Genera e combina l'audio
                combined_audio = None
                with tempfile.TemporaryDirectory() as temp_dir:
                    for i, chunk in enumerate(chunks):
                        temp_file = os.path.join(temp_dir, f'chunk_{i}.mp3')

                        # Usa gTTS con velocità normale per un ritmo più naturale
                        tts = gTTS(text=chunk, lang=lang, slow=False)
                        tts.save(temp_file)

                        # Processa il chunk audio
                        audio_chunk = AudioSegment.from_mp3(temp_file)
                        processed_chunk = self.process_audio_segment(audio_chunk)

                        # Aggiunge pause naturali tra le frasi
                        if combined_audio is None:
                            combined_audio = processed_chunk
                        else:
                            # Pausa più breve tra le frasi
                            combined_audio += AudioSegment.silent(duration=100) + processed_chunk

                # Normalizzazione finale e export
                combined_audio = combined_audio.normalize()
                combined_audio = combined_audio.compress_dynamic_range()  # Migliora la chiarezza
                combined_audio.export(filename, format='mp3', bitrate='192k',
                                    parameters=["-ar", "44100", "-ac", "2"])  # Parametri di qualità

                return filename

            except Exception as e:
                self.logger.error(f"Error in text-to-speech: {str(e)}")
                raise

    def create_slide(self, text: str, filename: str, heading_level: int = 0) -> str:
        """Crea una slide con design migliorato."""
        try:
            # Crea l'immagine base
            image = self.create_gradient_background()
            draw = ImageDraw.Draw(image)

            try:
                font_size = self.heading_sizes.get(heading_level, self.heading_sizes[0])
                font = ImageFont.truetype(self.font_path, font_size)
            except:
                self.logger.warning(f"Could not load font {self.font_path}, using default")
                font = ImageFont.load_default()

            # Calcola il wrapping del testo
            max_width = self.width - (self.margin * 2)
            lines = []
            for line in text.split('\n'):
                wrapped = textwrap.fill(line, width=int(max_width / (font_size * 0.5)))
                lines.extend(wrapped.split('\n'))

            # Calcola l'altezza totale del testo
            line_height = font_size * self.line_spacing
            total_height = len(lines) * line_height

            # Posiziona il testo
            y = (self.height - total_height) / 2
            for line in lines:
                # Centra ogni linea
                line_width = font.getlength(line)
                x = (self.width - line_width) / 2

                # Aggiungi ombra per i titoli
                if heading_level in [1, 2, 3]:
                    shadow_offset = 2
                    draw.text((x + shadow_offset, y + shadow_offset),
                            line, font=font, fill='#000000', alpha=100)

                # Disegna il testo
                draw.text((x, y), line, font=font, fill=self.text_color)
                y += line_height

            # Salva l'immagine
            image.save(filename, quality=95)
            return filename

        except Exception as e:
            self.logger.error(f"Error creating slide: {str(e)}")
            raise

    def create_video_segment(self, text: str, segment_number: int, heading_level: int = 0) -> VideoFileClip:
        """Crea un segmento video con transizioni fluide."""
        temp_dir = Path(self.output_dir) / 'temp'
        temp_dir.mkdir(exist_ok=True)

        try:
            # Crea slide e audio
            image_file = str(temp_dir / f'slide_{segment_number}.png')
            audio_file = str(temp_dir / f'audio_{segment_number}.mp3')

            self.create_slide(text, image_file, heading_level)
            self.text_to_speech(text, audio_file)

            # Crea video con transizioni
            audio = AudioFileClip(audio_file)
            video = (ImageClip(image_file)
                    .set_duration(audio.duration)
                    .fadein(0.7)
                    .fadeout(0.7))

            # Combina audio e video
            final_clip = video.set_audio(audio)
            return final_clip

        except Exception as e:
            self.logger.error(f"Error creating video segment: {str(e)}")
            raise

    def create_video(self, script_content: dict) -> str:
            """Crea il video completo dallo script."""
            try:
                self.logger.info(f"Creating video for: {script_content['title']}")
                clips = []

                # Crea intro
                intro_clip = self.create_video_segment(
                    script_content['title'],
                    0,
                    heading_level=1
                )
                clips.append(intro_clip)

                # Processa le sezioni
                for i, section in enumerate(script_content['sections'], 1):
                    if section['title']:
                        clips.append(self.create_video_segment(
                            section['title'],
                            i,
                            heading_level=section['level']
                        ))

                    if section['content']:
                        content_text = ' '.join(section['content'])
                        clips.append(self.create_video_segment(
                            content_text,
                            i + 1000,
                            heading_level=0
                        ))

                # Concatena i clip con transizioni
                final_video = concatenate_videoclips(clips, method="compose")

                # Genera il nome del file di output
                safe_title = re.sub(r'[^\w\s-]', '', script_content['title'])
                safe_title = re.sub(r'[-\s]+', '_', safe_title)
                output_file = os.path.join(
                    self.output_dir,
                    f"video_{safe_title[:30]}.mp4"
                )

                # Renderizza il video finale
                final_video.write_videofile(
                    output_file,
                    fps=self.fps,
                    codec='libx264',
                    audio_codec='aac',
                    bitrate=self.bitrate,
                    write_logfile=False
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
                        try:
                            file.unlink()
                        except Exception as e:
                            self.logger.warning(f"Could not delete temporary file {file}: {str(e)}")
                    try:
                        temp_dir.rmdir()
                    except Exception as e:
                        self.logger.warning(f"Could not delete temporary directory: {str(e)}")