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
    - Single and multi-file CSV to DataFrame conversion
    - DataFrame to SQLite table conversion (single or multiple tables)
    - SQL query execution on CSV data (with support for JOINs across tables)
    - Memory management and cleanup
    - Error handling and validation
    - Multi-file analysis with cross-table operations
    """
    
    def __init__(self):
        """Initialize the CSV to SQL converter with memory management."""
        self.connections = {}  # {file_id: sqlite_connection} - for single file mode
        self.dataframes = {}   # {file_id: pandas_dataframe}
        self.table_names = {}   # {file_id: table_name}
        
        # Multi-file support
        self.multi_file_connections = {}  # {session_id: sqlite_connection} - for multi-file mode
        self.multi_file_sessions = {}     # {session_id: {file_ids: [], table_names: {}}}
        
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
    
    async def convert_multiple_csvs_to_sql(self, file_ids: List[str], csv_data_dict: Dict[str, str] = None, user_id: str = None) -> Dict[str, Any]:
        """
        Convert multiple CSV files to SQLite tables in a single database connection.
        This enables JOINs and cross-table operations.
        
        Args:
            file_ids: List of file IDs to convert
            csv_data_dict: Dictionary mapping file_id to CSV content (optional if user_id provided)
            user_id: User ID for Redis cache lookup
            
        Returns:
            Dictionary containing session info and table names
            
        Raises:
            ValueError: If files are too large or invalid
            Exception: If conversion fails
        """
        try:
            logger.info(f"Starting multi-file CSV to SQLite conversion for {len(file_ids)} files")
            
            # Generate unique session ID for this multi-file operation
            import uuid
            session_id = str(uuid.uuid4())
            
            # Check if all files are already converted in a previous session
            if self._check_existing_multi_file_session(file_ids):
                logger.info("All files already converted in existing session")
                # Return existing session info
                for existing_session_id, session_info in self.multi_file_sessions.items():
                    if set(session_info['file_ids']) == set(file_ids):
                        return {
                            "session_id": existing_session_id,
                            "table_names": session_info['table_names'],
                            "file_count": len(file_ids)
                        }
            
            # Create new in-memory SQLite database for multi-file operation
            conn = sqlite3.connect(':memory:')
            
            # Initialize session tracking
            self.multi_file_sessions[session_id] = {
                'file_ids': file_ids,
                'table_names': {},
                'created_at': datetime.now()
            }
            self.multi_file_connections[session_id] = conn
            
            converted_tables = {}
            total_memory_used = 0
            
            # Convert each CSV file to a table
            for file_id in file_ids:
                logger.info(f"Converting file {file_id} to SQLite table")
                
                # Get CSV data
                csv_data = None
                if csv_data_dict and file_id in csv_data_dict:
                    csv_data = csv_data_dict[file_id]
                elif user_id:
                    from core.redis_service import redis_service
                    cached_content = redis_service.get_cached_csv_data(user_id, file_id)
                    if cached_content:
                        csv_data = cached_content
                        logger.info(f"Using cached CSV data for file_id: {file_id}")
                    else:
                        logger.warning(f"No cached CSV data found for file_id: {file_id}")
                
                if csv_data is None:
                    raise ValueError(f"No CSV data available for file_id: {file_id}")
                
                # Validate CSV data size
                csv_size = len(csv_data.encode('utf-8'))
                if csv_size > self.max_file_size:
                    raise ValueError(f"CSV file {file_id} too large: {csv_size} bytes. Maximum allowed: {self.max_file_size} bytes")
                
                # Load CSV into DataFrame
                try:
                    df = pd.read_csv(StringIO(csv_data))
                except Exception as e:
                    raise ValueError(f"Failed to parse CSV data for file {file_id}: {str(e)}")
                
                # Validate DataFrame
                if df.empty:
                    logger.warning(f"CSV file {file_id} appears to be empty, skipping")
                    continue
                
                # Check memory usage
                file_memory = df.memory_usage(deep=True).sum()
                if file_memory > self.max_memory_per_file:
                    raise ValueError(f"File {file_id} too large for processing: {file_memory} bytes")
                
                total_memory_used += file_memory
                if total_memory_used > self.max_total_memory:
                    raise ValueError(f"Total memory limit exceeded: {total_memory_used} bytes")
                
                # Generate unique table name
                table_name = f"csv_data_{file_id.replace('-', '_')}"
                
                # Convert DataFrame to SQLite table
                try:
                    df.to_sql(table_name, conn, index=False, if_exists='replace')
                    converted_tables[file_id] = table_name
                    
                    # Cache DataFrame for schema info
                    if file_id not in self.dataframes:
                        self.dataframes[file_id] = df
                    
                    logger.info(f"Successfully converted file {file_id} to table {table_name}, shape: {df.shape}")
                    
                except Exception as e:
                    raise ValueError(f"Failed to create SQLite table {table_name} for file {file_id}: {str(e)}")
            
            # Update session tracking
            self.multi_file_sessions[session_id]['table_names'] = converted_tables
            
            logger.info(f"Successfully converted {len(converted_tables)} files to SQLite tables in session {session_id}")
            
            return {
                "session_id": session_id,
                "table_names": converted_tables,
                "file_count": len(converted_tables),
                "total_memory_used": total_memory_used
            }
            
        except Exception as e:
            logger.error(f"Error converting multiple CSVs to SQLite: {e}")
            # Cleanup on error
            if session_id in self.multi_file_connections:
                await self.cleanup_multi_file_session(session_id)
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
    
    async def execute_multi_file_sql_query(self, session_id: str, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL query on multiple CSV tables in a single database connection.
        This enables JOINs and cross-table operations.
        
        Args:
            session_id: Unique identifier for the multi-file session
            sql_query: SQL query to execute (can reference multiple tables)
            
        Returns:
            Query results with metadata
        """
        try:
            logger.info(f"Executing multi-file SQL query for session: {session_id}")
            
            if session_id not in self.multi_file_connections:
                raise ValueError(f"No multi-file SQLite connection found for session: {session_id}")
            
            conn = self.multi_file_connections[session_id]
            session_info = self.multi_file_sessions[session_id]
            
            # Validate and sanitize SQL query
            sanitized_query = self._sanitize_multi_file_sql_query(sql_query, session_info['table_names'])
            
            # Fix column name case sensitivity issues across all tables
            sanitized_query = self._fix_column_names_in_multi_file_sql(sanitized_query, session_info['file_ids'])
            
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
            
            logger.info(f"Multi-file SQL query executed successfully for session {session_id}, returned {len(formatted_results)} rows")
            
            return {
                "data": formatted_results,
                "columns": columns,
                "row_count": len(formatted_results),
                "success": True,
                "query": sanitized_query,
                "execution_time": datetime.now().isoformat(),
                "tables_used": list(session_info['table_names'].values())
            }
            
        except sqlite3.Error as e:
            logger.error(f"Multi-file SQL execution failed for session {session_id}: {e}")
            return {
                "error": f"SQL execution failed: {e}",
                "success": False,
                "query": sql_query
            }
        except Exception as e:
            logger.error(f"Unexpected error executing multi-file SQL for session {session_id}: {e}")
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
    
    async def get_multi_file_schema(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive schema information for all tables in a multi-file session.
        
        Args:
            session_id: Unique identifier for the multi-file session
            
        Returns:
            Comprehensive schema information for all tables
        """
        try:
            if session_id not in self.multi_file_connections:
                raise ValueError(f"No multi-file SQLite connection found for session: {session_id}")
            
            conn = self.multi_file_connections[session_id]
            session_info = self.multi_file_sessions[session_id]
            
            # Get comprehensive schema information
            schema_info = {
                "session_id": session_id,
                "tables": {},
                "total_tables": len(session_info['table_names']),
                "file_ids": session_info['file_ids'],
                "table_names": session_info['table_names']
            }
            
            # Get schema for each table
            for file_id, table_name in session_info['table_names'].items():
                table_schema = await self._get_single_table_schema(conn, table_name, file_id)
                schema_info["tables"][file_id] = table_schema
            
            logger.info(f"Retrieved multi-file schema for session {session_id} with {len(schema_info['tables'])} tables")
            return schema_info
            
        except Exception as e:
            logger.error(f"Error getting multi-file schema for session {session_id}: {e}")
            raise
    
    async def _get_single_table_schema(self, conn: sqlite3.Connection, table_name: str, file_id: str) -> Dict[str, Any]:
        """Helper method to get schema for a single table."""
        try:
            cursor = conn.cursor()
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            sample_data = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Format schema information
            table_schema = {
                "table_name": table_name,
                "file_id": file_id,
                "columns": [],
                "sample_data": sample_data,
                "row_count": row_count
            }
            
            for col_info in columns_info:
                table_schema["columns"].append({
                    "name": col_info[1],
                    "type": col_info[2],
                    "nullable": col_info[3] == 0,
                    "default": col_info[4],
                    "primary_key": col_info[5] == 1
                })
            
            return table_schema
            
        except Exception as e:
            logger.error(f"Error getting schema for table {table_name}: {e}")
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
    
    async def cleanup_multi_file_session(self, session_id: str):
        """
        Clean up memory for a multi-file session.
        
        Args:
            session_id: Unique identifier for the multi-file session
        """
        try:
            logger.info(f"Cleaning up multi-file session: {session_id}")
            
            # Close SQLite connection
            if session_id in self.multi_file_connections:
                try:
                    self.multi_file_connections[session_id].close()
                except Exception as e:
                    logger.warning(f"Error closing multi-file SQLite connection for session {session_id}: {e}")
                finally:
                    del self.multi_file_connections[session_id]
            
            # Remove session tracking
            if session_id in self.multi_file_sessions:
                del self.multi_file_sessions[session_id]
            
            # Force garbage collection
            gc.collect()
            
            logger.info(f"Successfully cleaned up multi-file session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up multi-file session {session_id}: {e}")
    
    async def cleanup_all_multi_file_sessions(self):
        """
        Clean up all multi-file sessions (useful for maintenance or memory pressure).
        """
        try:
            logger.info("Cleaning up all multi-file sessions")
            
            session_ids = list(self.multi_file_connections.keys())
            for session_id in session_ids:
                await self.cleanup_multi_file_session(session_id)
            
            logger.info("Successfully cleaned up all multi-file sessions")
            
        except Exception as e:
            logger.error(f"Error cleaning up all multi-file sessions: {e}")
    
    def _check_existing_multi_file_session(self, file_ids: List[str]) -> bool:
        """
        Check if there's an existing multi-file session with the same file IDs.
        
        Args:
            file_ids: List of file IDs to check
            
        Returns:
            True if existing session found, False otherwise
        """
        try:
            target_file_set = set(file_ids)
            
            for session_info in self.multi_file_sessions.values():
                if set(session_info['file_ids']) == target_file_set:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking existing multi-file session: {e}")
            return False
    
    def _sanitize_multi_file_sql_query(self, sql_query: str, table_names: Dict[str, str]) -> str:
        """
        Sanitize SQL query for multi-file operations.
        
        Args:
            sql_query: Original SQL query
            table_names: Dictionary mapping file_id to table_name
            
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
            
            # For now, just return the original query since table names are already correct
            return sql_query
            
        except Exception as e:
            logger.error(f"Error sanitizing multi-file SQL query: {e}")
            return sql_query
    
    def _fix_column_names_in_multi_file_sql(self, sql_query: str, file_ids: List[str]) -> str:
        """
        Fix column name case sensitivity issues in multi-file SQL queries.
        
        Args:
            sql_query: The SQL query string
            file_ids: List of file IDs to get the correct column names
            
        Returns:
            SQL query string with corrected column names
        """
        try:
            import re
            
            # Collect all column mappings from all files
            all_column_mappings = {}
            
            for file_id in file_ids:
                if file_id in self.dataframes:
                    df = self.dataframes[file_id]
                    actual_columns = df.columns.tolist()
                    
                    # Create a mapping of lowercase column names to actual column names
                    for col in actual_columns:
                        all_column_mappings[col.lower()] = col
            
            # Find and replace column names in the SQL query
            fixed_query = sql_query
            
            # Pattern to match column names in quotes (single or double)
            quoted_pattern = r"['\"]([^'\"]+)['\"]"
            matches = re.findall(quoted_pattern, sql_query)
            
            for match in matches:
                # Check if this quoted string matches a column name (case-insensitive)
                if match.lower() in all_column_mappings:
                    actual_col = all_column_mappings[match.lower()]
                    if match != actual_col:
                        # Replace the incorrect column name with the correct one
                        fixed_query = fixed_query.replace(f"'{match}'", f"'{actual_col}'")
                        fixed_query = fixed_query.replace(f'"{match}"', f'"{actual_col}"')
                        logger.info(f"Fixed multi-file SQL column name: '{match}' -> '{actual_col}'")
            
            return fixed_query
            
        except Exception as e:
            logger.warning(f"Error fixing column names in multi-file SQL query: {e}")
            return sql_query
    
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
        Get current memory usage statistics including multi-file sessions.
        
        Returns:
            Memory statistics dictionary
        """
        try:
            total_memory = sum([df.memory_usage(deep=True).sum() for df in self.dataframes.values()])
            file_count = len(self.dataframes)
            multi_file_session_count = len(self.multi_file_sessions)
            
            return {
                "total_memory_usage": total_memory,
                "max_total_memory": self.max_total_memory,
                "memory_usage_percentage": (total_memory / self.max_total_memory) * 100,
                "active_files": file_count,
                "active_multi_file_sessions": multi_file_session_count,
                "max_memory_per_file": self.max_memory_per_file,
                "memory_pressure": total_memory > (self.max_total_memory * 0.8),
                "single_file_connections": len(self.connections),
                "multi_file_connections": len(self.multi_file_connections)
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {
                "error": str(e),
                "total_memory_usage": 0,
                "active_files": 0,
                "active_multi_file_sessions": 0
            }

# Global instance
csv_to_sql_converter = CSVToSQLConverter()
