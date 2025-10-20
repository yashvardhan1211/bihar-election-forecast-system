# Implementation Plan

- [x] 1. Set up project structure and core configuration
  - Create directory structure for src/, data/, and all subdirectories
  - Implement centralized configuration management with environment variable support
  - Create requirements.txt with all necessary dependencies
  - Set up .env.example file with required API keys
  - _Requirements: 8.1, 8.4_

- [x] 2. Implement data ingestion foundation
  - [x] 2.1 Create news ingestion system with NewsAPI integration
    - Implement NewsIngestor class with API key handling and error recovery
    - Add keyword-based filtering for Bihar election terms
    - Implement fallback sample data generation for testing
    - Add data deduplication and validation logic
    - _Requirements: 1.1, 1.4, 5.1_

  - [x] 2.2 Implement poll data ingestion
    - Create PollIngestor class for opinion poll data collection
    - Add sample size and margin of error tracking
    - Implement historical poll data management with CSV persistence
    - _Requirements: 1.2, 1.4_

  - [x] 2.3 Create Google Trends integration
    - Implement TrendsIngestor with pytrends library integration
    - Add geographic filtering for Bihar region
    - Create fallback sample trend data for development
    - _Requirements: 1.3, 1.4_

  - [ ]* 2.4 Write unit tests for data ingestion components
    - Test NewsIngestor with mocked API responses
    - Test PollIngestor data validation and persistence
    - Test TrendsIngestor with sample data
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 3. Build NLP processing engine
  - [x] 3.1 Implement sentiment analysis engine
    - Create SentimentEngine class with transformer model support
    - Add TextBlob fallback for reliability
    - Implement confidence scoring and batch processing
    - Add proper error handling for model loading failures
    - _Requirements: 2.1, 2.4_

  - [x] 3.2 Create entity mapping system
    - Implement EntityMapper class for party identification
    - Add regional mapping with keyword-based classification
    - Create constituency mapping with fuzzy matching capabilities
    - Implement dataframe enrichment with all entity mappings
    - _Requirements: 2.2, 2.3_

  - [ ]* 3.3 Write unit tests for NLP components
    - Test sentiment analysis with known positive/negative samples
    - Test entity mapping accuracy with sample news articles
    - Test batch processing performance and error handling
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 4. Develop feature engineering system
  - [x] 4.1 Create feature updater with EMA smoothing
    - Implement FeatureUpdater class with exponential moving average logic
    - Add sentiment aggregation with temporal decay weighting
    - Create regional sentiment modifiers for constituency-level updates
    - Implement feature bounds clipping to prevent outliers
    - _Requirements: 3.1, 3.3, 3.4_

  - [x] 4.2 Implement poll-based feature updates
    - Add weighted poll averaging based on sample sizes and recency
    - Create swing calculation from baseline election results
    - Implement EMA integration for smooth poll-based updates
    - _Requirements: 3.2, 3.4_

  - [x] 4.3 Add feature persistence and versioning
    - Implement feature loading from CSV with error handling
    - Add timestamped feature backups for audit trails
    - Create feature validation and consistency checks
    - _Requirements: 3.5, 7.4_

  - [ ]* 4.4 Write unit tests for feature engineering
    - Test EMA calculations with known input/output pairs
    - Test sentiment aggregation with sample news data
    - Test feature bounds and validation logic
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 5. Implement model management system
  - [x] 5.1 Create model updater with persistence
    - Implement ModelUpdater class for loading and saving trained models
    - Add model versioning with timestamped backups
    - Create incremental learning support (sliding window retraining)
    - Implement probability calibration maintenance
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 5.2 Add Monte Carlo simulation engine
    - Create simulation runner that uses loaded model for predictions
    - Implement 5000+ simulation runs with proper random seeding
    - Add percentile calculation and statistical summary generation
    - Create marginal seat identification with competitiveness classification
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.3 Write unit tests for model management
    - Test model loading and saving with mock models
    - Test Monte Carlo simulation with deterministic seeds
    - Test statistical calculations and percentile accuracy
    - _Requirements: 4.1, 4.2, 4.3, 7.1, 7.2_

- [x] 6. Build pipeline orchestration system
  - [x] 6.1 Create daily update pipeline
    - Implement DailyUpdatePipeline class with sequential step execution
    - Add comprehensive error handling with partial failure recovery
    - Create progress tracking and detailed logging throughout pipeline
    - Implement result archiving with automated cleanup of old data
    - _Requirements: 1.5, 6.3, 6.4_

  - [x] 6.2 Implement automated scheduler
    - Create ForecastScheduler class using APScheduler for cron-based scheduling
    - Add configurable daily update timing (default 6 AM)
    - Implement robust error logging and graceful failure handling
    - Create manual override capabilities for immediate updates
    - _Requirements: 6.1, 6.2, 6.5_

  - [x] 6.3 Add pipeline integration and workflow
    - Integrate all components (ingestion, NLP, features, models) in pipeline
    - Add data flow validation between pipeline steps
    - Implement rollback capabilities for failed updates
    - Create pipeline status reporting and monitoring
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2_

  - [ ]* 6.4 Write integration tests for pipeline
    - Test complete pipeline execution with sample data
    - Test error recovery and partial failure scenarios
    - Test scheduler reliability and timing accuracy
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 7. Develop interactive dashboard
  - [x] 7.1 Create Streamlit dashboard foundation
    - Implement ForecastDashboard class with Streamlit UI components
    - Add latest results loading with proper error handling
    - Create main dashboard layout with key metrics display
    - Implement historical data loading for trend analysis
    - _Requirements: 5.1, 5.2, 5.4_

  - [x] 7.2 Build forecast visualization components
    - Create interactive seat distribution charts using Plotly
    - Add percentile tables and statistical summaries
    - Implement marginal seats visualization with competitiveness colors
    - Create seat classification pie charts (Safe/Lean/Toss-up)
    - _Requirements: 5.2, 5.3_

  - [x] 7.3 Add historical trends and data export
    - Implement historical forecast trend charts over 30-day periods
    - Add probability trend visualization for majority chances
    - Create CSV download functionality for marginal seats data
    - Add full report text download capabilities
    - _Requirements: 5.4, 5.5_

  - [ ]* 7.4 Write UI tests for dashboard components
    - Test dashboard loading with sample forecast data
    - Test chart rendering and interactivity
    - Test data export functionality and file generation
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 8. Create CLI interface and system initialization
  - [x] 8.1 Implement main CLI entrypoint
    - Create main.py with argparse for command-line interface
    - Add commands for update, schedule, dashboard, and init operations
    - Implement proper exit codes and error handling
    - Create help documentation and usage examples
    - _Requirements: 6.5, 8.2_

  - [x] 8.2 Add system initialization and setup
    - Create init command that sets up directory structure automatically
    - Add environment file template generation (.env.example)
    - Implement dependency checking and installation guidance
    - Create setup validation and system health checks
    - _Requirements: 8.1, 8.4_

  - [x] 8.3 Integrate all components in CLI
    - Wire together all pipeline components through CLI commands
    - Add configuration validation and error reporting
    - Implement graceful shutdown handling for scheduler
    - Create comprehensive logging setup for all operations
    - _Requirements: 6.1, 6.2, 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 8.4 Write end-to-end system tests
    - Test complete system initialization from scratch
    - Test full pipeline execution through CLI commands
    - Test dashboard launch and basic functionality
    - Test error scenarios and recovery mechanisms
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 9. Add documentation and deployment preparation
  - [x] 9.1 Create comprehensive README documentation
    - Write installation and setup instructions
    - Add configuration guide with API key setup
    - Create usage examples for all CLI commands
    - Document architecture and component overview
    - _Requirements: 8.2, 8.3_

  - [x] 9.2 Add example configuration and sample data
    - Create .env.example with all required environment variables
    - Add sample news, poll, and trend data for testing
    - Create example feature files for initial system setup
    - Add sample model file or training instructions
    - _Requirements: 8.1, 8.4_

  - [x] 9.3 Implement production deployment features
    - Add logging configuration for production environments
    - Create backup and recovery procedures documentation
    - Add monitoring and health check endpoints
    - Implement graceful error handling for production scenarios
    - _Requirements: 6.2, 6.3, 6.4, 6.5_