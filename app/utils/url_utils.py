"""
URL utilities for canonicalization, resolution, validation, and domain boundary checking.
"""

from typing import Optional, Set
from urllib.parse import (
    urljoin,
    urlparse,
    urlunparse,
    parse_qsl,
    urlencode,
    urldefrag,
)

# Common analytics tracking parameters to strip for clean deduplication
TRACKING_PARAMS: Set[str] = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
    "ref_src",
}

# Non-HTML static file extensions to skip during crawling
IGNORED_EXTENSIONS: Set[str] = {
    ".pdf", ".zip", ".tar", ".gz", ".rar", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv",
    ".css", ".js", ".json", ".xml", ".woff", ".woff2", ".ttf",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
}


def is_valid_url(url: str) -> bool:
    """Verifies that a URL has a valid http/https scheme and hostname."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    Normalizes a URL to ensure reliable duplicate prevention.
    - Strips fragment identifiers (#...)
    - Lowercases scheme and hostname
    - Removes default ports (:80, :443)
    - Strips tracking query parameters (e.g. utm_source)
    - Sorts query parameters for consistent hash representation
    - Normalizes trailing slashes on path
    """
    if not url:
        return ""

    url, _ = urldefrag(url.strip())
    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip default ports
    if (scheme == "http" and netloc.endswith(":80")) or (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc.rsplit(":", 1)[0]

    # Normalize path
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Strip tracking parameters and sort remaining queries
    query_str = ""
    if parsed.query:
        query_items = parse_qsl(parsed.query, keep_blank_values=True)
        filtered = [
            (k, v) for k, v in query_items
            if k.lower() not in TRACKING_PARAMS
        ]
        filtered.sort(key=lambda item: item[0])
        query_str = urlencode(filtered)

    return urlunparse((scheme, netloc, path, parsed.params, query_str, ""))


def resolve_url(base_url: str, link: str) -> Optional[str]:
    """
    Resolves relative or partial links to absolute URLs against the base URL.
    Discards non-HTTP protocols (javascript:, mailto:, tel:).
    """
    if not link or not isinstance(link, str):
        return None

    cleaned_link = link.strip()
    if not cleaned_link:
        return None

    # Filter out non-web protocol schemes
    lower = cleaned_link.lower()
    if lower.startswith(("javascript:", "mailto:", "tel:", "data:", "ftp:", "android-app:")):
        return None

    try:
        joined = urljoin(base_url, cleaned_link)
        if is_valid_url(joined):
            return normalize_url(joined)
        return None
    except Exception:
        return None


def get_domain(url: str) -> str:
    """Extracts the lowercased network hostname from a URL."""
    try:
        return urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return ""


def is_internal_url(url: str, base_url: str) -> bool:
    """
    Checks if target URL shares the exact same hostname as the base/seed URL.
    Ensures the crawler stays strictly on the seed domain.
    """
    url_host = get_domain(url)
    base_host = get_domain(base_url)
    if not url_host or not base_host:
        return False
    return url_host == base_host


def is_crawlable_resource(url: str) -> bool:
    """
    Checks whether a URL points to an HTML resource rather than a static asset or binary file.
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        return not any(path.endswith(ext) for ext in IGNORED_EXTENSIONS)
    except Exception:
        return True
