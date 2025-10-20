#!/usr/bin/env python3
"""Test entity mapping on sentiment-analyzed Bihar election news"""

import pandas as pd
from src.nlp.entity_mapper import EntityMapper
from src.config.settings import Config
import json

def test_entity_mapping():
    print("🗺️ Testing Advanced Entity Mapping on Bihar Election News")
    print("=" * 70)
    
    # Load sentiment-analyzed news data
    print("\n📊 Loading sentiment-analyzed news data...")
    
    try:
        # Load the sentiment-analyzed data
        analyzed_path = Config.PROCESSED_DATA_DIR / "sentiment_analyzed_news_2025-10-17.csv"
        
        if analyzed_path.exists():
            analyzed_df = pd.read_csv(analyzed_path)
            print(f"✅ Loaded {len(analyzed_df)} sentiment-analyzed articles")
        else:
            print("❌ Sentiment-analyzed data not found")
            return
    
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    # Initialize entity mapper
    print("\n🔄 Initializing Advanced Entity Mapping System...")
    entity_mapper = EntityMapper()
    
    # Test individual article mapping
    print("\n🔍 Testing Individual Article Entity Mapping...")
    
    if len(analyzed_df) > 0:
        sample_article = analyzed_df.iloc[0]
        sample_text = sample_article['full_text']
        
        print(f"📄 Sample article: {sample_article['title'][:60]}...")
        
        # Test individual mapping functions
        party = entity_mapper.map_party(sample_text)
        region = entity_mapper.map_region(sample_text)
        constituencies = entity_mapper.map_constituencies(sample_text)
        entities = entity_mapper.extract_political_entities(sample_text)
        
        print(f"📊 Individual Mapping Results:")
        print(f"   • Primary Party: {party}")
        print(f"   • Region: {region}")
        print(f"   • Constituencies: {constituencies[:3]}{'...' if len(constituencies) > 3 else ''}")
        print(f"   • Leaders Mentioned: {entities['leaders']}")
        print(f"   • Parties Mentioned: {entities['parties'][:3]}{'...' if len(entities['parties']) > 3 else ''}")
    
    # Test batch entity mapping
    print(f"\n🔄 Running Batch Entity Mapping on {len(analyzed_df)} Articles...")
    
    enriched_df = entity_mapper.enrich_dataframe(analyzed_df)
    
    # Show detailed results
    print(f"\n📊 DETAILED ENTITY MAPPING RESULTS")
    print("-" * 50)
    
    # Party-wise analysis
    print(f"\n🏛️ Party-wise Coverage Analysis:")
    party_coverage = entity_mapper.analyze_party_coverage(enriched_df)
    
    for party, analysis in party_coverage.items():
        print(f"\n   📊 {party.upper()} Coverage:")
        print(f"      • Articles: {analysis['article_count']} ({analysis['percentage_of_coverage']:.1f}%)")
        if 'average_sentiment' in analysis:
            print(f"      • Avg Sentiment: {analysis['average_sentiment']:.3f}")
        if 'top_leaders' in analysis:
            top_leader = list(analysis['top_leaders'].keys())[0] if analysis['top_leaders'] else 'None'
            print(f"      • Top Leader: {top_leader}")
        if analysis['regions_covered']:
            top_region = max(analysis['regions_covered'], key=analysis['regions_covered'].get)
            print(f"      • Main Region: {top_region}")
    
    # Regional analysis
    print(f"\n🗺️ Regional Coverage Distribution:")
    region_counts = enriched_df['region'].value_counts()
    for region, count in region_counts.head(5).items():
        percentage = (count / len(enriched_df)) * 100
        print(f"   • {region}: {count} articles ({percentage:.1f}%)")
    
    # Constituency analysis
    print(f"\n🎯 Constituency Coverage Analysis:")
    const_type_counts = enriched_df['constituency_type'].value_counts()
    for const_type, count in const_type_counts.items():
        percentage = (count / len(enriched_df)) * 100
        print(f"   • {const_type.title()}: {count} articles ({percentage:.1f}%)")
    
    # Top constituencies mentioned
    all_constituencies = []
    for const_list in enriched_df['constituencies']:
        if isinstance(const_list, str):
            # Handle string representation of list
            const_list = eval(const_list) if const_list.startswith('[') else [const_list]
        if 'statewide' not in const_list:
            all_constituencies.extend(const_list)
    
    if all_constituencies:
        const_counts = pd.Series(all_constituencies).value_counts()
        print(f"\n🏆 Top Mentioned Constituencies:")
        for const, count in const_counts.head(5).items():
            print(f"   • {const}: {count} mentions")
    
    # Leader analysis
    all_leaders = []
    for leaders_list in enriched_df['leaders_mentioned']:
        if isinstance(leaders_list, str):
            # Handle string representation of list
            leaders_list = eval(leaders_list) if leaders_list.startswith('[') else [leaders_list]
        all_leaders.extend(leaders_list)
    
    if all_leaders:
        leader_counts = pd.Series(all_leaders).value_counts()
        print(f"\n👥 Top Mentioned Leaders:")
        for leader, count in leader_counts.head(5).items():
            print(f"   • {leader}: {count} mentions")
    
    # Generate comprehensive summary
    print(f"\n📈 Generating Comprehensive Entity Summary...")
    summary = entity_mapper.get_entity_summary(enriched_df)
    
    if summary:
        print(f"\n📋 COMPREHENSIVE ENTITY SUMMARY")
        print("-" * 50)
        print(f"📊 Total Articles Analyzed: {summary['total_articles']}")
        
        print(f"\n🏛️ Party Coverage Distribution:")
        for party, count in summary['party_distribution'].items():
            percentage = (count / summary['total_articles']) * 100
            print(f"   • {party.upper()}: {count} articles ({percentage:.1f}%)")
        
        print(f"\n🗺️ Regional Coverage Distribution:")
        for region, count in summary['region_distribution'].items():
            percentage = (count / summary['total_articles']) * 100
            print(f"   • {region}: {count} articles ({percentage:.1f}%)")
        
        if 'top_leaders' in summary:
            print(f"\n👥 Most Mentioned Leaders:")
            for leader, count in list(summary['top_leaders'].items())[:5]:
                print(f"   • {leader}: {count} mentions")
        
        if 'top_constituencies' in summary:
            print(f"\n🎯 Most Mentioned Constituencies:")
            for const, count in list(summary['top_constituencies'].items())[:5]:
                print(f"   • {const}: {count} mentions")
        
        # Party-sentiment matrix if available
        if 'party_sentiment_matrix' in summary:
            print(f"\n📊 Party-Sentiment Analysis:")
            for party, sentiments in summary['party_sentiment_matrix'].items():
                if party != 'general':
                    pos = sentiments.get('positive', 0)
                    neg = sentiments.get('negative', 0)
                    neu = sentiments.get('neutral', 0)
                    total = pos + neg + neu
                    if total > 0:
                        print(f"   • {party.upper()}: {pos}+ {neu}= {neg}- (total: {total})")
    
    # Cross-analysis: Sentiment by Party
    print(f"\n🔍 CROSS-ANALYSIS: Sentiment by Party")
    print("-" * 50)
    
    for party in enriched_df['party_mentioned'].unique():
        if party == 'general':
            continue
            
        party_articles = enriched_df[enriched_df['party_mentioned'] == party]
        if len(party_articles) > 0 and 'sentiment_score' in party_articles.columns:
            avg_sentiment = party_articles['sentiment_score'].mean()
            sentiment_dist = party_articles['sentiment_label'].value_counts()
            
            sentiment_emoji = "📈" if avg_sentiment > 0.1 else "📉" if avg_sentiment < -0.1 else "➡️"
            
            print(f"   {sentiment_emoji} {party.upper()}: {avg_sentiment:.3f} avg sentiment")
            print(f"      Distribution: {dict(sentiment_dist)}")
    
    # Save enriched data
    print(f"\n💾 Saving Entity-Enriched Data...")
    
    output_path = Config.PROCESSED_DATA_DIR / "entity_enriched_news_2025-10-17.csv"
    enriched_df.to_csv(output_path, index=False)
    print(f"✅ Saved enriched data to {output_path}")
    
    # Save entity summary
    summary_path = Config.PROCESSED_DATA_DIR / "entity_summary_2025-10-17.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"✅ Saved entity summary to {summary_path}")
    
    # Final assessment
    print(f"\n" + "=" * 70)
    print(f"🎯 ENTITY MAPPING ASSESSMENT")
    print("=" * 70)
    
    if summary:
        # Coverage balance assessment
        party_counts = summary['party_distribution']
        nda_coverage = party_counts.get('NDA', 0)
        indi_coverage = party_counts.get('INDI', 0)
        general_coverage = party_counts.get('general', 0)
        
        total_political = nda_coverage + indi_coverage
        political_percentage = (total_political / summary['total_articles']) * 100
        
        print(f"🏛️ Political Coverage: {political_percentage:.1f}% of articles")
        print(f"📊 NDA Coverage: {nda_coverage} articles")
        print(f"📊 INDI Coverage: {indi_coverage} articles")
        print(f"📊 General/Other: {general_coverage} articles")
        
        # Coverage balance
        if abs(nda_coverage - indi_coverage) <= 5:
            balance_assessment = "BALANCED"
        elif nda_coverage > indi_coverage:
            balance_assessment = "NDA-LEANING"
        else:
            balance_assessment = "INDI-LEANING"
        
        print(f"⚖️ Coverage Balance: {balance_assessment}")
        
        # Regional coverage
        region_counts = summary['region_distribution']
        statewide_pct = (region_counts.get('statewide', 0) / summary['total_articles']) * 100
        
        print(f"🗺️ Statewide Coverage: {statewide_pct:.1f}%")
        print(f"🎯 Regional Focus: {100 - statewide_pct:.1f}%")
        
        # Entity extraction quality
        if 'top_leaders' in summary:
            leader_mentions = sum(summary['top_leaders'].values())
            print(f"👥 Leader Mentions: {leader_mentions} total")
        
        if 'top_constituencies' in summary:
            const_mentions = sum(summary['top_constituencies'].values())
            print(f"🏛️ Constituency Mentions: {const_mentions} total")
        
        print(f"\n💡 Key Insights:")
        print(f"   • {political_percentage:.1f}% of articles have clear political alignment")
        print(f"   • Coverage balance is {balance_assessment.lower()}")
        print(f"   • {statewide_pct:.1f}% focus on statewide issues")
        print(f"   • Entity extraction captured detailed political context")
    
    print(f"\n🚀 SUCCESS: Advanced entity mapping is operational!")
    print(f"💡 Ready for feature engineering and constituency-level analysis!")
    
    return enriched_df, summary

if __name__ == "__main__":
    test_entity_mapping()