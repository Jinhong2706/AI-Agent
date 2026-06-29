"""
Async Web Scraper Example
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
from dataclasses import dataclass
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Article:
    title: str
    url: str
    summary: str = ""
    published_date: str = ""
    author: str = ""

class AsyncScraper:
    def __init__(self, base_url: str, max_concurrent: int = 10):
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.session = None
        self.seen_urls = set()
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def fetch_page(self, url: str) -> str:
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return ""
    
    async def parse_articles(self, html: str, selector: str = ".article") -> List[Article]:
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        for article_elem in soup.select(selector):
            try:
                title_elem = article_elem.select_one('h2, .title')
                link_elem = article_elem.select_one('a')
                summary_elem = article_elem.select_one('.summary, .excerpt')
                
                if title_elem and link_elem:
                    article = Article(
                        title=title_elem.get_text(strip=True),
                        url=link_elem.get('href', ''),
                        summary=summary_elem.get_text(strip=True) if summary_elem else ""
                    )
                    articles.append(article)
            except Exception as e:
                logger.error(f"Error parsing article: {e}")
        
        return articles
    
    async def scrape(self, max_pages: int = 10) -> List[Article]:
        tasks = []
        page_urls = [f"{self.base_url}/page/{i}" for i in range(1, max_pages + 1)]
        
        for url in page_urls:
            if url in self.seen_urls:
                continue
            self.seen_urls.add(url)
            tasks.append(self.fetch_and_parse(url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
        
        return all_articles
    
    async def fetch_and_parse(self, url: str) -> List[Article]:
        logger.info(f"Fetching: {url}")
        html = await self.fetch_page(url)
        if html:
            return await self.parse_articles(html)
        return []

# Usage example
async def main():
    async with AsyncScraper("https://example-news-site.com") as scraper:
        articles = await scraper.scrape(max_pages=5)
        
        for article in articles[:10]:  # Print first 10 articles
            print(f"\nTitle: {article.title}")
            print(f"URL: {article.url}")
            print(f"Summary: {article.summary[:100]}...")
        
        # Save to JSON
        with open('articles.json', 'w', encoding='utf-8') as f:
            json.dump([{
                'title': a.title,
                'url': a.url,
                'summary': a.summary,
                'published_date': a.published_date,
                'author': a.author
            } for a in articles], f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())