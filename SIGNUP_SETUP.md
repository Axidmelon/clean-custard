# Signup Integration Setup

The frontend signup is now connected to the backend database. Here's what has been implemented:

## What's Working

1. **Frontend Signup Form** (`/frontend/src/app/signup/page.tsx`)
   - Collects email, password, and name
   - Calls the backend API to create user in database
   - Redirects to verification page after successful signup

2. **API Route** (`/frontend/src/app/api/auth/signup/route.ts`)
   - Proxies signup requests to backend
   - Each user gets their own unique organization ID
   - Handles error responses from backend

3. **Backend Integration** (`/backend/api/v1/endpoints/auth.py`)
   - Creates user in database with hashed password
   - Creates unique organization for each user
   - Generates verification token
   - Sends verification email

4. **Verification Flow** (`/frontend/src/app/verify/page.tsx`)
   - Shows verification pending message after signup
   - Handles email verification via token

## Environment Variables

Create a `.env.local` file in the frontend directory with:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
```

## Testing the Flow

1. Start the backend server:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload --port 8000
   ```

2. Start the frontend server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Visit `http://localhost:3000/signup`
4. Fill out the form and submit
5. Check your email for verification link
6. Click the verification link to complete the process

## Database Schema

The signup creates a user record with:
- `id`: UUID (auto-generated)
- `email`: User's email address
- `hashed_password`: Bcrypt hashed password
- `organization_id`: Unique organization UUID (one per user)
- `is_verified`: Boolean (false initially)
- `verification_token`: UUID for email verification
- `created_at`: Timestamp

## Notes

- Each user gets their own unique organization for true multi-tenancy
- Organization name is based on user's email (e.g., "john@example.com" → "john's Organization")
- Email verification is required before users can log in
- Password is hashed using bcrypt before storage
- All database operations are handled by the backend API
