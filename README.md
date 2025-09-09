# 🍮 Clean Custard Analytics Platform

A production-ready AI data agent platform with comprehensive safeguards, monitoring, and deployment automation.

## 🚀 Features

### Core Platform
- **Frontend**: Modern React + TypeScript + Vite application
- **Backend**: FastAPI + PostgreSQL + WebSocket real-time communication
- **Agent System**: Secure database connector agents
- **Authentication**: JWT-based auth with email verification

### Production Safeguards
- **Health Checks**: Multiple endpoints (`/health`, `/ready`, `/status`)
- **Startup Validation**: Database connectivity test before accepting traffic
- **Graceful Shutdown**: Proper cleanup of connections and resources
- **Monitoring**: Prometheus + Grafana + AlertManager
- **Deployment**: Automated scripts with rollback capability

### Security & Performance
- **Docker**: Production-ready containers with security best practices
- **Nginx**: Reverse proxy with rate limiting and security headers
- **Database**: Connection pooling and performance optimization
- **Monitoring**: Real-time health monitoring and alerting

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React/Vite)  │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   WebSocket     │    │   Monitoring    │
│   (Reverse      │    │   Manager       │    │   (Prometheus   │
│    Proxy)       │    │                 │    │    + Grafana)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for development)
- Python 3.13+ (for development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/axidmelon/clean-custard.git
   cd clean-custard
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp env.production.template .env
   # Edit .env with your configuration
   python -m uvicorn main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Production Deployment

1. **Configure Environment**
   ```bash
   cp backend/env.production.template backend/.env.production
   # Edit .env.production with your production values
   ```

2. **Deploy with Monitoring**
   ```bash
   cd backend
   chmod +x deploy-production.sh
   ./deploy-production.sh deploy
   ```

3. **Access Production Services**
   - Application: http://localhost:8000
   - Health Check: http://localhost:8000/health
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090

## 🛡️ Production Safeguards

### Health Monitoring
- **`/health`**: Basic health check with database connectivity
- **`/ready`**: Kubernetes-style readiness probe (503 if not ready)
- **`/status`**: Detailed system status including agent connections
- **`/production-readiness`**: Configuration validation

### Automatic Safeguards
- ✅ Backend won't start if database is unavailable
- ✅ Health checks continuously monitor service status
- ✅ Automatic rollback on deployment failures
- ✅ Real-time monitoring prevents silent failures
- ✅ Production configuration validation before startup

### Monitoring & Alerting
- **Prometheus**: Metrics collection and storage
- **Grafana**: Real-time dashboards and visualization
- **AlertManager**: Critical alerts and notifications
- **Custom Dashboards**: Application-specific monitoring

## 📁 Project Structure

```
clean-custard/
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Application pages
│   │   ├── services/       # API service layer
│   │   └── hooks/          # Custom React hooks
│   └── package.json
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   ├── core/               # Core services (auth, config)
│   ├── db/                 # Database models and migrations
│   ├── monitoring/         # Monitoring configuration
│   ├── ws/                 # WebSocket management
│   └── main.py
├── agent/                  # Database connector agents
└── docs/                   # Documentation
```

## 🔧 Configuration

### Environment Variables
See `backend/env.production.template` for all available configuration options.

### Key Settings
- **Database**: PostgreSQL connection string
- **Security**: JWT secrets and API keys
- **External Services**: OpenAI, Resend email service
- **Monitoring**: Sentry DSN, Grafana password
- **Deployment**: Domain settings, SSL configuration

## 📊 Monitoring

### Health Endpoints
- **Health Check**: `GET /health` - Basic health status
- **Readiness**: `GET /ready` - Kubernetes readiness probe
- **Status**: `GET /status` - Detailed system status
- **Production Readiness**: `GET /production-readiness` - Config validation

### Metrics
- Application performance metrics
- Database connection metrics
- WebSocket connection metrics
- System resource utilization
- Error rates and response times

### Alerts
- Backend service down
- Database connection failure
- High error rates
- High response times
- Resource usage thresholds

## 🚀 Deployment

### Docker Compose
```bash
# Production deployment
docker-compose -f docker-compose.production.yml up -d

# With monitoring
docker-compose -f docker-compose.production.yml -f monitoring/docker-compose.monitoring.yml up -d
```

### Automated Deployment
```bash
# Deploy with health checks and rollback
./deploy-production.sh deploy

# Rollback if needed
./deploy-production.sh rollback

# Health check
./deploy-production.sh health-check
```

## 🔒 Security

### Container Security
- Non-root user execution
- Minimal base images
- Security scanning
- Resource limits

### Network Security
- Rate limiting
- CORS protection
- Security headers
- SSL/TLS support

### Data Security
- Encrypted database connections
- Secure secret management
- Regular backup encryption
- Access logging

## 📈 Performance

### Optimization
- Database connection pooling
- Query optimization
- Caching strategies
- Resource monitoring

### Scaling
- Horizontal scaling support
- Load balancer configuration
- Database clustering
- WebSocket distribution

## 🛠️ Development

### Code Quality
- TypeScript for type safety
- ESLint for code linting
- Prettier for code formatting
- Comprehensive error handling

### Testing
- Unit tests for core functionality
- Integration tests for API endpoints
- Health check validation
- Performance testing

## 📚 Documentation

- **Production Safeguards**: `backend/PRODUCTION_SAFEGUARDS.md`
- **Deployment Guide**: `backend/PRODUCTION_DEPLOYMENT.md`
- **API Documentation**: Available at `/docs` when running
- **Monitoring Setup**: `backend/monitoring/README.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section in the documentation
2. Review the monitoring dashboards
3. Check container logs
4. Create an issue on GitHub

---

**⚠️ Important**: This is a production-ready platform with comprehensive safeguards. Always test in a staging environment first and ensure you have proper backups before deploying to production.

## 🎯 Key Benefits

- **Zero-downtime deployments** with health checks
- **Automatic failure detection** and recovery
- **Real-time monitoring** of all critical services
- **Proactive alerting** before issues impact users
- **Comprehensive logging** for debugging
- **Production-ready security** and performance optimizations

Your production deployment is bulletproof! 🛡️