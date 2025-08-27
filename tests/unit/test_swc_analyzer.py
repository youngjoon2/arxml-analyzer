"""Unit tests for SWCAnalyzer."""

import pytest
from pathlib import Path
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

from arxml_analyzer.analyzers.swc_analyzer import (
    SWCAnalyzer,
    SWCInfo,
    PortInfo,
    RunnableInfo
)
from arxml_analyzer.models.arxml_document import ARXMLDocument
from arxml_analyzer.core.analyzer.base_analyzer import AnalysisLevel, AnalysisStatus
from arxml_analyzer.utils.exceptions import AnalysisError


class TestSWCAnalyzer:
    """Test suite for SWCAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an SWCAnalyzer instance."""
        return SWCAnalyzer()
    
    @pytest.fixture
    def sample_swc_xml(self):
        """Create a sample SWC ARXML content."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Components</SHORT-NAME>
                    <ELEMENTS>
                        <APPLICATION-SW-COMPONENT-TYPE>
                            <SHORT-NAME>TestComponent</SHORT-NAME>
                            <CATEGORY>APPLICATION_SW_COMPONENT</CATEGORY>
                            <PORTS>
                                <P-PORT-PROTOTYPE>
                                    <SHORT-NAME>PP_Output</SHORT-NAME>
                                    <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">/Interfaces/SR_TestInterface</PROVIDED-INTERFACE-TREF>
                                </P-PORT-PROTOTYPE>
                                <R-PORT-PROTOTYPE>
                                    <SHORT-NAME>RP_Input</SHORT-NAME>
                                    <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">/Interfaces/SR_InputInterface</REQUIRED-INTERFACE-TREF>
                                </R-PORT-PROTOTYPE>
                                <PR-PORT-PROTOTYPE>
                                    <SHORT-NAME>PRP_Service</SHORT-NAME>
                                    <PROVIDED-REQUIRED-INTERFACE-TREF DEST="CLIENT-SERVER-INTERFACE">/Interfaces/CS_ServiceInterface</PROVIDED-REQUIRED-INTERFACE-TREF>
                                </PR-PORT-PROTOTYPE>
                            </PORTS>
                            <INTERNAL-BEHAVIORS>
                                <SWC-INTERNAL-BEHAVIOR>
                                    <SHORT-NAME>TestComponent_InternalBehavior</SHORT-NAME>
                                    <RUNNABLES>
                                        <RUNNABLE-ENTITY>
                                            <SHORT-NAME>RE_MainFunction</SHORT-NAME>
                                            <MINIMUM-START-INTERVAL>0.01</MINIMUM-START-INTERVAL>
                                            <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
                                            <SYMBOL>RE_MainFunction</SYMBOL>
                                            <DATA-READ-ACCESSS>
                                                <VARIABLE-ACCESS>
                                                    <SHORT-NAME>DA_ReadInput</SHORT-NAME>
                                                </VARIABLE-ACCESS>
                                            </DATA-READ-ACCESSS>
                                            <DATA-WRITE-ACCESSS>
                                                <VARIABLE-ACCESS>
                                                    <SHORT-NAME>DA_WriteOutput</SHORT-NAME>
                                                </VARIABLE-ACCESS>
                                            </DATA-WRITE-ACCESSS>
                                        </RUNNABLE-ENTITY>
                                    </RUNNABLES>
                                </SWC-INTERNAL-BEHAVIOR>
                            </INTERNAL-BEHAVIORS>
                        </APPLICATION-SW-COMPONENT-TYPE>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
    
    @pytest.fixture
    def complex_swc_xml(self):
        """Create a complex SWC with multiple components."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Components</SHORT-NAME>
                    <ELEMENTS>
                        <APPLICATION-SW-COMPONENT-TYPE>
                            <SHORT-NAME>Component1</SHORT-NAME>
                            <PORTS>
                                <P-PORT-PROTOTYPE>
                                    <SHORT-NAME>PP_Out1</SHORT-NAME>
                                    <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">/If/SR_1</PROVIDED-INTERFACE-TREF>
                                </P-PORT-PROTOTYPE>
                                <P-PORT-PROTOTYPE>
                                    <SHORT-NAME>PP_Out2</SHORT-NAME>
                                    <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">/If/SR_2</PROVIDED-INTERFACE-TREF>
                                </P-PORT-PROTOTYPE>
                            </PORTS>
                        </APPLICATION-SW-COMPONENT-TYPE>
                        <COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE>
                            <SHORT-NAME>CDD_Component</SHORT-NAME>
                            <PORTS>
                                <R-PORT-PROTOTYPE>
                                    <SHORT-NAME>RP_In1</SHORT-NAME>
                                    <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">/If/SR_1</REQUIRED-INTERFACE-TREF>
                                </R-PORT-PROTOTYPE>
                            </PORTS>
                            <INTERNAL-BEHAVIORS>
                                <SWC-INTERNAL-BEHAVIOR>
                                    <SHORT-NAME>CDD_Behavior</SHORT-NAME>
                                    <RUNNABLES>
                                        <RUNNABLE-ENTITY>
                                            <SHORT-NAME>RE_Fast</SHORT-NAME>
                                            <MINIMUM-START-INTERVAL>0.001</MINIMUM-START-INTERVAL>
                                            <CAN-BE-INVOKED-CONCURRENTLY>true</CAN-BE-INVOKED-CONCURRENTLY>
                                        </RUNNABLE-ENTITY>
                                        <RUNNABLE-ENTITY>
                                            <SHORT-NAME>RE_Slow</SHORT-NAME>
                                            <MINIMUM-START-INTERVAL>1.0</MINIMUM-START-INTERVAL>
                                        </RUNNABLE-ENTITY>
                                    </RUNNABLES>
                                </SWC-INTERNAL-BEHAVIOR>
                            </INTERNAL-BEHAVIORS>
                        </COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
    
    def test_analyzer_initialization(self, analyzer):
        """Test SWCAnalyzer initialization."""
        assert analyzer.analyzer_name == "SWCAnalyzer"
        assert "SWC" in analyzer.supported_types
        assert "APPLICATION-SW-COMPONENT-TYPE" in analyzer.supported_types
    
    def test_can_analyze_swc_document(self, analyzer, sample_swc_xml):
        """Test can_analyze method with SWC document."""
        root = ET.fromstring(sample_swc_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        assert analyzer.can_analyze(doc) is True
    
    def test_can_analyze_non_swc_document(self, analyzer):
        """Test can_analyze method with non-SWC document."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Test</SHORT-NAME>
                    <ELEMENTS>
                        <ECUC-MODULE-CONFIGURATION-VALUES>
                            <SHORT-NAME>TestModule</SHORT-NAME>
                        </ECUC-MODULE-CONFIGURATION-VALUES>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        root = ET.fromstring(xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        assert analyzer.can_analyze(doc) is False
    
    def test_analyze_simple_swc(self, analyzer, sample_swc_xml):
        """Test analyzing a simple SWC."""
        root = ET.fromstring(sample_swc_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        
        assert result.metadata.analyzer_name == "SWCAnalyzer"
        assert result.metadata.status == AnalysisStatus.SUCCESS
        assert result.details["total_components"] == 1
        
        # Check component details
        components = result.details["components"]
        assert len(components) == 1
        assert components[0]["name"] == "TestComponent"
        assert components[0]["type"] == "APPLICATION"
        
        # Check ports
        ports = components[0]["ports"]
        assert len(ports["provided"]) == 1
        assert len(ports["required"]) == 1
        assert len(ports["pr"]) == 1
        
        # Check runnables
        runnables = components[0]["runnables"]
        assert len(runnables) == 1
        assert runnables[0]["name"] == "RE_MainFunction"
        assert runnables[0]["min_interval"] == 0.01
        assert runnables[0]["concurrent"] is False
    
    def test_analyze_multiple_components(self, analyzer, complex_swc_xml):
        """Test analyzing multiple SWC components."""
        root = ET.fromstring(complex_swc_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        
        assert result.details["total_components"] == 2
        
        components = result.details["components"]
        component_names = [c["name"] for c in components]
        assert "Component1" in component_names
        assert "CDD_Component" in component_names
        
        # Check component types
        component_types = [c["type"] for c in components]
        assert "APPLICATION" in component_types
        assert "COMPLEX_DEVICE_DRIVER" in component_types
    
    def test_port_statistics(self, analyzer, complex_swc_xml):
        """Test port statistics calculation."""
        root = ET.fromstring(complex_swc_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        port_stats = result.details["port_statistics"]
        
        assert port_stats["provided_ports"] == 2
        assert port_stats["required_ports"] == 1
        assert port_stats["pr_ports"] == 0
        assert port_stats["total_ports"] == 3
        assert port_stats["avg_ports_per_component"] == 1.5
    
    def test_runnable_statistics(self, analyzer, complex_swc_xml):
        """Test runnable statistics calculation."""
        root = ET.fromstring(complex_swc_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        runnable_stats = result.details["runnable_statistics"]
        
        assert runnable_stats["total_runnables"] == 2
        assert runnable_stats["periodic_runnables"] == 2
        assert runnable_stats["concurrent_runnables"] == 1
        assert runnable_stats["min_interval"] == 0.001
        assert runnable_stats["max_interval"] == 1.0
    
    def test_interface_usage_analysis(self, analyzer, complex_swc_xml):
        """Test interface usage analysis."""
        root = ET.fromstring(complex_swc_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        interface_usage = result.details["interface_usage"]
        
        assert interface_usage["unique_interfaces"] == 2
        # SR_1 is used by both Component1 (provided) and CDD_Component (required)
        most_used = interface_usage["most_used_interfaces"]
        assert len(most_used) > 0
        assert most_used[0][0] == "/If/SR_1"
        assert most_used[0][1] == 2  # Used twice
    
    def test_complexity_metrics(self, analyzer, sample_swc_xml):
        """Test complexity metrics calculation."""
        root = ET.fromstring(sample_swc_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        complexity = result.details["complexity_metrics"]
        
        assert "min_complexity" in complexity
        assert "max_complexity" in complexity
        assert "avg_complexity" in complexity
        assert "complexity_distribution" in complexity
        
        # Check complexity distribution categories
        distribution = complexity["complexity_distribution"]
        assert "simple" in distribution
        assert "moderate" in distribution
        assert "complex" in distribution
        assert "very_complex" in distribution
    
    def test_get_patterns(self, analyzer):
        """Test get_patterns method."""
        patterns = analyzer.get_patterns()
        
        assert len(patterns) > 0
        pattern_names = [p["name"] for p in patterns]
        assert "Port Connection Pattern" in pattern_names
        assert "Runnable Timing Pattern" in pattern_names
        assert "Data Access Pattern" in pattern_names
        assert "Event-Runnable Mapping" in pattern_names
    
    def test_error_handling(self, analyzer):
        """Test error handling in analysis."""
        # Create invalid document
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <INVALID>Invalid content</INVALID>
        </AUTOSAR>"""
        
        root = ET.fromstring(invalid_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        # Should not raise error but return empty results
        result = analyzer.analyze(doc)
        assert result.metadata.status == AnalysisStatus.SUCCESS
        assert result.details["total_components"] == 0
    
    def test_extract_swc_with_service_components(self, analyzer):
        """Test extracting service SW components."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Services</SHORT-NAME>
                    <ELEMENTS>
                        <SERVICE-SW-COMPONENT-TYPE>
                            <SHORT-NAME>DiagnosticService</SHORT-NAME>
                            <CATEGORY>SERVICE_SW_COMPONENT</CATEGORY>
                            <PORTS>
                                <P-PORT-PROTOTYPE>
                                    <SHORT-NAME>PP_Diagnostic</SHORT-NAME>
                                    <PROVIDED-INTERFACE-TREF DEST="CLIENT-SERVER-INTERFACE">/If/CS_Diagnostic</PROVIDED-INTERFACE-TREF>
                                </P-PORT-PROTOTYPE>
                            </PORTS>
                        </SERVICE-SW-COMPONENT-TYPE>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        root = ET.fromstring(xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        
        assert result.details["total_components"] == 1
        component = result.details["components"][0]
        assert component["name"] == "DiagnosticService"
        assert component["type"] == "SERVICE"
        assert component["category"] == "SERVICE_SW_COMPONENT"