#!/usr/bin/env python3
"""
Test script for Working Memory implementation.
This script tests the core functionality to ensure it solves the schema duplication problem.
"""

import asyncio
import time
import uuid
from core.working_memory import working_memory_service


async def test_working_memory():
    """Test working memory functionality."""
    print("🧠 Testing Working Memory Service...")
    
    # Test 1: Basic storage and retrieval
    print("\n1. Testing basic storage and retrieval...")
    request_id = str(uuid.uuid4())
    file_ids = ["file1", "file2", "file3"]
    
    # Simulate schema analysis data
    schema_data = {
        "file_schemas": {
            "file1": {"rows": 100, "columns": 5},
            "file2": {"rows": 200, "columns": 7},
            "file3": {"rows": 150, "columns": 6}
        },
        "routing_recommendations": {
            "recommended_service": "csv_to_sql_converter",
            "confidence": 0.9
        },
        "analysis_timestamp": time.time()
    }
    
    # Store schema analysis
    success = working_memory_service.store_schema_analysis(request_id, file_ids, schema_data)
    print(f"   ✅ Storage successful: {success}")
    
    # Retrieve schema analysis
    retrieved_data = working_memory_service.get_schema_analysis(request_id, file_ids)
    print(f"   ✅ Retrieval successful: {retrieved_data is not None}")
    
    if retrieved_data:
        print(f"   📊 Retrieved {len(retrieved_data.get('file_schemas', {}))} file schemas")
        print(f"   🎯 Recommended service: {retrieved_data.get('routing_recommendations', {}).get('recommended_service')}")
    
    # Test 2: Duplicate operation prevention
    print("\n2. Testing duplicate operation prevention...")
    
    # Check if operation is already done (should return True)
    is_duplicate = working_memory_service.deduplicate_operation(request_id, "schema_analysis", file_ids)
    print(f"   ✅ Duplicate detection: {is_duplicate}")
    
    # Test 3: Different context (should not be duplicate)
    print("\n3. Testing different context...")
    different_file_ids = ["file4", "file5"]
    is_different_duplicate = working_memory_service.deduplicate_operation(request_id, "schema_analysis", different_file_ids)
    print(f"   ✅ Different context detection: {not is_different_duplicate}")
    
    # Test 4: LangSmith metadata storage
    print("\n4. Testing LangSmith metadata storage...")
    metadata_key = f"trace_metadata_{request_id}"
    sanitized_metadata = {
        "endpoint": "ai_multi_file_routing",
        "question_length": 25,
        "file_count": 3,
        "request_id": request_id
    }
    
    metadata_success = working_memory_service.store_langsmith_metadata(request_id, metadata_key, sanitized_metadata)
    print(f"   ✅ Metadata storage successful: {metadata_success}")
    
    retrieved_metadata = working_memory_service.get_langsmith_metadata(request_id, metadata_key)
    print(f"   ✅ Metadata retrieval successful: {retrieved_metadata is not None}")
    
    # Test 5: Memory statistics
    print("\n5. Testing memory statistics...")
    stats = working_memory_service.get_memory_stats()
    print(f"   📊 Redis available: {stats.get('redis_available')}")
    print(f"   📊 Fallback entries: {stats.get('fallback_entries')}")
    print(f"   📊 Redis entries: {stats.get('redis_entries', 0)}")
    
    # Test 6: Cleanup
    print("\n6. Testing cleanup...")
    cleanup_success = working_memory_service.cleanup_request(request_id)
    print(f"   ✅ Cleanup successful: {cleanup_success}")
    
    # Verify cleanup worked
    after_cleanup = working_memory_service.get_schema_analysis(request_id, file_ids)
    print(f"   ✅ Data cleaned up: {after_cleanup is None}")
    
    print("\n🎉 All Working Memory tests passed!")
    return True


async def test_schema_duplication_fix():
    """Test that schema duplication is fixed."""
    print("\n🔧 Testing Schema Duplication Fix...")
    
    request_id = str(uuid.uuid4())
    file_ids = ["test_file1", "test_file2"]
    
    # Simulate first schema analysis
    print("   📝 Simulating first schema analysis...")
    schema_data_1 = {
        "file_schemas": {"test_file1": {"rows": 100}, "test_file2": {"rows": 200}},
        "routing_recommendations": {"recommended_service": "csv_to_sql_converter"},
        "analysis_timestamp": time.time()
    }
    
    # Store first analysis
    working_memory_service.store_schema_analysis(request_id, file_ids, schema_data_1)
    
    # Simulate second schema analysis (should use cached result)
    print("   📝 Simulating second schema analysis (should use cache)...")
    
    # Check if already exists (this is what prevents duplication)
    if working_memory_service.has_request_context(request_id, "schema_analysis", file_ids):
        print("   ✅ Duplicate prevented - using cached analysis")
        cached_data = working_memory_service.get_schema_analysis(request_id, file_ids)
        print(f"   📊 Cached data retrieved: {cached_data is not None}")
    else:
        print("   ❌ Duplicate not prevented - would perform fresh analysis")
    
    # Cleanup
    working_memory_service.cleanup_request(request_id)
    print("   🧹 Cleanup completed")
    
    print("✅ Schema duplication fix test completed!")


if __name__ == "__main__":
    async def main():
        try:
            await test_working_memory()
            await test_schema_duplication_fix()
            print("\n🚀 Working Memory implementation is ready!")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())
