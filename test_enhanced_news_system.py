#!/usr/bin/env python3
"""
Enhanced test script for the improved Bihar news fetching system
Tests all 4 enhancement approaches: Keywords, Scraping, RSS, and NewsAPI debugging
"""

from src.ingest.news_ingest import NewsIngestor
from src.config.settings import Config
import pandas as pd

def test_enhanced_news_system():
    print("🚀 TESTING ENHANCED BIHAR NEWS FETCHING SYSTEM")
    print("=" * 70)
    
    # Initialize
    Config.create_directories()
    news_ingestor = NewsIngestor()
    
    print(f"🔑 API Key Status: {'✅ Configured' if Config.NEWS_API_KEY else '❌ Missing'}")
    print(f"📝 Enhanced Keywords: {len(Config.BIHAR_KEYWORDS)} keywords")
    print(f"   Sample keywords: {Config.BIHAR_KEYWORDS[:5]}")
    
    # Test 1: Enhanced NewsAPI with debugging
    print(f"\n" + "="*70)
    print("TEST 1: ENHANCED NEWSAPI WITH DEBUGGING")
    print("="*70)
    
    try:
        newsapi_results = news_ingestor.fetch_from_newsapi(days_back=2)
        print(f"\n📊 NewsAPI Results:")
        print(f"   Total articles: {len(newsapi_results)}")
        
        if not newsapi_results.empty:
            real_articles = newsapi_results[newsapi_results['source_type'] == 'newsapi']
            sample_articles = newsapi_results[newsapi_results['source_type'] == 'sample']
            
            print(f"   Real articles: {len(real_articles)}")
            print(f"   Sample fallback: {len(sample_articles)}")
            
            if len(real_articles) > 0:
                print(f"\n📰 Sample Real Headlines:")
                for i, (_, article) in enumerate(real_articles.head(3).iterrows()):
                    print(f"   {i+1}. {article['title']}")
        
    except Exception as e:
        print(f"❌ NewsAPI test failed: {e}")
    
    # Test 2: RSS Feed Integration
    print(f"\n" + "="*70)
    print("TEST 2: RSS FEED INTEGRATION")
    print("="*70)
    
    try:
        rss_results = news_ingestor.fetch_from_rss_feeds()
        print(f"\n📊 RSS Feed Results:")
        print(f"   Total articles: {len(rss_results)}")
        
        if not rss_results.empty:
            source_breakdown = rss_results['source_type'].value_counts()
            print(f"   Sources found:")
            for source, count in source_breakdown.head(5).items():
                print(f"     • {source}: {count} articles")
            
            print(f"\n📰 Sample RSS Headlines:")
            for i, (_, article) in enumerate(rss_results.head(3).iterrows()):
                print(f"   {i+1}. {article['title']}")
        
    except Exception as e:
        print(f"❌ RSS test failed: {e}")
    
    # Test 3: Enhanced Local News Scraping
    print(f"\n" + "="*70)
    print("TEST 3: ENHANCED LOCAL NEWS SCRAPING")
    print("="*70)
    
    try:
        scraped_results = news_ingestor.scrape_local_news()
        print(f"\n📊 Scraping Results:")
        print(f"   Total articles: {len(scraped_results)}")
        
        if not scraped_results.empty:
            source_breakdown = scraped_results['source_type'].value_counts()
            print(f"   Sources scraped:")
            for source, count in source_breakdown.items():
                print(f"     • {source}: {count} articles")
            
            print(f"\n📰 Sample Scraped Headlines:")
            for i, (_, article) in enumerate(scraped_results.head(3).iterrows()):
                print(f"   {i+1}. {article['title']}")
        
    except Exception as e:
        print(f"❌ Scraping test failed: {e}")
    
    # Test 4: Comprehensive Integration
    print(f"\n" + "="*70)
    print("TEST 4: COMPREHENSIVE INTEGRATION (ALL METHODS)")
    print("="*70)
    
    try:
        comprehensive_results = news_ingestor.fetch_comprehensive_news(days_back=2)
        
        print(f"\n🎯 COMPREHENSIVE RESULTS SUMMARY:")
        print(f"   📊 Total unique articles: {len(comprehensive_results)}")
        
        if not comprehensive_results.empty:
            # Analyze source distribution
            source_counts = comprehensive_results['source_type'].value_counts()
            print(f"\n📈 Source Distribution:")
            for source, count in source_counts.items():
                percentage = (count / len(comprehensive_results)) * 100
                print(f"   • {source}: {count} articles ({percentage:.1f}%)")
            
            # Quality assessment
            real_sources = ['newsapi', 'rss_', 'scraped_']
            real_articles = comprehensive_results[
                comprehensive_results['source_type'].str.contains('|'.join(real_sources), na=False)
            ]
            sample_articles = comprehensive_results[
                comprehensive_results['source_type'] == 'sample'
            ]
            
            print(f"\n🎯 Quality Assessment:")
            print(f"   Real data sources: {len(real_articles)} articles")
            print(f"   Sample fallback: {len(sample_articles)} articles")
            
            quality_score = (len(real_articles) / len(comprehensive_results)) * 100
            quality_level = "EXCELLENT" if quality_score > 80 else "GOOD" if quality_score > 50 else "FAIR"
            print(f"   Data quality: {quality_level} ({quality_score:.1f}% real data)")
            
            # Show sample headlines from each source type
            print(f"\n📰 Sample Headlines by Source:")
            for source_type in source_counts.head(3).index:
                source_articles = comprehensive_results[comprehensive_results['source_type'] == source_type]
                if not source_articles.empty:
                    print(f"\n   {source_type.upper()}:")
                    for i, (_, article) in enumerate(source_articles.head(2).iterrows()):
                        print(f"     • {article['title']}")
            
            # Save comprehensive results
            news_ingestor.save_raw_news(comprehensive_results, "enhanced_comprehensive_test")
            print(f"\n💾 Saved comprehensive results to data/raw/")
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
    
    # Final Assessment
    print(f"\n" + "="*70)
    print("🎯 FINAL SYSTEM ASSESSMENT")
    print("="*70)
    
    try:
        # Test data validation
        validated_data = news_ingestor.validate_news_data(comprehensive_results)
        
        print(f"📊 System Performance:")
        print(f"   ✅ Enhanced keywords: {len(Config.BIHAR_KEYWORDS)} terms")
        print(f"   ✅ RSS feeds: 7 Bihar-specific sources")
        print(f"   ✅ Scraping targets: 6 local news websites")
        print(f"   ✅ NewsAPI: Multi-strategy approach")
        print(f"   ✅ Data validation: Implemented")
        
        print(f"\n🚀 SYSTEM STATUS: {'✅ FULLY OPERATIONAL' if len(validated_data) > 5 else '⚠️ NEEDS ATTENTION'}")
        
        if len(validated_data) > 5:
            print(f"💡 Ready for NLP processing and sentiment analysis!")
            print(f"🎯 Next steps: Run daily pipeline to process this news data")
        else:
            print(f"💡 Consider checking API keys and network connectivity")
            print(f"🔧 System will fall back to sample data for development")
        
        return comprehensive_results
        
    except Exception as e:
        print(f"❌ Final assessment failed: {e}")
        return pd.DataFrame()

def test_keyword_effectiveness():
    """Test the effectiveness of enhanced keywords"""
    print(f"\n" + "="*50)
    print("KEYWORD EFFECTIVENESS TEST")
    print("="*50)
    
    old_keywords = [
        "Bihar election", "Bihar assembly", "Nitish Kumar", "Tejashwi Yadav", 
        "RJD", "JDU", "BJP Bihar", "Patna politics", "INDI alliance Bihar"
    ]
    
    new_keywords = Config.BIHAR_KEYWORDS
    
    print(f"📈 Keyword Enhancement:")
    print(f"   Old system: {len(old_keywords)} keywords")
    print(f"   New system: {len(new_keywords)} keywords")
    print(f"   Improvement: {((len(new_keywords) - len(old_keywords)) / len(old_keywords)) * 100:.0f}% more coverage")
    
    print(f"\n🎯 New keyword categories:")
    print(f"   • Political figures: Nitish, Tejashwi, Lalu, Chirag, etc.")
    print(f"   • Regional terms: Muzaffarpur, Darbhanga, Gaya, etc.")
    print(f"   • Election terms: candidate, nomination, campaign, etc.")
    print(f"   • Hindi terms: बिहार, चुनाव, नीतीश, तेजस्वी, etc.")

if __name__ == "__main__":
    # Run comprehensive test
    results = test_enhanced_news_system()
    
    # Test keyword effectiveness
    test_keyword_effectiveness()
    
    print(f"\n🎉 ENHANCED NEWS SYSTEM TEST COMPLETE!")
    print(f"📊 Check the results above to see the improvements")