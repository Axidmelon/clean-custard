# File: backend/services/railway_csv_to_sql_converter.py
# Railway-optimized CSV-to-SQL converter using PostgreSQL

import pandas as pd
import logging
from typing import Dict, Any, Optional
from io import StringIO
from sqlalchemy import create_engine, text
from core.config import settings

logger = logging.getLogger(__name__)

class RailwayCSVToSQLConverter:
    """
    Railway-optimized CSV-to-SQL converter using PostgreSQL for persistence.
    
    This version stores SQL tables in Railway's PostgreSQL database instead of in-memory SQLite.
    """
    
    def __init__(self):
        """Initialize with PostgreSQL connection."""
        self.engine = create_engine(settings.database_url)
        self.table_prefix = "csv_data_"
        logger.info("Railway CSV-to-SQL Converter initialized with PostgreSQL")
    
    async def convert_csv_to_sql(self, file_id: str, csv_data: str) -> str:
        """
        Convert CSV data to PostgreSQL table.
        
        Args:
            file_id: Unique identifier for the file
            csv_data: CSV content as string
            
        Returns:
            Table name for SQL queries
        """
        try:
            logger.info(f"Converting CSV to PostgreSQL table for file_id: {file_id}")
            
            # Load CSV into DataFrame
            df = pd.read_csv(StringIO(csv_data))
            
            if df.empty:
                raise ValueError("CSV file appears to be empty")
            
            # Generate table name
            table_name = f"{self.table_prefix}{file_id.replace('-', '_')}"
            
            # Convert DataFrame to PostgreSQL table
            df.to_sql(
                table_name, 
                self.engine, 
                if_exists='replace', 
                index=False,
                method='multi'
            )
            
            logger.info(f"Successfully created PostgreSQL table: {table_name}")
            return table_name
            
        except Exception as e:
            logger.error(f"Error converting CSV to PostgreSQL: {e}")
            raise
    
    async def execute_sql_query(self, file_id: str, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL query on PostgreSQL table.
        
        Args:
            file_id: Unique identifier for the file
            sql_query: SQL query to execute
            
        Returns:
            Query results with metadata
        """
        try:
            table_name = f"{self.table_prefix}{file_id.replace('-', '_')}"
            
            # Replace table references in query
            sanitized_query = sql_query.replace('FROM csv_data', f'FROM {table_name}')
            sanitized_query = sanitized_query.replace('from csv_data', f'from {table_name}')
            
            # Execute query
            with self.engine.connect() as conn:
                result = conn.execute(text(sanitized_query))
                rows = result.fetchall()
                columns = list(result.keys()) if result.keys() else []
                
                # Convert to list format
                data = [list(row) for row in rows]
                
                return {
                    "data": data,
                    "columns": columns,
                    "row_count": len(data),
                    "success": True,
                    "query": sanitized_query
                }
                
        except Exception as e:
            logger.error(f"Error executing PostgreSQL query: {e}")
            return {
                "error": f"PostgreSQL query failed: {e}",
                "success": False,
                "query": sql_query
            }
    
    async def cleanup_file_data(self, file_id: str):
        """
        Clean up PostgreSQL table.
        
        Args:
            file_id: Unique identifier for the file
        """
        try:
            table_name = f"{self.table_prefix}{file_id.replace('-', '_')}"
            
            # Drop the table
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                conn.commit()
            
            logger.info(f"Cleaned up PostgreSQL table: {table_name}")
            
        except Exception as e:
            logger.error(f"Error cleaning up PostgreSQL table: {e}")

# Global instance
railway_csv_to_sql_converter = RailwayCSVToSQLConverter()
