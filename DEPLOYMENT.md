# Bihar Election Forecast System - Production Deployment Guide

## 🚀 Production Deployment

This guide covers deploying the Bihar Election Forecast System in a production environment with monitoring, backup, and recovery capabilities.

## 📋 Pre-Deployment Checklist

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS
- **Python**: 3.8 or higher
- **Memory**: 8GB+ RAM (16GB recommended for large simulations)
- **Storage**: 50GB+ available disk space
- **CPU**: 4+ cores (8+ recommended for parallel processing)
- **Network**: Stable internet connection for API access

### Dependencies
```bash
# System packages (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip python3-venv git curl

# Or macOS with Homebrew
brew install python git
```

## 🔧 Production Setup

### 1. Environment Setup
```bash
# Create production user (recommended)
sudo useradd -m -s /bin/bash bihar-forecast
sudo usermod -aG sudo bihar-forecast
su - bihar-forecast

# Clone repository
git clone <repository-url> bihar-forecast-system
cd bihar-forecast-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Initialize system
python main.py init

# Configure environment
cp .env.example .env
nano .env  # Edit with your API keys and settings
```

**Production Environment Variables:**
```bash
# API Keys
NEWS_API_KEY=your_production_newsapi_key
TWITTER_BEARER_TOKEN=your_twitter_token  # Optional

# System Configuration
LOG_LEVEL=INFO
DATA_UPDATE_HOUR=6
N_MONTE_CARLO_SIMS=10000

# Production Settings
ENVIRONMENT=production
BACKUP_ENABLED=true
HEALTH_CHECK_ENABLED=true
```

### 3. Directory Permissions
```bash
# Set proper permissions
chmod 755 /home/bihar-forecast/bihar-forecast-system
chmod 644 .env
chmod +x main.py

# Create log directory with proper permissions
mkdir -p logs
chmod 755 logs
```

## 🔄 Service Configuration

### 1. Systemd Service (Recommended)

Create service file:
```bash
sudo nano /etc/systemd/system/bihar-forecast.service
```

```ini
[Unit]
Description=Bihar Election Forecast System
After=network.target

[Service]
Type=simple
User=bihar-forecast
Group=bihar-forecast
WorkingDirectory=/home/bihar-forecast/bihar-forecast-system
Environment=PATH=/home/bihar-forecast/bihar-forecast-system/venv/bin
ExecStart=/home/bihar-forecast/bihar-forecast-system/venv/bin/python main.py schedule
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=bihar-forecast

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/home/bihar-forecast/bihar-forecast-system

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bihar-forecast
sudo systemctl start bihar-forecast
sudo systemctl status bihar-forecast
```

### 2. Dashboard Service (Optional)

Create dashboard service:
```bash
sudo nano /etc/systemd/system/bihar-forecast-dashboard.service
```

```ini
[Unit]
Description=Bihar Election Forecast Dashboard
After=network.target

[Service]
Type=simple
User=bihar-forecast
Group=bihar-forecast
WorkingDirectory=/home/bihar-forecast/bihar-forecast-system
Environment=PATH=/home/bihar-forecast/bihar-forecast-system/venv/bin
ExecStart=/home/bihar-forecast/bihar-forecast-system/venv/bin/python main.py dashboard --host 0.0.0.0 --port 8501
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 📊 Monitoring & Health Checks

### 1. Health Check Endpoint
```bash
# Manual health check
python main.py health-check

# Automated health monitoring (add to crontab)
crontab -e
```

Add to crontab:
```bash
# Health check every 30 minutes
*/30 * * * * cd /home/bihar-forecast/bihar-forecast-system && /home/bihar-forecast/bihar-forecast-system/venv/bin/python main.py health-check >> logs/health.log 2>&1

# Daily backup at 2 AM
0 2 * * * cd /home/bihar-forecast/bihar-forecast-system && /home/bihar-forecast/bihar-forecast-system/venv/bin/python -c "from src.utils.backup_recovery import create_backup; create_backup('full')" >> logs/backup.log 2>&1

# Weekly cleanup at 3 AM Sunday
0 3 * * 0 cd /home/bihar-forecast/bihar-forecast-system && /home/bihar-forecast/bihar-forecast-system/venv/bin/python -c "from src.utils.backup_recovery import BackupManager; BackupManager().cleanup_old_backups()" >> logs/cleanup.log 2>&1
```

### 2. Log Monitoring
```bash
# View real-time logs
tail -f logs/bihar_forecast.log

# View error logs
tail -f logs/errors.log

# View system logs
sudo journalctl -u bihar-forecast -f
```

### 3. Performance Monitoring
```bash
# System resource usage
htop

# Disk usage
df -h

# Service status
systemctl status bihar-forecast
systemctl status bihar-forecast-dashboard
```

## 🔒 Security Configuration

### 1. Firewall Setup
```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow dashboard (if external access needed)
sudo ufw allow 8501/tcp

# Check status
sudo ufw status
```

### 2. API Key Security
```bash
# Secure .env file
chmod 600 .env
chown bihar-forecast:bihar-forecast .env

# Consider using environment variables instead of .env file
export NEWS_API_KEY="your_key_here"
```

### 3. Log Security
```bash
# Rotate logs to prevent disk filling
sudo nano /etc/logrotate.d/bihar-forecast
```

```
/home/bihar-forecast/bihar-forecast-system/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 bihar-forecast bihar-forecast
}
```

## 💾 Backup & Recovery

### 1. Automated Backups
```python
# Create full backup
from src.utils.backup_recovery import create_backup
backup_path = create_backup('full')

# Create incremental backup
backup_path = create_backup('incremental')
```

### 2. Manual Backup
```bash
# Create backup via CLI (when implemented)
python main.py backup --type full

# List backups
python main.py backup --list

# Restore from backup
python main.py restore --backup-path /path/to/backup.tar.gz
```

### 3. Recovery Procedures

**Data Corruption Recovery:**
```bash
# Stop services
sudo systemctl stop bihar-forecast
sudo systemctl stop bihar-forecast-dashboard

# Restore from latest backup
python -c "
from src.utils.backup_recovery import BackupManager
manager = BackupManager()
backups = manager.list_backups()
if backups:
    manager.restore_backup(backups[0]['path'])
"

# Restart services
sudo systemctl start bihar-forecast
sudo systemctl start bihar-forecast-dashboard
```

**Complete System Recovery:**
```bash
# Fresh installation
git clone <repository-url> bihar-forecast-system-new
cd bihar-forecast-system-new
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Restore data from backup
python -c "
from src.utils.backup_recovery import restore_from_backup
restore_from_backup('/path/to/backup.tar.gz', '.')
"

# Update configuration
cp /path/to/old/.env .env

# Initialize and start
python main.py init
sudo systemctl start bihar-forecast
```

## 🔍 Troubleshooting

### Common Issues

**1. Service Won't Start**
```bash
# Check logs
sudo journalctl -u bihar-forecast --no-pager -l

# Check permissions
ls -la /home/bihar-forecast/bihar-forecast-system/
sudo -u bihar-forecast python main.py --help

# Check Python environment
sudo -u bihar-forecast /home/bihar-forecast/bihar-forecast-system/venv/bin/python --version
```

**2. API Connection Issues**
```bash
# Test API connectivity
python -c "
from src.utils.health_check import run_health_check
result = run_health_check()
print(result['checks']['api_connectivity'])
"

# Check network connectivity
curl -I https://newsapi.org
ping google.com
```

**3. High Memory Usage**
```bash
# Check memory usage
free -h
ps aux | grep python

# Reduce Monte Carlo simulations
export N_MONTE_CARLO_SIMS=1000
```

**4. Disk Space Issues**
```bash
# Check disk usage
df -h
du -sh data/ logs/ backups/

# Clean up old data
python -c "
from src.utils.backup_recovery import BackupManager
BackupManager().cleanup_old_backups()
"

# Clean up logs
sudo logrotate -f /etc/logrotate.d/bihar-forecast
```

### Performance Optimization

**1. Database Optimization**
```bash
# Use faster storage for data directory
sudo mkdir /mnt/ssd/bihar-data
sudo chown bihar-forecast:bihar-forecast /mnt/ssd/bihar-data
ln -s /mnt/ssd/bihar-data data
```

**2. Memory Optimization**
```bash
# Increase swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**3. CPU Optimization**
```bash
# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Deploy multiple instances with load balancer
- Use shared storage for data synchronization
- Implement distributed Monte Carlo simulations

### Vertical Scaling
- Increase RAM for larger simulations
- Add more CPU cores for parallel processing
- Use faster storage (SSD) for data operations

### Cloud Deployment
- AWS EC2 with EBS storage
- Google Cloud Compute Engine
- Azure Virtual Machines
- Docker containerization for easy deployment

## 🔄 Maintenance Schedule

### Daily
- Automated data updates (6 AM)
- Health checks (every 30 minutes)
- Log monitoring

### Weekly
- Model retraining (Sunday 1 AM)
- Incremental backups cleanup
- Performance review

### Monthly
- Full system backup
- Security updates
- Capacity planning review
- API quota monitoring

## 📞 Support & Monitoring

### Alerting Setup
```bash
# Email alerts for critical errors (requires mail setup)
echo "*/15 * * * * cd /home/bihar-forecast/bihar-forecast-system && python -c \"
from src.utils.health_check import run_health_check
result = run_health_check()
if result['overall_status'] == 'UNHEALTHY':
    import subprocess
    subprocess.run(['mail', '-s', 'Bihar Forecast System Alert', 'admin@example.com'], 
                   input=f'System health check failed: {result}', text=True)
\"" | crontab -
```

### Monitoring Dashboard
- System metrics via htop/top
- Application logs via tail -f
- Health status via web dashboard
- Custom monitoring integration (Prometheus, Grafana)

---

**Production deployment complete! 🎉**

The system is now running in production with:
- ✅ Automated daily updates
- ✅ Health monitoring
- ✅ Backup & recovery
- ✅ Security hardening
- ✅ Performance optimization
- ✅ Error handling & logging