import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from src.config.settings import Config
import json
import traceback
import logging

# Import all our components
from src.ingest.news_ingest import NewsIngestor
from src.ingest.poll_ingest import PollIngestor
from src.ingest.trends_ingest import TrendsIngestor
from src.ingest.eci_ingest import ECIIngestor
from src.ingest.real_data_sources import RealDataManager
from src.nlp.sentiment_engine import SentimentEngine
from src.nlp.entity_mapper import EntityMapper
from src.features.feature_updater import FeatureUpdater
from src.features.poll_feature_engine import PollFeatureEngine
from src.features.feature_store import FeatureStore
from src.modeling.model_updater import ModelUpdater
from src.modeling.monte_carlo_simulator import MonteCarloSimulator


class DailyUpdatePipeline:
    """Master orchestrator for daily Bihar election forecast updates"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
        self.date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Initialize directories
        Config.create_directories()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.components = {}
        self._initialize_components()
        
        print(f"✅ Daily update pipeline initialized for {self.date_str}")
    
    def _setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Config.BASE_DIR / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"daily_update_{self.date_str}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Daily update pipeline started at {datetime.now()}")
    
    def _initialize_components(self):
        """Initialize all pipeline components"""
        try:
            self.components = {
                'news_ingestor': NewsIngestor(),
                'poll_ingestor': PollIngestor(),
                'trends_ingestor': TrendsIngestor(),
                'eci_ingestor': ECIIngestor(),
                'real_data_manager': RealDataManager(),
                'sentiment_engine': SentimentEngine(),
                'entity_mapper': EntityMapper(),
                'feature_updater': FeatureUpdater(),
                'poll_feature_engine': PollFeatureEngine(),
                'feature_store': FeatureStore(),
                'model_updater': ModelUpdater()
            }
            self.logger.info("All pipeline components initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    def run_full_pipeline(self) -> Dict:
        """Execute the complete daily update pipeline"""
        self.logger.info("=" * 70)
        self.logger.info(f"STARTING DAILY BIHAR ELECTION FORECAST UPDATE - {self.date_str}")
        self.logger.info("=" * 70)
        
        pipeline_results = {
            'timestamp': datetime.now().isoformat(),
            'date': self.date_str,
            'success': False,
            'steps_completed': [],
            'errors': [],
            'results': {}
        }
        
        try:
            # Step 1: Data Ingestion
            self.logger.info("\n🔄 STEP 1: DATA INGESTION")
            ingestion_results = self._run_data_ingestion()
            pipeline_results['results']['ingestion'] = ingestion_results
            pipeline_results['steps_completed'].append('data_ingestion')
            
            # Step 2: NLP Processing
            self.logger.info("\n🧠 STEP 2: NLP PROCESSING")
            nlp_results = self._run_nlp_processing(ingestion_results)
            pipeline_results['results']['nlp'] = nlp_results
            pipeline_results['steps_completed'].append('nlp_processing')
            
            # Step 3: Feature Engineering
            self.logger.info("\n⚙️ STEP 3: FEATURE ENGINEERING")
            feature_results = self._run_feature_engineering(nlp_results)
            pipeline_results['results']['features'] = feature_results
            pipeline_results['steps_completed'].append('feature_engineering')
            
            # Step 4: Model Management
            self.logger.info("\n🤖 STEP 4: MODEL MANAGEMENT")
            model_results = self._run_model_management(feature_results)
            pipeline_results['results']['model'] = model_results
            pipeline_results['steps_completed'].append('model_management')
            
            # Step 5: Monte Carlo Simulation
            self.logger.info("\n🎲 STEP 5: MONTE CARLO SIMULATION")
            simulation_results = self._run_monte_carlo_simulation(model_results, feature_results)
            pipeline_results['results']['simulation'] = simulation_results
            pipeline_results['steps_completed'].append('monte_carlo_simulation')
            
            # Step 6: Results Analysis & Export
            self.logger.info("\n📊 STEP 6: RESULTS ANALYSIS & EXPORT")
            analysis_results = self._run_results_analysis(simulation_results)
            pipeline_results['results']['analysis'] = analysis_results
            pipeline_results['steps_completed'].append('results_analysis')
            
            # Step 7: Cleanup & Archival
            self.logger.info("\n🗂️ STEP 7: CLEANUP & ARCHIVAL")
            cleanup_results = self._run_cleanup_archival()
            pipeline_results['results']['cleanup'] = cleanup_results
            pipeline_results['steps_completed'].append('cleanup_archival')
            
            pipeline_results['success'] = True
            self.logger.info("\n✅ DAILY UPDATE PIPELINE COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            error_msg = f"Pipeline failed at step {len(pipeline_results['steps_completed']) + 1}: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            pipeline_results['errors'].append(error_msg)
            pipeline_results['success'] = False
        
        # Save pipeline results
        self._save_pipeline_results(pipeline_results)
        
        return pipeline_results
    
    def _run_data_ingestion(self) -> Dict:
        """Step 1: Comprehensive data ingestion"""
        results = {
            'news_articles': 0,
            'poll_data_points': 0,
            'trends_keywords': 0,
            'eci_data_available': False,
            'data_sources_active': 0
        }
        
        try:
            # Enhanced comprehensive news ingestion
            self.logger.info("   Fetching news from ALL sources (NewsAPI + RSS + Scraping)...")
            news_df = self.components['news_ingestor'].fetch_comprehensive_news(days_back=1)
            
            if not news_df.empty:
                # Save raw news
                self.components['news_ingestor'].save_raw_news(news_df, self.date_str)
                results['news_articles'] = len(news_df)
                self.logger.info(f"   ✅ Fetched {len(news_df)} news articles")
            else:
                self.logger.warning("   ⚠️ No news articles fetched")
            
            # Poll data ingestion
            self.logger.info("   Fetching opinion polls...")
            polls_df = self.components['poll_ingestor'].fetch_opinion_polls()
            
            if not polls_df.empty:
                self.components['poll_ingestor'].save_polls(polls_df)
                results['poll_data_points'] = len(polls_df)
                self.logger.info(f"   ✅ Fetched {len(polls_df)} poll data points")
            
            # Trends data ingestion
            self.logger.info("   Fetching Google Trends data...")
            trends_df = self.components['trends_ingestor'].fetch_keyword_trends()
            
            if not trends_df.empty:
                self.components['trends_ingestor'].save_trends_data(trends_df, self.date_str)
                results['trends_keywords'] = len([col for col in trends_df.columns if col not in ['date', 'fetch_timestamp', 'timeframe', 'geo']])
                self.logger.info(f"   ✅ Fetched trends for {results['trends_keywords']} keywords")
            
            # ECI data ingestion - ENHANCED
            self.logger.info("   Fetching ECI live data and results...")
            eci_trends = self.components['eci_ingestor'].get_real_time_trends()
            eci_results_df = self.components['eci_ingestor'].fetch_live_results()
            eci_party_df = self.components['eci_ingestor'].fetch_constituency_details()
            
            results['eci_data_available'] = bool(eci_trends)
            results['eci_live_results'] = len(eci_results_df) if not eci_results_df.empty else 0
            results['eci_party_data'] = len(eci_party_df) if not eci_party_df.empty else 0
            
            # Save ECI data if available
            if not eci_results_df.empty:
                self.components['eci_ingestor'].save_eci_data('live_results', eci_results_df)
                self.logger.info(f"   ✅ Fetched {len(eci_results_df)} ECI live results")
            
            if not eci_party_df.empty:
                self.components['eci_ingestor'].save_eci_data('party_performance', eci_party_df)
                self.logger.info(f"   ✅ Fetched ECI party performance data")
            
            if eci_trends:
                # Save ECI trends data
                trends_path = Config.RAW_DATA_DIR / f"eci_trends_{self.date_str}.json"
                with open(trends_path, 'w') as f:
                    json.dump(eci_trends, f, indent=2, default=str)
                self.logger.info(f"   ✅ Saved ECI real-time trends data")
            
            # Data freshness check
            freshness = self.components['real_data_manager'].check_data_freshness()
            results['data_sources_active'] = freshness['news_sources_active']
            
            results['raw_data'] = {
                'news_df': news_df,
                'polls_df': polls_df,
                'trends_df': trends_df,
                'eci_results_df': eci_results_df if not eci_results_df.empty else pd.DataFrame(),
                'eci_party_df': eci_party_df if not eci_party_df.empty else pd.DataFrame(),
                'eci_trends': eci_trends
            }
            
        except Exception as e:
            self.logger.error(f"Data ingestion error: {e}")
            raise
        
        return results
    
    def _run_nlp_processing(self, ingestion_results: Dict) -> Dict:
        """Step 2: Advanced NLP processing"""
        results = {
            'articles_analyzed': 0,
            'sentiment_distribution': {},
            'entities_extracted': 0,
            'political_coverage_pct': 0
        }
        
        try:
            news_df = ingestion_results['raw_data']['news_df']
            
            if news_df.empty:
                self.logger.warning("   No news data for NLP processing")
                return results
            
            # Sentiment analysis
            self.logger.info("   Running sentiment analysis...")
            analyzed_df = self.components['sentiment_engine'].analyze_dataframe(news_df)
            results['articles_analyzed'] = len(analyzed_df)
            results['sentiment_distribution'] = analyzed_df['sentiment_label'].value_counts().to_dict()
            
            # Entity mapping
            self.logger.info("   Mapping political entities...")
            enriched_df = self.components['entity_mapper'].enrich_dataframe(analyzed_df)
            
            # Calculate political coverage
            political_articles = len(enriched_df[enriched_df['party_mentioned'] != 'general'])
            results['political_coverage_pct'] = (political_articles / len(enriched_df)) * 100
            
            # Count entities
            all_leaders = []
            for leaders_list in enriched_df['leaders_mentioned']:
                if isinstance(leaders_list, str):
                    leaders_list = eval(leaders_list) if leaders_list.startswith('[') else [leaders_list]
                all_leaders.extend(leaders_list)
            results['entities_extracted'] = len(set(all_leaders))
            
            # Save processed data
            processed_path = Config.PROCESSED_DATA_DIR / f"nlp_processed_{self.date_str}.csv"
            enriched_df.to_csv(processed_path, index=False)
            
            results['processed_data'] = enriched_df
            
            self.logger.info(f"   ✅ Processed {len(enriched_df)} articles, {results['political_coverage_pct']:.1f}% political coverage")
            
        except Exception as e:
            self.logger.error(f"NLP processing error: {e}")
            raise
        
        return results
    
    def _run_feature_engineering(self, nlp_results: Dict) -> Dict:
        """Step 3: Advanced feature engineering"""
        results = {
            'constituencies_updated': 0,
            'features_count': 0,
            'sentiment_coverage': 0,
            'poll_swing_applied': False
        }
        
        try:
            # Load base features
            self.logger.info("   Loading base features...")
            base_features = self.components['feature_updater'].load_base_features()
            
            # Update sentiment features
            if 'processed_data' in nlp_results:
                self.logger.info("   Updating sentiment features...")
                news_df = nlp_results['processed_data']
                sentiment_agg = self.components['feature_updater'].aggregate_news_sentiment(news_df)
                updated_features = self.components['feature_updater'].update_sentiment_features(base_features, sentiment_agg)
                
                # Calculate sentiment coverage
                results['sentiment_coverage'] = (updated_features['news_sentiment_nda'] != 0).sum() / len(updated_features)
            else:
                updated_features = base_features
            
            # Update poll features with ECI data integration
            self.logger.info("   Applying poll-based updates with ECI data...")
            
            # Load existing polls
            polls_path = Config.PROCESSED_DATA_DIR / "enhanced_polls_2025-10-17.csv"
            if polls_path.exists():
                polls_df = pd.read_csv(polls_path)
                
                # Integrate ECI data if available
                eci_data = nlp_results.get('raw_data', {})
                if 'eci_party_df' in eci_data and not eci_data['eci_party_df'].empty:
                    self.logger.info("   Integrating ECI live data into poll features...")
                    
                    # Convert ECI party performance to poll format
                    eci_party_df = eci_data['eci_party_df']
                    eci_poll_data = self._convert_eci_to_poll_format(eci_party_df)
                    
                    if not eci_poll_data.empty:
                        # Add ECI data as most recent "poll"
                        polls_df = pd.concat([polls_df, eci_poll_data], ignore_index=True)
                        self.logger.info(f"   ✅ Added ECI data as latest poll update")
                
                # Advanced poll aggregation
                poll_aggregates = self.components['poll_feature_engine'].calculate_poll_aggregates(polls_df)
                
                # Apply poll swing
                updated_features = self.components['poll_feature_engine'].apply_poll_swing_to_constituencies(
                    updated_features, poll_aggregates
                )
                
                # Calculate probabilities
                updated_features = self.components['poll_feature_engine'].calculate_seat_probabilities(updated_features)
                
                results['poll_swing_applied'] = True
                results['eci_data_integrated'] = 'eci_party_df' in eci_data and not eci_data['eci_party_df'].empty
            
            # Calculate derived features
            self.logger.info("   Calculating derived features...")
            final_features = self.components['feature_updater'].calculate_derived_features(updated_features)
            
            # Save features with versioning
            version = self.components['feature_store'].save_features(
                final_features, 
                f"daily_{self.date_str}",
                {'pipeline_run': True, 'data_sources': nlp_results.get('articles_analyzed', 0)}
            )
            
            results['constituencies_updated'] = len(final_features)
            results['features_count'] = len(final_features.columns)
            results['feature_version'] = version
            results['final_features'] = final_features
            
            self.logger.info(f"   ✅ Updated {len(final_features)} constituencies with {len(final_features.columns)} features")
            
        except Exception as e:
            self.logger.error(f"Feature engineering error: {e}")
            raise
        
        return results
    
    def _run_model_management(self, feature_results: Dict) -> Dict:
        """Step 4: Model management and updates"""
        results = {
            'model_loaded': False,
            'model_updated': False,
            'model_accuracy': 0.0,
            'predictions_generated': False
        }
        
        try:
            features_df = feature_results['final_features']
            
            # Load or create model
            self.logger.info("   Loading production model...")
            try:
                model = self.components['model_updater'].load_model("latest")
                results['model_loaded'] = True
                self.logger.info("   ✅ Loaded existing model")
            except FileNotFoundError:
                self.logger.info("   Creating new model...")
                model = self.components['model_updater'].create_initial_model(features_df)
                self.components['model_updater'].save_model()
                results['model_loaded'] = True
                self.logger.info("   ✅ Created and saved new model")
            
            # Evaluate model
            evaluation = self.components['model_updater'].evaluate_model(features_df)
            results['model_accuracy'] = evaluation['metrics']['accuracy']
            
            # Generate predictions
            self.logger.info("   Generating constituency predictions...")
            predictions_df = self.components['model_updater'].predict_constituencies(features_df)
            
            # Save predictions
            pred_path = Config.RESULTS_DIR / self.date_str
            pred_path.mkdir(parents=True, exist_ok=True)
            predictions_df.to_csv(pred_path / "constituency_predictions.csv", index=False)
            
            results['predictions_generated'] = True
            results['model'] = model
            results['predictions'] = predictions_df
            
            self.logger.info(f"   ✅ Model accuracy: {results['model_accuracy']:.3f}")
            
        except Exception as e:
            self.logger.error(f"Model management error: {e}")
            raise
        
        return results
    
    def _run_monte_carlo_simulation(self, model_results: Dict, feature_results: Dict) -> Dict:
        """Step 5: Monte Carlo simulation"""
        results = {
            'simulations_run': 0,
            'mean_nda_seats': 0,
            'probability_majority': 0.0,
            'competitive_seats': 0
        }
        
        try:
            model = model_results['model']
            features_df = feature_results['final_features']
            
            # Initialize simulator
            self.logger.info(f"   Initializing Monte Carlo simulator...")
            simulator = MonteCarloSimulator(model, features_df)
            
            # Run simulations
            self.logger.info(f"   Running {Config.N_MONTE_CARLO_SIMS:,} simulations...")
            simulation_results = simulator.run_simulations(
                n_sims=Config.N_MONTE_CARLO_SIMS,
                uncertainty_factor=1.0,
                correlation_factor=0.3,
                parallel=True
            )
            
            # Extract key statistics
            stats = simulation_results['statistics']
            results['simulations_run'] = Config.N_MONTE_CARLO_SIMS
            results['mean_nda_seats'] = stats['mean_nda_seats']
            results['probability_majority'] = stats['prob_nda_majority']
            results['competitive_seats'] = stats['toss_up_seats']
            
            # Analyze scenarios
            scenarios = simulator.analyze_scenarios(simulation_results)
            results['scenarios'] = scenarios
            
            # Get marginal seats
            marginal_seats = simulator.get_marginal_seats(simulation_results)
            results['marginal_seats'] = marginal_seats
            
            # Export results
            export_files = simulator.export_results(simulation_results, Config.RESULTS_DIR / self.date_str)
            results['export_files'] = export_files
            results['simulation_data'] = simulation_results
            
            self.logger.info(f"   ✅ Simulations complete: {results['mean_nda_seats']:.1f} mean NDA seats, {results['probability_majority']:.1%} majority probability")
            
        except Exception as e:
            self.logger.error(f"Monte Carlo simulation error: {e}")
            raise
        
        return results
    
    def _run_results_analysis(self, simulation_results: Dict) -> Dict:
        """Step 6: Comprehensive results analysis"""
        results = {
            'reports_generated': 0,
            'visualizations_created': 0,
            'summary_statistics': {}
        }
        
        try:
            # Generate comprehensive summary
            self.logger.info("   Generating analysis summary...")
            
            stats = simulation_results['simulation_data']['statistics']
            
            summary = {
                'forecast_date': self.date_str,
                'total_simulations': simulation_results['simulations_run'],
                'nda_projection': {
                    'mean_seats': stats['mean_nda_seats'],
                    'median_seats': stats['median_nda_seats'],
                    'confidence_interval_95': [stats['p5_nda_seats'], stats['p95_nda_seats']],
                    'probability_majority': stats['prob_nda_majority'],
                    'probability_supermajority': stats['prob_nda_supermajority']
                },
                'seat_classification': {
                    'safe_nda': stats['safe_nda_seats'],
                    'likely_nda': stats['likely_nda_seats'],
                    'lean_nda': stats['lean_nda_seats'],
                    'toss_up': stats['toss_up_seats'],
                    'lean_indi': stats['lean_indi_seats'],
                    'likely_indi': stats['likely_indi_seats'],
                    'safe_indi': stats['safe_indi_seats']
                },
                'key_insights': self._generate_key_insights(simulation_results)
            }
            
            # Save summary
            results_dir = Config.RESULTS_DIR / self.date_str
            summary_path = results_dir / "forecast_summary.json"
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            results['summary_statistics'] = summary
            results['reports_generated'] = 1
            
            self.logger.info("   ✅ Analysis summary generated")
            
        except Exception as e:
            self.logger.error(f"Results analysis error: {e}")
            raise
        
        return results
    
    def _run_cleanup_archival(self) -> Dict:
        """Step 7: Cleanup and archival"""
        results = {
            'old_versions_cleaned': 0,
            'files_archived': 0,
            'storage_optimized': False
        }
        
        try:
            # Cleanup old feature versions
            self.logger.info("   Cleaning up old feature versions...")
            cleaned_features = self.components['feature_store'].cleanup_old_versions(keep_days=30, keep_count=10)
            results['old_versions_cleaned'] += cleaned_features
            
            # Cleanup old model versions
            self.logger.info("   Cleaning up old model versions...")
            cleaned_models = self.components['model_updater'].cleanup_old_models(keep_count=5)
            results['old_versions_cleaned'] += cleaned_models
            
            # Archive old results (keep last 60 days)
            self.logger.info("   Archiving old results...")
            cutoff_date = datetime.now() - timedelta(days=60)
            archived_count = 0
            
            for result_dir in Config.RESULTS_DIR.iterdir():
                if result_dir.is_dir():
                    try:
                        dir_date = datetime.strptime(result_dir.name, '%Y-%m-%d')
                        if dir_date < cutoff_date:
                            # In production, move to archive storage instead of deleting
                            archived_count += 1
                    except ValueError:
                        continue  # Skip non-date directories
            
            results['files_archived'] = archived_count
            results['storage_optimized'] = True
            
            self.logger.info(f"   ✅ Cleanup complete: {results['old_versions_cleaned']} old versions removed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
            # Don't raise - cleanup errors shouldn't fail the pipeline
        
        return results
    
    def _generate_key_insights(self, simulation_results: Dict) -> List[str]:
        """Generate key insights from simulation results"""
        insights = []
        
        stats = simulation_results['simulation_data']['statistics']
        scenarios = simulation_results.get('scenarios', {})
        
        # Majority probability insight
        majority_prob = stats['prob_nda_majority']
        if majority_prob > 0.7:
            insights.append(f"NDA has a strong {majority_prob:.0%} chance of winning majority")
        elif majority_prob > 0.3:
            insights.append(f"Election is competitive with {majority_prob:.0%} NDA majority probability")
        else:
            insights.append(f"INDI alliance favored with {1-majority_prob:.0%} majority probability")
        
        # Seat range insight
        p25, p75 = stats['p25_nda_seats'], stats['p75_nda_seats']
        insights.append(f"NDA likely to win {p25:.0f}-{p75:.0f} seats (50% confidence interval)")
        
        # Competitive seats insight
        toss_ups = stats['toss_up_seats']
        if toss_ups > 20:
            insights.append(f"High uncertainty with {toss_ups} highly competitive seats")
        elif toss_ups > 10:
            insights.append(f"Moderate uncertainty with {toss_ups} competitive seats")
        else:
            insights.append(f"Low uncertainty with only {toss_ups} truly competitive seats")
        
        # Regional insights
        if 'regional_analysis' in stats:
            regional_stats = stats['regional_analysis']
            strongest_region = max(regional_stats.keys(), 
                                 key=lambda r: regional_stats[r]['expected_nda_seats'] / regional_stats[r]['total_seats'])
            insights.append(f"NDA strongest in {strongest_region} region")
        
        return insights
    
    def _convert_eci_to_poll_format(self, eci_party_df: pd.DataFrame) -> pd.DataFrame:
        """Convert ECI party performance data to poll format"""
        try:
            if eci_party_df.empty:
                return pd.DataFrame()
            
            # Calculate total seats from ECI data
            total_seats = eci_party_df['seats_won'].sum() + eci_party_df['seats_leading'].sum()
            
            if total_seats == 0:
                return pd.DataFrame()
            
            # Map parties to alliances
            nda_parties = ['BJP', 'JDU', 'NDA', 'Janata Dal (United)', 'Bharatiya Janata Party']
            indi_parties = ['RJD', 'Congress', 'INDI', 'Rashtriya Janata Dal', 'Indian National Congress']
            
            nda_seats = 0
            indi_seats = 0
            others_seats = 0
            
            for _, row in eci_party_df.iterrows():
                party = row['party']
                seats = row.get('seats_won', 0) + row.get('seats_leading', 0)
                
                if any(nda_party.lower() in party.lower() for nda_party in nda_parties):
                    nda_seats += seats
                elif any(indi_party.lower() in party.lower() for indi_party in indi_parties):
                    indi_seats += seats
                else:
                    others_seats += seats
            
            # Convert to percentages
            nda_percent = (nda_seats / total_seats) * 100 if total_seats > 0 else 0
            indi_percent = (indi_seats / total_seats) * 100 if total_seats > 0 else 0
            others_percent = (others_seats / total_seats) * 100 if total_seats > 0 else 0
            
            # Create poll-format dataframe
            eci_poll = pd.DataFrame([{
                'date': datetime.now().strftime('%Y-%m-%d'),
                'pollster': 'ECI_Live_Results',
                'sample_size': total_seats * 1000,  # Estimate based on constituency size
                'nda_percent': nda_percent,
                'indi_percent': indi_percent,
                'others_percent': others_percent,
                'margin_of_error': 1.0,  # Very low error for actual results
                'methodology': 'Live Election Results',
                'region': 'Statewide',
                'weight': 10.0,  # High weight for actual results
                'data_source': 'ECI'
            }])
            
            self.logger.info(f"   Converted ECI data: NDA {nda_percent:.1f}%, INDI {indi_percent:.1f}%, Others {others_percent:.1f}%")
            return eci_poll
            
        except Exception as e:
            self.logger.error(f"Error converting ECI data to poll format: {e}")
            return pd.DataFrame()
    
    def _save_pipeline_results(self, pipeline_results: Dict):
        """Save comprehensive pipeline results"""
        results_dir = Config.RESULTS_DIR / self.date_str
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Save pipeline summary
        pipeline_summary = {
            'success': pipeline_results['success'],
            'timestamp': pipeline_results['timestamp'],
            'steps_completed': pipeline_results['steps_completed'],
            'errors': pipeline_results['errors'],
            'summary_stats': {}
        }
        
        # Extract key statistics
        if 'simulation' in pipeline_results['results']:
            sim_results = pipeline_results['results']['simulation']
            pipeline_summary['summary_stats'] = {
                'mean_nda_seats': sim_results.get('mean_nda_seats', 0),
                'probability_majority': sim_results.get('probability_majority', 0),
                'competitive_seats': sim_results.get('competitive_seats', 0),
                'simulations_run': sim_results.get('simulations_run', 0)
            }
        
        # Save to file
        summary_path = results_dir / "pipeline_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(pipeline_summary, f, indent=2, default=str)
        
        self.logger.info(f"Pipeline results saved to {results_dir}")
    
    def run_quick_update(self) -> Dict:
        """Run a quick update with minimal processing"""
        self.logger.info("Running quick update pipeline...")
        
        try:
            # Quick data fetch
            news_df = self.components['real_data_manager'].get_live_news_data()
            
            # Quick sentiment analysis
            if not news_df.empty:
                analyzed_df = self.components['sentiment_engine'].analyze_dataframe(news_df)
                
                # Quick feature update
                base_features = self.components['feature_updater'].load_base_features()
                sentiment_agg = self.components['feature_updater'].aggregate_news_sentiment(analyzed_df)
                updated_features = self.components['feature_updater'].update_sentiment_features(base_features, sentiment_agg)
                
                # Save quick update
                version = self.components['feature_store'].save_features(
                    updated_features, 
                    f"quick_{self.timestamp}",
                    {'quick_update': True}
                )
                
                return {
                    'success': True,
                    'articles_processed': len(analyzed_df),
                    'feature_version': version,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'No news data available for quick update'
                }
                
        except Exception as e:
            self.logger.error(f"Quick update failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }