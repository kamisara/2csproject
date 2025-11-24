# VulnScan Setup Guide

## Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL database
- Redis server

## Quick Start with Docker (Recommended)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/vulnscan.git
cd vulnscan
```

### 2. Environment Configuration
Create `.env` file in the project root:
```env
# Database Configuration (PostgreSQL)
DB_NAME=vulnscan
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=require

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Django Configuration
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 3. Start Services with Docker Compose
```bash
docker-compose up -d
```

This will start all services:
- **Backend API** - http://localhost:8000
- **Frontend** - http://localhost:5173
- **PostgreSQL** - port 5432
- **Redis** - port 6379
- **Celery Worker** - background task processing

### 4. Access the Application
- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Admin Interface**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/docs

### 5. Create Superuser (Optional)
```bash
docker-compose exec web python manage.py createsuperuser
```

## Manual Development Setup

### Backend Setup

#### 1. Set up Python Environment
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Database Configuration
Ensure PostgreSQL is running and create a database:
```sql
CREATE DATABASE vulnscan;
CREATE USER vulnscan_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE vulnscan TO vulnscan_user;
```

#### 3. Environment Setup
Create `backend/.env`:
```env
DB_NAME=vulnscan
DB_USER=vulnscan_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=disable

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

SECRET_KEY=your-secret-key-here
DEBUG=True
```

#### 4. Database Migrations
```bash
python manage.py migrate
python manage.py collectstatic
```

#### 5. Create Superuser
```bash
python manage.py createsuperuser
```

#### 6. Start Development Server
```bash
python manage.py runserver
```

### Frontend Setup

#### 1. Install Dependencies
```bash
cd frontend
npm install
```

#### 2. Environment Configuration
Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME=VulnScan
```

#### 3. Start Development Server
```bash
npm run dev
```

### Celery Worker Setup

#### 1. Start Redis Server
```bash
# On Ubuntu/Debian
sudo systemctl start redis

# On macOS with Homebrew
brew services start redis

# Or run directly
redis-server
```

#### 2. Start Celery Worker
```bash
cd backend
celery -A vulnscanner worker --loglevel=info -Q scans
```

#### 3. Start Celery Beat (for periodic tasks)
```bash
celery -A vulnscanner beat --loglevel=info
```

## Production Deployment

### 1. Environment Configuration
Update `.env` for production:
```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
SECRET_KEY=your-production-secret-key

# Database
DB_HOST=your-production-db-host
DB_PASSWORD=your-production-db-password

# Security
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

### 2. Docker Production Setup
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. SSL Configuration (Recommended)
Use nginx as reverse proxy with SSL:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Configuration Details

### Database Configuration
VulnScan uses PostgreSQL with the following settings:
- **Database**: PostgreSQL 13+
- **Extensions**: Required for full functionality
- **Connection Pooling**: Recommended for production

### Redis Configuration
- **Port**: 6379 (default)
- **Database 0**: Celery broker
- **Database 1**: Result backend
- **Password**: Set in production

### Celery Configuration
- **Queue**: `scans` for scan tasks
- **Concurrency**: 4 workers by default
- **Time Limits**: 15 minutes max per task

## Troubleshooting

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Test database connection
python manage.py check --database default

# Reset database (development only)
python manage.py reset_db
python manage.py migrate
```

#### Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

#### Celery Worker Issues
```bash
# Check Celery status
celery -A vulnscanner status

# View Celery logs
celery -A vulnscanner worker --loglevel=debug
```

#### Frontend Build Issues
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
```

#### Port Conflicts
If ports are already in use:
```bash
# Check what's using port 8000
lsof -i :8000

# Or use different ports
python manage.py runserver 8001
```

### Health Checks

#### Backend Health
```bash
curl http://localhost:8000/api/health
```

#### Database Health
```bash
python manage.py check --database default
```

#### Redis Health
```bash
redis-cli ping
```

#### Celery Health
```bash
celery -A vulnscanner inspect active
```

### Performance Optimization

#### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_scans_user_id ON scans_app_scan(user_id);
CREATE INDEX CONCURRENTLY idx_scans_status ON scans_app_scan(status);
CREATE INDEX CONCURRENTLY idx_vulnerabilities_scan_id ON scans_app_vulnerability(scan_id);
```

#### Celery Optimization
```python
# In settings.py
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
```

## Monitoring

### Log Files
- **Django Logs**: `logs/django.log`
- **Celery Logs**: `logs/celery.log`
- **Nginx Logs**: `/var/log/nginx/`

### Performance Monitoring
```bash
# Monitor database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Monitor Redis memory usage
redis-cli info memory

# Monitor Celery queue
celery -A vulnscanner inspect reserved
```

## Backup and Recovery

### Database Backup
```bash
# Backup database
pg_dump vulnscan > backup_$(date +%Y%m%d).sql

# Restore database
psql vulnscan < backup_file.sql
```

### Media Files Backup
```bash
# Backup media files
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Restore media files
tar -xzf media_backup_file.tar.gz
```

## Support

For additional help:
1. Check the application logs in `logs/` directory
2. Review Django debug information at `/api/debug/` (development only)
3. Check Celery task status: `celery -A vulnscanner inspect active`
4. Contact the development team with error logs and reproduction steps

## Security Notes
- Always use strong passwords in production
- Enable SSL/HTTPS in production environments
- Regularly update dependencies
- Monitor logs for suspicious activities
- Use environment variables for sensitive configuration
