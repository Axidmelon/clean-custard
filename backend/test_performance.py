#!/usr/bin/env python3
"""
Performance test script for signed URL generation
"""
import time
import requests
import json
from datetime import datetime

def test_signed_url_performance():
    """Test the performance of signed URL generation"""
    
    # Test file ID (you'll need to replace this with an actual file ID)
    test_file_id = "dd4d467d-bd5a-4d19-8573-90dd6dfb4111"  # From the console logs
    
    # Test URL
    base_url = "http://localhost:8000"
    signed_url_endpoint = f"{base_url}/api/v1/files/signed-url/{test_file_id}"
    
    print(f"🚀 Testing signed URL performance for file: {test_file_id}")
    print(f"📅 Test started at: {datetime.now()}")
    print("-" * 60)
    
    # Test multiple requests to see caching in action
    for i in range(3):
        print(f"\n🔄 Test #{i+1}:")
        
        start_time = time.time()
        
        try:
            # Make request (you'll need to add proper authentication)
            response = requests.get(signed_url_endpoint, timeout=10)
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                cached = data.get('cached', False)
                print(f"✅ Success: {duration_ms:.1f}ms (cached: {cached})")
                
                if 'signed_url' in data:
                    print(f"🔗 URL generated: {data['signed_url'][:50]}...")
                if 'expires_at' in data:
                    print(f"⏰ Expires at: {data['expires_at']}")
                    
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            print(f"❌ Request failed: {e} ({duration_ms:.1f}ms)")
    
    print("\n" + "=" * 60)
    print("🎯 Performance Test Complete!")
    print("📊 Expected results:")
    print("   - First request: ~100-500ms (new URL generation)")
    print("   - Subsequent requests: <50ms (cached responses)")

if __name__ == "__main__":
    test_signed_url_performance()
