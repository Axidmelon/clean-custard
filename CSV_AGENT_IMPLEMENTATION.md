# Data Analysis Service Implementation

## Overview

The Data Analysis Service is a comprehensive service that allows users to ask natural language questions about uploaded data files and get instant, intelligent answers. This service bridges the gap between non-technical users and their data by providing a conversational interface for advanced data analysis.

## Architecture

### Backend Integration
The CSV agent is implemented as a **backend service** rather than a separate Docker agent, providing:

- **No Docker Required**: Non-technical users don't need to set up containers
- **Simpler Deployment**: No additional infrastructure needed
- **Better Performance**: Direct file processing without WebSocket overhead
- **Cost Effective**: No additional hosting requirements

### Service Architecture
```
Frontend (React) → Backend (FastAPI) → CSV Query Service → CSV Processing
                                    → Agent PostgreSQL → Database
```

## Components

### 1. CSV Query Service (`backend/services/csv_query_service.py`)

**Core Functionality:**
- CSV schema analysis and caching
- Natural language to pandas query conversion
- Query execution and result formatting
- Integration with existing file upload system

**Key Features:**
- **Schema Discovery**: Automatically analyzes CSV structure, data types, and patterns
- **Query Generation**: Converts natural language to pandas operations using LLM
- **Safe Execution**: Executes queries in a controlled environment
- **Result Formatting**: Converts results to natural language responses
- **Caching**: Caches CSV data and schema for performance

### 2. CSV API Endpoints (`backend/api/v1/endpoints/csv_query.py`)

**Available Endpoints:**
- `POST /api/v1/csv/analyze` - Analyze CSV schema
- `POST /api/v1/csv/query` - Process natural language query
- `GET /api/v1/csv/schema/{file_id}` - Get cached schema
- `DELETE /api/v1/csv/cache/{file_id}` - Clear cache
- `GET /api/v1/csv/status` - Service status

### 3. Enhanced Query Endpoint (`backend/api/v1/endpoints/query.py`)

**Updated to support both data sources:**
- Database queries (existing functionality)
- CSV queries (new functionality)
- Automatic routing based on `data_source` parameter

### 4. Frontend Integration (`frontend/src/`)

**Updated Components:**
- `services/queryService.ts` - Added CSV-specific query functions
- `types/api.ts` - Updated QueryRequest interface
- `pages/TalkData.tsx` - Enhanced to handle both data sources

## Usage Examples

### 1. Schema Analysis
```python
# Analyze CSV schema
schema_info = await csv_query_service.analyze_csv_schema(file_id)
```

**Response:**
```json
{
  "file_info": {
    "shape": [1000, 5],
    "row_count": 1000,
    "column_count": 5
  },
  "columns": [
    {
      "name": "customer_id",
      "type": "int64",
      "sample_values": [1, 2, 3],
      "null_count": 0,
      "unique_count": 1000
    }
  ],
  "data_types": {
    "customer_id": "int64",
    "product_name": "object",
    "price": "float64"
  }
}
```

### 2. Natural Language Queries

**User Questions:**
- "What's the average salary?"
- "How many people are in Engineering?"
- "Show me the top 10 highest earners"
- "What's the trend in monthly sales?"
- "How many unique products do we have?"

**Generated Pandas Queries:**
```python
# "What's the average salary?"
df['salary'].mean()

# "How many people are in Engineering?"
len(df[df['department'] == 'Engineering'])

# "Show me the top 10 highest earners"
df.nlargest(10, 'salary')

# "What's the average age by department?"
df.groupby('department')['age'].mean()
```

### 3. API Usage

**CSV Query Request:**
```json
{
  "file_id": "uuid-here",
  "question": "What's the average salary by department?",
  "data_source": "csv"
}
```

**Response:**
```json
{
  "success": true,
  "question": "What's the average salary by department?",
  "natural_response": "The average salary by department is: Engineering: $55,000, Marketing: $62,000, Product: $66,000",
  "data": [
    ["Engineering", 55000],
    ["Marketing", 62000],
    ["Product", 66000]
  ],
  "columns": ["department", "avg_salary"],
  "row_count": 3,
  "result_type": "DataFrame",
  "display_type": "table"
}
```

## Supported Query Types

### 1. Aggregations
- `SUM`, `COUNT`, `AVG`, `MIN`, `MAX`
- Grouped aggregations
- Statistical summaries

### 2. Filtering
- WHERE conditions
- Date ranges
- Value ranges
- Multiple conditions

### 3. Sorting and Ranking
- ORDER BY operations
- Top N results
- Bottom N results

### 4. Grouping
- GROUP BY operations
- Multi-level grouping
- Aggregated metrics

### 5. Data Exploration
- Unique values
- Data distribution
- Missing value analysis
- Data quality metrics

## Security Features

### 1. User Access Control
- File access validation
- User-specific file isolation
- Authentication required

### 2. Safe Query Execution
- Controlled execution environment
- Limited function access
- No file system access
- Memory limits

### 3. Data Privacy
- No data persistence beyond session
- Cache clearing capabilities
- Secure file access

## Performance Optimizations

### 1. Caching Strategy
- **CSV Data Cache**: Stores parsed DataFrame in memory
- **Schema Cache**: Caches analyzed schema information
- **Query Cache**: (Future) Cache common query results

### 2. Memory Management
- Configurable cache limits
- Automatic cache cleanup
- Memory usage monitoring

### 3. Query Optimization
- Limited result sets (100 rows max)
- Efficient pandas operations
- Lazy loading for large files

## Testing

### Test Script
Run the test script to verify functionality:
```bash
cd /Users/axid/clean-custard
python test_csv_agent.py
```

### Test Coverage
- Schema analysis
- Query generation
- Query execution
- Result formatting
- Error handling

## Deployment

### 1. Backend Dependencies
Add to `requirements.txt`:
```
pandas>=2.0.0
numpy>=1.24.0
```

### 2. Environment Variables
No additional environment variables required. Uses existing:
- `OPENAI_API_KEY` for LLM integration
- Database connection for file metadata

### 3. API Integration
The CSV endpoints are automatically included when the backend starts.

## Future Enhancements

### 1. Advanced Analytics
- Time series analysis
- Statistical modeling
- Data visualization
- Export capabilities

### 2. Multi-File Support
- Join operations across files
- Data comparison
- Cross-file analytics

### 3. Performance Improvements
- Query result caching
- Background processing
- Streaming for large files

### 4. User Experience
- Query suggestions
- Data visualization
- Export to various formats
- Query history

## Troubleshooting

### Common Issues

1. **File Not Found**
   - Verify file_id exists
   - Check user permissions
   - Ensure file is CSV format

2. **Query Generation Errors**
   - Check OpenAI API key
   - Verify question clarity
   - Review schema information

3. **Memory Issues**
   - Clear cache: `DELETE /api/v1/csv/cache/{file_id}`
   - Check file size limits
   - Monitor memory usage

### Debug Mode
Enable debug logging:
```python
import logging
logging.getLogger('services.csv_query_service').setLevel(logging.DEBUG)
```

## API Reference

### CSV Query Service
- `analyze_csv_schema(file_id)` - Analyze CSV structure
- `process_query(question, file_id)` - Process natural language query
- `clear_cache(file_id)` - Clear cached data

### API Endpoints
- `POST /api/v1/csv/analyze` - Schema analysis
- `POST /api/v1/csv/query` - Query processing
- `GET /api/v1/csv/schema/{file_id}` - Get schema
- `DELETE /api/v1/csv/cache/{file_id}` - Clear cache
- `GET /api/v1/csv/status` - Service status

## Conclusion

The CSV Schema-Aware Agent provides a powerful, user-friendly interface for data analysis without requiring technical expertise. By integrating directly into the backend, it maintains simplicity while providing enterprise-grade functionality.

The agent successfully bridges the gap between non-technical users and their data, enabling natural language queries on CSV files with intelligent responses and comprehensive data analysis capabilities.
