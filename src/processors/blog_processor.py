from typing import List, Dict
import frontmatter
from datetime import datetime
from pathlib import Path
import re
from ..base_processor import BaseProcessor
import logging

class BlogProcessor(BaseProcessor):
    """Processor for blog posts"""

    def process(self, num_posts: int = None) -> List[Dict]:
        """Retrieve and process the most recent posts"""
        if num_posts is None:
            num_posts = self.config.NUM_POSTS

        self.callback.log_message("📥 Fetching recent posts...")

        try:
            md_files = []
            content_path = Path(self.config.CONTENT_DIR)

            # Collect all .md files recursively
            for md_file in content_path.rglob('*.md'):
                post = frontmatter.load(md_file)
                md_files.append({
                    'path': md_file,
                    'date': post.get('date', datetime.min),
                    'metadata': post.metadata,
                    'content': post.content
                })

            # Sort by date descending
            md_files.sort(key=lambda x: x['date'], reverse=True)

            processed_posts = []
            for file_data in md_files[:num_posts]:
                post = self._process_post(file_data)
                if post:
                    processed_posts.append(post)

            return processed_posts

        except Exception as e:
            self.logger.error(f"Error processing blog posts: {str(e)}")
            raise

    def _process_post(self, file_data: Dict) -> Dict:
        """Process a single post"""
        try:
            sections = self._parse_content(file_data['content'])

            return {
                'title': file_data['metadata'].get('title', ''),
                'url': file_data['metadata'].get('url', ''),
                'date': file_data['date'].strftime('%Y-%m-%d'),
                'content': file_data['content'],
                'sections': sections
            }

        except Exception as e:
            self.logger.error(f"Error processing post {file_data['path']}: {str(e)}")
            return None

    def _parse_content(self, content: str) -> List[Dict]:
        """Parse markdown content into structured sections"""
        sections = []
        current_section = {"level": 0, "title": "", "content": []}

        for line in content.split('\n'):
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if heading_match:
                if current_section["content"]:
                    sections.append(current_section)

                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                current_section = {
                    "level": level,
                    "title": title,
                    "content": []
                }
            elif line.strip():
                current_section["content"].append(line.strip())

        if current_section["content"]:
            sections.append(current_section)

        return sections