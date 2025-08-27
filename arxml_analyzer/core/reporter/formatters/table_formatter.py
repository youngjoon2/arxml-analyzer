"""Table formatter for analysis results."""

from typing import Any, Dict, List
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.text import Text
from io import StringIO

from arxml_analyzer.core.analyzer.base_analyzer import AnalysisResult
from arxml_analyzer.core.reporter.formatters.base_formatter import BaseFormatter


class TableFormatter(BaseFormatter):
    """Format analysis results as tables."""
    
    def format(self, result: AnalysisResult) -> str:
        """Format analysis result as table.
        
        Args:
            result: Analysis result to format
            
        Returns:
            Table formatted string
        """
        # Create a string buffer to capture console output
        string_buffer = StringIO()
        console = Console(file=string_buffer, force_terminal=True if self.options.color else False)
        
        # Metadata table
        if self.options.include_metadata:
            metadata_table = self._create_metadata_table(result)
            console.print(metadata_table)
            console.print()
        
        # Summary table
        summary_table = self._create_summary_table(result)
        console.print(summary_table)
        console.print()
        
        # Statistics table
        if self.options.include_statistics and result.statistics:
            stats_table = self._create_statistics_table(result)
            console.print(stats_table)
            console.print()
        
        # Patterns table
        if self.options.include_patterns and result.patterns:
            for pattern_type, patterns in result.patterns.items():
                if patterns:
                    pattern_table = self._create_pattern_table(pattern_type, patterns)
                    console.print(pattern_table)
                    console.print()
        
        # Recommendations
        if self.options.include_recommendations and result.recommendations:
            rec_table = self._create_recommendations_table(result)
            console.print(rec_table)
        
        return string_buffer.getvalue()
    
    def format_to_file(self, result: AnalysisResult, file_path: Path) -> None:
        """Format analysis result to file.
        
        Args:
            result: Analysis result to format
            file_path: Path to output file
        """
        table_content = self.format(result)
        file_path.write_text(table_content, encoding='utf-8')
    
    def _create_metadata_table(self, result: AnalysisResult) -> Table:
        """Create metadata table."""
        table = Table(title="Analysis Metadata", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        table.add_row("Analyzer", result.metadata.analyzer_name)
        table.add_row("Version", result.metadata.analyzer_version)
        table.add_row("Timestamp", result.metadata.analysis_timestamp.isoformat())
        table.add_row("Duration", f"{result.metadata.analysis_duration:.2f}s")
        table.add_row("File", str(result.metadata.file_path))
        table.add_row("File Size", f"{result.metadata.file_size:,} bytes")
        table.add_row("ARXML Type", result.metadata.arxml_type)
        table.add_row("Analysis Level", result.metadata.analysis_level.value)
        table.add_row("Status", result.metadata.status.value)
        
        return table
    
    def _create_summary_table(self, result: AnalysisResult) -> Table:
        """Create summary table."""
        table = Table(title="Analysis Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        for key, value in result.summary.items():
            table.add_row(self._format_key(key), self._format_value(value))
        
        return table
    
    def _create_statistics_table(self, result: AnalysisResult) -> Table:
        """Create statistics table."""
        table = Table(title="Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Statistic", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        for key, value in result.statistics.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    table.add_row(f"{self._format_key(key)} - {self._format_key(sub_key)}", 
                                  self._format_value(sub_value))
            else:
                table.add_row(self._format_key(key), self._format_value(value))
        
        return table
    
    def _create_pattern_table(self, pattern_type: str, patterns: List[Dict]) -> Table:
        """Create pattern table."""
        table = Table(title=f"Patterns: {pattern_type}", show_header=True, header_style="bold magenta")
        
        # Determine columns based on pattern structure
        if patterns:
            sample = patterns[0]
            for key in sample.keys():
                table.add_column(self._format_key(key), style="white")
            
            # Add rows
            for pattern in patterns[:10]:  # Limit to first 10 patterns
                row = [self._format_value(pattern.get(key, "")) for key in sample.keys()]
                table.add_row(*row)
            
            if len(patterns) > 10:
                table.add_row(*["..." for _ in sample.keys()])
        
        return table
    
    def _create_recommendations_table(self, result: AnalysisResult) -> Table:
        """Create recommendations table."""
        table = Table(title="Recommendations", show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", no_wrap=True, width=3)
        table.add_column("Recommendation", style="yellow")
        
        for idx, rec in enumerate(result.recommendations, 1):
            table.add_row(str(idx), rec)
        
        return table
    
    def _format_key(self, key: str) -> str:
        """Format key for display."""
        # Convert snake_case to Title Case
        return key.replace('_', ' ').title()
    
    def _format_value(self, value: Any) -> str:
        """Format value for display."""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, (int, float)):
            if isinstance(value, float):
                return f"{value:.2f}"
            else:
                return f"{value:,}"
        elif isinstance(value, list):
            return f"[{len(value)} items]"
        elif isinstance(value, dict):
            return f"{{{len(value)} keys}}"
        elif value is None:
            return "N/A"
        else:
            return str(value)