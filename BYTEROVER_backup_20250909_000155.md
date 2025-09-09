# Byterover Handbook

*Generated: 2025-01-27*

## Layer 1: System Overview

**Purpose**: Custard AI Data Agent Platform - A secure, AI-powered platform that allows users to ask natural language questions about their databases and get instant, accurate answers. Custard bridges the gap between business users and complex database queries through intelligent AI agents.

**Tech Stack**: 
- Backend: FastAPI, SQLAlchemy, Alembic, WebSockets, LangChain, OpenAI GPT-4, JWT, Python 3.11+
- Frontend: React 18, TypeScript, Vite, shadcn/ui, Tailwind CSS, React Router, React Query, React Hook Form
- Agent: Python, psycopg2, WebSockets, Docker
- Database: PostgreSQL, SQLite

**Architecture**: Microservices Architecture with three main components:
1. **Frontend** (React/TS on Vercel) - Modern web interface with real-time UI
2. **Backend** (FastAPI on Render) - REST API, WebSocket server, LLM integration, connection management
3. **Agent** (Docker Container) - WebSocket client, database connection, schema discovery, query execution

**Key Technical Decisions**:
- WebSocket-based real-time communication between backend and agents
- Read-only safety: Agents can only execute SELECT queries
- Multi-tenant support with organization-based user management
- JWT-based authentication with email verification
- Schema discovery and caching for performance
- Sandboxed agent execution in Docker containers

**Entry Points**: 
- Backend: `/Users/axid/custard/backend/main.py` (FastAPI app)
- Frontend: `/Users/axid/custard/frontend/src/main.tsx` (React app)
- Agent: `/Users/axid/custard/agent/main.py` (Agent service)

---

## Layer 2: Module Map

**Core Modules**:
- **Authentication Module** (`/backend/api/v1/endpoints/auth.py`) - User registration, login, email verification, password reset
- **Connection Module** (`/backend/api/v1/endpoints/connection.py`) - Database connection management, CRUD operations
- **Query Module** (`/backend/api/v1/endpoints/query.py`) - Natural language query processing with LLM integration
- **WebSocket Module** (`/backend/ws/connection_manager.py`) - Real-time communication with agents
- **Frontend Pages** (`/frontend/src/pages/`) - Dashboard, Connections, Login, Signup, Settings, TalkData

**Data Layer**:
- **Database Models** (`/backend/db/models.py`) - SQLAlchemy models for users, organizations, connections
- **Schemas** (`/backend/schemas/`) - Pydantic schemas for API validation
- **Database Configuration** (`/backend/db/database.py`) - SQLAlchemy engine and session management
- **Migrations** (`/backend/alembic/versions/`) - Database schema migrations

**Integration Points**:
- **API Endpoints** (`/backend/api/v1/endpoints/`) - REST API endpoints for all functionality
- **WebSocket Endpoints** (`/backend/main.py`) - Real-time agent communication
- **Frontend Services** (`/frontend/src/services/`) - API service layer with error handling
- **LLM Services** (`/backend/llm/services.py`) - OpenAI integration for natural language processing

**Utilities**:
- **JWT Handler** (`/backend/core/jwt_handler.py`) - Token generation and validation
- **Email Service** (`/backend/core/email_service.py`) - User verification and password reset emails
- **API Key Service** (`/backend/core/api_key_service.py`) - API key management
- **Frontend Hooks** (`/frontend/src/hooks/`) - Custom React hooks for data fetching

**Module Dependencies**:
- Frontend → Backend API (HTTP/WebSocket)
- Backend → Database (SQLAlchemy)
- Backend → LLM (OpenAI API)
- Backend → Email Service (Resend)
- Agent → Backend (WebSocket)
- Agent → Customer Database (psycopg2)

---

## Layer 3: Integration Guide

**API Endpoints**:
- **Authentication**: `/api/v1/auth/signup`, `/api/v1/auth/login`, `/api/v1/auth/verify-email`, `/api/v1/auth/forgot-password`, `/api/v1/auth/reset-password`
- **Connections**: `/api/v1/connections` (GET, POST), `/api/v1/connections/{id}` (GET, DELETE), `/api/v1/connections/{id}/refresh-schema` (POST)
- **Queries**: `/api/v1/query` (POST)
- **WebSocket**: `/api/v1/connections/ws/{agent_id}` (WebSocket)
- **Health**: `/health`, `/status`

**Configuration Files**:
- **Backend Environment** (`.env`): `OPENAI_API_KEY`, `DATABASE_URL`, `HOST`, `PORT`, `RELOAD`
- **Frontend Environment** (`.env`): `VITE_API_BASE_URL`
- **Agent Environment** (`.env`): `BACKEND_WEBSOCKET_URI`, `CONNECTION_ID`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **Vite Config** (`/frontend/vite.config.ts`): Proxy configuration for API calls
- **Database Config** (`/backend/alembic.ini`): Migration configuration

**External Integrations**:
- **OpenAI API** - Natural language processing and query generation
- **Resend** - Email service for user verification and password reset
- **PostgreSQL** - Primary database for application data
- **SQLite** - Backend metadata storage
- **LangSmith** - LLM monitoring and debugging

**Workflows**:
1. **User Registration**: Signup → Email Verification → Login → Dashboard
2. **Connection Management**: Create Connection → Agent Connection → Schema Discovery → Query Execution
3. **Query Processing**: Natural Language Input → LLM Processing → SQL Generation → Agent Execution → Result Display
4. **Real-time Communication**: Frontend ↔ Backend (HTTP) ↔ Agent (WebSocket) ↔ Database

**Interface Definitions**:
- **API Types** (`/frontend/src/types/api.ts`) - TypeScript interfaces for API communication
- **Pydantic Schemas** (`/backend/schemas/`) - Request/response validation
- **WebSocket Messages** - JSON-based message format for agent communication

---

## Layer 4: Extension Points

**Design Patterns**:
- **Repository Pattern** - Database access abstraction in services
- **Dependency Injection** - FastAPI dependency system for database sessions
- **Observer Pattern** - WebSocket connection management and event handling
- **Factory Pattern** - Agent creation and connection management
- **Strategy Pattern** - Different database connector implementations

**Extension Points**:
- **Database Connectors** - Add support for MySQL, MongoDB, Snowflake (currently supports PostgreSQL)
- **LLM Providers** - Switch from OpenAI to other LLM providers
- **Authentication Methods** - Add OAuth, SAML, or other auth providers
- **Query Optimization** - Add query caching and performance monitoring
- **Agent Plugins** - Extend agent functionality with custom plugins

**Customization Areas**:
- **UI Components** - shadcn/ui components can be customized and extended
- **API Middleware** - Add custom middleware for logging, rate limiting, etc.
- **Database Migrations** - Alembic migrations for schema changes
- **WebSocket Handlers** - Custom message handlers for agent communication
- **Email Templates** - Customize verification and reset password emails

**Plugin Architecture**:
- **Agent Plugins** - Extend agent functionality with custom database connectors
- **API Plugins** - Add custom endpoints and middleware
- **Frontend Plugins** - Add custom pages and components
- **LLM Plugins** - Add custom prompt templates and processing logic

**Recent Changes**:
- Connections page transformed into production-ready application with real-time data fetching
- Added comprehensive error handling and loading states
- Implemented React Query for efficient data fetching and caching
- Added CRUD operations for connection management
- Restructured connections page to show only Supabase, Snowflake, MongoDB, and MySQL databases

---

*Byterover handbook optimized for agent navigation and human developer onboarding*
