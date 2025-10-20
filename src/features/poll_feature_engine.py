import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from src.config.settings import Config
import json
from scipy import stats


class PollFeatureEngine:
    """Advanced poll-based feature engineering for Bihar election forecasting"""
    
    def __init__(self):
        self.ema_alpha = Config.EMA_ALPHA
        self.constituency_count = Config.CONSTITUENCY_COUNT
        
        # Poll weighting parameters
        self.recency_half_life = 14  # Days for recency decay
        self.min_sample_size = 1000  # Minimum sample size for credibility
        self.max_poll_age = 60  # Maximum age in days to consider
        
        print(f"✅ Poll feature engine initialized with {self.recency_half_life}d half-life")
    
    def calculate_poll_aggregates(self, polls_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate sophisticated poll aggregates with multiple weighting schemes"""
        if polls_df.empty:
            print("⚠️ No poll data available")
            return {}
        
        print(f"🔄 Processing {len(polls_df)} polls for aggregation...")
        
        # Prepare poll data
        polls_df = polls_df.copy()
        polls_df['date'] = pd.to_datetime(polls_df['date'])
        polls_df = polls_df.sort_values('date', ascending=False)
        
        # Filter recent polls
        cutoff_date = datetime.now() - timedelta(days=self.max_poll_age)
        recent_polls = polls_df[polls_df['date'] >= cutoff_date]
        
        if recent_polls.empty:
            print("⚠️ No recent polls found")
            return {}
        
        # Calculate various weights
        recent_polls = self._calculate_poll_weights(recent_polls)
        
        # Multiple aggregation methods
        aggregates = {
            'simple_average': self._simple_average(recent_polls),
            'weighted_average': self._weighted_average(recent_polls),
            'exponential_average': self._exponential_average(recent_polls),
            'bayesian_average': self._bayesian_average(recent_polls),
            'trend_adjusted': self._trend_adjusted_average(recent_polls)
        }
        
        # Meta-aggregate (ensemble of methods)
        aggregates['meta_aggregate'] = self._meta_aggregate(aggregates)
        
        # Calculate confidence intervals
        aggregates['confidence_intervals'] = self._calculate_confidence_intervals(recent_polls)
        
        # Poll momentum and volatility
        aggregates['momentum'] = self._calculate_momentum(recent_polls)
        aggregates['volatility'] = self._calculate_volatility(recent_polls)
        
        print(f"   Meta-aggregate: NDA {aggregates['meta_aggregate']['nda_vote']:.1f}%, INDI {aggregates['meta_aggregate']['indi_vote']:.1f}%")
        
        return aggregates
    
    def _calculate_poll_weights(self, polls_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate multiple weighting schemes for polls"""
        polls_df = polls_df.copy()
        
        # Recency weight (exponential decay)
        polls_df['days_old'] = (datetime.now() - polls_df['date']).dt.days
        polls_df['recency_weight'] = np.exp(-polls_df['days_old'] / self.recency_half_life)
        
        # Sample size weight (square root)
        polls_df['size_weight'] = np.sqrt(polls_df['sample_size'])
        
        # Quality weight (based on margin of error)
        polls_df['quality_weight'] = 1 / (polls_df['moe'] + 0.5)  # Add 0.5 to avoid division by zero
        
        # Pollster reliability weight (simplified - in production, use historical accuracy)
        pollster_reliability = {
            'C-Voter': 0.9,
            'India Today-Axis': 0.95,
            'ABP-CVoter': 0.85,
            'Times Now-Polstrat': 0.8,
            'Republic-Matrize': 0.75
        }
        polls_df['pollster_weight'] = polls_df['source'].map(pollster_reliability).fillna(0.7)
        
        # Combined weight
        polls_df['combined_weight'] = (
            polls_df['recency_weight'] * 
            polls_df['size_weight'] * 
            polls_df['quality_weight'] * 
            polls_df['pollster_weight']
        )
        
        # Normalize weights
        polls_df['normalized_weight'] = polls_df['combined_weight'] / polls_df['combined_weight'].sum()
        
        return polls_df
    
    def _simple_average(self, polls_df: pd.DataFrame) -> Dict[str, float]:
        """Simple unweighted average"""
        return {
            'nda_vote': polls_df['nda_vote'].mean(),
            'indi_vote': polls_df['indi_vote'].mean(),
            'others': polls_df['others'].mean(),
            'method': 'simple_average'
        }
    
    def _weighted_average(self, polls_df: pd.DataFrame) -> Dict[str, float]:
        """Weighted average using combined weights"""
        weights = polls_df['normalized_weight']
        
        return {
            'nda_vote': np.average(polls_df['nda_vote'], weights=weights),
            'indi_vote': np.average(polls_df['indi_vote'], weights=weights),
            'others': np.average(polls_df['others'], weights=weights),
            'method': 'weighted_average'
        }
    
    def _exponential_average(self, polls_df: pd.DataFrame) -> Dict[str, float]:
        """Exponential moving average giving more weight to recent polls"""
        # Sort by date (oldest first for EMA calculation)
        sorted_polls = polls_df.sort_values('date')
        
        nda_ema = sorted_polls['nda_vote'].iloc[0]
        indi_ema = sorted_polls['indi_vote'].iloc[0]
        others_ema = sorted_polls['others'].iloc[0]
        
        alpha = 0.3  # EMA smoothing factor
        
        for _, poll in sorted_polls.iloc[1:].iterrows():
            nda_ema = alpha * poll['nda_vote'] + (1 - alpha) * nda_ema
            indi_ema = alpha * poll['indi_vote'] + (1 - alpha) * indi_ema
            others_ema = alpha * poll['others'] + (1 - alpha) * others_ema
        
        return {
            'nda_vote': nda_ema,
            'indi_vote': indi_ema,
            'others': others_ema,
            'method': 'exponential_average'
        }
    
    def _bayesian_average(self, polls_df: pd.DataFrame) -> Dict[str, float]:
        """Bayesian average incorporating prior beliefs"""
        # Prior beliefs (based on 2020 election results)
        prior_nda = 38.0
        prior_indi = 42.0
        prior_others = 20.0
        prior_weight = 2.0  # Equivalent to 2 polls worth of prior belief
        
        # Calculate weighted average with priors
        total_weight = polls_df['normalized_weight'].sum() + prior_weight
        
        nda_bayesian = (
            (polls_df['nda_vote'] * polls_df['normalized_weight']).sum() + 
            prior_nda * prior_weight
        ) / total_weight
        
        indi_bayesian = (
            (polls_df['indi_vote'] * polls_df['normalized_weight']).sum() + 
            prior_indi * prior_weight
        ) / total_weight
        
        others_bayesian = (
            (polls_df['others'] * polls_df['normalized_weight']).sum() + 
            prior_others * prior_weight
        ) / total_weight
        
        return {
            'nda_vote': nda_bayesian,
            'indi_vote': indi_bayesian,
            'others': others_bayesian,
            'method': 'bayesian_average'
        }
    
    def _trend_adjusted_average(self, polls_df: pd.DataFrame) -> Dict[str, float]:
        """Trend-adjusted average accounting for momentum"""
        if len(polls_df) < 3:
            return self._weighted_average(polls_df)
        
        # Calculate trend using linear regression
        polls_df = polls_df.sort_values('date')
        days_since_first = (polls_df['date'] - polls_df['date'].iloc[0]).dt.days
        
        # Linear trend for each party
        nda_trend = stats.linregress(days_since_first, polls_df['nda_vote']).slope
        indi_trend = stats.linregress(days_since_first, polls_df['indi_vote']).slope
        others_trend = stats.linregress(days_since_first, polls_df['others']).slope
        
        # Project trend forward by 7 days (typical election horizon)
        projection_days = 7
        
        # Base weighted average
        base_avg = self._weighted_average(polls_df)
        
        return {
            'nda_vote': base_avg['nda_vote'] + nda_trend * projection_days,
            'indi_vote': base_avg['indi_vote'] + indi_trend * projection_days,
            'others': base_avg['others'] + others_trend * projection_days,
            'nda_trend': nda_trend,
            'indi_trend': indi_trend,
            'method': 'trend_adjusted'
        }
    
    def _meta_aggregate(self, aggregates: Dict) -> Dict[str, float]:
        """Meta-aggregate combining multiple methods"""
        methods = ['weighted_average', 'exponential_average', 'bayesian_average', 'trend_adjusted']
        method_weights = [0.3, 0.25, 0.25, 0.2]  # Weights for each method
        
        nda_meta = sum(aggregates[method]['nda_vote'] * weight 
                      for method, weight in zip(methods, method_weights))
        
        indi_meta = sum(aggregates[method]['indi_vote'] * weight 
                       for method, weight in zip(methods, method_weights))
        
        others_meta = sum(aggregates[method]['others'] * weight 
                         for method, weight in zip(methods, method_weights))
        
        return {
            'nda_vote': nda_meta,
            'indi_vote': indi_meta,
            'others': others_meta,
            'method': 'meta_aggregate'
        }
    
    def _calculate_confidence_intervals(self, polls_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate confidence intervals for poll estimates"""
        # Use weighted standard deviation
        weights = polls_df['normalized_weight']
        
        def weighted_std(values, weights):
            average = np.average(values, weights=weights)
            variance = np.average((values - average)**2, weights=weights)
            return np.sqrt(variance)
        
        nda_std = weighted_std(polls_df['nda_vote'], weights)
        indi_std = weighted_std(polls_df['indi_vote'], weights)
        
        # 95% confidence intervals (assuming normal distribution)
        z_score = 1.96
        
        nda_mean = np.average(polls_df['nda_vote'], weights=weights)
        indi_mean = np.average(polls_df['indi_vote'], weights=weights)
        
        return {
            'nda': {
                'lower': nda_mean - z_score * nda_std,
                'upper': nda_mean + z_score * nda_std,
                'std': nda_std
            },
            'indi': {
                'lower': indi_mean - z_score * indi_std,
                'upper': indi_mean + z_score * indi_std,
                'std': indi_std
            }
        }
    
    def _calculate_momentum(self, polls_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate polling momentum (recent vs earlier polls)"""
        if len(polls_df) < 4:
            return {'nda_momentum': 0.0, 'indi_momentum': 0.0}
        
        # Sort by date
        sorted_polls = polls_df.sort_values('date')
        
        # Compare recent third vs earlier third
        n_polls = len(sorted_polls)
        recent_third = sorted_polls.iloc[-n_polls//3:]
        earlier_third = sorted_polls.iloc[:n_polls//3]
        
        nda_momentum = recent_third['nda_vote'].mean() - earlier_third['nda_vote'].mean()
        indi_momentum = recent_third['indi_vote'].mean() - earlier_third['indi_vote'].mean()
        
        return {
            'nda_momentum': nda_momentum,
            'indi_momentum': indi_momentum
        }
    
    def _calculate_volatility(self, polls_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate polling volatility (standard deviation)"""
        return {
            'nda_volatility': polls_df['nda_vote'].std(),
            'indi_volatility': polls_df['indi_vote'].std(),
            'overall_volatility': (polls_df['nda_vote'].std() + polls_df['indi_vote'].std()) / 2
        }
    
    def apply_poll_swing_to_constituencies(self, features_df: pd.DataFrame, poll_aggregates: Dict) -> pd.DataFrame:
        """Apply poll-based swing to constituency features"""
        if not poll_aggregates or 'meta_aggregate' not in poll_aggregates:
            print("⚠️ No poll aggregates to apply")
            return features_df
        
        df = features_df.copy()
        
        print(f"🔄 Applying poll swing to {len(df)} constituencies...")
        
        # Get meta-aggregate results
        meta_agg = poll_aggregates['meta_aggregate']
        current_nda = meta_agg['nda_vote']
        current_indi = meta_agg['indi_vote']
        
        # Calculate swing from baseline (2020 results)
        baseline_nda = df['nda_share_2020'].mean()
        baseline_indi = df['indi_share_2020'].mean()
        
        nda_swing = current_nda - baseline_nda
        indi_swing = current_indi - baseline_indi
        
        print(f"   Calculated swing: NDA {nda_swing:+.1f}%, INDI {indi_swing:+.1f}%")
        
        # Apply uniform swing with regional modifiers
        df = self._apply_uniform_swing(df, nda_swing, indi_swing)
        
        # Apply momentum effects
        if 'momentum' in poll_aggregates:
            df = self._apply_momentum_effects(df, poll_aggregates['momentum'])
        
        # Apply volatility adjustments
        if 'volatility' in poll_aggregates:
            df = self._apply_volatility_adjustments(df, poll_aggregates['volatility'])
        
        # Update confidence intervals
        if 'confidence_intervals' in poll_aggregates:
            df = self._update_confidence_intervals(df, poll_aggregates['confidence_intervals'])
        
        return df
    
    def _apply_uniform_swing(self, df: pd.DataFrame, nda_swing: float, indi_swing: float) -> pd.DataFrame:
        """Apply uniform swing with regional variations"""
        # Regional swing modifiers (some regions swing more than others)
        regional_modifiers = {
            'Mithilanchal': {'nda': 0.8, 'indi': 1.2},  # INDI stronghold - amplifies INDI swing
            'Central Bihar': {'nda': 1.0, 'indi': 1.0},  # Neutral swing
            'South Bihar': {'nda': 1.2, 'indi': 0.8},   # NDA leaning - amplifies NDA swing
            'East Bihar': {'nda': 1.0, 'indi': 1.0},    # Neutral swing
            'Border Areas': {'nda': 0.7, 'indi': 1.3}   # INDI stronghold - amplifies INDI swing
        }
        
        for region, modifiers in regional_modifiers.items():
            region_mask = df['region'] == region
            
            if region_mask.any():
                regional_nda_swing = nda_swing * modifiers['nda']
                regional_indi_swing = indi_swing * modifiers['indi']
                
                # Apply swing with EMA smoothing
                df.loc[region_mask, 'poll_lead_nda'] = (
                    (1 - self.ema_alpha) * df.loc[region_mask, 'poll_lead_nda'] + 
                    self.ema_alpha * (df.loc[region_mask, 'nda_margin_2020'] + regional_nda_swing - regional_indi_swing)
                )
        
        return df
    
    def _apply_momentum_effects(self, df: pd.DataFrame, momentum: Dict) -> pd.DataFrame:
        """Apply momentum effects to poll features"""
        nda_momentum = momentum.get('nda_momentum', 0.0)
        indi_momentum = momentum.get('indi_momentum', 0.0)
        
        # Update momentum features with EMA
        df['poll_momentum_nda'] = (
            (1 - self.ema_alpha) * df['poll_momentum_nda'] + 
            self.ema_alpha * nda_momentum
        )
        
        # Momentum affects competitiveness (higher momentum = more volatile)
        momentum_effect = abs(nda_momentum) + abs(indi_momentum)
        df['momentum_volatility'] = momentum_effect
        
        return df
    
    def _apply_volatility_adjustments(self, df: pd.DataFrame, volatility: Dict) -> pd.DataFrame:
        """Apply volatility adjustments to uncertainty measures"""
        overall_volatility = volatility.get('overall_volatility', 2.5)
        
        # Update poll volatility with EMA
        df['poll_volatility'] = (
            (1 - self.ema_alpha) * df['poll_volatility'] + 
            self.ema_alpha * overall_volatility
        )
        
        return df
    
    def _update_confidence_intervals(self, df: pd.DataFrame, confidence_intervals: Dict) -> pd.DataFrame:
        """Update constituency-level confidence intervals"""
        nda_std = confidence_intervals['nda']['std']
        indi_std = confidence_intervals['indi']['std']
        
        # Add confidence interval features
        df['nda_ci_lower'] = df['poll_lead_nda'] - 1.96 * nda_std
        df['nda_ci_upper'] = df['poll_lead_nda'] + 1.96 * nda_std
        
        df['indi_ci_lower'] = -df['poll_lead_nda'] - 1.96 * indi_std
        df['indi_ci_upper'] = -df['poll_lead_nda'] + 1.96 * indi_std
        
        # Uncertainty score (wider intervals = more uncertain)
        df['poll_uncertainty'] = (df['nda_ci_upper'] - df['nda_ci_lower']) / 2
        
        return df
    
    def calculate_seat_probabilities(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate sophisticated seat win probabilities"""
        print("🔄 Calculating advanced seat probabilities...")
        
        # Base probability from poll lead (sigmoid transformation)
        df['base_prob_nda'] = 1 / (1 + np.exp(-df['poll_lead_nda'] / 5))
        
        # Adjust for uncertainty (more uncertain = closer to 50%)
        uncertainty_factor = df.get('poll_uncertainty', 5.0) / 10
        df['uncertainty_adjusted_prob'] = (
            df['base_prob_nda'] * (1 - uncertainty_factor) + 
            0.5 * uncertainty_factor
        )
        
        # Adjust for momentum (positive momentum increases probability)
        momentum_adjustment = df.get('poll_momentum_nda', 0.0) / 20  # Scale momentum effect
        df['momentum_adjusted_prob'] = np.clip(
            df['uncertainty_adjusted_prob'] + momentum_adjustment,
            0.01, 0.99
        )
        
        # Final probability with random noise for Monte Carlo
        noise_std = df.get('poll_volatility', 2.5) / 50  # Scale volatility to probability noise
        df['final_nda_prob'] = np.clip(
            df['momentum_adjusted_prob'] + np.random.normal(0, noise_std, len(df)),
            0.01, 0.99
        )
        
        return df
    
    def generate_poll_feature_summary(self, df: pd.DataFrame, poll_aggregates: Dict) -> Dict:
        """Generate comprehensive summary of poll-based features"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_constituencies': len(df),
            
            # Poll aggregates summary
            'poll_aggregates': poll_aggregates,
            
            # Constituency-level statistics
            'constituency_stats': {
                'avg_poll_lead_nda': df['poll_lead_nda'].mean(),
                'std_poll_lead_nda': df['poll_lead_nda'].std(),
                'avg_momentum': df.get('poll_momentum_nda', pd.Series([0])).mean(),
                'avg_volatility': df.get('poll_volatility', pd.Series([2.5])).mean(),
                'avg_uncertainty': df.get('poll_uncertainty', pd.Series([5.0])).mean()
            },
            
            # Probability distribution
            'probability_distribution': {
                'safe_nda': len(df[df.get('final_nda_prob', df.get('nda_win_prob', pd.Series([0.5]))) > 0.7]),
                'lean_nda': len(df[(df.get('final_nda_prob', df.get('nda_win_prob', pd.Series([0.5]))) > 0.55) & 
                                 (df.get('final_nda_prob', df.get('nda_win_prob', pd.Series([0.5]))) <= 0.7)]),
                'toss_up': len(df[(df.get('final_nda_prob', df.get('nda_win_prob', pd.Series([0.5]))) >= 0.45) & 
                                (df.get('final_nda_prob', df.get('nda_win_prob', pd.Series([0.5]))) <= 0.55)]),
                'lean_indi': len(df[(df.get('final_nda_prob', df.get('nda_win_prob', pd.Series([0.5]))) >= 0.3) & 
                                  (df.get('final_nda_prob', df.get('nda_win_prob', pd.Series([0.5]))) < 0.45)]),
                'safe_indi': len(df[df.get('final_nda_prob', df.get('nda_win_prob', pd.Series([0.5]))) < 0.3])
            },
            
            # Regional analysis
            'regional_analysis': {}
        }
        
        # Regional breakdown
        for region in df['region'].unique():
            region_df = df[df['region'] == region]
            prob_col = region_df.get('final_nda_prob', region_df.get('nda_win_prob', pd.Series([0.5] * len(region_df))))
            
            summary['regional_analysis'][region] = {
                'constituencies': len(region_df),
                'avg_nda_prob': prob_col.mean(),
                'avg_poll_lead': region_df['poll_lead_nda'].mean(),
                'expected_nda_seats': (prob_col > 0.5).sum(),
                'competitive_seats': ((prob_col >= 0.4) & (prob_col <= 0.6)).sum()
            }
        
        return summary