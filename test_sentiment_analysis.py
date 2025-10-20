#!/usr/bin/env python3
"""Test sentiment analysis on real Bihar election news"""

import pandas as pd
from src.nlp.sentiment_engine import SentimentEngine
from src.config.settings import Config
import json

def test_sentiment_analysis():
    print("🧠 Testing Sentiment Analysis on Real Bihar Election News")
    print("=" * 70)
    
    # Load real news data
    print("\n📰 Loading real Bihar election news...")
    
    try:
        # Load the real NewsAPI data we fetched
        news_path = Config.RAW_DATA_DIR / "news_real_newsapi_2025-10-17.json"
        
        if news_path.exists():
            with open(news_path, 'r') as f:
                news_data = json.load(f)
            
            news_df = pd.DataFrame(news_data)
            print(f"✅ Loaded {len(news_df)} real Bihar election articles")
        else:
            print("❌ Real news data not found, creating sample for testing")
            news_df = pd.DataFrame([
                {
                    'title': 'Bihar election: Miffed over seat-sharing, Upendra Kushwaha says nothing is well in NDA',
                    'description': 'RLM chief expresses dissatisfaction over BJP-led NDA seat-sharing formula',
                    'content': 'Bihar Elections 2025: Soon after the BJP-led NDA finalised the seat-sharing formula for the Bihar elections, Rashtriya Lok Morcha chief and Rajya Sabha MP Upendra Kushwaha expressed his displeasure over the alliance dynamics...',
                    'publishedAt': '2025-10-15T03:18:37Z',
                    'source_type': 'newsapi'
                }
            ])
    
    except Exception as e:
        print(f"Error loading news data: {e}")
        return
    
    # Initialize sentiment engine
    print("\n🔄 Initializing Advanced Sentiment Analysis Engine...")
    sentiment_engine = SentimentEngine()
    
    # Test individual article analysis
    print("\n🔍 Testing Individual Article Analysis...")
    
    if len(news_df) > 0:
        sample_article = news_df.iloc[0]
        sample_text = f"{sample_article['title']} {sample_article.get('description', '')} {sample_article.get('content', '')}"
        
        print(f"📄 Sample article: {sample_article['title'][:60]}...")
        
        individual_result = sentiment_engine.analyze_text(sample_text)
        
        print(f"📊 Individual Analysis Results:")
        print(f"   • Sentiment Score: {individual_result['sentiment_score']:.3f}")
        print(f"   • Sentiment Label: {individual_result['sentiment_label']}")
        print(f"   • Confidence: {individual_result['confidence']:.3f}")
        print(f"   • Political Context: {individual_result['political_context']}")
        print(f"   • Political Intensity: {individual_result['political_intensity']:.3f}")
        print(f"   • Analysis Method: {individual_result['method']}")
    
    # Test batch analysis
    print(f"\n🔄 Running Batch Sentiment Analysis on {len(news_df)} Articles...")
    
    analyzed_df = sentiment_engine.analyze_dataframe(news_df)
    
    # Show detailed results
    print(f"\n📊 DETAILED SENTIMENT ANALYSIS RESULTS")
    print("-" * 50)
    
    # Top positive articles
    positive_articles = analyzed_df[analyzed_df['sentiment_label'] == 'positive'].nlargest(3, 'sentiment_score')
    if len(positive_articles) > 0:
        print(f"\n✅ Most Positive Articles:")
        for i, (_, article) in enumerate(positive_articles.iterrows()):
            print(f"   {i+1}. {article['title'][:60]}...")
            print(f"      Score: {article['sentiment_score']:.3f}, Context: {article['political_context']}")
    
    # Top negative articles
    negative_articles = analyzed_df[analyzed_df['sentiment_label'] == 'negative'].nsmallest(3, 'sentiment_score')
    if len(negative_articles) > 0:
        print(f"\n❌ Most Negative Articles:")
        for i, (_, article) in enumerate(negative_articles.iterrows()):
            print(f"   {i+1}. {article['title'][:60]}...")
            print(f"      Score: {article['sentiment_score']:.3f}, Context: {article['political_context']}")
    
    # Generate comprehensive summary
    print(f"\n📈 Generating Comprehensive Sentiment Summary...")
    summary = sentiment_engine.get_sentiment_summary(analyzed_df)
    
    if summary:
        print(f"\n📋 COMPREHENSIVE SENTIMENT SUMMARY")
        print("-" * 50)
        print(f"📊 Total Articles Analyzed: {summary['total_articles']}")
        print(f"📈 Average Sentiment: {summary['average_sentiment']:.3f}")
        print(f"📊 Sentiment Standard Deviation: {summary['sentiment_std']:.3f}")
        print(f"🏛️ Average Political Intensity: {summary['average_political_intensity']:.3f}")
        
        print(f"\n📊 Sentiment Distribution:")
        for sentiment, count in summary['sentiment_distribution'].items():
            percentage = (count / summary['total_articles']) * 100
            print(f"   • {sentiment.capitalize()}: {count} articles ({percentage:.1f}%)")
        
        print(f"\n🏛️ Political Context Distribution:")
        for context, count in summary['political_context_distribution'].items():
            percentage = (count / summary['total_articles']) * 100
            print(f"   • {context.replace('_', ' ').title()}: {count} articles ({percentage:.1f}%)")
        
        print(f"\n🔧 Analysis Methods Used:")
        for method, count in summary['method_distribution'].items():
            percentage = (count / summary['total_articles']) * 100
            print(f"   • {method.capitalize()}: {count} articles ({percentage:.1f}%)")
        
        # Show daily trends if available
        if 'daily_sentiment_trend' in summary and summary['daily_sentiment_trend']:
            print(f"\n📅 Daily Sentiment Trends:")
            for date, sentiment in summary['daily_sentiment_trend'].items():
                print(f"   • {date}: {sentiment:.3f}")
        
        # Show extreme articles
        if 'most_positive_article' in summary:
            print(f"\n🏆 Most Positive Article:")
            print(f"   • {summary['most_positive_article']['title'][:60]}...")
            print(f"   • Score: {summary['most_positive_article']['sentiment_score']:.3f}")
        
        if 'most_negative_article' in summary:
            print(f"\n⚠️ Most Negative Article:")
            print(f"   • {summary['most_negative_article']['title'][:60]}...")
            print(f"   • Score: {summary['most_negative_article']['sentiment_score']:.3f}")
    
    # Save analyzed data
    print(f"\n💾 Saving Analyzed Data...")
    
    output_path = Config.PROCESSED_DATA_DIR / "sentiment_analyzed_news_2025-10-17.csv"
    analyzed_df.to_csv(output_path, index=False)
    print(f"✅ Saved analyzed data to {output_path}")
    
    # Save summary
    summary_path = Config.PROCESSED_DATA_DIR / "sentiment_summary_2025-10-17.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"✅ Saved sentiment summary to {summary_path}")
    
    # Final assessment
    print(f"\n" + "=" * 70)
    print(f"🎯 SENTIMENT ANALYSIS ASSESSMENT")
    print("=" * 70)
    
    if summary:
        avg_sentiment = summary['average_sentiment']
        political_intensity = summary['average_political_intensity']
        
        # Overall sentiment assessment
        if avg_sentiment > 0.1:
            sentiment_assessment = "POSITIVE"
            sentiment_emoji = "📈"
        elif avg_sentiment < -0.1:
            sentiment_assessment = "NEGATIVE"
            sentiment_emoji = "📉"
        else:
            sentiment_assessment = "NEUTRAL"
            sentiment_emoji = "➡️"
        
        # Political intensity assessment
        if political_intensity > 0.1:
            intensity_assessment = "HIGH"
        elif political_intensity > 0.05:
            intensity_assessment = "MEDIUM"
        else:
            intensity_assessment = "LOW"
        
        print(f"{sentiment_emoji} Overall Sentiment: {sentiment_assessment} ({avg_sentiment:.3f})")
        print(f"🏛️ Political Intensity: {intensity_assessment} ({political_intensity:.3f})")
        print(f"📊 Data Quality: {'EXCELLENT' if len(analyzed_df) > 50 else 'GOOD' if len(analyzed_df) > 20 else 'FAIR'}")
        
        print(f"\n💡 Key Insights:")
        positive_pct = summary['sentiment_distribution'].get('positive', 0) / summary['total_articles'] * 100
        negative_pct = summary['sentiment_distribution'].get('negative', 0) / summary['total_articles'] * 100
        
        print(f"   • {positive_pct:.1f}% of articles have positive sentiment")
        print(f"   • {negative_pct:.1f}% of articles have negative sentiment")
        print(f"   • Political content intensity is {intensity_assessment.lower()}")
        
        if avg_sentiment > 0:
            print(f"   • Overall media coverage leans slightly positive")
        elif avg_sentiment < 0:
            print(f"   • Overall media coverage leans slightly negative")
        else:
            print(f"   • Media coverage is balanced/neutral")
    
    print(f"\n🚀 SUCCESS: Advanced sentiment analysis is operational!")
    print(f"💡 Ready for entity mapping and constituency analysis!")
    
    return analyzed_df, summary

if __name__ == "__main__":
    test_sentiment_analysis()