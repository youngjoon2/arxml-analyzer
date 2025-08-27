"""Unit tests for output formatters."""

import pytest
import json
import yaml
import csv
from io import StringIO
from pathlib import Path
from datetime import datetime
import tempfile

from arxml_analyzer.core.analyzer.base_analyzer import (
    AnalysisResult,
    AnalysisMetadata,
    AnalysisLevel,
    AnalysisStatus
)
from arxml_analyzer.core.reporter.formatters import (
    FormatterOptions,
    JSONFormatter,
    YAMLFormatter,
    TableFormatter,
    CSVFormatter,
    TreeFormatter
)


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return AnalysisMetadata(
        analyzer_name="TestAnalyzer",
        analyzer_version="1.0.0",
        analysis_timestamp=datetime.now(),
        analysis_duration=1.23,
        file_path=Path("/test/file.arxml"),
        file_size=1024,
        arxml_type="TEST",
        analysis_level=AnalysisLevel.DETAILED,
        status=AnalysisStatus.COMPLETED
    )


@pytest.fixture
def sample_result(sample_metadata):
    """Create sample analysis result for testing."""
    return AnalysisResult(
        metadata=sample_metadata,
        summary={
            "total_elements": 100,
            "unique_types": 5,
            "max_depth": 10
        },
        details={
            "elements": ["elem1", "elem2"],
            "types": {"type1": 50, "type2": 30}
        },
        patterns={
            "structural": [
                {"type": "deep_nesting", "depth": 10, "path": "/root/deep"},
                {"type": "high_fanout", "count": 20, "path": "/root/wide"}
            ],
            "reference": [
                {"type": "dangling", "ref": "REF123", "path": "/root/ref"}
            ]
        },
        statistics={
            "element_count": {"total": 100, "by_type": {"A": 60, "B": 40}},
            "depth_metrics": {"max": 10, "avg": 5.5}
        },
        recommendations=[
            "Consider reducing nesting depth",
            "Review dangling references"
        ]
    )


class TestFormatterOptions:
    """Test FormatterOptions dataclass."""
    
    def test_default_options(self):
        """Test default formatter options."""
        options = FormatterOptions()
        assert options.indent == 2
        assert options.include_metadata is True
        assert options.include_details is True
        assert options.include_patterns is True
        assert options.include_statistics is True
        assert options.include_recommendations is True
        assert options.output_file is None
        assert options.color is True
        assert options.verbose is False
    
    def test_custom_options(self):
        """Test custom formatter options."""
        options = FormatterOptions(
            indent=4,
            include_metadata=False,
            color=False,
            verbose=True
        )
        assert options.indent == 4
        assert options.include_metadata is False
        assert options.color is False
        assert options.verbose is True


class TestJSONFormatter:
    """Test JSONFormatter class."""
    
    def test_format_basic(self, sample_result):
        """Test basic JSON formatting."""
        formatter = JSONFormatter()
        output = formatter.format(sample_result)
        
        # Parse JSON to verify structure
        data = json.loads(output)
        assert "metadata" in data
        assert "summary" in data
        assert "details" in data
        assert "patterns" in data
        assert "statistics" in data
        assert "recommendations" in data
    
    def test_format_with_options(self, sample_result):
        """Test JSON formatting with custom options."""
        options = FormatterOptions(
            include_metadata=False,
            include_details=False,
            indent=4
        )
        formatter = JSONFormatter(options)
        output = formatter.format(sample_result)
        
        data = json.loads(output)
        assert "metadata" not in data
        assert "details" not in data
        assert "summary" in data
    
    def test_format_to_file(self, sample_result):
        """Test JSON formatting to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            file_path = Path(f.name)
        
        formatter = JSONFormatter()
        formatter.format_to_file(sample_result, file_path)
        
        # Read and verify file content
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "summary" in data
        
        # Clean up
        file_path.unlink()


class TestYAMLFormatter:
    """Test YAMLFormatter class."""
    
    def test_format_basic(self, sample_result):
        """Test basic YAML formatting."""
        formatter = YAMLFormatter()
        output = formatter.format(sample_result)
        
        # Parse YAML to verify structure
        data = yaml.safe_load(output)
        assert "metadata" in data
        assert "summary" in data
        assert "details" in data
        assert "patterns" in data
        assert "statistics" in data
        assert "recommendations" in data
    
    def test_format_with_options(self, sample_result):
        """Test YAML formatting with custom options."""
        options = FormatterOptions(
            include_patterns=False,
            include_statistics=False,
            indent=4
        )
        formatter = YAMLFormatter(options)
        output = formatter.format(sample_result)
        
        data = yaml.safe_load(output)
        assert "patterns" not in data
        assert "statistics" not in data
        assert "summary" in data
    
    def test_format_to_file(self, sample_result):
        """Test YAML formatting to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            file_path = Path(f.name)
        
        formatter = YAMLFormatter()
        formatter.format_to_file(sample_result, file_path)
        
        # Read and verify file content
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "metadata" in data
        assert "summary" in data
        
        # Clean up
        file_path.unlink()


class TestTableFormatter:
    """Test TableFormatter class."""
    
    def test_format_basic(self, sample_result):
        """Test basic table formatting."""
        formatter = TableFormatter()
        output = formatter.format(sample_result)
        
        # Verify output contains expected sections
        assert "Analysis Metadata" in output
        assert "Analysis Summary" in output
        assert "Statistics" in output
        assert "Patterns" in output
        assert "Recommendations" in output
    
    def test_format_with_options(self, sample_result):
        """Test table formatting with custom options."""
        options = FormatterOptions(
            include_metadata=False,
            include_patterns=False,
            color=False
        )
        formatter = TableFormatter(options)
        output = formatter.format(sample_result)
        
        assert "Analysis Metadata" not in output
        assert "Patterns" not in output
        assert "Analysis Summary" in output
    
    def test_format_empty_patterns(self, sample_metadata):
        """Test table formatting with empty patterns."""
        result = AnalysisResult(
            metadata=sample_metadata,
            summary={"elements": 10},
            details={},
            patterns={},
            statistics={},
            recommendations=[]
        )
        
        formatter = TableFormatter()
        output = formatter.format(result)
        assert "Analysis Summary" in output


class TestCSVFormatter:
    """Test CSVFormatter class."""
    
    def test_format_basic(self, sample_result):
        """Test basic CSV formatting."""
        formatter = CSVFormatter()
        output = formatter.format(sample_result)
        
        # Verify CSV sections
        assert "# Metadata" in output
        assert "# Summary" in output
        assert "# Statistics" in output
        assert "# Patterns" in output
        assert "# Recommendations" in output
        
        # Verify CSV structure
        reader = csv.reader(StringIO(output))
        lines = list(reader)
        assert len(lines) > 0
    
    def test_format_with_options(self, sample_result):
        """Test CSV formatting with custom options."""
        options = FormatterOptions(
            include_metadata=False,
            include_recommendations=False
        )
        formatter = CSVFormatter(options)
        output = formatter.format(sample_result)
        
        assert "# Metadata" not in output
        assert "# Recommendations" not in output
        assert "# Summary" in output
    
    def test_csv_parsing(self, sample_result):
        """Test that CSV output is parseable."""
        formatter = CSVFormatter()
        output = formatter.format(sample_result)
        
        # Split into sections and parse each
        sections = output.split("\n# ")
        for section in sections:
            if section.strip():
                lines = section.strip().split('\n')
                # Skip header line
                csv_lines = [line for line in lines[1:] if line and not line.startswith('#')]
                if csv_lines:
                    reader = csv.reader(csv_lines)
                    rows = list(reader)
                    assert len(rows) > 0  # At least header row


class TestTreeFormatter:
    """Test TreeFormatter class."""
    
    def test_format_basic(self, sample_result):
        """Test basic tree formatting."""
        formatter = TreeFormatter()
        output = formatter.format(sample_result)
        
        # TreeFormatter returns formatted string
        assert isinstance(output, str)
        assert len(output) > 0
    
    def test_format_with_options(self, sample_result):
        """Test tree formatting with custom options."""
        options = FormatterOptions(
            include_metadata=False,
            color=False
        )
        formatter = TreeFormatter(options)
        output = formatter.format(sample_result)
        
        assert isinstance(output, str)
        assert len(output) > 0


class TestFormatterIntegration:
    """Test formatter integration scenarios."""
    
    def test_all_formatters_produce_output(self, sample_result):
        """Test that all formatters produce non-empty output."""
        formatters = [
            JSONFormatter(),
            YAMLFormatter(),
            TableFormatter(),
            CSVFormatter(),
            TreeFormatter()
        ]
        
        for formatter in formatters:
            output = formatter.format(sample_result)
            assert output is not None
            assert len(output) > 0
    
    def test_formatters_respect_options(self, sample_result):
        """Test that all formatters respect common options."""
        options = FormatterOptions(
            include_metadata=False,
            include_details=False,
            include_patterns=False,
            include_statistics=False,
            include_recommendations=False
        )
        
        json_formatter = JSONFormatter(options)
        yaml_formatter = YAMLFormatter(options)
        
        json_output = json_formatter.format(sample_result)
        yaml_output = yaml_formatter.format(sample_result)
        
        json_data = json.loads(json_output)
        yaml_data = yaml.safe_load(yaml_output)
        
        for data in [json_data, yaml_data]:
            assert "metadata" not in data
            assert "details" not in data
            assert "patterns" not in data
            assert "statistics" not in data
            assert "recommendations" not in data
            assert "summary" in data  # Summary should always be included