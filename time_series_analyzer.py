# time_series_analyzer.py
import instructor
from openai import OpenAI
from typing import List, Dict, Any
from datetime import datetime, timedelta
from data_models import Article, TimeSeriesAnalysis, MonthlyTrend, EventCategory
from news_fetcher import get_historical_news_summary

def analyze_time_series(client: OpenAI, articles: List[Article]) -> TimeSeriesAnalysis:
    """
    Analyzes historical news articles to identify time series trends in cyber events.
    
    Args:
        client: OpenAI client instance
        articles: List of historical articles
    
    Returns:
        TimeSeriesAnalysis object with monthly trends and insights
    """
    
    # Get historical summary data
    monthly_data = get_historical_news_summary(articles)
    
    # Prepare data for LLM analysis
    analysis_data = prepare_time_series_data(monthly_data)
    
    system_prompt = """
    You are a Senior Cyber Threat Intelligence Analyst specializing in time series analysis.
    Your task is to analyze 12 months of cybersecurity news data to identify emerging trends,
    patterns, and insights in the cyber threat landscape.
    
    Analyze the provided monthly data to:
    1. Identify the overall trend direction across the 12-month period
    2. Determine which threat category shows the most volatility
    3. Identify emerging patterns and shifts in the threat landscape
    4. Provide insights about each month's key characteristics
    5. Generate a comprehensive summary of the time series analysis
    
    Focus on:
    - Trend analysis (increasing, decreasing, or stable patterns)
    - Category volatility and shifts in threat types
    - Seasonal patterns or cyclical behaviors
    - Emerging threat categories
    - Strategic implications for organizations
    
    Your analysis should be data-driven and provide actionable insights for cybersecurity strategy.
    """
    
    return client.chat.completions.create(
        model="gpt-4-turbo",
        response_model=TimeSeriesAnalysis,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this 12-month cybersecurity news data:\n{analysis_data}"},
        ],
        max_retries=2,
    )

def prepare_time_series_data(monthly_data: Dict[str, Any]) -> str:
    """
    Prepare monthly data for LLM analysis.
    
    Args:
        monthly_data: Dictionary with monthly breakdown
    
    Returns:
        Formatted string for LLM analysis
    """
    
    # Sort months chronologically
    sorted_months = sorted(monthly_data.keys())
    
    analysis_text = "12-Month Cybersecurity News Analysis Data:\n\n"
    
    for month in sorted_months:
        data = monthly_data[month]
        analysis_text += f"Month: {month}\n"
        analysis_text += f"Total Events: {data['total_count']}\n"
        analysis_text += "Category Breakdown:\n"
        
        for category, count in data['categories'].items():
            percentage = (count / data['total_count']) * 100 if data['total_count'] > 0 else 0
            analysis_text += f"  - {category}: {count} events ({percentage:.1f}%)\n"
        
        # Add sample article titles for context
        analysis_text += "Sample Headlines:\n"
        for i, article in enumerate(data['articles'][:3]):  # Show first 3 articles
            analysis_text += f"  {i+1}. {article.title}\n"
        
        analysis_text += "\n"
    
    return analysis_text

def generate_time_series_commentary(client: OpenAI, time_series_analysis: TimeSeriesAnalysis) -> str:
    """
    Generates detailed commentary on the time series analysis.
    
    Args:
        client: OpenAI client instance
        time_series_analysis: Completed time series analysis
    
    Returns:
        Detailed commentary string
    """
    
    system_prompt = """
    You are a cybersecurity expert providing detailed commentary on time series analysis of cyber threats.
    Based on the provided analysis, write a comprehensive commentary that includes:
    
    1. Executive Summary: High-level overview of the 12-month trend
    2. Key Findings: Most significant discoveries from the analysis
    3. Threat Evolution: How threats have changed over the period
    4. Seasonal Patterns: Any cyclical or seasonal behaviors identified
    5. Strategic Implications: What this means for organizations
    6. Recommendations: Suggested actions based on the trends
    
    Write in a professional, analytical tone suitable for board-level presentation.
    Focus on actionable insights and strategic implications.
    """
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate detailed commentary for this time series analysis:\n{time_series_analysis.model_dump_json(indent=2)}"},
        ],
        max_retries=2,
    )
    
    return response.choices[0].message.content

def create_time_series_chart_data(time_series_analysis: TimeSeriesAnalysis) -> Dict[str, Any]:
    """
    Prepare data for time series charts in the dashboard.
    
    Args:
        time_series_analysis: Completed time series analysis
    
    Returns:
        Dictionary with chart-ready data
    """
    
    # Prepare data for line chart showing total events over time
    timeline_data = {
        'labels': [],
        'datasets': []
    }
    
    # Get all unique categories
    all_categories = set()
    for trend in time_series_analysis.monthly_trends:
        for category in trend.categories:
            all_categories.add(category.category)
    
    # Create dataset for each category
    category_datasets = {}
    for category in all_categories:
        category_datasets[category] = {
            'label': category,
            'data': [],
            'borderColor': get_category_color(category),
            'backgroundColor': get_category_color(category, alpha=0.1),
            'fill': False,
            'tension': 0.4
        }
    
    # Add total events dataset
    total_dataset = {
        'label': 'Total Events',
        'data': [],
        'borderColor': '#667eea',
        'backgroundColor': 'rgba(102, 126, 234, 0.1)',
        'fill': True,
        'tension': 0.4,
        'borderWidth': 3
    }
    
    # Populate data
    for trend in time_series_analysis.monthly_trends:
        timeline_data['labels'].append(trend.month)
        total_dataset['data'].append(trend.total_events)
        
        # Initialize category counts for this month
        month_categories = {cat.category: cat.count for cat in trend.categories}
        
        for category in all_categories:
            count = month_categories.get(category, 0)
            category_datasets[category]['data'].append(count)
    
    # Add datasets to chart data
    timeline_data['datasets'].append(total_dataset)
    for dataset in category_datasets.values():
        timeline_data['datasets'].append(dataset)
    
    return timeline_data

def get_category_color(category: str, alpha: float = 1.0) -> str:
    """
    Get consistent color for a category.
    
    Args:
        category: Category name
        alpha: Alpha value for transparency
    
    Returns:
        Color string
    """
    
    colors = {
        'Ransomware': f'rgba(220, 53, 69, {alpha})',      # Red
        'Data Breach': f'rgba(255, 193, 7, {alpha})',     # Yellow
        'Phishing': f'rgba(40, 167, 69, {alpha})',        # Green
        'Malware': f'rgba(23, 162, 184, {alpha})',        # Cyan
        'Vulnerability': f'rgba(111, 66, 193, {alpha})',   # Purple
        'DDoS': f'rgba(253, 126, 20, {alpha})',           # Orange
        'Supply Chain': f'rgba(108, 117, 125, {alpha})',  # Gray
        'State-Sponsored': f'rgba(220, 53, 69, {alpha})', # Red
        'Insider Threat': f'rgba(255, 193, 7, {alpha})',  # Yellow
        'IoT Security': f'rgba(40, 167, 69, {alpha})',    # Green
        'Other': f'rgba(108, 117, 125, {alpha})'          # Gray
    }
    
    return colors.get(category, f'rgba(108, 117, 125, {alpha})')
