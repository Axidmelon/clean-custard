# Custard Backend Production Deployment Guide

This guide covers the complete production deployment setup for the Custard Backend API.

## 🚀 Quick Start

### 1. Generate Secure Configuration
```bash
# Generate production environment with secure secrets
python3 generate-env.py --env production

# Update API keys and domain settings
nano .env.production
```

### 2. Deploy to Production
```bash
# Run the automated deployment script
./deploy-production.sh
```

### 3. Verify Deployment
```bash
# Check service health
curl http://localhost:8000/health

# View service status
docker-compose -f docker-compose-production.yml ps
```

## 📁 File Structure

```
backend/
├── docker-compose-production.yml    # Production Docker Compose
├── docker-compose-monitoring.yml    # Monitoring stack
├── generate-env.py                  # Secure environment generator
├── deploy-production.sh             # Automated deployment script
├── .env.production                  # Production environment (generated)
├── monitoring/                      # Monitoring configurations
│   ├── prometheus.yml
│   ├── grafana/
│   ├── logstash/
│   └── filebeat/
└── backups/                         # Database backups
```

## 🔧 Configuration

### Environment Variables

The production configuration includes:

- **Security**: Secure secret keys, JWT tokens, database passwords
- **Database**: PostgreSQL with connection pooling and performance tuning
- **API**: CORS settings, rate limiting, logging levels
- **External Services**: OpenAI, Resend email service
- **Monitoring**: Log levels, Sentry integration
- **Backup**: Automated backup schedules

### Security Features

- ✅ Non-root container execution
- ✅ Secure secret generation
- ✅ Database connection encryption
- ✅ Rate limiting enabled
- ✅ CORS protection
- ✅ Health checks and monitoring
- ✅ Automated backups

## 🐳 Docker Services

### Core Services
- **custard-backend**: FastAPI application (port 8000)
- **postgres**: PostgreSQL database (port 5432)
- **redis**: Redis cache (port 6379)

### Optional Services
- **nginx**: Reverse proxy (ports 80, 443) - use `--profile with-nginx`
- **monitoring**: Prometheus, Grafana, ELK stack - use `--profile monitoring`

## 📊 Monitoring

### Metrics Collection
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Node Exporter**: System metrics
- **cAdvisor**: Container metrics

### Log Aggregation
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Filebeat**: Log shipping from containers

### Access URLs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Kibana: http://localhost:5601

## 🔄 Deployment Commands

### Basic Operations
```bash
# Start production services
docker-compose -f docker-compose-production.yml up -d

# Stop services
docker-compose -f docker-compose-production.yml down

# View logs
docker-compose -f docker-compose-production.yml logs -f

# Restart services
docker-compose -f docker-compose-production.yml restart
```

### With Monitoring
```bash
# Start with monitoring stack
docker-compose -f docker-compose-production.yml -f docker-compose-monitoring.yml up -d

# Start with nginx reverse proxy
docker-compose -f docker-compose-production.yml --profile with-nginx up -d
```

### Database Operations
```bash
# Run migrations
docker-compose -f docker-compose-production.yml exec custard-backend alembic upgrade head

# Backup database
docker-compose -f docker-compose-production.yml exec postgres pg_dump -U custard custard_db > backup.sql

# Restore database
docker-compose -f docker-compose-production.yml exec -T postgres psql -U custard custard_db < backup.sql
```

## 🛡️ Security Checklist

### Before Production
- [ ] Update all API keys in `.env.production`
- [ ] Configure proper `ALLOWED_ORIGINS` and `FRONTEND_URL`
- [ ] Set up SSL/TLS certificates for nginx
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Configure backup retention policies
- [ ] Set up monitoring alerts

### Ongoing Security
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Regular backup testing
- [ ] Access log review
- [ ] Dependency vulnerability scanning

## 📈 Performance Tuning

### Database Optimization
- Connection pooling configured
- Query optimization indexes
- Memory settings tuned for production
- Backup compression enabled

### Application Optimization
- Multi-stage Docker builds
- Health checks configured
- Resource limits set
- Logging optimized

## 🔍 Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   # Check logs
   docker-compose -f docker-compose-production.yml logs
   
   # Check environment file
   cat .env.production
   ```

2. **Database connection issues**
   ```bash
   # Test database connection
   docker-compose -f docker-compose-production.yml exec postgres psql -U custard -d custard_db -c "SELECT 1;"
   ```

3. **API not responding**
   ```bash
   # Check health endpoint
   curl -v http://localhost:8000/health
   
   # Check container status
   docker-compose -f docker-compose-production.yml ps
   ```

### Log Locations
- Application logs: `./logs/`
- Database logs: `docker-compose logs postgres`
- Container logs: `docker-compose logs [service-name]`

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review container logs
3. Check the monitoring dashboards
4. Consult the main project documentation

## 🔄 Updates

To update the deployment:
1. Pull latest changes
2. Rebuild images: `docker-compose -f docker-compose-production.yml build --no-cache`
3. Run deployment script: `./deploy-production.sh`

---

**⚠️ Important**: This is a production-ready configuration. Always test in a staging environment first and ensure you have proper backups before deploying to production.
