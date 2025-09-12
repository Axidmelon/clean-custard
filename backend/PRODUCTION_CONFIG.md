# Production Configuration Guide

## Environment Variables for Production

Set these environment variables in your production deployment (Railway, Docker, etc.):

### Security Configuration
```bash
SECRET_KEY=your-super-secure-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Database Configuration
```bash
DATABASE_URL=postgresql://username:password@host:port/database
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
```

### API Configuration
```bash
HOST=0.0.0.0
PORT=8000
RELOAD=false
ENVIRONMENT=production
DEBUG=false
ENABLE_DOCS=false
LOG_LEVEL=INFO
```

### CORS Configuration
```bash
ALLOWED_ORIGINS=https://your-frontend.railway.app,https://yourdomain.com
FRONTEND_URL=https://your-frontend.railway.app
BACKEND_URL=https://your-backend.railway.app
```

### External Services
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.1

RESEND_API_KEY=re_your-resend-api-key-here
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Custard AI
```

### Monitoring & Logging
```bash
SENTRY_DSN=https://your-sentry-dsn-here@sentry.io/project-id
```

### WebSocket Configuration
```bash
WS_HEARTBEAT_INTERVAL=30
WS_CONNECTION_TIMEOUT=300
```

### Rate Limiting
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_URL=redis://redis:6379/0
```

### Production Security
```bash
MAX_REQUEST_SIZE=16777216
REQUEST_TIMEOUT=30
KEEP_ALIVE_TIMEOUT=5
```

## Production Features Enabled

### Security
- ✅ Security headers (HSTS, CSP, X-Frame-Options, etc.)
- ✅ Trusted host middleware
- ✅ CORS configuration
- ✅ Request size limits
- ✅ Input validation

### Performance
- ✅ Gzip compression
- ✅ Database connection pooling
- ✅ Request timing middleware
- ✅ Optimized Docker configuration
- ✅ Multi-worker setup

### Monitoring
- ✅ Enhanced health checks
- ✅ Metrics endpoint (`/metrics`)
- ✅ Production logging
- ✅ Error tracking (Sentry ready)
- ✅ Database pool monitoring

### Reliability
- ✅ Graceful shutdown
- ✅ Database connection validation
- ✅ WebSocket connection management
- ✅ Error handling and recovery

## Deployment Checklist

- [ ] Set all environment variables
- [ ] Configure CORS origins
- [ ] Set up database
- [ ] Configure external services (OpenAI, Resend)
- [ ] Set up monitoring (Sentry)
- [ ] Test health endpoints
- [ ] Verify security headers
- [ ] Test WebSocket connections
- [ ] Run production readiness check (`/production-readiness`)

## Health Check Endpoints

- `GET /health` - Basic health check
- `GET /ready` - Kubernetes readiness probe
- `GET /metrics` - Application metrics
- `GET /production-readiness` - Production validation

## Security Considerations

1. **Never commit secrets** to version control
2. **Use HTTPS** in production
3. **Configure CORS** with specific origins
4. **Set up monitoring** and alerting
5. **Regular security updates** of dependencies
6. **Database access** should be restricted
7. **Log sensitive operations** for audit trails
