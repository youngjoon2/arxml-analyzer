"""CSV formatter for analysis results."""

import csv
from typing import Any, Dict, List
from pathlib import Path
from io import StringIO

from arxml_analyzer.core.analyzer.base_analyzer import AnalysisResult
from arxml_analyzer.core.reporter.formatters.base_formatter import BaseFormatter


class CSVFormatter(BaseFormatter):
    """Format analysis results as CSV."""
    
    def format(self, result: AnalysisResult) -> str:
        """Format analysis result as CSV.
        
        Args:
            result: Analysis result to format
            
        Returns:
            CSV formatted string
        """
        output = StringIO()
        
        # Write metadata section
        if self.options.include_metadata:
            self._write_metadata_csv(output, result)
            output.write("\n")
        
        # Write summary section
        self._write_summary_csv(output, result)
        output.write("\n")
        
        # Write statistics section
        if self.options.include_statistics and result.statistics:
            self._write_statistics_csv(output, result)
            output.write("\n")
        
        # Write patterns sections
        if self.options.include_patterns and result.patterns:
            for pattern_type, patterns in result.patterns.items():
                if patterns:
                    self._write_patterns_csv(output, pattern_type, patterns)
                    output.write("\n")
        
        # Write recommendations section
        if self.options.include_recommendations and result.recommendations:
            self._write_recommendations_csv(output, result)
        
        return output.getvalue()
    
    def format_to_file(self, result: AnalysisResult, file_path: Path) -> None:
        """Format analysis result to CSV file.
        
        Args:
            result: Analysis result to format
            file_path: Path to output file
        """
        csv_content = self.format(result)
        file_path.write_text(csv_content, encoding='utf-8')
    
    def _write_metadata_csv(self, output: StringIO, result: AnalysisResult) -> None:
        """Write metadata section to CSV."""
        output.write("# Metadata\n")
        writer = csv.writer(output)
        writer.writerow(["Property", "Value"])
        writer.writerow(["Analyzer", result.metadata.analyzer_name])
        writer.writerow(["Version", result.metadata.analyzer_version])
        writer.writerow(["Timestamp", result.metadata.analysis_timestamp.isoformat()])
        writer.writerow(["Duration", f"{result.metadata.analysis_duration:.2f}"])
        writer.writerow(["File", str(result.metadata.file_path)])
        writer.writerow(["File Size", result.metadata.file_size])
        writer.writerow(["ARXML Type", result.metadata.arxml_type])
        writer.writerow(["Analysis Level", result.metadata.analysis_level.value])
        writer.writerow(["Status", result.metadata.status.value])
    
    def _write_summary_csv(self, output: StringIO, result: AnalysisResult) -> None:
        """Write summary section to CSV."""
        output.write("# Summary\n")
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        for key, value in result.summary.items():
            writer.writerow([key, self._format_value(value)])
    
    def _write_statistics_csv(self, output: StringIO, result: AnalysisResult) -> None:
        """Write statistics section to CSV."""
        output.write("# Statistics\n")
        writer = csv.writer(output)
        writer.writerow(["Category", "Statistic", "Value"])
        
        for key, value in result.statistics.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    writer.writerow([key, sub_key, self._format_value(sub_value)])
            else:
                writer.writerow([key, "-", self._format_value(value)])
    
    def _write_patterns_csv(self, output: StringIO, pattern_type: str, patterns: List[Dict]) -> None:
        """Write patterns section to CSV."""
        output.write(f"# Patterns: {pattern_type}\n")
        
        if not patterns:
            return
        
        # Collect all unique keys from all patterns
        all_keys = set()
        for pattern in patterns:
            all_keys.update(pattern.keys())
        headers = sorted(list(all_keys))
        
        writer = csv.DictWriter(output, fieldnames=headers, restval="")
        writer.writeheader()
        
        # Write pattern data
        for pattern in patterns:
            # Convert complex values to strings
            formatted_pattern = {}
            for key in headers:
                value = pattern.get(key, "")
                formatted_pattern[key] = self._format_value(value)
            writer.writerow(formatted_pattern)
    
    def _write_recommendations_csv(self, output: StringIO, result: AnalysisResult) -> None:
        """Write recommendations section to CSV."""
        output.write("# Recommendations\n")
        writer = csv.writer(output)
        writer.writerow(["Index", "Recommendation"])
        
        for idx, rec in enumerate(result.recommendations, 1):
            writer.writerow([idx, rec])
    
    def _format_value(self, value: Any) -> str:
        """Format value for CSV output."""
        if isinstance(value, bool):
            return "True" if value else "False"
        elif isinstance(value, (list, tuple)):
            return f"[{len(value)} items]"
        elif isinstance(value, dict):
            return f"{{{len(value)} keys}}"
        elif value is None:
            return ""
        else:
            return str(value)