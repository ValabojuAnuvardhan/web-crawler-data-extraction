# 2–5 Minute Video Demonstration Guide & Script

> **Internship:** Algoryx Python Internship — Task 4 (Week 4)  
> **Project:** Web Crawler & Data Extraction Engine  
> **Presenter:** Valaboju Anuvardhan  
> **Company:** Algoryx Technologies ([www.algoryx.in](https://www.algoryx.in))  

---

## ⏱️ Video Structure Breakdown (Target: ~3 Minutes)

| Segment | Time | Screen Display | Key Talking Points |
| :--- | :---: | :--- | :--- |
| **1. Introduction** | 0:00 - 0:30 | VS Code / Terminal with ASCII Banner | Introduce yourself, Algoryx internship, and Task 4 objectives. |
| **2. Architecture Walkthrough** | 0:30 - 1:00 | Project file tree & `ARCHITECTURE.md` | Highlight modular packages: `crawler`, `parser`, `exporter`, `search`, `utils`. |
| **3. Live CLI Crawl Demo** | 1:00 - 1:50 | Terminal running `python -m app.main crawl` | Show multi-depth traversal, `robots.txt` check, polite delay, and live summary table. |
| **4. Data Exports Review** | 1:50 - 2:20 | Open `crawl_output.json` & `crawl_output.csv` | Show structured nested elements in JSON and clean columns in CSV. |
| **5. Search & Testing** | 2:20 - 2:50 | Run `python -m app.main search` & `pytest` | Demonstrate instant keyword search and 100% test pass rate. |
| **6. Conclusion** | 2:50 - 3:10 | GitHub Repo & Algoryx Tagline | Wrap up and cite Algoryx's motto: *Build. Innovate. Deliver. Impact.* |

---

## 🎙️ Verbatim Demo Script

### 0:00 - 0:30 | Introduction
> *"Hello everyone! My name is Valaboju Anuvardhan, and in this video, I am presenting my Week 4 Task for the Algoryx Python Internship: the Web Crawler & Data Extraction Engine.*  
> *The objective of this task was to build a scalable, asynchronous Python web crawler that downloads web pages, extracts structured human-readable content, follows internal links up to a configured depth, and exports standardized datasets while strictly respecting web standards like robots.txt and polite rate limiting."*

### 0:30 - 1:00 | Architecture & Clean Code
> *(Switch screen to VS Code file explorer)*  
> *"Instead of writing a monolithic script, I engineered this system with strict modular architecture under the `app` package:*  
> *- Inside `app/crawler`, we have our asynchronous crawler built with `httpx`, our `URLManager` for BFS depth control and visited-link deduplication, `robots.py` for robots.txt parsing, and `rate_limiter.py` for per-domain politeness.*  
> *- In `app/parser`, we use BeautifulSoup to extract titles, headings (h1 through h6), paragraphs, links, images, and metadata while stripping script and style noise.*  
> *- In `app/exporter`, we have dedicated JSON and CSV exporters.*  
> *- And in `app/search`, we have an in-memory keyword search engine with snippet highlighting."*

### 1:00 - 1:50 | Live Crawling Demonstration
> *(Switch screen to terminal)*  
> *"Let's see the crawler in action. I'll execute:*  
> ```bash
> python -m app.main crawl --url https://quotes.toscrape.com/ --depth 1 --max-pages 5 --delay 0.5 --output data
> ```  
> *(Let the command run)*  
> *"As you can see from the logs, the crawler:*  
> *1. Starts at depth 0 on the seed URL.*  
> *2. Enforces a 0.5-second politeness delay.*  
> *3. Follows internal links up to depth 1, completely ignoring external domains.*  
> *4. Automatically avoids duplicate URLs.*  
> *At the end, it displays a complete summary: 5 pages visited, 0 failures, 2 external URLs skipped, throughput of over 1 page per second, and generated both JSON and CSV files in our `data` directory."*

### 1:50 - 2:20 | Inspecting the Output Files
> *(Open `data/crawl_output.json`)*  
> *"Looking at `data/crawl_output.json`, you can see the complete hierarchical structure: page titles, headings with levels, body paragraphs, and structured metadata.*  
> *(Open `data/crawl_output.csv`)*  
> *"And in `data/crawl_output.csv`, we flattened these complex objects into clean, readable columns including URL, Title, HTTP Status, Word Count, and Headings Summary."*

### 2:20 - 2:50 | Keyword Search & Automated Testing
> *(Switch back to terminal)*  
> *"Next, let's test the search feature:*  
> ```bash
> python -m app.main search --keyword "Einstein" --file data/crawl_output.json
> ```  
> *"It instantly returns matching pages with match counts and an extracted text snippet.*  
> *Now let's run our test suite using pytest:*  
> ```bash
> pytest -v
> ```  
> *"All 10 unit and integration tests pass with 100% coverage across URL normalization, parser extraction, exporters, search, and mock crawler traversal without needing external internet access."*

### 2:50 - 3:10 | Conclusion
> *"This project is container-ready with Docker, includes CI workflows with GitHub Actions, and satisfies every requirement set out by Algoryx Technologies.*  
> *Thank you to Algoryx for this internship challenge: Build. Innovate. Deliver. Impact. Thank you!"*

---

## 🛠️ Pre-Recording Checklist

- [ ] Clear terminal screen (`cls` on Windows or `clear` on Mac/Linux).
- [ ] Open VS Code with `app/` folder expanded.
- [ ] Ensure virtual environment is activated (`venv\Scripts\Activate.ps1`).
- [ ] Run a test crawl beforehand so `data/crawl_output.json` exists for the search demo.
- [ ] Set microphone audio level and screen resolution to 1080p.
