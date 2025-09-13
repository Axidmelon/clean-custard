# File: backend/examples/ai_routing_example.py
# Example demonstrating AI-powered routing agent

import asyncio
import sys
import os
sys.path.append('.')
from services.ai_routing_agent import ai_routing_agent, AnalysisContext

async def test_ai_routing():
    """Test the AI routing agent with various question types."""
    
    print("🤖 Testing AI-Powered Routing Agent")
    print("=" * 50)
    
    # Test cases with different question types
    test_cases = [
        {
            "question": "What is the average salary?",
            "context": {"file_size": 10 * 1024 * 1024, "data_source": "csv"},
            "expected": "Simple query - should recommend CSV SQL"
        },
        {
            "question": "Calculate the correlation between price and sales volume",
            "context": {"file_size": 50 * 1024 * 1024, "data_source": "csv"},
            "expected": "Complex statistical - should recommend CSV pandas"
        },
        {
            "question": "Pivot the data to show sales by region and month",
            "context": {"file_size": 20 * 1024 * 1024, "data_source": "csv"},
            "expected": "Data transformation - should recommend CSV pandas"
        },
        {
            "question": "Show me real-time sales data from the database",
            "context": {"data_source": "database"},
            "expected": "Real-time analysis - should recommend database"
        },
        {
            "question": "SELECT department, COUNT(*) FROM employees GROUP BY department",
            "context": {"file_size": 5 * 1024 * 1024, "data_source": "csv"},
            "expected": "SQL query - should recommend CSV SQL"
        },
        {
            "question": "Find outliers in the dataset using machine learning",
            "context": {"file_size": 100 * 1024 * 1024, "data_source": "csv"},
            "expected": "ML analysis - should recommend CSV pandas"
        },
        {
            "question": "Join customer data with order data",
            "context": {"file_size": 30 * 1024 * 1024, "data_source": "csv"},
            "expected": "Joins required - should recommend CSV pandas"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['question']}")
        print(f"Expected: {test_case['expected']}")
        
        # Create context
        context = AnalysisContext(
            question=test_case["question"],
            **test_case["context"]
        )
        
        # Get AI analysis
        result = await ai_routing_agent.analyze_and_route(
            question=test_case["question"],
            context=context
        )
        
        print(f"🤖 AI Recommended Service: {result['recommended_service']}")
        print(f"🧠 AI Analysis Type: {result.get('ai_analysis', 'unknown')}")
        print(f"💭 AI Reasoning: {result['reasoning']}")
        print(f"🎯 AI Confidence: {result['confidence']:.2f}")
        print(f"🔍 Key Factors: {', '.join(result.get('key_factors', []))}")
        print("-" * 40)
    
    print("\n🎉 AI Routing Test Complete!")

async def test_ai_explanations():
    """Test AI agent's ability to explain decisions."""
    
    print("\n🧠 Testing AI Decision Explanations")
    print("=" * 50)
    
    questions = [
        "What is the average salary by department?",
        "Calculate correlation between price and sales",
        "Show me real-time inventory levels"
    ]
    
    for question in questions:
        print(f"\n📝 Question: {question}")
        
        # Get detailed explanation
        explanation = await ai_routing_agent.explain_decision(question)
        print(explanation)
        print("-" * 50)

async def test_user_preferences():
    """Test how AI agent handles user preferences."""
    
    print("\n👤 Testing AI Agent with User Preferences")
    print("=" * 50)
    
    question = "What is the average salary by department?"
    
    # Test with SQL preference
    context_sql = AnalysisContext(
        question=question,
        file_size=10 * 1024 * 1024,
        data_source="csv",
        user_preference="sql"
    )
    
    result_sql = await ai_routing_agent.analyze_and_route(question, context_sql)
    
    print(f"🔍 Question: {question}")
    print(f"👤 User Preference: SQL")
    print(f"🤖 AI Recommended: {result_sql['recommended_service']}")
    print(f"💭 AI Reasoning: {result_sql['reasoning']}")
    
    # Test with Python preference
    context_python = AnalysisContext(
        question=question,
        file_size=10 * 1024 * 1024,
        data_source="csv",
        user_preference="python"
    )
    
    result_python = await ai_routing_agent.analyze_and_route(question, context_python)
    
    print(f"\n👤 User Preference: Python")
    print(f"🤖 AI Recommended: {result_python['recommended_service']}")
    print(f"💭 AI Reasoning: {result_python['reasoning']}")

async def test_complex_scenarios():
    """Test AI agent with complex, ambiguous scenarios."""
    
    print("\n🎯 Testing Complex AI Scenarios")
    print("=" * 50)
    
    complex_cases = [
        {
            "question": "I need to analyze customer behavior patterns and predict churn",
            "context": {"file_size": 200 * 1024 * 1024, "data_source": "csv"},
            "description": "Complex ML task with large dataset"
        },
        {
            "question": "Show me the top 10 customers by revenue",
            "context": {"file_size": 5 * 1024 * 1024, "data_source": "csv"},
            "description": "Simple query with small dataset"
        },
        {
            "question": "Merge sales data with customer data and calculate lifetime value",
            "context": {"file_size": 50 * 1024 * 1024, "data_source": "csv"},
            "description": "Data transformation with joins"
        }
    ]
    
    for case in complex_cases:
        print(f"\n📝 Scenario: {case['description']}")
        print(f"Question: {case['question']}")
        
        context = AnalysisContext(
            question=case["question"],
            **case["context"]
        )
        
        result = await ai_routing_agent.analyze_and_route(case["question"], context)
        
        print(f"🤖 AI Decision: {result['recommended_service']}")
        print(f"🧠 Analysis: {result.get('ai_analysis', 'unknown')}")
        print(f"💭 Reasoning: {result['reasoning']}")
        print(f"🎯 Confidence: {result['confidence']:.2f}")
        print("-" * 30)

async def main():
    """Run all AI routing tests."""
    try:
        await test_ai_routing()
        await test_ai_explanations()
        await test_user_preferences()
        await test_complex_scenarios()
        
        print("\n🚀 All AI Agent tests completed!")
        print("\n💡 Key Benefits of AI-Powered Routing:")
        print("   • Uses LLM intelligence for decision making")
        print("   • Understands context and nuance")
        print("   • Adapts to new question types")
        print("   • Provides detailed explanations")
        print("   • Respects user preferences")
        print("   • Handles complex, ambiguous scenarios")
        print("   • Learns from patterns in questions")
        
    except Exception as e:
        print(f"❌ Error running AI tests: {e}")
        print("Make sure OpenAI API key is configured!")

if __name__ == "__main__":
    asyncio.run(main())
