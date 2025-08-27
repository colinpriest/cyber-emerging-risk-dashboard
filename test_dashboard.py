#!/usr/bin/env python3
"""
Test script for the dashboard generator.
"""

from pathlib import Path
from dashboard_generator import DashboardGenerator

def test_dashboard_generation():
    """Test the dashboard generation functionality."""
    
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("❌ Output directory not found. Please run the main analysis first.")
        return False
    
    # Check if required JSON files exist
    required_files = [
        "1_risk_analysis.json",
        "2_board_action_plan.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not (output_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        print("Please run the main analysis first to generate these files.")
        return False
    
    try:
        # Generate dashboard
        print("🔄 Generating dashboard...")
        dashboard_generator = DashboardGenerator(output_dir)
        dashboard_path = dashboard_generator.save_dashboard()
        
        # Check if dashboard was created
        if dashboard_path.exists():
            file_size = dashboard_path.stat().st_size
            print(f"✅ Dashboard generated successfully!")
            print(f"📁 Location: {dashboard_path}")
            print(f"📊 File size: {file_size:,} bytes")
            print(f"🌐 Open {dashboard_path} in your web browser to view the dashboard.")
            return True
        else:
            print("❌ Dashboard file was not created.")
            return False
            
    except Exception as e:
        print(f"❌ Error generating dashboard: {e}")
        return False

if __name__ == "__main__":
    test_dashboard_generation()
