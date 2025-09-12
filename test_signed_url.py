#!/usr/bin/env python3
"""
Simple test script for the signed URL functionality
Run this after starting both backend and frontend servers
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8080"

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/files/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is running")
            print(f"   Cloudinary configured: {data.get('configured', False)}")
            print(f"   Cloud name: {data.get('cloud_name', 'N/A')}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def test_frontend_health():
    """Test if frontend is running"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"❌ Frontend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        return False

def test_signed_url_endpoint():
    """Test the signed URL endpoint (requires authentication)"""
    print("\n🔧 Testing Signed URL Endpoint...")
    print("   Note: This test requires authentication")
    print("   Please ensure you have a valid JWT token")
    
    # You would need to provide a valid JWT token and file ID
    # For now, just show the expected format
    print("\n   To test manually:")
    print(f"   curl -X GET '{BACKEND_URL}/api/v1/files/signed-url/{{file_id}}' \\")
    print("     -H 'Authorization: Bearer {{your_jwt_token}}'")
    
    return True

def show_testing_instructions():
    """Show manual testing instructions"""
    print("\n📋 Manual Testing Instructions:")
    print("=" * 50)
    
    print("\n1. 🌐 Open your browser and go to:")
    print(f"   {FRONTEND_URL}/talk-data")
    
    print("\n2. 🔐 Make sure you're logged in")
    
    print("\n3. 📁 Upload a CSV file if you haven't already:")
    print(f"   {FRONTEND_URL}/uploads")
    
    print("\n4. 🧪 Test the CSV loading:")
    print("   - Go to Talk Data page")
    print("   - Select a CSV file from the dropdown")
    print("   - Watch the browser console (F12)")
    print("   - You should see logs about signed URL generation")
    
    print("\n5. 📊 Expected Console Logs:")
    print("   Loading CSV via signed URL: filename.csv")
    print("   Got signed URL, fetching content directly from Cloudinary")
    print("   Successfully fetched CSV content from Cloudinary")
    
    print("\n6. ⚡ Performance Test:")
    print("   - Open Chrome DevTools (F12)")
    print("   - Go to Network tab")
    print("   - Select a CSV file")
    print("   - Check the load time (should be <500ms)")
    
    print("\n7. 🔄 Cache Test:")
    print("   - Select the same CSV file again")
    print("   - Should see 'Using cached signed URL' in console")
    
    print("\n8. 🛡️ Fallback Test:")
    print("   - Block res.cloudinary.com in DevTools")
    print("   - Select a CSV file")
    print("   - Should fallback to backend and still work")

def main():
    """Main test function"""
    print("🧪 CSV Performance Optimization - Test Script")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test backend health
    backend_ok = test_backend_health()
    
    # Test frontend health
    frontend_ok = test_frontend_health()
    
    # Test signed URL endpoint (info only)
    test_signed_url_endpoint()
    
    if backend_ok and frontend_ok:
        print("\n✅ Both servers are running!")
        show_testing_instructions()
    else:
        print("\n❌ Some servers are not running. Please check:")
        if not backend_ok:
            print("   - Backend server (python main.py)")
        if not frontend_ok:
            print("   - Frontend server (npm run dev)")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()
