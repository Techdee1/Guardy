# Docker Deployment Guide

Complete guide for containerizing and deploying the Guardy AI Microservice using Docker and Docker Compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Docker Images](#docker-images)
4. [Docker Compose](#docker-compose)
5. [Environment Configuration](#environment-configuration)
6. [Development Workflow](#development-workflow)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git**: For cloning repository

### Verify Installation

```bash
docker --version          # Docker version 20.10.0+
docker-compose --version  # Docker Compose version 2.0.0+
```

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/HenryTech12/Guardy.git
cd Guardy/ai-microservice
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
nano .env
```

### 3. Start Services

```bash
# Production mode
docker-compose up -d

# Development mode (with hot reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 4. Verify Deployment

```bash
# Check service health
curl http://localhost:8000/api/v1/models/health

# View logs
docker-compose logs -f api

# Check running containers
docker-compose ps
```

### 5. Access Services

- **API Documentation**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/api/v1/models/health
- **Redis Commander** (dev): http://localhost:8081
- **pgAdmin** (dev): http://localhost:5050

---

## Docker Images

### Multi-Stage Build

The Dockerfile uses multi-stage builds for optimization:

1. **base**: Base Python image with system dependencies
2. **dependencies**: Python package installation
3. **production**: Minimal production image
4. **development**: Development image with extra tools

### Build Production Image

```bash
docker build -t guardy-ai:latest .
```

### Build Development Image

```bash
docker build -t guardy-ai:dev --target development .
```

### Image Sizes

- **Production**: ~800MB (optimized)
- **Development**: ~950MB (includes dev tools)
- **Base Python**: ~150MB

### Push to Registry

```bash
# Tag for registry
docker tag guardy-ai:latest your-registry.com/guardy-ai:latest

# Push to registry
docker push your-registry.com/guardy-ai:latest
```

---

## Docker Compose

### Services Overview

| Service | Port | Description |
|---------|------|-------------|
| **api** | 8000 | FastAPI application |
| **redis** | 6379 | Cache layer |
| **postgres** | 5432 | Database |
| **nginx** | 80, 443 | Reverse proxy (production) |
| **pgadmin** | 5050 | Database admin (dev only) |
| **redis-commander** | 8081 | Cache admin (dev only) |

### Start All Services

```bash
# Start in background
docker-compose up -d

# Start with logs
docker-compose up

# Start specific service
docker-compose up -d redis postgres
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v

# Stop specific service
docker-compose stop api
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Scale Services

```bash
# Scale API to 3 instances
docker-compose up -d --scale api=3

# Note: Requires load balancer (nginx) for proper distribution
```

---

## Environment Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

### Key Variables

**Application:**
```env
APP_NAME="Guardy AI Microservice"
LOG_LEVEL="INFO"
DEBUG=false
```

**Database:**
```env
DB_HOST="postgres"
DB_PORT=5432
DB_NAME="floodguard"
DB_USER="floodguard_user"
DB_PASSWORD="secure_password_here"
```

**Redis:**
```env
REDIS_HOST="redis"
REDIS_PORT=6379
REDIS_ENABLED=true
```

**Performance:**
```env
MAX_BATCH_SIZE=100
WORKER_THREADS=4
CACHE_TTL_FLOOD_RISK=300
```

### Secrets Management

For production, use Docker secrets or external secret managers:

```bash
# Docker Swarm secrets
echo "my_db_password" | docker secret create db_password -

# Kubernetes secrets
kubectl create secret generic guardy-secrets \
  --from-literal=db-password='my_password'
```

---

## Development Workflow

### Development Mode

Start with development configuration:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Features:**
- Hot reload on code changes
- Development tools installed
- Source code mounted as volume
- Debug port exposed (5678)
- pgAdmin and Redis Commander included

### Execute Commands in Container

```bash
# Run shell in API container
docker-compose exec api bash

# Run Python script
docker-compose exec api python scripts/train_risk_scorer.py

# Run tests
docker-compose exec api pytest tests/

# Check Python version
docker-compose exec api python --version
```

### Database Operations

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U floodguard_user -d floodguard

# Run SQL file
docker-compose exec -T postgres psql -U floodguard_user -d floodguard < database/sensor_tables.sql

# Backup database
docker-compose exec -T postgres pg_dump -U floodguard_user floodguard > backup.sql

# Restore database
docker-compose exec -T postgres psql -U floodguard_user floodguard < backup.sql
```

### Redis Operations

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Check cache statistics
docker-compose exec redis redis-cli INFO stats

# Clear all cache
docker-compose exec redis redis-cli FLUSHALL

# Monitor commands
docker-compose exec redis redis-cli MONITOR
```

### Rebuild After Changes

```bash
# Rebuild specific service
docker-compose build api

# Rebuild and restart
docker-compose up -d --build api

# Force rebuild (no cache)
docker-compose build --no-cache api
```

---

## Production Deployment

### Production Checklist

- [ ] Update `.env` with production values
- [ ] Set `DEBUG=false`
- [ ] Configure strong database passwords
- [ ] Enable Redis password authentication
- [ ] Set up SSL certificates for HTTPS
- [ ] Configure firewall rules
- [ ] Set resource limits
- [ ] Enable logging and monitoring
- [ ] Configure backups
- [ ] Test health checks

### Production Deployment

```bash
# Pull latest images
docker-compose pull

# Start in production mode
docker-compose up -d

# With nginx reverse proxy
docker-compose --profile production up -d
```

### Resource Limits

Configure in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### SSL/TLS Configuration

1. **Obtain SSL certificates** (Let's Encrypt recommended):
   ```bash
   certbot certonly --standalone -d your-domain.com
   ```

2. **Copy certificates to nginx/ssl/:**
   ```bash
   cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
   cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
   ```

3. **Update nginx.conf** (uncomment HTTPS server block)

4. **Restart nginx:**
   ```bash
   docker-compose restart nginx
   ```

### Health Monitoring

```bash
# Check service health
docker-compose ps

# API health endpoint
curl http://localhost:8000/api/v1/models/health

# Docker health status
docker inspect guardy-api --format='{{.State.Health.Status}}'
```

### Automated Deployment

**Using Docker Swarm:**
```bash
docker stack deploy -c docker-compose.yml guardy
```

**Using Kubernetes:**
```bash
# Convert docker-compose to k8s manifests
kompose convert -f docker-compose.yml

# Apply to cluster
kubectl apply -f .
```

---

## Troubleshooting

### Common Issues

#### 1. Models Not Loading

**Symptoms**: `503 Service Unavailable`, "Models not loaded"

**Solutions**:
```bash
# Check if models directory is mounted
docker-compose exec api ls -la /app/models

# Check logs
docker-compose logs api | grep "Loading ML models"

# Verify model files exist
docker-compose exec api ls -lh /app/models/*.pkl /app/models/*.h5
```

#### 2. Redis Connection Failed

**Symptoms**: "Redis connection failed", cache disabled

**Solutions**:
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec api redis-cli -h redis ping

# Check Redis logs
docker-compose logs redis
```

#### 3. Database Connection Error

**Symptoms**: "Could not connect to database"

**Solutions**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Verify credentials
docker-compose exec postgres psql -U floodguard_user -d floodguard

# Check logs
docker-compose logs postgres
```

#### 4. Port Already in Use

**Symptoms**: "Bind for 0.0.0.0:8000 failed: port is already allocated"

**Solutions**:
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

#### 5. Container Keeps Restarting

**Symptoms**: Container exits immediately, restart loop

**Solutions**:
```bash
# Check exit code
docker-compose ps

# View full logs
docker-compose logs --tail=100 api

# Run container with shell
docker-compose run --rm api bash

# Disable restart policy temporarily
restart: "no"
```

### Performance Issues

#### High Memory Usage

```bash
# Check memory usage
docker stats

# Limit memory in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
```

#### Slow Response Times

```bash
# Check API metrics
curl http://localhost:8000/api/v1/metrics/performance

# Profile inside container
docker-compose exec api python scripts/profile_memory.py

# Check Redis cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace
```

### Logs and Debugging

```bash
# Export logs to file
docker-compose logs > guardy-logs.txt

# Follow logs with timestamps
docker-compose logs -f -t api

# Debug mode (development)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Inspect container
docker inspect guardy-api

# Check environment variables
docker-compose exec api env
```

---

## Best Practices

### 1. Use Multi-Stage Builds

Reduces image size and improves security:
```dockerfile
FROM python:3.12-slim as base
# ...build stages...
FROM base as production
```

### 2. Non-Root User

Run containers as non-root:
```dockerfile
USER floodguard
```

### 3. Health Checks

Ensure services are healthy:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 4. Volume Management

Persist data and separate concerns:
```yaml
volumes:
  - ./models:/app/models:ro        # Read-only models
  - ./logs:/app/logs               # Writable logs
  - postgres_data:/var/lib/postgresql/data  # Named volume
```

### 5. Environment Variables

Use .env files and secrets:
```yaml
env_file:
  - .env
```

### 6. Resource Limits

Prevent resource exhaustion:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

### 7. Logging

Centralize logs:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 8. Networks

Isolate services:
```yaml
networks:
  guardy-network:
    driver: bridge
```

---

## Next Steps

1. **Configure CI/CD**: Set up automated builds and deployments
2. **Monitoring**: Add Prometheus and Grafana (Task 14)
3. **Scaling**: Deploy to Kubernetes or Docker Swarm
4. **Backups**: Automate database and model backups
5. **Logging**: Configure centralized logging (ELK stack)

---

**Last Updated**: December 12, 2024  
**Version**: 1.0.0  
**Docker Version**: 20.10+  
**Docker Compose Version**: 2.0+
