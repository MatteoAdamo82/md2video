from typing import List, Dict, Optional, Callable
from .processors import BlogProcessor, ScriptProcessor, VideoProcessor
from .base_processor import ProcessorCallback

class VideoGenerator:
    """Facade pattern per l'intero processo di generazione video"""

    def __init__(self):
        self.blog_processor = BlogProcessor()
        self.script_processor = ScriptProcessor()
        self.video_processor = VideoProcessor()

    def set_callbacks(self, message_callback: Optional[Callable] = None,
                     progress_callback: Optional[Callable] = None):
        """Imposta i callback per tutti i processor"""
        callback = ProcessorCallback(message_callback, progress_callback)

        for processor in [self.blog_processor, self.script_processor, self.video_processor]:
            processor.set_callbacks(message_callback, progress_callback)

    def generate_scripts(self, num_posts: Optional[int] = None) -> List[Dict]:
        """Genera solo gli script dai post"""
        try:
            posts = self.blog_processor.process(num_posts)
            results = []

            for post in posts:
                script_file, _ = self.script_processor.process(post)
                results.append({
                    'title': post['title'],
                    'script_file': script_file,
                    'url': post['url']
                })

            return results

        except Exception as e:
            raise Exception(f"Error generating scripts: {str(e)}")

    def generate_video(self, script_path: str) -> str:
        """Genera un video da uno script esistente"""
        try:
            return self.video_processor.process(script_path)
        except Exception as e:
            raise Exception(f"Error generating video: {str(e)}")

    def process_recent_posts(self, num_posts: Optional[int] = None) -> List[Dict]:
        """Processo completo: da post a video"""
        try:
            results = []

            # Genera gli script
            script_results = self.generate_scripts(num_posts)

            # Genera i video per ogni script
            for item in script_results:
                video_file = self.generate_video(item['script_file'])
                results.append({
                    'title': item['title'],
                    'script_file': item['script_file'],
                    'video_file': video_file,
                    'url': item['url']
                })

            return results

        except Exception as e:
            raise Exception(f"Error processing posts: {str(e)}")

    def cleanup(self):
        """Pulisce le risorse temporanee"""
        for processor in [self.blog_processor, self.script_processor, self.video_processor]:
            processor.cleanup()

# Example usage in CLI
if __name__ == "__main__":
    def print_progress(info):
        print(f"Progress: {info['value']}% - {info['status']}")

    generator = VideoGenerator()
    generator.set_callbacks(print, print_progress)

    try:
        results = generator.process_recent_posts()
        print("\n✅ Generated files:")
        for item in results:
            print(f"\n📄 {item['title']}")
            print(f"   📝 Script: {item['script_file']}")
            print(f"   🎥 Video: {item['video_file']}")
            print(f"   🔗 URL: {item['url']}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        generator.cleanup()