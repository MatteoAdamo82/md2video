from typing import Tuple, Dict, List
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import re
import os
import emoji
from ..base_processor import BaseProcessor
import logging

class ScriptProcessor(BaseProcessor):
    """Script generation processor"""

    def process(self, post: Dict) -> Tuple[str, str]:
        """Generate an XML script from the post"""
        try:
            root = self._create_xml_structure(post)
            xml_str = self._format_xml(root)
            filepath = self._save_script(xml_str, post['title'])

            return str(filepath), xml_str

        except Exception as e:
            self.logger.error(f"Error generating script: {str(e)}")
            raise

    def _create_xml_structure(self, post: Dict) -> ET.Element:
        """Create the XML structure of the script"""
        root = ET.Element("script", version="1.0")

        # Metadata
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "title").text = post['title']
        ET.SubElement(metadata, "url").text = post['url']
        ET.SubElement(metadata, "date").text = post['date']

        # Content
        content = ET.SubElement(root, "content")

        # Intro
        self._add_intro_section(content)

        # Main content
        for section in post['sections']:
            self._add_content_section(content, section)

        # Outro
        self._add_outro_section(content)

        return root

    def _format_xml(self, root: ET.Element) -> str:
        """Format XML to be readable"""
        from xml.dom import minidom
        return minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

    def _save_script(self, xml_str: str, title: str) -> Path:
        """Save the script to a file"""
        filename = f"script_{title[:30]}_{datetime.now():%Y%m%d_%H%M%S}.xml"
        filepath = Path(self.config.SCRIPT_DIR) / filename

        self.logger.info(f"=== Script Debug Info ===")
        self.logger.info(f"Config SCRIPT_DIR: {self.config.SCRIPT_DIR}")
        self.logger.info(f"Trying to save script to: {filepath}")
        self.logger.info(f"Current working dir: {os.getcwd()}")
        self.logger.info(f"SCRIPT_DIR exists: {Path(self.config.SCRIPT_DIR).exists()}")
        self.logger.info(f"SCRIPT_DIR is writable: {os.access(self.config.SCRIPT_DIR, os.W_OK)}")

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            self.logger.info(f"Script successfully saved to: {filepath}")
            self.logger.info(f"File exists after save: {filepath.exists()}")
        except Exception as e:
            self.logger.error(f"Error saving script: {str(e)}")
            raise

        return filepath

    def _add_intro_section(self, content: ET.Element):
        intro = ET.SubElement(content, "section", level="1", type="intro")
        ET.SubElement(intro, "heading").text = "Introduzione"
        ET.SubElement(intro, "speech", pause="0.5").text = self.config.INTRO_TEXT

    def _add_outro_section(self, content: ET.Element):
        outro = ET.SubElement(content, "section", level="1", type="outro")
        ET.SubElement(outro, "heading").text = "Conclusione"
        ET.SubElement(outro, "speech", pause="1.0").text = self.config.OUTRO_TEXT

    def _add_content_section(self, content: ET.Element, section: Dict):
        sec = ET.SubElement(content, "section",
                          level=str(section['level']),
                          type="content")

        if section['title']:
            ET.SubElement(sec, "heading").text = section['title']

        for para in section['content']:
            self._add_paragraph_content(sec, para)

    def _add_paragraph_content(self, section: ET.Element, paragraph: str):
        """Adds paragraph content, handling both text and lists"""
        components = self._parse_paragraph_components(paragraph)

        for component in components:
            if component['type'] == 'text':
                ## Splits text into natural sentences
                sentences = self._split_into_sentences(component['content'])
                for sentence in sentences:
                    if sentence.strip():
                        speech = ET.SubElement(section, "speech")
                        speech.text = self._clean_text(sentence)
                        # Longer pause for full stops and exclamation marks
                        speech.set("pause", "0.7" if sentence.rstrip()[-1] in '.!?' else "0.3")

            elif component['type'] == 'list':
                list_elem = ET.SubElement(section, "list")
                for item in component['items']:
                    list_item = ET.SubElement(list_elem, "item", pause="0.3")
                    list_item.text = self._clean_text(item)

    def _parse_paragraph_components(self, paragraph: str) -> List[Dict]:
        """Paragraph parses and divides it into components (text and lists)"""
        components = []
        current_text = []
        current_list = []
        list_started = False

        lines = paragraph.split('\n')

        for line in lines:
            # Pattern for numbered lists (1. or 1) or letters (a. or a))
            numbered_list = re.match(r'^\s*(?:\d+|[a-z])[).]\s+(.+)$', line.strip())
            # Pattern for bulleted lists
            bulleted_list = re.match(r'^\s*[-*•]\s+(.+)$', line.strip())

            if numbered_list or bulleted_list:
                # If there was text before the list, save it
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
                # If there was a list in progress, save it
                if list_started:
                    components.append({
                        "type": "list",
                        "items": current_list
                    })
                    current_list = []
                    list_started = False

                if line.strip():
                    current_text.append(line.strip())

        # Managing the latest elements
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

    def _split_into_sentences(self, text: str) -> List[str]:
        """Divide text into natural sentences"""
        # Punctuation-preserving sentence division pattern
        pattern = r'([.!?])\s+'
        sentences = []

        # Split text using pattern
        parts = re.split(pattern, text)

        # Reconstructs sentences with punctuation
        for i in range(0, len(parts)-1, 2):
            sentence = parts[i] + (parts[i+1] if i+1 < len(parts) else '')
            sentences.append(sentence)

        # Adds the last part if exists
        if len(parts) % 2 == 1:
            sentences.append(parts[-1])

        return [s.strip() for s in sentences if s.strip()]

    def _clean_text(self, text: str) -> str:
        """Cleans up text while maintaining essential punctuation"""
        # Remove emoji
        text = emoji.replace_emoji(text, '')

        # Removes unnecessary characters while keeping punctuation and apostrophes
        text = re.sub(r'[^\w\s,.!?;:\'\'-]', '', text)

        # Remove multiple spaces
        text = ' '.join(text.split())

        return text