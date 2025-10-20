import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from src.config.settings import Config
import json


class FeatureUpdater:
    """Advanced feature engineering with EMA smoothing for Bihar election forecasting"""
    
    def __init__(self):
        self.ema_alpha = Config.EMA_ALPHA
        self.sentiment_weight = Config.SENTIMENT_WEIGHT
        self.news_decay_days = Config.NEWS_DECAY_DAYS
        
        print(f"✅ Feature updater initialized with EMA α={self.ema_alpha}, sentiment weight={self.sentiment_weight}")
    
    def load_base_features(self) -> pd.DataFrame:
        """Load latest feature state or create initial features"""
        feature_path = Config.PROCESSED_DATA_DIR / "features_latest.csv"
        
        if feature_path.exists():
            print(f"📊 Loading existing features from {feature_path}")
            return pd.read_csv(feature_path)
        else:
            print("🔄 Creating initial feature set...")
            return self._create_initial_features()
    
    def _create_initial_features(self) -> pd.DataFrame:
        """Create initial feature set for all constituencies"""
        constituencies = []
        
        # Create features for all 243 Bihar constituencies
        for i in range(1, Config.CONSTITUENCY_COUNT + 1):
            # Determine region based on constituency number (simplified)
            if i <= 60:
                region = 'Mithilanchal'
            elif i <= 120:
                region = 'Central Bihar'
            elif i <= 180:
                region = 'South Bihar'
            elif i <= 220:
                region = 'East Bihar'
            else:
                region = 'Border Areas'
            
            # Create realistic baseline features (based on 2020 Bihar election patterns)
            base_nda_share = np.random.normal(38.0, 8.0)  # NDA got ~38% vote share in 2020
            base_indi_share = np.random.normal(42.0, 8.0)  # INDI got ~42% vote share in 2020
            
            # Ensure shares are realistic
            base_nda_share = max(15, min(65, base_nda_share))
            base_indi_share = max(15, min(65, base_indi_share))
            
            constituency = {
                'constituency': f'AC_{i:03d}',
                'constituency_number': i,
                'region': region,
                
                # Historical baseline (2020 election)
                'nda_share_2020': base_nda_share,
                'indi_share_2020': base_indi_share,
                'others_share_2020': 100 - base_nda_share - base_indi_share,
                'nda_margin_2020': base_nda_share - base_indi_share,
                'turnout_2020': np.random.normal(58.0, 5.0),  # Average turnout ~58%
                
                # Current sentiment features (initialized to neutral)
                'social_sentiment_nda': 0.0,
                'social_sentiment_indi': 0.0,
                'news_sentiment_nda': 0.0,
                'news_sentiment_indi': 0.0,
                
                # Poll-based features
                'poll_lead_nda': base_nda_share - base_indi_share,
                'poll_momentum_nda': 0.0,
                'poll_volatility': 2.5,  # Standard poll volatility
                
                # Demographic features (simplified)
                'urban_percentage': np.random.uniform(20, 80),
                'rural_percentage': np.random.uniform(20, 80),
                'literacy_rate': np.random.uniform(50, 85),
                
                # Economic features
                'development_index': np.random.uniform(0.3, 0.8),
                'employment_rate': np.random.uniform(40, 70),
                
                # Social features
                'caste_diversity_index': np.random.uniform(0.4, 0.9),
                'religious_diversity_index': np.random.uniform(0.2, 0.8),
                
                # Campaign features
                'campaign_intensity_nda': 0.5,
                'campaign_intensity_indi': 0.5,
                'rally_count_nda': 0,
                'rally_count_indi': 0,
                
                # Metadata
                'last_updated': datetime.now().isoformat(),
                'update_count': 0
            }
            
            constituencies.append(constituency)
        
        df = pd.DataFrame(constituencies)
        
        # Add some realistic regional variations
        df = self._add_regional_variations(df)
        
        print(f"✅ Created initial features for {len(df)} constituencies")
        return df
    
    def _add_regional_variations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add realistic regional variations to features"""
        
        # Regional political preferences (based on historical patterns)
        regional_adjustments = {
            'Mithilanchal': {'nda_boost': -2, 'indi_boost': 3},  # INDI stronghold
            'Central Bihar': {'nda_boost': 1, 'indi_boost': -1},  # Competitive
            'South Bihar': {'nda_boost': 2, 'indi_boost': -2},   # NDA leaning
            'East Bihar': {'nda_boost': 0, 'indi_boost': 0},     # Balanced
            'Border Areas': {'nda_boost': -3, 'indi_boost': 4}   # INDI stronghold
        }
        
        for region, adjustments in regional_adjustments.items():
            region_mask = df['region'] == region
            
            df.loc[region_mask, 'nda_share_2020'] += adjustments['nda_boost']
            df.loc[region_mask, 'indi_share_2020'] += adjustments['indi_boost']
            df.loc[region_mask, 'nda_margin_2020'] = (
                df.loc[region_mask, 'nda_share_2020'] - df.loc[region_mask, 'indi_share_2020']
            )
            df.loc[region_mask, 'poll_lead_nda'] = df.loc[region_mask, 'nda_margin_2020']
        
        return df
    
    def aggregate_news_sentiment(self, news_df: pd.DataFrame) -> Dict[str, Dict]:
        """Aggregate sentiment from news data with temporal decay"""
        if news_df.empty:
            print("⚠️ No news data to aggregate")
            return {'party': {}, 'regional': {}, 'constituency': {}}
        
        print(f"🔄 Aggregating sentiment from {len(news_df)} news articles...")
        
        # Calculate temporal weights (exponential decay)
        # Handle timezone-aware datetime conversion with flexible parsing
        try:
            published_dates = pd.to_datetime(news_df['publishedAt'], format='mixed', utc=True)
        except:
            # Fallback: parse without timezone then localize
            published_dates = pd.to_datetime(news_df['publishedAt'], format='mixed')
            if published_dates.dt.tz is None:
                published_dates = published_dates.dt.tz_localize('UTC')
        
        current_time = pd.Timestamp.now(tz='UTC')
        news_df['days_old'] = (current_time - published_dates).dt.total_seconds() / (24 * 3600)
        news_df['temporal_weight'] = np.exp(-news_df['days_old'] / self.news_decay_days)
        
        # Calculate article weights (temporal * confidence)
        news_df['article_weight'] = (
            news_df['temporal_weight'] * 
            news_df.get('sentiment_confidence', 0.5) *
            news_df.get('political_intensity', 0.1)
        )
        
        aggregation = {
            'party': self._aggregate_party_sentiment(news_df),
            'regional': self._aggregate_regional_sentiment(news_df),
            'constituency': self._aggregate_constituency_sentiment(news_df)
        }
        
        return aggregation
    
    def _aggregate_party_sentiment(self, news_df: pd.DataFrame) -> Dict[str, float]:
        """Aggregate sentiment by party with weighted averaging"""
        party_sentiment = {}
        
        for party in ['NDA', 'INDI', 'Others']:
            party_articles = news_df[news_df['party_mentioned'] == party]
            
            if len(party_articles) > 0:
                # Weighted average sentiment
                weights = party_articles['article_weight']
                sentiments = party_articles['sentiment_score']
                
                if weights.sum() > 0:
                    weighted_sentiment = np.average(sentiments, weights=weights)
                    party_sentiment[party] = weighted_sentiment
                else:
                    party_sentiment[party] = sentiments.mean()
            else:
                party_sentiment[party] = 0.0
        
        print(f"   Party sentiment: NDA={party_sentiment['NDA']:.3f}, INDI={party_sentiment['INDI']:.3f}")
        return party_sentiment
    
    def _aggregate_regional_sentiment(self, news_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Aggregate sentiment by region and party"""
        regional_sentiment = {}
        
        for region in news_df['region'].unique():
            if pd.isna(region) or region == 'statewide':
                continue
                
            region_articles = news_df[news_df['region'] == region]
            regional_sentiment[region] = {}
            
            for party in ['NDA', 'INDI']:
                party_region_articles = region_articles[region_articles['party_mentioned'] == party]
                
                if len(party_region_articles) > 0:
                    weights = party_region_articles['article_weight']
                    sentiments = party_region_articles['sentiment_score']
                    
                    if weights.sum() > 0:
                        regional_sentiment[region][party] = np.average(sentiments, weights=weights)
                    else:
                        regional_sentiment[region][party] = sentiments.mean()
                else:
                    regional_sentiment[region][party] = 0.0
        
        return regional_sentiment
    
    def _aggregate_constituency_sentiment(self, news_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Aggregate sentiment by specific constituencies mentioned"""
        constituency_sentiment = {}
        
        # Process articles with specific constituency mentions
        specific_articles = news_df[news_df['constituency_type'] == 'specific']
        
        for _, article in specific_articles.iterrows():
            constituencies = article['constituencies']
            
            # Handle string representation of list
            if isinstance(constituencies, str):
                try:
                    constituencies = eval(constituencies)
                except:
                    constituencies = [constituencies]
            
            for constituency in constituencies:
                if constituency == 'statewide':
                    continue
                    
                if constituency not in constituency_sentiment:
                    constituency_sentiment[constituency] = {'NDA': [], 'INDI': []}
                
                party = article['party_mentioned']
                if party in ['NDA', 'INDI']:
                    sentiment_score = article['sentiment_score']
                    weight = article['article_weight']
                    
                    constituency_sentiment[constituency][party].append({
                        'sentiment': sentiment_score,
                        'weight': weight
                    })
        
        # Calculate weighted averages for each constituency
        final_constituency_sentiment = {}
        for constituency, party_data in constituency_sentiment.items():
            final_constituency_sentiment[constituency] = {}
            
            for party, sentiment_list in party_data.items():
                if sentiment_list:
                    sentiments = [item['sentiment'] for item in sentiment_list]
                    weights = [item['weight'] for item in sentiment_list]
                    
                    if sum(weights) > 0:
                        final_constituency_sentiment[constituency][party] = np.average(sentiments, weights=weights)
                    else:
                        final_constituency_sentiment[constituency][party] = np.mean(sentiments)
                else:
                    final_constituency_sentiment[constituency][party] = 0.0
        
        return final_constituency_sentiment
    
    def update_sentiment_features(self, base_df: pd.DataFrame, sentiment_agg: Dict) -> pd.DataFrame:
        """Apply sentiment updates to features using EMA smoothing"""
        df = base_df.copy()
        
        print(f"🔄 Updating sentiment features with EMA smoothing (α={self.ema_alpha})...")
        
        # Update statewide party sentiment
        party_sentiment = sentiment_agg['party']
        
        nda_sentiment_delta = party_sentiment.get('NDA', 0.0) * self.sentiment_weight
        indi_sentiment_delta = party_sentiment.get('INDI', 0.0) * self.sentiment_weight
        
        # Apply EMA smoothing to all constituencies
        df['news_sentiment_nda'] = (
            (1 - self.ema_alpha) * df['news_sentiment_nda'] + 
            self.ema_alpha * nda_sentiment_delta
        )
        
        df['news_sentiment_indi'] = (
            (1 - self.ema_alpha) * df['news_sentiment_indi'] + 
            self.ema_alpha * indi_sentiment_delta
        )
        
        # Apply regional sentiment modifiers
        regional_sentiment = sentiment_agg['regional']
        for region, party_sentiments in regional_sentiment.items():
            region_mask = df['region'] == region
            
            if region_mask.any():
                nda_regional_boost = party_sentiments.get('NDA', 0.0) * self.sentiment_weight * 0.5
                indi_regional_boost = party_sentiments.get('INDI', 0.0) * self.sentiment_weight * 0.5
                
                df.loc[region_mask, 'news_sentiment_nda'] += nda_regional_boost
                df.loc[region_mask, 'news_sentiment_indi'] += indi_regional_boost
        
        # Apply constituency-specific sentiment
        constituency_sentiment = sentiment_agg['constituency']
        for constituency, party_sentiments in constituency_sentiment.items():
            const_mask = df['constituency'] == constituency
            
            if const_mask.any():
                nda_const_boost = party_sentiments.get('NDA', 0.0) * self.sentiment_weight * 0.3
                indi_const_boost = party_sentiments.get('INDI', 0.0) * self.sentiment_weight * 0.3
                
                df.loc[const_mask, 'news_sentiment_nda'] += nda_const_boost
                df.loc[const_mask, 'news_sentiment_indi'] += indi_const_boost
        
        # Clip sentiment features to reasonable bounds
        df['news_sentiment_nda'] = df['news_sentiment_nda'].clip(-1, 1)
        df['news_sentiment_indi'] = df['news_sentiment_indi'].clip(-1, 1)
        
        # Update social sentiment (combination of news and other social signals)
        df['social_sentiment_nda'] = (
            0.7 * df['news_sentiment_nda'] + 
            0.3 * df['social_sentiment_nda']
        ).clip(-1, 1)
        
        df['social_sentiment_indi'] = (
            0.7 * df['news_sentiment_indi'] + 
            0.3 * df['social_sentiment_indi']
        ).clip(-1, 1)
        
        print(f"   Updated sentiment features for {len(df)} constituencies")
        return df
    
    def update_poll_features(self, base_df: pd.DataFrame, polls_df: pd.DataFrame) -> pd.DataFrame:
        """Update poll-based features from recent polls"""
        if polls_df.empty:
            print("⚠️ No poll data to process")
            return base_df
        
        df = base_df.copy()
        
        print(f"🔄 Updating poll features from {len(polls_df)} polls...")
        
        # Get recent polls (last 30 days) and calculate weighted average
        recent_polls = polls_df.sort_values('date', ascending=False).head(10)
        
        # Calculate weights based on sample size and recency
        recent_polls['days_old'] = (datetime.now() - pd.to_datetime(recent_polls['date'])).dt.days
        recent_polls['recency_weight'] = np.exp(-recent_polls['days_old'] / 14)  # 14-day half-life
        recent_polls['size_weight'] = np.sqrt(recent_polls['sample_size'])
        recent_polls['total_weight'] = recent_polls['recency_weight'] * recent_polls['size_weight']
        
        # Calculate weighted poll averages
        if recent_polls['total_weight'].sum() > 0:
            avg_nda = np.average(recent_polls['nda_vote'], weights=recent_polls['total_weight'])
            avg_indi = np.average(recent_polls['indi_vote'], weights=recent_polls['total_weight'])
            
            # Calculate swing from baseline
            baseline_nda = df['nda_share_2020'].mean()
            baseline_indi = df['indi_share_2020'].mean()
            
            nda_swing = avg_nda - baseline_nda
            indi_swing = avg_indi - baseline_indi
            
            print(f"   Poll swing: NDA {nda_swing:+.1f}%, INDI {indi_swing:+.1f}%")
            
            # Apply swing with EMA smoothing
            df['poll_lead_nda'] = (
                (1 - self.ema_alpha) * df['poll_lead_nda'] + 
                self.ema_alpha * (df['nda_margin_2020'] + nda_swing)
            )
            
            # Update poll momentum (change in recent polls)
            if len(recent_polls) >= 2:
                latest_nda = recent_polls.iloc[0]['nda_vote']
                earlier_nda = recent_polls.iloc[-1]['nda_vote']
                momentum = latest_nda - earlier_nda
                
                df['poll_momentum_nda'] = (
                    (1 - self.ema_alpha) * df['poll_momentum_nda'] + 
                    self.ema_alpha * momentum
                )
            
            # Update poll volatility
            if len(recent_polls) >= 3:
                nda_volatility = recent_polls['nda_vote'].std()
                df['poll_volatility'] = (
                    (1 - self.ema_alpha) * df['poll_volatility'] + 
                    self.ema_alpha * nda_volatility
                )
        
        return df
    
    def calculate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate derived features from base features"""
        print("🔄 Calculating derived features...")
        
        # Combined sentiment score
        df['combined_sentiment_nda'] = (
            0.6 * df['social_sentiment_nda'] + 
            0.4 * df['news_sentiment_nda']
        )
        
        df['combined_sentiment_indi'] = (
            0.6 * df['social_sentiment_indi'] + 
            0.4 * df['news_sentiment_indi']
        )
        
        # Sentiment advantage
        df['sentiment_advantage_nda'] = (
            df['combined_sentiment_nda'] - df['combined_sentiment_indi']
        )
        
        # Total advantage (polls + sentiment)
        df['total_advantage_nda'] = (
            0.7 * df['poll_lead_nda'] + 
            0.3 * df['sentiment_advantage_nda'] * 10  # Scale sentiment to poll points
        )
        
        # Competitiveness score (lower = more competitive)
        df['competitiveness'] = np.abs(df['total_advantage_nda'])
        
        # Volatility score (higher = more unpredictable)
        df['volatility_score'] = (
            df['poll_volatility'] + 
            np.abs(df['poll_momentum_nda']) + 
            np.abs(df['sentiment_advantage_nda'])
        )
        
        # Win probability (sigmoid transformation)
        df['nda_win_prob_raw'] = 1 / (1 + np.exp(-df['total_advantage_nda'] / 5))
        
        # Adjust for uncertainty
        uncertainty_factor = df['volatility_score'] / 10
        df['nda_win_prob'] = np.clip(
            df['nda_win_prob_raw'] + np.random.normal(0, uncertainty_factor, len(df)),
            0.01, 0.99
        )
        
        print(f"   Calculated derived features for {len(df)} constituencies")
        return df
    
    def save_updated_features(self, df: pd.DataFrame):
        """Save updated features with timestamp and backup"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
        
        # Update metadata
        df['last_updated'] = datetime.now().isoformat()
        df['update_count'] = df['update_count'] + 1
        
        # Save latest version
        latest_path = Config.PROCESSED_DATA_DIR / "features_latest.csv"
        df.to_csv(latest_path, index=False)
        
        # Save timestamped backup
        backup_path = Config.PROCESSED_DATA_DIR / f"features_{timestamp}.csv"
        df.to_csv(backup_path, index=False)
        
        print(f"✅ Updated features saved to {latest_path}")
        print(f"📁 Backup saved to {backup_path}")
    
    def get_feature_summary(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive feature summary"""
        summary = {
            'total_constituencies': len(df),
            'timestamp': datetime.now().isoformat(),
            
            # Sentiment statistics
            'sentiment_stats': {
                'avg_nda_sentiment': df['combined_sentiment_nda'].mean(),
                'avg_indi_sentiment': df['combined_sentiment_indi'].mean(),
                'sentiment_advantage_nda': df['sentiment_advantage_nda'].mean(),
                'sentiment_std': df['sentiment_advantage_nda'].std()
            },
            
            # Poll statistics
            'poll_stats': {
                'avg_nda_lead': df['poll_lead_nda'].mean(),
                'avg_momentum': df['poll_momentum_nda'].mean(),
                'avg_volatility': df['poll_volatility'].mean()
            },
            
            # Competitiveness analysis
            'competitiveness': {
                'safe_nda': len(df[df['nda_win_prob'] > 0.7]),
                'lean_nda': len(df[(df['nda_win_prob'] > 0.55) & (df['nda_win_prob'] <= 0.7)]),
                'toss_up': len(df[(df['nda_win_prob'] >= 0.45) & (df['nda_win_prob'] <= 0.55)]),
                'lean_indi': len(df[(df['nda_win_prob'] >= 0.3) & (df['nda_win_prob'] < 0.45)]),
                'safe_indi': len(df[df['nda_win_prob'] < 0.3])
            },
            
            # Regional breakdown
            'regional_stats': {}
        }
        
        # Regional analysis
        for region in df['region'].unique():
            region_df = df[df['region'] == region]
            summary['regional_stats'][region] = {
                'constituencies': len(region_df),
                'avg_nda_prob': region_df['nda_win_prob'].mean(),
                'avg_sentiment_advantage': region_df['sentiment_advantage_nda'].mean(),
                'competitive_seats': len(region_df[region_df['competitiveness'] < 5])
            }
        
        return summary