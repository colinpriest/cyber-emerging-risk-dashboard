#!/usr/bin/env python3
"""
News fetcher module for cyber security emerging risk detector.
Fetches cybersecurity news from Google Custom Search API.
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from data_models import Article, CyberEventCategory
import re
from dateutil.parser import parse as dateutil_parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field

class ArticleToClassify(BaseModel):
    id: int
    text: str

class ClassifiedArticle(BaseModel):
    id: int
    category: CyberEventCategory
    is_cyber_event: bool = Field(..., description="Set to True if the article is about a specific, recent cyber attack event, otherwise False.")

def scrape_article_for_date(browser, url: str) -> Optional[str]:
    """
    Scrapes a URL for a publication date using an isolated, stealthed Playwright page.
    """
    page = None
    try:
        page = browser.new_page()
        stealth_sync(page) # Apply stealth measures

        response = page.goto(url, timeout=20000, wait_until='domcontentloaded')
        if not response or not response.ok:
            print(f"    - Scraping failed for {url}: HTTP status {response.status if response else 'N/A'}")
            return None

        content = page.content()
        soup = BeautifulSoup(content, 'lxml')

        # More comprehensive selectors for finding dates in HTML
        selectors = [
            {'tag': 'meta', 'attrs': {'property': 'article:published_time'}},
            {'tag': 'meta', 'attrs': {'name': 'pubdate'}},
            {'tag': 'meta', 'attrs': {'name': 'date'}},
            {'tag': 'time', 'attrs': {}},
        ]
        for selector in selectors:
            element = soup.find(selector['tag'], selector['attrs'])
            if element:
                date_str = element.get('content') or element.text
                if date_str:
                    return date_str
    except PlaywrightTimeoutError:
        print(f"    - Scraping timed out for {url}")
    except Exception as e:
        print(f"    - Scraping failed for {url}: {e}")
    finally:
        if page:
            page.close()
    return None


def parse_date(
    raw_article_pagemap: Dict[str, Any],
    fallback_month: str,
    browser: Optional[Any] = None,
    url: Optional[str] = None
) -> Optional[str]:
    """
    Parses the publication date from a Google search result item.
    Uses multiple fallbacks, including scraping the article page.
    """
    # Primary method: Check for structured date data in 'pagemap'
    if raw_article_pagemap:
        try:
            # Look in various common places for date metadata
            metatags = raw_article_pagemap.get('metatags', [{}])[0]
            cse_image = raw_article_pagemap.get('cse_image', [{}])[0]
            
            date_str = (
                metatags.get('og:article:published_time') or
                metatags.get('article:published_time') or
                metatags.get('og:published_time') or
                metatags.get('published_date') or
                metatags.get('date') or
                cse_image.get('date') # Check image metadata as a last resort
            )
            if date_str:
                return date_str
        except (KeyError, IndexError):
            pass

    # Fallback 1: Scrape the article URL for the date if other methods fail
    if browser and url:
        scraped_date = scrape_article_for_date(browser, url)
        if scraped_date:
            return scraped_date

    # Fallback 2: If no date found, assign to the first day of the month being queried
    try:
        year, month = map(int, fallback_month.split('-'))
        return datetime(year, month, 1).isoformat()
    except (ValueError, TypeError):
        return None


def run_google_search(
    google_cx: str,
    google_api_key: str,
    query: str,
    sort_by_date_range: str,
    pages: int = 10
) -> List[Dict[str, Any]]:
    """
    Generic function to run a paginated Google Custom Search.
    This function directly calls the Google Custom Search API endpoint.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    all_results = []
    
    for i in range(pages):
        start_index = 1 + (i * 10)
        params = {
            "key": google_api_key,
            "cx": google_cx,
            "q": query,
            "num": 10,
            "sort": sort_by_date_range,
            "start": start_index
        }
        try:
            response = requests.get(url, params=params, timeout=20)
            if response.status_code == 429:
                print("    - Rate limited by Google API. Waiting 60s...")
                time.sleep(60)
                response = requests.get(url, params=params, timeout=20) # Retry once
            
            response.raise_for_status()
            data = response.json()
            results = data.get("items", [])
            
            if not results:
                break
            
            all_results.extend(results)
            time.sleep(1) # Small delay between pages
        except requests.RequestException as e:
            print(f"    - Error during Google search for query '{query}': {e}")
            break # Stop trying for this query if an error occurs
    
    return all_results

def fetch_monthly_articles(
    google_cx: str,
    google_api_key: str,
    month_key: str,
    articles_needed: int = 100, # Increased to 100
) -> List[Article]:
    """
    Fetches and processes news articles for a specific month.
    """
    start_date_obj = datetime.strptime(f"{month_key}-01", "%Y-%m-%d")
    end_of_month = (start_date_obj + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    end_date_str = end_of_month.strftime("%Y-%m-%d")
    start_date_str = start_date_obj.strftime("%Y-%m-%d")

    filter_after_date = datetime(2024, 7, 1)

    search_query = f'cybersecurity ("data breach" OR "ransomware" OR "phishing" OR "vulnerability") after:{start_date_str} before:{end_date_str}'
    sort_by_date_range = f"date:r:{start_date_str.replace('-', '')}:{end_date_str.replace('-', '')}"

    raw_articles = run_google_search(google_cx, google_api_key, search_query, sort_by_date_range)
    print(f"    Fetched {len(raw_articles)} potential articles for {month_key}.")

    processed_articles = []
    processed_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for raw_article in raw_articles:
            link = raw_article.get("link")
            if not link or link in processed_urls:
                continue

            pagemap = raw_article.get('pagemap', {})
            published_date_str = parse_date(
                pagemap, # Pass the whole pagemap object
                month_key,
                browser=browser,
                url=link
            )

            if not published_date_str:
                continue

            try:
                published_date = dateutil_parse(published_date_str, ignoretz=True)
            except (ValueError, TypeError):
                continue
            
            # Filtering logic
            if published_date < filter_after_date:
                continue
            if not (start_date_obj <= published_date <= end_of_month):
                continue

            title = raw_article.get("title", "No Title")
            description = raw_article.get("snippet", "No Description").replace("\n", "")
            source_domain = extract_domain(link)

            article = Article(
                title=title,
                description=description,
                published_date=published_date.isoformat(),
                source=source_domain,
            )
            processed_articles.append(article)
            processed_urls.add(link)

            if len(processed_articles) >= articles_needed:
                break
        
        browser.close()

    return processed_articles


def get_news(google_cx: str, google_api_key: str, save_dir: Path, months_back: int = 12, articles_per_month: int = 10) -> List[Article]:
    """
    Fetches cybersecurity news articles for the specified time period.
    
    Args:
        google_cx: Google Custom Search Engine ID
        google_api_key: Google API Key
        save_dir: Directory to save news articles
        months_back: Number of months to go back
        articles_per_month: Number of articles to fetch per month
    
    Returns:
        List of Article objects
    """
    
    all_articles = []
    cache_dir = save_dir / "cache"
    cache_dir.mkdir(exist_ok=True)

    # Generate date ranges for each month
    current_date = datetime.now()
    date_ranges = []
    
    for i in range(months_back):
        # Calculate start and end of month using proper month arithmetic
        if i == 0:
            # Current month
            month_start = current_date.replace(day=1)
            month_end = current_date
        else:
            # Previous months - use proper month calculation
            # Go back i months from current date
            year = current_date.year
            month = current_date.month - i
            
            # Handle year rollback
            while month <= 0:
                month += 12
                year -= 1
            
            month_start = datetime(year, month, 1)
            # Calculate end of month
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            month_end = next_month - timedelta(days=1)
        
        date_ranges.append({
            'start': month_start.strftime('%Y-%m-%d'),
            'end': month_end.strftime('%Y-%m-%d'),
            'month': month_start.strftime('%Y-%m')
        })

    print(f"Fetching {articles_per_month} articles for each of the past {months_back} months...")
    print("Using cache to avoid unnecessary API calls...")
    
    for date_range in date_ranges:
        month_articles = fetch_monthly_articles_with_cache(
            google_cx,
            google_api_key,
            date_range['start'], 
            date_range['end'], 
            date_range['month'],
            articles_per_month,
            cache_dir
        )
        
        print(f"  {date_range['month']}: Found {len(month_articles)} articles")
        all_articles.extend(month_articles)
        
        # Add delay to avoid rate limiting (only for new API calls)
        time.sleep(1)
    
    # Save all articles to a single file with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    save_path = save_dir / f"{timestamp}.json"
    
    with open(save_path, "w") as f:
        json.dump([article.model_dump() for article in all_articles], f, indent=2)
    
    print(f"Saved {len(all_articles)} articles to {save_path}")
    return all_articles


def fetch_monthly_articles_with_cache(
    google_cx: str,
    google_api_key: str,
    start_date: str,
    end_date: str,
    month_key: str,
    max_results: int = 10,
    cache_dir: Path = None
) -> List[Article]:
    """
    Fetches articles for a specific date range with caching.
    
    Args:
        google_cx: Google Custom Search Engine ID
        google_api_key: Google API Key
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        month_key: Month key for caching (YYYY-MM format)
        max_results: Maximum number of results to fetch
        cache_dir: Directory for cache files
    
    Returns:
        List of Article objects
    """
    
    # Check cache first
    cache_file = cache_dir / f"{month_key}_articles.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Check if cache is recent (within 7 days for current month, 30 days for past months)
            cache_date = datetime.fromisoformat(cached_data.get('cache_date', '2020-01-01'))
            current_date = datetime.now()
            
            # Determine cache validity period
            if month_key == current_date.strftime('%Y-%m'):
                # Current month: cache for 7 days
                cache_valid_days = 7
            else:
                # Past months: cache for 30 days
                cache_valid_days = 30
            
            if (current_date - cache_date).days < cache_valid_days:
                print(f"    📦 Using cached data for {month_key} (cached {cached_data.get('cache_date', 'unknown')})")
                articles = [Article(**article_data) for article_data in cached_data.get('articles', [])]
                return articles[:max_results]
            else:
                print(f"    ⏰ Cache expired for {month_key}, fetching fresh data...")
        except Exception as e:
            print(f"    ⚠️  Cache corrupted for {month_key}: {e}, fetching fresh data...")
    
    # Fetch fresh data if no cache or cache expired
    print(f"    🔍 Fetching fresh data for {month_key}...")
    articles = fetch_monthly_articles(
        google_cx, 
        google_api_key, 
        month_key,  # Pass month_key for fallback
        max_results
    )
    
    # Save to cache
    if cache_dir:
        cache_data = {
            'month': month_key,
            'cache_date': datetime.now().isoformat(),
            'articles': [article.model_dump() for article in articles],
            'count': len(articles)
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            print(f"    💾 Cached {len(articles)} articles for {month_key}")
        except Exception as e:
            print(f"    ⚠️  Failed to cache data for {month_key}: {e}")

    return articles


def convert_to_ascii(text: str) -> str:
    """
    Convert text to ASCII, removing or replacing Unicode characters.
    
    Args:
        text: Input text that may contain Unicode characters
    
    Returns:
        ASCII-only text string
    """
    if not text:
        return ""
    
    # First try to encode to ASCII with errors='ignore' to remove non-ASCII chars
    try:
        # Convert to ASCII, ignoring characters that can't be encoded
        ascii_text = text.encode('ascii', errors='ignore').decode('ascii')
        
        # Clean up common Unicode punctuation replacements
        replacements = {
            '"': '"',  # Smart quotes
            '"': '"',
            ''': "'",
            ''': "'",
            '–': "-",  # En dash
            '—': "-",  # Em dash
            '…': "...",  # Ellipsis
            '®': "(R)",
            '©': "(C)",
            '™': "(TM)",
            '°': " degrees",
            '±': "+/-",
        }
        
        for unicode_char, ascii_replacement in replacements.items():
            ascii_text = ascii_text.replace(unicode_char, ascii_replacement)
        
        # Remove any remaining non-printable characters except common whitespace
        cleaned_text = ''.join(char for char in ascii_text if char.isprintable() or char in '\n\r\t ')
        
        # Clean up multiple spaces
        cleaned_text = ' '.join(cleaned_text.split())
        
        return cleaned_text
        
    except Exception:
        # Fallback: very aggressive ASCII conversion
        return ''.join(char for char in text if ord(char) < 128 and (char.isprintable() or char in '\n\r\t '))


def extract_domain(url: str) -> str:
    """Extract domain name from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return convert_to_ascii(parsed.netloc)
    except:
        return "unknown.com"


def categorize_articles_with_llm(client: instructor.Instructor, articles: List[Article]) -> List[Article]:
    """
    Classifies a list of articles using an LLM according to the defined taxonomy.
    """
    
    # Create a list of articles with a simple ID for the LLM to reference
    articles_to_classify = [
        ArticleToClassify(id=i, text=f"Title: {article.title}\nDescription: {article.description}")
        for i, article in enumerate(articles)
    ]
    
    try:
        classified_results = client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=List[ClassifiedArticle],
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert cybersecurity analyst. Your task is to classify news articles. For each article, provide two outputs:\n"
                        "1. `category`: Choose the single best category from the provided taxonomy.\n"
                        "2. `is_cyber_event`: Set this to `True` ONLY if the article describes a specific, recent cyber attack, data breach, or ransomware incident at a named entity. "
                        "Set it to `False` if the article is general news, educational content, policy discussion, a product announcement, or a vulnerability report without a specific active exploit mentioned.\n\n"
                        f"Taxonomy:\n{', '.join([cat.value for cat in CyberEventCategory])}"
                    )
                },
                {
                    "role": "user",
                    "content": f"Please classify the following articles:\n{json.dumps([a.model_dump() for a in articles_to_classify], indent=2)}"
                }
            ],
            max_retries=2
        )
        
        # Map the classifications back to the original Article objects
        for result in classified_results:
            if result.id < len(articles):
                articles[result.id].category = result.category
                articles[result.id].is_cyber_event = result.is_cyber_event
        
        return articles

    except Exception as e:
        print(f"    - LLM categorization failed: {e}")
        # In case of failure, assign default values
        for article in articles:
            article.category = CyberEventCategory.OTHER
            article.is_cyber_event = False # Default to False to be safe
        return articles

def get_historical_news_summary(articles: List[Article]) -> Dict[str, Any]:
    """
    Creates a summary of historical news data from pre-categorized articles.
    """
    
    # Group articles by month
    monthly_data = {}
    
    for article in articles:
        month_key = None
        
        if article.published_date:
            try:
                date_obj = dateutil_parse(article.published_date, ignoretz=True)
                month_key = date_obj.strftime('%Y-%m')
            except (ValueError, TypeError, AttributeError):
                print(f"    ⚠️ Could not parse date '{article.published_date}' for article '{article.title[:30]}...'. Skipping.")
                continue
        
        if not month_key:
            print(f"    ⚠️ Article '{article.title[:30]}...' has a null date after fetching. Skipping.")
            continue

        if month_key not in monthly_data:
            monthly_data[month_key] = {
                'articles': [],
                'total_count': 0,
                'categories': {}
            }
        
        monthly_data[month_key]['articles'].append(article)
        monthly_data[month_key]['total_count'] += 1
        
        # Use the pre-assigned category from the LLM
        category = article.category.value if article.category else CyberEventCategory.OTHER.value
        if category not in monthly_data[month_key]['categories']:
            monthly_data[month_key]['categories'][category] = 0
        monthly_data[month_key]['categories'][category] += 1
    
    return monthly_data


def clear_cache(cache_dir: Path = None) -> None:
    """
    Clear the cache directory.
    
    Args:
        cache_dir: Directory for cache files (defaults to news/cache)
    """
    if cache_dir is None:
        cache_dir = Path("news/cache")
    
    if cache_dir.exists():
        for cache_file in cache_dir.glob("*.json"):
            cache_file.unlink()
        print(f"🗑️  Cleared cache directory: {cache_dir}")
    else:
        print(f"📁 Cache directory does not exist: {cache_dir}")


def get_cache_info(cache_dir: Path = None) -> Dict[str, Any]:
    """
    Get information about cached data.
    
    Args:
        cache_dir: Directory for cache files (defaults to news/cache)
    
    Returns:
        Dictionary with cache information
    """
    if cache_dir is None:
        cache_dir = Path("news/cache")
    
    cache_info = {
        'cache_dir': str(cache_dir),
        'exists': cache_dir.exists(),
        'files': [],
        'total_articles': 0,
        'oldest_cache': None,
        'newest_cache': None
    }
    
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.json"))
        cache_info['file_count'] = len(cache_files)
        
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                cache_date = datetime.fromisoformat(data.get('cache_date', '2020-01-01'))
                month = data.get('month', 'unknown')
                count = data.get('count', 0)
                
                cache_info['files'].append({
                    'file': cache_file.name,
                    'month': month,
                    'cache_date': data.get('cache_date'),
                    'article_count': count,
                    'age_days': (datetime.now() - cache_date).days
                })
                
                cache_info['total_articles'] += count
                
                if cache_info['oldest_cache'] is None or cache_date < datetime.fromisoformat(cache_info['oldest_cache']):
                    cache_info['oldest_cache'] = data.get('cache_date')
                
                if cache_info['newest_cache'] is None or cache_date > datetime.fromisoformat(cache_info['newest_cache']):
                    cache_info['newest_cache'] = data.get('cache_date')
                    
            except Exception as e:
                cache_info['files'].append({
                    'file': cache_file.name,
                    'error': str(e)
                })
    
    return cache_info


def calculate_days_between(start_date: str, end_date: str) -> int:
    """Calculate the number of days between two dates."""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    return (end - start).days + 1