# Design Document

## Overview

The Bihar Election Forecast System is designed as a modular, event-driven architecture that processes real-time political data through a daily pipeline. The system combines multiple data sources (news, polls, trends) with advanced NLP processing and machine learning models to generate probabilistic election forecasts. The architecture emphasizes reliability, scalability, and maintainability through clear separation of concerns and robust error handling.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   NLP Engine    │    │  ML Pipeline    │
│                 │    │                 │    │                 │
│ • NewsAPI       │───▶│ • Sentiment     │───▶│ • Feature Update│
│ • Local Scraping│    │ • Entity Mapping│    │ • Monte Carlo   │
│ • Polls         │    │ • Geo Mapping   │    │ • Calibration   │
│ • Google Trends │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Storage   │    │   Scheduler     │    │   Dashboard     │
│                 │    │                 │    │                 │
│ • Raw Data      │    │ • Daily Updates │    │ • Streamlit UI  │
│ • Processed     │    │ • Error Handling│    │ • Visualizations│
│ • Features      │    │ • Logging       │    │ • Downloads     │
│ • Models        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Architecture

The system follows a layered architecture with clear interfaces:

1. **Data Layer**: Raw and processed data storage with versioning
2. **Ingestion Layer**: Pluggable data source connectors
3. **Processing Layer**: NLP and feature engineering components  
4. **Model Layer**: ML models with incremental learning capabilities
5. **Analysis Layer**: Monte Carlo simulation and result generation
6. **Presentation Layer**: Interactive dashboard and reporting
7. **Orchestration Layer**: Pipeline scheduling and error handling

## Components and Interfaces

### 1. Configuration Management (`src/config/settings.py`)

**Purpose**: Centralized configuration with environment variable support

**Key Features**:
- Environment-based configuration loading
- Directory structure management
- API key management with fallbacks
- Configurable parameters (weights, schedules, thresholds)

**Interface**:
```python
class Config:
    @classmethod
    def create_directories(cls) -> None
    
    # Properties for paths, API keys, and parameters
    BASE_DIR: Path
    NEWS_API_KEY: str
    N_MONTE_CARLO_SIMS: int
    EMA_ALPHA: float
```

### 2. Data Ingestion Components

#### News Ingestor (`src/ingest/news_ingest.py`)

**Purpose**: Fetch and normalize news from multiple sources

**Key Features**:
- NewsAPI integration with keyword-based filtering
- Local news website scraping capability
- Fallback sample data for testing
- Deduplication and data validation

**Interface**:
```python
class NewsIngestor:
    def fetch_from_newsapi(self, days_back: int = 1) -> pd.DataFrame
    def scrape_local_news(self) -> pd.DataFrame
    def save_raw_news(self, df: pd.DataFrame, date_str: str = None) -> None
```

#### Poll Ingestor (`src/ingest/poll_ingest.py`)

**Purpose**: Aggregate polling data from various sources

**Key Features**:
- Opinion poll data collection
- Sample size and margin of error tracking
- Historical poll data management
- Weighted averaging capabilities

#### Trends Ingestor (`src/ingest/trends_ingest.py`)

**Purpose**: Collect Google Trends data for political keywords

**Key Features**:
- pytrends integration for search volume data
- Geographic filtering for Bihar region
- Keyword trend analysis for political figures
- Time series data collection

### 3. NLP Processing Components

#### Sentiment Engine (`src/nlp/sentiment_engine.py`)

**Purpose**: Advanced sentiment analysis with transformer models

**Key Features**:
- Transformer-based sentiment analysis (RoBERTa/BERT)
- TextBlob fallback for reliability
- Confidence scoring for sentiment predictions
- Batch processing capabilities

**Interface**:
```python
class SentimentEngine:
    def analyze_text(self, text: str) -> Dict[str, float]
    def analyze_dataframe(self, df: pd.DataFrame, text_column: str) -> pd.DataFrame
```

#### Entity Mapper (`src/nlp/entity_mapper.py`)

**Purpose**: Map news content to political entities and geographic regions

**Key Features**:
- Political party identification (NDA, INDI, others)
- Regional mapping (Mithilanchal, Central, South, Border)
- Constituency-level mapping with fuzzy matching
- Keyword-based entity extraction

**Interface**:
```python
class EntityMapper:
    def map_party(self, text: str) -> str
    def map_region(self, text: str) -> str
    def map_constituency(self, text: str) -> List[str]
    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame
```

### 4. Feature Engineering Components

#### Feature Updater (`src/features/feature_updater.py`)

**Purpose**: Incremental feature updates with exponential moving averages

**Key Features**:
- Exponential moving average updates for smooth transitions
- Sentiment aggregation with temporal decay
- Poll-based feature updates with sample size weighting
- Regional sentiment modifiers

**Interface**:
```python
class FeatureUpdater:
    def load_base_features(self) -> pd.DataFrame
    def aggregate_news_sentiment(self, news_df: pd.DataFrame) -> Dict[str, pd.Series]
    def update_sentiment_features(self, base_df: pd.DataFrame, sentiment_agg: Dict) -> pd.DataFrame
    def update_poll_features(self, base_df: pd.DataFrame, polls_df: pd.DataFrame) -> pd.DataFrame
    def save_updated_features(self, df: pd.DataFrame) -> None
```

### 5. Model Management Components

#### Model Updater (`src/modeling/model_updater.py`)

**Purpose**: Handle model persistence and incremental updates

**Key Features**:
- Model loading and saving with versioning
- Incremental learning support (where possible)
- Probability calibration maintenance
- Model backup and rollback capabilities

**Interface**:
```python
class ModelUpdater:
    def load_model(self) -> Any
    def incremental_update(self, X_new: pd.DataFrame, y_new: np.ndarray) -> None
    def save_model(self) -> None
```

### 6. Pipeline Orchestration

#### Daily Update Pipeline (`src/pipeline/daily_update.py`)

**Purpose**: Orchestrate the complete daily update workflow

**Key Features**:
- Sequential pipeline execution with error handling
- Progress tracking and logging
- Partial failure recovery
- Result archiving and cleanup

**Workflow**:
1. Data ingestion (news, polls, trends)
2. NLP processing (sentiment, entity mapping)
3. Feature updates with EMA smoothing
4. Model loading and prediction
5. Monte Carlo simulation
6. Analysis and report generation
7. Result archiving

#### Scheduler (`src/pipeline/scheduler.py`)

**Purpose**: Automated scheduling with robust error handling

**Key Features**:
- Cron-based scheduling with APScheduler
- Comprehensive error logging
- Graceful failure handling
- Manual override capabilities

### 7. Analysis and Visualization

#### Dashboard (`src/dashboard/app.py`)

**Purpose**: Interactive Streamlit dashboard for forecast visualization

**Key Features**:
- Real-time forecast display with key metrics
- Interactive seat distribution charts
- Marginal seat analysis with competitiveness classification
- Historical trend visualization
- Data export capabilities

**Dashboard Sections**:
- Overview metrics (mean seats, majority probability)
- Seat distribution with percentiles
- Top marginal seats with win probabilities
- Historical forecast trends
- Detailed data tables and downloads

## Data Models

### News Article Schema
```python
{
    'title': str,
    'description': str,
    'content': str,
    'url': str,
    'publishedAt': datetime,
    'fetch_date': str,
    'source_type': str,
    'sentiment_score': float,
    'sentiment_label': str,
    'sentiment_confidence': float,
    'party_mentioned': str,
    'region': str,
    'constituencies': List[str]
}
```

### Poll Data Schema
```python
{
    'date': str,
    'source': str,
    'nda_vote': float,
    'indi_vote': float,
    'others': float,
    'sample_size': int,
    'moe': float
}
```

### Feature Schema
```python
{
    'constituency': str,
    'region': str,
    'nda_share_2020': float,
    'nda_margin_2020': float,
    'social_sentiment_nda': float,
    'social_sentiment_indi': float,
    'poll_lead_nda': float,
    # Additional demographic and historical features
}
```

### Simulation Results Schema
```python
{
    'nda_seats': np.ndarray,  # Array of seat counts from simulations
    'win_probs': np.ndarray,  # Win probabilities per constituency
    'mean_seats': float,
    'median_seats': float,
    'percentiles': Dict[str, float],
    'p_majority_122': float,
    'p_strong_majority_140': float
}
```

## Error Handling

### Error Categories and Strategies

1. **Data Source Failures**:
   - Graceful degradation with available sources
   - Fallback to sample/cached data for testing
   - Detailed logging with retry mechanisms

2. **NLP Processing Errors**:
   - Fallback from transformer models to TextBlob
   - Skip problematic articles with logging
   - Continue processing with partial results

3. **Model Loading/Prediction Errors**:
   - Model version compatibility checks
   - Fallback to previous model versions
   - Graceful handling of feature mismatches

4. **Pipeline Execution Errors**:
   - Step-by-step error isolation
   - Partial result preservation
   - Comprehensive error reporting

### Error Recovery Mechanisms

- **Retry Logic**: Exponential backoff for API calls
- **Circuit Breakers**: Prevent cascade failures
- **Fallback Data**: Sample data for development/testing
- **Partial Processing**: Continue with available data
- **State Persistence**: Save intermediate results

## Testing Strategy

### Unit Testing
- Individual component testing with mocked dependencies
- Data validation and transformation testing
- Model prediction accuracy testing
- Configuration and error handling testing

### Integration Testing
- End-to-end pipeline testing with sample data
- API integration testing with mock responses
- Database and file system interaction testing
- Dashboard functionality testing

### Performance Testing
- Large dataset processing performance
- Monte Carlo simulation timing
- Memory usage optimization
- Concurrent processing capabilities

### Reliability Testing
- Error injection and recovery testing
- Long-running scheduler stability testing
- Data corruption and recovery testing
- Network failure simulation

### Test Data Strategy
- Sample news articles with known sentiment
- Historical poll data for validation
- Synthetic constituency features
- Known election outcomes for backtesting

## Security Considerations

### API Key Management
- Environment variable storage
- Key rotation capabilities
- Access logging and monitoring
- Secure key distribution

### Data Privacy
- No personal information collection
- Public data source usage only
- Secure data transmission (HTTPS)
- Data retention policies

### System Security
- Input validation and sanitization
- SQL injection prevention (if using databases)
- File system access controls
- Logging without sensitive data exposure

## Performance Optimization

### Data Processing
- Batch processing for large datasets
- Efficient pandas operations
- Memory-mapped file access for large files
- Parallel processing where applicable

### Model Inference
- Model caching and reuse
- Batch prediction optimization
- Feature preprocessing optimization
- GPU acceleration for transformer models (optional)

### Storage Optimization
- Compressed data storage formats
- Efficient file organization
- Automated cleanup of old data
- Index optimization for fast retrieval

## Deployment Considerations

### Environment Setup
- Python virtual environment management
- Dependency version pinning
- Environment-specific configuration
- Database setup (if required)

### Monitoring and Logging
- Structured logging with timestamps
- Performance metrics collection
- Error rate monitoring
- Data quality monitoring

### Backup and Recovery
- Automated data backups
- Model version control
- Configuration backup
- Disaster recovery procedures

### Scalability
- Horizontal scaling capabilities
- Load balancing for dashboard
- Database scaling strategies
- Cloud deployment options