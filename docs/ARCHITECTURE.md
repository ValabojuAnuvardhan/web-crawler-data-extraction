# System Architecture & Technical Design

> **Project:** Algoryx Web Crawler & Data Extraction Engine (Task 4)  
> **Company:** [Algoryx Technologies](https://www.algoryx.in)  
> **Author:** Valaboju Anuvardhan  

---

## 1. High-Level Architecture Overview

The Web Crawler & Data Extraction Engine is designed around clean object-oriented architecture, modular separation of concerns, and asynchronous networking. 

The architecture strictly separates responsibilities into distinct packages:
- **`app.crawler`**: Orchestration, frontier queue management, politeness, and robots.txt evaluation.
- **`app.parser`**: HTML parsing, element filtering, and structured content extraction.
- **`app.exporter`**: Dataset serialization into JSON and CSV.
- **`app.search`**: In-memory and dataset-driven case-insensitive full-text search.
- **`app.models`**: Strongly typed data models representing pages, elements, and metadata.
- **`app.utils`**: Cross-cutting concerns including URL canonicalization, configuration, and logging.

```
                              CRAWL PIPELINE
                              ==============

    [Seed URLs] 
         │
         ▼
  ┌───────────────┐        Is Allowed?
  │  URLManager   │ ────► [RobotsManager] ───► Disallowed (Skip)
  └───────────────┘             │ Allowed
         ▲                      ▼
         │             ┌────────────────┐
         │             │  RateLimiter   │ (Configurable Delay)
         │             └────────────────┘
         │                      │
         │                      ▼
         │             ┌────────────────┐
         │             │   WebCrawler   │ (httpx.AsyncClient + Retries)
         │             └────────────────┘
         │                      │ HTML Response
         │                      ▼
         │             ┌────────────────┐
         │             │   HTMLParser   │ (BeautifulSoup)
         │             └────────────────┘
         │                      │
         ├──────────────────────┼──────────────────────┐
         │ Internal Links       ▼                      ▼
  (depth < max_depth)    [CrawledPage]          [ExtractedContent]
                                │                 - Title, Headings
                                │                 - Paragraphs
                                ▼                 - Links, Images
                       ┌────────────────┐         - Metadata
                       │ Export Engine  │
                       └────────────────┘
                         │            │
                         ▼            ▼
                    [JSON Export] [CSV Export]
                         │
                         ▼
                ┌────────────────┐
                │  SearchEngine  │
                └────────────────┘
```

---

## 2. Component Responsibilities

| Component | Module | Responsibility |
| :--- | :--- | :--- |
| **`WebCrawler`** | `app.crawler.crawler` | Coordinates async page downloads, retries, and invokes parser and rate limiter. |
| **`URLManager`** | `app.crawler.url_manager` | Maintains FIFO BFS queue, tracks visited links, strips fragments, and discards duplicates. |
| **`RobotsManager`** | `app.crawler.robots` | Fetches, caches, and parses `robots.txt` per host; checks authorization via `urllib.robotparser`. |
| **`RateLimiter`** | `app.crawler.rate_limiter` | Enforces politeness delay between consecutive HTTP requests directed to the same domain. |
| **`HTMLParser`** | `app.parser.html_parser` | Parses HTML using BeautifulSoup; cleans script/style noise and extracts structured models. |
| **`JSONExporter`** | `app.exporter.json_exporter` | Serializes complete hierarchical page graphs and run metadata into standard JSON format. |
| **`CSVExporter`** | `app.exporter.csv_exporter` | Flattens structured page attributes into a clean, spreadsheet-friendly tabular CSV. |
| **`SearchEngine`** | `app.search.search_engine` | Performs case-insensitive keyword search over collected content, returning excerpts and match counts. |
| **`Config`** | `app.utils.config` | Loads strongly typed configuration from `.env` and environment variables. |
| **`Logger`** | `app.utils.logger` | Dual-output logging (console formatting and rotating file handler). |
| **`URLUtils`** | `app.utils.url_utils` | URL canonicalization, tracking parameter stripping, and relative-to-absolute resolution. |

---

## 3. Crawl Lifecycle & Execution Flow

1. **Initialization:**
   - Configuration is loaded from environment or CLI arguments.
   - Output and log directories are validated and created.
   - `URLManager` is seeded with initial seed URLs at `depth = 0`.
   - Origin domain is recorded to establish the internal crawl boundary.

2. **Frontier Dequeuing:**
   - The crawler pops the next `(url, depth)` from `URLManager`.
   - If the queue is empty or `max_pages` has been reached, the crawl terminates.

3. **Robots.txt Evaluation:**
   - `RobotsManager` inspects its in-memory cache for the domain's `robots.txt`.
   - If absent, it downloads `https://<domain>/robots.txt` and parses directives.
   - If the candidate URL is disallowed by a `Disallow:` directive matching `AlgoryxBot` or `*`, it is skipped.

4. **Politeness Delay:**
   - `RateLimiter` measures the time elapsed since the last request to that domain.
   - If the elapsed time is less than `crawl_delay` (or the `Crawl-delay` directive from `robots.txt`), the worker pauses asynchronously.

5. **HTTP Request & Resilience:**
   - A request is dispatched using `httpx.AsyncClient`.
   - If a `5xx` server error or connection/timeout error occurs, the crawler retries up to `max_retries` with incremental backoff.
   - Response latency (`response_time_ms`) and bytes transferred are recorded.

6. **Content Parsing:**
   - For `2xx` responses with `text/html` MIME types, `HTMLParser` parses the document.
   - Decomposes non-content elements (`<script>`, `<style>`, `<noscript>`).
   - Extracts page title, headings (`h1`-`h6`), body paragraphs (`<p>`), hyperlinks (`<a href>`), images (`<img src>`), and `<meta>` tags.

7. **Internal Link Discovery:**
   - Extracted links are resolved from relative to absolute URLs.
   - Each link is validated:
     - Must be valid HTTP/HTTPS.
     - Must point to an HTML-like resource (not `.pdf`, `.zip`, `.png`, etc.).
     - Must match the seed domain (`is_internal_url`).
   - If `current_depth < max_depth`, newly discovered internal URLs are enqueued at `depth + 1`.

8. **Export & Summary:**
   - All collected `CrawledPage` instances are serialized to JSON (`data/crawl_output.json`) and CSV (`data/crawl_output.csv`).
   - Performance metrics (pages visited, failures, skipped URLs, execution time, throughput) are printed.

---

## 4. URL Handling & Duplicate Prevention Strategy

URL duplication is prevented through a deterministic multi-stage canonicalization pipeline in `app.utils.url_utils.normalize_url`:

1. **Fragment Stripping:** Removes `#anchor` identifiers (e.g. `https://example.com/page#top` -> `https://example.com/page`).
2. **Case Normalization:** Lowercases protocol scheme and hostname.
3. **Port Stripping:** Drops default HTTP (`:80`) and HTTPS (`:443`) port designations.
4. **Marketing Query Stripping:** Strips common tracking query parameters (`utm_source`, `utm_medium`, `utm_campaign`, `fbclid`, `gclid`, `ref`).
5. **Deterministic Query Sorting:** Alphabetizes query string key-value pairs so `?b=2&a=1` matches `?a=1&b=2`.
6. **Path Normalization:** Strips trailing slashes from non-root paths (e.g. `/about/` -> `/about`).

Visited URLs are tracked in an in-memory hash set within `URLManager`. Lookup and insertion operate in $O(1)$ time complexity.

---

## 5. Security & Ethical Crawling Principles

In compliance with Algoryx's engineering standards:
- **Strict Domain Scoping:** The crawler never traverses outside seed domains. External links are captured in page metadata for analytics, but are never queued.
- **Robots.txt Adherence:** Webmaster exclusions are checked and respected prior to any content request.
- **Configurable Politeness:** Rate-limiting delays prevent denial-of-service pressure on target servers.
- **Concurrency Caps:** Uses `asyncio.Semaphore` to bound concurrent requests.
- **Hard Boundaries:** Bounded by both `max_depth` and `max_pages` ceiling safeguards.
- **Identifiable User-Agent:** The crawler identifies itself via a descriptive User-Agent header with contact/internship context.
