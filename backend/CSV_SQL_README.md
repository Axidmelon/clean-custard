# CSV-to-SQL Implementation

This document describes the CSV-to-SQL functionality implemented in Phase 1 of the clean-custard project.

## Overview

The CSV-to-SQL feature allows users to execute SQL queries on uploaded CSV files using an in-memory SQLite database. This provides a familiar SQL interface for data analysis while maintaining simplicity and cost-effectiveness.

## Architecture

```
CSV Upload → Cloudinary Storage → Backend Download → pandas DataFrame → SQLite In-Memory Table → SQL Query Execution → Results
```

### Key Components

1. **CSVToSQLConverter Service** (`services/csv_to_sql_converter.py`)
   - Converts CSV data to SQLite tables
   - Executes SQL queries on CSV data
   - Manages memory and connections
   - Provides schema information

2. **Enhanced Query Endpoint** (`api/v1/endpoints/query.py`)
   - Routes CSV SQL queries to the converter
   - Integrates with existing TextToSQLService
   - Returns consistent response format

3. **Integration Points**
   - Uses existing DataAnalysisService for CSV loading
   - Leverages TextToSQLService for SQL generation
   - Integrates with file upload system

## Usage

### API Endpoint

```http
POST /api/v1/query
Content-Type: application/json

{
    "file_id": "your-file-id",
    "question": "What is the average salary by department?",
    "data_source": "csv_sql"
}
```

### Response Format

```json
{
    "answer": "The result is: 60000",
    "sql_query": "SELECT AVG(salary) FROM csv_data_your_file_id GROUP BY department",
    "data": [[60000]],
    "columns": ["avg_salary"],
    "row_count": 1
}
```

### Data Sources

The query endpoint supports three data sources:

- `"database"`: Traditional database queries via agents
- `"csv"`: CSV data analysis using pandas operations
- `"csv_sql"`: CSV data analysis using SQL queries on in-memory SQLite

## Features

### Supported SQL Operations

- **Data Selection**: SELECT, WHERE, LIMIT, DISTINCT
- **Aggregation**: COUNT, SUM, AVG, MIN, MAX, GROUP BY, HAVING
- **Sorting**: ORDER BY (ASC/DESC), multiple columns
- **Filtering**: LIKE, IN, BETWEEN, IS NULL, IS NOT NULL
- **Subqueries**: Nested queries, EXISTS, IN clauses
- **String Operations**: SUBSTR, REPLACE, UPPER, LOWER, LENGTH
- **Date Functions**: DATE, STRFTIME, date arithmetic
- **Set Operations**: UNION, UNION ALL
- **Conditional Logic**: CASE statements

### Memory Management

- **File Size Limit**: 50MB per CSV file
- **Memory Limit**: 100MB per file, 500MB total
- **Automatic Cleanup**: Memory is cleaned up when sessions end
- **Memory Monitoring**: Real-time memory usage tracking

### Error Handling

- **File Validation**: Checks for valid CSV format
- **SQL Injection Prevention**: Basic query sanitization
- **Memory Protection**: Prevents memory exhaustion
- **Graceful Degradation**: Clear error messages

## Implementation Details

### CSVToSQLConverter Class

```python
class CSVToSQLConverter:
    async def convert_csv_to_sql(self, file_id: str, csv_data: str) -> str
    async def execute_sql_query(self, file_id: str, sql_query: str) -> Dict[str, Any]
    async def get_table_schema(self, file_id: str) -> Dict[str, Any]
    async def cleanup_file_data(self, file_id: str)
    async def cleanup_all_data(self)
    def get_memory_stats(self) -> Dict[str, Any]
```

### Integration Flow

1. **File Validation**: Check file exists in database
2. **CSV Loading**: Use DataAnalysisService to load CSV data
3. **SQLite Conversion**: Convert DataFrame to SQLite table
4. **Schema Generation**: Create schema string for TextToSQLService
5. **SQL Generation**: Use TextToSQLService to generate SQL query
6. **Query Execution**: Execute SQL on SQLite table
7. **Result Formatting**: Return formatted results

## Testing

### Test Suite

- **Unit Tests**: `tests/test_csv_sql_converter.py`
- **Integration Tests**: `tests/test_csv_sql_integration.py`
- **Performance Tests**: Memory and query performance testing

### Running Tests

```bash
# Run all CSV-to-SQL tests
pytest backend/tests/test_csv_sql_converter.py -v
pytest backend/tests/test_csv_sql_integration.py -v

# Run with coverage
pytest backend/tests/test_csv_sql_converter.py --cov=services.csv_to_sql_converter
```

### Example Usage

```bash
# Run the example script
python backend/examples/csv_sql_example.py
```

## Configuration

### Environment Variables

No additional environment variables are required. The service uses:
- Existing database configuration
- Existing file upload configuration (Cloudinary)
- Existing LLM configuration (OpenAI)

### Memory Limits

Memory limits can be adjusted in the CSVToSQLConverter class:

```python
self.max_memory_per_file = 100 * 1024 * 1024  # 100MB per file
self.max_total_memory = 500 * 1024 * 1024     # 500MB total
self.max_file_size = 50 * 1024 * 1024         # 50MB file size limit
```

## Performance Considerations

### Memory Usage

- **Per File**: ~100MB for typical CSV files
- **Total Memory**: Scales linearly with number of active users
- **Cleanup**: Automatic cleanup prevents memory leaks

### Query Performance

- **Small Files** (< 10MB): < 1 second query time
- **Medium Files** (10-50MB): 1-3 seconds query time
- **Large Files** (> 50MB): Not supported (memory limit)

### Scalability

- **Concurrent Users**: Supports multiple users simultaneously
- **Memory Isolation**: Each file gets its own SQLite database
- **Resource Management**: Automatic cleanup and memory monitoring

## Security

### SQL Injection Prevention

- **Query Sanitization**: Basic keyword filtering
- **Table Name Validation**: Ensures queries use correct table names
- **Input Validation**: Validates CSV data and file IDs

### File Access Control

- **User Validation**: Only file owners can query their files
- **File Existence**: Validates files exist in database
- **URL Validation**: Ensures file URLs are accessible

## Monitoring

### Memory Statistics

```python
stats = csv_to_sql_converter.get_memory_stats()
# Returns:
# {
#     "total_memory_usage": 1048576,
#     "max_total_memory": 524288000,
#     "memory_usage_percentage": 0.2,
#     "active_files": 1,
#     "max_memory_per_file": 104857600,
#     "memory_pressure": false
# }
```

### Logging

The service provides comprehensive logging:
- **Conversion Events**: CSV to SQLite conversion
- **Query Execution**: SQL query execution and results
- **Memory Management**: Memory usage and cleanup
- **Error Handling**: Detailed error logging

## Future Enhancements

### Phase 2 Features

- **Advanced SQL Features**: Window functions, CTEs, complex joins
- **Performance Optimization**: Query caching, connection pooling
- **Frontend Integration**: SQL query interface in UI

### Phase 3 Features

- **Production Safeguards**: Enhanced error handling, monitoring
- **Scalability**: Horizontal scaling support
- **Advanced Analytics**: Query optimization, performance metrics

## Troubleshooting

### Common Issues

1. **Memory Errors**
   - Check file size limits
   - Monitor memory usage
   - Clean up unused files

2. **SQL Errors**
   - Validate SQL syntax
   - Check table names
   - Review query complexity

3. **File Not Found**
   - Verify file exists in database
   - Check file URL accessibility
   - Ensure proper file upload

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('services.csv_to_sql_converter').setLevel(logging.DEBUG)
```

## Contributing

### Code Style

- Follow existing code style
- Add comprehensive tests
- Include docstrings
- Handle errors gracefully

### Testing

- Write unit tests for new features
- Add integration tests for API endpoints
- Include performance tests for memory usage
- Test error conditions

### Documentation

- Update this README for new features
- Add inline documentation
- Include usage examples
- Document configuration options
