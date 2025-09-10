# WebSocket CORS Configuration

This document explains how to configure WebSocket CORS for both development and production environments.

## Overview

The WebSocket CORS system provides centralized, environment-aware CORS validation for all WebSocket endpoints. It automatically handles different configurations for development and production environments.

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment mode (`development`, `staging`, `production`) | `production` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed origins | `https://custard.app,https://app.custard.com` |

### Development Environment

In development mode, the system automatically adds common localhost origins:

- `http://localhost:3000`
- `http://localhost:8080`
- `http://localhost:5173`
- `https://localhost:3000`
- `https://localhost:8080`
- `https://localhost:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:8080`
- `http://127.0.0.1:5173`

**Example development configuration:**
```env
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Production Environment

In production mode, only explicitly configured origins are allowed. The system also supports subdomain matching.

**Example production configuration:**
```env
ENVIRONMENT=production
ALLOWED_ORIGINS=https://custard.app,https://app.custard.com
```

This configuration allows:
- `https://custard.app` (exact match)
- `https://app.custard.com` (exact match)
- `https://staging.custard.app` (subdomain of custard.app)
- `https://api.custard.app` (subdomain of custard.app)

## WebSocket Endpoints

The CORS validation is applied to:

1. **Status WebSocket** (`/api/v1/status/ws`)
   - Used by frontend for real-time status updates
   - Requires valid origin header

2. **Agent WebSocket** (`/api/v1/connections/ws/{agent_id}`)
   - Used by agent containers
   - Allows connections without origin header (for agents)

## Security Features

### Origin Validation
- Exact domain matching
- Subdomain matching in production
- Rejection of unknown origins with proper logging

### Logging
- All connection attempts are logged
- Rejected origins are logged with warnings
- Connection context is captured for monitoring

### Error Handling
- WebSocket connections are closed with appropriate error codes
- Graceful handling of malformed origins
- No information leakage in error responses

## Testing

### Test Development Configuration
```bash
ENVIRONMENT=development ALLOWED_ORIGINS=http://localhost:3000 python -c "
from core.websocket_cors import cors_validator
print('Development origins:', cors_validator.allowed_origins)
print('localhost:3000 allowed:', cors_validator.is_origin_allowed('http://localhost:3000'))
"
```

### Test Production Configuration
```bash
ENVIRONMENT=production ALLOWED_ORIGINS=https://custard.app python -c "
from core.websocket_cors import cors_validator
print('Production origins:', cors_validator.allowed_origins)
print('custard.app allowed:', cors_validator.is_origin_allowed('https://custard.app'))
print('staging.custard.app allowed:', cors_validator.is_origin_allowed('https://staging.custard.app'))
"
```

## Migration from Hardcoded Origins

The old hardcoded origin lists have been replaced with this centralized system. No code changes are needed - just update your environment variables.

### Before (Hardcoded)
```python
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8080", 
    "http://localhost:5173"
]
```

### After (Configuration-Driven)
```env
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

## Monitoring

Monitor WebSocket CORS activity through logs:

- **INFO**: Successful connections
- **WARNING**: Rejected origins
- **DEBUG**: Detailed connection context

Example log entries:
```
INFO: status-websocket connection attempt from origin: https://custard.app
INFO: status-websocket connection allowed for origin: https://custard.app
WARNING: status-websocket connection rejected - origin not allowed: https://malicious.com
```
