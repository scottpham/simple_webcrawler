#!/usr/bin/env python3
"""
Async Playwright-based CLI Web Crawler with Markdown content extraction
Usage: python crawler.py <url> <max_pages>

Install with UV:
uv add playwright beautifulsoup4 html2text aiofiles
uv run playwright install
"""

import argparse
import asyncio
import time
import sys
import os
import json
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
from bs4 import BeautifulSoup
from collections import deque
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import html2text
import aiofiles

class AsyncPlaywrightWebCrawler:
    def __init__(self, start_url, max_pages=10, delay=1, headless=True, max_concurrent=3):
        self.start_url = start_url
        self.max_pages = max_pages
        self.delay = delay
        self.headless = headless
        self.max_concurrent = max_concurrent
        self.visited = set()
        self.to_visit = deque([start_url])
        self.base_domain = urlparse(start_url).netloc
        
        # Create output directory
        self.output_dir = Path(f"crawled_{self.base_domain.replace('.', '_')}")
        self.output_dir.mkdir(exist_ok=True)
        
        # Playwright instances
        self.playwright = None
        self.browser = None
        self.context = None
        
        # Content extraction setup
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_emphasis = False
        self.html_converter.body_width = 0  # Don't wrap lines
        
        # Crawl statistics
        self.crawl_stats = {
            'pages_crawled': 0,
            'pages_saved': 0,
            'start_time': time.time(),
            'urls_discovered': 0
        }
    
    async def setup_browser(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()
        
        # Use Chromium for best compatibility
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Create context with realistic browser settings
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
    
    async def cleanup(self):
        """Clean up Playwright resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except:
            pass
    
    def is_valid_url(self, url):
        """Check if URL is valid and within the same domain"""
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc == self.base_domain and
                parsed.scheme in ['http', 'https'] and
                not any(ext in url.lower() for ext in [
                    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
                    '.css', '.js', '.json', '.xml', '.zip', '.rar', '.tar',
                    '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv'
                ])
            )
        except:
            return False
    
    def extract_links(self, html, base_url):
        """Extract all valid links from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        
        # Extract from various link sources
        selectors = [
            'a[href]',           # Standard links
            'area[href]',        # Image map areas
        ]
        
        for selector in selectors:
            for element in soup.select(selector):
                href = element.get('href')
                if href:
                    # Handle relative URLs
                    full_url = urljoin(base_url, href)
                    # Remove fragment identifiers
                    full_url = full_url.split('#')[0]
                    if self.is_valid_url(full_url):
                        links.add(full_url)
        
        return links
    
    def extract_main_content(self, html):
        """Extract main content from HTML, removing navigation, ads, etc."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        unwanted_selectors = [
            'nav', 'header', 'footer', 'aside',
            '.navigation', '.nav', '.menu', '.sidebar',
            '.advertisement', '.ads', '.ad', '.promo',
            '.social', '.share', '.comments', '.comment',
            '.popup', '.modal', '.overlay',
            'script', 'style', 'noscript',
            '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Try to find main content area
        main_content_selectors = [
            'main', 'article', '[role="main"]',
            '.main', '.content', '.post', '.entry',
            '#main', '#content', '#post', '#article'
        ]
        
        main_content = None
        for selector in main_content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # Fallback to body if no main content found
        if not main_content:
            main_content = soup.find('body') or soup
        
        return str(main_content)
    
    async def save_page_content(self, url, title, html_content):
        """Save page content as markdown"""
        try:
            # Extract main content
            main_content_html = self.extract_main_content(html_content)
            
            # Convert to markdown
            markdown_content = self.html_converter.handle(main_content_html)
            
            # Create filename from URL
            filename = re.sub(r'[^\w\-_.]', '_', url.replace('https://', '').replace('http://', ''))
            filename = filename[:100]  # Limit filename length
            if not filename.endswith('.md'):
                filename += '.md'
            
            filepath = self.output_dir / filename
            
            # Create markdown with metadata
            markdown_with_meta = f"""# {title}

**URL:** {url}  
**Crawled:** {time.strftime('%Y-%m-%d %H:%M:%S')}

---

{markdown_content}
"""
            
            # Save asynchronously
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(markdown_with_meta)
            
            self.crawl_stats['pages_saved'] += 1
            return True
            
        except Exception as e:
            print(f"  Error saving content: {e}")
            return False
    
    async def crawl_page(self, semaphore, url):
        """Crawl a single page and return its content and links"""
        async with semaphore:
            page = await self.context.new_page()
            try:
                print(f"Crawling: {url}")
                
                # Navigate to page
                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                if not response:
                    print("  Error: No response received")
                    return None, set()
                
                print(f"  Status: {response.status}")
                
                if response.status >= 400:
                    print(f"  Error: HTTP {response.status}")
                    return None, set()
                
                # Wait for content to load
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    await asyncio.sleep(0.5)  # Additional wait for dynamic content
                except PlaywrightTimeoutError:
                    print("  Warning: Page may still be loading")
                
                # Get page title
                try:
                    title = await page.title()
                    print(f"  Title: {title}")
                except:
                    title = "No title"
                    print("  Title: No title")
                
                # Get page content after JavaScript execution
                html_content = await page.content()
                print(f"  Size: {len(html_content)} bytes")
                
                # Save content as markdown
                saved = await self.save_page_content(url, title, html_content)
                if saved:
                    print("  ✓ Content saved as markdown")
                else:
                    print("  ✗ Failed to save content")
                
                # Extract links from rendered content
                links = self.extract_links(html_content, url)
                print(f"  Found {len(links)} links")
                
                self.crawl_stats['pages_crawled'] += 1
                return html_content, links
                
            except PlaywrightTimeoutError:
                print("  Error: Page load timeout")
                return None, set()
            except Exception as e:
                print(f"  Error: {e}")
                return None, set()
            finally:
                await page.close()
                # Add delay between requests
                await asyncio.sleep(self.delay)
    
    async def save_crawl_summary(self):
        """Save summary of crawl results"""
        summary = {
            'domain': self.base_domain,
            'start_url': self.start_url,
            'crawl_stats': self.crawl_stats,
            'total_urls_visited': list(self.visited),
            'crawl_duration': time.time() - self.crawl_stats['start_time']
        }
        
        summary_path = self.output_dir / 'crawl_summary.json'
        async with aiofiles.open(summary_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(summary, indent=2))
    
    async def crawl(self):
        """Main crawling loop with async concurrency"""
        print(f"Starting async Playwright crawl of {self.start_url}")
        print(f"Max pages: {self.max_pages}")
        print(f"Domain: {self.base_domain}")
        print(f"Concurrent pages: {self.max_concurrent}")
        print(f"Output directory: {self.output_dir}")
        print(f"Mode: {'Headless' if self.headless else 'GUI'}")
        print("-" * 50)
        
        try:
            await self.setup_browser()
            
            # Semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            while self.to_visit and self.crawl_stats['pages_crawled'] < self.max_pages:
                # Collect URLs to crawl in this batch
                batch_urls = []
                while (self.to_visit and 
                       len(batch_urls) < self.max_concurrent and 
                       self.crawl_stats['pages_crawled'] + len(batch_urls) < self.max_pages):
                    
                    url = self.to_visit.popleft()
                    if url not in self.visited:
                        batch_urls.append(url)
                        self.visited.add(url)
                
                if not batch_urls:
                    break
                
                # Crawl batch concurrently
                tasks = [self.crawl_page(semaphore, url) for url in batch_urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"  Error processing {batch_urls[i]}: {result}")
                        continue
                    
                    content, links = result
                    if content is not None:
                        # Add new links to queue
                        new_links = links - self.visited
                        for link in new_links:
                            if link not in self.to_visit:
                                self.to_visit.append(link)
                        
                        self.crawl_stats['urls_discovered'] += len(new_links)
                
                print(f"Progress: {self.crawl_stats['pages_crawled']}/{self.max_pages}")
                print("-" * 30)
            
            # Save crawl summary
            await self.save_crawl_summary()
            
            print(f"\nCrawl completed!")
            print(f"Pages crawled: {self.crawl_stats['pages_crawled']}")
            print(f"Pages saved: {self.crawl_stats['pages_saved']}")
            print(f"Total URLs discovered: {self.crawl_stats['urls_discovered']}")
            print(f"URLs remaining in queue: {len(self.to_visit)}")
            print(f"Output directory: {self.output_dir}")
            print(f"Duration: {time.time() - self.crawl_stats['start_time']:.1f} seconds")
            
        finally:
            await self.cleanup()

async def main():
    parser = argparse.ArgumentParser(description='Async Playwright-based CLI Web Crawler with Markdown export')
    parser.add_argument('url', help='Starting URL to crawl')
    parser.add_argument('pages', type=int, help='Maximum number of pages to crawl')
    parser.add_argument('--delay', type=float, default=1.0, 
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--concurrent', type=int, default=3,
                       help='Maximum concurrent pages to crawl (default: 3)')
    parser.add_argument('--gui', action='store_true',
                       help='Run browser in GUI mode (not headless)')
    
    args = parser.parse_args()
    
    # Validate URL
    if not args.url.startswith(('http://', 'https://')):
        args.url = 'https://' + args.url
    
    if args.pages <= 0:
        print("Error: Number of pages must be positive")
        sys.exit(1)
    
    if args.concurrent <= 0 or args.concurrent > 10:
        print("Error: Concurrent pages must be between 1 and 10")
        sys.exit(1)
    
    try:
        crawler = AsyncPlaywrightWebCrawler(
            args.url, 
            args.pages, 
            args.delay,
            headless=not args.gui,
            max_concurrent=args.concurrent
        )
        await crawler.crawl()
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())