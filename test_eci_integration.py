#!/usr/bin/env python3
"""
Test ECI Integration in Bihar Election Forecast System
"""

import pandas as pd
from datetime import datetime
from src.ingest.eci_ingest import ECIIngestor
from src.pipeline.daily_update import DailyUpdatePipeline


def test_eci_ingestor():
    """Test ECI data ingestion"""
    print("🔄 Testing ECI Data Ingestion...")
    
    try:
        eci = ECIIngestor()
        
        # Test live results fetch
        print("   Testing live results fetch...")
        results_df = eci.fetch_live_results()
        print(f"   ✅ Live results: {len(results_df)} records")
        
        # Test constituency details
        print("   Testing constituency details...")
        party_df = eci.fetch_constituency_details()
        print(f"   ✅ Party data: {len(party_df)} records")
        
        # Test real-time trends
        print("   Testing real-time trends...")
        trends = eci.get_real_time_trends()
        print(f"   ✅ Trends data: {len(trends)} fields")
        
        if trends:
            print(f"   Leading alliance: {trends.get('leading_alliance', 'Unknown')}")
            print(f"   Results declared: {trends.get('results_declared', 0)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ECI ingestion test failed: {e}")
        return False


def test_eci_poll_conversion():
    """Test conversion of ECI data to poll format"""
    print("\n🔄 Testing ECI to Poll Conversion...")
    
    try:
        # Create sample ECI party data
        sample_eci_data = pd.DataFrame([
            {'party': 'BJP', 'seats_won': 50, 'seats_leading': 25, 'total_seats': 75},
            {'party': 'JDU', 'seats_won': 30, 'seats_leading': 15, 'total_seats': 45},
            {'party': 'RJD', 'seats_won': 40, 'seats_leading': 20, 'total_seats': 60},
            {'party': 'Congress', 'seats_won': 20, 'seats_leading': 10, 'total_seats': 30},
            {'party': 'Others', 'seats_won': 15, 'seats_leading': 18, 'total_seats': 33}
        ])
        
        # Test conversion
        pipeline = DailyUpdatePipeline()
        poll_data = pipeline._convert_eci_to_poll_format(sample_eci_data)
        
        if not poll_data.empty:
            print(f"   ✅ Conversion successful:")
            print(f"   NDA: {poll_data.iloc[0]['nda_percent']:.1f}%")
            print(f"   INDI: {poll_data.iloc[0]['indi_percent']:.1f}%")
            print(f"   Others: {poll_data.iloc[0]['others_percent']:.1f}%")
            return True
        else:
            print("   ❌ Conversion failed - empty result")
            return False
            
    except Exception as e:
        print(f"   ❌ ECI conversion test failed: {e}")
        return False


def test_pipeline_eci_integration():
    """Test ECI integration in full pipeline"""
    print("\n🔄 Testing Pipeline ECI Integration...")
    
    try:
        pipeline = DailyUpdatePipeline()
        
        # Test data ingestion step with ECI
        print("   Testing data ingestion with ECI...")
        ingestion_results = pipeline._run_data_ingestion()
        
        eci_available = ingestion_results.get('eci_data_available', False)
        eci_results = ingestion_results.get('eci_live_results', 0)
        eci_party = ingestion_results.get('eci_party_data', 0)
        
        print(f"   ✅ ECI data available: {eci_available}")
        print(f"   ✅ ECI live results: {eci_results}")
        print(f"   ✅ ECI party data: {eci_party}")
        
        # Check if ECI data is in raw_data
        raw_data = ingestion_results.get('raw_data', {})
        has_eci_results = 'eci_results_df' in raw_data and not raw_data['eci_results_df'].empty
        has_eci_party = 'eci_party_df' in raw_data and not raw_data['eci_party_df'].empty
        has_eci_trends = 'eci_trends' in raw_data and raw_data['eci_trends']
        
        print(f"   ECI results in pipeline: {has_eci_results}")
        print(f"   ECI party data in pipeline: {has_eci_party}")
        print(f"   ECI trends in pipeline: {has_eci_trends}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Pipeline ECI integration test failed: {e}")
        return False


def test_eci_data_quality():
    """Test ECI data quality and validation"""
    print("\n🔄 Testing ECI Data Quality...")
    
    try:
        eci = ECIIngestor()
        
        # Test data parsing
        sample_html = """
        <table>
            <tr><th>Constituency</th><th>Candidate</th><th>Party</th><th>Votes</th><th>Margin</th><th>Status</th></tr>
            <tr><td>Patna Sahib</td><td>John Doe</td><td>BJP</td><td>50,000</td><td>5,000</td><td>Won</td></tr>
            <tr><td>Bankipore</td><td>Jane Smith</td><td>RJD</td><td>45,000</td><td>2,000</td><td>Won</td></tr>
        </table>
        """
        
        # Test HTML parsing
        results_df = eci._parse_eci_results(sample_html.encode())
        
        if not results_df.empty:
            print(f"   ✅ Parsed {len(results_df)} sample results")
            print(f"   Columns: {list(results_df.columns)}")
            
            # Validate data types
            required_columns = ['constituency', 'candidate_name', 'party', 'votes_received']
            missing_columns = [col for col in required_columns if col not in results_df.columns]
            
            if not missing_columns:
                print("   ✅ All required columns present")
                return True
            else:
                print(f"   ❌ Missing columns: {missing_columns}")
                return False
        else:
            print("   ❌ No data parsed from sample HTML")
            return False
            
    except Exception as e:
        print(f"   ❌ ECI data quality test failed: {e}")
        return False


def main():
    """Run all ECI integration tests"""
    print("=" * 70)
    print("🗳️ BIHAR ELECTION FORECAST - ECI INTEGRATION TESTS")
    print("=" * 70)
    
    tests = [
        ("ECI Ingestor", test_eci_ingestor),
        ("ECI Poll Conversion", test_eci_poll_conversion),
        ("Pipeline Integration", test_pipeline_eci_integration),
        ("Data Quality", test_eci_data_quality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("🎉 All ECI integration tests passed!")
        print("\n📋 ECI Integration Features:")
        print("   ✅ Live election results ingestion")
        print("   ✅ Party performance data integration")
        print("   ✅ Real-time trends calculation")
        print("   ✅ ECI to poll format conversion")
        print("   ✅ Pipeline integration")
        print("   ✅ Data quality validation")
        
        print("\n🚀 Ready for production ECI data integration!")
    else:
        print(f"⚠️ {total - passed} tests failed - check implementation")
    
    return passed == total


if __name__ == "__main__":
    main()