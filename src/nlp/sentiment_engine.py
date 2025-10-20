import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from textblob import TextBlob
import re
from datetime import datetime

# Try to import transformers for better sentiment
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
    print("✅ Transformers library available for advanced sentiment analysis")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not available, using TextBlob fallback")


class SentimentEngine:
    """Advanced sentiment analysis engine for Bihar election news"""
    
    def __init__(self, model_name="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        self.model = None
        self.model_name = model_name
        self.political_keywords = self._load_political_keywords()
        
        # Initialize transformer model if available
        if TRANSFORMERS_AVAILABLE:
            try:
                print(f"🔄 Loading transformer model: {model_name}")
                self.model = pipeline(
                    "sentiment-analysis", 
                    model=model_name, 
                    max_length=512, 
                    truncation=True,
                    return_all_scores=True
                )
                print(f"✅ Loaded transformer model successfully")
            except Exception as e:
                print(f"⚠️ Could not load transformer model: {e}")
                print("🔄 Falling back to TextBlob")
                self.model = None
    
    def _load_political_keywords(self) -> Dict[str, List[str]]:
        """Load political keywords for context-aware sentiment analysis"""
        return {
            'positive_political': [
                'development', 'progress', 'growth', 'welfare', 'benefit', 'improvement',
                'success', 'achievement', 'victory', 'support', 'endorsement', 'approval',
                'popular', 'leading', 'ahead', 'winning', 'strong', 'confident'
            ],
            'negative_political': [
                'corruption', 'scandal', 'controversy', 'protest', 'opposition', 'criticism',
                'failure', 'decline', 'problem', 'issue', 'crisis', 'defeat', 'losing',
                'weak', 'unpopular', 'dissatisfaction', 'anger', 'frustration'
            ],
            'neutral_political': [
                'election', 'campaign', 'candidate', 'party', 'alliance', 'constituency',
                'voting', 'poll', 'survey', 'announcement', 'statement', 'meeting'
            ]
        }
    
    def analyze_text(self, text: str, context: str = None) -> Dict[str, float]:
        """Analyze sentiment of a single text with political context"""
        if not text or not isinstance(text, str):
            return {
                'sentiment_score': 0.0, 
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'political_context': 'none'
            }
        
        # Clean and prepare text
        cleaned_text = self._clean_text(text)
        
        # Get base sentiment
        base_sentiment = self._get_base_sentiment(cleaned_text)
        
        # Apply political context adjustment
        political_adjustment = self._analyze_political_context(cleaned_text)
        
        # Combine base sentiment with political context
        final_sentiment = self._combine_sentiments(base_sentiment, political_adjustment)
        
        return final_sentiment
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        # Limit length for processing
        return text[:512]
    
    def _get_base_sentiment(self, text: str) -> Dict[str, float]:
        """Get base sentiment using transformer or TextBlob"""
        if self.model is not None:
            try:
                # Use transformer model
                results = self.model(text)
                
                # Handle different output formats
                if isinstance(results, list) and len(results) > 0:
                    if isinstance(results[0], list):
                        # Multiple scores returned
                        scores = results[0]
                        sentiment_map = {}
                        for score in scores:
                            label = score['label'].lower()
                            if 'pos' in label:
                                sentiment_map['positive'] = score['score']
                            elif 'neg' in label:
                                sentiment_map['negative'] = score['score']
                            else:
                                sentiment_map['neutral'] = score['score']
                        
                        # Calculate final score (-1 to 1)
                        pos_score = sentiment_map.get('positive', 0)
                        neg_score = sentiment_map.get('negative', 0)
                        final_score = pos_score - neg_score
                        
                        # Determine label
                        if final_score > 0.1:
                            label = 'positive'
                        elif final_score < -0.1:
                            label = 'negative'
                        else:
                            label = 'neutral'
                        
                        return {
                            'sentiment_score': final_score,
                            'sentiment_label': label,
                            'confidence': max(pos_score, neg_score, sentiment_map.get('neutral', 0)),
                            'method': 'transformer'
                        }
                    else:
                        # Single result
                        result = results[0]
                        label_map = {
                            'POSITIVE': 1.0, 'positive': 1.0,
                            'NEGATIVE': -1.0, 'negative': -1.0,
                            'NEUTRAL': 0.0, 'neutral': 0.0
                        }
                        
                        score = label_map.get(result['label'], 0.0) * result['score']
                        
                        return {
                            'sentiment_score': score,
                            'sentiment_label': result['label'].lower(),
                            'confidence': result['score'],
                            'method': 'transformer'
                        }
                        
            except Exception as e:
                print(f"Transformer analysis failed: {e}, falling back to TextBlob")
        
        # Fallback to TextBlob
        return self._textblob_sentiment(text)
    
    def _textblob_sentiment(self, text: str) -> Dict[str, float]:
        """Get sentiment using TextBlob as fallback"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        # Determine label
        if polarity > 0.1:
            label = 'positive'
        elif polarity < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'sentiment_score': polarity,
            'sentiment_label': label,
            'confidence': abs(polarity) if abs(polarity) > 0.1 else subjectivity,
            'method': 'textblob'
        }
    
    def _analyze_political_context(self, text: str) -> Dict[str, float]:
        """Analyze political context and bias in the text"""
        text_lower = text.lower()
        
        # Count political keywords
        positive_count = sum(1 for word in self.political_keywords['positive_political'] 
                           if word in text_lower)
        negative_count = sum(1 for word in self.political_keywords['negative_political'] 
                           if word in text_lower)
        neutral_count = sum(1 for word in self.political_keywords['neutral_political'] 
                          if word in text_lower)
        
        total_political = positive_count + negative_count + neutral_count
        
        if total_political == 0:
            return {
                'political_sentiment': 0.0,
                'political_intensity': 0.0,
                'context': 'non_political'
            }
        
        # Calculate political sentiment bias
        political_sentiment = (positive_count - negative_count) / total_political
        political_intensity = total_political / len(text_lower.split())
        
        # Determine context
        if total_political > 3:
            context = 'highly_political'
        elif total_political > 1:
            context = 'political'
        else:
            context = 'mildly_political'
        
        return {
            'political_sentiment': political_sentiment,
            'political_intensity': political_intensity,
            'context': context
        }
    
    def _combine_sentiments(self, base_sentiment: Dict, political_context: Dict) -> Dict[str, float]:
        """Combine base sentiment with political context"""
        base_score = base_sentiment['sentiment_score']
        political_score = political_context.get('political_sentiment', 0.0)
        political_intensity = political_context.get('political_intensity', 0.0)
        
        # Weight political context based on intensity
        political_weight = min(political_intensity * 2, 0.3)  # Max 30% influence
        
        # Combine scores
        final_score = (base_score * (1 - political_weight)) + (political_score * political_weight)
        
        # Determine final label
        if final_score > 0.1:
            final_label = 'positive'
        elif final_score < -0.1:
            final_label = 'negative'
        else:
            final_label = 'neutral'
        
        return {
            'sentiment_score': final_score,
            'sentiment_label': final_label,
            'confidence': base_sentiment['confidence'],
            'political_context': political_context.get('context', 'none'),
            'political_intensity': political_intensity,
            'method': base_sentiment.get('method', 'unknown'),
            'base_sentiment': base_score,
            'political_adjustment': political_score * political_weight
        }
    
    def analyze_dataframe(self, df: pd.DataFrame, text_column='content') -> pd.DataFrame:
        """Analyze sentiment for all articles in dataframe"""
        if df.empty:
            print("⚠️ No data to analyze")
            return df
        
        print(f"🔄 Analyzing sentiment for {len(df)} articles...")
        
        # Combine title and content for better analysis
        df['full_text'] = (df.get('title', '').fillna('') + ' ' + 
                          df.get('description', '').fillna('') + ' ' + 
                          df.get(text_column, '').fillna(''))
        
        # Analyze each article
        results = []
        for i, text in enumerate(df['full_text']):
            if i % 10 == 0:
                print(f"   Processing article {i+1}/{len(df)}...")
            
            result = self.analyze_text(text)
            results.append(result)
        
        # Add results to dataframe
        df['sentiment_score'] = [r['sentiment_score'] for r in results]
        df['sentiment_label'] = [r['sentiment_label'] for r in results]
        df['sentiment_confidence'] = [r['confidence'] for r in results]
        df['political_context'] = [r['political_context'] for r in results]
        df['political_intensity'] = [r['political_intensity'] for r in results]
        df['analysis_method'] = [r['method'] for r in results]
        
        # Generate summary
        sentiment_dist = df['sentiment_label'].value_counts()
        context_dist = df['political_context'].value_counts()
        
        print(f"✅ Sentiment analysis complete!")
        print(f"📊 Sentiment distribution: {sentiment_dist.to_dict()}")
        print(f"🏛️ Political context: {context_dist.to_dict()}")
        print(f"📈 Average sentiment: {df['sentiment_score'].mean():.3f}")
        print(f"🎯 Average political intensity: {df['political_intensity'].mean():.3f}")
        
        return df
    
    def get_sentiment_summary(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive sentiment summary"""
        if df.empty or 'sentiment_score' not in df.columns:
            return {}
        
        summary = {
            'total_articles': len(df),
            'sentiment_distribution': df['sentiment_label'].value_counts().to_dict(),
            'average_sentiment': df['sentiment_score'].mean(),
            'sentiment_std': df['sentiment_score'].std(),
            'political_context_distribution': df['political_context'].value_counts().to_dict(),
            'average_political_intensity': df['political_intensity'].mean(),
            'method_distribution': df['analysis_method'].value_counts().to_dict(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Calculate sentiment trends by date if available
        if 'publishedAt' in df.columns:
            df['publish_date'] = pd.to_datetime(df['publishedAt']).dt.date
            daily_sentiment = df.groupby('publish_date')['sentiment_score'].mean()
            # Convert date keys to strings for JSON serialization
            summary['daily_sentiment_trend'] = {str(k): v for k, v in daily_sentiment.to_dict().items()}
        
        # Identify most positive and negative articles
        if len(df) > 0:
            most_positive = df.loc[df['sentiment_score'].idxmax()]
            most_negative = df.loc[df['sentiment_score'].idxmin()]
            
            summary['most_positive_article'] = {
                'title': most_positive.get('title', ''),
                'sentiment_score': most_positive['sentiment_score'],
                'url': most_positive.get('url', '')
            }
            
            summary['most_negative_article'] = {
                'title': most_negative.get('title', ''),
                'sentiment_score': most_negative['sentiment_score'],
                'url': most_negative.get('url', '')
            }
        
        return summary
    
    def analyze_entity_sentiment(self, df: pd.DataFrame, entity_column='party_mentioned') -> Dict:
        """Analyze sentiment by political entity/party"""
        if df.empty or 'sentiment_score' not in df.columns or entity_column not in df.columns:
            return {}
        
        entity_sentiment = {}
        
        for entity in df[entity_column].unique():
            if pd.isna(entity):
                continue
                
            entity_articles = df[df[entity_column] == entity]
            
            if len(entity_articles) > 0:
                entity_sentiment[entity] = {
                    'article_count': len(entity_articles),
                    'average_sentiment': entity_articles['sentiment_score'].mean(),
                    'sentiment_std': entity_articles['sentiment_score'].std(),
                    'positive_articles': len(entity_articles[entity_articles['sentiment_label'] == 'positive']),
                    'negative_articles': len(entity_articles[entity_articles['sentiment_label'] == 'negative']),
                    'neutral_articles': len(entity_articles[entity_articles['sentiment_label'] == 'neutral'])
                }
        
        return entity_sentiment