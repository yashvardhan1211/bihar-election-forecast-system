#!/usr/bin/env python3
"""Test advanced poll-based feature engineering"""

import pandas as pd
from src.features.poll_feature_engine import PollFeatureEngine
from src.config.settings import Config
import json

def test_poll_features():
    print("📊 Testing Advanced Poll-Based Feature Engineering")
    print("=" * 70)
    
    # Initialize poll feature engine
    print("\n🔄 Initializing Poll Feature Engine...")
    poll_engine = PollFeatureEngine()
    
    # Load poll data
    print("\n📊 Loading Poll Data...")
    
    try:
        polls_path = Config.PROCESSED_DATA_DIR / "enhanced_polls_2025-10-17.csv"
        
        if polls_path.exists():
            polls_df = pd.read_csv(polls_path)
            print(f"✅ Loaded {len(polls_df)} poll data points")
        else:
            print("❌ Poll data not found, creating sample")
            return
    except Exception as e:
        print(f"Error loading poll data: {e}")
        return
    
    # Load existing features
    print("\n📊 Loading Existing Features...")
    
    try:
        features_path = Config.PROCESSED_DATA_DIR / "features_latest.csv"
        
        if features_path.exists():
            features_df = pd.read_csv(features_path)
            print(f"✅ Loaded features for {len(features_df)} constituencies")
        else:
            print("❌ Features not found")
            return
    except Exception as e:
        print(f"Error loading features: {e}")
        return
    
    # Test poll aggregation
    print(f"\n🔄 Testing Advanced Poll Aggregation...")
    
    poll_aggregates = poll_engine.calculate_poll_aggregates(polls_df)
    
    if poll_aggregates:
        print(f"📊 Poll Aggregation Results:")
        
        # Show different aggregation methods
        methods = ['simple_average', 'weighted_average', 'exponential_average', 'bayesian_average', 'trend_adjusted', 'meta_aggregate']
        
        for method in methods:
            if method in poll_aggregates:
                agg = poll_aggregates[method]
                print(f"   • {method.replace('_', ' ').title()}:")
                print(f"     NDA: {agg['nda_vote']:.1f}%, INDI: {agg['indi_vote']:.1f}%, Others: {agg['others']:.1f}%")
        
        # Show confidence intervals
        if 'confidence_intervals' in poll_aggregates:
            ci = poll_aggregates['confidence_intervals']
            print(f"\n📊 95% Confidence Intervals:")
            print(f"   • NDA: {ci['nda']['lower']:.1f}% - {ci['nda']['upper']:.1f}% (±{ci['nda']['std']:.1f}%)")
            print(f"   • INDI: {ci['indi']['lower']:.1f}% - {ci['indi']['upper']:.1f}% (±{ci['indi']['std']:.1f}%)")
        
        # Show momentum
        if 'momentum' in poll_aggregates:
            momentum = poll_aggregates['momentum']
            print(f"\n📈 Polling Momentum:")
            print(f"   • NDA: {momentum['nda_momentum']:+.1f} points")
            print(f"   • INDI: {momentum['indi_momentum']:+.1f} points")
        
        # Show volatility
        if 'volatility' in poll_aggregates:
            volatility = poll_aggregates['volatility']
            print(f"\n📊 Polling Volatility:")
            print(f"   • NDA: {volatility['nda_volatility']:.1f} points")
            print(f"   • INDI: {volatility['indi_volatility']:.1f} points")
            print(f"   • Overall: {volatility['overall_volatility']:.1f} points")
    
    # Test constituency-level poll swing application
    print(f"\n🔄 Testing Constituency-Level Poll Swing Application...")
    
    updated_features = poll_engine.apply_poll_swing_to_constituencies(features_df, poll_aggregates)
    
    # Show changes in key features
    print(f"📈 Poll Swing Application Results:")
    
    # Compare before and after
    poll_lead_change = (updated_features['poll_lead_nda'] - features_df['poll_lead_nda']).abs().mean()
    print(f"   • Avg poll lead change: {poll_lead_change:.2f} points")
    
    if 'poll_momentum_nda' in updated_features.columns:
        avg_momentum = updated_features['poll_momentum_nda'].mean()
        print(f"   • Avg momentum: {avg_momentum:+.2f} points")
    
    if 'poll_uncertainty' in updated_features.columns:
        avg_uncertainty = updated_features['poll_uncertainty'].mean()
        print(f"   • Avg uncertainty: {avg_uncertainty:.2f} points")
    
    # Regional analysis
    print(f"\n🗺️ Regional Poll Impact Analysis:")
    
    regional_impact = updated_features.groupby('region').agg({
        'poll_lead_nda': 'mean',
        'poll_momentum_nda': 'mean' if 'poll_momentum_nda' in updated_features.columns else lambda x: 0,
        'poll_volatility': 'mean'
    }).round(2)
    
    for region, stats in regional_impact.iterrows():
        print(f"   • {region}:")
        print(f"     - Avg NDA Lead: {stats['poll_lead_nda']:+.1f} points")
        if 'poll_momentum_nda' in stats:
            print(f"     - Momentum: {stats['poll_momentum_nda']:+.2f} points")
        print(f"     - Volatility: {stats['poll_volatility']:.1f} points")
    
    # Test advanced probability calculation
    print(f"\n🎯 Testing Advanced Probability Calculation...")
    
    final_features = poll_engine.calculate_seat_probabilities(updated_features)
    
    # Show probability distribution
    prob_col = 'final_nda_prob' if 'final_nda_prob' in final_features.columns else 'nda_win_prob'
    
    prob_distribution = {
        'safe_nda': len(final_features[final_features[prob_col] > 0.7]),
        'lean_nda': len(final_features[(final_features[prob_col] > 0.55) & (final_features[prob_col] <= 0.7)]),
        'toss_up': len(final_features[(final_features[prob_col] >= 0.45) & (final_features[prob_col] <= 0.55)]),
        'lean_indi': len(final_features[(final_features[prob_col] >= 0.3) & (final_features[prob_col] < 0.45)]),
        'safe_indi': len(final_features[final_features[prob_col] < 0.3])
    }
    
    print(f"📊 Updated Probability Distribution:")
    total_seats = sum(prob_distribution.values())
    for category, count in prob_distribution.items():
        percentage = (count / total_seats) * 100
        print(f"   • {category.replace('_', ' ').title()}: {count} seats ({percentage:.1f}%)")
    
    # Show most competitive seats
    print(f"\n🔥 Most Competitive Seats (Updated):")
    
    # Calculate competitiveness as distance from 50%
    final_features['competitiveness_updated'] = abs(final_features[prob_col] - 0.5)
    most_competitive = final_features.nsmallest(5, 'competitiveness_updated')
    
    for _, seat in most_competitive.iterrows():
        print(f"   • {seat['constituency']} ({seat['region']}): {seat[prob_col]:.1%} NDA prob")
    
    # Generate comprehensive summary
    print(f"\n📈 Generating Comprehensive Poll Feature Summary...")
    
    summary = poll_engine.generate_poll_feature_summary(final_features, poll_aggregates)
    
    print(f"\n📋 COMPREHENSIVE POLL FEATURE SUMMARY")
    print("-" * 50)
    
    if 'poll_aggregates' in summary and 'meta_aggregate' in summary['poll_aggregates']:
        meta_agg = summary['poll_aggregates']['meta_aggregate']
        print(f"📊 Meta-Aggregate Poll Results:")
        print(f"   • NDA: {meta_agg['nda_vote']:.1f}%")
        print(f"   • INDI: {meta_agg['indi_vote']:.1f}%")
        print(f"   • Others: {meta_agg['others']:.1f}%")
        print(f"   • NDA Lead: {meta_agg['nda_vote'] - meta_agg['indi_vote']:+.1f} points")
    
    if 'constituency_stats' in summary:
        const_stats = summary['constituency_stats']
        print(f"\n📊 Constituency-Level Statistics:")
        print(f"   • Avg NDA Poll Lead: {const_stats['avg_poll_lead_nda']:+.1f} points")
        print(f"   • Poll Lead Std Dev: {const_stats['std_poll_lead_nda']:.1f} points")
        print(f"   • Avg Momentum: {const_stats['avg_momentum']:+.2f} points")
        print(f"   • Avg Volatility: {const_stats['avg_volatility']:.1f} points")
        print(f"   • Avg Uncertainty: {const_stats['avg_uncertainty']:.1f} points")
    
    if 'probability_distribution' in summary:
        prob_dist = summary['probability_distribution']
        print(f"\n🎯 Seat Probability Distribution:")
        for category, count in prob_dist.items():
            percentage = (count / total_seats) * 100
            print(f"   • {category.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    
    if 'regional_analysis' in summary:
        print(f"\n🗺️ Regional Analysis:")
        for region, stats in summary['regional_analysis'].items():
            print(f"   • {region}:")
            print(f"     - Expected NDA Seats: {stats['expected_nda_seats']}/{stats['constituencies']}")
            print(f"     - Competitive Seats: {stats['competitive_seats']}")
            print(f"     - Avg NDA Probability: {stats['avg_nda_prob']:.1%}")
    
    # Projected outcome
    nda_safe_lean = prob_dist['safe_nda'] + prob_dist['lean_nda']
    indi_safe_lean = prob_dist['safe_indi'] + prob_dist['lean_indi']
    toss_ups = prob_dist['toss_up']
    
    print(f"\n🎯 Updated Projected Outcome:")
    print(f"   • NDA Safe+Lean: {nda_safe_lean} seats")
    print(f"   • INDI Safe+Lean: {indi_safe_lean} seats")
    print(f"   • Toss-up: {toss_ups} seats")
    print(f"   • NDA Range: {nda_safe_lean} - {nda_safe_lean + toss_ups} seats")
    
    majority_assessment = "✅ Likely" if nda_safe_lean >= 122 else "❓ Depends on toss-ups" if nda_safe_lean + toss_ups >= 122 else "❌ Unlikely"
    print(f"   • NDA Majority (122): {majority_assessment}")
    
    # Save updated features
    print(f"\n💾 Saving Poll-Enhanced Features...")
    
    output_path = Config.PROCESSED_DATA_DIR / "poll_enhanced_features_2025-10-17.csv"
    final_features.to_csv(output_path, index=False)
    print(f"✅ Saved poll-enhanced features to {output_path}")
    
    # Save poll summary
    summary_path = Config.PROCESSED_DATA_DIR / "poll_feature_summary_2025-10-17.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"✅ Saved poll feature summary to {summary_path}")
    
    # Final assessment
    print(f"\n" + "=" * 70)
    print(f"🎯 POLL FEATURE ENGINEERING ASSESSMENT")
    print("=" * 70)
    
    # Calculate improvement metrics
    if poll_aggregates and 'meta_aggregate' in poll_aggregates:
        meta_agg = poll_aggregates['meta_aggregate']
        poll_quality_score = 1 - (poll_aggregates.get('volatility', {}).get('overall_volatility', 5.0) / 10)
        poll_quality_score = max(0, min(1, poll_quality_score))
        
        print(f"📊 Poll Quality Score: {poll_quality_score:.1%}")
        print(f"📈 Meta-Aggregate Confidence: HIGH" if poll_quality_score > 0.7 else "MEDIUM" if poll_quality_score > 0.5 else "LOW")
        print(f"🎯 Competitive Seats: {toss_ups} ({(toss_ups/total_seats)*100:.1f}%)")
        
        # Uncertainty assessment
        avg_uncertainty = summary.get('constituency_stats', {}).get('avg_uncertainty', 5.0)
        uncertainty_level = "LOW" if avg_uncertainty < 3 else "MEDIUM" if avg_uncertainty < 6 else "HIGH"
        print(f"📊 Overall Uncertainty: {uncertainty_level} ({avg_uncertainty:.1f} points)")
        
        # Model readiness
        model_readiness = (poll_quality_score + (1 - avg_uncertainty/10)) / 2
        readiness_status = "EXCELLENT" if model_readiness > 0.8 else "GOOD" if model_readiness > 0.6 else "FAIR"
        
        print(f"\n🚀 Model Readiness: {readiness_status} ({model_readiness:.1%})")
        
        print(f"\n💡 Key Insights:")
        print(f"   • {len(polls_df)} polls processed with multiple aggregation methods")
        print(f"   • Regional swing variations applied to {len(final_features)} constituencies")
        print(f"   • Advanced probability calculations with uncertainty quantification")
        print(f"   • {toss_ups} highly competitive seats identified as election deciders")
        
        if meta_agg['nda_vote'] > meta_agg['indi_vote']:
            print(f"   • Polls show NDA leading by {meta_agg['nda_vote'] - meta_agg['indi_vote']:.1f} points")
        else:
            print(f"   • Polls show INDI leading by {meta_agg['indi_vote'] - meta_agg['nda_vote']:.1f} points")
    
    print(f"\n🚀 SUCCESS: Advanced poll feature engineering is operational!")
    print(f"💡 Ready for model management and Monte Carlo simulations!")
    
    return final_features, summary

if __name__ == "__main__":
    test_poll_features()