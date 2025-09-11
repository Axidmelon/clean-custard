# Railway Deployment Guide for Custard Backend

This guide covers deploying the Custard Backend to Railway with SSL and monitoring.

## 🚀 **Quick Railway Deployment**

### **1. Prepare for Railway**

Railway will handle SSL automatically, so we can simplify the setup:

```bash
# Railway handles reverse proxy and SSL automatically
# Updated requirements.txt includes all necessary dependencies
# Single Dockerfile for production deployment
# Uses docker-compose.railway.yml for Railway-specific configuration
```

### **📋 Pre-Deployment Checklist**

- ✅ **requirements.txt** - Updated with all dependencies including gunicorn
- ✅ **Dockerfile** - Single production Dockerfile optimized for Railway
- ✅ **docker-compose.railway.yml** - Railway-specific compose configuration

### **2. Railway-Specific Docker Compose**

Use the existing Railway-optimized version:

```yaml
# docker-compose.railway.yml
version: '3.8'

services:
  custard-backend:
    build:
      context: .
      dockerfile: Dockerfile.production
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - ENABLE_DOCS=false
      - LOG_LEVEL=INFO
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - RESEND_API_KEY=${RESEND_API_KEY}
      - FROM_EMAIL=${FROM_EMAIL}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
      - FRONTEND_URL=${FRONTEND_URL}
      - SENTRY_DSN=${SENTRY_DSN}
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-custard_db}
      - POSTGRES_USER=${POSTGRES_USER:-custard}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-custard} -d ${POSTGRES_DB:-custard_db}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  postgres_data:
  redis_data:
```

### **3. Railway Environment Variables**

Set these in Railway dashboard:

```env
# Database (Railway will provide this automatically)
DATABASE_URL=postgresql://postgres:password@host:port/database

# Security (REQUIRED)
SECRET_KEY=your-super-secure-secret-key-32-chars-min
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Configuration (REQUIRED)
ENVIRONMENT=production
DEBUG=false
ENABLE_DOCS=false
LOG_LEVEL=INFO

# CORS (REQUIRED - update with your actual domains)
ALLOWED_ORIGINS=https://your-frontend.railway.app,https://yourdomain.com
FRONTEND_URL=https://your-frontend.railway.app
BACKEND_URL=https://your-backend.railway.app

# External Services (REQUIRED for full functionality)
OPENAI_API_KEY=sk-your-openai-api-key
RESEND_API_KEY=re_your-resend-api-key
FROM_EMAIL=noreply@yourdomain.com

# Redis (Railway will provide this automatically)
REDIS_URL=redis://redis:6379

# Monitoring (optional but recommended)
SENTRY_DSN=https://your-sentry-dsn

# Railway-specific (automatically set by Railway)
PORT=8000
```

## 🔧 **Railway Deployment Steps**

### **1. Connect to Railway**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init
```

### **2. Deploy Backend**
```bash
# Deploy from backend directory
cd backend
railway up

# Railway will automatically:
# - Build Docker image using Dockerfile
# - Install dependencies from requirements.txt
# - Use docker-compose.railway.yml configuration
# - Provide SSL certificate
# - Set up custom domain
# - Handle scaling
```

### **3. Add Database**
```bash
# Add PostgreSQL service
railway add postgresql

# Add Redis service  
railway add redis

# Railway will automatically set DATABASE_URL
```

### **4. Configure Environment**
```bash
# Set environment variables
railway variables set SECRET_KEY=your-secret-key
railway variables set OPENAI_API_KEY=your-openai-key
railway variables set ALLOWED_ORIGINS=https://your-frontend.railway.app
```

## 📊 **Railway Monitoring Features**

Railway provides built-in monitoring:

### **Metrics Dashboard**
- **CPU Usage** - Real-time CPU monitoring
- **Memory Usage** - Memory consumption tracking
- **Request Rate** - HTTP request metrics
- **Response Time** - API response times
- **Error Rate** - Error tracking and alerts

### **Logs**
- **Real-time logs** - Live log streaming
- **Log search** - Search through historical logs
- **Log filtering** - Filter by level, service, time
- **Log export** - Download logs for analysis

### **Alerts**
- **Resource alerts** - CPU/memory thresholds
- **Error alerts** - High error rates
- **Deployment alerts** - Failed deployments
- **Custom alerts** - Based on your metrics

## 🔍 **Accessing Railway Monitoring**

1. **Go to Railway Dashboard**
2. **Select your project**
3. **Click on "Metrics" tab** for real-time metrics
4. **Click on "Logs" tab** for log viewing
5. **Set up alerts** in the "Settings" tab

## 🚨 **Health Checks**

Railway automatically monitors:
- **Container health** - Based on your health check endpoint
- **Service availability** - HTTP response codes
- **Resource usage** - CPU, memory, disk
- **Deployment status** - Success/failure

## 🔄 **Deployment Process**

Railway handles:
1. **Automatic builds** on git push
2. **Zero-downtime deployments** with health checks
3. **Automatic rollbacks** on failure
4. **SSL certificate renewal** (automatic)
5. **Custom domain setup** (automatic)

## 📦 **Updated Dependencies for Railway**

The `requirements.txt` has been optimized for Railway deployment:

### **Core Production Dependencies**
- **FastAPI** - Web framework with automatic OpenAPI docs
- **Uvicorn** - ASGI server with WebSocket support
- **Gunicorn** - Production WSGI server with worker processes
- **SQLAlchemy** - Database ORM with connection pooling
- **Alembic** - Database migrations
- **psycopg2-binary** - PostgreSQL adapter

### **Security & Authentication**
- **python-jose[cryptography]** - JWT token handling
- **passlib[bcrypt]** - Password hashing
- **bcrypt** - Secure password hashing
- **cryptography** - Cryptographic operations

### **External Services**
- **OpenAI** - AI/LLM integration
- **Resend** - Email service
- **Redis** - Caching and rate limiting

### **Production Monitoring**
- **psutil** - System resource monitoring
- **structlog** - Structured logging
- **httpx** - Modern HTTP client

## 💡 **Railway Best Practices**

### **1. Use Railway's Database**
- Don't use external databases unless necessary
- Railway provides managed PostgreSQL/Redis
- Automatic backups and scaling

### **2. Environment Variables**
- Use Railway's environment variable system
- Don't commit secrets to git
- Use Railway's secret management

### **3. Health Checks**
- Ensure your `/ready` endpoint works
- Railway uses this for deployment health
- Keep health checks fast and reliable

### **4. Resource Management**
- Railway auto-scales based on usage
- Monitor your usage in the dashboard
- Set up alerts for unusual patterns

## 🆚 **Railway vs Custom Monitoring**

| Feature | Railway Built-in | Custom Stack |
|---------|------------------|--------------|
| **Setup** | ✅ Automatic | ❌ Manual |
| **SSL** | ✅ Automatic | ❌ Manual |
| **Scaling** | ✅ Automatic | ❌ Manual |
| **Logs** | ✅ Built-in | ✅ Prometheus/Grafana |
| **Metrics** | ✅ Basic | ✅ Advanced |
| **Alerts** | ✅ Basic | ✅ Custom |
| **Cost** | ✅ Included | ❌ Additional resources |

## 🎯 **Recommendation**

**Use Railway's built-in monitoring** because:
- ✅ **Zero setup** - works out of the box
- ✅ **Integrated** - native Railway features
- ✅ **Cost effective** - no additional resources
- ✅ **Reliable** - managed by Railway team
- ✅ **Scalable** - grows with your app

Only consider custom monitoring if you need:
- Advanced application metrics
- Custom dashboards
- Complex alerting rules
- Multi-service monitoring

---

**🚀 Ready to deploy?** Railway makes it simple - just push your code and Railway handles the rest!
