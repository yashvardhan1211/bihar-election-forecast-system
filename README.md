# Bihar Election Forecast System 🗳️

A comprehensive AI-powered election forecasting system for Bihar Assembly elections, combining real-time data ingestion, advanced NLP sentiment analysis, and Monte Carlo simulations to predict electoral outcomes.

## 🚀 Features

### Core Capabilities
- **Real-time Data Ingestion**: News, polls, Google Trends, and ECI live results
- **ECI Integration**: Live election results and constituency data from Election Commission
- **Advanced NLP Processing**: Sentiment analysis and entity mapping
- **Intelligent Feature Engineering**: EMA smoothing and temporal weighting
- **Hybrid ML Models**: RandomForest + Fuzzy Logic for predictions
- **Monte Carlo Simulations**: 5000+ simulations for uncertainty quantification
- **Interactive Dashboard**: Real-time visualization with Streamlit
- **Automated Pipeline**: Daily updates with robust error handling

### Key Components
- 📰 **News Sentiment Analysis**: Real-time sentiment tracking from news sources
- 🗳️ **ECI Live Results**: Direct integration with Election Commission data
- 📊 **Poll Aggregation**: Weighted averaging of opinion polls with recency bias
- 📈 **Trend Analysis**: Google Trends integration for public interest tracking
- 🎯 **Constituency Mapping**: 243 Bihar constituencies with regional analysis
- 🔮 **Probabilistic Forecasting**: Seat predictions with confidence intervals
- 📱 **Web Dashboard**: Interactive charts and downloadable reports

## 📋 Prerequisites

- Python 3.8+
- API Keys (optional but recommended):
  - NewsAPI key for real news data
  - Google Trends access (automatic via pytrends)

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd bihar-election-forecast
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize System
```bash
python main.py init
```

## 🏛️ ECI-Style Homepage

The system features a professional **Election Commission of India (ECI) style homepage** that matches the official government results page design.

### Launch ECI Homepage
```bash
# Method 1: Direct ECI Homepage
streamlit run eci_homepage.py

# Method 2: Style Selection Dashboard  
streamlit run src/dashboard/app.py
# Then select "ECI Official Style" in sidebar

# Method 3: Main Application
python main.py dashboard
```

### ECI Homepage Features
- 🏛️ **Official ECI Design**: Authentic government styling with ECI colors and branding
- 📊 **Party-wise Results**: Alliance and individual party performance tables
- 🎯 **Constituency Summary**: Top battleground seats with leading status
- 📱 **Live Updates**: Real-time forecast changes and model updates
- 🔒 **Professional Layout**: Government-standard presentation for public use

This will:
- Create all necessary directories
- Generate `.env.example` template
- Set up initial configuration
- Validate system dependencies

### 4. Configure Environment (Optional)
```bash
cp .env.example .env
# Edit .env with your API keys
```

**Environment Variables:**
```bash
# Optional: For real news data (fallback to sample data if not provided)
NEWSAPI_KEY=your_newsapi_key_here

# System Configuration
LOG_LEVEL=INFO
DATA_UPDATE_HOUR=6
N_MONTE_CARLO_SIMS=5000
```

## 🚀 Quick Start

### Option 1: Full Automated System
```bash
# Start the automated daily update scheduler
python main.py schedule

# In another terminal, launch the dashboard
python main.py dashboard
```

### Option 2: Manual Updates
```bash
# Run a single forecast update
python main.py update

# Launch dashboard to view results
python main.py dashboard
```

### Option 3: Development Mode
```bash
# Run update with sample data (no API keys needed)
python main.py update --sample-data

# Launch dashboard
python main.py dashboard
```

## 📊 Dashboard Usage

The interactive dashboard provides:

### Main Forecast View
- **Current Seat Prediction**: NDA vs INDI seat counts with confidence intervals
- **Probability Meters**: Chances of majority, supermajority, hung assembly
- **Seat Classification**: Safe, Likely, Lean, and Toss-up seats breakdown

### Detailed Analysis
- **Marginal Seats**: Most competitive constituencies ranked by uncertainty
- **Regional Breakdown**: Performance by Bihar regions (Mithilanchal, Central, etc.)
- **Historical Trends**: 30-day forecast evolution charts
- **Monte Carlo Results**: Full statistical distribution of outcomes

### Data Export
- Download marginal seats as CSV
- Export full forecast report
- Historical data download

## 🏗️ System Architecture

```
├── src/
│   ├── config/          # Configuration management
│   ├── ingest/          # Data ingestion (News, Polls, Trends)
│   ├── nlp/             # Sentiment analysis & entity mapping
│   ├── features/        # Feature engineering & persistence
│   ├── modeling/        # ML models & Monte Carlo simulation
│   ├── pipeline/        # Orchestration & scheduling
│   └── dashboard/       # Streamlit web interface
├── data/
│   ├── raw/             # Raw ingested data
│   ├── processed/       # Processed features
│   ├── models/          # Trained ML models
│   └── results/         # Forecast outputs
└── main.py              # CLI entry point
```

## 🔧 CLI Commands

### System Management
```bash
# Initialize system (first-time setup)
python main.py init

# Run single forecast update
python main.py update

# Start automated scheduler (runs daily at 6 AM)
python main.py schedule

# Launch interactive dashboard
python main.py dashboard
```

### Advanced Options
```bash
# Update with sample data (no API keys needed)
python main.py update --sample-data

# Force update even if recent data exists
python main.py update --force

# Run with debug logging
python main.py update --verbose

# Custom Monte Carlo simulations
python main.py update --n-sims 10000
```

## 📈 Data Sources

### Primary Sources
1. **News Data**: NewsAPI integration with Bihar election keywords
2. **ECI Live Data**: Real-time results from Election Commission of India
3. **Opinion Polls**: Manual entry system with CSV persistence
4. **Google Trends**: Automated trend tracking for key political terms
5. **Historical Results**: 2020 Bihar Assembly election baseline

### Fallback Data
- Sample news articles with realistic sentiment distributions
- Synthetic poll data based on historical patterns
- Generated trend data for development/testing

## 🤖 Machine Learning Pipeline

### 1. Data Ingestion
- Real-time news article collection and filtering
- ECI live results and constituency data integration
- Opinion poll aggregation with quality weighting
- Google Trends data normalization

### 2. NLP Processing
- Transformer-based sentiment analysis (DistilBERT)
- TextBlob fallback for reliability
- Entity mapping for parties and constituencies

### 3. Feature Engineering
- Exponential Moving Average (EMA) smoothing
- Temporal decay weighting for recency bias
- Regional sentiment modifiers
- Poll momentum calculations

### 4. Prediction Models
- **Hybrid Model**: RandomForest + Fuzzy Logic rules
- **Calibrated Probabilities**: Isotonic regression calibration
- **Regional Adjustments**: Bihar-specific political context

### 5. Monte Carlo Simulation
- 5000+ simulation runs with correlated uncertainty
- Regional and national swing modeling
- Percentile-based confidence intervals

## 📊 Output Formats

### Dashboard Visualizations
- Interactive seat distribution charts
- Probability trend lines
- Regional heatmaps
- Marginal seat rankings

### Exportable Data
- **CSV**: Marginal seats with competitiveness scores
- **JSON**: Full forecast statistics and metadata
- **Text Reports**: Human-readable forecast summaries

### API-Ready Outputs
All results stored in structured JSON format for easy integration with external systems.

## 🔍 Monitoring & Validation

### Data Quality Checks
- Sentiment score validation (-1 to +1 range)
- Probability bounds enforcement (0.01 to 0.99)
- Feature consistency validation
- Missing data detection and handling

### Model Performance
- Cross-validation during training
- Calibration curve monitoring
- Feature importance tracking
- Prediction confidence scoring

### System Health
- Pipeline execution logging
- Error recovery mechanisms
- Data freshness monitoring
- Resource usage tracking

## 🛡️ Error Handling

### Robust Fallbacks
- **API Failures**: Automatic fallback to sample data
- **Model Loading**: Graceful degradation to simpler models
- **Data Corruption**: Validation and recovery procedures
- **Network Issues**: Retry logic with exponential backoff

### Logging & Debugging
- Comprehensive logging at all pipeline stages
- Error categorization and reporting
- Debug mode for development
- Performance profiling capabilities

## 🔧 Configuration

### Key Settings (config/settings.py)
```python
# Data Update Schedule
DATA_UPDATE_HOUR = 6  # Daily update at 6 AM

# Monte Carlo Simulations
N_MONTE_CARLO_SIMS = 5000

# Feature Engineering
EMA_ALPHA = 0.3  # Exponential smoothing factor
SENTIMENT_DECAY_DAYS = 7  # Sentiment relevance decay

# Model Parameters
MODEL_RETRAIN_DAYS = 7  # Weekly model retraining
UNCERTAINTY_FACTOR = 1.0  # Monte Carlo uncertainty scaling
```

### Directory Structure
All paths configurable via `Config` class:
- `RAW_DATA_DIR`: Raw ingested data storage
- `PROCESSED_DATA_DIR`: Processed features and engineered data
- `MODELS_DIR`: Trained model persistence
- `RESULTS_DIR`: Forecast outputs and archives

## 🚀 Production Deployment

### System Requirements
- **Memory**: 4GB+ RAM recommended
- **Storage**: 10GB+ for data and model storage
- **CPU**: Multi-core recommended for Monte Carlo simulations
- **Network**: Stable internet for API access

### Deployment Checklist
1. ✅ Install Python 3.8+ and dependencies
2. ✅ Configure environment variables
3. ✅ Run system initialization
4. ✅ Test with sample data
5. ✅ Configure API keys (optional)
6. ✅ Set up automated scheduling
7. ✅ Monitor logs and performance

### Monitoring
- Daily pipeline execution logs
- Model performance metrics
- Data quality indicators
- System resource usage

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests (when available)
python -m pytest tests/

# Run with sample data for development
python main.py update --sample-data
```

### Code Structure
- **Modular Design**: Each component is independently testable
- **Configuration-Driven**: All parameters externally configurable
- **Error-Resilient**: Comprehensive error handling and recovery
- **Extensible**: Easy to add new data sources or models

## 📝 License & Copyright

© 2025 YV Predicts. Educational and research purposes only.

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Data Sources**: NewsAPI, Google Trends, Election Commission of India
- **ML Libraries**: scikit-learn, transformers, pandas, numpy
- **Visualization**: Streamlit, Plotly, matplotlib
- **Scheduling**: APScheduler for automated updates

## 📞 Support

For issues, questions, or contributions:
1. Check existing documentation
2. Review error logs in `logs/` directory
3. Test with sample data mode
4. Create detailed issue reports with logs

---

**Built for accurate, transparent, and real-time Bihar election forecasting** 🗳️✨