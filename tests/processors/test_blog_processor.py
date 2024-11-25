import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import frontmatter
from datetime import datetime
from src.processors.blog_processor import BlogProcessor

@pytest.fixture
def mock_content_dir(tmp_path):
    post_dir = tmp_path / "content"
    post_dir.mkdir()
    post_file = post_dir / "test_post.md"
    post_file.write_text("""---
title: Test Post
date: 2024-01-01
url: https://example.com/test
---
# Introduction
This is the introduction paragraph.

## First Section
This is the first section content.
- List item 1
- List item 2""")
    return post_dir

@pytest.fixture
def blog_processor(tmp_path):
    with patch('src.base_processor.Config') as mock_config:
        config = mock_config.return_value
        config.CONTENT_DIR = tmp_path / "content"
        config.NUM_POSTS = 5
        return BlogProcessor()

def test_blog_processor_initialization():
    processor = BlogProcessor()
    assert isinstance(processor, BlogProcessor)

def test_process_post(blog_processor):
    file_data = {
        'path': Path('test.md'),
        'date': datetime(2024, 1, 1),
        'metadata': {
            'title': 'Test Post',
            'url': 'https://example.com/test'
        },
        'content': '''# Introduction
This is a test paragraph.

## Section
This is a section paragraph.'''
    }

    result = blog_processor._process_post(file_data)

    assert result is not None
    assert result['title'] == 'Test Post'
    assert result['url'] == 'https://example.com/test'
    assert result['date'] == '2024-01-01'
    assert isinstance(result['sections'], list)
    assert len(result['sections']) > 0

def test_parse_content(blog_processor):
    content = """# Heading 1
Content for heading 1

## Heading 2
Content for heading 2
- List item 1
- List item 2

### Heading 3
Final content"""

    sections = blog_processor._parse_content(content)

    assert len(sections) == 3
    assert sections[0]['level'] == 1
    assert sections[0]['title'] == 'Heading 1'
    assert sections[1]['level'] == 2
    assert 'List item 1' in ' '.join(sections[1]['content'])
    assert sections[2]['level'] == 3

def test_process_with_no_posts(blog_processor, tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with patch('src.base_processor.Config') as mock_config:
        mock_config.return_value.CONTENT_DIR = empty_dir
        result = blog_processor.process()
        assert result == []

def test_process_with_multiple_posts(blog_processor, mock_content_dir):
    # Crea multipli post di test
    for i in range(3):
        post = mock_content_dir / f"post_{i}.md"
        content = f"""---
title: Post {i}
date: 2024-01-0{i+1}
url: https://example.com/post{i}
---
# Post {i}
Content for post {i}"""
        post.write_text(content)

    result = blog_processor.process(num_posts=2)

    assert len(result) == 2  # Dovrebbe limitare a 2 post
    assert result[0]['title'] == 'Post 2'  # Il più recente
    assert result[1]['title'] == 'Post 1'  # Il secondo più recente

def test_error_handling(blog_processor):
    invalid_data = {
        'path': Path('invalid.md'),
        'date': None,
        'metadata': {},
        'content': 'Invalid content'
    }

    result = blog_processor._process_post(invalid_data)
    assert result is None

def test_callback_usage(blog_processor):
    message_mock = Mock()
    progress_mock = Mock()
    blog_processor.set_callbacks(message_mock, progress_mock)

    blog_processor.process()

    message_mock.assert_called_with('📥 Fetching recent posts...')