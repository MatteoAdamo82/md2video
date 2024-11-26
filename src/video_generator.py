import logging
from typing import List, Dict, Optional, Callable
from .processors import BlogProcessor, ScriptProcessor, VideoProcessor
from .base_processor import ProcessorCallback

class VideoGenerator:
    """Facade pattern for the entire video generation process"""

    def __init__(self):
        self.blog_processor = BlogProcessor()
        self.script_processor = ScriptProcessor()
        self.video_processor = VideoProcessor()
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_callbacks(self, message_callback: Optional[Callable] = None,
                     progress_callback: Optional[Callable] = None):
        """Set callbacks for all processors"""
        callback = ProcessorCallback(message_callback, progress_callback)

        for processor in [self.blog_processor, self.script_processor, self.video_processor]:
            processor.set_callbacks(message_callback, progress_callback)

    def generate_scripts(self, num_posts: Optional[int] = None) -> List[Dict]:
        """Only generate scripts from posts"""
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
        """Generate a video from an existing script"""
        try:
            return self.video_processor.process(script_path)
        except Exception as e:
            raise Exception(f"Error generating video: {str(e)}")

    def process_recent_posts(self, num_posts: Optional[int] = None) -> List[Dict]:
        """Complete process: from post to video"""
        try:
            results = []
            script_results = self.generate_scripts(num_posts)
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
            """Cleans up resources from all processors, handling any errors"""
            errors = []
            for processor in [self.blog_processor, self.script_processor, self.video_processor]:
                try:
                    processor.cleanup()
                except Exception as e:
                    errors.append(str(e))

            if errors:
                self.logger.warning(f"Errors during cleanup: {', '.join(errors)}")

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