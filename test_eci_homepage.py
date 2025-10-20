#!/usr/bin/env python3
"""
Test script for ECI-style homepage
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_eci_homepage():
    print("🏛️ TESTING ECI-STYLE HOMEPAGE")
    print("=" * 50)
    
    try:
        # Test import
        from src.dashboard.eci_style_app import ECIStyleDashboard
        print("✅ ECI Style Dashboard imported successfully")
        
        # Test initialization
        dashboard = ECIStyleDashboard()
        print("✅ ECI Style Dashboard initialized successfully")
        
        # Test data loading
        summary, marginal_df, const_prob_df, latest_dir = dashboard.load_latest_results()
        print(f"✅ Data loading test completed")
        print(f"   - Summary available: {'Yes' if summary else 'No (using sample data)'}")
        print(f"   - Marginal seats: {len(marginal_df) if marginal_df is not None and not marginal_df.empty else 0} records")
        print(f"   - Constituency data: {len(const_prob_df) if const_prob_df is not None and not const_prob_df.empty else 0} records")
        
        print(f"\n🎯 ECI Homepage Status: ✅ READY")
        print(f"📋 To launch ECI homepage:")
        print(f"   streamlit run eci_homepage.py")
        print(f"   OR")
        print(f"   streamlit run src/dashboard/app.py (select ECI style)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_eci_homepage()
    if success:
        print(f"\n🎉 ECI HOMEPAGE TEST PASSED!")
    else:
        print(f"\n💥 ECI HOMEPAGE TEST FAILED!")