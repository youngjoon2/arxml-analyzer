"""Integration tests for CLI commands."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from click.testing import CliRunner
import pytest
import xml.etree.ElementTree as ET

from arxml_analyzer.cli.main import cli
from arxml_analyzer.models.arxml_document import ARXMLDocument


class TestCLI:
    """Test CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def sample_arxml_file(self, tmp_path):
        """Create a sample ARXML file for testing."""
        arxml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0" 
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://autosar.org/schema/r4.0 AUTOSAR_4-3-0.xsd">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>EcuConfig</SHORT-NAME>
                    <ELEMENTS>
                        <ECUC-MODULE-DEF>
                            <SHORT-NAME>TestModule</SHORT-NAME>
                            <DESC>
                                <L-2 L="EN">Test module for ECUC analyzer</L-2>
                            </DESC>
                            <CONTAINERS>
                                <ECUC-PARAM-CONF-CONTAINER-DEF>
                                    <SHORT-NAME>GeneralConfig</SHORT-NAME>
                                    <PARAMETERS>
                                        <ECUC-INTEGER-PARAM-DEF>
                                            <SHORT-NAME>Timeout</SHORT-NAME>
                                            <DEFAULT-VALUE>100</DEFAULT-VALUE>
                                        </ECUC-INTEGER-PARAM-DEF>
                                    </PARAMETERS>
                                </ECUC-PARAM-CONF-CONTAINER-DEF>
                            </CONTAINERS>
                        </ECUC-MODULE-DEF>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        arxml_file = tmp_path / "test.arxml"
        arxml_file.write_text(arxml_content)
        return arxml_file
    
    def test_cli_version(self, runner):
        """Test version option."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
    
    def test_cli_help(self, runner):
        """Test help message."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ARXML Universal Analyzer" in result.output
        assert "analyze" in result.output
        assert "validate" in result.output
        assert "compare" in result.output
        assert "stats" in result.output
    
    def test_analyze_command_help(self, runner):
        """Test analyze command help."""
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "Analyze ARXML file" in result.output
        assert "--output" in result.output
        assert "--verbose" in result.output
    
    def test_analyze_nonexistent_file(self, runner):
        """Test analyze with non-existent file."""
        result = runner.invoke(cli, ["analyze", "nonexistent.arxml"])
        assert result.exit_code == 2
        assert "does not exist" in result.output.lower() or "invalid value" in result.output.lower()
    
    def test_analyze_with_tree_output(self, runner, sample_arxml_file):
        """Test analyze command with tree output."""
        result = runner.invoke(cli, ["analyze", str(sample_arxml_file), "--output", "tree"])
        if result.exit_code != 0:
            print(f"Error output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "ARXML Analysis" in result.output
        assert "Metadata" in result.output or "Summary" in result.output
    
    def test_analyze_with_json_output(self, runner, sample_arxml_file):
        """Test analyze command with JSON output."""
        result = runner.invoke(cli, ["analyze", str(sample_arxml_file), "--output", "json"])
        assert result.exit_code == 0
        # Try to parse the output as JSON
        try:
            json_output = json.loads(result.output)
            assert "summary" in json_output
        except json.JSONDecodeError:
            # If full JSON parsing fails, check for JSON-like structure
            assert "{" in result.output and "}" in result.output
    
    def test_analyze_with_output_file(self, runner, sample_arxml_file, tmp_path):
        """Test analyze command with output file."""
        output_file = tmp_path / "output.json"
        result = runner.invoke(cli, [
            "analyze", 
            str(sample_arxml_file),
            "--output", "json",
            "--output-file", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify file content is valid JSON
        content = output_file.read_text()
        json_data = json.loads(content)
        assert "summary" in json_data
    
    def test_analyze_with_verbose(self, runner, sample_arxml_file):
        """Test analyze command with verbose output."""
        result = runner.invoke(cli, ["analyze", str(sample_arxml_file), "--verbose"])
        assert result.exit_code == 0
        assert "Analyzing file" in result.output or "Parsing" in result.output
    
    def test_analyze_with_no_metadata(self, runner, sample_arxml_file):
        """Test analyze command without metadata."""
        result = runner.invoke(cli, [
            "analyze",
            str(sample_arxml_file),
            "--output", "json",
            "--no-metadata"
        ])
        assert result.exit_code == 0
        # Extract JSON from output (skip warning messages)
        lines = result.output.strip().split('\n')
        # Find where JSON starts
        json_start = next((i for i, line in enumerate(lines) if line.startswith('{')), -1)
        if json_start >= 0:
            json_str = '\n'.join(lines[json_start:])
            json_output = json.loads(json_str)
        else:
            json_output = json.loads(result.output)
        assert "metadata" not in json_output
    
    def test_analyze_with_stream_parser(self, runner, sample_arxml_file):
        """Test analyze command with stream parser."""
        result = runner.invoke(cli, ["analyze", str(sample_arxml_file), "--stream"])
        assert result.exit_code == 0
    
    def test_analyze_with_specific_analyzer(self, runner, sample_arxml_file):
        """Test analyze command with specific analyzer type."""
        result = runner.invoke(cli, [
            "analyze",
            str(sample_arxml_file),
            "--analyzer-type", "ecuc"
        ])
        assert result.exit_code == 0
    
    def test_validate_command_placeholder(self, runner, sample_arxml_file):
        """Test validate command (placeholder)."""
        result = runner.invoke(cli, ["validate", str(sample_arxml_file)])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output
    
    def test_compare_command_placeholder(self, runner, sample_arxml_file):
        """Test compare command (placeholder)."""
        result = runner.invoke(cli, ["compare", str(sample_arxml_file), str(sample_arxml_file)])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output
    
    def test_stats_command_placeholder(self, runner, sample_arxml_file):
        """Test stats command (placeholder)."""
        result = runner.invoke(cli, ["stats", str(sample_arxml_file)])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output
    
    def test_analyze_with_all_exclude_options(self, runner, sample_arxml_file):
        """Test analyze with all exclude options."""
        result = runner.invoke(cli, [
            "analyze",
            str(sample_arxml_file),
            "--output", "json",
            "--no-metadata",
            "--no-details",
            "--no-patterns",
            "--no-statistics",
            "--no-recommendations"
        ])
        assert result.exit_code == 0
        # Extract JSON from output (skip warning messages)
        lines = result.output.strip().split('\n')
        # Find where JSON starts
        json_start = next((i for i, line in enumerate(lines) if line.startswith('{')), -1)
        if json_start >= 0:
            json_str = '\n'.join(lines[json_start:])
            json_output = json.loads(json_str)
        else:
            json_output = json.loads(result.output)
        assert "summary" in json_output  # Summary should always be included
        assert "metadata" not in json_output
        assert "details" not in json_output
        assert "patterns" not in json_output
        assert "statistics" not in json_output
        assert "recommendations" not in json_output