# news_fetcher.py
import requests
import json
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
    Fetches cybersecurity news articles from Google Custom Search API.
    
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
    
    for date_range in date_ranges:
        month_articles = fetch_monthly_articles(
            google_cx, 
            google_api_key, 
            date_range['start'], 
            date_range['end'], 
            articles_per_month
        )
        
        print(f"  {date_range['month']}: Found {len(month_articles)} articles")
        all_articles.extend(month_articles)
    
    # Save all articles to a single file with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    save_path = save_dir / f"{timestamp}.json"
    
    with open(save_path, "w") as f:
        json.dump([article.model_dump() for article in all_articles], f, indent=2)
    
    print(f"Saved {len(all_articles)} articles to {save_path}")
    return all_articles

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
    
    # Cybersecurity search terms
    search_terms = [
        "cybersecurity breach",
        "ransomware attack",
        "data breach",
        "phishing campaign",
        "cyber attack",
        "malware outbreak",
        "zero-day vulnerability",
        "cyber threat",
        "information security incident",
        "cybercrime"
    ]
    
    articles = []
    
    for term in search_terms:
        if len(articles) >= max_results:
            break
            
        params = {
            'key': google_api_key,
            'cx': google_cx,
            'q': f'"{term}"',
            'dateRestrict': f'd{calculate_days_between(start_date, end_date)}',
            'sort': 'date:r:20230101:20241231',  # Sort by date, reverse chronological
            'num': min(10, max_results - len(articles))  # Google allows max 10 per request
        }
        
        try:
            response = requests.get(base_url, params=params)
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
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching articles for term '{term}': {e}")
            continue
    
    return articles

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