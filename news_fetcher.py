# news_fetcher.py
import requests
import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from data_models import Article

def get_news(google_cx: str, google_api_key: str, save_dir: Path) -> List[Article]:
    """
    Fetches cybersecurity news using Google Custom Search API and engineers features.
    
    Returns:
        A list of Article objects, each containing title, description, published date, and source.
    """
    search_terms = [
        '"cybersecurity risk"', '"cyber threat"', '"data breach"', 
        '"ransomware attack"', '"phishing"', '"malware"', '"cyber attack"',
        '"information security"', '"cyber insurance"', '"data protection"',
        '"privacy regulations"', '"GDPR compliance"', '"cyber risk management"'
    ]
    query = " OR ".join(search_terms)

    params = {
        "q": query,
        "cx": google_cx,
        "key": google_api_key,
        "num": 10,
        "lr": "lang_en",
        "filter": 1,
        "dateRestrict": "m1",  # Last month
        "cr": "countryUS",
        "start": 1,
    }

    try:
        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        response.raise_for_status()
        search_results = response.json().get("items", [])
        
        # Save raw results for auditing
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        with open(save_dir / f"{timestamp}.json", "w") as f:
            json.dump(search_results, f, indent=2)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return []

    # Feature Engineering Step
    articles: List[Article] = []
    for item in search_results:
        try:
            metatags = item.get("pagemap", {}).get("metatags", [{}])[0]
            article = Article(
                title=metatags.get("og:title", item.get("title")),
                description=metatags.get("og:description", item.get("snippet")),
                # Extracting date and source is key for trend analysis
                published_date=metatags.get("article:published_time"),
                source=item.get("displayLink", "Unknown Source")
            )
            articles.append(article)
        except Exception as e:
            print(f"Error processing article {item.get('link')}: {e}")

    return articles