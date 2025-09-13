#!/usr/bin/env python3
"""
LangSmith Installation and Testing Script for Clean Custard

This script helps with:
1. Installing LangSmith dependencies
2. Testing LangSmith integration
3. Validating configuration
4. Running basic functionality tests
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def install_dependencies():
    """Install LangSmith dependencies."""
    logger.info("Installing LangSmith dependencies...")
    
    try:
        # Install LangSmith and related packages
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "langsmith>=0.1.0",
            "langchain-community>=0.3.0"
        ])
        logger.info("✅ LangSmith dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False


def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing imports...")
    
    try:
        # Test LangSmith imports
        import langsmith
        from langchain.callbacks import LangChainTracer
        logger.info("✅ LangSmith imports successful")
        
        # Test our custom modules
        from core.langsmith_service import langsmith_service
        from core.config import settings
        logger.info("✅ Custom module imports successful")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False


def test_configuration():
    """Test LangSmith configuration."""
    logger.info("Testing configuration...")
    
    try:
        from core.config import settings
        
        # Check if LangSmith settings are present
        if hasattr(settings, 'langsmith_api_key'):
            logger.info(f"✅ LangSmith API key configured: {settings.langsmith_api_key[:10]}...")
        else:
            logger.warning("⚠️ LangSmith API key not configured")
        
        if hasattr(settings, 'langsmith_project'):
            logger.info(f"✅ LangSmith project configured: {settings.langsmith_project}")
        else:
            logger.warning("⚠️ LangSmith project not configured")
        
        if hasattr(settings, 'langsmith_tracing_enabled'):
            logger.info(f"✅ LangSmith tracing enabled: {settings.langsmith_tracing_enabled}")
        else:
            logger.warning("⚠️ LangSmith tracing not configured")
        
        return True
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


def test_langsmith_service():
    """Test LangSmith service initialization."""
    logger.info("Testing LangSmith service...")
    
    try:
        from core.langsmith_service import langsmith_service
        
        # Test service initialization
        logger.info(f"✅ LangSmith service initialized: {langsmith_service._initialized}")
        logger.info(f"✅ Tracing enabled: {langsmith_service.is_enabled}")
        
        # Test project info
        project_info = langsmith_service.get_project_info()
        logger.info(f"✅ Project info: {project_info}")
        
        # Test trace creation (if enabled)
        if langsmith_service.is_enabled:
            with langsmith_service.create_trace("test_trace", metadata={"test": True}) as trace:
                # Test adding metadata
                langsmith_service.add_metadata(trace, {"additional_test": True})
            logger.info("✅ Trace creation test successful")
        else:
            logger.info("ℹ️ Tracing disabled, skipping trace test")
        
        return True
    except Exception as e:
        logger.error(f"❌ LangSmith service test failed: {e}")
        return False


def test_llm_services():
    """Test LLM services with LangSmith integration."""
    logger.info("Testing LLM services...")
    
    try:
        # Test TextToSQLService
        from llm.services import TextToSQLService
        sql_service = TextToSQLService()
        logger.info("✅ TextToSQLService initialized with LangSmith")
        
        # Test DataAnalysisService
        from services.data_analysis_service import DataAnalysisService
        data_service = DataAnalysisService()
        logger.info("✅ DataAnalysisService initialized with LangSmith")
        
        # Test AIRoutingAgent
        from services.ai_routing_agent import AIRoutingAgent
        routing_agent = AIRoutingAgent()
        logger.info("✅ AIRoutingAgent initialized with LangSmith")
        
        return True
    except Exception as e:
        logger.error(f"❌ LLM services test failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    logger.info("🚀 Starting LangSmith integration tests...")
    
    tests = [
        ("Dependencies", install_dependencies),
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("LangSmith Service", test_langsmith_service),
        ("LLM Services", test_llm_services)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 All tests passed! LangSmith integration is ready.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return False


def main():
    """Main function."""
    logger.info("🍮 Clean Custard - LangSmith Integration Setup")
    logger.info("="*60)
    
    # Check if we're in the right directory
    if not (backend_dir / "main.py").exists():
        logger.error("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    
    if success:
        logger.info("\n🎯 Next steps:")
        logger.info("1. Set LANGSMITH_API_KEY in your environment")
        logger.info("2. Set LANGSMITH_PROJECT in your environment")
        logger.info("3. Start your backend server")
        logger.info("4. Check /api/v1/langsmith/status endpoint")
        logger.info("5. Start making queries to see LangSmith traces!")
        sys.exit(0)
    else:
        logger.error("\n❌ Setup incomplete. Please fix the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
