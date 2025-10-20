import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from src.config.settings import Config
import json
import hashlib
import shutil


class FeatureStore:
    """Advanced feature persistence and versioning system"""
    
    def __init__(self):
        self.base_path = Config.PROCESSED_DATA_DIR
        self.features_dir = self.base_path / "features"
        self.versions_dir = self.features_dir / "versions"
        self.metadata_dir = self.features_dir / "metadata"
        
        # Create directories
        for dir_path in [self.features_dir, self.versions_dir, self.metadata_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Feature store initialized at {self.features_dir}")
    
    def save_features(self, df: pd.DataFrame, version_name: str = None, metadata: Dict = None) -> str:
        """Save features with automatic versioning"""
        if version_name is None:
            version_name = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate feature hash for integrity
        feature_hash = self._generate_feature_hash(df)
        
        # Save main features file
        features_path = self.versions_dir / f"features_{version_name}.csv"
        df.to_csv(features_path, index=False)
        
        # Save metadata
        full_metadata = {
            'version': version_name,
            'timestamp': datetime.now().isoformat(),
            'feature_count': len(df.columns),
            'constituency_count': len(df),
            'feature_hash': feature_hash,
            'file_path': str(features_path),
            'custom_metadata': metadata or {}
        }
        
        metadata_path = self.metadata_dir / f"metadata_{version_name}.json"
        with open(metadata_path, 'w') as f:
            json.dump(full_metadata, f, indent=2)
        
        # Update latest symlink
        latest_path = self.base_path / "features_latest.csv"
        if latest_path.exists():
            latest_path.unlink()
        shutil.copy2(features_path, latest_path)
        
        print(f"✅ Saved features version {version_name} with hash {feature_hash[:8]}")
        return version_name
    
    def load_features(self, version: str = "latest") -> pd.DataFrame:
        """Load features by version"""
        if version == "latest":
            features_path = self.base_path / "features_latest.csv"
        else:
            features_path = self.versions_dir / f"features_{version}.csv"
        
        if not features_path.exists():
            raise FileNotFoundError(f"Features version {version} not found")
        
        df = pd.read_csv(features_path)
        print(f"✅ Loaded features version {version}: {len(df)} constituencies, {len(df.columns)} features")
        return df
    
    def list_versions(self) -> List[Dict]:
        """List all available feature versions"""
        versions = []
        
        for metadata_file in self.metadata_dir.glob("metadata_*.json"):
            try:
                with open(metadata_file) as f:
                    metadata = json.load(f)
                versions.append(metadata)
            except Exception as e:
                print(f"Error reading {metadata_file}: {e}")
        
        # Sort by timestamp
        versions.sort(key=lambda x: x['timestamp'], reverse=True)
        return versions
    
    def compare_versions(self, version1: str, version2: str) -> Dict:
        """Compare two feature versions"""
        df1 = self.load_features(version1)
        df2 = self.load_features(version2)
        
        comparison = {
            'version1': version1,
            'version2': version2,
            'feature_changes': {},
            'constituency_changes': {},
            'summary': {}
        }
        
        # Compare feature columns
        cols1 = set(df1.columns)
        cols2 = set(df2.columns)
        
        comparison['feature_changes'] = {
            'added': list(cols2 - cols1),
            'removed': list(cols1 - cols2),
            'common': list(cols1 & cols2)
        }
        
        # Compare values for common features
        common_cols = list(cols1 & cols2)
        if common_cols and len(df1) == len(df2):
            for col in common_cols:
                if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col]):
                    diff = (df2[col] - df1[col]).abs().mean()
                    comparison['constituency_changes'][col] = {
                        'mean_abs_change': diff,
                        'max_change': (df2[col] - df1[col]).abs().max(),
                        'changed_constituencies': ((df2[col] - df1[col]).abs() > 0.001).sum()
                    }
        
        # Summary statistics
        comparison['summary'] = {
            'features_added': len(comparison['feature_changes']['added']),
            'features_removed': len(comparison['feature_changes']['removed']),
            'total_changes': sum(c.get('changed_constituencies', 0) for c in comparison['constituency_changes'].values())
        }
        
        return comparison
    
    def validate_features(self, df: pd.DataFrame) -> Dict:
        """Validate feature data quality"""
        validation = {
            'timestamp': datetime.now().isoformat(),
            'total_features': len(df.columns),
            'total_constituencies': len(df),
            'issues': [],
            'warnings': [],
            'quality_score': 0.0
        }
        
        # Check for missing values
        missing_counts = df.isnull().sum()
        if missing_counts.sum() > 0:
            validation['issues'].append({
                'type': 'missing_values',
                'details': missing_counts[missing_counts > 0].to_dict()
            })
        
        # Check for infinite values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        inf_counts = {}
        for col in numeric_cols:
            inf_count = np.isinf(df[col]).sum()
            if inf_count > 0:
                inf_counts[col] = inf_count
        
        if inf_counts:
            validation['issues'].append({
                'type': 'infinite_values',
                'details': inf_counts
            })
        
        # Check for duplicate constituencies
        if df['constituency'].duplicated().any():
            validation['issues'].append({
                'type': 'duplicate_constituencies',
                'count': df['constituency'].duplicated().sum()
            })
        
        # Check probability bounds
        prob_cols = [col for col in df.columns if 'prob' in col.lower()]
        for col in prob_cols:
            out_of_bounds = ((df[col] < 0) | (df[col] > 1)).sum()
            if out_of_bounds > 0:
                validation['warnings'].append({
                    'type': 'probability_out_of_bounds',
                    'column': col,
                    'count': out_of_bounds
                })
        
        # Check sentiment bounds
        sentiment_cols = [col for col in df.columns if 'sentiment' in col.lower()]
        for col in sentiment_cols:
            out_of_bounds = ((df[col] < -1) | (df[col] > 1)).sum()
            if out_of_bounds > 0:
                validation['warnings'].append({
                    'type': 'sentiment_out_of_bounds',
                    'column': col,
                    'count': out_of_bounds
                })
        
        # Calculate quality score
        total_cells = len(df) * len(df.columns)
        issues_count = sum(len(issue.get('details', {})) if isinstance(issue.get('details'), dict) 
                          else issue.get('count', 0) for issue in validation['issues'])
        warnings_count = sum(w.get('count', 0) for w in validation['warnings'])
        
        validation['quality_score'] = max(0, 1 - (issues_count + warnings_count * 0.5) / total_cells)
        
        return validation
    
    def cleanup_old_versions(self, keep_days: int = 30, keep_count: int = 10):
        """Clean up old feature versions"""
        versions = self.list_versions()
        
        # Keep recent versions by date
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        recent_versions = [v for v in versions if datetime.fromisoformat(v['timestamp']) > cutoff_date]
        
        # Keep top N versions regardless of date
        versions_to_keep = set()
        for v in versions[:keep_count]:
            versions_to_keep.add(v['version'])
        for v in recent_versions:
            versions_to_keep.add(v['version'])
        
        # Delete old versions
        deleted_count = 0
        for version in versions:
            if version['version'] not in versions_to_keep:
                try:
                    # Delete feature file
                    feature_file = self.versions_dir / f"features_{version['version']}.csv"
                    if feature_file.exists():
                        feature_file.unlink()
                    
                    # Delete metadata file
                    metadata_file = self.metadata_dir / f"metadata_{version['version']}.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
                    
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting version {version['version']}: {e}")
        
        print(f"✅ Cleaned up {deleted_count} old feature versions")
        return deleted_count
    
    def export_features(self, version: str = "latest", format: str = "csv") -> Path:
        """Export features in different formats"""
        df = self.load_features(version)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == "csv":
            export_path = self.base_path / f"export_features_{version}_{timestamp}.csv"
            df.to_csv(export_path, index=False)
        elif format == "json":
            export_path = self.base_path / f"export_features_{version}_{timestamp}.json"
            df.to_json(export_path, orient='records', indent=2)
        elif format == "parquet":
            export_path = self.base_path / f"export_features_{version}_{timestamp}.parquet"
            df.to_parquet(export_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"✅ Exported features to {export_path}")
        return export_path
    
    def _generate_feature_hash(self, df: pd.DataFrame) -> str:
        """Generate hash for feature integrity checking"""
        # Create a string representation of the dataframe
        df_string = df.to_string()
        return hashlib.md5(df_string.encode()).hexdigest()
    
    def get_feature_statistics(self, version: str = "latest") -> Dict:
        """Get comprehensive feature statistics"""
        df = self.load_features(version)
        
        stats = {
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'basic_stats': {
                'total_constituencies': len(df),
                'total_features': len(df.columns),
                'numeric_features': len(df.select_dtypes(include=[np.number]).columns),
                'categorical_features': len(df.select_dtypes(include=['object']).columns)
            },
            'feature_stats': {},
            'regional_stats': {},
            'quality_metrics': {}
        }
        
        # Feature-level statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            stats['feature_stats'][col] = {
                'mean': df[col].mean(),
                'std': df[col].std(),
                'min': df[col].min(),
                'max': df[col].max(),
                'missing_count': df[col].isnull().sum(),
                'unique_values': df[col].nunique()
            }
        
        # Regional statistics
        if 'region' in df.columns:
            for region in df['region'].unique():
                region_df = df[df['region'] == region]
                stats['regional_stats'][region] = {
                    'constituency_count': len(region_df),
                    'avg_nda_prob': region_df.get('nda_win_prob', pd.Series([0.5])).mean(),
                    'competitive_seats': len(region_df[
                        (region_df.get('nda_win_prob', pd.Series([0.5])) >= 0.4) & 
                        (region_df.get('nda_win_prob', pd.Series([0.5])) <= 0.6)
                    ])
                }
        
        # Quality metrics
        validation = self.validate_features(df)
        stats['quality_metrics'] = {
            'quality_score': validation['quality_score'],
            'issues_count': len(validation['issues']),
            'warnings_count': len(validation['warnings'])
        }
        
        return stats