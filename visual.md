# Custard System Architecture

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
│         HTTP(S) Request         │◄───►│  │  • WebSocket Server (/ws)       │  │◄──►│  │  • Security Sandbox                 │  │
│         & Response              │    │  │  • Query Orchestrator           │  │    │  │  • Query Executor (psycopg2)        │  │
│                                 │    │  │  • LLM Service (LangChain)      │  │    │  └─────────────────────────────────────┘  │
│  User asks question,            │    │  └─────────────────────────────────┘  │    │                    │                    │
│  sees final answer              │    │              │        │              │    │                    │ (SQL, Read-Only)   │
└─────────────────────────────────┘    │              │        │              │    │                    ▼                    │
                                       │              │        ▼              │    │  ┌─────────────────────────────────────┐  │
                                       │              │  ┌─────────────┐      │    │  │          CUSTOMER'S DB              │  │
                                       │              │  │ OpenAI API  │      │    │  │          (Supabase/PostgreSQL)      │  │
                                       │              │  └─────────────┘      │    │  └─────────────────────────────────────┘  │
                                       │              ▼                      │    │                                           │
                                       │  ┌─────────────────┐                │    └───────────────────────────────────────────┘
                                       │  │ Application DB  │                │
                                       │  │ (PostgreSQL)    │                │
                                       │  └─────────────────┘                │
                                       │         │                           │
                                       │         ▼                           │
                                       │  ┌─────────────┐                    │
                                       │  │ LangSmith   │                    │
                                       │  └─────────────┘                    │
                                       └─────────────────────────────────────┘
```

## Communication Flow

1. **User Interaction**: User asks questions through the React frontend
2. **API Processing**: Backend processes requests via REST API and WebSocket
3. **Query Orchestration**: Backend coordinates with LLM services and manages queries
4. **Agent Communication**: Secure WebSocket connection to customer's agent
5. **Database Query**: Agent executes read-only SQL queries on customer's database
6. **Response Chain**: Results flow back through the system to the user

## Detailed Query Flow

```
User Question → Frontend → Backend API → LLM Service → Agent → Database → Agent → Backend → Frontend → User Answer
```

### Step-by-Step Process:
1. **Question Input**: User submits "How many engineers?" via frontend
2. **API Call**: Frontend sends POST to `/api/v1/query` with connection_id, question, agent_id
3. **Schema Retrieval**: Backend fetches cached database schema for the connection
4. **SQL Generation**: LLM service (OpenAI) converts question to SQL query
5. **Agent Communication**: Backend sends SQL query to agent via WebSocket
6. **Query Execution**: Agent executes read-only SQL on customer's database
7. **Result Processing**: Agent sends results back to backend
8. **Response Formatting**: Backend formats results into human-readable answer
9. **User Response**: Frontend displays the final answer to user

## Key Components

### Frontend
- **Technology**: React/TypeScript application
- **Hosting**: Vercel
- **Purpose**: User interface for asking questions and viewing results

### Backend (FastAPI)
- **API Endpoints**: 
  - `POST /api/v1` - Create connections
  - `POST /api/v1/query` - Process user questions
  - `POST /api/v1/{id}/refresh-schema` - Refresh database schema
  - `GET /health` - Health check
- **WebSocket Server**: Real-time communication with agents
- **LLM Integration**: OpenAI API for SQL generation
- **Database**: SQLite for connection management

### Agent (Docker Container)
- **WebSocket Client**: Connects to backend
- **Database Access**: Direct connection to customer's database
- **Security Sandbox**: Read-only query execution
- **Schema Discovery**: Automatic database schema detection
- **Query Execution**: Safe SQL query processing

### Database
- **Customer Database**: Supabase/PostgreSQL instance
- **Backend Database**: SQLite for connection metadata
- **Schema Caching**: Stored schema for efficient query generation

### AI Services
- **OpenAI API**: GPT-4 for natural language to SQL conversion
- **LangChain**: Framework for LLM integration
- **LangSmith**: Optional monitoring and debugging

## Security Features

- **Read-Only Access**: Agent can only execute SELECT queries
- **Secure WebSocket**: Encrypted communication between backend and agent
- **Sandboxed Execution**: Agent runs in isolated Docker container
- **HTTPS**: All web traffic encrypted
- **Query Validation**: SQL queries are validated before execution
- **Connection Management**: Secure connection ID-based authentication

## Current Implementation Status

### ✅ Completed Features
- Backend API with FastAPI
- WebSocket communication system
- Agent with database connectivity
- Schema discovery and caching
- Query endpoint with LLM integration
- Message format standardization
- Error handling and validation

### 🔄 In Progress
- Frontend React application
- Production deployment setup
- Advanced query optimization

### 📋 Planned Features
- Multi-tenant support
- Query history and analytics
- Advanced security features
- Performance monitoring
