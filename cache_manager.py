#!/usr/bin/env python3
"""
Cache management utility for the cyber emerging risk detector.
"""

from pathlib import Path
from datetime import datetime
from news_fetcher import get_cache_info, clear_cache

def display_cache_info():
    """Display detailed information about the cache."""
    
    print("🗄️  News Cache Information")
    print("=" * 50)
    
    cache_info = get_cache_info()
    
    if not cache_info['exists']:
        print("📁 No cache directory found.")
        print(f"Cache location: {cache_info['cache_dir']}")
        return
    
    print(f"📁 Cache directory: {cache_info['cache_dir']}")
    print(f"📊 Total cache files: {cache_info.get('file_count', 0)}")
    print(f"📰 Total cached articles: {cache_info['total_articles']}")
    
    if cache_info['oldest_cache']:
        print(f"📅 Oldest cache: {cache_info['oldest_cache']}")
    if cache_info['newest_cache']:
        print(f"📅 Newest cache: {cache_info['newest_cache']}")
    
    print("\n📋 Cache Files:")
    print("-" * 50)
    
    if cache_info['files']:
        for file_info in sorted(cache_info['files'], key=lambda x: x.get('month', '')):
            if 'error' in file_info:
                print(f"❌ {file_info['file']}: ERROR - {file_info['error']}")
            else:
                age = file_info.get('age_days', 0)
                status = "🟢 Fresh" if age < 7 else "🟡 Recent" if age < 30 else "🔴 Old"
                print(f"{status} {file_info['file']}")
                print(f"    Month: {file_info['month']}")
                print(f"    Articles: {file_info['article_count']}")
                print(f"    Cached: {file_info['cache_date']} ({age} days ago)")
                print()
    else:
        print("No cache files found.")

def clear_cache_command():
    """Clear the cache with confirmation."""
    
    print("🗑️  Clear News Cache")
    print("=" * 30)
    
    cache_info = get_cache_info()
    
    if not cache_info['exists'] or not cache_info['files']:
        print("📁 No cache to clear.")
        return
    
    print(f"📊 Found {cache_info.get('file_count', 0)} cache files")
    print(f"📰 Total articles to remove: {cache_info['total_articles']}")
    
    response = input("\n❓ Are you sure you want to clear the cache? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        clear_cache()
        print("✅ Cache cleared successfully!")
    else:
        print("❌ Cache clear cancelled.")

def cache_health_check():
    """Check the health of the cache and identify issues."""
    
    print("🏥 Cache Health Check")
    print("=" * 30)
    
    cache_info = get_cache_info()
    
    if not cache_info['exists']:
        print("📁 No cache directory found - this is normal for first run.")
        return
    
    issues = []
    warnings = []
    
    for file_info in cache_info['files']:
        if 'error' in file_info:
            issues.append(f"Corrupted cache file: {file_info['file']}")
        else:
            age = file_info.get('age_days', 0)
            if age > 30:
                warnings.append(f"Old cache for {file_info['month']}: {age} days old")
            elif age > 7:
                warnings.append(f"Recent cache for {file_info['month']}: {age} days old")
    
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print()
    
    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if not issues and not warnings:
        print("✅ Cache is healthy!")
    
    print(f"📊 Summary: {len(cache_info['files'])} files, {cache_info['total_articles']} articles")

def main():
    """Main cache management interface."""
    
    print("🗄️  Cyber Emerging Risk Detector - Cache Manager")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. 📋 View cache information")
        print("2. 🏥 Health check")
        print("3. 🗑️  Clear cache")
        print("4. 🚪 Exit")
        
        choice = input("\nSelect an option (1-4): ").strip()
        
        if choice == '1':
            display_cache_info()
        elif choice == '2':
            cache_health_check()
        elif choice == '3':
            clear_cache_command()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please select 1-4.")

if __name__ == "__main__":
    main()
