# Custard Backend Docker Setup

This directory contains Docker configuration for the Custard Backend API service.

## Quick Start

### Development Environment

1. **Copy environment template:**
   ```bash
   cp env.template .env
   ```

2. **Update environment variables:**
   Edit `.env` file with your actual API keys and configuration.

3. **Start development environment:**
   ```bash
   docker-compose -f docker-compose-backend.yml up --build
   ```

4. **Access the API:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Production Deployment

1. **Build production image:**
   ```bash
   docker build -t custard-backend:latest --target production .
   ```

2. **Run production container:**
   ```bash
   docker run -d \
     --name custard-backend \
     -p 8000:8000 \
     --env-file .env \
     custard-backend:latest
   ```

## Docker Images

### Multi-Stage Build

The Dockerfile uses a multi-stage build process:

1. **Builder Stage**: Installs build dependencies and creates virtual environment
2. **Production Stage**: Creates optimized production image
3. **Development Stage**: Adds development tools and auto-reload

### Image Sizes

- **Production**: ~200MB (optimized for production)
- **Development**: ~300MB (includes dev tools)

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key (min 32 chars) | `your-super-secret-key-32-chars-min` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `RESEND_API_KEY` | Resend email service key | `re_...` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `ENVIRONMENT` | `development` | Environment (development/staging/production) |
| `DEBUG` | `false` | Debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SENTRY_DSN` | - | Sentry error tracking |

## Docker Compose Services

### Development Stack

- **custard-backend**: FastAPI application with auto-reload
- **postgres**: PostgreSQL 15 database
- **redis**: Redis 7 for caching and rate limiting

### Production Stack

Uncomment the production service in `docker-compose-backend.yml` for production deployment.

## Health Checks

The container includes built-in health checks:

```bash
# Check container health
docker ps

# View health check logs
docker inspect custard-backend | grep -A 10 Health
```

## Security Features

- **Non-root user**: Runs as `custard` user
- **Minimal attack surface**: Only necessary packages installed
- **Security headers**: CORS and security middleware configured
- **Environment validation**: Pydantic settings validation

## Monitoring

### Health Endpoints

- `GET /health` - Basic health check
- `GET /status` - Detailed system status
- `GET /production-readiness` - Production readiness validation

### Logs

```bash
# View application logs
docker logs custard-backend

# Follow logs in real-time
docker logs -f custard-backend

# View logs with timestamps
docker logs -t custard-backend
```

## Database Migrations

Run Alembic migrations:

```bash
# Inside container
docker exec custard-backend alembic upgrade head

# Or with docker-compose
docker-compose -f docker-compose-backend.yml exec custard-backend alembic upgrade head
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Change port in docker-compose-backend.yml
   ports:
     - "8001:8000"  # Use different host port
   ```

2. **Database connection failed:**
   - Check `DATABASE_URL` in `.env`
   - Ensure PostgreSQL container is running
   - Verify network connectivity

3. **Permission denied:**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

4. **Build failures:**
   ```bash
   # Clean build
   docker-compose -f docker-compose-backend.yml down
   docker system prune -f
   docker-compose -f docker-compose-backend.yml up --build
   ```

### Debug Mode

Enable debug mode for detailed error messages:

```bash
# Set in .env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Performance Optimization

### Production Optimizations

1. **Use production target:**
   ```bash
   docker build --target production .
   ```

2. **Enable Redis caching:**
   ```bash
   RATE_LIMIT_REDIS_URL=redis://redis:6379
   ```

3. **Configure database pooling:**
   ```bash
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=30
   ```

### Resource Limits

Add resource limits in production:

```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

## Backup and Recovery

### Database Backups

```bash
# Backup database
docker exec postgres pg_dump -U custard custard_db > backup.sql

# Restore database
docker exec -i postgres psql -U custard custard_db < backup.sql
```

### Application Backups

```bash
# Backup application data
docker cp custard-backend:/app/logs ./backup-logs
docker cp custard-backend:/app/backups ./backup-data
```

## Scaling

### Horizontal Scaling

```yaml
# Scale backend service
docker-compose -f docker-compose-backend.yml up --scale custard-backend=3
```

### Load Balancing

Use nginx or similar load balancer for multiple backend instances.

## Security Checklist

- [ ] Change default `SECRET_KEY`
- [ ] Use strong database passwords
- [ ] Configure `ALLOWED_ORIGINS` for production
- [ ] Enable HTTPS in production
- [ ] Set up Sentry monitoring
- [ ] Configure rate limiting
- [ ] Regular security updates
- [ ] Network segmentation
- [ ] Backup strategy

## Support

For issues and questions:

1. Check the logs: `docker logs custard-backend`
2. Verify environment variables
3. Check network connectivity
4. Review the main README.md
5. Check GitHub issues
