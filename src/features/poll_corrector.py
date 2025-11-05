import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from src.config.settings import Config
import json
import warnings
from scipy import stats
from sklearn.linear_model import LinearRegression
import logging

warnings.filterwarnings('ignore')

class PollCorrector:
    """Advanced poll correction system with house effect and reliability weighting"""
    
    def __init__(self):
        self.data_dir = Config.DATA_DIR
        self.features_dir = Config.FEATURES_DIR
        
        # Pollster reliability database
        self.pollster_reliability = {}
        self.house_effects = {}
        
        # Correction parameters
        self.min_sample_size = 500
        self.max_age_days = 30
        self.reliability_threshold = 0.6
        
        self.logger = logging.getLogger(__name__)
        print(f"✅ Poll Corrector initialized")
    
    def load_pollster_database(self) -> None:
        """Load pollster reliability and house effect database"""
        print("🔄 Loading pollster reliability database...")
        
        # Define known pollster characteristics (based on historical performance)
        self.pollster_reliability = {
            'CVoter': {'reliability': 0.75, 'sample_quality': 0.8, 'methodology_score': 0.7},
            'ABP-CVoter': {'reliability': 0.78, 'sample_quality': 0.8, 'methodology_score': 0.75},
            'India Today-Axis': {'reliability': 0.72, 'sample_quality': 0.75, 'methodology_score': 0.7},
            'Times Now-VMR': {'reliability': 0.68, 'sample_quality': 0.7, 'methodology_score': 0.65},
            'Republic-CNX': {'reliability': 0.65, 'sample_quality': 0.7, 'methodology_score': 0.6},
            'News18-IPSOS': {'reliability': 0.73, 'sample_quality': 0.75, 'methodology_score': 0.7},
            'ABP News-C-Voter': {'reliability': 0.76, 'sample_quality': 0.8, 'methodology_score': 0.72},
            'Local_Poll': {'reliability': 0.55, 'sample_quality': 0.6, 'methodology_score': 0.5},
            'Unknown': {'reliability': 0.5, 'sample_quality': 0.5, 'methodology_score': 0.5},
            # Exit polls have higher reliability (closer to actual voting)
            'CVoter Exit Poll': {'reliability': 0.85, 'sample_quality': 0.9, 'methodology_score': 0.85},
            'Axis My India Exit Poll': {'reliability': 0.82, 'sample_quality': 0.85, 'methodology_score': 0.8},
            'CNX Exit Poll': {'reliability': 0.78, 'sample_quality': 0.8, 'methodology_score': 0.75},
            'TOI Exit Poll': {'reliability': 0.80, 'sample_quality': 0.82, 'methodology_score': 0.78},
            'NDTV Exit Poll': {'reliability': 0.75, 'sample_quality': 0.78, 'methodology_score': 0.72},
            'India Today-Axis Exit Poll': {'reliability': 0.82, 'sample_quality': 0.85, 'methodology_score': 0.8},
            'Generic Exit Poll': {'reliability': 0.75, 'sample_quality': 0.75, 'methodology_score': 0.7}
        }
        
        # Define house effects (tendency to favor one alliance over another)
        self.house_effects = {
            'CVoter': {'nda_bias': -0.5, 'indi_bias': 0.5},  # Slight INDI lean
            'ABP-CVoter': {'nda_bias': -0.3, 'indi_bias': 0.3},
            'India Today-Axis': {'nda_bias': 1.2, 'indi_bias': -1.2},  # NDA lean
            'Times Now-VMR': {'nda_bias': 0.8, 'indi_bias': -0.8},
            'Republic-CNX': {'nda_bias': 1.5, 'indi_bias': -1.5},  # Strong NDA lean
            'News18-IPSOS': {'nda_bias': 0.2, 'indi_bias': -0.2},  # Neutral
            'ABP News-C-Voter': {'nda_bias': -0.4, 'indi_bias': 0.4},
            'Local_Poll': {'nda_bias': 0.0, 'indi_bias': 0.0},  # Unknown bias
            'Unknown': {'nda_bias': 0.0, 'indi_bias': 0.0},
            # Exit poll specific house effects (generally more accurate)
            'CVoter Exit Poll': {'nda_bias': -0.2, 'indi_bias': 0.2},  # Reduced bias for exit polls
            'Axis My India Exit Poll': {'nda_bias': 0.3, 'indi_bias': -0.3},
            'CNX Exit Poll': {'nda_bias': 0.5, 'indi_bias': -0.5},
            'TOI Exit Poll': {'nda_bias': 0.1, 'indi_bias': -0.1},
            'NDTV Exit Poll': {'nda_bias': -0.1, 'indi_bias': 0.1},
            'India Today-Axis Exit Poll': {'nda_bias': 0.3, 'indi_bias': -0.3}
        }
        
        print(f"   Loaded {len(self.pollster_reliability)} pollster profiles")
    
    def correct_poll_data(self, polls_df: pd.DataFrame) -> pd.DataFrame:
        """Apply comprehensive poll corrections"""
        print("🔄 Applying poll corrections...")
        
        if polls_df.empty:
            print("   No poll data to correct")
            return polls_df
        
        # Load pollster database
        self.load_pollster_database()
        
        corrected_polls = polls_df.copy()
        
        # Apply house effect corrections
        corrected_polls = self._apply_house_effect_corrections(corrected_polls)
        
        # Apply sample size adjustments
        corrected_polls = self._apply_sample_size_adjustments(corrected_polls)
        
        # Apply recency weighting
        corrected_polls = self._apply_recency_weighting(corrected_polls)
        
        # Calculate reliability scores
        corrected_polls = self._calculate_reliability_scores(corrected_polls)
        
        # Apply methodology adjustments
        corrected_polls = self._apply_methodology_adjustments(corrected_polls)
        
        print(f"   Poll corrections applied to {len(corrected_polls)} polls")
        return corrected_polls
    
    def _apply_house_effect_corrections(self, polls_df: pd.DataFrame) -> pd.DataFrame:
        """Apply house effect corrections to remove pollster bias"""
        print("   Applying house effect corrections...")
        
        corrected_polls = polls_df.copy()
        
        for idx, poll in corrected_polls.iterrows():
            pollster = poll.get('source', 'Unknown')
            
            # Get house effect for this pollster
            house_effect = self.house_effects.get(pollster, self.house_effects['Unknown'])
            
            # Apply corrections
            if 'nda_vote' in poll:
                original_nda = poll['nda_vote']
                original_indi = poll.get('indi_vote', 100 - original_nda - poll.get('others', 0))
                
                # Correct for house effects
                corrected_nda = original_nda - house_effect['nda_bias']
                corrected_indi = original_indi - house_effect['indi_bias']
                
                # Ensure values sum to reasonable total (allowing for others)
                others = poll.get('others', 0)
                total_corrected = corrected_nda + corrected_indi + others
                
                if total_corrected > 0:
                    # Normalize to maintain total
                    normalization_factor = (100 - others) / (corrected_nda + corrected_indi)
                    corrected_nda *= normalization_factor
                    corrected_indi *= normalization_factor
                
                # Store corrected values
                corrected_polls.loc[idx, 'nda_vote_corrected'] = max(0, min(100, corrected_nda))
                corrected_polls.loc[idx, 'indi_vote_corrected'] = max(0, min(100, corrected_indi))
                corrected_polls.loc[idx, 'house_effect_nda'] = house_effect['nda_bias']
                corrected_polls.loc[idx, 'house_effect_indi'] = house_effect['indi_bias']
            
        return corrected_polls
    
    def _apply_sample_size_adjustments(self, polls_df: pd.DataFrame) -> pd.DataFrame:
        """Apply sample size-based confidence adjustments"""
        print("   Applying sample size adjustments...")
        
        corrected_polls = polls_df.copy()
        
        for idx, poll in corrected_polls.iterrows():
            sample_size = poll.get('sample_size', 1000)
            
            # Calculate margin of error based on sample size
            if sample_size > 0:
                # Standard formula for margin of error at 95% confidence
                moe = 1.96 * np.sqrt(0.25 / sample_size) * 100  # 25% for maximum variance
                
                # Calculate sample size weight (larger samples get higher weight)
                sample_weight = min(1.0, sample_size / 2000)  # Cap at 2000 sample size
                
                # Adjust for small sample sizes
                if sample_size < self.min_sample_size:
                    sample_weight *= 0.5  # Reduce weight for small samples
                
                corrected_polls.loc[idx, 'margin_of_error'] = moe
                corrected_polls.loc[idx, 'sample_weight'] = sample_weight
                corrected_polls.loc[idx, 'sample_size_adjusted'] = sample_size
            else:
                corrected_polls.loc[idx, 'margin_of_error'] = 10.0  # High uncertainty
                corrected_polls.loc[idx, 'sample_weight'] = 0.1  # Very low weight
                corrected_polls.loc[idx, 'sample_size_adjusted'] = 500  # Default
        
        return corrected_polls
    
    def _apply_recency_weighting(self, polls_df: pd.DataFrame) -> pd.DataFrame:
        """Apply time-based recency weighting"""
        print("   Applying recency weighting...")
        
        corrected_polls = polls_df.copy()
        
        # Convert date column to datetime if it's not already
        if 'date' in corrected_polls.columns:
            corrected_polls['date'] = pd.to_datetime(corrected_polls['date'])
            current_date = datetime.now()
            
            for idx, poll in corrected_polls.iterrows():
                poll_date = poll['date']
                
                if pd.isna(poll_date):
                    age_days = 15  # Default age
                else:
                    age_days = (current_date - poll_date).days
                
                # Calculate recency weight (exponential decay)
                # Half-life of 7 days
                recency_weight = np.exp(-age_days / 10.0)
                
                # Apply maximum age limit
                if age_days > self.max_age_days:
                    recency_weight *= 0.5  # Reduce weight for old polls
                
                corrected_polls.loc[idx, 'age_days'] = age_days
                corrected_polls.loc[idx, 'recency_weight'] = recency_weight
        else:
            # If no date column, assume all polls are recent
            corrected_polls['age_days'] = 7
            corrected_polls['recency_weight'] = 1.0
        
        return corrected_polls
    
    def _calculate_reliability_scores(self, polls_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate overall reliability scores for each poll"""
        print("   Calculating reliability scores...")
        
        corrected_polls = polls_df.copy()
        
        for idx, poll in corrected_polls.iterrows():
            pollster = poll.get('source', 'Unknown')
            
            # Get pollster reliability metrics
            reliability_data = self.pollster_reliability.get(pollster, self.pollster_reliability['Unknown'])
            
            # Base reliability score
            base_reliability = reliability_data['reliability']
            sample_quality = reliability_data['sample_quality']
            methodology_score = reliability_data['methodology_score']
            
            # Get weights from previous calculations
            sample_weight = poll.get('sample_weight', 0.5)
            recency_weight = poll.get('recency_weight', 0.5)
            
            # Calculate composite reliability score
            reliability_score = (
                base_reliability * 0.4 +
                sample_quality * sample_weight * 0.3 +
                methodology_score * 0.2 +
                recency_weight * 0.1
            )
            
            # Apply minimum threshold
            if reliability_score < self.reliability_threshold:
                reliability_score *= 0.7  # Reduce unreliable polls
            
            corrected_polls.loc[idx, 'reliability_score'] = reliability_score
            corrected_polls.loc[idx, 'pollster_base_reliability'] = base_reliability
        
        return corrected_polls
    
    def _apply_methodology_adjustments(self, polls_df: pd.DataFrame) -> pd.DataFrame:
        """Apply methodology-based adjustments"""
        print("   Applying methodology adjustments...")
        
        corrected_polls = polls_df.copy()
        
        for idx, poll in corrected_polls.iterrows():
            # Check for methodology indicators
            methodology_type = poll.get('methodology', 'Unknown')
            
            # Methodology adjustments
            methodology_adjustments = {
                'CATI': {'reliability_boost': 0.05, 'uncertainty_reduction': 0.8},  # Phone interviews
                'Face-to-Face': {'reliability_boost': 0.1, 'uncertainty_reduction': 0.9},  # Best method
                'Online': {'reliability_boost': -0.05, 'uncertainty_reduction': 0.7},  # Less reliable
                'IVR': {'reliability_boost': -0.1, 'uncertainty_reduction': 0.6},  # Automated calls
                'Mixed': {'reliability_boost': 0.02, 'uncertainty_reduction': 0.75},
                'Unknown': {'reliability_boost': 0.0, 'uncertainty_reduction': 0.7}
            }
            
            adjustment = methodology_adjustments.get(methodology_type, methodology_adjustments['Unknown'])
            
            # Apply methodology adjustment to reliability
            current_reliability = poll.get('reliability_score', 0.5)
            adjusted_reliability = current_reliability + adjustment['reliability_boost']
            adjusted_reliability = max(0.1, min(1.0, adjusted_reliability))
            
            corrected_polls.loc[idx, 'reliability_score_final'] = adjusted_reliability
            corrected_polls.loc[idx, 'methodology_adjustment'] = adjustment['reliability_boost']
            corrected_polls.loc[idx, 'uncertainty_factor'] = adjustment['uncertainty_reduction']
        
        return corrected_polls
    
    def aggregate_corrected_polls(self, corrected_polls_df: pd.DataFrame) -> Dict:
        """Aggregate corrected polls with proper weighting"""
        print("🔄 Aggregating corrected polls...")
        
        if corrected_polls_df.empty:
            return self._get_default_poll_aggregation()
        
        # Use final reliability scores as weights with exit poll bonus
        base_weights = corrected_polls_df.get('reliability_score_final', corrected_polls_df.get('reliability_score', 1.0))
        
        # Apply exit poll bonus
        weights = base_weights.copy()
        for idx, row in corrected_polls_df.iterrows():
            # Check if this is an exit poll
            is_exit_poll = False
            if 'type' in row and row['type'] == 'exit_poll':
                is_exit_poll = True
            elif 'source' in row and 'exit poll' in str(row['source']).lower():
                is_exit_poll = True
            
            if is_exit_poll:
                weights.iloc[idx] *= 2.0  # Double weight for exit polls
                print(f"   Applied exit poll bonus to {row.get('source', 'Unknown')}")
        
        # Calculate weighted averages
        if 'nda_vote_corrected' in corrected_polls_df.columns:
            nda_votes = corrected_polls_df['nda_vote_corrected']
            indi_votes = corrected_polls_df['indi_vote_corrected']
        else:
            nda_votes = corrected_polls_df.get('nda_vote', 45)
            indi_votes = corrected_polls_df.get('indi_vote', 55)
        
        # Weighted aggregation
        total_weight = weights.sum()
        if total_weight > 0:
            weighted_nda = (nda_votes * weights).sum() / total_weight
            weighted_indi = (indi_votes * weights).sum() / total_weight
        else:
            weighted_nda = nda_votes.mean()
            weighted_indi = indi_votes.mean()
        
        # Calculate uncertainty metrics
        poll_volatility = self._calculate_poll_volatility(corrected_polls_df, weights)
        poll_uncertainty = self._calculate_poll_uncertainty(corrected_polls_df, weights)
        
        # Calculate momentum (trend over time)
        poll_momentum = self._calculate_poll_momentum(corrected_polls_df)
        
        aggregation_result = {
            'weighted_nda_vote': weighted_nda,
            'weighted_indi_vote': weighted_indi,
            'poll_lead_nda': weighted_nda - weighted_indi,
            'poll_volatility': poll_volatility,
            'poll_uncertainty': poll_uncertainty,
            'poll_momentum_nda': poll_momentum['nda_momentum'],
            'poll_momentum_indi': poll_momentum['indi_momentum'],
            'n_polls_used': len(corrected_polls_df),
            'total_weight': total_weight,
            'avg_reliability': weights.mean(),
            'aggregation_timestamp': datetime.now().isoformat()
        }
        
        print(f"   Aggregated {len(corrected_polls_df)} polls: NDA {weighted_nda:.1f}%, INDI {weighted_indi:.1f}%")
        return aggregation_result
    
    def _calculate_poll_volatility(self, polls_df: pd.DataFrame, weights: pd.Series) -> float:
        """Calculate poll volatility (weighted standard deviation)"""
        if len(polls_df) < 2:
            return 5.0  # Default volatility
        
        nda_votes = polls_df.get('nda_vote_corrected', polls_df.get('nda_vote', 45))
        
        # Weighted standard deviation
        weighted_mean = (nda_votes * weights).sum() / weights.sum()
        weighted_variance = ((nda_votes - weighted_mean) ** 2 * weights).sum() / weights.sum()
        volatility = np.sqrt(weighted_variance)
        
        return min(15.0, max(1.0, volatility))  # Cap between 1% and 15%
    
    def _calculate_poll_uncertainty(self, polls_df: pd.DataFrame, weights: pd.Series) -> float:
        """Calculate overall poll uncertainty"""
        # Base uncertainty from margin of error
        if 'margin_of_error' in polls_df.columns:
            avg_moe = (polls_df['margin_of_error'] * weights).sum() / weights.sum()
        else:
            avg_moe = 3.5  # Default MOE
        
        # Adjust for number of polls (more polls = less uncertainty)
        n_polls = len(polls_df)
        poll_count_factor = 1.0 / np.sqrt(max(1, n_polls))
        
        # Adjust for reliability
        avg_reliability = weights.mean()
        reliability_factor = 2.0 - avg_reliability  # Lower reliability = higher uncertainty
        
        uncertainty = avg_moe * poll_count_factor * reliability_factor
        return min(10.0, max(2.0, uncertainty))  # Cap between 2% and 10%
    
    def _calculate_poll_momentum(self, polls_df: pd.DataFrame) -> Dict:
        """Calculate polling momentum over time"""
        if len(polls_df) < 2 or 'date' not in polls_df.columns:
            return {'nda_momentum': 0.0, 'indi_momentum': 0.0}
        
        # Sort by date
        sorted_polls = polls_df.sort_values('date')
        
        # Get recent vs older polls
        mid_point = len(sorted_polls) // 2
        recent_polls = sorted_polls.iloc[mid_point:]
        older_polls = sorted_polls.iloc[:mid_point]
        
        if len(recent_polls) == 0 or len(older_polls) == 0:
            return {'nda_momentum': 0.0, 'indi_momentum': 0.0}
        
        # Calculate averages
        nda_col = 'nda_vote_corrected' if 'nda_vote_corrected' in sorted_polls.columns else 'nda_vote'
        indi_col = 'indi_vote_corrected' if 'indi_vote_corrected' in sorted_polls.columns else 'indi_vote'
        
        recent_nda = recent_polls[nda_col].mean()
        older_nda = older_polls[nda_col].mean()
        recent_indi = recent_polls[indi_col].mean()
        older_indi = older_polls[indi_col].mean()
        
        # Calculate momentum (change over time)
        nda_momentum = recent_nda - older_nda
        indi_momentum = recent_indi - older_indi
        
        return {
            'nda_momentum': nda_momentum,
            'indi_momentum': indi_momentum
        }
    
    def _get_default_poll_aggregation(self) -> Dict:
        """Get default poll aggregation when no polls are available"""
        return {
            'weighted_nda_vote': 45.0,
            'weighted_indi_vote': 55.0,
            'poll_lead_nda': -10.0,
            'poll_volatility': 5.0,
            'poll_uncertainty': 8.0,
            'poll_momentum_nda': 0.0,
            'poll_momentum_indi': 0.0,
            'n_polls_used': 0,
            'total_weight': 0.0,
            'avg_reliability': 0.5,
            'aggregation_timestamp': datetime.now().isoformat()
        }
    
    def create_poll_features(self, constituency_df: pd.DataFrame, polls_df: pd.DataFrame) -> pd.DataFrame:
        """Create poll-based features for constituencies"""
        print("🔄 Creating poll-based features...")
        
        # Correct and aggregate polls
        corrected_polls = self.correct_poll_data(polls_df)
        poll_aggregation = self.aggregate_corrected_polls(corrected_polls)
        
        # Add poll features to each constituency
        enhanced_df = constituency_df.copy()
        
        # State-level poll features (same for all constituencies)
        for key, value in poll_aggregation.items():
            if key != 'aggregation_timestamp':
                enhanced_df[key] = value
        
        # Add constituency-specific poll adjustments
        enhanced_df = self._add_constituency_poll_adjustments(enhanced_df, poll_aggregation)
        
        print(f"   Poll features added to {len(enhanced_df)} constituencies")
        return enhanced_df
    
    def _add_constituency_poll_adjustments(self, constituency_df: pd.DataFrame, 
                                         poll_aggregation: Dict) -> pd.DataFrame:
        """Add constituency-specific adjustments to state-level polls"""
        print("   Adding constituency-specific poll adjustments...")
        
        # Regional adjustments based on historical performance vs polls
        regional_adjustments = {
            'Mithilanchal': {'nda_adjustment': -2.0, 'indi_adjustment': 2.0},
            'Central': {'nda_adjustment': 1.0, 'indi_adjustment': -1.0},
            'South': {'nda_adjustment': 0.5, 'indi_adjustment': -0.5},
            'Border': {'nda_adjustment': -1.5, 'indi_adjustment': 1.5}
        }
        
        base_nda_vote = poll_aggregation['weighted_nda_vote']
        base_indi_vote = poll_aggregation['weighted_indi_vote']
        
        for idx, row in constituency_df.iterrows():
            region = row.get('region', 'Central')
            adjustment = regional_adjustments.get(region, {'nda_adjustment': 0, 'indi_adjustment': 0})
            
            # Apply regional adjustments
            adjusted_nda = base_nda_vote + adjustment['nda_adjustment']
            adjusted_indi = base_indi_vote + adjustment['indi_adjustment']
            
            # Store adjusted values
            constituency_df.loc[idx, 'poll_nda_adjusted'] = adjusted_nda
            constituency_df.loc[idx, 'poll_indi_adjusted'] = adjusted_indi
            constituency_df.loc[idx, 'poll_lead_nda_adjusted'] = adjusted_nda - adjusted_indi
            constituency_df.loc[idx, 'regional_poll_adjustment_nda'] = adjustment['nda_adjustment']
            constituency_df.loc[idx, 'regional_poll_adjustment_indi'] = adjustment['indi_adjustment']
        
        return constituency_df
    
    def save_corrected_polls(self, corrected_polls_df: pd.DataFrame, filename: str = None) -> str:
        """Save corrected poll data"""
        if filename is None:
            filename = f"corrected_polls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.features_dir / filename
        corrected_polls_df.to_csv(filepath, index=False)
        
        print(f"✅ Corrected polls saved to {filepath}")
        return str(filepath)
    
    def get_correction_summary(self, original_polls_df: pd.DataFrame, 
                             corrected_polls_df: pd.DataFrame) -> Dict:
        """Generate summary of poll corrections applied"""
        if original_polls_df.empty or corrected_polls_df.empty:
            return {'error': 'No poll data to analyze'}
        
        # Calculate correction impacts
        original_nda_avg = original_polls_df.get('nda_vote', 45).mean()
        corrected_nda_avg = corrected_polls_df.get('nda_vote_corrected', original_nda_avg).mean()
        
        original_indi_avg = original_polls_df.get('indi_vote', 55).mean()
        corrected_indi_avg = corrected_polls_df.get('indi_vote_corrected', original_indi_avg).mean()
        
        summary = {
            'original_polls': len(original_polls_df),
            'corrected_polls': len(corrected_polls_df),
            'corrections_applied': {
                'nda_vote_change': corrected_nda_avg - original_nda_avg,
                'indi_vote_change': corrected_indi_avg - original_indi_avg,
                'lead_change': (corrected_nda_avg - corrected_indi_avg) - (original_nda_avg - original_indi_avg)
            },
            'reliability_metrics': {
                'avg_reliability': corrected_polls_df.get('reliability_score_final', 0.5).mean(),
                'min_reliability': corrected_polls_df.get('reliability_score_final', 0.5).min(),
                'max_reliability': corrected_polls_df.get('reliability_score_final', 0.5).max()
            },
            'house_effects_applied': len(corrected_polls_df[corrected_polls_df.get('house_effect_nda', 0) != 0]),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary