import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import json
from bs4 import BeautifulSoup
import feedparser
import re
from src.config.settings import Config


class NewsIngestor:
    """Fetch daily news from multiple sources"""
    
    def __init__(self):
        self.api_key = Config.NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2/everything"
    
    def fetch_from_newsapi(self, days_back=1) -> pd.DataFrame:
        """Enhanced NewsAPI fetching with debugging and multiple strategies"""
        if not self.api_key:
            print("Warning: NewsAPI key not configured. Using fallback.")
            return self._generate_sample_news()
        
        print(f"🔍 Fetching Bihar news from NewsAPI (last {days_back} days)")
        print(f"🔑 API Key: {self.api_key[:10]}...")
        
        all_articles = []
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Strategy 1: Individual keyword searches
        print("\n📰 Strategy 1: Individual keyword searches")
        for i, keyword in enumerate(Config.BIHAR_KEYWORDS[:10]):  # Limit to avoid rate limits
            params = {
                'q': f'"{keyword}"',  # Use quotes for exact phrase matching
                'from': from_date,
                'language': 'en',
                'sortBy': 'relevancy',
                'apiKey': self.api_key,
                'pageSize': 15
            }
            
            try:
                print(f"  Searching for: {keyword}")
                response = requests.get(self.base_url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    print(f"    ✅ Found {len(articles)} articles")
                    all_articles.extend(articles)
                    
                elif response.status_code == 429:
                    print(f"    ⚠️ Rate limit hit for '{keyword}' - waiting...")
                    import time
                    time.sleep(2)
                else:
                    print(f"    ❌ API error for '{keyword}': {response.status_code}")
                    if response.status_code == 401:
                        print(f"    🔑 Invalid API key - check your NewsAPI configuration")
                    elif response.status_code == 426:
                        print(f"    💳 Upgrade required - using free tier limits")
                        
            except Exception as e:
                print(f"    ❌ Error fetching '{keyword}': {e}")
        
        # Strategy 2: Combined searches for better coverage
        print(f"\n📰 Strategy 2: Combined searches")
        combined_searches = [
            "Bihar AND election",
            "Bihar AND politics", 
            "Nitish Kumar OR Tejashwi Yadav",
            "RJD OR JDU OR BJP AND Bihar",
            "Patna AND politics"
        ]
        
        for search_query in combined_searches:
            params = {
                'q': search_query,
                'from': from_date,
                'language': 'en',
                'sortBy': 'relevancy',
                'apiKey': self.api_key,
                'pageSize': 20
            }
            
            try:
                print(f"  Combined search: {search_query}")
                response = requests.get(self.base_url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    print(f"    ✅ Found {len(articles)} articles")
                    all_articles.extend(articles)
                else:
                    print(f"    ❌ Error: {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        # Strategy 3: Source-specific searches
        print(f"\n📰 Strategy 3: Source-specific searches")
        indian_sources = [
            "the-times-of-india",
            "the-hindu", 
            "ndtv",
            "india-today",
            "hindustan-times"
        ]
        
        for source in indian_sources:
            params = {
                'q': 'Bihar',
                'sources': source,
                'from': from_date,
                'apiKey': self.api_key,
                'pageSize': 10
            }
            
            try:
                print(f"  Source search: {source}")
                response = requests.get(self.base_url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    print(f"    ✅ Found {len(articles)} articles")
                    all_articles.extend(articles)
                else:
                    print(f"    ❌ Error: {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        print(f"\n📊 Total articles collected: {len(all_articles)}")
        
        if not all_articles:
            print("❌ No articles found from NewsAPI - using sample data")
            return self._generate_sample_news()
        
        # Process and clean the articles
        df = pd.DataFrame(all_articles)
        df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')
        df['source_type'] = 'newsapi'
        
        # Clean and standardize
        required_columns = ['title', 'description', 'content', 'url', 'publishedAt', 'fetch_date', 'source_type']
        
        # Ensure all required columns exist
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        df = df[required_columns].drop_duplicates(subset=['title'])
        
        # Handle null values
        df['description'] = df['description'].fillna('')
        df['content'] = df['content'].fillna('')
        
        # Filter for Bihar relevance
        bihar_mask = df['title'].str.contains('Bihar|bihar|Nitish|Tejashwi|RJD|JDU|Patna', case=False, na=False)
        df_filtered = df[bihar_mask]
        
        print(f"✅ Filtered to {len(df_filtered)} Bihar-relevant articles")
        
        return df_filtered if not df_filtered.empty else df
    
    def scrape_local_news(self) -> pd.DataFrame:
        """Scrape local Bihar news websites with enhanced targeting"""
        articles = []
        
        # Enhanced Bihar news sources with specific election pages
        news_sources = {
            'Dainik Jagran': [
                'https://www.jagran.com/bihar/',
                'https://www.jagran.com/elections/',
                'https://www.jagran.com/bihar/patna-city.html'
            ],
            'Prabhat Khabar': [
                'https://www.prabhatkhabar.com/state/bihar',
                'https://www.prabhatkhabar.com/election'
            ],
            'Hindustan': [
                'https://www.livehindustan.com/bihar/',
                'https://www.livehindustan.com/election/'
            ],
            'Dainik Bhaskar': [
                'https://www.bhaskar.com/bihar/',
                'https://www.bhaskar.com/election/'
            ],
            'Aaj Tak': [
                'https://aajtak.intoday.in/bihar',
                'https://aajtak.intoday.in/election'
            ],
            'News18 Bihar': [
                'https://hindi.news18.com/bihar/',
                'https://hindi.news18.com/election/'
            ]
        }
        
        # Enhanced Bihar election keywords for filtering
        bihar_keywords = [
            'bihar', 'बिहार', 'election', 'चुनाव', 'nitish', 'नीतीश', 'tejashwi', 'तेजस्वी',
            'assembly', 'विधानसभा', 'rjd', 'jdu', 'bjp', 'congress', 'patna', 'पटना',
            'rally', 'रैली', 'campaign', 'प्रचार', 'candidate', 'उम्मीदवार', 'alliance', 'गठबंधन'
        ]
        
        for source_name, urls in news_sources.items():
            for url in urls:
                try:
                    print(f"Scraping {source_name} from {url}...")
                    response = requests.get(url, timeout=15, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    })
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Multiple selectors for different news site structures
                        article_selectors = [
                            'a[href*="bihar"]',
                            'a[href*="election"]',
                            'a[href*="politics"]',
                            '.news-item a',
                            '.article-title a',
                            '.headline a',
                            'h2 a',
                            'h3 a'
                        ]
                        
                        found_links = []
                        for selector in article_selectors:
                            found_links.extend(soup.select(selector))
                        
                        for link in found_links[:15]:  # Increased limit
                            href = link.get('href', '')
                            title = link.get_text(strip=True)
                            
                            # Enhanced filtering with both English and Hindi keywords
                            if title and len(title) > 15:
                                title_lower = title.lower()
                                if any(keyword.lower() in title_lower for keyword in bihar_keywords):
                                    # Build full URL
                                    if href.startswith('http'):
                                        full_url = href
                                    elif href.startswith('/'):
                                        base_url = '/'.join(url.split('/')[:3])
                                        full_url = base_url + href
                                    else:
                                        full_url = url.rstrip('/') + '/' + href
                                    
                                    articles.append({
                                        'title': title,
                                        'description': title,
                                        'content': self._fetch_article_content(full_url, source_name),
                                        'url': full_url,
                                        'publishedAt': datetime.now().isoformat(),
                                        'fetch_date': datetime.now().strftime('%Y-%m-%d'),
                                        'source_type': f'scraped_{source_name.lower().replace(" ", "_")}'
                                    })
                    
                    source_articles = [a for a in articles if source_name.lower().replace(" ", "_") in a['source_type']]
                    print(f"Found {len(source_articles)} articles from {source_name}")
                    
                except Exception as e:
                    print(f"Error scraping {source_name} from {url}: {e}")
                    continue
        
        if articles:
            df = pd.DataFrame(articles)
            # Remove duplicates based on title similarity
            df = df.drop_duplicates(subset=['title'], keep='first')
            print(f"Total unique scraped articles: {len(df)}")
            return df
        else:
            print("No articles scraped, will use sample data")
            return pd.DataFrame()
    
    def _fetch_article_content(self, url: str, source: str) -> str:
        """Fetch full article content from URL"""
        try:
            if not url.startswith('http'):
                return ""
            
            response = requests.get(url, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Common content selectors for news sites
                content_selectors = [
                    'div.story-content',
                    'div.article-content', 
                    'div.content',
                    'div.story-body',
                    'article',
                    'div.post-content'
                ]
                
                for selector in content_selectors:
                    content_div = soup.select_one(selector)
                    if content_div:
                        return content_div.get_text(strip=True)[:1000]  # Limit to 1000 chars
                
                # Fallback: get all paragraph text
                paragraphs = soup.find_all('p')
                if paragraphs:
                    return ' '.join([p.get_text(strip=True) for p in paragraphs[:3]])[:1000]
            
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
        
        return ""
    
    def fetch_from_rss_feeds(self) -> pd.DataFrame:
        """Fetch Bihar election news from RSS feeds"""
        articles = []
        
        # Bihar-focused RSS feeds
        rss_feeds = {
            'Times of India Bihar': 'https://timesofindia.indiatimes.com/rssfeeds/4118245.cms',
            'Hindustan Times Bihar': 'https://www.hindustantimes.com/feeds/rss/bihar/rssfeed.xml',
            'Indian Express Bihar': 'https://indianexpress.com/section/cities/patna/feed/',
            'NDTV Bihar': 'https://feeds.feedburner.com/ndtv/Tkri',
            'News18 Bihar': 'https://hindi.news18.com/rss/bihar.xml',
            'ABP News Bihar': 'https://www.abplive.com/states/bihar/feed',
            'Zee News Bihar': 'https://zeenews.india.com/bihar/rss.xml'
        }
        
        bihar_filter_keywords = [
            'bihar', 'बिहार', 'nitish', 'नीतीश', 'tejashwi', 'तेजस्वी', 'patna', 'पटना',
            'election', 'चुनाव', 'assembly', 'विधानसभा', 'rjd', 'jdu', 'bjp', 'congress'
        ]
        
        for source_name, rss_url in rss_feeds.items():
            try:
                print(f"Fetching RSS feed from {source_name}...")
                
                # Parse RSS feed
                feed = feedparser.parse(rss_url)
                
                if feed.entries:
                    for entry in feed.entries[:20]:  # Limit to 20 per feed
                        title = entry.get('title', '')
                        description = entry.get('description', '') or entry.get('summary', '')
                        link = entry.get('link', '')
                        published = entry.get('published', datetime.now().isoformat())
                        
                        # Filter for Bihar-related content
                        content_text = f"{title} {description}".lower()
                        if any(keyword.lower() in content_text for keyword in bihar_filter_keywords):
                            
                            # Clean HTML from description
                            if description:
                                description = BeautifulSoup(description, 'html.parser').get_text(strip=True)
                            
                            articles.append({
                                'title': title,
                                'description': description[:500],  # Limit description length
                                'content': description,
                                'url': link,
                                'publishedAt': published,
                                'fetch_date': datetime.now().strftime('%Y-%m-%d'),
                                'source_type': f'rss_{source_name.lower().replace(" ", "_")}'
                            })
                
                source_count = len([a for a in articles if source_name.lower().replace(" ", "_") in a['source_type']])
                print(f"Found {source_count} Bihar articles from {source_name} RSS")
                
            except Exception as e:
                print(f"Error fetching RSS from {source_name}: {e}")
                continue
        
        if articles:
            df = pd.DataFrame(articles)
            # Remove duplicates
            df = df.drop_duplicates(subset=['title'], keep='first')
            print(f"Total RSS articles: {len(df)}")
            return df
        else:
            print("No RSS articles found")
            return pd.DataFrame()
    
    def _generate_sample_news(self) -> pd.DataFrame:
        """Generate sample news for testing"""
        sample_articles = [
            {
                'title': 'NDA holds massive rally in Patna, promises development',
                'description': 'Nitish Kumar addresses crowd of thousands',
                'content': 'The NDA alliance held a major rally in Patna today with Chief Minister Nitish Kumar promising continued development...',
                'url': 'http://example.com/1',
                'publishedAt': datetime.now().isoformat(),
                'fetch_date': datetime.now().strftime('%Y-%m-%d'),
                'source_type': 'sample'
            },
            {
                'title': 'Tejashwi Yadav criticizes govt on unemployment in Darbhanga',
                'description': 'RJD leader campaigns in North Bihar',
                'content': 'RJD leader Tejashwi Yadav launched a scathing attack on the government over rising unemployment during his Darbhanga visit...',
                'url': 'http://example.com/2',
                'publishedAt': datetime.now().isoformat(),
                'fetch_date': datetime.now().strftime('%Y-%m-%d'),
                'source_type': 'sample'
            },
            {
                'title': 'Muslim voters express concerns over alliance stability in Kishanganj',
                'description': 'Ground report from border constituency',
                'content': 'In Kishanganj constituency, Muslim voters are divided over which alliance to support...',
                'url': 'http://example.com/3',
                'publishedAt': datetime.now().isoformat(),
                'fetch_date': datetime.now().strftime('%Y-%m-%d'),
                'source_type': 'sample'
            },
            {
                'title': 'BJP announces candidate list for 50 Bihar seats',
                'description': 'Party releases first phase of nominations',
                'content': 'The BJP today announced its candidate list for 50 constituencies in Bihar, signaling the start of serious campaign preparations...',
                'url': 'http://example.com/4',
                'publishedAt': (datetime.now() - timedelta(hours=2)).isoformat(),
                'fetch_date': datetime.now().strftime('%Y-%m-%d'),
                'source_type': 'sample'
            },
            {
                'title': 'Congress-RJD seat sharing talks continue in Patna',
                'description': 'INDI alliance finalizing constituency distribution',
                'content': 'Senior leaders from Congress and RJD continued their seat-sharing negotiations for the upcoming Bihar assembly elections...',
                'url': 'http://example.com/5',
                'publishedAt': (datetime.now() - timedelta(hours=4)).isoformat(),
                'fetch_date': datetime.now().strftime('%Y-%m-%d'),
                'source_type': 'sample'
            }
        ]
        
        return pd.DataFrame(sample_articles)
    
    def fetch_comprehensive_news(self, days_back=1) -> pd.DataFrame:
        """Comprehensive news fetching using all available methods"""
        print("🚀 COMPREHENSIVE BIHAR NEWS FETCHING")
        print("=" * 60)
        
        all_news_sources = []
        
        # Method 1: Enhanced NewsAPI
        print("\n1️⃣ Fetching from NewsAPI...")
        try:
            newsapi_df = self.fetch_from_newsapi(days_back)
            if not newsapi_df.empty:
                all_news_sources.append(newsapi_df)
                print(f"   ✅ NewsAPI: {len(newsapi_df)} articles")
            else:
                print(f"   ❌ NewsAPI: No articles")
        except Exception as e:
            print(f"   ❌ NewsAPI failed: {e}")
        
        # Method 2: RSS Feeds
        print("\n2️⃣ Fetching from RSS feeds...")
        try:
            rss_df = self.fetch_from_rss_feeds()
            if not rss_df.empty:
                all_news_sources.append(rss_df)
                print(f"   ✅ RSS Feeds: {len(rss_df)} articles")
            else:
                print(f"   ❌ RSS Feeds: No articles")
        except Exception as e:
            print(f"   ❌ RSS Feeds failed: {e}")
        
        # Method 3: Local News Scraping
        print("\n3️⃣ Scraping local news websites...")
        try:
            scraped_df = self.scrape_local_news()
            if not scraped_df.empty:
                all_news_sources.append(scraped_df)
                print(f"   ✅ Scraped News: {len(scraped_df)} articles")
            else:
                print(f"   ❌ Scraped News: No articles")
        except Exception as e:
            print(f"   ❌ Scraping failed: {e}")
        
        # Combine all sources
        if all_news_sources:
            combined_df = pd.concat(all_news_sources, ignore_index=True)
            
            # Remove duplicates across all sources
            combined_df = combined_df.drop_duplicates(subset=['title'], keep='first')
            
            # Sort by relevance (NewsAPI first, then RSS, then scraped)
            source_priority = {'newsapi': 1, 'rss': 2, 'scraped': 3}
            combined_df['priority'] = combined_df['source_type'].apply(
                lambda x: min([source_priority.get(key, 4) for key in source_priority.keys() if key in x])
            )
            combined_df = combined_df.sort_values('priority').drop('priority', axis=1)
            
            print(f"\n🎯 FINAL RESULTS:")
            print(f"   📊 Total unique articles: {len(combined_df)}")
            
            # Show breakdown by source
            source_counts = combined_df['source_type'].value_counts()
            for source, count in source_counts.items():
                print(f"   • {source}: {count} articles")
            
            return combined_df
        
        else:
            print(f"\n❌ All methods failed - using sample data")
            return self._generate_sample_news()
    
    def save_raw_news(self, df: pd.DataFrame, date_str: str = None):
        """Save raw news to JSON"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        output_path = Config.RAW_DATA_DIR / f"news_{date_str}.json"
        df.to_json(output_path, orient='records', indent=2)
        print(f"Saved {len(df)} articles to {output_path}")
    
    def validate_news_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean news data"""
        if df.empty:
            print("Warning: No news data to validate")
            return df
        
        # Remove articles with missing titles
        initial_count = len(df)
        df = df.dropna(subset=['title'])
        
        # Remove duplicate titles
        df = df.drop_duplicates(subset=['title'], keep='first')
        
        # Ensure required columns exist
        required_cols = ['title', 'description', 'content', 'url', 'publishedAt', 'fetch_date', 'source_type']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
        
        final_count = len(df)
        if final_count < initial_count:
            print(f"Cleaned news data: {initial_count} -> {final_count} articles")
        
        return df