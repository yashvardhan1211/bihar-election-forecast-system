#!/usr/bin/env python3
"""
Bihar Election Forecast System - Main CLI Entrypoint

A comprehensive election forecasting system with real-time data ingestion,
advanced NLP processing, and Monte Carlo simulations.

© 2025 YV Predicts. Educational and research purposes only.

Usage:
    python main.py init                    # Initialize system (first time setup)
    python main.py update                  # Run daily update once
    python main.py schedule                # Start scheduler for automated updates
    python main.py dashboard               # Launch web dashboard
    python main.py test                    # Run system tests
    python main.py status                  # Show system status
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.config.settings import Config
from src.pipeline.daily_update import DailyUpdatePipeline
from src.pipeline.scheduler import create_default_scheduler


def cmd_init():
    """Initialize the Bihar Forecast System"""
    print("🚀 Initializing Bihar Election Forecast System...")
    print("=" * 60)
    
    # Create directory structure
    print("\n📁 Creating directory structure...")
    Config.create_directories()
    
    print("✅ Directory structure created:")
    print(f"   📂 {Config.RAW_DATA_DIR}")
    print(f"   📂 {Config.PROCESSED_DATA_DIR}")
    print(f"   📂 {Config.MODELS_DIR}")
    print(f"   📂 {Config.RESULTS_DIR}")
    
    # Check for .env file
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print(f"\n⚠️  Environment file not found. Please:")
        print(f"   1. Copy .env.example to .env")
        print(f"   2. Add your API keys (especially NEWS_API_KEY)")
    elif env_file.exists():
        print(f"\n✅ Environment file found")
    
    # Check dependencies
    print(f"\n📦 Checking dependencies...")
    try:
        import pandas
        import numpy
        import sklearn
        import streamlit
        import plotly
        print("✅ Core dependencies installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    # Test basic functionality
    print(f"\n🧪 Testing basic functionality...")
    try:
        from src.ingest.news_ingest import NewsIngestor
        from src.nlp.sentiment_engine import SentimentEngine
        
        # Test news ingestion
        news_ingestor = NewsIngestor()
        sample_news = news_ingestor._generate_sample_news()
        print(f"✅ News ingestion: {len(sample_news)} sample articles")
        
        # Test sentiment analysis
        sentiment_engine = SentimentEngine()
        test_result = sentiment_engine.analyze_text("This is a positive test message")
        print(f"✅ Sentiment analysis: {test_result['sentiment_label']} sentiment detected")
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False
    
    print(f"\n" + "=" * 60)
    print(f"🎉 INITIALIZATION COMPLETE!")
    print(f"=" * 60)
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Configure API keys in .env file")
    print(f"   2. Run first update: python main.py update")
    print(f"   3. View dashboard: python main.py dashboard")
    print(f"   4. Start scheduler: python main.py schedule")
    
    return True


def cmd_update():
    """Run daily update pipeline once"""
    print("🔄 Running Daily Update Pipeline with ECI Integration...")
    print("=" * 60)
    
    try:
        pipeline = DailyUpdatePipeline()
        results = pipeline.run_full_pipeline()
        
        if results['success']:
            print(f"\n✅ Update completed successfully!")
            
            # Show comprehensive results
            if 'simulation' in results['results']:
                sim_results = results['results']['simulation']
                
                # Import party and candidate analysis
                from src.data.bihar_parties import BIHAR_PARTIES, NDA_PARTIES, INDI_PARTIES, OTHER_PARTIES
                from src.data.constituency_candidates import constituency_analyzer
                
                print(f"\n🏛️ DETAILED PARTY-WISE FORECAST:")
                print(f"=" * 60)
                
                # Individual Party Analysis
                mean_nda = sim_results.get('mean_nda_seats', 0)
                mean_indi = 243 - mean_nda
                
                print(f"\n🔵 NDA ALLIANCE ({mean_nda:.1f} seats):")
                nda_seat_share = mean_nda / 243 * 100
                for party in NDA_PARTIES:
                    party_info = BIHAR_PARTIES[party]
                    # Estimate party-wise seats (simplified)
                    if party == 'BJP':
                        party_seats = mean_nda * 0.55  # BJP gets ~55% of NDA seats
                    elif party == 'JDU':
                        party_seats = mean_nda * 0.35  # JDU gets ~35% of NDA seats
                    else:
                        party_seats = mean_nda * 0.05  # Others get ~5% each
                    
                    print(f"   • {party_info['full_name']} ({party}): {party_seats:.0f} seats")
                    print(f"     Leader: {party_info['state_leader']} | Symbol: {party_info['symbol']}")
                
                print(f"\n🔴 INDI ALLIANCE ({mean_indi:.1f} seats):")
                for party in INDI_PARTIES:
                    party_info = BIHAR_PARTIES[party]
                    # Estimate party-wise seats (simplified)
                    if party == 'RJD':
                        party_seats = mean_indi * 0.60  # RJD gets ~60% of INDI seats
                    elif party == 'INC':
                        party_seats = mean_indi * 0.25  # INC gets ~25% of INDI seats
                    else:
                        party_seats = mean_indi * 0.05  # Others get ~5% each
                    
                    print(f"   • {party_info['full_name']} ({party}): {party_seats:.0f} seats")
                    print(f"     Leader: {party_info['state_leader']} | Symbol: {party_info['symbol']}")
                
                print(f"\n⚪ OTHER PARTIES:")
                for party in ['AIMIM', 'BSP', 'LJSP', 'JSP']:
                    if party in BIHAR_PARTIES:
                        party_info = BIHAR_PARTIES[party]
                        print(f"   • {party_info['full_name']} ({party}): 0-2 seats")
                        print(f"     Leader: {party_info['state_leader']} | Symbol: {party_info['symbol']}")
                
                # Constituency-wise Sample Analysis
                print(f"\n🏛️ CONSTITUENCY-WISE CANDIDATE ANALYSIS:")
                print(f"=" * 70)
                
                # Show sample constituencies with detailed candidate matchups
                all_constituencies = list(constituency_analyzer.constituencies.keys())
                sample_constituencies = all_constituencies[:5]  # Show first 5 constituencies
                
                for const_name in sample_constituencies:
                    matchup = constituency_analyzer.get_candidate_matchup(const_name)
                    if matchup:
                        print(f"\n📍 {const_name.upper()} ({matchup['region']})")
                        print(f"   Battle Type: {matchup['battle_type']}")
                        print(f"   Key Contest: {matchup['key_contest']}")
                        
                        print(f"   Candidates:")
                        for i, candidate in enumerate(matchup['candidates'][:3]):  # Top 3 candidates
                            status = "🥇 Expected Winner" if i == 0 else f"🥈 Runner-up #{i}"
                            print(f"   {status}: {candidate['name']} ({candidate['party_code']})")
                            print(f"      Party: {candidate['party_name']}")
                            print(f"      Winning Chance: {candidate['winning_chances']:.1f}%")
                            print(f"      Experience: {candidate['experience']}")
                            print(f"      Assets: {candidate['assets']} | Cases: {candidate['criminal_cases']}")
                        
                        # Historical context
                        hist = matchup['historical_context']
                        print(f"   Previous Winners:")
                        print(f"      2020 Assembly: {hist['last_winner']} ({hist['last_party']})")
                        print(f"      Margin: {hist['last_margin']:,} votes | Trend: {hist['trend']}")
                
                # Show competitive seats summary
                if 'marginal_seats' in sim_results:
                    marginal_df = sim_results['marginal_seats']
                    print(f"\n🔥 TOP 10 MOST COMPETITIVE CONSTITUENCIES:")
                    print(f"=" * 80)
                    print(f"{'Rank':<4} {'Constituency':<20} {'NDA Prob':<10} {'Status':<12} {'Region':<15}")
                    print(f"-" * 80)
                    for i, (_, row) in enumerate(marginal_df.head(10).iterrows()):
                        constituency = row['constituency']
                        prob = row['nda_win_prob']
                        classification = row['classification']
                        region = row.get('region', 'Unknown')
                        print(f"{i+1:<4} {constituency:<20} {prob:.1%}{'':>4} {classification:<12} {region:<15}")
                
            print(f"\n💡 Full Interactive Analysis: python main.py dashboard")
            return True
        else:
            print(f"\n❌ Update failed!")
            for error in results['errors']:
                print(f"   Error: {error}")
            return False
            
    except Exception as e:
        print(f"\n💥 Update crashed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cmd_schedule():
    """Start the scheduler for automated daily updates"""
    print("⏰ Starting Bihar Forecast Scheduler...")
    print("=" * 60)
    
    try:
        scheduler = create_default_scheduler(background_mode=False)
        
        print(f"\n📅 Scheduled Jobs:")
        for job in scheduler.scheduler.get_jobs():
            print(f"   • {job.name}")
            print(f"     Next run: {job.next_run_time}")
        
        print(f"\n🚀 Scheduler starting... (Press Ctrl+C to stop)")
        scheduler.start()
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Scheduler stopped by user")
        return True
    except Exception as e:
        print(f"\n💥 Scheduler failed: {e}")
        return False


def cmd_dashboard(host="localhost", port="8501"):
    """Launch Streamlit dashboard"""
    print("🌐 Launching Bihar Election Forecast Dashboard...")
    print("=" * 60)
    
    try:
        dashboard_path = Path("src/dashboard/app.py")
        
        if not dashboard_path.exists():
            print(f"❌ Dashboard file not found: {dashboard_path}")
            return False
        
        print(f"🚀 Starting Streamlit server...")
        print(f"📱 Dashboard will open in your browser")
        print(f"🔗 URL: http://{host}:{port}")
        print(f"\n⏹️  Press Ctrl+C to stop the dashboard")
        
        # Run streamlit
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.port", port,
            "--server.address", host
        ])
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Dashboard stopped by user")
        return True
    except Exception as e:
        print(f"\n💥 Dashboard failed: {e}")
        return False


def cmd_test():
    """Run system tests"""
    print("🧪 Running Bihar Forecast System Tests...")
    print("=" * 60)
    
    test_results = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    def run_test(test_name, test_func):
        """Run a single test"""
        test_results['total_tests'] += 1
        print(f"\n🔍 Testing {test_name}...")
        
        try:
            success = test_func()
            if success:
                print(f"   ✅ {test_name} passed")
                test_results['passed'] += 1
            else:
                print(f"   ❌ {test_name} failed")
                test_results['failed'] += 1
        except Exception as e:
            print(f"   💥 {test_name} crashed: {e}")
            test_results['failed'] += 1
            test_results['errors'].append(f"{test_name}: {e}")
    
    # Test data ingestion
    def test_data_ingestion():
        from src.ingest.news_ingest import NewsIngestor
        ingestor = NewsIngestor()
        news_df = ingestor.fetch_from_newsapi(days_back=1)
        return len(news_df) > 0
    
    # Test NLP processing
    def test_nlp_processing():
        from src.nlp.sentiment_engine import SentimentEngine
        engine = SentimentEngine()
        result = engine.analyze_text("This is a test message for Bihar elections")
        return 'sentiment_score' in result
    
    # Test feature engineering
    def test_feature_engineering():
        from src.features.feature_updater import FeatureUpdater
        updater = FeatureUpdater()
        features = updater.load_base_features()
        return len(features) > 0
    
    # Test model management
    def test_model_management():
        from src.modeling.model_updater import ModelUpdater
        updater = ModelUpdater()
        # Just test initialization
        return updater is not None
    
    # Test dashboard components
    def test_dashboard():
        from src.dashboard.app import ForecastDashboard
        dashboard = ForecastDashboard()
        return dashboard is not None
    
    # Run all tests
    run_test("Data Ingestion", test_data_ingestion)
    run_test("NLP Processing", test_nlp_processing)
    run_test("Feature Engineering", test_feature_engineering)
    run_test("Model Management", test_model_management)
    run_test("Dashboard Components", test_dashboard)
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"🧪 TEST SUMMARY")
    print(f"=" * 60)
    print(f"📊 Total Tests: {test_results['total_tests']}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    
    if test_results['errors']:
        print(f"\n💥 Errors:")
        for error in test_results['errors']:
            print(f"   • {error}")
    
    success_rate = test_results['passed'] / test_results['total_tests']
    if success_rate >= 0.8:
        print(f"\n🎉 System health: GOOD ({success_rate:.0%})")
        return True
    else:
        print(f"\n⚠️  System health: POOR ({success_rate:.0%})")
        return False


def cmd_status():
    """Show system status"""
    print("📊 Bihar Forecast System Status")
    print("=" * 60)
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'directories': {},
        'data_files': {},
        'recent_results': {},
        'configuration': {}
    }
    
    # Check directories
    print(f"\n📁 Directory Status:")
    directories = [
        ('Raw Data', Config.RAW_DATA_DIR),
        ('Processed Data', Config.PROCESSED_DATA_DIR),
        ('Models', Config.MODELS_DIR),
        ('Results', Config.RESULTS_DIR)
    ]
    
    for name, path in directories:
        exists = path.exists()
        file_count = len(list(path.glob('*'))) if exists else 0
        status['directories'][name] = {'exists': exists, 'file_count': file_count}
        
        status_icon = "✅" if exists else "❌"
        print(f"   {status_icon} {name}: {file_count} files" if exists else f"   {status_icon} {name}: Not found")
    
    # Check recent data files
    print(f"\n📊 Recent Data Files:")
    today = datetime.now().strftime('%Y-%m-%d')
    
    data_checks = [
        ('News Data', Config.RAW_DATA_DIR / f"*news*{today}*"),
        ('Poll Data', Config.PROCESSED_DATA_DIR / f"*poll*{today}*"),
        ('Features', Config.PROCESSED_DATA_DIR / f"features*{today}*"),
        ('Results', Config.RESULTS_DIR / today)
    ]
    
    for name, pattern in data_checks:
        if isinstance(pattern, Path):
            exists = pattern.exists()
            count = len(list(pattern.glob('*'))) if exists else 0
        else:
            files = list(pattern.parent.glob(pattern.name))
            exists = len(files) > 0
            count = len(files)
        
        status['data_files'][name] = {'exists': exists, 'count': count}
        
        status_icon = "✅" if exists else "⚠️"
        print(f"   {status_icon} {name}: {count} files" if exists else f"   {status_icon} {name}: No recent files")
    
    # Check configuration
    print(f"\n⚙️  Configuration:")
    
    env_file = Path(".env")
    config_items = [
        ('Environment File', env_file.exists()),
        ('News API Key', bool(Config.NEWS_API_KEY)),
        ('Twitter Token', bool(Config.TWITTER_BEARER_TOKEN)),
        ('HuggingFace Token', bool(Config.HUGGINGFACE_TOKEN))
    ]
    
    for name, exists in config_items:
        status['configuration'][name] = exists
        status_icon = "✅" if exists else "⚠️"
        print(f"   {status_icon} {name}")
    
    # Check latest results
    print(f"\n📈 Latest Results:")
    
    try:
        result_dirs = sorted([d for d in Config.RESULTS_DIR.iterdir() if d.is_dir()], reverse=True)
        if result_dirs:
            latest_dir = result_dirs[0]
            summary_file = latest_dir / "forecast_summary.json"
            
            if summary_file.exists():
                with open(summary_file) as f:
                    summary = json.load(f)
                
                if 'nda_projection' in summary:
                    nda_proj = summary['nda_projection']
                    print(f"   📅 Latest Forecast: {latest_dir.name}")
                    print(f"   🎯 Mean NDA Seats: {nda_proj.get('mean_seats', 0):.0f}")
                    print(f"   📊 Majority Probability: {nda_proj.get('probability_majority', 0):.1%}")
                    
                    status['recent_results'] = {
                        'date': latest_dir.name,
                        'mean_seats': nda_proj.get('mean_seats', 0),
                        'majority_prob': nda_proj.get('probability_majority', 0)
                    }
                else:
                    print(f"   ⚠️  Latest results incomplete")
            else:
                print(f"   ⚠️  No forecast summary found")
        else:
            print(f"   ⚠️  No results available")
    
    except Exception as e:
        print(f"   ❌ Error reading results: {e}")
    
    # Overall health assessment
    print(f"\n" + "=" * 60)
    
    # Calculate health score
    health_score = 0
    total_checks = 0
    
    # Directory health (25%)
    dir_health = sum(1 for d in status['directories'].values() if d['exists']) / len(status['directories'])
    health_score += dir_health * 0.25
    
    # Data health (25%)
    data_health = sum(1 for d in status['data_files'].values() if d['exists']) / len(status['data_files'])
    health_score += data_health * 0.25
    
    # Config health (25%)
    config_health = sum(1 for c in status['configuration'].values() if c) / len(status['configuration'])
    health_score += config_health * 0.25
    
    # Results health (25%)
    results_health = 1.0 if status['recent_results'] else 0.0
    health_score += results_health * 0.25
    
    if health_score >= 0.8:
        health_status = "🟢 EXCELLENT"
    elif health_score >= 0.6:
        health_status = "🟡 GOOD"
    elif health_score >= 0.4:
        health_status = "🟠 FAIR"
    else:
        health_status = "🔴 POOR"
    
    print(f"🏥 System Health: {health_status} ({health_score:.0%})")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if not status['configuration']['News API Key']:
        print(f"   • Add NEWS_API_KEY to .env file for real news data")
    if not status['data_files']['Results']['exists']:
        print(f"   • Run 'python main.py update' to generate forecasts")
    if data_health < 0.5:
        print(f"   • Run daily updates to refresh data")
    
    return health_score >= 0.6


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Bihar Election Forecast System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py init                    # First time setup
  python main.py update                  # Run daily update
  python main.py dashboard               # Launch web interface
  python main.py schedule                # Start automated updates
  python main.py status                  # Check system health
  python main.py test                    # Run system tests

For more information, visit: https://github.com/yourusername/bihar-forecast
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize system (first time setup)')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Run daily update once')
    
    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Start automated scheduler')
    schedule_parser.add_argument('--daily-hour', type=int, default=6, 
                               help='Hour for daily update (0-23)')
    schedule_parser.add_argument('--quick-interval', type=int, default=4,
                               help='Hours between quick updates')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Launch web dashboard')
    dashboard_parser.add_argument('--port', type=int, default=8501,
                                help='Port for dashboard server')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run system tests')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    args = parser.parse_args()
    
    # Execute commands
    success = False
    
    if args.command == 'init':
        success = cmd_init()
    elif args.command == 'update':
        success = cmd_update()
    elif args.command == 'schedule':
        success = cmd_schedule()
    elif args.command == 'dashboard':
        success = cmd_dashboard()
    elif args.command == 'test':
        success = cmd_test()
    elif args.command == 'status':
        success = cmd_status()
    else:
        parser.print_help()
        success = True
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()