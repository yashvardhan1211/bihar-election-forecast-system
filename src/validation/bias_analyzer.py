import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from src.config.settings import Config
import json
import warnings
from sklearn.metrics import accuracy_score, precision_score, recall_score
from scipy import stats
import logging

warnings.filterwarnings('ignore')

class BiasAnalyzer:
    """Systematic bias analysis and error detection for electoral predictions"""
    
    def __init__(self):
        self.results_dir = Config.RESULTS_DIR
        self.bias_results = {}
        self.logger = logging.getLogger(__name__)
        print(f"✅ Bias Analyzer initialized")
    
    def analyze_systematic_bias(self, y_true: pd.Series, y_pred: np.ndarray, 
                              y_prob: np.ndarray, metadata: pd.DataFrame) -> Dict:
        """Comprehensive systematic bias analysis"""
        print("🔄 Analyzing systematic bias...")
        
        bias_analysis = {
            'overall_bias': self._calculate_overall_bias(y_true, y_pred, y_prob),
            'regional_bias': self._analyze_regional_bias(y_true, y_pred, y_prob, metadata),
            'party_bias': self._analyze_party_bias(y_true, y_pred, y_prob),
            'demographic_bias': self._analyze_demographic_bias(y_true, y_pred, y_prob, metadata),
            'margin_bias': self._analyze_margin_bias(y_true, y_pred, y_prob, metadata),
            'temporal_bias': self._analyze_temporal_bias(y_true, y_pred, y_prob, metadata),
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Bias analysis complete")
        return bias_analysis
    
    def _calculate_overall_bias(self, y_true: pd.Series, y_pred: np.ndarray, 
                              y_prob: np.ndarray) -> Dict:
        """Calculate overall prediction bias"""
        # Directional bias (tendency to favor one party)
        nda_predicted = np.sum(y_pred)
        nda_actual = np.sum(y_true)
        seat_bias = nda_predicted - nda_actual
        
        # Probability bias
        if y_prob is not None:
            avg_predicted_prob = np.mean(y_prob[:, 1])  # NDA probability
            actual_rate = np.mean(y_true)
            prob_bias = avg_predicted_prob - actual_rate
        else:
            prob_bias = 0.0
        
        # Confidence bias (overconfidence/underconfidence)
        if y_prob is not None:
            confidence = np.max(y_prob, axis=1)
            correct_predictions = (y_true == y_pred)
            
            # Calibration analysis
            high_conf_mask = confidence > 0.8
            if np.any(high_conf_mask):
                high_conf_accuracy = np.mean(correct_predictions[high_conf_mask])
                confidence_bias = np.mean(confidence[high_conf_mask]) - high_conf_accuracy
            else:
                confidence_bias = 0.0
        else:
            confidence_bias = 0.0
        
        return {
            'seat_bias': int(seat_bias),
            'seat_bias_percentage': (seat_bias / len(y_true)) * 100,
            'probability_bias': prob_bias,
            'confidence_bias': confidence_bias,
            'bias_direction': 'pro_nda' if seat_bias > 0 else 'pro_indi' if seat_bias < 0 else 'neutral'
        }
    
    def _analyze_regional_bias(self, y_true: pd.Series, y_pred: np.ndarray,
                             y_prob: np.ndarray, metadata: pd.DataFrame) -> Dict:
        """Analyze bias by region"""
        if 'region' not in metadata.columns:
            return {'error': 'No region information available'}
        
        regional_bias = {}
        
        for region in metadata['region'].unique():
            region_mask = metadata['region'] == region
            
            if np.sum(region_mask) == 0:
                continue
            
            region_y_true = y_true[region_mask]
            region_y_pred = y_pred[region_mask]
            region_y_prob = y_prob[region_mask] if y_prob is not None else None
            
            # Calculate regional metrics
            accuracy = accuracy_score(region_y_true, region_y_pred)
            nda_predicted = np.sum(region_y_pred)
            nda_actual = np.sum(region_y_true)
            
            regional_bias[region] = {
                'accuracy': accuracy,
                'nda_predicted': int(nda_predicted),
                'nda_actual': int(nda_actual),
                'seat_bias': int(nda_predicted - nda_actual),
                'total_seats': int(np.sum(region_mask))
            }
            
            if region_y_prob is not None:
                avg_prob = np.mean(region_y_prob[:, 1])
                actual_rate = np.mean(region_y_true)
                regional_bias[region]['probability_bias'] = avg_prob - actual_rate
        
        # Identify most biased regions
        bias_scores = {region: abs(data['seat_bias']) for region, data in regional_bias.items()}
        most_biased = max(bias_scores.keys(), key=lambda k: bias_scores[k]) if bias_scores else None
        
        return {
            'regional_results': regional_bias,
            'most_biased_region': most_biased,
            'regional_variance': np.var(list(bias_scores.values())) if bias_scores else 0
        }
    
    def _analyze_party_bias(self, y_true: pd.Series, y_pred: np.ndarray,
                          y_prob: np.ndarray) -> Dict:
        """Analyze bias toward specific parties"""
        # NDA bias analysis
        nda_true_positive = np.sum((y_true == 1) & (y_pred == 1))
        nda_false_positive = np.sum((y_true == 0) & (y_pred == 1))
        nda_true_negative = np.sum((y_true == 0) & (y_pred == 0))
        nda_false_negative = np.sum((y_true == 1) & (y_pred == 0))
        
        # Calculate precision and recall for each party
        nda_precision = nda_true_positive / (nda_true_positive + nda_false_positive) if (nda_true_positive + nda_false_positive) > 0 else 0
        nda_recall = nda_true_positive / (nda_true_positive + nda_false_negative) if (nda_true_positive + nda_false_negative) > 0 else 0
        
        indi_precision = nda_true_negative / (nda_true_negative + nda_false_negative) if (nda_true_negative + nda_false_negative) > 0 else 0
        indi_recall = nda_true_negative / (nda_true_negative + nda_false_positive) if (nda_true_negative + nda_false_positive) > 0 else 0
        
        # Bias indicators
        precision_bias = nda_precision - indi_precision
        recall_bias = nda_recall - indi_recall
        
        return {
            'nda_metrics': {
                'precision': nda_precision,
                'recall': nda_recall,
                'true_positives': int(nda_true_positive),
                'false_positives': int(nda_false_positive),
                'false_negatives': int(nda_false_negative)
            },
            'indi_metrics': {
                'precision': indi_precision,
                'recall': indi_recall,
                'true_positives': int(nda_true_negative),
                'false_positives': int(nda_false_negative),
                'false_negatives': int(nda_false_positive)
            },
            'bias_indicators': {
                'precision_bias': precision_bias,
                'recall_bias': recall_bias,
                'overall_bias_direction': 'pro_nda' if (precision_bias + recall_bias) > 0 else 'pro_indi'
            }
        }
    
    def _analyze_demographic_bias(self, y_true: pd.Series, y_pred: np.ndarray,
                                y_prob: np.ndarray, metadata: pd.DataFrame) -> Dict:
        """Analyze bias across demographic groups"""
        demographic_bias = {}
        
        # Urban vs Rural bias
        if 'urban_percentage' in metadata.columns:
            # Classify as urban/rural based on threshold
            urban_threshold = 50
            is_urban = metadata['urban_percentage'] > urban_threshold
            
            for category, mask in [('urban', is_urban), ('rural', ~is_urban)]:
                if np.sum(mask) > 0:
                    cat_accuracy = accuracy_score(y_true[mask], y_pred[mask])
                    demographic_bias[f'{category}_accuracy'] = cat_accuracy
        
        # Caste-based bias analysis
        caste_columns = ['upper_caste_percentage', 'obc_percentage', 'sc_percentage', 'muslim_percentage']
        available_caste_cols = [col for col in caste_columns if col in metadata.columns]
        
        if available_caste_cols:
            # Find dominant caste for each constituency
            caste_data = metadata[available_caste_cols]
            dominant_caste = caste_data.idxmax(axis=1)
            
            for caste in available_caste_cols:
                caste_mask = dominant_caste == caste
                if np.sum(caste_mask) > 5:  # Minimum sample size
                    caste_accuracy = accuracy_score(y_true[caste_mask], y_pred[caste_mask])
                    demographic_bias[f'{caste}_accuracy'] = caste_accuracy
        
        return demographic_bias
    
    def _analyze_margin_bias(self, y_true: pd.Series, y_pred: np.ndarray,
                           y_prob: np.ndarray, metadata: pd.DataFrame) -> Dict:
        """Analyze bias based on victory margins"""
        if y_prob is None:
            return {'error': 'Probability predictions required for margin analysis'}
        
        # Calculate predicted margins
        predicted_margins = np.abs(y_prob[:, 1] - 0.5) * 2  # Convert to 0-1 scale
        
        # Categorize by predicted margin
        margin_categories = {
            'safe': predicted_margins > 0.6,
            'likely': (predicted_margins > 0.3) & (predicted_margins <= 0.6),
            'toss_up': predicted_margins <= 0.3
        }
        
        margin_bias = {}
        
        for category, mask in margin_categories.items():
            if np.sum(mask) > 0:
                cat_accuracy = accuracy_score(y_true[mask], y_pred[mask])
                cat_confidence = np.mean(np.max(y_prob[mask], axis=1))
                
                margin_bias[category] = {
                    'accuracy': cat_accuracy,
                    'confidence': cat_confidence,
                    'count': int(np.sum(mask)),
                    'calibration_gap': cat_confidence - cat_accuracy
                }
        
        return margin_bias
    
    def _analyze_temporal_bias(self, y_true: pd.Series, y_pred: np.ndarray,
                             y_prob: np.ndarray, metadata: pd.DataFrame) -> Dict:
        """Analyze bias over time (if temporal data available)"""
        if 'date' not in metadata.columns:
            return {'note': 'No temporal data available for bias analysis'}
        
        # Group by time periods
        dates = pd.to_datetime(metadata['date'])
        
        # Analyze by month or quarter
        temporal_groups = dates.dt.to_period('M')  # Monthly groups
        
        temporal_bias = {}
        
        for period in temporal_groups.unique():
            period_mask = temporal_groups == period
            
            if np.sum(period_mask) > 0:
                period_accuracy = accuracy_score(y_true[period_mask], y_pred[period_mask])
                temporal_bias[str(period)] = {
                    'accuracy': period_accuracy,
                    'count': int(np.sum(period_mask))
                }
        
        return temporal_bias
    
    def detect_systematic_errors(self, y_true: pd.Series, y_pred: np.ndarray,
                               y_prob: np.ndarray, metadata: pd.DataFrame) -> Dict:
        """Detect systematic error patterns"""
        print("🔄 Detecting systematic error patterns...")
        
        error_patterns = {
            'overconfidence_errors': self._detect_overconfidence_errors(y_true, y_pred, y_prob),
            'consistent_misclassification': self._detect_consistent_misclassification(y_true, y_pred, metadata),
            'probability_calibration_errors': self._detect_calibration_errors(y_true, y_prob),
            'regional_error_clusters': self._detect_regional_error_clusters(y_true, y_pred, metadata),
            'timestamp': datetime.now().isoformat()
        }
        
        print("✅ Systematic error detection complete")
        return error_patterns
    
    def _detect_overconfidence_errors(self, y_true: pd.Series, y_pred: np.ndarray,
                                    y_prob: np.ndarray) -> Dict:
        """Detect overconfidence in incorrect predictions"""
        if y_prob is None:
            return {'error': 'Probability predictions required'}
        
        confidence = np.max(y_prob, axis=1)
        incorrect_mask = y_true != y_pred
        
        if not np.any(incorrect_mask):
            return {'overconfident_errors': 0}
        
        # High confidence incorrect predictions
        high_conf_threshold = 0.8
        overconfident_errors = np.sum(incorrect_mask & (confidence > high_conf_threshold))
        
        # Average confidence of incorrect predictions
        avg_incorrect_confidence = np.mean(confidence[incorrect_mask])
        
        return {
            'overconfident_errors': int(overconfident_errors),
            'total_incorrect': int(np.sum(incorrect_mask)),
            'overconfidence_rate': overconfident_errors / np.sum(incorrect_mask),
            'avg_incorrect_confidence': avg_incorrect_confidence
        }
    
    def _detect_consistent_misclassification(self, y_true: pd.Series, y_pred: np.ndarray,
                                          metadata: pd.DataFrame) -> Dict:
        """Detect constituencies consistently misclassified"""
        # This would require multiple prediction rounds - simplified for single prediction
        incorrect_mask = y_true != y_pred
        
        misclassification_analysis = {
            'total_misclassified': int(np.sum(incorrect_mask)),
            'misclassification_rate': np.mean(incorrect_mask)
        }
        
        # Analyze misclassification by characteristics
        if 'region' in metadata.columns:
            regional_errors = {}
            for region in metadata['region'].unique():
                region_mask = metadata['region'] == region
                region_error_rate = np.mean(incorrect_mask[region_mask])
                regional_errors[region] = region_error_rate
            
            misclassification_analysis['regional_error_rates'] = regional_errors
        
        return misclassification_analysis
    
    def _detect_calibration_errors(self, y_true: pd.Series, y_prob: np.ndarray) -> Dict:
        """Detect probability calibration errors"""
        if y_prob is None:
            return {'error': 'Probability predictions required'}
        
        from sklearn.calibration import calibration_curve
        
        try:
            # Calculate calibration curve
            fraction_of_positives, mean_predicted_value = calibration_curve(
                y_true, y_prob[:, 1], n_bins=10
            )
            
            # Calculate calibration error
            calibration_error = np.mean(np.abs(fraction_of_positives - mean_predicted_value))
            
            # Identify worst calibrated bins
            bin_errors = np.abs(fraction_of_positives - mean_predicted_value)
            worst_bin_idx = np.argmax(bin_errors)
            
            return {
                'calibration_error': calibration_error,
                'worst_bin_error': bin_errors[worst_bin_idx],
                'worst_bin_predicted': mean_predicted_value[worst_bin_idx],
                'worst_bin_actual': fraction_of_positives[worst_bin_idx],
                'reliability_score': 1 - calibration_error
            }
            
        except Exception as e:
            return {'error': f'Calibration analysis failed: {e}'}
    
    def _detect_regional_error_clusters(self, y_true: pd.Series, y_pred: np.ndarray,
                                      metadata: pd.DataFrame) -> Dict:
        """Detect regional clusters of prediction errors"""
        if 'region' not in metadata.columns:
            return {'error': 'No regional information available'}
        
        incorrect_mask = y_true != y_pred
        regional_clusters = {}
        
        for region in metadata['region'].unique():
            region_mask = metadata['region'] == region
            region_error_count = np.sum(incorrect_mask[region_mask])
            region_total = np.sum(region_mask)
            
            if region_total > 0:
                regional_clusters[region] = {
                    'error_count': int(region_error_count),
                    'total_constituencies': int(region_total),
                    'error_rate': region_error_count / region_total,
                    'is_error_cluster': region_error_count / region_total > 0.5
                }
        
        # Identify regions with high error rates
        error_clusters = [region for region, data in regional_clusters.items() 
                         if data['is_error_cluster']]
        
        return {
            'regional_analysis': regional_clusters,
            'error_cluster_regions': error_clusters,
            'n_error_clusters': len(error_clusters)
        }
    
    def generate_bias_report(self, bias_analysis: Dict, error_patterns: Dict) -> Dict:
        """Generate comprehensive bias report"""
        print("🔄 Generating bias report...")
        
        # Extract key findings
        overall_bias = bias_analysis.get('overall_bias', {})
        regional_bias = bias_analysis.get('regional_bias', {})
        party_bias = bias_analysis.get('party_bias', {})
        
        # Severity assessment
        severity_indicators = {
            'seat_bias_severity': self._assess_bias_severity(abs(overall_bias.get('seat_bias', 0)), 'seat'),
            'probability_bias_severity': self._assess_bias_severity(abs(overall_bias.get('probability_bias', 0)), 'probability'),
            'regional_bias_severity': self._assess_regional_bias_severity(regional_bias),
            'party_bias_severity': self._assess_party_bias_severity(party_bias)
        }
        
        # Recommendations
        recommendations = self._generate_bias_recommendations(bias_analysis, error_patterns)
        
        bias_report = {
            'executive_summary': {
                'overall_bias_direction': overall_bias.get('bias_direction', 'unknown'),
                'seat_bias': overall_bias.get('seat_bias', 0),
                'most_biased_region': regional_bias.get('most_biased_region', 'none'),
                'primary_bias_type': self._identify_primary_bias_type(bias_analysis)
            },
            'severity_assessment': severity_indicators,
            'detailed_analysis': {
                'bias_analysis': bias_analysis,
                'error_patterns': error_patterns
            },
            'recommendations': recommendations,
            'report_timestamp': datetime.now().isoformat()
        }
        
        print("✅ Bias report generated")
        return bias_report
    
    def _assess_bias_severity(self, bias_value: float, bias_type: str) -> str:
        """Assess severity of bias"""
        if bias_type == 'seat':
            if bias_value <= 2:
                return 'low'
            elif bias_value <= 5:
                return 'moderate'
            else:
                return 'high'
        elif bias_type == 'probability':
            if bias_value <= 0.05:
                return 'low'
            elif bias_value <= 0.15:
                return 'moderate'
            else:
                return 'high'
        return 'unknown'
    
    def _assess_regional_bias_severity(self, regional_bias: Dict) -> str:
        """Assess severity of regional bias"""
        if 'regional_results' not in regional_bias:
            return 'unknown'
        
        regional_results = regional_bias['regional_results']
        max_regional_bias = max([abs(data.get('seat_bias', 0)) for data in regional_results.values()])
        
        return self._assess_bias_severity(max_regional_bias, 'seat')
    
    def _assess_party_bias_severity(self, party_bias: Dict) -> str:
        """Assess severity of party bias"""
        if 'bias_indicators' not in party_bias:
            return 'unknown'
        
        bias_indicators = party_bias['bias_indicators']
        max_bias = max(abs(bias_indicators.get('precision_bias', 0)), 
                      abs(bias_indicators.get('recall_bias', 0)))
        
        return self._assess_bias_severity(max_bias, 'probability')
    
    def _identify_primary_bias_type(self, bias_analysis: Dict) -> str:
        """Identify the primary type of bias"""
        bias_scores = {}
        
        # Overall bias
        overall_bias = bias_analysis.get('overall_bias', {})
        bias_scores['directional'] = abs(overall_bias.get('seat_bias', 0))
        
        # Regional bias
        regional_bias = bias_analysis.get('regional_bias', {})
        bias_scores['regional'] = regional_bias.get('regional_variance', 0)
        
        # Party bias
        party_bias = bias_analysis.get('party_bias', {})
        if 'bias_indicators' in party_bias:
            bias_indicators = party_bias['bias_indicators']
            bias_scores['party'] = max(abs(bias_indicators.get('precision_bias', 0)),
                                     abs(bias_indicators.get('recall_bias', 0)))
        
        return max(bias_scores.keys(), key=lambda k: bias_scores[k]) if bias_scores else 'unknown'
    
    def _generate_bias_recommendations(self, bias_analysis: Dict, error_patterns: Dict) -> List[str]:
        """Generate recommendations to address identified biases"""
        recommendations = []
        
        overall_bias = bias_analysis.get('overall_bias', {})
        
        # Directional bias recommendations
        if abs(overall_bias.get('seat_bias', 0)) > 3:
            recommendations.append("Consider recalibrating model to reduce directional bias")
            recommendations.append("Review training data for class imbalance issues")
        
        # Regional bias recommendations
        regional_bias = bias_analysis.get('regional_bias', {})
        if regional_bias.get('most_biased_region'):
            recommendations.append(f"Focus on improving predictions for {regional_bias['most_biased_region']} region")
            recommendations.append("Consider region-specific model adjustments")
        
        # Overconfidence recommendations
        overconf_errors = error_patterns.get('overconfidence_errors', {})
        if overconf_errors.get('overconfidence_rate', 0) > 0.3:
            recommendations.append("Implement probability calibration to reduce overconfidence")
            recommendations.append("Consider ensemble methods to improve uncertainty quantification")
        
        # Calibration recommendations
        calib_errors = error_patterns.get('probability_calibration_errors', {})
        if calib_errors.get('calibration_error', 0) > 0.1:
            recommendations.append("Apply post-hoc calibration methods (Platt scaling, isotonic regression)")
        
        return recommendations