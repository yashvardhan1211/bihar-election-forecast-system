"""
Generate comprehensive candidate data for all 243 Bihar constituencies
"""

import pandas as pd
import random
from typing import Dict, List
# from src.data.bihar_parties import BIHAR_PARTIES, NDA_PARTIES, INDI_PARTIES, OTHER_PARTIES

# Bihar constituency names and regions
BIHAR_CONSTITUENCIES = {
    # Mithilanchal Region (60 seats)
    'Mithilanchal': [
        'Valmiki Nagar', 'Raxaul', 'Sugauli', 'Narkatia', 'Bagaha', 'Lauriya', 'Narkatiaganj',
        'Sikta', 'Bettiah', 'Chanpatia', 'Majhaulia', 'Gaunaha', 'Bagaha', 'Madhubani',
        'Phulparas', 'Benipatti', 'Khajauli', 'Babubarhi', 'Madhwapur', 'Laukaha',
        'Jhanjharpur', 'Sakri', 'Mahishi', 'Kurhani', 'Muzaffarpur', 'Minapur',
        'Bochaha', 'Sakra', 'Kurhani', 'Gaighat', 'Aurai', 'Cheria-Bariarpur',
        'Marhaura', 'Mushahari', 'Goreyakothi', 'Vaishali', 'Patepur', 'Kalyanpur',
        'Jandaha', 'Mahua', 'Raghopur', 'Mahnar', 'Paroo', 'Sahebganj', 'Rosera',
        'Morwa', 'Samastipur', 'Pusa', 'Mohiuddinnagar', 'Bibhutipur', 'Dalsinghsarai',
        'Hayaghat', 'Alauli', 'Khagaria', 'Parbatta', 'Beldaur', 'Madhepura',
        'Singheshwar', 'Bihariganj', 'Raniganj'
    ],
    
    # Central Bihar (80 seats)
    'Central Bihar': [
        'Patna Sahib', 'Bankipore', 'Kumhrar', 'Patliputra', 'Danapur', 'Maner',
        'Phulwari Sharif', 'Masaurhi', 'Daudnagar', 'Aurangabad', 'Rafiganj', 'Gurua',
        'Tikari', 'Nathnagar', 'Hisua', 'Nawada', 'Rajauli', 'Gobindpur', 'Biharsharif',
        'Rajgir', 'Islampur', 'Hilsa', 'Nalanda', 'Asthawan', 'Barbigha', 'Mokameh',
        'Barh', 'Bakhtiarpur', 'Mahnar', 'Tarapur', 'Kusheshwar Asthan', 'Ghanshyampur',
        'Patori', 'Pusa', 'Samastipur', 'Ujiarpur', 'Morwa', 'Sarairanjan', 'Lalganj',
        'Mirganj', 'Sriramnagar', 'Narpatganj', 'Kochadhaman', 'Nirmali', 'Rupauli',
        'Forbesganj', 'Araria', 'Jokihat', 'Sikti', 'Raniganj', 'Kishanganj', 'Kochadhaman',
        'Amour', 'Bahadurganj', 'Thakurganj', 'Balrampur', 'Benipur', 'Darbhanga Rural',
        'Darbhanga', 'Hanuman Nagar', 'Singhwara', 'Kusheshwar Asthan', 'Ghanshyampur',
        'Keoti', 'Jale', 'Babubarhi', 'Madhwapur', 'Laukaha', 'Jhanjharpur', 'Sakri',
        'Mahishi', 'Kurhani', 'Muzaffarpur', 'Minapur', 'Bochaha', 'Sakra', 'Kurhani',
        'Gaighat', 'Aurai', 'Cheria-Bariarpur', 'Marhaura', 'Mushahari', 'Goreyakothi'
    ],
    
    # South Bihar (60 seats)
    'South Bihar': [
        'Sasaram', 'Nokha', 'Dehri', 'Bhabua', 'Chainpur', 'Chenari', 'Mohania',
        'Ramgarh', 'Kargahar', 'Dinara', 'Bikramganj', 'Arwal', 'Karpi', 'Jehanabad',
        'Ghosi', 'Makhdumpur', 'Belaganj', 'Gaya Town', 'Sherghati', 'Bodhgaya',
        'Tikari', 'Atri', 'Wazirganj', 'Obra', 'Aurangabad', 'Kutumba', 'Rafiganj',
        'Gurua', 'Imamganj', 'Dumraon', 'Buxar', 'Brahmpur', 'Chakia', 'Sandesh',
        'Maharajganj', 'Siwan', 'Darauli', 'Ekma', 'Sonepur', 'Riga', 'Amnour',
        'Ziradei', 'Raghunathpur', 'Gopalganj', 'Kuchaikote', 'Barauli', 'Manjhi',
        'Masrakh', 'Baniapur', 'Maharajganj', 'Runnisaidpur', 'Chapra', 'Garkha',
        'Amnour', 'Parsa', 'Sonpur', 'Chhapra', 'Taraiya', 'Ekma', 'Sonepur', 'Riga'
    ],
    
    # East Bihar (43 seats)
    'East Bihar': [
        'Murliganj', 'Saharsa', 'Mahishi', 'Simri Bakhtiarpur', 'Sonbarsa', 'Supaul',
        'Triveniganj', 'Chhatapur', 'Pipra', 'Madhepura', 'Singheshwar', 'Bihariganj',
        'Raniganj', 'Bhagalpur', 'Sultanganj', 'Kahalgaon', 'Pirpainti', 'Nathnagar',
        'Gopalpur', 'Bihpur', 'Sabour', 'Naugachia', 'Goradih', 'Bhagalpur', 'Ismailpur',
        'Katihar', 'Kadwa', 'Balrampur', 'Pranpur', 'Maheshkhunt', 'Korha', 'Barsoi',
        'Forbesganj', 'Araria', 'Jokihat', 'Sikti', 'Raniganj', 'Kishanganj', 'Kochadhaman',
        'Amour', 'Bahadurganj', 'Thakurganj', 'Balrampur'
    ]
}

# Common candidate names for Bihar
CANDIDATE_NAMES = {
    'male': [
        'Rajesh Kumar', 'Suresh Yadav', 'Ramesh Singh', 'Mukesh Sahani', 'Dinesh Kumar',
        'Nitish Kumar', 'Lalu Prasad', 'Tejashwi Yadav', 'Sushil Modi', 'Ravi Shankar',
        'Ashok Kumar', 'Vinod Singh', 'Manoj Yadav', 'Santosh Kumar', 'Prakash Singh',
        'Anil Kumar', 'Sunil Yadav', 'Rajesh Ranjan', 'Lalit Yadav', 'Nand Kishore',
        'Bhola Singh', 'Ram Chandra', 'Shyam Sundar', 'Hari Narayan', 'Gopal Yadav',
        'Krishna Kumar', 'Shiv Kumar', 'Raman Singh', 'Brajesh Yadav', 'Upendra Kushwaha'
    ],
    'female': [
        'Meira Kumar', 'Renu Kushwaha', 'Sita Sahu', 'Geeta Devi', 'Sunita Yadav',
        'Meera Singh', 'Kavita Devi', 'Pushpa Devi', 'Anita Kumar', 'Rekha Devi',
        'Shanti Devi', 'Kamala Devi', 'Urmila Yadav', 'Savita Singh', 'Poonam Devi',
        'Lalita Yadav', 'Sudha Devi', 'Kiran Devi', 'Mamta Singh', 'Priya Yadav'
    ]
}

def generate_candidate_name(gender_preference=None):
    """Generate realistic candidate name"""
    if gender_preference == 'female' or (gender_preference is None and random.random() < 0.25):
        return random.choice(CANDIDATE_NAMES['female'])
    else:
        return random.choice(CANDIDATE_NAMES['male'])

def generate_candidate_data(constituency, region, party):
    """Generate realistic candidate data"""
    name = generate_candidate_name()
    
    # Age distribution
    age = random.randint(35, 70)
    
    # Education levels
    education_options = ['Graduate', 'Post Graduate', '12th Pass', 'Diploma', 'Professional']
    education = random.choice(education_options)
    
    # Assets (in lakhs)
    if party in ['BJP', 'JDU', 'RJD', 'INC']:
        assets_lakhs = random.randint(50, 500)  # Major parties tend to have wealthier candidates
    else:
        assets_lakhs = random.randint(10, 200)
    
    assets = f"₹{assets_lakhs} L" if assets_lakhs < 100 else f"₹{assets_lakhs/100:.1f} Cr"
    
    # Criminal cases
    criminal_cases = random.choices([0, 1, 2, 3, 4, 5], weights=[60, 20, 10, 5, 3, 2])[0]
    
    # Experience
    experience_options = [
        'First time', 'Sitting MLA', 'Former MLA', 'Former MP', 'Social Worker',
        'Business Leader', 'Youth Leader', 'Local Leader', 'Party Worker'
    ]
    
    # Sitting MLAs more likely for major parties
    if party in ['BJP', 'JDU', 'RJD', 'INC'] and random.random() < 0.3:
        experience = 'Sitting MLA'
    elif random.random() < 0.2:
        experience = 'Former MLA'
    else:
        experience = random.choice(experience_options)
    
    return {
        'name': name,
        'party': party,
        'age': age,
        'education': education,
        'assets': assets,
        'criminal_cases': criminal_cases,
        'experience': experience
    }

def generate_historical_results(constituency, region):
    """Generate realistic historical election results"""
    
    # Determine likely winning party based on region
    if region == 'Mithilanchal':
        likely_winners = ['RJD', 'JDU', 'INC']
        weights = [0.5, 0.3, 0.2]
    elif region == 'Central Bihar':
        likely_winners = ['BJP', 'JDU', 'RJD', 'INC']
        weights = [0.35, 0.25, 0.25, 0.15]
    elif region == 'South Bihar':
        likely_winners = ['BJP', 'JDU', 'RJD']
        weights = [0.45, 0.35, 0.2]
    else:  # East Bihar
        likely_winners = ['RJD', 'BJP', 'INC', 'JDU']
        weights = [0.4, 0.3, 0.2, 0.1]
    
    winner_2020 = random.choices(likely_winners, weights=weights)[0]
    winner_2019 = random.choices(likely_winners, weights=weights)[0]
    winner_2015 = random.choices(likely_winners, weights=weights)[0]
    
    return {
        '2020_assembly': {
            'winner': generate_candidate_name(),
            'party': winner_2020,
            'margin': random.randint(500, 25000),
            'vote_share': random.uniform(35, 65),
            'turnout': random.uniform(60, 80)
        },
        '2019_lok_sabha': {
            'winner': generate_candidate_name(),
            'party': winner_2019,
            'margin': random.randint(1000, 50000),
            'vote_share': random.uniform(30, 70),
            'turnout': random.uniform(45, 65)
        },
        '2015_assembly': {
            'winner': generate_candidate_name(),
            'party': winner_2015,
            'margin': random.randint(800, 30000),
            'vote_share': random.uniform(32, 68),
            'turnout': random.uniform(55, 75)
        }
    }

def generate_demographics(constituency, region):
    """Generate realistic demographic data"""
    
    # Base voters
    base_voters = random.randint(200000, 350000)
    
    # Gender split
    male_percentage = random.uniform(0.52, 0.58)
    male_voters = int(base_voters * male_percentage)
    female_voters = base_voters - male_voters
    
    # Urban percentage by region
    if region == 'Central Bihar':
        urban_pct = random.uniform(40, 80)
    elif region == 'Mithilanchal':
        urban_pct = random.uniform(15, 40)
    elif region == 'South Bihar':
        urban_pct = random.uniform(25, 50)
    else:  # East Bihar
        urban_pct = random.uniform(20, 45)
    
    # Literacy rate
    literacy_rate = random.uniform(60, 85)
    
    return {
        'total_voters': base_voters,
        'male_voters': male_voters,
        'female_voters': female_voters,
        'urban_percentage': round(urban_pct, 1),
        'literacy_rate': round(literacy_rate, 1)
    }

def generate_all_constituencies():
    """Generate candidate data for all 243 Bihar constituencies"""
    
    all_constituencies = {}
    constituency_counter = 1
    
    for region, constituencies in BIHAR_CONSTITUENCIES.items():
        for constituency in constituencies:
            
            # Generate 3-4 candidates per constituency
            num_candidates = random.choice([3, 4])
            candidates = []
            
            # Ensure major parties are represented
            parties_pool = ['BJP', 'JDU', 'RJD', 'INC']
            
            # Add other parties occasionally
            if random.random() < 0.3:
                parties_pool.append(random.choice(['CPI_ML', 'HAM', 'VIP', 'BSP', 'AIMIM']))
            
            # Select parties for this constituency
            selected_parties = random.sample(parties_pool, min(num_candidates, len(parties_pool)))
            
            # Generate candidates
            for party in selected_parties:
                candidate = generate_candidate_data(constituency, region, party)
                candidates.append(candidate)
            
            # Generate constituency data
            all_constituencies[constituency] = {
                'constituency_code': f'AC_{constituency_counter:03d}',
                'region': region,
                'candidates': candidates,
                'historical_results': generate_historical_results(constituency, region),
                'demographics': generate_demographics(constituency, region)
            }
            
            constituency_counter += 1
            
            # Stop at 243 constituencies
            if constituency_counter > 243:
                break
        
        if constituency_counter > 243:
            break
    
    return all_constituencies

def save_constituencies_data():
    """Generate and save all constituency data"""
    print("🔄 Generating candidate data for all 243 Bihar constituencies...")
    
    all_data = generate_all_constituencies()
    
    # Save to file
    import json
    with open('src/data/all_constituencies.json', 'w') as f:
        json.dump(all_data, f, indent=2, default=str)
    
    print(f"✅ Generated data for {len(all_data)} constituencies")
    print(f"📁 Saved to src/data/all_constituencies.json")
    
    # Generate summary
    summary = {
        'total_constituencies': len(all_data),
        'by_region': {},
        'total_candidates': 0
    }
    
    for const_name, const_data in all_data.items():
        region = const_data['region']
        if region not in summary['by_region']:
            summary['by_region'][region] = 0
        summary['by_region'][region] += 1
        summary['total_candidates'] += len(const_data['candidates'])
    
    print(f"\n📊 Summary:")
    print(f"   Total Constituencies: {summary['total_constituencies']}")
    print(f"   Total Candidates: {summary['total_candidates']}")
    print(f"   By Region:")
    for region, count in summary['by_region'].items():
        print(f"     {region}: {count} constituencies")
    
    return all_data

if __name__ == "__main__":
    save_constituencies_data()