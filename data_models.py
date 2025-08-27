# data_models.py
from pydantic import BaseModel, Field
from typing import List

class Article(BaseModel):
    """Represents a single news article with engineered features."""
    title: str = Field(..., description="The headline of the news article.")
    description: str = Field(..., description="A brief summary or snippet of the article.")
    published_date: str | None = Field(None, description="The ISO 8601 publication date of the article.")
    source: str = Field(..., description="The domain name of the news source, e.g., 'reuters.com'.")

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