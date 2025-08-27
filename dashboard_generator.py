# dashboard_generator.py
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from data_models import CyberRiskAnalysis, BoardActionPlan, ProjectPlan, TimeSeriesAnalysis
from time_series_analyzer import create_time_series_chart_data

class DashboardGenerator:
    """Generates a visually appealing HTML dashboard from analysis results."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        
    def load_json_data(self, filename: str) -> Dict[str, Any]:
        """Load JSON data from a file."""
        file_path = self.output_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def load_text_data(self, filename: str) -> str:
        """Load text data from a file."""
        file_path = self.output_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def generate_risk_heatmap_data(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert risk data to heatmap format."""
        heatmap_data = []
        for risk in risks:
            heatmap_data.append({
                'x': risk['impact_score'],
                'y': risk['likelihood_score'],
                'value': risk['impact_score'] * risk['likelihood_score'],
                'title': risk['risk_title'],
                'description': risk['description']
            })
        return heatmap_data
    
    def generate_html(self) -> str:
        """Generate the complete HTML dashboard."""
        
        # Load all data
        risk_analysis = self.load_json_data("1_risk_analysis.json")
        time_series_analysis = self.load_json_data("2_time_series_analysis.json")
        time_series_commentary = self.load_text_data("3_time_series_commentary.txt")
        action_plan = self.load_json_data("4_board_action_plan.json")
        
        # Load project plans
        project_plans = []
        i = 1
        while True:
            plan_data = self.load_json_data(f"5_project_plan_{i}.json")
            if not plan_data:
                break
            project_plans.append(plan_data)
            i += 1
        
        # Generate heatmap data
        heatmap_data = self.generate_risk_heatmap_data(risk_analysis.get('emerging_risks', []))
        
        # Generate time series chart data
        time_series_chart_data = None
        if time_series_analysis and time_series_analysis.get('monthly_trends'):
            try:
                time_series_obj = TimeSeriesAnalysis(**time_series_analysis)
                time_series_chart_data = create_time_series_chart_data(time_series_obj)
            except Exception as e:
                print(f"Warning: Could not create time series chart: {e}")
                time_series_chart_data = None
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyber Emerging Risk Analysis Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-matrix@2.0.0/dist/chartjs-chart-matrix.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        
        .card h2 {{
            color: #4a5568;
            margin-bottom: 20px;
            font-size: 1.5rem;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .risk-item {{
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 0 8px 8px 0;
        }}
        
        .risk-title {{
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 8px;
        }}
        
        .risk-description {{
            color: #4a5568;
            line-height: 1.6;
            margin-bottom: 10px;
        }}
        
        .risk-scores {{
            display: flex;
            gap: 15px;
        }}
        
        .score-item {{
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }}
        
        .action-item {{
            background: #f0fff4;
            border-left: 4px solid #48bb78;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 0 8px 8px 0;
        }}
        
        .action-priority {{
            background: #48bb78;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 8px;
        }}
        
        .action-owner {{
            color: #2f855a;
            font-weight: bold;
            font-size: 0.9rem;
            margin-top: 8px;
        }}
        
        .project-item {{
            background: #fffaf0;
            border-left: 4px solid #ed8936;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 0 8px 8px 0;
        }}
        
        .project-title {{
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 8px;
        }}
        
        .project-objective {{
            color: #4a5568;
            line-height: 1.6;
            margin-bottom: 10px;
            font-style: italic;
        }}
        
        .list-section {{
            margin-top: 10px;
        }}
        
        .list-section h4 {{
            color: #2d3748;
            margin-bottom: 5px;
            font-size: 0.9rem;
        }}
        
        .list-section ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .list-section li {{
            background: #f7fafc;
            padding: 5px 10px;
            margin-bottom: 3px;
            border-radius: 4px;
            font-size: 0.85rem;
            color: #4a5568;
        }}
        
        .board-summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
            line-height: 1.8;
            font-size: 1.1rem;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .chart-container h2 {{
            color: #4a5568;
            margin-bottom: 20px;
            text-align: center;
            font-size: 1.5rem;
        }}
        
        .chart-wrapper {{
            position: relative;
            height: 400px;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
        }}
        
        .time-series-commentary {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            line-height: 1.8;
            font-size: 1rem;
            color: #495057;
        }}
        
        .time-series-commentary h3 {{
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }}
        
        .time-series-commentary p {{
            margin-bottom: 15px;
        }}
        
        @media (max-width: 768px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .container {{
                padding: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Cyber Emerging Risk Analysis Dashboard</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="board-summary">
            <h3>📋 Board Summary</h3>
            <p>{risk_analysis.get('board_summary', 'No board summary available.')}</p>
        </div>
        
        <div class="chart-container">
            <h2>🎯 Risk Impact vs Likelihood Matrix</h2>
            <div class="chart-wrapper">
                <canvas id="riskMatrix"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📈 12-Month Cyber Threat Time Series (10 Articles/Month)</h2>
            <div class="chart-wrapper">
                {f'<canvas id="timeSeriesChart"></canvas>' if time_series_chart_data else '<p style="text-align: center; color: #666; font-style: italic;">No time series data available</p>'}
            </div>
        </div>
        
        <div class="card">
            <h2>📊 Time Series Analysis Commentary</h2>
            <div class="time-series-commentary">
                {time_series_commentary.replace(chr(10), '<br>') if time_series_commentary else '<p>No time series commentary available.</p>'}
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h2>⚠️ Emerging Risks</h2>
                {self._generate_risks_html(risk_analysis.get('emerging_risks', []))}
            </div>
            
            <div class="card">
                <h2>🎯 Strategic Action Points</h2>
                {self._generate_actions_html(action_plan.get('action_points', []))}
            </div>
        </div>
        
        <div class="card">
            <h2>📋 Project Plans</h2>
            {self._generate_projects_html(project_plans)}
        </div>
        
        <div class="footer">
            <p>Cyber Emerging Risk Detector • Powered by AI Analysis</p>
        </div>
    </div>
    
    <script>
        // Risk Matrix Chart
        const ctx = document.getElementById('riskMatrix').getContext('2d');
        const heatmapData = {json.dumps(heatmap_data)};
        
        new Chart(ctx, {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: 'Emerging Risks',
                    data: heatmapData.map(item => ({{
                        x: item.x,
                        y: item.y,
                        r: Math.sqrt(item.value) * 2
                    }})),
                    backgroundColor: heatmapData.map(item => {{
                        const intensity = item.value / 100;
                        return `rgba(102, 126, 234, ${{intensity}})`;
                    }}),
                    borderColor: '#667eea',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: 'Impact Score (1-10)'
                        }},
                        min: 0,
                        max: 10,
                        ticks: {{
                            stepSize: 1
                        }}
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: 'Likelihood Score (1-10)'
                        }},
                        min: 0,
                        max: 10,
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }},
                plugins: {{
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const dataIndex = context.dataIndex;
                                const risk = heatmapData[dataIndex];
                                return [
                                    `Risk: ${{risk.title}}`,
                                    `Impact: ${{risk.x}}/10`,
                                    `Likelihood: ${{risk.y}}/10`,
                                    `Risk Score: ${{risk.value}}`
                                ];
                            }}
                        }}
                    }},
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        
        // Time Series Chart
        {f"const timeSeriesData = {json.dumps(time_series_chart_data)};" if time_series_chart_data else "const timeSeriesData = null;"}
        
        if (timeSeriesData) {{
            const timeSeriesCtx = document.getElementById('timeSeriesChart').getContext('2d');
            
            new Chart(timeSeriesCtx, {{
                type: 'line',
                data: timeSeriesData,
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false,
                    }},
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: 'Month'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: 'Number of Articles'
                            }},
                            beginAtZero: true,
                            max: 10
                        }}
                    }},
                    plugins: {{
                        tooltip: {{
                            callbacks: {{
                                title: function(context) {{
                                    return `Month: ${{context[0].label}}`;
                                }},
                                label: function(context) {{
                                    return `${{context.dataset.label}}: ${{context.parsed.y}} events`;
                                }}
                            }}
                        }},
                        legend: {{
                            display: true,
                            position: 'top'
                        }}
                    }}
                }}
            }});
        }}
    </script>
</body>
</html>
"""
        return html_content
    
    def _generate_risks_html(self, risks: List[Dict[str, Any]]) -> str:
        """Generate HTML for risks section."""
        if not risks:
            return "<p>No emerging risks identified.</p>"
        
        html_parts = []
        for risk in risks:
            html_parts.append(f"""
                <div class="risk-item">
                    <div class="risk-title">{risk['risk_title']}</div>
                    <div class="risk-description">{risk['description']}</div>
                    <div class="risk-scores">
                        <span class="score-item">Impact: {risk['impact_score']}/10</span>
                        <span class="score-item">Likelihood: {risk['likelihood_score']}/10</span>
                        <span class="score-item">Risk Score: {risk['impact_score'] * risk['likelihood_score']}</span>
                    </div>
                </div>
            """)
        return ''.join(html_parts)
    
    def _generate_actions_html(self, actions: List[Dict[str, Any]]) -> str:
        """Generate HTML for action points section."""
        if not actions:
            return "<p>No action points generated.</p>"
        
        html_parts = []
        for action in actions:
            html_parts.append(f"""
                <div class="action-item">
                    <div class="action-priority">Priority {action['priority']}</div>
                    <div class="risk-description">{action['description']}</div>
                    <div class="action-owner">Owner: {action['suggested_owner']}</div>
                </div>
            """)
        return ''.join(html_parts)
    
    def _generate_projects_html(self, projects: List[Dict[str, Any]]) -> str:
        """Generate HTML for project plans section."""
        if not projects:
            return "<p>No project plans generated.</p>"
        
        html_parts = []
        for i, project in enumerate(projects, 1):
            html_parts.append(f"""
                <div class="project-item">
                    <div class="project-title">Project {i}: {project['title']}</div>
                    <div class="project-objective">{project['objective']}</div>
                    
                    <div class="list-section">
                        <h4>Stakeholders:</h4>
                        <ul>
                            {''.join(f'<li>{stakeholder}</li>' for stakeholder in project.get('stakeholders', []))}
                        </ul>
                    </div>
                    
                    <div class="list-section">
                        <h4>Timeline Phases:</h4>
                        <ul>
                            {''.join(f'<li>{phase}</li>' for phase in project.get('timeline_phases', []))}
                        </ul>
                    </div>
                    
                    <div class="list-section">
                        <h4>Key Performance Indicators:</h4>
                        <ul>
                            {''.join(f'<li>{kpi}</li>' for kpi in project.get('kpis', []))}
                        </ul>
                    </div>
                    
                    <div class="list-section">
                        <h4>Potential Risks:</h4>
                        <ul>
                            {''.join(f'<li>{risk}</li>' for risk in project.get('risks', []))}
                        </ul>
                    </div>
                </div>
            """)
        return ''.join(html_parts)
    
    def save_dashboard(self, filename: str = "dashboard.html") -> Path:
        """Generate and save the HTML dashboard."""
        html_content = self.generate_html()
        dashboard_path = self.output_dir / filename
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return dashboard_path
