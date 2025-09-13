# CSV-to-SQL Implementation Plan

## **Overview**
Implementing DataFrame + SQLite approach to enable SQL queries on uploaded CSV data in clean-custard.

## **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User's Browser │    │  Clean-Custard  │    │   Cloudinary    │
│                 │    │     Backend      │    │   (File Storage)│
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Upload CSV    │───▶│ • Receive CSV   │───▶│ • Store CSV     │
│ • Ask Questions │───▶│ • Download CSV  │    │                 │
│ • View Results  │◀───│ • Process Data  │◀───│ • Serve CSV     │
│                 │    │ • Execute SQL   │    │                 │
│                 │    │ • Send Results  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Our Server    │
                    │      RAM        │
                    ├─────────────────┤
                    │ • CSV DataFrame │
                    │ • SQLite Table  │
                    │ • Query Results │
                    └─────────────────┘
```

### **Data Flow Process**
1. **User uploads CSV** → Stored on **our servers** (Cloudinary)
2. **User asks SQL question** → **Our backend** downloads CSV
3. **Our backend** loads CSV into **our server's RAM**
4. **Our backend** creates SQLite table in **our server's RAM**
5. **Our backend** executes SQL query on **our servers**
6. **Our backend** sends results to user's browser
7. **User's browser** just displays the results

### **Memory Usage**
- **Our Servers**: ~100MB per active user
- **User's Browser**: ~1MB (just UI data)

## **Implementation Phases**

### **Phase 1: Core Implementation (Weeks 1-4)**
**Goal**: Basic CSV-to-SQL functionality working end-to-end

#### **Task 1: Architecture Analysis & Integration Points**
- Analyze current `DataAnalysisService` and `TextToSQLService`
- Identify integration points with existing query endpoint
- Design CSVToSQLConverter class structure
- Plan memory management strategy

#### **Task 2: CSVToSQLConverter Implementation**
- Create `CSVToSQLConverter` class in `backend/services/`
- Implement CSV → DataFrame → SQLite conversion
- Add SQL query execution capabilities
- Implement memory cleanup and connection management

#### **Task 3: Enhanced Query Endpoint**
- Modify `backend/api/v1/endpoints/query.py`
- Add CSV SQL query routing logic
- Integrate with existing `TextToSQLService`
- Handle both database and CSV data sources seamlessly

#### **Task 4: Testing & Validation**
- Create comprehensive test suite
- Test with various CSV file sizes and structures
- Validate SQL query execution
- Test error handling and edge cases

### **Phase 2: Enhancement & Optimization (Weeks 5-6)**
**Goal**: Production-ready features and performance optimization

#### **Task 5: Advanced SQL Features**
- Add support for complex SQL operations
- Implement query validation and security
- Add query explanation and optimization hints
- Support for advanced SQL syntax

#### **Task 6: Performance Optimization**
- Implement query result caching
- Add memory usage monitoring
- Optimize DataFrame to SQLite conversion
- Add connection pooling and resource management

#### **Task 7: Frontend Integration**
- Update `TalkData` component to support SQL queries
- Add SQL query interface alongside natural language
- Implement result comparison (SQL vs Python)
- Add query history and favorites

### **Phase 3: Production & Monitoring (Weeks 7-8)**
**Goal**: Production deployment and monitoring

#### **Task 8: Production Safeguards**
- Add comprehensive error handling
- Implement memory limits and file size restrictions
- Add logging and monitoring
- Create deployment documentation

## **Detailed Implementation Tasks**

### **Phase 1: Core Implementation**

#### **1.1 Create CSVToSQLConverter Service**
```python
# File: backend/services/csv_to_sql_converter.py
class CSVToSQLConverter:
    def __init__(self):
        self.connections = {}  # {file_id: sqlite_connection}
        self.dataframes = {}    # {file_id: pandas_dataframe}
    
    async def convert_csv_to_sql(self, file_id: str, csv_data: str) -> str:
        """Convert CSV data to SQLite table"""
        
    async def execute_sql_query(self, file_id: str, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query on CSV data"""
        
    async def cleanup_file_data(self, file_id: str):
        """Clean up memory when done"""
```

#### **1.2 Enhance Query Endpoint**
```python
# File: backend/api/v1/endpoints/query.py
async def handle_csv_sql_query(request: QueryRequest, db: Session) -> QueryResponse:
    """Handle SQL queries on CSV data using in-memory SQLite"""
    
    # 1. Get CSV data
    # 2. Convert to SQLite table
    # 3. Generate SQL query
    # 4. Execute SQL on CSV data
    # 5. Return formatted results
```

#### **1.3 Integration with Existing Services**
- Leverage existing `DataAnalysisService` for CSV data loading
- Use existing `TextToSQLService` for SQL query generation
- Integrate with existing file upload and storage system

#### **1.4 Testing Implementation**
```python
# File: backend/tests/test_csv_sql_converter.py
class TestCSVToSQLConverter:
    def test_basic_conversion(self):
        """Test CSV to SQLite conversion"""
        
    def test_sql_query_execution(self):
        """Test SQL query execution"""
        
    def test_memory_cleanup(self):
        """Test memory cleanup"""
        
    def test_error_handling(self):
        """Test error handling"""
```

### **Phase 2: Enhancement**

#### **2.1 Advanced SQL Features**
- Window functions (ROW_NUMBER, RANK, DENSE_RANK)
- Complex joins (INNER, LEFT, RIGHT, FULL OUTER)
- Subqueries and CTEs
- String and date functions

#### **2.2 Performance Optimization**
- Query result caching
- Memory usage monitoring
- Connection pooling
- Background processing for large files

#### **2.3 Frontend Integration**
- SQL query interface in TalkData component
- Query mode selection (Natural Language vs SQL)
- Result comparison and explanation
- Query history and favorites

### **Phase 3: Production**

#### **3.1 Production Safeguards**
- File size limits (100MB)
- Memory usage limits (200MB per user)
- Query timeout limits (30 seconds)
- Error handling and recovery

#### **3.2 Monitoring & Metrics**
- Query execution time tracking
- Memory usage monitoring
- Error rate tracking
- User engagement metrics

## **File Structure**

```
backend/
├── services/
│   ├── csv_to_sql_converter.py     # New: Core CSV-to-SQL conversion
│   ├── data_analysis_service.py    # Existing: CSV data loading
│   └── user_services.py            # Existing: User management
├── api/v1/endpoints/
│   └── query.py                    # Enhanced: Support CSV SQL queries
├── tests/
│   └── test_csv_sql_converter.py   # New: Comprehensive tests
└── requirements.txt                # Updated: Add sqlite3 (built-in)
```

## **Dependencies**

### **New Dependencies**
- `sqlite3` (built-in Python module)
- No additional external dependencies required

### **Existing Dependencies Used**
- `pandas` (already in requirements.txt)
- `sqlalchemy` (already in requirements.txt)
- `fastapi` (already in requirements.txt)

## **Success Criteria**

### **Phase 1 Success**
- ✅ CSV files can be converted to SQLite tables
- ✅ SQL queries can be executed on CSV data
- ✅ Results are returned in consistent format
- ✅ Basic error handling works
- ✅ Memory cleanup functions properly

### **Phase 2 Success**
- ✅ Advanced SQL features work
- ✅ Performance is optimized
- ✅ Frontend integration complete
- ✅ User experience is smooth

### **Phase 3 Success**
- ✅ Production deployment successful
- ✅ Monitoring and metrics working
- ✅ Error rates < 0.1%
- ✅ User satisfaction > 4.5/5

## **Risk Mitigation**

### **Memory Management**
- Implement file size limits (100MB)
- Add memory usage monitoring
- Automatic cleanup when sessions end
- Resource quotas per user

### **Performance**
- Query result caching
- Connection pooling
- Background processing for large files
- Timeout limits

### **Error Handling**
- Graceful error messages
- Fallback to pandas operations
- Comprehensive logging
- User-friendly error recovery

## **Timeline**

- **Week 1**: Architecture analysis and CSVToSQLConverter implementation
- **Week 2**: Query endpoint enhancement and integration
- **Week 3**: Testing and validation
- **Week 4**: Phase 1 completion and review
- **Week 5**: Advanced features and optimization
- **Week 6**: Frontend integration
- **Week 7**: Production safeguards and monitoring
- **Week 8**: Deployment and final testing

## **Implementation Checklist**

### **Phase 1: Core Implementation**
- [ ] **Task 1**: Architecture Analysis & Integration Points
  - [ ] Analyze current DataAnalysisService
  - [ ] Analyze current TextToSQLService
  - [ ] Identify integration points
  - [ ] Design CSVToSQLConverter class structure
  - [ ] Plan memory management strategy

- [ ] **Task 2**: CSVToSQLConverter Implementation
  - [ ] Create CSVToSQLConverter class
  - [ ] Implement CSV → DataFrame → SQLite conversion
  - [ ] Add SQL query execution capabilities
  - [ ] Implement memory cleanup and connection management
  - [ ] Add error handling and validation

- [ ] **Task 3**: Enhanced Query Endpoint
  - [ ] Modify query.py endpoint
  - [ ] Add CSV SQL query routing logic
  - [ ] Integrate with existing TextToSQLService
  - [ ] Handle both database and CSV data sources
  - [ ] Test endpoint functionality

- [ ] **Task 4**: Testing & Validation
  - [ ] Create comprehensive test suite
  - [ ] Test with various CSV file sizes
  - [ ] Test with different CSV structures
  - [ ] Validate SQL query execution
  - [ ] Test error handling and edge cases
  - [ ] Performance testing

### **Phase 2: Enhancement & Optimization**
- [ ] **Task 5**: Advanced SQL Features
  - [ ] Add window functions support
  - [ ] Implement complex joins
  - [ ] Add subqueries and CTEs
  - [ ] Implement string and date functions
  - [ ] Add query validation and security

- [ ] **Task 6**: Performance Optimization
  - [ ] Implement query result caching
  - [ ] Add memory usage monitoring
  - [ ] Optimize DataFrame to SQLite conversion
  - [ ] Add connection pooling
  - [ ] Implement resource management

- [ ] **Task 7**: Frontend Integration
  - [ ] Update TalkData component
  - [ ] Add SQL query interface
  - [ ] Implement query mode selection
  - [ ] Add result comparison
  - [ ] Implement query history

### **Phase 3: Production & Monitoring**
- [ ] **Task 8**: Production Safeguards
  - [ ] Add comprehensive error handling
  - [ ] Implement memory limits
  - [ ] Add file size restrictions
  - [ ] Add logging and monitoring
  - [ ] Create deployment documentation

## **Code Examples**

### **CSVToSQLConverter Class Structure**
```python
import sqlite3
import pandas as pd
from typing import Dict, Any, Optional
import logging

class CSVToSQLConverter:
    """
    Converts CSV data to SQL-queryable format using in-memory SQLite
    """
    
    def __init__(self):
        self.connections = {}  # {file_id: sqlite_connection}
        self.dataframes = {}    # {file_id: pandas_dataframe}
        self.max_memory_per_file = 100 * 1024 * 1024  # 100MB
        self.max_total_memory = 500 * 1024 * 1024     # 500MB
        self.logger = logging.getLogger(__name__)
    
    async def convert_csv_to_sql(self, file_id: str, csv_data: str) -> str:
        """
        Convert CSV data to SQLite table
        
        Args:
            file_id: Unique identifier for the file
            csv_data: CSV content as string
            
        Returns:
            Table name for SQL queries
        """
        try:
            # Load CSV into DataFrame
            df = pd.read_csv(StringIO(csv_data))
            
            # Check memory usage
            if not await self._check_memory_usage(file_id, df):
                raise ValueError("File too large for in-memory processing")
            
            # Create in-memory SQLite database
            conn = sqlite3.connect(':memory:')
            
            # Convert DataFrame to SQLite table
            df.to_sql('csv_data', conn, index=False, if_exists='replace')
            
            # Cache connection and DataFrame
            self.connections[file_id] = conn
            self.dataframes[file_id] = df
            
            self.logger.info(f"Successfully converted CSV to SQLite for file_id: {file_id}")
            return "csv_data"
            
        except Exception as e:
            self.logger.error(f"Error converting CSV to SQLite: {e}")
            raise
    
    async def execute_sql_query(self, file_id: str, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL query on CSV data
        
        Args:
            file_id: Unique identifier for the file
            sql_query: SQL query to execute
            
        Returns:
            Query results with metadata
        """
        try:
            if file_id not in self.connections:
                raise ValueError(f"No SQLite connection found for file_id: {file_id}")
            
            conn = self.connections[file_id]
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(sql_query)
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            return {
                "data": results,
                "columns": columns,
                "row_count": len(results),
                "success": True
            }
            
        except sqlite3.Error as e:
            return {
                "error": f"SQL execution failed: {e}",
                "success": False
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {e}",
                "success": False
            }
    
    async def cleanup_file_data(self, file_id: str):
        """
        Clean up memory when user is done with file
        
        Args:
            file_id: Unique identifier for the file
        """
        try:
            # Close SQLite connection
            if file_id in self.connections:
                self.connections[file_id].close()
                del self.connections[file_id]
            
            # Remove DataFrame from memory
            if file_id in self.dataframes:
                del self.dataframes[file_id]
            
            # Force garbage collection
            import gc
            gc.collect()
            
            self.logger.info(f"Cleaned up memory for file_id: {file_id}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up memory: {e}")
    
    async def _check_memory_usage(self, file_id: str, df: pd.DataFrame) -> bool:
        """
        Check if file can fit in memory
        
        Args:
            file_id: Unique identifier for the file
            df: DataFrame to check
            
        Returns:
            True if file can fit, False otherwise
        """
        file_size = df.memory_usage(deep=True).sum()
        total_memory = sum([df.memory_usage(deep=True).sum() for df in self.dataframes.values()])
        
        if file_size > self.max_memory_per_file:
            self.logger.warning(f"File {file_id} too large: {file_size} bytes")
            return False
        
        if total_memory + file_size > self.max_total_memory:
            self.logger.warning(f"Total memory limit exceeded: {total_memory + file_size} bytes")
            return False
        
        return True
```

### **Enhanced Query Endpoint**
```python
# File: backend/api/v1/endpoints/query.py

async def handle_csv_sql_query(request: QueryRequest, db: Session) -> QueryResponse:
    """
    Handle SQL queries on CSV data using in-memory SQLite
    """
    from services.csv_to_sql_converter import CSVToSQLConverter
    from services.data_analysis_service import data_analysis_service
    from llm.services import TextToSQLService
    
    try:
        logger.info(f"Processing CSV SQL query for file_id: {request.file_id}")
        
        # Get CSV data
        df = await data_analysis_service._get_csv_data(request.file_id)
        if df is None:
            raise HTTPException(status_code=404, detail="CSV file not found")
        
        # Convert to SQLite table
        csv_converter = CSVToSQLConverter()
        table_name = await csv_converter.convert_csv_to_sql(request.file_id, df.to_csv())
        
        # Generate SQL query using existing TextToSQLService
        schema = await data_analysis_service.analyze_data_schema(request.file_id)
        text_to_sql = TextToSQLService()
        sql_query = text_to_sql.generate_sql(request.question, schema)
        
        # Execute SQL on CSV data
        result = await csv_converter.execute_sql_query(request.file_id, sql_query)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return QueryResponse(
            answer=format_agent_result(result["data"]),
            sql_query=sql_query,
            data=result["data"],
            columns=result["columns"],
            row_count=result["row_count"]
        )
        
    except Exception as e:
        logger.error(f"Error processing CSV SQL query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### **Test Implementation**
```python
# File: backend/tests/test_csv_sql_converter.py

import pytest
import pandas as pd
from io import StringIO
from services.csv_to_sql_converter import CSVToSQLConverter

class TestCSVToSQLConverter:
    
    @pytest.fixture
    def csv_converter(self):
        return CSVToSQLConverter()
    
    @pytest.fixture
    def sample_csv_data(self):
        return """name,age,salary,department
John,25,50000,Engineering
Jane,30,60000,Marketing
Bob,35,70000,Engineering
Alice,28,55000,Sales"""
    
    async def test_basic_conversion(self, csv_converter, sample_csv_data):
        """Test CSV to SQLite conversion"""
        file_id = "test_file_1"
        table_name = await csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
        
        assert table_name == "csv_data"
        assert file_id in csv_converter.connections
        assert file_id in csv_converter.dataframes
    
    async def test_sql_query_execution(self, csv_converter, sample_csv_data):
        """Test SQL query execution"""
        file_id = "test_file_2"
        await csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
        
        # Test basic SELECT
        result = await csv_converter.execute_sql_query(file_id, "SELECT COUNT(*) FROM csv_data")
        assert result["success"] == True
        assert result["data"][0][0] == 4
        
        # Test WHERE clause
        result = await csv_converter.execute_sql_query(file_id, "SELECT * FROM csv_data WHERE age > 30")
        assert result["success"] == True
        assert result["row_count"] == 1
        
        # Test GROUP BY
        result = await csv_converter.execute_sql_query(file_id, "SELECT department, COUNT(*) FROM csv_data GROUP BY department")
        assert result["success"] == True
        assert result["row_count"] == 3
    
    async def test_memory_cleanup(self, csv_converter, sample_csv_data):
        """Test memory cleanup"""
        file_id = "test_file_3"
        await csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
        
        # Verify data exists
        assert file_id in csv_converter.connections
        assert file_id in csv_converter.dataframes
        
        # Clean up
        await csv_converter.cleanup_file_data(file_id)
        
        # Verify cleanup
        assert file_id not in csv_converter.connections
        assert file_id not in csv_converter.dataframes
    
    async def test_error_handling(self, csv_converter):
        """Test error handling"""
        # Test invalid SQL
        result = await csv_converter.execute_sql_query("nonexistent", "SELECT * FROM invalid_table")
        assert result["success"] == False
        assert "error" in result
        
        # Test invalid file_id
        result = await csv_converter.execute_sql_query("nonexistent", "SELECT 1")
        assert result["success"] == False
        assert "error" in result
```

## **Deployment Checklist**

### **Pre-Deployment**
- [ ] All tests passing
- [ ] Code review completed
- [ ] Performance testing completed
- [ ] Security review completed
- [ ] Documentation updated

### **Deployment**
- [ ] Deploy to staging environment
- [ ] Run integration tests
- [ ] Deploy to production
- [ ] Monitor error rates
- [ ] Verify functionality

### **Post-Deployment**
- [ ] Monitor performance metrics
- [ ] Collect user feedback
- [ ] Track error rates
- [ ] Monitor memory usage
- [ ] Document lessons learned

---

**Ready for Implementation!** 🚀

This comprehensive plan provides everything needed to implement the CSV-to-SQL functionality using the DataFrame + SQLite approach. The plan is structured, detailed, and includes all necessary components for successful implementation.
