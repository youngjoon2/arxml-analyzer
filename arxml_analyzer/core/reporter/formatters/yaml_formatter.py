"""YAML formatter for analysis results."""

import yaml
from typing import Any, Dict
from pathlib import Path

from arxml_analyzer.core.analyzer.base_analyzer import AnalysisResult
from arxml_analyzer.core.reporter.formatters.base_formatter import BaseFormatter


class YAMLFormatter(BaseFormatter):
    """Format analysis results as YAML."""
    
    def format(self, result: AnalysisResult) -> str:
        """Format analysis result as YAML.
        
        Args:
            result: Analysis result to format
            
        Returns:
            YAML formatted string
        """
        filtered_result = self._filter_result(result)
        
        # Configure YAML output options
        yaml_options = {
            'default_flow_style': False,
            'indent': self.options.indent,
            'sort_keys': False,
            'allow_unicode': True,
            'width': 120,
        }
        
        return yaml.dump(filtered_result, **yaml_options)
    
    def format_to_file(self, result: AnalysisResult, file_path: Path) -> None:
        """Format analysis result to YAML file.
        
        Args:
            result: Analysis result to format
            file_path: Path to output file
        """
        yaml_content = self.format(result)
        file_path.write_text(yaml_content, encoding='utf-8')
    
    def _serialize_for_yaml(self, obj: Any) -> Any:
        """Serialize objects for YAML output.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serialized object suitable for YAML
        """
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_yaml(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._serialize_for_yaml(value) for key, value in obj.items()}
        else:
            return obj