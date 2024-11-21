from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import *
from typing import Dict, List
import os
import xml.etree.ElementTree as ET
from ..base_processor import BaseProcessor
import logging

class VideoEffect:
    """Strategy pattern per gli effetti video"""
    @staticmethod
    def fade(clip):
        return clip.fadein(0.5).fadeout(0.5)

    @staticmethod
    def slide_left(clip, width):
        return clip.set_position(lambda t: ('center', 'center') if t > 0.5
                               else (width * (1-2*t), 'center'))

    @staticmethod
    def zoom_in(clip):
        return clip.resize(lambda t: 1 + 0.5 * t)

    @staticmethod
    def rotate_cw(clip):
        return clip.rotate(lambda t: 360 * t)

class VideoProcessor(BaseProcessor):
    """Processor per la generazione dei video"""

    def __init__(self):
        super().__init__()
        self.effects = {
            'fade': VideoEffect.fade,
            'slide_left': lambda clip: VideoEffect.slide_left(clip, self.config.VIDEO_WIDTH),
            'zoom_in': VideoEffect.zoom_in,
            'rotate': VideoEffect.rotate_cw
        }

    def process(self, script_path: str) -> str:
        """Processo principale di generazione video"""
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

    def _parse_script(self, script_path: str) -> Dict:
        """Parser dello script XML"""
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
        """Estrae le sezioni dallo script"""
        sections = []
        for section in content.findall("section"):
            sections.append({
                'level': int(section.get("level")),
                'type': section.get("type"),
                'heading': section.find("heading").text if section.find("heading") is not None else "",
                'speeches': [{
                    'text': speech.text,
                    'pause': float(speech.get("pause", 0.5))
                } for speech in section.findall("speech")]
            })
        return sections

    def _create_segment(self, section: Dict, segment_number: int) -> VideoFileClip:
        """Crea un segmento video per una sezione"""
        temp_path = Path(self.config.TEMP_DIR)
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
                # Crea slide e audio
                self._create_slide(speech['text'], image_path, section['level'])
                self._create_audio(speech['text'], audio_path, speech['pause'])

                # Prima carica l'audio
                audio_clip = AudioFileClip(str(audio_path))

                # Poi crea il video con la stessa durata dell'audio
                video_clip = ImageClip(str(image_path)).set_duration(audio_clip.duration)

                # Combina esplicitamente audio e video
                final_clip = video_clip.set_audio(audio_clip)

                self.logger.info(f"Clip {i} - Audio duration: {audio_clip.duration}, Video duration: {video_clip.duration}")
                clips.append(final_clip)

            except Exception as e:
                self.logger.error(f"Error processing speech {i}: {str(e)}")
                continue

        if not clips:
            return None

        try:
            # Concatena mantenendo l'audio
            final_clip = concatenate_videoclips(clips, method="compose")
            self.logger.info(f"Final segment duration: {final_clip.duration}, Has audio: {final_clip.audio is not None}")
            return final_clip
        except Exception as e:
            self.logger.error(f"Error concatenating clips: {str(e)}")
            return None

    def _render_final_video(self, clips: List[VideoFileClip], title: str) -> str:
        """Renderizza il video finale"""
        output_file = f"video_{title[:30].replace(' ', '_')}.mp4"
        output_path = self.config.OUTPUT_DIR / output_file

        self.callback.log_message(f"\nRendering final video to: {output_path}")

        try:
            # Filtra i clip nulli
            valid_clips = [clip for clip in clips if clip is not None and clip.audio is not None]

            if not valid_clips:
                raise ValueError("No valid clips with audio to render")

            self.callback.log_message(f"Concatenating {len(valid_clips)} segments...")

            # Concatenazione con verifica audio
            final_video = concatenate_videoclips(valid_clips, method="compose")

            if final_video.audio is None:
                self.logger.error("Final video has no audio after concatenation!")

            self.callback.log_message("Writing final video file...")
            self.logger.info(f"Final duration: {final_video.duration}, Has audio: {final_video.audio is not None}")

            # Usa ffmpeg_params per forzare l'inclusione dell'audio
            final_video.write_videofile(
                str(output_path),
                fps=self.config.VIDEO_FPS,
                codec=self.config.VIDEO_CODEC,
                audio_codec=self.config.AUDIO_CODEC,
                bitrate=self.config.VIDEO_BITRATE,
                audio_bitrate=self.config.AUDIO_BITRATE,
                verbose=True,
                ffmpeg_params=["-c:a", "aac", "-strict", "-2"],
                temp_audiofile=str(Path(self.config.TEMP_DIR) / "temp_audio.m4a")
            )

            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                self.callback.log_message(f"✅ Video saved successfully!")
                self.callback.log_message(f"📍 Location: {output_path}")
                self.callback.log_message(f"📊 Size: {size_mb:.1f}MB")
                self.callback.log_message(f"⏱️ Duration: {final_video.duration:.1f}s")
            else:
                raise FileNotFoundError(f"Video file was not created")

            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error saving video: {str(e)}")
            raise
        finally:
            # Chiusura pulita di tutti i clips
            for clip in clips:
                if clip is not None:
                    try:
                        clip.close()
                    except:
                        pass
            if 'final_video' in locals():
                try:
                    final_video.close()
                except:
                    pass

    def _create_slide(self, text: str, output_path: Path, heading_level: int):
        """Crea una slide con testo"""
        # Crea background
        image = self._create_background()
        draw = ImageDraw.Draw(image)

        # Configura il font
        font_size = self.config.FONT_SIZES.get(
            f'h{heading_level}' if heading_level in [1,2,3] else 'text'
        )
        try:
            font = ImageFont.truetype(self.config.FONT_PATH, font_size)
        except:
            self.logger.warning(f"Could not load font {self.config.FONT_PATH}, using default")
            font = ImageFont.load_default()

        # Calcola il layout del testo
        margin = int(self.config.VIDEO_WIDTH * self.config.TEXT_MARGIN)
        max_width = self.config.VIDEO_WIDTH - (2 * margin)
        lines = self._wrap_text(text, font, max_width)

        # Disegna il testo
        y = (self.config.VIDEO_HEIGHT - (len(lines) * font_size * self.config.TEXT_LINE_SPACING)) / 2

        for line in lines:
            x = (self.config.VIDEO_WIDTH - font.getlength(line)) / 2
            draw.text((x, y), line, font=font, fill=self.config.TEXT_COLOR)
            y += font_size * self.config.TEXT_LINE_SPACING

        image.save(output_path)

    def _create_audio(self, text: str, output_path: Path, pause: float):
        """Crea l'audio da testo"""
        try:
            # Genera l'audio base
            tts = gTTS(text=text, lang=self.config.SPEECH_LANG)
            temp_path = str(output_path).replace('.mp3', '_temp.mp3')
            tts.save(temp_path)

            # Carica l'audio generato
            audio = AudioFileClip(temp_path)

            if pause > 0:
                # Crea il silenzio
                silence = AudioClip(
                    lambda t: 0,
                    duration=pause
                ).set_fps(self.config.AUDIO_FPS)

                # Combina audio e silenzio
                final_audio = CompositeAudioClip([
                    audio,
                    silence.set_start(audio.duration)
                ])

                # Ottieni la durata totale prevista
                expected_duration = audio.duration + pause

                # Salva l'audio finale
                final_audio.write_audiofile(
                    str(output_path),
                    fps=self.config.AUDIO_FPS,
                    codec=self.config.AUDIO_CODEC,
                    bitrate=self.config.AUDIO_BITRATE,
                    write_logfile=False,
                    verbose=False
                )

                # Verifica la durata finale
                check_audio = AudioFileClip(str(output_path))
                if abs(check_audio.duration - expected_duration) > 0.01:
                    self.logger.warning(
                        f"Audio duration mismatch. Expected: {expected_duration:.2f}s, "
                        f"Got: {check_audio.duration:.2f}s"
                    )
                check_audio.close()

            else:
                # Se non c'è pausa, usa direttamente l'audio originale
                os.rename(temp_path, str(output_path))

        except Exception as e:
            self.logger.error(f"Error creating audio: {str(e)}")
            raise

        finally:
            # Pulizia
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

            # Chiudi i clip audio
            if 'audio' in locals():
                audio.close()
            if 'silence' in locals():
                silence.close()
            if 'final_audio' in locals():
                final_audio.close()

    def _create_background(self) -> Image:
        """Crea lo sfondo per le slide"""
        image = Image.new('RGB', (self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT))
        draw = ImageDraw.Draw(image)

        # Converti colore hex in RGB
        bg_color = tuple(int(self.config.BGCOLOR[i:i+2], 16) for i in (1, 3, 5))

        # Crea gradiente verticale
        for y in range(self.config.VIDEO_HEIGHT):
            factor = 1 - y/self.config.VIDEO_HEIGHT * 0.2
            color = tuple(int(c * factor) for c in bg_color)
            draw.line([(0, y), (self.config.VIDEO_WIDTH, y)], fill=color)

        return image

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Divide il testo in linee che si adattano alla larghezza massima"""
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
        """Pulisce i file temporanei"""
        temp_dir = Path(self.config.TEMP_DIR)
        if temp_dir.exists():
            for file in temp_dir.glob('*'):
                try:
                    file.unlink()
                except Exception as e:
                    self.logger.error(f"Error deleting temporary file {file}: {str(e)}")