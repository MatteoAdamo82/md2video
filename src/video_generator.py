import os
from docx import Document
from datetime import datetime
import logging
from typing import Dict, List
from dotenv import load_dotenv
from .blog_parser import BlogParser
from .video_maker import VideoMaker

class VideoGenerator:
    def __init__(self):
        load_dotenv()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Inizializza le configurazioni dall'env
        self.content_dir = os.getenv('HUGO_CONTENT_DIR', 'content/posts')
        self.num_posts = int(os.getenv('NUM_POSTS', '5'))
        self.output_dir = os.getenv('SCRIPT_OUTPUT_DIR', 'video_scripts')
        self.video_output_dir = os.getenv('VIDEO_OUTPUT_DIR', 'video_output')
        self.intro_text = os.getenv('VIDEO_INTRO_TEXT', 'Ciao a tutti e bentornati sul canale!')
        self.outro_text = os.getenv('VIDEO_OUTRO_TEXT', 'Grazie per aver guardato questo video! Non dimenticare di iscriverti al canale!')

        # Inizializza i componenti
        self.parser = BlogParser(self.content_dir)
        self.video_maker = VideoMaker(self.video_output_dir)

        # Crea directory se non esistono
        for directory in [self.output_dir, self.video_output_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"Created directory: {directory}")

    def create_script(self, post: Dict) -> tuple[str, Dict]:
        """Crea uno script e restituisce il filename e il contenuto formattato"""
        try:
            self.logger.info(f"Creating script for: {post['title']}")
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
            self.logger.info(f"Saved script to: {filename}")

            return filename, formatted_content

        except Exception as e:
            self.logger.error(f"Error creating script for {post['title']}: {str(e)}")
            raise

    def process_recent_posts(self) -> List[Dict]:
        """Processa i post e crea script e video"""
        self.logger.info("Starting to process recent posts...")
        created_items = []
        posts = self.parser.fetch_posts(self.num_posts)

        for post in posts:
            try:
                self.logger.info(f"Processing post: {post['title']}")
                script_file, formatted_content = self.create_script(post)

                self.logger.info(f"Creating video for: {post['title']}")
                video_file = self.video_maker.create_video(formatted_content)

                created_items.append({
                    'title': post['title'],
                    'script_file': script_file,
                    'video_file': video_file,
                    'url': post['url']
                })

                self.logger.info(f"Completed processing: {post['title']}")

            except Exception as e:
                self.logger.error(f"Failed to process post {post['title']}: {str(e)}")
                self.logger.exception(e)
                continue

        return created_items

def main():
    try:
        generator = VideoGenerator()

        print(f"📥 Recupero post da {generator.content_dir}...")
        items = generator.process_recent_posts()

        if not items:
            print("\n❌ Nessun file creato. Controlla i log per i dettagli.")
            return

        print("\n✅ File creati:")
        for item in items:
            print(f"\n📄 {item['title']}")
            print(f"   📝 Script: {item['script_file']}")
            print(f"   🎥 Video: {item['video_file']}")
            print(f"   🔗 URL: {item['url']}")

    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {str(e)}")
        logging.error("Critical error", exc_info=True)

if __name__ == "__main__":
    main()