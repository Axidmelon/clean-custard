# Vercel Environment Variables Configuration

## Required Environment Variables for Vercel Deployment

Configure these environment variables in your Vercel dashboard:

### Core Application Settings
- `VITE_APP_ENV` = `production`
- `VITE_DEBUG` = `false`
- `VITE_APP_NAME` = `Custard` (optional, defaults to "Custard")
- `VITE_APP_VERSION` = `1.0.0` (optional, defaults to "1.0.0")

### API Configuration
- `VITE_API_BASE_URL` = Your backend API URL (e.g., `https://your-backend-domain.com/api/v1`)

## Environment Variable Setup in Vercel

1. Go to your Vercel project dashboard
2. Navigate to Settings → Environment Variables
3. Add each variable above with the appropriate values
4. Make sure to set them for Production environment
5. Redeploy your application after adding the variables

## Notes

- The `VITE_API_BASE_URL` should point to your backend API endpoint
- If not set, the app will default to `/api/v1` (relative path)
- All environment variables prefixed with `VITE_` are available in the frontend code
- The build process will embed these values into the production bundle

