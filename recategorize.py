#!/usr/bin/env python3
"""
A script to analyze articles categorized as "Other" and suggest new categories.
"""

import os
import json
from pathlib import Path
from typing import List
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv

# Import the Article model from our existing data_models
from data_models import Article, CyberEventCategory

# --- Pydantic Models for LLM Interaction ---

class ArticleForRecategorization(BaseModel):
    """A simplified model for sending article data to the LLM."""
    title: str
    description: str

class SuggestedCategory(BaseModel):
    """A model to structure the LLM's suggestion for a new category."""
    suggested_category_name: str = Field(..., description="A concise, well-named new category for a group of articles.")
    rationale: str = Field(..., description="A brief explanation of why this new category is needed and what it covers.")
    article_titles: List[str] = Field(..., description="A list of the article titles from the input that fit into this new category.")

class CategorySuggestions(BaseModel):
    """The top-level response model from the LLM."""
    suggestions: List[SuggestedCategory]

def analyze_other_category():
    """
    Finds articles categorized as "Other", sends them to an LLM for new category
    suggestions, and prints the results.
    """
    load_dotenv(find_dotenv())
    
    # Configure OpenAI client
    try:
        client = instructor.patch(OpenAI())
    except Exception as e:
        print(f"❌ Error: Failed to initialize OpenAI client. Have you set your OPENAI_API_KEY? Error: {e}")
        return

    # Find the latest news file
    news_dir = Path("news")
    try:
        latest_news_file = max(news_dir.glob("*.json"), key=os.path.getctime)
        print(f"🔎 Analyzing latest news file: {latest_news_file.name}\n")
    except ValueError:
        print("❌ Error: No news files found in the 'news' directory.")
        return

    # Load and filter articles
    with open(latest_news_file, "r", encoding="utf-8") as f:
        all_articles_data = json.load(f)
        all_articles = [Article(**data) for data in all_articles_data]

    other_articles = [
        article for article in all_articles 
        if article.category and article.category == CyberEventCategory.OTHER
    ]

    if not other_articles:
        print("✅ No articles were categorized as 'Other'. No analysis needed.")
        return

    print(f"Found {len(other_articles)} articles categorized as 'Other'.")
    print("----------------------------------------------------")
    for article in other_articles:
        print(f"  - {article.title}")
    print("----------------------------------------------------\n")

    articles_to_analyze = [
        ArticleForRecategorization(title=a.title, description=a.description) 
        for a in other_articles
    ]

    # Send to LLM for suggestions
    print("🤖 Sending to AI for new category suggestions...\n")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=CategorySuggestions,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert cybersecurity taxonomist. Analyze the provided list of articles, "
                        "which were all categorized as 'Other'. Your task is to identify common themes or specific, "
                        "recurring event types within this group. Based on your analysis, suggest new, more precise "
                        "category names. For each new category you suggest, provide a brief rationale and list the "
                        "titles of the articles that fit into it."
                    )
                },
                {
                    "role": "user",
                    "content": f"Here are the articles to re-categorize:\n{json.dumps([a.model_dump() for a in articles_to_analyze], indent=2)}"
                }
            ]
        )

        # Report the suggestions
        print("💡 AI Recommendations for New Categories:")
        print("==========================================")
        if not response.suggestions:
            print("The AI did not find any clear new categories to suggest.")
        
        for suggestion in response.suggestions:
            print(f"\n🆕 Suggested Category: {suggestion.suggested_category_name}")
            print(f"   Rationale: {suggestion.rationale}")
            print("   Matching Articles:")
            for title in suggestion.article_titles:
                print(f"     - {title}")
        print("\n==========================================")

    except Exception as e:
        print(f"❌ Error: Failed to get suggestions from the AI. Error: {e}")

if __name__ == "__main__":
    analyze_other_category()
