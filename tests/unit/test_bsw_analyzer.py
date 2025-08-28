"""BSWAnalyzer 단위 테스트"""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

from arxml_analyzer.analyzers.bsw_analyzer import (
    BSWAnalyzer,
    BSWModule,
    BSWInterface,
    BSWService,
    BSWConfiguration
)
from arxml_analyzer.core.analyzer.base_analyzer import AnalysisResult, AnalysisMetadata
from arxml_analyzer.core.analyzer.pattern_finder import PatternType


class TestBSWAnalyzer:
    """BSWAnalyzer 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        """테스트용 analyzer 인스턴스"""
        return BSWAnalyzer()
    
    @pytest.fixture
    def sample_bsw_xml(self):
        """테스트용 BSW XML 데이터"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR>
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <ELEMENTS>
                        <ECUC-MODULE-DEF UUID="test-uuid-ecum">
                            <SHORT-NAME>EcuM</SHORT-NAME>
                            <DESC>
                                <L-2>ECU State Manager</L-2>
                            </DESC>
                            <MODULE-ID>10</MODULE-ID>
                            <ECUC-PARAM-CONF-CONTAINER-DEF>
                                <SHORT-NAME>EcuMGeneral</SHORT-NAME>
                                <ECUC-BOOLEAN-PARAM-DEF>
                                    <SHORT-NAME>EcuMDevErrorDetect</SHORT-NAME>
                                    <DEFAULT-VALUE>true</DEFAULT-VALUE>
                                </ECUC-BOOLEAN-PARAM-DEF>
                                <ECUC-INTEGER-PARAM-DEF>
                                    <SHORT-NAME>EcuMMainFunctionPeriod</SHORT-NAME>
                                    <MIN>1</MIN>
                                    <MAX>1000</MAX>
                                    <DEFAULT-VALUE>10</DEFAULT-VALUE>
                                </ECUC-INTEGER-PARAM-DEF>
                            </ECUC-PARAM-CONF-CONTAINER-DEF>
                        </ECUC-MODULE-DEF>
                        
                        <BSW-MODULE-DESCRIPTION>
                            <SHORT-NAME>NvM</SHORT-NAME>
                            <MODULE-ID>20</MODULE-ID>
                            <PROVIDED-INTERFACE>
                                <SHORT-NAME>NvM_Service</SHORT-NAME>
                                <OPERATION>
                                    <SHORT-NAME>ReadBlock</SHORT-NAME>
                                </OPERATION>
                                <OPERATION>
                                    <SHORT-NAME>WriteBlock</SHORT-NAME>
                                </OPERATION>
                            </PROVIDED-INTERFACE>
                            <REQUIRED-INTERFACE>
                                <SHORT-NAME>MemIf_Service</SHORT-NAME>
                            </REQUIRED-INTERFACE>
                        </BSW-MODULE-DESCRIPTION>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
            
            <BSW-MODULE-ENTRY>
                <SHORT-NAME>EcuM_MainFunction</SHORT-NAME>
                <SERVICE-ID>0x00</SERVICE-ID>
                <IS-SYNCHRONOUS>true</IS-SYNCHRONOUS>
                <IS-REENTRANT>false</IS-REENTRANT>
                <MODULE-NAME>EcuM</MODULE-NAME>
            </BSW-MODULE-ENTRY>
            
            <BSW-SCHEDULABLE-ENTITY>
                <SHORT-NAME>NvM_MainFunction</SHORT-NAME>
                <CAN-INTERRUPT>false</CAN-INTERRUPT>
                <EXCLUSIVE-AREA-REF DEST="EXCLUSIVE-AREA">NvM_ExclusiveArea</EXCLUSIVE-AREA-REF>
            </BSW-SCHEDULABLE-ENTITY>
            
            <BSW-MODULE-DEPENDENCY>
                <MODULE-NAME>NvM</MODULE-NAME>
                <REQUIRED-MODULE-REF>MemIf</REQUIRED-MODULE-REF>
            </BSW-MODULE-DEPENDENCY>
        </AUTOSAR>"""
        return ET.fromstring(xml_content)
    
    @pytest.fixture
    def sample_bsw_service_xml(self):
        """테스트용 BSW 서비스 XML"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR>
            <BSW-SERVICE-DEPENDENCY>
                <SHORT-NAME>Dcm_Service</SHORT-NAME>
                <SERVICE-KIND>DIAGNOSTIC</SERVICE-KIND>
                <ASSIGNED-CONTROLLER-REF>DcmController</ASSIGNED-CONTROLLER-REF>
                <SERVICE-POINT>
                    <SHORT-NAME>ReadDataByIdentifier</SHORT-NAME>
                </SERVICE-POINT>
                <SERVICE-POINT>
                    <SHORT-NAME>WriteDataByIdentifier</SHORT-NAME>
                </SERVICE-POINT>
            </BSW-SERVICE-DEPENDENCY>
            
            <BSW-CALLED-ENTITY>
                <SHORT-NAME>Com_MainFunctionTx</SHORT-NAME>
                <MINIMUM-START-INTERVAL>0.01</MINIMUM-START-INTERVAL>
                <IMPLEMENTED-ENTRY-REF>Com_MainFunctionTx_Entry</IMPLEMENTED-ENTRY-REF>
            </BSW-CALLED-ENTITY>
        </AUTOSAR>"""
        return ET.fromstring(xml_content)
    
    def test_analyzer_initialization(self, analyzer):
        """analyzer 초기화 테스트"""
        assert analyzer.type_identifier == "BSW"
        assert analyzer.name == "BSWAnalyzer"
        assert "System" in analyzer.module_categories
        assert "Memory" in analyzer.module_categories
        assert "EcuM" in analyzer.module_categories["System"]
        assert "NvM" in analyzer.module_categories["Memory"]
    
    def test_can_analyze_bsw_document(self, analyzer, sample_bsw_xml):
        """BSW 문서 분석 가능 여부 테스트"""
        assert analyzer.can_analyze(sample_bsw_xml) is True
    
    def test_can_analyze_non_bsw_document(self, analyzer):
        """비BSW 문서 분석 불가 테스트"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR>
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>Other</SHORT-NAME>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>"""
        root = ET.fromstring(xml_content)
        assert analyzer.can_analyze(root) is False
    
    def test_get_patterns(self, analyzer):
        """패턴 반환 테스트"""
        patterns = analyzer.get_patterns()
        
        assert PatternType.XPATH in patterns
        assert PatternType.REFERENCE in patterns
        
        # BSW 관련 패턴 확인
        assert any("BSW-MODULE-DESCRIPTION" in p for p in patterns[PatternType.XPATH])
        assert any("BSW-MODULE-ENTRY" in p for p in patterns[PatternType.XPATH])
        assert any("MODULE-REF" in p for p in patterns[PatternType.REFERENCE])
    
    def test_analyze_bsw_modules(self, analyzer, sample_bsw_xml):
        """BSW 모듈 분석 테스트"""
        result = analyzer.analyze(sample_bsw_xml)
        
        assert result is not None
        assert "modules" in result.details
        
        modules = result.details["modules"]
        assert len(modules) >= 2  # EcuM and NvM
        
        # EcuM 모듈 확인
        ecum = next((m for m in modules if m.get("name") == "EcuM"), None)
        assert ecum is not None
        assert ecum["type"] == "System"
        assert ecum["module_id"] == "10"
        
        # NvM 모듈 확인
        nvm = next((m for m in modules if m.get("name") == "NvM"), None)
        assert nvm is not None
        assert nvm["type"] == "Memory"
        assert nvm["module_id"] == "20"
    
    def test_analyze_bsw_interfaces(self, analyzer, sample_bsw_xml):
        """BSW 인터페이스 분석 테스트"""
        result = analyzer.analyze(sample_bsw_xml)
        
        assert "interfaces" in result.details
        interfaces = result.details["interfaces"]
        
        # Provided interface 확인
        provided = [i for i in interfaces if i.get("type") == "PROVIDED"]
        assert len(provided) > 0
        
        nvm_service = next((i for i in provided if i.get("name") == "NvM_Service"), None)
        assert nvm_service is not None
        assert "ReadBlock" in nvm_service["operations"]
        assert "WriteBlock" in nvm_service["operations"]
        
        # Required interface 확인
        required = [i for i in interfaces if i.get("type") == "REQUIRED"]
        assert len(required) > 0
    
    def test_analyze_bsw_services(self, analyzer, sample_bsw_service_xml):
        """BSW 서비스 분석 테스트"""
        result = analyzer.analyze(sample_bsw_service_xml)
        
        assert "services" in result.details
        services = result.details["services"]
        assert len(services) >= 2
        
        # Service dependency 확인
        dcm_service = next((s for s in services if s.get("name") == "Dcm_Service"), None)
        assert dcm_service is not None
        assert dcm_service["type"] == "DIAGNOSTIC"
        assert len(dcm_service["service_points"]) == 2
        
        # Called entity 확인
        com_entity = next((s for s in services if s.get("name") == "Com_MainFunctionTx"), None)
        assert com_entity is not None
        assert com_entity["type"] == "CALLED_ENTITY"
    
    def test_analyze_bsw_configurations(self, analyzer, sample_bsw_xml):
        """BSW 구성 분석 테스트"""
        result = analyzer.analyze(sample_bsw_xml)
        
        assert "configurations" in result.details
        configs = result.details["configurations"]
        assert len(configs) >= 2
        
        # Boolean parameter 확인
        bool_param = next((c for c in configs if c.get("parameter") == "EcuMDevErrorDetect"), None)
        assert bool_param is not None
        assert bool_param["type"] == "BOOLEAN"
        assert bool_param["default_value"] == "true"
        
        # Integer parameter 확인  
        int_param = next((c for c in configs if c.get("parameter") == "EcuMMainFunctionPeriod"), None)
        assert int_param is not None
        assert int_param["type"] == "INTEGER"
        assert int_param["min"] == "1"
        assert int_param["max"] == "1000"
    
    def test_analyze_bsw_dependencies(self, analyzer, sample_bsw_xml):
        """BSW 의존성 분석 테스트"""
        result = analyzer.analyze(sample_bsw_xml)
        
        assert "dependencies" in result.details
        deps = result.details["dependencies"]
        
        # NvM -> MemIf 의존성 확인
        assert "NvM" in deps
        assert "MemIf" in deps["NvM"]
    
    def test_calculate_bsw_metrics(self, analyzer):
        """BSW 메트릭 계산 테스트"""
        details = {
            "modules": [
                {"name": "EcuM", "type": "System"},
                {"name": "BswM", "type": "System"},
                {"name": "NvM", "type": "Memory"},
                {"name": "Com", "type": "Communication"}
            ],
            "interfaces": [
                {"type": "PROVIDED"},
                {"type": "PROVIDED"},
                {"type": "REQUIRED"}
            ],
            "services": [{"name": "service1"}],
            "configurations": [{"name": "config1"}, {"name": "config2"}],
            "dependencies": {
                "NvM": ["MemIf"],
                "Com": ["PduR"]
            }
        }
        
        metrics = analyzer._calculate_bsw_metrics(details)
        
        assert metrics["total_modules"] == 4
        assert metrics["total_interfaces"] == 3
        assert metrics["total_services"] == 1
        assert metrics["total_configurations"] == 2
        assert metrics["module_categories"]["System"] == 2
        assert metrics["module_categories"]["Memory"] == 1
        assert metrics["module_categories"]["Communication"] == 1
        assert 0 <= metrics["interface_balance"] <= 1
        assert metrics["dependency_depth"] > 0
    
    def test_validate_bsw_configuration(self, analyzer):
        """BSW 구성 검증 테스트"""
        metadata = AnalysisMetadata(analyzer_name="TestAnalyzer")
        result = AnalysisResult(metadata=metadata)
        result.details = {
            "modules": [
                {"name": "Module1", "type": "System"},
                {"name": "Module1", "type": "System"},  # 중복
                {"name": "UnknownModule", "type": "Unknown"}  # 알 수 없는 타입
            ],
            "interfaces": [
                {"name": "Interface1", "type": "PROVIDED"},
                {"name": "Interface2", "type": "REQUIRED"}
            ],
            "dependencies": {}
        }
        
        validations = analyzer._validate_bsw_configuration(result)
        
        # 중복 모듈 에러 확인
        assert any("Duplicate module" in v["message"] and v["level"] == "ERROR" 
                  for v in validations)
        
        # 알 수 없는 모듈 경고 확인
        assert any("Unknown module category" in v["message"] and v["level"] == "WARNING"
                  for v in validations)
    
    def test_detect_dependency_cycles(self, analyzer):
        """순환 의존성 감지 테스트"""
        # 순환 의존성이 있는 경우
        dependencies = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"]  # 순환
        }
        
        cycles = analyzer._detect_dependency_cycles(dependencies)
        assert len(cycles) > 0
        
        # 순환 의존성이 없는 경우
        dependencies_no_cycle = {
            "A": ["B"],
            "B": ["C"],
            "C": []
        }
        
        cycles_no = analyzer._detect_dependency_cycles(dependencies_no_cycle)
        assert len(cycles_no) == 0
    
    def test_full_analysis(self, analyzer):
        """전체 분석 프로세스 테스트"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR>
            <ECUC-MODULE-DEF UUID="test-uuid">
                <SHORT-NAME>EcuM</SHORT-NAME>
                <MODULE-ID>10</MODULE-ID>
            </ECUC-MODULE-DEF>
            <BSW-MODULE-DESCRIPTION>
                <SHORT-NAME>NvM</SHORT-NAME>
                <MODULE-ID>20</MODULE-ID>
            </BSW-MODULE-DESCRIPTION>
        </AUTOSAR>"""
        root = ET.fromstring(xml_content)
        
        result = analyzer.analyze(root)
        
        assert result is not None
        assert len(result.metadata.errors) == 0
        assert result.summary is not None
        assert "BSW Analysis Summary" in result.summary