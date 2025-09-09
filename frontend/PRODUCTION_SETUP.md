# Production Setup Guide

This guide provides step-by-step instructions for setting up the frontend application for production deployment.

## 🚀 Prerequisites

- Node.js 18+ or Bun
- Access to your production API
- Vercel account (or your preferred deployment platform)

## 📋 Environment Configuration

### 1. Create Environment Files

Create the following environment files in the frontend directory:

#### `.env.production`
```env
VITE_API_BASE_URL=https://api.custard.app
VITE_APP_NAME=Custard Analytics
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=production
VITE_DEBUG=false
```

#### `.env.development`
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Custard Analytics
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=development
VITE_DEBUG=true
```

#### `.env` (default for development)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Custard Analytics
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=development
VITE_DEBUG=true
```

### 2. Environment Variables Reference

| Variable | Description | Development | Production |
|----------|-------------|-------------|------------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` | `https://api.custard.app` |
| `VITE_APP_NAME` | Application name | `Custard Analytics` | `Custard Analytics` |
| `VITE_APP_VERSION` | Application version | `1.0.0` | `1.0.0` |
| `VITE_APP_ENV` | Environment name | `development` | `production` |
| `VITE_DEBUG` | Debug mode | `true` | `false` |

## 🔧 Build Configuration

### 1. TypeScript Configuration

The TypeScript configuration has been standardized for production:
- Strict type checking enabled
- Unused variables/parameters detection enabled
- Null checks enabled

### 2. Vite Configuration

The Vite configuration includes:
- Environment-specific builds
- Source maps disabled in production
- Code minification enabled in production
- Proper chunk splitting for optimization

## 🔐 Security Improvements

### 1. Token Security

- JWT tokens are now validated for expiration
- Secure token storage with metadata
- Automatic token cleanup on expiration
- Token refresh mechanism (placeholder for future implementation)

### 2. API Authentication

- All API calls now include proper Authorization headers
- Token validation before API requests
- Automatic logout on token expiration

### 3. Security Headers

The Vercel configuration includes security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

## 🚨 Error Handling

### 1. Global Error Handler

- Catches unhandled errors and promise rejections
- Rate limiting to prevent error spam
- Error reporting with unique IDs
- Session tracking for debugging

### 2. Error Boundaries

- Enhanced error boundary with user-friendly messages
- Error reporting functionality
- Development vs production error display
- Recovery options for users

## 🚀 Deployment

### 1. Vercel Deployment

The application is configured for Vercel deployment with:
- Bun as the package manager
- Production build command
- Security headers
- Environment variables

### 2. Build Commands

```bash
# Development build
bun run build:dev

# Production build
bun run build

# Staging build (if .env.staging exists)
bun run build:staging
```

### 3. Local Production Testing

```bash
# Build for production
bun run build

# Preview production build
bun run preview:prod
```

## 📊 Monitoring and Logging

### 1. Logging System

- Environment-aware logging (debug logs only in development)
- Structured logging with prefixes
- Error logging always enabled
- API response logging in development

### 2. Error Tracking

- Unique error IDs for tracking
- Session and user context in error reports
- Rate limiting to prevent spam
- Development vs production error details

## ✅ Production Checklist

Before deploying to production, ensure:

- [ ] Environment files are created with correct values
- [ ] API base URL points to production backend
- [ ] Debug mode is disabled
- [ ] All environment variables are set
- [ ] Production build completes successfully
- [ ] Error handling is working
- [ ] Authentication flow is tested
- [ ] API calls include proper headers
- [ ] Security headers are configured
- [ ] Error reporting is functional

## 🔍 Testing Production Build

### 1. Local Testing

```bash
# Build for production
bun run build

# Start preview server
bun run preview:prod

# Test in browser
open http://localhost:4173
```

### 2. Verification Steps

1. **Environment Variables**: Check that all environment variables are loaded correctly
2. **API Connectivity**: Verify API calls work with production URLs
3. **Authentication**: Test login/logout flow
4. **Error Handling**: Test error boundary functionality
5. **Performance**: Check bundle size and loading times
6. **Security**: Verify security headers are present

## 🐛 Troubleshooting

### Common Issues

1. **Environment Variables Not Loading**
   - Ensure files are named correctly (`.env.production`, not `.env.prod`)
   - Check that variables start with `VITE_`
   - Restart the development server after changes

2. **API Calls Failing**
   - Verify `VITE_API_BASE_URL` is correct
   - Check that backend is running and accessible
   - Ensure CORS is configured on backend

3. **Build Failures**
   - Check TypeScript errors: `bun run lint`
   - Verify all imports are correct
   - Ensure all environment variables have fallback values

4. **Authentication Issues**
   - Check that tokens are being stored correctly
   - Verify token expiration handling
   - Ensure API calls include Authorization headers

## 📞 Support

If you encounter issues during production setup:

1. Check the console for error messages
2. Review the error logs in the browser
3. Verify environment configuration
4. Test with a fresh build
5. Contact the development team with error details

---

**Last Updated**: January 2025  
**Version**: 1.0.0
