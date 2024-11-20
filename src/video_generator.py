import os
from pathlib import Path
import logging
from typing import Dict, List, Optional, Callable
from dotenv import load_dotenv
from .blog_parser import BlogParser
from .video_maker import VideoMaker
from .script_generator import ScriptGenerator
import sys

class VideoManager:
    def __init__(self):
        load_dotenv()
        self.content_dir = os.getenv('HUGO_CONTENT_DIR', 'content/posts')
        self.num_posts = int(os.getenv('NUM_POSTS', '5'))
        self.output_dir = os.getenv('SCRIPT_OUTPUT_DIR', 'scripts')
        self.video_output_dir = os.getenv('VIDEO_OUTPUT_DIR', 'videos')

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Crea directory se non esistono
        for directory in [self.output_dir, self.video_output_dir]:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def list_available_scripts(self) -> List[Path]:
        """Lista gli script disponibili"""
        return list(Path(self.output_dir).glob('*.xml'))

    def generate_scripts(self, message_callback=None, progress_callback=None) -> List[Dict]:
        """Genera solo gli script dai post"""
        try:
            self.log_message(message_callback, "📥 Fetching recent posts...")
            parser = BlogParser(self.content_dir)
            posts = parser.fetch_posts(self.num_posts)

            if not posts:
                self.log_message(message_callback, "❌ No posts found.")
                return []

            results = []
            total_posts = len(posts)
            script_generator = ScriptGenerator(self.output_dir)

            for i, post in enumerate(posts, 1):
                try:
                    self.update_progress(progress_callback, (i * 100) // total_posts,
                                      f"Creating script {i} of {total_posts}")
                    script_file, _ = script_generator.generate_xml_script(post)
                    results.append({
                        'title': post['title'],
                        'script_file': script_file,
                        'url': post['url']
                    })
                    self.log_message(message_callback, f"✅ Created script for: {post['title']}")
                except Exception as e:
                    self.log_message(message_callback, f"❌ Error: {str(e)}")

            return results
        except Exception as e:
            raise Exception(f"Error generating scripts: {str(e)}")

    def generate_video_from_script(self, script_path: str, message_callback=None,
                                progress_callback=None) -> str:
        """Genera un video da uno script esistente"""
        try:
            video_maker = VideoMaker(self.video_output_dir)
            return video_maker.create_video(script_path)
        except Exception as e:
            raise Exception(f"Error generating video: {str(e)}")

    def process_post(self, post: Dict, message_callback: Optional[Callable] = None,
                    progress_callback: Optional[Callable] = None) -> Dict:
        """Processa un singolo post"""
        try:
            self.update_progress(progress_callback, 0, f"Processing: {post['title']}")
            self.log_message(message_callback, f"Starting processing of: {post['title']}")

            # Genera script
            script_generator = ScriptGenerator(self.output_dir)
            self.log_message(message_callback, f"Creating script for: {post['title']}")
            script_file, _ = script_generator.generate_xml_script(post)
            self.update_progress(progress_callback, 30, f"Script created for: {post['title']}")

            # Genera video
            self.log_message(message_callback, f"Creating video for: {post['title']}")
            video_maker = VideoMaker(self.video_output_dir)
            video_file = video_maker.create_video(script_file)
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
                    overall_progress = ((i - 1) * 100) // total_posts
                    self.update_progress(progress_callback, overall_progress,
                                      f"Processing post {i} of {total_posts}")

                    result = self.process_post(post, message_callback, progress_callback)
                    if result:
                        processed_items.append(result)
                        self.log_message(message_callback,
                                      f"✅ Successfully processed: {post['title']}")

                except Exception as e:
                    self.logger.error(f"Error processing post {post['title']}: {str(e)}")
                    self.log_message(message_callback,
                                  f"⚠️ Error processing post {post['title']}: {str(e)}")
                    continue

            self.update_progress(progress_callback, 100, "Processing complete")
            return processed_items

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            self.logger.error(error_msg)
            self.log_message(message_callback, f"❌ {error_msg}")
            raise

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

def main():
    try:
        manager = VideoManager()
        print("🚀 Starting video generation...")

        def progress_callback(info: Dict):
            progress = info.get('value', 0)
            status = info.get('status', '')
            print(f"Progress: {progress}% - {status}")

        items = manager.process_recent_posts(
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