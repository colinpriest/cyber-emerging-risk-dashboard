# data_models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class CyberEventCategory(str, Enum):
    """A taxonomy of cyber event types for classification."""
    RANSOMWARE = "Ransomware"
    DATA_BREACH = "Data Breach"
    PHISHING = "Phishing"
    VULNERABILITY_EXPLOIT = "Vulnerability Exploit"
    STATE_SPONSORED_ATTACK = "State-Sponsored Attack"
    SUPPLY_CHAIN_ATTACK = "Supply Chain Attack"
    MALWARE = "Malware"
    INSIDER_THREAT = "Insider Threat"
    DENIAL_OF_SERVICE = "Denial of Service"
    OTHER = "Other"

class Article(BaseModel):
    """Represents a single news article with engineered features."""
    title: str = Field(..., description="The headline of the news article.")
    description: str = Field(..., description="A brief summary or snippet of the article.")
    published_date: Optional[str] = Field(None, description="The ISO 8601 publication date of the article.")
    source: str = Field(..., description="The domain name of the news source, e.g., 'reuters.com'.")
    category: Optional[CyberEventCategory] = Field(None, description="The cyber event category classified by the LLM.")
    is_cyber_event: Optional[bool] = Field(None, description="Flag indicating if the article is about a specific cyber attack event.")

class EmergingRisk(BaseModel):
    """Data model for a single identified emerging cyber risk."""
    risk_title: str = Field(..., description="A concise, descriptive title for the emerging risk.")
    description: str = Field(..., description="A detailed explanation of the risk, its nature, and potential targets.")
    impact_score: int = Field(..., ge=1, le=10, description="A score from 1-10 indicating the potential business impact.")
    likelihood_score: int = Field(..., ge=1, le=10, description="A score from 1-10 indicating the likelihood of this risk materializing.")

class CyberRiskAnalysis(BaseModel):
    """Top-level model for the complete cyber risk analysis report."""
    emerging_risks: List[EmergingRisk] = Field(..., description="A list of the top 3-5 notable emerging cyber risks.")
    board_summary: str = Field(..., description="A high-level summary for the Board of Directors, synthesizing the identified risks and their strategic implications.")

class ActionPoint(BaseModel):
    """A single, prioritized, and actionable recommendation for the Board."""
    priority: int = Field(..., description="The priority of the action, where 1 is the highest.")
    description: str = Field(..., description="A clear, single-sentence action item for the Board to consider.")
    suggested_owner: str = Field(..., description="The suggested role or department to own this action, e.g., 'CISO', 'Head of Compliance'.")

class BoardActionPlan(BaseModel):
    """A collection of prioritized action points for the Board."""
    action_points: List[ActionPoint]

class ProjectPlan(BaseModel):
    """A structured, high-level project plan to address an action point."""
    title: str = Field(..., description="The title of the project, derived from the action point.")
    objective: str = Field(..., description="A clear statement of what the project aims to achieve.")
    stakeholders: List[str] = Field(..., description="Key roles or departments involved in the project.")
    timeline_phases: List[str] = Field(..., description="High-level phases of the project, e.g., 'Phase 1: Discovery', 'Phase 2: Vendor Evaluation'.")
    kpis: List[str] = Field(..., description="Key Performance Indicators to measure the project's success.")
    risks: List[str] = Field(..., description="Potential risks or obstacles that could hinder the project.")

class ConsolidatedProjectPlan(BaseModel):
    """A collection of all generated project plans."""
    projects: List[ProjectPlan]

# New models for time series analysis
class EventCategory(BaseModel):
    """Represents a category of cyber events with count and trend information."""
    category: str = Field(..., description="The name of the event category (e.g., 'Ransomware', 'Data Breach', 'Phishing')")
    count: int = Field(..., description="Number of events in this category for the month")
    trend: str = Field(..., description="Trend direction: 'increasing', 'decreasing', 'stable'")
    percentage_change: float = Field(..., description="Percentage change from previous month")

class MonthlyTrend(BaseModel):
    """Represents cyber event trends for a specific month."""
    month: str = Field(..., description="Month in YYYY-MM format")
    total_events: int = Field(..., description="Total number of cyber events for the month")
    categories: List[EventCategory] = Field(..., description="Breakdown of events by category")
    top_threat: str = Field(..., description="The most prominent threat type for the month")
    key_insight: str = Field(..., description="Key insight about the month's cyber landscape")

class TimeSeriesAnalysis(BaseModel):
    """Complete time series analysis of cyber events over 12 months."""
    monthly_trends: List[MonthlyTrend] = Field(..., description="Monthly breakdown of cyber events")
    overall_trend: str = Field(..., description="Overall trend direction across the 12-month period")
    most_volatile_category: str = Field(..., description="Category with the most variation over time")
    emerging_patterns: List[str] = Field(..., description="List of emerging patterns identified in the time series")
    time_series_summary: str = Field(..., description="Comprehensive summary of the 12-month time series analysis")