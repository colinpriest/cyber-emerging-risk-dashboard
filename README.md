# Cyber Emerging Risk Detector

An AI-powered system that analyzes recent cybersecurity news to identify emerging risks and generate strategic action plans for organizations.

## Features

- **News Analysis**: Fetches and analyzes recent cybersecurity news articles
- **Risk Identification**: Identifies emerging cyber risks with impact and likelihood scoring
- **Strategic Planning**: Generates prioritized action points for board-level decision making
- **Project Planning**: Creates detailed project plans for each action point
- **Interactive Dashboard**: Visual HTML dashboard with charts and comprehensive analysis display

## Outputs

The system generates several outputs:

1. **JSON Analysis Files**:
   - `1_risk_analysis.json` - Identified emerging risks and board summary
   - `2_board_action_plan.json` - Prioritized strategic action points
   - `3_project_plan_*.json` - Detailed project plans for each action

2. **HTML Dashboard** (`dashboard.html`):
   - Interactive risk matrix visualization
   - Comprehensive risk analysis display
   - Strategic action points overview
   - Detailed project plans
   - Responsive design for all devices

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API Keys** (create a `.env` file):
   ```
   GOOGLE_CUSTOMSEARCH_CX_KEY=your_google_cx_key
   GOOGLE_CUSTOMSEARCH_API_KEY=your_google_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

3. **Run the Analysis**:
   ```bash
   python main.py
   ```

4. **View Results**:
   - Check the `output/` directory for JSON files
   - Open `output/dashboard.html` in your web browser for the interactive dashboard

## Dashboard Features

The HTML dashboard provides:

- **Risk Matrix Chart**: Interactive scatter plot showing impact vs likelihood of identified risks
- **Board Summary**: High-level executive summary
- **Emerging Risks**: Detailed breakdown of each identified risk with scores
- **Action Points**: Prioritized strategic recommendations with ownership
- **Project Plans**: Comprehensive project details including stakeholders, timeline, KPIs, and risks
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## API Requirements

- **Google Custom Search API**: For fetching recent cybersecurity news
- **OpenAI API**: For AI-powered analysis and content generation

## Project Structure

```
cyber-emerging-risk-detector/
├── main.py                 # Main execution script
├── news_fetcher.py         # News article fetching and processing
├── risk_analyzer.py        # AI-powered risk analysis
├── dashboard_generator.py  # HTML dashboard generation
├── data_models.py          # Pydantic data models
├── requirements.txt        # Python dependencies
├── test_dashboard.py       # Dashboard testing utility
├── news/                   # Cached news articles
└── output/                 # Generated analysis files and dashboard
```

## Testing

Test the dashboard generation:
```bash
python test_dashboard.py
```

## Requirements

- Python 3.8+
- OpenAI API access
- Google Custom Search API access
- Internet connection for news fetching and AI analysis
