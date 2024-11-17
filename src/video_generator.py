import os
from docx import Document
from datetime import datetime
import logging
from typing import Dict, List, Optional, Callable
from dotenv import load_dotenv
from .blog_parser import BlogParser
from .video_maker import VideoMaker
import sys

class VideoGenerator:
    def __init__(self):
        load_dotenv()
        self.content_dir = os.getenv('HUGO_CONTENT_DIR', 'content/posts')
        self.num_posts = int(os.getenv('NUM_POSTS', '5'))
        self.output_dir = os.getenv('SCRIPT_OUTPUT_DIR', 'video_scripts')
        self.video_output_dir = os.getenv('VIDEO_OUTPUT_DIR', 'video_output')
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
            if not os.path.exists(directory):
                os.makedirs(directory)

    def print_progress(self, percentage: float, status: str):
        """Stampa una barra di progresso sulla console"""
        bar_width = 50
        filled = int(bar_width * percentage / 100)
        bar = '=' * filled + '-' * (bar_width - filled)
        print(f'\r[{bar}] {percentage:.1f}% {status}', end='', flush=True)
        if percentage == 100:
            print()  # Nuova riga alla fine

    def process_recent_posts(self) -> List[Dict]:
        """Processa i post con una barra di progresso sulla console"""
        try:
            self.parser = BlogParser(self.content_dir)
            self.video_maker = VideoMaker(self.video_output_dir)

            print("📥 Recupero post...")
            posts = self.parser.fetch_posts(self.num_posts)

            if not posts:
                print("❌ Nessun post trovato.")
                return []

            created_items = []
            total_steps = len(posts) * 2  # Script + Video per ogni post
            current_step = 0

            for post in posts:
                try:
                    # Creazione script
                    status = f"Creazione script per: {post['title']}"
                    self.print_progress((current_step / total_steps) * 100, status)
                    script_file, formatted_content = self.create_script(post)
                    current_step += 1

                    # Creazione video
                    status = f"Creazione video per: {post['title']}"
                    self.print_progress((current_step / total_steps) * 100, status)
                    video_file = self.video_maker.create_video(formatted_content)
                    current_step += 1

                    created_items.append({
                        'title': post['title'],
                        'script_file': script_file,
                        'video_file': video_file,
                        'url': post['url']
                    })

                except Exception as e:
                    self.logger.error(f"Errore nel processing del post {post['title']}: {str(e)}")
                    print(f"\n⚠️  Errore nel processing del post {post['title']}: {str(e)}")
                    continue

            self.print_progress(100, "Completato!")
            return created_items

        except Exception as e:
            self.logger.error(f"Errore critico: {str(e)}")
            print(f"\n❌ Errore critico: {str(e)}")
            raise

    def create_script(self, post: Dict) -> tuple[str, Dict]:
        """Crea uno script e restituisce il filename e il contenuto formattato"""
        try:
            doc = Document()

            formatted_content = {
                'title': post['title'],
                'url': post['url'],
                'date': post['date'],
                'content': post['content'],
            }

            doc.add_heading(f'Script Video: {post["title"]}', 0)
            doc.add_paragraph(f'Post originale: {post["url"]}')
            doc.add_paragraph(f'Data post: {post["date"]}')

            doc.add_heading('🎬 Intro:', 1)
            doc.add_paragraph(self.intro_text)
            formatted_content['intro'] = self.intro_text

            doc.add_paragraph(f'Oggi parleremo di {post["title"]}')

            doc.add_heading('📝 Contenuto:', 1)
            paragraphs = post["content"].split('\n\n')
            for para in paragraphs:
                if len(para.strip()) > 0:
                    doc.add_paragraph(para)

            formatted_content['outro'] = self.outro_text

            filename = os.path.join(
                self.output_dir,
                f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{post['title'][:30]}.docx"
            )
            doc.save(filename)

            return filename, formatted_content

        except Exception as e:
            self.logger.error(f"Error creating script for {post['title']}: {str(e)}")
            raise

def main():
    try:
        generator = VideoGenerator()
        print("🚀 Avvio generazione video...")
        items = generator.process_recent_posts()

        if items:
            print("\n✅ File creati:")
            for item in items:
                print(f"\n📄 {item['title']}")
                print(f"   📝 Script: {item['script_file']}")
                print(f"   🎥 Video: {item['video_file']}")
                print(f"   🔗 URL: {item['url']}")
        else:
            print("\n❌ Nessun file creato. Controlla i log per i dettagli.")

    except Exception as e:
        print(f"\n❌ Errore durante l'esecuzione: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()