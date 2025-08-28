"""Unit tests for ECUCAnalyzer."""

import pytest
from lxml import etree
from pathlib import Path

from arxml_analyzer.analyzers.ecuc_analyzer import (
    ECUCAnalyzer, 
    ECUCModule,
    ECUCParameter
)
from arxml_analyzer.models.arxml_document import ARXMLDocument
from arxml_analyzer.core.analyzer.base_analyzer import (
    AnalysisLevel,
    AnalysisStatus
)


class TestECUCAnalyzer:
    """Test cases for ECUCAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an ECUCAnalyzer instance."""
        return ECUCAnalyzer()
    
    @pytest.fixture
    def sample_ecuc_xml(self):
        """Create sample ECUC ARXML content."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://www.autosar.org/schema/r4.0" 
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>EcucModuleConfigurationValues</SHORT-NAME>
                    <ELEMENTS>
                        <ECUC-MODULE-CONFIGURATION-VALUES>
                            <SHORT-NAME>Os</SHORT-NAME>
                            <DEFINITION-REF>/AUTOSAR/EcucDefs/Os</DEFINITION-REF>
                            <CONTAINERS>
                                <ECUC-CONTAINER-VALUE>
                                    <SHORT-NAME>OsOS</SHORT-NAME>
                                    <DEFINITION-REF>/AUTOSAR/EcucDefs/Os/OsOS</DEFINITION-REF>
                                    <PARAMETER-VALUES>
                                        <ECUC-NUMERICAL-PARAM-VALUE>
                                            <DEFINITION-REF>/AUTOSAR/EcucDefs/Os/OsOS/OsStackMonitoring</DEFINITION-REF>
                                            <VALUE>1</VALUE>
                                        </ECUC-NUMERICAL-PARAM-VALUE>
                                        <ECUC-TEXTUAL-PARAM-VALUE>
                                            <DEFINITION-REF>/AUTOSAR/EcucDefs/Os/OsOS/OsStatus</DEFINITION-REF>
                                            <VALUE>EXTENDED</VALUE>
                                        </ECUC-TEXTUAL-PARAM-VALUE>
                                    </PARAMETER-VALUES>
                                    <SUB-CONTAINERS>
                                        <ECUC-CONTAINER-VALUE>
                                            <SHORT-NAME>OsHooks</SHORT-NAME>
                                            <DEFINITION-REF>/AUTOSAR/EcucDefs/Os/OsOS/OsHooks</DEFINITION-REF>
                                            <PARAMETER-VALUES>
                                                <ECUC-NUMERICAL-PARAM-VALUE>
                                                    <DEFINITION-REF>/AUTOSAR/EcucDefs/Os/OsOS/OsHooks/OsErrorHook</DEFINITION-REF>
                                                    <VALUE>1</VALUE>
                                                </ECUC-NUMERICAL-PARAM-VALUE>
                                            </PARAMETER-VALUES>
                                        </ECUC-CONTAINER-VALUE>
                                    </SUB-CONTAINERS>
                                </ECUC-CONTAINER-VALUE>
                                <ECUC-CONTAINER-VALUE>
                                    <SHORT-NAME>OsTask</SHORT-NAME>
                                    <DEFINITION-REF>/AUTOSAR/EcucDefs/Os/OsTask</DEFINITION-REF>
                                    <PARAMETER-VALUES>
                                        <ECUC-NUMERICAL-PARAM-VALUE>
                                            <DEFINITION-REF>/AUTOSAR/EcucDefs/Os/OsTask/OsTaskPriority</DEFINITION-REF>
                                            <VALUE>10</VALUE>
                                        </ECUC-NUMERICAL-PARAM-VALUE>
                                    </PARAMETER-VALUES>
                                    <REFERENCE-VALUES>
                                        <ECUC-REFERENCE-VALUE>
                                            <DEFINITION-REF>/AUTOSAR/EcucDefs/Os/OsTask/OsTaskResourceRef</DEFINITION-REF>
                                            <VALUE-REF>/EcucModuleConfigurationValues/Os/OsResource</VALUE-REF>
                                        </ECUC-REFERENCE-VALUE>
                                    </REFERENCE-VALUES>
                                </ECUC-CONTAINER-VALUE>
                            </CONTAINERS>
                        </ECUC-MODULE-CONFIGURATION-VALUES>
                        <ECUC-MODULE-CONFIGURATION-VALUES>
                            <SHORT-NAME>Com</SHORT-NAME>
                            <DEFINITION-REF>/AUTOSAR/EcucDefs/Com</DEFINITION-REF>
                            <CONTAINERS>
                                <ECUC-CONTAINER-VALUE>
                                    <SHORT-NAME>ComConfig</SHORT-NAME>
                                    <DEFINITION-REF>/AUTOSAR/EcucDefs/Com/ComConfig</DEFINITION-REF>
                                    <PARAMETER-VALUES>
                                        <ECUC-NUMERICAL-PARAM-VALUE>
                                            <DEFINITION-REF>/AUTOSAR/EcucDefs/Com/ComConfig/ComAppModeNum</DEFINITION-REF>
                                            <VALUE>2</VALUE>
                                        </ECUC-NUMERICAL-PARAM-VALUE>
                                    </PARAMETER-VALUES>
                                </ECUC-CONTAINER-VALUE>
                            </CONTAINERS>
                        </ECUC-MODULE-CONFIGURATION-VALUES>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        return content
    
    @pytest.fixture
    def ecuc_document(self, sample_ecuc_xml, tmp_path):
        """Create an ARXMLDocument with ECUC content."""
        # Write to temporary file
        test_file = tmp_path / "test_ecuc.arxml"
        test_file.write_text(sample_ecuc_xml)
        
        # Create document with required parameters
        root = etree.fromstring(sample_ecuc_xml.encode())
        doc = ARXMLDocument(
            root=root,
            file_path=str(test_file),
            namespaces={'ar': 'http://www.autosar.org/schema/r4.0'}
        )
        doc.content = sample_ecuc_xml
        doc.detected_types = [{'type': 'ECUC', 'confidence': 0.95}]
        return doc
    
    def test_analyzer_initialization(self, analyzer):
        """Test ECUCAnalyzer initialization."""
        assert analyzer.name == "ECUCAnalyzer"
        assert analyzer.version == "2.0.0"
        # Note: V2 uses adaptive type detection instead of hardcoded supported_types
    
    def test_can_analyze_ecuc_document(self, analyzer, ecuc_document):
        """Test if analyzer can handle ECUC documents."""
        assert analyzer.can_analyze(ecuc_document) is True
    
    def test_analyze_ecuc_modules(self, analyzer, ecuc_document):
        """Test ECUC module extraction and analysis."""
        result = analyzer.analyze(ecuc_document)
        
        # Check metadata
        assert result.metadata.analyzer_name == "ECUCAnalyzer"
        assert result.metadata.arxml_type == "ECUC"
        assert result.metadata.status == AnalysisStatus.COMPLETED
        
        # Check module extraction
        assert 'modules' in result.details
        modules = result.details['modules']
        assert len(modules) == 2
        
        # Check Os module
        os_module = next((m for m in modules if m['name'] == 'Os'), None)
        assert os_module is not None
        assert os_module['container_count'] == 2
        assert os_module['parameter_count'] == 0  # Module-level parameters
        
        # Check Com module
        com_module = next((m for m in modules if m['name'] == 'Com'), None)
        assert com_module is not None
        assert com_module['container_count'] == 1
    
    def test_analyze_parameters(self, analyzer, ecuc_document):
        """Test parameter extraction and analysis."""
        result = analyzer.analyze(ecuc_document)
        
        assert 'parameter_analysis' in result.details
        param_analysis = result.details['parameter_analysis']
        
        # Check parameter statistics
        assert param_analysis['total'] > 0
        assert 'INTEGER' in param_analysis['by_type']
        assert 'STRING' in param_analysis['by_type']
        
        # Check specific parameter values
        assert param_analysis['by_type']['INTEGER'] >= 3  # At least 3 numerical params
        assert param_analysis['by_type']['STRING'] >= 1  # At least 1 textual param
    
    def test_analyze_containers(self, analyzer, ecuc_document):
        """Test container structure analysis."""
        result = analyzer.analyze(ecuc_document)
        
        assert 'container_analysis' in result.details
        container_analysis = result.details['container_analysis']
        
        # Check container statistics
        assert container_analysis['total'] == 3  # OsOS, OsTask, ComConfig
        assert container_analysis['max_depth'] >= 2  # OsOS has OsHooks as sub-container
        
        # Check for empty containers
        assert isinstance(container_analysis['empty_containers'], list)
    
    def test_analyze_references(self, analyzer, ecuc_document):
        """Test reference integrity checking."""
        result = analyzer.analyze(ecuc_document)
        
        assert 'reference_analysis' in result.details
        ref_analysis = result.details['reference_analysis']
        
        # Check reference statistics
        assert ref_analysis['total'] == 1  # OsTaskResourceRef
        assert isinstance(ref_analysis['broken'], list)
        assert isinstance(ref_analysis['external'], list)
    
    def test_analyze_dependencies(self, analyzer, ecuc_document):
        """Test dependency analysis."""
        result = analyzer.analyze(ecuc_document)
        
        assert 'dependencies' in result.details
        dependencies = result.details['dependencies']
        
        # Check dependency structure
        assert 'module_dependencies' in dependencies
        assert 'common_parameters' in dependencies
        assert 'configuration_groups' in dependencies
    
    def test_find_patterns(self, analyzer, ecuc_document):
        """Test pattern detection in ECUC configuration."""
        result = analyzer.analyze(ecuc_document)
        
        # Check for patterns - patterns is a dict of lists
        assert isinstance(result.patterns, dict)
        
        # If patterns found, verify structure
        if result.patterns:
            assert len(result.patterns) > 0  # Should have at least one pattern type
            for pattern_type, patterns in result.patterns.items():
                assert isinstance(patterns, list)
                assert len(patterns) > 0  # Should have at least one pattern of this type
                for pattern in patterns:
                    assert isinstance(pattern, dict)
    
    def test_generate_statistics(self, analyzer, ecuc_document):
        """Test statistics generation."""
        result = analyzer.analyze(ecuc_document)
        
        assert len(result.statistics) > 0
        
        # Check module statistics
        assert 'modules' in result.statistics
        module_stats = result.statistics['modules']
        assert module_stats['count'] == 2
        
        # Check parameter statistics  
        assert 'parameters' in result.statistics
        param_stats = result.statistics['parameters']
        assert param_stats['total'] > 0
        
        # Check container statistics
        assert 'containers' in result.statistics
        container_stats = result.statistics['containers']
        assert container_stats['total'] == 3
        
        # Check complexity metrics
        assert 'complexity' in result.statistics
    
    def test_generate_recommendations(self, analyzer, ecuc_document):
        """Test recommendation generation."""
        result = analyzer.analyze(ecuc_document)
        
        # Recommendations should be generated based on findings
        assert isinstance(result.recommendations, list)
        
        # Check if recommendations are strings
        for rec in result.recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0
    
    def test_empty_document(self, analyzer, tmp_path):
        """Test handling of empty ECUC document."""
        empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://www.autosar.org/schema/r4.0">
            <AR-PACKAGES/>
        </AUTOSAR>"""
        
        # Write to temporary file
        test_file = tmp_path / "empty_ecuc.arxml"
        test_file.write_text(empty_xml)
        
        doc = ARXMLDocument(
            root=etree.fromstring(empty_xml.encode()),
            file_path=str(test_file),
            namespaces={'ar': 'http://www.autosar.org/schema/r4.0'}
        )
        doc.content = empty_xml
        doc.detected_types = [{'type': 'ECUC', 'confidence': 0.8}]
        
        result = analyzer.analyze(doc)
        
        # Should complete without errors
        assert result.metadata.status == AnalysisStatus.COMPLETED
        assert result.summary['total_modules'] == 0
    
    def test_malformed_parameters(self, analyzer, tmp_path):
        """Test handling of malformed parameter values."""
        malformed_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://www.autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <ELEMENTS>
                        <ECUC-MODULE-CONFIGURATION-VALUES>
                            <SHORT-NAME>TestModule</SHORT-NAME>
                            <CONTAINERS>
                                <ECUC-CONTAINER-VALUE>
                                    <SHORT-NAME>TestContainer</SHORT-NAME>
                                    <PARAMETER-VALUES>
                                        <ECUC-NUMERICAL-PARAM-VALUE>
                                            <DEFINITION-REF>/Test/Param</DEFINITION-REF>
                                            <VALUE>not_a_number</VALUE>
                                        </ECUC-NUMERICAL-PARAM-VALUE>
                                    </PARAMETER-VALUES>
                                </ECUC-CONTAINER-VALUE>
                            </CONTAINERS>
                        </ECUC-MODULE-CONFIGURATION-VALUES>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        # Write to temporary file
        test_file = tmp_path / "malformed_ecuc.arxml"
        test_file.write_text(malformed_xml)
        
        doc = ARXMLDocument(
            root=etree.fromstring(malformed_xml.encode()),
            file_path=str(test_file),
            namespaces={'ar': 'http://www.autosar.org/schema/r4.0'}
        )
        doc.content = malformed_xml
        doc.detected_types = [{'type': 'ECUC', 'confidence': 0.9}]
        
        # Should handle gracefully
        result = analyzer.analyze(doc)
        assert result.metadata.status in [AnalysisStatus.COMPLETED, AnalysisStatus.PARTIAL]
    
    def test_deep_nesting_detection(self, analyzer, tmp_path):
        """Test detection of deeply nested containers."""
        # Create a deeply nested structure
        deep_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://www.autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <ELEMENTS>
                        <ECUC-MODULE-CONFIGURATION-VALUES>
                            <SHORT-NAME>DeepModule</SHORT-NAME>
                            <CONTAINERS>
                                <ECUC-CONTAINER-VALUE>
                                    <SHORT-NAME>Level1</SHORT-NAME>
                                    <SUB-CONTAINERS>
                                        <ECUC-CONTAINER-VALUE>
                                            <SHORT-NAME>Level2</SHORT-NAME>
                                            <SUB-CONTAINERS>
                                                <ECUC-CONTAINER-VALUE>
                                                    <SHORT-NAME>Level3</SHORT-NAME>
                                                    <SUB-CONTAINERS>
                                                        <ECUC-CONTAINER-VALUE>
                                                            <SHORT-NAME>Level4</SHORT-NAME>
                                                            <SUB-CONTAINERS>
                                                                <ECUC-CONTAINER-VALUE>
                                                                    <SHORT-NAME>Level5</SHORT-NAME>
                                                                    <SUB-CONTAINERS>
                                                                        <ECUC-CONTAINER-VALUE>
                                                                            <SHORT-NAME>Level6</SHORT-NAME>
                                                                        </ECUC-CONTAINER-VALUE>
                                                                    </SUB-CONTAINERS>
                                                                </ECUC-CONTAINER-VALUE>
                                                            </SUB-CONTAINERS>
                                                        </ECUC-CONTAINER-VALUE>
                                                    </SUB-CONTAINERS>
                                                </ECUC-CONTAINER-VALUE>
                                            </SUB-CONTAINERS>
                                        </ECUC-CONTAINER-VALUE>
                                    </SUB-CONTAINERS>
                                </ECUC-CONTAINER-VALUE>
                            </CONTAINERS>
                        </ECUC-MODULE-CONFIGURATION-VALUES>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        # Write to temporary file
        test_file = tmp_path / "deep_ecuc.arxml"
        test_file.write_text(deep_xml)
        
        doc = ARXMLDocument(
            root=etree.fromstring(deep_xml.encode()),
            file_path=str(test_file),
            namespaces={'ar': 'http://www.autosar.org/schema/r4.0'}
        )
        doc.content = deep_xml
        doc.detected_types = [{'type': 'ECUC', 'confidence': 0.95}]
        
        result = analyzer.analyze(doc)
        
        # Check for deep nesting warning
        assert any('deep nesting' in warning.lower() for warning in result.metadata.warnings)
        
        # Check recommendations
        assert any('deep' in rec.lower() or 'nesting' in rec.lower() 
                  for rec in result.recommendations)
    
    def test_get_patterns(self, analyzer):
        """Test pattern definition retrieval."""
        patterns = analyzer.get_patterns()
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        
        # Check pattern structure
        for pattern in patterns:
            assert 'name' in pattern
            assert 'description' in pattern
            assert 'type' in pattern
    
    def test_safe_analyze(self, analyzer, ecuc_document):
        """Test safe analysis with error handling."""
        result = analyzer.analyze_safe(ecuc_document)
        
        # Should always return a result
        assert result is not None
        assert result.metadata.status in [
            AnalysisStatus.COMPLETED,
            AnalysisStatus.PARTIAL,
            AnalysisStatus.FAILED
        ]
        
        # Check timing information
        assert result.metadata.analysis_duration >= 0