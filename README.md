# Custard AI Data Agent Platform

A secure, AI-powered platform that allows users to ask natural language questions about their databases and get instant, accurate answers. Custard bridges the gap between business users and complex database queries through intelligent AI agents.

## 🚀 Features

- **Natural Language Queries**: Ask questions in plain English and get SQL-generated answers
- **Secure Agent Architecture**: Deploy lightweight agents in your own network for maximum security
- **Real-time Communication**: WebSocket-based communication between backend and agents
- **Schema Discovery**: Automatic database schema detection and caching
- **Read-only Safety**: Agents can only execute SELECT queries, ensuring data safety
- **Multi-tenant Support**: Organization-based user and connection management
- **User Authentication**: Complete user registration, login, and email verification system
- **Password Reset**: Secure password reset functionality with email verification
- **Database Connection Management**: Real-time UI for managing database connections with CRUD operations
- **Modern Web Interface**: React-based frontend with TypeScript and shadcn/ui components
- **RESTful API**: Clean, well-documented API endpoints with FastAPI
- **Production Ready**: Comprehensive error handling, loading states, and user experience improvements

## 🏗️ Architecture

```
┌─────────────────────────────────┐    ┌─────────────────────────────────────────┐    ┌───────────────────────────────────────────┐
│        USER'S BROWSER           │    │        CUSTARD CLOUD PLATFORM           │    │      CUSTOMER'S SECURE NETWORK            │
├─────────────────────────────────┤    ├─────────────────────────────────────────┤    ├───────────────────────────────────────────┤
│                                 │    │                                         │    │                                           │
│  ┌───────────────────────────┐  │    │  ┌─────────────────────────────────┐  │    │  ┌─────────────────────────────────────┐  │
│  │    CUSTARD FRONTEND       │  │    │  │          CUSTARD BACKEND        │  │    │  │          CONNECTOR AGENT            │  │
│  │   (React/TS on Vercel)    │  │    │  │       (FastAPI on Render)       │  │    │  │          (Docker Container)         │  │
│  └───────────────────────────┘  │    │  │                                 │  │    │  │                                     │  │
│               ↕                 │    │  │  • REST API (/api/v1)           │  │    │  │  • WebSocket Client                 │  │
│         HTTPS/WebSocket         │    │  │  • WebSocket Server             │  │    │  │  • Database Connection             │  │
│                                 │    │  │  • LLM Integration              │  │    │  │  • Schema Discovery                │  │
│                                 │    │  │  • Connection Management        │  │    │  │  • Query Execution                 │  │
│                                 │    │  └─────────────────────────────────┘  │    │  └─────────────────────────────────────┘  │
│                                 │    │               ↕                      │    │               ↕                        │
│                                 │    │         WebSocket/HTTPS              │    │         Secure WebSocket                │
│                                 │    │                                         │    │                                         │
│                                 │    │  ┌─────────────────────────────────┐  │    │  ┌─────────────────────────────────────┐  │
│                                 │    │  │         CUSTOMER DATABASE       │  │    │  │        CUSTOMER DATABASE            │  │
│                                 │    │  │      (Supabase/PostgreSQL)      │  │    │  │      (Supabase/PostgreSQL)         │  │
│                                 │    │  └─────────────────────────────────┘  │    │  └─────────────────────────────────────┘  │
│                                 │    │                                         │    │                                         │
│                                 │    │  ┌─────────────┐                    │    │  ┌─────────────┐                      │
│                                 │    │  │ LangSmith   │                    │    │  │ LangSmith   │                      │
│                                 │    │  └─────────────┘                    │    │  └─────────────┘                      │
│                                 │    └─────────────────────────────────────────┘    └───────────────────────────────────────────┘
```

## 📁 Project Structure

```
Custard/
├── backend/                    # FastAPI backend service
│   ├── api/v1/endpoints/      # API endpoint definitions (auth, connection, query, websocket)
│   ├── core/                  # Core services (JWT, email, API keys)
│   ├── db/                    # Database models, dependencies, and configuration
│   ├── llm/                   # AI/LLM services and integration
│   ├── schemas/               # Pydantic schemas for validation
│   ├── services/              # Business logic services
│   ├── ws/                    # WebSocket connection management
│   ├── alembic/               # Database migrations
│   └── main.py               # FastAPI application entry point
├── agent/                     # Connector agent service
│   ├── main.py               # Agent entry point
│   ├── schema_discoverer.py  # Database schema discovery
│   └── requirements.txt      # Agent dependencies
├── frontend/                 # React frontend with TypeScript and shadcn/ui
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/           # Application pages
│   │   ├── services/        # API service layer
│   │   ├── hooks/           # Custom React hooks
│   │   ├── contexts/        # React contexts
│   │   └── types/           # TypeScript type definitions
│   └── package.json         # Frontend dependencies
└── README.md                 # This file
```

## 🛠️ Technology Stack

### Backend
- **FastAPI 0.116.1**: Modern, fast web framework for building APIs
- **SQLAlchemy 2.0.43**: SQL toolkit and ORM
- **Alembic 1.16.5**: Database migration tool
- **WebSockets 15.0.1**: Real-time communication
- **LangChain 0.3.27**: LLM integration framework
- **OpenAI 1.105.0**: Natural language processing
- **JWT**: Secure authentication tokens with python-jose
- **Email Service**: User verification and password reset with Resend
- **Redis 5.2.0**: Caching and session management
- **Pydantic 2.11.7**: Data validation and serialization

### Frontend
- **React 18.3.1**: Modern UI library with hooks
- **TypeScript 5.8.3**: Type-safe JavaScript
- **Vite 5.4.19**: Fast build tool and dev server
- **shadcn/ui**: Beautiful, accessible UI components with Radix UI primitives
- **Tailwind CSS 3.4.17**: Utility-first CSS framework
- **React Router 6.30.1**: Client-side routing
- **TanStack Query 5.83.0**: Data fetching and caching
- **React Hook Form 7.61.1**: Form handling with validation
- **Zod 3.25.76**: Schema validation
- **Lucide React 0.462.0**: Icon library

### Agent
- **Python 3.11+**: Core agent logic
- **psycopg2-binary 2.9.10**: PostgreSQL database adapter
- **WebSockets 15.0.1**: Communication with backend
- **Docker**: Containerized deployment

### Database
- **PostgreSQL**: Primary database
- **SQLite**: Backend metadata storage

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL database
- OpenAI API key
- Docker (for agent deployment)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/custard.git
cd custard
```

### 2. Set Up Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the backend directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./custard_app.db
HOST=127.0.0.1
PORT=8000
RELOAD=true
JWT_SECRET_KEY=your_jwt_secret_key_here
RESEND_API_KEY=your_resend_api_key_here
REDIS_URL=redis://localhost:6379
```

Run database migrations:

```bash
alembic upgrade head
```

Start the backend server:

```bash
python main.py
```

The backend will be available at `http://127.0.0.1:8000`

### 3. Set Up Frontend

```bash
cd frontend
npm install
```

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. Set Up Agent

```bash
cd agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the agent directory:

```env
BACKEND_WEBSOCKET_URI=ws://localhost:8000/api/v1/connections/ws/agent-007
CONNECTION_ID=agent-007
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

Start the agent:

```bash
python main.py
```

### 5. Test the System

1. **Check Backend Health**:
   ```bash
   curl -X GET http://127.0.0.1:8000/health
   ```

2. **Create a Connection**:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1 \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Connection"}'
   ```

3. **Refresh Schema**:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/{connection_id}/refresh-schema \
     -H "Content-Type: application/json" \
     -d '{"agent_id": "agent-007"}'
   ```

4. **Ask a Question**:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{
       "connection_id": "your-connection-id",
       "question": "How many users do we have?",
       "agent_id": "agent-007"
     }'
   ```

## 📚 API Documentation

### Core Endpoints

#### Health Check
- **GET** `/health` - System health status
- **GET** `/status` - Detailed system status with agent connections

#### Authentication
- **POST** `/api/v1/auth/signup` - Register a new user
- **POST** `/api/v1/auth/login` - User login
- **POST** `/api/v1/auth/verify-email` - Verify user email
- **POST** `/api/v1/auth/forgot-password` - Request password reset
- **POST** `/api/v1/auth/reset-password` - Reset password with token
- **GET** `/api/v1/auth/profile` - Get user profile
- **PUT** `/api/v1/auth/profile` - Update user profile

#### Connections
- **POST** `/api/v1/connections` - Create a new connection with API key generation
- **GET** `/api/v1/connections` - List all connections with status and metadata
- **GET** `/api/v1/connections/{connection_id}` - Get specific connection details
- **POST** `/api/v1/connections/{connection_id}/refresh-schema` - Refresh database schema
- **DELETE** `/api/v1/connections/{connection_id}` - Delete connection

#### Queries
- **POST** `/api/v1/query` - Ask a natural language question

#### WebSocket
- **WS** `/api/v1/connections/ws/{agent_id}` - Agent connection endpoint

### Request/Response Examples

#### User Registration
```json
POST /api/v1/auth/signup
{
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Create Connection
```json
POST /api/v1/connections
{
  "name": "Production Database",
  "db_type": "POSTGRESQL"
}
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Production Database",
  "db_type": "POSTGRESQL",
  "status": "PENDING",
  "api_key": "custard_abc123...",
  "created_at": "2025-01-27T10:00:00Z"
}
```

#### Ask Question
```json
POST /api/v1/query
{
  "connection_id": "123e4567-e89b-12d3-a456-426614174000",
  "question": "How many orders were placed last month?",
  "agent_id": "agent-007"
}
```

#### Response
```json
{
  "answer": "The result is: 1,247 orders",
  "sql_query": "SELECT COUNT(*) FROM orders WHERE order_date >= '2024-01-01' AND order_date < '2024-02-01'"
}
```

## 🔒 Security Features

- **Read-only Access**: Agents can only execute SELECT queries
- **Secure WebSocket**: Encrypted communication between backend and agents
- **Sandboxed Execution**: Agents run in isolated Docker containers
- **Query Validation**: SQL queries are validated before execution
- **Connection Management**: Secure connection ID-based authentication
- **HTTPS**: All web traffic encrypted

## 🐳 Docker Deployment

### Agent Container

Create a `Dockerfile` in the agent directory:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:

```bash
# Option 1: Docker build and run
docker build -t custard-agent .
docker run -d --name custard-agent \
  -e BACKEND_WEBSOCKET_URI=ws://your-backend-url/api/v1/connections/ws/agent-007 \
  -e CONNECTION_ID=agent-007 \
  -e DB_HOST=your-db-host \
  -e DB_NAME=your-db-name \
  -e DB_USER=your-db-user \
  -e DB_PASSWORD=your-db-password \
  custard-agent

# Option 2: Docker Compose (recommended for development)
cd agent
docker-compose -f docker-compose-agent.yml up --build
```

## 🧪 Testing

### Unit Tests
```bash
cd backend
python -m pytest tests/
```

### Integration Tests
```bash
# Test backend health
curl -X GET http://127.0.0.1:8000/health

# Test agent connection
curl -X GET http://127.0.0.1:8000/test/agents
```

## 🐛 Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guide.

### Common Issues

1. **Agent won't connect**: Ensure backend is running first
2. **Schema not cached**: Refresh schema after agent connects
3. **Query timeout**: Check agent responsiveness and network connectivity
4. **Database connection failed**: Verify credentials and network access

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

## 🗺️ Roadmap

### ✅ Completed
- Backend API with FastAPI
- WebSocket communication system
- Agent with database connectivity
- Schema discovery and caching
- Query endpoint with LLM integration
- Message format standardization
- Error handling and validation
- User authentication system (signup, login, email verification)
- Password reset functionality with email verification
- React frontend with TypeScript and modern UI components
- Database connection management UI with CRUD operations
- Real-time connection status updates
- Modern UI with shadcn/ui components and Radix UI primitives
- Multi-tenant support with organizations
- JWT-based authentication with secure token handling
- Email service integration with Resend
- Production-ready error handling and loading states
- API key generation and management for agents
- Comprehensive form validation with Zod
- Responsive design with mobile support

### 🔄 In Progress
- Production deployment setup
- Advanced query optimization
- Query history and analytics
- Dashboard implementation with charts and insights

### 📋 Planned
- Advanced security features
- Performance monitoring
- Real-time dashboards
- Query optimization suggestions
- Additional database connectors (MySQL, MongoDB, Snowflake)
- Advanced query caching
- User role management
- Agent health monitoring
- Query performance analytics
- Custom dashboard widgets
- Advanced authentication (OAuth, SAML)

---

**Version**: 1.0.0  
**Last Updated**: January 2025
