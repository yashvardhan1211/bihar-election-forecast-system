#!/usr/bin/env python3
"""Test script for real data ingestion from ECI and news sources"""

from src.ingest.news_ingest import NewsIngestor
from src.ingest.poll_ingest import PollIngestor
from src.ingest.eci_ingest import ECIIngestor
from src.config.settings import Config

def test_real_data_ingestion():
    print("Testing REAL Data Ingestion System...")
    print("=" * 60)
    
    # Initialize directories
    Config.create_directories()
    
    # Test ECI Data Ingestion
    print("\n🏛️  TESTING ECI DATA INGESTION")
    print("-" * 40)
    
    eci_ingestor = ECIIngestor()
    
    # Test live results
    print("1. Fetching live ECI results...")
    live_results = eci_ingestor.fetch_live_results()
    if not live_results.empty:
        print(f"   ✅ Fetched {len(live_results)} live results")
        print(f"   Sample: {live_results.head(2)['constituency'].tolist()}")
    else:
        print("   ⚠️  No live results available (election may not be active)")
    
    # Test constituency details
    print("\n2. Fetching constituency details...")
    const_details = eci_ingestor.fetch_constituency_details()
    if not const_details.empty:
        print(f"   ✅ Fetched details for {len(const_details)} parties")
        print(f"   Parties: {const_details['party'].tolist()}")
    else:
        print("   ⚠️  No constituency details available")
    
    # Test real-time trends
    print("\n3. Getting real-time trends...")
    trends = eci_ingestor.get_real_time_trends()
    if trends:
        print(f"   ✅ Real-time trends calculated")
        print(f"   Leading alliance: {trends.get('leading_alliance', 'Unknown')}")
        print(f"   Results declared: {trends.get('results_declared', 0)}")
    else:
        print("   ⚠️  No real-time trends available")
    
    # Test Real News Ingestion
    print("\n📰 TESTING REAL NEWS INGESTION")
    print("-" * 40)
    
    news_ingestor = NewsIngestor()
    
    # Test NewsAPI (if key available)
    print("1. Fetching from NewsAPI...")
    newsapi_articles = news_ingestor.fetch_from_newsapi(days_back=1)
    print(f"   Fetched {len(newsapi_articles)} articles from NewsAPI")
    if len(newsapi_articles) > 0:
        real_articles = newsapi_articles[newsapi_articles['source_type'] == 'newsapi']
        sample_articles = newsapi_articles[newsapi_articles['source_type'] == 'sample']
        print(f"   Real articles: {len(real_articles)}, Sample articles: {len(sample_articles)}")
    
    # Test local news scraping
    print("\n2. Scraping local Bihar news websites...")
    local_articles = news_ingestor.scrape_local_news()
    if not local_articles.empty:
        print(f"   ✅ Scraped {len(local_articles)} articles from local sources")
        sources = local_articles['source_type'].unique()
        print(f"   Sources: {sources}")
        
        # Show sample headlines
        print("   Sample headlines:")
        for i, title in enumerate(local_articles['title'].head(3)):
            print(f"     • {title[:80]}...")
    else:
        print("   ⚠️  No local articles scraped")
    
    # Test Real Poll Data
    print("\n📊 TESTING REAL POLL DATA INGESTION")
    print("-" * 40)
    
    poll_ingestor = PollIngestor()
    
    print("1. Fetching real opinion polls...")
    polls_df = poll_ingestor.fetch_opinion_polls()
    
    real_polls = 0
    sample_polls = 0
    
    if not polls_df.empty:
        # Check if we got any real data
        for source in polls_df['source'].unique():
            if 'sample' not in source.lower():
                real_polls += len(polls_df[polls_df['source'] == source])
            else:
                sample_polls += len(polls_df[polls_df['source'] == source])
    
    print(f"   Real polls: {real_polls}, Sample polls: {sample_polls}")
    
    # Test live constituency data
    print("\n2. Fetching live constituency data...")
    live_const_data = poll_ingestor.fetch_live_constituency_data()
    if not live_const_data.empty:
        print(f"   ✅ Fetched live data for {len(live_const_data)} constituencies")
    else:
        print("   ⚠️  No live constituency data available")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 REAL DATA INGESTION SUMMARY")
    print("=" * 60)
    
    total_real_data_points = 0
    
    if not live_results.empty:
        total_real_data_points += len(live_results)
        print(f"✅ ECI Live Results: {len(live_results)} constituencies")
    
    if not const_details.empty:
        total_real_data_points += len(const_details)
        print(f"✅ ECI Party Details: {len(const_details)} parties")
    
    real_news = len(local_articles) if not local_articles.empty else 0
    if real_news > 0:
        total_real_data_points += real_news
        print(f"✅ Real News Articles: {real_news} articles")
    
    if real_polls > 0:
        total_real_data_points += real_polls
        print(f"✅ Real Opinion Polls: {real_polls} polls")
    
    if not live_const_data.empty:
        total_real_data_points += len(live_const_data)
        print(f"✅ Live Constituency Data: {len(live_const_data)} constituencies")
    
    print(f"\n🎯 Total Real Data Points: {total_real_data_points}")
    
    if total_real_data_points > 0:
        print("🚀 SUCCESS: Real data ingestion is working!")
    else:
        print("⚠️  WARNING: Only sample data available. Check API keys and data sources.")
    
    print("\n💡 Next Steps:")
    print("   1. Set up NewsAPI key in .env for real news data")
    print("   2. Monitor ECI website during active election periods")
    print("   3. Enhance scraping for more news sources")
    print("   4. Add more polling agency integrations")
    
    return {
        'eci_results': live_results,
        'eci_details': const_details,
        'news_articles': local_articles,
        'polls': polls_df,
        'live_constituency': live_const_data,
        'total_real_points': total_real_data_points
    }

if __name__ == "__main__":
    test_real_data_ingestion()