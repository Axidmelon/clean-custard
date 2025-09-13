# User Query Flow - Clean & Simple

## 🎯 **Overview**

When a user asks a question through the `/api/v1/query` endpoint, the system intelligently routes the request to the optimal service based on the data source and AI analysis.

## 📋 **Request Format**

```json
{
  "question": "What is the average salary by department?",
  "data_source": "auto|csv|csv_sql|database",
  "file_id": "uuid-string",           // For CSV queries
  "connection_id": "uuid-string",     // For database queries
  "user_preference": "sql|python"     // Optional
}
```

## 🔄 **Main Flow**

```
┌─────────────────┐
│   User Query    │
│   /api/v1/query │
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
    ▼           ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│database │ │   csv   │ │csv_sql  │ │   auto   │
│Handler  │ │Handler  │ │Handler  │ │AI Router │
└─────────┘ └─────────┘ └─────────┘ └─────┬───┘
                                          │
                                          ▼
                                    ┌─────────────┐
                                    │ AI Analysis │
                                    │ & Decision  │
                                    └─────┬───────┘
                                          │
                                    ┌─────┴─────┐
                                    │           │
                                    ▼           ▼           ▼
                              ┌─────────┐ ┌─────────┐ ┌─────────┐
                              │database │ │   csv   │ │csv_sql  │
                              │Handler  │ │Handler  │ │Handler  │
                              └─────────┘ └─────────┘ └─────────┘
                                    │           │           │
                                    └───────────┼───────────┘
                                                │
                                                ▼
                                    ┌─────────────────┐
                                    │   Return        │
                                    │   Results       │
                                    └─────────────────┘
```

## 🤖 **AI Routing (`data_source: "auto"`)**

### **Process:**
```
User Question → AI Analysis → Service Selection → Execute Query → Return Results
```

### **Context-Aware Routing:**

**CSV File Context** (when `file_id` is provided):
- ✅ AI chooses: `csv_to_sql_converter` or `data_analysis_service` only
- ❌ AI NEVER chooses: `database`
- 🛡️ **Safety**: Multiple validation layers prevent database routing

**Database Context** (when `connection_id` is provided):
- ✅ AI chooses: `csv_to_sql_converter`, `data_analysis_service`, or `database`
- 🎯 **Full Flexibility**: All services available

### **Step-by-Step:**

1. **🔍 Context Analysis**
   - Determine if CSV file or database connection
   - Get file size and user preferences

2. **🧠 AI Decision**
   - Analyze question complexity
   - Choose optimal service based on context
   - Generate recommendation with reasoning

3. **🎯 Execute & Return**
   - Route to selected service
   - Execute query and return results

## 🗄️ **Database Query (`data_source: "database"`)**

### **Process:**
```
User Question → Generate SQL → Send to Agent → Database Query → Return Results
```

### **Step-by-Step:**

1. **🔍 Validate Connection**
   - Check `connection_id` and convert to UUID
   - Verify connection exists with agent_id and schema

2. **🤖 Generate SQL**
   - Use `TextToSQLService` to convert question to SQL
   - Input: Question + database schema

3. **📡 Execute Query**
   - Send SQL to agent via WebSocket
   - Agent executes query on database
   - Return formatted results

## 📊 **CSV Analysis (`data_source: "csv"`)**

### **Process:**
```
User Question → Load CSV → Pandas Analysis → Return Results
```

### **Step-by-Step:**

1. **🔍 Validate File**
   - Check `file_id` exists in database
   - Verify file URL is available

2. **📥 Load & Analyze**
   - Download CSV from Cloudinary
   - Convert to pandas DataFrame
   - Use `DataAnalysisService` for pandas operations

3. **📊 Return Results**
   - Execute pandas operations
   - Format results and return

## 🗃️ **CSV SQL (`data_source: "csv_sql"`)**

### **Process:**
```
User Question → Load CSV → Convert to SQLite → Generate SQL → Execute → Return Results
```

### **Step-by-Step:**

1. **🔍 Validate File**
   - Check `file_id` exists in database
   - Verify file URL is available

2. **📥 Load & Convert**
   - Download CSV from Cloudinary
   - Convert to pandas DataFrame
   - Create in-memory SQLite table

3. **🤖 Generate & Execute SQL**
   - Use `TextToSQLService` to generate SQL
   - Execute SQL on SQLite table
   - Return formatted results

## 📋 **Response Format**

```json
{
  "answer": "Human-readable answer",
  "sql_query": "Generated SQL query (if applicable)",
  "data": [["result1"], ["result2"]],
  "columns": ["column1", "column2"],
  "row_count": 2,
  "ai_routing": {
    "service_used": "csv_to_sql_converter",
    "reasoning": "Simple aggregation query",
    "confidence": 0.95
  }
}
```

## 🔧 **Key Components**

### **Services:**
- **`AIRoutingAgent`**: AI-powered routing with context-aware service isolation
- **`TextToSQLService`**: Converts natural language to SQL
- **`DataAnalysisService`**: Handles CSV data loading and pandas operations
- **`CSVToSQLConverter`**: Converts CSV to SQLite and executes SQL
- **`ConnectionManager`**: Manages WebSocket connections to agents

### **Models:**
- **`QueryRequest`**: Input validation with `data_source` and `user_preference`
- **`QueryResponse`**: Structured output format
- **`AnalysisContext`**: Context for AI routing analysis

## ⚡ **Performance**

- **AI Routing**: < 2 seconds for routing decisions
- **Database Queries**: Fast (direct database access)
- **CSV Analysis**: Medium (pandas operations)
- **CSV SQL**: Fast (SQLite in-memory)

## 🚨 **Error Handling**

### **Common Errors:**
1. **Missing Parameters**: `connection_id` or `file_id` not provided
2. **File Not Found**: CSV file doesn't exist in database
3. **Agent Disconnected**: WebSocket agent not available
4. **AI Routing Failed**: LLM couldn't analyze question
5. **SQL Generation Failed**: LLM couldn't generate valid SQL
6. **Service Isolation Violation**: AI attempted to route CSV file to database service (automatically corrected)

## 🎯 **Current Status**

✅ **Implemented and Working:**
- **AI Routing Agent**: Intelligent service selection with context-aware isolation
- **Database query flow**: Direct database access via WebSocket agents
- **CSV analysis flow**: Pandas-based data analysis
- **CSV SQL flow**: In-memory SQLite for SQL queries on CSV data
- **Service Isolation**: CSV files never route to database service

✅ **Ready for Production:**
- **Four data sources supported**: `auto`, `database`, `csv`, `csv_sql`
- **AI-powered routing**: Automatic optimal service selection
- **Service isolation**: CSV files only use CSV services
- **Multiple safety layers**: Prompt restriction + validation + endpoint checks
- **Comprehensive error handling**: Graceful fallbacks and error recovery

## 🎯 **Key Benefits**

- **🧠 Intelligent Decisions**: AI analyzes questions and selects optimal service
- **⚡ Optimal Performance**: Right tool for the right job automatically
- **🎯 User-Friendly**: No technical decisions required from users
- **📊 Context-Aware**: Considers file size, preferences, and question complexity
- **🔒 Service Isolation**: CSV files never route to database service (agent-postgresql)
- **🛡️ Multiple Safety Layers**: Prompt restriction + validation + endpoint checks
- **🔄 Seamless Experience**: Transparent routing with explanations

---

**The system now supports four complete query flows with AI-powered intelligent routing, giving users maximum flexibility and optimal performance!** 🎉🤖✨
