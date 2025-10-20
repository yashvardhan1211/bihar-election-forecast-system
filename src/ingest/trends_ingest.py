import pandas as pd
from datetime import datetime, timedelta
from typing import List
from src.config.settings import Config
import numpy as np

# Try to import pytrends, fall back to sample data if not available
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("Warning: pytrends not available. Using sample data.")


class TrendsIngestor:
    """Fetch Google Trends data for Bihar keywords"""
    
    def __init__(self):
        self.pytrends = None
        if PYTRENDS_AVAILABLE:
            try:
                self.pytrends = TrendReq(hl='en-IN', tz=330)
                print("Google Trends API initialized successfully")
            except Exception as e:
                print(f"Warning: Could not initialize pytrends: {e}")
                self.pytrends = None
    
    def fetch_keyword_trends(self, keywords: List[str] = None, timeframe='now 7-d') -> pd.DataFrame:
        """Fetch search trend data"""
        if keywords is None:
            keywords = ['Nitish Kumar', 'Tejashwi Yadav', 'Bihar election']
        
        if self.pytrends is None:
            return self._generate_sample_trends(keywords)
        
        try:
            # Build payload for Google Trends
            self.pytrends.build_payload(keywords, timeframe=timeframe, geo='IN-BR')
            
            # Get interest over time
            trends_df = self.pytrends.interest_over_time()
            
            if not trends_df.empty:
                # Remove the 'isPartial' column if it exists
                trends_df = trends_df.drop(columns=['isPartial'], errors='ignore')
                
                # Reset index to make date a column
                trends_df = trends_df.reset_index()
                
                # Add metadata
                trends_df['fetch_timestamp'] = datetime.now().isoformat()
                trends_df['timeframe'] = timeframe
                trends_df['geo'] = 'IN-BR'
                
                return trends_df
            else:
                print("No trends data returned from API")
                return self._generate_sample_trends(keywords)
                
        except Exception as e:
            print(f"Error fetching trends: {e}")
            return self._generate_sample_trends(keywords)
    
    def _generate_sample_trends(self, keywords: List[str] = None) -> pd.DataFrame:
        """Generate sample trend data for testing"""
        if keywords is None:
            keywords = ['Nitish Kumar', 'Tejashwi Yadav', 'Bihar election']
        
        # Generate 7 days of sample data
        dates = pd.date_range(end=datetime.now(), periods=7, freq='D')
        
        # Create realistic trend patterns
        data = {'date': dates}
        
        for keyword in keywords:
            if 'Nitish Kumar' in keyword:
                # Stable trend with slight decline
                base_values = [45, 48, 52, 50, 55, 53, 58]
            elif 'Tejashwi Yadav' in keyword:
                # Rising trend
                base_values = [60, 62, 65, 68, 70, 72, 75]
            elif 'Bihar election' in keyword:
                # Increasing interest
                base_values = [30, 35, 40, 42, 45, 48, 50]
            else:
                # Random pattern for other keywords
                base_values = np.random.randint(20, 80, 7).tolist()
            
            # Add some noise
            noise = np.random.normal(0, 3, 7)
            data[keyword] = [max(0, min(100, val + n)) for val, n in zip(base_values, noise)]
        
        df = pd.DataFrame(data)
        df['fetch_timestamp'] = datetime.now().isoformat()
        df['timeframe'] = 'sample_7d'
        df['geo'] = 'IN-BR'
        
        return df
    
    def fetch_related_queries(self, keyword: str) -> dict:
        """Fetch related queries for a keyword"""
        if self.pytrends is None:
            return self._generate_sample_related_queries(keyword)
        
        try:
            self.pytrends.build_payload([keyword], timeframe='now 7-d', geo='IN-BR')
            
            # Get related queries
            related_queries = self.pytrends.related_queries()
            
            if keyword in related_queries and related_queries[keyword]['top'] is not None:
                return {
                    'keyword': keyword,
                    'top_queries': related_queries[keyword]['top'].to_dict('records'),
                    'rising_queries': related_queries[keyword]['rising'].to_dict('records') if related_queries[keyword]['rising'] is not None else []
                }
            else:
                return self._generate_sample_related_queries(keyword)
                
        except Exception as e:
            print(f"Error fetching related queries for '{keyword}': {e}")
            return self._generate_sample_related_queries(keyword)
    
    def _generate_sample_related_queries(self, keyword: str) -> dict:
        """Generate sample related queries"""
        if 'Nitish Kumar' in keyword:
            top_queries = [
                {'query': 'nitish kumar news', 'value': 100},
                {'query': 'nitish kumar latest', 'value': 85},
                {'query': 'jdu nitish kumar', 'value': 70},
                {'query': 'bihar cm nitish kumar', 'value': 65}
            ]
            rising_queries = [
                {'query': 'nitish kumar rally', 'value': '+150%'},
                {'query': 'nitish kumar speech', 'value': '+120%'}
            ]
        elif 'Tejashwi Yadav' in keyword:
            top_queries = [
                {'query': 'tejashwi yadav news', 'value': 100},
                {'query': 'rjd tejashwi yadav', 'value': 90},
                {'query': 'tejashwi yadav latest', 'value': 75},
                {'query': 'tejashwi yadav rally', 'value': 60}
            ]
            rising_queries = [
                {'query': 'tejashwi yadav campaign', 'value': '+200%'},
                {'query': 'tejashwi yadav interview', 'value': '+180%'}
            ]
        else:
            top_queries = [
                {'query': f'{keyword} news', 'value': 100},
                {'query': f'{keyword} latest', 'value': 80},
                {'query': f'{keyword} update', 'value': 60}
            ]
            rising_queries = [
                {'query': f'{keyword} today', 'value': '+100%'}
            ]
        
        return {
            'keyword': keyword,
            'top_queries': top_queries,
            'rising_queries': rising_queries
        }
    
    def calculate_trend_momentum(self, df: pd.DataFrame, keyword: str) -> dict:
        """Calculate trend momentum and statistics"""
        if df.empty or keyword not in df.columns:
            return {}
        
        values = df[keyword].values
        dates = pd.to_datetime(df['date'])
        
        # Calculate basic statistics
        current_value = values[-1]
        avg_value = np.mean(values)
        max_value = np.max(values)
        min_value = np.min(values)
        
        # Calculate trend direction (linear regression slope)
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        # Calculate momentum (recent vs earlier periods)
        if len(values) >= 4:
            recent_avg = np.mean(values[-3:])  # Last 3 days
            earlier_avg = np.mean(values[:-3])  # Earlier days
            momentum = ((recent_avg - earlier_avg) / earlier_avg) * 100 if earlier_avg > 0 else 0
        else:
            momentum = 0
        
        # Determine trend direction
        if slope > 1:
            trend_direction = 'Rising'
        elif slope < -1:
            trend_direction = 'Falling'
        else:
            trend_direction = 'Stable'
        
        return {
            'keyword': keyword,
            'current_value': current_value,
            'average_value': avg_value,
            'max_value': max_value,
            'min_value': min_value,
            'trend_slope': slope,
            'trend_direction': trend_direction,
            'momentum_pct': momentum,
            'volatility': np.std(values),
            'date_range': f"{dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}"
        }
    
    def save_trends_data(self, df: pd.DataFrame, date_str: str = None):
        """Save trends data to CSV"""
        if df.empty:
            print("No trends data to save")
            return
        
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        output_path = Config.PROCESSED_DATA_DIR / f"trends_{date_str}.csv"
        df.to_csv(output_path, index=False)
        print(f"Saved trends data to {output_path}")
    
    def get_keyword_comparison(self, df: pd.DataFrame) -> dict:
        """Compare performance of different keywords"""
        if df.empty:
            return {}
        
        # Get numeric columns (keywords)
        keyword_cols = [col for col in df.columns if col not in ['date', 'fetch_timestamp', 'timeframe', 'geo']]
        
        if not keyword_cols:
            return {}
        
        comparison = {}
        for keyword in keyword_cols:
            values = df[keyword].values
            comparison[keyword] = {
                'average': np.mean(values),
                'peak': np.max(values),
                'current': values[-1] if len(values) > 0 else 0,
                'trend': 'up' if len(values) > 1 and values[-1] > values[0] else 'down'
            }
        
        # Find the most trending keyword
        most_trending = max(comparison.keys(), key=lambda k: comparison[k]['average'])
        
        return {
            'keyword_stats': comparison,
            'most_trending': most_trending,
            'comparison_date': datetime.now().strftime('%Y-%m-%d')
        }