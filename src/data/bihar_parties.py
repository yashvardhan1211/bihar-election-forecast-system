"""
Bihar Political Parties and Candidate Database
"""

# Major Bihar Political Parties
BIHAR_PARTIES = {
    # NDA Alliance
    'BJP': {
        'full_name': 'Bharatiya Janata Party',
        'alliance': 'NDA',
        'color': '#FF9933',
        'symbol': 'Lotus',
        'leader': 'Narendra Modi',
        'state_leader': 'Sushil Kumar Modi'
    },
    'JDU': {
        'full_name': 'Janata Dal (United)',
        'alliance': 'NDA',
        'color': '#138808',
        'symbol': 'Arrow',
        'leader': 'Nitish Kumar',
        'state_leader': 'Nitish Kumar'
    },
    'HAM': {
        'full_name': 'Hindustani Awam Morcha',
        'alliance': 'NDA',
        'color': '#800080',
        'symbol': 'Pressure Cooker',
        'leader': 'Jitan Ram Manjhi',
        'state_leader': 'Jitan Ram Manjhi'
    },
    'VIP': {
        'full_name': 'Vikassheel Insaan Party',
        'alliance': 'NDA',
        'color': '#FFD700',
        'symbol': 'Broom',
        'leader': 'Mukesh Sahani',
        'state_leader': 'Mukesh Sahani'
    },
    
    # INDI Alliance (Mahagathbandhan)
    'RJD': {
        'full_name': 'Rashtriya Janata Dal',
        'alliance': 'INDI',
        'color': '#008000',
        'symbol': 'Lantern',
        'leader': 'Lalu Prasad Yadav',
        'state_leader': 'Tejashwi Yadav'
    },
    'INC': {
        'full_name': 'Indian National Congress',
        'alliance': 'INDI',
        'color': '#19AAED',
        'symbol': 'Hand',
        'leader': 'Mallikarjun Kharge',
        'state_leader': 'Madan Mohan Jha'
    },
    'CPI_ML': {
        'full_name': 'Communist Party of India (Marxist-Leninist)',
        'alliance': 'INDI',
        'color': '#FF0000',
        'symbol': 'Sickle',
        'leader': 'Dipankar Bhattacharya',
        'state_leader': 'Kunal'
    },
    'CPI': {
        'full_name': 'Communist Party of India',
        'alliance': 'INDI',
        'color': '#ED1E26',
        'symbol': 'Ears of Corn and Sickle',
        'leader': 'D. Raja',
        'state_leader': 'Ramnaresh Pandey'
    },
    'CPM': {
        'full_name': 'Communist Party of India (Marxist)',
        'alliance': 'INDI',
        'color': '#CC0000',
        'symbol': 'Hammer, Sickle and Star',
        'leader': 'Sitaram Yechury',
        'state_leader': 'Awadhesh Kumar'
    },
    
    # Other Parties
    'AIMIM': {
        'full_name': 'All India Majlis-e-Ittehadul Muslimeen',
        'alliance': 'Others',
        'color': '#00FF00',
        'symbol': 'Kite',
        'leader': 'Asaduddin Owaisi',
        'state_leader': 'Akhtarul Iman'
    },
    'BSP': {
        'full_name': 'Bahujan Samaj Party',
        'alliance': 'Others',
        'color': '#0000FF',
        'symbol': 'Elephant',
        'leader': 'Mayawati',
        'state_leader': 'Bharat Singh'
    },
    'LJSP': {
        'full_name': 'Lok Janshakti Party (Secular)',
        'alliance': 'Others',
        'color': '#4169E1',
        'symbol': 'Helicopter',
        'leader': 'Chirag Paswan',
        'state_leader': 'Chirag Paswan'
    },
    'JSP': {
        'full_name': 'Jan Swaraj Party',
        'alliance': 'Others',
        'color': '#800000',
        'symbol': 'Whistle',
        'leader': 'Yogendra Yadav',
        'state_leader': 'Yogendra Yadav'
    },
    'NOTA': {
        'full_name': 'None of the Above',
        'alliance': 'Others',
        'color': '#808080',
        'symbol': 'NOTA',
        'leader': 'N/A',
        'state_leader': 'N/A'
    }
}

# Alliance Mappings
NDA_PARTIES = ['BJP', 'JDU', 'HAM', 'VIP']
INDI_PARTIES = ['RJD', 'INC', 'CPI_ML', 'CPI', 'CPM']
OTHER_PARTIES = ['AIMIM', 'BSP', 'LJSP', 'JSP', 'NOTA']

def get_party_alliance(party_code):
    """Get alliance for a party"""
    if party_code in NDA_PARTIES:
        return 'NDA'
    elif party_code in INDI_PARTIES:
        return 'INDI'
    else:
        return 'Others'

def get_party_info(party_code):
    """Get detailed party information"""
    return BIHAR_PARTIES.get(party_code, {
        'full_name': party_code,
        'alliance': 'Others',
        'color': '#808080',
        'symbol': 'Unknown',
        'leader': 'Unknown',
        'state_leader': 'Unknown'
    })