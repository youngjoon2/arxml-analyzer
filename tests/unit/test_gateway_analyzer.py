"""Unit tests for GatewayAnalyzer."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime
from lxml import etree as ET

from arxml_analyzer.analyzers.gateway_analyzer import (
    GatewayAnalyzer,
    RoutingPath,
    SignalGateway,
    NetworkInterface,
    ProtocolConversion
)
from arxml_analyzer.models.arxml_document import ARXMLDocument
from arxml_analyzer.core.analyzer.base_analyzer import (
    AnalysisResult,
    AnalysisStatus,
    AnalysisLevel
)
from arxml_analyzer.core.analyzer.pattern_finder import PatternType
from arxml_analyzer.utils.exceptions import AnalysisError


class TestGatewayAnalyzer:
    """Test suite for GatewayAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a GatewayAnalyzer instance."""
        return GatewayAnalyzer()
        
    @pytest.fixture
    def sample_gateway_xml(self):
        """Create sample gateway ARXML content."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>PduR</SHORT-NAME>
                    <ELEMENTS>
                        <ROUTING-PATH>
                            <SHORT-NAME>CanToEth_Route</SHORT-NAME>
                            <SOURCE>
                                <SOURCE-PDU-REF>/Pdus/CanPdu1</SOURCE-PDU-REF>
                                <SOURCE-MODULE>CanIf</SOURCE-MODULE>
                            </SOURCE>
                            <DESTINATION>
                                <DESTINATION-PDU-REF>/Pdus/EthPdu1</DESTINATION-PDU-REF>
                                <DESTINATION-MODULE>SoAd</DESTINATION-MODULE>
                            </DESTINATION>
                            <ROUTING-TYPE>IF</ROUTING-TYPE>
                            <GATEWAY-TYPE>ON_THE_FLY</GATEWAY-TYPE>
                        </ROUTING-PATH>
                        
                        <ROUTING-PATH>
                            <SHORT-NAME>TP_Route</SHORT-NAME>
                            <SOURCE>
                                <SOURCE-PDU-REF>/Pdus/TpSource</SOURCE-PDU-REF>
                                <SOURCE-MODULE>CanTp</SOURCE-MODULE>
                            </SOURCE>
                            <DESTINATION>
                                <DESTINATION-PDU-REF>/Pdus/TpDest</DESTINATION-PDU-REF>
                                <DESTINATION-MODULE>FrTp</DESTINATION-MODULE>
                            </DESTINATION>
                            <ROUTING-TYPE>TP</ROUTING-TYPE>
                            <GATEWAY-TYPE>FIFO</GATEWAY-TYPE>
                            <BUFFER-SIZE>4096</BUFFER-SIZE>
                            <THRESHOLD>2048</THRESHOLD>
                        </ROUTING-PATH>
                    </ELEMENTS>
                </AR-PACKAGE>
                
                <AR-PACKAGE>
                    <SHORT-NAME>Gateways</SHORT-NAME>
                    <ELEMENTS>
                        <SIGNAL-GATEWAY>
                            <SHORT-NAME>SignalGw1</SHORT-NAME>
                            <SOURCE-SIGNAL>
                                <SIGNAL-REF>/Signals/Speed</SIGNAL-REF>
                                <I-PDU-REF>/Pdus/CanPdu1</I-PDU-REF>
                            </SOURCE-SIGNAL>
                            <DESTINATION-SIGNAL>
                                <SIGNAL-REF>/Signals/VehicleSpeed</SIGNAL-REF>
                                <I-PDU-REF>/Pdus/EthPdu1</I-PDU-REF>
                            </DESTINATION-SIGNAL>
                            <TRANSFORMATION>LINEAR_SCALE</TRANSFORMATION>
                            <UPDATE-INDICATION>true</UPDATE-INDICATION>
                        </SIGNAL-GATEWAY>
                    </ELEMENTS>
                </AR-PACKAGE>
                
                <AR-PACKAGE>
                    <SHORT-NAME>Networks</SHORT-NAME>
                    <ELEMENTS>
                        <CAN-CLUSTER>
                            <SHORT-NAME>CAN1</SHORT-NAME>
                            <CAN-CONTROLLER-REF>/Controllers/CanController1</CAN-CONTROLLER-REF>
                        </CAN-CLUSTER>
                        
                        <ETHERNET-CLUSTER>
                            <SHORT-NAME>ETH1</SHORT-NAME>
                            <ETHERNET-CONTROLLER-REF>/Controllers/EthController1</ETHERNET-CONTROLLER-REF>
                            <VLAN-ID>100</VLAN-ID>
                        </ETHERNET-CLUSTER>
                        
                        <LIN-CLUSTER>
                            <SHORT-NAME>LIN1</SHORT-NAME>
                            <LIN-CONTROLLER-REF>/Controllers/LinController1</LIN-CONTROLLER-REF>
                        </LIN-CLUSTER>
                        
                        <FLEXRAY-CLUSTER>
                            <SHORT-NAME>FR1</SHORT-NAME>
                            <FLEXRAY-CONTROLLER-REF>/Controllers/FrController1</FLEXRAY-CONTROLLER-REF>
                        </FLEXRAY-CLUSTER>
                    </ELEMENTS>
                </AR-PACKAGE>
                
                <AR-PACKAGE>
                    <SHORT-NAME>Conversions</SHORT-NAME>
                    <ELEMENTS>
                        <PROTOCOL-CONVERSION>
                            <SHORT-NAME>CanToEthConversion</SHORT-NAME>
                            <SOURCE-PROTOCOL>CAN</SOURCE-PROTOCOL>
                            <DESTINATION-PROTOCOL>ETHERNET</DESTINATION-PROTOCOL>
                            <CONVERSION-TYPE>PDU_MAPPING</CONVERSION-TYPE>
                            <PARAMETER>
                                <SHORT-NAME>MaxLatency</SHORT-NAME>
                                <VALUE>100</VALUE>
                            </PARAMETER>
                        </PROTOCOL-CONVERSION>
                    </ELEMENTS>
                </AR-PACKAGE>
                
                <AR-PACKAGE>
                    <SHORT-NAME>Multicast</SHORT-NAME>
                    <ELEMENTS>
                        <MULTICAST-GROUP>
                            <SHORT-NAME>MulticastGroup1</SHORT-NAME>
                            <GROUP-ADDRESS>239.0.0.1</GROUP-ADDRESS>
                            <PORT>5000</PORT>
                            <MEMBER>
                                <SHORT-NAME>Member1</SHORT-NAME>
                                <IP-ADDRESS>192.168.1.10</IP-ADDRESS>
                            </MEMBER>
                            <MEMBER>
                                <SHORT-NAME>Member2</SHORT-NAME>
                                <IP-ADDRESS>192.168.1.11</IP-ADDRESS>
                            </MEMBER>
                        </MULTICAST-GROUP>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
    @pytest.fixture
    def gateway_document(self, sample_gateway_xml):
        """Create an ARXMLDocument with gateway content."""
        root = ET.fromstring(sample_gateway_xml.encode('utf-8'))
        doc = ARXMLDocument(
            root=root,
            file_path="/test/gateway.arxml",
            namespaces={"ar": "http://autosar.org/schema/r4.0"}
        )
        return doc
        
    def test_analyzer_initialization(self, analyzer):
        """Test GatewayAnalyzer initialization."""
        assert analyzer.analyzer_name == "GatewayAnalyzer"
        assert analyzer.analyzer_version == "1.0.0"
        assert "GATEWAY" in analyzer.supported_arxml_types
        assert "COMMUNICATION" in analyzer.supported_arxml_types
        assert "SYSTEM" in analyzer.supported_arxml_types
        
    def test_can_analyze_gateway_document(self, analyzer, gateway_document):
        """Test can_analyze with gateway document."""
        assert analyzer.can_analyze(gateway_document) is True
        
    def test_can_analyze_non_gateway_document(self, analyzer):
        """Test can_analyze with non-gateway document."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Other</SHORT-NAME>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        root = ET.fromstring(xml_content.encode('utf-8'))
        doc = ARXMLDocument(
            root=root,
            file_path="/test/other.arxml",
            namespaces={"ar": "http://autosar.org/schema/r4.0"}
        )
        assert analyzer.can_analyze(doc) is False
        
    def test_extract_routing_paths(self, analyzer, gateway_document):
        """Test extraction of routing paths."""
        paths = analyzer._extract_routing_paths(gateway_document)
        
        assert len(paths) == 2
        
        # Check first routing path
        assert paths[0].name == "CanToEth_Route"
        assert paths[0].source_pdu == "CanPdu1"
        assert paths[0].destination_pdu == "EthPdu1"
        assert paths[0].source_module == "CanIf"
        assert paths[0].destination_module == "SoAd"
        assert paths[0].routing_type == "IF"
        assert paths[0].gateway_type == "ON_THE_FLY"
        
        # Check second routing path
        assert paths[1].name == "TP_Route"
        assert paths[1].source_pdu == "TpSource"
        assert paths[1].destination_pdu == "TpDest"
        assert paths[1].routing_type == "TP"
        assert paths[1].gateway_type == "FIFO"
        assert paths[1].buffer_size == 4096
        assert paths[1].threshold == 2048
        
    def test_extract_signal_gateways(self, analyzer, gateway_document):
        """Test extraction of signal gateways."""
        gateways = analyzer._extract_signal_gateways(gateway_document)
        
        assert len(gateways) == 1
        assert gateways[0].name == "SignalGw1"
        assert gateways[0].source_signal == "Speed"
        assert gateways[0].destination_signal == "VehicleSpeed"
        assert gateways[0].source_pdu == "CanPdu1"
        assert gateways[0].destination_pdu == "EthPdu1"
        assert gateways[0].transformation == "LINEAR_SCALE"
        assert gateways[0].update_indication is True
        
    def test_extract_network_interfaces(self, analyzer, gateway_document):
        """Test extraction of network interfaces."""
        interfaces = analyzer._extract_network_interfaces(gateway_document)
        
        assert len(interfaces) == 4
        
        # Check CAN interface
        can_if = next(i for i in interfaces if i.interface_type == "CAN")
        assert can_if.name == "CAN1"
        assert can_if.controller_ref == "/Controllers/CanController1"
        assert "CAN" in can_if.supported_protocols
        
        # Check Ethernet interface
        eth_if = next(i for i in interfaces if i.interface_type == "ETHERNET")
        assert eth_if.name == "ETH1"
        assert eth_if.vlan_id == 100
        assert "TCP" in eth_if.supported_protocols
        assert "UDP" in eth_if.supported_protocols
        
        # Check LIN interface
        lin_if = next(i for i in interfaces if i.interface_type == "LIN")
        assert lin_if.name == "LIN1"
        
        # Check FlexRay interface
        fr_if = next(i for i in interfaces if i.interface_type == "FLEXRAY")
        assert fr_if.name == "FR1"
        
    def test_extract_protocol_conversions(self, analyzer, gateway_document):
        """Test extraction of protocol conversions."""
        conversions = analyzer._extract_protocol_conversions(gateway_document)
        
        assert len(conversions) == 1
        assert conversions[0].name == "CanToEthConversion"
        assert conversions[0].source_protocol == "CAN"
        assert conversions[0].destination_protocol == "ETHERNET"
        assert conversions[0].conversion_type == "PDU_MAPPING"
        assert conversions[0].parameters["MaxLatency"] == "100"
        
    def test_extract_multicast_groups(self, analyzer, gateway_document):
        """Test extraction of multicast groups."""
        groups = analyzer._extract_multicast_groups(gateway_document)
        
        assert len(groups) == 1
        assert groups[0]["name"] == "MulticastGroup1"
        assert groups[0]["group_address"] == "239.0.0.1"
        assert groups[0]["port"] == 5000
        assert len(groups[0]["members"]) == 2
        assert groups[0]["members"][0]["name"] == "Member1"
        assert groups[0]["members"][0]["address"] == "192.168.1.10"
        
    def test_analyze_gateway_metrics(self, analyzer):
        """Test gateway metrics analysis."""
        paths = [
            RoutingPath("Path1", "Src1", "Dst1", "Mod1", "Mod2", "IF", "ON_THE_FLY", 1024, None),
            RoutingPath("Path2", "Src2", "Dst2", "Mod1", "Mod3", "TP", "FIFO", 2048, None)
        ]
        
        gateways = [
            SignalGateway("Gw1", "Sig1", "Sig2", "Pdu1", "Pdu2", None, False)
        ]
        
        interfaces = [
            NetworkInterface("CAN1", "CAN", "Ctrl1", "Cluster1", None, ["CAN"]),
            NetworkInterface("ETH1", "ETHERNET", "Ctrl2", "Cluster2", 100, ["TCP", "UDP"])
        ]
        
        metrics = analyzer._analyze_gateway_metrics(paths, gateways, interfaces)
        
        assert metrics["gateway_load"] == 3  # 2 paths + 1 gateway
        assert metrics["routing_distribution"]["IF"] == 1
        assert metrics["routing_distribution"]["TP"] == 1
        assert metrics["network_utilization"]["CAN"] == 1
        assert metrics["network_utilization"]["ETHERNET"] == 1
        assert metrics["total_buffer_size"] == 3072  # 1024 + 2048
        assert metrics["protocol_diversity"] == 3  # CAN, TCP, UDP
        
    def test_analyze_routing_complexity(self, analyzer):
        """Test routing complexity analysis."""
        paths = [
            RoutingPath("Path1", "Src1", "Dst1", "Mod1", "Mod2", "IF", "ON_THE_FLY", None, None),
            RoutingPath("Path2", "Src1", "Dst2", "Mod1", "Mod3", "IF", "ON_THE_FLY", None, None),
            RoutingPath("Path3", "Src2", "Dst1", "Mod2", "Mod3", "IF", "ON_THE_FLY", None, None)
        ]
        
        complexity = analyzer._analyze_routing_complexity(paths)
        
        assert complexity["max_fanout"] == 2  # Src1 has 2 destinations
        assert complexity["max_fanin"] == 2  # Dst1 has 2 sources
        assert complexity["module_transitions"] == 3
        
    def test_validate_gateway_configuration(self, analyzer):
        """Test gateway configuration validation."""
        # Create paths with issues
        paths = [
            RoutingPath("Path1", "Src1", "Dst1", "Mod1", "Mod2", "IF", "ON_THE_FLY", None, None),
            RoutingPath("Path2", "Src1", "Dst1", "Mod1", "Mod2", "IF", "ON_THE_FLY", None, None),  # Duplicate
            RoutingPath("Path3", "Circular", "Circular", "Mod1", "Mod1", "IF", "ON_THE_FLY", None, None),  # Circular
            RoutingPath("Path4", "Src2", "Dst2", "Mod1", "Mod2", "TP", "FIFO", None, None)  # TP without buffer
        ]
        
        gateways = []
        interfaces = [
            NetworkInterface("CAN1", "CAN", "Ctrl1", "Cluster1", None, ["CAN"])
        ]
        
        validation = analyzer._validate_gateway_configuration(paths, gateways, interfaces)
        
        assert len(validation["errors"]) == 2  # Duplicate and circular
        assert len(validation["warnings"]) == 2  # TP without buffer and single interface
        assert "Duplicate routing path" in validation["errors"][0]
        assert "Circular routing" in validation["errors"][1]
        assert "without buffer size" in validation["warnings"][0]
        assert "at least 2 network interfaces" in validation["warnings"][1]
        
    def test_generate_recommendations(self, analyzer):
        """Test recommendation generation."""
        metrics = {
            "gateway_load": 1500,
            "total_buffer_size": 2097152,  # 2MB
            "protocol_diversity": 6
        }
        
        complexity = {
            "max_fanout": 15,
            "routing_hotspots": ["Pdu1", "Pdu2"]
        }
        
        validation = {
            "errors": ["Error1"],
            "warnings": []
        }
        
        recommendations = analyzer._generate_recommendations(metrics, complexity, validation)
        
        assert any("High gateway load" in r for r in recommendations)
        assert any("High routing fan-out" in r for r in recommendations)
        assert any("Routing hotspots" in r for r in recommendations)
        assert any("Large total buffer size" in r for r in recommendations)
        assert any("Critical configuration errors" in r for r in recommendations)
        assert any("High protocol diversity" in r for r in recommendations)
        
    def test_performance_metrics(self, analyzer):
        """Test performance metrics calculation."""
        paths = [
            RoutingPath("Path1", "Src1", "Dst1", "Mod1", "Mod2", "IF", "ON_THE_FLY", None, None),
            RoutingPath("Path2", "Src2", "Dst2", "Mod1", "Mod2", "TP", "FIFO", 1024, None)
        ]
        
        gateways = [
            SignalGateway("Gw1", "Sig1", "Sig2", "Pdu1", "Pdu2", None, False)
        ]
        
        metrics = analyzer._calculate_performance_metrics(paths, gateways)
        
        assert "estimated_latency" in metrics
        assert "estimated_throughput" in metrics
        assert "routing_efficiency" in metrics
        assert "buffer_efficiency" in metrics
        assert metrics["routing_efficiency"] == 50.0  # 1 ON_THE_FLY out of 2
        
    def test_full_analysis(self, analyzer, gateway_document):
        """Test full gateway analysis."""
        result = analyzer.analyze(gateway_document)
        
        # Check result structure
        assert isinstance(result, AnalysisResult)
        assert result.metadata.analyzer_name == "GatewayAnalyzer"
        assert result.metadata.status == AnalysisStatus.WARNING  # Due to validation warnings
        
        # Check summary
        assert result.summary["total_routing_paths"] == 2
        assert result.summary["total_signal_gateways"] == 1
        assert result.summary["total_network_interfaces"] == 4
        assert result.summary["total_protocol_conversions"] == 1
        assert result.summary["total_multicast_groups"] == 1
        
        # Check details
        assert "routing_paths" in result.details
        assert "signal_gateways" in result.details
        assert "network_interfaces" in result.details
        assert "protocol_conversions" in result.details
        assert "multicast_groups" in result.details
        assert "gateway_metrics" in result.details
        assert "routing_complexity" in result.details
        assert "validation_results" in result.details
        
        # Check statistics
        assert "routing_statistics" in result.statistics
        assert "signal_statistics" in result.statistics
        assert "network_statistics" in result.statistics
        assert "performance_metrics" in result.statistics
        
        # Check patterns
        assert "routing_path_pattern" in result.patterns
        assert "signal_gateway_pattern" in result.patterns
        
        # Check recommendations
        assert len(result.recommendations) > 0
        
    def test_get_patterns(self, analyzer):
        """Test get_patterns method."""
        patterns = analyzer.get_patterns()
        
        assert len(patterns) > 0
        assert any(p["name"] == "routing_paths" for p in patterns)
        assert any(p["name"] == "signal_gateways" for p in patterns)
        assert any(p["name"] == "multicast_groups" for p in patterns)
        assert any(p["name"] == "protocol_conversions" for p in patterns)
        assert any(p["name"] == "network_clusters" for p in patterns)
        assert any(p["name"] == "gateway_modules" for p in patterns)
        
        # Check pattern structure
        for pattern in patterns:
            assert "name" in pattern
            assert "type" in pattern
            assert "xpath" in pattern
            assert "description" in pattern
            assert pattern["type"] == PatternType.XPATH
            
    def test_error_handling(self, analyzer):
        """Test error handling in analysis."""
        # Create document that will cause parsing error
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <INVALID>
        </AUTOSAR>"""
        
        # This XML is actually well-formed, so we need a different approach
        # Mock the document to raise an exception
        doc = Mock(spec=ARXMLDocument)
        doc.file_path = "/test/error.arxml"
        doc.get_file_size.return_value = 100
        doc.xpath.side_effect = Exception("Parsing error")
        
        with pytest.raises(AnalysisError) as exc_info:
            analyzer.analyze(doc)
            
        assert "Gateway analysis failed" in str(exc_info.value)
        
    def test_safe_int_conversion(self, analyzer):
        """Test safe integer conversion."""
        assert analyzer._safe_int("123") == 123
        assert analyzer._safe_int("0") == 0
        assert analyzer._safe_int("-456") == -456
        assert analyzer._safe_int(None) is None
        assert analyzer._safe_int("") is None
        assert analyzer._safe_int("not_a_number") is None
        assert analyzer._safe_int("12.34") is None
        
    def test_data_class_conversions(self, analyzer):
        """Test conversion of data classes to dictionaries."""
        # Test RoutingPath conversion
        path = RoutingPath("Path1", "Src1", "Dst1", "Mod1", "Mod2", "IF", "ON_THE_FLY", 1024, 512)
        path_dict = analyzer._routing_path_to_dict(path)
        assert path_dict["name"] == "Path1"
        assert path_dict["source_pdu"] == "Src1"
        assert path_dict["buffer_size"] == 1024
        
        # Test SignalGateway conversion
        gateway = SignalGateway("Gw1", "Sig1", "Sig2", "Pdu1", "Pdu2", "SCALE", True)
        gw_dict = analyzer._signal_gateway_to_dict(gateway)
        assert gw_dict["name"] == "Gw1"
        assert gw_dict["transformation"] == "SCALE"
        assert gw_dict["update_indication"] is True
        
        # Test NetworkInterface conversion
        interface = NetworkInterface("ETH1", "ETHERNET", "Ctrl1", "Cluster1", 100, ["TCP", "UDP"])
        if_dict = analyzer._network_interface_to_dict(interface)
        assert if_dict["name"] == "ETH1"
        assert if_dict["vlan_id"] == 100
        assert "TCP" in if_dict["supported_protocols"]
        
        # Test ProtocolConversion conversion
        conversion = ProtocolConversion("Conv1", "CAN", "ETH", "MAPPING", {"key": "value"})
        conv_dict = analyzer._protocol_conversion_to_dict(conversion)
        assert conv_dict["name"] == "Conv1"
        assert conv_dict["parameters"]["key"] == "value"