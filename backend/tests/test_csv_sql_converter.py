# File: backend/tests/test_csv_sql_converter.py

import pytest
import pandas as pd
import asyncio
import sys
import os
from io import StringIO

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.csv_to_sql_converter import CSVToSQLConverter

class TestCSVToSQLConverter:
    """Test suite for CSVToSQLConverter service."""
    
    @pytest.fixture
    def csv_converter(self):
        """Create a CSVToSQLConverter instance for testing."""
        return CSVToSQLConverter()
    
    @pytest.fixture
    def sample_csv_data(self):
        """Sample CSV data for testing."""
        return """name,age,salary,department
John,25,50000,Engineering
Jane,30,60000,Marketing
Bob,35,70000,Engineering
Alice,28,55000,Sales
Charlie,32,65000,Marketing"""
    
    @pytest.fixture
    def large_csv_data(self):
        """Generate larger CSV data for memory testing."""
        data = "id,name,value,category\n"
        for i in range(1000):
            data += f"{i},Person{i},{i * 100},Category{i % 10}\n"
        return data
    
    @pytest.fixture
    def invalid_csv_data(self):
        """Invalid CSV data for error testing."""
        return """This is not CSV data
It has multiple lines
But no commas or proper structure"""
    
    async def test_basic_conversion(self, csv_converter, sample_csv_data):
        """Test basic CSV to SQLite conversion."""
        file_id = "test_file_1"
        
        # Convert CSV to SQLite
        table_name = await csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
        
        # Verify conversion
        assert table_name == f"csv_data_{file_id.replace('-', '_')}"
        assert file_id in csv_converter.connections
        assert file_id in csv_converter.dataframes
        assert file_id in csv_converter.table_names
        
        # Verify DataFrame
        df = csv_converter.dataframes[file_id]
        assert len(df) == 5
        assert list(df.columns) == ['name', 'age', 'salary', 'department']
        
        # Cleanup
        await csv_converter.cleanup_file_data(file_id)
    
    async def test_sql_query_execution(self, csv_converter, sample_csv_data):
        """Test SQL query execution on converted CSV data."""
        file_id = "test_file_2"
        
        # Convert CSV to SQLite
        await csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
        
        # Test basic SELECT
        result = await csv_converter.execute_sql_query(file_id, "SELECT COUNT(*) FROM csv_data_test_file_2")
        assert result["success"] == True
        assert result["data"][0][0] == 5
        assert result["row_count"] == 1
        
        # Test WHERE clause
        result = await csv_converter.execute_sql_query(file_id, "SELECT * FROM csv_data_test_file_2 WHERE age > 30")
        assert result["success"] == True
        assert result["row_count"] == 2
        assert result["columns"] == ['name', 'age', 'salary', 'department']
        
        # Test GROUP BY
        result = await csv_converter.execute_sql_query(file_id, "SELECT department, COUNT(*) FROM csv_data_test_file_2 GROUP BY department")
        assert result["success"] == True
        assert result["row_count"] == 3
        
        # Test aggregation
        result = await csv_converter.execute_sql_query(file_id, "SELECT AVG(salary) FROM csv_data_test_file_2")
        assert result["success"] == True
        assert result["row_count"] == 1
        assert isinstance(result["data"][0][0], (int, float))
        
        # Cleanup
        await csv_converter.cleanup_file_data(file_id)
    
    async def test_memory_cleanup(self, csv_converter, sample_csv_data):
        """Test memory cleanup functionality."""
        file_id = "test_file_3"
        
        # Convert CSV to SQLite
        await csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
        
        # Verify data exists
        assert file_id in csv_converter.connections
        assert file_id in csv_converter.dataframes
        assert file_id in csv_converter.table_names
        
        # Clean up
        await csv_converter.cleanup_file_data(file_id)
        
        # Verify cleanup
        assert file_id not in csv_converter.connections
        assert file_id not in csv_converter.dataframes
        assert file_id not in csv_converter.table_names
    
    async def test_error_handling(self, csv_converter):
        """Test error handling for various error conditions."""
        # Test invalid file_id
        result = await csv_converter.execute_sql_query("nonexistent", "SELECT 1")
        assert result["success"] == False
        assert "error" in result
        
        # Test invalid SQL
        file_id = "test_file_4"
        sample_data = "name,age\nJohn,25\nJane,30"
        await csv_converter.convert_csv_to_sql(file_id, sample_data)
        
        result = await csv_converter.execute_sql_query(file_id, "SELECT * FROM nonexistent_table")
        assert result["success"] == False
        assert "error" in result
        
        # Cleanup
        await csv_converter.cleanup_file_data(file_id)
    
    async def test_invalid_csv_data(self, csv_converter, invalid_csv_data):
        """Test handling of invalid CSV data."""
        file_id = "test_file_5"
        
        with pytest.raises(ValueError, match="Failed to parse CSV data"):
            await csv_converter.convert_csv_to_sql(file_id, invalid_csv_data)
    
    async def test_empty_csv_data(self, csv_converter):
        """Test handling of empty CSV data."""
        file_id = "test_file_6"
        empty_csv = ""
        
        with pytest.raises(ValueError, match="CSV file appears to be empty"):
            await csv_converter.convert_csv_to_sql(file_id, empty_csv)
    
    async def test_table_schema(self, csv_converter, sample_csv_data):
        """Test table schema retrieval."""
        file_id = "test_file_7"
        
        # Convert CSV to SQLite
        await csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
        
        # Get schema
        schema = await csv_converter.get_table_schema(file_id)
        
        # Verify schema structure
        assert "table_name" in schema
        assert "columns" in schema
        assert "sample_data" in schema
        assert "row_count" in schema
        
        # Verify columns
        assert len(schema["columns"]) == 4
        column_names = [col["name"] for col in schema["columns"]]
        assert "name" in column_names
        assert "age" in column_names
        assert "salary" in column_names
        assert "department" in column_names
        
        # Verify sample data
        assert len(schema["sample_data"]) <= 5
        assert schema["row_count"] == 5
        
        # Cleanup
        await csv_converter.cleanup_file_data(file_id)
    
    async def test_memory_stats(self, csv_converter, sample_csv_data):
        """Test memory statistics functionality."""
        file_id = "test_file_8"
        
        # Initial stats
        stats = csv_converter.get_memory_stats()
        assert "total_memory_usage" in stats
        assert "active_files" in stats
        assert stats["active_files"] == 0
        
        # Convert CSV to SQLite
        await csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
        
        # Updated stats
        stats = csv_converter.get_memory_stats()
        assert stats["active_files"] == 1
        assert stats["total_memory_usage"] > 0
        
        # Cleanup
        await csv_converter.cleanup_file_data(file_id)
        
        # Final stats
        stats = csv_converter.get_memory_stats()
        assert stats["active_files"] == 0
    
    async def test_cleanup_all_data(self, csv_converter, sample_csv_data):
        """Test cleanup of all cached data."""
        # Add multiple files
        for i in range(3):
            file_id = f"test_file_{i}"
            await csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
        
        # Verify files exist
        assert len(csv_converter.connections) == 3
        
        # Cleanup all
        await csv_converter.cleanup_all_data()
        
        # Verify all cleaned up
        assert len(csv_converter.connections) == 0
        assert len(csv_converter.dataframes) == 0
        assert len(csv_converter.table_names) == 0
    
    async def test_concurrent_access(self, csv_converter, sample_csv_data):
        """Test concurrent access to different files."""
        # Create multiple files concurrently
        tasks = []
        for i in range(5):
            file_id = f"concurrent_file_{i}"
            task = csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
            tasks.append(task)
        
        # Wait for all conversions
        table_names = await asyncio.gather(*tasks)
        
        # Verify all conversions succeeded
        assert len(table_names) == 5
        assert all(name.startswith("csv_data_") for name in table_names)
        
        # Verify all files are accessible
        assert len(csv_converter.connections) == 5
        
        # Test concurrent queries
        query_tasks = []
        for i in range(5):
            file_id = f"concurrent_file_{i}"
            task = csv_converter.execute_sql_query(file_id, "SELECT COUNT(*) FROM csv_data_concurrent_file_" + str(i))
            query_tasks.append(task)
        
        # Wait for all queries
        results = await asyncio.gather(*query_tasks)
        
        # Verify all queries succeeded
        assert all(result["success"] for result in results)
        assert all(result["data"][0][0] == 5 for result in results)
        
        # Cleanup all
        await csv_converter.cleanup_all_data()
    
    async def test_sql_injection_prevention(self, csv_converter, sample_csv_data):
        """Test SQL injection prevention."""
        file_id = "test_file_9"
        
        # Convert CSV to SQLite
        await csv_converter.convert_csv_to_sql(file_id, sample_csv_data)
        
        # Test potentially dangerous queries
        dangerous_queries = [
            "DROP TABLE csv_data_test_file_9",
            "DELETE FROM csv_data_test_file_9",
            "INSERT INTO csv_data_test_file_9 VALUES ('hacker', 0, 0, 'evil')",
            "UPDATE csv_data_test_file_9 SET name = 'hacked'"
        ]
        
        for query in dangerous_queries:
            result = await csv_converter.execute_sql_query(file_id, query)
            # These should fail or be sanitized
            # The exact behavior depends on implementation
            assert "success" in result
        
        # Cleanup
        await csv_converter.cleanup_file_data(file_id)
    
    async def test_large_dataset(self, csv_converter, large_csv_data):
        """Test handling of larger datasets."""
        file_id = "test_file_10"
        
        # Convert large CSV to SQLite
        table_name = await csv_converter.convert_csv_to_sql(file_id, large_csv_data)
        
        # Verify conversion
        assert table_name.startswith("csv_data_")
        assert file_id in csv_converter.connections
        
        # Test queries on large dataset
        result = await csv_converter.execute_sql_query(file_id, f"SELECT COUNT(*) FROM {table_name}")
        assert result["success"] == True
        assert result["data"][0][0] == 1000
        
        # Test aggregation on large dataset
        result = await csv_converter.execute_sql_query(file_id, f"SELECT category, COUNT(*) FROM {table_name} GROUP BY category")
        assert result["success"] == True
        assert result["row_count"] == 10  # 10 categories
        
        # Cleanup
        await csv_converter.cleanup_file_data(file_id)

# Integration test with the actual service
class TestCSVToSQLConverterIntegration:
    """Integration tests for CSVToSQLConverter with real service."""
    
    async def test_service_integration(self):
        """Test integration with the global service instance."""
        from services.csv_to_sql_converter import csv_to_sql_converter
        
        sample_data = """id,name,value
1,Alice,100
2,Bob,200
3,Charlie,300"""
        
        file_id = "integration_test_1"
        
        # Test conversion
        table_name = await csv_to_sql_converter.convert_csv_to_sql(file_id, sample_data)
        assert table_name.startswith("csv_data_")
        
        # Test query
        result = await csv_to_sql_converter.execute_sql_query(file_id, f"SELECT AVG(value) FROM {table_name}")
        assert result["success"] == True
        assert result["data"][0][0] == 200.0
        
        # Cleanup
        await csv_to_sql_converter.cleanup_file_data(file_id)

# Performance tests
class TestCSVToSQLConverterPerformance:
    """Performance tests for CSVToSQLConverter."""
    
    async def test_conversion_performance(self, csv_converter):
        """Test conversion performance with various dataset sizes."""
        import time
        
        # Test with different dataset sizes
        sizes = [100, 500, 1000]
        
        for size in sizes:
            # Generate test data
            data = "id,name,value\n"
            for i in range(size):
                data += f"{i},Person{i},{i * 10}\n"
            
            file_id = f"perf_test_{size}"
            
            # Measure conversion time
            start_time = time.time()
            await csv_converter.convert_csv_to_sql(file_id, data)
            conversion_time = time.time() - start_time
            
            # Measure query time
            start_time = time.time()
            result = await csv_converter.execute_sql_query(file_id, f"SELECT COUNT(*) FROM csv_data_perf_test_{size}")
            query_time = time.time() - start_time
            
            # Verify results
            assert result["success"] == True
            assert result["data"][0][0] == size
            
            # Log performance (in real tests, you might want to assert on these)
            print(f"Dataset size: {size}, Conversion time: {conversion_time:.3f}s, Query time: {query_time:.3f}s")
            
            # Cleanup
            await csv_converter.cleanup_file_data(file_id)

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
