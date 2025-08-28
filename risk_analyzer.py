# risk_analyzer.py
import instructor
from openai import OpenAI
from typing import List
from data_models import CyberRiskAnalysis, BoardActionPlan, ProjectPlan, Article
from news_fetcher import convert_to_ascii
import json

def convert_model_to_ascii(model_instance):
    """Recursively convert all string fields in a Pydantic model to ASCII."""
    if model_instance is None:
        return None
    
    model_dict = model_instance.model_dump()
    
    for key, value in model_dict.items():
        if isinstance(value, str):
            model_dict[key] = convert_to_ascii(value)
        elif isinstance(value, list):
            new_list = []
            for item in value:
                if isinstance(item, str):
                    new_list.append(convert_to_ascii(item))
                elif isinstance(item, dict) and all(isinstance(k, str) for k in item.keys()):
                    # It's a dict that might represent a nested model
                    new_item_dict = {}
                    for k, v in item.items():
                        new_item_dict[k] = convert_to_ascii(v) if isinstance(v, str) else v
                    new_list.append(new_item_dict)
                else:
                    new_list.append(item)
            model_dict[key] = new_list
        # Note: No need for a separate check for nested models,
        # as model_dump() already converted them to dicts.

    # Re-create the model from the cleaned dictionary
    return model_instance.__class__(**model_dict)


class RiskAnalyzer:
    def __init__(self, client: OpenAI):
        self.client = client

    def analyze_emerging_risks(self, articles: List[Article], output_path: str) -> CyberRiskAnalysis:
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
        
        print(f"Analyzing {len(articles)} articles for emerging risks...")
        
        risk_analysis: CyberRiskAnalysis = self.client.chat.completions.create(
            model="gpt-4-turbo",
            response_model=CyberRiskAnalysis,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here are the news articles to analyze:\n{articles}"},
            ],
            max_retries=2,
        )
        
        # Convert all string fields to ASCII before saving
        ascii_risk_analysis = convert_model_to_ascii(risk_analysis)
        
        with open(output_path, "w") as f:
            json.dump(ascii_risk_analysis.model_dump(), f, indent=2)
            
        return risk_analysis

    def generate_board_action_plan(self, risk_analysis: CyberRiskAnalysis, output_path: str) -> BoardActionPlan:
        """
        Generates prioritized, strategic action points based on a cyber risk analysis.

        Returns:
            A BoardActionPlan object containing a list of ActionPoints.
        """
        print("Generating strategic action points...")
        
        action_plan: BoardActionPlan = self.client.chat.completions.create(
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
                {"role": "user", "content": f"Here is the risk analysis:\n{risk_analysis.model_dump_json(indent=2)}"},
            ],
            max_retries=2,
        )
        
        # Convert all string fields to ASCII before saving
        ascii_action_plan = convert_model_to_ascii(action_plan)
        
        with open(output_path, "w") as f:
            json.dump(ascii_action_plan.model_dump(), f, indent=2)
        
        return action_plan

    def create_project_plan(self, action_point: str, risk_analysis: CyberRiskAnalysis, output_path: str) -> ProjectPlan:
        """
        Creates a high-level project plan for a given action point.

        Returns:
            A ProjectPlan object.
        """
        project_plan: ProjectPlan = self.client.chat.completions.create(
            model="gpt-4o-mini",
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
                {"role": "user", "content": f"Generate a project plan for this action point:\n{action_point}"},
            ],
            max_retries=2,
        )

        # Convert all string fields to ASCII before saving
        ascii_project_plan = convert_model_to_ascii(project_plan)

        with open(output_path, "w") as f:
            json.dump(ascii_project_plan.model_dump(), f, indent=2)
        
        return project_plan