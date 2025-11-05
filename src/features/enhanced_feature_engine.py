import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from src.config.settings import Config
import json
import warnings
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from scipy import stats
import logging

warnings.filterwarnings('ignore')

class EnhancedFeatureEngine:
    """Advanced feature engineering with historical swing analysis and domain expertise"""
    
    def __init__(self):
        self.features_dir = Config.FEATURES_DIR
        self.data_dir = Config.DATA_DIR
        self.features_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize scalers for feature normalization
        self.standard_scaler = StandardScaler()
        self.minmax_scaler = MinMaxScaler()
        
        # Feature validation thresholds
        self.min_predictive_power = 0.01  # Minimum correlation with target
        self.max_missing_rate = 0.3  # Maximum allowed missing values
        self.max_correlation = 0.95  # Maximum correlation between features
        
        # Historical data cache
        self._historical_data_cache = {}
        
        self.logger = logging.getLogger(__name__)
        print(f"✅ Enhanced Feature Engine initialized")
    
    def create_base_features(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Create base feature set with validation"""
        print("🔄 Creating base feature set...")
        
        # Start with existing features
        base_features = constituency_df.copy()
        
        # Ensure required columns exist
        required_columns = ['constituency', 'region']
        for col in required_columns:
            if col not in base_features.columns:
                raise ValueError(f"Required column '{col}' not found in input data")
        
        # Add feature creation timestamp
        base_features['feature_creation_timestamp'] = datetime.now().isoformat()
        
        print(f"   Base features created: {len(base_features)} constituencies, {len(base_features.columns)} features")
        return base_features
    
    def load_historical_data(self, data_type: str, year: int = None) -> pd.DataFrame:
        """Load historical election data with caching"""
        cache_key = f"{data_type}_{year}" if year else data_type
        
        if cache_key in self._historical_data_cache:
            return self._historical_data_cache[cache_key].copy()
        
        # Define data file paths
        data_paths = {
            'election_2020': self.data_dir / 'historical' / 'bihar_2020_results.csv',
            'election_2015': self.data_dir / 'historical' / 'bihar_2015_results.csv',
            'demographics': self.data_dir / 'static' / 'constituency_demographics.csv',
            'polling_history': self.data_dir / 'historical' / 'polling_data_historical.csv'
        }
        
        file_path = data_paths.get(data_type)
        if not file_path or not file_path.exists():
            self.logger.warning(f"Historical data file not found: {file_path}")
            return pd.DataFrame()
        
        try:
            data = pd.read_csv(file_path)
            self._historical_data_cache[cache_key] = data.copy()
            print(f"   Loaded {data_type} data: {len(data)} records")
            return data
        except Exception as e:
            self.logger.error(f"Error loading historical data {data_type}: {e}")
            return pd.DataFrame()
    
    def calculate_swing_patterns(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate historical swing patterns between elections"""
        print("🔄 Calculating swing patterns...")
        
        # Load historical election results
        results_2020 = self.load_historical_data('election_2020')
        results_2015 = self.load_historical_data('election_2015')
        
        if results_2020.empty or results_2015.empty:
            self.logger.warning("Historical election data not available, using default swing values")
            return self._add_default_swing_features(constituency_df)
        
        # Calculate swing for each constituency
        swing_data = []
        
        for _, row in constituency_df.iterrows():
            constituency = row['constituency']
            
            # Find matching records in historical data
            data_2020 = results_2020[results_2020['constituency'] == constituency]
            data_2015 = results_2015[results_2015['constituency'] == constituency]
            
            if data_2020.empty or data_2015.empty:
                # Use regional average if constituency data not available
                swing_features = self._calculate_regional_swing(constituency, row['region'], results_2020, results_2015)
            else:
                swing_features = self._calculate_constituency_swing(data_2020.iloc[0], data_2015.iloc[0])
            
            swing_features['constituency'] = constituency
            swing_data.append(swing_features)
        
        swing_df = pd.DataFrame(swing_data)
        
        # Merge with original data
        enhanced_df = constituency_df.merge(swing_df, on='constituency', how='left')
        
        print(f"   Swing patterns calculated for {len(swing_df)} constituencies")
        return enhanced_df
    
    def _calculate_constituency_swing(self, data_2020: pd.Series, data_2015: pd.Series) -> Dict:
        """Calculate swing metrics for a single constituency"""
        # Calculate vote share changes
        nda_swing = data_2020.get('nda_vote_share', 0) - data_2015.get('nda_vote_share', 0)
        indi_swing = data_2020.get('indi_vote_share', 0) - data_2015.get('indi_vote_share', 0)
        
        # Calculate margin changes
        margin_2020 = abs(data_2020.get('nda_vote_share', 0) - data_2020.get('indi_vote_share', 0))
        margin_2015 = abs(data_2015.get('nda_vote_share', 0) - data_2015.get('indi_vote_share', 0))
        margin_change = margin_2020 - margin_2015
        
        # Calculate volatility (sum of absolute swings)
        volatility = abs(nda_swing) + abs(indi_swing)
        
        # Determine incumbent advantage
        winner_2015 = 'NDA' if data_2015.get('nda_vote_share', 0) > data_2015.get('indi_vote_share', 0) else 'INDI'
        winner_2020 = 'NDA' if data_2020.get('nda_vote_share', 0) > data_2020.get('indi_vote_share', 0) else 'INDI'
        incumbent_retained = 1 if winner_2015 == winner_2020 else 0
        
        return {
            'swing_nda_2015_2020': nda_swing,
            'swing_indi_2015_2020': indi_swing,
            'margin_change_2015_2020': margin_change,
            'volatility_2015_2020': volatility,
            'incumbent_retained': incumbent_retained,
            'incumbent_advantage': nda_swing if winner_2015 == 'NDA' else -nda_swing
        }
    
    def _calculate_regional_swing(self, constituency: str, region: str, 
                                results_2020: pd.DataFrame, results_2015: pd.DataFrame) -> Dict:
        """Calculate regional average swing when constituency data is missing"""
        # Filter by region
        region_2020 = results_2020[results_2020['region'] == region] if 'region' in results_2020.columns else results_2020
        region_2015 = results_2015[results_2015['region'] == region] if 'region' in results_2015.columns else results_2015
        
        if region_2020.empty or region_2015.empty:
            return self._get_default_swing_values()
        
        # Calculate regional averages
        avg_nda_2020 = region_2020['nda_vote_share'].mean() if 'nda_vote_share' in region_2020.columns else 0
        avg_nda_2015 = region_2015['nda_vote_share'].mean() if 'nda_vote_share' in region_2015.columns else 0
        avg_indi_2020 = region_2020['indi_vote_share'].mean() if 'indi_vote_share' in region_2020.columns else 0
        avg_indi_2015 = region_2015['indi_vote_share'].mean() if 'indi_vote_share' in region_2015.columns else 0
        
        nda_swing = avg_nda_2020 - avg_nda_2015
        indi_swing = avg_indi_2020 - avg_indi_2015
        volatility = abs(nda_swing) + abs(indi_swing)
        
        return {
            'swing_nda_2015_2020': nda_swing,
            'swing_indi_2015_2020': indi_swing,
            'margin_change_2015_2020': 0,  # Unknown for regional average
            'volatility_2015_2020': volatility,
            'incumbent_retained': 0.5,  # Neutral for regional average
            'incumbent_advantage': 0
        }
    
    def _add_default_swing_features(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add default swing features when historical data is unavailable"""
        default_values = self._get_default_swing_values()
        
        for key, value in default_values.items():
            constituency_df[key] = value
        
        return constituency_df
    
    def _get_default_swing_values(self) -> Dict:
        """Get default swing values for missing data"""
        return {
            'swing_nda_2015_2020': 0.0,
            'swing_indi_2015_2020': 0.0,
            'margin_change_2015_2020': 0.0,
            'volatility_2015_2020': 5.0,  # Moderate volatility
            'incumbent_retained': 0.5,
            'incumbent_advantage': 0.0
        }
    
    def validate_features(self, features_df: pd.DataFrame, target_column: str = None) -> Dict:
        """Validate feature quality and predictive power"""
        print("🔄 Validating feature quality...")
        
        validation_results = {
            'total_features': len(features_df.columns),
            'total_samples': len(features_df),
            'missing_data_report': {},
            'correlation_issues': [],
            'low_variance_features': [],
            'predictive_power': {},
            'validation_passed': True,
            'issues_found': []
        }
        
        # Check for missing data
        missing_rates = features_df.isnull().mean()
        high_missing = missing_rates[missing_rates > self.max_missing_rate]
        
        if not high_missing.empty:
            validation_results['missing_data_report'] = high_missing.to_dict()
            validation_results['issues_found'].append(f"High missing data in {len(high_missing)} features")
        
        # Check for low variance features
        numeric_features = features_df.select_dtypes(include=[np.number])
        low_variance = []
        
        for col in numeric_features.columns:
            if numeric_features[col].var() < 1e-6:
                low_variance.append(col)
        
        if low_variance:
            validation_results['low_variance_features'] = low_variance
            validation_results['issues_found'].append(f"Low variance in {len(low_variance)} features")
        
        # Check for high correlation between features
        if len(numeric_features.columns) > 1:
            corr_matrix = numeric_features.corr().abs()
            high_corr_pairs = []
            
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    if corr_matrix.iloc[i, j] > self.max_correlation:
                        high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
            
            if high_corr_pairs:
                validation_results['correlation_issues'] = high_corr_pairs
                validation_results['issues_found'].append(f"High correlation in {len(high_corr_pairs)} feature pairs")
        
        # Check predictive power if target is provided
        if target_column and target_column in features_df.columns:
            target = features_df[target_column]
            predictive_power = {}
            
            for col in numeric_features.columns:
                if col != target_column:
                    try:
                        correlation = abs(numeric_features[col].corr(target))
                        predictive_power[col] = correlation
                        
                        if correlation < self.min_predictive_power:
                            validation_results['issues_found'].append(f"Low predictive power in feature {col}")
                    except:
                        predictive_power[col] = 0.0
            
            validation_results['predictive_power'] = predictive_power
        
        # Overall validation status
        validation_results['validation_passed'] = len(validation_results['issues_found']) == 0
        
        print(f"   Feature validation complete: {validation_results['total_features']} features, "
              f"{len(validation_results['issues_found'])} issues found")
        
        return validation_results
    
    def save_features(self, features_df: pd.DataFrame, filename: str = None) -> str:
        """Save features with metadata"""
        if filename is None:
            filename = f"enhanced_features_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.features_dir / filename
        
        # Save features
        features_df.to_csv(filepath, index=False)
        
        # Save metadata
        metadata = {
            'filename': filename,
            'created_at': datetime.now().isoformat(),
            'n_constituencies': len(features_df),
            'n_features': len(features_df.columns),
            'feature_names': list(features_df.columns),
            'data_types': features_df.dtypes.astype(str).to_dict()
        }
        
        metadata_path = self.features_dir / f"{filename.replace('.csv', '_metadata.json')}"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Features saved to {filepath}")
        return str(filepath)
    
    def load_features(self, filename: str) -> pd.DataFrame:
        """Load previously saved features"""
        filepath = self.features_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Feature file not found: {filepath}")
        
        features_df = pd.read_csv(filepath)
        print(f"✅ Features loaded from {filepath}: {len(features_df)} constituencies, {len(features_df.columns)} features")
        
        return features_df
    
    def create_advanced_swing_features(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Create advanced swing pattern features with regional correlation analysis"""
        print("🔄 Creating advanced swing pattern features...")
        
        # Start with basic swing patterns
        enhanced_df = self.calculate_swing_patterns(constituency_df)
        
        # Add regional swing correlation features
        enhanced_df = self._add_regional_swing_correlations(enhanced_df)
        
        # Add volatility pattern features
        enhanced_df = self._add_volatility_patterns(enhanced_df)
        
        # Add incumbent advantage modeling
        enhanced_df = self._add_incumbent_advantage_features(enhanced_df)
        
        # Add anti-incumbency indicators
        enhanced_df = self._add_anti_incumbency_features(enhanced_df)
        
        print(f"   Advanced swing features created: {len(enhanced_df.columns)} total features")
        return enhanced_df
    
    def _add_regional_swing_correlations(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add regional swing correlation and momentum features"""
        print("   Adding regional swing correlations...")
        
        # Group by region to calculate regional patterns
        regional_stats = {}
        
        for region in constituency_df['region'].unique():
            region_data = constituency_df[constituency_df['region'] == region]
            
            if len(region_data) > 1:
                # Calculate regional swing statistics
                regional_stats[region] = {
                    'avg_nda_swing': region_data['swing_nda_2015_2020'].mean(),
                    'avg_indi_swing': region_data['swing_indi_2015_2020'].mean(),
                    'swing_correlation': region_data['swing_nda_2015_2020'].corr(region_data['swing_indi_2015_2020']),
                    'volatility_std': region_data['volatility_2015_2020'].std(),
                    'swing_momentum': region_data['swing_nda_2015_2020'].mean() - region_data['swing_indi_2015_2020'].mean()
                }
            else:
                # Single constituency region - use constituency values
                regional_stats[region] = {
                    'avg_nda_swing': region_data['swing_nda_2015_2020'].iloc[0],
                    'avg_indi_swing': region_data['swing_indi_2015_2020'].iloc[0],
                    'swing_correlation': 0.0,
                    'volatility_std': 0.0,
                    'swing_momentum': 0.0
                }
        
        # Add regional features to each constituency
        for idx, row in constituency_df.iterrows():
            region = row['region']
            stats = regional_stats.get(region, {})
            
            constituency_df.loc[idx, 'regional_avg_nda_swing'] = stats.get('avg_nda_swing', 0)
            constituency_df.loc[idx, 'regional_avg_indi_swing'] = stats.get('avg_indi_swing', 0)
            constituency_df.loc[idx, 'regional_swing_correlation'] = stats.get('swing_correlation', 0)
            constituency_df.loc[idx, 'regional_volatility_std'] = stats.get('volatility_std', 0)
            constituency_df.loc[idx, 'regional_swing_momentum'] = stats.get('swing_momentum', 0)
            
            # Calculate deviation from regional average
            constituency_df.loc[idx, 'swing_deviation_from_region'] = abs(
                row['swing_nda_2015_2020'] - stats.get('avg_nda_swing', 0)
            )
        
        return constituency_df
    
    def _add_volatility_patterns(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility pattern analysis features"""
        print("   Adding volatility pattern features...")
        
        # Calculate volatility percentiles for classification
        volatility_values = constituency_df['volatility_2015_2020'].values
        volatility_25 = np.percentile(volatility_values, 25)
        volatility_75 = np.percentile(volatility_values, 75)
        
        # Classify constituencies by volatility
        def classify_volatility(vol):
            if vol <= volatility_25:
                return 'Low'
            elif vol >= volatility_75:
                return 'High'
            else:
                return 'Medium'
        
        constituency_df['volatility_category'] = constituency_df['volatility_2015_2020'].apply(classify_volatility)
        
        # Add volatility-based features
        constituency_df['volatility_percentile'] = constituency_df['volatility_2015_2020'].rank(pct=True)
        constituency_df['high_volatility_indicator'] = (constituency_df['volatility_2015_2020'] > volatility_75).astype(int)
        constituency_df['stable_constituency_indicator'] = (constituency_df['volatility_2015_2020'] < volatility_25).astype(int)
        
        # Calculate swing consistency (inverse of volatility)
        max_volatility = constituency_df['volatility_2015_2020'].max()
        constituency_df['swing_consistency'] = 1 - (constituency_df['volatility_2015_2020'] / max_volatility)
        
        return constituency_df
    
    def _add_incumbent_advantage_features(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add incumbent advantage modeling features"""
        print("   Adding incumbent advantage features...")
        
        # Load historical data to determine incumbency patterns
        results_2020 = self.load_historical_data('election_2020')
        results_2015 = self.load_historical_data('election_2015')
        
        if not results_2020.empty and not results_2015.empty:
            # Calculate incumbent advantage by party
            nda_incumbent_advantage = []
            indi_incumbent_advantage = []
            
            for _, row in constituency_df.iterrows():
                constituency = row['constituency']
                
                # Find historical data
                data_2020 = results_2020[results_2020['constituency'] == constituency]
                data_2015 = results_2015[results_2015['constituency'] == constituency]
                
                if not data_2020.empty and not data_2015.empty:
                    # Determine who was incumbent in 2020 (winner in 2015)
                    winner_2015 = 'NDA' if data_2015.iloc[0].get('nda_vote_share', 0) > data_2015.iloc[0].get('indi_vote_share', 0) else 'INDI'
                    
                    # Calculate advantage/disadvantage
                    if winner_2015 == 'NDA':
                        nda_advantage = data_2020.iloc[0].get('nda_vote_share', 0) - data_2015.iloc[0].get('nda_vote_share', 0)
                        nda_incumbent_advantage.append(nda_advantage)
                        indi_incumbent_advantage.append(-nda_advantage)  # Challenger disadvantage
                    else:
                        indi_advantage = data_2020.iloc[0].get('indi_vote_share', 0) - data_2015.iloc[0].get('indi_vote_share', 0)
                        indi_incumbent_advantage.append(indi_advantage)
                        nda_incumbent_advantage.append(-indi_advantage)  # Challenger disadvantage
                else:
                    nda_incumbent_advantage.append(0)
                    indi_incumbent_advantage.append(0)
            
            constituency_df['nda_incumbent_advantage'] = nda_incumbent_advantage
            constituency_df['indi_incumbent_advantage'] = indi_incumbent_advantage
            
            # Calculate overall incumbent advantage strength
            constituency_df['incumbent_advantage_strength'] = np.maximum(
                np.abs(constituency_df['nda_incumbent_advantage']),
                np.abs(constituency_df['indi_incumbent_advantage'])
            )
        else:
            # Default values when historical data is not available
            constituency_df['nda_incumbent_advantage'] = 0.0
            constituency_df['indi_incumbent_advantage'] = 0.0
            constituency_df['incumbent_advantage_strength'] = 0.0
        
        return constituency_df
    
    def _add_anti_incumbency_features(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add anti-incumbency effect indicators"""
        print("   Adding anti-incumbency features...")
        
        # Calculate anti-incumbency indicators based on swing patterns
        constituency_df['anti_incumbency_nda'] = np.where(
            constituency_df['nda_incumbent_advantage'] < -2.0,  # Lost more than 2% as incumbent
            1, 0
        )
        
        constituency_df['anti_incumbency_indi'] = np.where(
            constituency_df['indi_incumbent_advantage'] < -2.0,  # Lost more than 2% as incumbent
            1, 0
        )
        
        # Overall anti-incumbency strength
        constituency_df['anti_incumbency_strength'] = np.maximum(
            constituency_df['anti_incumbency_nda'] * abs(constituency_df['nda_incumbent_advantage']),
            constituency_df['anti_incumbency_indi'] * abs(constituency_df['indi_incumbent_advantage'])
        )
        
        # Swing reversal indicator (complete change in winner)
        constituency_df['swing_reversal'] = np.where(
            constituency_df['incumbent_retained'] == 0, 1, 0
        )
        
        # Calculate swing magnitude categories
        swing_magnitude = np.maximum(
            abs(constituency_df['swing_nda_2015_2020']),
            abs(constituency_df['swing_indi_2015_2020'])
        )
        
        swing_75 = np.percentile(swing_magnitude, 75)
        constituency_df['major_swing_indicator'] = (swing_magnitude > swing_75).astype(int)
        
        return constituency_df
    
    def add_demographic_features(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive demographic and caste-based features"""
        print("🔄 Adding demographic and caste-based features...")
        
        # Load demographic data
        demographics = self.load_historical_data('demographics')
        
        if demographics.empty:
            print("   Warning: Demographic data not available, using synthetic features")
            return self._add_synthetic_demographic_features(constituency_df)
        
        # Merge demographic data
        enhanced_df = constituency_df.merge(demographics, on='constituency', how='left')
        
        # Add caste-based voting pattern features
        enhanced_df = self._add_caste_voting_patterns(enhanced_df)
        
        # Add urban-rural divide features
        enhanced_df = self._add_urban_rural_features(enhanced_df)
        
        # Add socio-economic indicators
        enhanced_df = self._add_socioeconomic_features(enhanced_df)
        
        # Add religious composition features
        enhanced_df = self._add_religious_features(enhanced_df)
        
        print(f"   Demographic features added: {len(enhanced_df.columns)} total features")
        return enhanced_df
    
    def _add_caste_voting_patterns(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add caste composition impact on voting patterns"""
        print("   Adding caste-based voting pattern features...")
        
        # Define caste categories and their typical voting patterns (based on Bihar electoral history)
        caste_voting_patterns = {
            'upper_caste_percentage': {'nda_preference': 0.6, 'indi_preference': 0.4},
            'obc_percentage': {'nda_preference': 0.45, 'indi_preference': 0.55},
            'sc_percentage': {'nda_preference': 0.3, 'indi_preference': 0.7},
            'st_percentage': {'nda_preference': 0.4, 'indi_preference': 0.6},
            'muslim_percentage': {'nda_preference': 0.15, 'indi_preference': 0.85},
            'yadav_percentage': {'nda_preference': 0.2, 'indi_preference': 0.8}
        }
        
        # Calculate caste-based voting preference scores
        nda_caste_score = 0
        indi_caste_score = 0
        
        for caste_col, preferences in caste_voting_patterns.items():
            if caste_col in constituency_df.columns:
                caste_percentage = constituency_df[caste_col].fillna(0) / 100.0  # Convert to proportion
                nda_caste_score += caste_percentage * preferences['nda_preference']
                indi_caste_score += caste_percentage * preferences['indi_preference']
            else:
                # Use regional/state averages if specific data not available
                avg_percentage = self._get_average_caste_percentage(caste_col, constituency_df['region'])
                nda_caste_score += avg_percentage * preferences['nda_preference']
                indi_caste_score += avg_percentage * preferences['indi_preference']
        
        constituency_df['caste_based_nda_preference'] = nda_caste_score
        constituency_df['caste_based_indi_preference'] = indi_caste_score
        constituency_df['caste_preference_advantage_nda'] = nda_caste_score - indi_caste_score
        
        # Calculate caste diversity index (higher diversity = more competitive)
        caste_columns = [col for col in caste_voting_patterns.keys() if col in constituency_df.columns]
        if caste_columns:
            caste_values = constituency_df[caste_columns].fillna(0)
            # Calculate Herfindahl-Hirschman Index for caste diversity
            caste_proportions = caste_values.div(caste_values.sum(axis=1), axis=0).fillna(0)
            hhi = (caste_proportions ** 2).sum(axis=1)
            constituency_df['caste_diversity_index'] = 1 - hhi  # Higher value = more diverse
        else:
            constituency_df['caste_diversity_index'] = 0.5  # Moderate diversity default
        
        # Add dominant caste indicators
        if caste_columns:
            dominant_caste = constituency_df[caste_columns].idxmax(axis=1)
            constituency_df['dominant_caste'] = dominant_caste.str.replace('_percentage', '')
            
            # Create binary indicators for major castes
            for caste_col in caste_columns:
                caste_name = caste_col.replace('_percentage', '')
                constituency_df[f'dominant_{caste_name}'] = (dominant_caste == caste_col).astype(int)
        
        return constituency_df
    
    def _add_urban_rural_features(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add urban-rural divide effect features"""
        print("   Adding urban-rural divide features...")
        
        # Urban-rural voting patterns (based on Bihar electoral trends)
        urban_voting_pattern = {'nda_preference': 0.52, 'indi_preference': 0.48}
        rural_voting_pattern = {'nda_preference': 0.42, 'indi_preference': 0.58}
        
        # Calculate urban-rural preference scores
        if 'urban_percentage' in constituency_df.columns and 'rural_percentage' in constituency_df.columns:
            urban_prop = constituency_df['urban_percentage'].fillna(20) / 100.0  # Default 20% urban
            rural_prop = constituency_df['rural_percentage'].fillna(80) / 100.0  # Default 80% rural
        else:
            # Estimate based on constituency type or region
            urban_prop = self._estimate_urban_percentage(constituency_df)
            rural_prop = 1 - urban_prop
            constituency_df['urban_percentage'] = urban_prop * 100
            constituency_df['rural_percentage'] = rural_prop * 100
        
        # Calculate urban-rural voting preferences
        constituency_df['urban_nda_preference'] = urban_prop * urban_voting_pattern['nda_preference']
        constituency_df['urban_indi_preference'] = urban_prop * urban_voting_pattern['indi_preference']
        constituency_df['rural_nda_preference'] = rural_prop * rural_voting_pattern['nda_preference']
        constituency_df['rural_indi_preference'] = rural_prop * rural_voting_pattern['indi_preference']
        
        # Combined urban-rural preference
        constituency_df['urbanrural_nda_preference'] = (
            constituency_df['urban_nda_preference'] + constituency_df['rural_nda_preference']
        )
        constituency_df['urbanrural_indi_preference'] = (
            constituency_df['urban_indi_preference'] + constituency_df['rural_indi_preference']
        )
        
        # Urban-rural advantage
        constituency_df['urban_rural_advantage_nda'] = (
            constituency_df['urbanrural_nda_preference'] - constituency_df['urbanrural_indi_preference']
        )
        
        # Constituency type classification
        constituency_df['constituency_type'] = pd.cut(
            urban_prop * 100,
            bins=[0, 20, 50, 100],
            labels=['Rural', 'Semi-Urban', 'Urban']
        )
        
        return constituency_df
    
    def _add_socioeconomic_features(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add educational and economic indicators"""
        print("   Adding socio-economic features...")
        
        # Educational impact on voting (higher education tends to favor different parties)
        education_voting_impact = {
            'literacy_rate': {'nda_boost': 0.002, 'indi_boost': -0.001},  # Per percentage point
            'higher_education_rate': {'nda_boost': 0.003, 'indi_boost': -0.002}
        }
        
        # Economic indicators impact
        economic_voting_impact = {
            'employment_rate': {'nda_boost': 0.001, 'indi_boost': 0.001},  # Both benefit from employment
            'poverty_rate': {'nda_boost': -0.002, 'indi_boost': 0.003},  # Poverty favors opposition
            'development_index': {'nda_boost': 0.002, 'indi_boost': -0.001}  # Development favors incumbent
        }
        
        # Calculate education-based voting adjustments
        education_nda_adjustment = 0
        education_indi_adjustment = 0
        
        for edu_indicator, impact in education_voting_impact.items():
            if edu_indicator in constituency_df.columns:
                rate = constituency_df[edu_indicator].fillna(constituency_df[edu_indicator].mean())
                education_nda_adjustment += rate * impact['nda_boost']
                education_indi_adjustment += rate * impact['indi_boost']
            else:
                # Use regional/state averages
                avg_rate = self._get_average_education_rate(edu_indicator, constituency_df['region'])
                education_nda_adjustment += avg_rate * impact['nda_boost']
                education_indi_adjustment += avg_rate * impact['indi_boost']
        
        constituency_df['education_nda_adjustment'] = education_nda_adjustment
        constituency_df['education_indi_adjustment'] = education_indi_adjustment
        
        # Calculate economic-based voting adjustments
        economic_nda_adjustment = 0
        economic_indi_adjustment = 0
        
        for econ_indicator, impact in economic_voting_impact.items():
            if econ_indicator in constituency_df.columns:
                rate = constituency_df[econ_indicator].fillna(constituency_df[econ_indicator].mean())
                economic_nda_adjustment += rate * impact['nda_boost']
                economic_indi_adjustment += rate * impact['indi_boost']
            else:
                # Use regional/state averages
                avg_rate = self._get_average_economic_indicator(econ_indicator, constituency_df['region'])
                economic_nda_adjustment += avg_rate * impact['nda_boost']
                economic_indi_adjustment += avg_rate * impact['indi_boost']
        
        constituency_df['economic_nda_adjustment'] = economic_nda_adjustment
        constituency_df['economic_indi_adjustment'] = economic_indi_adjustment
        
        # Combined socio-economic advantage
        constituency_df['socioeconomic_nda_advantage'] = (
            education_nda_adjustment + economic_nda_adjustment - 
            education_indi_adjustment - economic_indi_adjustment
        )
        
        return constituency_df
    
    def _add_religious_features(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add religious composition features"""
        print("   Adding religious composition features...")
        
        # Religious voting patterns (based on Bihar electoral history)
        religious_voting_patterns = {
            'hindu_percentage': {'nda_preference': 0.48, 'indi_preference': 0.52},
            'muslim_percentage': {'nda_preference': 0.15, 'indi_preference': 0.85},
            'christian_percentage': {'nda_preference': 0.35, 'indi_preference': 0.65},
            'sikh_percentage': {'nda_preference': 0.45, 'indi_preference': 0.55},
            'other_religion_percentage': {'nda_preference': 0.4, 'indi_preference': 0.6}
        }
        
        # Calculate religious-based voting preference scores
        religious_nda_score = 0
        religious_indi_score = 0
        
        for religion_col, preferences in religious_voting_patterns.items():
            if religion_col in constituency_df.columns:
                religion_percentage = constituency_df[religion_col].fillna(0) / 100.0
                religious_nda_score += religion_percentage * preferences['nda_preference']
                religious_indi_score += religion_percentage * preferences['indi_preference']
            else:
                # Use state averages for missing data
                avg_percentage = self._get_average_religious_percentage(religion_col)
                religious_nda_score += avg_percentage * preferences['nda_preference']
                religious_indi_score += avg_percentage * preferences['indi_preference']
        
        constituency_df['religious_nda_preference'] = religious_nda_score
        constituency_df['religious_indi_preference'] = religious_indi_score
        constituency_df['religious_preference_advantage_nda'] = religious_nda_score - religious_indi_score
        
        # Calculate religious diversity index
        religion_columns = [col for col in religious_voting_patterns.keys() if col in constituency_df.columns]
        if religion_columns:
            religion_values = constituency_df[religion_columns].fillna(0)
            religion_proportions = religion_values.div(religion_values.sum(axis=1), axis=0).fillna(0)
            religious_hhi = (religion_proportions ** 2).sum(axis=1)
            constituency_df['religious_diversity_index'] = 1 - religious_hhi
        else:
            constituency_df['religious_diversity_index'] = 0.3  # Low diversity default for Bihar
        
        # Muslim concentration indicator (important for Bihar politics)
        if 'muslim_percentage' in constituency_df.columns:
            constituency_df['high_muslim_concentration'] = (constituency_df['muslim_percentage'] > 30).astype(int)
            constituency_df['muslim_decisive_factor'] = (constituency_df['muslim_percentage'] > 20).astype(int)
        else:
            constituency_df['high_muslim_concentration'] = 0
            constituency_df['muslim_decisive_factor'] = 0
        
        return constituency_df
    
    def _add_synthetic_demographic_features(self, constituency_df: pd.DataFrame) -> pd.DataFrame:
        """Add synthetic demographic features when real data is unavailable"""
        print("   Adding synthetic demographic features...")
        
        # Generate realistic synthetic features based on Bihar demographics
        np.random.seed(42)  # For reproducibility
        n_constituencies = len(constituency_df)
        
        # Caste composition (approximate Bihar averages)
        constituency_df['upper_caste_percentage'] = np.random.normal(15, 5, n_constituencies).clip(5, 30)
        constituency_df['obc_percentage'] = np.random.normal(45, 10, n_constituencies).clip(25, 65)
        constituency_df['sc_percentage'] = np.random.normal(16, 4, n_constituencies).clip(8, 25)
        constituency_df['st_percentage'] = np.random.normal(2, 1, n_constituencies).clip(0, 8)
        constituency_df['muslim_percentage'] = np.random.normal(17, 8, n_constituencies).clip(2, 40)
        constituency_df['yadav_percentage'] = np.random.normal(14, 6, n_constituencies).clip(5, 30)
        
        # Urban-rural split
        constituency_df['urban_percentage'] = np.random.normal(20, 10, n_constituencies).clip(5, 60)
        constituency_df['rural_percentage'] = 100 - constituency_df['urban_percentage']
        
        # Education indicators
        constituency_df['literacy_rate'] = np.random.normal(65, 10, n_constituencies).clip(40, 85)
        constituency_df['higher_education_rate'] = np.random.normal(12, 5, n_constituencies).clip(3, 25)
        
        # Economic indicators
        constituency_df['employment_rate'] = np.random.normal(45, 8, n_constituencies).clip(25, 65)
        constituency_df['poverty_rate'] = np.random.normal(35, 12, n_constituencies).clip(15, 60)
        constituency_df['development_index'] = np.random.normal(0.5, 0.15, n_constituencies).clip(0.2, 0.8)
        
        # Religious composition
        constituency_df['hindu_percentage'] = 100 - constituency_df['muslim_percentage'] - np.random.normal(2, 1, n_constituencies).clip(0, 5)
        constituency_df['christian_percentage'] = np.random.normal(1, 0.5, n_constituencies).clip(0, 3)
        constituency_df['other_religion_percentage'] = np.random.normal(1, 0.5, n_constituencies).clip(0, 3)
        
        return constituency_df
    
    def _get_average_caste_percentage(self, caste_col: str, regions: pd.Series) -> float:
        """Get average caste percentage for missing data"""
        # Bihar state averages (approximate)
        state_averages = {
            'upper_caste_percentage': 15,
            'obc_percentage': 45,
            'sc_percentage': 16,
            'st_percentage': 2,
            'muslim_percentage': 17,
            'yadav_percentage': 14
        }
        return state_averages.get(caste_col, 10) / 100.0
    
    def _estimate_urban_percentage(self, constituency_df: pd.DataFrame) -> pd.Series:
        """Estimate urban percentage based on constituency characteristics"""
        # Simple estimation based on region (can be improved with more data)
        region_urban_avg = {
            'Mithilanchal': 15,
            'Central': 25,
            'South': 20,
            'Border': 18
        }
        
        urban_estimates = []
        for _, row in constituency_df.iterrows():
            region = row.get('region', 'Central')
            base_urban = region_urban_avg.get(region, 20)
            # Add some random variation
            urban_est = np.random.normal(base_urban, 5)
            urban_estimates.append(max(5, min(60, urban_est)))
        
        return pd.Series(urban_estimates) / 100.0
    
    def _get_average_education_rate(self, indicator: str, regions: pd.Series) -> float:
        """Get average education rate for missing data"""
        state_averages = {
            'literacy_rate': 65,
            'higher_education_rate': 12
        }
        return state_averages.get(indicator, 50)
    
    def _get_average_economic_indicator(self, indicator: str, regions: pd.Series) -> float:
        """Get average economic indicator for missing data"""
        state_averages = {
            'employment_rate': 45,
            'poverty_rate': 35,
            'development_index': 0.5
        }
        return state_averages.get(indicator, 50)
    
    def _get_average_religious_percentage(self, religion_col: str) -> float:
        """Get average religious percentage for missing data"""
        state_averages = {
            'hindu_percentage': 82,
            'muslim_percentage': 17,
            'christian_percentage': 1,
            'sikh_percentage': 0.1,
            'other_religion_percentage': 0.9
        }
        return state_averages.get(religion_col, 1) / 100.0

    def get_feature_statistics(self, features_df: pd.DataFrame) -> Dict:
        """Generate comprehensive feature statistics"""
        numeric_features = features_df.select_dtypes(include=[np.number])
        
        statistics = {
            'summary': {
                'total_features': len(features_df.columns),
                'numeric_features': len(numeric_features.columns),
                'categorical_features': len(features_df.columns) - len(numeric_features.columns),
                'total_samples': len(features_df),
                'missing_values': features_df.isnull().sum().sum()
            },
            'numeric_stats': {},
            'missing_data': features_df.isnull().mean().to_dict(),
            'correlation_summary': {}
        }
        
        # Numeric feature statistics
        if not numeric_features.empty:
            statistics['numeric_stats'] = {
                'mean': numeric_features.mean().to_dict(),
                'std': numeric_features.std().to_dict(),
                'min': numeric_features.min().to_dict(),
                'max': numeric_features.max().to_dict(),
                'median': numeric_features.median().to_dict()
            }
            
            # Correlation summary
            if len(numeric_features.columns) > 1:
                corr_matrix = numeric_features.corr()
                statistics['correlation_summary'] = {
                    'max_correlation': corr_matrix.abs().max().max(),
                    'mean_correlation': corr_matrix.abs().mean().mean(),
                    'highly_correlated_pairs': len(corr_matrix[corr_matrix.abs() > 0.8]) - len(corr_matrix)
                }
        
        return statistics