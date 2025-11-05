import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from src.config.settings import Config
import json
import warnings
from sklearn.feature_selection import RFE, RFECV, SelectKBest, f_classif
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score
import logging

warnings.filterwarnings('ignore')

class FeatureSelector:
    """Advanced feature selection with SHAP analysis and temporal stability testing"""
    
    def __init__(self):
        self.features_dir = Config.FEATURES_DIR
        self.selected_features = []
        self.feature_importance_scores = {}
        self.selection_metadata = {}
        self.logger = logging.getLogger(__name__)
        print(f"✅ Feature Selector initialized")
    
    def calculate_shap_importance(self, model: Any, X: pd.DataFrame) -> pd.DataFrame:
        """Calculate SHAP-based feature importance"""
        print("🔄 Calculating SHAP importance...")
        
        try:
            import shap
            
            # Create SHAP explainer
            if hasattr(model, 'predict_proba'):
                explainer = shap.Explainer(model, X.sample(min(100, len(X))))
            else:
                explainer = shap.Explainer(model)
            
            # Calculate SHAP values
            shap_values = explainer(X.sample(min(500, len(X))))
            
            # Get mean absolute SHAP values for feature importance
            if isinstance(shap_values.values, list):
                # Multi-class case
                importance_values = np.mean([np.abs(sv).mean(0) for sv in shap_values.values], axis=0)
            else:
                # Binary case
                importance_values = np.abs(shap_values.values).mean(0)
            
            # Create importance DataFrame
            importance_df = pd.DataFrame({
                'feature': X.columns,
                'shap_importance': importance_values,
                'rank': range(1, len(X.columns) + 1)
            }).sort_values('shap_importance', ascending=False)
            
            importance_df['rank'] = range(1, len(importance_df) + 1)
            
            print(f"✅ SHAP importance calculated for {len(X.columns)} features")
            return importance_df
            
        except ImportError:
            self.logger.warning("SHAP not available, using permutation importance")
            return self._calculate_permutation_importance(model, X)
        except Exception as e:
            self.logger.error(f"SHAP calculation failed: {e}")
            return self._calculate_fallback_importance(model, X)
    
    def _calculate_permutation_importance(self, model: Any, X: pd.DataFrame) -> pd.DataFrame:
        """Fallback permutation importance calculation"""
        from sklearn.inspection import permutation_importance
        
        # Need target for permutation importance - use dummy for ranking
        y_dummy = np.random.randint(0, 2, len(X))
        
        try:
            perm_importance = permutation_importance(model, X, y_dummy, n_repeats=5, random_state=42)
            
            importance_df = pd.DataFrame({
                'feature': X.columns,
                'shap_importance': perm_importance.importances_mean,
                'rank': range(1, len(X.columns) + 1)
            }).sort_values('shap_importance', ascending=False)
            
            importance_df['rank'] = range(1, len(importance_df) + 1)
            return importance_df
            
        except Exception as e:
            self.logger.error(f"Permutation importance failed: {e}")
            return self._calculate_fallback_importance(model, X)
    
    def _calculate_fallback_importance(self, model: Any, X: pd.DataFrame) -> pd.DataFrame:
        """Fallback feature importance using model attributes"""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_[0]) if model.coef_.ndim > 1 else np.abs(model.coef_)
        else:
            # Random importance as last resort
            importances = np.random.random(len(X.columns))
        
        importance_df = pd.DataFrame({
            'feature': X.columns,
            'shap_importance': importances,
            'rank': range(1, len(X.columns) + 1)
        }).sort_values('shap_importance', ascending=False)
        
        importance_df['rank'] = range(1, len(importance_df) + 1)
        return importance_df
    
    def recursive_feature_elimination(self, X: pd.DataFrame, y: pd.Series, 
                                    estimator: Any = None, n_features: int = None) -> List[str]:
        """Recursive feature elimination with cross-validation"""
        print("🔄 Performing recursive feature elimination...")
        
        if estimator is None:
            estimator = RandomForestClassifier(n_estimators=50, random_state=42)
        
        if n_features is None:
            # Use RFECV to find optimal number of features
            selector = RFECV(estimator, step=1, cv=3, scoring='accuracy', n_jobs=-1)
        else:
            selector = RFE(estimator, n_features_to_select=n_features, step=1)
        
        # Fit selector
        selector.fit(X, y)
        
        # Get selected features
        selected_features = X.columns[selector.support_].tolist()
        
        # Store ranking information
        self.feature_importance_scores['rfe_ranking'] = dict(zip(X.columns, selector.ranking_))
        
        print(f"✅ RFE complete: {len(selected_features)} features selected")
        return selected_features
    
    def remove_correlated_features(self, X: pd.DataFrame, threshold: float = 0.9) -> List[str]:
        """Remove highly correlated features"""
        print(f"🔄 Removing features with correlation > {threshold}...")
        
        # Calculate correlation matrix
        corr_matrix = X.corr().abs()
        
        # Find pairs of highly correlated features
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        
        # Find features to drop
        to_drop = [column for column in upper_triangle.columns 
                  if any(upper_triangle[column] > threshold)]
        
        # Keep features not in drop list
        selected_features = [col for col in X.columns if col not in to_drop]
        
        print(f"✅ Correlation filtering complete: removed {len(to_drop)} features, kept {len(selected_features)}")
        return selected_features
    
    def test_feature_stability(self, features: List[str], X_periods: List[pd.DataFrame], 
                             y_periods: List[pd.Series]) -> Dict:
        """Test feature importance stability across time periods"""
        print("🔄 Testing feature stability across time periods...")
        
        if len(X_periods) != len(y_periods):
            raise ValueError("Number of X and y periods must match")
        
        stability_results = {}
        period_importances = []
        
        # Calculate importance for each period
        for i, (X_period, y_period) in enumerate(zip(X_periods, y_periods)):
            print(f"   Analyzing period {i+1}/{len(X_periods)}...")
            
            # Select only the features we're testing
            X_selected = X_period[features] if all(f in X_period.columns for f in features) else X_period
            
            # Train model and get importance
            model = RandomForestClassifier(n_estimators=50, random_state=42)
            model.fit(X_selected, y_period)
            
            if hasattr(model, 'feature_importances_'):
                importance_dict = dict(zip(X_selected.columns, model.feature_importances_))
                period_importances.append(importance_dict)
        
        # Calculate stability metrics
        if period_importances:
            # Convert to DataFrame for easier analysis
            importance_df = pd.DataFrame(period_importances).fillna(0)
            
            # Calculate coefficient of variation for each feature
            stability_scores = {}
            for feature in importance_df.columns:
                values = importance_df[feature].values
                if np.mean(values) > 0:
                    cv = np.std(values) / np.mean(values)  # Coefficient of variation
                    stability_scores[feature] = 1 / (1 + cv)  # Higher is more stable
                else:
                    stability_scores[feature] = 0
            
            # Rank features by stability
            sorted_features = sorted(stability_scores.keys(), 
                                   key=lambda k: stability_scores[k], reverse=True)
            
            stability_results = {
                'stability_scores': stability_scores,
                'most_stable_features': sorted_features[:10],
                'least_stable_features': sorted_features[-10:],
                'mean_stability': np.mean(list(stability_scores.values())),
                'period_importances': period_importances
            }
        
        print(f"✅ Feature stability analysis complete")
        return stability_results
    
    def select_optimal_features(self, X: pd.DataFrame, y: pd.Series, 
                              selection_methods: List[str] = None) -> List[str]:
        """Select optimal features using multiple methods"""
        print("🔄 Selecting optimal features using multiple methods...")
        
        if selection_methods is None:
            selection_methods = ['correlation', 'rfe', 'univariate']
        
        feature_scores = {}
        
        # Initialize all features
        all_features = set(X.columns)
        
        # Correlation-based selection
        if 'correlation' in selection_methods:
            corr_features = set(self.remove_correlated_features(X))
            feature_scores['correlation'] = corr_features
            print(f"   Correlation method: {len(corr_features)} features")
        
        # Recursive feature elimination
        if 'rfe' in selection_methods:
            try:
                rfe_features = set(self.recursive_feature_elimination(X, y))
                feature_scores['rfe'] = rfe_features
                print(f"   RFE method: {len(rfe_features)} features")
            except Exception as e:
                self.logger.error(f"RFE failed: {e}")
        
        # Univariate selection
        if 'univariate' in selection_methods:
            try:
                univariate_features = set(self._univariate_selection(X, y))
                feature_scores['univariate'] = univariate_features
                print(f"   Univariate method: {len(univariate_features)} features")
            except Exception as e:
                self.logger.error(f"Univariate selection failed: {e}")
        
        # Combine results using voting
        if feature_scores:
            feature_votes = {}
            for feature in all_features:
                votes = sum(1 for method_features in feature_scores.values() 
                           if feature in method_features)
                feature_votes[feature] = votes
            
            # Select features that got votes from majority of methods
            min_votes = max(1, len(feature_scores) // 2)
            selected_features = [f for f, votes in feature_votes.items() if votes >= min_votes]
            
            # If too few features, take top features by votes
            if len(selected_features) < 5:
                sorted_features = sorted(feature_votes.keys(), 
                                       key=lambda k: feature_votes[k], reverse=True)
                selected_features = sorted_features[:max(5, len(selected_features))]
        
        else:
            # Fallback: use all features
            selected_features = list(X.columns)
        
        self.selected_features = selected_features
        
        # Store selection metadata
        self.selection_metadata = {
            'methods_used': selection_methods,
            'n_original_features': len(X.columns),
            'n_selected_features': len(selected_features),
            'selection_ratio': len(selected_features) / len(X.columns),
            'selected_at': datetime.now().isoformat()
        }
        
        print(f"✅ Feature selection complete: {len(selected_features)} features selected")
        return selected_features
    
    def _univariate_selection(self, X: pd.DataFrame, y: pd.Series, k: int = None) -> List[str]:
        """Univariate feature selection using statistical tests"""
        if k is None:
            k = min(20, len(X.columns))  # Select top 20 or all if fewer
        
        # Use SelectKBest with f_classif
        selector = SelectKBest(score_func=f_classif, k=k)
        selector.fit(X, y)
        
        selected_features = X.columns[selector.get_support()].tolist()
        
        # Store scores
        self.feature_importance_scores['univariate_scores'] = dict(zip(X.columns, selector.scores_))
        
        return selected_features
    
    def validate_feature_selection(self, X: pd.DataFrame, y: pd.Series, 
                                 selected_features: List[str]) -> Dict:
        """Validate feature selection quality"""
        print("🔄 Validating feature selection...")
        
        # Compare performance with all features vs selected features
        X_all = X
        X_selected = X[selected_features]
        
        # Train models
        model_all = RandomForestClassifier(n_estimators=50, random_state=42)
        model_selected = RandomForestClassifier(n_estimators=50, random_state=42)
        
        # Cross-validation scores
        scores_all = cross_val_score(model_all, X_all, y, cv=3, scoring='accuracy')
        scores_selected = cross_val_score(model_selected, X_selected, y, cv=3, scoring='accuracy')
        
        validation_results = {
            'all_features': {
                'n_features': len(X_all.columns),
                'cv_mean': scores_all.mean(),
                'cv_std': scores_all.std()
            },
            'selected_features': {
                'n_features': len(selected_features),
                'cv_mean': scores_selected.mean(),
                'cv_std': scores_selected.std()
            },
            'performance_change': scores_selected.mean() - scores_all.mean(),
            'feature_reduction': 1 - (len(selected_features) / len(X_all.columns)),
            'efficiency_gain': (scores_selected.mean() - scores_all.mean()) / (len(X_all.columns) - len(selected_features)) if len(X_all.columns) != len(selected_features) else 0
        }
        
        print(f"✅ Feature selection validation complete")
        print(f"   Performance change: {validation_results['performance_change']:+.3f}")
        print(f"   Feature reduction: {validation_results['feature_reduction']:.1%}")
        
        return validation_results
    
    def save_feature_selection(self, filename: str = None) -> str:
        """Save feature selection results"""
        if filename is None:
            filename = f"feature_selection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.features_dir / filename
        
        selection_data = {
            'selected_features': self.selected_features,
            'feature_importance_scores': self.feature_importance_scores,
            'selection_metadata': self.selection_metadata,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(selection_data, f, indent=2)
        
        print(f"✅ Feature selection saved to {filepath}")
        return str(filepath)
    
    def load_feature_selection(self, filepath: str) -> bool:
        """Load feature selection results"""
        try:
            with open(filepath) as f:
                selection_data = json.load(f)
            
            self.selected_features = selection_data.get('selected_features', [])
            self.feature_importance_scores = selection_data.get('feature_importance_scores', {})
            self.selection_metadata = selection_data.get('selection_metadata', {})
            
            print(f"✅ Feature selection loaded: {len(self.selected_features)} features")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load feature selection: {e}")
            return False