import os
from pathlib import Path

# Try to load dotenv if available, otherwise continue without it
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using environment variables directly.")

class Config:
    """Central configuration for the forecast system"""
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    MODELS_DIR = DATA_DIR / "models"
    RESULTS_DIR = DATA_DIR / "results"
    
    # API Keys
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
    
    # Data Sources
    NEWS_SOURCES = [
        "the-times-of-india",
        "the-hindu", 
        "ndtv",
        "india-today"
    ]
    
    BIHAR_KEYWORDS = [
        # Core election terms
        "Bihar election", "Bihar assembly", "Bihar polls", "Bihar voting", "Bihar constituency",
        
        # Key political figures
        "Nitish Kumar", "Tejashwi Yadav", "Lalu Prasad", "Sushil Modi", "Chirag Paswan",
        "Jitan Ram Manjhi", "Upendra Kushwaha", "Pappu Yadav", "Mukesh Sahani",
        
        # Political parties
        "RJD Bihar", "JDU Bihar", "BJP Bihar", "Congress Bihar", "LJP Bihar", 
        "HAM Bihar", "RLSP Bihar", "VIP Bihar", "CPI Bihar", "CPI(M) Bihar",
        
        # Alliances and coalitions
        "NDA Bihar", "INDI alliance Bihar", "Mahagathbandhan Bihar", "Grand Alliance Bihar",
        
        # Regional terms
        "Patna politics", "Muzaffarpur election", "Darbhanga politics", "Gaya election",
        "Bhagalpur politics", "Purnia election", "Araria politics", "Kishanganj election",
        
        # Election-specific terms
        "Bihar candidate", "Bihar nomination", "Bihar campaign", "Bihar rally",
        "Bihar seat sharing", "Bihar alliance", "Bihar manifesto", "Bihar debate"
    ]
    
    # Model parameters
    N_MONTE_CARLO_SIMS = 5000
    SENTIMENT_WEIGHT = 0.15
    NEWS_DECAY_DAYS = 7  # Exponential decay for news sentiment
    
    # Scheduler
    DAILY_UPDATE_HOUR = 6  # 6 AM daily update
    DAILY_UPDATE_MINUTE = 0
    
    # Feature smoothing
    EMA_ALPHA = 0.3  # Exponential moving average weight for new data
    
    # Constituency mapping
    CONSTITUENCY_COUNT = 243
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        for dir_path in [cls.RAW_DATA_DIR, cls.PROCESSED_DATA_DIR, cls.MODELS_DIR, cls.RESULTS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)