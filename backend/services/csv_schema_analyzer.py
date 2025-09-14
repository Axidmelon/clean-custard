# File: backend/services/csv_schema_analyzer.py

import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from io import StringIO
import re
from core.redis_service import redis_service

logger = logging.getLogger(__name__)

class CSVSchemaAnalyzer:
    """
    Analyzes CSV schema and data characteristics from cached CSV content.
    
    This service provides:
    - Schema analysis (columns, data types, relationships)
    - Data quality assessment
    - Statistical analysis for AI routing decisions
    - Multi-file relationship detection
    """
    
    def __init__(self):
        self.logger = logger
    
    def analyze_csv_schema(self, csv_content: str, file_id: str) -> Dict[str, Any]:
        """
        Analyze CSV schema and return comprehensive metadata.
        
        Args:
            csv_content: Raw CSV content as string
            file_id: File identifier for logging
            
        Returns:
            Dictionary containing schema analysis results
        """
        try:
            # Parse CSV content
            df = pd.read_csv(StringIO(csv_content))
            
            # Basic schema information
            schema_info = {
                "file_id": file_id,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": [],
                "data_types": {},
                "null_counts": {},
                "unique_counts": {},
                "sample_data": {},
                "statistical_summary": {},
                "data_quality_score": 0.0,
                "analysis_timestamp": pd.Timestamp.now().isoformat()
            }
            
            # Analyze each column
            for col in df.columns:
                col_info = self._analyze_column(df[col], col)
                schema_info["columns"].append(col_info)
                schema_info["data_types"][col] = str(df[col].dtype)
                schema_info["null_counts"][col] = int(df[col].isnull().sum())
                schema_info["unique_counts"][col] = int(df[col].nunique())
                
                # Sample data (first 3 non-null values)
                sample_values = df[col].dropna().head(3).tolist()
                schema_info["sample_data"][col] = [str(val) for val in sample_values]
            
            # Statistical summary for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                schema_info["statistical_summary"] = df[numeric_cols].describe().to_dict()
            
            # Calculate data quality score
            schema_info["data_quality_score"] = self._calculate_data_quality_score(df)
            
            self.logger.info(f"Schema analysis completed for {file_id}: {len(df)} rows, {len(df.columns)} columns")
            return schema_info
            
        except Exception as e:
            self.logger.error(f"Failed to analyze CSV schema for {file_id}: {e}")
            return {
                "file_id": file_id,
                "error": str(e),
                "analysis_timestamp": pd.Timestamp.now().isoformat()
            }
    
    def _analyze_column(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """Analyze individual column characteristics."""
        col_info = {
            "name": column_name,
            "data_type": str(series.dtype),
            "null_count": int(series.isnull().sum()),
            "null_percentage": float(series.isnull().sum() / len(series) * 100),
            "unique_count": int(series.nunique()),
            "unique_percentage": float(series.nunique() / len(series) * 100),
            "is_categorical": False,
            "is_numeric": False,
            "is_datetime": False,
            "is_text": False,
            "suggested_analysis_type": "unknown"
        }
        
        # Determine column type and analysis suggestions
        if pd.api.types.is_numeric_dtype(series):
            col_info["is_numeric"] = True
            col_info["suggested_analysis_type"] = "statistical"
        elif pd.api.types.is_datetime64_any_dtype(series):
            col_info["is_datetime"] = True
            col_info["suggested_analysis_type"] = "temporal"
        elif series.nunique() / len(series) < 0.1:  # Less than 10% unique values
            col_info["is_categorical"] = True
            col_info["suggested_analysis_type"] = "categorical"
        else:
            col_info["is_text"] = True
            col_info["suggested_analysis_type"] = "text_analysis"
        
        return col_info
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate overall data quality score (0-100)."""
        try:
            total_cells = len(df) * len(df.columns)
            null_cells = df.isnull().sum().sum()
            
            # Base score from null percentage
            null_score = max(0, 100 - (null_cells / total_cells * 100))
            
            # Bonus for having data
            data_bonus = min(10, len(df) / 100)  # Up to 10 points for having data
            
            # Penalty for too many columns (potential data quality issues)
            column_penalty = max(0, (len(df.columns) - 20) * 0.5)  # Penalty for >20 columns
            
            final_score = null_score + data_bonus - column_penalty
            return min(100, max(0, final_score))
            
        except Exception:
            return 50.0  # Default score if calculation fails
    
    def analyze_multiple_files(self, file_ids: List[str], user_id: str) -> Dict[str, Any]:
        """
        Analyze multiple CSV files and detect relationships.
        
        Args:
            file_ids: List of file IDs to analyze
            user_id: User ID for cache access
            
        Returns:
            Dictionary containing multi-file analysis results
        """
        try:
            file_schemas = {}
            all_columns = set()
            common_columns = None
            
            # Analyze each file
            for file_id in file_ids:
                csv_content = redis_service.get_cached_csv_data(user_id, file_id)
                if csv_content:
                    schema = self.analyze_csv_schema(csv_content, file_id)
                    file_schemas[file_id] = schema
                    
                    # Track columns for relationship analysis
                    file_columns = set(schema.get("columns", []))
                    all_columns.update(file_columns)
                    
                    if common_columns is None:
                        common_columns = file_columns
                    else:
                        common_columns = common_columns.intersection(file_columns)
            
            # Multi-file analysis
            analysis_result = {
                "file_count": len(file_schemas),
                "file_schemas": file_schemas,
                "total_unique_columns": len(all_columns),
                "common_columns": list(common_columns) if common_columns else [],
                "relationship_score": len(common_columns) / len(all_columns) if all_columns else 0,
                "suggested_analysis_type": self._suggest_multi_file_analysis(file_schemas),
                "analysis_timestamp": pd.Timestamp.now().isoformat()
            }
            
            self.logger.info(f"Multi-file analysis completed: {len(file_schemas)} files, {len(common_columns)} common columns")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze multiple files: {e}")
            return {
                "error": str(e),
                "file_count": 0,
                "analysis_timestamp": pd.Timestamp.now().isoformat()
            }
    
    def _suggest_multi_file_analysis(self, file_schemas: Dict[str, Any]) -> str:
        """Suggest the best analysis type for multiple files."""
        try:
            if not file_schemas:
                return "single_file"
            
            # Count analysis types
            analysis_types = {}
            for schema in file_schemas.values():
                for col in schema.get("columns", []):
                    analysis_type = col.get("suggested_analysis_type", "unknown")
                    analysis_types[analysis_type] = analysis_types.get(analysis_type, 0) + 1
            
            # Determine primary analysis type
            if analysis_types.get("statistical", 0) > analysis_types.get("categorical", 0):
                return "statistical_analysis"
            elif analysis_types.get("categorical", 0) > 0:
                return "categorical_analysis"
            else:
                return "data_exploration"
                
        except Exception:
            return "data_exploration"
    
    def get_ai_routing_recommendation(self, file_ids: List[str], user_id: str, question: str) -> Dict[str, Any]:
        """
        Provide AI routing recommendations based on schema analysis.
        
        Args:
            file_ids: List of file IDs
            user_id: User ID for cache access
            question: User's question for context
            
        Returns:
            Dictionary with routing recommendations
        """
        try:
            # Analyze files
            multi_file_analysis = self.analyze_multiple_files(file_ids, user_id)
            
            # Analyze question for intent
            question_intent = self._analyze_question_intent(question)
            
            # Generate recommendations
            recommendations = {
                "recommended_service": "csv_to_sql_converter",  # Default
                "confidence": 0.7,
                "reasoning": "Default recommendation",
                "schema_analysis": multi_file_analysis,
                "question_intent": question_intent,
                "optimization_suggestions": []
            }
            
            # Determine best service based on analysis
            if len(file_ids) == 1:
                # Single file analysis
                file_schema = multi_file_analysis.get("file_schemas", {}).get(file_ids[0], {})
                if file_schema.get("data_quality_score", 0) > 80:
                    recommendations["recommended_service"] = "data_analysis_service"
                    recommendations["confidence"] = 0.9
                    recommendations["reasoning"] = "High-quality single file suitable for advanced analysis"
                else:
                    recommendations["recommended_service"] = "csv_to_sql_converter"
                    recommendations["confidence"] = 0.8
                    recommendations["reasoning"] = "Single file with moderate quality, SQL conversion recommended"
            else:
                # Multi-file analysis
                relationship_score = multi_file_analysis.get("relationship_score", 0)
                if relationship_score > 0.3:
                    recommendations["recommended_service"] = "csv_to_sql_converter"
                    recommendations["confidence"] = 0.9
                    recommendations["reasoning"] = f"Multiple files with {relationship_score:.1%} common columns, ideal for SQL joins"
                else:
                    recommendations["recommended_service"] = "data_analysis_service"
                    recommendations["confidence"] = 0.7
                    recommendations["reasoning"] = "Multiple independent files, individual analysis recommended"
            
            # Adjust based on question intent
            if question_intent.get("requires_joins", False) and len(file_ids) > 1:
                recommendations["recommended_service"] = "csv_to_sql_converter"
                recommendations["confidence"] = min(0.95, recommendations["confidence"] + 0.1)
                recommendations["reasoning"] += " (Question requires cross-file analysis)"
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate AI routing recommendations: {e}")
            return {
                "recommended_service": "csv_to_sql_converter",
                "confidence": 0.5,
                "reasoning": f"Default recommendation due to analysis error: {str(e)}",
                "error": str(e)
            }
    
    def _analyze_question_intent(self, question: str) -> Dict[str, Any]:
        """Analyze user question to understand intent."""
        question_lower = question.lower()
        
        intent = {
            "requires_joins": False,
            "requires_statistics": False,
            "requires_grouping": False,
            "requires_filtering": False,
            "complexity_score": 0.5
        }
        
        # Check for join-related keywords
        join_keywords = ["join", "combine", "merge", "compare", "relationship", "between", "across"]
        if any(keyword in question_lower for keyword in join_keywords):
            intent["requires_joins"] = True
            intent["complexity_score"] += 0.3
        
        # Check for statistical keywords
        stat_keywords = ["average", "mean", "median", "sum", "count", "total", "statistics", "distribution"]
        if any(keyword in question_lower for keyword in stat_keywords):
            intent["requires_statistics"] = True
            intent["complexity_score"] += 0.2
        
        # Check for grouping keywords
        group_keywords = ["group by", "category", "group", "each", "per"]
        if any(keyword in question_lower for keyword in group_keywords):
            intent["requires_grouping"] = True
            intent["complexity_score"] += 0.2
        
        # Check for filtering keywords
        filter_keywords = ["where", "filter", "only", "exclude", "include"]
        if any(keyword in question_lower for keyword in filter_keywords):
            intent["requires_filtering"] = True
            intent["complexity_score"] += 0.1
        
        intent["complexity_score"] = min(1.0, intent["complexity_score"])
        return intent

# Global instance
csv_schema_analyzer = CSVSchemaAnalyzer()
