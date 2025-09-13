# 🍮 LangSmith Integration Setup Guide

## Overview

This guide will help you set up LangSmith integration for Clean Custard, providing comprehensive AI observability and evaluation capabilities.

## Prerequisites

- Clean Custard backend running
- Python 3.11+ environment
- LangSmith account (free tier available)

## Quick Setup

### 1. Create LangSmith Account

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Sign up for a free account
3. Create a new project called "Clean Custard Production"
4. Get your API key from Settings → API Keys

### 2. Install Dependencies

```bash
cd backend
python install_langsmith.py
```

This script will:
- Install LangSmith dependencies
- Test all integrations
- Validate configuration
- Provide setup guidance

### 3. Configure Environment

Add these variables to your `.env` file:

```bash
# LangSmith Configuration
LANGSMITH_API_KEY=your-langsmith-api-key-here
LANGSMITH_PROJECT=clean-custard-prod
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING_ENABLED=true
```

### 4. Test Integration

```bash
# Start your backend server
python main.py

# Test LangSmith status endpoint
curl http://localhost:8000/api/v1/langsmith/status

# Test health check
curl http://localhost:8000/api/v1/langsmith/health
```

## What's Integrated

### 🔍 **TextToSQLService**
- **Traces**: SQL generation, natural response formatting
- **Metrics**: Response time, token usage, SQL accuracy
- **Metadata**: Question type, schema complexity, model settings

### 📊 **DataAnalysisService**
- **Traces**: Pandas code generation, natural response formatting
- **Metrics**: Code correctness, execution success, response quality
- **Metadata**: Data shape, column types, analysis complexity

### 🤖 **AIRoutingAgent**
- **Traces**: Routing decisions, service recommendations
- **Metrics**: Routing accuracy, confidence scores, decision consistency
- **Metadata**: Question complexity, file size, user preferences

### 🌐 **Query Endpoint**
- **Traces**: Complete request/response cycles
- **Metrics**: End-to-end performance, user satisfaction
- **Metadata**: Data source type, user preferences, organization context

## LangSmith Dashboard

Once integrated, you'll see:

### **Traces Tab**
- All LLM interactions with detailed execution paths
- Input/output data for each trace
- Performance metrics and timing
- Error tracking and debugging information

### **Datasets Tab**
- Evaluation datasets for testing AI performance
- Quality metrics and benchmarks
- A/B testing results

### **Evaluations Tab**
- Automated testing results
- Performance comparisons
- Regression detection

## API Endpoints

### **LangSmith Status**
```bash
GET /api/v1/langsmith/status
```
Returns LangSmith service status and configuration.

### **LangSmith Health Check**
```bash
GET /api/v1/langsmith/health
```
Performs health check on LangSmith service.

## Monitoring & Observability

### **Real-time Monitoring**
- Live dashboards showing AI system performance
- Response time tracking across all services
- Token usage and cost monitoring
- Error rate and success rate tracking

### **Performance Metrics**
- SQL generation accuracy
- Pandas code generation success rate
- Routing decision accuracy
- Natural response quality scores

### **Error Tracking**
- LLM error capture and analysis
- Fallback mechanism monitoring
- Performance degradation detection
- Cost optimization insights

## Troubleshooting

### **Common Issues**

#### 1. LangSmith Not Initializing
```bash
# Check environment variables
echo $LANGSMITH_API_KEY
echo $LANGSMITH_PROJECT

# Test configuration
python -c "from core.config import settings; print(settings.langsmith_api_key)"
```

#### 2. Tracing Not Working
```bash
# Check service status
curl http://localhost:8000/api/v1/langsmith/status

# Test trace creation
python -c "from core.langsmith_service import langsmith_service; print(langsmith_service.is_enabled)"
```

#### 3. Import Errors
```bash
# Reinstall dependencies
pip install langsmith>=0.1.0 langchain-community>=0.3.0

# Test imports
python install_langsmith.py
```

### **Debug Mode**

Enable debug logging:
```bash
# In your .env file
LOG_LEVEL=DEBUG
LANGSMITH_TRACING_ENABLED=true
```

## Production Deployment

### **Railway Deployment**

1. Add environment variables in Railway dashboard:
   - `LANGSMITH_API_KEY`
   - `LANGSMITH_PROJECT`
   - `LANGSMITH_ENDPOINT`
   - `LANGSMITH_TRACING_ENABLED=true`

2. Deploy your backend

3. Test production endpoints:
   ```bash
   curl https://your-backend.railway.app/api/v1/langsmith/status
   ```

### **Docker Deployment**

Update your Dockerfile to include LangSmith dependencies:

```dockerfile
# Add to requirements.txt
RUN pip install langsmith>=0.1.0 langchain-community>=0.3.0
```

## Benefits

### **Immediate Benefits**
- **Visibility**: Complete visibility into AI system performance
- **Debugging**: Quick identification and resolution of AI issues
- **Cost Control**: Monitor and optimize token usage
- **Performance**: Track and improve response times

### **Long-term Benefits**
- **Quality**: Continuous improvement of AI responses
- **Reliability**: Proactive error detection and resolution
- **Scalability**: Data-driven scaling decisions
- **Competitive Advantage**: Superior AI performance through optimization

## Next Steps

1. **Set up evaluation datasets** for automated testing
2. **Configure alerts** for performance thresholds
3. **Create custom metrics** for your specific use cases
4. **Implement A/B testing** for prompt optimization
5. **Set up cost monitoring** and optimization

## Support

- **LangSmith Documentation**: [https://docs.smith.langchain.com/](https://docs.smith.langchain.com/)
- **Clean Custard Issues**: GitHub Issues
- **Community**: LangSmith Discord

---

**Clean Custard + LangSmith = Next-Level AI Observability** 🍮✨
