import os
from docx import Document
from datetime import datetime
import logging
from typing import Dict, List, Optional, Callable
from dotenv import load_dotenv
from .blog_parser import BlogParser
from .video_maker import VideoMaker
import sys
from pathlib import Path

class VideoGenerator:
    def __init__(self):
        load_dotenv()
        self.content_dir = os.getenv('HUGO_CONTENT_DIR', 'content/posts')
        self.num_posts = int(os.getenv('NUM_POSTS', '5'))
        self.output_dir = os.getenv('SCRIPT_OUTPUT_DIR', 'video_scripts')
        self.video_output_dir = os.getenv('VIDEO_OUTPUT_DIR', 'video_output')

        # Messaggi predefiniti
        self.intro_text = os.getenv('VIDEO_INTRO_TEXT', 'Ciao a tutti e bentornati sul canale!')
        self.outro_text = os.getenv('VIDEO_OUTRO_TEXT', 'Grazie per aver guardato questo video!')

        # Configura logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Crea directory se non esistono
        for directory in [self.output_dir, self.video_output_dir]:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def create_script(self, post: Dict) -> tuple[str, Dict]:
        """Crea uno script formattato dal post"""
        try:
            doc = Document()
            script_content = {
                'title': post['title'],
                'url': post['url'],
                'date': post['date'],
                'sections': []
            }

            # Intestazione del documento
            doc.add_heading(f'Script Video: {post["title"]}', 0)
            doc.add_paragraph(f'Post originale: {post["url"]}')
            doc.add_paragraph(f'Data post: {post["date"]}')

            # Intro
            intro_section = {
                'level': 1,
                'title': 'Introduzione',
                'content': [self.intro_text, f'Oggi parleremo di {post["title"]}']
            }
            script_content['sections'].append(intro_section)

            doc.add_heading('🎬 Introduzione', 1)
            doc.add_paragraph(self.intro_text)
            doc.add_paragraph(f'Oggi parleremo di {post["title"]}')

            # Contenuto principale
            doc.add_heading('📝 Contenuto', 1)
            if 'sections' in post:
                script_content['sections'].extend(post['sections'])

                for section in post['sections']:
                    if section['title']:
                        doc.add_heading(section['title'], section['level'])
                    if section['content']:
                        for para in section['content']:
                            doc.add_paragraph(para)

            # Outro
            outro_section = {
                'level': 1,
                'title': 'Conclusione',
                'content': [self.outro_text]
            }
            script_content['sections'].append(outro_section)

            doc.add_heading('🎬 Conclusione', 1)
            doc.add_paragraph(self.outro_text)

            # Salva il documento
            filename = os.path.join(
                self.output_dir,
                f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{post['title'][:30]}.docx"
            )
            doc.save(filename)

            self.logger.info(f"Created script: {filename}")
            return filename, script_content

        except Exception as e:
            error_msg = f"Error creating script for {post['title']}: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def update_progress(self, progress_callback: Optional[Callable] = None,
                       progress: float = 0, status: str = ""):
        """Utility method per aggiornare il progresso in modo sicuro"""
        if progress_callback:
            try:
                progress_callback({
                    "value": progress,
                    "status": status
                })
            except Exception as e:
                self.logger.error(f"Error updating progress: {str(e)}")

    def log_message(self, message_callback: Optional[Callable] = None, message: str = ""):
        """Utility method per loggare messaggi in modo sicuro"""
        if message_callback:
            try:
                message_callback(message)
            except Exception as e:
                self.logger.error(f"Error logging message: {str(e)}")

    def process_post(self, post: Dict, message_callback: Optional[Callable] = None,
                    progress_callback: Optional[Callable] = None) -> Dict:
        """Processa un singolo post"""
        try:
            # Inizio processo
            self.update_progress(progress_callback, 0, f"Processing: {post['title']}")
            self.log_message(message_callback, f"Starting processing of: {post['title']}")

            # Crea lo script
            self.log_message(message_callback, f"Creating script for: {post['title']}")
            script_file, script_content = self.create_script(post)
            self.update_progress(progress_callback, 30, f"Script created for: {post['title']}")

            # Crea il video
            self.log_message(message_callback, f"Creating video for: {post['title']}")
            video_maker = VideoMaker(self.video_output_dir)
            video_file = video_maker.create_video(script_content)
            self.update_progress(progress_callback, 100, f"Video created for: {post['title']}")

            return {
                'title': post['title'],
                'script_file': script_file,
                'video_file': video_file,
                'url': post['url']
            }

        except Exception as e:
            error_msg = f"Error processing post {post['title']}: {str(e)}"
            self.logger.error(error_msg)
            self.log_message(message_callback, f"❌ {error_msg}")
            raise

    def process_recent_posts(self, message_callback: Optional[Callable] = None,
                           progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Processa i post più recenti"""
        try:
            self.log_message(message_callback, "📥 Fetching recent posts...")

            parser = BlogParser(self.content_dir)
            posts = parser.fetch_posts(self.num_posts)

            if not posts:
                self.log_message(message_callback, "❌ No posts found.")
                return []

            processed_items = []
            total_posts = len(posts)

            for i, post in enumerate(posts, 1):
                try:
                    # Calcola e aggiorna il progresso generale
                    overall_progress = ((i - 1) * 100) // total_posts
                    self.update_progress(
                        progress_callback,
                        overall_progress,
                        f"Processing post {i} of {total_posts}"
                    )

                    # Processa il post
                    result = self.process_post(post, message_callback, progress_callback)
                    if result:
                        processed_items.append(result)
                        self.log_message(
                            message_callback,
                            f"✅ Successfully processed: {post['title']}"
                        )

                except Exception as e:
                    self.logger.error(f"Error processing post {post['title']}: {str(e)}")
                    self.log_message(
                        message_callback,
                        f"⚠️ Error processing post {post['title']}: {str(e)}"
                    )
                    continue

            # Completamento
            self.update_progress(progress_callback, 100, "Processing complete")
            return processed_items

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            self.logger.error(error_msg)
            self.log_message(message_callback, f"❌ {error_msg}")
            raise

def main():
    try:
        generator = VideoGenerator()
        print("🚀 Starting video generation...")

        def progress_callback(info: Dict):
            progress = info.get('value', 0)
            status = info.get('status', '')
            print(f"Progress: {progress}% - {status}")

        items = generator.process_recent_posts(
            message_callback=print,
            progress_callback=progress_callback
        )

        if items:
            print("\n✅ Created files:")
            for item in items:
                print(f"\n📄 {item['title']}")
                print(f"   📝 Script: {item['script_file']}")
                print(f"   🎥 Video: {item['video_file']}")
                print(f"   🔗 URL: {item['url']}")
        else:
            print("\n❌ No files created. Check logs for details.")

    except Exception as e:
        print(f"\n❌ Execution error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()