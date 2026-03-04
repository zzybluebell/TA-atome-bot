import cloudscraper
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AtomeCrawler:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://help.atome.ph/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def crawl(self, url: str) -> List[Document]:
        """
        Crawl the Atome help center category page and its articles.
        Returns a list of LangChain Documents.
        """
        logger.info(f"Starting crawl for: {url}")
        try:
            response = self.scraper.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            article_links = set()
            section_links = set()

            # 1. Find direct article links and section links on the category page
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_link = href if href.startswith('http') else f"https://help.atome.ph{href}"
                
                if '/articles/' in href:
                    article_links.add(full_link)
                elif '/sections/' in href:
                    section_links.add(full_link)
            
            logger.info(f"Found {len(article_links)} articles and {len(section_links)} sections on category page.")

            # 2. If we found sections, crawl them to find more articles
            for section_url in section_links:
                try:
                    logger.info(f"Crawling section: {section_url}")
                    sec_response = self.scraper.get(section_url, headers=self.headers)
                    if sec_response.status_code == 200:
                        sec_soup = BeautifulSoup(sec_response.text, 'html.parser')
                        for a in sec_soup.find_all('a', href=True):
                            href = a['href']
                            if '/articles/' in href:
                                full_link = href if href.startswith('http') else f"https://help.atome.ph{href}"
                                article_links.add(full_link)
                except Exception as e:
                    logger.error(f"Error crawling section {section_url}: {e}")

            article_links = list(article_links)
            logger.info(f"Total unique articles found: {len(article_links)}")

            documents = []
            # Crawl all articles (limit increased from 20 to 200 to cover all ~152 articles)
            for link in article_links[:200]: 
                doc = self._crawl_article(link)
                if doc:
                    documents.append(doc)
            
            return documents
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return []

    def _crawl_article(self, url: str) -> Document:
        try:
            logger.info(f"Crawling article: {url}")
            response = self.scraper.get(url, headers=self.headers)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_tag = soup.find('h1', class_='article-title')
            title = title_tag.get_text(strip=True) if title_tag else "No Title"
            
            # Extract body
            body_tag = soup.find('div', class_='article-body')
            body = body_tag.get_text(separator="\n", strip=True) if body_tag else ""
            
            if not body:
                return None

            return Document(
                page_content=f"Title: {title}\nURL: {url}\nContent:\n{body}",
                metadata={"source": url, "title": title}
            )
        except Exception as e:
            logger.error(f"Error crawling article {url}: {e}")
            return None
