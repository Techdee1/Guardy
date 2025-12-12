# Render.com Deployment Guide

This guide walks you through deploying the Guardy AI Microservice to Render.com.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Methods](#deployment-methods)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Redis Setup](#redis-setup)
- [Custom Domains](#custom-domains)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

## Prerequisites

1. **Render.com Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code must be in a GitHub repository
3. **Docker Support**: Render supports Dockerfile-based deployments
4. **Payment Method**: Add payment method for paid plans (free tier available)

### Verify Local Setup

```bash
# Ensure your code is in git
cd /workspaces/Guardy/ai-microservice
git status

# Ensure Dockerfile exists
ls -la Dockerfile

# Ensure render.yaml exists
ls -la render.yaml
```

## Quick Start

### Method 1: Deploy via Render Blueprint (Recommended)

This method uses the `render.yaml` file to automatically provision all services.

1. **Push Code to GitHub**

```bash
cd /workspaces/Guardy
git add .
git commit -m "Add Render deployment configuration"
git push origin master
```

2. **Create New Blueprint in Render**

   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click **"New +"** → **"Blueprint"**
   - Connect your GitHub repository
   - Select the repository: `HenryTech12/Guardy`
   - Render will detect `render.yaml` automatically
   - Click **"Apply"**

3. **Configure Secrets**

   After blueprint creation, add sensitive environment variables:
   
   - Go to **guardy-ai-api** service
   - Click **"Environment"** tab
   - Add:
     - `SECRET_KEY`: Generate with `openssl rand -hex 32`
     - `API_KEY`: Your API authentication key (optional)

4. **Wait for Deployment**

   - Render will:
     - Create PostgreSQL database (guardy-db)
     - Create Redis instance (guardy-redis)
     - Build Docker image for API
     - Deploy the API service
   - Initial deployment takes 5-10 minutes

5. **Verify Deployment**

```bash
# Get your Render URL (e.g., https://guardy-ai-api.onrender.com)
curl https://guardy-ai-api.onrender.com/api/v1/models/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-12-12T10:30:00Z",
#   "models": {...}
# }
```

### Method 2: Manual Service Creation

If you prefer manual setup without Blueprint:

#### 1. Create PostgreSQL Database

1. Dashboard → **"New +"** → **"PostgreSQL"**
2. Configure:
   - Name: `guardy-db`
   - Database: `guardy`
   - User: `guardy`
   - Region: `Oregon`
   - Plan: `Starter` (free)
3. Click **"Create Database"**
4. Save the connection details (displayed after creation)

#### 2. Create Redis Instance

1. Dashboard → **"New +"** → **"Redis"**
2. Configure:
   - Name: `guardy-redis`
   - Region: `Oregon`
   - Plan: `Starter` (free, 25MB)
   - Maxmemory Policy: `allkeys-lru`
3. Click **"Create Redis"**
4. Save the connection string

#### 3. Create Web Service

1. Dashboard → **"New +"** → **"Web Service"**
2. Connect GitHub repository: `HenryTech12/Guardy`
3. Configure:
   - Name: `guardy-ai-api`
   - Region: `Oregon`
   - Branch: `master`
   - Root Directory: `ai-microservice`
   - Runtime: **Docker**
   - Dockerfile Path: `./Dockerfile`
   - Docker Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4`
   - Plan: `Starter` (free) or `Standard` ($7/month)
4. Add Environment Variables (see [Environment Variables](#environment-variables) section)
5. Add Disk:
   - Name: `guardy-models`
   - Mount Path: `/app/models`
   - Size: `10 GB`
6. Click **"Create Web Service"**

## Deployment Methods

### Automatic Deployment (Recommended)

Render supports automatic deployments on git push:

1. **Enable Auto-Deploy**
   - Service Settings → **"Build & Deploy"**
   - Enable **"Auto-Deploy"**
   - Select branch: `master`

2. **Deploy Triggers**
   - Automatic: Every push to `master` branch
   - Manual: Click **"Manual Deploy"** → **"Deploy latest commit"**

### Manual Deployment

```bash
# Push changes to GitHub
git add .
git commit -m "Update API endpoint"
git push origin master

# Render will auto-deploy if enabled
# Or go to Dashboard → Service → "Manual Deploy" → "Deploy latest commit"
```

### Deployment via CLI (Render CLI)

```bash
# Install Render CLI (optional)
npm install -g @render/cli

# Login
render login

# Deploy
render deploy --service guardy-ai-api
```

## Configuration

### render.yaml Structure

The `render.yaml` file defines three main components:

```yaml
services:
  - type: web               # API web service
    name: guardy-ai-api
    runtime: docker
    # ... configuration

databases:
  - name: guardy-db         # PostgreSQL database
    databaseName: guardy
    # ... configuration

  - name: guardy-redis      # Redis cache
    plan: starter
    # ... configuration
```

### Service Configuration Options

**Web Service Plans:**
- **Starter**: Free (512MB RAM, 0.1 CPU, sleeps after 15min inactivity)
- **Standard**: $7/month (512MB RAM, 0.5 CPU, always on)
- **Pro**: $25/month (2GB RAM, 1 CPU)
- **Pro Plus**: $85/month (4GB RAM, 2 CPU)

**Database Plans:**
- **Starter**: Free (1GB storage, 97 connections)
- **Standard**: $7/month (10GB storage, 97 connections)
- **Pro**: $20/month (50GB storage, 197 connections)

**Redis Plans:**
- **Starter**: Free (25MB, no persistence)
- **Standard**: $10/month (256MB, persistence)
- **Pro**: $50/month (1GB, persistence, high availability)

### Regions

Available regions:
- **Oregon** (us-west): Best for US West Coast
- **Frankfurt** (eu-central): Best for Europe
- **Singapore** (asia-southeast): Best for Asia

## Environment Variables

### Required Variables

These are automatically populated via `render.yaml`:

```bash
# Application
APP_NAME=Guardy AI Microservice
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Database (auto-populated from database service)
DATABASE_URL=postgresql://user:pass@host:port/dbname
DB_HOST=<auto>
DB_PORT=<auto>
DB_NAME=<auto>
DB_USER=<auto>
DB_PASSWORD=<auto>

# Redis (auto-populated from Redis service)
REDIS_URL=redis://default:password@host:port
REDIS_HOST=<auto>
REDIS_PORT=<auto>
REDIS_PASSWORD=<auto>
CACHE_ENABLED=true

# Cache TTL (seconds)
CACHE_TTL_FLOOD_RISK=300
CACHE_TTL_NOWCAST=600
CACHE_TTL_ANOMALY=60
CACHE_TTL_BATCH=180
CACHE_TTL_EVACUATION=900

# Performance
MAX_BATCH_SIZE=100
WORKER_THREADS=4
REQUEST_TIMEOUT=30
ENABLE_MODEL_WARMUP=true
ENABLE_PROFILING=false

# CORS
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=true
```

### Manual Secrets (Set via Dashboard)

**CRITICAL**: Set these manually in Render Dashboard for security:

1. **SECRET_KEY**: Application secret key
   ```bash
   # Generate locally
   openssl rand -hex 32
   
   # Add to Render Dashboard:
   # Service → Environment → Add Environment Variable
   # Key: SECRET_KEY
   # Value: <your_generated_key>
   ```

2. **API_KEY**: Optional API authentication key
   ```bash
   # Generate if needed
   openssl rand -hex 16
   
   # Add to Render Dashboard
   # Key: API_KEY
   # Value: <your_api_key>
   ```

### Environment Groups (Optional)

For managing shared variables across multiple services:

1. Dashboard → **"Environment Groups"** → **"New Environment Group"**
2. Name: `guardy-shared-config`
3. Add common variables:
   - `LOG_LEVEL=INFO`
   - `ENVIRONMENT=production`
   - `CORS_ORIGINS=*`
4. Link to services via render.yaml:
   ```yaml
   services:
     - type: web
       name: guardy-ai-api
       envVarGroups:
         - guardy-shared-config
   ```

## Database Setup

### Initial Database Schema

After PostgreSQL is created, initialize the schema:

```bash
# Option 1: Connect via psql (get connection string from Render Dashboard)
psql postgresql://user:pass@host:port/guardy

# Run schema creation
\i /path/to/database/sensor_tables.sql
```

### Database Migrations with Alembic

```bash
# Install alembic
pip install alembic

# Initialize alembic
alembic init alembic

# Edit alembic.ini - set sqlalchemy.url to your DATABASE_URL
# (Get from Render Dashboard → guardy-db → Connection Details)

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### Database Backups

Render provides automatic daily backups for paid plans:

1. Dashboard → **guardy-db** → **"Backups"**
2. View automatic backups (7-day retention)
3. Manual backup:
   ```bash
   # Click "Create Backup" button
   # Or via CLI:
   render backup create --database guardy-db
   ```

### Database Restore

```bash
# Via Dashboard
# guardy-db → Backups → Select backup → "Restore"

# Via CLI
render backup restore --database guardy-db --backup <backup-id>
```

## Redis Setup

### Redis Configuration

Redis is configured in `render.yaml` with:

```yaml
- name: guardy-redis
  plan: starter
  maxmemoryPolicy: allkeys-lru  # Evict oldest keys when memory full
```

### Redis Persistence

- **Starter Plan**: No persistence (data lost on restart)
- **Standard/Pro Plans**: Persistence enabled (RDB + AOF)

For production, use Standard or Pro plan for data persistence.

### Redis CLI Access

```bash
# Get Redis URL from Dashboard → guardy-redis → Info
redis-cli -u redis://default:password@host:port

# Test connection
> PING
PONG

# View keys
> KEYS flood_risk:*

# View cache stats
> INFO stats

# Clear cache
> FLUSHDB
```

## Custom Domains

### Add Custom Domain

1. Dashboard → **guardy-ai-api** → **"Settings"** → **"Custom Domains"**
2. Click **"Add Custom Domain"**
3. Enter your domain: `api.guardy.com`
4. Render provides DNS records:
   ```
   Type: CNAME
   Name: api
   Value: guardy-ai-api.onrender.com
   ```
5. Add DNS records to your domain provider (e.g., Cloudflare, Namecheap)
6. Wait for DNS propagation (5-60 minutes)
7. Render will automatically provision SSL certificate (Let's Encrypt)

### SSL/TLS

- **Automatic SSL**: Render provides free SSL certificates via Let's Encrypt
- **Custom SSL**: Upload your own certificate (Pro plans only)
- **Force HTTPS**: Enabled by default

## Monitoring

### Built-in Monitoring

Render provides:

1. **Metrics Dashboard**
   - Service → **"Metrics"**
   - CPU usage, Memory usage, Request rate, Response times

2. **Logs**
   - Service → **"Logs"**
   - Real-time log streaming
   - Filter by log level
   - Download logs

3. **Events**
   - Service → **"Events"**
   - Deployment history
   - Health check failures
   - Auto-scaling events

### External Monitoring

Integrate with external services:

1. **Sentry** (Error Tracking)
   ```bash
   # Add to requirements.txt
   sentry-sdk==1.40.0
   
   # Add environment variable
   SENTRY_DSN=https://xxx@sentry.io/yyy
   ```

2. **Datadog** (APM)
   ```bash
   # Add to requirements.txt
   ddtrace
   
   # Modify Docker command in render.yaml
   dockerCommand: ddtrace-run uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
   ```

3. **New Relic** (APM)
   ```bash
   # Add to requirements.txt
   newrelic
   
   # Add environment variable
   NEW_RELIC_LICENSE_KEY=xxx
   ```

### Health Checks

Configure health checks in render.yaml:

```yaml
services:
  - type: web
    healthCheckPath: /api/v1/models/health
```

Health check behavior:
- **Interval**: Every 30 seconds
- **Timeout**: 5 seconds
- **Unhealthy threshold**: 3 consecutive failures
- **Action on failure**: Restart service

### Uptime Monitoring

Use external uptime monitors:

1. **UptimeRobot** (Free)
   - Monitor: `https://guardy-ai-api.onrender.com/api/v1/models/health`
   - Interval: 5 minutes
   - Alerts: Email, Slack, SMS

2. **Pingdom** (Paid)
   - More advanced monitoring
   - Multiple locations
   - Performance reports

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

**Symptoms**: Service status shows "Deploy failed"

**Solutions**:
```bash
# Check build logs
# Dashboard → Service → Logs → Filter by "build"

# Common causes:
# - Docker build errors
# - Missing dependencies
# - Invalid Dockerfile

# Test locally
docker build -t guardy-ai .
docker run -p 8000:8000 guardy-ai
```

#### 2. Database Connection Errors

**Symptoms**: `OperationalError: could not connect to server`

**Solutions**:
```bash
# Verify DATABASE_URL is set correctly
# Dashboard → guardy-ai-api → Environment

# Check database is running
# Dashboard → guardy-db → Status should be "Available"

# Verify IP allowlist
# Dashboard → guardy-db → Access Control
# Ensure allowlist is empty or includes Render IPs

# Test connection
psql $DATABASE_URL
```

#### 3. Redis Connection Errors

**Symptoms**: `ConnectionError: Error connecting to Redis`

**Solutions**:
```bash
# Check Redis service status
# Dashboard → guardy-redis → Status should be "Available"

# Verify REDIS_URL is set
# Dashboard → guardy-ai-api → Environment

# Check Redis plan
# Starter plan may have connection limits

# Test connection
redis-cli -u $REDIS_URL ping
```

#### 4. Models Not Loading

**Symptoms**: `FileNotFoundError: models/nowcast_lstm_v1.h5`

**Solutions**:
```bash
# Ensure disk is mounted
# Dashboard → guardy-ai-api → Disks
# Mount path should be /app/models

# Upload model files
# Option 1: SSH into service
render ssh guardy-ai-api
cd /app/models
# Upload via scp or git-lfs

# Option 2: Store models in cloud (S3, GCS)
# Download during container startup
```

#### 5. High Memory Usage

**Symptoms**: Service keeps restarting, OOM errors

**Solutions**:
```bash
# Check memory usage
# Dashboard → guardy-ai-api → Metrics

# Optimize:
# 1. Reduce WORKER_THREADS in environment
WORKER_THREADS=2

# 2. Disable model warmup
ENABLE_MODEL_WARMUP=false

# 3. Upgrade to higher plan
# Standard: 512MB → Pro: 2GB

# 4. Implement model lazy loading
# Load models only when needed, not on startup
```

#### 6. Slow Response Times

**Symptoms**: API requests timeout or are very slow

**Solutions**:
```bash
# Check metrics
# Dashboard → guardy-ai-api → Metrics → Response times

# Causes:
# 1. Free tier sleeps after 15min inactivity
#    Solution: Upgrade to Standard plan ($7/month)

# 2. Cold start (Docker image loading)
#    Solution: Keep service warm with uptime monitor

# 3. Redis not enabled
#    Solution: Verify CACHE_ENABLED=true

# 4. Database query slowness
#    Solution: Add indexes, optimize queries

# Enable profiling temporarily
ENABLE_PROFILING=true
```

#### 7. Deployment Stuck

**Symptoms**: Deployment shows "In progress" for >10 minutes

**Solutions**:
```bash
# Check build logs for errors
# Dashboard → Service → Logs

# Common causes:
# - Large Docker image (optimize with multi-stage builds)
# - Slow pip install (use --no-cache-dir)
# - Network issues (retry deployment)

# Cancel and retry
# Dashboard → Service → "Cancel Build" → "Manual Deploy"
```

### Support Resources

1. **Render Status**: [status.render.com](https://status.render.com)
2. **Documentation**: [render.com/docs](https://render.com/docs)
3. **Community**: [community.render.com](https://community.render.com)
4. **Support**: support@render.com (paid plans)

## Cost Optimization

### Free Tier Limits

Render provides generous free tier:

- **Web Service**: 1 free instance (sleeps after 15min inactivity)
- **PostgreSQL**: 1 free database (1GB storage, expires after 90 days)
- **Redis**: 1 free instance (25MB, no persistence)
- **Build minutes**: 500 minutes/month
- **Bandwidth**: 100GB/month

### Tips to Minimize Costs

1. **Use Free Tier for Development**
   ```yaml
   # render.yaml for dev
   services:
     - type: web
       plan: starter  # Free
   databases:
     - name: guardy-db
       plan: starter  # Free
     - name: guardy-redis
       plan: starter  # Free
   ```

2. **Upgrade Only Production**
   ```yaml
   # render.yaml for production
   services:
     - type: web
       plan: standard  # $7/month
   databases:
     - name: guardy-db
       plan: standard  # $7/month
     - name: guardy-redis
       plan: standard  # $10/month
   # Total: $24/month
   ```

3. **Use Environment Variables for Branch-based Plans**
   ```bash
   # Set plan based on branch
   # master branch: standard plan
   # develop branch: starter (free) plan
   ```

4. **Optimize Resource Usage**
   - Reduce `numInstances` (use 1 for dev/staging)
   - Reduce `WORKER_THREADS` (use 2 instead of 4)
   - Disable `ENABLE_MODEL_WARMUP` for dev
   - Use smaller disk sizes (10GB vs 50GB)

5. **Suspend Unused Services**
   ```bash
   # Dashboard → Service → Settings → "Suspend Service"
   # No charges while suspended
   # Resume when needed
   ```

### Estimated Costs

**Development Environment (Free Tier)**:
- Web Service: $0
- PostgreSQL: $0
- Redis: $0
- **Total: $0/month**

**Production Environment (Recommended)**:
- Web Service (Standard): $7/month
- PostgreSQL (Standard): $7/month
- Redis (Standard): $10/month
- **Total: $24/month**

**Production Environment (High Performance)**:
- Web Service (Pro): $25/month
- PostgreSQL (Pro): $20/month
- Redis (Pro): $50/month
- **Total: $95/month**

## Next Steps

1. ✅ Deploy to Render using Blueprint
2. ⏭️ Set up monitoring (Sentry, Datadog)
3. ⏭️ Configure custom domain
4. ⏭️ Set up CI/CD with GitHub Actions
5. ⏭️ Implement database backups
6. ⏭️ Add uptime monitoring

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Render Blog](https://render.com/blog)
- [Docker Deployment Guide](./DOCKER_GUIDE.md)
- [API Documentation](../README.md)
- [Performance Optimization](./PERFORMANCE_OPTIMIZATION.md)
