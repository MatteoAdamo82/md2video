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
        """Rimuove emoji mantenendo apostrofi, punteggiatura e caratteri speciali essenziali"""
        # Rimuove solo emoji mantenendo apostrofi e altri caratteri necessari
        text = emoji.replace_emoji(text, '')
        # Permette apostrofi (sia dritti che curvi) e caratteri essenziali
        text = re.sub(r'[^\w\s,.!?;:\'\'-]', '', text)
        return ' '.join(text.split())

    def parse_paragraph(self, text: str) -> list:
        """Analizza un paragrafo e lo divide in componenti (testo e liste)"""
        components = []
        current_text = []
        current_list = []
        list_started = False

        lines = text.split('\n')

        for line in lines:
            # Pattern per liste numerate (1. o 1) o lettere (a. o a))
            numbered_list = re.match(r'^\s*(?:\d+|[a-z])[).]\s+(.+)$', line.strip())
            # Pattern per liste puntate
            bulleted_list = re.match(r'^\s*[-*•]\s+(.+)$', line.strip())

            if numbered_list or bulleted_list:
                # Se c'era del testo prima della lista, salvalo
                if current_text and not list_started:
                    components.append({
                        "type": "text",
                        "content": ' '.join(current_text)
                    })
                    current_text = []

                list_started = True
                list_item = numbered_list.group(1) if numbered_list else bulleted_list.group(1)
                current_list.append(list_item)
            else:
                # Se era in corso una lista, salvala
                if list_started:
                    components.append({
                        "type": "list",
                        "items": current_list
                    })
                    current_list = []
                    list_started = False

                if line.strip():
                    current_text.append(line.strip())

        # Gestione degli ultimi elementi
        if current_text and not list_started:
            components.append({
                "type": "text",
                "content": ' '.join(current_text)
            })
        if current_list:
            components.append({
                "type": "list",
                "items": current_list
            })

        return components

    def create_speech_segments(self, text: str) -> list:
        """Divide il testo in segmenti naturali con pause appropriate"""
        segments = []

        # Analizza il paragrafo in componenti
        components = self.parse_paragraph(text)

        for component in components:
            if component["type"] == "text":
                # Dividi il testo in frasi
                sentences = re.split(r'([.!?])\s+', component["content"])
                for i in range(0, len(sentences)-1, 2):
                    text = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                    if text.strip():
                        segments.append({
                            "type": "speech",
                            "text": self.clean_text(text),
                            "pause": 0.5 if sentences[i+1] in '.!?' else 0.3
                        })
            elif component["type"] == "list":
                segments.append({
                    "type": "list",
                    "items": [self.clean_text(item) for item in component["items"]]
                })

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
                    if segment["type"] == "speech":
                        speech = ET.SubElement(sec, "speech", pause=str(segment["pause"]))
                        speech.text = segment["text"]
                    elif segment["type"] == "list":
                        list_elem = ET.SubElement(sec, "list")
                        for item in segment["items"]:
                            list_item = ET.SubElement(list_elem, "item", pause="0.3")
                            list_item.text = item

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
                } for speech in section.findall("speech")],
                "lists": [{
                    "items": [{
                        "text": item.text,
                        "pause": float(item.get("pause", 0.3))
                    } for item in list_elem.findall("item")]
                } for list_elem in section.findall("list")]
            })
        return sections

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