import os
from pathlib import Path
import frontmatter
import logging
from typing import List, Dict
from datetime import datetime
import re

class BlogParser:
    def __init__(self, content_dir: str):
        self.content_dir = content_dir
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def parse_markdown_content(self, content: str) -> List[Dict]:
        """Parse il contenuto markdown in sezioni strutturate"""
        sections = []
        current_section = {"level": 0, "title": "", "content": []}
        lines = content.split('\n')

        for line in lines:
            # Identifica gli heading
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if heading_match:
                # Se c'era una sezione precedente, salvala
                if current_section["content"]:
                    sections.append(current_section)

                # Crea una nuova sezione
                level = len(heading_match.group(1))  # Numero di #
                title = heading_match.group(2).strip()
                current_section = {
                    "level": level,
                    "title": title,
                    "content": []
                }
            elif line.strip():
                # Aggiunge linee non vuote al contenuto corrente
                current_section["content"].append(line.strip())

        # Aggiungi l'ultima sezione se contiene contenuto
        if current_section["content"]:
            sections.append(current_section)

        return sections

    def fetch_post_content(self, file_path: str) -> str:
        """Recupera il contenuto del post dal file MD"""
        try:
            self.logger.info(f"Reading content from: {file_path}")
            post = frontmatter.load(file_path)
            return post.content

        except Exception as e:
            self.logger.error(f"Error reading post content: {str(e)}")
            return ""

    def fetch_posts(self, num_posts: int = 5) -> List[Dict]:
        """Recupera i post più recenti dalla directory dei contenuti"""
        self.logger.info(f"Fetching {num_posts} posts from {self.content_dir}")

        try:
            md_files = []
            content_path = Path(self.content_dir)

            # Raccoglie tutti i file .md ricorsivamente
            for md_file in content_path.rglob('*.md'):
                post = frontmatter.load(md_file)
                md_files.append({
                    'path': md_file,
                    'date': post.get('date', datetime.min),
                    'metadata': post.metadata
                })

            # Ordina per data decrescente
            md_files.sort(key=lambda x: x['date'], reverse=True)

            posts = []
            for file_data in md_files[:num_posts]:
                self.logger.info(f"Processing post: {file_data['path']}")

                content = self.fetch_post_content(file_data['path'])

                if content:
                    # Parse il contenuto in sezioni strutturate
                    parsed_content = self.parse_markdown_content(content)

                    post = {
                        'title': file_data['metadata'].get('title', ''),
                        'url': file_data['metadata'].get('url', ''),
                        'date': file_data['date'].strftime('%Y-%m-%d'),
                        'content': content,  # contenuto originale
                        'sections': parsed_content  # contenuto strutturato
                    }
                    posts.append(post)
                    self.logger.info(f"Successfully processed: {post['title']}")
                else:
                    self.logger.warning(f"No content found in: {file_data['path']}")

            return posts

        except Exception as e:
            self.logger.error(f"Error processing posts: {str(e)}")
            return []