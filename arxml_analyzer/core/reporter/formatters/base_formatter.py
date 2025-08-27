"""Base formatter for analysis results."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path
from dataclasses import dataclass

from arxml_analyzer.core.analyzer.base_analyzer import AnalysisResult


@dataclass
class FormatterOptions:
    """Options for formatters."""
    
    indent: int = 2
    include_metadata: bool = True
    include_details: bool = True
    include_patterns: bool = True
    include_statistics: bool = True
    include_recommendations: bool = True
    output_file: Optional[Path] = None
    color: bool = True
    verbose: bool = False


class BaseFormatter(ABC):
    """Base class for all output formatters."""
    
    def __init__(self, options: Optional[FormatterOptions] = None):
        """Initialize formatter with options.
        
        Args:
            options: Formatter options
        """
        self.options = options or FormatterOptions()
    
    @abstractmethod
    def format(self, result: AnalysisResult) -> str:
        """Format analysis result.
        
        Args:
            result: Analysis result to format
            
        Returns:
            Formatted string representation
        """
        pass
    
    @abstractmethod
    def format_to_file(self, result: AnalysisResult, file_path: Path) -> None:
        """Format analysis result to file.
        
        Args:
            result: Analysis result to format
            file_path: Path to output file
        """
        pass
    
    def get_format_type(self) -> str:
        """Get formatter type name.
        
        Returns:
            Name of the formatter type
        """
        return self.__class__.__name__.replace("Formatter", "").lower()
    
    def _filter_result(self, result: AnalysisResult) -> Dict[str, Any]:
        """Filter result based on formatter options.
        
        Args:
            result: Analysis result to filter
            
        Returns:
            Filtered result dictionary
        """
        filtered: Dict[str, Any] = {}
        
        if self.options.include_metadata:
            filtered["metadata"] = {
                "analyzer_name": result.metadata.analyzer_name,
                "analyzer_version": result.metadata.analyzer_version,
                "analysis_timestamp": result.metadata.analysis_timestamp.isoformat(),
                "analysis_duration": result.metadata.analysis_duration,
                "file_path": str(result.metadata.file_path),
                "file_size": result.metadata.file_size,
                "arxml_type": result.metadata.arxml_type,
                "analysis_level": result.metadata.analysis_level.value,
                "status": result.metadata.status.value,
            }
        
        filtered["summary"] = result.summary
        
        if self.options.include_details:
            filtered["details"] = result.details
        
        if self.options.include_patterns:
            filtered["patterns"] = result.patterns
        
        if self.options.include_statistics:
            filtered["statistics"] = result.statistics
        
        if self.options.include_recommendations:
            filtered["recommendations"] = result.recommendations
        
        return filtered