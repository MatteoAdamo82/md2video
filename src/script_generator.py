import os
from pathlib import Path
import json
from datetime import datetime
import logging
from typing import Dict, Optional

class ScriptGenerator:
    def __init__(self, output_dir: str = 'script_output'):
        """
        Inizializza il generatore di script.

        Args:
            output_dir: Directory dove salvare gli script generati
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def generate_script(self, content: Dict, template: Optional[Dict] = None) -> str:
        """
        Genera uno script per video partendo dal contenuto parsato.

        Args:
            content: Dizionario con il contenuto parsato dal MDParser
            template: Template opzionale per personalizzare lo script

        Returns:
            Path del file script generato
        """
        try:
            # Usa template default se non specificato
            if template is None:
                template = {
                    'intro': "Ciao a tutti! Oggi parleremo di {title}",
                    'outro': "Grazie per aver guardato questo video! Non dimenticare di iscriverti al canale!",
                    'transition': "Passiamo ora al prossimo punto..."
                }

            # Crea struttura script
            script_content = {
                'title': content['title'],
                'source_file': content['source_file'],
                'date_created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'slides': [
                    {
                        'type': 'intro',
                        'content': template['intro'].format(title=content['title'])
                    }
                ]
            }

            # Processa ogni sezione
            for section in content['sections']:
                slide = {
                    'type': section.type,
                    'level': section.level,
                    'content': section.content
                }
                script_content['slides'].append(slide)

            # Aggiungi outro
            script_content['slides'].append({
                'type': 'outro',
                'content': template['outro']
            })

            # Genera nome file
            filename = self.output_dir / f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content['title'][:30]}.json"

            # Salva script
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(script_content, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Script generato: {filename}")
            return str(filename)

        except Exception as e:
            self.logger.error(f"Errore nella generazione dello script: {str(e)}")
            raise

    def load_script(self, script_path: str) -> Dict:
        """
        Carica uno script esistente.

        Args:
            script_path: Percorso del file script da caricare

        Returns:
            Contenuto dello script
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Errore nel caricamento dello script: {str(e)}")
            raise

    def update_script(self, script_path: str, updates: Dict) -> str:
        """
        Aggiorna uno script esistente.

        Args:
            script_path: Percorso del file script da aggiornare
            updates: Dizionario con gli aggiornamenti da applicare

        Returns:
            Path del file script aggiornato
        """
        try:
            script = self.load_script(script_path)
            script.update(updates)

            with open(script_path, 'w', encoding='utf-8') as f:
                json.dump(script, f, ensure_ascii=False, indent=2)

            return script_path

        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento dello script: {str(e)}")
            raise