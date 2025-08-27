"""Tree formatter using Rich library for beautiful console output."""

from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.tree import Tree
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from arxml_analyzer.core.analyzer.base_analyzer import AnalysisResult, AnalysisStatus
from .base_formatter import BaseFormatter, FormatterOptions


class TreeFormatter(BaseFormatter):
    """Format analysis results as a tree structure using Rich."""
    
    def __init__(self, options: FormatterOptions = None):
        """Initialize tree formatter.
        
        Args:
            options: Formatter options
        """
        super().__init__(options)
        self.console = Console(color_system="auto" if options and options.color else None)
        
    def format(self, result: AnalysisResult) -> str:
        """Format analysis result as tree structure.
        
        Args:
            result: Analysis result to format
            
        Returns:
            Tree string representation
        """
        # Create main tree
        tree = self._create_tree(result)
        
        # Capture output to string
        from io import StringIO
        string_io = StringIO()
        temp_console = Console(file=string_io, force_terminal=True, color_system="auto" if self.options.color else None)
        temp_console.print(tree)
        return string_io.getvalue()
    
    def format_to_file(self, result: AnalysisResult, file_path: Path) -> None:
        """Format analysis result to file.
        
        Args:
            result: Analysis result to format
            file_path: Path to output file
        """
        output = self.format(result)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(output)
    
    def _create_tree(self, result: AnalysisResult) -> Tree:
        """Create tree structure from analysis result.
        
        Args:
            result: Analysis result
            
        Returns:
            Rich Tree object
        """
        # Create root tree with file name
        root_label = Text(f"📊 ARXML Analysis: {result.metadata.file_path.name}", style="bold cyan")
        tree = Tree(root_label)
        
        # Add metadata if included
        if self.options.include_metadata:
            metadata_branch = tree.add("📋 [bold]Metadata[/bold]")
            self._add_metadata(metadata_branch, result)
        
        # Add summary
        summary_branch = tree.add("📈 [bold]Summary[/bold]")
        self._add_dict_to_tree(summary_branch, result.summary)
        
        # Add details if included
        if self.options.include_details and result.details:
            details_branch = tree.add("🔍 [bold]Details[/bold]")
            self._add_dict_to_tree(details_branch, result.details)
        
        # Add patterns if included
        if self.options.include_patterns and result.patterns:
            patterns_branch = tree.add("🎯 [bold]Patterns[/bold]")
            self._add_patterns(patterns_branch, result.patterns)
        
        # Add statistics if included
        if self.options.include_statistics and result.statistics:
            stats_branch = tree.add("📊 [bold]Statistics[/bold]")
            self._add_dict_to_tree(stats_branch, result.statistics)
        
        # Add recommendations if included
        if self.options.include_recommendations and result.recommendations:
            rec_branch = tree.add("💡 [bold]Recommendations[/bold]")
            for rec in result.recommendations:
                rec_branch.add(f"• {rec}")
        
        return tree
    
    def _add_metadata(self, branch: Tree, result: AnalysisResult) -> None:
        """Add metadata to tree branch.
        
        Args:
            branch: Tree branch to add to
            result: Analysis result
        """
        metadata = result.metadata
        
        # Status with color
        status_color = "green" if metadata.status == AnalysisStatus.COMPLETED else "red"
        branch.add(f"Status: [{status_color}]{metadata.status.value}[/{status_color}]")
        
        branch.add(f"Analyzer: {metadata.analyzer_name} v{metadata.analyzer_version}")
        branch.add(f"ARXML Type: {metadata.arxml_type}")
        branch.add(f"File Size: {metadata.file_size:,} bytes")
        branch.add(f"Analysis Time: {metadata.analysis_duration:.2f}s")
        branch.add(f"Timestamp: {metadata.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        branch.add(f"Analysis Level: {metadata.analysis_level.value}")
    
    def _add_dict_to_tree(self, branch: Tree, data: Dict[str, Any], level: int = 0) -> None:
        """Recursively add dictionary to tree.
        
        Args:
            branch: Tree branch to add to
            data: Dictionary data
            level: Current nesting level
        """
        for key, value in data.items():
            if isinstance(value, dict):
                sub_branch = branch.add(f"[yellow]{key}[/yellow]")
                self._add_dict_to_tree(sub_branch, value, level + 1)
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    list_branch = branch.add(f"[yellow]{key}[/yellow] ({len(value)} items)")
                    for i, item in enumerate(value[:10]):  # Limit to first 10 items
                        item_branch = list_branch.add(f"[{i}]")
                        self._add_dict_to_tree(item_branch, item, level + 1)
                    if len(value) > 10:
                        list_branch.add(f"... and {len(value) - 10} more items")
                else:
                    branch.add(f"[cyan]{key}[/cyan]: {self._format_value(value)}")
            else:
                branch.add(f"[cyan]{key}[/cyan]: {self._format_value(value)}")
    
    def _add_patterns(self, branch: Tree, patterns: Dict[str, List[Dict]]) -> None:
        """Add patterns to tree branch.
        
        Args:
            branch: Tree branch to add to
            patterns: Pattern data
        """
        for pattern_type, pattern_list in patterns.items():
            if pattern_list:
                type_branch = branch.add(f"[magenta]{pattern_type}[/magenta] ({len(pattern_list)} patterns)")
                for i, pattern in enumerate(pattern_list[:5]):  # Show first 5 patterns
                    pattern_text = self._format_pattern(pattern)
                    type_branch.add(pattern_text)
                if len(pattern_list) > 5:
                    type_branch.add(f"... and {len(pattern_list) - 5} more patterns")
    
    def _format_pattern(self, pattern: Dict) -> str:
        """Format a single pattern for display.
        
        Args:
            pattern: Pattern dictionary
            
        Returns:
            Formatted pattern string
        """
        if "name" in pattern:
            text = f"[bold]{pattern['name']}[/bold]"
            if "count" in pattern:
                text += f" (found {pattern['count']} times)"
            if "severity" in pattern:
                severity_color = self._get_severity_color(pattern["severity"])
                text += f" [{severity_color}]{pattern['severity']}[/{severity_color}]"
            return text
        else:
            return str(pattern)
    
    def _format_value(self, value: Any) -> str:
        """Format a value for display.
        
        Args:
            value: Value to format
            
        Returns:
            Formatted string
        """
        if isinstance(value, bool):
            return "✓" if value else "✗"
        elif isinstance(value, (int, float)):
            if isinstance(value, float):
                return f"{value:.2f}"
            else:
                return f"{value:,}"
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, list):
            return f"[{len(value)} items]"
        else:
            return str(value)
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level.
        
        Args:
            severity: Severity level string
            
        Returns:
            Color name for Rich
        """
        severity_lower = severity.lower()
        if severity_lower in ["critical", "error", "high"]:
            return "red"
        elif severity_lower in ["warning", "medium"]:
            return "yellow"
        elif severity_lower in ["info", "low"]:
            return "blue"
        else:
            return "white"