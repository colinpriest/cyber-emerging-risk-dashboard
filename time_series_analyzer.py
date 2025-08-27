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
    
    # Create actual time series data from real articles
    monthly_trends = create_actual_monthly_trends(monthly_data)
    
    # Calculate overall trend from actual data
    overall_trend = calculate_overall_trend(monthly_data)
    
    # Calculate most volatile category from actual data
    most_volatile_category = calculate_most_volatile_category(monthly_data)
    
    # Generate insights from actual data
    emerging_patterns = identify_emerging_patterns(monthly_data)
    
    # Create summary from actual data
    time_series_summary = create_summary_from_data(monthly_data)
    
    return TimeSeriesAnalysis(
        monthly_trends=monthly_trends,
        overall_trend=overall_trend,
        most_volatile_category=most_volatile_category,
        emerging_patterns=emerging_patterns,
        time_series_summary=time_series_summary
    )

def create_actual_monthly_trends(monthly_data: Dict[str, Any]) -> List[MonthlyTrend]:
    """
    Create actual monthly trends from real article data.
    
    Args:
        monthly_data: Dictionary with monthly breakdown
    
    Returns:
        List of MonthlyTrend objects with actual counts
    """
    
    monthly_trends = []
    sorted_months = sorted(monthly_data.keys())
    
    for month in sorted_months:
        data = monthly_data[month]
        
        # Create EventCategory objects from actual data
        categories = []
        for category_name, count in data['categories'].items():
            categories.append(EventCategory(
                category=category_name,
                count=count,
                trend="stable",  # We don't have historical data to calculate trends
                percentage_change=0.0  # We don't have historical data to calculate changes
            ))
        
        # Find top threat (category with highest count)
        top_threat = max(data['categories'].items(), key=lambda x: x[1])[0] if data['categories'] else "None"
        
        # Create key insight based on actual data
        total_articles = data['total_count']
        key_insight = f"Found {total_articles} cybersecurity articles in {month}"
        if data['categories']:
            top_category = max(data['categories'].items(), key=lambda x: x[1])
            key_insight += f", with {top_category[0]} being the most prominent threat ({top_category[1]} articles)"
        
        monthly_trend = MonthlyTrend(
            month=month,
            total_events=data['total_count'],  # Actual article count
            categories=categories,
            top_threat=top_threat,
            key_insight=key_insight
        )
        
        monthly_trends.append(monthly_trend)
    
    return monthly_trends

def calculate_overall_trend(monthly_data: Dict[str, Any]) -> str:
    """Calculate overall trend from actual monthly data."""
    if len(monthly_data) < 2:
        return "insufficient_data"
    
    # Get total counts for each month
    monthly_counts = []
    sorted_months = sorted(monthly_data.keys())
    
    for month in sorted_months:
        monthly_counts.append(monthly_data[month]['total_count'])
    
    # Calculate trend
    if len(monthly_counts) >= 2:
        first_half = sum(monthly_counts[:len(monthly_counts)//2])
        second_half = sum(monthly_counts[len(monthly_counts)//2:])
        
        if second_half > first_half * 1.1:  # 10% increase threshold
            return "increasing"
        elif second_half < first_half * 0.9:  # 10% decrease threshold
            return "decreasing"
        else:
            return "stable"
    
    return "stable"

def calculate_most_volatile_category(monthly_data: Dict[str, Any]) -> str:
    """Calculate most volatile category from actual data."""
    if len(monthly_data) < 2:
        return "insufficient_data"
    
    category_variance = {}
    
    # Get all unique categories
    all_categories = set()
    for month_data in monthly_data.values():
        all_categories.update(month_data['categories'].keys())
    
    for category in all_categories:
        counts = []
        for month_data in monthly_data.values():
            counts.append(month_data['categories'].get(category, 0))
        
        if len(counts) > 1:
            # Calculate variance
            mean_count = sum(counts) / len(counts)
            variance = sum((count - mean_count) ** 2 for count in counts) / len(counts)
            category_variance[category] = variance
    
    if category_variance:
        return max(category_variance.items(), key=lambda x: x[1])[0]
    else:
        return "none"

def identify_emerging_patterns(monthly_data: Dict[str, Any]) -> List[str]:
    """Identify emerging patterns from actual data."""
    patterns = []
    
    if len(monthly_data) < 2:
        return ["Insufficient data for pattern analysis"]
    
    # Check for increasing trend
    monthly_counts = []
    sorted_months = sorted(monthly_data.keys())
    for month in sorted_months:
        monthly_counts.append(monthly_data[month]['total_count'])
    
    if len(monthly_counts) >= 3:
        # Check if recent months show an increase
        recent_avg = sum(monthly_counts[-3:]) / 3
        earlier_avg = sum(monthly_counts[:-3]) / len(monthly_counts[:-3]) if len(monthly_counts) > 3 else monthly_counts[0]
        
        if recent_avg > earlier_avg * 1.2:
            patterns.append("Recent increase in cyber threat activity")
        elif recent_avg < earlier_avg * 0.8:
            patterns.append("Recent decrease in cyber threat activity")
    
    # Check for category dominance
    all_categories = {}
    for month_data in monthly_data.values():
        for category, count in month_data['categories'].items():
            all_categories[category] = all_categories.get(category, 0) + count
    
    if all_categories:
        top_category = max(all_categories.items(), key=lambda x: x[1])
        total_articles = sum(all_categories.values())
        if top_category[1] > total_articles * 0.4:  # If one category is >40% of total
            patterns.append(f"{top_category[0]} is the dominant threat category")
    
    return patterns if patterns else ["No clear patterns identified in available data"]

def create_summary_from_data(monthly_data: Dict[str, Any]) -> str:
    """Create summary from actual data."""
    if not monthly_data:
        return "No data available for analysis."
    
    total_articles = sum(data['total_count'] for data in monthly_data.values())
    total_months = len(monthly_data)
    
    # Get category breakdown
    all_categories = {}
    for month_data in monthly_data.values():
        for category, count in month_data['categories'].items():
            all_categories[category] = all_categories.get(category, 0) + count
    
    summary = f"Analysis of {total_articles} cybersecurity articles across {total_months} months. "
    
    if all_categories:
        top_category = max(all_categories.items(), key=lambda x: x[1])
        summary += f"The most common threat type was {top_category[0]} with {top_category[1]} articles. "
    
    avg_per_month = total_articles / total_months if total_months > 0 else 0
    summary += f"Average of {avg_per_month:.1f} articles per month."
    
    return summary

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
    
    IMPORTANT: The data represents actual news articles (maximum 10 per month). Focus on
    insights from this real data rather than assuming larger datasets.
    
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
        'label': 'Total Articles',
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
