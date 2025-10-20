"""
Bihar Constituency Candidates and Historical Data
"""

import pandas as pd
from typing import Dict, List, Optional
from src.data.bihar_parties import get_party_info, get_party_alliance

# Load comprehensive constituency data
def load_all_constituencies():
    """Load all constituency data from generated file"""
    try:
        import json
        from pathlib import Path
        
        data_file = Path(__file__).parent / 'all_constituencies.json'
        if data_file.exists():
            with open(data_file, 'r') as f:
                return json.load(f)
        else:
            # Fallback to sample data
            return SAMPLE_CONSTITUENCY_CANDIDATES
    except Exception as e:
        print(f"Error loading constituency data: {e}")
        return SAMPLE_CONSTITUENCY_CANDIDATES

# Sample constituency candidate data (fallback)
SAMPLE_CONSTITUENCY_CANDIDATES = {
    'Patna Sahib': {
        'constituency_code': 'AC_163',
        'region': 'Central Bihar',
        'candidates': [
            {
                'name': 'Nand Kishore Yadav',
                'party': 'BJP',
                'age': 58,
                'education': 'Graduate',
                'assets': '₹2.5 Cr',
                'criminal_cases': 0,
                'experience': 'Former MLA'
            },
            {
                'name': 'Kunal Kumar',
                'party': 'RJD',
                'age': 45,
                'education': 'Post Graduate',
                'assets': '₹1.8 Cr',
                'criminal_cases': 1,
                'experience': 'First time'
            },
            {
                'name': 'Renu Kushwaha',
                'party': 'INC',
                'age': 52,
                'education': 'Graduate',
                'assets': '₹95 L',
                'criminal_cases': 0,
                'experience': 'Social Worker'
            }
        ],
        'historical_results': {
            '2020_assembly': {
                'winner': 'Nand Kishore Yadav',
                'party': 'BJP',
                'margin': 8542,
                'vote_share': 52.3,
                'turnout': 68.5
            },
            '2019_lok_sabha': {
                'winner': 'Ravi Shankar Prasad',
                'party': 'BJP',
                'margin': 285,
                'vote_share': 49.8,
                'turnout': 52.1
            },
            '2015_assembly': {
                'winner': 'Luv Sinha',
                'party': 'INC',
                'margin': 2021,
                'vote_share': 45.2,
                'turnout': 61.2
            }
        },
        'demographics': {
            'total_voters': 285432,
            'male_voters': 152341,
            'female_voters': 133091,
            'urban_percentage': 75.2,
            'literacy_rate': 78.5
        }
    },
    
    'Bankipore': {
        'constituency_code': 'AC_164',
        'region': 'Central Bihar',
        'candidates': [
            {
                'name': 'Nitin Nabin',
                'party': 'INC',
                'age': 41,
                'education': 'Post Graduate',
                'assets': '₹1.2 Cr',
                'criminal_cases': 0,
                'experience': 'Sitting MLA'
            },
            {
                'name': 'Visheshwar Ojha',
                'party': 'BJP',
                'age': 55,
                'education': 'Graduate',
                'assets': '₹3.1 Cr',
                'criminal_cases': 2,
                'experience': 'Former MLA'
            },
            {
                'name': 'Sandeep Saurav',
                'party': 'RJD',
                'age': 38,
                'education': 'Graduate',
                'assets': '₹75 L',
                'criminal_cases': 0,
                'experience': 'Youth Leader'
            }
        ],
        'historical_results': {
            '2020_assembly': {
                'winner': 'Nitin Nabin',
                'party': 'INC',
                'margin': 1274,
                'vote_share': 46.2,
                'turnout': 71.2
            },
            '2019_lok_sabha': {
                'winner': 'Shatrughan Sinha',
                'party': 'INC',
                'margin': 1203,
                'vote_share': 48.1,
                'turnout': 54.8
            },
            '2015_assembly': {
                'winner': 'Luv Sinha',
                'party': 'INC',
                'margin': 8956,
                'vote_share': 52.1,
                'turnout': 65.3
            }
        },
        'demographics': {
            'total_voters': 298765,
            'male_voters': 159432,
            'female_voters': 139333,
            'urban_percentage': 68.3,
            'literacy_rate': 75.2
        }
    },
    
    'Darbhanga Rural': {
        'constituency_code': 'AC_078',
        'region': 'Mithilanchal',
        'candidates': [
            {
                'name': 'Lalit Yadav',
                'party': 'RJD',
                'age': 48,
                'education': 'Graduate',
                'assets': '₹2.8 Cr',
                'criminal_cases': 3,
                'experience': 'Sitting MLA'
            },
            {
                'name': 'Rajesh Ranjan',
                'party': 'BJP',
                'age': 52,
                'education': 'Post Graduate',
                'assets': '₹1.9 Cr',
                'criminal_cases': 1,
                'experience': 'Former MP'
            },
            {
                'name': 'Sita Sahu',
                'party': 'JDU',
                'age': 45,
                'education': 'Graduate',
                'assets': '₹1.1 Cr',
                'criminal_cases': 0,
                'experience': 'Social Worker'
            }
        ],
        'historical_results': {
            '2020_assembly': {
                'winner': 'Lalit Yadav',
                'party': 'RJD',
                'margin': 12543,
                'vote_share': 49.2,
                'turnout': 74.2
            },
            '2019_lok_sabha': {
                'winner': 'Gopal Jee Thakur',
                'party': 'BJP',
                'margin': 8765,
                'vote_share': 51.3,
                'turnout': 58.7
            },
            '2015_assembly': {
                'winner': 'Lalit Yadav',
                'party': 'RJD',
                'margin': 15432,
                'vote_share': 52.8,
                'turnout': 69.1
            }
        },
        'demographics': {
            'total_voters': 312456,
            'male_voters': 165234,
            'female_voters': 147222,
            'urban_percentage': 25.3,
            'literacy_rate': 72.8
        }
    }
}

# Set the sample data as fallback
CONSTITUENCY_CANDIDATES = SAMPLE_CONSTITUENCY_CANDIDATES

class ConstituencyAnalyzer:
    """Analyze constituency-level candidate matchups and predictions"""
    
    def __init__(self):
        self.constituencies = load_all_constituencies()
        print(f"✅ Loaded {len(self.constituencies)} constituencies with candidate data")
    
    def get_constituency_details(self, constituency_name: str) -> Optional[Dict]:
        """Get detailed constituency information"""
        return self.constituencies.get(constituency_name)
    
    def get_candidate_matchup(self, constituency_name: str) -> Dict:
        """Get detailed candidate vs candidate analysis"""
        const_data = self.get_constituency_details(constituency_name)
        
        if not const_data:
            return {}
        
        candidates = const_data['candidates']
        historical = const_data['historical_results']
        
        # Create matchup analysis
        matchup = {
            'constituency': constituency_name,
            'constituency_code': const_data['constituency_code'],
            'region': const_data['region'],
            'total_candidates': len(candidates),
            'candidates': [],
            'battle_type': self._determine_battle_type(candidates),
            'key_contest': self._identify_key_contest(candidates, historical),
            'historical_context': self._get_historical_context(historical),
            'demographics': const_data['demographics']
        }
        
        # Analyze each candidate
        for candidate in candidates:
            party_info = get_party_info(candidate['party'])
            alliance = get_party_alliance(candidate['party'])
            
            candidate_analysis = {
                'name': candidate['name'],
                'party_code': candidate['party'],
                'party_name': party_info['full_name'],
                'alliance': alliance,
                'party_color': party_info['color'],
                'party_symbol': party_info['symbol'],
                'age': candidate['age'],
                'education': candidate['education'],
                'assets': candidate['assets'],
                'criminal_cases': candidate['criminal_cases'],
                'experience': candidate['experience'],
                'winning_chances': self._calculate_winning_chances(candidate, const_data),
                'strengths': self._identify_strengths(candidate, const_data),
                'challenges': self._identify_challenges(candidate, const_data)
            }
            
            matchup['candidates'].append(candidate_analysis)
        
        # Sort candidates by winning chances
        matchup['candidates'].sort(key=lambda x: x['winning_chances'], reverse=True)
        
        return matchup
    
    def _determine_battle_type(self, candidates: List[Dict]) -> str:
        """Determine the type of electoral battle"""
        parties = [c['party'] for c in candidates]
        
        has_bjp = 'BJP' in parties
        has_rjd = 'RJD' in parties
        has_inc = 'INC' in parties
        has_jdu = 'JDU' in parties
        
        if has_bjp and has_rjd:
            return "BJP vs RJD Battle"
        elif has_bjp and has_inc:
            return "BJP vs Congress Battle"
        elif has_jdu and has_rjd:
            return "JDU vs RJD Battle"
        elif len(candidates) >= 4:
            return "Multi-cornered Contest"
        else:
            return "Triangular Contest"
    
    def _identify_key_contest(self, candidates: List[Dict], historical: Dict) -> str:
        """Identify the key contest based on candidates and history"""
        # Get last winner's party
        last_winner_party = historical.get('2020_assembly', {}).get('party', 'Unknown')
        
        # Find current candidates from major parties
        major_candidates = []
        for candidate in candidates:
            if candidate['party'] in ['BJP', 'RJD', 'INC', 'JDU']:
                major_candidates.append(f"{candidate['name']} ({candidate['party']})")
        
        if len(major_candidates) >= 2:
            return f"{major_candidates[0]} vs {major_candidates[1]}"
        else:
            return "Open Contest"
    
    def _get_historical_context(self, historical: Dict) -> Dict:
        """Get historical election context"""
        context = {
            'last_winner': 'Unknown',
            'last_party': 'Unknown',
            'last_margin': 0,
            'trend': 'Stable',
            'swing_potential': 'Medium'
        }
        
        if '2020_assembly' in historical:
            last_result = historical['2020_assembly']
            context['last_winner'] = last_result.get('winner', 'Unknown')
            context['last_party'] = last_result.get('party', 'Unknown')
            context['last_margin'] = last_result.get('margin', 0)
            
            # Determine trend
            if last_result.get('margin', 0) > 10000:
                context['trend'] = 'Safe Seat'
                context['swing_potential'] = 'Low'
            elif last_result.get('margin', 0) < 5000:
                context['trend'] = 'Marginal Seat'
                context['swing_potential'] = 'High'
            else:
                context['trend'] = 'Competitive'
                context['swing_potential'] = 'Medium'
        
        return context
    
    def _calculate_winning_chances(self, candidate: Dict, const_data: Dict) -> float:
        """Calculate candidate's winning chances (simplified model)"""
        base_chance = 33.33  # Equal chance among 3 candidates
        
        # Adjust based on party strength
        party = candidate['party']
        if party in ['BJP', 'RJD']:
            base_chance += 15
        elif party in ['INC', 'JDU']:
            base_chance += 10
        elif party in ['CPI_ML', 'HAM']:
            base_chance += 5
        
        # Adjust based on experience
        if 'Sitting' in candidate.get('experience', ''):
            base_chance += 10
        elif 'Former' in candidate.get('experience', ''):
            base_chance += 5
        
        # Adjust based on criminal cases
        if candidate.get('criminal_cases', 0) > 2:
            base_chance -= 5
        
        # Adjust based on historical performance
        historical = const_data.get('historical_results', {})
        if '2020_assembly' in historical:
            last_winner_party = historical['2020_assembly'].get('party')
            if party == last_winner_party:
                base_chance += 8
        
        return min(max(base_chance, 5), 85)  # Keep between 5-85%
    
    def _identify_strengths(self, candidate: Dict, const_data: Dict) -> List[str]:
        """Identify candidate's key strengths"""
        strengths = []
        
        if 'Sitting' in candidate.get('experience', ''):
            strengths.append("Incumbent Advantage")
        
        if candidate.get('criminal_cases', 0) == 0:
            strengths.append("Clean Image")
        
        if candidate.get('age', 0) < 45:
            strengths.append("Youth Appeal")
        
        if 'Post Graduate' in candidate.get('education', ''):
            strengths.append("Well Educated")
        
        party = candidate['party']
        if party in ['BJP', 'RJD']:
            strengths.append("Strong Party Base")
        
        return strengths
    
    def _identify_challenges(self, candidate: Dict, const_data: Dict) -> List[str]:
        """Identify candidate's key challenges"""
        challenges = []
        
        if candidate.get('criminal_cases', 0) > 0:
            challenges.append(f"{candidate['criminal_cases']} Criminal Cases")
        
        if 'First time' in candidate.get('experience', ''):
            challenges.append("Lack of Experience")
        
        if candidate.get('age', 0) > 65:
            challenges.append("Age Factor")
        
        # Check if party lost last election
        historical = const_data.get('historical_results', {})
        if '2020_assembly' in historical:
            last_winner_party = historical['2020_assembly'].get('party')
            if candidate['party'] != last_winner_party:
                challenges.append("Anti-incumbency")
        
        return challenges
    
    def get_all_constituencies_summary(self) -> pd.DataFrame:
        """Get summary of all constituencies"""
        summary_data = []
        
        for const_name, const_data in self.constituencies.items():
            matchup = self.get_candidate_matchup(const_name)
            
            if matchup['candidates']:
                top_candidate = matchup['candidates'][0]
                runner_up = matchup['candidates'][1] if len(matchup['candidates']) > 1 else None
                
                summary_data.append({
                    'constituency': const_name,
                    'region': const_data['region'],
                    'battle_type': matchup['battle_type'],
                    'expected_winner': top_candidate['name'],
                    'winner_party': top_candidate['party_code'],
                    'winner_alliance': top_candidate['alliance'],
                    'winning_chance': f"{top_candidate['winning_chances']:.1f}%",
                    'runner_up': runner_up['name'] if runner_up else 'N/A',
                    'runner_up_party': runner_up['party_code'] if runner_up else 'N/A',
                    'contest_margin': 'Close' if top_candidate['winning_chances'] < 50 else 'Clear',
                    'last_winner': const_data['historical_results'].get('2020_assembly', {}).get('winner', 'Unknown'),
                    'last_party': const_data['historical_results'].get('2020_assembly', {}).get('party', 'Unknown'),
                    'total_voters': const_data['demographics']['total_voters']
                })
        
        return pd.DataFrame(summary_data)

# Initialize analyzer
constituency_analyzer = ConstituencyAnalyzer()