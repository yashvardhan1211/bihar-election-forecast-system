import shutil
import json
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import os
from src.config.settings import Config
from src.utils.logging_config import ProductionLogger


class BackupManager:
    """Production backup and recovery system"""
    
    def __init__(self):
        self.logger = ProductionLogger.get_logger('bihar_forecast.backup')
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup configuration
        self.backup_config = {
            'keep_daily_backups': 7,
            'keep_weekly_backups': 4,
            'keep_monthly_backups': 3,
            'compression_level': 6
        }
        
        print("✅ Backup manager initialized")
    
    def create_full_backup(self, backup_name: str = None) -> str:
        """Create complete system backup"""
        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"full_backup_{timestamp}"
        
        self.logger.info(f"Starting full backup: {backup_name}")
        
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"
        
        try:
            with tarfile.open(backup_path, 'w:gz', compresslevel=self.backup_config['compression_level']) as tar:
                
                # Backup critical directories
                backup_items = [
                    ('data/processed', 'processed_data'),
                    ('data/models', 'models'),
                    ('data/results', 'results'),
                    ('src/config', 'config'),
                    ('.env', 'environment') if Path('.env').exists() else None,
                    ('logs', 'logs')
                ]
                
                backup_manifest = {
                    'backup_name': backup_name,
                    'timestamp': datetime.now().isoformat(),
                    'backup_type': 'full',
                    'items_backed_up': [],
                    'total_size_mb': 0
                }
                
                for item in backup_items:
                    if item is None:
                        continue
                        
                    source_path, archive_name = item
                    source = Path(source_path)
                    
                    if source.exists():
                        self.logger.info(f"Backing up {source_path}")
                        
                        if source.is_file():
                            tar.add(source, arcname=f"{backup_name}/{archive_name}/{source.name}")
                            size_mb = source.stat().st_size / (1024**2)
                        else:
                            tar.add(source, arcname=f"{backup_name}/{archive_name}")
                            size_mb = sum(f.stat().st_size for f in source.rglob('*') if f.is_file()) / (1024**2)
                        
                        backup_manifest['items_backed_up'].append({
                            'source': source_path,
                            'archive_name': archive_name,
                            'size_mb': size_mb
                        })
                        backup_manifest['total_size_mb'] += size_mb
                
                # Add manifest to backup
                manifest_json = json.dumps(backup_manifest, indent=2)
                manifest_info = tarfile.TarInfo(name=f"{backup_name}/backup_manifest.json")
                manifest_info.size = len(manifest_json.encode())
                tar.addfile(manifest_info, fileobj=io.BytesIO(manifest_json.encode()))
            
            self.logger.info(f"Full backup completed: {backup_path} ({backup_manifest['total_size_mb']:.1f} MB)")
            
            # Save backup metadata
            self._save_backup_metadata(backup_name, backup_manifest)
            
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Full backup failed: {e}")
            if backup_path.exists():
                backup_path.unlink()
            raise
    
    def create_incremental_backup(self, since_date: datetime = None) -> str:
        """Create incremental backup of changed files"""
        if since_date is None:
            since_date = datetime.now() - timedelta(days=1)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"incremental_backup_{timestamp}"
        
        self.logger.info(f"Starting incremental backup since {since_date}")
        
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"
        
        try:
            with tarfile.open(backup_path, 'w:gz', compresslevel=self.backup_config['compression_level']) as tar:
                
                backup_manifest = {
                    'backup_name': backup_name,
                    'timestamp': datetime.now().isoformat(),
                    'backup_type': 'incremental',
                    'since_date': since_date.isoformat(),
                    'items_backed_up': [],
                    'total_size_mb': 0
                }
                
                # Find changed files
                changed_files = self._find_changed_files(since_date)
                
                for file_path in changed_files:
                    self.logger.debug(f"Backing up changed file: {file_path}")
                    
                    tar.add(file_path, arcname=f"{backup_name}/{file_path}")
                    size_mb = file_path.stat().st_size / (1024**2)
                    
                    backup_manifest['items_backed_up'].append({
                        'file': str(file_path),
                        'size_mb': size_mb,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
                    backup_manifest['total_size_mb'] += size_mb
                
                # Add manifest
                manifest_json = json.dumps(backup_manifest, indent=2)
                manifest_info = tarfile.TarInfo(name=f"{backup_name}/backup_manifest.json")
                manifest_info.size = len(manifest_json.encode())
                tar.addfile(manifest_info, fileobj=io.BytesIO(manifest_json.encode()))
            
            self.logger.info(f"Incremental backup completed: {backup_path} ({len(changed_files)} files, {backup_manifest['total_size_mb']:.1f} MB)")
            
            self._save_backup_metadata(backup_name, backup_manifest)
            
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Incremental backup failed: {e}")
            if backup_path.exists():
                backup_path.unlink()
            raise
    
    def restore_backup(self, backup_path: str, restore_location: str = None) -> bool:
        """Restore from backup"""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            self.logger.error(f"Backup file not found: {backup_path}")
            return False
        
        if restore_location is None:
            restore_location = "."
        
        restore_dir = Path(restore_location)
        
        self.logger.info(f"Starting restore from {backup_path} to {restore_location}")
        
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                
                # Extract manifest first
                manifest_member = None
                for member in tar.getmembers():
                    if member.name.endswith('backup_manifest.json'):
                        manifest_member = member
                        break
                
                if manifest_member:
                    manifest_file = tar.extractfile(manifest_member)
                    manifest = json.loads(manifest_file.read().decode())
                    self.logger.info(f"Restoring backup: {manifest['backup_name']} ({manifest['backup_type']})")
                
                # Extract all files
                tar.extractall(path=restore_dir)
                
                self.logger.info("Backup restore completed successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Backup restore failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List available backups with metadata"""
        backups = []
        
        # Get backup files
        backup_files = list(self.backup_dir.glob('*.tar.gz'))
        
        for backup_file in backup_files:
            backup_info = {
                'filename': backup_file.name,
                'path': str(backup_file),
                'size_mb': backup_file.stat().st_size / (1024**2),
                'created': datetime.fromtimestamp(backup_file.stat().st_ctime).isoformat()
            }
            
            # Try to load metadata
            metadata_file = self.backup_dir / f"{backup_file.stem}_metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    backup_info.update(metadata)
                except Exception as e:
                    self.logger.warning(f"Failed to load metadata for {backup_file.name}: {e}")
            
            backups.append(backup_info)
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return backups
    
    def cleanup_old_backups(self) -> int:
        """Clean up old backups according to retention policy"""
        self.logger.info("Starting backup cleanup")
        
        backups = self.list_backups()
        deleted_count = 0
        
        # Separate backups by type and age
        now = datetime.now()
        daily_backups = []
        weekly_backups = []
        monthly_backups = []
        
        for backup in backups:
            created = datetime.fromisoformat(backup['created'])
            age_days = (now - created).days
            
            if age_days <= 7:
                daily_backups.append(backup)
            elif age_days <= 30:
                weekly_backups.append(backup)
            else:
                monthly_backups.append(backup)
        
        # Keep only specified number of each type
        backups_to_delete = []
        
        if len(daily_backups) > self.backup_config['keep_daily_backups']:
            backups_to_delete.extend(daily_backups[self.backup_config['keep_daily_backups']:])
        
        if len(weekly_backups) > self.backup_config['keep_weekly_backups']:
            backups_to_delete.extend(weekly_backups[self.backup_config['keep_weekly_backups']:])
        
        if len(monthly_backups) > self.backup_config['keep_monthly_backups']:
            backups_to_delete.extend(monthly_backups[self.backup_config['keep_monthly_backups']:])
        
        # Delete old backups
        for backup in backups_to_delete:
            try:
                backup_path = Path(backup['path'])
                if backup_path.exists():
                    backup_path.unlink()
                    deleted_count += 1
                    self.logger.info(f"Deleted old backup: {backup['filename']}")
                
                # Delete metadata file
                metadata_file = self.backup_dir / f"{backup_path.stem}_metadata.json"
                if metadata_file.exists():
                    metadata_file.unlink()
                    
            except Exception as e:
                self.logger.error(f"Failed to delete backup {backup['filename']}: {e}")
        
        self.logger.info(f"Backup cleanup completed: {deleted_count} backups deleted")
        return deleted_count
    
    def _find_changed_files(self, since_date: datetime) -> List[Path]:
        """Find files modified since given date"""
        changed_files = []
        
        # Directories to check for changes
        check_dirs = [
            Path('data/processed'),
            Path('data/models'),
            Path('data/results'),
            Path('src/config')
        ]
        
        since_timestamp = since_date.timestamp()
        
        for check_dir in check_dirs:
            if check_dir.exists():
                for file_path in check_dir.rglob('*'):
                    if file_path.is_file() and file_path.stat().st_mtime > since_timestamp:
                        changed_files.append(file_path)
        
        return changed_files
    
    def _save_backup_metadata(self, backup_name: str, manifest: Dict):
        """Save backup metadata to separate file"""
        metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
        
        try:
            with open(metadata_file, 'w') as f:
                json.dump(manifest, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save backup metadata: {e}")
    
    def verify_backup_integrity(self, backup_path: str) -> bool:
        """Verify backup file integrity"""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            return False
        
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                # Try to read all members
                for member in tar.getmembers():
                    if member.isfile():
                        tar.extractfile(member).read(1024)  # Read first 1KB
                
                self.logger.info(f"Backup integrity verified: {backup_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Backup integrity check failed for {backup_path}: {e}")
            return False


# Convenience functions
def create_backup(backup_type: str = 'full') -> str:
    """Create backup (full or incremental)"""
    manager = BackupManager()
    
    if backup_type == 'full':
        return manager.create_full_backup()
    elif backup_type == 'incremental':
        return manager.create_incremental_backup()
    else:
        raise ValueError("backup_type must be 'full' or 'incremental'")


def restore_from_backup(backup_path: str, restore_location: str = None) -> bool:
    """Restore from backup file"""
    manager = BackupManager()
    return manager.restore_backup(backup_path, restore_location)


# Add missing import
import io