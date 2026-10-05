"""
Unit tests for JSONExporter and CSVExporter.
"""

import json
import csv
import tempfile
from pathlib import Path
from app.models.page import (
    CrawledPage,
    ExtractedContent,
    HeadingItem,
    LinkItem,
    ImageItem,
    PageMetadata,
)
from app.exporter.json_exporter import JSONExporter
from app.exporter.csv_exporter import CSVExporter


def _create_sample_page() -> CrawledPage:
    return CrawledPage(
        url="https://example.com/test",
        canonical_url="https://example.com/test",
        depth=0,
        status_code=200,
        response_time_ms=85.2,
        content_length=512,
        content=ExtractedContent(
            title="Export Test Title",
            headings=[HeadingItem(level=1, text="Main Heading")],
            paragraphs=["This is a test paragraph for export."],
            links=[LinkItem(url="https://example.com/sub", text="Sub Page", is_internal=True)],
            images=[ImageItem(src="https://example.com/img.jpg", alt="Test Alt")],
            metadata=PageMetadata(description="Test Description"),
            raw_text="Main Heading This is a test paragraph for export.",
            word_count=8,
        ),
    )


def test_json_exporter():
    with tempfile.TemporaryDirectory() as tmp:
        exporter = JSONExporter(output_dir=tmp)
        page = _create_sample_page()
        json_file = exporter.export([page], metadata={"test_run": True})

        assert json_file.exists()
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["total_pages"] == 1
        assert data["metadata"]["test_run"] is True
        assert data["pages"][0]["url"] == "https://example.com/test"
        assert data["pages"][0]["content"]["title"] == "Export Test Title"


def test_csv_exporter():
    with tempfile.TemporaryDirectory() as tmp:
        exporter = CSVExporter(output_dir=tmp)
        page = _create_sample_page()
        csv_file = exporter.export([page])

        assert csv_file.exists()
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["URL"] == "https://example.com/test"
        assert rows[0]["Title"] == "Export Test Title"
        assert rows[0]["HTTP Status"] == "200"
        assert rows[0]["Headings"] == "[1] Main Heading"
        assert rows[0]["Paragraph Count"] == "1"
        assert rows[0]["Link Count"] == "1"
        assert rows[0]["Image Count"] == "1"
