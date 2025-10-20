import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Dict, List
from src.config.settings import Config
import json
import re


class ECIIngestor:
    """Fetch real-time data from Election Commission of India"""
    
    def __init__(self):
        self.base_url = "https://results.eci.gov.in"
        self.bihar_code = "S04"  # Bihar state code in ECI system
        
    def fetch_live_results(self) -> pd.DataFrame:
        """Fetch live election results from ECI"""
        try:
            # ECI live results URL for Bihar
            results_url = f"{self.base_url}/AcGenMar2022/constituencywise-{self.bihar_code}.htm"
            
            response = requests.get(results_url, timeout=15)
            if response.status_code == 200:
                return self._parse_eci_results(response.content)
            else:
                print(f"ECI results not available (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"Error fetching ECI live results: {e}")
        
        return pd.DataFrame()
    
    def fetch_constituency_details(self) -> pd.DataFrame:
        """Fetch detailed constituency information"""
        try:
            # ECI constituency details
            const_url = f"{self.base_url}/AcGenMar2022/partywiseresult-{self.bihar_code}.htm"
            
            response = requests.get(const_url, timeout=15)
            if response.status_code == 200:
                return self._parse_constituency_data(response.content)
                
        except Exception as e:
            print(f"Error fetching constituency details: {e}")
        
        return pd.DataFrame()
    
    def fetch_candidate_list(self) -> pd.DataFrame:
        """Fetch candidate list for all constituencies"""
        try:
            # This would fetch from ECI's candidate database
            # ECI provides candidate lists in PDF/Excel format
            candidates_url = f"{self.base_url}/Candidate_List/Candidate_List_{self.bihar_code}.pdf"
            
            # For now, we'll scrape from the main results page
            # In production, you'd parse the PDF or Excel files
            
            return self._fetch_candidates_from_results()
            
        except Exception as e:
            print(f"Error fetching candidate list: {e}")
        
        return pd.DataFrame()
    
    def _parse_eci_results(self, html_content) -> pd.DataFrame:
        """Parse ECI HTML results into structured data"""
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        
        # Find result tables
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 6:  # Ensure we have enough columns
                    try:
                        constituency = cells[0].get_text(strip=True)
                        candidate = cells[1].get_text(strip=True)
                        party = cells[2].get_text(strip=True)
                        votes = cells[3].get_text(strip=True)
                        margin = cells[4].get_text(strip=True)
                        status = cells[5].get_text(strip=True)
                        
                        # Clean and validate data
                        if constituency and candidate:
                            results.append({
                                'constituency': constituency,
                                'candidate_name': candidate,
                                'party': party,
                                'votes_received': self._parse_number(votes),
                                'margin': self._parse_number(margin),
                                'status': status,
                                'fetch_timestamp': datetime.now().isoformat(),
                                'source': 'ECI_live'
                            })
                    except Exception as e:
                        continue  # Skip malformed rows
        
        if results:
            df = pd.DataFrame(results)
            print(f"Parsed {len(df)} constituency results from ECI")
            return df
        
        return pd.DataFrame()
    
    def _parse_constituency_data(self, html_content) -> pd.DataFrame:
        """Parse constituency-wise party performance"""
        soup = BeautifulSoup(html_content, 'html.parser')
        party_data = []
        
        # Look for party-wise result tables
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 4:
                    try:
                        party = cells[0].get_text(strip=True)
                        seats_won = cells[1].get_text(strip=True)
                        seats_leading = cells[2].get_text(strip=True)
                        total_seats = cells[3].get_text(strip=True)
                        
                        if party and any(char.isdigit() for char in seats_won):
                            party_data.append({
                                'party': party,
                                'seats_won': self._parse_number(seats_won),
                                'seats_leading': self._parse_number(seats_leading),
                                'total_seats': self._parse_number(total_seats),
                                'fetch_timestamp': datetime.now().isoformat()
                            })
                    except:
                        continue
        
        if party_data:
            df = pd.DataFrame(party_data)
            print(f"Parsed party data for {len(df)} parties from ECI")
            return df
        
        return pd.DataFrame()
    
    def _fetch_candidates_from_results(self) -> pd.DataFrame:
        """Extract candidate information from results pages"""
        try:
            # Fetch from multiple constituency pages
            candidates = []
            
            # Bihar has 243 constituencies
            for const_num in range(1, 244):
                const_url = f"{self.base_url}/AcGenMar2022/candidateswise-{self.bihar_code}{const_num:03d}.htm"
                
                try:
                    response = requests.get(const_url, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Parse candidate table
                        table = soup.find('table')
                        if table:
                            rows = table.find_all('tr')[1:]  # Skip header
                            
                            for row in rows:
                                cells = row.find_all('td')
                                if len(cells) >= 4:
                                    candidates.append({
                                        'constituency_number': const_num,
                                        'candidate_name': cells[0].get_text(strip=True),
                                        'party': cells[1].get_text(strip=True),
                                        'votes': self._parse_number(cells[2].get_text(strip=True)),
                                        'vote_percentage': cells[3].get_text(strip=True)
                                    })
                
                except:
                    continue  # Skip failed constituencies
                
                # Limit to first 10 constituencies for testing
                if const_num >= 10:
                    break
            
            if candidates:
                df = pd.DataFrame(candidates)
                print(f"Fetched candidate data for {len(df)} candidates")
                return df
                
        except Exception as e:
            print(f"Error fetching candidate data: {e}")
        
        return pd.DataFrame()
    
    def _parse_number(self, text: str) -> int:
        """Extract number from text string"""
        if not text:
            return 0
        
        # Remove commas and extract digits
        numbers = re.findall(r'\d+', text.replace(',', ''))
        if numbers:
            return int(numbers[0])
        return 0
    
    def get_real_time_trends(self) -> Dict:
        """Get real-time election trends"""
        try:
            # Fetch current results
            results_df = self.fetch_live_results()
            party_df = self.fetch_constituency_details()
            
            if results_df.empty and party_df.empty:
                return {}
            
            trends = {
                'timestamp': datetime.now().isoformat(),
                'total_constituencies': Config.CONSTITUENCY_COUNT,
                'results_declared': len(results_df) if not results_df.empty else 0,
                'party_performance': {},
                'leading_alliance': None,
                'swing_constituencies': []
            }
            
            # Calculate party performance
            if not party_df.empty:
                for _, row in party_df.iterrows():
                    party = row['party']
                    trends['party_performance'][party] = {
                        'seats_won': row.get('seats_won', 0),
                        'seats_leading': row.get('seats_leading', 0),
                        'total': row.get('seats_won', 0) + row.get('seats_leading', 0)
                    }
                
                # Determine leading alliance
                nda_seats = sum([data['total'] for party, data in trends['party_performance'].items() 
                               if party in ['BJP', 'JDU', 'NDA']])
                indi_seats = sum([data['total'] for party, data in trends['party_performance'].items() 
                                if party in ['RJD', 'Congress', 'INDI']])
                
                if nda_seats > indi_seats:
                    trends['leading_alliance'] = 'NDA'
                elif indi_seats > nda_seats:
                    trends['leading_alliance'] = 'INDI'
                else:
                    trends['leading_alliance'] = 'Tied'
            
            return trends
            
        except Exception as e:
            print(f"Error calculating real-time trends: {e}")
            return {}
    
    def save_eci_data(self, data_type: str, df: pd.DataFrame):
        """Save ECI data to files"""
        if df.empty:
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
        filename = f"eci_{data_type}_{timestamp}.csv"
        filepath = Config.RAW_DATA_DIR / filename
        
        df.to_csv(filepath, index=False)
        print(f"Saved ECI {data_type} data to {filepath}")