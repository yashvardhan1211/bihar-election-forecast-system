import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from src.config.settings import Config
import json
import warnings
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from scipy import stats
import logging

warnings.filterwarnings('ignore')

class ModelMonitor:
    """Real-time model performance monitoring with A/B testing and automated rollback"""
    
    def __init__(self):
        self.results_dir = Config.RESULTS_DIR
        self.monitoring_dir = self.results_dir / 'monitoring'
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.performance_history = []
        self.current_experiments = {}
        self.alert_thresholds = {
            'accuracy_drop': 0.05,
            'drift_threshold': 0.1,
            'min_samples': 50
        }
        
        # Model versions
        self.model_versions = {}
        self.active_model = None
        
        self.logger = logging.getLogger(__name__)
        print(f"✅ Model Monitor initialized")
    
    def setup_ab_test(self, model_a: Any, model_b: Any, traffic_split: float = 0.5,
                     test_name: str = None) -> str:
        """Set up A/B test between two models"""
        if test_name is None:
            test_name = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"🔄 Setting up A/B test: {test_name}")
        
        experiment = {
            'test_name': test_name,
            'model_a': model_a,
            'model_b': model_b,
            'traffic_split': traffic_split,
            'start_time': datetime.now().isoformat(),
            'status': 'active',
            'results_a': [],
            'results_b': [],
            'metadata': {
                'model_a_type': type(model_a).__name__,
                'model_b_type': type(model_b).__name__
            }
        }
        
        self.current_experiments[test_name] = experiment
        
        print(f"✅ A/B test setup complete: {traffic_split:.0%} traffic to model A")
        return test_name
    
    def track_prediction_accuracy(self, predictions: pd.DataFrame, 
                                actuals: pd.DataFrame, model_version: str = None) -> Dict:
        """Track prediction accuracy in real-time"""
        print("🔄 Tracking prediction accuracy...")
        
        if model_version is None:
            model_version = 'default'
        
        # Calculate metrics
        accuracy = accuracy_score(actuals['actual'], predictions['predicted'])
        precision = precision_score(actuals['actual'], predictions['predicted'], average='weighted')
        recall = recall_score(actuals['actual'], predictions['predicted'], average='weighted')
        f1 = f1_score(actuals['actual'], predictions['predicted'], average='weighted')
        
        # Create performance record
        performance_record = {
            'timestamp': datetime.now().isoformat(),
            'model_version': model_version,
            'n_predictions': len(predictions),
            'metrics': {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            },
            'prediction_distribution': {
                'predicted_positive': int(predictions['predicted'].sum()),
                'actual_positive': int(actuals['actual'].sum())
            }
        }
        
        # Store in history
        self.performance_history.append(performance_record)
        
        # Check for performance degradation
        drift_detected = self.detect_performance_drift([accuracy], accuracy)
        
        if drift_detected:
            self.logger.warning(f"Performance drift detected for {model_version}")
            performance_record['drift_alert'] = True
        
        print(f"✅ Performance tracked: {accuracy:.3f} accuracy")
        return performance_record
    
    def detect_performance_drift(self, recent_scores: List[float], 
                               baseline: float, window_size: int = 10) -> bool:
        """Detect performance drift using statistical tests"""
        if len(recent_scores) < self.alert_thresholds['min_samples']:
            return False
        
        # Use recent window for comparison
        recent_window = recent_scores[-window_size:] if len(recent_scores) >= window_size else recent_scores
        
        # Statistical test for drift
        if len(recent_window) >= 5:
            # One-sample t-test against baseline
            t_stat, p_value = stats.ttest_1samp(recent_window, baseline)
            
            # Check for significant degradation
            mean_recent = np.mean(recent_window)
            drift_magnitude = baseline - mean_recent
            
            # Drift detected if significant drop and magnitude exceeds threshold
            drift_detected = (p_value < 0.05 and 
                            drift_magnitude > self.alert_thresholds['accuracy_drop'])
            
            return drift_detected
        
        return False
    
    def run_ab_test_analysis(self, test_name: str, X_test: pd.DataFrame, 
                           y_test: pd.Series) -> Dict:
        """Run A/B test analysis and determine winner"""
        if test_name not in self.current_experiments:
            raise ValueError(f"A/B test {test_name} not found")
        
        print(f"🔄 Running A/B test analysis: {test_name}")
        
        experiment = self.current_experiments[test_name]
        model_a = experiment['model_a']
        model_b = experiment['model_b']
        
        # Generate predictions from both models
        pred_a = model_a.predict(X_test)
        pred_b = model_b.predict(X_test)
        
        # Calculate metrics for both models
        metrics_a = {
            'accuracy': accuracy_score(y_test, pred_a),
            'precision': precision_score(y_test, pred_a, average='weighted'),
            'recall': recall_score(y_test, pred_a, average='weighted'),
            'f1_score': f1_score(y_test, pred_a, average='weighted')
        }
        
        metrics_b = {
            'accuracy': accuracy_score(y_test, pred_b),
            'precision': precision_score(y_test, pred_b, average='weighted'),
            'recall': recall_score(y_test, pred_b, average='weighted'),
            'f1_score': f1_score(y_test, pred_b, average='weighted')
        }
        
        # Statistical significance testing
        significance_results = self._test_statistical_significance(
            pred_a, pred_b, y_test
        )
        
        # Determine winner
        primary_metric = 'accuracy'
        winner = 'model_a' if metrics_a[primary_metric] > metrics_b[primary_metric] else 'model_b'
        
        # Calculate confidence in winner
        performance_diff = abs(metrics_a[primary_metric] - metrics_b[primary_metric])
        confidence = min(0.99, performance_diff / 0.1)  # Normalize to confidence score
        
        ab_results = {
            'test_name': test_name,
            'winner': winner,
            'confidence': confidence,
            'model_a_metrics': metrics_a,
            'model_b_metrics': metrics_b,
            'performance_difference': metrics_b[primary_metric] - metrics_a[primary_metric],
            'statistical_significance': significance_results,
            'test_samples': len(X_test),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Update experiment status
        experiment['status'] = 'completed'
        experiment['results'] = ab_results
        
        print(f"✅ A/B test analysis complete: {winner} wins with {confidence:.1%} confidence")
        return ab_results
    
    def _test_statistical_significance(self, pred_a: np.ndarray, pred_b: np.ndarray,
                                     y_true: np.ndarray) -> Dict:
        """Test statistical significance between model predictions"""
        # Calculate per-sample accuracy
        correct_a = (pred_a == y_true).astype(int)
        correct_b = (pred_b == y_true).astype(int)
        
        # Paired t-test
        t_stat, p_value = stats.ttest_rel(correct_a, correct_b)
        
        # McNemar's test for paired binary outcomes
        # Create contingency table
        both_correct = np.sum((correct_a == 1) & (correct_b == 1))
        a_correct_b_wrong = np.sum((correct_a == 1) & (correct_b == 0))
        a_wrong_b_correct = np.sum((correct_a == 0) & (correct_b == 1))
        both_wrong = np.sum((correct_a == 0) & (correct_b == 0))
        
        # McNemar's test statistic
        if a_correct_b_wrong + a_wrong_b_correct > 0:
            mcnemar_stat = ((abs(a_correct_b_wrong - a_wrong_b_correct) - 1) ** 2) / (a_correct_b_wrong + a_wrong_b_correct)
            mcnemar_p = 1 - stats.chi2.cdf(mcnemar_stat, 1)
        else:
            mcnemar_stat = 0
            mcnemar_p = 1.0
        
        return {
            'paired_t_test': {
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            },
            'mcnemar_test': {
                'statistic': mcnemar_stat,
                'p_value': mcnemar_p,
                'significant': mcnemar_p < 0.05
            },
            'contingency_table': {
                'both_correct': int(both_correct),
                'a_correct_b_wrong': int(a_correct_b_wrong),
                'a_wrong_b_correct': int(a_wrong_b_correct),
                'both_wrong': int(both_wrong)
            }
        }
    
    def trigger_model_rollback(self, reason: str, target_version: str = None) -> bool:
        """Trigger automated model rollback"""
        print(f"🔄 Triggering model rollback: {reason}")
        
        if target_version is None:
            # Rollback to previous stable version
            if len(self.model_versions) < 2:
                self.logger.error("No previous version available for rollback")
                return False
            
            # Get second most recent version
            sorted_versions = sorted(self.model_versions.keys(), reverse=True)
            target_version = sorted_versions[1]
        
        if target_version not in self.model_versions:
            self.logger.error(f"Target version {target_version} not found")
            return False
        
        # Perform rollback
        try:
            self.active_model = target_version
            
            # Log rollback event
            rollback_event = {
                'timestamp': datetime.now().isoformat(),
                'reason': reason,
                'rolled_back_to': target_version,
                'triggered_by': 'automated_monitor'
            }
            
            self._log_rollback_event(rollback_event)
            
            print(f"✅ Model rollback successful to version {target_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False
    
    def _log_rollback_event(self, rollback_event: Dict) -> None:
        """Log rollback event to file"""
        rollback_log_path = self.monitoring_dir / 'rollback_log.json'
        
        # Load existing log or create new
        if rollback_log_path.exists():
            with open(rollback_log_path) as f:
                rollback_log = json.load(f)
        else:
            rollback_log = []
        
        # Add new event
        rollback_log.append(rollback_event)
        
        # Save updated log
        with open(rollback_log_path, 'w') as f:
            json.dump(rollback_log, f, indent=2)
    
    def generate_monitoring_report(self, period: str = '24h') -> Dict:
        """Generate comprehensive monitoring report"""
        print(f"🔄 Generating monitoring report for {period}...")
        
        # Parse period
        if period == '24h':
            cutoff_time = datetime.now() - timedelta(hours=24)
        elif period == '7d':
            cutoff_time = datetime.now() - timedelta(days=7)
        elif period == '30d':
            cutoff_time = datetime.now() - timedelta(days=30)
        else:
            cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Filter performance history
        recent_performance = [
            record for record in self.performance_history
            if datetime.fromisoformat(record['timestamp']) >= cutoff_time
        ]
        
        if not recent_performance:
            return {'error': f'No performance data available for period {period}'}
        
        # Calculate summary statistics
        accuracies = [record['metrics']['accuracy'] for record in recent_performance]
        
        summary_stats = {
            'period': period,
            'total_predictions': sum(record['n_predictions'] for record in recent_performance),
            'mean_accuracy': np.mean(accuracies),
            'std_accuracy': np.std(accuracies),
            'min_accuracy': np.min(accuracies),
            'max_accuracy': np.max(accuracies),
            'accuracy_trend': self._calculate_trend(accuracies)
        }
        
        # Active experiments summary
        active_experiments = {
            name: {
                'status': exp['status'],
                'start_time': exp['start_time'],
                'traffic_split': exp['traffic_split']
            }
            for name, exp in self.current_experiments.items()
            if exp['status'] == 'active'
        }
        
        # Alert summary
        alerts = [
            record for record in recent_performance
            if record.get('drift_alert', False)
        ]
        
        monitoring_report = {
            'report_period': period,
            'summary_statistics': summary_stats,
            'active_experiments': active_experiments,
            'alerts': {
                'drift_alerts': len(alerts),
                'alert_details': alerts[-5:]  # Last 5 alerts
            },
            'model_versions': {
                'active_model': self.active_model,
                'available_versions': list(self.model_versions.keys())
            },
            'generated_at': datetime.now().isoformat()
        }
        
        print(f"✅ Monitoring report generated: {len(recent_performance)} records analyzed")
        return monitoring_report
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from time series values"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple linear regression to determine trend
        x = np.arange(len(values))
        slope, _, _, p_value, _ = stats.linregress(x, values)
        
        if p_value > 0.05:
            return 'stable'
        elif slope > 0:
            return 'improving'
        else:
            return 'declining'
    
    def save_monitoring_state(self, filename: str = None) -> str:
        """Save monitoring state to file"""
        if filename is None:
            filename = f"monitoring_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.monitoring_dir / filename
        
        monitoring_state = {
            'performance_history': self.performance_history[-100:],  # Keep last 100 records
            'current_experiments': self.current_experiments,
            'alert_thresholds': self.alert_thresholds,
            'model_versions': self.model_versions,
            'active_model': self.active_model,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(monitoring_state, f, indent=2)
        
        print(f"✅ Monitoring state saved to {filepath}")
        return str(filepath)
    
    def load_monitoring_state(self, filepath: str) -> bool:
        """Load monitoring state from file"""
        try:
            with open(filepath) as f:
                monitoring_state = json.load(f)
            
            self.performance_history = monitoring_state.get('performance_history', [])
            self.current_experiments = monitoring_state.get('current_experiments', {})
            self.alert_thresholds = monitoring_state.get('alert_thresholds', self.alert_thresholds)
            self.model_versions = monitoring_state.get('model_versions', {})
            self.active_model = monitoring_state.get('active_model')
            
            print(f"✅ Monitoring state loaded: {len(self.performance_history)} performance records")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load monitoring state: {e}")
            return False
    
    def register_model_version(self, model: Any, version: str, metadata: Dict = None) -> None:
        """Register a new model version"""
        self.model_versions[version] = {
            'model': model,
            'registered_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        if self.active_model is None:
            self.active_model = version
        
        print(f"✅ Model version {version} registered")
    
    def get_monitoring_summary(self) -> Dict:
        """Get summary of monitoring system state"""
        return {
            'performance_records': len(self.performance_history),
            'active_experiments': len([exp for exp in self.current_experiments.values() 
                                     if exp['status'] == 'active']),
            'total_experiments': len(self.current_experiments),
            'model_versions': len(self.model_versions),
            'active_model': self.active_model,
            'alert_thresholds': self.alert_thresholds
        }