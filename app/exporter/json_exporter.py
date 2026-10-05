"""
Structured JSON exporter preserving nested content and metadata.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.models.page import CrawledPage
from app.utils.logger import get_logger

logger = get_logger("exporter.json")


class JSONExporter:
    """Exports crawled page datasets to structured JSON files."""

    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        pages: List[CrawledPage],
        filepath: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        indent: int = 2,
    ) -> Path:
        """
        Exports a list of CrawledPage objects into a well-formatted JSON document.

        Args:
            pages: List of crawled page records.
            filepath: Destination file path.
            metadata: Optional summary statistics or crawl configuration.
            indent: Indentation spaces for readability.

        Returns:
            Path to the written JSON file.
        """
        target = Path(filepath) if filepath else self.output_dir / "crawl_output.json"
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "metadata": metadata or {},
            "total_pages": len(pages),
            "pages": [p.to_dict() for p in pages],
        }

        with open(target, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=indent)

        logger.info(f"Exported {len(pages)} pages to JSON: {target}")
        return target
