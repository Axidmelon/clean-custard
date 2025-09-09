# Custard Agent Setup Checklist

## ⚠️ Important: Docker Command Alone is NOT Sufficient

The generated Docker command is just the first step. You need to complete additional setup for the agent to work properly.

## ✅ Pre-Deployment Checklist

### 1. Network Requirements
- [ ] **Internet Access**: Docker container can reach the internet
- [ ] **Backend Connectivity**: Can connect to `your-backend.railway.app`
- [ ] **Database Access**: Can connect to your database server
- [ ] **Firewall Configuration**: Outbound HTTPS (port 443) is allowed
- [ ] **WebSocket Support**: WebSocket protocol is not blocked

### 2. Database Setup
- [ ] **Read-Only User Created**: Dedicated user with SELECT permissions only
- [ ] **Database Accessible**: Database server is reachable from Docker container
- [ ] **Credentials Ready**: Username, password, host, port, and database name
- [ ] **SSL/TLS Configured**: If required by your database

### 3. Environment Preparation
- [ ] **Docker Installed**: Docker is installed and running
- [ ] **Network Tested**: Connectivity tests pass (see commands below)
- [ ] **Credentials Secured**: Database credentials are properly secured
- [ ] **Documentation Reviewed**: Read the full deployment guide

## 🧪 Quick Tests (Run Before Deployment)

### Test 1: Internet Connectivity
```bash
docker run --rm alpine ping -c 3 8.8.8.8
```

### Test 2: Backend Connectivity
```bash
curl -I https://your-backend.railway.app/health
```

### Test 3: WebSocket Connectivity
```bash
# If wscat is installed
wscat -c ws://your-backend.railway.app/api/v1/connections/ws/test-agent
```

### Test 4: Database Connectivity
```bash
# PostgreSQL
docker run --rm postgres:15-alpine pg_isready -h your-db-host.com -p 5432

# MySQL
docker run --rm mysql:8.0 mysql -h your-db-host.com -P 3306 -u username -p

# MongoDB
docker run --rm mongo:7.0 mongosh --host your-db-host.com --port 27017
```

## 🚨 Common Issues & Quick Fixes

### Issue: Connection Timeout
**Fix**: Check firewall, ensure outbound HTTPS is allowed

### Issue: DNS Resolution Failed
**Fix**: Check internet access, verify domain name

### Issue: Database Connection Failed
**Fix**: Verify credentials, check database accessibility

### Issue: WebSocket Handshake Failed
**Fix**: Ensure WebSocket protocol is not blocked

## 📋 Post-Deployment Verification

### 1. Check Container Status
```bash
docker ps | grep custard-agent
```

### 2. Monitor Logs
```bash
docker logs custard-agent-[name]
```

### 3. Expected Success Logs
```
✅ Successfully connected to Custard backend
Database schema discovery completed
```

### 4. Test in Dashboard
- Go to Custard dashboard
- Check connection status shows "Connected"
- Try executing a test query

## 📚 Additional Resources

- **Full Deployment Guide**: [AGENT_DEPLOYMENT_GUIDE.md](./AGENT_DEPLOYMENT_GUIDE.md)
- **Troubleshooting**: See deployment guide for detailed solutions
- **Support**: Contact Custard support if issues persist

## ⏱️ Estimated Setup Time

- **Simple setup**: 15-30 minutes
- **Corporate environment**: 1-2 hours (may require IT approval)
- **Complex network**: 2-4 hours (may require network admin)

## 🔒 Security Reminders

- ✅ Use read-only database users only
- ✅ Never use admin/root database credentials
- ✅ Use strong, unique passwords
- ✅ Enable SSL/TLS for database connections
- ✅ Monitor agent logs regularly
