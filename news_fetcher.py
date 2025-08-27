# news_fetcher.py
import requests
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from data_models import Article

def get_news(
    google_cx: str,
    google_api_key: str,
    save_dir: Path,
    months_back: int = 12,
    articles_per_month: int = 10
) -> List[Article]:
    """
    Fetches cybersecurity news articles from Google Custom Search API with caching.
    
    Args:
        google_cx: Google Custom Search Engine ID
        google_api_key: Google API Key
        save_dir: Directory to save fetched articles
        months_back: Number of months to look back (default: 12)
        articles_per_month: Number of articles to fetch per month (default: 10)
    
    Returns:
        List of Article objects with engineered features
    """
    
    all_articles = []
    cache_dir = save_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    # Generate date ranges for each month
    current_date = datetime.now()
    date_ranges = []
    
    for i in range(months_back):
        # Calculate start and end of month
        if i == 0:
            # Current month
            month_start = current_date.replace(day=1)
            month_end = current_date
        else:
            # Previous months
            month_start = (current_date - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
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
        start_date, 
        end_date, 
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

def fetch_monthly_articles(
    google_cx: str,
    google_api_key: str,
    start_date: str,
    end_date: str,
    max_results: int = 10
) -> List[Article]:
    """
    Fetches articles for a specific date range.
    
    Args:
        google_cx: Google Custom Search Engine ID
        google_api_key: Google API Key
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_results: Maximum number of results to fetch
    
    Returns:
        List of Article objects
    """
    
    base_url = "https://www.googleapis.com/customsearch/v1"
    
    # Simplified search terms - less restrictive
    search_terms = [
        "cybersecurity",
        "cyber attack",
        "data breach",
        "ransomware",
        "phishing"
    ]
    
    articles = []
    
    for term in search_terms:
        if len(articles) >= max_results:
            break
            
        # Simplified parameters - remove restrictive date filtering
        params = {
            'key': google_api_key,
            'cx': google_cx,
            'q': term,
            'num': min(10, max_results - len(articles)),  # Google allows max 10 per request
            'dateRestrict': 'm12',  # Last 12 months, less restrictive
            'sort': 'date'  # Sort by date
        }
        
        try:
            response = requests.get(base_url, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                print(f"Rate limited for term '{term}'. Waiting 60 seconds...")
                time.sleep(60)
                continue
                
            response.raise_for_status()
            
            data = response.json()
            
            if 'items' in data:
                for item in data['items']:
                    if len(articles) >= max_results:
                        break
                        
                    # Extract article information
                    title = item.get('title', '')
                    description = item.get('snippet', '')
                    link = item.get('link', '')
                    
                    # Extract source from link
                    source = extract_domain(link)
                    
                    # Extract date if available
                    published_date = None
                    if 'pagemap' in item and 'metatags' in item['pagemap']:
                        metatags = item['pagemap']['metatags'][0]
                        published_date = (
                            metatags.get('article:published_time') or
                            metatags.get('og:updated_time') or
                            metatags.get('date')
                        )
                    
                    # Create Article object
                    article = Article(
                        title=title,
                        description=description,
                        published_date=published_date,
                        source=source
                    )
                    
                    # Avoid duplicates
                    if not any(existing.title == title for existing in articles):
                        articles.append(article)
            
            # Add delay between requests to avoid rate limiting
            time.sleep(2)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching articles for term '{term}': {e}")
            time.sleep(5)  # Wait longer on error
            continue
    
    return articles

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

def extract_domain(url: str) -> str:
    """Extract domain name from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return "unknown.com"

def get_historical_news_summary(articles: List[Article]) -> Dict[str, Any]:
    """
    Creates a summary of historical news data for time series analysis.
    
    Args:
        articles: List of Article objects
    
    Returns:
        Dictionary with monthly breakdown and statistics
    """
    
    # Group articles by month
    monthly_data = {}
    
    for article in articles:
        if article.published_date:
            try:
                # Parse the date and get month
                if 'T' in article.published_date:
                    date_obj = datetime.fromisoformat(article.published_date.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(article.published_date, '%Y-%m-%d')
                
                month_key = date_obj.strftime('%Y-%m')
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'articles': [],
                        'total_count': 0,
                        'categories': {}
                    }
                
                monthly_data[month_key]['articles'].append(article)
                monthly_data[month_key]['total_count'] += 1
                
                # Categorize article based on content
                category = categorize_article(article)
                if category not in monthly_data[month_key]['categories']:
                    monthly_data[month_key]['categories'][category] = 0
                monthly_data[month_key]['categories'][category] += 1
                
            except (ValueError, TypeError):
                continue
    
    return monthly_data

def categorize_article(article: Article) -> str:
    """
    Categorize an article based on its content.
    
    Args:
        article: Article object
    
    Returns:
        Category string
    """
    
    title_lower = article.title.lower()
    desc_lower = article.description.lower()
    content = f"{title_lower} {desc_lower}"
    
    # Define category keywords
    categories = {
        'Ransomware': ['ransomware', 'ransom', 'encryption', 'decrypt'],
        'Data Breach': ['data breach', 'breach', 'leak', 'stolen data', 'compromised'],
        'Phishing': ['phishing', 'spear phishing', 'email scam', 'social engineering'],
        'Malware': ['malware', 'virus', 'trojan', 'spyware', 'botnet'],
        'Vulnerability': ['vulnerability', 'zero-day', 'exploit', 'patch', 'cve'],
        'DDoS': ['ddos', 'distributed denial of service', 'dos attack'],
        'Supply Chain': ['supply chain', 'third party', 'vendor', 'dependency'],
        'State-Sponsored': ['nation state', 'state-sponsored', 'apt', 'advanced persistent threat'],
        'Insider Threat': ['insider', 'employee', 'internal', 'disgruntled'],
        'IoT Security': ['iot', 'internet of things', 'smart device', 'connected device']
    }
    
    # Find the best matching category
    best_category = 'Other'
    max_matches = 0
    
    for category, keywords in categories.items():
        matches = sum(1 for keyword in keywords if keyword in content)
        if matches > max_matches:
            max_matches = matches
            best_category = category
    
    return best_category