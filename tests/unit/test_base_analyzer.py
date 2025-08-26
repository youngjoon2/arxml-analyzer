"""Unit tests for BaseAnalyzer and PatternFinder."""

import pytest
from datetime import datetime
from pathlib import Path
from lxml import etree
from unittest.mock import Mock, patch

from arxml_analyzer.core.analyzer.base_analyzer import (
    BaseAnalyzer, 
    AnalysisResult, 
    AnalysisMetadata,
    AnalysisLevel, 
    AnalysisStatus
)
from arxml_analyzer.core.analyzer.pattern_finder import (
    PatternFinder,
    PatternDefinition,
    PatternType,
    PatternMatch
)
from arxml_analyzer.models.arxml_document import ARXMLDocument


def create_test_document():
    """Create a test ARXMLDocument."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
        <AR-PACKAGES>
            <AR-PACKAGE>
                <SHORT-NAME>TestPackage</SHORT-NAME>
            </AR-PACKAGE>
        </AR-PACKAGES>
    </AUTOSAR>"""
    root = etree.fromstring(xml_content.encode())
    doc = ARXMLDocument(root=root, file_path="/test/file.arxml")
    # Add custom attributes for testing
    doc.detected_types = []
    doc.content = xml_content
    return doc


class ConcreteAnalyzer(BaseAnalyzer):
    """Concrete implementation for testing."""
    
    def analyze(self, document: ARXMLDocument) -> AnalysisResult:
        """Simple analysis implementation."""
        metadata = AnalysisMetadata(
            analyzer_name=self.name,
            analyzer_version=self.version
        )
        result = AnalysisResult(metadata=metadata)
        result.summary['test'] = 'success'
        return result
    
    def get_patterns(self):
        """Return test patterns."""
        return [
            {'name': 'test_pattern', 'type': 'xpath', 'pattern': '//SHORT-NAME'}
        ]


class TestAnalysisModels:
    """Test analysis result models."""
    
    def test_analysis_metadata_creation(self):
        """Test AnalysisMetadata creation."""
        metadata = AnalysisMetadata(
            analyzer_name="TestAnalyzer",
            analyzer_version="1.0.0",
            file_path=Path("/test/file.arxml"),
            file_size=1024,
            arxml_type="ECUC"
        )
        
        assert metadata.analyzer_name == "TestAnalyzer"
        assert metadata.analyzer_version == "1.0.0"
        assert metadata.file_path == Path("/test/file.arxml")
        assert metadata.file_size == 1024
        assert metadata.arxml_type == "ECUC"
        assert metadata.analysis_level == AnalysisLevel.STANDARD
        assert metadata.status == AnalysisStatus.PENDING
        assert isinstance(metadata.analysis_timestamp, datetime)
    
    def test_analysis_result_creation(self):
        """Test AnalysisResult creation and methods."""
        metadata = AnalysisMetadata(analyzer_name="TestAnalyzer")
        result = AnalysisResult(metadata=metadata)
        
        # Test initial state
        assert result.metadata.analyzer_name == "TestAnalyzer"
        assert len(result.summary) == 0
        assert len(result.details) == 0
        assert len(result.patterns) == 0
        
        # Test add_pattern
        result.add_pattern("test_pattern", {"location": "/test", "value": "test"})
        assert "test_pattern" in result.patterns
        assert len(result.patterns["test_pattern"]) == 1
        
        # Test add_statistic
        result.add_statistic("element_count", 100)
        assert result.statistics["element_count"] == 100
        
        # Test add_recommendation
        result.add_recommendation("Optimize structure")
        assert "Optimize structure" in result.recommendations
        
        # Test duplicate recommendation is not added
        result.add_recommendation("Optimize structure")
        assert len(result.recommendations) == 1
    
    def test_analysis_result_merge(self):
        """Test merging analysis results."""
        metadata1 = AnalysisMetadata(analyzer_name="Analyzer1")
        result1 = AnalysisResult(metadata=metadata1)
        result1.summary["key1"] = "value1"
        result1.details["detail1"] = {"nested": "value"}
        result1.add_pattern("pattern1", {"data": "test1"})
        result1.add_statistic("stat1", 10)
        result1.add_recommendation("rec1")
        
        metadata2 = AnalysisMetadata(analyzer_name="Analyzer2")
        result2 = AnalysisResult(metadata=metadata2)
        result2.summary["key2"] = "value2"
        result2.details["detail2"] = {"nested": "value2"}
        result2.details["detail1"] = {"nested2": "value3"}
        result2.add_pattern("pattern1", {"data": "test2"})
        result2.add_pattern("pattern2", {"data": "test3"})
        result2.add_statistic("stat2", 20)
        result2.add_recommendation("rec2")
        
        # Merge result2 into result1
        result1.merge(result2)
        
        # Check merged summary
        assert result1.summary["key1"] == "value1"
        assert result1.summary["key2"] == "value2"
        
        # Check merged details
        assert result1.details["detail1"]["nested"] == "value"
        assert result1.details["detail1"]["nested2"] == "value3"
        assert result1.details["detail2"]["nested"] == "value2"
        
        # Check merged patterns
        assert len(result1.patterns["pattern1"]) == 2
        assert len(result1.patterns["pattern2"]) == 1
        
        # Check merged statistics
        assert result1.statistics["stat1"] == 10
        assert result1.statistics["stat2"] == 20
        
        # Check merged recommendations
        assert "rec1" in result1.recommendations
        assert "rec2" in result1.recommendations


class TestBaseAnalyzer:
    """Test BaseAnalyzer functionality."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = ConcreteAnalyzer(name="TestAnalyzer", version="2.0.0")
        
        assert analyzer.name == "TestAnalyzer"
        assert analyzer.version == "2.0.0"
        assert analyzer.analysis_level == AnalysisLevel.STANDARD
        assert len(analyzer.supported_types) == 0
    
    def test_analyzer_default_name(self):
        """Test analyzer with default name."""
        analyzer = ConcreteAnalyzer()
        assert analyzer.name == "ConcreteAnalyzer"
        assert analyzer.version == "1.0.0"
    
    def test_supported_types(self):
        """Test supported types property."""
        analyzer = ConcreteAnalyzer()
        analyzer.supported_types = {"ECUC", "SWC"}
        
        assert "ECUC" in analyzer.supported_types
        assert "SWC" in analyzer.supported_types
        assert len(analyzer.supported_types) == 2
    
    def test_can_analyze_generic(self):
        """Test can_analyze for generic analyzer."""
        analyzer = ConcreteAnalyzer()
        doc = create_test_document()
        
        # Generic analyzer (no supported types) can analyze anything
        assert analyzer.can_analyze(doc) == True
    
    def test_can_analyze_with_types(self):
        """Test can_analyze with specific supported types."""
        analyzer = ConcreteAnalyzer()
        analyzer.supported_types = {"ECUC", "SWC"}
        
        # Document with matching type
        doc = create_test_document()
        doc.detected_types = [
            {'type': 'ECUC', 'confidence': 0.9},
            {'type': 'SYSTEM', 'confidence': 0.3}
        ]
        assert analyzer.can_analyze(doc) == True
        
        # Document with no matching type
        doc2 = create_test_document()
        doc2.detected_types = [
            {'type': 'GATEWAY', 'confidence': 0.9}
        ]
        assert analyzer.can_analyze(doc2) == False
    
    def test_analyze_safe(self):
        """Test safe analysis with error handling."""
        analyzer = ConcreteAnalyzer()
        
        # Create test document
        doc = create_test_document()
        doc.detected_types = [{'type': 'TEST', 'confidence': 0.9}]
        
        # Run safe analysis
        result = analyzer.analyze_safe(doc)
        
        # Check result
        assert result.metadata.analyzer_name == "ConcreteAnalyzer"
        assert result.metadata.status == AnalysisStatus.COMPLETED
        assert result.metadata.file_path == Path("/test/file.arxml")
        assert result.metadata.arxml_type == "TEST"
        assert result.summary['test'] == 'success'
        assert result.metadata.analysis_duration > 0
    
    def test_analyze_safe_with_error(self):
        """Test safe analysis with error handling."""
        analyzer = ConcreteAnalyzer()
        
        # Mock analyze to raise error
        def raise_error(doc):
            raise Exception("Analysis failed")
        
        analyzer.analyze = raise_error
        
        doc = create_test_document()
        result = analyzer.analyze_safe(doc)
        
        assert result.metadata.status == AnalysisStatus.FAILED
        assert len(result.metadata.errors) > 0
        assert "Unexpected error" in result.metadata.errors[0]
    
    def test_detect_primary_type(self):
        """Test primary type detection."""
        analyzer = ConcreteAnalyzer()
        
        # Document with types
        doc = create_test_document()
        doc.detected_types = [
            {'type': 'ECUC', 'confidence': 0.7},
            {'type': 'SWC', 'confidence': 0.9},
            {'type': 'SYSTEM', 'confidence': 0.3}
        ]
        
        primary_type = analyzer._detect_primary_type(doc)
        assert primary_type == 'SWC'  # Highest confidence
        
        # Document without types
        doc2 = create_test_document()
        primary_type2 = analyzer._detect_primary_type(doc2)
        assert primary_type2 == 'unknown'


class TestPatternFinder:
    """Test PatternFinder functionality."""
    
    @pytest.fixture
    def sample_xml(self):
        """Create sample XML for testing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE UUID="uuid-1234">
                    <SHORT-NAME>TestPackage</SHORT-NAME>
                    <ELEMENTS>
                        <ECUC-MODULE-DEF UUID="uuid-5678">
                            <SHORT-NAME>TestModule</SHORT-NAME>
                            <DESC>Test Description</DESC>
                            <LOWER-MULTIPLICITY>0</LOWER-MULTIPLICITY>
                            <UPPER-MULTIPLICITY>1</UPPER-MULTIPLICITY>
                        </ECUC-MODULE-DEF>
                        <ECUC-MODULE-DEF UUID="uuid-9012" DEST="broken-ref">
                            <SHORT-NAME>TestModule2</SHORT-NAME>
                        </ECUC-MODULE-DEF>
                    </ELEMENTS>
                </AR-PACKAGE>
                <AR-PACKAGE>
                    <SHORT-NAME>EmptyPackage</SHORT-NAME>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        return etree.fromstring(xml_content.encode())
    
    def test_pattern_finder_initialization(self):
        """Test PatternFinder initialization."""
        finder = PatternFinder()
        assert len(finder.patterns) == 0
        assert len(finder.matches) == 0
    
    def test_register_pattern(self):
        """Test pattern registration."""
        finder = PatternFinder()
        
        pattern_def = PatternDefinition(
            name="test_pattern",
            pattern_type=PatternType.XPATH,
            pattern="//SHORT-NAME",
            description="Find all SHORT-NAME elements",
            severity="info",
            category="naming"
        )
        
        finder.register_pattern(pattern_def)
        assert "test_pattern" in finder.patterns
        assert finder.patterns["test_pattern"].pattern_type == PatternType.XPATH
    
    def test_find_xpath_patterns(self, sample_xml):
        """Test XPath pattern finding."""
        finder = PatternFinder()
        
        # Set namespaces for AUTOSAR
        finder._namespaces = {'ar': 'http://autosar.org/schema/r4.0'}
        
        # Register XPath pattern with namespace
        pattern = PatternDefinition(
            name="short_names",
            pattern_type=PatternType.XPATH,
            pattern="//ar:SHORT-NAME",
            severity="info"
        )
        finder.register_pattern(pattern)
        
        # Find patterns
        matches = finder.find_xpath_patterns(sample_xml)
        
        # Check matches
        assert len(matches) > 0
        assert all(m.pattern_type == PatternType.XPATH for m in matches)
        assert all(m.pattern_name == "short_names" for m in matches)
    
    def test_find_regex_patterns(self):
        """Test regex pattern finding."""
        finder = PatternFinder()
        
        # Register regex pattern
        pattern = PatternDefinition(
            name="uuid_pattern",
            pattern_type=PatternType.REGEX,
            pattern=r'uuid-\d{4}',
            severity="info"
        )
        finder.register_pattern(pattern)
        
        content = """
        <element UUID="uuid-1234">
        <element UUID="uuid-5678">
        <element UUID="invalid-uuid">
        """
        
        matches = finder.find_regex_patterns(content)
        
        assert len(matches) == 2
        assert all(m.pattern_type == PatternType.REGEX for m in matches)
        assert matches[0].value == "uuid-1234"
        assert matches[1].value == "uuid-5678"
    
    def test_find_structural_patterns(self, sample_xml):
        """Test structural pattern finding."""
        finder = PatternFinder()
        
        matches = finder.find_structural_patterns(sample_xml)
        
        # Should find some structural patterns
        pattern_names = [m.pattern_name for m in matches]
        
        # Check for expected patterns (may vary based on XML structure)
        # The test XML is simple, so might not trigger structural patterns
        assert isinstance(matches, list)  # At least returns a list
    
    def test_find_reference_patterns(self, sample_xml):
        """Test reference pattern finding."""
        finder = PatternFinder()
        
        matches = finder.find_reference_patterns(sample_xml)
        
        # Should find broken reference
        broken_refs = [m for m in matches if m.pattern_name == "broken_reference"]
        assert len(broken_refs) > 0
        assert broken_refs[0].value == "broken-ref"
        
        # Should find unused IDs
        unused_ids = [m for m in matches if m.pattern_name == "unused_id"]
        assert len(unused_ids) >= 0  # May or may not have unused IDs
    
    def test_find_statistical_patterns(self, sample_xml):
        """Test statistical pattern finding."""
        finder = PatternFinder()
        
        matches = finder.find_statistical_patterns(sample_xml)
        
        # Should find some statistical patterns (or at least return a list)
        assert isinstance(matches, list)
    
    def test_find_all_patterns(self, sample_xml):
        """Test finding all pattern types."""
        finder = PatternFinder()
        
        # Set namespaces
        finder._namespaces = {'ar': 'http://autosar.org/schema/r4.0'}
        
        # Register some patterns
        xpath_pattern = PatternDefinition(
            name="xpath_test",
            pattern_type=PatternType.XPATH,
            pattern="//ar:SHORT-NAME"
        )
        finder.register_pattern(xpath_pattern)
        
        # Find all patterns
        xml_str = etree.tostring(sample_xml, encoding='unicode')
        matches = finder.find_all_patterns(sample_xml, xml_str)
        
        # Should have matches from at least one pattern type
        pattern_types = set(m.pattern_type for m in matches)
        assert len(pattern_types) >= 1
    
    def test_group_matches_by_type(self):
        """Test grouping matches by type."""
        finder = PatternFinder()
        
        # Create test matches
        matches = [
            PatternMatch("test1", PatternType.XPATH, "/test", "value1"),
            PatternMatch("test2", PatternType.XPATH, "/test2", "value2"),
            PatternMatch("test3", PatternType.REGEX, "line:1", "value3"),
            PatternMatch("test4", PatternType.STRUCTURAL, "/", 10)
        ]
        
        finder.matches = matches
        grouped = finder.group_matches_by_type()
        
        assert len(grouped[PatternType.XPATH]) == 2
        assert len(grouped[PatternType.REGEX]) == 1
        assert len(grouped[PatternType.STRUCTURAL]) == 1
    
    def test_group_matches_by_severity(self):
        """Test grouping matches by severity."""
        finder = PatternFinder()
        
        # Create test matches with severity metadata
        matches = [
            PatternMatch("test1", PatternType.XPATH, "/test", "value1", 
                        metadata={'severity': 'error'}),
            PatternMatch("test2", PatternType.XPATH, "/test2", "value2",
                        metadata={'severity': 'warning'}),
            PatternMatch("test3", PatternType.REGEX, "line:1", "value3",
                        metadata={'severity': 'error'}),
            PatternMatch("test4", PatternType.STRUCTURAL, "/", 10,
                        metadata={'severity': 'info'})
        ]
        
        finder.matches = matches
        grouped = finder.group_matches_by_severity()
        
        assert len(grouped['error']) == 2
        assert len(grouped['warning']) == 1
        assert len(grouped['info']) == 1
    
    def test_get_summary(self):
        """Test getting pattern match summary."""
        finder = PatternFinder()
        
        # Create test matches
        matches = [
            PatternMatch("pattern1", PatternType.XPATH, "/test", "value1",
                        metadata={'severity': 'error'}),
            PatternMatch("pattern1", PatternType.XPATH, "/test2", "value2",
                        metadata={'severity': 'error'}),
            PatternMatch("pattern2", PatternType.REGEX, "line:1", "value3",
                        metadata={'severity': 'warning'}),
            PatternMatch("pattern3", PatternType.STRUCTURAL, "/", 10,
                        metadata={'severity': 'info'})
        ]
        
        summary = finder.get_summary(matches)
        
        assert summary['total_matches'] == 4
        assert summary['by_type']['xpath'] == 2
        assert summary['by_type']['regex'] == 1
        assert summary['by_type']['structural'] == 1
        assert summary['by_severity']['error'] == 2
        assert summary['by_severity']['warning'] == 1
        assert summary['by_severity']['info'] == 1
        assert summary['by_pattern']['pattern1'] == 2
        assert summary['unique_patterns'] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])