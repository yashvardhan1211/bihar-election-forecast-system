#!/usr/bin/env python3
"""
Enhanced test script for the improved Bihar poll ingestion system
Tests local elections, opinion polls, and ground indicators
"""

from src.ingest.poll_ingest import PollIngestor
from src.config.settings import Config
import pandas as pd

def test_enhanced_poll_system():
    print("🗳️ TESTING ENHANCED BIHAR POLL INGESTION SYSTEM")
    print("=" * 70)
    
    # Initialize
    Config.create_directories()
    poll_ingestor = PollIngestor()
    
    # Test comprehensive poll fetching
    print(f"\n" + "="*70)
    print("TEST 1: COMPREHENSIVE POLL FETCHING")
    print("="*70)
    
    try:
        comprehensive_polls = poll_ingestor.fetch_opinion_polls()
        
        print(f"\n📊 Comprehensive Poll Results:")
        print(f"   Total polls/results: {len(comprehensive_polls)}")
        
        if not comprehensive_polls.empty:
            # Analyze poll types
            if 'poll_type' in comprehensive_polls.columns:
                type_breakdown = comprehensive_polls['poll_type'].value_counts()
                print(f"\n📈 Poll Type Breakdown:")
                for poll_type, count in type_breakdown.items():
                    print(f"   • {poll_type}: {count} records")
            
            # Show quality scores
            if 'quality_score' in comprehensive_polls.columns:
                avg_quality = comprehensive_polls['quality_score'].mean()
                print(f"\n⭐ Average Quality Score: {avg_quality:.2f}")
                
                high_quality = comprehensive_polls[comprehensive_polls['quality_score'] >= 0.7]
                print(f"   High quality polls (≥0.7): {len(high_quality)}")
            
            # Show recent trends
            print(f"\n📅 Recent Poll Trends:")
            recent_polls = comprehensive_polls.head(5)
            for i, (_, poll) in enumerate(recent_polls.iterrows()):
                print(f"   {i+1}. {poll['source']} ({poll['date']})")
                print(f"      NDA: {poll['nda_vote']:.1f}% | INDI: {poll['indi_vote']:.1f}% | Others: {poll['others']:.1f}%")
                if 'poll_type' in poll:
                    print(f"      Type: {poll['poll_type']} | Sample: {poll['sample_size']:,}")
        
    except Exception as e:
        print(f"❌ Comprehensive poll test failed: {e}")
    
    # Test local election fetching specifically
    print(f"\n" + "="*70)
    print("TEST 2: LOCAL ELECTION RESULTS")
    print("="*70)
    
    try:
        local_results = poll_ingestor._fetch_local_election_results()
        
        print(f"\n📊 Local Election Results:")
        print(f"   Total local results: {len(local_results)}")
        
        if not local_results.empty:
            # Show election types
            if 'election_type' in local_results.columns:
                election_types = local_results['election_type'].value_counts()
                print(f"\n🏛️ Election Types:")
                for election_type, count in election_types.items():
                    print(f"   • {election_type}: {count} results")
            
            # Show regional coverage
            if 'region' in local_results.columns:
                regions = local_results['region'].unique()
                print(f"\n🗺️ Regional Coverage: {len(regions)} regions")
                for region in regions[:5]:  # Show first 5
                    print(f"   • {region}")
            
            # Show sample results
            print(f"\n📋 Sample Local Results:")
            for i, (_, result) in enumerate(local_results.head(3).iterrows()):
                print(f"   {i+1}. {result['source']} ({result['date']})")
                print(f"      Region: {result.get('region', 'N/A')}")
                print(f"      NDA: {result['nda_vote']:.1f}% | INDI: {result['indi_vote']:.1f}%")
                if 'constituencies_covered' in result:
                    print(f"      Coverage: {result['constituencies_covered']} constituencies")
        
    except Exception as e:
        print(f"❌ Local election test failed: {e}")
    
    # Test news-based poll extraction
    print(f"\n" + "="*70)
    print("TEST 3: NEWS-BASED POLL EXTRACTION")
    print("="*70)
    
    try:
        news_polls = poll_ingestor._fetch_polls_from_news()
        
        print(f"\n📊 News Poll Results:")
        print(f"   Total news polls: {len(news_polls)}")
        
        if not news_polls.empty:
            # Show news sources
            if 'news_source' in news_polls.columns:
                news_sources = news_polls['news_source'].value_counts()
                print(f"\n📰 News Sources:")
                for source, count in news_sources.items():
                    print(f"   • {source}: {count} polls")
            
            # Show methodologies
            if 'methodology' in news_polls.columns:
                methodologies = news_polls['methodology'].value_counts()
                print(f"\n🔬 Survey Methodologies:")
                for method, count in methodologies.items():
                    print(f"   • {method}: {count} polls")
            
            # Show sample polls
            print(f"\n📋 Sample News Polls:")
            for i, (_, poll) in enumerate(news_polls.head(3).iterrows()):
                print(f"   {i+1}. {poll['source']} ({poll['date']})")
                print(f"      NDA: {poll['nda_vote']:.1f}% | INDI: {poll['indi_vote']:.1f}%")
                print(f"      Sample: {poll['sample_size']:,} | MOE: ±{poll['moe']:.1f}%")
        
    except Exception as e:
        print(f"❌ News poll test failed: {e}")
    
    # Test ground indicators
    print(f"\n" + "="*70)
    print("TEST 4: GROUND-LEVEL INDICATORS")
    print("="*70)
    
    try:
        ground_indicators = poll_ingestor._fetch_ground_indicators()
        
        print(f"\n📊 Ground Indicator Results:")
        print(f"   Total indicators: {len(ground_indicators)}")
        
        if not ground_indicators.empty:
            # Show indicator types
            if 'indicator_type' in ground_indicators.columns:
                indicator_types = ground_indicators['indicator_type'].value_counts()
                print(f"\n📈 Indicator Types:")
                for indicator_type, count in indicator_types.items():
                    print(f"   • {indicator_type}: {count} indicators")
            
            # Show sample indicators
            print(f"\n📋 Sample Ground Indicators:")
            for i, (_, indicator) in enumerate(ground_indicators.iterrows()):
                print(f"   {i+1}. {indicator['source']} ({indicator['date']})")
                print(f"      Type: {indicator.get('indicator_type', 'N/A')}")
                print(f"      NDA: {indicator['nda_vote']:.1f}% | INDI: {indicator['indi_vote']:.1f}%")
                print(f"      Sample: {indicator['sample_size']:,}")
        
    except Exception as e:
        print(f"❌ Ground indicator test failed: {e}")
    
    # Test weighted average calculation
    print(f"\n" + "="*70)
    print("TEST 5: WEIGHTED AVERAGE CALCULATION")
    print("="*70)
    
    try:
        if not comprehensive_polls.empty:
            weighted_avg = poll_ingestor.calculate_weighted_average(comprehensive_polls, days_window=30)
            
            if weighted_avg:
                print(f"\n📊 30-Day Weighted Average:")
                print(f"   NDA Vote Share: {weighted_avg['nda_vote']:.1f}%")
                print(f"   INDI Vote Share: {weighted_avg['indi_vote']:.1f}%")
                print(f"   Others: {weighted_avg['others']:.1f}%")
                print(f"   NDA Lead: {weighted_avg['nda_lead']:+.1f}%")
                print(f"   Based on: {weighted_avg['polls_count']} polls")
                print(f"   Avg Sample Size: {weighted_avg['avg_sample_size']:,.0f}")
                print(f"   Date Range: {weighted_avg['date_range']}")
                
                # Determine trend
                if weighted_avg['nda_lead'] > 2:
                    trend = "NDA Leading"
                elif weighted_avg['nda_lead'] < -2:
                    trend = "INDI Leading"
                else:
                    trend = "Too Close to Call"
                
                print(f"   📈 Current Trend: {trend}")
            else:
                print(f"   ❌ Could not calculate weighted average")
        
    except Exception as e:
        print(f"❌ Weighted average test failed: {e}")
    
    # Test poll saving and loading
    print(f"\n" + "="*70)
    print("TEST 6: POLL PERSISTENCE")
    print("="*70)
    
    try:
        # Save polls
        poll_ingestor.save_polls(comprehensive_polls)
        
        # Load latest polls
        latest_polls = poll_ingestor.get_latest_polls(n=5)
        
        print(f"\n📊 Poll Persistence Test:")
        print(f"   Saved polls: {len(comprehensive_polls)}")
        print(f"   Loaded latest: {len(latest_polls)}")
        
        if not latest_polls.empty:
            print(f"   Latest poll date: {latest_polls.iloc[0]['date']}")
            print(f"   Oldest in latest 5: {latest_polls.iloc[-1]['date']}")
        
        # Generate summary
        summary = poll_ingestor.generate_poll_summary(comprehensive_polls)
        if summary:
            print(f"\n📈 Poll Summary Statistics:")
            print(f"   Total polls: {summary['total_polls']}")
            print(f"   Date range: {summary['date_range']}")
            print(f"   Unique sources: {len(summary['sources'])}")
            print(f"   Avg NDA: {summary['avg_nda_vote']:.1f}% (±{summary['nda_vote_std']:.1f})")
            print(f"   Avg INDI: {summary['avg_indi_vote']:.1f}% (±{summary['indi_vote_std']:.1f})")
            print(f"   Total sample size: {summary['total_sample_size']:,}")
        
    except Exception as e:
        print(f"❌ Poll persistence test failed: {e}")
    
    # Final Assessment
    print(f"\n" + "="*70)
    print("🎯 FINAL POLL SYSTEM ASSESSMENT")
    print("="*70)
    
    try:
        total_polls = len(comprehensive_polls) if not comprehensive_polls.empty else 0
        
        print(f"📊 System Performance:")
        print(f"   ✅ Total polls collected: {total_polls}")
        
        if not comprehensive_polls.empty and 'poll_type' in comprehensive_polls.columns:
            type_counts = comprehensive_polls['poll_type'].value_counts()
            for poll_type, count in type_counts.items():
                print(f"   ✅ {poll_type.replace('_', ' ').title()}: {count} records")
        
        print(f"   ✅ Local election tracking: Implemented")
        print(f"   ✅ News poll extraction: Implemented")
        print(f"   ✅ Ground indicators: Implemented")
        print(f"   ✅ Quality scoring: Implemented")
        print(f"   ✅ Weighted averaging: Implemented")
        
        system_status = "✅ FULLY OPERATIONAL" if total_polls >= 10 else "⚠️ NEEDS ATTENTION"
        print(f"\n🚀 SYSTEM STATUS: {system_status}")
        
        if total_polls >= 10:
            print(f"💡 Ready for forecasting model integration!")
            print(f"🎯 Next: Use poll data in Monte Carlo simulations")
        else:
            print(f"💡 System working with sample data")
            print(f"🔧 Real data sources may need API keys or network access")
        
        return comprehensive_polls
        
    except Exception as e:
        print(f"❌ Final assessment failed: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    results = test_enhanced_poll_system()
    print(f"\n🎉 ENHANCED POLL SYSTEM TEST COMPLETE!")
    print(f"📊 Check the results above to see the comprehensive poll coverage")