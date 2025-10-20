#!/usr/bin/env python3
"""Initialize directory structure for Bihar Forecast System"""

from src.config.settings import Config

if __name__ == "__main__":
    print("Initializing Bihar Forecast System directories...")
    Config.create_directories()
    
    print("✓ Directory structure created:")
    print(f"  - {Config.RAW_DATA_DIR}")
    print(f"  - {Config.PROCESSED_DATA_DIR}")
    print(f"  - {Config.MODELS_DIR}")
    print(f"  - {Config.RESULTS_DIR}")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and add your API keys")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run: python init_directories.py")