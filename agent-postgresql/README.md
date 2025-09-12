# Agent PostgreSQL Docker Setup

This directory contains the Docker configuration for the Custard Agent service.

## Overview

The Agent PostgreSQL is a Python-based service that:
- Connects to the backend via WebSocket
- Executes read-only SQL queries on customer databases
- Discovers database schemas
- Provides secure, sandboxed database access

## Quick Start

### 1. Environment Setup

Copy the environment template and configure it:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```bash
# Backend WebSocket Connection
BACKEND_WEBSOCKET_URI=ws://localhost:8000/api/v1/connections/ws/agent-007

# Agent Configuration
CONNECTION_ID=agent-007

# Database Connection (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### 2. Build and Run

#### Option A: Docker Compose (Recommended for development)

```bash
# Build and start the agent with a test database
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop services
docker-compose down
```

#### Option B: Docker Build

```bash
# Build the image
docker build -t agent-postgresql .

# Run the container
docker run --env-file .env agent-postgresql
```

### 3. Testing

The agent will automatically:
- Connect to the backend WebSocket endpoint
- Wait for SQL query requests
- Execute read-only queries safely
- Return results to the backend

## Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐    SQL    ┌─────────────────┐
│   Backend       │◄──────────────►│   Agent         │◄─────────►│   Customer      │
│   (FastAPI)     │                │   PostgreSQL    │           │   Database      │
│   (FastAPI)     │                │   (Docker)      │           │   (PostgreSQL)  │
└─────────────────┘                └─────────────────┘           └─────────────────┘
```

## Security Features

- **Read-only queries only**: Agent blocks all non-SELECT operations
- **Non-root user**: Container runs as unprivileged user
- **Minimal attack surface**: Only essential dependencies included
- **Input validation**: SQL queries are validated before execution
- **Connection isolation**: Each agent instance connects to one database

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_WEBSOCKET_URI` | WebSocket endpoint for backend communication | `ws://localhost:8000/api/v1/connections/ws/agent-007` |
| `CONNECTION_ID` | Unique identifier for this agent instance | `agent-007` |
| `DB_HOST` | Database host address | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `postgres` |
| `DB_USER` | Database username | `postgres` |
| `DB_PASSWORD` | Database password | Required |

### Docker Configuration

- **Base Image**: Python 3.11-slim
- **Multi-stage build**: Optimized for production
- **Health checks**: Built-in container health monitoring
- **Security**: Non-root user execution

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py
```

### Testing

```bash
# Test WebSocket server
python test_server.py

# Test schema discovery
python schema_discoverer.py
```

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure the backend is running and accessible
2. **Database connection failed**: Check database credentials and network connectivity
3. **Permission denied**: Verify database user has appropriate permissions

### Logs

```bash
# View container logs
docker logs agent-postgresql

# Follow logs in real-time
docker logs -f agent-postgresql
```

### Health Check

The container includes a health check that verifies WebSocket connectivity:

```bash
# Check container health
docker inspect agent-postgresql --format='{{.State.Health.Status}}'
```

## Production Deployment

### Environment Configuration

For production deployment, ensure you have:

1. **Secure Environment Variables**: Use proper secrets management (e.g., Kubernetes secrets, Docker secrets, or cloud provider secret managers)
2. **Database SSL**: Set `DB_SSLMODE=require` for secure database connections
3. **Network Security**: Ensure proper firewall rules and network isolation
4. **Monitoring**: Set up logging and monitoring for the agent

### Production Docker Compose

Create a production `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  agent-postgresql:
    build: .
    container_name: agent-postgresql-prod
    restart: unless-stopped
    env_file:
      - .env.production
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./logs:/app/logs
    networks:
      - custard-network
    healthcheck:
      test: ["CMD", "python", "-c", "import asyncio; import websockets; import psycopg2; print('Agent is healthy')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

networks:
  custard-network:
    driver: bridge
```

### Kubernetes Deployment

For Kubernetes deployment, create these manifests:

1. **ConfigMap** for non-sensitive configuration
2. **Secret** for database credentials and WebSocket URLs
3. **Deployment** for the agent pod
4. **Service** for internal communication (if needed)

### Security Best Practices

1. **Non-root user**: Container runs as unprivileged user `custard`
2. **Read-only queries**: Agent only executes SELECT statements
3. **Input validation**: SQL queries are validated before execution
4. **Connection isolation**: Each agent instance connects to one database
5. **Minimal attack surface**: Only essential dependencies included
6. **Health checks**: Built-in container health monitoring

## Support

For issues and questions, refer to the main Custard documentation or contact the development team.
