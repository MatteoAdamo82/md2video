import pytest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET
from pathlib import Path
from src.processors.script_processor import ScriptProcessor

@pytest.fixture
def sample_post():
    return {
        'title': 'Test Post',
        'url': 'https://example.com/test',
        'date': '2024-01-01',
        'content': 'Test content',
        'sections': [
            {
                'level': 1,
                'title': 'Introduction',
                'content': ['First paragraph', 'Second paragraph']
            },
            {
                'level': 2,
                'title': 'Section 1',
                'content': [
                    'Content paragraph',
                    '- List item 1',
                    '- List item 2'
                ]
            }
        ]
    }

@pytest.fixture
def script_processor(tmp_path):
    with patch('src.base_processor.Config') as mock_config:  # Cambio qui: patchiamo Config nel base_processor
        mock_config.return_value.SCRIPT_DIR = tmp_path
        mock_config.return_value.INTRO_TEXT = "Welcome"
        mock_config.return_value.OUTRO_TEXT = "Thanks"
        return ScriptProcessor()

def test_create_xml_structure(script_processor, sample_post):
    root = script_processor._create_xml_structure(sample_post)

    # Verifica struttura base
    assert root.tag == 'script'
    assert root.get('version') == '1.0'

    # Verifica metadata
    metadata = root.find('metadata')
    assert metadata is not None
    assert metadata.find('title').text == 'Test Post'
    assert metadata.find('url').text == 'https://example.com/test'
    assert metadata.find('date').text == '2024-01-01'

    # Verifica content
    content = root.find('content')
    assert content is not None
    sections = content.findall('section')
    assert len(sections) > 0

def test_format_xml(script_processor):
    root = ET.Element('script', version='1.0')
    ET.SubElement(root, 'test').text = 'content'

    formatted = script_processor._format_xml(root)
    assert '<?xml version="1.0" ?>' in formatted
    assert '<script version="1.0">' in formatted
    assert '<test>content</test>' in formatted

def test_save_script(script_processor, tmp_path):
    xml_content = '<?xml version="1.0" ?><script><test>content</test></script>'
    filepath = script_processor._save_script(xml_content, 'Test Title')

    assert filepath.exists()
    assert filepath.suffix == '.xml'
    with open(filepath) as f:
        content = f.read()
        assert 'content' in content

    intro = content.find('section')
    assert intro is not None
    assert isinstance(filepath, Path)

def test_add_outro_section(script_processor):
    content = ET.Element('content')
    script_processor._add_outro_section(content)

    outro = content.find('section')
    assert outro is not None
    assert outro.get('level') == '1'
    assert outro.get('type') == 'outro'
    assert outro.find('heading').text == 'Conclusione'
    assert outro.find('speech').text == "Thanks"

def test_add_content_section(script_processor):
    content = ET.Element('content')
    section_data = {
        'level': 2,
        'title': 'Test Section',
        'content': ['Paragraph 1', '- List item 1', '- List item 2']
    }

    script_processor._add_content_section(content, section_data)

    section = content.find('section')
    assert section is not None
    assert section.get('level') == '2'
    assert section.get('type') == 'content'
    assert section.find('heading').text == 'Test Section'
    speeches = section.findall('speech')
    assert len(speeches) > 0

def test_parse_paragraph_components(script_processor):
    # Test paragrafo normale
    components = script_processor._parse_paragraph_components("Normal paragraph text")
    assert len(components) == 1
    assert components[0]['type'] == 'text'

    # Test lista puntata
    components = script_processor._parse_paragraph_components("- Item 1\n- Item 2")
    assert len(components) == 1
    assert components[0]['type'] == 'list'
    assert len(components[0]['items']) == 2

    # Test lista numerata
    components = script_processor._parse_paragraph_components("1. Item 1\n2. Item 2")
    assert len(components) == 1
    assert components[0]['type'] == 'list'
    assert len(components[0]['items']) == 2

def test_split_into_sentences(script_processor):
    text = "First sentence. Second sentence! Third sentence?"
    sentences = script_processor._split_into_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "First sentence."
    assert sentences[1] == "Second sentence!"
    assert sentences[2] == "Third sentence?"

def test_clean_text(script_processor):
    text = "Hello 👋 world! This is a test..."
    cleaned = script_processor._clean_text(text)
    assert "👋" not in cleaned
    assert "Hello world" in cleaned

def test_process_complete(script_processor, sample_post):
    script_file, xml_content = script_processor.process(sample_post)

    assert script_file is not None
    assert xml_content is not None
    assert Path(script_file).exists()
    assert '<?xml version="1.0" ?>' in xml_content
    assert sample_post['title'] in xml_content
