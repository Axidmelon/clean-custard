# 🍮 Clean Custard Analytics Platform

A secure, AI-powered platform that allows users to ask natural language questions about their databases and get instant, accurate answers. Clean Custard bridges the gap between business users and complex database queries through intelligent AI agents that run securely within your own network.

## 🚀 Features

### Core Platform
- **Frontend**: Modern React 18 + TypeScript + Vite application with shadcn/ui components
- **Backend**: FastAPI + PostgreSQL + WebSocket real-time communication
- **Agent System**: Secure database connector agents running in Docker containers
- **Authentication**: JWT-based auth with email verification and multi-tenant support
- **AI Integration**: OpenAI GPT-4 powered natural language query processing

### Security-First Architecture
- **Zero-Trust Database Access**: Your database credentials never leave your network
- **Read-Only Safety**: Agents can only execute SELECT queries, preventing data modification
- **Sandboxed Execution**: Agents run in isolated Docker containers
- **Encrypted Communication**: All data transmission uses WebSocket over TLS
- **Multi-Tenant Support**: Organization-based user management and data isolation

### Production Safeguards
- **Health Checks**: Multiple endpoints (`/health`, `/ready`, `/status`, `/production-readiness`)
- **Startup Validation**: Database connectivity test before accepting traffic
- **Graceful Shutdown**: Proper cleanup of connections and resources
- **Real-Time Monitoring**: WebSocket-based live connection status updates
- **Schema Discovery**: Automatic database schema analysis and caching

## 🏗️ Architecture

Clean Custard uses a microservices architecture with three main components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Your Database │
│   (React/TS)    │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL,  │
│   on Vercel     │    │   on Railway    │    │    MySQL, etc.) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User          │    │   WebSocket     │    │   Agent         │
│   Interface     │    │   Manager       │    │   (Docker       │
│   & Auth        │    │   & LLM         │    │    Container)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

1. **Frontend** (React/TypeScript on Vercel)
   - Modern web interface with real-time UI updates
   - Secure connection management and query interface
   - WebSocket-based live status monitoring

2. **Backend** (FastAPI on Railway)
   - REST API and WebSocket server
   - LLM integration for natural language processing
   - Connection management and user authentication
   - Real-time agent communication

3. **Agent** (Docker Container in Your Network)
   - WebSocket client connecting to backend
   - Direct database connection and query execution
   - Schema discovery and caching
   - Read-only query safety enforcement

## 🚀 Quick Start

### Prerequisites
- Docker installed and running
- Node.js 18+ (for development)
- Python 3.11+ (for development)
- Database access (PostgreSQL, MySQL, MongoDB, or Snowflake)

### For End Users (Recommended)

1. **Sign up** at the Clean Custard web application
2. **Create a connection** by selecting your database type
3. **Run the secure agent** using the provided Docker command
4. **Start asking questions** about your data in natural language

### For Developers

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

4. **Agent Setup** (for testing)
   ```bash
   cd agent-postgresql
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   # Configure environment variables
   python main.py
   ```

5. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 🔐 Security Model

### Zero-Trust Database Access
- **Your credentials never leave your network** - agents run locally in your environment
- **Read-only safety** - agents can only execute SELECT queries, preventing data modification
- **Encrypted communication** - all data transmission uses WebSocket over TLS
- **Sandboxed execution** - agents run in isolated Docker containers

### Supported Databases
- **PostgreSQL** (including Supabase)
- **MySQL** 
- **MongoDB**
- **Snowflake**

### Agent Deployment
The agent runs as a Docker container in your network and connects to Clean Custard via WebSocket. No database credentials are stored in our system.

```bash
docker run -d \
  --name agent-postgresql-your-db \
  -e CONNECTION_ID="your-connection-id" \
  -e AGENT_ID="your-agent-id" \
  -e BACKEND_WEBSOCKET_URI="wss://your-backend.railway.app/api/v1/connections/ws/your-agent-id" \
  -e DB_HOST="your-database-host" \
  -e DB_PORT="5432" \
  -e DB_USER="your-readonly-user" \
  -e DB_PASSWORD="your-password" \
  -e DB_NAME="your-database" \
  -e DB_SSLMODE="require" \
  custard/agent:latest
```

## 🛡️ Production Safeguards

### Health Monitoring
- **`/health`**: Basic health check with database connectivity
- **`/ready`**: Kubernetes-style readiness probe (503 if not ready)
- **`/status`**: Detailed system status including agent connections
- **`/production-readiness`**: Configuration validation

### Automatic Safeguards
- ✅ Backend won't start if database is unavailable
- ✅ Health checks continuously monitor service status
- ✅ Real-time WebSocket monitoring prevents silent failures
- ✅ Production configuration validation before startup
- ✅ Graceful shutdown with proper resource cleanup

### Real-Time Monitoring
- **WebSocket Status**: Live connection status updates
- **Agent Health**: Real-time agent connection monitoring
- **Query Performance**: Response time and success rate tracking
- **Error Handling**: Comprehensive error logging and reporting

## 📁 Project Structure

```
clean-custard/
├── frontend/                 # React 18 + TypeScript + Vite frontend
│   ├── src/
│   │   ├── components/      # Reusable UI components (shadcn/ui)
│   │   ├── pages/          # Application pages (Connections, Talk Data)
│   │   ├── services/       # API service layer
│   │   ├── hooks/          # Custom React hooks
│   │   ├── contexts/       # React contexts (AuthContext)
│   │   └── lib/            # Utility functions and configurations
│   └── package.json
├── backend/                 # FastAPI backend
│   ├── api/v1/endpoints/   # API endpoints (auth, connections, query)
│   ├── core/               # Core services (auth, config, email)
│   ├── db/                 # Database models and migrations (Alembic)
│   ├── ws/                 # WebSocket management
│   ├── llm/                # LLM integration services
│   ├── services/           # Business logic services
│   └── main.py
├── agent-postgresql/       # Database connector agents
│   ├── main.py            # Agent main entry point
│   ├── schema_discoverer.py # Database schema discovery
│   └── requirements.txt
└── docs/                   # Documentation and guides
```

## 🔧 Configuration

### Environment Variables
See `backend/env.production.template` for all available configuration options.

### Key Settings
- **Database**: PostgreSQL connection string for the main application database
- **Security**: JWT secrets and API keys for authentication
- **External Services**: OpenAI API key, Resend email service
- **WebSocket**: CORS configuration and connection management
- **Agent**: Docker image configuration and deployment settings

### Agent Configuration
The agent requires these environment variables:
- `CONNECTION_ID`: Unique connection identifier
- `AGENT_ID`: Agent identifier for WebSocket routing
- `BACKEND_WEBSOCKET_URI`: WebSocket endpoint URL
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: Database connection details
- `DB_SSLMODE`: SSL mode for secure connections (required for cloud databases)

## 📊 Monitoring

### Health Endpoints
- **Health Check**: `GET /health` - Basic health status with database connectivity
- **Readiness**: `GET /ready` - Kubernetes readiness probe (503 if not ready)
- **Status**: `GET /status` - Detailed system status including agent connections
- **Production Readiness**: `GET /production-readiness` - Configuration validation

### Real-Time Monitoring
- **WebSocket Status**: Live connection status updates via WebSocket
- **Agent Health**: Real-time monitoring of connected agents
- **Query Performance**: Response time and success rate tracking
- **Connection Management**: Active connection monitoring and management

### Logging
- **Structured Logging**: Comprehensive logging with different levels
- **Error Tracking**: Detailed error logging and reporting
- **Performance Metrics**: Query execution time and resource usage
- **Security Events**: Authentication and authorization logging

## 🚀 Deployment

### Production Deployment
Clean Custard is designed for cloud deployment with the following architecture:

- **Frontend**: Deployed on Vercel with automatic CI/CD
- **Backend**: Deployed on Railway with PostgreSQL database
- **Agents**: Run in customer environments via Docker containers

### Agent Deployment
The agent deployment is the key component that customers run in their own environment:

1. **Generate Connection**: Create a connection in the web interface
2. **Copy Docker Command**: Get the pre-configured Docker command
3. **Run Agent**: Execute the command in your environment
4. **Verify Connection**: Check connection status in the dashboard

### Development Deployment
For local development, use Docker Compose:

```bash
# Backend with database
cd backend
docker-compose -f docker-compose.local.yml up -d

# Frontend (separate terminal)
cd frontend
npm run dev
```

## 🔒 Security

### Zero-Trust Architecture
- **No Database Credentials Stored**: Your database credentials never leave your network
- **Read-Only Safety**: Agents can only execute SELECT queries, preventing data modification
- **Sandboxed Execution**: Agents run in isolated Docker containers
- **Encrypted Communication**: All data transmission uses WebSocket over TLS

### Container Security
- Non-root user execution in agent containers
- Minimal base images for reduced attack surface
- Resource limits and isolation
- Regular security updates

### Network Security
- WebSocket over TLS for all agent communication
- CORS protection for web interface
- Rate limiting on API endpoints
- Secure authentication with JWT tokens

### Data Security
- Encrypted database connections (SSL/TLS)
- Secure secret management
- Multi-tenant data isolation
- Comprehensive access logging

## 📈 Performance

### Optimization
- **Database Connection Pooling**: Efficient database connection management
- **Schema Discovery Caching**: Cached database schema for faster queries
- **Query Optimization**: AI-powered query generation and optimization
- **WebSocket Efficiency**: Real-time communication with minimal overhead

### Scaling
- **Horizontal Scaling**: Support for multiple agent connections
- **Load Balancing**: WebSocket connection distribution
- **Database Scaling**: Support for multiple database types and connections
- **Cloud-Native**: Designed for cloud deployment and scaling

## 🛠️ Development

### Tech Stack
- **Frontend**: React 18, TypeScript, Vite, shadcn/ui, Tailwind CSS
- **Backend**: FastAPI, SQLAlchemy, Alembic, WebSockets, LangChain
- **Agent**: Python, psycopg2, WebSockets, Docker
- **Database**: PostgreSQL, MySQL, MongoDB, Snowflake support

### Code Quality
- **TypeScript**: Full type safety across frontend and backend
- **ESLint**: Comprehensive code linting and formatting
- **Error Handling**: Robust error handling and logging
- **API Documentation**: Auto-generated OpenAPI documentation

### Development Features
- **Hot Reload**: Fast development with Vite and uvicorn
- **WebSocket Testing**: Real-time connection testing tools
- **Schema Discovery**: Automatic database schema analysis
- **Query Validation**: SQL query safety validation

## 📚 Documentation

- **Agent Deployment Guide**: `AGENT_DEPLOYMENT_GUIDE.md` - Complete guide for deploying agents
- **Production Safeguards**: `backend/PRODUCTION_SAFEGUARDS.md` - Production safety measures
- **API Documentation**: Available at `/docs` when running the backend
- **Frontend Setup**: `frontend/README.md` - Frontend development guide
- **User Flow**: `user_flow.md` - Detailed user experience flow

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
2. Review the agent deployment guide
3. Check container logs for agent issues
4. Create an issue on GitHub

---

## 🎯 Key Benefits

- **🔒 Zero-Trust Security**: Your database credentials never leave your network
- **🤖 AI-Powered Queries**: Natural language to SQL with OpenAI GPT-4
- **⚡ Real-Time Monitoring**: Live connection status and performance tracking
- **🛡️ Read-Only Safety**: Agents can only execute SELECT queries
- **🚀 Easy Deployment**: Simple Docker-based agent deployment
- **📊 Multi-Database Support**: PostgreSQL, MySQL, MongoDB, Snowflake
- **🔄 Live Updates**: WebSocket-based real-time communication

**Clean Custard makes your data accessible through natural language while keeping it completely secure!** 🍮✨