#!/usr/bin/env python3
import cmd
import sys
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from .video_generator import VideoGenerator

class VideoGeneratorCLI(cmd.Cmd):
    intro = f"""\033[1m{'-'*50}
Benvenuto nel Video Generator!
Digita 'help' o '?' per la lista dei comandi.
{'-'*50}\033[0m"""
    prompt = '\033[94m(video)\033[0m '

    def __init__(self, stdout=None):
        super().__init__()
        self.stdout = stdout or sys.stdout
        load_dotenv()
        self.generator = VideoGenerator()

    def do_script(self, arg: str) -> None:
        try:
            def progress_callback(info):
                progress = info.get('value', 0)
                status = info.get('status', '')
                print(f"Progresso: {progress}% - {status}", file=self.stdout)

            print("\nGenerazione script in corso...", file=self.stdout)
            items = self.generator.generate_scripts(
                message_callback=lambda msg: print(msg, file=self.stdout),
                progress_callback=progress_callback
            )

            if items:
                print("\n✅ Script generati:", file=self.stdout)
                for item in items:
                    print(f"\n📄 {item['title']}", file=self.stdout)
                    print(f"   📝 Script: {item['script_file']}", file=self.stdout)
            else:
                print("\n❌ Nessuno script generato.", file=self.stdout)

        except Exception as e:
            print(f"\n❌ Errore: {str(e)}", file=self.stdout)

    def do_video(self, arg: str) -> None:
        try:
            print("\nRicerca script disponibili...", file=self.stdout)
            scripts = self.generator.list_available_scripts()

            if not scripts:
                print("❌ Nessuno script trovato nella directory.", file=self.stdout)
                return

            print("\nScript disponibili:", file=self.stdout)
            for i, script in enumerate(scripts, 1):
                print(f"{i}. {os.path.basename(script)}", file=self.stdout)

            while True:
                choice = input("\nSeleziona il numero dello script (0 per annullare): ")
                if choice == "0":
                    return
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(scripts):
                        selected_script = scripts[idx]
                        print(f"\nGenerazione video per: {os.path.basename(selected_script)}")

                        self.generator.generate_video_from_script(
                            str(selected_script),
                            message_callback=lambda msg: print(msg, file=self.stdout),
                            progress_callback=lambda info: print(
                                f"Progresso: {info['value']}% - {info['status']}",
                                file=self.stdout
                            )
                        )
                        break
                    else:
                        print("❌ Selezione non valida.", file=self.stdout)
                except ValueError:
                    print("❌ Inserisci un numero valido.", file=self.stdout)
                except NotImplementedError as e:
                    print(f"\n⚠️ {str(e)}", file=self.stdout)
                except Exception as e:
                    print(f"\n❌ Errore: {str(e)}", file=self.stdout)

        except Exception as e:
            print(f"\n❌ Errore: {str(e)}", file=self.stdout)

    def do_genera(self, arg: str) -> None:
        try:
            def progress_callback(info):
                progress = info.get('value', 0)
                status = info.get('status', '')
                print(f"Progresso: {progress}% - {status}", file=self.stdout)

            print("\nGenerazione script e video in corso...", file=self.stdout)
            items = self.generator.process_recent_posts(
                message_callback=lambda msg: print(msg, file=self.stdout),
                progress_callback=progress_callback
            )

            if items:
                print("\n✅ File generati:", file=self.stdout)
                for item in items:
                    print(f"\n📄 {item['title']}", file=self.stdout)
                    print(f"   📝 Script: {item['script_file']}", file=self.stdout)
                    print(f"   🎥 Video: {item['video_file']}", file=self.stdout)
            else:
                print("\n❌ Nessun file generato.", file=self.stdout)

        except Exception as e:
            print(f"\n❌ Errore: {str(e)}", file=self.stdout)

    def do_help(self, arg: str) -> None:
        if arg:
            super().do_help(arg)
        else:
            print("\nComandi disponibili:", file=self.stdout)
            print("  script  - Genera solo gli script dai post", file=self.stdout)
            print("  video   - Genera video dagli script esistenti", file=self.stdout)
            print("  genera  - Genera sia script che video dai post", file=self.stdout)
            print("  help    - Mostra questo messaggio", file=self.stdout)
            print("  quit    - Esci dal programma", file=self.stdout)
            print(file=self.stdout)

    def do_quit(self, arg: str) -> bool:
        print("\nArrivederci!\n", file=self.stdout)
        return True

    def default(self, line: str) -> None:
        print(f"\n❌ Comando non riconosciuto: {line}", file=self.stdout)
        print("Usa 'help' per vedere i comandi disponibili.", file=self.stdout)

    def emptyline(self) -> None:
        pass

def main():
    try:
        VideoGeneratorCLI().cmdloop()
    except KeyboardInterrupt:
        print("\nArrivederci!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()