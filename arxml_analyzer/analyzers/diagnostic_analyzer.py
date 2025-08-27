"""
Diagnostic Analyzer for AUTOSAR ARXML files.

This module analyzes diagnostic-related configurations in ARXML files,
including DCM (Diagnostic Communication Manager) and DEM (Diagnostic Event Manager).
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging

from ..core.analyzer.base_analyzer import (
    BaseAnalyzer,
    AnalysisResult,
    AnalysisMetadata,
    AnalysisLevel,
    AnalysisStatus
)
from ..models.arxml_document import ARXMLDocument

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticService:
    """Represents a diagnostic service."""
    service_id: str
    service_name: str
    service_type: str
    sub_functions: List[str] = field(default_factory=list)
    security_level: Optional[str] = None
    session_types: List[str] = field(default_factory=list)
    timing_values: Dict[str, float] = field(default_factory=dict)
    supported_addresses: List[str] = field(default_factory=list)


@dataclass
class DiagnosticTroubleCode:
    """Represents a Diagnostic Trouble Code (DTC)."""
    dtc_number: str
    dtc_name: str
    severity: Optional[str] = None
    event_name: Optional[str] = None
    failure_threshold: Optional[int] = None
    operation_cycle: Optional[str] = None
    priority: Optional[int] = None
    aging_cycles: Optional[int] = None


@dataclass
class DiagnosticProtocol:
    """Represents a diagnostic protocol configuration."""
    protocol_name: str
    protocol_type: str  # UDS, KWP2000, etc.
    timing_parameters: Dict[str, float] = field(default_factory=dict)
    buffer_size: Optional[int] = None
    max_pdus: Optional[int] = None


@dataclass
class DiagnosticSession:
    """Represents a diagnostic session."""
    session_id: str
    session_name: str
    session_type: str  # DEFAULT, PROGRAMMING, EXTENDED, etc.
    p2_server_max: Optional[float] = None
    p2_star_server_max: Optional[float] = None
    allowed_services: List[str] = field(default_factory=list)


@dataclass
class SecurityAccessLevel:
    """Represents a security access level."""
    level_id: str
    level_name: str
    seed_size: Optional[int] = None
    key_size: Optional[int] = None
    delay_time: Optional[float] = None
    max_attempts: Optional[int] = None
    required_services: List[str] = field(default_factory=list)


class DiagnosticAnalyzer(BaseAnalyzer):
    """
    Analyzer for diagnostic-related ARXML files.
    
    Analyzes DCM (Diagnostic Communication Manager) and DEM (Diagnostic Event Manager)
    configurations to extract diagnostic services, DTCs, protocols, and sessions.
    """
    
    def __init__(self):
        """Initialize the DiagnosticAnalyzer."""
        super().__init__()
        self.analyzer_name = "DiagnosticAnalyzer"
        self.supported_types = ["DIAGNOSTIC", "ECUC", "BSW"]
    
    def analyze(self, document: ARXMLDocument) -> AnalysisResult:
        """
        Analyze diagnostic configurations in the ARXML document.
        
        Args:
            document: The ARXML document to analyze
            
        Returns:
            AnalysisResult containing diagnostic analysis
        """
        start_time = datetime.now()
        
        # Extract diagnostic components
        dcm_config = self.extract_dcm_configuration(document)
        dem_config = self.extract_dem_configuration(document)
        services = self.extract_diagnostic_services(document)
        dtcs = self.extract_dtc_configuration(document)
        protocols = self.extract_diagnostic_protocols(document)
        sessions = self.extract_diagnostic_sessions(document)
        security_levels = self.extract_security_access_levels(document)
        
        # Analyze diagnostic metrics
        service_metrics = self.analyze_service_metrics(services)
        dtc_metrics = self.analyze_dtc_metrics(dtcs)
        protocol_metrics = self.analyze_protocol_metrics(protocols)
        session_metrics = self.analyze_session_metrics(sessions)
        security_metrics = self.analyze_security_metrics(security_levels)
        
        # Validate diagnostic configuration
        validation_results = self.validate_diagnostic_configuration(
            services, dtcs, protocols, sessions, security_levels
        )
        
        # Generate recommendations
        recommendations = self.generate_diagnostic_recommendations(
            service_metrics, dtc_metrics, protocol_metrics, 
            session_metrics, security_metrics, validation_results
        )
        
        # Build analysis result
        analysis_time = (datetime.now() - start_time).total_seconds()
        
        # Get file size safely
        try:
            file_size = document.get_file_size()
        except (FileNotFoundError, AttributeError):
            file_size = 0
        
        metadata = AnalysisMetadata(
            analyzer_name=self.analyzer_name,
            analyzer_version=self.version,
            analysis_timestamp=datetime.now(),
            analysis_duration=analysis_time,
            file_path=Path(document.file_path) if document.file_path else None,
            file_size=file_size,
            arxml_type="DIAGNOSTIC",
            analysis_level=AnalysisLevel.DETAILED,
            status=AnalysisStatus.COMPLETED
        )
        
        summary = {
            "dcm_modules": len(dcm_config),
            "dem_modules": len(dem_config),
            "diagnostic_services": len(services),
            "diagnostic_trouble_codes": len(dtcs),
            "diagnostic_protocols": len(protocols),
            "diagnostic_sessions": len(sessions),
            "security_access_levels": len(security_levels),
            "validation_issues": len(validation_results.get("issues", []))
        }
        
        details = {
            "dcm_configuration": dcm_config,
            "dem_configuration": dem_config,
            "services": [self._service_to_dict(s) for s in services],
            "dtcs": [self._dtc_to_dict(d) for d in dtcs],
            "protocols": [self._protocol_to_dict(p) for p in protocols],
            "sessions": [self._session_to_dict(s) for s in sessions],
            "security_levels": [self._security_to_dict(sl) for sl in security_levels],
            "metrics": {
                "service_metrics": service_metrics,
                "dtc_metrics": dtc_metrics,
                "protocol_metrics": protocol_metrics,
                "session_metrics": session_metrics,
                "security_metrics": security_metrics
            },
            "validation": validation_results
        }
        
        statistics = {
            "total_elements": document.get_element_count(),
            "service_distribution": self._calculate_service_distribution(services),
            "dtc_severity_distribution": self._calculate_dtc_severity_distribution(dtcs),
            "session_type_distribution": self._calculate_session_distribution(sessions),
            "protocol_distribution": self._calculate_protocol_distribution(protocols)
        }
        
        # Find patterns using PatternFinder
        from ..core.analyzer.pattern_finder import PatternFinder, PatternDefinition, PatternType
        pattern_finder = PatternFinder()
        patterns = {}
        
        # Apply diagnostic-specific patterns
        for pattern_def in self.get_patterns():
            if pattern_def["type"] == "XPATH":
                # Create PatternDefinition object
                pd = PatternDefinition(
                    name=pattern_def["description"],
                    pattern_type=PatternType.XPATH,
                    pattern=pattern_def["pattern"],
                    description=pattern_def["description"],
                    severity=pattern_def.get("severity", "info").lower()
                )
                found = pattern_finder.find_xpath_patterns(document.root, [pd])
                if found:
                    patterns[pattern_def["description"]] = [
                        {"location": m.location, "value": m.value} for m in found
                    ]
        
        return AnalysisResult(
            metadata=metadata,
            summary=summary,
            details=details,
            patterns=patterns,
            statistics=statistics,
            recommendations=recommendations
        )
    
    def extract_dcm_configuration(self, document: ARXMLDocument) -> Dict[str, Any]:
        """Extract DCM (Diagnostic Communication Manager) configuration."""
        dcm_config = {}
        
        # Find DCM module definitions (with namespace support)
        dcm_modules = document.xpath(
            "//ECUC-MODULE-DEF[SHORT-NAME='Dcm']"
        ) or document.xpath(
            "//*[local-name()='ECUC-MODULE-DEF'][*[local-name()='SHORT-NAME' and text()='Dcm']]"
        )
        
        for module in dcm_modules:
            module_name = self._get_element_text(module, "SHORT-NAME")
            description = self._get_element_text(module, "L-2")
            
            config = {
                "module_name": module_name,
                "description": description,
                "containers": []
            }
            
            # Extract DCM containers (with namespace support)
            containers = module.xpath(".//ECUC-PARAM-CONF-CONTAINER-DEF") or \
                        module.xpath(".//*[local-name()='ECUC-PARAM-CONF-CONTAINER-DEF']")
            for container in containers:
                cont_name = self._get_element_text(container, "SHORT-NAME")
                config["containers"].append({
                    "name": cont_name,
                    "multiplicity": {
                        "lower": self._get_element_text(container, "LOWER-MULTIPLICITY", "0"),
                        "upper": self._get_element_text(container, "UPPER-MULTIPLICITY", "1")
                    }
                })
            
            dcm_config[module_name] = config
        
        return dcm_config
    
    def extract_dem_configuration(self, document: ARXMLDocument) -> Dict[str, Any]:
        """Extract DEM (Diagnostic Event Manager) configuration."""
        dem_config = {}
        
        # Find DEM module definitions (with namespace support)
        dem_modules = document.xpath(
            "//ECUC-MODULE-DEF[SHORT-NAME='Dem']"
        ) or document.xpath(
            "//*[local-name()='ECUC-MODULE-DEF'][*[local-name()='SHORT-NAME' and text()='Dem']]"
        )
        
        for module in dem_modules:
            module_name = self._get_element_text(module, "SHORT-NAME")
            description = self._get_element_text(module, "L-2")
            
            config = {
                "module_name": module_name,
                "description": description,
                "event_parameters": [],
                "dtc_settings": []
            }
            
            # Extract DEM event parameters
            event_params = module.xpath(".//ECUC-PARAM-CONF-CONTAINER-DEF[contains(SHORT-NAME, 'Event')]")
            for param in event_params:
                config["event_parameters"].append({
                    "name": param.findtext("SHORT-NAME", ""),
                    "type": "EVENT_PARAMETER"
                })
            
            # Extract DTC settings
            dtc_settings = module.xpath(".//ECUC-PARAM-CONF-CONTAINER-DEF[contains(SHORT-NAME, 'Dtc')]")
            for setting in dtc_settings:
                config["dtc_settings"].append({
                    "name": setting.findtext("SHORT-NAME", ""),
                    "type": "DTC_SETTING"
                })
            
            dem_config[module_name] = config
        
        return dem_config
    
    def extract_diagnostic_services(self, document: ARXMLDocument) -> List[DiagnosticService]:
        """Extract diagnostic services from the document."""
        services = []
        
        # Find service tables (with namespace support)
        service_tables = document.xpath(
            "//ECUC-PARAM-CONF-CONTAINER-DEF[contains(SHORT-NAME, 'ServiceTable')]"
        ) or document.xpath(
            "//*[local-name()='ECUC-PARAM-CONF-CONTAINER-DEF'][contains(*[local-name()='SHORT-NAME'], 'ServiceTable')]"
        )
        
        for table in service_tables:
            # Extract individual services
            service_defs = table.xpath(".//ECUC-PARAM-CONF-CONTAINER-DEF[contains(SHORT-NAME, 'Service')]")
            
            for service_def in service_defs:
                service = DiagnosticService(
                    service_id=service_def.findtext(".//DcmDsdServiceId", ""),
                    service_name=service_def.findtext("SHORT-NAME", ""),
                    service_type=self._determine_service_type(service_def)
                )
                
                # Extract sub-functions
                sub_funcs = service_def.xpath(".//ECUC-PARAM-CONF-CONTAINER-DEF[contains(SHORT-NAME, 'SubService')]")
                for sub_func in sub_funcs:
                    service.sub_functions.append(sub_func.findtext("SHORT-NAME", ""))
                
                # Extract security level
                service.security_level = service_def.findtext(".//DcmDsdServiceSecurityLevelRef", None)
                
                # Extract session types
                sessions = service_def.xpath(".//DcmDsdServiceSessionRef")
                service.session_types = [s.text for s in sessions if s.text]
                
                # Extract timing values
                service.timing_values = {
                    "P2ServerMax": self._safe_float_conversion(
                        service_def.findtext(".//DcmDsdServiceP2ServerMax", "0")
                    ),
                    "P2StarServerMax": self._safe_float_conversion(
                        service_def.findtext(".//DcmDsdServiceP2StarServerMax", "0")
                    )
                }
                
                services.append(service)
        
        # Also look for UDS services
        uds_services = document.xpath(
            "//DIAGNOSTIC-SERVICE"
        ) or document.xpath(
            "//*[local-name()='DIAGNOSTIC-SERVICE']"
        )
        
        for uds_service in uds_services:
            service = DiagnosticService(
                service_id=self._get_element_text(uds_service, "SERVICE-ID"),
                service_name=self._get_element_text(uds_service, "SHORT-NAME"),
                service_type="UDS"
            )
            services.append(service)
        
        return services
    
    def extract_dtc_configuration(self, document: ARXMLDocument) -> List[DiagnosticTroubleCode]:
        """Extract Diagnostic Trouble Codes (DTCs) from the document."""
        dtcs = []
        
        # Find DTC definitions (with namespace support)
        dtc_defs = document.xpath(
            "//ECUC-PARAM-CONF-CONTAINER-DEF[contains(SHORT-NAME, 'Dtc')]"
        ) or document.xpath(
            "//*[local-name()='ECUC-PARAM-CONF-CONTAINER-DEF'][contains(*[local-name()='SHORT-NAME'], 'Dtc')]"
        )
        
        for dtc_def in dtc_defs:
            dtc = DiagnosticTroubleCode(
                dtc_number=dtc_def.findtext(".//DemDtcNumber", ""),
                dtc_name=dtc_def.findtext("SHORT-NAME", "")
            )
            
            # Extract severity
            dtc.severity = dtc_def.findtext(".//DemDtcSeverity", None)
            
            # Extract event name
            dtc.event_name = dtc_def.findtext(".//DemEventRef", None)
            
            # Extract failure threshold
            threshold = dtc_def.findtext(".//DemEventFailureThreshold", None)
            if threshold:
                dtc.failure_threshold = self._safe_int_conversion(threshold)
            
            # Extract operation cycle
            dtc.operation_cycle = dtc_def.findtext(".//DemOperationCycleRef", None)
            
            # Extract priority
            priority = dtc_def.findtext(".//DemDtcPriority", None)
            if priority:
                dtc.priority = self._safe_int_conversion(priority)
            
            # Extract aging cycles
            aging = dtc_def.findtext(".//DemAgingCycles", None)
            if aging:
                dtc.aging_cycles = self._safe_int_conversion(aging)
            
            if dtc.dtc_number or dtc.dtc_name:  # Only add valid DTCs
                dtcs.append(dtc)
        
        # Also look for DTC specifications
        dtc_specs = document.xpath(
            "//DIAGNOSTIC-TROUBLE-CODE"
        ) or document.xpath(
            "//*[local-name()='DIAGNOSTIC-TROUBLE-CODE']"
        )
        
        for spec in dtc_specs:
            dtc = DiagnosticTroubleCode(
                dtc_number=self._get_element_text(spec, "TROUBLE-CODE"),
                dtc_name=self._get_element_text(spec, "SHORT-NAME"),
                severity=self._get_element_text(spec, "SEVERITY", None)
            )
            dtcs.append(dtc)
        
        return dtcs
    
    def extract_diagnostic_protocols(self, document: ARXMLDocument) -> List[DiagnosticProtocol]:
        """Extract diagnostic protocol configurations."""
        protocols = []
        
        # Find protocol definitions (with namespace support)
        protocol_defs = document.xpath(
            "//ECUC-PARAM-CONF-CONTAINER-DEF[contains(SHORT-NAME, 'Protocol')]"
        ) or document.xpath(
            "//*[local-name()='ECUC-PARAM-CONF-CONTAINER-DEF'][contains(*[local-name()='SHORT-NAME'], 'Protocol')]"
        )
        
        for protocol_def in protocol_defs:
            protocol = DiagnosticProtocol(
                protocol_name=protocol_def.findtext("SHORT-NAME", ""),
                protocol_type=self._determine_protocol_type(protocol_def)
            )
            
            # Extract timing parameters
            protocol.timing_parameters = {
                "P2ServerMax": self._safe_float_conversion(
                    protocol_def.findtext(".//DcmDslProtocolP2ServerMax", "0")
                ),
                "P2StarServerMax": self._safe_float_conversion(
                    protocol_def.findtext(".//DcmDslProtocolP2StarServerMax", "0")
                ),
                "P3Maximum": self._safe_float_conversion(
                    protocol_def.findtext(".//DcmDslProtocolP3Maximum", "0")
                )
            }
            
            # Extract buffer size
            buffer_size = protocol_def.findtext(".//DcmDslProtocolBufferSize", None)
            if buffer_size:
                protocol.buffer_size = self._safe_int_conversion(buffer_size)
            
            # Extract max PDUs
            max_pdus = protocol_def.findtext(".//DcmDslProtocolMaximumNumberOfPendingDTCs", None)
            if max_pdus:
                protocol.max_pdus = self._safe_int_conversion(max_pdus)
            
            protocols.append(protocol)
        
        # Also look for diagnostic protocols
        diag_protocols = document.xpath(
            "//DIAGNOSTIC-PROTOCOL"
        ) or document.xpath(
            "//*[local-name()='DIAGNOSTIC-PROTOCOL']"
        )
        
        for diag_protocol in diag_protocols:
            protocol = DiagnosticProtocol(
                protocol_name=self._get_element_text(diag_protocol, "SHORT-NAME"),
                protocol_type=self._get_element_text(diag_protocol, "PROTOCOL-KIND", "UNKNOWN")
            )
            protocols.append(protocol)
        
        return protocols
    
    def extract_diagnostic_sessions(self, document: ARXMLDocument) -> List[DiagnosticSession]:
        """Extract diagnostic session configurations."""
        sessions = []
        
        # Find session definitions (with namespace support)
        session_defs = document.xpath(
            "//ECUC-PARAM-CONF-CONTAINER-DEF[contains(SHORT-NAME, 'Session')]"
        ) or document.xpath(
            "//*[local-name()='ECUC-PARAM-CONF-CONTAINER-DEF'][contains(*[local-name()='SHORT-NAME'], 'Session')]"
        )
        
        for session_def in session_defs:
            session = DiagnosticSession(
                session_id=session_def.findtext(".//DcmDspSessionId", ""),
                session_name=session_def.findtext("SHORT-NAME", ""),
                session_type=self._determine_session_type(session_def)
            )
            
            # Extract timing values
            p2_max = session_def.findtext(".//DcmDspSessionP2ServerMax", None)
            if p2_max:
                session.p2_server_max = self._safe_float_conversion(p2_max)
            
            p2_star_max = session_def.findtext(".//DcmDspSessionP2StarServerMax", None)
            if p2_star_max:
                session.p2_star_server_max = self._safe_float_conversion(p2_star_max)
            
            # Extract allowed services
            service_refs = session_def.xpath(".//DcmDspSessionServiceRef")
            session.allowed_services = [ref.text for ref in service_refs if ref.text]
            
            sessions.append(session)
        
        return sessions
    
    def extract_security_access_levels(self, document: ARXMLDocument) -> List[SecurityAccessLevel]:
        """Extract security access level configurations."""
        security_levels = []
        
        # Find security level definitions (with namespace support)
        security_defs = document.xpath(
            "//ECUC-PARAM-CONF-CONTAINER-DEF[contains(SHORT-NAME, 'SecurityLevel')]"
        ) or document.xpath(
            "//*[local-name()='ECUC-PARAM-CONF-CONTAINER-DEF'][contains(*[local-name()='SHORT-NAME'], 'SecurityLevel')]"
        )
        
        for security_def in security_defs:
            security_level = SecurityAccessLevel(
                level_id=security_def.findtext(".//DcmDspSecurityLevelId", ""),
                level_name=security_def.findtext("SHORT-NAME", "")
            )
            
            # Extract seed and key sizes
            seed_size = security_def.findtext(".//DcmDspSecuritySeedSize", None)
            if seed_size:
                security_level.seed_size = self._safe_int_conversion(seed_size)
            
            key_size = security_def.findtext(".//DcmDspSecurityKeySize", None)
            if key_size:
                security_level.key_size = self._safe_int_conversion(key_size)
            
            # Extract delay time
            delay_time = security_def.findtext(".//DcmDspSecurityDelayTime", None)
            if delay_time:
                security_level.delay_time = self._safe_float_conversion(delay_time)
            
            # Extract max attempts
            max_attempts = security_def.findtext(".//DcmDspSecurityMaxAttempts", None)
            if max_attempts:
                security_level.max_attempts = self._safe_int_conversion(max_attempts)
            
            security_levels.append(security_level)
        
        return security_levels
    
    def analyze_service_metrics(self, services: List[DiagnosticService]) -> Dict[str, Any]:
        """Analyze metrics for diagnostic services."""
        if not services:
            return {}
        
        return {
            "total_services": len(services),
            "services_with_subfunctions": len([s for s in services if s.sub_functions]),
            "average_subfunctions": sum(len(s.sub_functions) for s in services) / len(services) if services else 0,
            "secured_services": len([s for s in services if s.security_level]),
            "session_restricted_services": len([s for s in services if s.session_types]),
            "service_types": self._count_service_types(services)
        }
    
    def analyze_dtc_metrics(self, dtcs: List[DiagnosticTroubleCode]) -> Dict[str, Any]:
        """Analyze metrics for DTCs."""
        if not dtcs:
            return {}
        
        severity_counts = {}
        for dtc in dtcs:
            severity = dtc.severity or "UNKNOWN"
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_dtcs": len(dtcs),
            "dtcs_with_events": len([d for d in dtcs if d.event_name]),
            "dtcs_with_thresholds": len([d for d in dtcs if d.failure_threshold]),
            "severity_distribution": severity_counts,
            "average_aging_cycles": sum(d.aging_cycles or 0 for d in dtcs) / len(dtcs) if dtcs else 0,
            "dtcs_with_priority": len([d for d in dtcs if d.priority is not None])
        }
    
    def analyze_protocol_metrics(self, protocols: List[DiagnosticProtocol]) -> Dict[str, Any]:
        """Analyze metrics for diagnostic protocols."""
        if not protocols:
            return {}
        
        protocol_types = {}
        for protocol in protocols:
            ptype = protocol.protocol_type
            protocol_types[ptype] = protocol_types.get(ptype, 0) + 1
        
        return {
            "total_protocols": len(protocols),
            "protocol_types": protocol_types,
            "protocols_with_buffers": len([p for p in protocols if p.buffer_size]),
            "average_buffer_size": sum(p.buffer_size or 0 for p in protocols) / len(protocols) if protocols else 0,
            "protocols_with_timing": len([p for p in protocols if p.timing_parameters])
        }
    
    def analyze_session_metrics(self, sessions: List[DiagnosticSession]) -> Dict[str, Any]:
        """Analyze metrics for diagnostic sessions."""
        if not sessions:
            return {}
        
        session_types = {}
        for session in sessions:
            stype = session.session_type
            session_types[stype] = session_types.get(stype, 0) + 1
        
        return {
            "total_sessions": len(sessions),
            "session_types": session_types,
            "sessions_with_timing": len([s for s in sessions if s.p2_server_max or s.p2_star_server_max]),
            "sessions_with_service_restrictions": len([s for s in sessions if s.allowed_services]),
            "average_allowed_services": sum(len(s.allowed_services) for s in sessions) / len(sessions) if sessions else 0
        }
    
    def analyze_security_metrics(self, security_levels: List[SecurityAccessLevel]) -> Dict[str, Any]:
        """Analyze metrics for security access levels."""
        if not security_levels:
            return {}
        
        return {
            "total_security_levels": len(security_levels),
            "levels_with_delay": len([s for s in security_levels if s.delay_time]),
            "levels_with_max_attempts": len([s for s in security_levels if s.max_attempts]),
            "average_seed_size": sum(s.seed_size or 0 for s in security_levels) / len(security_levels) if security_levels else 0,
            "average_key_size": sum(s.key_size or 0 for s in security_levels) / len(security_levels) if security_levels else 0
        }
    
    def validate_diagnostic_configuration(
        self,
        services: List[DiagnosticService],
        dtcs: List[DiagnosticTroubleCode],
        protocols: List[DiagnosticProtocol],
        sessions: List[DiagnosticSession],
        security_levels: List[SecurityAccessLevel]
    ) -> Dict[str, Any]:
        """Validate the diagnostic configuration."""
        issues = []
        warnings = []
        
        # Check for duplicate service IDs
        service_ids = [s.service_id for s in services if s.service_id]
        duplicate_ids = self._find_duplicates(service_ids)
        if duplicate_ids:
            issues.append(f"Duplicate service IDs found: {duplicate_ids}")
        
        # Check for duplicate DTC numbers
        dtc_numbers = [d.dtc_number for d in dtcs if d.dtc_number]
        duplicate_dtcs = self._find_duplicates(dtc_numbers)
        if duplicate_dtcs:
            issues.append(f"Duplicate DTC numbers found: {duplicate_dtcs}")
        
        # Check for missing timing parameters
        protocols_without_timing = [p.protocol_name for p in protocols if not p.timing_parameters]
        if protocols_without_timing:
            warnings.append(f"Protocols without timing parameters: {protocols_without_timing}")
        
        # Check for sessions without timing
        sessions_without_timing = [s.session_name for s in sessions 
                                  if not s.p2_server_max and not s.p2_star_server_max]
        if sessions_without_timing:
            warnings.append(f"Sessions without timing values: {sessions_without_timing}")
        
        # Check security level consistency
        for level in security_levels:
            if level.seed_size and level.key_size:
                if level.key_size < level.seed_size:
                    warnings.append(f"Security level {level.level_name}: Key size smaller than seed size")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "checks_performed": [
                "Duplicate service IDs",
                "Duplicate DTC numbers",
                "Missing timing parameters",
                "Security level consistency"
            ]
        }
    
    def generate_diagnostic_recommendations(
        self,
        service_metrics: Dict[str, Any],
        dtc_metrics: Dict[str, Any],
        protocol_metrics: Dict[str, Any],
        session_metrics: Dict[str, Any],
        security_metrics: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on diagnostic analysis."""
        recommendations = []
        
        # Service recommendations
        if service_metrics.get("secured_services", 0) == 0:
            recommendations.append("Consider adding security levels to diagnostic services")
        
        if service_metrics.get("average_subfunctions", 0) < 1:
            recommendations.append("Most services lack sub-functions - verify if this is intentional")
        
        # DTC recommendations
        if dtc_metrics.get("dtcs_with_events", 0) < dtc_metrics.get("total_dtcs", 0) * 0.5:
            recommendations.append("Many DTCs lack associated events - consider adding event definitions")
        
        if dtc_metrics.get("dtcs_with_thresholds", 0) < dtc_metrics.get("total_dtcs", 0) * 0.3:
            recommendations.append("Most DTCs lack failure thresholds - consider adding threshold values")
        
        # Protocol recommendations
        if protocol_metrics.get("protocols_with_buffers", 0) < protocol_metrics.get("total_protocols", 0):
            recommendations.append("Some protocols lack buffer size configuration")
        
        # Session recommendations
        if session_metrics.get("sessions_with_timing", 0) < session_metrics.get("total_sessions", 0):
            recommendations.append("Some sessions lack timing configuration")
        
        # Security recommendations
        if security_metrics.get("total_security_levels", 0) == 0:
            recommendations.append("No security levels defined - consider adding security access levels")
        elif security_metrics.get("levels_with_delay", 0) < security_metrics.get("total_security_levels", 0):
            recommendations.append("Some security levels lack delay time configuration")
        
        # Add validation issues to recommendations
        for issue in validation_results.get("issues", []):
            recommendations.append(f"Fix validation issue: {issue}")
        
        for warning in validation_results.get("warnings", []):
            recommendations.append(f"Review warning: {warning}")
        
        return recommendations
    
    def can_analyze(self, document: ARXMLDocument) -> bool:
        """
        Check if this analyzer can handle the document.
        
        Args:
            document: The ARXML document to check
            
        Returns:
            True if the document contains diagnostic configurations
        """
        # Check for DCM module definitions (with and without namespace)
        dcm_modules = document.xpath("//ECUC-MODULE-DEF[SHORT-NAME='Dcm']") or \
                     document.xpath("//*[local-name()='ECUC-MODULE-DEF'][*[local-name()='SHORT-NAME' and text()='Dcm']]")
        if dcm_modules:
            return True
        
        # Check for DEM module definitions (with and without namespace)
        dem_modules = document.xpath("//ECUC-MODULE-DEF[SHORT-NAME='Dem']") or \
                     document.xpath("//*[local-name()='ECUC-MODULE-DEF'][*[local-name()='SHORT-NAME' and text()='Dem']]")
        if dem_modules:
            return True
        
        # Check for diagnostic services
        diag_services = document.xpath("//DIAGNOSTIC-SERVICE") or \
                       document.xpath("//*[local-name()='DIAGNOSTIC-SERVICE']")
        if diag_services:
            return True
        
        # Check for DTCs
        dtcs = document.xpath("//DIAGNOSTIC-TROUBLE-CODE") or \
               document.xpath("//*[local-name()='DIAGNOSTIC-TROUBLE-CODE']")
        if dtcs:
            return True
        
        return False
    
    def get_patterns(self) -> List[Dict[str, Any]]:
        """
        Get the patterns this analyzer looks for.
        
        Returns:
            List of pattern definitions
        """
        return [
            {
                "type": "XPATH",
                "pattern": "//ECUC-MODULE-DEF[SHORT-NAME='Dcm']",
                "description": "DCM module definitions",
                "severity": "INFO"
            },
            {
                "type": "XPATH",
                "pattern": "//ECUC-MODULE-DEF[SHORT-NAME='Dem']",
                "description": "DEM module definitions",
                "severity": "INFO"
            },
            {
                "type": "XPATH",
                "pattern": "//DIAGNOSTIC-SERVICE",
                "description": "Diagnostic service definitions",
                "severity": "INFO"
            },
            {
                "type": "XPATH",
                "pattern": "//DIAGNOSTIC-TROUBLE-CODE",
                "description": "DTC definitions",
                "severity": "INFO"
            },
            {
                "type": "XPATH",
                "pattern": "//ECUC-PARAM-CONF-CONTAINER-DEF[contains(SHORT-NAME, 'SecurityLevel')]",
                "description": "Security level configurations",
                "severity": "INFO"
            }
        ]
    
    # Helper methods
    def _get_element_text(self, element, tag_name: str, default: str = "") -> str:
        """Get text from element with namespace handling."""
        if element is None:
            return default
            
        # Try different approaches
        text = element.findtext(tag_name, None)
        if text:
            return text
            
        # Try with namespace if available
        if hasattr(element, 'nsmap') and element.nsmap:
            ns = element.nsmap.get(None, '')
            if ns:
                text = element.findtext(f".//{{{ns}}}{tag_name}", None)
                if text:
                    return text
            
        # Try with local-name
        try:
            elem = element.find(f".//*[local-name()='{tag_name}']")
            if elem is not None:
                return elem.text or default
        except:
            # If XPath fails, try direct child search
            for child in element:
                if child.tag.endswith(tag_name):
                    return child.text or default
            
        return default
    
    def _determine_service_type(self, service_def) -> str:
        """Determine the type of diagnostic service."""
        short_name = service_def.findtext("SHORT-NAME", "").upper()
        
        if "READ" in short_name:
            return "READ_DATA"
        elif "WRITE" in short_name:
            return "WRITE_DATA"
        elif "CONTROL" in short_name:
            return "IO_CONTROL"
        elif "ROUTINE" in short_name:
            return "ROUTINE_CONTROL"
        elif "CLEAR" in short_name:
            return "CLEAR_DTC"
        elif "TESTER" in short_name:
            return "TESTER_PRESENT"
        else:
            return "GENERIC"
    
    def _determine_protocol_type(self, protocol_def) -> str:
        """Determine the type of diagnostic protocol."""
        short_name = protocol_def.findtext("SHORT-NAME", "").upper()
        
        if "UDS" in short_name:
            return "UDS"
        elif "KWP" in short_name or "KWP2000" in short_name:
            return "KWP2000"
        elif "OBD" in short_name:
            return "OBD"
        elif "WWH" in short_name:
            return "WWH-OBD"
        else:
            return "GENERIC"
    
    def _determine_session_type(self, session_def) -> str:
        """Determine the type of diagnostic session."""
        short_name = session_def.findtext("SHORT-NAME", "").upper()
        session_id = session_def.findtext(".//DcmDspSessionId", "")
        
        if "DEFAULT" in short_name or session_id == "0x01":
            return "DEFAULT"
        elif "PROGRAMMING" in short_name or session_id == "0x02":
            return "PROGRAMMING"
        elif "EXTENDED" in short_name or session_id == "0x03":
            return "EXTENDED"
        elif "SAFETY" in short_name or session_id == "0x04":
            return "SAFETY_SYSTEM"
        else:
            return "VENDOR_SPECIFIC"
    
    def _count_service_types(self, services: List[DiagnosticService]) -> Dict[str, int]:
        """Count services by type."""
        type_counts = {}
        for service in services:
            stype = service.service_type
            type_counts[stype] = type_counts.get(stype, 0) + 1
        return type_counts
    
    def _find_duplicates(self, items: List[str]) -> List[str]:
        """Find duplicate items in a list."""
        seen = set()
        duplicates = set()
        for item in items:
            if item in seen:
                duplicates.add(item)
            seen.add(item)
        return list(duplicates)
    
    def _safe_int_conversion(self, value: str) -> Optional[int]:
        """Safely convert string to integer."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_float_conversion(self, value: str) -> float:
        """Safely convert string to float."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _service_to_dict(self, service: DiagnosticService) -> Dict[str, Any]:
        """Convert DiagnosticService to dictionary."""
        return {
            "service_id": service.service_id,
            "service_name": service.service_name,
            "service_type": service.service_type,
            "sub_functions": service.sub_functions,
            "security_level": service.security_level,
            "session_types": service.session_types,
            "timing_values": service.timing_values,
            "supported_addresses": service.supported_addresses
        }
    
    def _dtc_to_dict(self, dtc: DiagnosticTroubleCode) -> Dict[str, Any]:
        """Convert DiagnosticTroubleCode to dictionary."""
        return {
            "dtc_number": dtc.dtc_number,
            "dtc_name": dtc.dtc_name,
            "severity": dtc.severity,
            "event_name": dtc.event_name,
            "failure_threshold": dtc.failure_threshold,
            "operation_cycle": dtc.operation_cycle,
            "priority": dtc.priority,
            "aging_cycles": dtc.aging_cycles
        }
    
    def _protocol_to_dict(self, protocol: DiagnosticProtocol) -> Dict[str, Any]:
        """Convert DiagnosticProtocol to dictionary."""
        return {
            "protocol_name": protocol.protocol_name,
            "protocol_type": protocol.protocol_type,
            "timing_parameters": protocol.timing_parameters,
            "buffer_size": protocol.buffer_size,
            "max_pdus": protocol.max_pdus
        }
    
    def _session_to_dict(self, session: DiagnosticSession) -> Dict[str, Any]:
        """Convert DiagnosticSession to dictionary."""
        return {
            "session_id": session.session_id,
            "session_name": session.session_name,
            "session_type": session.session_type,
            "p2_server_max": session.p2_server_max,
            "p2_star_server_max": session.p2_star_server_max,
            "allowed_services": session.allowed_services
        }
    
    def _security_to_dict(self, security_level: SecurityAccessLevel) -> Dict[str, Any]:
        """Convert SecurityAccessLevel to dictionary."""
        return {
            "level_id": security_level.level_id,
            "level_name": security_level.level_name,
            "seed_size": security_level.seed_size,
            "key_size": security_level.key_size,
            "delay_time": security_level.delay_time,
            "max_attempts": security_level.max_attempts,
            "required_services": security_level.required_services
        }
    
    def _calculate_service_distribution(self, services: List[DiagnosticService]) -> Dict[str, int]:
        """Calculate distribution of services by type."""
        return self._count_service_types(services)
    
    def _calculate_dtc_severity_distribution(self, dtcs: List[DiagnosticTroubleCode]) -> Dict[str, int]:
        """Calculate distribution of DTCs by severity."""
        severity_counts = {}
        for dtc in dtcs:
            severity = dtc.severity or "UNKNOWN"
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return severity_counts
    
    def _calculate_session_distribution(self, sessions: List[DiagnosticSession]) -> Dict[str, int]:
        """Calculate distribution of sessions by type."""
        session_counts = {}
        for session in sessions:
            stype = session.session_type
            session_counts[stype] = session_counts.get(stype, 0) + 1
        return session_counts
    
    def _calculate_protocol_distribution(self, protocols: List[DiagnosticProtocol]) -> Dict[str, int]:
        """Calculate distribution of protocols by type."""
        protocol_counts = {}
        for protocol in protocols:
            ptype = protocol.protocol_type
            protocol_counts[ptype] = protocol_counts.get(ptype, 0) + 1
        return protocol_counts