#!/usr/bin/env python3
"""
Test script to verify AI routing agent fix.
Ensures AI routing agent only chooses CSV services when CSV file is selected.
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_routing_agent import AIRoutingAgent, AnalysisContext

async def test_csv_file_routing():
    """Test that AI routing agent only chooses CSV services when CSV file is selected."""
    
    print("🧪 Testing AI Routing Agent Fix")
    print("=" * 50)
    
    # Initialize AI routing agent
    ai_agent = AIRoutingAgent()
    
    # Test cases for CSV file context
    csv_test_cases = [
        {
            "question": "What is the average salary by department?",
            "context": AnalysisContext(
                question="What is the average salary by department?",
                file_size=1024*1024,  # 1MB
                data_source="csv",
                user_preference="sql"
            ),
            "expected_services": ["csv_sql", "csv"],
            "description": "Simple aggregation query on CSV file"
        },
        {
            "question": "Find correlation between sales and marketing spend",
            "context": AnalysisContext(
                question="Find correlation between sales and marketing spend",
                file_size=5*1024*1024,  # 5MB
                data_source="csv",
                user_preference="python"
            ),
            "expected_services": ["csv_sql", "csv"],
            "description": "Complex statistical analysis on CSV file"
        },
        {
            "question": "Show me real-time sales data",
            "context": AnalysisContext(
                question="Show me real-time sales data",
                file_size=1024*1024,  # 1MB
                data_source="csv",
                user_preference=None
            ),
            "expected_services": ["csv_sql", "csv"],
            "description": "Real-time query on CSV file (should NOT route to database)"
        }
    ]
    
    # Test cases for database context
    database_test_cases = [
        {
            "question": "What is the current inventory count?",
            "context": AnalysisContext(
                question="What is the current inventory count?",
                file_size=None,
                data_source="database",
                user_preference=None
            ),
            "expected_services": ["csv_sql", "csv", "database"],
            "description": "Real-time database query"
        }
    ]
    
    print("\n📊 Testing CSV File Context (Should NOT recommend database):")
    print("-" * 60)
    
    csv_passed = 0
    csv_total = len(csv_test_cases)
    
    for i, test_case in enumerate(csv_test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Question: {test_case['question']}")
        
        try:
            result = await ai_agent.analyze_and_route(
                test_case['question'], 
                test_case['context']
            )
            
            recommended_service = result["recommended_service"]
            reasoning = result["reasoning"]
            confidence = result["confidence"]
            
            print(f"   ✅ AI Recommendation: {recommended_service}")
            print(f"   📝 Reasoning: {reasoning}")
            print(f"   🎯 Confidence: {confidence:.2f}")
            
            # Check if recommendation is valid for CSV context
            if recommended_service in test_case["expected_services"]:
                print(f"   ✅ PASS: Correctly chose CSV service")
                csv_passed += 1
            else:
                print(f"   ❌ FAIL: Recommended {recommended_service} (not allowed for CSV)")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n🗄️ Testing Database Context (Can recommend all services):")
    print("-" * 60)
    
    db_passed = 0
    db_total = len(database_test_cases)
    
    for i, test_case in enumerate(database_test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Question: {test_case['question']}")
        
        try:
            result = await ai_agent.analyze_and_route(
                test_case['question'], 
                test_case['context']
            )
            
            recommended_service = result["recommended_service"]
            reasoning = result["reasoning"]
            confidence = result["confidence"]
            
            print(f"   ✅ AI Recommendation: {recommended_service}")
            print(f"   📝 Reasoning: {reasoning}")
            print(f"   🎯 Confidence: {confidence:.2f}")
            
            # Check if recommendation is valid for database context
            if recommended_service in test_case["expected_services"]:
                print(f"   ✅ PASS: Valid recommendation")
                db_passed += 1
            else:
                print(f"   ❌ FAIL: Recommended {recommended_service} (not in allowed list)")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"CSV Context Tests: {csv_passed}/{csv_total} passed")
    print(f"Database Context Tests: {db_passed}/{db_total} passed")
    print(f"Total Tests: {csv_passed + db_passed}/{csv_total + db_total} passed")
    
    if csv_passed == csv_total and db_passed == db_total:
        print("\n🎉 ALL TESTS PASSED! AI routing agent fix is working correctly.")
        print("✅ CSV files will only route to CSV services (csv_sql or csv)")
        print("✅ Database context can still route to all services")
        return True
    else:
        print("\n❌ SOME TESTS FAILED! AI routing agent needs further fixes.")
        return False

async def main():
    """Run the test."""
    try:
        success = await test_csv_file_routing()
        if success:
            print("\n🚀 Fix verification completed successfully!")
        else:
            print("\n⚠️ Fix verification failed - manual review needed.")
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
