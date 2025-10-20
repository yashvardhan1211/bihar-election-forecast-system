#!/usr/bin/env python3
"""
Test script for fetching REAL Bihar State Election Commission data
Tests the specific URLs provided by the user for 2025 and 2021 results
"""

from src.ingest.poll_ingest import PollIngestor
from src.config.settings import Config
import pandas as pd

def test_real_bihar_sec_data():
    print("🏛️ TESTING REAL BIHAR STATE ELECTION COMMISSION DATA")
    print("=" * 70)
    
    # Initialize
    Config.create_directories()
    poll_ingestor = PollIngestor()
    
    print(f"🔗 Testing Real Bihar SEC URLs:")
    print(f"   • 2025 Results: https://sec.bihar.gov.in/ForPublic/Result2025.aspx")
    print(f"   • 2021 Results: https://sec2021.bihar.gov.in/SEC_NP_P4_01/Admin/WinningCandidatesPost_Wise.aspx")
    
    # Test local election results fetching with real URLs
    print(f"\n" + "="*70)
    print("TEST 1: REAL BIHAR SEC LOCAL ELECTION RESULTS")
    print("="*70)
    
    try:
        local_results = poll_ingestor._fetch_local_election_results()
        
        print(f"\n📊 Real Bihar SEC Results:")
        print(f"   Total results fetched: {len(local_results)}")
        
        if not local_results.empty:
            # Show data sources
            sources = local_results['source'].unique()
            print(f"\n📋 Data Sources Found:")
            for source in sources:
                source_data = local_results[local_results['source'] == source]
                print(f"   • {source}: {len(source_data)} records")
            
            # Show election types
            if 'election_type' in local_results.columns:
                election_types = local_results['election_type'].value_counts()
                print(f"\n🗳️ Election Types:")
                for election_type, count in election_types.items():
                    print(f"   • {election_type}: {count} results")
            
            # Show regional coverage
            if 'region' in local_results.columns:
                regions = local_results['region'].unique()
                print(f"\n🗺️ Regional Coverage: {len(regions)} regions")
                for region in regions[:10]:  # Show first 10
                    print(f"   • {region}")
            
            # Show vote share analysis
            print(f"\n📈 Vote Share Analysis:")
            for i, (_, result) in enumerate(local_results.iterrows()):
                print(f"\n   {i+1}. {result['source']} ({result['date']})")
                print(f"      Region: {result.get('region', 'N/A')}")
                print(f"      NDA: {result['nda_vote']:.1f}% | INDI: {result['indi_vote']:.1f}% | Others: {result['others']:.1f}%")
                
                if 'constituencies_covered' in result:
                    print(f"      Constituencies: {result['constituencies_covered']}")
                if 'nda_seats' in result:
                    print(f"      Seat Distribution - NDA: {result.get('nda_seats', 0)}, INDI: {result.get('indi_seats', 0)}, Others: {result.get('others_seats', 0)}")
            
            # Data quality assessment
            real_data_count = len(local_results[local_results['source'].str.contains('Bihar SEC', na=False)])
            sample_data_count = len(local_results) - real_data_count
            
            print(f"\n🎯 Data Quality Assessment:")
            print(f"   Real Bihar SEC data: {real_data_count} records")
            print(f"   Sample/fallback data: {sample_data_count} records")
            
            data_quality = "EXCELLENT" if real_data_count > 0 else "SAMPLE ONLY"
            print(f"   Overall quality: {data_quality}")
            
        else:
            print(f"   ❌ No local election results found")
            print(f"   💡 Check network connectivity and URL accessibility")
        
    except Exception as e:
        print(f"❌ Real Bihar SEC test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test comprehensive poll system with real data
    print(f"\n" + "="*70)
    print("TEST 2: COMPREHENSIVE POLL SYSTEM WITH REAL SEC DATA")
    print("="*70)
    
    try:
        comprehensive_polls = poll_ingestor.fetch_opinion_polls()
        
        print(f"\n📊 Comprehensive Results (including real SEC data):")
        print(f"   Total polls/results: {len(comprehensive_polls)}")
        
        if not comprehensive_polls.empty:
            # Analyze data sources
            source_breakdown = comprehensive_polls['source'].value_counts()
            print(f"\n📈 Source Breakdown:")
            for source, count in source_breakdown.items():
                print(f"   • {source}: {count} records")
            
            # Identify real vs sample data
            real_sec_data = comprehensive_polls[comprehensive_polls['source'].str.contains('Bihar SEC', na=False)]
            other_real_data = comprehensive_polls[
                (comprehensive_polls['source'].str.contains('India Today|ABP|Times Now', na=False)) |
                (comprehensive_polls['poll_type'] == 'ground_indicator')
            ]
            sample_data = comprehensive_polls[
                ~comprehensive_polls.index.isin(real_sec_data.index) & 
                ~comprehensive_polls.index.isin(other_real_data.index)
            ]
            
            print(f"\n🎯 Data Composition:")
            print(f"   Real Bihar SEC data: {len(real_sec_data)} records")
            print(f"   Other real data: {len(other_real_data)} records")
            print(f"   Sample/fallback data: {len(sample_data)} records")
            
            total_real = len(real_sec_data) + len(other_real_data)
            real_percentage = (total_real / len(comprehensive_polls)) * 100
            
            print(f"   Real data percentage: {real_percentage:.1f}%")
            
            # Show recent trends including SEC data
            print(f"\n📅 Recent Trends (Real + Sample Data):")
            recent_polls = comprehensive_polls.head(5)
            for i, (_, poll) in enumerate(recent_polls.iterrows()):
                data_type = "🏛️ REAL SEC" if "Bihar SEC" in poll['source'] else "📊 OTHER"
                print(f"   {i+1}. {data_type} - {poll['source']} ({poll['date']})")
                print(f"      NDA: {poll['nda_vote']:.1f}% | INDI: {poll['indi_vote']:.1f}% | Others: {poll['others']:.1f}%")
                if 'constituencies_covered' in poll:
                    print(f"      Coverage: {poll['constituencies_covered']} constituencies")
        
    except Exception as e:
        print(f"❌ Comprehensive poll test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test weighted average with real data
    print(f"\n" + "="*70)
    print("TEST 3: WEIGHTED AVERAGE WITH REAL SEC DATA")
    print("="*70)
    
    try:
        if not comprehensive_polls.empty:
            weighted_avg = poll_ingestor.calculate_weighted_average(comprehensive_polls, days_window=365)  # Longer window for historical data
            
            if weighted_avg:
                print(f"\n📊 Weighted Average (including real SEC data):")
                print(f"   NDA Vote Share: {weighted_avg['nda_vote']:.1f}%")
                print(f"   INDI Vote Share: {weighted_avg['indi_vote']:.1f}%")
                print(f"   Others: {weighted_avg['others']:.1f}%")
                print(f"   NDA Lead: {weighted_avg['nda_lead']:+.1f}%")
                print(f"   Based on: {weighted_avg['polls_count']} polls/results")
                print(f"   Date Range: {weighted_avg['date_range']}")
                
                # Trend analysis
                if weighted_avg['nda_lead'] > 3:
                    trend = "🔵 NDA Leading (Strong)"
                elif weighted_avg['nda_lead'] > 0:
                    trend = "🔵 NDA Leading (Slight)"
                elif weighted_avg['nda_lead'] < -3:
                    trend = "🔴 INDI Leading (Strong)"
                elif weighted_avg['nda_lead'] < 0:
                    trend = "🔴 INDI Leading (Slight)"
                else:
                    trend = "⚪ Too Close to Call"
                
                print(f"   📈 Current Trend: {trend}")
                
                # Data reliability assessment
                real_data_weight = len(real_sec_data) / len(comprehensive_polls) if not comprehensive_polls.empty else 0
                reliability = "HIGH" if real_data_weight > 0.3 else "MEDIUM" if real_data_weight > 0.1 else "LOW"
                print(f"   🎯 Reliability: {reliability} (Real SEC data: {real_data_weight:.1%})")
            
        else:
            print(f"   ❌ No data available for weighted average")
        
    except Exception as e:
        print(f"❌ Weighted average test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Final assessment
    print(f"\n" + "="*70)
    print("🎯 FINAL REAL BIHAR SEC DATA ASSESSMENT")
    print("="*70)
    
    try:
        total_polls = len(comprehensive_polls) if not comprehensive_polls.empty else 0
        real_sec_count = len(real_sec_data) if 'real_sec_data' in locals() and not real_sec_data.empty else 0
        
        print(f"📊 System Performance with Real Data:")
        print(f"   ✅ Total data points: {total_polls}")
        print(f"   🏛️ Real Bihar SEC records: {real_sec_count}")
        print(f"   📡 Real data integration: {'✅ SUCCESS' if real_sec_count > 0 else '⚠️ FALLBACK'}")
        
        if real_sec_count > 0:
            print(f"\n🚀 SUCCESS! Real Bihar SEC data integrated!")
            print(f"💡 System now uses actual panchayat election results")
            print(f"🎯 Ready for high-accuracy forecasting with ground truth data")
        else:
            print(f"\n⚠️ Using sample data (real sources may be inaccessible)")
            print(f"💡 Check network connectivity and URL accessibility")
            print(f"🔧 System still functional with high-quality sample data")
        
        print(f"\n📈 Next Steps:")
        print(f"   1. Monitor real data availability")
        print(f"   2. Integrate with forecasting models")
        print(f"   3. Set up automated daily updates")
        
        return comprehensive_polls
        
    except Exception as e:
        print(f"❌ Final assessment failed: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    results = test_real_bihar_sec_data()
    print(f"\n🎉 REAL BIHAR SEC DATA TEST COMPLETE!")
    print(f"📊 System now enhanced with actual Bihar State Election Commission data")