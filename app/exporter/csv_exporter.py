"""
Tabular CSV exporter flattening nested page attributes into practical columns.
"""

import csv
from pathlib import Path
from typing import List, Optional
from app.models.page import CrawledPage
from app.utils.logger import get_logger

logger = get_logger("exporter.csv")

CSV_COLUMNS = [
    "URL",
    "Title",
    "HTTP Status",
    "Depth",
    "Response Time (ms)",
    "Word Count",
    "Headings Count",
    "Headings",
    "Paragraph Count",
    "Body Preview",
    "Link Count",
    "Image Count",
    "Meta Description",
    "Meta Keywords",
    "Error",
    "Crawled At",
]


class CSVExporter:
    """Exports crawled pages into flattened tabular CSV files."""

    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        pages: List[CrawledPage],
        filepath: Optional[str] = None,
    ) -> Path:
        """
        Exports a list of CrawledPage objects into a CSV file.

        Args:
            pages: List of crawled page records.
            filepath: Destination file path.

        Returns:
            Path to the written CSV file.
        """
        target = Path(filepath) if filepath else self.output_dir / "crawl_output.csv"
        target.parent.mkdir(parents=True, exist_ok=True)

        with open(target, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=CSV_COLUMNS,
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writeheader()
            for p in pages:
                writer.writerow(p.to_flat_dict())

        logger.info(f"Exported {len(pages)} rows to CSV: {target}")
        return target
