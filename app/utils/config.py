"""
Configuration management loading settings from environment variables and .env file.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()


@dataclass
class Config:
    """Crawler runtime configuration parameters."""

    user_agent: str = field(
        default_factory=lambda: os.getenv(
            "CRAWLER_USER_AGENT",
            "AlgoryxBot/1.0 (+https://www.algoryx.in; internship-task-4)",
        )
    )
    request_timeout: float = field(
        default_factory=lambda: float(os.getenv("REQUEST_TIMEOUT", "15.0"))
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("MAX_RETRIES", "3"))
    )
    crawl_delay: float = field(
        default_factory=lambda: float(os.getenv("CRAWL_DELAY", "1.0"))
    )
    respect_robots: bool = field(
        default_factory=lambda: os.getenv("RESPECT_ROBOTS", "true").lower() in ("true", "1", "yes")
    )
    max_depth: int = field(
        default_factory=lambda: int(os.getenv("MAX_DEPTH", "2"))
    )
    max_pages: int = field(
        default_factory=lambda: int(os.getenv("MAX_PAGES", "30"))
    )
    max_concurrency: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENCY", "3"))
    )
    output_directory: str = field(
        default_factory=lambda: os.getenv("OUTPUT_DIRECTORY", "data")
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )
    log_file: str = field(
        default_factory=lambda: os.getenv("LOG_FILE", "logs/crawler.log")
    )

    def ensure_directories(self) -> None:
        """Ensures output and logging directories exist."""
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)


def get_default_config() -> Config:
    """Factory function returning a default Config instance."""
    config = Config()
    config.ensure_directories()
    return config
