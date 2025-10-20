import pandas as pd
import re
from typing import Dict, List, Tuple, Set
from src.config.settings import Config
import json
from datetime import datetime


class EntityMapper:
    """Advanced entity mapping for Bihar election news - maps to parties, regions, and constituencies"""
    
    def __init__(self):
        # Load comprehensive political entity mappings
        self.party_keywords = self._load_party_keywords()
        self.leader_keywords = self._load_leader_keywords()
        self.region_keywords = self._load_region_keywords()
        self.constituency_keywords = self._load_constituency_keywords()
        
        # Load constituency database
        self.constituencies = self._load_constituencies()
        
        print(f"✅ Entity mapper initialized with {len(self.constituencies)} constituencies")
    
    def _load_party_keywords(self) -> Dict[str, List[str]]:
        """Load comprehensive party and alliance keywords"""
        return {
            'NDA': [
                # Core NDA parties
                'NDA', 'BJP', 'JDU', 'JD(U)', 'Janata Dal United',
                'National Democratic Alliance', 'BJP-JDU', 'NDA alliance',
                
                # Leaders associated with NDA
                'Nitish Kumar', 'Narendra Modi', 'Amit Shah', 'Sushil Modi',
                'Ravi Shankar Prasad', 'Giriraj Singh', 'Ashwini Choubey',
                
                # NDA-friendly terms
                'ruling alliance', 'government alliance', 'coalition government',
                'Chief Minister Nitish', 'PM Modi', 'saffron party'
            ],
            
            'INDI': [
                # Core INDI/Opposition parties
                'INDI', 'RJD', 'Congress', 'Rashtriya Janata Dal', 'Indian National Congress',
                'Mahagathbandhan', 'Grand Alliance', 'opposition alliance',
                'INDIA bloc', 'INDIA alliance',
                
                # Leaders associated with INDI
                'Tejashwi Yadav', 'Lalu Prasad', 'Lalu Yadav', 'Rahul Gandhi',
                'Misa Bharti', 'Jagadanand Singh', 'Shivanand Tiwari',
                
                # Opposition terms
                'opposition parties', 'anti-BJP', 'secular alliance',
                'Lalu family', 'Yadav family'
            ],
            
            'Others': [
                # Other parties
                'AIMIM', 'BSP', 'CPI', 'CPI(M)', 'CPI(ML)', 'CPIM', 'CPIML',
                'Bahujan Samaj Party', 'All India Majlis-e-Ittehadul Muslimeen',
                'Communist Party', 'Left parties', 'Lok Janshakti Party', 'LJP',
                'Rashtriya Lok Morcha', 'RLM', 'Upendra Kushwaha',
                
                # Independent and smaller parties
                'independent', 'Independent candidate', 'smaller parties',
                'regional parties', 'local parties'
            ]
        }
    
    def _load_leader_keywords(self) -> Dict[str, str]:
        """Map leaders to their parties"""
        return {
            # NDA Leaders
            'Nitish Kumar': 'NDA', 'Narendra Modi': 'NDA', 'Amit Shah': 'NDA',
            'Sushil Modi': 'NDA', 'Ravi Shankar Prasad': 'NDA', 'Giriraj Singh': 'NDA',
            'Ashwini Choubey': 'NDA', 'Samrat Chaudhary': 'NDA',
            
            # INDI Leaders  
            'Tejashwi Yadav': 'INDI', 'Lalu Prasad': 'INDI', 'Lalu Yadav': 'INDI',
            'Rahul Gandhi': 'INDI', 'Misa Bharti': 'INDI', 'Jagadanand Singh': 'INDI',
            'Shivanand Tiwari': 'INDI', 'Manoj Jha': 'INDI',
            
            # Others
            'Upendra Kushwaha': 'Others', 'Asaduddin Owaisi': 'Others',
            'Mayawati': 'Others', 'Chirag Paswan': 'Others'
        }
    
    def _load_region_keywords(self) -> Dict[str, List[str]]:
        """Load Bihar regional keywords"""
        return {
            'Mithilanchal': [
                'Darbhanga', 'Madhubani', 'Samastipur', 'Muzaffarpur', 'Sitamarhi',
                'Sheohar', 'East Champaran', 'West Champaran', 'Gopalganj',
                'Mithila', 'North Bihar', 'Tirhut'
            ],
            
            'Central Bihar': [
                'Patna', 'Nalanda', 'Vaishali', 'Saran', 'Siwan', 'Bhojpur',
                'Buxar', 'Kaimur', 'Rohtas', 'Jehanabad', 'Arwal',
                'Central Bihar', 'Magadh'
            ],
            
            'South Bihar': [
                'Gaya', 'Aurangabad', 'Nawada', 'Jamui', 'Munger', 'Lakhisarai',
                'Sheikhpura', 'Begusarai', 'Khagaria', 'South Bihar', 'Magadh region'
            ],
            
            'East Bihar': [
                'Bhagalpur', 'Banka', 'Godda', 'Sahebganj', 'Pakur', 'Dumka',
                'East Bihar', 'Santhal Pargana'
            ],
            
            'Border Areas': [
                'Kishanganj', 'Araria', 'Katihar', 'Purnia', 'Madhepura', 'Supaul',
                'Saharsa', 'Border constituency', 'Nepal border', 'Bangladesh border',
                'Seemanchal'
            ]
        }
    
    def _load_constituency_keywords(self) -> Dict[str, List[str]]:
        """Load constituency-specific keywords"""
        # This would be expanded with all 243 constituencies
        return {
            'Patna Sahib': ['Patna Sahib', 'Patna city', 'capital constituency'],
            'Darbhanga': ['Darbhanga city', 'Darbhanga urban', 'Mithila capital'],
            'Muzaffarpur': ['Muzaffarpur city', 'Litchi city'],
            'Gaya': ['Gaya city', 'Bodh Gaya', 'Buddhist circuit'],
            'Bhagalpur': ['Bhagalpur city', 'Silk city'],
            'Kishanganj': ['Kishanganj', 'border seat', 'Muslim majority'],
            'Araria': ['Araria', 'Forbesganj', 'border area'],
            'Siwan': ['Siwan', 'Lalu stronghold', 'RJD bastion'],
            'Begusarai': ['Begusarai', 'industrial town'],
            'Madhubani': ['Madhubani', 'Mithila art', 'cultural center']
        }
    
    def _load_constituencies(self) -> List[Dict]:
        """Load comprehensive constituency database"""
        # In production, this would load from a database or CSV
        # For now, creating a representative sample
        constituencies = []
        
        # Sample constituencies with realistic data
        sample_constituencies = [
            {'name': 'Patna Sahib', 'number': 1, 'region': 'Central Bihar', 'type': 'Urban', 'reserved': 'General'},
            {'name': 'Darbhanga', 'number': 2, 'region': 'Mithilanchal', 'type': 'Urban', 'reserved': 'General'},
            {'name': 'Muzaffarpur', 'number': 3, 'region': 'Mithilanchal', 'type': 'Urban', 'reserved': 'General'},
            {'name': 'Gaya', 'number': 4, 'region': 'South Bihar', 'type': 'Urban', 'reserved': 'General'},
            {'name': 'Bhagalpur', 'number': 5, 'region': 'East Bihar', 'type': 'Urban', 'reserved': 'General'},
            {'name': 'Kishanganj', 'number': 6, 'region': 'Border Areas', 'type': 'Rural', 'reserved': 'General'},
            {'name': 'Araria', 'number': 7, 'region': 'Border Areas', 'type': 'Rural', 'reserved': 'General'},
            {'name': 'Siwan', 'number': 8, 'region': 'Central Bihar', 'type': 'Rural', 'reserved': 'General'},
            {'name': 'Begusarai', 'number': 9, 'region': 'South Bihar', 'type': 'Semi-Urban', 'reserved': 'General'},
            {'name': 'Madhubani', 'number': 10, 'region': 'Mithilanchal', 'type': 'Rural', 'reserved': 'General'}
        ]
        
        # Generate remaining constituencies
        for i in range(11, Config.CONSTITUENCY_COUNT + 1):
            region = ['Mithilanchal', 'Central Bihar', 'South Bihar', 'East Bihar', 'Border Areas'][i % 5]
            const_type = ['Urban', 'Rural', 'Semi-Urban'][i % 3]
            reserved = 'SC' if i % 7 == 0 else 'ST' if i % 11 == 0 else 'General'
            
            constituencies.append({
                'name': f'AC_{i:03d}',
                'number': i,
                'region': region,
                'type': const_type,
                'reserved': reserved
            })
        
        return sample_constituencies + constituencies
    
    def map_party(self, text: str) -> str:
        """Identify which party/alliance the article is about"""
        text_lower = text.lower()
        party_scores = {}
        
        # Score based on keyword matches
        for party, keywords in self.party_keywords.items():
            score = 0
            for keyword in keywords:
                # Exact matches get higher score
                if keyword.lower() in text_lower:
                    score += 2
                
                # Partial matches get lower score
                keyword_words = keyword.lower().split()
                if len(keyword_words) > 1:
                    if all(word in text_lower for word in keyword_words):
                        score += 1
            
            party_scores[party] = score
        
        # Check leader mentions
        for leader, party in self.leader_keywords.items():
            if leader.lower() in text_lower:
                party_scores[party] = party_scores.get(party, 0) + 3  # Leaders get high weight
        
        # Return party with highest score, or 'general' if no clear match
        if max(party_scores.values()) == 0:
            return 'general'
        
        return max(party_scores, key=party_scores.get)
    
    def map_region(self, text: str) -> str:
        """Identify which region the article is about"""
        text_lower = text.lower()
        region_scores = {}
        
        for region, keywords in self.region_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1
            region_scores[region] = score
        
        # Return region with highest score, or 'statewide' if no clear match
        if max(region_scores.values()) == 0:
            return 'statewide'
        
        return max(region_scores, key=region_scores.get)
    
    def map_constituencies(self, text: str) -> List[str]:
        """Identify specific constituencies mentioned"""
        text_lower = text.lower()
        mentioned_constituencies = []
        
        # Check for direct constituency mentions
        for const_name, keywords in self.constituency_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    mentioned_constituencies.append(const_name)
                    break
        
        # Check for constituency names in the full database
        for constituency in self.constituencies:
            const_name = constituency['name']
            if const_name.lower() in text_lower:
                mentioned_constituencies.append(const_name)
        
        # If specific constituencies found, return them
        if mentioned_constituencies:
            return list(set(mentioned_constituencies))  # Remove duplicates
        
        # Otherwise, map based on region
        region = self.map_region(text)
        if region != 'statewide':
            # Return constituencies from that region
            region_constituencies = [
                const['name'] for const in self.constituencies 
                if const['region'] == region
            ]
            return region_constituencies[:5]  # Limit to 5 for relevance
        
        return ['statewide']
    
    def extract_political_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract all political entities mentioned in text"""
        text_lower = text.lower()
        entities = {
            'leaders': [],
            'parties': [],
            'regions': [],
            'constituencies': []
        }
        
        # Extract leaders
        for leader in self.leader_keywords.keys():
            if leader.lower() in text_lower:
                entities['leaders'].append(leader)
        
        # Extract party mentions
        all_parties = []
        for party_list in self.party_keywords.values():
            all_parties.extend(party_list)
        
        for party in all_parties:
            if party.lower() in text_lower:
                entities['parties'].append(party)
        
        # Extract regions
        for region, keywords in self.region_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    entities['regions'].append(region)
                    break
        
        # Extract constituencies
        entities['constituencies'] = self.map_constituencies(text)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive entity mappings to news dataframe"""
        if df.empty:
            print("⚠️ No data to enrich")
            return df
        
        print(f"🔄 Mapping entities for {len(df)} articles...")
        
        # Combine title, description, and content for better context
        df['full_text'] = (
            df.get('title', '').fillna('') + ' ' + 
            df.get('description', '').fillna('') + ' ' + 
            df.get('content', '').fillna('')
        ).str[:2000]  # Limit length for processing
        
        # Apply entity mapping
        print("   Mapping parties...")
        df['party_mentioned'] = df['full_text'].apply(self.map_party)
        
        print("   Mapping regions...")
        df['region'] = df['full_text'].apply(self.map_region)
        
        print("   Mapping constituencies...")
        df['constituencies'] = df['full_text'].apply(self.map_constituencies)
        
        print("   Extracting political entities...")
        entity_results = df['full_text'].apply(self.extract_political_entities)
        
        df['leaders_mentioned'] = entity_results.apply(lambda x: x['leaders'])
        df['parties_mentioned'] = entity_results.apply(lambda x: x['parties'])
        df['regions_mentioned'] = entity_results.apply(lambda x: x['regions'])
        
        # Add constituency count and type
        df['constituency_count'] = df['constituencies'].apply(len)
        df['constituency_type'] = df['constituencies'].apply(
            lambda x: 'specific' if len(x) <= 5 and 'statewide' not in x else 'regional' if len(x) > 5 else 'statewide'
        )
        
        # Generate summary statistics
        party_dist = df['party_mentioned'].value_counts()
        region_dist = df['region'].value_counts()
        
        print(f"✅ Entity mapping complete!")
        print(f"📊 Party distribution: {party_dist.to_dict()}")
        print(f"🗺️ Region distribution: {region_dist.to_dict()}")
        
        # Count articles with specific constituency mentions
        specific_const = len(df[df['constituency_type'] == 'specific'])
        print(f"🎯 Articles with specific constituencies: {specific_const}")
        
        return df
    
    def get_entity_summary(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive entity mapping summary"""
        if df.empty or 'party_mentioned' not in df.columns:
            return {}
        
        summary = {
            'total_articles': len(df),
            'party_distribution': df['party_mentioned'].value_counts().to_dict(),
            'region_distribution': df['region'].value_counts().to_dict(),
            'constituency_type_distribution': df['constituency_type'].value_counts().to_dict(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Most mentioned leaders
        all_leaders = []
        for leaders_list in df['leaders_mentioned']:
            all_leaders.extend(leaders_list)
        
        if all_leaders:
            leader_counts = pd.Series(all_leaders).value_counts()
            summary['top_leaders'] = leader_counts.head(10).to_dict()
        
        # Most mentioned constituencies
        all_constituencies = []
        for const_list in df['constituencies']:
            if 'statewide' not in const_list:
                all_constituencies.extend(const_list)
        
        if all_constituencies:
            const_counts = pd.Series(all_constituencies).value_counts()
            summary['top_constituencies'] = const_counts.head(10).to_dict()
        
        # Articles by party and sentiment (if available)
        if 'sentiment_label' in df.columns:
            party_sentiment = df.groupby(['party_mentioned', 'sentiment_label']).size().unstack(fill_value=0)
            summary['party_sentiment_matrix'] = party_sentiment.to_dict()
        
        return summary
    
    def analyze_party_coverage(self, df: pd.DataFrame) -> Dict:
        """Analyze coverage patterns by party"""
        if df.empty or 'party_mentioned' not in df.columns:
            return {}
        
        party_analysis = {}
        
        for party in df['party_mentioned'].unique():
            if party == 'general':
                continue
                
            party_articles = df[df['party_mentioned'] == party]
            
            analysis = {
                'article_count': len(party_articles),
                'percentage_of_coverage': (len(party_articles) / len(df)) * 100,
                'regions_covered': party_articles['region'].value_counts().to_dict(),
                'constituency_focus': party_articles['constituency_type'].value_counts().to_dict()
            }
            
            # Add sentiment analysis if available
            if 'sentiment_score' in party_articles.columns:
                analysis['average_sentiment'] = party_articles['sentiment_score'].mean()
                analysis['sentiment_distribution'] = party_articles['sentiment_label'].value_counts().to_dict()
            
            # Most mentioned leaders for this party
            party_leaders = []
            for leaders_list in party_articles['leaders_mentioned']:
                party_leaders.extend(leaders_list)
            
            if party_leaders:
                leader_counts = pd.Series(party_leaders).value_counts()
                analysis['top_leaders'] = leader_counts.head(5).to_dict()
            
            party_analysis[party] = analysis
        
        return party_analysis