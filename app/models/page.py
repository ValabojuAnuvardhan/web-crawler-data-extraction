"""
Structured data models representing extracted webpage content and crawl records.
Uses Python dataclasses with type hints.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any


@dataclass
class HeadingItem:
    """Represents an HTML heading element (h1-h6)."""
    level: int
    text: str


@dataclass
class LinkItem:
    """Represents a hyperlink found on a crawled page."""
    url: str
    text: str = ""
    is_internal: bool = True


@dataclass
class ImageItem:
    """Represents an image element found on a page."""
    src: str
    alt: str = ""
    title: Optional[str] = None


@dataclass
class PageMetadata:
    """Represents metadata tags extracted from HTML head."""
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    author: Optional[str] = None
    canonical: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExtractedContent:
    """Clean structured content extracted from parsed HTML."""
    title: str = ""
    headings: List[HeadingItem] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)
    links: List[LinkItem] = field(default_factory=list)
    images: List[ImageItem] = field(default_factory=list)
    metadata: PageMetadata = field(default_factory=PageMetadata)
    raw_text: str = ""
    word_count: int = 0


@dataclass
class CrawledPage:
    """
    Complete record of a crawled webpage including network diagnostics,
    status code, crawl depth, and extracted content.
    """
    url: str
    canonical_url: str = ""
    depth: int = 0
    status_code: int = 0
    response_time_ms: float = 0.0
    content_length: int = 0
    content: Optional[ExtractedContent] = None
    error: Optional[str] = None
    crawled_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Converts the CrawledPage instance to a clean dictionary."""
        return asdict(self)

    def to_flat_dict(self) -> Dict[str, Any]:
        """
        Flattens page attributes for tabular (CSV) export.
        Avoids embedding raw Python objects into CSV cells.
        """
        content = self.content or ExtractedContent()
        meta = content.metadata or PageMetadata()

        # Format headings into a concise readable string
        headings_summary = " | ".join(f"[{h.level}] {h.text}" for h in content.headings[:5])

        # Short body preview
        body_preview = " ".join(content.paragraphs[:2])
        if len(body_preview) > 160:
            body_preview = body_preview[:157] + "..."

        return {
            "URL": self.url,
            "Title": content.title,
            "HTTP Status": self.status_code,
            "Depth": self.depth,
            "Response Time (ms)": round(self.response_time_ms, 2),
            "Word Count": content.word_count,
            "Headings Count": len(content.headings),
            "Headings": headings_summary,
            "Paragraph Count": len(content.paragraphs),
            "Body Preview": body_preview,
            "Link Count": len(content.links),
            "Image Count": len(content.images),
            "Meta Description": meta.description or "",
            "Meta Keywords": ", ".join(meta.keywords),
            "Error": self.error or "",
            "Crawled At": self.crawled_at,
        }
