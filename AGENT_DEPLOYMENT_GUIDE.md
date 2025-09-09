# Custard Agent Deployment Guide

## Overview

This guide provides complete instructions for deploying the Custard Agent in your environment. The generated Docker command is just the first step - additional configuration is required for successful deployment.

## Prerequisites

Before running the Custard Agent, ensure you have:

- [ ] Docker installed and running
- [ ] Network access to the Custard backend
- [ ] Database credentials and connectivity
- [ ] Proper firewall configuration
- [ ] Required environment variables

## Step-by-Step Deployment

### Step 1: Generate the Docker Command

1. Log into your Custard dashboard
2. Navigate to **Connections** page
3. Click **Connect** on your desired database type
4. Enter your connection name
5. Copy the generated Docker command

### Step 2: Network Requirements

#### 2.1 Outbound Connections Required

The agent needs to make outbound connections to:

| Service | Destination | Port | Protocol | Purpose |
|---------|-------------|------|----------|---------|
| Custard Backend | `your-backend.railway.app` | 443 | HTTPS/WebSocket | Agent communication |
| Your Database | `your-db-host.com` | 5432/3306/27017 | Database-specific | Query execution |

#### 2.2 Test Network Connectivity

Before running the agent, test connectivity:

```bash
# Test backend connectivity
curl -I https://your-backend.railway.app/health

# Test WebSocket connectivity (if wscat is installed)
wscat -c ws://your-backend.railway.app/api/v1/connections/ws/test-agent

# Test database connectivity
telnet your-db-host.com 5432
```

### Step 3: Firewall Configuration

#### 3.1 Corporate Networks

If you're in a corporate environment, contact your network administrator to:

- **Whitelist domains**: Add `*.railway.app` to allowed domains
- **Allow outbound HTTPS**: Ensure port 443 is not blocked
- **Enable WebSocket protocol**: Ensure WebSocket over TLS is permitted
- **Database access**: Allow connections to your database server

#### 3.2 Cloud Providers

For cloud deployments (AWS, Azure, GCP), configure:

- **Security Groups**: Allow outbound HTTPS (port 443)
- **Network ACLs**: Permit external connections
- **DNS Resolution**: Ensure containers can resolve external domains
- **VPC Configuration**: Allow outbound internet access

#### 3.3 Docker Networks

Ensure Docker has proper network access:

```bash
# Test Docker internet access
docker run --rm alpine ping -c 3 8.8.8.8

# Test WebSocket from Docker
docker run --rm --network host alpine/curl wscat -c ws://your-backend.railway.app/api/v1/connections/ws/test
```

### Step 4: Database Configuration

#### 4.1 Create Read-Only User

**CRITICAL**: Create a dedicated read-only user for the agent:

```sql
-- PostgreSQL
CREATE USER custard_agent WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE your_database TO custard_agent;
GRANT USAGE ON SCHEMA public TO custard_agent;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO custard_agent;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO custard_agent;

-- MySQL
CREATE USER 'custard_agent'@'%' IDENTIFIED BY 'secure_password';
GRANT SELECT ON your_database.* TO 'custard_agent'@'%';
FLUSH PRIVILEGES;

-- MongoDB
use admin
db.createUser({
  user: "custard_agent",
  pwd: "secure_password",
  roles: [{ role: "read", db: "your_database" }]
})
```

#### 4.2 Database Accessibility

Ensure your database is accessible from the Docker container:

- **Internal networks**: Use internal IP addresses
- **External databases**: Ensure public access is configured
- **VPN requirements**: Connect to VPN if database is behind VPN
- **SSL/TLS**: Configure SSL if required

### Step 5: Environment Variables

Replace the placeholder values in the Docker command:

```bash
# Example with real values
docker run -d \
  --name custard-agent-production-db \
  -e CONNECTION_ID="agent-production-db-1234567890" \
  -e BACKEND_WEBSOCKET_URI="ws://your-backend.railway.app/api/v1/connections/ws/agent-production-db-1234567890" \
  -e DB_HOST="db.example.com" \
  -e DB_PORT="5432" \
  -e DB_USER="custard_agent" \
  -e DB_PASSWORD="your_secure_password" \
  -e DB_NAME="production_database" \
  custard/agent:latest
```

### Step 6: Run the Agent

Execute the configured Docker command:

```bash
# Run the agent
docker run -d \
  --name custard-agent-production-db \
  -e CONNECTION_ID="agent-production-db-1234567890" \
  -e BACKEND_WEBSOCKET_URI="ws://your-backend.railway.app/api/v1/connections/ws/agent-production-db-1234567890" \
  -e DB_HOST="db.example.com" \
  -e DB_PORT="5432" \
  -e DB_USER="custard_agent" \
  -e DB_PASSWORD="your_secure_password" \
  -e DB_NAME="production_database" \
  custard/agent:latest
```

### Step 7: Verify Deployment

#### 7.1 Check Agent Status

```bash
# Check if container is running
docker ps | grep custard-agent

# Check agent logs
docker logs custard-agent-production-db

# Follow logs in real-time
docker logs -f custard-agent-production-db
```

#### 7.2 Expected Log Output

Successful deployment should show:

```
2024-01-15 10:30:00 - INFO - Starting Custard Agent: agent-production-db-1234567890
2024-01-15 10:30:01 - INFO - Connecting to backend at: ws://your-backend.railway.app/api/v1/connections/ws/agent-production-db-1234567890
2024-01-15 10:30:02 - INFO - ✅ Successfully connected to Custard backend
2024-01-15 10:30:03 - INFO - Database schema discovery completed
```

#### 7.3 Test Connection

1. Go to your Custard dashboard
2. Navigate to **Connections**
3. Verify your connection shows as **Connected**
4. Try executing a test query

## Troubleshooting

### Common Issues

#### Issue 1: Connection Timeout

**Symptoms:**
```
Failed to connect to backend: [Errno 110] Connection timed out
```

**Solutions:**
- Check firewall configuration
- Verify network connectivity
- Ensure Railway backend is accessible
- Check if WebSocket protocol is blocked

#### Issue 2: DNS Resolution Failure

**Symptoms:**
```
Failed to connect to backend: [Errno -3] Temporary failure in name resolution
```

**Solutions:**
- Check DNS configuration
- Ensure internet access from Docker
- Verify domain name is correct
- Test with IP address instead of domain

#### Issue 3: Database Connection Failed

**Symptoms:**
```
Database query failed: connection to server at "db.example.com" (192.168.1.100), port 5432 failed
```

**Solutions:**
- Verify database credentials
- Check database server accessibility
- Ensure read-only user exists
- Verify network connectivity to database

#### Issue 4: WebSocket Handshake Failed

**Symptoms:**
```
WebSocket handshake failed: 403 Forbidden
```

**Solutions:**
- Check if WebSocket protocol is allowed
- Verify CORS configuration
- Ensure proper authentication
- Check if backend is running

### Debug Commands

```bash
# Test network connectivity
docker run --rm alpine ping -c 3 your-backend.railway.app

# Test WebSocket connectivity
docker run --rm --network host alpine/curl wscat -c ws://your-backend.railway.app/api/v1/connections/ws/test

# Test database connectivity
docker run --rm postgres:15-alpine pg_isready -h your-db-host.com -p 5432

# Check Docker network configuration
docker network ls
docker network inspect bridge
```

## Security Considerations

### 1. Database Security

- **Use read-only users**: Never use admin/root database users
- **Limit permissions**: Only grant SELECT permissions
- **Use strong passwords**: Generate secure, unique passwords
- **Enable SSL/TLS**: Use encrypted connections when possible

### 2. Network Security

- **Firewall rules**: Only allow necessary outbound connections
- **VPN access**: Use VPN for internal databases
- **Network isolation**: Run agent in isolated network segment
- **Regular updates**: Keep Docker and agent images updated

### 3. Container Security

- **Non-root user**: Agent runs as non-root user
- **Minimal image**: Only essential dependencies included
- **Resource limits**: Set appropriate CPU/memory limits
- **Log monitoring**: Monitor agent logs for suspicious activity

## Monitoring and Maintenance

### 1. Health Checks

```bash
# Check container health
docker inspect custard-agent-production-db --format='{{.State.Health.Status}}'

# Check resource usage
docker stats custard-agent-production-db

# Check logs for errors
docker logs custard-agent-production-db | grep ERROR
```

### 2. Updates

```bash
# Pull latest agent image
docker pull custard/agent:latest

# Stop and remove old container
docker stop custard-agent-production-db
docker rm custard-agent-production-db

# Run new container with same configuration
# (Use your saved Docker command)
```

### 3. Backup

- **Configuration backup**: Save your Docker command and environment variables
- **Database backup**: Ensure regular database backups
- **Log retention**: Configure log rotation and retention

## Support

If you encounter issues not covered in this guide:

1. **Check logs**: Review agent and Docker logs
2. **Test connectivity**: Use debug commands above
3. **Contact support**: Reach out to Custard support team
4. **Provide details**: Include logs, configuration, and error messages

## Quick Reference

### Essential Commands

```bash
# Run agent
docker run -d --name custard-agent-[name] -e [env-vars] custard/agent:latest

# Check status
docker ps | grep custard-agent

# View logs
docker logs custard-agent-[name]

# Stop agent
docker stop custard-agent-[name]

# Remove agent
docker rm custard-agent-[name]
```

### Required Environment Variables

- `CONNECTION_ID`: Unique agent identifier
- `BACKEND_WEBSOCKET_URI`: WebSocket endpoint URL
- `DB_HOST`: Database host address
- `DB_PORT`: Database port
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name

### Network Requirements

- Outbound HTTPS (port 443) to `*.railway.app`
- Outbound database port to your database server
- DNS resolution for external domains
- WebSocket protocol support
