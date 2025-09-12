# CSV Performance Optimization - Testing Guide

## 🧪 Testing Plan for Pre-signed URL Implementation

This guide will help you test the new CSV data transport optimization to ensure it's working correctly and delivering the expected performance improvements.

---

## 📋 Pre-Testing Checklist

### Backend Requirements
- [ ] Cloudinary is properly configured (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET)
- [ ] Backend server is running on `http://localhost:8000`
- [ ] Database has uploaded CSV files
- [ ] User authentication is working

### Frontend Requirements
- [ ] Frontend is running on `http://localhost:8080`
- [ ] User is logged in
- [ ] At least one CSV file is uploaded and visible in the Uploads page

---

## 🔧 Backend API Testing

### 1. Test Signed URL Generation

**Endpoint**: `GET /api/v1/files/signed-url/{file_id}`

```bash
# Test with curl (replace {file_id} and {token} with actual values)
curl -X GET "http://localhost:8000/api/v1/files/signed-url/{file_id}?expiration_hours=2" \
  -H "Authorization: Bearer {your_jwt_token}" \
  -H "Content-Type: application/json"
```

**Expected Response**:
```json
{
  "success": true,
  "signed_url": "https://res.cloudinary.com/your-cloud/raw/upload/v1234567890/signature=abc123~expires=1705324800~public_id=uploads/2024/01/user123/file.csv",
  "expires_at": 1705324800,
  "expires_in_hours": 2,
  "file_info": {
    "filename": "test.csv",
    "size": 49700,
    "content_type": "text/csv",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2. Test Direct Cloudinary Access

```bash
# Test the signed URL directly
curl -X GET "{signed_url_from_step_1}"
```

**Expected**: CSV file content should be returned directly from Cloudinary

### 3. Test Fallback Endpoint

```bash
# Test the fallback endpoint
curl -X GET "http://localhost:8000/api/v1/files/content/{file_id}" \
  -H "Authorization: Bearer {your_jwt_token}"
```

**Expected**: CSV file content returned via backend proxy

---

## 🖥️ Frontend Testing

### 1. Basic CSV Loading Test

1. **Navigate to Talk Data page**
   - Go to `http://localhost:8080/talk-data`
   - Should see database and CSV file dropdowns

2. **Select a CSV file**
   - Choose a CSV file from the dropdown
   - Watch the browser console for logs

**Expected Console Logs**:
```
Loading CSV via signed URL: filename.csv
Got signed URL, fetching content directly from Cloudinary
Successfully fetched CSV content from Cloudinary
```

3. **Verify CSV Preview**
   - Blue callout should appear with "CSV Data Preview"
   - Table should show first 50 rows
   - Loading should complete in <500ms

### 2. Performance Testing

**Test with Network Throttling**:
1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Throttle to "Slow 3G"
4. Select a CSV file and measure load time

**Expected Performance**:
- **Before optimization**: 2-5 seconds
- **After optimization**: <1 second

### 3. Fallback Testing

**Simulate Signed URL Failure**:
1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Right-click and "Block request domain" for `res.cloudinary.com`
4. Select a CSV file

**Expected Behavior**:
- Console should show: "Signed URL method failed, falling back to backend proxy"
- CSV should still load successfully via backend

### 4. Cache Testing

**Test URL Caching**:
1. Select a CSV file (first time)
2. Deselect and select the same file again
3. Check console logs

**Expected**:
- First load: "Fetching new signed URL"
- Second load: "Using cached signed URL"

---

## 📊 Performance Metrics to Track

### Key Metrics
- **Time to First Byte**: Should be <100ms
- **Total Load Time**: Should be <500ms
- **Cache Hit Rate**: Should be >80% on second load
- **Error Rate**: Should be <1%

### Network Analysis
1. **Open DevTools Network tab**
2. **Select a CSV file**
3. **Check the requests**:
   - Should see: `GET /api/v1/files/signed-url/{file_id}`
   - Should see: `GET https://res.cloudinary.com/...` (direct to Cloudinary)
   - Should NOT see: `GET /api/v1/files/content/{file_id}` (unless fallback)

---

## 🐛 Common Issues & Troubleshooting

### Issue 1: "Failed to get signed URL"
**Cause**: Cloudinary not configured or file not found
**Solution**: 
- Check Cloudinary environment variables
- Verify file exists in database
- Check user authentication

### Issue 2: CORS Errors
**Cause**: Cloudinary CORS not configured for your domain
**Solution**:
- Configure CORS in Cloudinary dashboard
- Allow origin: `http://localhost:8080`

### Issue 3: Signed URL Expired
**Cause**: URL expired (default 2 hours)
**Solution**:
- URLs auto-refresh 30 minutes before expiration
- Check cache status in console

### Issue 4: Slow Performance
**Cause**: Network issues or large files
**Solution**:
- Check network throttling in DevTools
- Verify Cloudinary CDN is working
- Check file size (<10MB recommended)

---

## 📈 Success Criteria

### ✅ Performance Goals
- [ ] CSV load time <500ms (vs 1200ms before)
- [ ] Backend bandwidth usage reduced by 95%
- [ ] Cache hit rate >80% for repeated loads
- [ ] Error rate <1%

### ✅ User Experience Goals
- [ ] CSV preview appears quickly
- [ ] No loading spinners for >1 second
- [ ] Smooth fallback if direct access fails
- [ ] Clear error messages if something goes wrong

### ✅ Technical Goals
- [ ] Signed URLs generate correctly
- [ ] Direct Cloudinary access works
- [ ] Fallback mechanism functions
- [ ] Caching works properly
- [ ] No memory leaks or performance degradation

---

## 🚀 Advanced Testing

### Load Testing
```bash
# Test with multiple concurrent requests
for i in {1..10}; do
  curl -X GET "http://localhost:8000/api/v1/files/signed-url/{file_id}" \
    -H "Authorization: Bearer {token}" &
done
wait
```

### Security Testing
1. **Test expired URLs**: Wait 2+ hours and try to access
2. **Test unauthorized access**: Try accessing other users' files
3. **Test URL manipulation**: Try modifying signed URL parameters

### Browser Compatibility
Test in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

---

## 📝 Test Results Template

```
Test Date: ___________
Tester: ___________

Backend API Tests:
[ ] Signed URL generation works
[ ] Direct Cloudinary access works
[ ] Fallback endpoint works

Frontend Tests:
[ ] CSV loading works
[ ] Performance improvement visible
[ ] Fallback mechanism works
[ ] Caching works

Performance Metrics:
- Average load time: _____ms
- Cache hit rate: _____%
- Error rate: _____%

Issues Found:
1. ___________
2. ___________

Overall Status: [ ] PASS [ ] FAIL [ ] NEEDS WORK
```

---

## 🎯 Next Steps After Testing

### If Tests Pass:
1. Deploy to staging environment
2. Run full integration tests
3. Monitor performance metrics
4. Plan production rollout

### If Tests Fail:
1. Check error logs in console
2. Verify Cloudinary configuration
3. Test individual components
4. Fix issues and retest

### Performance Monitoring:
1. Set up monitoring for signed URL generation
2. Track cache hit rates
3. Monitor error rates
4. Measure user satisfaction

---

*Happy Testing! 🚀*
