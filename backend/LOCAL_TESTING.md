# Local Docker Testing Guide

This guide helps you test your Custard Backend locally before deploying to Railway.

## 🚀 **Quick Test**

```bash
# Run the complete test suite
./test-local.sh

# Or run individual commands
./test-local.sh start    # Start services
./test-local.sh test     # Run tests
./test-local.sh status   # Check status
./test-local.sh stop     # Stop services
```

## 🧪 **What Gets Tested**

### **1. Docker Build**
- ✅ Dockerfile builds successfully
- ✅ All dependencies installed
- ✅ Application starts correctly

### **2. Health Endpoints**
- ✅ `/health` - Detailed health status
- ✅ `/ready` - Readiness probe
- ✅ `/status` - System status
- ✅ `/docs` - API documentation

### **3. Database Connectivity**
- ✅ PostgreSQL connection
- ✅ Database migrations
- ✅ Health check integration

### **4. Redis Connectivity**
- ✅ Redis connection
- ✅ Cache functionality

### **5. Environment Variables**
- ✅ All required variables set
- ✅ Configuration loaded correctly

## 🔧 **Local Testing Setup**

### **Services Started:**
- **custard-backend** - Your FastAPI app (port 8000)
- **postgres** - PostgreSQL database (port 5432)
- **redis** - Redis cache (port 6379)

### **Environment:**
- **Database**: `postgresql://custard:password@postgres:5432/custard_db`
- **Redis**: `redis://redis:6379`
- **API**: `http://localhost:8000`
- **Docs**: `http://localhost:8000/docs`

## 📊 **Test Results**

### **Success Indicators:**
- ✅ All services start without errors
- ✅ Health checks pass
- ✅ API endpoints respond correctly
- ✅ Database connectivity works
- ✅ No error logs

### **Failure Indicators:**
- ❌ Services fail to start
- ❌ Health checks timeout
- ❌ API endpoints return errors
- ❌ Database connection failures
- ❌ Error logs in containers

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **Port conflicts**
   ```bash
   # Check if ports are in use
   lsof -i :8000
   lsof -i :5432
   lsof -i :6379
   ```

2. **Docker build failures**
   ```bash
   # Check Docker logs
   docker-compose -f docker-compose.local.yml logs custard-backend
   ```

3. **Database connection issues**
   ```bash
   # Check database logs
   docker-compose -f docker-compose.local.yml logs postgres
   ```

4. **Health check failures**
   ```bash
   # Test endpoints manually
   curl http://localhost:8000/health
   curl http://localhost:8000/ready
   ```

### **Debug Commands:**
```bash
# View all logs
docker-compose -f docker-compose.local.yml logs

# View specific service logs
docker-compose -f docker-compose.local.yml logs custard-backend

# Check service status
docker-compose -f docker-compose.local.yml ps

# Access container shell
docker-compose -f docker-compose.local.yml exec custard-backend bash
```

## 🎯 **After Successful Testing**

Once all tests pass:

1. **Your Docker setup is verified** ✅
2. **Health endpoints work correctly** ✅
3. **Database connectivity is confirmed** ✅
4. **You're ready for Railway deployment** ✅

## 🚀 **Next Steps**

After successful local testing:

1. **Deploy to Railway**: `railway up`
2. **Add services**: `railway add postgresql` and `railway add redis`
3. **Configure environment**: Set variables in Railway dashboard
4. **Monitor deployment**: Use Railway dashboard

## 💡 **Pro Tips**

- **Run tests frequently** during development
- **Check logs** if tests fail
- **Test with different environments** (dev, staging)
- **Keep services running** for manual testing if needed
- **Clean up** after testing to free resources

---

**Ready to test?** Run `./test-local.sh` and ensure everything works before Railway deployment! 🧪
