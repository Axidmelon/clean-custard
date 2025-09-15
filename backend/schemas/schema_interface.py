# File: backend/schemas/schema_interface.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ColumnInfo:
    """Standardized column information."""
    name: str
    data_type: str
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    is_categorical: bool
    is_numeric: bool
    is_datetime: bool
    is_text: bool
    suggested_analysis_type: str
    sample_values: List[str]


@dataclass
class FileInfo:
    """Standardized file information."""
    file_id: str
    row_count: int
    column_count: int
    data_quality_score: float
    analysis_timestamp: str


@dataclass
class StandardSchemaFormat:
    """Standardized schema format for all services."""
    file_info: FileInfo
    columns: List[ColumnInfo]
    data_types: Dict[str, str]
    null_counts: Dict[str, int]
    unique_counts: Dict[str, int]
    sample_data: Dict[str, List[str]]
    statistical_summary: Dict[str, Any]
    analysis_timestamp: str
    
    @classmethod
    def from_csv_schema_analyzer(cls, schema_data: Dict[str, Any]) -> 'StandardSchemaFormat':
        """Convert CSV schema analyzer format to standard format."""
        file_info = FileInfo(
            file_id=schema_data.get('file_id', 'unknown'),
            row_count=schema_data.get('total_rows', 0),
            column_count=schema_data.get('total_columns', 0),
            data_quality_score=schema_data.get('data_quality_score', 0.0),
            analysis_timestamp=schema_data.get('analysis_timestamp', datetime.now().isoformat())
        )
        
        columns = []
        for col_data in schema_data.get('columns', []):
            column = ColumnInfo(
                name=col_data.get('name', 'unknown'),
                data_type=col_data.get('data_type', 'unknown'),
                null_count=col_data.get('null_count', 0),
                null_percentage=col_data.get('null_percentage', 0.0),
                unique_count=col_data.get('unique_count', 0),
                unique_percentage=col_data.get('unique_percentage', 0.0),
                is_categorical=col_data.get('is_categorical', False),
                is_numeric=col_data.get('is_numeric', False),
                is_datetime=col_data.get('is_datetime', False),
                is_text=col_data.get('is_text', False),
                suggested_analysis_type=col_data.get('suggested_analysis_type', 'unknown'),
                sample_values=col_data.get('sample_data', [])
            )
            columns.append(column)
        
        return cls(
            file_info=file_info,
            columns=columns,
            data_types=schema_data.get('data_types', {}),
            null_counts=schema_data.get('null_counts', {}),
            unique_counts=schema_data.get('unique_counts', {}),
            sample_data=schema_data.get('sample_data', {}),
            statistical_summary=schema_data.get('statistical_summary', {}),
            analysis_timestamp=schema_data.get('analysis_timestamp', datetime.now().isoformat())
        )
    
    @classmethod
    def from_data_analysis_service(cls, schema_data: Dict[str, Any]) -> 'StandardSchemaFormat':
        """Convert data analysis service format to standard format."""
        file_info_data = schema_data.get('file_info', {})
        file_info = FileInfo(
            file_id=file_info_data.get('file_id', 'unknown'),
            row_count=file_info_data.get('row_count', 0),
            column_count=file_info_data.get('column_count', 0),
            data_quality_score=file_info_data.get('data_quality_score', 0.0),
            analysis_timestamp=file_info_data.get('analysis_timestamp', datetime.now().isoformat())
        )
        
        columns = []
        for col_data in schema_data.get('columns', []):
            column = ColumnInfo(
                name=col_data.get('name', 'unknown'),
                data_type=col_data.get('type', 'unknown'),
                null_count=col_data.get('null_count', 0),
                null_percentage=col_data.get('null_percentage', 0.0),
                unique_count=col_data.get('unique_count', 0),
                unique_percentage=col_data.get('unique_percentage', 0.0),
                is_categorical=col_data.get('is_categorical', False),
                is_numeric=col_data.get('is_numeric', False),
                is_datetime=col_data.get('is_datetime', False),
                is_text=col_data.get('is_text', False),
                suggested_analysis_type=col_data.get('suggested_analysis_type', 'unknown'),
                sample_values=col_data.get('sample_values', [])
            )
            columns.append(column)
        
        return cls(
            file_info=file_info,
            columns=columns,
            data_types=schema_data.get('data_types', {}),
            null_counts=schema_data.get('null_counts', {}),
            unique_counts=schema_data.get('unique_counts', {}),
            sample_data=schema_data.get('sample_data', {}),
            statistical_summary=schema_data.get('statistical_summary', {}),
            analysis_timestamp=schema_data.get('analysis_timestamp', datetime.now().isoformat())
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'file_info': {
                'file_id': self.file_info.file_id,
                'row_count': self.file_info.row_count,
                'column_count': self.file_info.column_count,
                'data_quality_score': self.file_info.data_quality_score,
                'analysis_timestamp': self.file_info.analysis_timestamp
            },
            'columns': [
                {
                    'name': col.name,
                    'data_type': col.data_type,
                    'null_count': col.null_count,
                    'null_percentage': col.null_percentage,
                    'unique_count': col.unique_count,
                    'unique_percentage': col.unique_percentage,
                    'is_categorical': col.is_categorical,
                    'is_numeric': col.is_numeric,
                    'is_datetime': col.is_datetime,
                    'is_text': col.is_text,
                    'suggested_analysis_type': col.suggested_analysis_type,
                    'sample_values': col.sample_values
                }
                for col in self.columns
            ],
            'data_types': self.data_types,
            'null_counts': self.null_counts,
            'unique_counts': self.unique_counts,
            'sample_data': self.sample_data,
            'statistical_summary': self.statistical_summary,
            'analysis_timestamp': self.analysis_timestamp
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the schema."""
        return f"File {self.file_info.file_id}: {self.file_info.row_count} rows, {self.file_info.column_count} columns, Quality: {self.file_info.data_quality_score:.1f}%"


class SchemaConverter:
    """Utility class for converting between different schema formats."""
    
    @staticmethod
    def convert_to_standard(schema_data: Dict[str, Any], source_format: str) -> StandardSchemaFormat:
        """Convert schema data to standard format."""
        if source_format == 'csv_schema_analyzer':
            return StandardSchemaFormat.from_csv_schema_analyzer(schema_data)
        elif source_format == 'data_analysis_service':
            return StandardSchemaFormat.from_data_analysis_service(schema_data)
        else:
            raise ValueError(f"Unknown source format: {source_format}")
    
    @staticmethod
    def convert_to_csv_schema_analyzer(standard_schema: StandardSchemaFormat) -> Dict[str, Any]:
        """Convert standard schema to CSV schema analyzer format."""
        return {
            'file_id': standard_schema.file_info.file_id,
            'total_rows': standard_schema.file_info.row_count,
            'total_columns': standard_schema.file_info.column_count,
            'data_quality_score': standard_schema.file_info.data_quality_score,
            'columns': [
                {
                    'name': col.name,
                    'data_type': col.data_type,
                    'null_count': col.null_count,
                    'null_percentage': col.null_percentage,
                    'unique_count': col.unique_count,
                    'unique_percentage': col.unique_percentage,
                    'is_categorical': col.is_categorical,
                    'is_numeric': col.is_numeric,
                    'is_datetime': col.is_datetime,
                    'is_text': col.is_text,
                    'suggested_analysis_type': col.suggested_analysis_type,
                    'sample_data': col.sample_values
                }
                for col in standard_schema.columns
            ],
            'data_types': standard_schema.data_types,
            'null_counts': standard_schema.null_counts,
            'unique_counts': standard_schema.unique_counts,
            'sample_data': standard_schema.sample_data,
            'statistical_summary': standard_schema.statistical_summary,
            'analysis_timestamp': standard_schema.analysis_timestamp
        }
    
    @staticmethod
    def convert_to_data_analysis_service(standard_schema: StandardSchemaFormat) -> Dict[str, Any]:
        """Convert standard schema to data analysis service format."""
        return {
            'file_info': {
                'file_id': standard_schema.file_info.file_id,
                'row_count': standard_schema.file_info.row_count,
                'column_count': standard_schema.file_info.column_count,
                'data_quality_score': standard_schema.file_info.data_quality_score,
                'analysis_timestamp': standard_schema.file_info.analysis_timestamp
            },
            'columns': [
                {
                    'name': col.name,
                    'type': col.data_type,
                    'null_count': col.null_count,
                    'null_percentage': col.null_percentage,
                    'unique_count': col.unique_count,
                    'unique_percentage': col.unique_percentage,
                    'is_categorical': col.is_categorical,
                    'is_numeric': col.is_numeric,
                    'is_datetime': col.is_datetime,
                    'is_text': col.is_text,
                    'suggested_analysis_type': col.suggested_analysis_type,
                    'sample_values': col.sample_values
                }
                for col in standard_schema.columns
            ],
            'data_types': standard_schema.data_types,
            'null_counts': standard_schema.null_counts,
            'unique_counts': standard_schema.unique_counts,
            'sample_data': standard_schema.sample_data,
            'statistical_summary': standard_schema.statistical_summary,
            'analysis_timestamp': standard_schema.analysis_timestamp
        }
