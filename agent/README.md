# Custard Agent Docker Setup

This directory contains the Docker configuration for the Custard Agent service.

## Overview

The Custard Agent is a Python-based service that:
- Connects to the Custard backend via WebSocket
- Executes read-only SQL queries on customer databases
- Discovers database schemas
- Provides secure, sandboxed database access

## Quick Start

### 1. Environment Setup

Copy the environment template and configure it:

```bash
cp env.template .env
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
docker-compose -f docker-compose-agent.yml up --build

# Run in background
docker-compose -f docker-compose-agent.yml up -d --build
```

#### Option B: Docker Build

```bash
# Build the image
docker build -t custard-agent .

# Run the container
docker run --env-file .env custard-agent
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
│   Custard       │◄──────────────►│   Custard       │◄─────────►│   Customer      │
│   Backend       │                │   Agent         │           │   Database      │
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
docker logs custard-agent

# Follow logs in real-time
docker logs -f custard-agent
```

### Health Check

The container includes a health check that verifies WebSocket connectivity:

```bash
# Check container health
docker inspect custard-agent --format='{{.State.Health.Status}}'
```

## Production Deployment

For production deployment:

1. Use a production-ready base image
2. Configure proper secrets management
3. Set up monitoring and logging
4. Use container orchestration (Kubernetes, Docker Swarm)
5. Implement proper backup and recovery procedures

## Support

For issues and questions, refer to the main Custard documentation or contact the development team.
