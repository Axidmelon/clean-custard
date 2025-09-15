# File: backend/services/data_analysis_service.py

import os
import pandas as pd
import numpy as np
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from io import StringIO
import httpx
from datetime import datetime
import re

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from core.config import settings
from core.langsmith_service import langsmith_service
from llm.services import ResultFormatter

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
            max_tokens=settings.openai_max_tokens,
            callbacks=[langsmith_service.get_tracer()] if langsmith_service.is_enabled else None
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

STATISTICAL ANALYSIS (when applicable):
For regression analysis, correlation, or advanced statistics, use statsmodels:
   - import statsmodels.api as sm
   - For linear regression: X = sm.add_constant(df['predictor']); model = sm.OLS(df['target'], X).fit()
   - For correlation: df[['col1', 'col2']].corr()
   - For statistical tests: from scipy import stats; stats.ttest_ind(df['group1'], df['group2'])

CRITICAL RULE FOR STATISTICAL RESULTS:
When performing regression or statistical analysis, ALWAYS create a results dictionary:
   - For regression: results = {{'r_squared': model.rsquared, 'coefficients': model.params.to_dict(), 'p_values': model.pvalues.to_dict(), 'summary': str(model.summary())}}
   - For correlation: results = {{'correlation_matrix': df[['col1', 'col2']].corr().to_dict()}}
   - For other stats: results = {{'statistic': result_stat, 'p_value': p_val, 'interpretation': 'your_interpretation'}}

IMPORTANT RULES:
- Always use 'df' as the DataFrame variable name
- Return ONLY the pandas code, no explanations
- Handle missing values with .fillna() if needed
- Use .iloc[:10] to limit results to first 10 rows for large datasets
- For aggregations, use .agg() with proper column names
- For statistical analysis, ALWAYS create a 'results' variable with structured output

PANDAS CODE:
"""
        self.query_prompt = ChatPromptTemplate.from_template(prompt_template)
        self.query_chain = self.query_prompt | self.llm
    
    async def analyze_data_schema(self, file_id: str, user_id: str = None, request_id: str = None) -> Dict[str, Any]:
        """
        Analyze CSV file and return detailed schema information.
        Now uses working memory to share schema analysis across services.
        
        Args:
            file_id: ID of the uploaded CSV file
            user_id: User ID for Redis cache lookup
            request_id: Request ID for working memory lookup
            
        Returns:
            Dictionary containing schema analysis
        """
        try:
            logger.info(f"Starting schema analysis for file_id: {file_id}")
            
            # Check working memory first (new approach)
            if request_id:
                from core.working_memory import working_memory_service
                cached_schema = working_memory_service.get_schema_analysis(request_id, [file_id])
                if cached_schema:
                    logger.info(f"🧠 Using working memory schema for file_id: {file_id}")
                    file_schemas = cached_schema.get('file_schemas', {})
                    if file_id in file_schemas:
                        # Convert from standardized format to data analysis service format
                        from schemas.schema_interface import SchemaConverter
                        standard_schema = SchemaConverter.convert_to_standard(file_schemas[file_id], 'csv_schema_analyzer')
                        return SchemaConverter.convert_to_data_analysis_service(standard_schema)
            
            # Check if schema is already cached in service
            if file_id in self.schema_cache:
                logger.info(f"Schema found in service cache for file_id: {file_id}")
                return self.schema_cache[file_id]
            
            # Get CSV data
            df = await self._get_csv_data(file_id, user_id)
            if df is None:
                raise ValueError(f"Could not load CSV data for file_id: {file_id}")
            
            # Analyze schema
            schema_info = self._analyze_dataframe_schema(df)
            
            # Cache the schema in service cache
            self.schema_cache[file_id] = schema_info
            
            logger.info(f"Schema analysis completed for file_id: {file_id}")
            return schema_info
            
        except Exception as e:
            logger.error(f"Error analyzing CSV schema for file_id {file_id}: {e}")
            raise
    
    async def process_query(self, question: str, file_id: str, user_id: str = None) -> Dict[str, Any]:
        """
        Process a natural language question on CSV data.
        
        Args:
            question: Natural language question
            file_id: ID of the CSV file
            user_id: User ID for Redis cache lookup
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            logger.info(f"Processing query: '{question}' for file_id: {file_id}")
            
            # Get CSV data with Redis caching
            df = await self._get_csv_data(file_id, user_id)
            if df is None:
                raise ValueError(f"Could not load CSV data for file_id: {file_id}")
            
            # Get schema information with Redis caching
            schema_info = await self.analyze_data_schema(file_id, user_id)
            
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
    
    async def _get_csv_data(self, file_id: str, user_id: str = None) -> Optional[pd.DataFrame]:
        """
        Get CSV data with Redis caching optimization.
        
        Args:
            file_id: ID of the uploaded file
            user_id: User ID for Redis cache lookup
            
        Returns:
            pandas DataFrame or None if error
        """
        try:
            # 1. Check Redis cache first (new optimization)
            if user_id:
                from core.redis_service import redis_service
                cached_content = redis_service.get_cached_csv_data(user_id, file_id)
                if cached_content:
                    logger.info(f"CSV data found in Redis cache for file_id: {file_id}, user: {user_id}")
                    df = pd.read_csv(StringIO(cached_content))
                    # Also cache in service cache for this session
                    self.csv_cache[file_id] = df
                    return df
            
            # 2. Check service's own cache
            if file_id in self.csv_cache:
                logger.debug(f"CSV data found in service cache for file_id: {file_id}")
                return self.csv_cache[file_id]
            
            # 3. Fallback to fetching from Cloudinary
            logger.info(f"Fetching CSV data from Cloudinary for file_id: {file_id}")
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
            
            # Cache the data in both caches
            self.csv_cache[file_id] = df
            
            # Cache in Redis if user_id is available
            if user_id:
                from core.redis_service import redis_service
                redis_service.cache_csv_data(user_id, file_id, content, ttl=7200)  # 2 hours
                logger.info(f"Cached CSV data in Redis for file_id: {file_id}, user: {user_id}")
            
            logger.info(f"CSV data loaded successfully for file_id: {file_id}, shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV data for file_id {file_id}: {e}")
            return None
    
    async def _fetch_file_content(self, file_id: str) -> Optional[str]:
        """
        Fetch file content from Cloudinary using the file URL with enhanced error handling.
        
        Args:
            file_id: ID of the uploaded file
            
        Returns:
            File content as string or None if error
        """
        try:
            # Import here to avoid circular imports
            from db.database import SessionLocal
            from db.models import UploadedFile
            
            logger.info(f"Fetching file content for file_id: {file_id}")
            
            # Get file info from database with enhanced error handling
            db = SessionLocal()
            try:
                # Validate file_id format first
                if not file_id or len(file_id.strip()) == 0:
                    logger.error("Empty or invalid file_id provided")
                    return None
                
                # Query database with better error handling
                try:
                    uploaded_file = db.query(UploadedFile).filter(
                        UploadedFile.id == file_id
                    ).first()
                except Exception as db_error:
                    logger.error(f"Database query error for file_id {file_id}: {db_error}")
                    return None
                
                if not uploaded_file:
                    logger.error(f"File not found in database: {file_id}")
                    return None
                
                logger.info(f"Found file in database: {uploaded_file.original_filename}")
                
                # Validate file URL exists
                if not uploaded_file.file_url:
                    logger.error(f"File URL is empty for file_id: {file_id}")
                    return None
                
                # Fetch file content from Cloudinary URL with timeout and retry
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.get(uploaded_file.file_url)
                            
                            if response.status_code == 200:
                                logger.info(f"Successfully fetched file content for file_id: {file_id}")
                                return response.text
                            else:
                                logger.warning(f"Failed to fetch file content from Cloudinary (attempt {attempt + 1}): {response.status_code}")
                                if attempt == max_retries - 1:  # Last attempt
                                    logger.error(f"All attempts failed to fetch file content for file_id: {file_id}")
                                    return None
                                # Wait before retry
                                await asyncio.sleep(1)
                    except httpx.TimeoutException:
                        logger.warning(f"Timeout fetching file content (attempt {attempt + 1}) for file_id: {file_id}")
                        if attempt == max_retries - 1:
                            logger.error(f"Timeout after all retries for file_id: {file_id}")
                            return None
                        await asyncio.sleep(1)
                    except Exception as fetch_error:
                        logger.warning(f"Error fetching file content (attempt {attempt + 1}) for file_id {file_id}: {fetch_error}")
                        if attempt == max_retries - 1:
                            logger.error(f"Failed to fetch file content after all retries for file_id: {file_id}")
                            return None
                        await asyncio.sleep(1)
                        
            finally:
                try:
                    db.close()
                except Exception as close_error:
                    logger.error(f"Error closing database session: {close_error}")
                    
        except Exception as e:
            logger.error(f"Unexpected error fetching file content for file_id {file_id}: {e}")
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
        with langsmith_service.create_trace("pandas_query_generation") as trace_obj:
            # Add initial metadata
            trace_obj.metadata = {
                "question_type": "pandas_analysis",
                "question_length": len(question),
                "schema_complexity": len(schema_info.get("columns", [])),
                "data_shape": schema_info.get("file_info", {}).get("shape", "unknown"),
                "model": settings.openai_model,
                "temperature": settings.openai_temperature
            }

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
                
                # Add success metadata
                langsmith_service.add_metadata(trace_obj, {
                    "pandas_query_length": len(pandas_query),
                    "success": True,
                    "response_time_ms": "calculated_by_langsmith"
                })
                
                logger.info(f"Generated pandas query: {pandas_query}")
                langsmith_service.log_trace_event("pandas_query_generation", f"Successfully generated pandas query for question: {question[:100]}...")
                
                return pandas_query
                
            except Exception as e:
                # Add error metadata
                langsmith_service.add_metadata(trace_obj, {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                
                logger.error(f"Error generating pandas query: {e}")
                langsmith_service.log_trace_event("pandas_query_error", f"Failed to generate pandas query: {str(e)}")
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
    
    def _fix_column_names_in_query(self, pandas_query: str, df: pd.DataFrame) -> str:
        """
        Fix column name case sensitivity issues in pandas queries.
        
        This method performs case-insensitive column name matching to resolve
        issues where the AI generates queries with incorrect column name casing.
        
        Args:
            pandas_query: The pandas query string
            df: DataFrame with actual column names
            
        Returns:
            Query string with corrected column names
        """
        try:
            # Get actual column names from DataFrame
            actual_columns = df.columns.tolist()
            
            # Create a mapping of lowercase column names to actual column names
            column_mapping = {}
            for col in actual_columns:
                column_mapping[col.lower()] = col
            
            # Find and replace column names in the query
            fixed_query = pandas_query
            
            # Pattern to match column names in quotes (single or double)
            import re
            
            # Find all quoted strings that might be column names
            quoted_pattern = r"['\"]([^'\"]+)['\"]"
            matches = re.findall(quoted_pattern, pandas_query)
            
            for match in matches:
                # Check if this quoted string matches a column name (case-insensitive)
                if match.lower() in column_mapping:
                    actual_col = column_mapping[match.lower()]
                    if match != actual_col:
                        # Replace the incorrect column name with the correct one
                        fixed_query = fixed_query.replace(f"'{match}'", f"'{actual_col}'")
                        fixed_query = fixed_query.replace(f'"{match}"', f'"{actual_col}"')
                        logger.info(f"Fixed column name: '{match}' -> '{actual_col}'")
            
            # Also check for unquoted column names in common pandas operations
            # Pattern for df['column'] or df["column"] or df.column
            df_column_pattern = r"df\[['\"]([^'\"]+)['\"]\]|df\.([a-zA-Z_][a-zA-Z0-9_]*)"
            df_matches = re.findall(df_column_pattern, pandas_query)
            
            for match in df_matches:
                col_name = match[0] if match[0] else match[1]  # Get the column name
                if col_name.lower() in column_mapping:
                    actual_col = column_mapping[col_name.lower()]
                    if col_name != actual_col:
                        # Replace in the query
                        fixed_query = re.sub(
                            rf"df\[['\"]{re.escape(col_name)}['\"]\]",
                            f"df['{actual_col}']",
                            fixed_query
                        )
                        fixed_query = re.sub(
                            rf"df\.{re.escape(col_name)}\b",
                            f"df['{actual_col}']",
                            fixed_query
                        )
                        logger.info(f"Fixed df column reference: '{col_name}' -> '{actual_col}'")
            
            return fixed_query
            
        except Exception as e:
            logger.warning(f"Error fixing column names in query: {e}")
            return pandas_query  # Return original query if fixing fails
    
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
            # Pre-process the query to fix column name case sensitivity issues
            pandas_query = self._fix_column_names_in_query(pandas_query, df)
            
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
                
                # First, check for 'results' variable (preferred for statistical analysis)
                if 'results' in safe_globals:
                    result = safe_globals['results']
                else:
                    # Look for other common result variables
                    for key, value in safe_globals.items():
                        if key not in ['df', 'pd', 'np', 'len', 'sum', 'max', 'min', 'abs', 'round', 'sm', 'stats']:
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
                # Convert Series to list format for API compatibility
                if len(result) == 1:
                    # Single value - convert to list format
                    formatted_result.update({
                        "data": [[result.iloc[0]]],
                        "columns": [result.name] if result.name else ["value"],
                        "row_count": 1,
                        "display_type": "single_value"
                    })
                else:
                    # Multiple values - convert to list of lists
                    formatted_result.update({
                        "data": [[idx, val] for idx, val in result.head(100).items()],
                        "columns": ["index", result.name] if result.name else ["index", "value"],
                        "row_count": len(result),
                        "display_type": "series"
                    })
            elif isinstance(result, dict):
                # Handle statistical results dictionary
                formatted_result.update({
                    "data": self._format_statistical_results(result),
                    "columns": ["Metric", "Value"],
                    "row_count": len(result),
                    "display_type": "statistical_results"
                })
            elif isinstance(result, (int, float, str, bool)):
                formatted_result.update({
                    "data": [[result]],
                    "columns": ["result"],
                    "row_count": 1,
                    "display_type": "single_value"
                })
            else:
                # Check if it's a statsmodels result object
                if hasattr(result, 'rsquared') and hasattr(result, 'params'):
                    # It's a statsmodels regression result
                    formatted_result.update({
                        "data": self._format_statsmodels_result(result),
                        "columns": ["Metric", "Value"],
                        "row_count": len(self._format_statsmodels_result(result)),
                        "display_type": "regression_results"
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
    
    def _format_statistical_results(self, result_dict: dict) -> List[List[str]]:
        """
        Format statistical results dictionary into table format.
        
        Args:
            result_dict: Dictionary containing statistical results
            
        Returns:
            List of rows for display
        """
        try:
            rows = []
            for key, value in result_dict.items():
                if isinstance(value, dict):
                    # Handle nested dictionaries (like coefficients)
                    for sub_key, sub_value in value.items():
                        rows.append([f"{key} ({sub_key})", str(sub_value)])
                elif isinstance(value, (int, float)):
                    # Format numbers nicely
                    if isinstance(value, float):
                        rows.append([key, f"{value:.4f}"])
                    else:
                        rows.append([key, str(value)])
                else:
                    rows.append([key, str(value)])
            return rows
        except Exception as e:
            logger.error(f"Error formatting statistical results: {e}")
            return [["Error", str(e)]]
    
    def _format_statsmodels_result(self, model) -> List[List[str]]:
        """
        Format statsmodels regression result into table format.
        
        Args:
            model: statsmodels regression model result
            
        Returns:
            List of rows for display
        """
        try:
            rows = []
            
            # Add basic regression statistics
            rows.append(["R-squared", f"{model.rsquared:.4f}"])
            rows.append(["Adj. R-squared", f"{model.rsquared_adj:.4f}"])
            rows.append(["F-statistic", f"{model.fvalue:.4f}"])
            rows.append(["Prob (F-statistic)", f"{model.f_pvalue:.4f}"])
            rows.append(["AIC", f"{model.aic:.4f}"])
            rows.append(["BIC", f"{model.bic:.4f}"])
            
            # Add coefficients
            rows.append(["", ""])  # Empty row for separation
            rows.append(["Coefficients", ""])
            
            for param_name, param_value in model.params.items():
                p_value = model.pvalues.get(param_name, 0)
                significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else ""
                rows.append([f"  {param_name}", f"{param_value:.4f} {significance}"])
            
            return rows
        except Exception as e:
            logger.error(f"Error formatting statsmodels result: {e}")
            return [["Error", str(e)]]
    
    def _generate_natural_response(self, result: Any, question: str) -> str:
        """
        Generate natural language response from query result using LLM and ResultFormatter.
        
        Args:
            result: Query execution result
            question: Original question
            
        Returns:
            Natural language response
        """
        try:
            # Handle different result types
            if isinstance(result, pd.DataFrame):
                if len(result) == 1 and len(result.columns) == 1:
                    # Single value result - use ResultFormatter
                    result_value = result.iloc[0, 0]
                    return ResultFormatter.generate_contextual_response(question, result_value)
                else:
                    # Multiple rows - use LLM with formatted summary
                    result_summary = self._prepare_result_summary(result)
                    return self._generate_llm_response(question, result_summary)
            
            elif isinstance(result, pd.Series):
                if len(result) == 1:
                    # Single value result - use ResultFormatter
                    result_value = result.iloc[0]
                    return ResultFormatter.generate_contextual_response(question, result_value)
                else:
                    # Multiple values - use LLM with formatted summary
                    result_summary = self._prepare_result_summary(result)
                    return self._generate_llm_response(question, result_summary)
            
            elif isinstance(result, dict):
                # Statistical results dictionary - generate specialized response
                return self._generate_statistical_response(question, result)
            
            elif hasattr(result, 'rsquared') and hasattr(result, 'params'):
                # statsmodels regression result - generate specialized response
                return self._generate_regression_response(question, result)
            
            elif isinstance(result, (int, float, str)):
                # Single value - use ResultFormatter
                return ResultFormatter.generate_contextual_response(question, result)
            
            else:
                # Complex result - use LLM
                result_summary = self._prepare_result_summary(result)
                return self._generate_llm_response(question, result_summary)
            
        except Exception as e:
            logger.error(f"Error generating natural response: {e}")
            # Fallback to simple response
            return self._generate_fallback_response(result)
    
    def _generate_statistical_response(self, question: str, result_dict: dict) -> str:
        """
        Generate specialized response for statistical results dictionary.
        
        Args:
            question: Original question
            result_dict: Dictionary containing statistical results
            
        Returns:
            Natural language response
        """
        try:
            if 'r_squared' in result_dict:
                # Regression analysis results
                r_squared = result_dict.get('r_squared', 0)
                coefficients = result_dict.get('coefficients', {})
                
                response = f"The regression analysis shows an R-squared value of {r_squared:.4f}, "
                response += f"indicating that {r_squared*100:.1f}% of the variance in the dependent variable is explained by the model. "
                
                if coefficients:
                    main_coeff = None
                    for key, value in coefficients.items():
                        if key != 'const':
                            main_coeff = (key, value)
                            break
                    
                    if main_coeff:
                        var_name, coeff_value = main_coeff
                        response += f"The coefficient for {var_name} is {coeff_value:.4f}, "
                        if coeff_value > 0:
                            response += "indicating a positive relationship. "
                        else:
                            response += "indicating a negative relationship. "
                
                return response + "This suggests a statistically significant relationship between the variables."
            
            elif 'correlation_matrix' in result_dict:
                # Correlation analysis results
                corr_matrix = result_dict['correlation_matrix']
                response = "The correlation analysis shows the relationship between variables: "
                for var1, correlations in corr_matrix.items():
                    for var2, corr_value in correlations.items():
                        if var1 != var2:
                            response += f"{var1} and {var2} have a correlation of {corr_value:.4f}. "
                return response
            
            else:
                # Generic statistical results
                response = "The statistical analysis reveals: "
                for key, value in result_dict.items():
                    if isinstance(value, (int, float)):
                        response += f"{key}: {value:.4f}. "
                    else:
                        response += f"{key}: {value}. "
                return response
                
        except Exception as e:
            logger.error(f"Error generating statistical response: {e}")
            return "Statistical analysis completed successfully."
    
    def _generate_regression_response(self, question: str, model) -> str:
        """
        Generate specialized response for statsmodels regression results.
        
        Args:
            question: Original question
            model: statsmodels regression model result
            
        Returns:
            Natural language response
        """
        try:
            response = f"The regression analysis shows an R-squared value of {model.rsquared:.4f}, "
            response += f"indicating that {model.rsquared*100:.1f}% of the variance is explained by the model. "
            
            # Find the main predictor variable
            main_predictor = None
            main_coeff = None
            for param_name, param_value in model.params.items():
                if param_name != 'const':
                    main_predictor = param_name
                    main_coeff = param_value
                    break
            
            if main_predictor and main_coeff is not None:
                p_value = model.pvalues.get(main_predictor, 1)
                response += f"The coefficient for {main_predictor} is {main_coeff:.4f} "
                
                if p_value < 0.001:
                    response += "(highly significant, p < 0.001). "
                elif p_value < 0.01:
                    response += "(very significant, p < 0.01). "
                elif p_value < 0.05:
                    response += "(significant, p < 0.05). "
                else:
                    response += f"(not significant, p = {p_value:.4f}). "
                
                if main_coeff > 0:
                    response += "This indicates a positive relationship between the variables. "
                else:
                    response += "This indicates a negative relationship between the variables. "
            
            # Add model quality assessment
            if model.rsquared > 0.8:
                response += "The model provides an excellent fit to the data. "
            elif model.rsquared > 0.6:
                response += "The model provides a good fit to the data. "
            elif model.rsquared > 0.3:
                response += "The model provides a moderate fit to the data. "
            else:
                response += "The model provides a weak fit to the data. "
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating regression response: {e}")
            return "Regression analysis completed successfully."
    
    def _generate_llm_response(self, question: str, result_summary: str) -> str:
        """
        Generate LLM response for complex results.
        
        Args:
            question: Original question
            result_summary: Formatted result summary
            
        Returns:
            Natural language response
        """
        with langsmith_service.create_trace("pandas_natural_response") as trace_obj:
            # Add initial metadata
            trace_obj.metadata = {
                "question_type": "pandas_natural_response",
                "question_length": len(question),
                "result_summary_length": len(result_summary),
                "question_category": "data_analysis",
                "model": settings.openai_model
            }

            try:
                response_prompt = f"""
You are an expert data analyst who explains query results in natural, conversational language.

User's Question: {question}
Query Result: {result_summary}

Generate a natural, contextual response that directly answers the user's question using the result.
Make it sound conversational and informative.

Examples:
- "What is the total revenue?" with result 1234567 → "The total revenue is $1,234,567"
- "How many customers do we have?" with result 42 → "We have 42 customers"
- "What's the average order value?" with result 99.99 → "The average order value is $99.99"
- "Show me the top 5 products" with multiple results → "Here are the top 5 products: [list]"
- "Which state has the highest consumers?" with result "California" → "The state with the highest consumers is California"

Response:"""
                
                # Use LLM to generate natural response
                response = self.llm.invoke(response_prompt)
                natural_response = response.content.strip()
                
                # Add success metadata
                langsmith_service.add_metadata(trace_obj, {
                    "response_length": len(natural_response),
                    "success": True,
                    "response_time_ms": "calculated_by_langsmith"
                })
                
                logger.info(f"Generated LLM response: {natural_response}")
                langsmith_service.log_trace_event("pandas_natural_response", f"Successfully generated natural response for question: {question[:100]}...")
                
                return natural_response
                
            except Exception as e:
                # Add error metadata
                langsmith_service.add_metadata(trace_obj, {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                
                logger.error(f"Error generating LLM response: {e}")
                langsmith_service.log_trace_event("pandas_natural_response_error", f"Failed to generate natural response: {str(e)}")
                return f"Query completed successfully. Result: {result_summary}"
    
    def _prepare_result_summary(self, result: Any) -> str:
        """
        Prepare a summary of the result for LLM processing.
        
        Args:
            result: Query execution result
            
        Returns:
            String summary of the result
        """
        try:
            if isinstance(result, pd.DataFrame):
                if len(result) == 1 and len(result.columns) == 1:
                    return str(result.iloc[0, 0])
                elif len(result) <= 5:
                    return f"DataFrame with {len(result)} rows: {result.to_dict('records')}"
                else:
                    return f"DataFrame with {len(result)} rows (showing first 3): {result.head(3).to_dict('records')}"
            
            elif isinstance(result, pd.Series):
                if len(result) == 1:
                    return str(result.iloc[0])
                elif len(result) <= 5:
                    return f"Series with {len(result)} values: {result.to_dict()}"
                else:
                    return f"Series with {len(result)} values (showing first 3): {result.head(3).to_dict()}"
            
            elif isinstance(result, (int, float, str)):
                return str(result)
            
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Error preparing result summary: {e}")
            return str(result)
    
    def _generate_fallback_response(self, result: Any) -> str:
        """
        Generate a fallback response when LLM generation fails.
        
        Args:
            result: Query execution result
            
        Returns:
            Simple fallback response
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
            logger.error(f"Error generating fallback response: {e}")
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

    # --- Multi-File Analysis Methods ---
    
    async def process_intelligent_query(
        self, 
        file_ids: List[str], 
        question: str, 
        user_id: str = None,
        user_preference: str = None,
        force_multi_file: bool = False,
        request_id: str = None
    ) -> Dict[str, Any]:
        """
        Process a natural language question with intelligent file selection and routing.
        
        This method:
        1. Analyzes the question to determine optimal file combination
        2. Selects only necessary files for the analysis
        3. Chooses between single-file and multi-file analysis
        4. Routes to appropriate service (SQL vs pandas)
        
        Args:
            file_ids: List of available file IDs
            question: Natural language question
            user_id: User ID for Redis cache lookup
            user_preference: User preference ('sql' or 'python')
            force_multi_file: Force multi-file analysis even if single file could work
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            logger.info(f"Processing intelligent query: '{question}' for {len(file_ids)} files")
            
            # Step 1: AI analyzes question complexity and determines optimal approach
            analysis_plan = await self._analyze_question_complexity(
                question, file_ids, user_preference, force_multi_file, user_id, request_id
            )
            
            logger.info(f"AI analysis plan: {analysis_plan}")
            
            # Step 2: Load only required files
            required_files = analysis_plan['required_files']
            dataframes = await self._load_required_files(required_files, user_id)
            
            # Step 3: Perform optimal analysis based on AI decision
            if analysis_plan['analysis_type'] == 'sql':
                result = await self._sql_analysis(dataframes, question, analysis_plan)
            else:
                result = await self._pandas_analysis(dataframes, question, analysis_plan)
            
            # Step 4: Add AI routing information to result
            result['files_used'] = required_files
            result['analysis_type'] = analysis_plan['analysis_type']
            result['ai_routing_info'] = {
                'reasoning': analysis_plan['reasoning'],
                'confidence': analysis_plan['confidence'],
                'files_analyzed': len(file_ids),
                'files_used': len(required_files),
                'optimization_applied': len(required_files) < len(file_ids)
            }
            
            logger.info(f"Intelligent query processed successfully using {len(required_files)} files")
            return result
            
        except Exception as e:
            logger.error(f"Error processing intelligent query: {e}")
            raise
    
    async def _analyze_question_complexity(
        self, 
        question: str, 
        available_files: List[str], 
        user_preference: str = None,
        force_multi_file: bool = False,
        user_id: str = None,
        request_id: str = None
    ) -> Dict[str, Any]:
        """
        Use AI to analyze question complexity and determine optimal file combination.
        
        Args:
            question: Natural language question
            available_files: List of available file IDs
            user_preference: User preference ('sql' or 'python')
            force_multi_file: Force multi-file analysis
            
        Returns:
            Analysis plan with required files and approach
        """
        try:
            # Get schema information for all available files using working memory
            schemas_info = {}
            for file_id in available_files:
                schema_info = await self.analyze_data_schema(file_id, user_id, request_id)
                schemas_info[file_id] = schema_info
            
            # Create enhanced prompt for AI analysis
            prompt = f"""
You are an expert data analyst who determines the optimal approach for analyzing CSV data.

QUESTION: {question}

AVAILABLE FILES AND THEIR SCHEMAS:
{self._format_schemas_for_ai(schemas_info)}

USER PREFERENCE: {user_preference or 'none specified'}

ANALYSIS REQUIREMENTS:
1. Determine if this question can be answered with a single file or requires multiple files
2. Identify which specific files are needed (if not all)
3. Decide between SQL analysis (csv_to_sql_converter) or pandas analysis (data_analysis_service)
4. Consider data relationships and JOIN requirements

DECISION CRITERIA:
- Single file sufficient: Questions about one dataset (e.g., "What's the total sales?", "Show me top products")
- Multiple files needed: Questions requiring data from multiple sources (e.g., "Compare sales between regions", "Customer lifetime value by segment")
- SQL approach: Structured queries, aggregations, JOINs, filtering
- Pandas approach: Complex data manipulation, statistical analysis, custom transformations

RESPONSE FORMAT (JSON):
{{
    "required_files": ["file_id1", "file_id2"],
    "analysis_type": "sql" or "pandas",
    "reasoning": "Explanation of decision",
    "confidence": 0.0-1.0,
    "join_strategy": "inner" or "left" or "right" or "full" or "none",
    "optimization_applied": true/false
}}

RESPONSE:"""
            
            # Use LLM to analyze question complexity
            response = await self.llm.ainvoke(prompt)
            
            # Clean and parse JSON response
            response_content = response.content.strip()
            
            # Remove markdown formatting if present
            if response_content.startswith("```json"):
                response_content = response_content[7:]
            elif response_content.startswith("```"):
                response_content = response_content[3:]
            
            if response_content.endswith("```"):
                response_content = response_content[:-3]
            
            # Find JSON object boundaries
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response_content = response_content[start_idx:end_idx + 1]
            
            analysis_plan = json.loads(response_content.strip())
            
            # Validate analysis plan
            if not analysis_plan.get('required_files'):
                analysis_plan['required_files'] = available_files[:1]  # Fallback to first file
            
            if analysis_plan['required_files'] not in available_files:
                # Ensure all required files are actually available
                analysis_plan['required_files'] = [
                    f for f in analysis_plan['required_files'] 
                    if f in available_files
                ]
            
            # Force multi-file if requested
            if force_multi_file and len(analysis_plan['required_files']) == 1:
                analysis_plan['required_files'] = available_files
                analysis_plan['reasoning'] += " (Forced multi-file analysis)"
            
            return analysis_plan
            
        except Exception as e:
            logger.error(f"Error analyzing question complexity: {e}")
            
            # Proper cleanup of any partial state
            try:
                # Clean up any partial analysis state
                if hasattr(self, '_current_analysis'):
                    delattr(self, '_current_analysis')
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")
            
            # Fallback to single file analysis
            return {
                'required_files': available_files[:1],
                'analysis_type': 'pandas',
                'reasoning': f'Fallback due to error: {str(e)}',
                'confidence': 0.5,
                'join_strategy': 'none',
                'optimization_applied': False
            }
    
    async def _load_required_files(self, file_ids: List[str], user_id: str = None) -> Dict[str, pd.DataFrame]:
        """
        Load only the required CSV files.
        
        Args:
            file_ids: List of file IDs to load
            user_id: User ID for Redis cache lookup
            
        Returns:
            Dictionary mapping file_id to DataFrame
        """
        try:
            dataframes = {}
            
            for file_id in file_ids:
                df = await self._get_csv_data(file_id, user_id)
                if df is not None:
                    dataframes[file_id] = df
                else:
                    logger.warning(f"Could not load CSV data for file_id: {file_id}")
            
            if not dataframes:
                raise ValueError("No CSV data could be loaded from the required files")
            
            logger.info(f"Loaded {len(dataframes)} CSV files successfully")
            return dataframes
            
        except Exception as e:
            logger.error(f"Error loading required files: {e}")
            raise
    
    async def _sql_analysis(
        self, 
        dataframes: Dict[str, pd.DataFrame], 
        question: str, 
        analysis_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform SQL-based analysis on multiple DataFrames.
        
        Args:
            dataframes: Dictionary mapping file_id to DataFrame
            question: Natural language question
            analysis_plan: AI analysis plan
            
        Returns:
            Formatted analysis result
        """
        try:
            # Import CSV to SQL converter
            from services.csv_to_sql_converter import csv_to_sql_converter
            
            # Convert DataFrames to SQLite tables
            table_names = {}
            for file_id, df in dataframes.items():
                table_name = await csv_to_sql_converter.convert_dataframe_to_sql(df, file_id)
                table_names[file_id] = table_name
            
            # Generate SQL query for multiple tables
            sql_query = await self._generate_multi_table_sql_query(
                question, table_names, analysis_plan
            )
            
            # Execute SQL query (assuming first table for now - will enhance later)
            first_file_id = list(dataframes.keys())[0]
            result = await csv_to_sql_converter.execute_sql_query(first_file_id, sql_query)
            
            # Format result
            formatted_result = self._format_query_result(result, question)
            
            logger.info(f"SQL analysis completed successfully")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error in SQL analysis: {e}")
            raise
    
    async def _pandas_analysis(
        self, 
        dataframes: Dict[str, pd.DataFrame], 
        question: str, 
        analysis_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform pandas-based analysis on multiple DataFrames.
        
        Args:
            dataframes: Dictionary mapping file_id to DataFrame
            question: Natural language question
            analysis_plan: AI analysis plan
            
        Returns:
            Formatted analysis result
        """
        try:
            if len(dataframes) == 1:
                # Single file analysis
                df = list(dataframes.values())[0]
                schema_info = await self.analyze_data_schema(list(dataframes.keys())[0])
                pandas_query = await self._generate_pandas_query(question, schema_info)
                result = self._execute_pandas_query(pandas_query, df)
            else:
                # Multi-file analysis
                result = await self._execute_multi_file_pandas_analysis(
                    dataframes, question, analysis_plan
                )
            
            # Format result
            formatted_result = self._format_query_result(result, question)
            
            logger.info(f"Pandas analysis completed successfully")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error in pandas analysis: {e}")
            raise
    
    async def _execute_multi_file_pandas_analysis(
        self, 
        dataframes: Dict[str, pd.DataFrame], 
        question: str, 
        analysis_plan: Dict[str, Any]
    ) -> Any:
        """
        Execute pandas analysis on multiple DataFrames.
        
        Args:
            dataframes: Dictionary mapping file_id to DataFrame
            question: Natural language question
            analysis_plan: AI analysis plan
            
        Returns:
            Analysis result
        """
        try:
            # Create combined schema information
            combined_schema = await self._create_combined_schema(dataframes)
            
            # Generate pandas query for multiple DataFrames
            pandas_query = await self._generate_multi_file_pandas_query(
                question, dataframes, combined_schema, analysis_plan
            )
            
            # Execute query safely
            result = self._execute_multi_file_pandas_query(pandas_query, dataframes)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing multi-file pandas analysis: {e}")
            raise
    
    async def analyze_combined_schema(self, schemas_info: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze and combine schemas from multiple files.
        
        Args:
            schemas_info: Dictionary mapping file_id to schema info
            
        Returns:
            Combined schema information
        """
        try:
            combined_schema = {
                "total_files": len(schemas_info),
                "files": {},
                "common_columns": [],
                "unique_columns": {},
                "data_types": {},
                "total_rows": 0,
                "join_candidates": []
            }
            
            all_columns = set()
            column_files = {}
            
            # Analyze each file's schema
            for file_id, schema in schemas_info.items():
                file_info = {
                    "columns": schema["columns"],
                    "row_count": schema["file_info"]["row_count"],
                    "column_count": schema["file_info"]["column_count"]
                }
                combined_schema["files"][file_id] = file_info
                combined_schema["total_rows"] += schema["file_info"]["row_count"]
                
                # Track columns across files
                for col in schema["columns"]:
                    col_name = col["name"]
                    all_columns.add(col_name)
                    
                    if col_name not in column_files:
                        column_files[col_name] = []
                    column_files[col_name].append(file_id)
            
            # Identify common and unique columns
            for col_name, files in column_files.items():
                if len(files) > 1:
                    combined_schema["common_columns"].append(col_name)
                else:
                    file_id = files[0]
                    if file_id not in combined_schema["unique_columns"]:
                        combined_schema["unique_columns"][file_id] = []
                    combined_schema["unique_columns"][file_id].append(col_name)
            
            # Identify potential JOIN candidates
            for col_name in combined_schema["common_columns"]:
                if col_name.lower() in ['id', 'key', 'name', 'date', 'time']:
                    combined_schema["join_candidates"].append(col_name)
            
            logger.info(f"Combined schema analysis completed for {len(schemas_info)} files")
            return combined_schema
            
        except Exception as e:
            logger.error(f"Error analyzing combined schema: {e}")
            raise
    
    def _format_schemas_for_ai(self, schemas_info: Dict[str, Dict[str, Any]]) -> str:
        """
        Format schema information for AI analysis.
        
        Args:
            schemas_info: Dictionary mapping file_id to schema info
            
        Returns:
            Formatted schema string
        """
        try:
            schema_text = ""
            
            for file_id, schema in schemas_info.items():
                schema_text += f"\nFILE: {file_id}\n"
                schema_text += f"Rows: {schema['file_info']['row_count']}, Columns: {schema['file_info']['column_count']}\n"
                schema_text += "Columns:\n"
                
                for col in schema["columns"]:
                    schema_text += f"  - {col['name']} ({col['type']}): "
                    schema_text += f"Sample: {col['sample_values'][:3]}, "
                    schema_text += f"Nulls: {col['null_count']}, "
                    schema_text += f"Unique: {col['unique_count']}\n"
                
                schema_text += "\n"
            
            return schema_text
            
        except Exception as e:
            logger.error(f"Error formatting schemas for AI: {e}")
            return "Schema information unavailable"
    
    async def _create_combined_schema(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Create combined schema information from multiple DataFrames.
        
        Args:
            dataframes: Dictionary mapping file_id to DataFrame
            
        Returns:
            Combined schema information
        """
        try:
            combined_schema = {
                "total_files": len(dataframes),
                "files": {},
                "common_columns": [],
                "unique_columns": {},
                "total_rows": 0
            }
            
            all_columns = set()
            column_files = {}
            
            # Analyze each DataFrame
            for file_id, df in dataframes.items():
                file_info = {
                    "columns": list(df.columns),
                    "row_count": len(df),
                    "column_count": len(df.columns)
                }
                combined_schema["files"][file_id] = file_info
                combined_schema["total_rows"] += len(df)
                
                # Track columns across files
                for col in df.columns:
                    all_columns.add(col)
                    
                    if col not in column_files:
                        column_files[col] = []
                    column_files[col].append(file_id)
            
            # Identify common and unique columns
            for col_name, files in column_files.items():
                if len(files) > 1:
                    combined_schema["common_columns"].append(col_name)
                else:
                    file_id = files[0]
                    if file_id not in combined_schema["unique_columns"]:
                        combined_schema["unique_columns"][file_id] = []
                    combined_schema["unique_columns"][file_id].append(col_name)
            
            return combined_schema
            
        except Exception as e:
            logger.error(f"Error creating combined schema: {e}")
            raise
    
    async def _generate_multi_file_pandas_query(
        self, 
        question: str, 
        dataframes: Dict[str, pd.DataFrame], 
        combined_schema: Dict[str, Any],
        analysis_plan: Dict[str, Any]
    ) -> str:
        """
        Generate pandas query for multiple DataFrames.
        
        Args:
            question: Natural language question
            dataframes: Dictionary mapping file_id to DataFrame
            combined_schema: Combined schema information
            analysis_plan: AI analysis plan
            
        Returns:
            Generated pandas query
        """
        try:
            # Create enhanced prompt for multi-file pandas query generation
            prompt = f"""
You are an expert data analyst who generates pandas code for analyzing multiple CSV files.

QUESTION: {question}

AVAILABLE DATAFRAMES:
{self._format_dataframes_for_ai(dataframes)}

COMBINED SCHEMA:
- Total files: {combined_schema['total_files']}
- Total rows: {combined_schema['total_rows']}
- Common columns: {combined_schema['common_columns']}
- Unique columns per file: {combined_schema['unique_columns']}

ANALYSIS PLAN:
- Join strategy: {analysis_plan.get('join_strategy', 'none')}
- Analysis type: {analysis_plan.get('analysis_type', 'pandas')}

REQUIREMENTS:
1. Generate pandas code that answers the question using the available DataFrames
2. Use appropriate JOIN operations if needed
3. Handle data type conversions and missing values
4. Optimize for performance
5. Return only the pandas code, no explanations

DATAFRAME VARIABLES:
{self._get_dataframe_variables(dataframes)}

RESPONSE (pandas code only):"""
            
            # Use LLM to generate pandas query
            response = await self.llm.ainvoke(prompt)
            pandas_query = response.content.strip()
            
            logger.info(f"Generated multi-file pandas query: {len(pandas_query)} characters")
            return pandas_query
            
        except Exception as e:
            logger.error(f"Error generating multi-file pandas query: {e}")
            raise
    
    def _execute_multi_file_pandas_query(self, pandas_query: str, dataframes: Dict[str, pd.DataFrame]) -> Any:
        """
        Execute pandas query on multiple DataFrames safely.
        
        Args:
            pandas_query: Generated pandas query
            dataframes: Dictionary mapping file_id to DataFrame
            
        Returns:
            Query result
        """
        try:
            # Create safe execution environment
            safe_globals = {
                'pd': pd,
                'np': np,
                'len': len,
                'sum': sum,
                'max': max,
                'min': min,
                'mean': np.mean,
                'std': np.std,
                'var': np.var,
                'count': lambda x: len(x) if hasattr(x, '__len__') else 1,
                'abs': abs,
                'round': round,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'enumerate': enumerate,
                'zip': zip,
                'range': range,
                'sorted': sorted,
                'reversed': reversed,
                'any': any,
                'all': all,
                'isinstance': isinstance,
                'type': type,
                'print': print,
                'datetime': datetime,
                'date': datetime.date,
                'time': datetime.time,
                'timedelta': datetime.timedelta,
            }
            
            # Add DataFrames to safe environment
            for file_id, df in dataframes.items():
                safe_globals[f'df_{file_id}'] = df
                safe_globals[f'df_{file_id.replace("-", "_")}'] = df
            
            # Execute query safely
            exec(pandas_query, safe_globals)
            
            # Get result from safe environment
            result = safe_globals.get('result')
            if result is None:
                # Try to get the last expression result
                result = safe_globals.get('_')
            
            logger.info(f"Multi-file pandas query executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing multi-file pandas query: {e}")
            raise
    
    def _format_dataframes_for_ai(self, dataframes: Dict[str, pd.DataFrame]) -> str:
        """
        Format DataFrame information for AI analysis.
        
        Args:
            dataframes: Dictionary mapping file_id to DataFrame
            
        Returns:
            Formatted DataFrame string
        """
        try:
            df_text = ""
            
            for file_id, df in dataframes.items():
                df_text += f"\nDataFrame: df_{file_id}\n"
                df_text += f"Shape: {df.shape}\n"
                df_text += f"Columns: {list(df.columns)}\n"
                df_text += f"Data types:\n"
                
                for col, dtype in df.dtypes.items():
                    df_text += f"  - {col}: {dtype}\n"
                
                df_text += f"Sample data (first 3 rows):\n"
                df_text += str(df.head(3).to_string())
                df_text += "\n\n"
            
            return df_text
            
        except Exception as e:
            logger.error(f"Error formatting DataFrames for AI: {e}")
            return "DataFrame information unavailable"
    
    def _get_dataframe_variables(self, dataframes: Dict[str, pd.DataFrame]) -> str:
        """
        Get DataFrame variable names for AI.
        
        Args:
            dataframes: Dictionary mapping file_id to DataFrame
            
        Returns:
            DataFrame variables string
        """
        try:
            variables = []
            for file_id in dataframes.keys():
                variables.append(f"df_{file_id}")
                variables.append(f"df_{file_id.replace('-', '_')}")
            
            return f"Available variables: {', '.join(variables)}"
            
        except Exception as e:
            logger.error(f"Error getting DataFrame variables: {e}")
            return "DataFrame variables unavailable"

# Global instance
data_analysis_service = DataAnalysisService()
