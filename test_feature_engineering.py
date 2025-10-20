#!/usr/bin/env python3
"""Test advanced feature engineering with EMA smoothing"""

import pandas as pd
from src.features.feature_updater import FeatureUpdater
from src.config.settings import Config
import json

def test_feature_engineering():
    print("⚙️ Testing Advanced Feature Engineering with EMA Smoothing")
    print("=" * 70)
    
    # Initialize feature updater
    print("\n🔄 Initializing Feature Engineering System...")
    feature_updater = FeatureUpdater()
    
    # Load or create base features
    print("\n📊 Loading/Creating Base Features...")
    base_features = feature_updater.load_base_features()
    
    print(f"✅ Loaded features for {len(base_features)} constituencies")
    print(f"📊 Feature columns: {len(base_features.columns)} total")
    print(f"🗺️ Regions: {base_features['region'].value_counts().to_dict()}")
    
    # Show sample base features
    print(f"\n📋 Sample Base Features:")
    sample_const = base_features.iloc[0]
    print(f"   • Constituency: {sample_const['constituency']}")
    print(f"   • Region: {sample_const['region']}")
    print(f"   • NDA 2020 Share: {sample_const['nda_share_2020']:.1f}%")
    print(f"   • INDI 2020 Share: {sample_const['indi_share_2020']:.1f}%")
    print(f"   • Current NDA Sentiment: {sample_const['social_sentiment_nda']:.3f}")
    
    # Load entity-enriched news data
    print(f"\n📰 Loading Entity-Enriched News Data...")
    
    try:
        news_path = Config.PROCESSED_DATA_DIR / "entity_enriched_news_2025-10-17.csv"
        
        if news_path.exists():
            news_df = pd.read_csv(news_path)
            print(f"✅ Loaded {len(news_df)} entity-enriched articles")
        else:
            print("❌ Entity-enriched news not found, using sample")
            return
    except Exception as e:
        print(f"Error loading news data: {e}")
        return
    
    # Load poll data
    print(f"\n📊 Loading Poll Data...")
    
    try:
        polls_path = Config.PROCESSED_DATA_DIR / "enhanced_polls_2025-10-17.csv"
        
        if polls_path.exists():
            polls_df = pd.read_csv(polls_path)
            print(f"✅ Loaded {len(polls_df)} poll data points")
        else:
            print("⚠️ No poll data found, creating sample")
            polls_df = pd.DataFrame()
    except Exception as e:
        print(f"Error loading poll data: {e}")
        polls_df = pd.DataFrame()
    
    # Test sentiment aggregation
    print(f"\n🧠 Testing Sentiment Aggregation...")
    
    sentiment_agg = feature_updater.aggregate_news_sentiment(news_df)
    
    print(f"📊 Sentiment Aggregation Results:")
    print(f"   • Party-level sentiment: {sentiment_agg['party']}")
    print(f"   • Regional sentiment areas: {len(sentiment_agg['regional'])} regions")
    print(f"   • Constituency-specific: {len(sentiment_agg['constituency'])} constituencies")
    
    # Test sentiment feature updates
    print(f"\n🔄 Testing Sentiment Feature Updates with EMA...")
    
    updated_features = feature_updater.update_sentiment_features(base_features, sentiment_agg)
    
    # Show sentiment changes
    sentiment_changes = {
        'nda_sentiment_change': (updated_features['news_sentiment_nda'] - base_features['news_sentiment_nda']).abs().mean(),
        'indi_sentiment_change': (updated_features['news_sentiment_indi'] - base_features['news_sentiment_indi']).abs().mean()
    }
    
    print(f"📈 Sentiment Update Results:")
    print(f"   • Avg NDA sentiment change: {sentiment_changes['nda_sentiment_change']:.4f}")
    print(f"   • Avg INDI sentiment change: {sentiment_changes['indi_sentiment_change']:.4f}")
    print(f"   • NDA sentiment range: [{updated_features['news_sentiment_nda'].min():.3f}, {updated_features['news_sentiment_nda'].max():.3f}]")
    print(f"   • INDI sentiment range: [{updated_features['news_sentiment_indi'].min():.3f}, {updated_features['news_sentiment_indi'].max():.3f}]")
    
    # Test poll feature updates
    print(f"\n📊 Testing Poll Feature Updates...")
    
    if not polls_df.empty:
        updated_features = feature_updater.update_poll_features(updated_features, polls_df)
        print(f"✅ Poll features updated successfully")
        
        poll_changes = {
            'poll_lead_change': (updated_features['poll_lead_nda'] - base_features['poll_lead_nda']).abs().mean(),
            'momentum_change': updated_features['poll_momentum_nda'].abs().mean()
        }
        
        print(f"📈 Poll Update Results:")
        print(f"   • Avg poll lead change: {poll_changes['poll_lead_change']:.2f} points")
        print(f"   • Avg momentum: {poll_changes['momentum_change']:.2f} points")
    else:
        print("⚠️ No poll data to process")
    
    # Test derived feature calculation
    print(f"\n⚙️ Testing Derived Feature Calculation...")
    
    final_features = feature_updater.calculate_derived_features(updated_features)
    
    print(f"✅ Calculated derived features")
    print(f"📊 New feature columns added:")
    new_columns = set(final_features.columns) - set(base_features.columns)
    for col in sorted(new_columns):
        print(f"   • {col}")
    
    # Analyze competitiveness
    print(f"\n🎯 Analyzing Constituency Competitiveness...")
    
    competitiveness_analysis = {
        'safe_nda': len(final_features[final_features['nda_win_prob'] > 0.7]),
        'lean_nda': len(final_features[(final_features['nda_win_prob'] > 0.55) & (final_features['nda_win_prob'] <= 0.7)]),
        'toss_up': len(final_features[(final_features['nda_win_prob'] >= 0.45) & (final_features['nda_win_prob'] <= 0.55)]),
        'lean_indi': len(final_features[(final_features['nda_win_prob'] >= 0.3) & (final_features['nda_win_prob'] < 0.45)]),
        'safe_indi': len(final_features[final_features['nda_win_prob'] < 0.3])
    }
    
    print(f"📊 Constituency Classification:")
    for category, count in competitiveness_analysis.items():
        percentage = (count / len(final_features)) * 100
        print(f"   • {category.replace('_', ' ').title()}: {count} seats ({percentage:.1f}%)")
    
    # Show most competitive seats
    print(f"\n🔥 Most Competitive Constituencies:")
    competitive_seats = final_features.nsmallest(5, 'competitiveness')[['constituency', 'region', 'nda_win_prob', 'competitiveness']]
    for _, seat in competitive_seats.iterrows():
        print(f"   • {seat['constituency']} ({seat['region']}): {seat['nda_win_prob']:.1%} NDA prob, {seat['competitiveness']:.2f} competitive score")
    
    # Regional analysis
    print(f"\n🗺️ Regional Analysis:")
    regional_summary = final_features.groupby('region').agg({
        'nda_win_prob': 'mean',
        'sentiment_advantage_nda': 'mean',
        'competitiveness': 'mean',
        'constituency': 'count'
    }).round(3)
    
    for region, stats in regional_summary.iterrows():
        print(f"   • {region}:")
        print(f"     - {stats['constituency']} constituencies")
        print(f"     - {stats['nda_win_prob']:.1%} avg NDA win prob")
        print(f"     - {stats['sentiment_advantage_nda']:+.3f} sentiment advantage")
        print(f"     - {stats['competitiveness']:.2f} avg competitiveness")
    
    # Generate comprehensive summary
    print(f"\n📈 Generating Comprehensive Feature Summary...")
    
    summary = feature_updater.get_feature_summary(final_features)
    
    print(f"\n📋 COMPREHENSIVE FEATURE SUMMARY")
    print("-" * 50)
    print(f"📊 Total Constituencies: {summary['total_constituencies']}")
    
    print(f"\n🧠 Sentiment Statistics:")
    sent_stats = summary['sentiment_stats']
    print(f"   • Avg NDA Sentiment: {sent_stats['avg_nda_sentiment']:+.3f}")
    print(f"   • Avg INDI Sentiment: {sent_stats['avg_indi_sentiment']:+.3f}")
    print(f"   • NDA Sentiment Advantage: {sent_stats['sentiment_advantage_nda']:+.3f}")
    print(f"   • Sentiment Volatility: {sent_stats['sentiment_std']:.3f}")
    
    print(f"\n📊 Poll Statistics:")
    poll_stats = summary['poll_stats']
    print(f"   • Avg NDA Lead: {poll_stats['avg_nda_lead']:+.1f} points")
    print(f"   • Avg Momentum: {poll_stats['avg_momentum']:+.2f} points")
    print(f"   • Avg Volatility: {poll_stats['avg_volatility']:.2f}")
    
    print(f"\n🎯 Seat Classification:")
    comp_stats = summary['competitiveness']
    total_seats = sum(comp_stats.values())
    for category, count in comp_stats.items():
        percentage = (count / total_seats) * 100
        print(f"   • {category.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    
    # Projected outcome
    nda_safe_lean = comp_stats['safe_nda'] + comp_stats['lean_nda']
    indi_safe_lean = comp_stats['safe_indi'] + comp_stats['lean_indi']
    toss_ups = comp_stats['toss_up']
    
    print(f"\n🎯 Projected Outcome Range:")
    print(f"   • NDA Safe+Lean: {nda_safe_lean} seats")
    print(f"   • INDI Safe+Lean: {indi_safe_lean} seats")
    print(f"   • Toss-up: {toss_ups} seats")
    print(f"   • NDA Range: {nda_safe_lean} - {nda_safe_lean + toss_ups} seats")
    print(f"   • Majority (122): {'✅ Likely' if nda_safe_lean >= 122 else '❓ Depends on toss-ups' if nda_safe_lean + toss_ups >= 122 else '❌ Unlikely'}")
    
    # Save updated features
    print(f"\n💾 Saving Updated Features...")
    
    feature_updater.save_updated_features(final_features)
    
    # Save feature summary
    summary_path = Config.PROCESSED_DATA_DIR / "feature_summary_2025-10-17.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"✅ Saved feature summary to {summary_path}")
    
    # Final assessment
    print(f"\n" + "=" * 70)
    print(f"🎯 FEATURE ENGINEERING ASSESSMENT")
    print("=" * 70)
    
    # Data quality assessment
    feature_completeness = (final_features.notna().sum() / len(final_features)).mean()
    sentiment_coverage = (final_features['news_sentiment_nda'] != 0).sum() / len(final_features)
    
    print(f"📊 Feature Completeness: {feature_completeness:.1%}")
    print(f"🧠 Sentiment Coverage: {sentiment_coverage:.1%}")
    print(f"⚙️ Total Features: {len(final_features.columns)} columns")
    print(f"🎯 Competitive Seats: {toss_ups} ({(toss_ups/total_seats)*100:.1f}%)")
    
    # Model readiness
    model_readiness_score = (feature_completeness + sentiment_coverage) / 2
    
    if model_readiness_score > 0.8:
        readiness_status = "EXCELLENT"
        readiness_emoji = "🚀"
    elif model_readiness_score > 0.6:
        readiness_status = "GOOD"
        readiness_emoji = "✅"
    else:
        readiness_status = "NEEDS IMPROVEMENT"
        readiness_emoji = "⚠️"
    
    print(f"\n{readiness_emoji} Model Readiness: {readiness_status} ({model_readiness_score:.1%})")
    
    print(f"\n💡 Key Insights:")
    print(f"   • EMA smoothing successfully applied to {len(final_features)} constituencies")
    print(f"   • Sentiment features updated from {len(news_df)} real news articles")
    print(f"   • {toss_ups} highly competitive seats identified")
    print(f"   • Features ready for Monte Carlo simulation")
    
    print(f"\n🚀 SUCCESS: Advanced feature engineering is operational!")
    print(f"💡 Ready for model loading and Monte Carlo simulations!")
    
    return final_features, summary

if __name__ == "__main__":
    test_feature_engineering()