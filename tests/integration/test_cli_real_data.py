"""Integration tests for CLI with real ARXML data files."""

import json
from pathlib import Path
from click.testing import CliRunner
import pytest

from arxml_analyzer.cli.main import cli


class TestCLIWithRealData:
    """Test CLI with real ARXML data files."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def data_dir(self):
        """Get the data directory path."""
        return Path(__file__).parent.parent.parent / "data"
    
    def test_analyze_os_ecuc_file(self, runner, data_dir):
        """Test analyzing real OS ECUC configuration file."""
        os_file = data_dir / "official" / "ecuc" / "Os_Ecuc.arxml"
        
        if not os_file.exists():
            pytest.skip(f"Test file {os_file} not found")
        
        result = runner.invoke(cli, ["analyze", str(os_file), "--output", "json"])
        assert result.exit_code == 0
        
        # Parse JSON output
        lines = result.output.strip().split('\n')
        json_start = next((i for i, line in enumerate(lines) if line.startswith('{')), -1)
        if json_start >= 0:
            json_str = '\n'.join(lines[json_start:])
            json_output = json.loads(json_str)
            
            # Verify ECUC specific content
            assert "summary" in json_output
            assert json_output["summary"]["total_modules"] > 0
            # OS module should be detected
            assert any("Os" in str(module) for module in json_output.get("details", {}).get("modules", []))
    
    def test_analyze_canif_ecuc_file(self, runner, data_dir):
        """Test analyzing real CanIf ECUC configuration file."""
        canif_file = data_dir / "official" / "ecuc" / "CanIf_Ecuc.arxml"
        
        if not canif_file.exists():
            pytest.skip(f"Test file {canif_file} not found")
        
        result = runner.invoke(cli, ["analyze", str(canif_file), "--output", "tree"])
        assert result.exit_code == 0
        assert "ARXML Analysis" in result.output
        assert "CanIf" in result.output or "CAN" in result.output
    
    def test_analyze_swc_file(self, runner, data_dir):
        """Test analyzing Software Component file."""
        swc_file = data_dir / "official" / "swc" / "ApplicationSwComponentType.arxml"
        
        if not swc_file.exists():
            pytest.skip(f"Test file {swc_file} not found")
        
        result = runner.invoke(cli, ["analyze", str(swc_file), "--output", "json", "--verbose"])
        assert result.exit_code == 0
        
        # Should detect as SWC or GENERIC type
        assert "EngineController" in result.output or "SWC" in result.output or "GENERIC" in result.output
    
    def test_analyze_interface_file(self, runner, data_dir):
        """Test analyzing Interface definition file."""
        interface_file = data_dir / "official" / "interface" / "PortInterfaces.arxml"
        
        if not interface_file.exists():
            pytest.skip(f"Test file {interface_file} not found")
        
        result = runner.invoke(cli, ["analyze", str(interface_file)])
        assert result.exit_code == 0
    
    def test_analyze_system_file(self, runner, data_dir):
        """Test analyzing System description file."""
        system_file = data_dir / "official" / "system" / "System.arxml"
        
        if not system_file.exists():
            pytest.skip(f"Test file {system_file} not found")
        
        result = runner.invoke(cli, ["analyze", str(system_file), "--output", "json"])
        assert result.exit_code == 0
    
    def test_analyze_minimal_ecuc(self, runner, data_dir):
        """Test analyzing minimal ECUC test fixture."""
        minimal_file = data_dir / "test_fixtures" / "ecuc" / "minimal_ecuc.arxml"
        
        if not minimal_file.exists():
            pytest.skip(f"Test file {minimal_file} not found")
        
        result = runner.invoke(cli, ["analyze", str(minimal_file), "--output", "json", "--no-patterns"])
        assert result.exit_code == 0
        
        # Parse JSON and verify minimal structure
        lines = result.output.strip().split('\n')
        json_start = next((i for i, line in enumerate(lines) if line.startswith('{')), -1)
        if json_start >= 0:
            json_str = '\n'.join(lines[json_start:])
            json_output = json.loads(json_str)
            assert "summary" in json_output
    
    def test_analyze_with_streaming(self, runner, data_dir):
        """Test analyzing with stream parser for larger files."""
        os_file = data_dir / "official" / "ecuc" / "Os_Ecuc.arxml"
        
        if not os_file.exists():
            pytest.skip(f"Test file {os_file} not found")
        
        result = runner.invoke(cli, ["analyze", str(os_file), "--stream", "--verbose"])
        assert result.exit_code == 0
        assert "streaming parser" in result.output.lower() or "stream" in result.output.lower()
    
    def test_analyze_multiple_formats(self, runner, data_dir):
        """Test analyzing same file with different output formats."""
        test_file = data_dir / "test_fixtures" / "ecuc" / "minimal_ecuc.arxml"
        
        if not test_file.exists():
            pytest.skip(f"Test file {test_file} not found")
        
        # Test JSON format
        json_result = runner.invoke(cli, ["analyze", str(test_file), "--output", "json"])
        assert json_result.exit_code == 0
        assert "{" in json_result.output
        
        # Test Tree format
        tree_result = runner.invoke(cli, ["analyze", str(test_file), "--output", "tree"])
        assert tree_result.exit_code == 0
        assert "│" in tree_result.output or "├" in tree_result.output or "└" in tree_result.output or "ARXML" in tree_result.output
    
    def test_analyze_with_output_file(self, runner, data_dir, tmp_path):
        """Test saving analysis results to file."""
        test_file = data_dir / "official" / "ecuc" / "Os_Ecuc.arxml"
        output_file = tmp_path / "analysis_result.json"
        
        if not test_file.exists():
            pytest.skip(f"Test file {test_file} not found")
        
        result = runner.invoke(cli, [
            "analyze", 
            str(test_file), 
            "--output", "json",
            "--output-file", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify file content
        with open(output_file, 'r') as f:
            json_data = json.load(f)
            assert "summary" in json_data
            assert "metadata" in json_data
    
    def test_performance_with_large_file(self, runner, data_dir):
        """Test performance with larger ARXML files."""
        # Use System.arxml as it's the largest generated file
        large_file = data_dir / "official" / "system" / "System.arxml"
        
        if not large_file.exists():
            pytest.skip(f"Test file {large_file} not found")
        
        import time
        start_time = time.time()
        
        result = runner.invoke(cli, ["analyze", str(large_file)])
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result.exit_code == 0
        # Should complete within reasonable time (5 seconds for test file)
        assert duration < 5.0, f"Analysis took too long: {duration:.2f} seconds"
    
    @pytest.mark.parametrize("file_type,expected_content", [
        ("ecuc", ["module", "container", "parameter"]),
        ("swc", ["component", "port", "runnable"]),
        ("interface", ["interface", "sender", "receiver"]),
        ("system", ["system", "ecu", "mapping"])
    ])
    def test_analyze_different_file_types(self, runner, data_dir, file_type, expected_content):
        """Test analyzing different ARXML file types."""
        # Find first file in the directory
        type_dir = data_dir / "official" / file_type
        
        if not type_dir.exists():
            pytest.skip(f"Directory {type_dir} not found")
        
        arxml_files = list(type_dir.glob("*.arxml"))
        if not arxml_files:
            pytest.skip(f"No ARXML files found in {type_dir}")
        
        test_file = arxml_files[0]
        result = runner.invoke(cli, ["analyze", str(test_file), "--output", "json"])
        assert result.exit_code == 0
        
        # Check that output contains expected keywords
        output_lower = result.output.lower()
        assert any(keyword in output_lower for keyword in expected_content), \
            f"Expected one of {expected_content} in output for {file_type} file"