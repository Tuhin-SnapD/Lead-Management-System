# Installing Redis on Windows

## Option 1: Using Windows Subsystem for Linux (WSL) - Recommended

1. Install WSL2 if you haven't already:
   ```powershell
   wsl --install
   ```

2. Install Redis in WSL:
   ```bash
   sudo apt update
   sudo apt install redis-server
   ```

3. Start Redis:
   ```bash
   sudo service redis-server start
   ```

4. Test Redis:
   ```bash
   redis-cli ping
   ```

## Option 2: Using Docker

1. Install Docker Desktop for Windows
2. Run Redis container:
   ```powershell
   docker run -d -p 6379:6379 --name redis redis:latest
   ```

## Option 3: Using Windows Redis (Limited)

1. Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
2. Install and start the Redis service

## Testing Redis Connection

After installation, test the connection:
```powershell
redis-cli ping
```

You should see: `PONG`

## Starting Redis with the Application

Once Redis is installed, you can start it before running Django:
```powershell
# If using WSL
wsl sudo service redis-server start

# If using Docker
docker start redis

# Then start Django
python manage.py runserver
```

## Note

The current implementation has been modified to work without Redis for development purposes. 
If you want to use the full Celery functionality (background tasks, scheduled jobs), 
you'll need to install Redis and revert the ML training view to use Celery tasks. 