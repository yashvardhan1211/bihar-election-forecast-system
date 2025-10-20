#!/usr/bin/env python3
"""Test script for trends ingestion system"""

from src.ingest.trends_ingest import TrendsIngestor
from src.config.settings import Config

def test_trends_ingestion():
    print("Testing Trends Ingestion System...")
    print("=" * 50)
    
    # Initialize directories
    Config.create_directories()
    
    # Create trends ingestor
    ingestor = TrendsIngestor()
    
    # Test fetching trends
    print("\n1. Fetching keyword trends...")
    keywords = ['Nitish Kumar', 'Tejashwi Yadav', 'Bihar election']
    trends_df = ingestor.fetch_keyword_trends(keywords)
    
    print(f"   Fetched trends for {len(keywords)} keywords over {len(trends_df)} days")
    print(f"   Columns: {list(trends_df.columns)}")
    
    # Show sample trends
    print("\n2. Sample trend data:")
    for keyword in keywords:
        if keyword in trends_df.columns:
            values = trends_df[keyword].values
            print(f"   - {keyword}: {values[-3:]} (last 3 days)")
    
    # Test trend momentum calculation
    print("\n3. Calculating trend momentum...")
    for keyword in keywords:
        if keyword in trends_df.columns:
            momentum = ingestor.calculate_trend_momentum(trends_df, keyword)
            if momentum:
                print(f"   - {keyword}:")
                print(f"     Current: {momentum['current_value']:.1f}, Avg: {momentum['average_value']:.1f}")
                print(f"     Trend: {momentum['trend_direction']} (slope: {momentum['trend_slope']:+.2f})")
                print(f"     Momentum: {momentum['momentum_pct']:+.1f}%")
    
    # Test keyword comparison
    print("\n4. Comparing keywords...")
    comparison = ingestor.get_keyword_comparison(trends_df)
    if comparison:
        print(f"   Most trending: {comparison['most_trending']}")
        for keyword, stats in comparison['keyword_stats'].items():
            print(f"   - {keyword}: Avg={stats['average']:.1f}, Peak={stats['peak']:.1f}, Trend={stats['trend']}")
    
    # Test related queries
    print("\n5. Fetching related queries...")
    for keyword in keywords[:2]:  # Test first 2 keywords
        related = ingestor.fetch_related_queries(keyword)
        if related and 'top_queries' in related:
            print(f"   - {keyword} top queries:")
            for query in related['top_queries'][:3]:
                print(f"     • {query['query']} ({query['value']})")
    
    # Test saving
    print("\n6. Saving trends data...")
    ingestor.save_trends_data(trends_df)
    
    print("\n✅ Trends ingestion test completed successfully!")
    return trends_df

if __name__ == "__main__":
    test_trends_ingestion()