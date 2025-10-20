#!/usr/bin/env python3
"""
Official-Style Homepage for Bihar Election Forecast System
Professional government-style interface for election forecasting

© 2025 YV Predicts. Educational and research purposes only.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import the official style dashboard
from src.dashboard.eci_style_app import OfficialStyleDashboard

def main():
    """Launch official-style homepage"""
    dashboard = OfficialStyleDashboard()
    dashboard.render()

if __name__ == "__main__":
    main()