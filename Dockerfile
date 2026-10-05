# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies for compiled extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user and persistent directories
RUN useradd -u 1000 -m crawleruser && \
    mkdir -p /app/data /app/logs && \
    chown -R crawleruser:crawleruser /app

USER crawleruser

VOLUME ["/app/data", "/app/logs"]

ENTRYPOINT ["python", "-m", "app.main"]
CMD ["crawl", "--url", "https://quotes.toscrape.com/", "--depth", "1", "--max-pages", "10", "--output", "data"]
