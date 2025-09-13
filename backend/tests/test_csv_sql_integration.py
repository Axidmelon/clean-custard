# File: backend/tests/test_csv_sql_integration.py

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

# Import the main app and dependencies
from main import app
from db.dependencies import get_db
from db.models import UploadedFile, User, Organization
import uuid

class TestCSVSQLIntegration:
    """Integration tests for the complete CSV-to-SQL flow."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
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
    def mock_db_session(self):
        """Mock database session."""
        session = MagicMock(spec=Session)
        return session
    
    @pytest.fixture
    def mock_uploaded_file(self):
        """Mock uploaded file."""
        file_id = str(uuid.uuid4())
        return UploadedFile(
            id=file_id,
            original_filename="test_data.csv",
            file_size="1000",
            file_path="test/path",
            file_url="https://example.com/test.csv",
            content_type="text/csv",
            cloudinary_public_id="test_id",
            organization_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
    
    def test_csv_sql_query_endpoint(self, client, sample_csv_data, mock_db_session, mock_uploaded_file):
        """Test the complete CSV SQL query endpoint."""
        
        # Mock the database query
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_uploaded_file
        
        # Mock the data analysis service
        with patch('services.data_analysis_service.data_analysis_service._get_csv_data') as mock_get_csv:
            # Create a mock DataFrame
            import pandas as pd
            from io import StringIO
            mock_df = pd.read_csv(StringIO(sample_csv_data))
            mock_get_csv.return_value = mock_df
            
            # Mock the CSV to SQL converter
            with patch('services.csv_to_sql_converter.csv_to_sql_converter') as mock_converter:
                # Mock converter methods
                mock_converter.convert_csv_to_sql.return_value = "csv_data_test"
                mock_converter.get_table_schema.return_value = {
                    "columns": [
                        {"name": "name", "type": "TEXT"},
                        {"name": "age", "type": "INTEGER"},
                        {"name": "salary", "type": "INTEGER"},
                        {"name": "department", "type": "TEXT"}
                    ],
                    "sample_data": [("John", 25, 50000, "Engineering")]
                }
                mock_converter.execute_sql_query.return_value = {
                    "success": True,
                    "data": [[50000]],
                    "columns": ["avg_salary"],
                    "row_count": 1
                }
                
                # Mock TextToSQLService
                with patch('llm.services.TextToSQLService') as mock_text_to_sql:
                    mock_text_to_sql.return_value.generate_sql.return_value = "SELECT AVG(salary) FROM csv_data_test"
                    
                    # Mock database dependency
                    with patch('db.dependencies.get_db', return_value=mock_db_session):
                        # Make the request
                        response = client.post(
                            "/api/v1/query",
                            json={
                                "file_id": str(mock_uploaded_file.id),
                                "question": "What is the average salary?",
                                "data_source": "csv_sql"
                            }
                        )
                        
                        # Verify response
                        assert response.status_code == 200
                        data = response.json()
                        
                        assert "answer" in data
                        assert "sql_query" in data
                        assert "data" in data
                        assert "columns" in data
                        assert "row_count" in data
                        
                        assert data["sql_query"] == "SELECT AVG(salary) FROM csv_data_test"
                        assert data["row_count"] == 1
                        assert data["data"] == [[50000]]
    
    def test_csv_sql_query_missing_file(self, client, mock_db_session):
        """Test CSV SQL query with missing file."""
        
        # Mock database query to return None (file not found)
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Mock database dependency
        with patch('db.dependencies.get_db', return_value=mock_db_session):
            response = client.post(
                "/api/v1/query",
                json={
                    "file_id": "nonexistent-file-id",
                    "question": "What is the average salary?",
                    "data_source": "csv_sql"
                }
            )
            
            # Verify error response
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "not found" in data["detail"].lower()
    
    def test_csv_sql_query_invalid_data_source(self, client):
        """Test CSV SQL query with invalid data source."""
        
        response = client.post(
            "/api/v1/query",
            json={
                "file_id": "test-file-id",
                "question": "What is the average salary?",
                "data_source": "invalid_source"
            }
        )
        
        # Should route to database query handler and fail due to missing connection_id
        assert response.status_code == 400
        data = response.json()
        assert "connection_id is required" in data["detail"]
    
    def test_csv_sql_query_missing_file_id(self, client):
        """Test CSV SQL query without file_id."""
        
        response = client.post(
            "/api/v1/query",
            json={
                "question": "What is the average salary?",
                "data_source": "csv_sql"
            }
        )
        
        # Verify error response
        assert response.status_code == 400
        data = response.json()
        assert "file_id is required" in data["detail"]

# Test the different data source routing
class TestQueryRouting:
    """Test the query routing logic."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_database_query_routing(self, client):
        """Test that database queries are routed correctly."""
        
        response = client.post(
            "/api/v1/query",
            json={
                "connection_id": "test-connection-id",
                "question": "What is the average salary?",
                "data_source": "database"
            }
        )
        
        # Should fail due to missing connection in database, but routing should work
        assert response.status_code == 404  # Connection not found
        data = response.json()
        assert "Connection not found" in data["detail"]
    
    def test_csv_query_routing(self, client):
        """Test that CSV queries are routed correctly."""
        
        response = client.post(
            "/api/v1/query",
            json={
                "file_id": "test-file-id",
                "question": "What is the average salary?",
                "data_source": "csv"
            }
        )
        
        # Should fail due to missing file, but routing should work
        assert response.status_code == 404  # File not found
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_csv_sql_query_routing(self, client):
        """Test that CSV SQL queries are routed correctly."""
        
        response = client.post(
            "/api/v1/query",
            json={
                "file_id": "test-file-id",
                "question": "What is the average salary?",
                "data_source": "csv_sql"
            }
        )
        
        # Should fail due to missing file, but routing should work
        assert response.status_code == 404  # File not found
        data = response.json()
        assert "not found" in data["detail"].lower()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
