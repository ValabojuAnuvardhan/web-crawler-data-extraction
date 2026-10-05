"""
Unit tests for HTMLParser: titles, headings (h1-h6), paragraphs, links, images, and metadata extraction.
"""

from app.parser.html_parser import HTMLParser
from app.models.page import ExtractedContent

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Algoryx Engineering Portal - Task 4</title>
    <meta name="description" content="Next-generation intelligent web systems and crawlers.">
    <meta name="keywords" content="web crawler, python, data engineering, algoryx">
    <meta name="author" content="Valaboju Anuvardhan">
    <link rel="canonical" href="https://example.com/portal">
    <meta property="og:title" content="OpenGraph Engineering Portal">
</head>
<body>
    <header>
        <h1>Algoryx Web Systems</h1>
        <h2>Scalable Architecture</h2>
        <h3>Subheading Level 3</h3>
        <h4>Subheading Level 4</h4>
        <h5>Subheading Level 5</h5>
        <h6>Subheading Level 6</h6>
    </header>
    <main>
        <p>Building high-performance platforms that solve real-world problems.</p>
        <p>Clean architecture and production-quality software engineering.</p>
        <a href="/docs/architecture" rel="help">Architecture Guide</a>
        <a href="https://external.org/library">External Reference</a>
        <img src="/assets/logo.png" alt="Algoryx Company Logo" title="Algoryx Logo">
    </main>
    <script>console.log("Ignore script text");</script>
    <style>.css-code { display: none; }</style>
</body>
</html>
"""


def test_html_parser_extraction():
    parser = HTMLParser()
    content: ExtractedContent = parser.parse(SAMPLE_HTML, base_url="https://example.com/portal")

    # Title
    assert content.title == "Algoryx Engineering Portal - Task 4"

    # All Headings (h1 through h6)
    assert len(content.headings) == 6
    assert content.headings[0].level == 1
    assert content.headings[0].text == "Algoryx Web Systems"
    assert content.headings[1].level == 2
    assert content.headings[1].text == "Scalable Architecture"
    assert content.headings[2].level == 3
    assert content.headings[5].level == 6

    # Paragraphs
    assert len(content.paragraphs) == 2
    assert "high-performance platforms" in content.paragraphs[0]
    assert "production-quality software" in content.paragraphs[1]

    # Links
    assert len(content.links) == 2
    internal = [l for l in content.links if l.is_internal]
    external = [l for l in content.links if not l.is_internal]
    assert len(internal) == 1
    assert internal[0].url == "https://example.com/docs/architecture"
    assert len(external) == 1
    assert external[0].url == "https://external.org/library"

    # Images
    assert len(content.images) == 1
    assert content.images[0].src == "https://example.com/assets/logo.png"
    assert content.images[0].alt == "Algoryx Company Logo"
    assert content.images[0].title == "Algoryx Logo"

    # Metadata
    assert content.metadata.description == "Next-generation intelligent web systems and crawlers."
    assert "web crawler" in content.metadata.keywords
    assert content.metadata.author == "Valaboju Anuvardhan"
    assert content.metadata.canonical == "https://example.com/portal"

    # Script and style excluded from raw text
    assert "Ignore script text" not in content.raw_text
    assert ".css-code" not in content.raw_text
    assert content.word_count > 10


def test_html_parser_fallback_title():
    # Fallback to OpenGraph title when <title> is absent
    og_html = """
    <html>
      <head><meta property="og:title" content="OpenGraph Fallback"></head>
      <body><h1>First Heading</h1></body>
    </html>
    """
    parser = HTMLParser()
    og_content = parser.parse(og_html, base_url="https://example.com")
    assert og_content.title == "OpenGraph Fallback"

    # Fallback to <h1> when both <title> and og:title are absent
    h1_html = "<html><body><h1>Direct Heading Title</h1></body></html>"
    h1_content = parser.parse(h1_html, base_url="https://example.com")
    assert h1_content.title == "Direct Heading Title"
