import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from src.config.settings import Config
import json
import joblib
import pickle
import warnings
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.calibration import CalibratedClassifierCV
import logging

warnings.filterwarnings('ignore')

class EnsemblePredictor:
    """Advanced ensemble modeling system with multiple algorithms and Bayesian averaging"""
    
    def __init__(self):
        self.models_dir = Config.MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Model storage
        self.base_models = {}
        self.ensemble_weights = {}
        self.model_metadata = {}
        
        # Ensemble configuration
        self.model_types = ['random_forest', 'xgboost', 'logistic_regression']
        self.calibration_method = 'isotonic'
        self.cv_folds = 5
        
        # Performance tracking
        self.performance_history = {}
        self.validation_scores = {}
        
        self.logger = logging.getLogger(__name__)
        print(f"✅ Ensemble Predictor initialized")
    
    def train_base_models(self, X: pd.DataFrame, y: pd.Series, 
                         model_configs: Dict = None) -> Dict[str, Any]:
        """Train all base models in the ensemble"""
        print("🔄 Training base models for ensemble...")
        
        if model_configs is None:
            model_configs = self._get_default_model_configs()
        
        trained_models = {}
        training_scores = {}
        
        for model_name in self.model_types:
            print(f"   Training {model_name}...")
            
            try:
                # Get model configuration
                config = model_configs.get(model_name, {})
                
                # Create and train model
                model = self._create_model(model_name, config)
                model.fit(X, y)
                
                # Calibrate probabilities
                calibrated_model = CalibratedClassifierCV(
                    model, method=self.calibration_method, cv=3
                )
                calibrated_model.fit(X, y)
                
                # Evaluate model
                cv_scores = cross_val_score(
                    calibrated_model, X, y, cv=self.cv_folds, scoring='accuracy'
                )
                
                # Store model and scores
                trained_models[model_name] = calibrated_model
                training_scores[model_name] = {
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'cv_scores': cv_scores.tolist()
                }
                
                print(f"     {model_name}: {cv_scores.mean():.3f} ± {cv_scores.std():.3f} accuracy")
                
            except Exception as e:
                self.logger.error(f"Error training {model_name}: {e}")
                print(f"     {model_name}: Training failed - {e}")
                continue
        
        # Store trained models
        self.base_models = trained_models
        self.validation_scores = training_scores
        
        # Calculate ensemble weights
        self.ensemble_weights = self.calculate_ensemble_weights(training_scores)
        
        # Store metadata
        self.model_metadata = {
            'training_timestamp': datetime.now().isoformat(),
            'n_features': len(X.columns),
            'n_samples': len(X),
            'feature_names': list(X.columns),
            'model_types': list(trained_models.keys()),
            'ensemble_weights': self.ensemble_weights,
            'validation_scores': training_scores
        }
        
        print(f"✅ Ensemble training complete: {len(trained_models)} models trained")
        return trained_models
    
    def _get_default_model_configs(self) -> Dict:
        """Get default configurations for each model type"""
        return {
            'random_forest': {
                'n_estimators': 200,
                'max_depth': 15,
                'min_samples_split': 10,
                'min_samples_leaf': 5,
                'max_features': 'sqrt',
                'bootstrap': True,
                'random_state': 42,
                'n_jobs': -1,
                'class_weight': 'balanced'
            },
            'xgboost': {
                'n_estimators': 200,
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'reg_alpha': 0.1,
                'reg_lambda': 1.0,
                'random_state': 42,
                'n_jobs': -1,
                'eval_metric': 'logloss'
            },
            'logistic_regression': {
                'C': 1.0,
                'penalty': 'l2',
                'solver': 'liblinear',
                'random_state': 42,
                'max_iter': 1000,
                'class_weight': 'balanced'
            }
        }
    
    def _create_model(self, model_name: str, config: Dict) -> Any:
        """Create a model instance based on type and configuration"""
        if model_name == 'random_forest':
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(**config)
        
        elif model_name == 'xgboost':
            try:
                import xgboost as xgb
                return xgb.XGBClassifier(**config)
            except ImportError:
                self.logger.warning("XGBoost not available, using RandomForest instead")
                from sklearn.ensemble import RandomForestClassifier
                rf_config = self._get_default_model_configs()['random_forest']
                return RandomForestClassifier(**rf_config)
        
        elif model_name == 'logistic_regression':
            from sklearn.linear_model import LogisticRegression
            return LogisticRegression(**config)
        
        else:
            raise ValueError(f"Unknown model type: {model_name}")
    
    def calculate_ensemble_weights(self, validation_scores: Dict) -> Dict[str, float]:
        """Calculate ensemble weights based on validation performance"""
        print("🔄 Calculating ensemble weights...")
        
        if not validation_scores:
            return {}
        
        # Extract performance scores
        model_scores = {}
        for model_name, scores in validation_scores.items():
            model_scores[model_name] = scores['cv_mean']
        
        # Calculate weights using softmax of performance scores
        scores_array = np.array(list(model_scores.values()))
        
        # Apply temperature scaling to control weight distribution
        temperature = 2.0  # Higher temperature = more uniform weights
        scaled_scores = scores_array / temperature
        
        # Softmax transformation
        exp_scores = np.exp(scaled_scores - np.max(scaled_scores))  # Numerical stability
        weights = exp_scores / np.sum(exp_scores)
        
        # Create weight dictionary
        weight_dict = {}
        for i, model_name in enumerate(model_scores.keys()):
            weight_dict[model_name] = float(weights[i])
        
        print("   Ensemble weights:")
        for model_name, weight in weight_dict.items():
            print(f"     {model_name}: {weight:.3f}")
        
        return weight_dict
    
    def predict_with_uncertainty(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Generate ensemble predictions with uncertainty quantification"""
        if not self.base_models:
            raise ValueError("No trained models available. Train models first.")
        
        print(f"🔄 Generating ensemble predictions for {len(X)} samples...")
        
        # Collect predictions from all models
        model_predictions = {}
        model_probabilities = {}
        
        for model_name, model in self.base_models.items():
            try:
                # Get predictions and probabilities
                pred = model.predict(X)
                prob = model.predict_proba(X)
                
                model_predictions[model_name] = pred
                model_probabilities[model_name] = prob
                
            except Exception as e:
                self.logger.error(f"Error in prediction from {model_name}: {e}")
                continue
        
        if not model_predictions:
            raise ValueError("No models could generate predictions")
        
        # Calculate ensemble predictions
        ensemble_pred, ensemble_prob = self._combine_predictions(
            model_predictions, model_probabilities
        )
        
        # Calculate uncertainty metrics
        uncertainty_metrics = self._calculate_prediction_uncertainty(
            model_predictions, model_probabilities
        )
        
        print(f"✅ Ensemble predictions generated: {np.sum(ensemble_pred)} NDA wins predicted")
        
        return ensemble_pred, ensemble_prob, uncertainty_metrics
    
    def _combine_predictions(self, model_predictions: Dict, 
                           model_probabilities: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """Combine predictions from multiple models using ensemble weights"""
        
        # Initialize arrays
        n_samples = len(next(iter(model_predictions.values())))
        n_classes = next(iter(model_probabilities.values())).shape[1]
        
        weighted_probabilities = np.zeros((n_samples, n_classes))
        
        # Combine probabilities using weights
        total_weight = 0
        for model_name, probabilities in model_probabilities.items():
            weight = self.ensemble_weights.get(model_name, 1.0 / len(model_probabilities))
            weighted_probabilities += probabilities * weight
            total_weight += weight
        
        # Normalize if weights don't sum to 1
        if total_weight > 0:
            weighted_probabilities /= total_weight
        
        # Generate final predictions
        ensemble_predictions = np.argmax(weighted_probabilities, axis=1)
        
        return ensemble_predictions, weighted_probabilities
    
    def _calculate_prediction_uncertainty(self, model_predictions: Dict, 
                                        model_probabilities: Dict) -> Dict:
        """Calculate uncertainty metrics for ensemble predictions"""
        
        # Convert predictions to arrays
        pred_arrays = [pred for pred in model_predictions.values()]
        prob_arrays = [prob for prob in model_probabilities.values()]
        
        if not pred_arrays:
            return {'error': 'No predictions available for uncertainty calculation'}
        
        # Stack predictions and probabilities
        stacked_predictions = np.stack(pred_arrays, axis=1)  # (n_samples, n_models)
        stacked_probabilities = np.stack(prob_arrays, axis=2)  # (n_samples, n_classes, n_models)
        
        # Calculate disagreement metrics
        prediction_variance = np.var(stacked_predictions, axis=1)  # Variance across models
        prediction_entropy = self._calculate_prediction_entropy(stacked_probabilities)
        
        # Calculate confidence metrics
        max_probabilities = np.max(stacked_probabilities, axis=1)  # Max prob for each model
        confidence_variance = np.var(max_probabilities, axis=1)  # Variance in confidence
        mean_confidence = np.mean(max_probabilities, axis=1)  # Average confidence
        
        # Model agreement (fraction of models agreeing with majority)
        majority_predictions = np.apply_along_axis(
            lambda x: np.bincount(x).argmax(), axis=1, arr=stacked_predictions
        )
        agreement_rates = np.mean(
            stacked_predictions == majority_predictions[:, np.newaxis], axis=1
        )
        
        uncertainty_metrics = {
            'prediction_variance': prediction_variance.tolist(),
            'prediction_entropy': prediction_entropy.tolist(),
            'confidence_variance': confidence_variance.tolist(),
            'mean_confidence': mean_confidence.tolist(),
            'model_agreement': agreement_rates.tolist(),
            'n_models': len(pred_arrays)
        }
        
        return uncertainty_metrics
    
    def _calculate_prediction_entropy(self, probabilities: np.ndarray) -> np.ndarray:
        """Calculate prediction entropy across models"""
        # Average probabilities across models
        mean_probs = np.mean(probabilities, axis=2)  # (n_samples, n_classes)
        
        # Calculate entropy
        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        entropy = -np.sum(mean_probs * np.log(mean_probs + epsilon), axis=1)
        
        return entropy
    
    def get_model_contributions(self, X: pd.DataFrame) -> pd.DataFrame:
        """Get individual model contributions to ensemble predictions"""
        if not self.base_models:
            raise ValueError("No trained models available")
        
        contributions = []
        
        for model_name, model in self.base_models.items():
            try:
                # Get model predictions
                predictions = model.predict(X)
                probabilities = model.predict_proba(X)
                
                # Get model weight
                weight = self.ensemble_weights.get(model_name, 1.0 / len(self.base_models))
                
                # Create contribution record
                contribution = {
                    'model_name': model_name,
                    'weight': weight,
                    'predictions': predictions.tolist(),
                    'nda_probabilities': probabilities[:, 1].tolist(),  # Assuming class 1 is NDA
                    'weighted_contribution': (probabilities[:, 1] * weight).tolist()
                }
                
                contributions.append(contribution)
                
            except Exception as e:
                self.logger.error(f"Error getting contributions from {model_name}: {e}")
                continue
        
        return contributions
    
    def update_ensemble_weights(self, new_performance: Dict) -> None:
        """Update ensemble weights based on new performance data"""
        print("🔄 Updating ensemble weights...")
        
        # Combine old and new performance data
        combined_scores = {}
        
        for model_name in self.model_types:
            old_score = self.validation_scores.get(model_name, {}).get('cv_mean', 0.5)
            new_score = new_performance.get(model_name, old_score)
            
            # Use exponential moving average to combine scores
            alpha = 0.3  # Weight for new performance
            combined_score = alpha * new_score + (1 - alpha) * old_score
            combined_scores[model_name] = {'cv_mean': combined_score}
        
        # Recalculate weights
        self.ensemble_weights = self.calculate_ensemble_weights(combined_scores)
        
        # Update validation scores
        self.validation_scores.update(new_performance)
        
        print("✅ Ensemble weights updated")
    
    def evaluate_ensemble(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Comprehensive evaluation of ensemble performance"""
        print("🔄 Evaluating ensemble performance...")
        
        if not self.base_models:
            raise ValueError("No trained models available")
        
        # Get ensemble predictions
        ensemble_pred, ensemble_prob, uncertainty_metrics = self.predict_with_uncertainty(X)
        
        # Calculate ensemble metrics
        ensemble_metrics = {
            'accuracy': accuracy_score(y, ensemble_pred),
            'precision': precision_score(y, ensemble_pred, average='weighted'),
            'recall': recall_score(y, ensemble_pred, average='weighted'),
            'f1_score': f1_score(y, ensemble_pred, average='weighted'),
            'roc_auc': roc_auc_score(y, ensemble_prob[:, 1])
        }
        
        # Evaluate individual models
        individual_metrics = {}
        for model_name, model in self.base_models.items():
            try:
                pred = model.predict(X)
                prob = model.predict_proba(X)
                
                individual_metrics[model_name] = {
                    'accuracy': accuracy_score(y, pred),
                    'precision': precision_score(y, pred, average='weighted'),
                    'recall': recall_score(y, pred, average='weighted'),
                    'f1_score': f1_score(y, pred, average='weighted'),
                    'roc_auc': roc_auc_score(y, prob[:, 1])
                }
            except Exception as e:
                self.logger.error(f"Error evaluating {model_name}: {e}")
                individual_metrics[model_name] = {'error': str(e)}
        
        evaluation_result = {
            'ensemble_metrics': ensemble_metrics,
            'individual_metrics': individual_metrics,
            'ensemble_weights': self.ensemble_weights,
            'uncertainty_summary': {
                'mean_prediction_variance': np.mean(uncertainty_metrics['prediction_variance']),
                'mean_model_agreement': np.mean(uncertainty_metrics['model_agreement']),
                'mean_confidence': np.mean(uncertainty_metrics['mean_confidence'])
            },
            'evaluation_timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Ensemble evaluation complete:")
        print(f"   Ensemble accuracy: {ensemble_metrics['accuracy']:.3f}")
        print(f"   Ensemble F1-score: {ensemble_metrics['f1_score']:.3f}")
        
        return evaluation_result
    
    def save_ensemble(self, version: str = None) -> str:
        """Save ensemble models and metadata"""
        if not self.base_models:
            raise ValueError("No trained models to save")
        
        if version is None:
            version = f"ensemble_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create version directory
        version_dir = self.models_dir / version
        version_dir.mkdir(exist_ok=True)
        
        # Save individual models
        model_paths = {}
        for model_name, model in self.base_models.items():
            model_path = version_dir / f"{model_name}.joblib"
            joblib.dump(model, model_path)
            model_paths[model_name] = str(model_path)
        
        # Save ensemble metadata
        ensemble_metadata = {
            **self.model_metadata,
            'version': version,
            'saved_at': datetime.now().isoformat(),
            'model_paths': model_paths,
            'ensemble_weights': self.ensemble_weights
        }
        
        metadata_path = version_dir / 'ensemble_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(ensemble_metadata, f, indent=2)
        
        # Update latest symlink
        latest_dir = self.models_dir / 'latest_ensemble'
        if latest_dir.exists():
            latest_dir.unlink()
        latest_dir.symlink_to(version_dir)
        
        print(f"✅ Ensemble saved as version {version}")
        return version
    
    def load_ensemble(self, version: str = "latest") -> bool:
        """Load ensemble models and metadata"""
        print(f"🔄 Loading ensemble version {version}...")
        
        if version == "latest":
            ensemble_dir = self.models_dir / 'latest_ensemble'
        else:
            ensemble_dir = self.models_dir / version
        
        if not ensemble_dir.exists():
            raise FileNotFoundError(f"Ensemble version {version} not found")
        
        # Load metadata
        metadata_path = ensemble_dir / 'ensemble_metadata.json'
        if not metadata_path.exists():
            raise FileNotFoundError(f"Ensemble metadata not found for version {version}")
        
        with open(metadata_path) as f:
            self.model_metadata = json.load(f)
        
        # Load individual models
        loaded_models = {}
        model_paths = self.model_metadata.get('model_paths', {})
        
        for model_name, model_path in model_paths.items():
            try:
                model = joblib.load(model_path)
                loaded_models[model_name] = model
                print(f"   Loaded {model_name}")
            except Exception as e:
                self.logger.error(f"Error loading {model_name}: {e}")
                continue
        
        if not loaded_models:
            raise ValueError("No models could be loaded")
        
        # Update instance variables
        self.base_models = loaded_models
        self.ensemble_weights = self.model_metadata.get('ensemble_weights', {})
        self.validation_scores = self.model_metadata.get('validation_scores', {})
        
        print(f"✅ Ensemble loaded: {len(loaded_models)} models")
        return True
    
    def create_optimized_random_forest(self, config: Dict = None) -> Any:
        """Create optimized Random Forest with electoral-specific hyperparameters"""
        from sklearn.ensemble import RandomForestClassifier
        
        if config is None:
            # Electoral-optimized hyperparameters
            config = {
                'n_estimators': 300,  # More trees for stability
                'max_depth': 12,      # Prevent overfitting on small datasets
                'min_samples_split': 15,  # Conservative splitting
                'min_samples_leaf': 8,    # Ensure leaf reliability
                'max_features': 'sqrt',   # Feature randomness
                'bootstrap': True,
                'oob_score': True,        # Out-of-bag evaluation
                'random_state': 42,
                'n_jobs': -1,
                'class_weight': 'balanced_subsample',  # Handle class imbalance
                'criterion': 'gini',
                'max_samples': 0.8        # Bootstrap sample size
            }
        
        model = RandomForestClassifier(**config)
        
        # Add custom attributes for electoral modeling
        model._electoral_optimized = True
        model._model_type = 'random_forest_electoral'
        
        return model
    
    def create_optimized_xgboost(self, config: Dict = None) -> Any:
        """Create optimized XGBoost with early stopping and regularization"""
        try:
            import xgboost as xgb
        except ImportError:
            self.logger.warning("XGBoost not available, falling back to RandomForest")
            return self.create_optimized_random_forest()
        
        if config is None:
            # Electoral-optimized XGBoost parameters
            config = {
                'n_estimators': 500,      # More estimators with early stopping
                'max_depth': 8,           # Moderate depth
                'learning_rate': 0.05,    # Lower learning rate for stability
                'subsample': 0.85,        # Row sampling
                'colsample_bytree': 0.8,  # Feature sampling
                'colsample_bylevel': 0.8, # Per-level feature sampling
                'reg_alpha': 0.1,         # L1 regularization
                'reg_lambda': 1.0,        # L2 regularization
                'gamma': 0.1,             # Minimum split loss
                'min_child_weight': 5,    # Minimum sum of instance weight
                'random_state': 42,
                'n_jobs': -1,
                'eval_metric': 'logloss',
                'early_stopping_rounds': 50,
                'verbosity': 0,
                'scale_pos_weight': 1.0   # Will be adjusted for class imbalance
            }
        
        # Create model with early stopping capability
        model = xgb.XGBClassifier(**config)
        
        # Add custom attributes
        model._electoral_optimized = True
        model._model_type = 'xgboost_electoral'
        model._early_stopping = True
        
        return model
    
    def create_optimized_logistic_regression(self, config: Dict = None) -> Any:
        """Create regularized Logistic Regression with polynomial features"""
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import PolynomialFeatures
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        
        if config is None:
            config = {
                'C': 0.1,                 # Strong regularization
                'penalty': 'elasticnet',  # Combined L1 and L2
                'l1_ratio': 0.5,         # Balance between L1 and L2
                'solver': 'saga',        # Supports elasticnet
                'random_state': 42,
                'max_iter': 2000,
                'class_weight': 'balanced',
                'tol': 1e-6
            }
        
        # Create pipeline with feature engineering
        pipeline_steps = [
            ('scaler', StandardScaler()),
            ('poly_features', PolynomialFeatures(
                degree=2, 
                interaction_only=True,  # Only interaction terms, no pure powers
                include_bias=False
            )),
            ('logistic', LogisticRegression(**config))
        ]
        
        model = Pipeline(pipeline_steps)
        
        # Add custom attributes
        model._electoral_optimized = True
        model._model_type = 'logistic_regression_electoral'
        model._has_feature_engineering = True
        
        return model
    
    def fit_model_with_validation(self, model: Any, X: pd.DataFrame, y: pd.Series,
                                 validation_split: float = 0.2) -> Tuple[Any, Dict]:
        """Fit model with validation and early stopping where applicable"""
        from sklearn.model_selection import train_test_split
        
        # Split data for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )
        
        # Check if model supports early stopping (XGBoost)
        if hasattr(model, '_early_stopping') and model._early_stopping:
            # Fit with early stopping
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
            
            # Get validation metrics
            val_pred = model.predict(X_val)
            val_prob = model.predict_proba(X_val)
            
        else:
            # Standard fitting
            model.fit(X_train, y_train)
            val_pred = model.predict(X_val)
            val_prob = model.predict_proba(X_val)
        
        # Calculate validation metrics
        validation_metrics = {
            'accuracy': accuracy_score(y_val, val_pred),
            'precision': precision_score(y_val, val_pred, average='weighted'),
            'recall': recall_score(y_val, val_pred, average='weighted'),
            'f1_score': f1_score(y_val, val_pred, average='weighted'),
            'roc_auc': roc_auc_score(y_val, val_prob[:, 1]),
            'validation_samples': len(y_val)
        }
        
        return model, validation_metrics
    
    def get_model_feature_importance(self, model: Any, feature_names: List[str]) -> Dict:
        """Extract feature importance from trained model"""
        importance_dict = {}
        
        try:
            model_type = getattr(model, '_model_type', 'unknown')
            
            if 'random_forest' in model_type:
                # Random Forest feature importance
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    importance_dict = dict(zip(feature_names, importances))
                
            elif 'xgboost' in model_type:
                # XGBoost feature importance
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    importance_dict = dict(zip(feature_names, importances))
                
            elif 'logistic' in model_type:
                # Logistic Regression coefficients
                if hasattr(model, 'named_steps'):
                    # Pipeline case
                    logistic_model = model.named_steps['logistic']
                    if hasattr(logistic_model, 'coef_'):
                        # Get feature names after polynomial transformation
                        poly_features = model.named_steps['poly_features']
                        poly_feature_names = poly_features.get_feature_names_out(feature_names)
                        
                        # Use absolute coefficients as importance
                        coefficients = np.abs(logistic_model.coef_[0])
                        importance_dict = dict(zip(poly_feature_names, coefficients))
                else:
                    # Direct logistic regression
                    if hasattr(model, 'coef_'):
                        coefficients = np.abs(model.coef_[0])
                        importance_dict = dict(zip(feature_names, coefficients))
            
            # Sort by importance
            importance_dict = dict(sorted(importance_dict.items(), 
                                        key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            self.logger.error(f"Error extracting feature importance: {e}")
            importance_dict = {'error': str(e)}
        
        return importance_dict
    
    def optimize_model_hyperparameters(self, model_type: str, X: pd.DataFrame, 
                                     y: pd.Series, n_trials: int = 50) -> Dict:
        """Optimize model hyperparameters using cross-validation"""
        print(f"🔄 Optimizing hyperparameters for {model_type}...")
        
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)
        except ImportError:
            self.logger.warning("Optuna not available, using default hyperparameters")
            return self._get_default_model_configs()[model_type]
        
        def objective(trial):
            # Define hyperparameter search spaces
            if model_type == 'random_forest':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                    'max_depth': trial.suggest_int('max_depth', 5, 20),
                    'min_samples_split': trial.suggest_int('min_samples_split', 5, 25),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 2, 15),
                    'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', 0.5, 0.8]),
                    'bootstrap': True,
                    'random_state': 42,
                    'n_jobs': -1,
                    'class_weight': 'balanced'
                }
                model = self.create_optimized_random_forest(params)
                
            elif model_type == 'xgboost':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 800),
                    'max_depth': trial.suggest_int('max_depth', 3, 12),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
                    'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 2.0),
                    'random_state': 42,
                    'n_jobs': -1,
                    'eval_metric': 'logloss'
                }
                model = self.create_optimized_xgboost(params)
                
            elif model_type == 'logistic_regression':
                params = {
                    'C': trial.suggest_float('C', 0.001, 10.0, log=True),
                    'l1_ratio': trial.suggest_float('l1_ratio', 0.0, 1.0),
                    'penalty': 'elasticnet',
                    'solver': 'saga',
                    'random_state': 42,
                    'max_iter': 2000,
                    'class_weight': 'balanced'
                }
                model = self.create_optimized_logistic_regression(params)
            
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Cross-validation score
            cv_scores = cross_val_score(model, X, y, cv=3, scoring='f1_weighted')
            return cv_scores.mean()
        
        # Run optimization
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        best_params = study.best_params
        best_score = study.best_value
        
        print(f"   Best {model_type} score: {best_score:.3f}")
        print(f"   Best parameters: {best_params}")
        
        return best_params
    
    def predict_constituencies_ensemble(self, X: pd.DataFrame, 
                                      use_bayesian: bool = True) -> pd.DataFrame:
        """Generate comprehensive ensemble predictions for constituencies"""
        print(f"🔄 Generating ensemble predictions for {len(X)} constituencies...")
        
        if not self.base_models:
            raise ValueError("No trained models available")
        
        # Get predictions from all models
        ensemble_pred, ensemble_prob, uncertainty_metrics = self.predict_with_uncertainty(X)
        
        # Use Bayesian averaging if requested
        if use_bayesian:
            try:
                from src.modeling.bayesian_ensemble import BayesianEnsemble
                
                bayesian_ensemble = BayesianEnsemble()
                
                # Get individual model probabilities
                model_probabilities = {}
                for model_name, model in self.base_models.items():
                    model_probabilities[model_name] = model.predict_proba(X)
                
                # Set priors and calculate Bayesian weights
                bayesian_ensemble.set_model_priors(list(self.base_models.keys()), 'performance_based')
                
                # Perform Bayesian averaging
                bayesian_probs, bayesian_uncertainty = bayesian_ensemble.bayesian_model_averaging(model_probabilities)
                
                # Calculate prediction intervals
                prediction_intervals = bayesian_ensemble.calculate_prediction_intervals(bayesian_probs, bayesian_uncertainty)
                
                # Use Bayesian results
                ensemble_prob = bayesian_probs
                uncertainty_metrics.update(bayesian_uncertainty)
                
            except Exception as e:
                self.logger.warning(f"Bayesian averaging failed, using standard ensemble: {e}")
        
        # Create results DataFrame
        results_df = pd.DataFrame({
            'constituency': X.index if hasattr(X, 'index') else range(len(X)),
            'predicted_winner': ['NDA' if p == 1 else 'INDI' for p in ensemble_pred],
            'nda_win_probability': ensemble_prob[:, 1],
            'indi_win_probability': ensemble_prob[:, 0],
            'prediction_confidence': np.max(ensemble_prob, axis=1),
            'prediction_uncertainty': uncertainty_metrics.get('total_uncertainty', [0.1] * len(X)),
            'model_agreement': uncertainty_metrics.get('model_agreement', [1.0] * len(X)),
            'epistemic_uncertainty': uncertainty_metrics.get('epistemic_uncertainty', [0.05] * len(X)),
            'aleatoric_uncertainty': uncertainty_metrics.get('aleatoric_uncertainty', [0.05] * len(X))
        })
        
        # Add prediction intervals if available
        if 'prediction_intervals' in locals():
            results_df['probability_lower_bound'] = prediction_intervals['lower_bounds']
            results_df['probability_upper_bound'] = prediction_intervals['upper_bounds']
            results_df['interval_width'] = prediction_intervals['interval_widths']
        
        # Add individual model contributions
        model_contributions = self.get_model_contributions(X)
        for contrib in model_contributions:
            model_name = contrib['model_name']
            results_df[f'{model_name}_probability'] = contrib['nda_probabilities']
            results_df[f'{model_name}_weight'] = contrib['weight']
        
        # Add metadata
        results_df['prediction_timestamp'] = datetime.now().isoformat()
        results_df['ensemble_method'] = 'bayesian' if use_bayesian else 'weighted_average'
        results_df['n_models_used'] = len(self.base_models)
        
        print(f"✅ Ensemble predictions complete: NDA {np.sum(ensemble_pred)} seats predicted")
        return results_df
    
    def evaluate_ensemble_comprehensive(self, X: pd.DataFrame, y: pd.Series,
                                      evaluation_metrics: List[str] = None) -> Dict:
        """Comprehensive ensemble evaluation with multiple metrics"""
        print("🔄 Performing comprehensive ensemble evaluation...")
        
        if evaluation_metrics is None:
            evaluation_metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 
                                'brier_score', 'log_loss', 'calibration']
        
        # Get ensemble predictions
        ensemble_pred, ensemble_prob, uncertainty_metrics = self.predict_with_uncertainty(X)
        
        # Calculate standard metrics
        evaluation_results = {}
        
        if 'accuracy' in evaluation_metrics:
            evaluation_results['accuracy'] = accuracy_score(y, ensemble_pred)
        
        if 'precision' in evaluation_metrics:
            evaluation_results['precision'] = precision_score(y, ensemble_pred, average='weighted')
        
        if 'recall' in evaluation_metrics:
            evaluation_results['recall'] = recall_score(y, ensemble_pred, average='weighted')
        
        if 'f1' in evaluation_metrics:
            evaluation_results['f1_score'] = f1_score(y, ensemble_pred, average='weighted')
        
        if 'roc_auc' in evaluation_metrics:
            try:
                evaluation_results['roc_auc'] = roc_auc_score(y, ensemble_prob[:, 1])
            except Exception as e:
                self.logger.warning(f"ROC AUC calculation failed: {e}")
                evaluation_results['roc_auc'] = None
        
        if 'brier_score' in evaluation_metrics:
            try:
                from sklearn.metrics import brier_score_loss
                evaluation_results['brier_score'] = brier_score_loss(y, ensemble_prob[:, 1])
            except Exception as e:
                self.logger.warning(f"Brier score calculation failed: {e}")
                evaluation_results['brier_score'] = None
        
        if 'log_loss' in evaluation_metrics:
            try:
                from sklearn.metrics import log_loss
                evaluation_results['log_loss'] = log_loss(y, ensemble_prob)
            except Exception as e:
                self.logger.warning(f"Log loss calculation failed: {e}")
                evaluation_results['log_loss'] = None
        
        # Calibration analysis
        if 'calibration' in evaluation_metrics:
            calibration_results = self._evaluate_calibration(y, ensemble_prob[:, 1])
            evaluation_results['calibration'] = calibration_results
        
        # Individual model comparison
        individual_results = {}
        for model_name, model in self.base_models.items():
            try:
                model_pred = model.predict(X)
                model_prob = model.predict_proba(X)
                
                individual_results[model_name] = {
                    'accuracy': accuracy_score(y, model_pred),
                    'f1_score': f1_score(y, model_pred, average='weighted'),
                    'roc_auc': roc_auc_score(y, model_prob[:, 1]) if model_prob.shape[1] > 1 else None
                }
            except Exception as e:
                self.logger.error(f"Error evaluating {model_name}: {e}")
                individual_results[model_name] = {'error': str(e)}
        
        # Uncertainty evaluation
        uncertainty_evaluation = self._evaluate_uncertainty_quality(y, ensemble_prob, uncertainty_metrics)
        
        # Ensemble diversity analysis
        model_predictions = {}
        for model_name, model in self.base_models.items():
            model_predictions[model_name] = model.predict(X)
        
        try:
            from src.modeling.bayesian_ensemble import BayesianEnsemble
            bayesian_ensemble = BayesianEnsemble()
            diversity_analysis = bayesian_ensemble.ensemble_diversity_analysis(model_predictions)
        except Exception as e:
            self.logger.warning(f"Diversity analysis failed: {e}")
            diversity_analysis = {'error': str(e)}
        
        # Compile comprehensive results
        comprehensive_results = {
            'ensemble_metrics': evaluation_results,
            'individual_model_metrics': individual_results,
            'uncertainty_evaluation': uncertainty_evaluation,
            'diversity_analysis': diversity_analysis,
            'ensemble_weights': self.ensemble_weights,
            'model_metadata': {
                'n_models': len(self.base_models),
                'model_types': list(self.base_models.keys()),
                'evaluation_samples': len(X),
                'positive_class_ratio': np.mean(y)
            },
            'evaluation_timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Comprehensive evaluation complete:")
        print(f"   Ensemble accuracy: {evaluation_results.get('accuracy', 'N/A'):.3f}")
        print(f"   Ensemble F1-score: {evaluation_results.get('f1_score', 'N/A'):.3f}")
        
        return comprehensive_results
    
    def _evaluate_calibration(self, y_true: np.ndarray, y_prob: np.ndarray, 
                            n_bins: int = 10) -> Dict:
        """Evaluate probability calibration quality"""
        from sklearn.calibration import calibration_curve
        
        try:
            # Calculate calibration curve
            fraction_of_positives, mean_predicted_value = calibration_curve(
                y_true, y_prob, n_bins=n_bins
            )
            
            # Calculate calibration metrics
            calibration_error = np.mean(np.abs(fraction_of_positives - mean_predicted_value))
            
            # Reliability (how close predicted probabilities are to actual frequencies)
            reliability = 1 - calibration_error
            
            # Resolution (ability to separate positive and negative cases)
            base_rate = np.mean(y_true)
            resolution = np.sum((mean_predicted_value - base_rate) ** 2 * 
                              np.histogram(y_prob, bins=n_bins)[0]) / len(y_prob)
            
            calibration_results = {
                'calibration_error': calibration_error,
                'reliability': reliability,
                'resolution': resolution,
                'fraction_of_positives': fraction_of_positives.tolist(),
                'mean_predicted_value': mean_predicted_value.tolist(),
                'n_bins': n_bins
            }
            
        except Exception as e:
            self.logger.error(f"Calibration evaluation failed: {e}")
            calibration_results = {'error': str(e)}
        
        return calibration_results
    
    def _evaluate_uncertainty_quality(self, y_true: np.ndarray, y_prob: np.ndarray,
                                    uncertainty_metrics: Dict) -> Dict:
        """Evaluate quality of uncertainty estimates"""
        
        # Get prediction correctness
        predictions = np.argmax(y_prob, axis=1)
        correct_predictions = (predictions == y_true).astype(int)
        
        # Analyze relationship between uncertainty and correctness
        uncertainty_evaluation = {}
        
        if 'prediction_variance' in uncertainty_metrics:
            variance = np.array(uncertainty_metrics['prediction_variance'])
            
            # Correlation between uncertainty and incorrectness
            uncertainty_correlation = np.corrcoef(variance, 1 - correct_predictions)[0, 1]
            uncertainty_evaluation['variance_correctness_correlation'] = uncertainty_correlation
        
        if 'model_agreement' in uncertainty_metrics:
            agreement = np.array(uncertainty_metrics['model_agreement'])
            
            # Correlation between agreement and correctness
            agreement_correlation = np.corrcoef(agreement, correct_predictions)[0, 1]
            uncertainty_evaluation['agreement_correctness_correlation'] = agreement_correlation
        
        if 'mean_confidence' in uncertainty_metrics:
            confidence = np.array(uncertainty_metrics['mean_confidence'])
            
            # Confidence-accuracy relationship
            confidence_correlation = np.corrcoef(confidence, correct_predictions)[0, 1]
            uncertainty_evaluation['confidence_correctness_correlation'] = confidence_correlation
        
        # Uncertainty calibration (are high uncertainty predictions actually more likely to be wrong?)
        try:
            max_probs = np.max(y_prob, axis=1)
            uncertainty_proxy = 1 - max_probs  # Higher uncertainty = lower max probability
            
            # Bin by uncertainty and calculate accuracy in each bin
            n_bins = 5
            bin_edges = np.linspace(0, 1, n_bins + 1)
            bin_accuracies = []
            bin_uncertainties = []
            
            for i in range(n_bins):
                mask = (uncertainty_proxy >= bin_edges[i]) & (uncertainty_proxy < bin_edges[i + 1])
                if np.sum(mask) > 0:
                    bin_accuracy = np.mean(correct_predictions[mask])
                    bin_uncertainty = np.mean(uncertainty_proxy[mask])
                    bin_accuracies.append(bin_accuracy)
                    bin_uncertainties.append(bin_uncertainty)
            
            uncertainty_evaluation['uncertainty_calibration'] = {
                'bin_accuracies': bin_accuracies,
                'bin_uncertainties': bin_uncertainties,
                'n_bins': n_bins
            }
            
        except Exception as e:
            self.logger.error(f"Uncertainty calibration evaluation failed: {e}")
        
        return uncertainty_evaluation
    
    def track_model_performance(self, new_performance: Dict) -> None:
        """Track model performance over time and update weights"""
        print("🔄 Tracking model performance...")
        
        # Update performance history
        timestamp = datetime.now().isoformat()
        
        if not hasattr(self, 'performance_history'):
            self.performance_history = {}
        
        self.performance_history[timestamp] = new_performance
        
        # Update ensemble weights based on recent performance
        self.update_ensemble_weights(new_performance)
        
        # Store updated metadata
        self.model_metadata['last_performance_update'] = timestamp
        self.model_metadata['performance_history_length'] = len(self.performance_history)
        
        print(f"   Performance tracking updated: {len(new_performance)} models")
    
    def generate_prediction_report(self, predictions_df: pd.DataFrame,
                                 include_details: bool = True) -> Dict:
        """Generate comprehensive prediction report"""
        print("🔄 Generating prediction report...")
        
        # Basic statistics
        nda_wins = np.sum(predictions_df['predicted_winner'] == 'NDA')
        indi_wins = np.sum(predictions_df['predicted_winner'] == 'INDI')
        total_seats = len(predictions_df)
        
        # Probability statistics
        nda_probs = predictions_df['nda_win_probability']
        mean_nda_prob = nda_probs.mean()
        median_nda_prob = nda_probs.median()
        
        # Uncertainty statistics
        if 'prediction_uncertainty' in predictions_df.columns:
            uncertainties = predictions_df['prediction_uncertainty']
            mean_uncertainty = uncertainties.mean()
            high_uncertainty_count = np.sum(uncertainties > uncertainties.quantile(0.75))
        else:
            mean_uncertainty = None
            high_uncertainty_count = None
        
        # Confidence statistics
        confidences = predictions_df['prediction_confidence']
        mean_confidence = confidences.mean()
        low_confidence_count = np.sum(confidences < 0.6)
        
        # Competitive seats (close probabilities)
        competitive_threshold = 0.1  # Within 10% of 50%
        competitive_seats = np.sum(np.abs(nda_probs - 0.5) < competitive_threshold)
        
        # Model agreement analysis
        if 'model_agreement' in predictions_df.columns:
            agreements = predictions_df['model_agreement']
            mean_agreement = agreements.mean()
            low_agreement_count = np.sum(agreements < 0.7)
        else:
            mean_agreement = None
            low_agreement_count = None
        
        # Create report
        report = {
            'summary': {
                'total_seats': total_seats,
                'nda_predicted_wins': nda_wins,
                'indi_predicted_wins': indi_wins,
                'nda_win_percentage': (nda_wins / total_seats) * 100,
                'competitive_seats': competitive_seats,
                'competitive_percentage': (competitive_seats / total_seats) * 100
            },
            'probability_statistics': {
                'mean_nda_probability': mean_nda_prob,
                'median_nda_probability': median_nda_prob,
                'min_nda_probability': nda_probs.min(),
                'max_nda_probability': nda_probs.max(),
                'std_nda_probability': nda_probs.std()
            },
            'confidence_statistics': {
                'mean_confidence': mean_confidence,
                'min_confidence': confidences.min(),
                'max_confidence': confidences.max(),
                'low_confidence_seats': low_confidence_count,
                'low_confidence_percentage': (low_confidence_count / total_seats) * 100
            },
            'uncertainty_statistics': {
                'mean_uncertainty': mean_uncertainty,
                'high_uncertainty_seats': high_uncertainty_count,
                'mean_model_agreement': mean_agreement,
                'low_agreement_seats': low_agreement_count
            },
            'ensemble_info': {
                'n_models_used': predictions_df['n_models_used'].iloc[0] if 'n_models_used' in predictions_df.columns else len(self.base_models),
                'ensemble_method': predictions_df['ensemble_method'].iloc[0] if 'ensemble_method' in predictions_df.columns else 'weighted_average',
                'model_weights': self.ensemble_weights
            },
            'report_timestamp': datetime.now().isoformat()
        }
        
        # Add detailed analysis if requested
        if include_details:
            # Top uncertain predictions
            if 'prediction_uncertainty' in predictions_df.columns:
                uncertain_seats = predictions_df.nlargest(10, 'prediction_uncertainty')[
                    ['constituency', 'predicted_winner', 'nda_win_probability', 'prediction_uncertainty']
                ].to_dict('records')
                report['most_uncertain_seats'] = uncertain_seats
            
            # Most competitive seats
            predictions_df['competitiveness'] = np.abs(predictions_df['nda_win_probability'] - 0.5)
            competitive_seats = predictions_df.nsmallest(10, 'competitiveness')[
                ['constituency', 'predicted_winner', 'nda_win_probability', 'competitiveness']
            ].to_dict('records')
            report['most_competitive_seats'] = competitive_seats
            
            # Safest predictions
            safe_seats = predictions_df.nlargest(10, 'prediction_confidence')[
                ['constituency', 'predicted_winner', 'nda_win_probability', 'prediction_confidence']
            ].to_dict('records')
            report['safest_predictions'] = safe_seats
        
        print(f"✅ Prediction report generated: {nda_wins} NDA, {indi_wins} INDI seats predicted")
        return report

    def get_ensemble_summary(self) -> Dict:
        """Get summary of current ensemble state"""
        return {
            'n_models': len(self.base_models),
            'model_types': list(self.base_models.keys()),
            'ensemble_weights': self.ensemble_weights,
            'validation_scores': self.validation_scores,
            'metadata': self.model_metadata,
            'is_trained': len(self.base_models) > 0
        }