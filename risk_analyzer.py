# risk_analyzer.py
import instructor
from openai import OpenAI
from typing import List
from data_models import Article, CyberRiskAnalysis, BoardActionPlan, ActionPoint, ProjectPlan

def analyze_emerging_risks(client: OpenAI, articles: List[Article]) -> CyberRiskAnalysis:
    """
    Analyzes a list of articles to identify emerging cyber risks using an LLM.

    Returns:
        A CyberRiskAnalysis object containing identified risks and a board summary.
    """
    system_prompt = """
    You are a world-class Senior Cyber Risk Analyst for a major insurance firm.
    Your task is to analyze the provided list of recent news articles to identify novel and emerging cyber risks.
    "Emerging" means new attack vectors, exploitation of new technologies (e.g., AI), significant shifts in ransomware tactics,
    or threats targeting new sectors or regions.
    
    Pay close attention to the `published_date` to identify trends that are new or accelerating in frequency.
    Correlate information across multiple articles to find underlying themes.
    
    Your output must be a structured analysis containing:
    1. A list of the top 3-5 emerging risks, each with a title, detailed description, and scores for impact and likelihood.
    2. A concise, professional summary for the Board of Directors, written in clear, non-technical language.
    
    Do not name specific companies or individuals in your report. Focus on the nature of the risk itself.
    """
    
    return client.chat.completions.create(
        model="gpt-4-turbo",
        response_model=CyberRiskAnalysis,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here are the news articles to analyze:\n{articles}"},
        ],
        max_retries=2,
    )

def generate_action_points(client: OpenAI, analysis: CyberRiskAnalysis) -> BoardActionPlan:
    """
    Generates prioritized, strategic action points based on a cyber risk analysis.

    Returns:
        A BoardActionPlan object containing a list of ActionPoints.
    """
    return client.chat.completions.create(
        model="gpt-4-turbo",
        response_model=BoardActionPlan,
        messages=[
            {
                "role": "system",
                "content": """
                You are a strategic advisor to the Board of Directors. Based on the provided cyber risk analysis,
                your task is to formulate 3 high-level, prioritized, and actionable recommendations.
                Each action point must be a single, complete sentence and assigned a priority and a suggested owner.
                Focus on strategic initiatives, not low-level technical tasks.
                """,
            },
            {"role": "user", "content": f"Here is the risk analysis:\n{analysis.model_dump_json(indent=2)}"},
        ],
        max_retries=2,
    )

def create_project_plan(client: OpenAI, action_point: ActionPoint) -> ProjectPlan:
    """
    Creates a high-level project plan for a given action point.

    Returns:
        A ProjectPlan object.
    """
    return client.chat.completions.create(
        model="gpt-4-turbo",
        response_model=ProjectPlan,
        messages=[
            {
                "role": "system",
                "content": """
                You are a Senior Project Manager. Your task is to expand the given strategic action point
                into a structured, high-level project plan. Fill in all the fields of the project plan
                with plausible, concise, and relevant information. The plan should be a starting point
                for internal discussion.
                """,
            },
            {"role": "user", "content": f"Generate a project plan for this action point:\n{action_point.model_dump_json(indent=2)}"},
        ],
        max_retries=2,
    )