# MongoDB Agent Deployment Guide

This guide explains how to deploy the Custard MongoDB Agent alongside your existing PostgreSQL agent.

## Architecture Overview

The MongoDB agent is a separate service that:
- Connects to MongoDB databases
- Provides schema discovery for MongoDB collections
- Executes read-only MongoDB queries
- Communicates with the Custard backend via WebSocket

## Prerequisites

- MongoDB database (local, Atlas, or self-hosted)
- Custard backend running
- Docker (for containerized deployment)
- Python 3.11+ (for local deployment)

## Environment Variables

Create a `.env` file for the MongoDB agent:

```env
# Backend connection (same as PostgreSQL agent)
BACKEND_WEBSOCKET_URI=wss://your-backend.com/api/v1/connections/ws/{agent_id}
CONNECTION_ID=your-connection-uuid
AGENT_ID=your-agent-id

# MongoDB connection
MONGODB_CONNECTION_STRING=mongodb://username:password@host:port/database
MONGODB_DATABASE_NAME=your_database_name

# Optional: Collection filtering
MONGODB_COLLECTION_FILTER=collection1,collection2,collection3
```

### MongoDB Connection String Examples

**Local MongoDB:**
```env
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/myapp
MONGODB_DATABASE_NAME=myapp
```

**MongoDB Atlas:**
```env
MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/myapp?retryWrites=true&w=majority
MONGODB_DATABASE_NAME=myapp
```

**MongoDB with Authentication:**
```env
MONGODB_CONNECTION_STRING=mongodb://username:password@host:port/myapp?authSource=admin
MONGODB_DATABASE_NAME=myapp
```

## Deployment Options

### Option 1: Docker Deployment (Recommended)

1. **Build the Docker image:**
   ```bash
   cd agent-mongodb
   docker build -t custard-mongodb-agent .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name custard-mongodb-agent \
     --env-file .env \
     --restart unless-stopped \
     custard-mongodb-agent
   ```

3. **Check logs:**
   ```bash
   docker logs custard-mongodb-agent
   ```

### Option 2: Local Python Deployment

1. **Install dependencies:**
   ```bash
   cd agent-mongodb
   pip install -r requirements.txt
   ```

2. **Run the agent:**
   ```bash
   python main.py
   ```

### Option 3: Docker Compose

Add to your existing `docker-compose.yml`:

```yaml
services:
  # ... existing services ...
  
  mongodb-agent:
    build: ./agent-mongodb
    container_name: custard-mongodb-agent
    env_file: ./agent-mongodb/.env
    restart: unless-stopped
    depends_on:
      - backend
```

## Backend Configuration

The backend automatically supports MongoDB connections. When creating a new connection:

1. Set `db_type` to `"MONGODB"`
2. The backend will route queries to the MongoDB agent
3. Schema discovery will use MongoDB-specific logic

## Testing the Deployment

1. **Test schema discovery:**
   ```bash
   # Test the schema discoverer directly
   cd agent-mongodb
   python schema_discoverer.py
   ```

2. **Test agent connection:**
   - Check agent logs for successful WebSocket connection
   - Verify agent appears in backend status endpoint

3. **Test query execution:**
   - Create a MongoDB connection in the backend
   - Refresh the schema
   - Send a test query

## Monitoring and Logs

### Health Checks

The agent includes health checks:
- WebSocket connection status
- MongoDB connectivity
- Query execution success rate

### Logging

The agent logs:
- Connection status
- Query execution
- Schema discovery
- Error conditions

### Monitoring Commands

```bash
# Check agent status
docker logs custard-mongodb-agent

# Check MongoDB connectivity
docker exec custard-mongodb-agent python -c "import pymongo; print('MongoDB connection OK')"

# Check WebSocket connection
# Look for "Successfully connected to Custard backend" in logs
```

## Security Considerations

1. **Network Security:**
   - Use TLS/SSL for MongoDB connections
   - Restrict network access to MongoDB
   - Use VPN or private networks when possible

2. **Authentication:**
   - Use strong MongoDB credentials
   - Rotate API keys regularly
   - Use MongoDB's built-in authentication

3. **Query Security:**
   - Agent only executes read-only queries
   - Dangerous operations are blocked
   - Input validation and sanitization

## Troubleshooting

### Common Issues

1. **Connection Failed:**
   - Check MongoDB connection string
   - Verify network connectivity
   - Check MongoDB server status

2. **WebSocket Connection Failed:**
   - Verify backend URL
   - Check agent ID and connection ID
   - Ensure backend is running

3. **Schema Discovery Failed:**
   - Check MongoDB permissions
   - Verify database name
   - Check collection filter settings

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

### Support

For issues:
1. Check agent logs
2. Verify environment variables
3. Test MongoDB connectivity
4. Check backend logs

## Scaling

### Multiple Agents

You can run multiple MongoDB agents for different databases:

```yaml
services:
  mongodb-agent-1:
    build: ./agent-mongodb
    environment:
      - AGENT_ID=agent-mongo-1
      - CONNECTION_ID=connection-1-uuid
      - MONGODB_DATABASE_NAME=database1
    # ... other config

  mongodb-agent-2:
    build: ./agent-mongodb
    environment:
      - AGENT_ID=agent-mongo-2
      - CONNECTION_ID=connection-2-uuid
      - MONGODB_DATABASE_NAME=database2
    # ... other config
```

### Load Balancing

For high availability:
- Use multiple agent instances
- Implement health checks
- Use load balancers for MongoDB

## Maintenance

### Updates

1. **Update agent:**
   ```bash
   docker pull custard-mongodb-agent:latest
   docker stop custard-mongodb-agent
   docker rm custard-mongodb-agent
   # Run new container with updated image
   ```

2. **Update dependencies:**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

### Backup

- Backup MongoDB data regularly
- Export agent configuration
- Document connection strings securely
