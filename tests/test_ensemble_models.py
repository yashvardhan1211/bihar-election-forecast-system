import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from modeling.ensemble_predictor import EnsemblePredictor
from modeling.bayesian_ensemble import BayesianEnsemble

class TestEnsemblePredictor(unittest.TestCase):
    """Test suite for Ensemble Predictor"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.test_models_dir = Path(self.test_dir) / 'models'
        self.test_models_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock Config
        import src.config.settings as config
        self.original_models_dir = config.Config.MODELS_DIR
        config.Config.MODELS_DIR = self.test_models_dir
        
        # Create test data
        np.random.seed(42)
        n_samples = 200
        n_features = 10
        
        # Generate synthetic electoral data
        self.X_train = pd.DataFrame(
            np.random.randn(n_samples, n_features),
            columns=[f'feature_{i}' for i in range(n_features)]
        )
        
        # Create target with some pattern
        linear_combination = (
            self.X_train['feature_0'] * 0.5 + 
            self.X_train['feature_1'] * 0.3 + 
            self.X_train['feature_2'] * -0.4 +
            np.random.normal(0, 0.1, n_samples)
        )
        self.y_train = (linear_combination > 0).astype(int)
        
        # Test data
        self.X_test = pd.DataFrame(
            np.random.randn(50, n_features),
            columns=[f'feature_{i}' for i in range(n_features)]
        )
        linear_combination_test = (
            self.X_test['feature_0'] * 0.5 + 
            self.X_test['feature_1'] * 0.3 + 
            self.X_test['feature_2'] * -0.4 +
            np.random.normal(0, 0.1, 50)
        )
        self.y_test = (linear_combination_test > 0).astype(int)
        
        # Initialize ensemble predictor
        self.ensemble = EnsemblePredictor()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Restore original config
        import src.config.settings as config
        config.Config.MODELS_DIR = self.original_models_dir
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_ensemble_initialization(self):
        """Test ensemble predictor initialization"""
        self.assertIsInstance(self.ensemble, EnsemblePredictor)
        self.assertEqual(len(self.ensemble.base_models), 0)
        self.assertEqual(len(self.ensemble.ensemble_weights), 0)
        self.assertIn('random_forest', self.ensemble.model_types)
        self.assertIn('logistic_regression', self.ensemble.model_types)
    
    def test_train_base_models(self):
        """Test training of base models"""
        trained_models = self.ensemble.train_base_models(self.X_train, self.y_train)
        
        # Check that models are trained
        self.assertTrue(len(trained_models) > 0)
        self.assertTrue(len(self.ensemble.base_models) > 0)
        
        # Check that weights are calculated
        self.assertTrue(len(self.ensemble.ensemble_weights) > 0)
        
        # Check that weights sum to approximately 1
        weight_sum = sum(self.ensemble.ensemble_weights.values())
        self.assertAlmostEqual(weight_sum, 1.0, places=2)
        
        # Check validation scores
        self.assertTrue(len(self.ensemble.validation_scores) > 0)
        for model_name, scores in self.ensemble.validation_scores.items():
            self.assertIn('cv_mean', scores)
            self.assertIn('cv_std', scores)
            self.assertTrue(0 <= scores['cv_mean'] <= 1)
    
    def test_create_optimized_models(self):
        """Test creation of optimized individual models"""
        # Test Random Forest
        rf_model = self.ensemble.create_optimized_random_forest()
        self.assertTrue(hasattr(rf_model, '_electoral_optimized'))
        self.assertEqual(rf_model._model_type, 'random_forest_electoral')
        
        # Test Logistic Regression
        lr_model = self.ensemble.create_optimized_logistic_regression()
        self.assertTrue(hasattr(lr_model, '_electoral_optimized'))
        self.assertEqual(lr_model._model_type, 'logistic_regression_electoral')
        
        # Test XGBoost (may fall back to RF if not available)
        xgb_model = self.ensemble.create_optimized_xgboost()
        self.assertTrue(hasattr(xgb_model, '_electoral_optimized'))
    
    def test_fit_model_with_validation(self):
        """Test model fitting with validation"""
        model = self.ensemble.create_optimized_random_forest()
        fitted_model, validation_metrics = self.ensemble.fit_model_with_validation(
            model, self.X_train, self.y_train
        )
        
        # Check that model is fitted
        self.assertTrue(hasattr(fitted_model, 'predict'))
        
        # Check validation metrics
        expected_metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']
        for metric in expected_metrics:
            self.assertIn(metric, validation_metrics)
            self.assertTrue(0 <= validation_metrics[metric] <= 1)
    
    def test_predict_with_uncertainty(self):
        """Test ensemble prediction with uncertainty quantification"""
        # Train ensemble first
        self.ensemble.train_base_models(self.X_train, self.y_train)
        
        # Make predictions
        predictions, probabilities, uncertainty_metrics = self.ensemble.predict_with_uncertainty(self.X_test)
        
        # Check predictions shape
        self.assertEqual(len(predictions), len(self.X_test))
        self.assertEqual(probabilities.shape, (len(self.X_test), 2))
        
        # Check predictions are binary
        self.assertTrue(all(p in [0, 1] for p in predictions))
        
        # Check probabilities sum to 1
        prob_sums = np.sum(probabilities, axis=1)
        np.testing.assert_allclose(prob_sums, 1.0, rtol=1e-5)
        
        # Check uncertainty metrics
        expected_uncertainty_keys = ['prediction_variance', 'model_agreement', 'mean_confidence']
        for key in expected_uncertainty_keys:
            self.assertIn(key, uncertainty_metrics)
            self.assertEqual(len(uncertainty_metrics[key]), len(self.X_test))
    
    def test_calculate_ensemble_weights(self):
        """Test ensemble weight calculation"""
        # Mock validation scores
        validation_scores = {
            'random_forest': {'cv_mean': 0.85, 'cv_std': 0.05},
            'logistic_regression': {'cv_mean': 0.80, 'cv_std': 0.08},
            'xgboost': {'cv_mean': 0.88, 'cv_std': 0.04}
        }
        
        weights = self.ensemble.calculate_ensemble_weights(validation_scores)
        
        # Check that weights are calculated
        self.assertEqual(len(weights), 3)
        
        # Check that weights sum to 1
        weight_sum = sum(weights.values())
        self.assertAlmostEqual(weight_sum, 1.0, places=5)
        
        # Check that better performing model gets higher weight
        self.assertTrue(weights['xgboost'] > weights['logistic_regression'])
    
    def test_get_model_contributions(self):
        """Test individual model contribution analysis"""
        # Train ensemble
        self.ensemble.train_base_models(self.X_train, self.y_train)
        
        # Get contributions
        contributions = self.ensemble.get_model_contributions(self.X_test)
        
        # Check structure
        self.assertIsInstance(contributions, list)
        self.assertTrue(len(contributions) > 0)
        
        for contrib in contributions:
            self.assertIn('model_name', contrib)
            self.assertIn('weight', contrib)
            self.assertIn('predictions', contrib)
            self.assertIn('nda_probabilities', contrib)
            self.assertEqual(len(contrib['predictions']), len(self.X_test))
            self.assertEqual(len(contrib['nda_probabilities']), len(self.X_test))
    
    def test_evaluate_ensemble(self):
        """Test ensemble evaluation"""
        # Train ensemble
        self.ensemble.train_base_models(self.X_train, self.y_train)
        
        # Evaluate
        evaluation_results = self.ensemble.evaluate_ensemble(self.X_test, self.y_test)
        
        # Check structure
        self.assertIn('ensemble_metrics', evaluation_results)
        self.assertIn('individual_metrics', evaluation_results)
        self.assertIn('ensemble_weights', evaluation_results)
        
        # Check ensemble metrics
        ensemble_metrics = evaluation_results['ensemble_metrics']
        expected_metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']
        for metric in expected_metrics:
            self.assertIn(metric, ensemble_metrics)
            self.assertTrue(0 <= ensemble_metrics[metric] <= 1)
        
        # Check individual metrics
        individual_metrics = evaluation_results['individual_metrics']
        self.assertTrue(len(individual_metrics) > 0)
    
    def test_predict_constituencies_ensemble(self):
        """Test comprehensive constituency predictions"""
        # Train ensemble
        self.ensemble.train_base_models(self.X_train, self.y_train)
        
        # Add constituency names to test data
        self.X_test.index = [f'Constituency_{i}' for i in range(len(self.X_test))]
        
        # Make predictions
        predictions_df = self.ensemble.predict_constituencies_ensemble(self.X_test, use_bayesian=False)
        
        # Check structure
        expected_columns = [
            'constituency', 'predicted_winner', 'nda_win_probability', 
            'indi_win_probability', 'prediction_confidence', 'prediction_uncertainty'
        ]
        for col in expected_columns:
            self.assertIn(col, predictions_df.columns)
        
        # Check data integrity
        self.assertEqual(len(predictions_df), len(self.X_test))
        
        # Check probabilities are valid
        self.assertTrue(all(0 <= p <= 1 for p in predictions_df['nda_win_probability']))
        self.assertTrue(all(0 <= p <= 1 for p in predictions_df['indi_win_probability']))
        
        # Check winners are consistent with probabilities
        for _, row in predictions_df.iterrows():
            if row['nda_win_probability'] > 0.5:
                self.assertEqual(row['predicted_winner'], 'NDA')
            else:
                self.assertEqual(row['predicted_winner'], 'INDI')
    
    def test_save_and_load_ensemble(self):
        """Test ensemble saving and loading"""
        # Train ensemble
        self.ensemble.train_base_models(self.X_train, self.y_train)
        
        # Save ensemble
        version = self.ensemble.save_ensemble()
        self.assertIsInstance(version, str)
        
        # Create new ensemble instance
        new_ensemble = EnsemblePredictor()
        
        # Load ensemble
        success = new_ensemble.load_ensemble(version)
        self.assertTrue(success)
        
        # Check that models are loaded
        self.assertEqual(len(new_ensemble.base_models), len(self.ensemble.base_models))
        self.assertEqual(new_ensemble.ensemble_weights, self.ensemble.ensemble_weights)
        
        # Test predictions are consistent
        orig_pred, orig_prob, _ = self.ensemble.predict_with_uncertainty(self.X_test)
        new_pred, new_prob, _ = new_ensemble.predict_with_uncertainty(self.X_test)
        
        np.testing.assert_array_equal(orig_pred, new_pred)
        np.testing.assert_allclose(orig_prob, new_prob, rtol=1e-5)
    
    def test_update_ensemble_weights(self):
        """Test ensemble weight updating"""
        # Train ensemble
        self.ensemble.train_base_models(self.X_train, self.y_train)
        
        # Store original weights
        original_weights = self.ensemble.ensemble_weights.copy()
        
        # Update with new performance
        new_performance = {
            'random_forest': {'cv_mean': 0.90},
            'logistic_regression': {'cv_mean': 0.75}
        }
        
        self.ensemble.update_ensemble_weights(new_performance)
        
        # Check that weights have changed
        self.assertNotEqual(self.ensemble.ensemble_weights, original_weights)
        
        # Check that weights still sum to approximately 1
        weight_sum = sum(self.ensemble.ensemble_weights.values())
        self.assertAlmostEqual(weight_sum, 1.0, places=2)


class TestBayesianEnsemble(unittest.TestCase):
    """Test suite for Bayesian Ensemble"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.test_models_dir = Path(self.test_dir) / 'models'
        self.test_models_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock Config
        import src.config.settings as config
        self.original_models_dir = config.Config.MODELS_DIR
        config.Config.MODELS_DIR = self.test_models_dir
        
        # Create test data
        np.random.seed(42)
        self.n_samples = 100
        self.n_classes = 2
        
        # Mock model predictions and probabilities
        self.model_predictions = {
            'model_1': np.random.randint(0, 2, self.n_samples),
            'model_2': np.random.randint(0, 2, self.n_samples),
            'model_3': np.random.randint(0, 2, self.n_samples)
        }
        
        self.model_probabilities = {
            'model_1': np.random.dirichlet([2, 2], self.n_samples),
            'model_2': np.random.dirichlet([2, 2], self.n_samples),
            'model_3': np.random.dirichlet([2, 2], self.n_samples)
        }
        
        # True labels
        self.y_true = np.random.randint(0, 2, self.n_samples)
        
        # Initialize Bayesian ensemble
        self.bayesian_ensemble = BayesianEnsemble()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Restore original config
        import src.config.settings as config
        config.Config.MODELS_DIR = self.original_models_dir
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_bayesian_ensemble_initialization(self):
        """Test Bayesian ensemble initialization"""
        self.assertIsInstance(self.bayesian_ensemble, BayesianEnsemble)
        self.assertEqual(len(self.bayesian_ensemble.model_priors), 0)
        self.assertEqual(len(self.bayesian_ensemble.bayesian_weights), 0)
    
    def test_set_model_priors(self):
        """Test setting model priors"""
        model_names = ['model_1', 'model_2', 'model_3']
        
        # Test uniform priors
        self.bayesian_ensemble.set_model_priors(model_names, 'uniform')
        
        # Check that priors are set
        self.assertEqual(len(self.bayesian_ensemble.model_priors), 3)
        
        # Check that priors sum to 1
        prior_sum = sum(self.bayesian_ensemble.model_priors.values())
        self.assertAlmostEqual(prior_sum, 1.0, places=5)
        
        # Check uniform distribution
        for prior in self.bayesian_ensemble.model_priors.values():
            self.assertAlmostEqual(prior, 1/3, places=5)
    
    def test_calculate_model_evidence(self):
        """Test model evidence calculation"""
        model_names = list(self.model_predictions.keys())
        self.bayesian_ensemble.set_model_priors(model_names, 'uniform')
        
        evidence_scores = self.bayesian_ensemble.calculate_model_evidence(
            self.model_predictions, self.model_probabilities, self.y_true
        )
        
        # Check that evidence is calculated for all models
        self.assertEqual(len(evidence_scores), 3)
        
        # Check that evidence scores are finite
        for score in evidence_scores.values():
            self.assertTrue(np.isfinite(score))
    
    def test_update_bayesian_weights(self):
        """Test Bayesian weight updating"""
        # Mock evidence scores
        evidence_scores = {
            'model_1': -50.2,
            'model_2': -48.7,
            'model_3': -52.1
        }
        
        bayesian_weights = self.bayesian_ensemble.update_bayesian_weights(evidence_scores)
        
        # Check that weights are calculated
        self.assertEqual(len(bayesian_weights), 3)
        
        # Check that weights sum to 1
        weight_sum = sum(bayesian_weights.values())
        self.assertAlmostEqual(weight_sum, 1.0, places=5)
        
        # Check that better evidence gets higher weight
        self.assertTrue(bayesian_weights['model_2'] > bayesian_weights['model_3'])
    
    def test_bayesian_model_averaging(self):
        """Test Bayesian model averaging"""
        # Set up weights
        self.bayesian_ensemble.bayesian_weights = {
            'model_1': 0.3,
            'model_2': 0.5,
            'model_3': 0.2
        }
        
        averaged_probs, uncertainty_metrics = self.bayesian_ensemble.bayesian_model_averaging(
            self.model_probabilities
        )
        
        # Check output shape
        self.assertEqual(averaged_probs.shape, (self.n_samples, self.n_classes))
        
        # Check probabilities sum to 1
        prob_sums = np.sum(averaged_probs, axis=1)
        np.testing.assert_allclose(prob_sums, 1.0, rtol=1e-5)
        
        # Check uncertainty metrics
        expected_keys = ['epistemic_uncertainty', 'aleatoric_uncertainty', 'total_uncertainty']
        for key in expected_keys:
            self.assertIn(key, uncertainty_metrics)
            self.assertEqual(len(uncertainty_metrics[key]), self.n_samples)
    
    def test_calculate_prediction_intervals(self):
        """Test prediction interval calculation"""
        # Mock averaged probabilities
        averaged_probs = np.random.dirichlet([2, 2], self.n_samples)
        
        # Mock uncertainty metrics
        uncertainty_metrics = {
            'total_uncertainty': np.random.uniform(0.01, 0.1, self.n_samples).tolist()
        }
        
        intervals = self.bayesian_ensemble.calculate_prediction_intervals(
            averaged_probs, uncertainty_metrics, confidence_level=0.95
        )
        
        # Check structure
        expected_keys = ['lower_bounds', 'upper_bounds', 'interval_widths', 'point_estimates']
        for key in expected_keys:
            self.assertIn(key, intervals)
            self.assertEqual(len(intervals[key]), self.n_samples)
        
        # Check that lower bounds <= upper bounds
        for i in range(self.n_samples):
            self.assertLessEqual(intervals['lower_bounds'][i], intervals['upper_bounds'][i])
        
        # Check that bounds are in [0, 1]
        for bound in intervals['lower_bounds'] + intervals['upper_bounds']:
            self.assertTrue(0 <= bound <= 1)
    
    def test_ensemble_diversity_analysis(self):
        """Test ensemble diversity analysis"""
        diversity_metrics = self.bayesian_ensemble.ensemble_diversity_analysis(self.model_predictions)
        
        # Check structure
        expected_keys = ['mean_pairwise_disagreement', 'mean_q_statistic', 'mean_entropy_diversity']
        for key in expected_keys:
            self.assertIn(key, diversity_metrics)
        
        # Check that disagreement is between 0 and 1
        self.assertTrue(0 <= diversity_metrics['mean_pairwise_disagreement'] <= 1)
        
        # Check that Q-statistic is between -1 and 1
        self.assertTrue(-1 <= diversity_metrics['mean_q_statistic'] <= 1)
        
        # Check disagreement matrix
        self.assertIn('disagreement_matrix', diversity_metrics)
        disagreement_matrix = np.array(diversity_metrics['disagreement_matrix'])
        self.assertEqual(disagreement_matrix.shape, (3, 3))
        
        # Diagonal should be 0 (model agrees with itself)
        np.testing.assert_allclose(np.diag(disagreement_matrix), 0, atol=1e-10)
    
    def test_model_selection_bayesian(self):
        """Test Bayesian model selection"""
        # Set up evidence weights
        self.bayesian_ensemble.evidence_weights = {
            'model_1': -50.2,
            'model_2': -48.7,  # Best evidence
            'model_3': -52.1
        }
        
        # Test evidence-based selection
        best_model = self.bayesian_ensemble.model_selection_bayesian({}, 'evidence')
        self.assertEqual(best_model, 'model_2')
        
        # Set up Bayesian weights
        self.bayesian_ensemble.bayesian_weights = {
            'model_1': 0.2,
            'model_2': 0.6,  # Highest weight
            'model_3': 0.2
        }
        
        # Test posterior-based selection
        best_model = self.bayesian_ensemble.model_selection_bayesian({}, 'posterior')
        self.assertEqual(best_model, 'model_2')
    
    def test_calculate_model_confidence(self):
        """Test model confidence calculation"""
        confidence_metrics = self.bayesian_ensemble.calculate_model_confidence(
            self.model_probabilities, self.y_true
        )
        
        # Check that confidence is calculated for all models
        self.assertEqual(len(confidence_metrics), 3)
        
        # Check structure for each model
        for model_name, metrics in confidence_metrics.items():
            expected_keys = ['mean_confidence', 'confidence_variance', 'mean_entropy']
            for key in expected_keys:
                self.assertIn(key, metrics)
            
            # Check that confidence is between 0 and 1
            self.assertTrue(0 <= metrics['mean_confidence'] <= 1)
            
            # Check that entropy is non-negative
            self.assertTrue(metrics['mean_entropy'] >= 0)
    
    def test_save_and_load_bayesian_ensemble(self):
        """Test saving and loading Bayesian ensemble state"""
        # Set up some state
        self.bayesian_ensemble.model_priors = {'model_1': 0.5, 'model_2': 0.5}
        self.bayesian_ensemble.bayesian_weights = {'model_1': 0.4, 'model_2': 0.6}
        
        # Save ensemble
        filepath = self.bayesian_ensemble.save_bayesian_ensemble()
        self.assertTrue(Path(filepath).exists())
        
        # Create new ensemble and load
        new_ensemble = BayesianEnsemble()
        success = new_ensemble.load_bayesian_ensemble(filepath)
        self.assertTrue(success)
        
        # Check that state is preserved
        self.assertEqual(new_ensemble.model_priors, self.bayesian_ensemble.model_priors)
        self.assertEqual(new_ensemble.bayesian_weights, self.bayesian_ensemble.bayesian_weights)


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add Ensemble Predictor tests
    suite.addTest(unittest.makeSuite(TestEnsemblePredictor))
    
    # Add Bayesian Ensemble tests
    suite.addTest(unittest.makeSuite(TestBayesianEnsemble))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")