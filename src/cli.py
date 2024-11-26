#!/usr/bin/env python3
import cmd
import sys
import os
from datetime import datetime
from typing import Optional
from pathlib import Path
from .video_generator import VideoGenerator

class VideoGeneratorCLI(cmd.Cmd):
    intro = f"""\033[1m{'-'*50}
Welcome to Video Generator!
Type 'help' o '?' for command list.
{'-'*50}\033[0m"""
    prompt = '\033[94m(video)\033[0m '

    def __init__(self, stdout=None):
        super().__init__()
        self.stdout = stdout or sys.stdout
        self.generator = VideoGenerator()
        self.generator.set_callbacks(
            message_callback=lambda msg: print(msg, file=self.stdout),
            progress_callback=lambda info: print(
                f"Progress: {info['value']}% - {info['status']}",
                file=self.stdout
            )
        )

    def do_script(self, arg: str) -> None:
        """Generating script from recent posts"""
        try:
            print("\nGenerating scripts...", file=self.stdout)
            items = self.generator.generate_scripts()

            if items:
                print("\n✅ Generated scripts:", file=self.stdout)
                for item in items:
                    print(f"\n📄 {item['title']}", file=self.stdout)
                    print(f"   📝 Script: {item['script_file']}", file=self.stdout)
            else:
                print("\n❌ No scripts generated.", file=self.stdout)

        except Exception as e:
            print(f"\n❌ Error: {str(e)}", file=self.stdout)

    def do_video(self, arg: str) -> None:
        """Generate video from XML scripts"""
        try:
            scripts = self._list_available_scripts()

            if not scripts:
                print("❌ No script files found.", file=self.stdout)
                return

            print("\nAvailable scripts:", file=self.stdout)
            for i, script in enumerate(scripts, 1):
                print(f"{i}. {script.name}", file=self.stdout)

            while True:
                choice = input("\nSelect script number (0 to cancel): ")
                if choice == "0":
                    return
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(scripts):
                        selected_script = scripts[idx]
                        print(f"\nGenerating video for: {selected_script.name}")

                        video_file = self.generator.generate_video(str(selected_script))
                        print(f"\n✅ Video generated: {video_file}", file=self.stdout)
                        break
                    else:
                        print("❌ Invalid selection.", file=self.stdout)
                except ValueError:
                    print("❌ Enter a valid number.", file=self.stdout)
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}", file=self.stdout)

        except Exception as e:
            print(f"\n❌ Error: {str(e)}", file=self.stdout)

    def do_genera(self, arg: str) -> None:
        """Generate both scripts and videos from posts"""
        try:
            print("\nGenerating scripts and videos...", file=self.stdout)
            items = self.generator.process_recent_posts()

            if items:
                print("\n✅ Generated files:", file=self.stdout)
                for item in items:
                    print(f"\n📄 {item['title']}", file=self.stdout)
                    print(f"   📝 Script: {item['script_file']}", file=self.stdout)
                    print(f"   🎥 Video: {item['video_file']}", file=self.stdout)
            else:
                print("\n❌ No files generated.", file=self.stdout)

        except Exception as e:
            print(f"\n❌ Error: {str(e)}", file=self.stdout)

    def do_help(self, arg: str) -> None:
        """Show available commands"""
        if arg:
            super().do_help(arg)
        else:
            print("\n Available commands:", file=self.stdout)
            print("  script  - Generate script only from post", file=self.stdout)
            print("  video   - Generate videos from existing XML scripts", file=self.stdout)
            print("  genera  - Generate both scripts and videos from posts", file=self.stdout)
            print("  help    - Show available commands", file=self.stdout)
            print("  quit    - Exit the program", file=self.stdout)
            print(file=self.stdout)

    def do_quit(self, arg: str) -> bool:
        """Exit the program"""
        print("\nGoodbye!\n", file=self.stdout)
        return True

    def default(self, line: str) -> None:
        """Handles unrecognized commands"""
        print(f"\n❌ Command not found: {line}", file=self.stdout)
        print("Please, use 'help' to see available commands.", file=self.stdout)

    def emptyline(self) -> None:
        """do nothing if just enter is pressed"""
        pass

    def _list_available_scripts(self) -> list[Path]:
        """List available XML scripts"""
        from pathlib import Path
        from .config import Config

        config = Config()
        script_dir = Path(config.SCRIPT_DIR)
        return sorted(script_dir.glob('*.xml'))

    def cleanup(self):
        """Cleans resources before exiting"""
        try:
            self.generator.cleanup()
        except Exception as e:
            print(f"\n⚠️ Error while cleaning: {str(e)}", file=self.stdout)

def main():
    """Main entry point"""
    cli = None
    try:
        cli = VideoGeneratorCLI()
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\nGoodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        if cli:
            cli.cleanup()

if __name__ == '__main__':
    main()