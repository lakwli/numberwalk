import os
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path
import json
from bs4 import BeautifulSoup

from ..models.article import Article

class ArticleHtmlRepository:
    """
    File-based repository for static articles using HTML files.
    Articles are stored as individual .html files with JSON metadata.
    """

    def __init__(self, content_dir: str = "content/articles"):
        self.content_dir = Path(content_dir)
        self.cache: Dict[str, Article] = {}
        self._ensure_dirs_exist()

    def _ensure_dirs_exist(self) -> None:
        """Ensure all required directories exist."""
        os.makedirs(self.content_dir, exist_ok=True)

    def _parse_html_file(self, file_path: Path) -> Optional[Article]:
        """Parse an HTML file into an Article object."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract metadata from JSON script tag
            meta_tag = soup.find('script', {'id': 'article-metadata', 'type': 'application/json'})
            if not meta_tag:
                raise ValueError("No metadata found in HTML file")
                
            metadata = json.loads(meta_tag.string)
            
            # Extract main content
            content_div = soup.find('div', {'class': 'article-content'})
            if not content_div:
                raise ValueError("No content div found in HTML file")

            # Extract canonical URL from meta tag
            canonical_tag = soup.find('meta', {'name': 'canonical-url'})
            canonical_path = canonical_tag['content'] if canonical_tag and 'content' in canonical_tag.attrs else None
            
            # Get article path relative to content dir
            rel_path = str(file_path.relative_to(self.content_dir)).replace('.html', '')

            # Convert date string to datetime if needed
            updated_at = metadata.get('updated_at')
            if isinstance(updated_at, str):
                # Handle 'Z' timezone designator for older Python versions
                if updated_at.endswith('Z'):
                    updated_at = updated_at[:-1] + '+00:00'
                updated_at = datetime.fromisoformat(updated_at)
            
            return Article(
                path=rel_path,
                title=metadata.get('title', ''),
                description=metadata.get('description', ''),
                content=str(content_div),
                type='article',
                updated_at=updated_at,
                keywords=metadata.get('keywords', []),
                image=metadata.get('image'),
                custom_css_file=metadata.get('custom_css_file'),
                custom_styles=metadata.get('custom_styles'),
                canonical_path=canonical_path # Add the extracted canonical path
            )
        except Exception as e:
            print(f"Error parsing HTML file {file_path}: {e}")
            return None

    def _create_html_content(self, article: Article) -> str:
        """Create HTML content from article."""
        metadata = {
            'title': article.title,
            'description': article.description,
            'type': 'article',
            'updated_at': article.updated_at.isoformat(),
            'keywords': article.keywords,
            'image': article.image,
            'custom_css_file': article.custom_css_file,
            'custom_styles': article.custom_styles
            # Note: canonical_path is not stored in JSON metadata, but directly in HTML meta tag
        }

        canonical_meta_tag = f'<meta name="canonical-url" content="{article.canonical_path}">' if article.canonical_path else ''
        
        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {canonical_meta_tag}
    <title>{article.title}</title>
    <script id="article-metadata" type="application/json">
    {json.dumps(metadata, indent=2)}
    </script>
</head>
<body>
    <article>
        <div class="article-content">
            {article.content}
        </div>
    </article>
</body>
</html>'''
        
        return html_template

    def get_all(self) -> List[Article]:
        """Get all articles."""
        articles = []
        for file_path in self.content_dir.rglob('*.html'):
            if article := self._parse_html_file(file_path):
                articles.append(article)
                self.cache[article.path] = article
        return sorted(articles, key=lambda x: x.updated_at, reverse=True)

    def get_by_path(self, article_path: str) -> Optional[Article]:
        """Get a single article by its path."""
        # Check cache first
        if article_path in self.cache:
            return self.cache[article_path]

        # Look for file
        file_path = self.content_dir / f"{article_path}.html"
        if file_path.exists():
            if article := self._parse_html_file(file_path):
                self.cache[article_path] = article
                return article
        return None

    def create(self, article: Article) -> Article:
        """Create a new article."""
        # Ensure parent directories exist
        file_path = self.content_dir / f"{article.path}.html"
        os.makedirs(file_path.parent, exist_ok=True)

        # Generate HTML content
        html_content = self._create_html_content(article)

        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Update cache
        self.cache[article.path] = article
        return article

    def update(self, article: Article) -> Article:
        """Update an existing article."""
        return self.create(article)  # Same operation as create

    def delete(self, article_path: str) -> bool:
        """Delete an article."""
        file_path = self.content_dir / f"{article_path}.html"
        try:
            if file_path.exists():
                file_path.unlink()
                if article_path in self.cache:
                    del self.cache[article_path]
                return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
        return False
