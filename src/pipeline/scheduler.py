from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from src.config.settings import Config
from src.pipeline.daily_update import DailyUpdatePipeline
import logging
import json
import traceback
import signal
import sys


class ForecastScheduler:
    """Advanced scheduler for Bihar election forecast updates"""
    
    def __init__(self, background_mode: bool = False):
        self.background_mode = background_mode
        
        # Initialize scheduler
        if background_mode:
            self.scheduler = BackgroundScheduler()
        else:
            self.scheduler = BlockingScheduler()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize pipeline
        self.pipeline = DailyUpdatePipeline()
        
        # Job tracking
        self.job_history = []
        self.max_history = 100
        
        # Setup event listeners
        self._setup_event_listeners()
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        self.logger.info("Forecast scheduler initialized")
    
    def _setup_logging(self):
        """Setup comprehensive logging for scheduler"""
        log_dir = Config.BASE_DIR / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "scheduler.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('ForecastScheduler')
    
    def _setup_event_listeners(self):
        """Setup event listeners for job monitoring"""
        self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def add_daily_forecast_job(self, hour: int = None, minute: int = 0, timezone: str = 'Asia/Kolkata'):
        """Add daily forecast update job"""
        if hour is None:
            hour = Config.DAILY_UPDATE_HOUR
        
        self.scheduler.add_job(
            func=self._run_daily_forecast,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
            id='daily_forecast_update',
            name='Daily Bihar Forecast Update',
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=3600  # 1 hour grace period
        )
        
        self.logger.info(f"Daily forecast job scheduled for {hour:02d}:{minute:02d} {timezone}")
    
    def add_quick_update_job(self, interval_hours: int = 4):
        """Add quick update job that runs every few hours"""
        self.scheduler.add_job(
            func=self._run_quick_update,
            trigger=IntervalTrigger(hours=interval_hours),
            id='quick_update',
            name='Quick Forecast Update',
            replace_existing=True,
            max_instances=1
        )
        
        self.logger.info(f"Quick update job scheduled every {interval_hours} hours")
    
    def add_data_monitoring_job(self, interval_minutes: int = 30):
        """Add data source monitoring job"""
        self.scheduler.add_job(
            func=self._monitor_data_sources,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='data_monitoring',
            name='Data Source Monitoring',
            replace_existing=True,
            max_instances=1
        )
        
        self.logger.info(f"Data monitoring job scheduled every {interval_minutes} minutes")
    
    def add_cleanup_job(self, hour: int = 2, minute: int = 0):
        """Add daily cleanup job"""
        self.scheduler.add_job(
            func=self._run_cleanup,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_cleanup',
            name='Daily Cleanup',
            replace_existing=True,
            max_instances=1
        )
        
        self.logger.info(f"Daily cleanup job scheduled for {hour:02d}:{minute:02d}")
    
    def add_custom_job(self, func: Callable, trigger_config: Dict, job_id: str, 
                      job_name: str = None, **kwargs):
        """Add custom job with flexible trigger configuration"""
        if job_name is None:
            job_name = job_id.replace('_', ' ').title()
        
        # Parse trigger configuration
        if trigger_config['type'] == 'cron':
            trigger = CronTrigger(**trigger_config['params'])
        elif trigger_config['type'] == 'interval':
            trigger = IntervalTrigger(**trigger_config['params'])
        else:
            raise ValueError(f"Unsupported trigger type: {trigger_config['type']}")
        
        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            name=job_name,
            replace_existing=True,
            max_instances=1,
            **kwargs
        )
        
        self.logger.info(f"Custom job '{job_name}' scheduled with {trigger_config['type']} trigger")
    
    def _run_daily_forecast(self):
        """Execute daily forecast update with comprehensive error handling"""
        job_start = datetime.now()
        job_id = f"daily_forecast_{job_start.strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info("=" * 60)
        self.logger.info("STARTING SCHEDULED DAILY FORECAST UPDATE")
        self.logger.info("=" * 60)
        
        job_record = {
            'job_id': job_id,
            'job_type': 'daily_forecast',
            'start_time': job_start.isoformat(),
            'status': 'running'
        }
        
        try:
            # Run full pipeline
            pipeline_results = self.pipeline.run_full_pipeline()
            
            job_record.update({
                'status': 'completed' if pipeline_results['success'] else 'failed',
                'end_time': datetime.now().isoformat(),
                'duration_minutes': (datetime.now() - job_start).total_seconds() / 60,
                'steps_completed': pipeline_results['steps_completed'],
                'errors': pipeline_results['errors']
            })
            
            if pipeline_results['success']:
                self.logger.info("✅ Daily forecast update completed successfully")
                
                # Extract key results for logging
                if 'simulation' in pipeline_results['results']:
                    sim_results = pipeline_results['results']['simulation']
                    self.logger.info(f"   Mean NDA seats: {sim_results.get('mean_nda_seats', 0):.1f}")
                    self.logger.info(f"   Majority probability: {sim_results.get('probability_majority', 0):.1%}")
                    self.logger.info(f"   Competitive seats: {sim_results.get('competitive_seats', 0)}")
            else:
                self.logger.error("❌ Daily forecast update failed")
                for error in pipeline_results['errors']:
                    self.logger.error(f"   Error: {error}")
        
        except Exception as e:
            error_msg = f"Daily forecast job crashed: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            
            job_record.update({
                'status': 'crashed',
                'end_time': datetime.now().isoformat(),
                'duration_minutes': (datetime.now() - job_start).total_seconds() / 60,
                'error': error_msg
            })
        
        # Record job history
        self._record_job_history(job_record)
        
        self.logger.info("=" * 60)
        self.logger.info("DAILY FORECAST UPDATE COMPLETED")
        self.logger.info("=" * 60)
    
    def _run_quick_update(self):
        """Execute quick update with minimal processing"""
        job_start = datetime.now()
        
        self.logger.info("Running scheduled quick update...")
        
        try:
            results = self.pipeline.run_quick_update()
            
            if results['success']:
                self.logger.info(f"✅ Quick update completed: {results.get('articles_processed', 0)} articles processed")
            else:
                self.logger.warning(f"⚠️ Quick update failed: {results.get('error', 'Unknown error')}")
            
            # Record job
            self._record_job_history({
                'job_type': 'quick_update',
                'start_time': job_start.isoformat(),
                'end_time': datetime.now().isoformat(),
                'status': 'completed' if results['success'] else 'failed',
                'articles_processed': results.get('articles_processed', 0)
            })
        
        except Exception as e:
            self.logger.error(f"Quick update crashed: {e}")
            self._record_job_history({
                'job_type': 'quick_update',
                'start_time': job_start.isoformat(),
                'end_time': datetime.now().isoformat(),
                'status': 'crashed',
                'error': str(e)
            })
    
    def _monitor_data_sources(self):
        """Monitor data source availability and quality"""
        try:
            # Check data source freshness
            freshness = self.pipeline.components['real_data_manager'].check_data_freshness()
            
            # Log status
            self.logger.info(f"Data monitoring: {freshness['news_sources_active']}/3 news sources active")
            
            # Alert if too many sources are down
            if freshness['news_sources_active'] < 2:
                self.logger.warning("⚠️ Multiple news sources unavailable")
            
            if not freshness['eci_accessible']:
                self.logger.warning("⚠️ ECI website not accessible")
            
            # Record monitoring result
            self._record_job_history({
                'job_type': 'data_monitoring',
                'timestamp': datetime.now().isoformat(),
                'status': 'completed',
                'news_sources_active': freshness['news_sources_active'],
                'eci_accessible': freshness['eci_accessible']
            })
        
        except Exception as e:
            self.logger.error(f"Data monitoring failed: {e}")
    
    def _run_cleanup(self):
        """Execute daily cleanup tasks"""
        job_start = datetime.now()
        
        self.logger.info("Running scheduled cleanup...")
        
        try:
            # Cleanup old feature versions
            cleaned_features = self.pipeline.components['feature_store'].cleanup_old_versions(
                keep_days=30, keep_count=10
            )
            
            # Cleanup old model versions
            cleaned_models = self.pipeline.components['model_updater'].cleanup_old_models(keep_count=5)
            
            # Cleanup old job history
            self._cleanup_job_history()
            
            total_cleaned = cleaned_features + cleaned_models
            
            self.logger.info(f"✅ Cleanup completed: {total_cleaned} items removed")
            
            # Record cleanup job
            self._record_job_history({
                'job_type': 'cleanup',
                'start_time': job_start.isoformat(),
                'end_time': datetime.now().isoformat(),
                'status': 'completed',
                'items_cleaned': total_cleaned
            })
        
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            self._record_job_history({
                'job_type': 'cleanup',
                'start_time': job_start.isoformat(),
                'end_time': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e)
            })
    
    def _job_executed_listener(self, event):
        """Handle job execution events"""
        job = self.scheduler.get_job(event.job_id)
        if job:
            self.logger.info(f"Job '{job.name}' executed successfully")
    
    def _job_error_listener(self, event):
        """Handle job error events"""
        job = self.scheduler.get_job(event.job_id)
        job_name = job.name if job else event.job_id
        
        self.logger.error(f"Job '{job_name}' failed with exception: {event.exception}")
        self.logger.error(f"Traceback: {event.traceback}")
        
        # Record error in job history
        self._record_job_history({
            'job_id': event.job_id,
            'job_type': 'error',
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'error': str(event.exception)
        })
    
    def _record_job_history(self, job_record: Dict):
        """Record job execution in history"""
        self.job_history.append(job_record)
        
        # Keep only recent history
        if len(self.job_history) > self.max_history:
            self.job_history = self.job_history[-self.max_history:]
        
        # Save to file
        history_file = Config.BASE_DIR / "logs" / "job_history.json"
        try:
            with open(history_file, 'w') as f:
                json.dump(self.job_history, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save job history: {e}")
    
    def _cleanup_job_history(self):
        """Clean up old job history entries"""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        original_count = len(self.job_history)
        self.job_history = [
            job for job in self.job_history
            if datetime.fromisoformat(job.get('start_time', job.get('timestamp', '1970-01-01'))) > cutoff_date
        ]
        
        cleaned_count = original_count - len(self.job_history)
        if cleaned_count > 0:
            self.logger.info(f"Cleaned {cleaned_count} old job history entries")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.get_jobs():
            self.logger.warning("No jobs scheduled. Add jobs before starting the scheduler.")
            return
        
        self.logger.info("Starting forecast scheduler...")
        self.logger.info(f"Scheduled jobs:")
        
        for job in self.scheduler.get_jobs():
            self.logger.info(f"  - {job.name} (ID: {job.id})")
            self.logger.info(f"    Next run: {job.next_run_time}")
        
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            self.logger.info("Scheduler interrupted by user")
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the scheduler"""
        self.logger.info("Shutting down scheduler...")
        
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        
        self.logger.info("Scheduler shutdown complete")
    
    def pause_job(self, job_id: str):
        """Pause a specific job"""
        try:
            self.scheduler.pause_job(job_id)
            self.logger.info(f"Job '{job_id}' paused")
        except Exception as e:
            self.logger.error(f"Failed to pause job '{job_id}': {e}")
    
    def resume_job(self, job_id: str):
        """Resume a paused job"""
        try:
            self.scheduler.resume_job(job_id)
            self.logger.info(f"Job '{job_id}' resumed")
        except Exception as e:
            self.logger.error(f"Failed to resume job '{job_id}': {e}")
    
    def remove_job(self, job_id: str):
        """Remove a job from the scheduler"""
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Job '{job_id}' removed")
        except Exception as e:
            self.logger.error(f"Failed to remove job '{job_id}': {e}")
    
    def get_job_status(self) -> Dict:
        """Get status of all scheduled jobs"""
        jobs_status = {
            'scheduler_running': self.scheduler.running,
            'total_jobs': len(self.scheduler.get_jobs()),
            'jobs': []
        }
        
        for job in self.scheduler.get_jobs():
            job_info = {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger),
                'max_instances': job.max_instances
            }
            jobs_status['jobs'].append(job_info)
        
        return jobs_status
    
    def get_job_history(self, job_type: str = None, limit: int = 20) -> List[Dict]:
        """Get job execution history"""
        history = self.job_history.copy()
        
        # Filter by job type if specified
        if job_type:
            history = [job for job in history if job.get('job_type') == job_type]
        
        # Sort by timestamp (most recent first)
        history.sort(key=lambda x: x.get('start_time', x.get('timestamp', '')), reverse=True)
        
        return history[:limit]
    
    def run_job_now(self, job_id: str):
        """Manually trigger a job to run immediately"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                self.logger.info(f"Job '{job_id}' scheduled to run immediately")
            else:
                self.logger.error(f"Job '{job_id}' not found")
        except Exception as e:
            self.logger.error(f"Failed to run job '{job_id}' immediately: {e}")


def create_default_scheduler(background_mode: bool = False) -> ForecastScheduler:
    """Create scheduler with default job configuration"""
    scheduler = ForecastScheduler(background_mode=background_mode)
    
    # Add default jobs
    scheduler.add_daily_forecast_job(hour=6, minute=0)  # 6 AM daily
    scheduler.add_quick_update_job(interval_hours=4)    # Every 4 hours
    scheduler.add_data_monitoring_job(interval_minutes=30)  # Every 30 minutes
    scheduler.add_cleanup_job(hour=2, minute=0)         # 2 AM daily cleanup
    
    return scheduler


if __name__ == "__main__":
    # Command line interface for scheduler
    import argparse
    
    parser = argparse.ArgumentParser(description="Bihar Election Forecast Scheduler")
    parser.add_argument('--background', action='store_true', help='Run in background mode')
    parser.add_argument('--daily-hour', type=int, default=6, help='Hour for daily update (0-23)')
    parser.add_argument('--quick-interval', type=int, default=4, help='Hours between quick updates')
    
    args = parser.parse_args()
    
    # Create and start scheduler
    scheduler = create_default_scheduler(background_mode=args.background)
    
    # Override default timings if specified
    if args.daily_hour != 6:
        scheduler.remove_job('daily_forecast_update')
        scheduler.add_daily_forecast_job(hour=args.daily_hour)
    
    if args.quick_interval != 4:
        scheduler.remove_job('quick_update')
        scheduler.add_quick_update_job(interval_hours=args.quick_interval)
    
    # Start scheduler
    scheduler.start()