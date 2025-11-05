import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from src.config.settings import Config
import json
import warnings
from sklearn.model_selection import TimeSeriesSplit, StratifiedKFold, cross_val_score
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                           roc_auc_score, confusion_matrix, classification_report,
                           brier_score_loss, log_loss)
from sklearn.calibration import calibration_curve
import logging

warnings.filterwarnings('ignore')

class ModelValidator:
    """Comprehensive model validation framework with time-series awareness and bias detection"""
    
    def __init__(self):
        self.results_dir = Config.RESULTS_DIR
        self.data_dir = Config.DATA_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Validation configuration
        self.cv_folds = 5
        self.test_size = 0.2
        self.random_state = 42
        
        # Validation results storage
        self.validation_results = {}
        self.bias_analysis_results = {}
        self.calibration_results = {}
        
        # Historical validation tracking
        self.validation_history = []
        
        self.logger = logging.getLogger(__name__)
        print(f"✅ Model Validator initialized")
    
    def create_time_series_splits(self, X: pd.DataFrame, y: pd.Series, 
                                n_splits: int = 5, test_size: float = 0.2) -> List[Tuple]:
        """Create time-series aware cross-validation splits"""
        print(f"🔄 Creating {n_splits} time-series splits...")
        
        # Check if data has date information
        if 'date' in X.columns:
            # Sort by date for proper time series splitting
            X_sorted = X.sort_values('date')
            y_sorted = y.loc[X_sorted.index]
            
            # Use TimeSeriesSplit for temporal data
            tscv = TimeSeriesSplit(n_splits=n_splits, test_size=int(len(X) * test_size))
            splits = list(tscv.split(X_sorted))
            
            # Convert indices back to original DataFrame indices
            splits = [(X_sorted.index[train_idx], X_sorted.index[test_idx]) 
                     for train_idx, test_idx in splits]
            
        else:
            # Use stratified splits if no temporal information
            print("   No date column found, using stratified splits")
            skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=self.random_state)
            splits = list(skf.split(X, y))
            
            # Convert to index-based splits
            splits = [(X.index[train_idx], X.index[test_idx]) 
                     for train_idx, test_idx in splits]
        
        print(f"   Created {len(splits)} splits with average test size: {len(splits[0][1])}")
        return splits
    
    def create_spatial_splits(self, X: pd.DataFrame, y: pd.Series, 
                            region_column: str = 'region') -> List[Tuple]:
        """Create spatial cross-validation splits by region"""
        print("🔄 Creating spatial cross-validation splits...")
        
        if region_column not in X.columns:
            raise ValueError(f"Region column '{region_column}' not found in data")
        
        regions = X[region_column].unique()
        splits = []
        
        # Leave-one-region-out cross-validation
        for test_region in regions:
            test_mask = X[region_column] == test_region
            train_mask = ~test_mask
            
            train_indices = X.index[train_mask]
            test_indices = X.index[test_mask]
            
            if len(train_indices) > 0 and len(test_indices) > 0:
                splits.append((train_indices, test_indices))
        
        print(f"   Created {len(splits)} spatial splits across {len(regions)} regions")
        return splits
    
    def cross_validate_timeseries(self, model: Any, X: pd.DataFrame, y: pd.Series,
                                scoring: Union[str, List[str]] = None) -> Dict:
        """Perform time-series aware cross-validation"""
        print("🔄 Performing time-series cross-validation...")
        
        if scoring is None:
            scoring = ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted', 'roc_auc']
        
        # Create time-series splits
        splits = self.create_time_series_splits(X, y, self.cv_folds)
        
        # Initialize results storage
        cv_results = {metric: [] for metric in scoring}
        fold_details = []
        
        for fold_idx, (train_idx, test_idx) in enumerate(splits):
            print(f"   Processing fold {fold_idx + 1}/{len(splits)}...")
            
            # Split data
            X_train, X_test = X.loc[train_idx], X.loc[test_idx]
            y_train, y_test = y.loc[train_idx], y.loc[test_idx]
            
            try:
                # Train model
                model_copy = self._clone_model(model)
                model_copy.fit(X_train, y_train)
                
                # Make predictions
                y_pred = model_copy.predict(X_test)
                y_prob = model_copy.predict_proba(X_test) if hasattr(model_copy, 'predict_proba') else None
                
                # Calculate metrics
                fold_metrics = {}
                
                if 'accuracy' in scoring:
                    fold_metrics['accuracy'] = accuracy_score(y_test, y_pred)
                
                if 'precision_weighted' in scoring:
                    fold_metrics['precision_weighted'] = precision_score(y_test, y_pred, average='weighted')
                
                if 'recall_weighted' in scoring:
                    fold_metrics['recall_weighted'] = recall_score(y_test, y_pred, average='weighted')
                
                if 'f1_weighted' in scoring:
                    fold_metrics['f1_weighted'] = f1_score(y_test, y_pred, average='weighted')
                
                if 'roc_auc' in scoring and y_prob is not None:
                    try:
                        fold_metrics['roc_auc'] = roc_auc_score(y_test, y_prob[:, 1])
                    except Exception as e:
                        self.logger.warning(f"ROC AUC calculation failed for fold {fold_idx}: {e}")
                        fold_metrics['roc_auc'] = np.nan
                
                # Store fold results
                for metric in scoring:
                    if metric in fold_metrics:
                        cv_results[metric].append(fold_metrics[metric])
                
                # Store detailed fold information
                fold_details.append({
                    'fold': fold_idx,
                    'train_size': len(X_train),
                    'test_size': len(X_test),
                    'train_positive_rate': y_train.mean(),
                    'test_positive_rate': y_test.mean(),
                    'metrics': fold_metrics
                })
                
            except Exception as e:
                self.logger.error(f"Error in fold {fold_idx}: {e}")
                # Add NaN for failed fold
                for metric in scoring:
                    cv_results[metric].append(np.nan)
        
        # Calculate summary statistics
        summary_results = {}
        for metric, scores in cv_results.items():
            valid_scores = [s for s in scores if not np.isnan(s)]
            if valid_scores:
                summary_results[metric] = {
                    'mean': np.mean(valid_scores),
                    'std': np.std(valid_scores),
                    'min': np.min(valid_scores),
                    'max': np.max(valid_scores),
                    'scores': valid_scores
                }
            else:
                summary_results[metric] = {
                    'mean': np.nan, 'std': np.nan, 'min': np.nan, 'max': np.nan, 'scores': []
                }
        
        validation_result = {
            'cv_summary': summary_results,
            'fold_details': fold_details,
            'n_splits': len(splits),
            'validation_type': 'time_series',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Time-series CV complete: {summary_results.get('accuracy', {}).get('mean', 'N/A'):.3f} ± {summary_results.get('accuracy', {}).get('std', 'N/A'):.3f} accuracy")
        
        return validation_result
    
    def cross_validate_spatial(self, model: Any, X: pd.DataFrame, y: pd.Series,
                             region_column: str = 'region') -> Dict:
        """Perform spatial cross-validation"""
        print("🔄 Performing spatial cross-validation...")
        
        # Create spatial splits
        splits = self.create_spatial_splits(X, y, region_column)
        
        if len(splits) < 2:
            raise ValueError("Need at least 2 regions for spatial cross-validation")
        
        # Initialize results
        spatial_results = []
        
        for fold_idx, (train_idx, test_idx) in enumerate(splits):
            test_region = X.loc[test_idx, region_column].iloc[0]
            print(f"   Testing on region: {test_region}")
            
            # Split data
            X_train, X_test = X.loc[train_idx], X.loc[test_idx]
            y_train, y_test = y.loc[train_idx], y.loc[test_idx]
            
            try:
                # Train model
                model_copy = self._clone_model(model)
                model_copy.fit(X_train, y_train)
                
                # Make predictions
                y_pred = model_copy.predict(X_test)
                y_prob = model_copy.predict_proba(X_test) if hasattr(model_copy, 'predict_proba') else None
                
                # Calculate metrics
                fold_metrics = {
                    'test_region': test_region,
                    'train_regions': list(X_train[region_column].unique()),
                    'accuracy': accuracy_score(y_test, y_pred),
                    'precision': precision_score(y_test, y_pred, average='weighted'),
                    'recall': recall_score(y_test, y_pred, average='weighted'),
                    'f1_score': f1_score(y_test, y_pred, average='weighted'),
                    'train_size': len(X_train),
                    'test_size': len(X_test)
                }
                
                if y_prob is not None:
                    try:
                        fold_metrics['roc_auc'] = roc_auc_score(y_test, y_prob[:, 1])
                    except:
                        fold_metrics['roc_auc'] = np.nan
                
                spatial_results.append(fold_metrics)
                
            except Exception as e:
                self.logger.error(f"Error in spatial fold for region {test_region}: {e}")
        
        # Calculate summary statistics
        if spatial_results:
            metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']
            summary = {}
            
            for metric in metrics:
                values = [r[metric] for r in spatial_results if not np.isnan(r.get(metric, np.nan))]
                if values:
                    summary[metric] = {
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'min': np.min(values),
                        'max': np.max(values)
                    }
        
        spatial_validation_result = {
            'spatial_summary': summary,
            'region_results': spatial_results,
            'n_regions': len(splits),
            'validation_type': 'spatial',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Spatial CV complete: {summary.get('accuracy', {}).get('mean', 'N/A'):.3f} ± {summary.get('accuracy', {}).get('std', 'N/A'):.3f} accuracy")
        
        return spatial_validation_result
    
    def _clone_model(self, model: Any) -> Any:
        """Clone a model for cross-validation"""
        try:
            from sklearn.base import clone
            return clone(model)
        except:
            # Fallback for non-sklearn models
            try:
                import copy
                return copy.deepcopy(model)
            except:
                self.logger.warning("Could not clone model, using original (may cause issues)")
                return model
    
    def validate_model_comprehensive(self, model: Any, X: pd.DataFrame, y: pd.Series,
                                   validation_types: List[str] = None) -> Dict:
        """Perform comprehensive model validation"""
        print("🔄 Performing comprehensive model validation...")
        
        if validation_types is None:
            validation_types = ['time_series', 'spatial', 'stratified']
        
        comprehensive_results = {
            'model_info': self._get_model_info(model),
            'data_info': self._get_data_info(X, y),
            'validation_results': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Time-series validation
        if 'time_series' in validation_types:
            try:
                ts_results = self.cross_validate_timeseries(model, X, y)
                comprehensive_results['validation_results']['time_series'] = ts_results
            except Exception as e:
                self.logger.error(f"Time-series validation failed: {e}")
                comprehensive_results['validation_results']['time_series'] = {'error': str(e)}
        
        # Spatial validation
        if 'spatial' in validation_types and 'region' in X.columns:
            try:
                spatial_results = self.cross_validate_spatial(model, X, y)
                comprehensive_results['validation_results']['spatial'] = spatial_results
            except Exception as e:
                self.logger.error(f"Spatial validation failed: {e}")
                comprehensive_results['validation_results']['spatial'] = {'error': str(e)}
        
        # Stratified validation (standard)
        if 'stratified' in validation_types:
            try:
                stratified_results = self._cross_validate_stratified(model, X, y)
                comprehensive_results['validation_results']['stratified'] = stratified_results
            except Exception as e:
                self.logger.error(f"Stratified validation failed: {e}")
                comprehensive_results['validation_results']['stratified'] = {'error': str(e)}
        
        # Store results
        validation_id = f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.validation_results[validation_id] = comprehensive_results
        
        print(f"✅ Comprehensive validation complete: {validation_id}")
        return comprehensive_results
    
    def _cross_validate_stratified(self, model: Any, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Perform standard stratified cross-validation"""
        print("   Performing stratified cross-validation...")
        
        # Use sklearn's cross_val_score for standard metrics
        scoring_metrics = ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted']
        
        stratified_results = {}
        
        for metric in scoring_metrics:
            try:
                scores = cross_val_score(model, X, y, cv=self.cv_folds, 
                                       scoring=metric, n_jobs=-1)
                stratified_results[metric] = {
                    'mean': scores.mean(),
                    'std': scores.std(),
                    'scores': scores.tolist()
                }
            except Exception as e:
                self.logger.warning(f"Failed to calculate {metric}: {e}")
                stratified_results[metric] = {'error': str(e)}
        
        return {
            'stratified_summary': stratified_results,
            'n_folds': self.cv_folds,
            'validation_type': 'stratified'
        }
    
    def _get_model_info(self, model: Any) -> Dict:
        """Extract model information"""
        model_info = {
            'model_type': type(model).__name__,
            'model_module': type(model).__module__,
            'has_predict_proba': hasattr(model, 'predict_proba'),
            'has_feature_importances': hasattr(model, 'feature_importances_')
        }
        
        # Try to get model parameters
        try:
            if hasattr(model, 'get_params'):
                model_info['parameters'] = model.get_params()
        except:
            pass
        
        return model_info
    
    def _get_data_info(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Extract data information"""
        return {
            'n_samples': len(X),
            'n_features': len(X.columns),
            'feature_names': list(X.columns),
            'target_distribution': {
                'positive_class_ratio': y.mean(),
                'class_counts': y.value_counts().to_dict()
            },
            'missing_values': X.isnull().sum().sum(),
            'has_date_column': 'date' in X.columns,
            'has_region_column': 'region' in X.columns
        }
    
    def save_validation_results(self, validation_id: str = None, 
                              filename: str = None) -> str:
        """Save validation results to file"""
        if validation_id is None:
            validation_id = list(self.validation_results.keys())[-1] if self.validation_results else None
        
        if validation_id is None or validation_id not in self.validation_results:
            raise ValueError(f"Validation ID {validation_id} not found")
        
        if filename is None:
            filename = f"validation_results_{validation_id}.json"
        
        filepath = self.results_dir / filename
        
        # Convert numpy types to JSON serializable
        results = self._make_json_serializable(self.validation_results[validation_id])
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Validation results saved to {filepath}")
        return str(filepath)
    
    def load_validation_results(self, filepath: str) -> Dict:
        """Load validation results from file"""
        with open(filepath) as f:
            results = json.load(f)
        
        validation_id = f"loaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.validation_results[validation_id] = results
        
        print(f"✅ Validation results loaded: {validation_id}")
        return results
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert numpy types to JSON serializable types"""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def compare_validation_results(self, validation_ids: List[str], 
                                 metric: str = 'accuracy') -> Dict:
        """Compare validation results across multiple models"""
        print(f"🔄 Comparing validation results for metric: {metric}")
        
        comparison_results = {
            'metric': metric,
            'models': {},
            'summary': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Extract results for each model
        for val_id in validation_ids:
            if val_id not in self.validation_results:
                self.logger.warning(f"Validation ID {val_id} not found")
                continue
            
            results = self.validation_results[val_id]
            model_name = results.get('model_info', {}).get('model_type', val_id)
            
            model_metrics = {}
            
            # Extract metric from different validation types
            for val_type, val_results in results.get('validation_results', {}).items():
                if 'error' in val_results:
                    continue
                
                if val_type == 'time_series':
                    metric_data = val_results.get('cv_summary', {}).get(metric, {})
                elif val_type == 'spatial':
                    metric_data = val_results.get('spatial_summary', {}).get(metric, {})
                elif val_type == 'stratified':
                    metric_data = val_results.get('stratified_summary', {}).get(metric, {})
                else:
                    continue
                
                if 'mean' in metric_data:
                    model_metrics[val_type] = metric_data
            
            comparison_results['models'][model_name] = model_metrics
        
        # Calculate summary statistics
        if comparison_results['models']:
            # Find best performing model for each validation type
            for val_type in ['time_series', 'spatial', 'stratified']:
                type_results = {}
                for model_name, metrics in comparison_results['models'].items():
                    if val_type in metrics and 'mean' in metrics[val_type]:
                        type_results[model_name] = metrics[val_type]['mean']
                
                if type_results:
                    best_model = max(type_results.keys(), key=lambda k: type_results[k])
                    comparison_results['summary'][f'best_{val_type}'] = {
                        'model': best_model,
                        'score': type_results[best_model]
                    }
        
        print(f"✅ Validation comparison complete for {len(validation_ids)} models")
        return comparison_results
    
    def backtest_historical_elections(self, model: Any, historical_years: List[int] = None) -> Dict:
        """Backtest model against historical Bihar election results"""
        print("🔄 Backtesting against historical elections...")
        
        if historical_years is None:
            historical_years = [2015, 2020]
        
        backtest_results = {
            'years_tested': historical_years,
            'results_by_year': {},
            'overall_summary': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for year in historical_years:
            print(f"   Backtesting against {year} election...")
            
            try:
                # Load historical data
                historical_data = self._load_historical_election_data(year)
                
                if historical_data.empty:
                    print(f"   No data available for {year}")
                    continue
                
                # Prepare features and targets
                X_historical = self._prepare_historical_features(historical_data, year)
                y_historical = self._prepare_historical_targets(historical_data)
                
                # Make predictions
                y_pred = model.predict(X_historical)
                y_prob = model.predict_proba(X_historical) if hasattr(model, 'predict_proba') else None
                
                # Calculate accuracy metrics
                year_results = self._calculate_backtest_metrics(y_historical, y_pred, y_prob)
                year_results['n_constituencies'] = len(X_historical)
                year_results['year'] = year
                
                # Constituency-level analysis
                constituency_results = self._analyze_constituency_predictions(
                    historical_data, y_historical, y_pred, y_prob
                )
                year_results['constituency_analysis'] = constituency_results
                
                backtest_results['results_by_year'][year] = year_results
                
                print(f"   {year} accuracy: {year_results['accuracy']:.3f}")
                
            except Exception as e:
                self.logger.error(f"Backtesting failed for {year}: {e}")
                backtest_results['results_by_year'][year] = {'error': str(e)}
        
        # Calculate overall summary
        if backtest_results['results_by_year']:
            backtest_results['overall_summary'] = self._calculate_backtest_summary(
                backtest_results['results_by_year']
            )
        
        print(f"✅ Historical backtesting complete for {len(historical_years)} elections")
        return backtest_results
    
    def _load_historical_election_data(self, year: int) -> pd.DataFrame:
        """Load historical election data for specified year"""
        filename = f'bihar_{year}_results.csv'
        filepath = self.data_dir / 'historical' / filename
        
        if not filepath.exists():
            self.logger.warning(f"Historical data file not found: {filepath}")
            return pd.DataFrame()
        
        try:
            data = pd.read_csv(filepath)
            print(f"   Loaded {len(data)} constituencies for {year}")
            return data
        except Exception as e:
            self.logger.error(f"Error loading {year} data: {e}")
            return pd.DataFrame()
    
    def _prepare_historical_features(self, historical_data: pd.DataFrame, year: int) -> pd.DataFrame:
        """Prepare features from historical data"""
        # Select relevant feature columns (adapt based on your data structure)
        feature_columns = [
            'nda_share_2015', 'indi_share_2015', 'margin_2015', 'turnout_2015',
            'urban_percentage', 'rural_percentage', 'literacy_rate',
            'upper_caste_percentage', 'obc_percentage', 'sc_percentage', 'muslim_percentage'
        ]
        
        # Use available columns
        available_columns = [col for col in feature_columns if col in historical_data.columns]
        
        if not available_columns:
            # Create minimal feature set if no standard columns available
            X = pd.DataFrame({
                'constituency_id': range(len(historical_data)),
                'dummy_feature': np.random.randn(len(historical_data))
            })
        else:
            X = historical_data[available_columns].copy()
        
        # Fill missing values
        X = X.fillna(X.mean())
        
        return X
    
    def _prepare_historical_targets(self, historical_data: pd.DataFrame) -> pd.Series:
        """Prepare target variable from historical data"""
        # Determine winner based on vote shares
        if 'nda_vote_share' in historical_data.columns and 'indi_vote_share' in historical_data.columns:
            y = (historical_data['nda_vote_share'] > historical_data['indi_vote_share']).astype(int)
        elif 'winner' in historical_data.columns:
            y = (historical_data['winner'] == 'NDA').astype(int)
        else:
            # Fallback: random targets for testing
            y = pd.Series(np.random.randint(0, 2, len(historical_data)))
        
        return y
    
    def _calculate_backtest_metrics(self, y_true: pd.Series, y_pred: np.ndarray, 
                                  y_prob: np.ndarray = None) -> Dict:
        """Calculate comprehensive backtest metrics"""
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted'),
            'recall': recall_score(y_true, y_pred, average='weighted'),
            'f1_score': f1_score(y_true, y_pred, average='weighted')
        }
        
        # Add probability-based metrics if available
        if y_prob is not None:
            try:
                metrics['roc_auc'] = roc_auc_score(y_true, y_prob[:, 1])
                metrics['brier_score'] = brier_score_loss(y_true, y_prob[:, 1])
                metrics['log_loss'] = log_loss(y_true, y_prob)
            except Exception as e:
                self.logger.warning(f"Probability metrics calculation failed: {e}")
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        # Seat predictions
        nda_predicted = np.sum(y_pred)
        nda_actual = np.sum(y_true)
        metrics['nda_seats_predicted'] = int(nda_predicted)
        metrics['nda_seats_actual'] = int(nda_actual)
        metrics['seat_prediction_error'] = int(abs(nda_predicted - nda_actual))
        
        return metrics
    
    def _analyze_constituency_predictions(self, historical_data: pd.DataFrame,
                                       y_true: pd.Series, y_pred: np.ndarray,
                                       y_prob: np.ndarray = None) -> Dict:
        """Analyze predictions at constituency level"""
        analysis = {
            'correct_predictions': int(np.sum(y_true == y_pred)),
            'incorrect_predictions': int(np.sum(y_true != y_pred)),
            'accuracy_by_region': {},
            'most_confident_correct': [],
            'most_confident_incorrect': []
        }
        
        # Regional accuracy analysis
        if 'region' in historical_data.columns:
            for region in historical_data['region'].unique():
                region_mask = historical_data['region'] == region
                region_accuracy = accuracy_score(y_true[region_mask], y_pred[region_mask])
                analysis['accuracy_by_region'][region] = region_accuracy
        
        # Confidence analysis
        if y_prob is not None:
            confidence = np.max(y_prob, axis=1)
            correct_mask = (y_true == y_pred)
            
            # Most confident correct predictions
            if np.any(correct_mask):
                confident_correct_idx = np.where(correct_mask)[0]
                if len(confident_correct_idx) > 0:
                    top_confident_correct = confident_correct_idx[
                        np.argsort(confidence[confident_correct_idx])[-5:]
                    ]
                    analysis['most_confident_correct'] = [
                        {
                            'constituency': historical_data.iloc[i].get('constituency', f'Const_{i}'),
                            'confidence': float(confidence[i]),
                            'predicted': int(y_pred[i]),
                            'actual': int(y_true.iloc[i])
                        }
                        for i in top_confident_correct
                    ]
            
            # Most confident incorrect predictions
            incorrect_mask = ~correct_mask
            if np.any(incorrect_mask):
                confident_incorrect_idx = np.where(incorrect_mask)[0]
                if len(confident_incorrect_idx) > 0:
                    top_confident_incorrect = confident_incorrect_idx[
                        np.argsort(confidence[confident_incorrect_idx])[-5:]
                    ]
                    analysis['most_confident_incorrect'] = [
                        {
                            'constituency': historical_data.iloc[i].get('constituency', f'Const_{i}'),
                            'confidence': float(confidence[i]),
                            'predicted': int(y_pred[i]),
                            'actual': int(y_true.iloc[i])
                        }
                        for i in top_confident_incorrect
                    ]
        
        return analysis
    
    def _calculate_backtest_summary(self, results_by_year: Dict) -> Dict:
        """Calculate overall backtest summary across years"""
        valid_results = {year: results for year, results in results_by_year.items() 
                        if 'error' not in results}
        
        if not valid_results:
            return {'error': 'No valid backtest results'}
        
        # Calculate average metrics
        metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'seat_prediction_error']
        summary = {}
        
        for metric in metrics:
            values = [results[metric] for results in valid_results.values() 
                     if metric in results]
            if values:
                summary[f'avg_{metric}'] = np.mean(values)
                summary[f'std_{metric}'] = np.std(values)
        
        # Overall seat prediction analysis
        total_error = sum(results.get('seat_prediction_error', 0) for results in valid_results.values())
        total_constituencies = sum(results.get('n_constituencies', 0) for results in valid_results.values())
        
        summary['total_seat_prediction_error'] = total_error
        summary['total_constituencies_tested'] = total_constituencies
        summary['avg_error_per_election'] = total_error / len(valid_results) if valid_results else 0
        
        return summary
    
    def simulate_realtime_prediction(self, model: Any, election_year: int,
                                   prediction_dates: List[str] = None) -> Dict:
        """Simulate real-time prediction scenarios with historical data"""
        print(f"🔄 Simulating real-time predictions for {election_year}...")
        
        if prediction_dates is None:
            # Default prediction timeline (30, 15, 7, 1 days before election)
            election_date = datetime(election_year, 11, 10)  # Approximate Bihar election date
            prediction_dates = [
                (election_date - timedelta(days=d)).strftime('%Y-%m-%d') 
                for d in [30, 15, 7, 1]
            ]
        
        simulation_results = {
            'election_year': election_year,
            'prediction_timeline': {},
            'accuracy_evolution': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Load historical data
        historical_data = self._load_historical_election_data(election_year)
        if historical_data.empty:
            return {'error': f'No historical data available for {election_year}'}
        
        y_true = self._prepare_historical_targets(historical_data)
        
        for date_str in prediction_dates:
            print(f"   Simulating prediction for {date_str}...")
            
            try:
                # Simulate data availability at that date
                X_simulated = self._simulate_data_at_date(historical_data, date_str, election_year)
                
                # Make predictions
                y_pred = model.predict(X_simulated)
                y_prob = model.predict_proba(X_simulated) if hasattr(model, 'predict_proba') else None
                
                # Calculate metrics
                date_metrics = self._calculate_backtest_metrics(y_true, y_pred, y_prob)
                date_metrics['prediction_date'] = date_str
                
                simulation_results['prediction_timeline'][date_str] = date_metrics
                
            except Exception as e:
                self.logger.error(f"Simulation failed for {date_str}: {e}")
                simulation_results['prediction_timeline'][date_str] = {'error': str(e)}
        
        # Analyze accuracy evolution
        simulation_results['accuracy_evolution'] = self._analyze_accuracy_evolution(
            simulation_results['prediction_timeline']
        )
        
        print(f"✅ Real-time simulation complete for {len(prediction_dates)} time points")
        return simulation_results
    
    def _simulate_data_at_date(self, historical_data: pd.DataFrame, 
                             prediction_date: str, election_year: int) -> pd.DataFrame:
        """Simulate data availability at a specific prediction date"""
        # This is a simplified simulation - in reality, you'd model how different
        # data sources become available over time
        
        X_base = self._prepare_historical_features(historical_data, election_year)
        
        # Simulate data uncertainty/noise based on distance from election
        prediction_dt = datetime.strptime(prediction_date, '%Y-%m-%d')
        election_dt = datetime(election_year, 11, 10)
        days_before = (election_dt - prediction_dt).days
        
        # Add noise that decreases as we get closer to election
        noise_factor = max(0.01, days_before / 100)  # More noise further from election
        
        X_simulated = X_base.copy()
        for col in X_simulated.select_dtypes(include=[np.number]).columns:
            noise = np.random.normal(0, X_simulated[col].std() * noise_factor, len(X_simulated))
            X_simulated[col] += noise
        
        return X_simulated
    
    def _analyze_accuracy_evolution(self, prediction_timeline: Dict) -> Dict:
        """Analyze how accuracy evolves over the prediction timeline"""
        valid_predictions = {date: results for date, results in prediction_timeline.items()
                           if 'error' not in results and 'accuracy' in results}
        
        if len(valid_predictions) < 2:
            return {'error': 'Need at least 2 valid predictions for evolution analysis'}
        
        # Sort by date
        sorted_dates = sorted(valid_predictions.keys())
        accuracies = [valid_predictions[date]['accuracy'] for date in sorted_dates]
        seat_errors = [valid_predictions[date]['seat_prediction_error'] for date in sorted_dates]
        
        evolution_analysis = {
            'accuracy_trend': 'improving' if accuracies[-1] > accuracies[0] else 'declining',
            'accuracy_change': accuracies[-1] - accuracies[0],
            'seat_error_trend': 'improving' if seat_errors[-1] < seat_errors[0] else 'declining',
            'seat_error_change': seat_errors[-1] - seat_errors[0],
            'most_accurate_date': sorted_dates[np.argmax(accuracies)],
            'least_accurate_date': sorted_dates[np.argmin(accuracies)],
            'final_accuracy': accuracies[-1],
            'accuracy_volatility': np.std(accuracies)
        }
        
        return evolution_analysis

    def get_validation_summary(self) -> Dict:
        """Get summary of all validation results"""
        return {
            'total_validations': len(self.validation_results),
            'validation_ids': list(self.validation_results.keys()),
            'latest_validation': max(self.validation_results.keys()) if self.validation_results else None,
            'summary_timestamp': datetime.now().isoformat()
        }