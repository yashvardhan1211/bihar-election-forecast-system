import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from src.config.settings import Config
import json
import warnings
from scipy import stats
from scipy.special import logsumexp
from sklearn.model_selection import cross_val_score
from sklearn.metrics import log_loss, brier_score_loss
import logging

warnings.filterwarnings('ignore')

class BayesianEnsemble:
    """Bayesian model averaging with uncertainty quantification for ensemble predictions"""
    
    def __init__(self):
        self.models_dir = Config.MODELS_DIR
        
        # Bayesian parameters
        self.model_priors = {}
        self.model_posteriors = {}
        self.evidence_weights = {}
        
        # Uncertainty quantification
        self.epistemic_uncertainty = {}  # Model uncertainty
        self.aleatoric_uncertainty = {}  # Data uncertainty
        
        # Performance tracking
        self.model_likelihoods = {}
        self.bayesian_weights = {}
        
        self.logger = logging.getLogger(__name__)
        print(f"✅ Bayesian Ensemble initialized")
    
    def set_model_priors(self, model_names: List[str], prior_type: str = 'uniform') -> None:
        """Set prior probabilities for models"""
        print(f"🔄 Setting {prior_type} priors for {len(model_names)} models...")
        
        if prior_type == 'uniform':
            # Equal prior probability for all models
            prior_prob = 1.0 / len(model_names)
            self.model_priors = {name: prior_prob for name in model_names}
            
        elif prior_type == 'performance_based':
            # Priors based on expected performance (can be updated with historical data)
            performance_priors = {
                'random_forest': 0.35,
                'xgboost': 0.40,
                'logistic_regression': 0.25
            }
            
            # Normalize to ensure sum = 1
            total_prior = sum(performance_priors.get(name, 0.33) for name in model_names)
            self.model_priors = {
                name: performance_priors.get(name, 0.33) / total_prior 
                for name in model_names
            }
            
        elif prior_type == 'complexity_based':
            # Priors favoring simpler models (Occam's razor)
            complexity_priors = {
                'logistic_regression': 0.5,  # Simplest
                'random_forest': 0.3,        # Medium complexity
                'xgboost': 0.2               # Most complex
            }
            
            total_prior = sum(complexity_priors.get(name, 0.33) for name in model_names)
            self.model_priors = {
                name: complexity_priors.get(name, 0.33) / total_prior 
                for name in model_names
            }
        
        print(f"   Model priors: {self.model_priors}")
    
    def calculate_model_evidence(self, model_predictions: Dict, model_probabilities: Dict,
                               y_true: np.ndarray) -> Dict[str, float]:
        """Calculate marginal likelihood (evidence) for each model"""
        print("🔄 Calculating model evidence...")
        
        evidence_scores = {}
        
        for model_name in model_predictions.keys():
            try:
                # Get model probabilities
                probs = model_probabilities[model_name]
                
                # Calculate log-likelihood
                log_likelihood = self._calculate_log_likelihood(probs, y_true)
                
                # Add prior
                prior = self.model_priors.get(model_name, 1.0 / len(model_predictions))
                log_prior = np.log(prior)
                
                # Evidence = likelihood * prior (in log space: log_likelihood + log_prior)
                log_evidence = log_likelihood + log_prior
                evidence_scores[model_name] = log_evidence
                
                print(f"   {model_name}: log_evidence = {log_evidence:.3f}")
                
            except Exception as e:
                self.logger.error(f"Error calculating evidence for {model_name}: {e}")
                evidence_scores[model_name] = -np.inf
        
        self.evidence_weights = evidence_scores
        return evidence_scores
    
    def _calculate_log_likelihood(self, probabilities: np.ndarray, y_true: np.ndarray) -> float:
        """Calculate log-likelihood of predictions given true labels"""
        # Ensure probabilities are valid
        probabilities = np.clip(probabilities, 1e-15, 1 - 1e-15)
        
        # Calculate log-likelihood
        n_samples = len(y_true)
        log_likelihood = 0.0
        
        for i in range(n_samples):
            true_class = int(y_true[i])
            pred_prob = probabilities[i, true_class]
            log_likelihood += np.log(pred_prob)
        
        return log_likelihood
    
    def update_bayesian_weights(self, evidence_scores: Dict[str, float]) -> Dict[str, float]:
        """Update Bayesian model weights using evidence"""
        print("🔄 Updating Bayesian weights...")
        
        # Convert log evidence to weights using softmax
        log_evidences = np.array(list(evidence_scores.values()))
        model_names = list(evidence_scores.keys())
        
        # Numerical stability: subtract max log evidence
        log_evidences_stable = log_evidences - np.max(log_evidences)
        
        # Calculate normalized weights
        weights = np.exp(log_evidences_stable)
        weights = weights / np.sum(weights)
        
        # Create weight dictionary
        bayesian_weights = dict(zip(model_names, weights))
        
        print("   Bayesian weights:")
        for model_name, weight in bayesian_weights.items():
            print(f"     {model_name}: {weight:.3f}")
        
        self.bayesian_weights = bayesian_weights
        return bayesian_weights
    
    def bayesian_model_averaging(self, model_probabilities: Dict) -> Tuple[np.ndarray, Dict]:
        """Perform Bayesian model averaging of predictions"""
        print("🔄 Performing Bayesian model averaging...")
        
        if not self.bayesian_weights:
            # Use uniform weights if Bayesian weights not calculated
            n_models = len(model_probabilities)
            self.bayesian_weights = {name: 1.0/n_models for name in model_probabilities.keys()}
        
        # Initialize averaged probabilities
        n_samples = next(iter(model_probabilities.values())).shape[0]
        n_classes = next(iter(model_probabilities.values())).shape[1]
        averaged_probs = np.zeros((n_samples, n_classes))
        
        # Weight and sum probabilities
        total_weight = 0.0
        for model_name, probabilities in model_probabilities.items():
            weight = self.bayesian_weights.get(model_name, 0.0)
            averaged_probs += probabilities * weight
            total_weight += weight
        
        # Normalize if needed
        if total_weight > 0:
            averaged_probs /= total_weight
        
        # Calculate prediction uncertainty
        uncertainty_metrics = self._calculate_bayesian_uncertainty(model_probabilities)
        
        print(f"✅ Bayesian averaging complete for {n_samples} predictions")
        return averaged_probs, uncertainty_metrics
    
    def _calculate_bayesian_uncertainty(self, model_probabilities: Dict) -> Dict:
        """Calculate epistemic and aleatoric uncertainty"""
        
        # Stack all model probabilities
        prob_arrays = list(model_probabilities.values())
        stacked_probs = np.stack(prob_arrays, axis=2)  # (n_samples, n_classes, n_models)
        
        # Calculate epistemic uncertainty (model disagreement)
        # Variance across models for each prediction
        epistemic_uncertainty = np.var(stacked_probs, axis=2)  # (n_samples, n_classes)
        epistemic_uncertainty_total = np.sum(epistemic_uncertainty, axis=1)  # Total per sample
        
        # Calculate aleatoric uncertainty (inherent data uncertainty)
        # Average entropy across models
        epsilon = 1e-15
        entropies = -np.sum(stacked_probs * np.log(stacked_probs + epsilon), axis=1)  # (n_samples, n_models)
        aleatoric_uncertainty = np.mean(entropies, axis=1)  # Average entropy per sample
        
        # Calculate total uncertainty
        total_uncertainty = epistemic_uncertainty_total + aleatoric_uncertainty
        
        # Calculate mutual information (reduction in uncertainty from ensemble)
        mean_probs = np.mean(stacked_probs, axis=2)  # (n_samples, n_classes)
        mean_entropy = -np.sum(mean_probs * np.log(mean_probs + epsilon), axis=1)
        mutual_information = aleatoric_uncertainty - mean_entropy
        
        uncertainty_metrics = {
            'epistemic_uncertainty': epistemic_uncertainty_total.tolist(),
            'aleatoric_uncertainty': aleatoric_uncertainty.tolist(),
            'total_uncertainty': total_uncertainty.tolist(),
            'mutual_information': mutual_information.tolist(),
            'mean_epistemic': float(np.mean(epistemic_uncertainty_total)),
            'mean_aleatoric': float(np.mean(aleatoric_uncertainty)),
            'mean_total': float(np.mean(total_uncertainty))
        }
        
        return uncertainty_metrics
    
    def calculate_prediction_intervals(self, averaged_probabilities: np.ndarray,
                                     uncertainty_metrics: Dict,
                                     confidence_level: float = 0.95) -> Dict:
        """Calculate prediction intervals using uncertainty estimates"""
        print(f"🔄 Calculating {confidence_level*100}% prediction intervals...")
        
        # Get uncertainty estimates
        total_uncertainty = np.array(uncertainty_metrics['total_uncertainty'])
        
        # Calculate confidence intervals using normal approximation
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        
        # For binary classification, focus on positive class probability
        positive_class_probs = averaged_probabilities[:, 1]  # Assuming class 1 is positive
        
        # Calculate intervals
        margin_of_error = z_score * np.sqrt(total_uncertainty)
        lower_bounds = np.clip(positive_class_probs - margin_of_error, 0, 1)
        upper_bounds = np.clip(positive_class_probs + margin_of_error, 0, 1)
        
        # Calculate interval widths
        interval_widths = upper_bounds - lower_bounds
        
        prediction_intervals = {
            'lower_bounds': lower_bounds.tolist(),
            'upper_bounds': upper_bounds.tolist(),
            'interval_widths': interval_widths.tolist(),
            'mean_interval_width': float(np.mean(interval_widths)),
            'confidence_level': confidence_level,
            'point_estimates': positive_class_probs.tolist()
        }
        
        print(f"   Mean interval width: {np.mean(interval_widths):.3f}")
        return prediction_intervals
    
    def model_selection_bayesian(self, model_performances: Dict, 
                                selection_criterion: str = 'evidence') -> str:
        """Select best model using Bayesian criteria"""
        print(f"🔄 Bayesian model selection using {selection_criterion}...")
        
        if selection_criterion == 'evidence':
            # Select model with highest evidence
            if not self.evidence_weights:
                raise ValueError("Evidence weights not calculated. Run calculate_model_evidence first.")
            
            best_model = max(self.evidence_weights.keys(), 
                           key=lambda k: self.evidence_weights[k])
            best_score = self.evidence_weights[best_model]
            
        elif selection_criterion == 'posterior':
            # Select model with highest posterior probability
            if not self.bayesian_weights:
                raise ValueError("Bayesian weights not calculated. Run update_bayesian_weights first.")
            
            best_model = max(self.bayesian_weights.keys(),
                           key=lambda k: self.bayesian_weights[k])
            best_score = self.bayesian_weights[best_model]
            
        elif selection_criterion == 'bic':
            # Bayesian Information Criterion
            bic_scores = {}
            for model_name, performance in model_performances.items():
                log_likelihood = performance.get('log_likelihood', 0)
                n_params = performance.get('n_parameters', 10)  # Estimate if not provided
                n_samples = performance.get('n_samples', 100)
                
                bic = -2 * log_likelihood + n_params * np.log(n_samples)
                bic_scores[model_name] = bic
            
            best_model = min(bic_scores.keys(), key=lambda k: bic_scores[k])  # Lower BIC is better
            best_score = bic_scores[best_model]
            
        else:
            raise ValueError(f"Unknown selection criterion: {selection_criterion}")
        
        print(f"   Best model: {best_model} (score: {best_score:.3f})")
        return best_model
    
    def calculate_model_confidence(self, model_probabilities: Dict, 
                                 y_true: np.ndarray = None) -> Dict:
        """Calculate confidence metrics for each model"""
        print("🔄 Calculating model confidence metrics...")
        
        confidence_metrics = {}
        
        for model_name, probabilities in model_probabilities.items():
            # Basic confidence metrics
            max_probs = np.max(probabilities, axis=1)
            mean_confidence = np.mean(max_probs)
            confidence_variance = np.var(max_probs)
            
            # Entropy-based uncertainty
            epsilon = 1e-15
            entropies = -np.sum(probabilities * np.log(probabilities + epsilon), axis=1)
            mean_entropy = np.mean(entropies)
            
            # Calibration metrics (if true labels available)
            calibration_metrics = {}
            if y_true is not None:
                try:
                    # Brier score (lower is better)
                    brier_score = brier_score_loss(y_true, probabilities[:, 1])
                    
                    # Log loss (lower is better)
                    log_loss_score = log_loss(y_true, probabilities)
                    
                    calibration_metrics = {
                        'brier_score': brier_score,
                        'log_loss': log_loss_score
                    }
                except Exception as e:
                    self.logger.error(f"Error calculating calibration for {model_name}: {e}")
            
            confidence_metrics[model_name] = {
                'mean_confidence': mean_confidence,
                'confidence_variance': confidence_variance,
                'mean_entropy': mean_entropy,
                'min_confidence': np.min(max_probs),
                'max_confidence': np.max(max_probs),
                **calibration_metrics
            }
        
        return confidence_metrics
    
    def ensemble_diversity_analysis(self, model_predictions: Dict) -> Dict:
        """Analyze diversity among ensemble models"""
        print("🔄 Analyzing ensemble diversity...")
        
        # Convert predictions to arrays
        pred_arrays = [pred for pred in model_predictions.values()]
        model_names = list(model_predictions.keys())
        
        if len(pred_arrays) < 2:
            return {'error': 'Need at least 2 models for diversity analysis'}
        
        # Stack predictions
        stacked_preds = np.stack(pred_arrays, axis=1)  # (n_samples, n_models)
        
        # Calculate pairwise disagreement
        n_models = len(pred_arrays)
        disagreement_matrix = np.zeros((n_models, n_models))
        
        for i in range(n_models):
            for j in range(i+1, n_models):
                disagreement = np.mean(pred_arrays[i] != pred_arrays[j])
                disagreement_matrix[i, j] = disagreement
                disagreement_matrix[j, i] = disagreement
        
        # Calculate diversity metrics
        mean_pairwise_disagreement = np.mean(disagreement_matrix[np.triu_indices(n_models, k=1)])
        
        # Q-statistic (Yule's Q) for pairwise diversity
        q_statistics = []
        for i in range(n_models):
            for j in range(i+1, n_models):
                q_stat = self._calculate_q_statistic(pred_arrays[i], pred_arrays[j])
                q_statistics.append(q_stat)
        
        mean_q_statistic = np.mean(q_statistics) if q_statistics else 0.0
        
        # Entropy-based diversity
        # For each sample, calculate entropy of model predictions
        sample_diversities = []
        for sample_idx in range(stacked_preds.shape[0]):
            sample_preds = stacked_preds[sample_idx, :]
            unique_preds, counts = np.unique(sample_preds, return_counts=True)
            probs = counts / len(sample_preds)
            entropy = -np.sum(probs * np.log(probs + 1e-15))
            sample_diversities.append(entropy)
        
        mean_entropy_diversity = np.mean(sample_diversities)
        
        diversity_metrics = {
            'mean_pairwise_disagreement': mean_pairwise_disagreement,
            'disagreement_matrix': disagreement_matrix.tolist(),
            'mean_q_statistic': mean_q_statistic,
            'q_statistics': q_statistics,
            'mean_entropy_diversity': mean_entropy_diversity,
            'sample_diversities': sample_diversities,
            'model_names': model_names
        }
        
        print(f"   Mean pairwise disagreement: {mean_pairwise_disagreement:.3f}")
        print(f"   Mean Q-statistic: {mean_q_statistic:.3f}")
        
        return diversity_metrics
    
    def _calculate_q_statistic(self, pred1: np.ndarray, pred2: np.ndarray) -> float:
        """Calculate Yule's Q statistic for two binary classifiers"""
        # Create confusion matrix
        both_correct = np.sum((pred1 == 1) & (pred2 == 1))
        both_wrong = np.sum((pred1 == 0) & (pred2 == 0))
        first_correct_second_wrong = np.sum((pred1 == 1) & (pred2 == 0))
        first_wrong_second_correct = np.sum((pred1 == 0) & (pred2 == 1))
        
        # Calculate Q-statistic
        numerator = both_correct * both_wrong - first_correct_second_wrong * first_wrong_second_correct
        denominator = both_correct * both_wrong + first_correct_second_wrong * first_wrong_second_correct
        
        if denominator == 0:
            return 0.0
        
        q_statistic = numerator / denominator
        return q_statistic
    
    def save_bayesian_ensemble(self, filepath: str = None) -> str:
        """Save Bayesian ensemble state"""
        if filepath is None:
            filepath = self.models_dir / f"bayesian_ensemble_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        ensemble_state = {
            'model_priors': self.model_priors,
            'model_posteriors': self.model_posteriors,
            'evidence_weights': self.evidence_weights,
            'bayesian_weights': self.bayesian_weights,
            'epistemic_uncertainty': self.epistemic_uncertainty,
            'aleatoric_uncertainty': self.aleatoric_uncertainty,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(ensemble_state, f, indent=2)
        
        print(f"✅ Bayesian ensemble saved to {filepath}")
        return str(filepath)
    
    def load_bayesian_ensemble(self, filepath: str) -> bool:
        """Load Bayesian ensemble state"""
        try:
            with open(filepath) as f:
                ensemble_state = json.load(f)
            
            self.model_priors = ensemble_state.get('model_priors', {})
            self.model_posteriors = ensemble_state.get('model_posteriors', {})
            self.evidence_weights = ensemble_state.get('evidence_weights', {})
            self.bayesian_weights = ensemble_state.get('bayesian_weights', {})
            self.epistemic_uncertainty = ensemble_state.get('epistemic_uncertainty', {})
            self.aleatoric_uncertainty = ensemble_state.get('aleatoric_uncertainty', {})
            
            print(f"✅ Bayesian ensemble loaded from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading Bayesian ensemble: {e}")
            return False