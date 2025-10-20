#!/usr/bin/env python3
"""Test script for news ingestion system"""

from src.ingest.news_ingest import NewsIngestor
from src.config.settings import Config

def test_news_ingestion():
    print("Testing News Ingestion System...")
    print("=" * 50)
    
    # Initialize directories
    Config.create_directories()
    
    # Create news ingestor
    ingestor = NewsIngestor()
    
    # Test fetching news (will use sample data if no API key)
    print("\n1. Fetching news articles...")
    news_df = ingestor.fetch_from_newsapi(days_back=1)
    
    print(f"   Fetched {len(news_df)} articles")
    print(f"   Columns: {list(news_df.columns)}")
    
    # Show sample articles
    print("\n2. Sample articles:")
    for i, row in news_df.head(3).iterrows():
        print(f"   - {row['title'][:60]}...")
        print(f"     Source: {row['source_type']}, Date: {row['publishedAt'][:10]}")
    
    # Test validation
    print("\n3. Validating news data...")
    validated_df = ingestor.validate_news_data(news_df)
    print(f"   Validated {len(validated_df)} articles")
    
    # Test saving
    print("\n4. Saving raw news data...")
    ingestor.save_raw_news(validated_df)
    
    print("\n✅ News ingestion test completed successfully!")
    return validated_df

if __name__ == "__main__":
    test_news_ingestion()