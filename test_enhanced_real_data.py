#!/usr/bin/env python3
"""Test enhanced real data ingestion system"""

from src.ingest.real_data_sources import RealDataManager
from src.config.settings import Config

def test_enhanced_real_data():
    print("🚀 Testing Enhanced Real Data System")
    print("=" * 60)
    
    # Initialize
    Config.create_directories()
    data_manager = RealDataManager()
    
    # Check data source freshness
    print("\n🔍 CHECKING DATA SOURCE FRESHNESS")
    print("-" * 40)
    
    freshness = data_manager.check_data_freshness()
    print(f"News sources active: {freshness['news_sources_active']}/3")
    print(f"ECI accessible: {'✅' if freshness['eci_accessible'] else '❌'}")
    print(f"Last update: {freshness['last_update'][:19]}")
    
    if freshness['recommendations']:
        print("\n💡 Recommendations:")
        for rec in freshness['recommendations']:
            print(f"   • {rec}")
    
    # Test live news data
    print("\n📰 TESTING ENHANCED NEWS INGESTION")
    print("-" * 40)
    
    news_df = data_manager.get_live_news_data()
    
    if not news_df.empty:
        print(f"✅ Successfully fetched {len(news_df)} news articles")
        
        # Analyze sources
        source_counts = news_df['source_type'].value_counts()
        print("\n📊 News sources breakdown:")
        for source, count in source_counts.items():
            print(f"   • {source}: {count} articles")
        
        # Show sample headlines
        print("\n📋 Sample headlines:")
        for i, title in enumerate(news_df['title'].head(3)):
            print(f"   {i+1}. {title[:70]}...")
    else:
        print("❌ No real news data fetched")
    
    # Test historical election data
    print("\n🏛️ TESTING HISTORICAL ELECTION DATA")
    print("-" * 40)
    
    historical_df = data_manager.get_historical_election_data()
    
    if not historical_df.empty:
        print(f"✅ Loaded historical data for {len(historical_df)} constituencies")
        print("\n📊 Sample historical results:")
        for _, row in historical_df.head(3).iterrows():
            print(f"   • {row['constituency']}: {row['winner_2020']} (margin: {row['margin_2020']:,})")
    else:
        print("❌ No historical data available")
    
    # Test enhanced poll aggregation
    print("\n📊 TESTING ENHANCED POLL AGGREGATION")
    print("-" * 40)
    
    polls_df = data_manager.get_real_poll_aggregation()
    
    if not polls_df.empty:
        print(f"✅ Generated {len(polls_df)} realistic poll data points")
        
        # Calculate trends
        latest_poll = polls_df.iloc[0]
        oldest_poll = polls_df.iloc[-1]
        
        nda_trend = latest_poll['nda_vote'] - oldest_poll['nda_vote']
        indi_trend = latest_poll['indi_vote'] - oldest_poll['indi_vote']
        
        print(f"\n📈 Poll trends (7-day):")
        print(f"   • NDA: {latest_poll['nda_vote']:.1f}% ({nda_trend:+.1f}%)")
        print(f"   • INDI: {latest_poll['indi_vote']:.1f}% ({indi_trend:+.1f}%)")
        print(f"   • Others: {latest_poll['others']:.1f}%")
        
        # Show methodology
        if 'methodology' in polls_df.columns:
            methods = polls_df['methodology'].unique()
            print(f"   • Methodologies: {', '.join(methods)}")
    else:
        print("❌ No poll data generated")
    
    # Save all real data
    print("\n💾 SAVING REAL DATA")
    print("-" * 40)
    
    timestamp = datetime.now().strftime('%Y-%m-%d')
    
    if not news_df.empty:
        news_path = Config.RAW_DATA_DIR / f"real_news_{timestamp}.json"
        news_df.to_json(news_path, orient='records', indent=2)
        print(f"✅ Saved news data: {news_path}")
    
    if not historical_df.empty:
        hist_path = Config.PROCESSED_DATA_DIR / f"historical_results_{timestamp}.csv"
        historical_df.to_csv(hist_path, index=False)
        print(f"✅ Saved historical data: {hist_path}")
    
    if not polls_df.empty:
        polls_path = Config.PROCESSED_DATA_DIR / f"enhanced_polls_{timestamp}.csv"
        polls_df.to_csv(polls_path, index=False)
        print(f"✅ Saved poll data: {polls_path}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 ENHANCED REAL DATA SUMMARY")
    print("=" * 60)
    
    total_data_points = len(news_df) + len(historical_df) + len(polls_df)
    
    print(f"🎯 Total data points collected: {total_data_points}")
    print(f"📰 News articles: {len(news_df)}")
    print(f"🏛️ Historical constituencies: {len(historical_df)}")
    print(f"📊 Poll data points: {len(polls_df)}")
    
    data_quality = "HIGH" if total_data_points > 15 else "MEDIUM" if total_data_points > 5 else "LOW"
    print(f"📈 Data quality: {data_quality}")
    
    if total_data_points > 0:
        print("\n🚀 SUCCESS: Enhanced real data system is operational!")
        print("💡 Ready for NLP processing and sentiment analysis!")
    else:
        print("\n⚠️ WARNING: Limited data available. Check network connectivity.")
    
    return {
        'news_data': news_df,
        'historical_data': historical_df,
        'poll_data': polls_df,
        'freshness_check': freshness,
        'total_points': total_data_points
    }

if __name__ == "__main__":
    from datetime import datetime
    test_enhanced_real_data()