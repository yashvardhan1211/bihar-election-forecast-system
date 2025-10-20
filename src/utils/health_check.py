import os
import psutil
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json
from src.config.settings import Config
from src.utils.logging_config import ProductionLogger


class HealthChecker:
    """Production health monitoring and system checks"""
    
    def __init__(self):
        self.logger = ProductionLogger.get_logger('bihar_forecast.health')
        self.health_dir = Path("health")
        self.health_dir.mkdir(exist_ok=True)
        
        # Health check thresholds
        self.thresholds = {
            'memory_usage_percent': 85.0,
            'disk_usage_percent': 90.0,
            'cpu_usage_percent': 90.0,
            'log_file_size_mb': 100,
            'data_freshness_hours': 25,  # Daily updates + 1 hour buffer
            'model_age_days': 8  # Weekly retraining + 1 day buffer
        }
        
        print("✅ Health checker initialized")
    
    def run_full_health_check(self) -> Dict:
        """Run comprehensive system health check"""
        self.logger.info("Starting full system health check")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'HEALTHY',
            'checks': {},
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        # Run individual checks
        checks = [
            ('system_resources', self._check_system_resources),
            ('disk_space', self._check_disk_space),
            ('data_freshness', self._check_data_freshness),
            ('model_status', self._check_model_status),
            ('log_health', self._check_log_health),
            ('api_connectivity', self._check_api_connectivity),
            ('directory_structure', self._check_directory_structure),
            ('configuration', self._check_configuration)
        ]
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                health_status['checks'][check_name] = result
                
                if result['status'] == 'WARNING':
                    health_status['warnings'].extend(result.get('issues', []))
                elif result['status'] == 'ERROR':
                    health_status['errors'].extend(result.get('issues', []))
                    health_status['overall_status'] = 'UNHEALTHY'
                
                if 'recommendations' in result:
                    health_status['recommendations'].extend(result['recommendations'])
                    
            except Exception as e:
                self.logger.error(f"Health check '{check_name}' failed: {e}")
                health_status['checks'][check_name] = {
                    'status': 'ERROR',
                    'issues': [f"Check failed: {str(e)}"]
                }
                health_status['errors'].append(f"Health check '{check_name}' failed")
                health_status['overall_status'] = 'UNHEALTHY'
        
        # Determine overall status
        if health_status['warnings'] and health_status['overall_status'] == 'HEALTHY':
            health_status['overall_status'] = 'WARNING'
        
        # Save health report
        self._save_health_report(health_status)
        
        self.logger.info(f"Health check complete: {health_status['overall_status']}")
        return health_status
    
    def _check_system_resources(self) -> Dict:
        """Check system resource usage"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # CPU usage (average over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            issues = []
            recommendations = []
            
            if memory_percent > self.thresholds['memory_usage_percent']:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
                recommendations.append("Consider increasing system memory or optimizing memory usage")
            
            if cpu_percent > self.thresholds['cpu_usage_percent']:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                recommendations.append("Check for resource-intensive processes")
            
            status = 'ERROR' if issues else 'HEALTHY'
            
            return {
                'status': status,
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent,
                'memory_available_gb': memory.available / (1024**3),
                'issues': issues,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'issues': [f"Failed to check system resources: {e}"]
            }
    
    def _check_disk_space(self) -> Dict:
        """Check disk space usage"""
        try:
            # Check main directory
            disk_usage = psutil.disk_usage('.')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            issues = []
            recommendations = []
            
            if disk_percent > self.thresholds['disk_usage_percent']:
                issues.append(f"Low disk space: {disk_percent:.1f}% used")
                recommendations.append("Clean up old data files or increase disk space")
            
            # Check specific directories
            dir_sizes = {}
            for dir_name in ['data', 'logs', 'models']:
                if Path(dir_name).exists():
                    size_mb = sum(f.stat().st_size for f in Path(dir_name).rglob('*') if f.is_file()) / (1024**2)
                    dir_sizes[dir_name] = size_mb
            
            status = 'ERROR' if issues else 'HEALTHY'
            
            return {
                'status': status,
                'disk_percent': disk_percent,
                'free_space_gb': disk_usage.free / (1024**3),
                'directory_sizes_mb': dir_sizes,
                'issues': issues,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'issues': [f"Failed to check disk space: {e}"]
            }
    
    def _check_data_freshness(self) -> Dict:
        """Check if data is fresh and up-to-date"""
        try:
            issues = []
            recommendations = []
            data_status = {}
            
            # Check various data files
            data_files = {
                'news_data': Config.RAW_DATA_DIR / 'news' / 'latest_news.json',
                'poll_data': Config.RAW_DATA_DIR / 'polls' / 'polls.csv',
                'trends_data': Config.RAW_DATA_DIR / 'trends' / 'trends.json',
                'features': Config.PROCESSED_DATA_DIR / 'features' / 'latest.csv'
            }
            
            current_time = datetime.now()
            
            for data_type, file_path in data_files.items():
                if file_path.exists():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    hours_old = (current_time - file_time).total_seconds() / 3600
                    
                    data_status[data_type] = {
                        'exists': True,
                        'hours_old': hours_old,
                        'last_updated': file_time.isoformat()
                    }
                    
                    if hours_old > self.thresholds['data_freshness_hours']:
                        issues.append(f"{data_type} is {hours_old:.1f} hours old")
                        recommendations.append(f"Update {data_type} - run data ingestion pipeline")
                else:
                    data_status[data_type] = {'exists': False}
                    issues.append(f"{data_type} file not found")
                    recommendations.append(f"Initialize {data_type} - run system setup")
            
            status = 'WARNING' if issues else 'HEALTHY'
            
            return {
                'status': status,
                'data_status': data_status,
                'issues': issues,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'issues': [f"Failed to check data freshness: {e}"]
            }
    
    def _check_model_status(self) -> Dict:
        """Check model availability and freshness"""
        try:
            issues = []
            recommendations = []
            
            # Check for latest model
            latest_model_path = Config.MODELS_DIR / 'latest_model.joblib'
            
            if not latest_model_path.exists():
                issues.append("No trained model found")
                recommendations.append("Train initial model using available data")
                return {
                    'status': 'ERROR',
                    'model_exists': False,
                    'issues': issues,
                    'recommendations': recommendations
                }
            
            # Check model age
            model_time = datetime.fromtimestamp(latest_model_path.stat().st_mtime)
            days_old = (datetime.now() - model_time).days
            
            model_status = {
                'exists': True,
                'days_old': days_old,
                'last_trained': model_time.isoformat(),
                'file_size_mb': latest_model_path.stat().st_size / (1024**2)
            }
            
            if days_old > self.thresholds['model_age_days']:
                issues.append(f"Model is {days_old} days old")
                recommendations.append("Retrain model with recent data")
            
            status = 'WARNING' if issues else 'HEALTHY'
            
            return {
                'status': status,
                'model_status': model_status,
                'issues': issues,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'issues': [f"Failed to check model status: {e}"]
            }
    
    def _check_log_health(self) -> Dict:
        """Check log file health and size"""
        try:
            issues = []
            recommendations = []
            log_status = {}
            
            logs_dir = Path('logs')
            if not logs_dir.exists():
                return {
                    'status': 'WARNING',
                    'issues': ['Logs directory not found'],
                    'recommendations': ['Initialize logging system']
                }
            
            # Check log files
            for log_file in logs_dir.glob('*.log'):
                size_mb = log_file.stat().st_size / (1024**2)
                log_status[log_file.name] = {
                    'size_mb': size_mb,
                    'last_modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                }
                
                if size_mb > self.thresholds['log_file_size_mb']:
                    issues.append(f"Large log file: {log_file.name} ({size_mb:.1f} MB)")
                    recommendations.append("Consider log rotation or cleanup")
            
            status = 'WARNING' if issues else 'HEALTHY'
            
            return {
                'status': status,
                'log_status': log_status,
                'issues': issues,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'issues': [f"Failed to check log health: {e}"]
            }
    
    def _check_api_connectivity(self) -> Dict:
        """Check external API connectivity"""
        try:
            issues = []
            recommendations = []
            api_status = {}
            
            # Check NewsAPI if key is available
            news_api_key = os.getenv('NEWS_API_KEY')
            if news_api_key and news_api_key != 'your_newsapi_key_here':
                try:
                    response = requests.get(
                        'https://newsapi.org/v2/everything',
                        params={'q': 'test', 'apiKey': news_api_key, 'pageSize': 1},
                        timeout=10
                    )
                    api_status['newsapi'] = {
                        'available': response.status_code == 200,
                        'status_code': response.status_code
                    }
                    
                    if response.status_code != 200:
                        issues.append(f"NewsAPI error: HTTP {response.status_code}")
                        recommendations.append("Check NewsAPI key and quota")
                        
                except requests.RequestException as e:
                    api_status['newsapi'] = {'available': False, 'error': str(e)}
                    issues.append(f"NewsAPI connection failed: {e}")
                    recommendations.append("Check internet connection and API key")
            else:
                api_status['newsapi'] = {'available': False, 'reason': 'No API key configured'}
            
            # Check Google Trends (pytrends)
            try:
                from pytrends.request import TrendReq
                pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
                api_status['google_trends'] = {'available': True}
            except Exception as e:
                api_status['google_trends'] = {'available': False, 'error': str(e)}
                issues.append(f"Google Trends unavailable: {e}")
                recommendations.append("Check pytrends installation and connectivity")
            
            status = 'WARNING' if issues else 'HEALTHY'
            
            return {
                'status': status,
                'api_status': api_status,
                'issues': issues,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'issues': [f"Failed to check API connectivity: {e}"]
            }
    
    def _check_directory_structure(self) -> Dict:
        """Check required directory structure"""
        try:
            issues = []
            recommendations = []
            
            required_dirs = [
                'data/raw/news',
                'data/raw/polls', 
                'data/raw/trends',
                'data/processed/features',
                'data/models',
                'data/results',
                'logs'
            ]
            
            missing_dirs = []
            for dir_path in required_dirs:
                if not Path(dir_path).exists():
                    missing_dirs.append(dir_path)
            
            if missing_dirs:
                issues.extend([f"Missing directory: {d}" for d in missing_dirs])
                recommendations.append("Run system initialization: python main.py init")
            
            status = 'ERROR' if missing_dirs else 'HEALTHY'
            
            return {
                'status': status,
                'required_directories': required_dirs,
                'missing_directories': missing_dirs,
                'issues': issues,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'issues': [f"Failed to check directory structure: {e}"]
            }
    
    def _check_configuration(self) -> Dict:
        """Check system configuration"""
        try:
            issues = []
            recommendations = []
            config_status = {}
            
            # Check environment variables
            env_vars = ['LOG_LEVEL', 'DATA_UPDATE_HOUR', 'N_MONTE_CARLO_SIMS']
            for var in env_vars:
                value = os.getenv(var)
                config_status[var] = value or 'Not set (using default)'
            
            # Check .env file
            env_file_exists = Path('.env').exists()
            config_status['env_file_exists'] = env_file_exists
            
            if not env_file_exists:
                issues.append("No .env file found")
                recommendations.append("Copy .env.example to .env and configure")
            
            # Check critical paths
            try:
                from src.config.settings import Config
                config_status['config_loaded'] = True
                config_status['base_dir'] = str(Config.BASE_DIR)
            except Exception as e:
                issues.append(f"Configuration loading failed: {e}")
                recommendations.append("Check src/config/settings.py")
                config_status['config_loaded'] = False
            
            status = 'WARNING' if issues else 'HEALTHY'
            
            return {
                'status': status,
                'config_status': config_status,
                'issues': issues,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'issues': [f"Failed to check configuration: {e}"]
            }
    
    def _save_health_report(self, health_status: Dict):
        """Save health report to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = self.health_dir / f'health_report_{timestamp}.json'
            
            with open(report_file, 'w') as f:
                json.dump(health_status, f, indent=2, default=str)
            
            # Keep only last 10 reports
            reports = sorted(self.health_dir.glob('health_report_*.json'))
            for old_report in reports[:-10]:
                old_report.unlink()
                
        except Exception as e:
            self.logger.error(f"Failed to save health report: {e}")
    
    def get_system_info(self) -> Dict:
        """Get basic system information"""
        try:
            import platform
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'disk_total_gb': psutil.disk_usage('.').total / (1024**3),
                'uptime_hours': (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds() / 3600
            }
        except Exception as e:
            return {'error': f"Failed to get system info: {e}"}


def run_health_check() -> Dict:
    """Convenience function to run health check"""
    checker = HealthChecker()
    return checker.run_full_health_check()