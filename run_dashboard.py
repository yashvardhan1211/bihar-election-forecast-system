#!/usr/bin/env python3
"""
Enhanced Bihar Election Forecast Dashboard Launcher
Run this script to start the interactive dashboard on localhost
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("🏛️ LAUNCHING BIHAR ELECTION FORECAST 2025 DASHBOARD")
    print("=" * 60)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit found")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "plotly"])
        print("✅ Streamlit installed")
    
    # Create necessary directories
    directories = ['data/features', 'data/historical', 'models', 'data/results']
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")
    
    # Dashboard path
    dashboard_path = "src/dashboard/enhanced_dashboard.py"
    
    if not Path(dashboard_path).exists():
        print(f"❌ Dashboard file not found: {dashboard_path}")
        return
    
    print("🚀 Starting Bihar Election Forecast Dashboard...")
    print("📊 Professional analytics dashboard will open in your browser")
    print("🌐 URL: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Launch streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            dashboard_path,
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

if __name__ == "__main__":
    main()