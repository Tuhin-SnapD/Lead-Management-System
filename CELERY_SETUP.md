# Celery Setup Guide

## Overview

The Lead Management System uses Celery for background task processing, including:
- Automated follow-up reminders
- Lead scoring updates
- Performance tracking
- ML model training (optional)

## Quick Start (Without Redis)

By default, Celery is **disabled** to avoid connection errors when Redis is not available. The ML training and other features will work synchronously.

### To use the system without Redis:

1. **No additional setup required** - the system works out of the box
2. **ML training** will run synchronously (may take a few seconds)
3. **Background tasks** will not run automatically

## Enabling Celery with Redis

### 1. Install Redis

#### Windows:
```bash
# Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
# Or use WSL2 with Redis
```

#### macOS:
```bash
brew install redis
```

#### Linux:
```bash
sudo apt-get install redis-server
```

### 2. Start Redis

#### Windows:
```bash
redis-server
```

#### macOS/Linux:
```bash
redis-server
# Or start as a service
sudo systemctl start redis
```

### 3. Enable Celery

Set the environment variable to enable Celery:

```bash
# Windows PowerShell
$env:CELERY_ENABLED="true"

# Windows Command Prompt
set CELERY_ENABLED=true

# Linux/macOS
export CELERY_ENABLED=true
```

### 4. Start Celery Workers

In separate terminal windows:

```bash
# Start Celery worker
celery -A server worker -l info

# Start Celery beat scheduler (for periodic tasks)
celery -A server beat -l info
```

## Configuration

### Environment Variables

- `CELERY_ENABLED`: Set to "true" to enable Celery (default: "false")
- `CELERY_BROKER_URL`: Redis connection URL (default: "redis://localhost:6379/0")
- `CELERY_RESULT_BACKEND`: Redis result backend URL (default: "redis://localhost:6379/0")

### Example .env file:

```env
CELERY_ENABLED=true
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Background Tasks

When Celery is enabled, the following tasks run automatically:

1. **Lead Score Updates** (daily): Updates ML-based lead scores
2. **Follow-up Reminders** (hourly): Sends email reminders for due follow-ups
3. **Snooze Expiration** (30 minutes): Checks and unsnoozes expired leads
4. **Agent Performance** (hourly): Updates agent performance metrics

## Troubleshooting

### Connection Refused Error

If you see `[WinError 10061] No connection could be made because the target machine actively refused it`:

1. **Ensure Celery is disabled** if you don't have Redis:
   ```bash
   set CELERY_ENABLED=false  # Windows
   export CELERY_ENABLED=false  # Linux/macOS
   ```

2. **Or start Redis** if you want to use Celery:
   ```bash
   redis-server
   ```

### ML Training Issues

- ML training works both with and without Celery
- Without Celery: runs synchronously (may take a few seconds)
- With Celery: runs as a background task

### Performance

- **Without Celery**: All operations are synchronous, may block the web interface
- **With Celery**: Background processing, better user experience

## Development vs Production

### Development
- Celery disabled by default
- Synchronous processing
- No Redis required

### Production
- Enable Celery for better performance
- Install and configure Redis
- Set up Celery workers and beat scheduler 