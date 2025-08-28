"""AUTOSAR Communication Stack (COM/PduR/CanTp) analyzer implementation."""

from typing import Dict, List, Any, Optional, Set
import re
from dataclasses import dataclass, field

from ..core.analyzer.base_analyzer import BaseAnalyzer, AnalysisResult, AnalysisMetadata
from ..core.analyzer.pattern_finder import PatternType


@dataclass
class SignalInfo:
    """Signal 정보"""
    name: str
    bit_position: int
    bit_size: int
    direction: str  # TX/RX
    init_value: Optional[Any] = None
    timeout: Optional[float] = None
    update_bit_position: Optional[int] = None
    transfer_property: Optional[str] = None  # TRIGGERED/PENDING


@dataclass
class IPduInfo:
    """I-PDU 정보"""
    name: str
    pdu_id: int
    direction: str  # TX/RX
    length: int
    signals: List[SignalInfo] = field(default_factory=list)
    trigger_mode: Optional[str] = None  # DIRECT/MIXED
    tx_mode: Optional[str] = None  # PERIODIC/MIXED/NONE


@dataclass
class SignalGroupInfo:
    """Signal Group 정보"""
    name: str
    signals: List[str]
    update_bit_enabled: bool = False
    transfer_property: Optional[str] = None


@dataclass
class PduRoutingPath:
    """PDU 라우팅 경로"""
    source_pdu: str
    dest_pdu: str
    routing_path_id: int
    gateway_type: Optional[str] = None  # DIRECT/TP


@dataclass
class TransportProtocolConfig:
    """Transport Protocol 설정"""
    protocol_type: str  # CAN-TP, FlexRay-TP
    bs: Optional[int] = None  # Block Size
    stmin: Optional[float] = None  # Separation Time
    n_ar: Optional[float] = None  # N_Ar timeout
    n_br: Optional[float] = None  # N_Br timeout
    n_cr: Optional[float] = None  # N_Cr timeout
    padding_enabled: bool = False


@dataclass
class GatewayMapping:
    """게이트웨이 매핑 정보"""
    source_signal: str
    dest_signal: str
    source_ipdu: str
    dest_ipdu: str
    transformation: Optional[str] = None


class CommunicationAnalyzer(BaseAnalyzer):
    """AUTOSAR Communication Stack 분석기"""
    
    def __init__(self):
        """초기화"""
        super().__init__()
        self.type_identifier = "COMMUNICATION"
        
    def can_analyze(self, root) -> bool:
        """통신 스택 문서 분석 가능 여부 확인"""
        patterns = [
            ".//ECUC-MODULE-DEF[SHORT-NAME='Com']",
            ".//ECUC-MODULE-DEF[SHORT-NAME='PduR']",
            ".//ECUC-MODULE-DEF[SHORT-NAME='CanTp']",
            './/COM-CONFIG',
            './/PDU-R-CONFIG',
            './/CAN-TP-CONFIG',
            './/I-PDU-GROUP',
            './/I-SIGNAL',
            './/GATEWAY-MAPPING'
        ]
        
        for pattern in patterns:
            if root.find(pattern) is not None:
                return True
                
        return False
    
    def get_patterns(self) -> Dict[PatternType, List[str]]:
        """통신 관련 패턴 반환"""
        return {
            PatternType.XPATH: [
                ".//ECUC-MODULE-DEF[SHORT-NAME='Com']",
                ".//ECUC-MODULE-DEF[SHORT-NAME='PduR']",
                ".//ECUC-MODULE-DEF[SHORT-NAME='CanTp']",
                './/COM-CONFIG',
                './/PDU-R-CONFIG',
                './/CAN-TP-CONFIG',
                './/COM-I-PDU',
                './/COM-I-PDU-GROUP',
                './/COM-SIGNAL',
                './/COM-SIGNAL-GROUP',
                './/COM-GATEWAY-MAPPING',
                './/PDU-R-ROUTING-PATH',
                './/CAN-TP-CHANNEL'
            ],
            PatternType.REFERENCE: [
                './/I-SIGNAL-REF',
                './/I-PDU-REF',
                './/PDU-REF',
                './/SOURCE-PDU-REF',
                './/DEST-PDU-REF'
            ]
        }
        
    def analyze(self, root) -> AnalysisResult:
        """통신 스택 분석 수행"""
        # 메타데이터 생성
        metadata = AnalysisMetadata(
            analyzer_name=self.name,
            analyzer_version=self.version,
            arxml_type="COMMUNICATION"
        )
        result = AnalysisResult(metadata=metadata)
        
        # modules 속성을 details에 초기화
        modules = {}
        
        try:
            # COM 모듈 분석
            com_analysis = self._analyze_com_module(root)
            if com_analysis:
                modules["COM"] = com_analysis
            
            # PduR 모듈 분석
            pdur_analysis = self._analyze_pdur_module(root)
            if pdur_analysis:
                modules["PduR"] = pdur_analysis
            
            # CanTp 모듈 분석
            cantp_analysis = self._analyze_cantp_module(root)
            if cantp_analysis:
                modules["CanTp"] = cantp_analysis
            
            # modules를 details에 저장
            result.details["modules"] = modules
            
            # 통신 메트릭 계산
            result.statistics = self._calculate_communication_metrics(modules)
            
            # 통신 관계 분석
            result.details["relationships"] = self._analyze_communication_relationships(root)
            
            # 검증 수행
            result.details["validation_results"] = self._validate_communication_config(result)
            
            result.summary = self._generate_summary(result)
            
        except Exception as e:
            result.metadata.errors.append(f"Communication analysis error: {str(e)}")
            
        return result
    
    def _analyze_com_module(self, root) -> Optional[Dict[str, Any]]:
        """COM 모듈 분석"""
        com_module = root.find(".//ECUC-MODULE-DEF[SHORT-NAME='Com']")
        if com_module is None:
            # Alternative: COM 구성 직접 찾기
            com_config = root.find('.//COM-CONFIG')
            if com_config is None:
                return None
                
        analysis = {
            "type": "COM",
            "ipdus": [],
            "signals": [],
            "signal_groups": [],
            "gateway_mappings": [],
            "configuration": {}
        }
        
        # I-PDU 분석
        for ipdu_elem in root.findall('.//COM-I-PDU'):
            ipdu_info = self._extract_ipdu_info(ipdu_elem)
            if ipdu_info:
                analysis["ipdus"].append(ipdu_info.__dict__)
        
        # Signal 분석
        for signal_elem in root.findall('.//COM-SIGNAL'):
            signal_info = self._extract_signal_info(signal_elem)
            if signal_info:
                analysis["signals"].append(signal_info.__dict__)
        
        # Signal Group 분석
        for sg_elem in root.findall('.//COM-SIGNAL-GROUP'):
            sg_info = self._extract_signal_group_info(sg_elem)
            if sg_info:
                analysis["signal_groups"].append(sg_info.__dict__)
        
        # Gateway Mapping 분석
        for gw_elem in root.findall('.//COM-GATEWAY-MAPPING'):
            gw_info = self._extract_gateway_mapping(gw_elem)
            if gw_info:
                analysis["gateway_mappings"].append(gw_info.__dict__)
        
        # COM 설정 파라미터 추출
        analysis["configuration"] = self._extract_com_configuration(root)
        
        return analysis
    
    def _analyze_pdur_module(self, root) -> Optional[Dict[str, Any]]:
        """PduR 모듈 분석"""
        pdur_module = root.find(".//ECUC-MODULE-DEF[SHORT-NAME='PduR']")
        if pdur_module is None:
            pdur_config = root.find('.//PDU-R-CONFIG')
            if pdur_config is None:
                return None
                
        analysis = {
            "type": "PduR",
            "routing_paths": [],
            "routing_tables": [],
            "tp_buffers": [],
            "configuration": {}
        }
        
        # Routing Path 분석
        for path_elem in root.findall('.//PDU-R-ROUTING-PATH'):
            path_info = self._extract_routing_path_info(path_elem)
            if path_info:
                analysis["routing_paths"].append(path_info.__dict__)
        
        # Routing Table 분석
        for table_elem in root.findall('.//PDU-R-ROUTING-TABLE'):
            table_info = self._extract_routing_table_info(table_elem)
            if table_info:
                analysis["routing_tables"].append(table_info)
        
        # TP Buffer 설정 분석
        for buffer_elem in root.findall('.//PDU-R-TP-BUFFER'):
            buffer_info = self._extract_tp_buffer_info(buffer_elem)
            if buffer_info:
                analysis["tp_buffers"].append(buffer_info)
        
        # PduR 설정 파라미터 추출
        analysis["configuration"] = self._extract_pdur_configuration(root)
        
        return analysis
    
    def _analyze_cantp_module(self, root) -> Optional[Dict[str, Any]]:
        """CanTp 모듈 분석"""
        cantp_module = root.find(".//ECUC-MODULE-DEF[SHORT-NAME='CanTp']")
        if cantp_module is None:
            cantp_config = root.find('.//CAN-TP-CONFIG')
            if cantp_config is None:
                return None
                
        analysis = {
            "type": "CanTp",
            "channels": [],
            "connections": [],
            "flow_control": [],
            "configuration": {}
        }
        
        # CanTp Channel 분석
        for channel_elem in root.findall('.//CAN-TP-CHANNEL'):
            channel_info = self._extract_cantp_channel_info(channel_elem)
            if channel_info:
                analysis["channels"].append(channel_info)
        
        # CanTp Connection 분석
        for conn_elem in root.findall('.//CAN-TP-CONNECTION'):
            conn_info = self._extract_cantp_connection_info(conn_elem)
            if conn_info:
                analysis["connections"].append(conn_info)
        
        # Flow Control 설정 분석
        for fc_elem in root.findall('.//CAN-TP-FLOW-CONTROL'):
            fc_info = self._extract_flow_control_info(fc_elem)
            if fc_info:
                analysis["flow_control"].append(fc_info)
        
        # CanTp 설정 파라미터 추출
        analysis["configuration"] = self._extract_cantp_configuration(root)
        
        return analysis
    
    def _extract_ipdu_info(self, elem) -> Optional[IPduInfo]:
        """I-PDU 정보 추출"""
        try:
            name = elem.findtext('.//SHORT-NAME', '')
            pdu_id = self._safe_int_conversion(elem.findtext('.//I-PDU-IDENTIFIER'))
            direction = elem.findtext('.//DIRECTION', 'UNKNOWN')
            length = self._safe_int_conversion(elem.findtext('.//LENGTH'))
            
            if not name or pdu_id is None:
                return None
                
            ipdu = IPduInfo(
                name=name,
                pdu_id=pdu_id,
                direction=direction,
                length=length if length is not None else 0
            )
            
            # Trigger Mode
            ipdu.trigger_mode = elem.findtext('.//TRIGGER-MODE')
            
            # Tx Mode
            ipdu.tx_mode = elem.findtext('.//TX-MODE')
            
            # 포함된 시그널들
            for signal_ref in elem.findall('.//I-SIGNAL-REF'):
                signal_name = signal_ref.get('DEST', '')
                if signal_name:
                    # 간단한 시그널 참조만 저장
                    ipdu.signals.append(SignalInfo(
                        name=signal_name,
                        bit_position=0,
                        bit_size=0,
                        direction=direction
                    ))
            
            return ipdu
            
        except Exception:
            return None
    
    def _extract_signal_info(self, elem) -> Optional[SignalInfo]:
        """Signal 정보 추출"""
        try:
            name = elem.findtext('.//SHORT-NAME', '')
            bit_position = self._safe_int_conversion(elem.findtext('.//BIT-POSITION'))
            bit_size = self._safe_int_conversion(elem.findtext('.//BIT-SIZE'))
            direction = elem.findtext('.//DIRECTION', 'UNKNOWN')
            
            if not name or bit_position is None or bit_size is None:
                return None
                
            signal = SignalInfo(
                name=name,
                bit_position=bit_position,
                bit_size=bit_size,
                direction=direction
            )
            
            # Optional fields
            signal.init_value = elem.findtext('.//INIT-VALUE')
            signal.timeout = self._safe_float_conversion(elem.findtext('.//TIMEOUT'))
            signal.update_bit_position = self._safe_int_conversion(
                elem.findtext('.//UPDATE-BIT-POSITION')
            )
            signal.transfer_property = elem.findtext('.//TRANSFER-PROPERTY')
            
            return signal
            
        except Exception:
            return None
    
    def _extract_signal_group_info(self, elem) -> Optional[SignalGroupInfo]:
        """Signal Group 정보 추출"""
        try:
            name = elem.findtext('.//SHORT-NAME', '')
            if not name:
                return None
                
            sg = SignalGroupInfo(name=name, signals=[])
            
            # Group에 포함된 시그널들
            for signal_ref in elem.findall('.//GROUP-SIGNAL-REF'):
                signal_name = signal_ref.get('DEST', '')
                if signal_name:
                    sg.signals.append(signal_name)
            
            # Update bit 설정
            update_bit = elem.findtext('.//UPDATE-BIT-USED')
            sg.update_bit_enabled = update_bit == 'true'
            
            # Transfer property
            sg.transfer_property = elem.findtext('.//TRANSFER-PROPERTY')
            
            return sg
            
        except Exception:
            return None
    
    def _extract_gateway_mapping(self, elem) -> Optional[GatewayMapping]:
        """게이트웨이 매핑 정보 추출"""
        try:
            source_signal = elem.findtext('.//SOURCE-SIGNAL-REF', '')
            dest_signal = elem.findtext('.//DEST-SIGNAL-REF', '')
            source_ipdu = elem.findtext('.//SOURCE-I-PDU-REF', '')
            dest_ipdu = elem.findtext('.//DEST-I-PDU-REF', '')
            
            if not source_signal or not dest_signal:
                return None
                
            gw = GatewayMapping(
                source_signal=source_signal,
                dest_signal=dest_signal,
                source_ipdu=source_ipdu,
                dest_ipdu=dest_ipdu
            )
            
            # Transformation
            gw.transformation = elem.findtext('.//TRANSFORMATION-TYPE')
            
            return gw
            
        except Exception:
            return None
    
    def _extract_routing_path_info(self, elem) -> Optional[PduRoutingPath]:
        """PDU 라우팅 경로 정보 추출"""
        try:
            source_pdu = elem.findtext('.//SOURCE-PDU-REF', '')
            dest_pdu = elem.findtext('.//DEST-PDU-REF', '')
            path_id = self._safe_int_conversion(elem.findtext('.//ROUTING-PATH-ID'))
            
            if not source_pdu or not dest_pdu or path_id is None:
                return None
                
            path = PduRoutingPath(
                source_pdu=source_pdu,
                dest_pdu=dest_pdu,
                routing_path_id=path_id
            )
            
            # Gateway type
            path.gateway_type = elem.findtext('.//GATEWAY-TYPE')
            
            return path
            
        except Exception:
            return None
    
    def _extract_routing_table_info(self, elem) -> Dict[str, Any]:
        """라우팅 테이블 정보 추출"""
        try:
            return {
                "name": elem.findtext('.//SHORT-NAME', ''),
                "routing_paths": len(elem.findall('.//ROUTING-PATH-REF')),
                "default_action": elem.findtext('.//DEFAULT-ACTION', 'NONE')
            }
        except Exception:
            return {}
    
    def _extract_tp_buffer_info(self, elem) -> Dict[str, Any]:
        """TP Buffer 정보 추출"""
        try:
            return {
                "buffer_size": self._safe_int_conversion(elem.findtext('.//BUFFER-SIZE')),
                "buffer_pool": elem.findtext('.//BUFFER-POOL-REF', ''),
                "shared": elem.findtext('.//SHARED', 'false') == 'true'
            }
        except Exception:
            return {}
    
    def _extract_cantp_channel_info(self, elem) -> Dict[str, Any]:
        """CanTp 채널 정보 추출"""
        try:
            return {
                "name": elem.findtext('.//SHORT-NAME', ''),
                "channel_mode": elem.findtext('.//CHANNEL-MODE', 'FULL_DUPLEX'),
                "padding_enabled": elem.findtext('.//PADDING-ACTIVATION', 'false') == 'true',
                "bs": self._safe_int_conversion(elem.findtext('.//BS')),
                "stmin": self._safe_float_conversion(elem.findtext('.//ST-MIN'))
            }
        except Exception:
            return {}
    
    def _extract_cantp_connection_info(self, elem) -> Dict[str, Any]:
        """CanTp 연결 정보 추출"""
        try:
            return {
                "name": elem.findtext('.//SHORT-NAME', ''),
                "addressing_format": elem.findtext('.//ADDRESSING-FORMAT', 'STANDARD'),
                "n_ar": self._safe_float_conversion(elem.findtext('.//N-AR')),
                "n_br": self._safe_float_conversion(elem.findtext('.//N-BR')),
                "n_cr": self._safe_float_conversion(elem.findtext('.//N-CR')),
                "rx_pdu": elem.findtext('.//RX-PDU-REF', ''),
                "tx_pdu": elem.findtext('.//TX-PDU-REF', '')
            }
        except Exception:
            return {}
    
    def _extract_flow_control_info(self, elem) -> Dict[str, Any]:
        """Flow Control 정보 추출"""
        try:
            return {
                "fc_pdu": elem.findtext('.//FC-PDU-REF', ''),
                "max_block_size": self._safe_int_conversion(elem.findtext('.//MAX-BLOCK-SIZE')),
                "flow_status": elem.findtext('.//FLOW-STATUS', 'CTS')
            }
        except Exception:
            return {}
    
    def _extract_com_configuration(self, root) -> Dict[str, Any]:
        """COM 설정 파라미터 추출"""
        config = {}
        
        try:
            # COM general configuration
            com_config = root.find('.//COM-CONFIG')
            if com_config is not None:
                config["configuration_id"] = self._safe_int_conversion(
                    com_config.findtext('.//CONFIGURATION-ID')
                )
                config["version_info_api"] = com_config.findtext(
                    './/VERSION-INFO-API', 'false'
                ) == 'true'
                config["dev_error_detect"] = com_config.findtext(
                    './/DEV-ERROR-DETECT', 'false'
                ) == 'true'
            
            # IPdu Group 개수
            config["ipdu_groups"] = len(root.findall('.//COM-I-PDU-GROUP'))
            
            # Total IPdus
            config["total_ipdus"] = len(root.findall('.//COM-I-PDU'))
            
            # Total Signals
            config["total_signals"] = len(root.findall('.//COM-SIGNAL'))
            
        except Exception:
            pass
            
        return config
    
    def _extract_pdur_configuration(self, root) -> Dict[str, Any]:
        """PduR 설정 파라미터 추출"""
        config = {}
        
        try:
            pdur_config = root.find('.//PDU-R-CONFIG')
            if pdur_config is not None:
                config["configuration_id"] = self._safe_int_conversion(
                    pdur_config.findtext('.//CONFIGURATION-ID')
                )
                config["dev_error_detect"] = pdur_config.findtext(
                    './/DEV-ERROR-DETECT', 'false'
                ) == 'true'
                config["version_info_api"] = pdur_config.findtext(
                    './/VERSION-INFO-API', 'false'
                ) == 'true'
            
            # Routing paths 개수
            config["total_routing_paths"] = len(root.findall('.//PDU-R-ROUTING-PATH'))
            
            # TP Buffers 개수
            config["total_tp_buffers"] = len(root.findall('.//PDU-R-TP-BUFFER'))
            
        except Exception:
            pass
            
        return config
    
    def _extract_cantp_configuration(self, root) -> Dict[str, Any]:
        """CanTp 설정 파라미터 추출"""
        config = {}
        
        try:
            cantp_config = root.find('.//CAN-TP-CONFIG')
            if cantp_config is not None:
                config["main_function_period"] = self._safe_float_conversion(
                    cantp_config.findtext('.//MAIN-FUNCTION-PERIOD')
                )
                config["dev_error_detect"] = cantp_config.findtext(
                    './/DEV-ERROR-DETECT', 'false'
                ) == 'true'
                config["version_info_api"] = cantp_config.findtext(
                    './/VERSION-INFO-API', 'false'
                ) == 'true'
            
            # Channels 개수
            config["total_channels"] = len(root.findall('.//CAN-TP-CHANNEL'))
            
            # Connections 개수  
            config["total_connections"] = len(root.findall('.//CAN-TP-CONNECTION'))
            
        except Exception:
            pass
            
        return config
    
    def _calculate_communication_metrics(self, modules: Dict[str, Any]) -> Dict[str, Any]:
        """통신 메트릭 계산"""
        metrics = {
            "total_modules": len(modules),
            "total_ipdus": 0,
            "total_signals": 0,
            "total_routing_paths": 0,
            "gateway_mappings": 0,
            "tp_channels": 0,
            "communication_complexity": 0.0
        }
        
        # COM 메트릭
        if "COM" in modules:
            com = modules["COM"]
            metrics["total_ipdus"] = len(com.get("ipdus", []))
            metrics["total_signals"] = len(com.get("signals", []))
            metrics["gateway_mappings"] = len(com.get("gateway_mappings", []))
        
        # PduR 메트릭
        if "PduR" in modules:
            pdur = modules["PduR"]
            metrics["total_routing_paths"] = len(pdur.get("routing_paths", []))
        
        # CanTp 메트릭
        if "CanTp" in modules:
            cantp = modules["CanTp"]
            metrics["tp_channels"] = len(cantp.get("channels", []))
        
        # 복잡도 계산 (0-10 scale)
        complexity_factors = [
            metrics["total_signals"] / 100.0,  # 100 signals = 1.0
            metrics["total_ipdus"] / 50.0,     # 50 IPDUs = 1.0
            metrics["total_routing_paths"] / 30.0,  # 30 paths = 1.0
            metrics["gateway_mappings"] / 20.0,     # 20 mappings = 1.0
            metrics["tp_channels"] / 10.0           # 10 channels = 1.0
        ]
        
        metrics["communication_complexity"] = min(
            sum(complexity_factors) * 2,  # Scale to 0-10
            10.0
        )
        
        return metrics
    
    def _analyze_communication_relationships(self, root) -> List[Dict[str, Any]]:
        """통신 관계 분석"""
        relationships = []
        
        try:
            # Signal to IPdu relationships
            for ipdu in root.findall('.//COM-I-PDU'):
                ipdu_name = ipdu.findtext('.//SHORT-NAME', '')
                for signal_ref in ipdu.findall('.//I-SIGNAL-REF'):
                    signal_name = signal_ref.get('DEST', '')
                    if ipdu_name and signal_name:
                        relationships.append({
                            "type": "SIGNAL_TO_IPDU",
                            "source": signal_name,
                            "target": ipdu_name
                        })
            
            # Gateway relationships
            for gw in root.findall('.//COM-GATEWAY-MAPPING'):
                source = gw.findtext('.//SOURCE-SIGNAL-REF', '')
                dest = gw.findtext('.//DEST-SIGNAL-REF', '')
                if source and dest:
                    relationships.append({
                        "type": "GATEWAY",
                        "source": source,
                        "target": dest
                    })
            
            # Routing relationships
            for path in root.findall('.//PDU-R-ROUTING-PATH'):
                source = path.findtext('.//SOURCE-PDU-REF', '')
                dest = path.findtext('.//DEST-PDU-REF', '')
                if source and dest:
                    relationships.append({
                        "type": "ROUTING",
                        "source": source,
                        "target": dest
                    })
            
        except Exception:
            pass
            
        return relationships
    
    def _validate_communication_config(self, result: AnalysisResult) -> List[Dict[str, Any]]:
        """통신 설정 검증"""
        validations = []
        
        try:
            modules = result.details.get("modules", {})
            
            # COM 검증
            if "COM" in modules:
                com = modules["COM"]
                
                # IPdu without signals
                for ipdu in com.get("ipdus", []):
                    if not ipdu.get("signals"):
                        validations.append({
                            "level": "WARNING",
                            "message": f"IPdu '{ipdu.get('name')}' has no signals"
                        })
                
                # Signal size validation
                for signal in com.get("signals", []):
                    if signal.get("bit_size", 0) > 64:
                        validations.append({
                            "level": "WARNING",
                            "message": f"Signal '{signal.get('name')}' has unusual bit size: {signal.get('bit_size')}"
                        })
            
            # PduR 검증
            if "PduR" in modules:
                pdur = modules["PduR"]
                
                # Routing path validation
                routing_paths = pdur.get("routing_paths", [])
                path_ids = [p.get("routing_path_id") for p in routing_paths]
                if len(path_ids) != len(set(path_ids)):
                    validations.append({
                        "level": "ERROR",
                        "message": "Duplicate routing path IDs detected"
                    })
            
            # CanTp 검증
            if "CanTp" in modules:
                cantp = modules["CanTp"]
                
                # Channel configuration validation
                for channel in cantp.get("channels", []):
                    if channel.get("bs", 0) > 255:
                        validations.append({
                            "level": "WARNING",
                            "message": f"Channel '{channel.get('name')}' has invalid BS value"
                        })
            
        except Exception as e:
            validations.append({
                "level": "ERROR",
                "message": f"Validation error: {str(e)}"
            })
            
        return validations
    
    def _safe_int_conversion(self, value: Any) -> Optional[int]:
        """안전한 정수 변환"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_float_conversion(self, value: Any) -> Optional[float]:
        """안전한 실수 변환"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _generate_summary(self, result: AnalysisResult) -> str:
        """분석 요약 생성"""
        summary_lines = ["Communication Stack Analysis Summary:"]
        
        if result.statistics:
            m = result.statistics
            summary_lines.extend([
                f"  - Modules analyzed: {m.get('total_modules', 0)}",
                f"  - Total IPDUs: {m.get('total_ipdus', 0)}",
                f"  - Total Signals: {m.get('total_signals', 0)}",
                f"  - Routing Paths: {m.get('total_routing_paths', 0)}",
                f"  - Gateway Mappings: {m.get('gateway_mappings', 0)}",
                f"  - TP Channels: {m.get('tp_channels', 0)}",
                f"  - Complexity Score: {m.get('communication_complexity', 0):.2f}/10"
            ])
        
        # Validation summary
        if result.details.get("validation_results"):
            validation_results = result.details.get("validation_results", [])
            errors = sum(1 for v in validation_results if v.get("level") == "ERROR")
            warnings = sum(1 for v in validation_results if v.get("level") == "WARNING")
            summary_lines.append(f"  - Validation: {errors} errors, {warnings} warnings")
        
        return "\n".join(summary_lines)