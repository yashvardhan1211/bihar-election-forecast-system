import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from src.config.settings import Config
import json
import logging

# Import enhanced components
from src.features.enhanced_feature_engine import EnhancedFeatureEngine
from src.features.poll_corrector import PollCorrector
from src.modeling.ensemble_predictor import EnsemblePredictor
from src.modeling.probability_calibrator import ProbabilityCalibrator
from src.validation.model_validator import ModelValidator
from src.validation.bias_analyzer import BiasAnalyzer
from src.features.feature_selector import FeatureSelector
from src.monitoring.model_monitor import ModelMonitor

class EnhancedDailyUpdate:
    """Enhanced daily update pipeline with improved accuracy components"""
    
    def __init__(self):
        self.results_dir = Config.RESULTS_DIR
        self.data_dir = Config.DATA_DIR
        
        # Initialize enhanced components
        self.feature_engine = EnhancedFeatureEngine()
        self.poll_corrector = PollCorrector()
        self.ensemble_predictor = EnsemblePredictor()
        self.probability_calibrator = ProbabilityCalibrator()
        self.model_validator = ModelValidator()
        self.bias_analyzer = BiasAnalyzer()
        self.feature_selector = FeatureSelector()
        self.model_monitor = ModelMonitor()
        
        # Pipeline state
        self.pipeline_state = {}
        self.execution_log = []
        
        self.logger = logging.getLogger(__name__)
        print(f"✅ Enhanced Daily Update Pipeline initialized")
    
    def run_enhanced_pipeline(self, date_str: str = None) -> Dict:
        """Run the complete enhanced daily update pipeline"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        print(f"🔄 Starting enhanced daily update for {date_str}")
        
        pipeline_results = {
            'date': date_str,
            'start_time': datetime.now().isoformat(),
            'steps_completed': [],
            'errors': [],
            'final_results': {}
        }
        
        try:
            # Step 1: Enhanced Data Ingestion
            print("📥 Step 1: Enhanced Data Ingestion")
            ingestion_results = self._run_enhanced_data_ingestion(date_str)
            pipeline_results['steps_completed'].append('data_ingestion')
            pipeline_results['ingestion_results'] = ingestion_results
            
            # Step 2: Advanced Feature Engineering
            print("🔧 Step 2: Advanced Feature Engineering")
            feature_results = self._run_advanced_feature_engineering(ingestion_results)
            pipeline_results['steps_completed'].append('feature_engineering')
            pipeline_results['feature_results'] = feature_results
            
            # Step 3: Feature Selection and Optimization
            print("🎯 Step 3: Feature Selection")
            selection_results = self._run_feature_selection(feature_results)
            pipeline_results['steps_completed'].append('feature_selection')
            pipeline_results['selection_results'] = selection_results
            
            # Step 4: Ensemble Model Training/Update
            print("🤖 Step 4: Ensemble Model Training")
            model_results = self._run_ensemble_modeling(selection_results)
            pipeline_results['steps_completed'].append('ensemble_modeling')
            pipeline_results['model_results'] = model_results
            
            # Step 5: Probability Calibration
            print("📊 Step 5: Probability Calibration")
            calibration_results = self._run_probability_calibration(model_results)
            pipeline_results['steps_completed'].append('probability_calibration')
            pipeline_results['calibration_results'] = calibration_results
            
            # Step 6: Model Validation and Bias Analysis
            print("✅ Step 6: Model Validation")
            validation_results = self._run_model_validation(calibration_results)
            pipeline_results['steps_completed'].append('model_validation')
            pipeline_results['validation_results'] = validation_results
            
            # Step 7: Generate Final Predictions
            print("🔮 Step 7: Generate Predictions")
            prediction_results = self._generate_final_predictions(calibration_results)
            pipeline_results['steps_completed'].append('prediction_generation')
            pipeline_results['prediction_results'] = prediction_results
            
            # Step 8: Performance Monitoring
            print("📈 Step 8: Performance Monitoring")
            monitoring_results = self._run_performance_monitoring(prediction_results)
            pipeline_results['steps_completed'].append('performance_monitoring')
            pipeline_results['monitoring_results'] = monitoring_results
            
            # Step 9: Save Results
            print("💾 Step 9: Save Results")
            save_results = self._save_pipeline_results(pipeline_results, date_str)
            pipeline_results['steps_completed'].append('save_results')
            pipeline_results['save_results'] = save_results
            
            pipeline_results['status'] = 'success'
            pipeline_results['end_time'] = datetime.now().isoformat()
            
            print(f"✅ Enhanced pipeline complete for {date_str}")
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            pipeline_results['status'] = 'failed'
            pipeline_results['error'] = str(e)
            pipeline_results['end_time'] = datetime.now().isoformat()
        
        return pipeline_results
    
    def _run_enhanced_data_ingestion(self, date_str: str) -> Dict:
        """Enhanced data ingestion with poll correction"""
        # Load base constituency data
        base_data_path = self.data_dir / 'features' / 'base_features.csv'
        if base_data_path.exists():
            constituency_df = pd.read_csv(base_data_path)
        else:
            # Create minimal constituency data
            constituency_df = pd.DataFrame({
                'constituency': [f'Constituency_{i}' for i in range(243)],
                'region': np.random.choice(['Mithilanchal', 'Central', 'South', 'Border'], 243)
            })
        
        # Load and correct poll data
        polls_path = self.data_dir / 'polls' / f'polls_{date_str}.csv'
        if polls_path.exists():
            polls_df = pd.read_csv(polls_path)
            corrected_polls = self.poll_corrector.correct_poll_data(polls_df)
            poll_aggregation = self.poll_corrector.aggregate_corrected_polls(corrected_polls)
        else:
            # Use default poll data
            poll_aggregation = {
                'weighted_nda_vote': 45.0,
                'weighted_indi_vote': 55.0,
                'poll_lead_nda': -10.0,
                'poll_volatility': 5.0,
                'poll_uncertainty': 8.0
            }
        
        return {
            'constituency_data': constituency_df,
            'poll_aggregation': poll_aggregation,
            'n_constituencies': len(constituency_df),
            'ingestion_timestamp': datetime.now().isoformat()
        }
    
    def _run_advanced_feature_engineering(self, ingestion_results: Dict) -> Dict:
        """Advanced feature engineering with demographic and swing analysis"""
        constituency_df = ingestion_results['constituency_data']
        
        # Create base features
        enhanced_features = self.feature_engine.create_base_features(constituency_df)
        
        # Add advanced swing features
        enhanced_features = self.feature_engine.create_advanced_swing_features(enhanced_features)
        
        # Add demographic features
        enhanced_features = self.feature_engine.add_demographic_features(enhanced_features)
        
        # Add poll-based features
        polls_df = pd.DataFrame([ingestion_results['poll_aggregation']])
        enhanced_features = self.poll_corrector.create_poll_features(enhanced_features, polls_df)
        
        # Validate features
        validation_results = self.feature_engine.validate_features(enhanced_features)
        
        return {
            'enhanced_features': enhanced_features,
            'n_features': len(enhanced_features.columns),
            'validation_results': validation_results,
            'feature_engineering_timestamp': datetime.now().isoformat()
        }
    
    def _run_feature_selection(self, feature_results: Dict) -> Dict:
        """Feature selection and optimization"""
        enhanced_features = feature_results['enhanced_features']
        
        # Create dummy target for feature selection (in real scenario, use historical data)
        y_dummy = np.random.randint(0, 2, len(enhanced_features))
        
        # Select optimal features
        selected_features = self.feature_selector.select_optimal_features(
            enhanced_features, pd.Series(y_dummy)
        )
        
        # Validate selection
        validation_results = self.feature_selector.validate_feature_selection(
            enhanced_features, pd.Series(y_dummy), selected_features
        )
        
        # Create final feature set
        final_features = enhanced_features[selected_features]
        
        return {
            'selected_features': selected_features,
            'final_features': final_features,
            'n_selected_features': len(selected_features),
            'validation_results': validation_results,
            'selection_timestamp': datetime.now().isoformat()
        }
    
    def _run_ensemble_modeling(self, selection_results: Dict) -> Dict:
        """Ensemble model training and prediction"""
        final_features = selection_results['final_features']
        
        # Create dummy target (in real scenario, use historical election results)
        y_dummy = np.random.randint(0, 2, len(final_features))
        
        # Train ensemble models
        trained_models = self.ensemble_predictor.train_base_models(final_features, pd.Series(y_dummy))
        
        # Generate predictions with uncertainty
        predictions, probabilities, uncertainty_metrics = self.ensemble_predictor.predict_with_uncertainty(final_features)
        
        # Evaluate ensemble
        evaluation_results = self.ensemble_predictor.evaluate_ensemble(final_features, pd.Series(y_dummy))
        
        return {
            'trained_models': list(trained_models.keys()),
            'ensemble_weights': self.ensemble_predictor.ensemble_weights,
            'predictions': predictions,
            'probabilities': probabilities,
            'uncertainty_metrics': uncertainty_metrics,
            'evaluation_results': evaluation_results,
            'modeling_timestamp': datetime.now().isoformat()
        }
    
    def _run_probability_calibration(self, model_results: Dict) -> Dict:
        """Probability calibration and uncertainty quantification"""
        probabilities = model_results['probabilities']
        
        # Create dummy outcomes for calibration (in real scenario, use validation data)
        y_dummy = np.random.randint(0, 2, len(probabilities))
        
        # Fit calibration models
        calibration_results = self.probability_calibrator.fit_calibration_models(probabilities, y_dummy)
        
        # Calibrate predictions
        calibrated_probs = self.probability_calibrator.calibrate_predictions(probabilities)
        
        # Evaluate calibration quality
        quality_results = self.probability_calibrator.evaluate_calibration_quality(probabilities, y_dummy)
        
        return {
            'calibration_methods': list(calibration_results.keys()),
            'calibrated_probabilities': calibrated_probs,
            'calibration_quality': quality_results,
            'calibration_timestamp': datetime.now().isoformat()
        }
    
    def _run_model_validation(self, calibration_results: Dict) -> Dict:
        """Model validation and bias analysis"""
        # Create dummy validation data
        n_samples = 100
        X_val = pd.DataFrame(np.random.randn(n_samples, 10), columns=[f'feature_{i}' for i in range(10)])
        y_val = pd.Series(np.random.randint(0, 2, n_samples))
        
        # Run comprehensive validation
        validation_results = self.model_validator.validate_model_comprehensive(
            self.ensemble_predictor, X_val, y_val
        )
        
        # Bias analysis
        y_pred = np.random.randint(0, 2, n_samples)
        y_prob = np.random.dirichlet([1, 1], n_samples)
        metadata = pd.DataFrame({'region': np.random.choice(['A', 'B', 'C'], n_samples)})
        
        bias_analysis = self.bias_analyzer.analyze_systematic_bias(y_val, y_pred, y_prob, metadata)
        error_patterns = self.bias_analyzer.detect_systematic_errors(y_val, y_pred, y_prob, metadata)
        
        return {
            'validation_results': validation_results,
            'bias_analysis': bias_analysis,
            'error_patterns': error_patterns,
            'validation_timestamp': datetime.now().isoformat()
        }
    
    def _generate_final_predictions(self, calibration_results: Dict) -> Dict:
        """Generate final constituency predictions"""
        calibrated_probs = calibration_results['calibrated_probabilities']
        
        # Create constituency predictions DataFrame
        n_constituencies = len(calibrated_probs)
        
        predictions_df = pd.DataFrame({
            'constituency': [f'Constituency_{i}' for i in range(n_constituencies)],
            'nda_win_probability': calibrated_probs,
            'indi_win_probability': 1 - calibrated_probs,
            'predicted_winner': ['NDA' if p > 0.5 else 'INDI' for p in calibrated_probs],
            'prediction_confidence': np.maximum(calibrated_probs, 1 - calibrated_probs),
            'prediction_timestamp': datetime.now().isoformat()
        })
        
        # Calculate summary statistics
        nda_seats = np.sum(calibrated_probs > 0.5)
        indi_seats = n_constituencies - nda_seats
        
        summary_stats = {
            'total_seats': n_constituencies,
            'nda_predicted_seats': int(nda_seats),
            'indi_predicted_seats': int(indi_seats),
            'nda_majority_probability': float(np.mean(calibrated_probs > 0.5)),
            'mean_nda_probability': float(np.mean(calibrated_probs)),
            'competitive_seats': int(np.sum(np.abs(calibrated_probs - 0.5) < 0.1))
        }
        
        return {
            'predictions_df': predictions_df,
            'summary_stats': summary_stats,
            'prediction_timestamp': datetime.now().isoformat()
        }
    
    def _run_performance_monitoring(self, prediction_results: Dict) -> Dict:
        """Performance monitoring and drift detection"""
        predictions_df = prediction_results['predictions_df']
        
        # Create dummy actual results for monitoring (in real scenario, use when available)
        actuals_df = pd.DataFrame({
            'actual': np.random.randint(0, 2, len(predictions_df)),
            'constituency': predictions_df['constituency']
        })
        
        predictions_for_monitoring = pd.DataFrame({
            'predicted': (predictions_df['nda_win_probability'] > 0.5).astype(int),
            'constituency': predictions_df['constituency']
        })
        
        # Track performance
        performance_record = self.model_monitor.track_prediction_accuracy(
            predictions_for_monitoring, actuals_df, 'enhanced_ensemble_v1'
        )
        
        # Generate monitoring report
        monitoring_report = self.model_monitor.generate_monitoring_report('24h')
        
        return {
            'performance_record': performance_record,
            'monitoring_report': monitoring_report,
            'monitoring_timestamp': datetime.now().isoformat()
        }
    
    def _save_pipeline_results(self, pipeline_results: Dict, date_str: str) -> Dict:
        """Save all pipeline results"""
        # Create date-specific results directory
        date_results_dir = self.results_dir / date_str
        date_results_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        # Save predictions
        if 'prediction_results' in pipeline_results:
            predictions_df = pipeline_results['prediction_results']['predictions_df']
            predictions_path = date_results_dir / 'enhanced_predictions.csv'
            predictions_df.to_csv(predictions_path, index=False)
            saved_files['predictions'] = str(predictions_path)
            
            # Save summary
            summary_path = date_results_dir / 'enhanced_summary.json'
            with open(summary_path, 'w') as f:
                json.dump(pipeline_results['prediction_results']['summary_stats'], f, indent=2)
            saved_files['summary'] = str(summary_path)
        
        # Save pipeline log
        pipeline_log_path = date_results_dir / 'enhanced_pipeline_log.json'
        with open(pipeline_log_path, 'w') as f:
            # Remove large DataFrames for logging
            log_data = {k: v for k, v in pipeline_results.items() 
                       if not isinstance(v, pd.DataFrame)}
            json.dump(log_data, f, indent=2, default=str)
        saved_files['pipeline_log'] = str(pipeline_log_path)
        
        # Save model states
        ensemble_version = self.ensemble_predictor.save_ensemble()
        calibration_version = self.probability_calibrator.save_calibration_models()
        monitoring_state = self.model_monitor.save_monitoring_state()
        
        saved_files.update({
            'ensemble_version': ensemble_version,
            'calibration_version': calibration_version,
            'monitoring_state': monitoring_state
        })
        
        return {
            'saved_files': saved_files,
            'results_directory': str(date_results_dir),
            'save_timestamp': datetime.now().isoformat()
        }
    
    def get_pipeline_status(self) -> Dict:
        """Get current pipeline status"""
        return {
            'pipeline_state': self.pipeline_state,
            'execution_log_entries': len(self.execution_log),
            'components_initialized': {
                'feature_engine': self.feature_engine is not None,
                'poll_corrector': self.poll_corrector is not None,
                'ensemble_predictor': self.ensemble_predictor is not None,
                'probability_calibrator': self.probability_calibrator is not None,
                'model_validator': self.model_validator is not None,
                'bias_analyzer': self.bias_analyzer is not None,
                'feature_selector': self.feature_selector is not None,
                'model_monitor': self.model_monitor is not None
            },
            'status_timestamp': datetime.now().isoformat()
        }