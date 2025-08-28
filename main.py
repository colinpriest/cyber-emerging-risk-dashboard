# main.py
import os
from pathlib import Path
from datetime import datetime
import instructor
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import json
from typing import Optional

from news_fetcher import get_news, get_historical_news_summary, categorize_articles_with_llm
from risk_analyzer import RiskAnalyzer
from dashboard_generator import DashboardGenerator
from data_models import (
    CyberRiskAnalysis, BoardActionPlan, ProjectPlan, TimeSeriesAnalysis, 
    MonthlyTrend, EventCategory, ConsolidatedProjectPlan
)
from time_series_analyzer import TimeSeriesAnalyzer

def get_env_var_priority(var_name: str) -> str:
    """
    Get environment variable with priority: .env file first, then environment variables.
    
    Args:
        var_name: The name of the environment variable to retrieve
        
    Returns:
        The value of the environment variable, or None if not found
    """
    # First, try to read from .env file directly
    dotenv_path = find_dotenv()
    if dotenv_path:
        try:
            with open(dotenv_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() == var_name:
                            # Return the value from .env file (prioritized)
                            return value.strip().strip('"').strip("'")
        except (FileNotFoundError, IOError):
            pass
    
    # Fall back to environment variables
    return os.getenv(var_name)

def main() -> None:
    """Main function to run the cyber risk analysis pipeline."""
    
    # --- Initialize data variables ---
    cyber_risk_analysis: Optional[CyberRiskAnalysis] = None
    board_action_plan: Optional[BoardActionPlan] = None
    project_plan: Optional[ConsolidatedProjectPlan] = None
    time_series_analysis: Optional[dict] = None
    time_series_commentary: Optional[str] = None
    
    # --- TEMPORARY: Set to True to regenerate the dashboard from existing data ---
    REGENERATE_DASHBOARD_ONLY = False

    # Load environment variables
    load_dotenv(find_dotenv())
    
    # Setup directories
    output_dir = Path("output")
    news_dir = Path("news")
    output_dir.mkdir(exist_ok=True)
    news_dir.mkdir(exist_ok=True)
    (news_dir / "cache").mkdir(exist_ok=True)
    
    # Get API keys from environment variables
    google_cx = os.getenv("GOOGLE_CUSTOMSEARCH_CX_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    openai_api_key = get_env_var_priority("OPENAI_API_KEY")

    if REGENERATE_DASHBOARD_ONLY:
        print("REGENERATING DASHBOARD FROM EXISTING DATA...")
        
        # Define paths to the latest data files
        try:
            latest_analysis = max(output_dir.glob('CyberRiskAnalysis_*.json'), key=os.path.getctime)
            latest_plan = max(output_dir.glob('BoardActionPlan_*.json'), key=os.path.getctime)
            latest_project_plan = max(output_dir.glob('ProjectPlan_*.json'), key=os.path.getctime)
            latest_time_series = max(output_dir.glob('TimeSeriesAnalysis_*.json'), key=os.path.getctime)
            latest_time_series_commentary = max(output_dir.glob('TimeSeriesCommentary_*.txt'), key=os.path.getctime)
        except ValueError:
            print("\n❌ Error: No data files found in the 'output' directory.")
            print("   Please run the full pipeline at least once by setting REGENERATE_DASHBOARD_ONLY to False.")
            return

        # Load the data
        cyber_risk_analysis = CyberRiskAnalysis.model_validate_json(latest_analysis.read_text())
        board_action_plan = BoardActionPlan.model_validate_json(latest_plan.read_text())
        
        # Load and consolidate all project plan files
        project_plan_files = output_dir.glob('ProjectPlan_*.json')
        all_individual_plans = [ProjectPlan.model_validate_json(f.read_text()) for f in project_plan_files]
        if all_individual_plans:
            project_plan = ConsolidatedProjectPlan(projects=all_individual_plans)
        
        time_series_analysis = json.loads(latest_time_series.read_text())
        time_series_commentary = latest_time_series_commentary.read_text()
        
        print("\nGenerating HTML dashboard...")
        if cyber_risk_analysis and board_action_plan and project_plan and time_series_analysis is not None and time_series_commentary is not None:
            dashboard_generator = DashboardGenerator(
                analysis_data=cyber_risk_analysis,
                board_action_plan=board_action_plan,
                project_plans=project_plan,
                time_series_analysis=time_series_analysis,
                time_series_commentary=time_series_commentary,
                output_dir=output_dir
            )
            dashboard_generator.save_dashboard()
            print(f"\n✅ Dashboard regenerated successfully!")
            print(f"📊 Open {output_dir / 'dashboard.html'} in your web browser to view the interactive dashboard.")
        else:
            print("❌ Error: Not all data was available to regenerate the dashboard.")
        
        return # Exit after regenerating

    # --- FULL PIPELINE ---
    try:
        # Check which API keys are missing and provide detailed error message
        missing_keys = []
        if not google_cx:
            missing_keys.append("GOOGLE_CUSTOMSEARCH_CX_KEY")
        if not google_api_key:
            missing_keys.append("GOOGLE_CUSTOMSEARCH_API_KEY")
        if not openai_api_key:
            missing_keys.append("OPENAI_API_KEY")
        
        if missing_keys:
            error_msg = f"Missing required API keys: {', '.join(missing_keys)}. "
            error_msg += "Please set these in your .env file or environment variables."
            raise ValueError(error_msg)

        # Create and patch OpenAI client with instructor
        client = instructor.patch(OpenAI(api_key=openai_api_key))
    
        print("Fetching and engineering news features...")
        articles = get_news(
            google_cx=google_cx,
            google_api_key=google_api_key,
            save_dir=news_dir,
            months_back=12,
            articles_per_month=100
        )
        
        if not articles:
            print("No articles found. Exiting.")
            return

        # NEW STEP: Categorize articles using the LLM
        print("Categorizing articles with LLM...")
        articles = categorize_articles_with_llm(client, articles)

        # --- NEW FILTERING STEP ---
        # 1. Filter out articles that are not about specific cyber events.
        event_articles = [article for article in articles if article.is_cyber_event]
        print(f"Filtered down to {len(event_articles)} articles about specific cyber events.")

        # 2. Keep the top 50 most relevant articles.
        articles = event_articles[:50]
        print(f"Keeping the top {len(articles)} for analysis.")

        # Save all categorized and filtered articles to a single file with a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        with open(news_dir / f"{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump([article.model_dump() for article in articles], f, indent=2)
        print(f"Saved {len(articles)} articles to news\\{timestamp}.json")

        # Create analyzer instances
        risk_analyzer = RiskAnalyzer(client)
        time_series_analyzer = TimeSeriesAnalyzer(client)
        
        # --- Run Analysis Pipeline ---
        
        # 1. Emerging Risk Analysis
        try:
            print("Analyzing articles for emerging risks...")
            cyber_risk_analysis = risk_analyzer.analyze_emerging_risks(
                articles=articles,
                output_path=output_dir / f"CyberRiskAnalysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            print(f"{datetime.now()} - Risk analysis complete.")
        except Exception as e:
            print(f"Error during risk analysis: {e}")
            return

        # 2. Time Series Analysis
        try:
            print("Analyzing time series trends over 12 months...")
            historical_summary = get_historical_news_summary(articles)
            time_series_analysis = time_series_analyzer.analyze_time_series(
                monthly_data=historical_summary,
                output_path=output_dir / f"TimeSeriesAnalysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            print(f"{datetime.now()} - Time series analysis complete.")

            print("Generating time series commentary...")
            time_series_commentary = time_series_analyzer.generate_time_series_commentary(
                time_series_analysis=time_series_analysis,
                output_path=output_dir / f"TimeSeriesCommentary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            print(f"{datetime.now()} - Time series commentary complete.")
        except Exception as e:
            print(f"Error during time series analysis: {e}")
            return

        # 3. Board Action Plan
        try:
            print("Generating strategic action points...")
            board_action_plan = risk_analyzer.generate_board_action_plan(
                risk_analysis=cyber_risk_analysis,
                output_path=output_dir / f"BoardActionPlan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            print(f"{datetime.now()} - Action points generated.")
        except Exception as e:
            print(f"Error generating board action plan: {e}")
            return

        # 4. Project Plans
        try:
            print("Creating project plans for each action point...")
            if not board_action_plan:
                print("Skipping project plan creation because the board action plan is missing.")
                return

            sorted_actions = sorted(board_action_plan.action_points, key=lambda x: x.priority)
            
            for i, action_point in enumerate(sorted_actions):
                risk_analyzer.create_project_plan(
                    action_point=action_point.description,
                    risk_analysis=cyber_risk_analysis,
                    output_path=output_dir / f"ProjectPlan_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                print(f"{datetime.now()} - Project plan for action {i+1} created.")
            
            print(f"{datetime.now()} - All project plans created.")
        
        except Exception as e:
            print(f"Error creating project plans: {e}")
            return
        
        # 5. Consolidate Project Plans for Dashboard
        all_project_plans = []
        for plan_file in output_dir.glob('ProjectPlan_*.json'):
            all_project_plans.append(ProjectPlan.model_validate_json(plan_file.read_text()))
        
        if all_project_plans:
            project_plan = ConsolidatedProjectPlan(projects=all_project_plans)

        print("\nGenerating HTML dashboard...")
        if cyber_risk_analysis and board_action_plan and project_plan and time_series_analysis is not None and time_series_commentary is not None:
            dashboard_generator = DashboardGenerator(
                analysis_data=cyber_risk_analysis,
                board_action_plan=board_action_plan,
                project_plans=project_plan,
                time_series_analysis=time_series_analysis,
                time_series_commentary=time_series_commentary,
                output_dir=output_dir
            )
            dashboard_generator.save_dashboard()
        else:
            print("❌ Error: Not all data was available to generate the dashboard.")

    except Exception as e:
        print(f"\nAn unexpected error occurred during the main pipeline: {e}")
        return

    print(f"\nPipeline finished successfully. Check the 'output' directory for results.")
    print(f"📊 Open {output_dir / 'dashboard.html'} in your web browser to view the interactive dashboard.")

if __name__ == "__main__":
    main()