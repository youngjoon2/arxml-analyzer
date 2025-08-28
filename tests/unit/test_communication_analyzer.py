"""CommunicationAnalyzer 단위 테스트"""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

from arxml_analyzer.analyzers.communication_analyzer import (
    CommunicationAnalyzer,
    SignalInfo,
    IPduInfo,
    SignalGroupInfo,
    PduRoutingPath,
    GatewayMapping
)
from arxml_analyzer.core.analyzer.base_analyzer import AnalysisResult, AnalysisMetadata
from arxml_analyzer.core.analyzer.pattern_finder import PatternType


class TestCommunicationAnalyzer:
    """CommunicationAnalyzer 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        """테스트용 analyzer 인스턴스"""
        return CommunicationAnalyzer()
    
    @pytest.fixture
    def sample_com_xml(self):
        """테스트용 COM XML 데이터"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR>
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <ELEMENTS>
                        <ECUC-MODULE-DEF UUID="test-uuid">
                            <SHORT-NAME>Com</SHORT-NAME>
                            <DESC>
                                <L-2>COM module configuration</L-2>
                            </DESC>
                        </ECUC-MODULE-DEF>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
            <COM-CONFIG>
                <CONFIGURATION-ID>1</CONFIGURATION-ID>
                <DEV-ERROR-DETECT>true</DEV-ERROR-DETECT>
            </COM-CONFIG>
            <COM-I-PDU>
                <SHORT-NAME>TestIPdu</SHORT-NAME>
                <I-PDU-IDENTIFIER>100</I-PDU-IDENTIFIER>
                <DIRECTION>TX</DIRECTION>
                <LENGTH>8</LENGTH>
                <TRIGGER-MODE>DIRECT</TRIGGER-MODE>
                <TX-MODE>PERIODIC</TX-MODE>
                <I-SIGNAL-REF DEST="TestSignal1"/>
                <I-SIGNAL-REF DEST="TestSignal2"/>
            </COM-I-PDU>
            <COM-SIGNAL>
                <SHORT-NAME>TestSignal1</SHORT-NAME>
                <BIT-POSITION>0</BIT-POSITION>
                <BIT-SIZE>16</BIT-SIZE>
                <DIRECTION>TX</DIRECTION>
                <INIT-VALUE>0</INIT-VALUE>
                <TRANSFER-PROPERTY>TRIGGERED</TRANSFER-PROPERTY>
            </COM-SIGNAL>
            <COM-SIGNAL>
                <SHORT-NAME>TestSignal2</SHORT-NAME>
                <BIT-POSITION>16</BIT-POSITION>
                <BIT-SIZE>8</BIT-SIZE>
                <DIRECTION>TX</DIRECTION>
                <TIMEOUT>1.0</TIMEOUT>
                <UPDATE-BIT-POSITION>23</UPDATE-BIT-POSITION>
            </COM-SIGNAL>
            <COM-SIGNAL-GROUP>
                <SHORT-NAME>TestSignalGroup</SHORT-NAME>
                <GROUP-SIGNAL-REF DEST="TestSignal1"/>
                <GROUP-SIGNAL-REF DEST="TestSignal2"/>
                <UPDATE-BIT-USED>true</UPDATE-BIT-USED>
                <TRANSFER-PROPERTY>PENDING</TRANSFER-PROPERTY>
            </COM-SIGNAL-GROUP>
            <COM-GATEWAY-MAPPING>
                <SOURCE-SIGNAL-REF>SourceSignal</SOURCE-SIGNAL-REF>
                <DEST-SIGNAL-REF>DestSignal</DEST-SIGNAL-REF>
                <SOURCE-I-PDU-REF>SourceIPdu</SOURCE-I-PDU-REF>
                <DEST-I-PDU-REF>DestIPdu</DEST-I-PDU-REF>
                <TRANSFORMATION-TYPE>LINEAR</TRANSFORMATION-TYPE>
            </COM-GATEWAY-MAPPING>
        </AUTOSAR>"""
        return ET.fromstring(xml_content)
    
    @pytest.fixture
    def sample_pdur_xml(self):
        """테스트용 PduR XML 데이터"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR>
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <ELEMENTS>
                        <ECUC-MODULE-DEF UUID="test-uuid">
                            <SHORT-NAME>PduR</SHORT-NAME>
                        </ECUC-MODULE-DEF>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
            <PDU-R-CONFIG>
                <CONFIGURATION-ID>2</CONFIGURATION-ID>
                <DEV-ERROR-DETECT>false</DEV-ERROR-DETECT>
                <VERSION-INFO-API>true</VERSION-INFO-API>
            </PDU-R-CONFIG>
            <PDU-R-ROUTING-PATH>
                <SOURCE-PDU-REF>SourcePdu</SOURCE-PDU-REF>
                <DEST-PDU-REF>DestPdu</DEST-PDU-REF>
                <ROUTING-PATH-ID>1</ROUTING-PATH-ID>
                <GATEWAY-TYPE>DIRECT</GATEWAY-TYPE>
            </PDU-R-ROUTING-PATH>
            <PDU-R-ROUTING-TABLE>
                <SHORT-NAME>MainRoutingTable</SHORT-NAME>
                <ROUTING-PATH-REF>Path1</ROUTING-PATH-REF>
                <ROUTING-PATH-REF>Path2</ROUTING-PATH-REF>
                <DEFAULT-ACTION>DROP</DEFAULT-ACTION>
            </PDU-R-ROUTING-TABLE>
            <PDU-R-TP-BUFFER>
                <BUFFER-SIZE>256</BUFFER-SIZE>
                <BUFFER-POOL-REF>TpBufferPool</BUFFER-POOL-REF>
                <SHARED>true</SHARED>
            </PDU-R-TP-BUFFER>
        </AUTOSAR>"""
        return ET.fromstring(xml_content)
    
    @pytest.fixture
    def sample_cantp_xml(self):
        """테스트용 CanTp XML 데이터"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR>
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <ELEMENTS>
                        <ECUC-MODULE-DEF UUID="test-uuid">
                            <SHORT-NAME>CanTp</SHORT-NAME>
                        </ECUC-MODULE-DEF>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
            <CAN-TP-CONFIG>
                <MAIN-FUNCTION-PERIOD>0.005</MAIN-FUNCTION-PERIOD>
                <DEV-ERROR-DETECT>true</DEV-ERROR-DETECT>
                <VERSION-INFO-API>false</VERSION-INFO-API>
            </CAN-TP-CONFIG>
            <CAN-TP-CHANNEL>
                <SHORT-NAME>Channel1</SHORT-NAME>
                <CHANNEL-MODE>FULL_DUPLEX</CHANNEL-MODE>
                <PADDING-ACTIVATION>true</PADDING-ACTIVATION>
                <BS>8</BS>
                <ST-MIN>0.001</ST-MIN>
            </CAN-TP-CHANNEL>
            <CAN-TP-CONNECTION>
                <SHORT-NAME>Connection1</SHORT-NAME>
                <ADDRESSING-FORMAT>EXTENDED</ADDRESSING-FORMAT>
                <N-AR>1.0</N-AR>
                <N-BR>2.0</N-BR>
                <N-CR>3.0</N-CR>
                <RX-PDU-REF>RxPdu</RX-PDU-REF>
                <TX-PDU-REF>TxPdu</TX-PDU-REF>
            </CAN-TP-CONNECTION>
            <CAN-TP-FLOW-CONTROL>
                <FC-PDU-REF>FlowControlPdu</FC-PDU-REF>
                <MAX-BLOCK-SIZE>16</MAX-BLOCK-SIZE>
                <FLOW-STATUS>CTS</FLOW-STATUS>
            </CAN-TP-FLOW-CONTROL>
        </AUTOSAR>"""
        return ET.fromstring(xml_content)
    
    def test_analyzer_initialization(self, analyzer):
        """analyzer 초기화 테스트"""
        assert analyzer.type_identifier == "COMMUNICATION"
        assert analyzer.name == "CommunicationAnalyzer"
    
    def test_can_analyze_com_document(self, analyzer, sample_com_xml):
        """COM 문서 분석 가능 여부 테스트"""
        assert analyzer.can_analyze(sample_com_xml) is True
    
    def test_can_analyze_pdur_document(self, analyzer, sample_pdur_xml):
        """PduR 문서 분석 가능 여부 테스트"""
        assert analyzer.can_analyze(sample_pdur_xml) is True
    
    def test_can_analyze_cantp_document(self, analyzer, sample_cantp_xml):
        """CanTp 문서 분석 가능 여부 테스트"""
        assert analyzer.can_analyze(sample_cantp_xml) is True
    
    def test_can_analyze_non_communication_document(self, analyzer):
        """비통신 문서 분석 불가 테스트"""
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
        
        # COM 관련 패턴 확인
        assert any("Com" in p for p in patterns[PatternType.XPATH])
        assert any("PduR" in p for p in patterns[PatternType.XPATH])
        assert any("CanTp" in p for p in patterns[PatternType.XPATH])
    
    def test_analyze_com_module(self, analyzer, sample_com_xml):
        """COM 모듈 분석 테스트"""
        result = analyzer.analyze(sample_com_xml)
        
        assert result is not None
        assert "modules" in result.details
        assert "COM" in result.details["modules"]
        
        com_module = result.details["modules"]["COM"]
        assert com_module["type"] == "COM"
        
        # IPDUs 확인
        assert len(com_module["ipdus"]) == 1
        ipdu = com_module["ipdus"][0]
        assert ipdu["name"] == "TestIPdu"
        assert ipdu["pdu_id"] == 100
        assert ipdu["direction"] == "TX"
        assert ipdu["trigger_mode"] == "DIRECT"
        
        # Signals 확인
        assert len(com_module["signals"]) == 2
        signal1 = com_module["signals"][0]
        assert signal1["name"] == "TestSignal1"
        assert signal1["bit_position"] == 0
        assert signal1["bit_size"] == 16
        
        # Signal Groups 확인
        assert len(com_module["signal_groups"]) == 1
        sg = com_module["signal_groups"][0]
        assert sg["name"] == "TestSignalGroup"
        assert len(sg["signals"]) == 2
        assert sg["update_bit_enabled"] is True
        
        # Gateway Mappings 확인
        assert len(com_module["gateway_mappings"]) == 1
        gw = com_module["gateway_mappings"][0]
        assert gw["source_signal"] == "SourceSignal"
        assert gw["dest_signal"] == "DestSignal"
    
    def test_analyze_pdur_module(self, analyzer, sample_pdur_xml):
        """PduR 모듈 분석 테스트"""
        result = analyzer.analyze(sample_pdur_xml)
        
        assert "modules" in result.details
        assert "PduR" in result.details["modules"]
        pdur_module = result.details["modules"]["PduR"]
        
        # Routing Paths 확인
        assert len(pdur_module["routing_paths"]) == 1
        path = pdur_module["routing_paths"][0]
        assert path["source_pdu"] == "SourcePdu"
        assert path["dest_pdu"] == "DestPdu"
        assert path["routing_path_id"] == 1
        
        # Routing Tables 확인
        assert len(pdur_module["routing_tables"]) == 1
        table = pdur_module["routing_tables"][0]
        assert table["name"] == "MainRoutingTable"
        assert table["routing_paths"] == 2
        
        # TP Buffers 확인
        assert len(pdur_module["tp_buffers"]) == 1
        buffer = pdur_module["tp_buffers"][0]
        assert buffer["buffer_size"] == 256
        assert buffer["shared"] is True
    
    def test_analyze_cantp_module(self, analyzer, sample_cantp_xml):
        """CanTp 모듈 분석 테스트"""
        result = analyzer.analyze(sample_cantp_xml)
        
        assert "modules" in result.details
        assert "CanTp" in result.details["modules"]
        cantp_module = result.details["modules"]["CanTp"]
        
        # Channels 확인
        assert len(cantp_module["channels"]) == 1
        channel = cantp_module["channels"][0]
        assert channel["name"] == "Channel1"
        assert channel["padding_enabled"] is True
        assert channel["bs"] == 8
        
        # Connections 확인
        assert len(cantp_module["connections"]) == 1
        conn = cantp_module["connections"][0]
        assert conn["name"] == "Connection1"
        assert conn["addressing_format"] == "EXTENDED"
        assert conn["n_ar"] == 1.0
        
        # Flow Control 확인
        assert len(cantp_module["flow_control"]) == 1
        fc = cantp_module["flow_control"][0]
        assert fc["fc_pdu"] == "FlowControlPdu"
        assert fc["max_block_size"] == 16
    
    def test_extract_ipdu_info(self, analyzer):
        """IPdu 정보 추출 테스트"""
        xml_content = """
        <COM-I-PDU>
            <SHORT-NAME>TestIPdu</SHORT-NAME>
            <I-PDU-IDENTIFIER>123</I-PDU-IDENTIFIER>
            <DIRECTION>RX</DIRECTION>
            <LENGTH>16</LENGTH>
            <TRIGGER-MODE>MIXED</TRIGGER-MODE>
            <TX-MODE>NONE</TX-MODE>
        </COM-I-PDU>"""
        elem = ET.fromstring(xml_content)
        
        ipdu = analyzer._extract_ipdu_info(elem)
        
        assert ipdu is not None
        assert ipdu.name == "TestIPdu"
        assert ipdu.pdu_id == 123
        assert ipdu.direction == "RX"
        assert ipdu.length == 16
        assert ipdu.trigger_mode == "MIXED"
        assert ipdu.tx_mode == "NONE"
    
    def test_extract_signal_info(self, analyzer):
        """Signal 정보 추출 테스트"""
        xml_content = """
        <COM-SIGNAL>
            <SHORT-NAME>TestSignal</SHORT-NAME>
            <BIT-POSITION>8</BIT-POSITION>
            <BIT-SIZE>32</BIT-SIZE>
            <DIRECTION>TX</DIRECTION>
            <INIT-VALUE>100</INIT-VALUE>
            <TIMEOUT>2.5</TIMEOUT>
            <UPDATE-BIT-POSITION>39</UPDATE-BIT-POSITION>
            <TRANSFER-PROPERTY>PENDING</TRANSFER-PROPERTY>
        </COM-SIGNAL>"""
        elem = ET.fromstring(xml_content)
        
        signal = analyzer._extract_signal_info(elem)
        
        assert signal is not None
        assert signal.name == "TestSignal"
        assert signal.bit_position == 8
        assert signal.bit_size == 32
        assert signal.direction == "TX"
        assert signal.init_value == "100"
        assert signal.timeout == 2.5
        assert signal.update_bit_position == 39
        assert signal.transfer_property == "PENDING"
    
    def test_calculate_communication_metrics(self, analyzer):
        """통신 메트릭 계산 테스트"""
        modules = {
            "COM": {
                "ipdus": [{"name": "ipdu1"}, {"name": "ipdu2"}],
                "signals": [{"name": "sig1"}, {"name": "sig2"}, {"name": "sig3"}],
                "gateway_mappings": [{"source": "s1", "dest": "d1"}]
            },
            "PduR": {
                "routing_paths": [{"id": 1}, {"id": 2}]
            },
            "CanTp": {
                "channels": [{"name": "ch1"}]
            }
        }
        
        metrics = analyzer._calculate_communication_metrics(modules)
        
        assert metrics["total_modules"] == 3
        assert metrics["total_ipdus"] == 2
        assert metrics["total_signals"] == 3
        assert metrics["total_routing_paths"] == 2
        assert metrics["gateway_mappings"] == 1
        assert metrics["tp_channels"] == 1
        assert 0 <= metrics["communication_complexity"] <= 10
    
    def test_validate_communication_config(self, analyzer):
        """통신 설정 검증 테스트"""
        metadata = AnalysisMetadata(analyzer_name="TestAnalyzer")
        result = AnalysisResult(metadata=metadata)
        result.details["modules"] = {}
        result.details["modules"]["COM"] = {
            "ipdus": [
                {"name": "EmptyIPdu", "signals": []},
                {"name": "NormalIPdu", "signals": [{"name": "sig1"}]}
            ],
            "signals": [
                {"name": "LargeSignal", "bit_size": 128},
                {"name": "NormalSignal", "bit_size": 16}
            ]
        }
        
        validations = analyzer._validate_communication_config(result)
        
        # Empty IPdu 경고 확인
        assert any("EmptyIPdu" in v["message"] and v["level"] == "WARNING" 
                  for v in validations)
        
        # Large signal 경고 확인
        assert any("LargeSignal" in v["message"] and v["level"] == "WARNING"
                  for v in validations)
    
    def test_analyze_communication_relationships(self, analyzer):
        """통신 관계 분석 테스트"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR>
            <COM-I-PDU>
                <SHORT-NAME>IPdu1</SHORT-NAME>
                <I-SIGNAL-REF DEST="Signal1"/>
            </COM-I-PDU>
            <COM-GATEWAY-MAPPING>
                <SOURCE-SIGNAL-REF>Signal1</SOURCE-SIGNAL-REF>
                <DEST-SIGNAL-REF>Signal2</DEST-SIGNAL-REF>
            </COM-GATEWAY-MAPPING>
            <PDU-R-ROUTING-PATH>
                <SOURCE-PDU-REF>Pdu1</SOURCE-PDU-REF>
                <DEST-PDU-REF>Pdu2</DEST-PDU-REF>
            </PDU-R-ROUTING-PATH>
        </AUTOSAR>"""
        root = ET.fromstring(xml_content)
        
        relationships = analyzer._analyze_communication_relationships(root)
        
        assert len(relationships) == 3
        
        # Signal to IPdu relationship
        assert any(r["type"] == "SIGNAL_TO_IPDU" and 
                  r["source"] == "Signal1" and 
                  r["target"] == "IPdu1" 
                  for r in relationships)
        
        # Gateway relationship
        assert any(r["type"] == "GATEWAY" and
                  r["source"] == "Signal1" and
                  r["target"] == "Signal2"
                  for r in relationships)
        
        # Routing relationship
        assert any(r["type"] == "ROUTING" and
                  r["source"] == "Pdu1" and
                  r["target"] == "Pdu2"
                  for r in relationships)
    
    def test_full_analysis(self, analyzer):
        """전체 분석 프로세스 테스트"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <AUTOSAR>
            <ECUC-MODULE-DEF UUID="test-uuid">
                <SHORT-NAME>Com</SHORT-NAME>
            </ECUC-MODULE-DEF>
            <COM-CONFIG>
                <CONFIGURATION-ID>1</CONFIGURATION-ID>
            </COM-CONFIG>
            <COM-I-PDU>
                <SHORT-NAME>TestIPdu</SHORT-NAME>
                <I-PDU-IDENTIFIER>100</I-PDU-IDENTIFIER>
                <DIRECTION>TX</DIRECTION>
            </COM-I-PDU>
            <COM-SIGNAL>
                <SHORT-NAME>TestSignal</SHORT-NAME>
                <BIT-POSITION>0</BIT-POSITION>
                <BIT-SIZE>8</BIT-SIZE>
                <DIRECTION>TX</DIRECTION>
            </COM-SIGNAL>
        </AUTOSAR>"""
        root = ET.fromstring(xml_content)
        
        result = analyzer.analyze(root)
        
        assert result is not None
        assert len(result.metadata.errors) == 0
        assert "modules" in result.details
        assert "COM" in result.details["modules"]
        assert result.summary is not None
        assert "Communication Stack Analysis Summary" in result.summary