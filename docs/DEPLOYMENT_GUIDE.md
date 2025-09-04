# 🚀 MEDLEY Deployment Guide

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment with HTTPS](#production-deployment-with-https)
4. [Environment Configuration](#environment-configuration)
5. [Troubleshooting](#troubleshooting)

---

## Local Development

### Quick Start (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/medley.git
cd medley

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements_web.txt

# 4. Set environment variables
export OPENROUTER_API_KEY='your-api-key-here'  # Optional for paid models
export USE_FREE_MODELS=true  # Use free models only (no API key needed)

# 5. Start the web application
python web_app.py
```

Access at: http://localhost:5002

### Alternative Startup Methods

#### Using Scripts
```bash
# Basic startup
python scripts/start_web.py

# With HTTPS (self-signed certificate)
python scripts/start_web_https.py
```

#### Using Flask CLI
```bash
export FLASK_APP=web_app.py
export FLASK_ENV=development
flask run --port 5002
```

#### Using Gunicorn (Production-like)
```bash
gunicorn --worker-class gevent \
         --workers 4 \
         --bind 0.0.0.0:5002 \
         --timeout 120 \
         web_app:app
```

---

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 1.29+
- 4GB RAM minimum
- 10GB disk space

### Basic Docker Setup

```bash
# 1. Navigate to deployment directory
cd deployment

# 2. Build and start containers
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f
```

### Docker Deployment Modes

#### Development Mode (HTTP only)
```bash
cd deployment
./scripts/deploy.sh
# Select option 1: Development
```

#### Production Mode with SSL
```bash
cd deployment
./scripts/deploy.sh
# Select option 2: Production with SSL
# Enter your domain and email when prompted
```

#### Production Mode without SSL
```bash
cd deployment
./scripts/deploy.sh
# Select option 3: Production without SSL
```

### Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Remove containers
docker-compose down

# Remove everything including volumes
docker-compose down -v

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Scale workers
docker-compose up -d --scale celery=3

# Access container shell
docker exec -it medley-web bash

# View real-time logs
docker-compose logs -f web
```

---

## Production Deployment with HTTPS

### Using Let's Encrypt SSL

```bash
# 1. Navigate to deployment
cd deployment

# 2. Set domain environment variable
export DOMAIN_NAME=medley.yourdomain.com

# 3. Run SSL setup script
./scripts/setup-ssl.sh $DOMAIN_NAME your-email@example.com

# 4. Start with SSL
docker-compose up -d nginx certbot web redis
```

### Manual SSL Certificate Setup

```bash
# 1. Place certificates in deployment/certbot/conf/live/yourdomain/
# - fullchain.pem
# - privkey.pem

# 2. Generate Diffie-Hellman parameters
openssl dhparam -out deployment/certbot/conf/ssl-dhparams.pem 2048

# 3. Update nginx configuration
sed -i "s/\${DOMAIN_NAME}/yourdomain.com/g" deployment/nginx/conf.d/medley.conf

# 4. Start services
docker-compose up -d
```

### Using Custom SSL Certificates

```bash
# 1. Create certs directory
mkdir -p deployment/certs

# 2. Copy your certificates
cp /path/to/cert.pem deployment/certs/
cp /path/to/key.pem deployment/certs/

# 3. Update docker-compose.yml volumes section
volumes:
  - ./certs/cert.pem:/etc/nginx/ssl/cert.pem:ro
  - ./certs/key.pem:/etc/nginx/ssl/key.pem:ro

# 4. Restart nginx
docker-compose restart nginx
```

---

## Environment Configuration

### Essential Environment Variables

```bash
# Create .env file in project root
cat > .env << EOF
# OpenRouter API (optional for free tier)
OPENROUTER_API_KEY=your-api-key-here

# Model Selection
USE_FREE_MODELS=true  # Use only free models
FORCE_FALLBACK=false  # Force fallback models

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_PORT=5002

# Database
DATABASE_URL=sqlite:///medley.db

# Redis (for sessions and caching)
REDIS_URL=redis://localhost:6379/0

# Domain (for production)
DOMAIN_NAME=localhost

# SSL Email (for Let's Encrypt)
SSL_EMAIL=admin@yourdomain.com

# Performance
MAX_PARALLEL_MODELS=10
MODEL_QUERY_TIMEOUT=60
CACHE_ENABLED=true

# Orchestrator
ORCHESTRATOR_MODEL=anthropic/claude-3-5-sonnet-20241022
ORCHESTRATOR_FALLBACK=neversleep/llama-3.1-lumimaid-70b
EOF
```

### Configuration Files

#### config/pipeline.yaml
```yaml
pipeline:
  max_parallel_queries: 10
  timeout_seconds: 60
  retry_attempts: 2
  cache_enabled: true
  
report:
  format: pdf
  include_minority_opinions: true
  max_alternatives: 10
```

#### config/models.yaml
```yaml
models:
  free_tier:
    - google/gemini-2.0-flash-exp:free
    - meta-llama/llama-3.2-3b-instruct:free
    - microsoft/phi-3-mini-128k-instruct:free
    
  orchestrator:
    primary: anthropic/claude-3-5-sonnet-20241022
    fallback: neversleep/llama-3.1-lumimaid-70b
```

---

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB
- **OS**: Linux, macOS, Windows 10+
- **Python**: 3.8+

### Recommended for Production
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: 100Mbps+

---

## Health Monitoring

### Check System Health

```bash
# Via API
curl http://localhost:5002/api/health

# Via CLI
python tests/health_check.py

# Docker health check
docker inspect medley-web | grep -A 5 Health
```

### Expected Health Response
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "checks": {
    "flask_running": true,
    "cache_directory": true,
    "reports_directory": true,
    "usecases_directory": true,
    "session_enabled": true,
    "socketio_enabled": true,
    "cached_reports": 75,
    "predefined_cases": 13
  }
}
```

---

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port
lsof -i :5002
# Kill process
kill -9 <PID>
# Or use different port
export FLASK_PORT=5003
python web_app.py
```

#### Docker Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

#### SSL Certificate Issues
```bash
# Test certificate
openssl s_client -connect yourdomain.com:443
# Renew certificate
docker-compose run --rm certbot renew
```

#### Database Locked
```bash
# Remove lock file
rm medley.db-journal
# Or use PostgreSQL in production
```

#### Out of Memory
```bash
# Increase Docker memory
# Docker Desktop > Settings > Resources > Memory: 8GB

# Or limit parallel models
export MAX_PARALLEL_MODELS=5
```

### Debug Mode

```bash
# Enable debug logging
export FLASK_ENV=development
export FLASK_DEBUG=1
export LOG_LEVEL=DEBUG

# Run with verbose output
python web_app.py --debug
```

### Log Files

```bash
# Application logs
tail -f logs/medley.log

# Docker logs
docker-compose logs -f --tail=100

# Nginx access logs
docker exec medley-nginx tail -f /var/log/nginx/access.log

# Nginx error logs
docker exec medley-nginx tail -f /var/log/nginx/error.log
```

---

## Performance Optimization

### Caching Strategy
```bash
# Enable aggressive caching
export CACHE_TTL=86400  # 24 hours
export CACHE_MAX_SIZE=1000  # Max entries

# Clear cache if needed
rm -rf cache/responses/*
```

### Database Optimization
```bash
# Use PostgreSQL for production
export DATABASE_URL=postgresql://user:pass@localhost/medley

# Enable connection pooling
export DATABASE_POOL_SIZE=10
export DATABASE_MAX_OVERFLOW=20
```

### Model Selection
```bash
# Use faster models for development
export FAST_MODE=true

# Limit models for testing
export MAX_MODELS=5
```

---

## Security Considerations

### Production Checklist
- [ ] Change SECRET_KEY from default
- [ ] Use HTTPS in production
- [ ] Set strong database password
- [ ] Enable rate limiting
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Backup database regularly

### Firewall Rules
```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (change port)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

---

## Backup and Recovery

### Backup Script
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/medley"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
cp medley.db $BACKUP_DIR/medley_$DATE.db

# Backup reports
tar -czf $BACKUP_DIR/reports_$DATE.tar.gz reports/

# Backup cache (optional)
tar -czf $BACKUP_DIR/cache_$DATE.tar.gz cache/

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

### Restore Process
```bash
# Stop application
docker-compose stop

# Restore database
cp /backups/medley/medley_20250812.db medley.db

# Restore reports
tar -xzf /backups/medley/reports_20250812.tar.gz

# Restart application
docker-compose start
```

---

## Support

For deployment issues:
- Check [GitHub Issues](https://github.com/yourusername/medley/issues)
- Review logs in `logs/` directory
- Contact: farhad.abtahi@ki.se

---

**Last Updated**: August 2025  
**Version**: 1.0.0