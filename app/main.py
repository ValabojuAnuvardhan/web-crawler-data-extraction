"""
Main CLI entry point for Algoryx Web Crawler & Data Extraction Engine.
Supports crawl and search commands.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.utils.config import Config
from app.utils.logger import setup_logger
from app.crawler.crawler import WebCrawler
from app.exporter.json_exporter import JSONExporter
from app.exporter.csv_exporter import CSVExporter
from app.search.search_engine import SearchEngine


def print_banner() -> None:
    """Prints the application banner."""
    print("=" * 70)
    print("      ALGORYX WEB CRAWLER & DATA EXTRACTION ENGINE (TASK 4)")
    print("          Build. Innovate. Deliver. Impact. | www.algoryx.in")
    print("=" * 70)


def cmd_crawl(args: argparse.Namespace) -> None:
    """Executes the crawl command."""
    print_banner()

    # Collect seed URLs
    urls: List[str] = []
    if args.url:
        urls.extend(args.url)
    if not urls:
        urls = ["https://quotes.toscrape.com/"]

    setup_logger(log_level=args.log_level)

    config = Config(
        max_depth=args.depth,
        max_pages=args.max_pages,
        crawl_delay=args.delay,
        respect_robots=not args.no_robots,
        output_directory=args.output,
        max_concurrency=args.concurrency,
        log_level=args.log_level,
    )
    config.ensure_directories()

    crawler = WebCrawler(config=config)

    print(f"\nSeed URLs:        {', '.join(urls)}")
    print(f"Max Depth:        {config.max_depth}")
    print(f"Max Pages:        {config.max_pages}")
    print(f"Crawl Delay:      {config.crawl_delay}s")
    print(f"Respect robots:   {config.respect_robots}")
    print(f"Output Directory: {config.output_directory}\n")

    pages = asyncio.run(crawler.crawl(seed_urls=urls))

    # Display crawl statistics
    crawler.summary.print_summary()

    # Export to JSON and CSV
    json_exporter = JSONExporter(output_dir=config.output_directory)
    csv_exporter = CSVExporter(output_dir=config.output_directory)

    json_path = json_exporter.export(
        pages=pages,
        filepath=str(Path(config.output_directory) / "crawl_output.json"),
        metadata={
            "seed_urls": urls,
            "max_depth": config.max_depth,
            "pages_visited": crawler.summary.pages_visited,
            "successful_pages": crawler.summary.successful_pages,
            "execution_time_seconds": round(crawler.summary.execution_time, 2),
        },
    )

    csv_path = csv_exporter.export(
        pages=pages,
        filepath=str(Path(config.output_directory) / "crawl_output.csv"),
    )

    print("Exports Generated:")
    print(f"  [JSON] -> {json_path}")
    print(f"  [CSV]  -> {csv_path}\n")


def cmd_search(args: argparse.Namespace) -> None:
    """Executes keyword search over exported dataset or live database."""
    print_banner()
    query = args.keyword
    data_file = args.file

    search_engine = SearchEngine()
    print(f"\nSearching for keyword: \"{query}\" in {data_file}...\n")

    results = search_engine.search_from_file(query=query, json_path=data_file, limit=args.limit)

    if not results:
        print(f"No matching pages found for \"{query}\".")
        return

    print(f"Found {len(results)} matching page(s):\n")
    print("-" * 70)
    for idx, r in enumerate(results, 1):
        print(f"[{idx}] {r.title}")
        print(f"    URL:     {r.url}")
        print(f"    Matches: {r.matches_count}")
        print(f"    Snippet: {r.snippet}")
        print("-" * 70)


def build_parser() -> argparse.ArgumentParser:
    """Constructs the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m app.main",
        description="Algoryx Web Crawler & Data Extraction Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: crawl
    crawl_p = subparsers.add_parser("crawl", help="Start web crawler")
    crawl_p.add_argument(
        "--url",
        action="append",
        help="Seed URL to crawl (can be specified multiple times)",
    )
    crawl_p.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Maximum link traversal depth (default: 2)",
    )
    crawl_p.add_argument(
        "--max-pages",
        type=int,
        default=30,
        help="Maximum total pages to crawl (default: 30)",
    )
    crawl_p.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Politeness delay in seconds between requests (default: 1.0)",
    )
    crawl_p.add_argument(
        "--output",
        default="data",
        help="Output directory for JSON and CSV exports (default: data)",
    )
    crawl_p.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Async concurrency limit (default: 3)",
    )
    crawl_p.add_argument(
        "--no-robots",
        action="store_true",
        help="Ignore robots.txt directives",
    )
    crawl_p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging severity level (default: INFO)",
    )
    crawl_p.set_defaults(func=cmd_crawl)

    # Subcommand: search
    search_p = subparsers.add_parser("search", help="Search collected content by keyword")
    search_p.add_argument(
        "--keyword",
        required=True,
        help="Keyword to search across crawled pages",
    )
    search_p.add_argument(
        "--file",
        default="data/crawl_output.json",
        help="Path to JSON dataset file to search (default: data/crawl_output.json)",
    )
    search_p.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum results to return (default: 10)",
    )
    search_p.set_defaults(func=cmd_search)

    return parser


def main() -> None:
    """CLI execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
