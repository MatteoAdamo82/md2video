import os
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import emoji
from datetime import datetime
from typing import Dict, Tuple

class ScriptGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.intro_text = os.getenv('VIDEO_INTRO_TEXT', 'Ciao a tutti e bentornati sul canale!')
        self.outro_text = os.getenv('VIDEO_OUTRO_TEXT', 'Grazie per aver guardato questo video!')
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def clean_text(self, text: str) -> str:
        """Rimuove emoji e caratteri speciali mantenendo la punteggiatura essenziale"""
        text = emoji.replace_emoji(text, '')
        text = re.sub(r'[^\w\s,.!?;:-]', '', text)
        return ' '.join(text.split())

    def create_speech_segments(self, text: str) -> list:
        """Divide il testo in segmenti naturali con pause appropriate"""
        segments = []
        sentences = re.split(r'([.!?])\s+', text)

        for i in range(0, len(sentences)-1, 2):
            text = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
            pause = 0.5 if sentences[i+1] in '.!?' else 0.3
            segments.append({"text": text, "pause": pause})

        return segments

    def generate_xml_script(self, post: Dict) -> Tuple[str, str]:
        """Genera uno script XML dal post"""
        root = ET.Element("script", version="1.0")

        # Metadata
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "title").text = post['title']
        ET.SubElement(metadata, "url").text = post['url']
        ET.SubElement(metadata, "date").text = post['date']

        content = ET.SubElement(root, "content")

        # Introduzione
        intro = ET.SubElement(content, "section", level="1", type="intro")
        ET.SubElement(intro, "heading").text = "Introduzione"
        speech = ET.SubElement(intro, "speech", pause="0.5")
        speech.text = self.clean_text(self.intro_text)
        intro_speech = ET.SubElement(intro, "speech", pause="0.5")
        intro_speech.text = f"Oggi parleremo di {self.clean_text(post['title'])}"

        # Contenuto principale
        for section in post['sections']:
            sec = ET.SubElement(content, "section",
                              level=str(section['level']),
                              type="content")

            if section['title']:
                ET.SubElement(sec, "heading").text = self.clean_text(section['title'])

            for para in section['content']:
                segments = self.create_speech_segments(para)
                for segment in segments:
                    speech = ET.SubElement(sec, "speech",
                                         pause=str(segment['pause']))
                    speech.text = self.clean_text(segment['text'])

        # Conclusione
        outro = ET.SubElement(content, "section", level="1", type="outro")
        ET.SubElement(outro, "heading").text = "Conclusione"
        speech = ET.SubElement(outro, "speech", pause="1.0")
        speech.text = self.clean_text(self.outro_text)

        # Formatta XML in modo leggibile
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

        # Salva il file
        filename = f"script_{post['title'][:30]}_{datetime.now():%Y%m%d_%H%M%S}.xml"
        filepath = Path(self.output_dir) / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_str)

        return str(filepath), xml_str


class ScriptParser:
    def __init__(self):
        self.tree = None
        self.root = None

    def load_script(self, xml_path: str):
        """Carica e valida lo script XML"""
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()

        if self.root.tag != "script":
            raise ValueError("Invalid script format")

    def get_metadata(self) -> dict:
        """Estrae i metadata dallo script"""
        metadata = self.root.find("metadata")
        return {
            "title": metadata.find("title").text,
            "url": metadata.find("url").text,
            "date": metadata.find("date").text
        }

    def get_sections(self) -> list:
        """Estrae le sezioni con il testo da sintetizzare"""
        sections = []
        for section in self.root.find("content").findall("section"):
            sections.append({
                "level": int(section.get("level")),
                "type": section.get("type"),
                "heading": section.find("heading").text if section.find("heading") is not None else "",
                "speeches": [{
                    "text": speech.text,
                    "pause": float(speech.get("pause", 0.5))
                } for speech in section.findall("speech")]
            })
        return sections