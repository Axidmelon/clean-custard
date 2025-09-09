# Environment Configuration Guide

This guide explains how to configure the frontend application for different environments (development, staging, production).

## Environment Files

The application uses Vite's environment variable system with the following files:

- `.env` - Default environment (development)
- `.env.development` - Development environment
- `.env.production` - Production environment
- `.env.staging` - Staging environment (optional)

## Available Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` | `https://api.custard.app` |
| `VITE_APP_NAME` | Application name | `Custard` | `Custard` |
| `VITE_APP_VERSION` | Application version | `1.0.0` | `1.0.0` |
| `VITE_APP_ENV` | Environment name | `development` | `production` |
| `VITE_DEBUG` | Debug mode flag | `true` | `false` |

## Running in Different Environments

### Development
```bash
npm run dev
# or explicitly
npm run dev --mode development
```

### Production
```bash
npm run dev:prod
# or
npm run dev --mode production
```

### Building for Different Environments

```bash
# Development build
npm run build:dev

# Production build
npm run build

# Staging build (if .env.staging exists)
npm run build:staging
```

## Configuration Management

All hardcoded values have been moved to `/src/lib/constants.ts`:

- API endpoints use `getApiBaseUrl()`
- Default values are centralized in `APP_CONFIG`
- Timeout values are configurable
- Database ports are standardized
- Documentation links are centralized

## Environment-Specific Features

### Development
- Debug mode enabled
- Console logging active
- Source maps enabled
- Hot reload enabled

### Production
- Debug mode disabled
- Console logging stripped
- Minified code
- Optimized bundle

## Testing Environment Configuration

You can test the environment configuration by importing and calling the test function:

```typescript
import { testEnvironmentConfig } from '@/lib/env-test';

// Call this in your component or console
testEnvironmentConfig();
```

## Migration from Hardcoded Values

The following hardcoded values have been replaced:

### Before
```typescript
const response = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
  // ...
});
```

### After
```typescript
import { getApiBaseUrl } from '@/lib/constants';

const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
  // ...
});
```

## Best Practices

1. **Never hardcode URLs** - Always use `getApiBaseUrl()`
2. **Use constants** - Import from `APP_CONFIG` for default values
3. **Environment-specific builds** - Use appropriate npm scripts
4. **Test configurations** - Verify environment variables are loaded correctly
5. **Document changes** - Update this guide when adding new environment variables

## Troubleshooting

### Environment Variables Not Loading
1. Check that the `.env` file exists in the frontend directory
2. Ensure variable names start with `VITE_`
3. Restart the development server after changing environment files

### API Calls Failing
1. Verify `VITE_API_BASE_URL` is set correctly
2. Check that the backend is running on the specified URL
3. Ensure CORS is configured properly on the backend

### Build Issues
1. Make sure all environment variables have fallback values
2. Check that constants are properly imported
3. Verify TypeScript types are correct
