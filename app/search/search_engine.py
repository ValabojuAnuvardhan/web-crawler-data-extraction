"""
In-memory keyword search engine performing case-insensitive search and snippet ranking.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from app.models.page import CrawledPage


@dataclass
class SearchResult:
    """Represents a matched webpage from a search query."""
    url: str
    title: str
    snippet: str
    matches_count: int


class SearchEngine:
    """Executes case-insensitive keyword searches over collected crawl datasets."""

    def search(self, query: str, pages: List[CrawledPage], limit: int = 20) -> List[SearchResult]:
        """
        Searches a list of CrawledPage objects for the specified keyword or phrase.

        Args:
            query: Keyword or search phrase.
            pages: List of crawled page records.
            limit: Maximum results to return.

        Returns:
            List of SearchResult objects sorted by match frequency descending.
        """
        cleaned_query = query.strip()
        if not cleaned_query or not pages:
            return []

        pattern = re.compile(re.escape(cleaned_query), re.IGNORECASE)
        results: List[SearchResult] = []

        for page in pages:
            if not page.content:
                continue

            content = page.content
            meta = content.metadata
            headings_text = " ".join(h.text for h in content.headings)
            paragraphs_text = " ".join(content.paragraphs)
            meta_text = f"{meta.description or ''} {' '.join(meta.keywords)}"
            raw_text = content.raw_text or ""

            combined = f"{content.title} {headings_text} {paragraphs_text} {raw_text} {meta_text}"
            matches = list(pattern.finditer(combined))

            if matches:
                snippet = self._generate_snippet(combined, cleaned_query)
                results.append(
                    SearchResult(
                        url=page.url,
                        title=content.title or "Untitled Page",
                        snippet=snippet,
                        matches_count=len(matches),
                    )
                )

        # Sort by match frequency descending
        results.sort(key=lambda r: r.matches_count, reverse=True)
        return results[:limit]

    def search_from_file(self, query: str, json_path: str, limit: int = 20) -> List[SearchResult]:
        """Loads a previously exported JSON dataset and runs a keyword search."""
        path = Path(json_path)
        if not path.exists():
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_pages = data.get("pages", [])
        from app.models.page import (
            HeadingItem, LinkItem, ImageItem, PageMetadata, ExtractedContent
        )

        crawled_pages: List[CrawledPage] = []
        for p in raw_pages:
            c = p.get("content") or {}
            m = c.get("metadata") or {}
            content = ExtractedContent(
                title=c.get("title", ""),
                headings=[HeadingItem(level=h["level"], text=h["text"]) for h in c.get("headings", [])],
                paragraphs=c.get("paragraphs", []),
                links=[LinkItem(url=l["url"], text=l.get("text", ""), is_internal=l.get("is_internal", True)) for l in c.get("links", [])],
                images=[ImageItem(src=img["src"], alt=img.get("alt", ""), title=img.get("title")) for img in c.get("images", [])],
                metadata=PageMetadata(
                    description=m.get("description"),
                    keywords=m.get("keywords", []),
                    author=m.get("author"),
                ),
                raw_text=c.get("raw_text", ""),
                word_count=c.get("word_count", 0),
            )
            crawled_pages.append(
                CrawledPage(
                    url=p["url"],
                    canonical_url=p.get("canonical_url", p["url"]),
                    depth=p.get("depth", 0),
                    status_code=p.get("status_code", 200),
                    content=content,
                )
            )

        return self.search(query, crawled_pages, limit=limit)

    def _generate_snippet(self, text: str, query: str, max_len: int = 160) -> str:
        """Extracts context window surrounding the first match."""
        idx = text.lower().find(query.lower())
        if idx == -1:
            return text[:max_len] + ("..." if len(text) > max_len else "")

        start = max(0, idx - 50)
        end = min(len(text), idx + len(query) + 80)

        snippet = text[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet
