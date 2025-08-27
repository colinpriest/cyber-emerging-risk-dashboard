# main.py
import os
from pathlib import Path
from datetime import datetime
import instructor
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

from news_fetcher import get_news
from risk_analyzer import analyze_emerging_risks, generate_action_points, create_project_plan
from time_series_analyzer import analyze_time_series, generate_time_series_commentary
from dashboard_generator import DashboardGenerator

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
    
    # Setup directories
    news_dir = Path("news")
    output_dir = Path("output")
    news_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Check for API keys with .env priority
    google_cx = get_env_var_priority("GOOGLE_CUSTOMSEARCH_CX_KEY")
    google_api_key = get_env_var_priority("GOOGLE_CUSTOMSEARCH_API_KEY")
    openai_api_key = get_env_var_priority("OPENAI_API_KEY")

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
        articles_per_month=10
    )
    if not articles:
        print("No articles found. Exiting.")
        return

    print(f"Found {len(articles)} articles. Analyzing for emerging risks...")
    risk_analysis = analyze_emerging_risks(client, articles)
    with open(output_dir / "1_risk_analysis.json", "w") as f:
        f.write(risk_analysis.model_dump_json(indent=2))
    print(f"{datetime.now()} - Risk analysis complete.")

    print("Analyzing time series trends over 12 months...")
    time_series_analysis = analyze_time_series(client, articles)
    with open(output_dir / "2_time_series_analysis.json", "w") as f:
        f.write(time_series_analysis.model_dump_json(indent=2))
    print(f"{datetime.now()} - Time series analysis complete.")

    print("Generating time series commentary...")
    time_series_commentary = generate_time_series_commentary(client, time_series_analysis)
    with open(output_dir / "3_time_series_commentary.txt", "w") as f:
        f.write(time_series_commentary)
    print(f"{datetime.now()} - Time series commentary complete.")

    print("Generating strategic action points...")
    action_plan = generate_action_points(client, risk_analysis)
    with open(output_dir / "4_board_action_plan.json", "w") as f:
        f.write(action_plan.model_dump_json(indent=2))
    print(f"{datetime.now()} - Action points generated.")

    print("Creating project plans for each action point...")
    # Sort action points by priority
    sorted_actions = sorted(action_plan.action_points, key=lambda x: x.priority)
    for i, action in enumerate(sorted_actions):
        project_plan = create_project_plan(client, action)
        with open(output_dir / f"5_project_plan_{i+1}.json", "w") as f:
            f.write(project_plan.model_dump_json(indent=2))
        print(f"{datetime.now()} - Project plan for action {action.priority} created.")

    print("\nGenerating HTML dashboard...")
    dashboard_generator = DashboardGenerator(output_dir)
    dashboard_path = dashboard_generator.save_dashboard()
    print(f"{datetime.now()} - HTML dashboard created: {dashboard_path}")

    print("\nPipeline finished successfully. Check the 'output' directory for results.")
    print(f"📊 Open {dashboard_path} in your web browser to view the interactive dashboard.")

if __name__ == "__main__":
    main()