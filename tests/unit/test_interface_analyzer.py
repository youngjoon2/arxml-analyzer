"""Unit tests for InterfaceAnalyzer."""

import pytest
from pathlib import Path
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

from arxml_analyzer.analyzers.interface_analyzer import (
    InterfaceAnalyzer,
    InterfaceInfo,
    DataElementInfo,
    OperationInfo,
    ModeGroupInfo
)
from arxml_analyzer.models.arxml_document import ARXMLDocument
from arxml_analyzer.core.analyzer.base_analyzer import AnalysisLevel, AnalysisStatus
from arxml_analyzer.utils.exceptions import AnalysisError


class TestInterfaceAnalyzer:
    """Test suite for InterfaceAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an InterfaceAnalyzer instance."""
        return InterfaceAnalyzer()
    
    @pytest.fixture
    def sample_sr_interface_xml(self):
        """Create a sample Sender-Receiver interface ARXML."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Interfaces</SHORT-NAME>
                    <ELEMENTS>
                        <SENDER-RECEIVER-INTERFACE>
                            <SHORT-NAME>SR_TestInterface</SHORT-NAME>
                            <IS-SERVICE>false</IS-SERVICE>
                            <DATA-ELEMENTS>
                                <VARIABLE-DATA-PROTOTYPE>
                                    <SHORT-NAME>TestData</SHORT-NAME>
                                    <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/DataTypes/uint32</TYPE-TREF>
                                    <INIT-VALUE>
                                        <NUMERICAL-VALUE-SPECIFICATION>
                                            <VALUE>0</VALUE>
                                        </NUMERICAL-VALUE-SPECIFICATION>
                                    </INIT-VALUE>
                                </VARIABLE-DATA-PROTOTYPE>
                                <VARIABLE-DATA-PROTOTYPE>
                                    <SHORT-NAME>StatusData</SHORT-NAME>
                                    <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/DataTypes/uint8</TYPE-TREF>
                                </VARIABLE-DATA-PROTOTYPE>
                            </DATA-ELEMENTS>
                            <INVALIDATION-POLICYS>
                                <INVALIDATION-POLICY>
                                    <DATA-ELEMENT-REF DEST="VARIABLE-DATA-PROTOTYPE">/Interfaces/SR_TestInterface/TestData</DATA-ELEMENT-REF>
                                    <HANDLE-INVALID>KEEP</HANDLE-INVALID>
                                </INVALIDATION-POLICY>
                            </INVALIDATION-POLICYS>
                        </SENDER-RECEIVER-INTERFACE>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
    
    @pytest.fixture
    def sample_cs_interface_xml(self):
        """Create a sample Client-Server interface ARXML."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Interfaces</SHORT-NAME>
                    <ELEMENTS>
                        <CLIENT-SERVER-INTERFACE>
                            <SHORT-NAME>CS_DiagnosticService</SHORT-NAME>
                            <IS-SERVICE>true</IS-SERVICE>
                            <OPERATIONS>
                                <CLIENT-SERVER-OPERATION>
                                    <SHORT-NAME>ReadData</SHORT-NAME>
                                    <ARGUMENTS>
                                        <ARGUMENT-DATA-PROTOTYPE>
                                            <SHORT-NAME>DataId</SHORT-NAME>
                                            <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/DataTypes/uint16</TYPE-TREF>
                                            <DIRECTION>IN</DIRECTION>
                                        </ARGUMENT-DATA-PROTOTYPE>
                                        <ARGUMENT-DATA-PROTOTYPE>
                                            <SHORT-NAME>DataBuffer</SHORT-NAME>
                                            <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/DataTypes/uint8Array</TYPE-TREF>
                                            <DIRECTION>OUT</DIRECTION>
                                        </ARGUMENT-DATA-PROTOTYPE>
                                    </ARGUMENTS>
                                    <POSSIBLE-ERROR-REFS>
                                        <POSSIBLE-ERROR-REF DEST="APPLICATION-ERROR">/Errors/E_NOT_OK</POSSIBLE-ERROR-REF>
                                        <POSSIBLE-ERROR-REF DEST="APPLICATION-ERROR">/Errors/E_PENDING</POSSIBLE-ERROR-REF>
                                    </POSSIBLE-ERROR-REFS>
                                </CLIENT-SERVER-OPERATION>
                                <CLIENT-SERVER-OPERATION>
                                    <SHORT-NAME>WriteData</SHORT-NAME>
                                    <ARGUMENTS>
                                        <ARGUMENT-DATA-PROTOTYPE>
                                            <SHORT-NAME>DataId</SHORT-NAME>
                                            <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/DataTypes/uint16</TYPE-TREF>
                                            <DIRECTION>IN</DIRECTION>
                                        </ARGUMENT-DATA-PROTOTYPE>
                                    </ARGUMENTS>
                                </CLIENT-SERVER-OPERATION>
                            </OPERATIONS>
                        </CLIENT-SERVER-INTERFACE>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
    
    @pytest.fixture
    def mixed_interfaces_xml(self):
        """Create an ARXML with multiple interface types."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Interfaces</SHORT-NAME>
                    <ELEMENTS>
                        <SENDER-RECEIVER-INTERFACE>
                            <SHORT-NAME>SR_Speed</SHORT-NAME>
                            <IS-SERVICE>false</IS-SERVICE>
                            <DATA-ELEMENTS>
                                <VARIABLE-DATA-PROTOTYPE>
                                    <SHORT-NAME>Value</SHORT-NAME>
                                    <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/DataTypes/uint16</TYPE-TREF>
                                </VARIABLE-DATA-PROTOTYPE>
                            </DATA-ELEMENTS>
                        </SENDER-RECEIVER-INTERFACE>
                        <SENDER-RECEIVER-INTERFACE>
                            <SHORT-NAME>SR_Temperature</SHORT-NAME>
                            <IS-SERVICE>false</IS-SERVICE>
                            <DATA-ELEMENTS>
                                <VARIABLE-DATA-PROTOTYPE>
                                    <SHORT-NAME>Value</SHORT-NAME>
                                    <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/DataTypes/sint16</TYPE-TREF>
                                </VARIABLE-DATA-PROTOTYPE>
                            </DATA-ELEMENTS>
                        </SENDER-RECEIVER-INTERFACE>
                        <CLIENT-SERVER-INTERFACE>
                            <SHORT-NAME>CS_Control</SHORT-NAME>
                            <IS-SERVICE>false</IS-SERVICE>
                            <OPERATIONS>
                                <CLIENT-SERVER-OPERATION>
                                    <SHORT-NAME>Start</SHORT-NAME>
                                </CLIENT-SERVER-OPERATION>
                                <CLIENT-SERVER-OPERATION>
                                    <SHORT-NAME>Stop</SHORT-NAME>
                                </CLIENT-SERVER-OPERATION>
                            </OPERATIONS>
                        </CLIENT-SERVER-INTERFACE>
                        <MODE-SWITCH-INTERFACE>
                            <SHORT-NAME>MS_VehicleMode</SHORT-NAME>
                            <IS-SERVICE>false</IS-SERVICE>
                            <MODE-GROUP>
                                <SHORT-NAME>CurrentMode</SHORT-NAME>
                                <TYPE-TREF DEST="MODE-DECLARATION-GROUP">/Modes/VehicleModeGroup</TYPE-TREF>
                            </MODE-GROUP>
                        </MODE-SWITCH-INTERFACE>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
    
    def test_analyzer_initialization(self, analyzer):
        """Test InterfaceAnalyzer initialization."""
        assert analyzer.analyzer_name == "InterfaceAnalyzer"
        assert "INTERFACE" in analyzer.supported_types
        assert "PORT-INTERFACE" in analyzer.supported_types
    
    def test_can_analyze_interface_document(self, analyzer, sample_sr_interface_xml):
        """Test can_analyze method with interface document."""
        root = ET.fromstring(sample_sr_interface_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        assert analyzer.can_analyze(doc) is True
    
    def test_can_analyze_non_interface_document(self, analyzer):
        """Test can_analyze method with non-interface document."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Test</SHORT-NAME>
                    <ELEMENTS>
                        <APPLICATION-SW-COMPONENT-TYPE>
                            <SHORT-NAME>TestComponent</SHORT-NAME>
                        </APPLICATION-SW-COMPONENT-TYPE>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        root = ET.fromstring(xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        assert analyzer.can_analyze(doc) is False
    
    def test_analyze_sr_interface(self, analyzer, sample_sr_interface_xml):
        """Test analyzing Sender-Receiver interface."""
        root = ET.fromstring(sample_sr_interface_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        
        assert result.metadata.analyzer_name == "InterfaceAnalyzer"
        assert result.metadata.status == AnalysisStatus.SUCCESS
        assert result.details["total_interfaces"] == 1
        
        # Check interface details
        interfaces = result.details["interfaces"]
        assert len(interfaces) == 1
        assert interfaces[0]["name"] == "SR_TestInterface"
        assert interfaces[0]["type"] == "SENDER-RECEIVER"
        assert interfaces[0]["is_service"] is False
        
        # Check data elements
        data_elements = interfaces[0]["data_elements"]
        assert len(data_elements) == 2
        assert data_elements[0]["name"] == "TestData"
        assert data_elements[0]["type_ref"] == "/DataTypes/uint32"
        assert data_elements[0]["init_value"] == "0"
        assert data_elements[1]["name"] == "StatusData"
        
        # Check invalidation policies
        inv_policies = interfaces[0]["invalidation_policies"]
        assert len(inv_policies) == 1
        assert inv_policies[0]["handle_invalid"] == "KEEP"
    
    def test_analyze_cs_interface(self, analyzer, sample_cs_interface_xml):
        """Test analyzing Client-Server interface."""
        root = ET.fromstring(sample_cs_interface_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        
        assert result.details["total_interfaces"] == 1
        
        interface = result.details["interfaces"][0]
        assert interface["name"] == "CS_DiagnosticService"
        assert interface["type"] == "CLIENT-SERVER"
        assert interface["is_service"] is True
        
        # Check operations
        operations = interface["operations"]
        assert len(operations) == 2
        
        # Check ReadData operation
        read_op = operations[0]
        assert read_op["name"] == "ReadData"
        assert len(read_op["arguments"]) == 2
        assert read_op["arguments"][0]["name"] == "DataId"
        assert read_op["arguments"][0]["direction"] == "IN"
        assert read_op["arguments"][1]["name"] == "DataBuffer"
        assert read_op["arguments"][1]["direction"] == "OUT"
        assert len(read_op["possible_errors"]) == 2
        assert "/Errors/E_NOT_OK" in read_op["possible_errors"]
        
        # Check WriteData operation
        write_op = operations[1]
        assert write_op["name"] == "WriteData"
        assert len(write_op["arguments"]) == 1
    
    def test_interface_statistics(self, analyzer, mixed_interfaces_xml):
        """Test interface statistics calculation."""
        root = ET.fromstring(mixed_interfaces_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        stats = result.details["statistics"]
        
        assert stats["interface_types"]["SENDER-RECEIVER"] == 2
        assert stats["interface_types"]["CLIENT-SERVER"] == 1
        assert stats["interface_types"]["MODE-SWITCH"] == 1
        assert stats["service_interfaces"] == 0
        assert stats["non_service_interfaces"] == 4
    
    def test_data_type_usage(self, analyzer, mixed_interfaces_xml):
        """Test data type usage analysis."""
        root = ET.fromstring(mixed_interfaces_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        type_usage = result.details["data_type_usage"]
        
        assert type_usage["unique_types"] >= 2  # uint16 and sint16
        assert type_usage["total_type_references"] >= 2
        
        # Check type categories
        categories = type_usage["type_categories"]
        assert categories["unsigned_integer"] >= 1
        assert categories["signed_integer"] >= 1
    
    def test_operation_complexity(self, analyzer, sample_cs_interface_xml):
        """Test operation complexity analysis."""
        root = ET.fromstring(sample_cs_interface_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        op_complexity = result.details["operation_complexity"]
        
        assert op_complexity["total_operations"] == 2
        assert op_complexity["avg_complexity"] > 0
        assert "complexity_distribution" in op_complexity
        assert "most_complex_operations" in op_complexity
        
        # ReadData should be more complex (2 args + 2 errors)
        most_complex = op_complexity["most_complex_operations"]
        assert len(most_complex) > 0
        assert most_complex[0]["operation"] == "ReadData"
        assert most_complex[0]["complexity"] == 4  # 2 args + 2 errors
    
    def test_interface_relationships(self, analyzer, mixed_interfaces_xml):
        """Test interface relationship analysis."""
        root = ET.fromstring(mixed_interfaces_xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        relationships = result.details["relationships"]
        
        assert "shared_data_types" in relationships
        assert "most_shared_types" in relationships
        assert "interface_coupling" in relationships
        assert "avg_coupling" in relationships
    
    def test_interface_validation(self, analyzer):
        """Test interface validation."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Interfaces</SHORT-NAME>
                    <ELEMENTS>
                        <SENDER-RECEIVER-INTERFACE>
                            <SHORT-NAME>SR_Invalid</SHORT-NAME>
                            <DATA-ELEMENTS>
                                <VARIABLE-DATA-PROTOTYPE>
                                    <SHORT-NAME>DataWithoutType</SHORT-NAME>
                                    <!-- Missing TYPE-TREF -->
                                </VARIABLE-DATA-PROTOTYPE>
                            </DATA-ELEMENTS>
                        </SENDER-RECEIVER-INTERFACE>
                        <CLIENT-SERVER-INTERFACE>
                            <SHORT-NAME>CS_Empty</SHORT-NAME>
                            <!-- No operations -->
                        </CLIENT-SERVER-INTERFACE>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        root = ET.fromstring(xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        validation = result.details["validation"]
        
        assert validation["valid"] is False
        assert validation["issue_count"] > 0
        assert validation["warning_count"] > 0
        assert len(validation["issues"]) > 0
        assert len(validation["warnings"]) > 0
    
    def test_get_patterns(self, analyzer):
        """Test get_patterns method."""
        patterns = analyzer.get_patterns()
        
        assert len(patterns) > 0
        pattern_names = [p["name"] for p in patterns]
        assert "Data Element Pattern" in pattern_names
        assert "Operation Pattern" in pattern_names
        assert "Type Reference Pattern" in pattern_names
        assert "Interface Hierarchy" in pattern_names
    
    def test_mode_switch_interface(self, analyzer):
        """Test Mode-Switch interface extraction."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Interfaces</SHORT-NAME>
                    <ELEMENTS>
                        <MODE-SWITCH-INTERFACE>
                            <SHORT-NAME>MS_EcuMode</SHORT-NAME>
                            <IS-SERVICE>false</IS-SERVICE>
                            <MODE-GROUP>
                                <SHORT-NAME>CurrentEcuMode</SHORT-NAME>
                                <TYPE-TREF DEST="MODE-DECLARATION-GROUP">/Modes/EcuModeGroup</TYPE-TREF>
                                <INITIAL-MODE-REF DEST="MODE-DECLARATION">/Modes/EcuModeGroup/STARTUP</INITIAL-MODE-REF>
                            </MODE-GROUP>
                        </MODE-SWITCH-INTERFACE>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        root = ET.fromstring(xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        
        assert result.details["total_interfaces"] == 1
        interface = result.details["interfaces"][0]
        assert interface["name"] == "MS_EcuMode"
        assert interface["type"] == "MODE-SWITCH"
        
        # Check mode groups
        mode_groups = interface["mode_groups"]
        assert len(mode_groups) == 1
        assert mode_groups[0]["name"] == "CurrentEcuMode"
        assert mode_groups[0]["type_ref"] == "/Modes/EcuModeGroup"
        assert mode_groups[0]["initial_mode"] == "/Modes/EcuModeGroup/STARTUP"
    
    def test_parameter_interface(self, analyzer):
        """Test Parameter interface extraction."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Interfaces</SHORT-NAME>
                    <ELEMENTS>
                        <PARAMETER-INTERFACE>
                            <SHORT-NAME>PI_CalibrationData</SHORT-NAME>
                            <IS-SERVICE>false</IS-SERVICE>
                            <PARAMETERS>
                                <PARAMETER-DATA-PROTOTYPE>
                                    <SHORT-NAME>CalibrationValue1</SHORT-NAME>
                                    <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/DataTypes/float32</TYPE-TREF>
                                    <INIT-VALUE>
                                        <NUMERICAL-VALUE-SPECIFICATION>
                                            <VALUE>1.5</VALUE>
                                        </NUMERICAL-VALUE-SPECIFICATION>
                                    </INIT-VALUE>
                                </PARAMETER-DATA-PROTOTYPE>
                            </PARAMETERS>
                        </PARAMETER-INTERFACE>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        root = ET.fromstring(xml)
        doc = ARXMLDocument(root, "test.arxml", {})
        
        result = analyzer.analyze(doc)
        
        assert result.details["total_interfaces"] == 1
        interface = result.details["interfaces"][0]
        assert interface["name"] == "PI_CalibrationData"
        assert interface["type"] == "PARAMETER"
        
        # Check parameters as data elements
        data_elements = interface["data_elements"]
        assert len(data_elements) == 1
        assert data_elements[0]["name"] == "CalibrationValue1"
        assert data_elements[0]["data_type"] == "PARAMETER"
        assert data_elements[0]["init_value"] == "1.5"