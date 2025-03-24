import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
import time
import random

class NewsScraper:
    """
    Class for scraping news articles about companies from Google News
    """
    
    def __init__(self):
        """Initialize the scraper with headers to mimic a browser"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def get_news_links(self, company_name: str, num_articles: int = 20) -> List[str]:
        """
        Get links to news articles about a company from Google News
        
        Args:
            company_name: The name of the company
            num_articles: Maximum number of articles to fetch
            
        Returns:
            List of URLs to news articles
        """
        # Format company name for URL
        query = company_name.replace(' ', '+')
        url = f"https://www.google.com/search?q={query}+news&tbm=nws&num=100"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract all news article links
            links = []
            i=1
            for g in soup.find_all('div', class_='SoaBEf'):
                # Find the anchor tag with the link
                a_tag = g.find('a')
                if a_tag and 'href' in a_tag.attrs:
                    link = a_tag['href']
                    # Check if it's a Google redirect URL
                    if link.startswith('/url?'):
                        # Extract the actual URL
                        link = re.search(r'url=([^&]+)', link).group(1)
                    if link:
                        # Filter out JavaScript-heavy sites and other unwanted domains
                        if not any(domain in link for domain in ['youtube.com', 'facebook.com', 'twitter.com', 'instagram.com']):
                            links.append(link)
                            if len(links) >= num_articles:
                                break
            return links
        
        except Exception as e:
            print(f"Error fetching news links for {company_name}: {e}")
            return []
    
    def scrape_article(self, url: str) -> Dict[str, Any]:
        """
        Scrape the content of a news article
        
        Args:
            url: URL of the article to scrape
            
        Returns:
            Dictionary containing the title and content of the article
        """
        try:
            # Add a random delay to avoid being blocked
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.text if soup.title else "No title found"
            
            # Extract article content
            # First try to find article tags
            article_tag = soup.find('article')
            
            if article_tag:
                content = ' '.join([p.text for p in article_tag.find_all(['p', 'h1', 'h2', 'h3'])])
            else:
                # If no article tag, try to find content in p tags
                content = ' '.join([p.text for p in soup.find_all('p')])
            
            # Clean the content
            content = re.sub(r'\s+', ' ', content).strip()
            
            # If content is too short, it might not be the actual article
            if len(content) < 100:
                content = "Unable to extract meaningful content from this webpage."
            
            return {
                "url": url,
                "title": title,
                "content": content[:5000]  # Limit content length
            }
            
        except Exception as e:
            print(f"Error scraping article at {url}: {e}")
            return {
                "url": url,
                "title": "Error scraping article",
                "content": f"Failed to extract content: {str(e)}"
            }
    
    def get_company_news(self, company_name: str, num_articles: int = 20) -> List[Dict[str, Any]]:
        """
        Get news articles about a company
        
        Args:
            company_name: The name of the company
            num_articles: Maximum number of articles to fetch
            
        Returns:
            List of dictionaries containing article information
        """
        links = self.get_news_links(company_name, num_articles)
        articles = []
        
        for link in links:
            article = self.scrape_article(link)
            if article["content"] != "Unable to extract meaningful content from this webpage.":
                if len(articles)<10:
                    articles.append(article)
        
        print(f"Scraped {len(articles)} articles for {company_name}")
        return articles 