"""
Unit tests for URLManager: duplicate prevention, normalization, and depth constraints.
"""

from app.crawler.url_manager import URLManager
from app.utils.url_utils import normalize_url, is_valid_url, is_internal_url, resolve_url


def test_url_validation():
    assert is_valid_url("https://example.com") is True
    assert is_valid_url("http://example.com/page") is True
    assert is_valid_url("ftp://example.com") is False
    assert is_valid_url("javascript:void(0)") is False
    assert is_valid_url("") is False


def test_url_normalization():
    # Fragment removal
    assert normalize_url("https://example.com/page#section") == "https://example.com/page"
    # Scheme and hostname lowercasing
    assert normalize_url("HTTPS://EXAMPLE.COM/Page") == "https://example.com/Page"
    # Tracking query stripping
    assert normalize_url("https://example.com/?utm_source=test&id=1") == "https://example.com/?id=1"
    # Port normalization
    assert normalize_url("http://example.com:80/about") == "http://example.com/about"
    assert normalize_url("https://example.com:443/about") == "https://example.com/about"


def test_relative_url_resolution():
    base = "https://example.com/blog/post-1"
    assert resolve_url(base, "/about") == "https://example.com/about"
    assert resolve_url(base, "post-2") == "https://example.com/blog/post-2"
    assert resolve_url(base, "../contact") == "https://example.com/contact"
    assert resolve_url(base, "mailto:test@example.com") is None


def test_internal_url_detection():
    base = "https://example.com/page"
    assert is_internal_url("https://example.com/about", base) is True
    assert is_internal_url("https://sub.example.com/page", base) is False
    assert is_internal_url("https://otherdomain.org/", base) is False


def test_url_manager_queue_and_duplicates():
    manager = URLManager(max_depth=2)

    # First add: successful
    assert manager.add_url("https://example.com/", depth=0) is True
    assert manager.queue_size == 1

    # Exact duplicate: rejected
    assert manager.add_url("https://example.com/", depth=0) is False
    # Canonical duplicate: rejected
    assert manager.add_url("https://example.com/#ref", depth=1) is False
    assert manager.queue_size == 1

    # Exceeds max depth: rejected
    assert manager.add_url("https://example.com/deep", depth=3) is False
    assert manager.queue_size == 1

    # Valid next level: accepted
    assert manager.add_url("https://example.com/page-1", depth=1) is True
    assert manager.queue_size == 2

    # Queue retrieval
    item = manager.get_next_url()
    assert item == ("https://example.com/", 0)
    manager.mark_visited(item[0])
    assert manager.is_visited("https://example.com/") is True
