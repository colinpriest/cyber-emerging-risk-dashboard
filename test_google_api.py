#!/usr/bin/env python3
"""
Test script for Google Custom Search API.
"""

import requests
import time
from dotenv import load_dotenv
import os

def test_google_api():
    """Test the Google Custom Search API with a simple query."""
    
    # Load environment variables
    load_dotenv()
    
    google_cx = os.getenv("GOOGLE_CUSTOMSEARCH_CX_KEY")
    google_api_key = os.getenv("GOOGLE_CUSTOMSEARCH_API_KEY")
    
    if not google_cx or not google_api_key:
        print("❌ Missing Google API credentials in .env file")
        print("Please ensure GOOGLE_CUSTOMSEARCH_CX_KEY and GOOGLE_CUSTOMSEARCH_API_KEY are set")
        return False
    
    print("🔍 Testing Google Custom Search API...")
    
    # Test with a simple query
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': google_api_key,
        'cx': google_cx,
        'q': 'cybersecurity',
        'num': 5,  # Just get 5 results for testing
        'dateRestrict': 'm1'  # Last month
    }
    
    try:
        print("Making test request...")
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                print(f"✅ API test successful! Found {len(data['items'])} results")
                print("\nSample results:")
                for i, item in enumerate(data['items'][:3], 1):
                    print(f"  {i}. {item.get('title', 'No title')}")
                    print(f"     Source: {item.get('displayLink', 'Unknown')}")
                    print()
                return True
            else:
                print("❌ No search results found")
                print("Response:", data)
                return False
        elif response.status_code == 429:
            print("❌ Rate limited (429 error)")
            print("This means you've exceeded your API quota")
            return False
        else:
            print(f"❌ API request failed with status code: {response.status_code}")
            print("Response:", response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def test_api_quota():
    """Test API quota and limits."""
    
    print("\n📊 Checking API quota information...")
    
    # Load environment variables
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_CUSTOMSEARCH_API_KEY")
    
    if not google_api_key:
        print("❌ Missing Google API key")
        return
    
    # Note: Google doesn't provide a direct quota endpoint, but we can check usage
    print("ℹ️  Google Custom Search API limits:")
    print("  - Free tier: 100 queries per day")
    print("  - Paid tier: 10,000 queries per day")
    print("  - Rate limit: ~10 queries per second")
    print("\n💡 If you're hitting rate limits, consider:")
    print("  - Upgrading to paid tier")
    print("  - Adding delays between requests")
    print("  - Reducing the number of search terms")

if __name__ == "__main__":
    print("🚀 Google Custom Search API Test")
    print("=" * 40)
    
    success = test_google_api()
    test_api_quota()
    
    if success:
        print("\n✅ API is working correctly!")
        print("You can now run the main analysis script.")
    else:
        print("\n❌ API test failed!")
        print("Please check your credentials and try again.")
