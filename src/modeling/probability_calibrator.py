import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from src.config.settings import Config
import json
import warnings
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.metrics import brier_score_loss, log_loss
from scipy.optimize import minimize_scalar
import logging

warnings.filterwarnings('ignore')

class ProbabilityCalibrator:
    """Advanced probability calibration system with multiple methods and constituency-specific adjustments"""
    
    def __init__(self):
        self.models_dir = Config.MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Calibration models
        self.platt_calibrator = None
        self.isotonic_calibrator = None
        self.temperature_scaler = None
        
        # Constituency-specific calibrators
        self.constituency_calibrators = {}
        
        # Calibration metadata
        self.calibration_metadata = {}
        self.calibration_quality = {}
        
        self.logger = logging.getLogger(__name__)
        print(f"✅ Probability Calibrator initialized")
    
    def fit_calibration_models(self, probabilities: np.ndarray, outcomes: np.ndarray,
                             methods: List[str] = None) -> Dict:
        """Fit multiple calibration models"""
        print("🔄 Fitting calibration models...")
        
        if methods is None:
            methods = ['platt', 'isotonic', 'temperature']
        
        calibration_results = {}
        
        # Ensure probabilities are for positive class
        if probabilities.ndim > 1:
            probs = probabilities[:, 1]  # Assuming binary classification
        else:
            probs = probabilities
        
        # Platt Scaling
        if 'platt' in methods:
            try:
                self.platt_calibrator = self._fit_platt_scaling(probs, outcomes)
                calibration_results['platt'] = {'status': 'success'}
                print("   Platt scaling fitted")
            except Exception as e:
                self.logger.error(f"Platt scaling failed: {e}")
                calibration_results['platt'] = {'status': 'failed', 'error': str(e)}
        
        # Isotonic Regression
        if 'isotonic' in methods:
            try:
                self.isotonic_calibrator = self._fit_isotonic_regression(probs, outcomes)
                calibration_results['isotonic'] = {'status': 'success'}
                print("   Isotonic regression fitted")
            except Exception as e:
                self.logger.error(f"Isotonic regression failed: {e}")
                calibration_results['isotonic'] = {'status': 'failed', 'error': str(e)}
        
        # Temperature Scaling
        if 'temperature' in methods:
            try:
                self.temperature_scaler = self._fit_temperature_scaling(probs, outcomes)
                calibration_results['temperature'] = {'status': 'success', 'temperature': self.temperature_scaler}
                print(f"   Temperature scaling fitted: T = {self.temperature_scaler:.3f}")
            except Exception as e:
                self.logger.error(f"Temperature scaling failed: {e}")
                calibration_results['temperature'] = {'status': 'failed', 'error': str(e)}
        
        # Store metadata
        self.calibration_metadata = {
            'fitted_methods': [method for method, result in calibration_results.items() 
                             if result['status'] == 'success'],
            'training_samples': len(probabilities),
            'positive_rate': np.mean(outcomes),
            'fitted_at': datetime.now().isoformat()
        }
        
        print(f"✅ Calibration models fitted: {len(self.calibration_metadata['fitted_methods'])} methods")
        return calibration_results
    
    def _fit_platt_scaling(self, probabilities: np.ndarray, outcomes: np.ndarray) -> LogisticRegression:
        """Fit Platt scaling (sigmoid calibration)"""
        # Convert probabilities to logits
        epsilon = 1e-15
        probs_clipped = np.clip(probabilities, epsilon, 1 - epsilon)
        logits = np.log(probs_clipped / (1 - probs_clipped))
        
        # Fit logistic regression
        platt_model = LogisticRegression()
        platt_model.fit(logits.reshape(-1, 1), outcomes)
        
        return platt_model
    
    def _fit_isotonic_regression(self, probabilities: np.ndarray, outcomes: np.ndarray) -> IsotonicRegression:
        """Fit isotonic regression calibration"""
        isotonic_model = IsotonicRegression(out_of_bounds='clip')
        isotonic_model.fit(probabilities, outcomes)
        
        return isotonic_model
    
    def _fit_temperature_scaling(self, probabilities: np.ndarray, outcomes: np.ndarray) -> float:
        """Fit temperature scaling parameter"""
        # Convert probabilities to logits
        epsilon = 1e-15
        probs_clipped = np.clip(probabilities, epsilon, 1 - epsilon)
        logits = np.log(probs_clipped / (1 - probs_clipped))
        
        # Optimize temperature parameter
        def temperature_loss(temperature):
            if temperature <= 0:
                return np.inf
            
            calibrated_probs = 1 / (1 + np.exp(-logits / temperature))
            return log_loss(outcomes, calibrated_probs)
        
        # Find optimal temperature
        result = minimize_scalar(temperature_loss, bounds=(0.1, 10.0), method='bounded')
        
        return result.x
    
    def calibrate_predictions(self, raw_probabilities: np.ndarray, 
                            method: str = 'best') -> np.ndarray:
        """Calibrate predictions using specified method"""
        if raw_probabilities.ndim > 1:
            probs = raw_probabilities[:, 1]  # Positive class probabilities
        else:
            probs = raw_probabilities
        
        if method == 'best':
            method = self._select_best_calibration_method()
        
        if method == 'platt' and self.platt_calibrator is not None:
            return self._apply_platt_scaling(probs)
        elif method == 'isotonic' and self.isotonic_calibrator is not None:
            return self._apply_isotonic_regression(probs)
        elif method == 'temperature' and self.temperature_scaler is not None:
            return self._apply_temperature_scaling(probs)
        else:
            self.logger.warning(f"Calibration method {method} not available, returning raw probabilities")
            return probs
    
    def _apply_platt_scaling(self, probabilities: np.ndarray) -> np.ndarray:
        """Apply Platt scaling to probabilities"""
        epsilon = 1e-15
        probs_clipped = np.clip(probabilities, epsilon, 1 - epsilon)
        logits = np.log(probs_clipped / (1 - probs_clipped))
        
        calibrated_probs = self.platt_calibrator.predict_proba(logits.reshape(-1, 1))[:, 1]
        return calibrated_probs
    
    def _apply_isotonic_regression(self, probabilities: np.ndarray) -> np.ndarray:
        """Apply isotonic regression to probabilities"""
        calibrated_probs = self.isotonic_calibrator.predict(probabilities)
        return calibrated_probs
    
    def _apply_temperature_scaling(self, probabilities: np.ndarray) -> np.ndarray:
        """Apply temperature scaling to probabilities"""
        epsilon = 1e-15
        probs_clipped = np.clip(probabilities, epsilon, 1 - epsilon)
        logits = np.log(probs_clipped / (1 - probs_clipped))
        
        calibrated_logits = logits / self.temperature_scaler
        calibrated_probs = 1 / (1 + np.exp(-calibrated_logits))
        
        return calibrated_probs
    
    def _select_best_calibration_method(self) -> str:
        """Select best calibration method based on quality metrics"""
        if not self.calibration_quality:
            return 'isotonic'  # Default fallback
        
        # Select method with lowest Brier score
        best_method = min(self.calibration_quality.keys(), 
                         key=lambda k: self.calibration_quality[k].get('brier_score', np.inf))
        
        return best_method
    
    def evaluate_calibration_quality(self, probabilities: np.ndarray, outcomes: np.ndarray,
                                   methods: List[str] = None) -> Dict:
        """Evaluate calibration quality for different methods"""
        print("🔄 Evaluating calibration quality...")
        
        if methods is None:
            methods = ['platt', 'isotonic', 'temperature']
        
        quality_results = {}
        
        for method in methods:
            try:
                calibrated_probs = self.calibrate_predictions(probabilities, method)
                
                # Calculate calibration metrics
                brier_score = brier_score_loss(outcomes, calibrated_probs)
                log_loss_score = log_loss(outcomes, calibrated_probs)
                
                # Reliability diagram metrics
                reliability_metrics = self._calculate_reliability_metrics(calibrated_probs, outcomes)
                
                quality_results[method] = {
                    'brier_score': brier_score,
                    'log_loss': log_loss_score,
                    **reliability_metrics
                }
                
            except Exception as e:
                self.logger.error(f"Calibration evaluation failed for {method}: {e}")
                quality_results[method] = {'error': str(e)}
        
        self.calibration_quality = quality_results
        
        print(f"✅ Calibration quality evaluated for {len(quality_results)} methods")
        return quality_results
    
    def _calculate_reliability_metrics(self, probabilities: np.ndarray, 
                                     outcomes: np.ndarray, n_bins: int = 10) -> Dict:
        """Calculate reliability diagram metrics"""
        try:
            fraction_of_positives, mean_predicted_value = calibration_curve(
                outcomes, probabilities, n_bins=n_bins
            )
            
            # Calibration error (Expected Calibration Error)
            bin_boundaries = np.linspace(0, 1, n_bins + 1)
            bin_lowers = bin_boundaries[:-1]
            bin_uppers = bin_boundaries[1:]
            
            ece = 0
            for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
                in_bin = (probabilities > bin_lower) & (probabilities <= bin_upper)
                prop_in_bin = in_bin.mean()
                
                if prop_in_bin > 0:
                    accuracy_in_bin = outcomes[in_bin].mean()
                    avg_confidence_in_bin = probabilities[in_bin].mean()
                    ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
            
            # Reliability (1 - calibration error)
            reliability = 1 - ece
            
            # Resolution (ability to separate classes)
            base_rate = np.mean(outcomes)
            resolution = np.sum((mean_predicted_value - base_rate) ** 2 * 
                              np.histogram(probabilities, bins=n_bins)[0]) / len(probabilities)
            
            return {
                'expected_calibration_error': ece,
                'reliability': reliability,
                'resolution': resolution,
                'calibration_curve_points': {
                    'fraction_of_positives': fraction_of_positives.tolist(),
                    'mean_predicted_value': mean_predicted_value.tolist()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Reliability metrics calculation failed: {e}")
            return {'error': str(e)}
    
    def fit_constituency_specific_calibration(self, probabilities: np.ndarray, 
                                            outcomes: np.ndarray, 
                                            constituency_ids: np.ndarray) -> Dict:
        """Fit constituency-specific calibration adjustments"""
        print("🔄 Fitting constituency-specific calibration...")
        
        constituency_results = {}
        
        for constituency in np.unique(constituency_ids):
            constituency_mask = constituency_ids == constituency
            
            if np.sum(constituency_mask) < 5:  # Minimum sample size
                continue
            
            const_probs = probabilities[constituency_mask]
            const_outcomes = outcomes[constituency_mask]
            
            try:
                # Fit simple isotonic regression for this constituency
                const_calibrator = IsotonicRegression(out_of_bounds='clip')
                const_calibrator.fit(const_probs, const_outcomes)
                
                # Evaluate constituency-specific calibration
                calibrated_probs = const_calibrator.predict(const_probs)
                brier_score = brier_score_loss(const_outcomes, calibrated_probs)
                
                self.constituency_calibrators[constituency] = const_calibrator
                constituency_results[constituency] = {
                    'samples': int(np.sum(constituency_mask)),
                    'brier_score': brier_score,
                    'fitted': True
                }
                
            except Exception as e:
                self.logger.error(f"Constituency calibration failed for {constituency}: {e}")
                constituency_results[constituency] = {'error': str(e), 'fitted': False}
        
        print(f"✅ Constituency-specific calibration fitted for {len(self.constituency_calibrators)} constituencies")
        return constituency_results
    
    def apply_constituency_calibration(self, probabilities: np.ndarray,
                                     constituency_ids: np.ndarray) -> np.ndarray:
        """Apply constituency-specific calibration adjustments"""
        calibrated_probs = probabilities.copy()
        
        for i, constituency in enumerate(constituency_ids):
            if constituency in self.constituency_calibrators:
                calibrator = self.constituency_calibrators[constituency]
                calibrated_probs[i] = calibrator.predict([probabilities[i]])[0]
        
        return calibrated_probs
    
    def generate_reliability_diagram(self, probabilities: np.ndarray, outcomes: np.ndarray,
                                   method: str = 'isotonic', n_bins: int = 10) -> Dict:
        """Generate reliability diagram data"""
        print(f"🔄 Generating reliability diagram for {method} calibration...")
        
        # Get calibrated probabilities
        calibrated_probs = self.calibrate_predictions(probabilities, method)
        
        # Calculate calibration curve
        fraction_of_positives, mean_predicted_value = calibration_curve(
            outcomes, calibrated_probs, n_bins=n_bins
        )
        
        # Calculate bin statistics
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_stats = []
        
        for i in range(n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]
            
            in_bin = (calibrated_probs >= bin_lower) & (calibrated_probs < bin_upper)
            if i == n_bins - 1:  # Include upper boundary for last bin
                in_bin = (calibrated_probs >= bin_lower) & (calibrated_probs <= bin_upper)
            
            if np.sum(in_bin) > 0:
                bin_stats.append({
                    'bin_lower': bin_lower,
                    'bin_upper': bin_upper,
                    'count': int(np.sum(in_bin)),
                    'mean_predicted': float(np.mean(calibrated_probs[in_bin])),
                    'fraction_positive': float(np.mean(outcomes[in_bin])),
                    'confidence_interval': self._calculate_confidence_interval(outcomes[in_bin])
                })
        
        reliability_diagram = {
            'method': method,
            'n_bins': n_bins,
            'bin_statistics': bin_stats,
            'calibration_curve': {
                'fraction_of_positives': fraction_of_positives.tolist(),
                'mean_predicted_value': mean_predicted_value.tolist()
            },
            'perfect_calibration_line': [0, 1],  # y = x line
            'generated_at': datetime.now().isoformat()
        }
        
        print(f"✅ Reliability diagram generated with {len(bin_stats)} bins")
        return reliability_diagram
    
    def _calculate_confidence_interval(self, binary_outcomes: np.ndarray, 
                                     confidence_level: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for binary proportion"""
        n = len(binary_outcomes)
        p = np.mean(binary_outcomes)
        
        if n == 0:
            return (0.0, 0.0)
        
        # Wilson score interval
        z = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
        
        denominator = 1 + z**2 / n
        centre_adjusted_probability = (p + z**2 / (2 * n)) / denominator
        adjusted_standard_deviation = np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
        
        lower_bound = centre_adjusted_probability - z * adjusted_standard_deviation
        upper_bound = centre_adjusted_probability + z * adjusted_standard_deviation
        
        return (max(0.0, lower_bound), min(1.0, upper_bound))
    
    def save_calibration_models(self, version: str = None) -> str:
        """Save calibration models and metadata"""
        if version is None:
            version = f"calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create version directory
        version_dir = self.models_dir / version
        version_dir.mkdir(exist_ok=True)
        
        # Save calibration models
        saved_models = {}
        
        if self.platt_calibrator is not None:
            platt_path = version_dir / 'platt_calibrator.joblib'
            import joblib
            joblib.dump(self.platt_calibrator, platt_path)
            saved_models['platt'] = str(platt_path)
        
        if self.isotonic_calibrator is not None:
            isotonic_path = version_dir / 'isotonic_calibrator.joblib'
            import joblib
            joblib.dump(self.isotonic_calibrator, isotonic_path)
            saved_models['isotonic'] = str(isotonic_path)
        
        if self.temperature_scaler is not None:
            temp_path = version_dir / 'temperature_scaler.json'
            with open(temp_path, 'w') as f:
                json.dump({'temperature': self.temperature_scaler}, f)
            saved_models['temperature'] = str(temp_path)
        
        # Save constituency calibrators
        if self.constituency_calibrators:
            const_path = version_dir / 'constituency_calibrators.joblib'
            import joblib
            joblib.dump(self.constituency_calibrators, const_path)
            saved_models['constituency'] = str(const_path)
        
        # Save metadata
        metadata = {
            'version': version,
            'saved_at': datetime.now().isoformat(),
            'calibration_metadata': self.calibration_metadata,
            'calibration_quality': self.calibration_quality,
            'saved_models': saved_models,
            'n_constituency_calibrators': len(self.constituency_calibrators)
        }
        
        metadata_path = version_dir / 'calibration_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Calibration models saved as version {version}")
        return version
    
    def load_calibration_models(self, version: str) -> bool:
        """Load calibration models and metadata"""
        print(f"🔄 Loading calibration models version {version}...")
        
        version_dir = self.models_dir / version
        if not version_dir.exists():
            raise FileNotFoundError(f"Calibration version {version} not found")
        
        # Load metadata
        metadata_path = version_dir / 'calibration_metadata.json'
        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)
            
            self.calibration_metadata = metadata.get('calibration_metadata', {})
            self.calibration_quality = metadata.get('calibration_quality', {})
            saved_models = metadata.get('saved_models', {})
        else:
            saved_models = {}
        
        # Load individual calibrators
        import joblib
        
        if 'platt' in saved_models:
            self.platt_calibrator = joblib.load(saved_models['platt'])
        
        if 'isotonic' in saved_models:
            self.isotonic_calibrator = joblib.load(saved_models['isotonic'])
        
        if 'temperature' in saved_models:
            with open(saved_models['temperature']) as f:
                temp_data = json.load(f)
            self.temperature_scaler = temp_data['temperature']
        
        if 'constituency' in saved_models:
            self.constituency_calibrators = joblib.load(saved_models['constituency'])
        
        print(f"✅ Calibration models loaded: {len(saved_models)} components")
        return True
    
    def get_calibration_summary(self) -> Dict:
        """Get summary of calibration state"""
        return {
            'fitted_methods': self.calibration_metadata.get('fitted_methods', []),
            'calibration_quality': self.calibration_quality,
            'n_constituency_calibrators': len(self.constituency_calibrators),
            'best_method': self._select_best_calibration_method(),
            'last_fitted': self.calibration_metadata.get('fitted_at', 'never')
        }