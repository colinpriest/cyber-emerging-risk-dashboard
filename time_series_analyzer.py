# time_series_analyzer.py
import instructor
from openai import OpenAI
from typing import List, Dict, Any
from datetime import datetime, timedelta
from data_models import Article, TimeSeriesAnalysis, MonthlyTrend, EventCategory
from news_fetcher import get_historical_news_summary, convert_to_ascii
import json
from risk_analyzer import convert_model_to_ascii

class TimeSeriesAnalyzer:
    def __init__(self, client: OpenAI):
        self.client = client

    def analyze_time_series(self, monthly_data: Dict[str, Any], output_path: str) -> TimeSeriesAnalysis:
        """
        Analyzes historical news data to identify trends.
        The analysis result is saved to a JSON file.
        """
        print("Analyzing time series trends over 12 months...")
        
        time_series_analysis = self._create_analysis_from_data(monthly_data)

        # Convert all string fields in the Pydantic model to ASCII before saving
        ascii_time_series_analysis = convert_model_to_ascii(time_series_analysis)
        
        with open(output_path, "w", encoding="utf-8") as f:
            # Use ascii_ensure=False for dump, as we've already converted
            json.dump(ascii_time_series_analysis.model_dump(), f, indent=2, ensure_ascii=False)
            
        return time_series_analysis
        
    def generate_time_series_commentary(self, time_series_analysis: TimeSeriesAnalysis, output_path: str) -> str:
        """
        Generates a high-level summary commentary based on time series data.
        """
        print("Generating time series commentary...")

        # Create a simplified context for the LLM
        context = (
            f"Time Series Summary: {time_series_analysis.time_series_summary}\n"
            f"Overall Trend: {time_series_analysis.overall_trend}\n"
            f"Most Volatile Category: {time_series_analysis.most_volatile_category}\n"
            f"Emerging Patterns: {', '.join(time_series_analysis.emerging_patterns)}"
        )
        
        system_prompt = """
        You are a Senior Cyber Intelligence Analyst. Your task is to provide a brief, high-level commentary 
        on the provided time series analysis of cybersecurity news. The commentary should be a single, well-written paragraph.

        Focus on the strategic implications of the data. What does the overall trend suggest? 
        What is the significance of the most volatile category? Are there any emerging patterns that 
        the board should be aware of?

        Your audience is the Board of Directors, so the tone should be professional, concise, and non-technical.
        Do not repeat the raw data; instead, provide interpretation and insight.
        """
        
        commentary = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please generate commentary based on this data:\n{context}"}
            ],
            response_model=str,
            max_retries=2,
        )
        
        # Convert the raw string commentary to ASCII
        ascii_commentary = convert_to_ascii(commentary)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ascii_commentary)
            
        return ascii_commentary

    def _create_analysis_from_data(self, monthly_data: Dict[str, Any]) -> TimeSeriesAnalysis:
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
        
        return TimeSeriesAnalysis(
            monthly_trends=monthly_trends,
            overall_trend=calculate_overall_trend(monthly_data),
            most_volatile_category=calculate_most_volatile_category(monthly_data),
            emerging_patterns=identify_emerging_patterns(monthly_data),
            time_series_summary=create_summary_from_data(monthly_data)
        )

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
