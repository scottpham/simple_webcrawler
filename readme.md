# Async Playwright Web Crawler with Markdown Export

A high-performance async CLI web crawler that handles JavaScript-rendered content and saves main content as Markdown files.

## Features

- **🚀 Async/Concurrent**: Crawls multiple pages simultaneously for much faster performance
- **📝 Markdown Export**: Extracts main content and saves as clean Markdown files
- **🧠 Smart Content Extraction**: Removes navigation, ads, and clutter to focus on main content
- **⚡ JavaScript Support**: Renders pages with Playwright to capture dynamically generated content
- **🎯 SPA Detection**: Recognizes Single Page Applications (React, Angular, Vue)
- **📊 Progress Tracking**: Real-time statistics and detailed logging
- **🛡️ Respectful Crawling**: Built-in delays and concurrent request limits

## Installation with UV

1. **Install UV** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Simple setup** (recommended for standalone script):
```bash
# Navigate to project directory
cd your-crawler-project

# Install dependencies directly
uv add playwright beautifulsoup4 html2text aiofiles

# Install Playwright browsers
uv run playwright install
```

3. **Alternative: Using requirements-style installation**:
```bash
# Create a virtual environment and install dependencies
uv venv
uv pip install playwright beautifulsoup4 html2text aiofiles
uv run playwright install
```

## Installation without UV (traditional pip)

```bash
pip install playwright beautifulsoup4 html2text aiofiles
playwright install
```

## Installation with Poetry

```bash
# Initialize poetry project (if not already done)
poetry init

# Add dependencies
poetry add playwright beautifulsoup4 html2text aiofiles

# Install Playwright browsers
poetry run playwright install
```

## Usage

### Basic Usage
```bash
# With UV
uv run python crawler.py example.com 10

# With Poetry
poetry run python crawler.py example.com 10

# With activated virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python crawler.py example.com 10
```

### Advanced Options
```bash
# Crawl with 5 concurrent pages and custom delay
uv run python crawler.py https://example.com 20 --concurrent 5 --delay 0.5
# or with Poetry:
poetry run python crawler.py https://example.com 20 --concurrent 5 --delay 0.5

# Run in GUI mode (see browser window)
uv run python crawler.py example.com 10 --gui

# High-performance crawling (more concurrent requests)
uv run python crawler.py example.com 50 --concurrent 8 --delay 0.2
```

## Content Output

The crawler now saves **multiple types of output**:

### 📁 File Structure
```
crawled_example_com/
├── example_com.md              # Homepage content (Markdown)
├── example_com_about.md        # About page content
├── example_com_products.md     # Products page content
├── crawl_summary.json         # Statistics and metadata
└── ...
```

### 📝 Markdown Files
**Each Markdown file contains:**
- Page title as header
- URL and crawl timestamp metadata
- Clean main content (navigation/ads removed)
- Preserved links and formatting

**Example output file:**
```markdown
# About Our Company

**URL:** https://example.com/about  
**Crawled:** 2025-07-18 14:30:15

---

Our company was founded in 2020 with a mission to...

## Our Team

We have a dedicated team of professionals...

[Contact us](https://example.com/contact) for more information.
```

### 📊 Crawl Summary
**`crawl_summary.json` contains crawl statistics and metadata:**
```json
{
  "domain": "example.com",
  "start_url": "https://example.com",
  "crawl_stats": {
    "pages_crawled": 10,
    "pages_saved": 10,
    "start_time": 1705589400.123,
    "urls_discovered": 27
  },
  "total_urls_visited": [
    "https://example.com",
    "https://example.com/about",
    "https://example.com/products"
  ],
  "crawl_duration": 8.3
}
```

## What It Does

1. **🔄 Async Crawling**: Launches multiple browser pages simultaneously for faster crawling
2. **🌐 JavaScript Execution**: Uses real browsers to execute JavaScript and capture dynamic content
3. **⏳ Smart Waiting**: Waits for AJAX requests and content to fully load
4. **🎯 Content Extraction**: Identifies and extracts main content, removing navigation/ads/clutter
5. **📝 Markdown Conversion**: Converts clean HTML to well-formatted Markdown
6. **💾 File Saving**: Saves each page as a separate Markdown file with metadata
7. **📊 Progress Tracking**: Shows real-time statistics and crawl summary
8. **🔗 Link Discovery**: Finds new pages to crawl within the same domain

## Output Example

```
Starting async Playwright crawl of https://example.com
Max pages: 10
Domain: example.com
Concurrent pages: 3
Output directory: crawled_example_com
Mode: Headless
--------------------------------------------------
Crawling: https://example.com
  Status: 200
  Title: Example Domain
  Size: 1256 bytes
  ✓ Content saved as markdown
  Found 3 links
Crawling: https://example.com/about
  Status: 200
  Title: About Us - Example
  Size: 2847 bytes
  ✓ Content saved as markdown
  Found 8 links
Crawling: https://example.com/products
  Status: 200
  Title: Our Products
  Size: 3421 bytes
  ✓ Content saved as markdown
  Found 12 links
Progress: 3/10
------------------------------

Crawl completed!
Pages crawled: 10
Pages saved: 10
Total URLs discovered: 27
URLs remaining in queue: 19
Output directory: crawled_example_com
Duration: 8.3 seconds
```

**Files created:**
```
crawled_example_com/
├── example_com.md                    # Homepage content
├── example_com_about.md             # About page
├── example_com_products.md          # Products page
├── example_com_contact.md           # Contact page
└── crawl_summary.json              # Crawl statistics and metadata
```

## Browser Management

The crawler automatically:
- Downloads and manages browser binaries
- Uses realistic browser headers and viewport
- Handles HTTPS errors gracefully
- Cleans up resources when finished or interrupted

## Troubleshooting

If you get browser installation errors:
```bash
# Reinstall browsers
uv run playwright install --force

# Or install specific browser
uv run playwright install chromium
```

For permission errors on Linux:
```bash
# Install system dependencies
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```