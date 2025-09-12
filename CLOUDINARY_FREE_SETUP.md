# Cloudinary Free Setup Guide 🆓

Cloudinary offers **25GB storage + 25GB bandwidth per month** completely FREE! No credit card required.

## Step 1: Create Free Cloudinary Account

1. Go to [cloudinary.com](https://cloudinary.com/)
2. Click "Sign Up For Free"
3. Fill in your details (no credit card required)
4. Verify your email

## Step 2: Get Your Credentials

1. After signing up, go to your [Dashboard](https://cloudinary.com/console)
2. You'll see your credentials:
   - **Cloud Name**: `your-cloud-name`
   - **API Key**: `123456789012345`
   - **API Secret**: `your-secret-key`

## Step 3: Configure Environment Variables

### For Local Development
Create a `.env` file in your backend directory:

```bash
# Cloudinary Configuration (FREE)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### For Production (Railway)
Set these environment variables in your Railway dashboard:

```bash
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## Step 4: Test the Setup

1. Start your backend server
2. Check the upload service status:
   ```bash
   curl http://localhost:8000/api/v1/files/status
   ```

## Cloudinary Free Tier Limits

- ✅ **25GB storage** (plenty for most projects)
- ✅ **25GB bandwidth** per month
- ✅ **10MB max file size** per upload
- ✅ **Unlimited transformations**
- ✅ **No credit card required**
- ✅ **No expiration date**

## File Organization

Files will be organized in Cloudinary as:
```
custard-uploads/
├── uploads/
│   ├── 2024/
│   │   ├── 01/
│   │   │   ├── user-123/
│   │   │   │   ├── uuid-file1.csv
│   │   │   │   └── uuid-file2.pdf
```

## Benefits of Cloudinary

1. **Image Optimization**: Automatically optimizes images
2. **Multiple Formats**: Supports images, videos, documents
3. **CDN**: Global content delivery network
4. **Transformations**: Resize, crop, filter images on-the-fly
5. **Analytics**: Track usage and performance

## Alternative Free Options

If Cloudinary doesn't work for you:

### Firebase Storage (Google)
- **Free**: 1GB storage + 10GB downloads/month
- **Setup**: [firebase.google.com](https://firebase.google.com/)

### AWS S3 (Amazon)
- **Free**: 5GB storage for 12 months (new accounts)
- **Setup**: [aws.amazon.com/s3](https://aws.amazon.com/s3/)

### Supabase Storage
- **Free**: 1GB storage + 2GB bandwidth/month
- **Setup**: [supabase.com](https://supabase.com/)

## Quick Start Commands

```bash
# Install dependencies
pip install cloudinary

# Test upload (replace with your credentials)
python -c "
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name='your-cloud-name',
    api_key='your-api-key',
    api_secret='your-api-secret'
)

result = cloudinary.uploader.upload('test.txt')
print('Upload successful:', result['secure_url'])
"
```

## Troubleshooting

### "Invalid credentials"
- Double-check your Cloud Name, API Key, and API Secret
- Make sure there are no extra spaces

### "File too large"
- Cloudinary free tier has 10MB file size limit
- Consider compressing files or upgrading

### "Bandwidth exceeded"
- You've used your 25GB monthly bandwidth
- Wait for next month or upgrade plan

## Cost Comparison

| Service | Free Storage | Free Bandwidth | Max File Size |
|---------|-------------|----------------|---------------|
| **Cloudinary** | 25GB | 25GB/month | 10MB |
| Firebase | 1GB | 10GB/month | 5GB |
| AWS S3 | 5GB | 20GB/month | 5GB |
| Supabase | 1GB | 2GB/month | 50MB |

**Cloudinary wins for free tier!** 🏆
