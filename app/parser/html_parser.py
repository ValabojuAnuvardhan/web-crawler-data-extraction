"""
HTML parsing engine using BeautifulSoup to extract structured human-readable content.
"""

import re
from typing import List, Optional
from bs4 import BeautifulSoup

from app.models.page import (
    HeadingItem,
    LinkItem,
    ImageItem,
    PageMetadata,
    ExtractedContent,
)
from app.utils.url_utils import resolve_url, is_internal_url
from app.utils.logger import get_logger

logger = get_logger("parser")

# Non-content tags stripped before extracting body text
IGNORED_TAGS = {"script", "style", "noscript", "svg", "template", "iframe"}


class HTMLParser:
    """Parses raw HTML text and extracts structured elements using BeautifulSoup."""

    def __init__(self, parser: str = "lxml"):
        self.parser = parser
        self._verify_backend()

    def _verify_backend(self) -> None:
        """Verifies if lxml is available, otherwise falls back to html.parser."""
        try:
            BeautifulSoup("<html></html>", self.parser)
        except Exception:
            logger.warning(f"Parser '{self.parser}' unavailable. Falling back to 'html.parser'.")
            self.parser = "html.parser"

    def parse(self, html: str, base_url: str) -> ExtractedContent:
        """
        Parses HTML string and extracts title, headings, paragraphs, links, images, and metadata.

        Args:
            html: Raw HTML content string.
            base_url: The URL of the page used to resolve relative links.

        Returns:
            ExtractedContent instance with extracted structured elements.
        """
        if not html or not isinstance(html, str):
            return ExtractedContent()

        soup = BeautifulSoup(html, self.parser)

        title = self._extract_title(soup)
        metadata = self._extract_metadata(soup, base_url)
        headings = self._extract_headings(soup)
        links = self._extract_links(soup, base_url)
        images = self._extract_images(soup, base_url)

        # Decompose script and style tags to extract human-readable text
        clean_soup = BeautifulSoup(str(soup), "html.parser")
        for tag in clean_soup.find_all(IGNORED_TAGS):
            tag.decompose()

        paragraphs = self._extract_paragraphs(clean_soup)
        raw_text = self._extract_raw_text(clean_soup)
        word_count = len(re.findall(r"\b\w+\b", raw_text))

        return ExtractedContent(
            title=title,
            headings=headings,
            paragraphs=paragraphs,
            links=links,
            images=images,
            metadata=metadata,
            raw_text=raw_text,
            word_count=word_count,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extracts page title from <title>, OpenGraph og:title, or first <h1>."""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            if title:
                return title

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return str(og_title["content"]).strip()

        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        return ""

    def _extract_metadata(self, soup: BeautifulSoup, base_url: str) -> PageMetadata:
        """Extracts description, keywords, author, and OpenGraph tags."""
        meta = PageMetadata()

        # Canonical link
        canonical = soup.find("link", rel=lambda r: r and "canonical" in r)
        if canonical and canonical.get("href"):
            meta.canonical = resolve_url(base_url, canonical["href"]) or canonical["href"]

        # Meta tags
        for tag in soup.find_all("meta"):
            name = tag.get("name", "").lower()
            prop = tag.get("property", "").lower()
            content = tag.get("content", "").strip()

            if not content:
                continue

            if name == "description" and not meta.description:
                meta.description = content
            elif name == "keywords" and not meta.keywords:
                meta.keywords = [k.strip() for k in content.split(",") if k.strip()]
            elif name == "author" and not meta.author:
                meta.author = content
            elif prop == "og:title" and not meta.og_title:
                meta.og_title = content
            elif prop == "og:description" and not meta.og_description:
                meta.og_description = content
            elif prop == "og:image" and not meta.og_image:
                meta.og_image = resolve_url(base_url, content) or content
            elif name or prop:
                meta.extra[name or prop] = content

        # Fallback description to og:description if missing
        if not meta.description and meta.og_description:
            meta.description = meta.og_description

        return meta

    def _extract_headings(self, soup: BeautifulSoup) -> List[HeadingItem]:
        """Extracts all h1-h6 headings in chronological order."""
        headings: List[HeadingItem] = []
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            text = tag.get_text(separator=" ", strip=True)
            if text:
                try:
                    level = int(tag.name[1])
                    headings.append(HeadingItem(level=level, text=text))
                except (ValueError, IndexError):
                    continue
        return headings

    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """Extracts substantive paragraph text (<p> tags)."""
        paragraphs: List[str] = []
        for p in soup.find_all("p"):
            text = p.get_text(separator=" ", strip=True)
            # Filter out trivially short tags
            if len(text) >= 5:
                cleaned = " ".join(text.split())
                paragraphs.append(cleaned)
        return paragraphs

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[LinkItem]:
        """Extracts hyperlinks and classifies internal vs external status."""
        links: List[LinkItem] = []
        seen = set()

        for a in soup.find_all("a", href=True):
            raw_href = a.get("href")
            resolved = resolve_url(base_url, raw_href)

            if not resolved or resolved in seen:
                continue

            seen.add(resolved)
            anchor_text = a.get_text(separator=" ", strip=True)
            is_internal = is_internal_url(resolved, base_url)

            links.append(
                LinkItem(
                    url=resolved,
                    text=anchor_text,
                    is_internal=is_internal,
                )
            )

        return links

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[ImageItem]:
        """Extracts images and resolves source paths."""
        images: List[ImageItem] = []
        seen = set()

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue

            resolved_src = resolve_url(base_url, src)
            if not resolved_src or resolved_src in seen:
                continue

            seen.add(resolved_src)
            alt = img.get("alt", "").strip()
            title = img.get("title", "").strip() or None

            images.append(
                ImageItem(
                    src=resolved_src,
                    alt=alt,
                    title=title,
                )
            )

        return images

    def _extract_raw_text(self, soup: BeautifulSoup) -> str:
        """Extracts clean human-readable body text."""
        body = soup.find("body") or soup
        text = body.get_text(separator=" ", strip=True)
        return " ".join(text.split())
