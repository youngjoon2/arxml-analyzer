"""
Unit tests for DiagnosticAnalyzer.
"""

import pytest
from pathlib import Path
from datetime import datetime
from lxml import etree as ET

from arxml_analyzer.analyzers.diagnostic_analyzer import (
    DiagnosticAnalyzer,
    DiagnosticService,
    DiagnosticTroubleCode,
    DiagnosticProtocol,
    DiagnosticSession,
    SecurityAccessLevel
)
from arxml_analyzer.models.arxml_document import ARXMLDocument
from arxml_analyzer.core.analyzer.base_analyzer import AnalysisStatus


class TestDiagnosticAnalyzer:
    """Test cases for DiagnosticAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a DiagnosticAnalyzer instance."""
        return DiagnosticAnalyzer()
    
    @pytest.fixture
    def dcm_document(self):
        """Create a sample DCM ARXML document."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>ArcCore</SHORT-NAME>
                    <AR-PACKAGES>
                        <AR-PACKAGE>
                            <SHORT-NAME>EcucDefs</SHORT-NAME>
                            <ELEMENTS>
                                <ECUC-MODULE-DEF>
                                    <SHORT-NAME>Dcm</SHORT-NAME>
                                    <DESC>
                                        <L-2 L="EN">Diagnostic Communication Manager configuration</L-2>
                                    </DESC>
                                    <CONTAINERS>
                                        <ECUC-PARAM-CONF-CONTAINER-DEF>
                                            <SHORT-NAME>DcmDsdServiceTable</SHORT-NAME>
                                            <LOWER-MULTIPLICITY>1</LOWER-MULTIPLICITY>
                                            <UPPER-MULTIPLICITY>256</UPPER-MULTIPLICITY>
                                            <SUB-CONTAINERS>
                                                <ECUC-PARAM-CONF-CONTAINER-DEF>
                                                    <SHORT-NAME>ReadDataByIdentifierService</SHORT-NAME>
                                                    <PARAMETERS>
                                                        <ECUC-INTEGER-PARAM-DEF>
                                                            <SHORT-NAME>DcmDsdServiceId</SHORT-NAME>
                                                            <DEFAULT-VALUE>0x22</DEFAULT-VALUE>
                                                        </ECUC-INTEGER-PARAM-DEF>
                                                    </PARAMETERS>
                                                    <SUB-CONTAINERS>
                                                        <ECUC-PARAM-CONF-CONTAINER-DEF>
                                                            <SHORT-NAME>SubService1</SHORT-NAME>
                                                        </ECUC-PARAM-CONF-CONTAINER-DEF>
                                                    </SUB-CONTAINERS>
                                                    <REFERENCES>
                                                        <ECUC-REFERENCE-DEF>
                                                            <SHORT-NAME>DcmDsdServiceSecurityLevelRef</SHORT-NAME>
                                                            <DEFAULT-VALUE>SecurityLevel1</DEFAULT-VALUE>
                                                        </ECUC-REFERENCE-DEF>
                                                        <ECUC-REFERENCE-DEF>
                                                            <SHORT-NAME>DcmDsdServiceSessionRef</SHORT-NAME>
                                                            <DEFAULT-VALUE>ExtendedSession</DEFAULT-VALUE>
                                                        </ECUC-REFERENCE-DEF>
                                                    </REFERENCES>
                                                </ECUC-PARAM-CONF-CONTAINER-DEF>
                                            </SUB-CONTAINERS>
                                        </ECUC-PARAM-CONF-CONTAINER-DEF>
                                        <ECUC-PARAM-CONF-CONTAINER-DEF>
                                            <SHORT-NAME>DcmDslProtocol</SHORT-NAME>
                                            <PARAMETERS>
                                                <ECUC-FLOAT-PARAM-DEF>
                                                    <SHORT-NAME>DcmDslProtocolP2ServerMax</SHORT-NAME>
                                                    <DEFAULT-VALUE>50.0</DEFAULT-VALUE>
                                                </ECUC-FLOAT-PARAM-DEF>
                                                <ECUC-INTEGER-PARAM-DEF>
                                                    <SHORT-NAME>DcmDslProtocolBufferSize</SHORT-NAME>
                                                    <DEFAULT-VALUE>4096</DEFAULT-VALUE>
                                                </ECUC-INTEGER-PARAM-DEF>
                                            </PARAMETERS>
                                        </ECUC-PARAM-CONF-CONTAINER-DEF>
                                        <ECUC-PARAM-CONF-CONTAINER-DEF>
                                            <SHORT-NAME>DefaultSession</SHORT-NAME>
                                            <PARAMETERS>
                                                <ECUC-INTEGER-PARAM-DEF>
                                                    <SHORT-NAME>DcmDspSessionId</SHORT-NAME>
                                                    <DEFAULT-VALUE>0x01</DEFAULT-VALUE>
                                                </ECUC-INTEGER-PARAM-DEF>
                                                <ECUC-FLOAT-PARAM-DEF>
                                                    <SHORT-NAME>DcmDspSessionP2ServerMax</SHORT-NAME>
                                                    <DEFAULT-VALUE>50.0</DEFAULT-VALUE>
                                                </ECUC-FLOAT-PARAM-DEF>
                                            </PARAMETERS>
                                        </ECUC-PARAM-CONF-CONTAINER-DEF>
                                        <ECUC-PARAM-CONF-CONTAINER-DEF>
                                            <SHORT-NAME>SecurityLevel1</SHORT-NAME>
                                            <PARAMETERS>
                                                <ECUC-INTEGER-PARAM-DEF>
                                                    <SHORT-NAME>DcmDspSecurityLevelId</SHORT-NAME>
                                                    <DEFAULT-VALUE>1</DEFAULT-VALUE>
                                                </ECUC-INTEGER-PARAM-DEF>
                                                <ECUC-INTEGER-PARAM-DEF>
                                                    <SHORT-NAME>DcmDspSecuritySeedSize</SHORT-NAME>
                                                    <DEFAULT-VALUE>4</DEFAULT-VALUE>
                                                </ECUC-INTEGER-PARAM-DEF>
                                                <ECUC-INTEGER-PARAM-DEF>
                                                    <SHORT-NAME>DcmDspSecurityKeySize</SHORT-NAME>
                                                    <DEFAULT-VALUE>4</DEFAULT-VALUE>
                                                </ECUC-INTEGER-PARAM-DEF>
                                            </PARAMETERS>
                                        </ECUC-PARAM-CONF-CONTAINER-DEF>
                                    </CONTAINERS>
                                </ECUC-MODULE-DEF>
                            </ELEMENTS>
                        </AR-PACKAGE>
                    </AR-PACKAGES>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        root = ET.fromstring(xml_content.encode())
        return ARXMLDocument(
            root=root,
            file_path="test_dcm.arxml",
            namespaces={"ar": "http://autosar.org/schema/r4.0"}
        )
    
    @pytest.fixture
    def dem_document(self):
        """Create a sample DEM ARXML document."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>ArcCore</SHORT-NAME>
                    <ELEMENTS>
                        <ECUC-MODULE-DEF>
                            <SHORT-NAME>Dem</SHORT-NAME>
                            <DESC>
                                <L-2 L="EN">Diagnostic Event Manager configuration</L-2>
                            </DESC>
                            <CONTAINERS>
                                <ECUC-PARAM-CONF-CONTAINER-DEF>
                                    <SHORT-NAME>DemDtc1</SHORT-NAME>
                                    <PARAMETERS>
                                        <ECUC-INTEGER-PARAM-DEF>
                                            <SHORT-NAME>DemDtcNumber</SHORT-NAME>
                                            <DEFAULT-VALUE>0x123456</DEFAULT-VALUE>
                                        </ECUC-INTEGER-PARAM-DEF>
                                        <ECUC-ENUMERATION-PARAM-DEF>
                                            <SHORT-NAME>DemDtcSeverity</SHORT-NAME>
                                            <DEFAULT-VALUE>HIGH</DEFAULT-VALUE>
                                        </ECUC-ENUMERATION-PARAM-DEF>
                                        <ECUC-INTEGER-PARAM-DEF>
                                            <SHORT-NAME>DemEventFailureThreshold</SHORT-NAME>
                                            <DEFAULT-VALUE>3</DEFAULT-VALUE>
                                        </ECUC-INTEGER-PARAM-DEF>
                                        <ECUC-INTEGER-PARAM-DEF>
                                            <SHORT-NAME>DemDtcPriority</SHORT-NAME>
                                            <DEFAULT-VALUE>1</DEFAULT-VALUE>
                                        </ECUC-INTEGER-PARAM-DEF>
                                    </PARAMETERS>
                                    <REFERENCES>
                                        <ECUC-REFERENCE-DEF>
                                            <SHORT-NAME>DemEventRef</SHORT-NAME>
                                            <DEFAULT-VALUE>DemEvent1</DEFAULT-VALUE>
                                        </ECUC-REFERENCE-DEF>
                                    </REFERENCES>
                                </ECUC-PARAM-CONF-CONTAINER-DEF>
                                <ECUC-PARAM-CONF-CONTAINER-DEF>
                                    <SHORT-NAME>DemEventParameter</SHORT-NAME>
                                </ECUC-PARAM-CONF-CONTAINER-DEF>
                            </CONTAINERS>
                        </ECUC-MODULE-DEF>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        root = ET.fromstring(xml_content.encode())
        return ARXMLDocument(
            root=root,
            file_path="test_dem.arxml",
            namespaces={"ar": "http://autosar.org/schema/r4.0"}
        )
    
    @pytest.fixture
    def diagnostic_document(self):
        """Create a sample diagnostic ARXML document."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR xmlns="http://autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>DiagnosticPackage</SHORT-NAME>
                    <ELEMENTS>
                        <DIAGNOSTIC-SERVICE>
                            <SHORT-NAME>ReadDataByIdentifier</SHORT-NAME>
                            <SERVICE-ID>0x22</SERVICE-ID>
                        </DIAGNOSTIC-SERVICE>
                        <DIAGNOSTIC-SERVICE>
                            <SHORT-NAME>WriteDataByIdentifier</SHORT-NAME>
                            <SERVICE-ID>0x2E</SERVICE-ID>
                        </DIAGNOSTIC-SERVICE>
                        <DIAGNOSTIC-TROUBLE-CODE>
                            <SHORT-NAME>DTC_PowerSupplyLow</SHORT-NAME>
                            <TROUBLE-CODE>P0562</TROUBLE-CODE>
                            <SEVERITY>MEDIUM</SEVERITY>
                        </DIAGNOSTIC-TROUBLE-CODE>
                        <DIAGNOSTIC-PROTOCOL>
                            <SHORT-NAME>UDS_Protocol</SHORT-NAME>
                            <PROTOCOL-KIND>UDS</PROTOCOL-KIND>
                        </DIAGNOSTIC-PROTOCOL>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        
        root = ET.fromstring(xml_content.encode())
        return ARXMLDocument(
            root=root,
            file_path="test_diagnostic.arxml",
            namespaces={"ar": "http://autosar.org/schema/r4.0"}
        )
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.analyzer_name == "DiagnosticAnalyzer"
        assert "DIAGNOSTIC" in analyzer.supported_types
        assert "ECUC" in analyzer.supported_types
        assert "BSW" in analyzer.supported_types
    
    def test_can_analyze_dcm_document(self, analyzer, dcm_document):
        """Test if analyzer can handle DCM documents."""
        assert analyzer.can_analyze(dcm_document) is True
    
    def test_can_analyze_dem_document(self, analyzer, dem_document):
        """Test if analyzer can handle DEM documents."""
        assert analyzer.can_analyze(dem_document) is True
    
    def test_can_analyze_diagnostic_document(self, analyzer, diagnostic_document):
        """Test if analyzer can handle diagnostic documents."""
        assert analyzer.can_analyze(diagnostic_document) is True
    
    def test_extract_dcm_configuration(self, analyzer, dcm_document):
        """Test DCM configuration extraction."""
        dcm_config = analyzer.extract_dcm_configuration(dcm_document)
        
        assert "Dcm" in dcm_config
        assert dcm_config["Dcm"]["module_name"] == "Dcm"
        assert "Diagnostic Communication Manager" in dcm_config["Dcm"]["description"]
        assert len(dcm_config["Dcm"]["containers"]) > 0
    
    def test_extract_dem_configuration(self, analyzer, dem_document):
        """Test DEM configuration extraction."""
        dem_config = analyzer.extract_dem_configuration(dem_document)
        
        assert "Dem" in dem_config
        assert dem_config["Dem"]["module_name"] == "Dem"
        assert "Diagnostic Event Manager" in dem_config["Dem"]["description"]
    
    def test_extract_diagnostic_services(self, analyzer, diagnostic_document):
        """Test diagnostic service extraction."""
        services = analyzer.extract_diagnostic_services(diagnostic_document)
        
        assert len(services) == 2
        assert services[0].service_id == "0x22"
        assert services[0].service_name == "ReadDataByIdentifier"
        assert services[1].service_id == "0x2E"
        assert services[1].service_name == "WriteDataByIdentifier"
    
    def test_extract_dtc_configuration(self, analyzer, diagnostic_document):
        """Test DTC extraction."""
        dtcs = analyzer.extract_dtc_configuration(diagnostic_document)
        
        assert len(dtcs) == 1
        assert dtcs[0].dtc_number == "P0562"
        assert dtcs[0].dtc_name == "DTC_PowerSupplyLow"
        assert dtcs[0].severity == "MEDIUM"
    
    def test_extract_diagnostic_protocols(self, analyzer, diagnostic_document):
        """Test diagnostic protocol extraction."""
        protocols = analyzer.extract_diagnostic_protocols(diagnostic_document)
        
        assert len(protocols) == 1
        assert protocols[0].protocol_name == "UDS_Protocol"
        assert protocols[0].protocol_type == "UDS"
    
    def test_analyze_service_metrics(self, analyzer):
        """Test service metrics analysis."""
        services = [
            DiagnosticService(
                service_id="0x22",
                service_name="ReadData",
                service_type="READ_DATA",
                sub_functions=["Sub1", "Sub2"],
                security_level="Level1",
                session_types=["Extended"]
            ),
            DiagnosticService(
                service_id="0x2E",
                service_name="WriteData",
                service_type="WRITE_DATA"
            )
        ]
        
        metrics = analyzer.analyze_service_metrics(services)
        
        assert metrics["total_services"] == 2
        assert metrics["services_with_subfunctions"] == 1
        assert metrics["secured_services"] == 1
        assert metrics["session_restricted_services"] == 1
        assert metrics["average_subfunctions"] == 1.0
    
    def test_analyze_dtc_metrics(self, analyzer):
        """Test DTC metrics analysis."""
        dtcs = [
            DiagnosticTroubleCode(
                dtc_number="P0562",
                dtc_name="PowerLow",
                severity="HIGH",
                event_name="Event1",
                failure_threshold=3,
                priority=1,
                aging_cycles=10
            ),
            DiagnosticTroubleCode(
                dtc_number="P0563",
                dtc_name="PowerHigh",
                severity="MEDIUM"
            )
        ]
        
        metrics = analyzer.analyze_dtc_metrics(dtcs)
        
        assert metrics["total_dtcs"] == 2
        assert metrics["dtcs_with_events"] == 1
        assert metrics["dtcs_with_thresholds"] == 1
        assert metrics["severity_distribution"]["HIGH"] == 1
        assert metrics["severity_distribution"]["MEDIUM"] == 1
        assert metrics["dtcs_with_priority"] == 1
    
    def test_analyze_protocol_metrics(self, analyzer):
        """Test protocol metrics analysis."""
        protocols = [
            DiagnosticProtocol(
                protocol_name="UDS_Main",
                protocol_type="UDS",
                buffer_size=4096
            ),
            DiagnosticProtocol(
                protocol_name="KWP_Legacy",
                protocol_type="KWP2000"
            )
        ]
        
        metrics = analyzer.analyze_protocol_metrics(protocols)
        
        assert metrics["total_protocols"] == 2
        assert metrics["protocol_types"]["UDS"] == 1
        assert metrics["protocol_types"]["KWP2000"] == 1
        assert metrics["protocols_with_buffers"] == 1
    
    def test_analyze_session_metrics(self, analyzer):
        """Test session metrics analysis."""
        sessions = [
            DiagnosticSession(
                session_id="0x01",
                session_name="Default",
                session_type="DEFAULT",
                p2_server_max=50.0
            ),
            DiagnosticSession(
                session_id="0x03",
                session_name="Extended",
                session_type="EXTENDED",
                allowed_services=["0x22", "0x2E"]
            )
        ]
        
        metrics = analyzer.analyze_session_metrics(sessions)
        
        assert metrics["total_sessions"] == 2
        assert metrics["session_types"]["DEFAULT"] == 1
        assert metrics["session_types"]["EXTENDED"] == 1
        assert metrics["sessions_with_timing"] == 1
        assert metrics["sessions_with_service_restrictions"] == 1
    
    def test_analyze_security_metrics(self, analyzer):
        """Test security metrics analysis."""
        security_levels = [
            SecurityAccessLevel(
                level_id="1",
                level_name="Level1",
                seed_size=4,
                key_size=4,
                delay_time=1000.0,
                max_attempts=3
            ),
            SecurityAccessLevel(
                level_id="2",
                level_name="Level2",
                seed_size=8,
                key_size=8
            )
        ]
        
        metrics = analyzer.analyze_security_metrics(security_levels)
        
        assert metrics["total_security_levels"] == 2
        assert metrics["levels_with_delay"] == 1
        assert metrics["levels_with_max_attempts"] == 1
        assert metrics["average_seed_size"] == 6.0
        assert metrics["average_key_size"] == 6.0
    
    def test_validate_diagnostic_configuration(self, analyzer):
        """Test diagnostic configuration validation."""
        services = [
            DiagnosticService("0x22", "ReadData", "READ_DATA"),
            DiagnosticService("0x22", "ReadDataDup", "READ_DATA")  # Duplicate ID
        ]
        
        dtcs = [
            DiagnosticTroubleCode("P0562", "PowerLow"),
            DiagnosticTroubleCode("P0562", "PowerLowDup")  # Duplicate DTC
        ]
        
        protocols = [DiagnosticProtocol("Protocol1", "UDS")]
        sessions = [DiagnosticSession("0x01", "Default", "DEFAULT")]
        security_levels = [
            SecurityAccessLevel("1", "Level1", seed_size=4, key_size=2)  # Key < Seed
        ]
        
        validation = analyzer.validate_diagnostic_configuration(
            services, dtcs, protocols, sessions, security_levels
        )
        
        assert validation["is_valid"] is False
        assert len(validation["issues"]) == 2  # Duplicate service ID and DTC
        assert len(validation["warnings"]) > 0
    
    def test_full_analysis(self, analyzer, dcm_document):
        """Test full diagnostic analysis."""
        result = analyzer.analyze(dcm_document)
        
        assert result.metadata.analyzer_name == "DiagnosticAnalyzer"
        assert result.metadata.status == AnalysisStatus.COMPLETED
        assert result.metadata.arxml_type == "DIAGNOSTIC"
        
        assert "dcm_modules" in result.summary
        assert "diagnostic_services" in result.summary
        assert "validation_issues" in result.summary
        
        assert "dcm_configuration" in result.details
        assert "services" in result.details
        assert "metrics" in result.details
        assert "validation" in result.details
        
        assert result.statistics is not None
        assert result.patterns is not None
        assert result.recommendations is not None
    
    def test_get_patterns(self, analyzer):
        """Test pattern definitions."""
        patterns = analyzer.get_patterns()
        
        assert len(patterns) > 0
        assert any(p["description"] == "DCM module definitions" for p in patterns)
        assert any(p["description"] == "DEM module definitions" for p in patterns)
        assert any(p["description"] == "Diagnostic service definitions" for p in patterns)
        assert all(p["type"] == "XPATH" for p in patterns)