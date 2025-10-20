import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from src.config.settings import Config
import json
import joblib
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')


class ModelUpdater:
    """Advanced model management with persistence and incremental updates"""
    
    def __init__(self):
        self.models_dir = Config.MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.model_metadata = {}
        
        print(f"✅ Model updater initialized at {self.models_dir}")
    
    def create_initial_model(self, features_df: pd.DataFrame) -> Any:
        """Create initial RandomForest model for Bihar election prediction"""
        print("🔄 Creating initial RandomForest model...")
        
        # Prepare features and targets
        X, y = self._prepare_training_data(features_df)
        
        # Create RandomForest with optimized parameters for election prediction
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features='sqrt',
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        
        # Train the model
        model.fit(X, y)
        
        # Calibrate probabilities
        calibrated_model = CalibratedClassifierCV(model, method='isotonic', cv=3)
        calibrated_model.fit(X, y)
        
        # Evaluate model
        cv_scores = cross_val_score(calibrated_model, X, y, cv=5, scoring='accuracy')
        
        # Store model and metadata
        self.model = calibrated_model
        self.model_metadata = {
            'model_type': 'RandomForestClassifier',
            'calibrated': True,
            'n_estimators': 200,
            'features_count': len(X.columns),
            'training_samples': len(X),
            'cv_accuracy': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'created_at': datetime.now().isoformat(),
            'feature_names': list(X.columns)
        }
        
        print(f"✅ Model created with {cv_scores.mean():.3f} ± {cv_scores.std():.3f} CV accuracy")
        return self.model
    
    def _prepare_training_data(self, features_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data from features"""
        # Select relevant features for training
        feature_columns = [
            'nda_share_2020', 'indi_share_2020', 'nda_margin_2020', 'turnout_2020',
            'social_sentiment_nda', 'social_sentiment_indi', 'news_sentiment_nda', 'news_sentiment_indi',
            'poll_lead_nda', 'poll_momentum_nda', 'poll_volatility',
            'urban_percentage', 'rural_percentage', 'literacy_rate', 'development_index',
            'employment_rate', 'caste_diversity_index', 'religious_diversity_index',
            'campaign_intensity_nda', 'campaign_intensity_indi'
        ]
        
        # Add derived features if they exist
        derived_features = [
            'combined_sentiment_nda', 'combined_sentiment_indi', 'sentiment_advantage_nda',
            'total_advantage_nda', 'competitiveness', 'volatility_score'
        ]
        
        available_features = [col for col in feature_columns + derived_features if col in features_df.columns]
        
        X = features_df[available_features].copy()
        
        # Handle missing values
        X = X.fillna(X.mean())
        
        # Create target variable (NDA win = 1, INDI win = 0)
        # Use win probability as proxy for actual results
        win_prob_col = 'nda_win_prob' if 'nda_win_prob' in features_df.columns else 'final_nda_prob'
        if win_prob_col in features_df.columns:
            y = (features_df[win_prob_col] > 0.5).astype(int)
        else:
            # Fallback: use poll lead
            y = (features_df['poll_lead_nda'] > 0).astype(int)
        
        print(f"   Training data: {len(X)} samples, {len(X.columns)} features")
        print(f"   Target distribution: NDA {y.sum()}, INDI {len(y) - y.sum()}")
        
        return X, y
    
    def save_model(self, version: str = None) -> str:
        """Save model with versioning"""
        if self.model is None:
            raise ValueError("No model to save")
        
        if version is None:
            version = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save model
        model_path = self.models_dir / f"model_{version}.joblib"
        joblib.dump(self.model, model_path)
        
        # Save metadata
        metadata_path = self.models_dir / f"metadata_{version}.json"
        full_metadata = {
            **self.model_metadata,
            'version': version,
            'saved_at': datetime.now().isoformat(),
            'model_path': str(model_path),
            'model_size_mb': model_path.stat().st_size / (1024 * 1024)
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(full_metadata, f, indent=2)
        
        # Update latest symlink
        latest_path = self.models_dir / "latest_model.joblib"
        if latest_path.exists():
            latest_path.unlink()
        joblib.dump(self.model, latest_path)
        
        print(f"✅ Saved model version {version} ({full_metadata['model_size_mb']:.1f} MB)")
        return version
    
    def load_model(self, version: str = "latest") -> Any:
        """Load model by version"""
        if version == "latest":
            model_path = self.models_dir / "latest_model.joblib"
            metadata_path = None
        else:
            model_path = self.models_dir / f"model_{version}.joblib"
            metadata_path = self.models_dir / f"metadata_{version}.json"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model version {version} not found")
        
        # Load model
        self.model = joblib.load(model_path)
        
        # Load metadata if available
        if metadata_path and metadata_path.exists():
            with open(metadata_path) as f:
                self.model_metadata = json.load(f)
        
        print(f"✅ Loaded model version {version}")
        return self.model
    
    def incremental_update(self, new_features_df: pd.DataFrame, update_method: str = "retrain") -> str:
        """Perform incremental model update"""
        if self.model is None:
            print("No existing model found, creating new model...")
            self.create_initial_model(new_features_df)
            return self.save_model()
        
        print(f"🔄 Performing incremental update using {update_method} method...")
        
        X_new, y_new = self._prepare_training_data(new_features_df)
        
        if update_method == "retrain":
            # Full retrain with new data
            updated_model = self._retrain_model(X_new, y_new)
        elif update_method == "ensemble":
            # Create ensemble with existing model
            updated_model = self._ensemble_update(X_new, y_new)
        else:
            raise ValueError(f"Unknown update method: {update_method}")
        
        # Evaluate updated model
        cv_scores = cross_val_score(updated_model, X_new, y_new, cv=3, scoring='accuracy')
        
        # Update model and metadata
        old_accuracy = self.model_metadata.get('cv_accuracy', 0)
        new_accuracy = cv_scores.mean()
        
        self.model = updated_model
        self.model_metadata.update({
            'last_updated': datetime.now().isoformat(),
            'update_method': update_method,
            'previous_accuracy': old_accuracy,
            'cv_accuracy': new_accuracy,
            'accuracy_improvement': new_accuracy - old_accuracy,
            'update_samples': len(X_new)
        })
        
        print(f"   Model updated: {old_accuracy:.3f} → {new_accuracy:.3f} accuracy ({new_accuracy - old_accuracy:+.3f})")
        
        return self.save_model()
    
    def _retrain_model(self, X: pd.DataFrame, y: pd.Series) -> Any:
        """Retrain model with new data"""
        # Create new model with same parameters
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features='sqrt',
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        
        # Train and calibrate
        model.fit(X, y)
        calibrated_model = CalibratedClassifierCV(model, method='isotonic', cv=3)
        calibrated_model.fit(X, y)
        
        return calibrated_model
    
    def _ensemble_update(self, X: pd.DataFrame, y: pd.Series) -> Any:
        """Create ensemble with existing and new model"""
        # Train new model on new data
        new_model = self._retrain_model(X, y)
        
        # Create simple ensemble (average predictions)
        class EnsembleModel:
            def __init__(self, model1, model2):
                self.model1 = model1
                self.model2 = model2
            
            def predict(self, X):
                pred1 = self.model1.predict(X)
                pred2 = self.model2.predict(X)
                return (pred1 + pred2) / 2
            
            def predict_proba(self, X):
                prob1 = self.model1.predict_proba(X)
                prob2 = self.model2.predict_proba(X)
                return (prob1 + prob2) / 2
        
        return EnsembleModel(self.model, new_model)
    
    def predict_constituencies(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Generate predictions for all constituencies"""
        if self.model is None:
            raise ValueError("No model loaded")
        
        print(f"🔄 Generating predictions for {len(features_df)} constituencies...")
        
        # Prepare features
        X, _ = self._prepare_training_data(features_df)
        
        # Generate predictions
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        
        # Create results dataframe
        results_df = features_df[['constituency', 'region']].copy()
        results_df['predicted_winner'] = ['NDA' if p == 1 else 'INDI' for p in predictions]
        results_df['nda_win_probability'] = probabilities[:, 1]  # Probability of NDA win
        results_df['indi_win_probability'] = probabilities[:, 0]  # Probability of INDI win
        results_df['prediction_confidence'] = np.max(probabilities, axis=1)
        results_df['prediction_timestamp'] = datetime.now().isoformat()
        
        print(f"✅ Predictions generated: NDA {(predictions == 1).sum()}, INDI {(predictions == 0).sum()}")
        
        return results_df
    
    def evaluate_model(self, features_df: pd.DataFrame) -> Dict:
        """Comprehensive model evaluation"""
        if self.model is None:
            raise ValueError("No model loaded")
        
        X, y = self._prepare_training_data(features_df)
        
        # Generate predictions
        y_pred = self.model.predict(X)
        y_prob = self.model.predict_proba(X)
        
        # Calculate metrics
        evaluation = {
            'timestamp': datetime.now().isoformat(),
            'model_version': self.model_metadata.get('version', 'unknown'),
            'test_samples': len(X),
            'metrics': {
                'accuracy': accuracy_score(y, y_pred),
                'precision': precision_score(y, y_pred, average='weighted'),
                'recall': recall_score(y, y_pred, average='weighted'),
                'f1_score': f1_score(y, y_pred, average='weighted')
            },
            'class_distribution': {
                'actual_nda': int(y.sum()),
                'actual_indi': int(len(y) - y.sum()),
                'predicted_nda': int(y_pred.sum()),
                'predicted_indi': int(len(y_pred) - y_pred.sum())
            },
            'probability_stats': {
                'mean_nda_prob': float(y_prob[:, 1].mean()),
                'std_nda_prob': float(y_prob[:, 1].std()),
                'min_confidence': float(np.max(y_prob, axis=1).min()),
                'max_confidence': float(np.max(y_prob, axis=1).max()),
                'avg_confidence': float(np.max(y_prob, axis=1).mean())
            }
        }
        
        return evaluation
    
    def get_feature_importance(self) -> Dict:
        """Get feature importance from the model"""
        if self.model is None:
            raise ValueError("No model loaded")
        
        # Extract base model from calibrated classifier
        base_model = self.model.base_estimator if hasattr(self.model, 'base_estimator') else self.model
        
        if hasattr(base_model, 'feature_importances_'):
            feature_names = self.model_metadata.get('feature_names', [])
            importances = base_model.feature_importances_
            
            # Create importance dictionary
            importance_dict = dict(zip(feature_names, importances))
            
            # Sort by importance
            sorted_importance = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            
            return {
                'timestamp': datetime.now().isoformat(),
                'model_version': self.model_metadata.get('version', 'unknown'),
                'feature_importance': sorted_importance,
                'top_5_features': list(sorted_importance.keys())[:5]
            }
        else:
            return {'error': 'Model does not support feature importance'}
    
    def list_model_versions(self) -> List[Dict]:
        """List all available model versions"""
        versions = []
        
        for metadata_file in self.models_dir.glob("metadata_*.json"):
            try:
                with open(metadata_file) as f:
                    metadata = json.load(f)
                versions.append(metadata)
            except Exception as e:
                print(f"Error reading {metadata_file}: {e}")
        
        # Sort by creation date
        versions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return versions
    
    def cleanup_old_models(self, keep_count: int = 5) -> int:
        """Clean up old model versions"""
        versions = self.list_model_versions()
        
        if len(versions) <= keep_count:
            print("No old models to clean up")
            return 0
        
        # Keep the most recent versions
        versions_to_delete = versions[keep_count:]
        deleted_count = 0
        
        for version in versions_to_delete:
            try:
                version_name = version['version']
                
                # Delete model file
                model_file = self.models_dir / f"model_{version_name}.joblib"
                if model_file.exists():
                    model_file.unlink()
                
                # Delete metadata file
                metadata_file = self.models_dir / f"metadata_{version_name}.json"
                if metadata_file.exists():
                    metadata_file.unlink()
                
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting model version {version.get('version', 'unknown')}: {e}")
        
        print(f"✅ Cleaned up {deleted_count} old model versions")
        return deleted_count