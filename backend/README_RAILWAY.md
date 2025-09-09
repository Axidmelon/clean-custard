# Custard Backend - Railway Deployment

This is the backend API for the Custard application, optimized for Railway deployment.

## 🚀 **Quick Start**

### **1. Deploy to Railway**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy from this directory
railway up
```

### **2. Add Services**
```bash
# Add PostgreSQL database
railway add postgresql

# Add Redis cache
railway add redis
```

### **3. Configure Environment**
Set these variables in Railway dashboard:
- `SECRET_KEY` - Your application secret key
- `OPENAI_API_KEY` - Your OpenAI API key
- `RESEND_API_KEY` - Your Resend email API key
- `ALLOWED_ORIGINS` - Your frontend domain(s)
- `FRONTEND_URL` - Your frontend URL

## 📁 **File Structure**

```
backend/
├── Dockerfile.production          # Production Docker image
├── docker-compose.railway.yml     # Railway-optimized compose
├── RAILWAY_DEPLOYMENT.md          # Detailed deployment guide
├── env.production.template        # Environment variables template
├── main.py                        # FastAPI application
├── api/                           # API endpoints
├── db/                            # Database models and config
├── core/                          # Core services
└── ws/                            # WebSocket handling
```

## 🔧 **Configuration**

### **Environment Variables**
See `env.production.template` for all available configuration options.

### **Database**
Railway automatically provides:
- PostgreSQL database
- Connection string in `DATABASE_URL`
- Automatic backups
- Scaling

### **SSL/TLS**
Railway automatically provides:
- SSL certificates (Let's Encrypt)
- HTTPS redirect
- Custom domain support

### **Monitoring**
Railway provides built-in:
- Application metrics
- Log aggregation
- Health checks
- Alerts

## 🏥 **Health Checks**

The application provides these health endpoints:
- `/health` - Detailed health status
- `/ready` - Kubernetes-style readiness probe
- `/status` - System status with agent connections

## 🔄 **Deployment**

Railway handles:
- Automatic builds on git push
- Zero-downtime deployments
- Automatic rollbacks on failure
- SSL certificate renewal
- Custom domain setup

## 📊 **Monitoring**

Access monitoring in Railway dashboard:
1. Go to your project
2. Click "Metrics" for real-time metrics
3. Click "Logs" for log viewing
4. Set up alerts in "Settings"

## 🆘 **Troubleshooting**

### **Common Issues**
1. **Health check failures** - Check `/ready` endpoint
2. **Database connection** - Verify `DATABASE_URL`
3. **CORS errors** - Update `ALLOWED_ORIGINS`
4. **API key errors** - Verify external service keys

### **Debug Commands**
```bash
# View logs
railway logs

# Check environment
railway variables

# Restart service
railway restart
```

## 📚 **Documentation**

- **Detailed Guide**: `RAILWAY_DEPLOYMENT.md`
- **Environment Setup**: `env.production.template`
- **API Documentation**: Available at `/docs` when deployed

## 🔗 **Links**

- [Railway Documentation](https://docs.railway.app/)
- [Railway CLI](https://docs.railway.app/develop/cli)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Ready to deploy?** Just run `railway up` and Railway handles the rest! 🚀
