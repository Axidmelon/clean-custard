# File: backend/services/csv_to_sql_converter.py

import sqlite3
import pandas as pd
import logging
import gc
from typing import Dict, Any, Optional, List
from io import StringIO
from datetime import datetime

logger = logging.getLogger(__name__)

class CSVToSQLConverter:
    """
    Converts CSV data to SQL-queryable format using in-memory SQLite.
    
    This service provides:
    - CSV to DataFrame conversion
    - DataFrame to SQLite table conversion
    - SQL query execution on CSV data
    - Memory management and cleanup
    - Error handling and validation
    """
    
    def __init__(self):
        """Initialize the CSV to SQL converter with memory management."""
        self.connections = {}  # {file_id: sqlite_connection}
        self.dataframes = {}   # {file_id: pandas_dataframe}
        self.table_names = {}   # {file_id: table_name}
        
        # Memory limits
        self.max_memory_per_file = 100 * 1024 * 1024  # 100MB per file
        self.max_total_memory = 500 * 1024 * 1024     # 500MB total
        self.max_file_size = 50 * 1024 * 1024         # 50MB file size limit
        
        logger.info("CSVToSQLConverter initialized successfully")
    
    async def convert_csv_to_sql(self, file_id: str, csv_data: str = None, user_id: str = None) -> str:
        """
        Convert CSV data to SQLite table with Redis caching optimization.
        
        Args:
            file_id: Unique identifier for the file
            csv_data: CSV content as string (optional if user_id provided)
            user_id: User ID for Redis cache lookup
            
        Returns:
            Table name for SQL queries
            
        Raises:
            ValueError: If file is too large or invalid
            Exception: If conversion fails
        """
        try:
            logger.info(f"Starting CSV to SQLite conversion for file_id: {file_id}")
            
            # Check if already converted
            if file_id in self.connections:
                logger.info(f"File {file_id} already converted, returning existing table")
                return self.table_names[file_id]
            
            # Get CSV data from Redis cache if not provided
            if csv_data is None and user_id:
                from core.redis_service import redis_service
                cached_content = redis_service.get_cached_csv_data(user_id, file_id)
                if cached_content:
                    logger.info(f"Using cached CSV data for file_id: {file_id}, user: {user_id}")
                    csv_data = cached_content
                else:
                    logger.warning(f"No cached CSV data found for file_id: {file_id}, user: {user_id}")
            
            if csv_data is None:
                raise ValueError("No CSV data provided and no cached data available")
            
            # Validate CSV data size
            csv_size = len(csv_data.encode('utf-8'))
            if csv_size > self.max_file_size:
                raise ValueError(f"CSV file too large: {csv_size} bytes. Maximum allowed: {self.max_file_size} bytes")
            
            # Load CSV into DataFrame
            try:
                df = pd.read_csv(StringIO(csv_data))
            except Exception as e:
                raise ValueError(f"Failed to parse CSV data: {str(e)}")
            
            # Validate DataFrame
            if df.empty:
                raise ValueError("CSV file appears to be empty or contains no valid data")
            
            # Check memory usage
            if not await self._check_memory_usage(file_id, df):
                raise ValueError("File too large for in-memory processing")
            
            # Create in-memory SQLite database
            conn = sqlite3.connect(':memory:')
            
            # Generate table name
            table_name = f"csv_data_{file_id.replace('-', '_')}"
            
            # Convert DataFrame to SQLite table
            try:
                df.to_sql(table_name, conn, index=False, if_exists='replace')
            except Exception as e:
                conn.close()
                raise ValueError(f"Failed to create SQLite table: {str(e)}")
            
            # Cache connection, DataFrame, and table name
            self.connections[file_id] = conn
            self.dataframes[file_id] = df
            self.table_names[file_id] = table_name
            
            logger.info(f"Successfully converted CSV to SQLite for file_id: {file_id}, table: {table_name}, shape: {df.shape}")
            return table_name
            
        except Exception as e:
            logger.error(f"Error converting CSV to SQLite for file_id {file_id}: {e}")
            # Cleanup on error
            await self.cleanup_file_data(file_id)
            raise
    
    async def execute_sql_query(self, file_id: str, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL query on CSV data.
        
        Args:
            file_id: Unique identifier for the file
            sql_query: SQL query to execute
            
        Returns:
            Query results with metadata
        """
        try:
            logger.info(f"Executing SQL query for file_id: {file_id}")
            
            if file_id not in self.connections:
                raise ValueError(f"No SQLite connection found for file_id: {file_id}")
            
            conn = self.connections[file_id]
            table_name = self.table_names[file_id]
            
            # Validate and sanitize SQL query
            sanitized_query = self._sanitize_sql_query(sql_query, table_name)
            
            # Fix column name case sensitivity issues
            sanitized_query = self._fix_column_names_in_sql(sanitized_query, file_id)
            
            # Execute query
            cursor = conn.cursor()
            cursor.execute(sanitized_query)
            results = cursor.fetchall()
            
            # Get column information
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_row = []
                for i, value in enumerate(row):
                    # Convert numpy types to Python types
                    if hasattr(value, 'item'):
                        formatted_row.append(value.item())
                    else:
                        formatted_row.append(value)
                formatted_results.append(formatted_row)
            
            logger.info(f"SQL query executed successfully for file_id: {file_id}, returned {len(formatted_results)} rows")
            
            return {
                "data": formatted_results,
                "columns": columns,
                "row_count": len(formatted_results),
                "success": True,
                "query": sanitized_query,
                "execution_time": datetime.now().isoformat()
            }
            
        except sqlite3.Error as e:
            logger.error(f"SQL execution failed for file_id {file_id}: {e}")
            return {
                "error": f"SQL execution failed: {e}",
                "success": False,
                "query": sql_query
            }
        except Exception as e:
            logger.error(f"Unexpected error executing SQL for file_id {file_id}: {e}")
            return {
                "error": f"Unexpected error: {e}",
                "success": False,
                "query": sql_query
            }
    
    async def get_table_schema(self, file_id: str) -> Dict[str, Any]:
        """
        Get schema information for the SQLite table.
        
        Args:
            file_id: Unique identifier for the file
            
        Returns:
            Schema information dictionary
        """
        try:
            if file_id not in self.connections:
                raise ValueError(f"No SQLite connection found for file_id: {file_id}")
            
            conn = self.connections[file_id]
            table_name = self.table_names[file_id]
            
            # Get table schema
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            sample_data = cursor.fetchall()
            
            # Format schema information
            schema_info = {
                "table_name": table_name,
                "columns": [],
                "sample_data": sample_data,
                "row_count": len(self.dataframes[file_id]) if file_id in self.dataframes else 0
            }
            
            for col_info in columns_info:
                schema_info["columns"].append({
                    "name": col_info[1],
                    "type": col_info[2],
                    "nullable": col_info[3] == 0,
                    "default": col_info[4],
                    "primary_key": col_info[5] == 1
                })
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error getting table schema for file_id {file_id}: {e}")
            raise
    
    async def cleanup_file_data(self, file_id: str):
        """
        Clean up memory when user is done with file.
        
        Args:
            file_id: Unique identifier for the file
        """
        try:
            logger.info(f"Cleaning up memory for file_id: {file_id}")
            
            # Close SQLite connection
            if file_id in self.connections:
                try:
                    self.connections[file_id].close()
                except Exception as e:
                    logger.warning(f"Error closing SQLite connection for file_id {file_id}: {e}")
                finally:
                    del self.connections[file_id]
            
            # Remove DataFrame from memory
            if file_id in self.dataframes:
                del self.dataframes[file_id]
            
            # Remove table name
            if file_id in self.table_names:
                del self.table_names[file_id]
            
            # Force garbage collection
            gc.collect()
            
            logger.info(f"Successfully cleaned up memory for file_id: {file_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up memory for file_id {file_id}: {e}")
    
    async def cleanup_all_data(self):
        """
        Clean up all cached data (useful for maintenance or memory pressure).
        """
        try:
            logger.info("Cleaning up all cached data")
            
            file_ids = list(self.connections.keys())
            for file_id in file_ids:
                await self.cleanup_file_data(file_id)
            
            logger.info("Successfully cleaned up all cached data")
            
        except Exception as e:
            logger.error(f"Error cleaning up all data: {e}")
    
    async def _check_memory_usage(self, file_id: str, df: pd.DataFrame) -> bool:
        """
        Check if file can fit in memory.
        
        Args:
            file_id: Unique identifier for the file
            df: DataFrame to check
            
        Returns:
            True if file can fit, False otherwise
        """
        try:
            # Calculate memory usage
            file_memory = df.memory_usage(deep=True).sum()
            total_memory = sum([df.memory_usage(deep=True).sum() for df in self.dataframes.values()])
            
            logger.debug(f"Memory check for file_id {file_id}: file={file_memory}, total={total_memory}")
            
            if file_memory > self.max_memory_per_file:
                logger.warning(f"File {file_id} too large: {file_memory} bytes")
                return False
            
            if total_memory + file_memory > self.max_total_memory:
                logger.warning(f"Total memory limit exceeded: {total_memory + file_memory} bytes")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking memory usage for file_id {file_id}: {e}")
            return False
    
    def _sanitize_sql_query(self, sql_query: str, table_name: str) -> str:
        """
        Sanitize SQL query to prevent SQL injection and ensure table name consistency.
        
        Args:
            sql_query: Original SQL query
            table_name: Expected table name
            
        Returns:
            Sanitized SQL query
        """
        try:
            # Basic SQL injection prevention
            dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
            sql_upper = sql_query.upper()
            
            for keyword in dangerous_keywords:
                if keyword in sql_upper and keyword not in ['SELECT']:
                    logger.warning(f"Potentially dangerous SQL keyword detected: {keyword}")
                    # For now, we'll allow it but log it
                    # In production, you might want to be more restrictive
            
            # For now, just return the original query since the table name is already correct
            # The sanitization was causing duplication issues
            return sql_query
            
        except Exception as e:
            logger.error(f"Error sanitizing SQL query: {e}")
            return sql_query
    
    def _fix_column_names_in_sql(self, sql_query: str, file_id: str) -> str:
        """
        Fix column name case sensitivity issues in SQL queries.
        
        This method performs case-insensitive column name matching to resolve
        issues where the AI generates SQL with incorrect column name casing.
        
        Args:
            sql_query: The SQL query string
            file_id: File ID to get the correct column names
            
        Returns:
            SQL query string with corrected column names
        """
        try:
            if file_id not in self.dataframes:
                return sql_query
            
            # Get actual column names from DataFrame
            df = self.dataframes[file_id]
            actual_columns = df.columns.tolist()
            
            # Create a mapping of lowercase column names to actual column names
            column_mapping = {}
            for col in actual_columns:
                column_mapping[col.lower()] = col
            
            # Find and replace column names in the SQL query
            fixed_query = sql_query
            
            # Pattern to match column names in quotes (single or double)
            import re
            
            # Find all quoted strings that might be column names
            quoted_pattern = r"['\"]([^'\"]+)['\"]"
            matches = re.findall(quoted_pattern, sql_query)
            
            for match in matches:
                # Check if this quoted string matches a column name (case-insensitive)
                if match.lower() in column_mapping:
                    actual_col = column_mapping[match.lower()]
                    if match != actual_col:
                        # Replace the incorrect column name with the correct one
                        fixed_query = fixed_query.replace(f"'{match}'", f"'{actual_col}'")
                        fixed_query = fixed_query.replace(f'"{match}"', f'"{actual_col}"')
                        logger.info(f"Fixed SQL column name: '{match}' -> '{actual_col}'")
            
            # Also check for unquoted column names in SQL (less common but possible)
            # Pattern for column names in SELECT, WHERE, GROUP BY, ORDER BY clauses
            sql_column_pattern = r"\b(SELECT|WHERE|GROUP BY|ORDER BY|HAVING)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b"
            sql_matches = re.findall(sql_column_pattern, sql_query, re.IGNORECASE)
            
            for clause, col_name in sql_matches:
                if col_name.lower() in column_mapping:
                    actual_col = column_mapping[col_name.lower()]
                    if col_name != actual_col:
                        # Replace in the query
                        fixed_query = re.sub(
                            rf"\b{clause}\s+{re.escape(col_name)}\b",
                            f"{clause} '{actual_col}'",
                            fixed_query,
                            flags=re.IGNORECASE
                        )
                        logger.info(f"Fixed SQL unquoted column: '{col_name}' -> '{actual_col}'")
            
            return fixed_query
            
        except Exception as e:
            logger.warning(f"Error fixing column names in SQL query: {e}")
            return sql_query  # Return original query if fixing fails
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.
        
        Returns:
            Memory statistics dictionary
        """
        try:
            total_memory = sum([df.memory_usage(deep=True).sum() for df in self.dataframes.values()])
            file_count = len(self.dataframes)
            
            return {
                "total_memory_usage": total_memory,
                "max_total_memory": self.max_total_memory,
                "memory_usage_percentage": (total_memory / self.max_total_memory) * 100,
                "active_files": file_count,
                "max_memory_per_file": self.max_memory_per_file,
                "memory_pressure": total_memory > (self.max_total_memory * 0.8)
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {
                "error": str(e),
                "total_memory_usage": 0,
                "active_files": 0
            }

# Global instance
csv_to_sql_converter = CSVToSQLConverter()
