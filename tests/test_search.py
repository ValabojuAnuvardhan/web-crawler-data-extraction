"""
Unit tests for SearchEngine: keyword search, case-insensitivity, and snippets.
"""

from app.models.page import (
    CrawledPage,
    ExtractedContent,
    HeadingItem,
    PageMetadata,
)
from app.search.search_engine import SearchEngine


def _create_searchable_pages():
    p1 = CrawledPage(
        url="https://example.com/python-guide",
        content=ExtractedContent(
            title="Modern Python Development",
            headings=[HeadingItem(level=1, text="Asynchronous Python Programming")],
            paragraphs=["Python 3.11 introduces faster execution and clean asyncio semantics."],
            metadata=PageMetadata(description="Comprehensive Python tutorial"),
        ),
    )
    p2 = CrawledPage(
        url="https://example.com/docker-guide",
        content=ExtractedContent(
            title="Containerization with Docker",
            headings=[HeadingItem(level=1, text="Building Containers")],
            paragraphs=["Docker enables consistent deployments across clouds."],
            metadata=PageMetadata(description="Learn Docker basics"),
        ),
    )
    return [p1, p2]


def test_keyword_search():
    engine = SearchEngine()
    pages = _create_searchable_pages()

    # Case-insensitive match on paragraph and title
    results = engine.search("python", pages)
    assert len(results) == 1
    assert results[0].url == "https://example.com/python-guide"
    assert results[0].matches_count >= 2
    assert "python" in results[0].snippet.lower()

    # Match in another document
    docker_results = engine.search("docker", pages)
    assert len(docker_results) == 1
    assert docker_results[0].url == "https://example.com/docker-guide"

    # Non-existent keyword
    no_results = engine.search("kubernetes", pages)
    assert len(no_results) == 0
