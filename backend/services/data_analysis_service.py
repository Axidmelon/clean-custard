# File: backend/services/data_analysis_service.py

import os
import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Any, Optional, Union
from io import StringIO
import httpx
from datetime import datetime
import re

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from core.config import settings

logger = logging.getLogger(__name__)

class DataAnalysisService:
    """
    Service for comprehensive data analysis of uploaded files.
    
    This service provides:
    - Data schema analysis and caching
    - Natural language to pandas query conversion
    - Advanced data analysis and statistical operations
    - Query execution and result formatting
    - Integration with existing file upload system
    """
    
    def __init__(self):
        """Initialize the data analysis service with LLM and caching."""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens
        )
        self.csv_cache = {}  # Cache for CSV data
        self.schema_cache = {}  # Cache for schema analysis
        
        # Initialize the prompt template for query generation
        self._setup_query_prompt()
        
        logger.info("Data Analysis Service initialized successfully")
    
    def _setup_query_prompt(self):
        """Setup the prompt template for converting natural language to pandas operations."""
        prompt_template = """
You are an expert data analyst who converts natural language questions into pandas DataFrame operations.

Your task is to analyze a CSV schema and convert a user's question into executable pandas code.

SCHEMA INFORMATION:
{schema_info}

USER QUESTION:
{question}

INSTRUCTIONS:
1. Analyze the schema to understand the data structure
2. Convert the question into pandas operations
3. Return ONLY the pandas code that can be executed
4. Use these common operations:
   - df.head() - show first few rows
   - df.describe() - statistical summary
   - df.groupby('column').agg({{'col': 'sum'}}) - grouping and aggregation
   - df[df['column'] > value] - filtering
   - df.sort_values('column', ascending=False) - sorting
   - df['column'].mean() - mean calculation
   - df['column'].sum() - sum calculation
   - df['column'].count() - count
   - df['column'].max() - maximum value
   - df['column'].min() - minimum value
   - df['column'].unique() - unique values
   - df['column'].nunique() - count of unique values

IMPORTANT RULES:
- Always use 'df' as the DataFrame variable name
- Return ONLY the pandas code, no explanations
- Handle missing values with .fillna() if needed
- Use .iloc[:10] to limit results to first 10 rows for large datasets
- For aggregations, use .agg() with proper column names

PANDAS CODE:
"""
        self.query_prompt = ChatPromptTemplate.from_template(prompt_template)
        self.query_chain = self.query_prompt | self.llm
    
    async def analyze_data_schema(self, file_id: str) -> Dict[str, Any]:
        """
        Analyze CSV file and return detailed schema information.
        
        Args:
            file_id: ID of the uploaded CSV file
            
        Returns:
            Dictionary containing schema analysis
        """
        try:
            logger.info(f"Starting schema analysis for file_id: {file_id}")
            
            # Check if schema is already cached
            if file_id in self.schema_cache:
                logger.info(f"Schema found in cache for file_id: {file_id}")
                return self.schema_cache[file_id]
            
            # Get CSV data
            df = await self._get_csv_data(file_id)
            if df is None:
                raise ValueError(f"Could not load CSV data for file_id: {file_id}")
            
            # Analyze schema
            schema_info = self._analyze_dataframe_schema(df)
            
            # Cache the schema
            self.schema_cache[file_id] = schema_info
            
            logger.info(f"Schema analysis completed for file_id: {file_id}")
            return schema_info
            
        except Exception as e:
            logger.error(f"Error analyzing CSV schema for file_id {file_id}: {e}")
            raise
    
    async def process_query(self, question: str, file_id: str) -> Dict[str, Any]:
        """
        Process a natural language question on CSV data.
        
        Args:
            question: Natural language question
            file_id: ID of the CSV file
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            logger.info(f"Processing query: '{question}' for file_id: {file_id}")
            
            # Get CSV data
            df = await self._get_csv_data(file_id)
            if df is None:
                raise ValueError(f"Could not load CSV data for file_id: {file_id}")
            
            # Get schema information
            schema_info = await self.analyze_data_schema(file_id)
            
            # Generate pandas query
            pandas_query = await self._generate_pandas_query(question, schema_info)
            
            # Execute query safely
            result = self._execute_pandas_query(pandas_query, df)
            
            # Format result
            formatted_result = self._format_query_result(result, question)
            
            logger.info(f"Query processed successfully for file_id: {file_id}")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error processing query for file_id {file_id}: {e}")
            raise
    
    async def _get_csv_data(self, file_id: str) -> Optional[pd.DataFrame]:
        """
        Get CSV data from file upload service.
        
        Args:
            file_id: ID of the uploaded file
            
        Returns:
            pandas DataFrame or None if error
        """
        try:
            # Check if data is already cached
            if file_id in self.csv_cache:
                logger.debug(f"CSV data found in cache for file_id: {file_id}")
                return self.csv_cache[file_id]
            
            # Get file content from backend API
            # This would typically call your file upload service
            # For now, we'll implement a placeholder
            content = await self._fetch_file_content(file_id)
            
            if content is None:
                logger.error(f"Could not fetch content for file_id: {file_id}")
                return None
            
            # Validate content is actually CSV, not HTML or other formats
            if not self._is_valid_csv_content(content):
                logger.error(f"File content is not valid CSV format for file_id: {file_id}")
                raise ValueError("File content is not valid CSV format. Please upload a proper CSV file.")
            
            # Parse CSV content
            df = pd.read_csv(StringIO(content))
            
            # Validate DataFrame was created successfully
            if df.empty:
                logger.warning(f"CSV file is empty for file_id: {file_id}")
                raise ValueError("CSV file appears to be empty or contains no valid data.")
            
            # Cache the data
            self.csv_cache[file_id] = df
            
            logger.info(f"CSV data loaded successfully for file_id: {file_id}, shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV data for file_id {file_id}: {e}")
            return None
    
    async def _fetch_file_content(self, file_id: str) -> Optional[str]:
        """
        Fetch file content from Cloudinary using the file URL.
        
        Args:
            file_id: ID of the uploaded file
            
        Returns:
            File content as string or None if error
        """
        try:
            # Import here to avoid circular imports
            from db.database import SessionLocal
            from db.models import UploadedFile
            
            # Get file info from database
            db = SessionLocal()
            try:
                uploaded_file = db.query(UploadedFile).filter(
                    UploadedFile.id == file_id
                ).first()
                
                if not uploaded_file:
                    logger.error(f"File not found in database: {file_id}")
                    return None
                
                # Fetch file content from Cloudinary URL
                async with httpx.AsyncClient() as client:
                    response = await client.get(uploaded_file.file_url)
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully fetched file content for file_id: {file_id}")
                        return response.text
                    else:
                        logger.error(f"Failed to fetch file content from Cloudinary: {response.status_code}")
                        return None
                        
            finally:
                db.close()
                    
        except Exception as e:
            logger.error(f"Error fetching file content for file_id {file_id}: {e}")
            return None
    
    def _analyze_dataframe_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze pandas DataFrame and return schema information.
        
        Args:
            df: pandas DataFrame to analyze
            
        Returns:
            Dictionary containing schema analysis
        """
        try:
            schema_info = {
                "file_info": {
                    "shape": df.shape,
                    "row_count": len(df),
                    "column_count": len(df.columns)
                },
                "columns": [],
                "data_types": {},
                "sample_data": [],
                "statistics": {},
                "data_quality": {}
            }
            
            # Analyze each column
            for col in df.columns:
                col_info = {
                    "name": col,
                    "type": str(df[col].dtype),
                    "sample_values": df[col].dropna().head(5).tolist(),
                    "null_count": df[col].isnull().sum(),
                    "null_percentage": (df[col].isnull().sum() / len(df)) * 100,
                    "unique_count": df[col].nunique()
                }
                
                # Add statistics for numeric columns
                if df[col].dtype in ['int64', 'float64']:
                    col_info["statistics"] = {
                        "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                        "median": float(df[col].median()) if not df[col].isnull().all() else None,
                        "min": float(df[col].min()) if not df[col].isnull().all() else None,
                        "max": float(df[col].max()) if not df[col].isnull().all() else None,
                        "std": float(df[col].std()) if not df[col].isnull().all() else None
                    }
                
                schema_info["columns"].append(col_info)
                schema_info["data_types"][col] = str(df[col].dtype)
            
            # Add sample data
            schema_info["sample_data"] = df.head(3).to_dict('records')
            
            # Add data quality metrics
            schema_info["data_quality"] = {
                "total_nulls": df.isnull().sum().sum(),
                "duplicate_rows": df.duplicated().sum(),
                "memory_usage": df.memory_usage(deep=True).sum()
            }
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error analyzing DataFrame schema: {e}")
            raise
    
    async def _generate_pandas_query(self, question: str, schema_info: Dict[str, Any]) -> str:
        """
        Generate pandas query from natural language question.
        
        Args:
            question: Natural language question
            schema_info: Schema information from CSV analysis
            
        Returns:
            pandas query string
        """
        try:
            # Format schema info for the prompt
            schema_text = self._format_schema_for_prompt(schema_info)
            
            # Generate pandas query using LLM
            response = await self.query_chain.ainvoke({
                "schema_info": schema_text,
                "question": question
            })
            
            pandas_query = response.content.strip()
            
            # Clean up the query (remove markdown formatting if present)
            pandas_query = re.sub(r'```python\n?', '', pandas_query)
            pandas_query = re.sub(r'```\n?', '', pandas_query)
            pandas_query = pandas_query.strip()
            
            logger.info(f"Generated pandas query: {pandas_query}")
            return pandas_query
            
        except Exception as e:
            logger.error(f"Error generating pandas query: {e}")
            raise
    
    def _format_schema_for_prompt(self, schema_info: Dict[str, Any]) -> str:
        """
        Format schema information for the LLM prompt.
        
        Args:
            schema_info: Schema information dictionary
            
        Returns:
            Formatted schema string
        """
        try:
            schema_text = f"Dataset Shape: {schema_info['file_info']['shape']}\n\n"
            schema_text += "Columns:\n"
            
            for col in schema_info["columns"]:
                schema_text += f"- {col['name']} ({col['type']}): "
                schema_text += f"Sample values: {col['sample_values'][:3]}, "
                schema_text += f"Nulls: {col['null_count']}, "
                schema_text += f"Unique: {col['unique_count']}\n"
                
                if "statistics" in col and col["statistics"]:
                    stats = col["statistics"]
                    schema_text += f"  Statistics: mean={stats.get('mean', 'N/A')}, "
                    schema_text += f"min={stats.get('min', 'N/A')}, "
                    schema_text += f"max={stats.get('max', 'N/A')}\n"
            
            return schema_text
            
        except Exception as e:
            logger.error(f"Error formatting schema for prompt: {e}")
            return "Schema information unavailable"
    
    def _execute_pandas_query(self, pandas_query: str, df: pd.DataFrame) -> Any:
        """
        Execute pandas query safely, handling both expressions and statements.
        
        Args:
            pandas_query: pandas code to execute
            df: DataFrame to operate on
            
        Returns:
            Query result
        """
        try:
            # Create a safe execution environment
            safe_globals = {
                'df': df,
                'pd': pd,
                'np': np,
                'len': len,
                'sum': sum,
                'max': max,
                'min': min,
                'abs': abs,
                'round': round
            }
            
            # Check if the query contains assignment (statement) or is just an expression
            if '=' in pandas_query and not pandas_query.strip().startswith('df'):
                # It's a statement with assignment - use exec()
                logger.info("Executing as statement with exec()")
                exec(pandas_query, safe_globals)
                
                # Try to find the result variable (look for common patterns)
                result = None
                for key, value in safe_globals.items():
                    if key not in ['df', 'pd', 'np', 'len', 'sum', 'max', 'min', 'abs', 'round']:
                        if not callable(value) and not key.startswith('_'):
                            result = value
                            break
                
                if result is None:
                    # Fallback: try to get the last assigned variable
                    lines = pandas_query.strip().split('\n')
                    last_line = lines[-1].strip()
                    if '=' in last_line:
                        var_name = last_line.split('=')[0].strip()
                        result = safe_globals.get(var_name)
                
                if result is None:
                    raise ValueError("Could not determine result from statement execution")
                    
            else:
                # It's an expression - use eval()
                logger.info("Executing as expression with eval()")
                result = eval(pandas_query, safe_globals)
            
            logger.info(f"Pandas query executed successfully, result type: {type(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing pandas query: {e}")
            raise
    
    def _format_query_result(self, result: Any, question: str) -> Dict[str, Any]:
        """
        Format query result for API response.
        
        Args:
            result: Query execution result
            question: Original question
            
        Returns:
            Formatted result dictionary
        """
        try:
            formatted_result = {
                "question": question,
                "result_type": type(result).__name__,
                "timestamp": datetime.now().isoformat()
            }
            
            # Handle different result types
            if isinstance(result, pd.DataFrame):
                formatted_result.update({
                    "data": result.head(100).to_dict('records'),  # Limit to 100 rows
                    "columns": list(result.columns),
                    "row_count": len(result),
                    "display_type": "table"
                })
            elif isinstance(result, pd.Series):
                formatted_result.update({
                    "data": result.head(100).to_dict(),
                    "columns": [result.name] if result.name else ["value"],
                    "row_count": len(result),
                    "display_type": "series"
                })
            elif isinstance(result, (int, float, str, bool)):
                formatted_result.update({
                    "data": [[result]],
                    "columns": ["result"],
                    "row_count": 1,
                    "display_type": "single_value"
                })
            else:
                # Convert to string for other types
                formatted_result.update({
                    "data": [[str(result)]],
                    "columns": ["result"],
                    "row_count": 1,
                    "display_type": "other"
                })
            
            # Generate natural language response
            formatted_result["natural_response"] = self._generate_natural_response(result, question)
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error formatting query result: {e}")
            raise
    
    def _generate_natural_response(self, result: Any, question: str) -> str:
        """
        Generate natural language response from query result.
        
        Args:
            result: Query execution result
            question: Original question
            
        Returns:
            Natural language response
        """
        try:
            if isinstance(result, pd.DataFrame):
                if len(result) == 1 and len(result.columns) == 1:
                    value = result.iloc[0, 0]
                    return f"The result is: {value}"
                else:
                    return f"Query returned {len(result)} rows. Here are the results:"
            
            elif isinstance(result, pd.Series):
                if len(result) == 1:
                    return f"The result is: {result.iloc[0]}"
                else:
                    return f"Query returned {len(result)} values."
            
            elif isinstance(result, (int, float)):
                return f"The result is: {result}"
            
            elif isinstance(result, str):
                return f"The result is: {result}"
            
            else:
                return f"Query completed successfully. Result: {str(result)}"
                
        except Exception as e:
            logger.error(f"Error generating natural response: {e}")
            return "Query completed successfully."
    
    def _is_valid_csv_content(self, content: str) -> bool:
        """
        Validate that content is actually CSV format, not HTML or other formats.
        
        Args:
            content: File content to validate
            
        Returns:
            True if content appears to be valid CSV, False otherwise
        """
        try:
            # Check for HTML tags
            if re.search(r'<[^>]+>', content):
                logger.warning("Content contains HTML tags, not valid CSV")
                return False
            
            # Check for common HTML patterns
            html_patterns = [
                r'<!DOCTYPE\s+html',
                r'<html[^>]*>',
                r'<head[^>]*>',
                r'<body[^>]*>',
                r'<meta[^>]*>',
                r'<title[^>]*>',
                r'<script[^>]*>',
                r'<style[^>]*>'
            ]
            
            for pattern in html_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    logger.warning(f"Content matches HTML pattern: {pattern}")
                    return False
            
            # Check for basic CSV structure (at least one comma-separated line)
            lines = content.strip().split('\n')
            if len(lines) < 1:
                logger.warning("Content has no lines")
                return False
            
            # Check if first few lines contain commas (basic CSV indicator)
            csv_lines = 0
            for line in lines[:5]:  # Check first 5 lines
                if ',' in line and not line.strip().startswith('#'):
                    csv_lines += 1
            
            if csv_lines == 0:
                logger.warning("No comma-separated lines found in content")
                return False
            
            logger.debug("Content appears to be valid CSV format")
            return True
            
        except Exception as e:
            logger.error(f"Error validating CSV content: {e}")
            return False

    def clear_cache(self, file_id: Optional[str] = None):
        """
        Clear cache for specific file or all files.
        
        Args:
            file_id: Specific file ID to clear, or None to clear all
        """
        if file_id:
            self.csv_cache.pop(file_id, None)
            self.schema_cache.pop(file_id, None)
            logger.info(f"Cache cleared for file_id: {file_id}")
        else:
            self.csv_cache.clear()
            self.schema_cache.clear()
            logger.info("All cache cleared")

# Global instance
data_analysis_service = DataAnalysisService()
