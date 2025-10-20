#!/usr/bin/env python3
"""Test real NewsAPI with actual API key"""

from src.ingest.news_ingest import NewsIngestor
from src.ingest.real_data_sources import RealDataManager
from src.config.settings import Config

def test_real_newsapi():
    print("🔥 Testing REAL NewsAPI with Your API Key")
    print("=" * 60)
    
    # Initialize
    Config.create_directories()
    
    # Test NewsAPI directly
    print(f"\n🔑 API Key configured: {Config.NEWS_API_KEY[:10]}...")
    
    print("\n📰 FETCHING REAL BIHAR NEWS FROM NEWSAPI")
    print("-" * 50)
    
    news_ingestor = NewsIngestor()
    
    # Fetch real news with your API key
    print("Fetching Bihar election news from NewsAPI...")
    real_news_df = news_ingestor.fetch_from_newsapi(days_back=3)  # Last 3 days
    
    if not real_news_df.empty:
        real_articles = real_news_df[real_news_df['source_type'] == 'newsapi']
        sample_articles = real_news_df[real_news_df['source_type'] == 'sample']
        
        print(f"\n✅ SUCCESS! Fetched {len(real_articles)} REAL articles from NewsAPI")
        print(f"📊 Real articles: {len(real_articles)}, Sample fallback: {len(sample_articles)}")
        
        if len(real_articles) > 0:
            print(f"\n📋 Real Bihar News Headlines:")
            for i, (_, article) in enumerate(real_articles.head(5).iterrows()):
                print(f"   {i+1}. {article['title']}")
                print(f"      Source: {article.get('source', {}).get('name', 'Unknown') if isinstance(article.get('source'), dict) else 'NewsAPI'}")
                print(f"      Published: {article['publishedAt'][:10]}")
                print(f"      URL: {article['url'][:60]}...")
                print()
        
        # Save real news data
        print("💾 Saving real news data...")
        news_ingestor.save_raw_news(real_news_df, "real_newsapi_2025-10-17")
        
    else:
        print("❌ No articles fetched - check API key or network")
    
    # Test enhanced data manager with real API
    print("\n🚀 TESTING ENHANCED DATA MANAGER WITH REAL API")
    print("-" * 50)
    
    data_manager = RealDataManager()
    enhanced_news = data_manager.get_live_news_data()
    
    if not enhanced_news.empty:
        print(f"✅ Enhanced system fetched {len(enhanced_news)} total articles")
        
        # Analyze sources
        source_breakdown = enhanced_news['source_type'].value_counts()
        print(f"\n📊 Source breakdown:")
        for source, count in source_breakdown.items():
            print(f"   • {source}: {count} articles")
        
        # Show mix of real vs sample
        newsapi_real = len(enhanced_news[enhanced_news['source_type'] == 'newsapi_real'])
        rss_real = len(enhanced_news[enhanced_news['source_type'] == 'rss_feed'])
        scraped_real = len(enhanced_news[enhanced_news['source_type'].str.contains('scraped', na=False)])
        
        total_real = newsapi_real + rss_real + scraped_real
        
        print(f"\n🎯 Real Data Summary:")
        print(f"   • NewsAPI real articles: {newsapi_real}")
        print(f"   • RSS feed articles: {rss_real}")
        print(f"   • Scraped articles: {scraped_real}")
        print(f"   • Total REAL articles: {total_real}")
        
        data_quality = "EXCELLENT" if total_real > 10 else "GOOD" if total_real > 5 else "FAIR"
        print(f"   • Data quality: {data_quality}")
        
        # Show sample content for analysis
        print(f"\n📝 Sample article content for NLP processing:")
        if len(enhanced_news) > 0:
            sample_article = enhanced_news.iloc[0]
            print(f"   Title: {sample_article['title']}")
            print(f"   Content preview: {sample_article['content'][:200]}...")
            print(f"   Source type: {sample_article['source_type']}")
    
    else:
        print("❌ Enhanced data manager returned no articles")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 REAL NEWSAPI TEST SUMMARY")
    print("=" * 60)
    
    total_articles = len(real_news_df) if not real_news_df.empty else 0
    real_count = len(real_news_df[real_news_df['source_type'] == 'newsapi']) if not real_news_df.empty else 0
    
    print(f"📊 Total articles fetched: {total_articles}")
    print(f"🔥 Real NewsAPI articles: {real_count}")
    print(f"🔑 API key working: {'✅ YES' if real_count > 0 else '❌ NO'}")
    
    if real_count > 0:
        print(f"\n🚀 SUCCESS! Your NewsAPI key is working perfectly!")
        print(f"💡 Ready to process real Bihar election news with NLP!")
        print(f"🎯 Next: Implement sentiment analysis on this real data")
    else:
        print(f"\n⚠️  API key may have issues or no Bihar news available")
        print(f"💡 Check NewsAPI dashboard for usage limits")
    
    return real_news_df

if __name__ == "__main__":
    test_real_newsapi()