# User Query Flow - Complete Process

## 🎯 **Current User Flow When Asking a Question**

When a user asks a question through the `/api/v1/query` endpoint, here's exactly what happens:

## 📋 **Request Format**

```json
{
  "connection_id": "uuid-string",     // Required for database queries
  "file_id": "uuid-string",          // Required for CSV queries  
  "question": "What is the average salary?",
  "data_source": "database|csv|csv_sql"  // Determines processing path
}
```

## 🔄 **Complete Flow Diagram**

```
┌─────────────────┐
│   User Sends    │
│   POST Request  │
│   /api/v1/query │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Query Endpoint │
│  ask_question() │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Route Based on │
│  data_source    │
└─────────┬───────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│database │ │   csv   │ │csv_sql  │
│Handler  │ │Handler  │ │Handler  │
└─────────┘ └─────────┘ └─────────┘
```

## 🗄️ **1. Database Query Flow (`data_source: "database"`)**

```
User Question → Database Handler → Agent System → Database → Results
```

### **Step-by-Step Process:**

1. **🔍 Validate Connection**
   - Check if `connection_id` is provided
   - Convert string to UUID
   - Query database for connection record
   - Verify agent_id exists
   - Verify db_schema_cache exists

2. **🤖 Generate SQL Query**
   - Use `TextToSQLService.generate_sql()`
   - Input: User question + database schema
   - Output: Generated SQL query

3. **📡 Send to Agent**
   - Check if agent is connected via WebSocket
   - Send SQL query to agent via `ConnectionManager`
   - Wait for agent response

4. **📊 Process Results**
   - Extract data, columns, row_count from agent response
   - Format human-readable answer
   - Return structured response

### **Example Database Flow:**
```json
Request: {
  "connection_id": "123e4567-e89b-12d3-a456-426614174000",
  "question": "What is the average salary?",
  "data_source": "database"
}

Response: {
  "answer": "The result is: 65000",
  "sql_query": "SELECT AVG(salary) FROM employees",
  "data": [[65000]],
  "columns": ["AVG(salary)"],
  "row_count": 1
}
```

## 📊 **2. CSV Analysis Flow (`data_source: "csv"`)**

```
User Question → CSV Handler → DataAnalysisService → Pandas → Results
```

### **Step-by-Step Process:**

1. **🔍 Validate File**
   - Check if `file_id` is provided
   - Query database for `UploadedFile` record
   - Verify file exists and has valid URL

2. **📥 Load CSV Data**
   - Use `DataAnalysisService._get_csv_data()`
   - Download CSV from Cloudinary
   - Convert to pandas DataFrame

3. **🧠 Process Query**
   - Use `DataAnalysisService.process_query()`
   - Convert natural language to pandas operations
   - Execute operations on DataFrame

4. **📊 Format Results**
   - Extract data, columns, row_count
   - Generate natural language response
   - Return structured response

### **Example CSV Flow:**
```json
Request: {
  "file_id": "456e7890-e89b-12d3-a456-426614174000",
  "question": "What is the average salary?",
  "data_source": "csv"
}

Response: {
  "answer": "The average salary is $65,000",
  "sql_query": "",
  "data": [[65000]],
  "columns": ["average_salary"],
  "row_count": 1
}
```

## 🗃️ **3. CSV SQL Flow (`data_source: "csv_sql"`)**

```
User Question → CSV SQL Handler → SQLite Conversion → SQL Execution → Results
```

### **Step-by-Step Process:**

1. **🔍 Validate File**
   - Check if `file_id` is provided
   - Query database for `UploadedFile` record
   - Verify file exists and has valid URL

2. **📥 Load CSV Data**
   - Use `DataAnalysisService._get_csv_data()`
   - Download CSV from Cloudinary
   - Convert to pandas DataFrame

3. **🗃️ Convert to SQLite**
   - Use `CSVToSQLConverter.convert_csv_to_sql()`
   - Create in-memory SQLite database
   - Convert DataFrame to SQLite table
   - Store connection and DataFrame in memory

4. **📋 Get Schema**
   - Use `CSVToSQLConverter.get_table_schema()`
   - Extract column names, types, sample data
   - Format schema for SQL generation

5. **🤖 Generate SQL Query**
   - Use `TextToSQLService.generate_sql()`
   - Input: User question + CSV schema
   - Output: Generated SQL query

6. **⚡ Execute SQL**
   - Use `CSVToSQLConverter.execute_sql_query()`
   - Execute SQL on in-memory SQLite table
   - Return query results

7. **📊 Format Results**
   - Extract data, columns, row_count
   - Generate human-readable answer
   - Return structured response

### **Example CSV SQL Flow:**
```json
Request: {
  "file_id": "456e7890-e89b-12d3-a456-426614174000",
  "question": "What is the average salary?",
  "data_source": "csv_sql"
}

Response: {
  "answer": "The result is: 65000",
  "sql_query": "SELECT AVG(salary) FROM csv_data_456e7890_e89b_12d3_a456_426614174000",
  "data": [[65000]],
  "columns": ["AVG(salary)"],
  "row_count": 1
}
```

## 🔧 **Key Components Used**

### **Services:**
- **`TextToSQLService`**: Converts natural language to SQL
- **`DataAnalysisService`**: Handles CSV data loading and pandas operations
- **`CSVToSQLConverter`**: Converts CSV to SQLite and executes SQL
- **`ConnectionManager`**: Manages WebSocket connections to agents

### **Models:**
- **`QueryRequest`**: Input validation
- **`QueryResponse`**: Structured output format
- **`UploadedFile`**: File metadata from database
- **`Connection`**: Database connection metadata

### **External Services:**
- **Cloudinary**: CSV file storage
- **WebSocket Agents**: Database query execution
- **PostgreSQL**: Metadata storage

## ⚡ **Performance Characteristics**

### **Database Queries:**
- **Speed**: Fast (direct database access)
- **Scalability**: High (agent-based)
- **Memory**: Low (no data storage)

### **CSV Analysis:**
- **Speed**: Medium (pandas operations)
- **Scalability**: Medium (memory-bound)
- **Memory**: Medium (DataFrame in RAM)

### **CSV SQL:**
- **Speed**: Fast (SQLite in-memory)
- **Scalability**: Low (memory-bound)
- **Memory**: High (DataFrame + SQLite in RAM)

## 🚨 **Error Handling**

### **Common Errors:**
1. **Missing Parameters**: `connection_id` or `file_id` not provided
2. **File Not Found**: CSV file doesn't exist in database
3. **Agent Disconnected**: WebSocket agent not available
4. **SQL Generation Failed**: LLM couldn't generate valid SQL
5. **Query Execution Failed**: SQL syntax error or data issue

### **Error Responses:**
```json
{
  "detail": "File with ID 123 not found. Please ensure the file was uploaded successfully.",
  "status_code": 404
}
```

## 🎯 **Current Status**

✅ **Implemented and Working:**
- Database query flow (existing)
- CSV analysis flow (existing) 
- CSV SQL flow (newly implemented)

✅ **Ready for Production:**
- All three data sources supported
- Comprehensive error handling
- Memory management for CSV SQL
- Integration with existing services

## 🚀 **Next Steps**

1. **Frontend Integration**: Update UI to support all three data sources
2. **Performance Optimization**: Add caching and optimization
3. **Monitoring**: Add metrics and logging
4. **Testing**: Comprehensive test coverage
5. **Documentation**: API documentation and user guides

---

**The system now supports three complete query flows, giving users maximum flexibility in how they interact with their data!** 🎉
