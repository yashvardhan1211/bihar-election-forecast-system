import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from features.enhanced_feature_engine import EnhancedFeatureEngine
from features.poll_corrector import PollCorrector

class TestEnhancedFeatureEngine(unittest.TestCase):
    """Test suite for Enhanced Feature Engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.test_dir) / 'data'
        self.test_features_dir = Path(self.test_dir) / 'features'
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        self.test_features_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock Config for testing
        import src.config.settings as config
        self.original_data_dir = config.Config.DATA_DIR
        self.original_features_dir = config.Config.FEATURES_DIR
        config.Config.DATA_DIR = self.test_data_dir
        config.Config.FEATURES_DIR = self.test_features_dir
        
        # Create test constituency data
        self.test_constituencies = pd.DataFrame({
            'constituency': ['Patna Sahib', 'Darbhanga', 'Muzaffarpur', 'Gaya', 'Bhagalpur'],
            'region': ['Central', 'Mithilanchal', 'Central', 'South', 'Border'],
            'nda_share_2020': [45.2, 38.7, 52.1, 41.3, 48.9],
            'indi_share_2020': [54.8, 61.3, 47.9, 58.7, 51.1]
        })
        
        # Create test historical data
        self.create_test_historical_data()
        
        # Initialize feature engine
        self.feature_engine = EnhancedFeatureEngine()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Restore original config
        import src.config.settings as config
        config.Config.DATA_DIR = self.original_data_dir
        config.Config.FEATURES_DIR = self.original_features_dir
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def create_test_historical_data(self):
        """Create test historical election data"""
        # 2020 election results
        results_2020 = pd.DataFrame({
            'constituency': ['Patna Sahib', 'Darbhanga', 'Muzaffarpur', 'Gaya', 'Bhagalpur'],
            'region': ['Central', 'Mithilanchal', 'Central', 'South', 'Border'],
            'nda_vote_share': [45.2, 38.7, 52.1, 41.3, 48.9],
            'indi_vote_share': [54.8, 61.3, 47.9, 58.7, 51.1],
            'winner': ['INDI', 'INDI', 'NDA', 'INDI', 'INDI']
        })
        
        # 2015 election results
        results_2015 = pd.DataFrame({
            'constituency': ['Patna Sahib', 'Darbhanga', 'Muzaffarpur', 'Gaya', 'Bhagalpur'],
            'region': ['Central', 'Mithilanchal', 'Central', 'South', 'Border'],
            'nda_vote_share': [52.1, 45.2, 48.7, 38.9, 51.2],
            'indi_vote_share': [47.9, 54.8, 51.3, 61.1, 48.8],
            'winner': ['NDA', 'INDI', 'INDI', 'INDI', 'NDA']
        })
        
        # Demographics data
        demographics = pd.DataFrame({
            'constituency': ['Patna Sahib', 'Darbhanga', 'Muzaffarpur', 'Gaya', 'Bhagalpur'],
            'upper_caste_percentage': [25.3, 12.1, 18.7, 14.2, 16.8],
            'obc_percentage': [38.2, 52.1, 45.3, 48.7, 42.1],
            'sc_percentage': [18.5, 16.2, 14.8, 19.3, 17.4],
            'muslim_percentage': [12.1, 18.7, 15.2, 14.8, 20.3],
            'urban_percentage': [65.2, 25.1, 35.7, 28.4, 42.1],
            'rural_percentage': [34.8, 74.9, 64.3, 71.6, 57.9],
            'literacy_rate': [78.5, 62.3, 68.7, 65.2, 71.4]
        })
        
        # Save test data
        historical_dir = self.test_data_dir / 'historical'
        static_dir = self.test_data_dir / 'static'
        historical_dir.mkdir(exist_ok=True)
        static_dir.mkdir(exist_ok=True)
        
        results_2020.to_csv(historical_dir / 'bihar_2020_results.csv', index=False)
        results_2015.to_csv(historical_dir / 'bihar_2015_results.csv', index=False)
        demographics.to_csv(static_dir / 'constituency_demographics.csv', index=False)
    
    def test_create_base_features(self):
        """Test base feature creation"""
        result = self.feature_engine.create_base_features(self.test_constituencies)
        
        # Check that all original columns are preserved
        for col in self.test_constituencies.columns:
            self.assertIn(col, result.columns)
        
        # Check that timestamp is added
        self.assertIn('feature_creation_timestamp', result.columns)
        
        # Check data integrity
        self.assertEqual(len(result), len(self.test_constituencies))
        
    def test_load_historical_data(self):
        """Test historical data loading"""
        # Test loading existing data
        results_2020 = self.feature_engine.load_historical_data('election_2020')
        self.assertFalse(results_2020.empty)
        self.assertEqual(len(results_2020), 5)
        self.assertIn('constituency', results_2020.columns)
        
        # Test loading non-existent data
        non_existent = self.feature_engine.load_historical_data('non_existent')
        self.assertTrue(non_existent.empty)
    
    def test_calculate_swing_patterns(self):
        """Test swing pattern calculation"""
        result = self.feature_engine.calculate_swing_patterns(self.test_constituencies)
        
        # Check that swing features are added
        expected_swing_features = [
            'swing_nda_2015_2020', 'swing_indi_2015_2020', 
            'margin_change_2015_2020', 'volatility_2015_2020',
            'incumbent_retained', 'incumbent_advantage'
        ]
        
        for feature in expected_swing_features:
            self.assertIn(feature, result.columns)
        
        # Check swing calculation for known constituency
        patna_row = result[result['constituency'] == 'Patna Sahib'].iloc[0]
        expected_nda_swing = 45.2 - 52.1  # 2020 - 2015
        self.assertAlmostEqual(patna_row['swing_nda_2015_2020'], expected_nda_swing, places=1)
        
        # Check volatility is positive
        self.assertTrue(all(result['volatility_2015_2020'] >= 0))
    
    def test_create_advanced_swing_features(self):
        """Test advanced swing feature creation"""
        result = self.feature_engine.create_advanced_swing_features(self.test_constituencies)
        
        # Check that advanced swing features are added
        advanced_features = [
            'regional_avg_nda_swing', 'regional_swing_correlation',
            'volatility_category', 'volatility_percentile',
            'swing_consistency', 'nda_incumbent_advantage'
        ]
        
        for feature in advanced_features:
            self.assertIn(feature, result.columns)
        
        # Check volatility categories
        volatility_categories = result['volatility_category'].unique()
        expected_categories = ['Low', 'Medium', 'High']
        for cat in volatility_categories:
            self.assertIn(cat, expected_categories)
    
    def test_add_demographic_features(self):
        """Test demographic feature addition"""
        result = self.feature_engine.add_demographic_features(self.test_constituencies)
        
        # Check that demographic features are added
        demographic_features = [
            'caste_based_nda_preference', 'caste_based_indi_preference',
            'caste_diversity_index', 'urbanrural_nda_preference',
            'religious_nda_preference', 'socioeconomic_nda_advantage'
        ]
        
        for feature in demographic_features:
            self.assertIn(feature, result.columns)
        
        # Check that preferences are between 0 and 1
        self.assertTrue(all(result['caste_based_nda_preference'] >= 0))
        self.assertTrue(all(result['caste_based_nda_preference'] <= 1))
        
        # Check diversity index is between 0 and 1
        self.assertTrue(all(result['caste_diversity_index'] >= 0))
        self.assertTrue(all(result['caste_diversity_index'] <= 1))
    
    def test_validate_features(self):
        """Test feature validation"""
        # Create features with some issues
        test_features = self.test_constituencies.copy()
        test_features['high_missing'] = [1, np.nan, np.nan, np.nan, np.nan]  # High missing rate
        test_features['low_variance'] = [1, 1, 1, 1, 1]  # No variance
        test_features['target'] = [0, 1, 0, 1, 0]  # Target for predictive power test
        
        validation_result = self.feature_engine.validate_features(test_features, 'target')
        
        # Check validation structure
        self.assertIn('total_features', validation_result)
        self.assertIn('missing_data_report', validation_result)
        self.assertIn('low_variance_features', validation_result)
        self.assertIn('validation_passed', validation_result)
        
        # Check that issues are detected
        self.assertIn('high_missing', validation_result['missing_data_report'])
        self.assertIn('low_variance', validation_result['low_variance_features'])
        self.assertFalse(validation_result['validation_passed'])
    
    def test_save_and_load_features(self):
        """Test feature saving and loading"""
        # Create some features
        features = self.feature_engine.create_base_features(self.test_constituencies)
        
        # Save features
        filename = 'test_features.csv'
        filepath = self.feature_engine.save_features(features, filename)
        
        # Check file exists
        self.assertTrue(Path(filepath).exists())
        
        # Check metadata file exists
        metadata_path = Path(filepath).parent / 'test_features_metadata.json'
        self.assertTrue(metadata_path.exists())
        
        # Load features back
        loaded_features = self.feature_engine.load_features(filename)
        
        # Check data integrity
        pd.testing.assert_frame_equal(features, loaded_features)
    
    def test_get_feature_statistics(self):
        """Test feature statistics generation"""
        features = self.feature_engine.create_base_features(self.test_constituencies)
        stats = self.feature_engine.get_feature_statistics(features)
        
        # Check statistics structure
        self.assertIn('summary', stats)
        self.assertIn('numeric_stats', stats)
        self.assertIn('missing_data', stats)
        
        # Check summary values
        self.assertEqual(stats['summary']['total_samples'], len(features))
        self.assertTrue(stats['summary']['total_features'] > 0)


class TestPollCorrector(unittest.TestCase):
    """Test suite for Poll Corrector"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.test_dir) / 'data'
        self.test_features_dir = Path(self.test_dir) / 'features'
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        self.test_features_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock Config
        import src.config.settings as config
        self.original_data_dir = config.Config.DATA_DIR
        self.original_features_dir = config.Config.FEATURES_DIR
        config.Config.DATA_DIR = self.test_data_dir
        config.Config.FEATURES_DIR = self.test_features_dir
        
        # Create test poll data
        self.test_polls = pd.DataFrame({
            'date': pd.date_range('2025-10-01', periods=5, freq='D'),
            'source': ['CVoter', 'India Today-Axis', 'Republic-CNX', 'News18-IPSOS', 'Unknown'],
            'nda_vote': [42.5, 46.2, 48.1, 44.3, 43.7],
            'indi_vote': [57.5, 53.8, 51.9, 55.7, 56.3],
            'sample_size': [2000, 1500, 1200, 1800, 800],
            'methodology': ['CATI', 'Face-to-Face', 'Online', 'CATI', 'Unknown']
        })
        
        # Initialize poll corrector
        self.poll_corrector = PollCorrector()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Restore original config
        import src.config.settings as config
        config.Config.DATA_DIR = self.original_data_dir
        config.Config.FEATURES_DIR = self.original_features_dir
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_load_pollster_database(self):
        """Test pollster database loading"""
        self.poll_corrector.load_pollster_database()
        
        # Check that databases are loaded
        self.assertTrue(len(self.poll_corrector.pollster_reliability) > 0)
        self.assertTrue(len(self.poll_corrector.house_effects) > 0)
        
        # Check specific pollster data
        self.assertIn('CVoter', self.poll_corrector.pollster_reliability)
        self.assertIn('CVoter', self.poll_corrector.house_effects)
        
        # Check data structure
        cvoter_reliability = self.poll_corrector.pollster_reliability['CVoter']
        self.assertIn('reliability', cvoter_reliability)
        self.assertIn('sample_quality', cvoter_reliability)
        
        cvoter_house_effect = self.poll_corrector.house_effects['CVoter']
        self.assertIn('nda_bias', cvoter_house_effect)
        self.assertIn('indi_bias', cvoter_house_effect)
    
    def test_correct_poll_data(self):
        """Test poll data correction"""
        corrected_polls = self.poll_corrector.correct_poll_data(self.test_polls)
        
        # Check that correction columns are added
        expected_columns = [
            'nda_vote_corrected', 'indi_vote_corrected',
            'house_effect_nda', 'house_effect_indi',
            'margin_of_error', 'sample_weight',
            'recency_weight', 'reliability_score'
        ]
        
        for col in expected_columns:
            self.assertIn(col, corrected_polls.columns)
        
        # Check that corrected values are reasonable
        self.assertTrue(all(corrected_polls['nda_vote_corrected'] >= 0))
        self.assertTrue(all(corrected_polls['nda_vote_corrected'] <= 100))
        self.assertTrue(all(corrected_polls['indi_vote_corrected'] >= 0))
        self.assertTrue(all(corrected_polls['indi_vote_corrected'] <= 100))
        
        # Check that weights are between 0 and 1
        self.assertTrue(all(corrected_polls['sample_weight'] >= 0))
        self.assertTrue(all(corrected_polls['sample_weight'] <= 1))
        self.assertTrue(all(corrected_polls['recency_weight'] >= 0))
        self.assertTrue(all(corrected_polls['recency_weight'] <= 1))
    
    def test_house_effect_corrections(self):
        """Test house effect corrections"""
        corrected_polls = self.poll_corrector.correct_poll_data(self.test_polls)
        
        # Check that house effects are applied
        republic_row = corrected_polls[corrected_polls['source'] == 'Republic-CNX'].iloc[0]
        
        # Republic-CNX should have positive NDA bias correction (reducing NDA vote)
        self.assertTrue(republic_row['house_effect_nda'] > 0)
        self.assertTrue(republic_row['nda_vote_corrected'] < republic_row['nda_vote'])
    
    def test_sample_size_adjustments(self):
        """Test sample size adjustments"""
        corrected_polls = self.poll_corrector.correct_poll_data(self.test_polls)
        
        # Larger samples should have higher weights
        large_sample_row = corrected_polls[corrected_polls['sample_size'] == 2000].iloc[0]
        small_sample_row = corrected_polls[corrected_polls['sample_size'] == 800].iloc[0]
        
        self.assertTrue(large_sample_row['sample_weight'] > small_sample_row['sample_weight'])
        self.assertTrue(large_sample_row['margin_of_error'] < small_sample_row['margin_of_error'])
    
    def test_recency_weighting(self):
        """Test recency weighting"""
        corrected_polls = self.poll_corrector.correct_poll_data(self.test_polls)
        
        # More recent polls should have higher recency weights
        recent_polls = corrected_polls.sort_values('date', ascending=False)
        
        # Check that recency weights generally decrease with age
        weights = recent_polls['recency_weight'].values
        # Allow for some variation but expect general trend
        self.assertTrue(weights[0] >= weights[-1])
    
    def test_aggregate_corrected_polls(self):
        """Test poll aggregation"""
        corrected_polls = self.poll_corrector.correct_poll_data(self.test_polls)
        aggregation = self.poll_corrector.aggregate_corrected_polls(corrected_polls)
        
        # Check aggregation structure
        expected_keys = [
            'weighted_nda_vote', 'weighted_indi_vote', 'poll_lead_nda',
            'poll_volatility', 'poll_uncertainty', 'poll_momentum_nda',
            'n_polls_used', 'avg_reliability'
        ]
        
        for key in expected_keys:
            self.assertIn(key, aggregation)
        
        # Check that values are reasonable
        self.assertTrue(0 <= aggregation['weighted_nda_vote'] <= 100)
        self.assertTrue(0 <= aggregation['weighted_indi_vote'] <= 100)
        self.assertTrue(aggregation['poll_volatility'] > 0)
        self.assertTrue(aggregation['poll_uncertainty'] > 0)
        self.assertEqual(aggregation['n_polls_used'], len(corrected_polls))
    
    def test_empty_polls_handling(self):
        """Test handling of empty poll data"""
        empty_polls = pd.DataFrame()
        
        # Should not crash and return default values
        corrected = self.poll_corrector.correct_poll_data(empty_polls)
        self.assertTrue(corrected.empty)
        
        aggregation = self.poll_corrector.aggregate_corrected_polls(empty_polls)
        self.assertEqual(aggregation['n_polls_used'], 0)
        self.assertTrue(aggregation['weighted_nda_vote'] > 0)  # Should have default
    
    def test_create_poll_features(self):
        """Test poll feature creation for constituencies"""
        # Create test constituency data
        constituencies = pd.DataFrame({
            'constituency': ['Test1', 'Test2'],
            'region': ['Central', 'South']
        })
        
        result = self.poll_corrector.create_poll_features(constituencies, self.test_polls)
        
        # Check that poll features are added
        poll_features = [
            'weighted_nda_vote', 'weighted_indi_vote', 'poll_lead_nda',
            'poll_volatility', 'poll_uncertainty'
        ]
        
        for feature in poll_features:
            self.assertIn(feature, result.columns)
        
        # Check that constituency-specific adjustments are added
        self.assertIn('poll_nda_adjusted', result.columns)
        self.assertIn('regional_poll_adjustment_nda', result.columns)
    
    def test_get_correction_summary(self):
        """Test correction summary generation"""
        corrected_polls = self.poll_corrector.correct_poll_data(self.test_polls)
        summary = self.poll_corrector.get_correction_summary(self.test_polls, corrected_polls)
        
        # Check summary structure
        self.assertIn('original_polls', summary)
        self.assertIn('corrected_polls', summary)
        self.assertIn('corrections_applied', summary)
        self.assertIn('reliability_metrics', summary)
        
        # Check values
        self.assertEqual(summary['original_polls'], len(self.test_polls))
        self.assertEqual(summary['corrected_polls'], len(corrected_polls))


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add Enhanced Feature Engine tests
    suite.addTest(unittest.makeSuite(TestEnhancedFeatureEngine))
    
    # Add Poll Corrector tests
    suite.addTest(unittest.makeSuite(TestPollCorrector))
    
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