"""JSON formatter for analysis results."""

import json
from typing import Any, Dict
from pathlib import Path
from datetime import datetime

from arxml_analyzer.core.analyzer.base_analyzer import AnalysisResult
from .base_formatter import BaseFormatter, FormatterOptions


class JSONFormatter(BaseFormatter):
    """Format analysis results as JSON."""
    
    def __init__(self, options: FormatterOptions = None):
        """Initialize JSON formatter.
        
        Args:
            options: Formatter options
        """
        super().__init__(options)
        
    def format(self, result: AnalysisResult) -> str:
        """Format analysis result as JSON.
        
        Args:
            result: Analysis result to format
            
        Returns:
            JSON string representation
        """
        filtered_result = self._filter_result(result)
        
        # Convert datetime objects to strings
        filtered_result = self._serialize_dates(filtered_result)
        
        if self.options.verbose:
            return json.dumps(filtered_result, indent=self.options.indent, ensure_ascii=False)
        else:
            return json.dumps(filtered_result, ensure_ascii=False)
    
    def format_to_file(self, result: AnalysisResult, file_path: Path) -> None:
        """Format analysis result to JSON file.
        
        Args:
            result: Analysis result to format
            file_path: Path to output file
        """
        filtered_result = self._filter_result(result)
        filtered_result = self._serialize_dates(filtered_result)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_result, f, indent=self.options.indent, ensure_ascii=False)
    
    def _serialize_dates(self, obj: Any) -> Any:
        """Recursively serialize datetime objects to ISO format strings and enums to values.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serialized object
        """
        from enum import Enum
        from pathlib import Path
        
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {key: self._serialize_dates(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_dates(item) for item in obj]
        elif isinstance(obj, tuple):
            return [self._serialize_dates(item) for item in obj]
        else:
            return obj