# 🚨 Cyber Emerging Risk Detector

An AI-powered system that analyzes recent cybersecurity news to identify emerging risks and generate strategic action plans for organizations. The system provides both structured JSON outputs and an interactive HTML dashboard for comprehensive risk visualization.

## ✨ Features

- **📰 News Analysis**: Fetches and analyzes recent cybersecurity news articles using Google Custom Search API
- **🎯 Risk Identification**: Identifies emerging cyber risks with impact and likelihood scoring (1-10 scale)
- **📋 Strategic Planning**: Generates prioritized action points for board-level decision making
- **📊 Project Planning**: Creates detailed project plans for each action point with stakeholders, timeline, and KPIs
- **🌐 Interactive Dashboard**: Visual HTML dashboard with interactive charts and comprehensive analysis display
- **🔒 Security Focused**: Designed for enterprise cybersecurity risk management

## 📊 Outputs

The system generates comprehensive outputs in multiple formats:

### 1. **JSON Analysis Files**:
- `1_risk_analysis.json` - Identified emerging risks and board summary
- `2_board_action_plan.json` - Prioritized strategic action points
- `3_project_plan_*.json` - Detailed project plans for each action

### 2. **HTML Dashboard** (`dashboard.html`):
- Interactive risk matrix visualization using Chart.js
- Comprehensive risk analysis display with color-coded sections
- Strategic action points overview with priority indicators
- Detailed project plans with stakeholders, timeline, KPIs, and risks
- Responsive design for desktop, tablet, and mobile devices

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API access
- Google Custom Search API access
- Internet connection for news fetching and AI analysis

### 1. **Clone the Repository**
```bash
git clone https://github.com/colinpriest/cyber-emerging-risk-dashboard.git
cd cyber-emerging-risk-dashboard
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Set up API Keys**
Create a `.env` file in the project root:
```env
GOOGLE_CUSTOMSEARCH_CX_KEY=your_google_cx_key
GOOGLE_CUSTOMSEARCH_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 4. **Run the Analysis**
```bash
python main.py
```

### 5. **View Results**
- Check the `output/` directory for JSON files
- Open `output/dashboard.html` in your web browser for the interactive dashboard

## 📈 Dashboard Features

The HTML dashboard provides a comprehensive view of your cyber risk analysis:

### **🎯 Risk Matrix Chart**
- Interactive scatter plot showing impact vs likelihood of identified risks
- Hover tooltips with detailed risk information
- Color-coded risk levels based on combined scores

### **📋 Executive Summary**
- High-level board summary for executive presentations
- Key insights and strategic implications

### **⚠️ Emerging Risks Section**
- Detailed breakdown of each identified risk
- Impact and likelihood scores with visual indicators
- Risk descriptions and potential targets

### **🎯 Action Points**
- Prioritized strategic recommendations
- Ownership assignments for each action
- Priority levels with visual indicators

### **📋 Project Plans**
- Comprehensive project details for implementation
- Stakeholder identification and responsibilities
- Timeline phases and milestones
- Key Performance Indicators (KPIs)
- Potential risks and mitigation strategies

## 🏗️ Project Structure

```
cyber-emerging-risk-dashboard/
├── main.py                 # Main execution script
├── news_fetcher.py         # News article fetching and processing
├── risk_analyzer.py        # AI-powered risk analysis
├── dashboard_generator.py  # HTML dashboard generation
├── data_models.py          # Pydantic data models
├── requirements.txt        # Python dependencies
├── test_dashboard.py       # Dashboard testing utility
├── README.md              # Project documentation
├── .gitignore             # Git ignore rules
├── news/                  # Cached news articles
└── output/                # Generated analysis files and dashboard
    ├── 1_risk_analysis.json
    ├── 2_board_action_plan.json
    ├── 3_project_plan_*.json
    └── dashboard.html
```

## 🔧 Configuration

### API Setup

#### Google Custom Search API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Custom Search API
4. Create credentials (API Key)
5. Set up Custom Search Engine at [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
6. Get your Search Engine ID (cx)

#### OpenAI API
1. Sign up at [OpenAI Platform](https://platform.openai.com/)
2. Generate an API key
3. Add to your `.env` file

### Environment Variables
The system prioritizes `.env` file over system environment variables for better security and ease of use.

## 🧪 Testing

### Test Dashboard Generation
```bash
python test_dashboard.py
```

### Expected Output
```
🔄 Generating dashboard...
✅ Dashboard generated successfully!
📁 Location: output\dashboard.html
📊 File size: 21,935 bytes
🌐 Open output\dashboard.html in your web browser to view the dashboard.
```

## 📋 Requirements

### Python Dependencies
- `openai` - OpenAI API client
- `instructor` - Structured output from LLMs
- `pydantic` - Data validation and settings
- `python-dotenv` - Environment variable management
- `requests` - HTTP library for API calls

### System Requirements
- Python 3.8+
- 4GB RAM minimum
- Internet connection
- Modern web browser (for dashboard viewing)

## 🔒 Security Considerations

- API keys are stored in `.env` file (not committed to Git)
- No sensitive data is logged or stored in plain text
- HTTPS is used for all API communications
- Input validation through Pydantic models

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/your-username/cyber-emerging-risk-dashboard.git
cd cyber-emerging-risk-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues:

1. Check the [Issues](https://github.com/colinpriest/cyber-emerging-risk-dashboard/issues) page
2. Create a new issue with detailed information
3. Include your Python version and error messages

## 🔄 Version History

- **v1.0.0** - Initial release with JSON outputs and HTML dashboard
- Core risk analysis functionality
- Interactive dashboard with Chart.js
- Comprehensive project planning features

## 🙏 Acknowledgments

- OpenAI for providing the GPT-4 API
- Google for Custom Search API
- Chart.js for interactive visualizations
- The cybersecurity community for inspiration

---

**Made with ❤️ for better cybersecurity risk management**
