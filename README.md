# Web Crawler & Data Extraction Engine

[![CI Test Suite](https://github.com/valabojuanuvardhan/algoryx-internship-task-4/actions/workflows/ci.yml/badge.svg)](https://github.com/valabojuanuvardhan/algoryx-internship-task-4/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Clean OOP](https://img.shields.io/badge/architecture-modular_OOP-green.svg)](docs/ARCHITECTURE.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Internship: Algoryx](https://img.shields.io/badge/Algoryx-Task_4-06b6d4.svg)](https://www.algoryx.in)

> **Algoryx Python Internship — Task 4 (Week 4)**  
> **Brand & Company:** [Algoryx Technologies](https://www.algoryx.in) | *Build. Innovate. Deliver. Impact.*  
> **Author:** Valaboju Anuvardhan  

---

## 1. Project Overview

The **Web Crawler & Data Extraction Engine** is a production-grade, asynchronous Python system designed to recursively discover, download, and extract structured human-readable content from web domains. Built using modern Python 3.11+ patterns (`asyncio`, `httpx`, `BeautifulSoup`), the system adheres strictly to ethical web scraping protocols (`robots.txt` compliance, rate limiting, domain boundaries) and exports clean, standardized datasets in both **JSON** and **CSV** formats, backed by an in-memory **keyword search engine**.

---

## 2. Problem Statement

Manual data collection from websites is inefficient, inconsistent, and error-prone. Building automated crawlers poses several engineering challenges:
- **Redundant Network Calls:** Cyclic hyperlinks and duplicate queries cause crawl loops.
- **Server Overload:** Unregulated crawlers flood target web servers, causing IP bans and service disruptions.
- **Complex & Noisy Markup:** Raw HTML contains heavy scripts, tracking pixels, ads, and boilerplate styling that pollute extracted datasets.
- **Network Instability:** Latency spikes, 5xx server errors, and dropped connections easily break rigid single-threaded pipelines.

This engine solves these issues by providing a deterministic, politeness-aware, and failure-resilient extraction pipeline.

---

## 3. Objectives

- **Scalable Asynchronous Networking:** Use non-blocking I/O (`httpx.AsyncClient` with connection pooling) to fetch pages concurrently with bounded semaphore limits.
- **Clean HTML Parsing:** Cleanly isolate human-readable text from script/style noise using BeautifulSoup.
- **Strict Scope Boundaries:** Enforce recursive crawling only on internal links within the seed domain.
- **Polite & Ethical Operation:** Check and obey `robots.txt` disallow rules and enforce per-domain rate limiting.
- **Structured Data Export:** Serialize output into hierarchical JSON and tabular CSV datasets.
- **Content Searchability:** Provide instant, case-insensitive keyword search over harvested content.

---

## 4. Key Features

- **Multi-Seed Crawling:** Accepts one or multiple initial seed URLs from the command line or configuration.
- **Recursive Internal Crawling:** Follows hyperlinks discovered within the seed domain up to a user-defined maximum depth.
- **URL Canonicalization & Deduplication:** Strips URL fragments, analytics query tags (`utm_*`, `fbclid`), normalizes ports/paths, and maintains an in-memory visited set.
- **Robots.txt & Politeness Engine:** Automatically downloads and parses `robots.txt` using Python's standard `urllib.robotparser`, respecting both disallow directives and `Crawl-delay`.
- **Fault-Tolerant Networking:** Implements configurable connection/read timeouts and automatic retry logic with incremental backoff on transient HTTP 5xx errors.
- **Comprehensive HTML Extraction:** Extracts page title, all heading levels (`h1`-`h6`), body paragraphs (`<p>`), internal and external hyperlinks, images (`src`, `alt`, `title`), and SEO metadata (`description`, `keywords`, OpenGraph tags).
- **Dual Format Exporters:**
  - **Structured JSON:** Preserves nested hierarchies, element lists, and crawl run metadata.
  - **Tabular CSV:** Flattens records into practical, human-readable spreadsheet columns.
- **Fast Keyword Search:** Case-insensitive search across collected page titles, headings, and paragraph text with contextual snippet generation.
- **Detailed Run Statistics:** Displays execution metrics including pages visited, success/fail counts, skipped URLs, total duration, and throughput (pages/sec).
- **Dual-Layer Logging:** Outputs formatted logs to the console and a rotating log file in `logs/crawler.log`.

---

## 5. System Architecture

The engine is built around clean Object-Oriented Programming (OOP) and the Single Responsibility Principle:

```
[Seed URLs] ──► [URLManager] ──► [RobotsManager] ──► [RateLimiter]
                     ▲                                      │
                     │ (Discovered internal links)          ▼
              [HTMLParser] ◄────── [httpx Client] ◄─────────┘
                     │
                     ├─► [JSONExporter] ──► data/crawl_output.json
                     ├─► [CSVExporter]  ──► data/crawl_output.csv
                     └─► [SearchEngine] ──► CLI Keyword Search
```

For detailed component breakdowns, class relationships, and lifecycle flowcharts, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 6. Project Structure

```
task-4/
├── app/
│   ├── __init__.py
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── crawler.py          # Core crawler engine with async httpx & retries
│   │   ├── url_manager.py      # Visited link set, BFS queue, and depth limits
│   │   ├── robots.py           # Robots.txt parser and permission validator
│   │   └── rate_limiter.py     # Per-domain politeness delay manager
│   ├── parser/
│   │   ├── __init__.py
│   │   └── html_parser.py      # BeautifulSoup extractor for headings, text, links, images
│   ├── exporter/
│   │   ├── __init__.py
│   │   ├── json_exporter.py    # Structured JSON dataset exporter
│   │   └── csv_exporter.py     # Tabular CSV spreadsheet exporter
│   ├── models/
│   │   ├── __init__.py
│   │   └── page.py             # Strongly typed dataclasses for pages and content
│   ├── search/
│   │   ├── __init__.py
│   │   └── search_engine.py    # Full-text keyword search and context snippet engine
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py           # Runtime configuration loader (.env / environment)
│   │   ├── logger.py           # Standard logging with console & rotating file handler
│   │   └── url_utils.py        # Normalization, relative resolution, domain checks
│   └── main.py                 # Command-line interface (CLI) entry point
├── tests/
│   ├── test_url_manager.py     # URL validation, canonicalization, and queue tests
│   ├── test_parser.py          # BeautifulSoup parsing and metadata extraction tests
│   ├── test_exporters.py       # JSON and CSV export verification tests
│   ├── test_search.py          # Case-insensitive search and snippet matching tests
│   └── test_crawler.py         # Mock HTTP integration tests for depth and robots.txt
├── data/
│   ├── sample.json             # Realistic sample JSON export
│   └── sample.csv              # Realistic sample CSV export
├── docs/
│   ├── ARCHITECTURE.md         # Comprehensive architectural documentation
│   └── REQUIREMENTS_CHECKLIST.md # Full Task 4 compliance verification matrix
├── logs/
│   └── .gitkeep                # Log directory placeholder
├── .env.example                # Example environment configuration file
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Minimal production dependencies
├── Dockerfile                  # Container definition for isolated execution
└── README.md                   # Complete project documentation
```

---

## 7. Installation

### Prerequisites
- **Python 3.11+** installed
- Git installed

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/valabojuanuvardhan/algoryx-internship-task-4.git
   cd algoryx-internship-task-4
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 8. Environment Configuration

Copy the sample environment file to configure default crawler parameters:

```bash
cp .env.example .env
```

Available `.env` settings:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `CRAWLER_USER_AGENT` | `AlgoryxBot/1.0 (+https://www.algoryx.in)` | HTTP User-Agent header |
| `REQUEST_TIMEOUT` | `15.0` | Total request timeout in seconds |
| `MAX_RETRIES` | `3` | Maximum retry attempts on 5xx or network errors |
| `CRAWL_DELAY` | `1.0` | Politeness delay between requests to same domain |
| `RESPECT_ROBOTS` | `true` | Obey robots.txt disallow directives |
| `MAX_DEPTH` | `2` | Maximum link traversal depth |
| `MAX_PAGES` | `30` | Maximum pages to crawl per execution |
| `MAX_CONCURRENCY` | `3` | Max concurrent worker connections |
| `OUTPUT_DIRECTORY` | `data` | Destination directory for export files |
| `LOG_LEVEL` | `INFO` | Console log severity (DEBUG, INFO, WARNING, ERROR) |

---

## 9. Usage & CLI Commands

The engine provides an intuitive command-line interface via `python -m app.main`.

### 1. Basic Web Crawl
Crawl a seed website up to depth 1 with default settings:
```bash
python -m app.main crawl --url https://quotes.toscrape.com/ --depth 1 --max-pages 10 --delay 0.5 --output data
```

### 2. Multi-Seed Crawl
Crawl multiple entrypoints concurrently:
```bash
python -m app.main crawl \
  --url https://quotes.toscrape.com/ \
  --url https://books.toscrape.com/ \
  --depth 1 \
  --max-pages 20
```

### 3. Custom Concurrency & Politeness
Run a polite crawl with a 2-second delay and bounded concurrency:
```bash
python -m app.main crawl --url https://quotes.toscrape.com/ --delay 2.0 --concurrency 2 --depth 2
```

### 4. Keyword Search Over Extracted Content
Search for terms across crawled pages:
```bash
python -m app.main search --keyword "Einstein" --file data/crawl_output.json
```

---

## 10. Crawl Workflow

1. **Seed Ingestion:** Target URLs are normalized and placed into the FIFO BFS queue at `depth = 0`.
2. **Domain Scoping:** The domain of each seed URL is stored to establish the strict internal crawl perimeter.
3. **Robots Check:** Before downloading a URL, the domain's `robots.txt` is retrieved and parsed. If disallowed, the URL is logged and skipped.
4. **Rate Limiting:** If consecutive requests target the same host, the crawler awaits the configured `crawl_delay`.
5. **Resilient Download:** `httpx.AsyncClient` downloads the page. Any connection drop or 5xx server error triggers up to 3 retries with backoff.
6. **Parsing & Filtering:** HTML content is parsed with BeautifulSoup. Scripts and stylesheets are stripped to isolate human-readable text.
7. **Child Link Discovery:** Internal links are resolved to absolute URLs. Valid, unvisited links are enqueued at `depth + 1`.
8. **Export & Summary:** Crawled records are serialized to JSON and CSV, and a summary table is printed.

---

## 11. Data Extraction & Output Formats

### Extracted Data Fields
Each crawled webpage captures:
- **`URL`**: Canonicalized URL
- **`Title`**: Content of `<title>`, `og:title`, or `<h1>`
- **`Headings`**: All `h1` through `h6` elements preserved with level and text
- **`Paragraphs`**: Cleaned, non-empty body paragraph strings (`<p>`)
- **`Links`**: Discovered links with anchor text and internal/external classification
- **`Images`**: Image source URLs (`src`), alt text, and title attributes
- **`Metadata`**: Meta description, keywords, author, and OpenGraph properties
- **`Diagnostics`**: HTTP status code, response latency (ms), content length, and timestamp

### JSON Export (`data/crawl_output.json`)
```json
{
  "metadata": {
    "seed_urls": ["https://quotes.toscrape.com/"],
    "max_depth": 1,
    "pages_visited": 5,
    "execution_time_seconds": 4.65
  },
  "total_pages": 5,
  "pages": [
    {
      "url": "https://quotes.toscrape.com/",
      "canonical_url": "https://quotes.toscrape.com/",
      "depth": 0,
      "status_code": 200,
      "response_time_ms": 112.4,
      "content": {
        "title": "Quotes to Scrape",
        "headings": [{"level": 1, "text": "Quotes to Scrape"}],
        "paragraphs": ["“The world as we have created it...”"],
        "links": [{"url": "https://quotes.toscrape.com/login", "text": "Login", "is_internal": true}],
        "images": [],
        "metadata": {"description": "A collection of inspiring quotes."}
      }
    }
  ]
}
```

### CSV Export (`data/crawl_output.csv`)
Columns:
`URL`, `Title`, `HTTP Status`, `Depth`, `Response Time (ms)`, `Word Count`, `Headings Count`, `Headings`, `Paragraph Count`, `Body Preview`, `Link Count`, `Image Count`, `Meta Description`, `Meta Keywords`, `Error`, `Crawled At`

---

## 12. Search Functionality

The built-in `SearchEngine` executes case-insensitive queries across all fields of harvested datasets:
- Page Title
- Headings (`h1`-`h6`)
- Body Paragraphs
- Meta Description & Keywords

Matches are ranked by term frequency, and contextual snippets highlighting the query are returned:
```bash
$ python -m app.main search --keyword Einstein
Searching for keyword: "Einstein" in data/crawl_output.json...

Found 1 matching page(s):
----------------------------------------------------------------------
[1] Quotes to Scrape
    URL:     https://quotes.toscrape.com/author/Albert-Einstein
    Matches: 1
    Snippet: Quotes to Scrape Quotes to Scrape Albert Einstein Login Born: March 14, 1879 in Ulm, Germany Description: Quotes by: GoodReads.co...
----------------------------------------------------------------------
```

---

## 13. Error Handling & Network Resilience

The crawler is engineered to withstand real-world network anomalies:
- **Timeouts:** Separate connection and total request timeouts prevent hangs on slow endpoints.
- **Automatic Retries:** HTTP 500, 502, 503, 504 responses trigger retries with linear backoff ($attempt \times 1.0s$).
- **Client Error Containment:** HTTP 404, 403, and 410 errors are recorded with their status codes without terminating the crawl.
- **Graceful Parsing Fallback:** Malformed HTML is parsed defensively, falling back from `lxml` to Python's built-in `html.parser` if required.

---

## 14. Logging Architecture

Logs are managed through Python's standard `logging` library with zero third-party logging overhead:
- **Console Output:** Clean, timestamped status updates (`[INFO] Fetching [depth=0]: ...`).
- **File Output:** Detailed diagnostic logs written to `logs/crawler.log` with automatic log rotation (5MB per file, 3 backups) preserving stack traces.

---

## 15. Testing Suite

The project includes 10 unit and integration tests covering all critical components without requiring an external internet connection.

Run tests using pytest:
```bash
pytest -v
```

### Test Coverage Summary:
- `tests/test_url_manager.py`: URL validation, canonicalization, tracking parameter stripping, and queue limits.
- `tests/test_parser.py`: Extraction of titles, headings, paragraphs, links, images, and metadata with script decomposition.
- `tests/test_exporters.py`: JSON structural integrity and CSV tabular flattening.
- `tests/test_search.py`: Case-insensitive search, match scoring, and snippet generation.
- `tests/test_crawler.py`: End-to-end crawl simulation using a mock HTTP transport verifying depth limits and `robots.txt` enforcement.

---

## 16. Docker Support

Run the crawler in an isolated container without installing local Python dependencies:

1. **Build the container image:**
   ```bash
   docker build -t algoryx-crawler .
   ```

2. **Run a crawl with mounted output:**
   ```bash
   docker run --rm -v ${PWD}/data:/app/data algoryx-crawler crawl \
     --url https://quotes.toscrape.com/ \
     --depth 1 \
     --max-pages 10
   ```

---

## 17. Example CLI Output

```
======================================================================
      ALGORYX WEB CRAWLER & DATA EXTRACTION ENGINE (TASK 4)
          Build. Innovate. Deliver. Impact. | www.algoryx.in
======================================================================

Seed URLs:        https://quotes.toscrape.com/
Max Depth:        1
Max Pages:        5
Crawl Delay:      0.5s
Respect robots:   True
Output Directory: data

==================================================
                 CRAWL SUMMARY
==================================================
Seed URLs:         https://quotes.toscrape.com/
Max Depth:         1
Pages Discovered:  47
Pages Visited:     5
Successful:        5
Failed:            0
Skipped (Total):   2
  - Robots.txt:    0
  - External:      2
Execution Time:    4.65 seconds
Throughput:        1.07 pages/sec
==================================================

Exports Generated:
  [JSON] -> data\crawl_output.json
  [CSV]  -> data\crawl_output.csv
```

---

## 18. Limitations

- **JavaScript Single-Page Apps (SPAs):** Pages rendered entirely via client-side JavaScript (e.g. React/Vue without SSR) require a headless browser (Playwright/Selenium), which is intentionally excluded to keep this engine lightweight and performant.
- **Authentication Barriers:** Paywalled or login-protected resources are deliberately skipped in alignment with ethical crawling rules.

---

## 19. Future Improvements

- Distributed frontier queue using Redis for multi-machine crawling clusters.
- Headless browser rendering plug-in for JavaScript-heavy dynamic single-page applications.
- Real-time Prometheus metrics exporter for monitoring throughput and latency in production.

---

## 20. Ethical & Responsible Crawling Notice

This project was built for academic and professional internship evaluation under the **Algoryx Internship Program**. It strictly respects webmaster guidelines:
- Adheres to `robots.txt` exclusions.
- Enforces non-zero crawl delays between requests to the same domain.
- Never attempts to bypass CAPTCHA, authentication, or anti-scraping protections.
- Bounded by hard depth and total page limits to avoid resource exhaustion.

---

## 21. Algoryx Internship Guidelines Alignment

In accordance with [ALGORYX_GUIDELINES.md](ALGORYX_GUIDELINES.md):
- **Code Standards:** 100% typed, modular OOP architecture with clear separation of concerns.
- **Deliverables:** All required deliverables (Source code, `README.md`, `requirements.txt`, `ARCHITECTURE.md`, sample exports, demo guide, LinkedIn post) are complete and documented.
- **Brand Standards:** Designed to reflect Algoryx Technologies' mission: *Build. Innovate. Deliver. Impact.*
