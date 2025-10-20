#!/usr/bin/env python3
"""Test script for poll ingestion system"""

from src.ingest.poll_ingest import PollIngestor
from src.config.settings import Config

def test_poll_ingestion():
    print("Testing Poll Ingestion System...")
    print("=" * 50)
    
    # Initialize directories
    Config.create_directories()
    
    # Create poll ingestor
    ingestor = PollIngestor()
    
    # Test fetching polls
    print("\n1. Fetching opinion polls...")
    polls_df = ingestor.fetch_opinion_polls()
    
    print(f"   Fetched {len(polls_df)} polls")
    print(f"   Columns: {list(polls_df.columns)}")
    
    # Show sample polls
    print("\n2. Sample polls:")
    for i, row in polls_df.head(3).iterrows():
        print(f"   - {row['source']} ({row['date'].strftime('%Y-%m-%d')})")
        print(f"     NDA: {row['nda_vote']:.1f}%, INDI: {row['indi_vote']:.1f}%, Others: {row['others']:.1f}%")
        print(f"     Sample: {row['sample_size']:,}, MoE: ±{row['moe']:.1f}%")
    
    # Test weighted average calculation
    print("\n3. Calculating weighted averages...")
    weighted_avg = ingestor.calculate_weighted_average(polls_df)
    if weighted_avg:
        print(f"   Weighted NDA: {weighted_avg['nda_vote']:.1f}%")
        print(f"   Weighted INDI: {weighted_avg['indi_vote']:.1f}%")
        print(f"   NDA Lead: {weighted_avg['nda_lead']:+.1f}%")
        print(f"   Based on {weighted_avg['polls_count']} polls")
    
    # Test saving
    print("\n4. Saving poll data...")
    ingestor.save_polls(polls_df)
    
    # Test summary generation
    print("\n5. Generating poll summary...")
    summary = ingestor.generate_poll_summary(polls_df)
    if summary:
        print(f"   Total polls: {summary['total_polls']}")
        print(f"   Date range: {summary['date_range']}")
        print(f"   Sources: {', '.join(summary['sources'])}")
        print(f"   Avg NDA: {summary['avg_nda_vote']:.1f}% (±{summary['nda_vote_std']:.1f}%)")
        print(f"   Avg INDI: {summary['avg_indi_vote']:.1f}% (±{summary['indi_vote_std']:.1f}%)")
    
    print("\n✅ Poll ingestion test completed successfully!")
    return polls_df

if __name__ == "__main__":
    test_poll_ingestion()