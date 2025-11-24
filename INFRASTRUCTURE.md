# 🚀 CarScout AI - Infrastructure Management

Complete guide to managing and monitoring your CarScout AI scraping system.

## 📋 Quick Reference

### Starting the System

```bash
# Start all 4 workers (covers all 20 brands)
./start_all_workers.sh

# Start Celery pipeline worker
./celery.sh start

# Check everything is healthy
./health_check.sh
```

### Monitoring

```bash
# Real-time dashboard (comprehensive)
./monitor.sh

# Quick status check
./status_workers.sh

# Full system health check
./health_check.sh

# Celery worker status
./celery.sh status
```

### Stopping

```bash
# Stop all scrapy workers
./stop_all_workers.sh

# Stop Celery
./celery.sh stop

# Stop everything
./stop_all_workers.sh && ./celery.sh stop
```

---

## 🛠️ Management Scripts

### 1. `start_all_workers.sh`
**Purpose**: Start all 4 Scrapy workers in parallel

**What it does**:
- Checks if workers are already running (prevents duplicates)
- Starts 4 workers with different brand configurations
- Saves PIDs for tracking
- Shows startup confirmation

**Usage**:
```bash
./start_all_workers.sh
```

**Expected output**:
- Worker 1 (Mercedes, BMW): PID XXXXX
- Worker 2 (Audi, VW, Opel): PID XXXXX  
- Worker 3 (Ford, Toyota, etc): PID XXXXX
- Worker 4 (Škoda, Seat, Honda, etc): PID XXXXX

---

### 2. `stop_all_workers.sh`
**Purpose**: Gracefully stop all running Scrapy workers

**What it does**:
- Finds all Scrapy processes
- Attempts graceful shutdown (SIGTERM)
- Force kills if needed (SIGKILL)
- Cleans up PID files

**Usage**:
```bash
./stop_all_workers.sh
```

---

### 3. `status_workers.sh`
**Purpose**: Quick status overview

**What it does**:
- Shows which workers are running
- Displays latest scraping activity
- Shows system resources
- Recent progress from logs

**Usage**:
```bash
./status_workers.sh
```

---

### 4. `monitor.sh` ⭐ NEW!
**Purpose**: Comprehensive real-time monitoring dashboard

**What it shows**:
- ✅ Worker status (running/stopped)
- 📊 Items scraped per worker
- 📄 Current page being scraped
- ⚡ Scraping rate (items/minute)
- ⏱️ Worker uptime
- 🎯 Estimated completion time
- 💻 System resources (CPU, memory, load)
- 💾 Database activity (inserts, updates)
- 🔧 Celery worker count
- 📝 Last 5 scraped items

**Usage**:
```bash
./monitor.sh
```

**Tips**:
- Run this to get a complete picture of system status
- Shows exactly how many items each worker has scraped
- Alerts if resources are running low
- Best for monitoring long-running jobs

---

### 5. `supervisor.sh` ⭐ NEW!
**Purpose**: Auto-restart crashed workers (self-healing system)

**What it does**:
- Monitors all 4 workers every 60 seconds
- Auto-restarts workers if they crash
- Health checks (log activity, error patterns)
- Restart throttling (prevents restart loops)
- Logs all events

**Usage**:
```bash
# Start supervisor in background
nohup ./supervisor.sh > logs/supervisor.log 2>&1 &

# Check supervisor logs
tail -f logs/supervisor.log

# Stop supervisor
pkill -f supervisor.sh
```

**Features**:
- ✅ Detects crashed workers
- ✅ Auto-restarts with 5-minute cooldown
- ✅ Stops after 10 restart attempts
- ✅ Checks log file activity
- ✅ Monitors for error patterns
- ✅ Status reports every 10 minutes

**When to use**:
- Running overnight/multi-day scraping
- Want hands-off operation
- Need resilience against crashes

---

### 6. `celery.sh` ⭐ NEW!
**Purpose**: Manage Celery pipeline workers

**Commands**:
```bash
./celery.sh start    # Start optimized Celery (4 concurrent tasks)
./celery.sh stop     # Stop all Celery workers
./celery.sh restart  # Restart Celery (fixes duplicates)
./celery.sh status   # Show Celery status
./celery.sh clean    # Kill all and clean up
```

**What it fixes**:
- ❌ **Problem**: You had 10+ duplicate Celery workers
- ✅ **Solution**: Runs 1 Celery with 4 concurrent tasks (optimized)

**Optimizations**:
- Concurrency: 4 (matches 4 Scrapy workers)
- Max tasks per child: 100 (prevents memory leaks)
- Time limit: 600s per task (prevents hanging)

**When to restart**:
- After system reboot
- If pipeline stops processing
- To clean up duplicates
- Weekly for memory refresh

---

### 7. `health_check.sh` ⭐ NEW!
**Purpose**: Comprehensive system diagnostics

**Checks performed**:
1. ✅ Scrapy workers (4 running?)
2. ✅ Celery workers (1-2 optimal)
3. ✅ Database connection
4. ✅ Disk space (<80% usage)
5. ✅ Log files (size, rotation)
6. ✅ System resources (CPU, memory)
7. ✅ Recent errors in logs
8. ✅ Worker progress (actively scraping?)

**Usage**:
```bash
./health_check.sh
```

**Exit codes**:
- `0` = All healthy ✅
- `1` = Warnings ⚠️
- `2` = Critical issues ❌

**Use in automation**:
```bash
# Run daily health check
if ! ./health_check.sh; then
    echo "System has issues!" | mail -s "CarScout Alert" you@email.com
fi
```

---

## 📊 System Architecture

### Worker Distribution
| Worker | Brands | Est. Listings | Runtime |
|--------|--------|---------------|---------|
| Worker 1 | Mercedes-Benz, BMW | 2,400 | 6-7h |
| Worker 2 | Audi, VW, Opel | 1,500 | 4-5h |
| Worker 3 | Ford, Toyota, Renault, Peugeot, Citroën | 1,800 | 5-6h |
| Worker 4 | Škoda, Seat, Honda, Mazda, Nissan, Hyundai, Kia, Volvo, Fiat, Alfa Romeo | 1,900 | 5-6h |
| **Total** | **20 brands** | **~7,600** | **6-7h** |

### Pipeline Flow
```
Scrapy Workers (4) → PostgreSQL → Celery (4 tasks) → Pipeline Tasks
                                                      ↓
                                            (normalize → price → score → notify)
                                                      ↓
                                            Telegram Channel 🎯
```

### Resource Usage
- **CPU**: ~30% with 4 workers
- **Memory**: ~2GB for Scrapy + 500MB for Celery
- **Disk**: ~500MB logs per cycle
- **Network**: ~5GB traffic per cycle

---

## 🔄 Typical Workflows

### Daily Scraping Run
```bash
# 1. Check system health
./health_check.sh

# 2. Clean up old Celery workers
./celery.sh restart

# 3. Start scraping
./start_all_workers.sh

# 4. Monitor progress
./monitor.sh

# 5. Check again after a few hours
./status_workers.sh
```

### Running Overnight (with Auto-Recovery)
```bash
# 1. Start supervisor first
nohup ./supervisor.sh > logs/supervisor.log 2>&1 &

# 2. Start workers
./start_all_workers.sh

# 3. Start Celery
./celery.sh start

# 4. Go to sleep 😴

# Next morning:
./monitor.sh  # See results!
```

### Troubleshooting
```bash
# Workers not scraping?
./status_workers.sh  # Check if running

# Check for errors
tail -100 logs/worker_*.log | grep ERROR

# Celery not processing?
./celery.sh status
./celery.sh restart  # Fix it

# System slow?
./health_check.sh  # Full diagnostics
top  # Check CPU/memory

# Clean restart everything
./stop_all_workers.sh
./celery.sh stop
sleep 5
./celery.sh start
./start_all_workers.sh
```

---

## 📈 Performance Optimization

### Already Implemented ✅
1. **Multi-worker parallelization** (4 workers = 4x speed)
2. **Optimized Celery** (4 tasks vs 10+ duplicates)
3. **Auto-recovery** (supervisor auto-restarts)
4. **Health monitoring** (proactive issue detection)

### Future Enhancements 🚀
1. **Smart scheduling** (cron jobs with intelligence)
2. **Database optimization** (connection pooling, indexes)
3. **Log rotation** (automatic cleanup of old logs)
4. **Alerting** (Telegram notifications for failures)
5. **Backup system** (automated database backups)

---

## 🐛 Common Issues

### Issue: "Workers stopped unexpectedly"
**Solution**:
```bash
# Check logs for errors
tail -100 logs/worker_*.log | grep ERROR

# Restart with supervisor
nohup ./supervisor.sh > logs/supervisor.log 2>&1 &
```

### Issue: "Too many Celery workers"
**Solution**:
```bash
./celery.sh restart
```

### Issue: "Disk full"
**Solution**:
```bash
# Clean old logs
find logs/ -name "*.log" -mtime +7 -delete

# Or rotate large logs
./celery.sh clean
```

### Issue: "Workers not scraping"
**Solution**:
```bash
# Check if Mobile.bg is accessible
curl -I https://www.mobile.bg

# Restart workers
./stop_all_workers.sh
./start_all_workers.sh
```

---

## 📝 Logs

### Log Files
- `logs/worker_1.log` - Worker 1 (Mercedes, BMW)
- `logs/worker_2.log` - Worker 2 (Audi, VW, Opel)  
- `logs/worker_3.log` - Worker 3 (Ford, Toyota, etc)
- `logs/worker_4.log` - Worker 4 (Remaining brands)
- `logs/celery_worker.log` - Celery pipeline
- `logs/supervisor.log` - Supervisor events

### Useful Log Commands
```bash
# Watch real-time scraping
tail -f logs/worker_1.log | grep "Scraped:"

# Count items scraped
grep "item_scraped_count" logs/worker_*.log

# Find good deals
grep "Score: [7-9]" logs/celery_worker.log

# Check for errors
tail -200 logs/worker_*.log | grep ERROR

# See database operations
tail -100 logs/worker_*.log | grep "INSERT\|UPDATE"
```

---

## 🎯 Best Practices

1. **Run health check before starting** (`./health_check.sh`)
2. **Use supervisor for long runs** (overnight, multi-day)
3. **Monitor with dashboard** (`./monitor.sh`)
4. **Restart Celery weekly** (prevents memory leaks)
5. **Clean logs monthly** (prevents disk full)
6. **Check for updates regularly** (git pull)

---

## 📞 Quick Help

```bash
# System not working?
./health_check.sh  # Diagnose

# Want to see progress?
./monitor.sh  # Real-time dashboard

# Need detailed status?
./status_workers.sh  # Quick overview

# Want auto-recovery?
nohup ./supervisor.sh > logs/supervisor.log 2>&1 &  # Self-healing

# Celery issues?
./celery.sh restart  # Fix most problems
```

---

**Made with ❤️ for reliable, hands-off car scraping** 🚗💨
