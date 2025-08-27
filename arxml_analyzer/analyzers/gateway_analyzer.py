"""Gateway analyzer for ARXML files.

Analyzes gateway-related configurations including:
- PDU routing paths
- Signal gateway configurations
- Network interface mappings
- Protocol conversions
- Multicast configurations
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from lxml import etree

from ..core.analyzer.base_analyzer import (
    BaseAnalyzer,
    AnalysisResult,
    AnalysisMetadata,
    AnalysisLevel,
    AnalysisStatus
)
from ..core.analyzer.pattern_finder import PatternFinder, PatternType, PatternDefinition
from ..models.arxml_document import ARXMLDocument
from ..utils.exceptions import AnalysisError


@dataclass
class RoutingPath:
    """Represents a PDU routing path."""
    name: str
    source_pdu: str
    destination_pdu: str
    source_module: str
    destination_module: str
    routing_type: str  # IF, TP, MULTICAST
    gateway_type: str  # ON_THE_FLY, FIFO
    buffer_size: Optional[int] = None
    threshold: Optional[int] = None


@dataclass
class SignalGateway:
    """Represents a signal gateway configuration."""
    name: str
    source_signal: str
    destination_signal: str
    source_pdu: str
    destination_pdu: str
    transformation: Optional[str] = None
    update_indication: bool = False


@dataclass
class NetworkInterface:
    """Represents a network interface."""
    name: str
    interface_type: str  # CAN, LIN, FLEXRAY, ETHERNET
    controller_ref: str
    cluster_ref: Optional[str] = None
    vlan_id: Optional[int] = None
    supported_protocols: List[str] = field(default_factory=list)


@dataclass
class ProtocolConversion:
    """Represents protocol conversion configuration."""
    name: str
    source_protocol: str
    destination_protocol: str
    conversion_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)


class GatewayAnalyzer(BaseAnalyzer):
    """Analyzer for Gateway ARXML configurations.
    
    Analyzes:
    - PDU routing configurations
    - Signal gateway mappings
    - Network interfaces and clusters
    - Protocol conversions
    - Multicast groups
    - Gateway performance metrics
    """
    
    def __init__(self):
        """Initialize the Gateway analyzer."""
        super().__init__()
        self.analyzer_name = "GatewayAnalyzer"
        self.analyzer_version = "1.0.0"
        self.supported_arxml_types = ["GATEWAY", "COMMUNICATION", "SYSTEM"]
        
    def can_analyze(self, document: ARXMLDocument) -> bool:
        """Check if this analyzer can handle the given document.
        
        Args:
            document: The ARXML document to check
            
        Returns:
            True if document contains gateway configurations
        """
        # Check for gateway-related elements
        # Note: Using local-name() to handle namespace issues
        gateway_indicators = [
            ".//*[local-name()='AR-PACKAGE']/*[local-name()='SHORT-NAME'][text()='PduR']/..",
            ".//*[local-name()='PDU-R']",
            ".//*[local-name()='GATEWAY-MODULE-INSTANTIATION']",
            ".//*[local-name()='I-PDU-ROUTING']",
            ".//*[local-name()='SIGNAL-GATEWAY']",
            ".//*[local-name()='ROUTING-PATH']",
            ".//*[local-name()='ROUTING-PATH-GROUP']",
            ".//*[local-name()='TP-CONNECTION']",
            ".//*[local-name()='GATEWAY-MAPPING']",
            ".//*[local-name()='PROTOCOL-CONVERSION']",
            ".//*[local-name()='MULTICAST-GROUP']"
        ]
        
        for xpath in gateway_indicators:
            if document.xpath(xpath):
                return True
                
        return False
        
    def analyze(self, document: ARXMLDocument) -> AnalysisResult:
        """Analyze gateway configurations in the ARXML document.
        
        Args:
            document: The ARXML document to analyze
            
        Returns:
            Analysis results containing gateway information
        """
        start_time = datetime.now()
        
        try:
            # Extract gateway components
            routing_paths = self._extract_routing_paths(document)
            signal_gateways = self._extract_signal_gateways(document)
            network_interfaces = self._extract_network_interfaces(document)
            protocol_conversions = self._extract_protocol_conversions(document)
            multicast_groups = self._extract_multicast_groups(document)
            
            # Analyze gateway metrics
            gateway_metrics = self._analyze_gateway_metrics(
                routing_paths, signal_gateways, network_interfaces
            )
            
            # Analyze routing complexity
            routing_complexity = self._analyze_routing_complexity(routing_paths)
            
            # Validate gateway configuration
            validation_results = self._validate_gateway_configuration(
                routing_paths, signal_gateways, network_interfaces
            )
            
            # Find patterns
            patterns = self._find_gateway_patterns(document)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                gateway_metrics, routing_complexity, validation_results
            )
            
            # Build results
            summary = {
                "total_routing_paths": len(routing_paths),
                "total_signal_gateways": len(signal_gateways),
                "total_network_interfaces": len(network_interfaces),
                "total_protocol_conversions": len(protocol_conversions),
                "total_multicast_groups": len(multicast_groups),
                "routing_types": self._count_routing_types(routing_paths),
                "network_types": self._count_network_types(network_interfaces),
                "gateway_load": gateway_metrics.get("gateway_load", 0),
                "validation_status": "PASSED" if not validation_results.get("errors") else "FAILED"
            }
            
            details = {
                "routing_paths": [self._routing_path_to_dict(rp) for rp in routing_paths],
                "signal_gateways": [self._signal_gateway_to_dict(sg) for sg in signal_gateways],
                "network_interfaces": [self._network_interface_to_dict(ni) for ni in network_interfaces],
                "protocol_conversions": [self._protocol_conversion_to_dict(pc) for pc in protocol_conversions],
                "multicast_groups": multicast_groups,
                "gateway_metrics": gateway_metrics,
                "routing_complexity": routing_complexity,
                "validation_results": validation_results
            }
            
            statistics = {
                "routing_statistics": self._calculate_routing_statistics(routing_paths),
                "signal_statistics": self._calculate_signal_statistics(signal_gateways),
                "network_statistics": self._calculate_network_statistics(network_interfaces),
                "performance_metrics": self._calculate_performance_metrics(
                    routing_paths, signal_gateways
                )
            }
            
            # Create metadata
            try:
                file_size = document.get_file_size()
            except:
                file_size = 0  # For test documents without actual files
            
            metadata = AnalysisMetadata(
                analyzer_name=self.analyzer_name,
                analyzer_version=self.analyzer_version,
                analysis_timestamp=start_time,
                analysis_duration=(datetime.now() - start_time).total_seconds(),
                file_path=Path(document.file_path),
                file_size=file_size,
                arxml_type="GATEWAY",
                analysis_level=AnalysisLevel.DETAILED,
                status=AnalysisStatus.SUCCESS if not validation_results.get("errors") else AnalysisStatus.WARNING
            )
            
            return AnalysisResult(
                metadata=metadata,
                summary=summary,
                details=details,
                patterns=patterns,
                statistics=statistics,
                recommendations=recommendations
            )
            
        except Exception as e:
            raise AnalysisError(f"Gateway analysis failed: {str(e)}")
            
    def _extract_routing_paths(self, document: ARXMLDocument) -> List[RoutingPath]:
        """Extract PDU routing paths from the document."""
        routing_paths = []
        
        # Extract routing paths from PduR configuration
        for path in document.xpath(".//*[local-name()='ROUTING-PATH']"):
            # Get SHORT-NAME
            name_list = path.xpath(".//*[local-name()='SHORT-NAME']/text()")
            name = name_list[0] if name_list else ""
            
            # Get SOURCE and DESTINATION elements
            source_list = path.xpath(".//*[local-name()='SOURCE']")
            dest_list = path.xpath(".//*[local-name()='DESTINATION']")
            
            if source_list and dest_list:
                source = source_list[0]
                dest = dest_list[0]
                
                # Extract source info
                source_pdu_list = source.xpath(".//*[local-name()='SOURCE-PDU-REF']/text()")
                source_pdu = source_pdu_list[0].split("/")[-1] if source_pdu_list else ""
                
                source_module_list = source.xpath(".//*[local-name()='SOURCE-MODULE']/text()")
                source_module = source_module_list[0] if source_module_list else ""
                
                # Extract destination info
                dest_pdu_list = dest.xpath(".//*[local-name()='DESTINATION-PDU-REF']/text()")
                dest_pdu = dest_pdu_list[0].split("/")[-1] if dest_pdu_list else ""
                
                dest_module_list = dest.xpath(".//*[local-name()='DESTINATION-MODULE']/text()")
                dest_module = dest_module_list[0] if dest_module_list else ""
                
                # Extract routing type and gateway type
                routing_type_list = path.xpath(".//*[local-name()='ROUTING-TYPE']/text()")
                routing_type = routing_type_list[0] if routing_type_list else "IF"
                
                gateway_type_list = path.xpath(".//*[local-name()='GATEWAY-TYPE']/text()")
                gateway_type = gateway_type_list[0] if gateway_type_list else "ON_THE_FLY"
                
                # Extract buffer size and threshold
                buffer_list = path.xpath(".//*[local-name()='BUFFER-SIZE']/text()")
                buffer_size = self._safe_int(buffer_list[0] if buffer_list else None)
                
                threshold_list = path.xpath(".//*[local-name()='THRESHOLD']/text()")
                threshold = self._safe_int(threshold_list[0] if threshold_list else None)
                
                routing_path = RoutingPath(
                    name=name,
                    source_pdu=source_pdu,
                    destination_pdu=dest_pdu,
                    source_module=source_module,
                    destination_module=dest_module,
                    routing_type=routing_type,
                    gateway_type=gateway_type,
                    buffer_size=buffer_size,
                    threshold=threshold
                )
                routing_paths.append(routing_path)
                
        return routing_paths
        
    def _extract_signal_gateways(self, document: ARXMLDocument) -> List[SignalGateway]:
        """Extract signal gateway configurations."""
        signal_gateways = []
        
        # Use XPath with local-name() to be namespace-agnostic
        gateways = document.root.xpath(".//*[local-name()='SIGNAL-GATEWAY']")
        
        for gateway in gateways:
            # Get SHORT-NAME
            name_list = gateway.xpath(".//*[local-name()='SHORT-NAME']/text()")
            name = name_list[0] if name_list else ""
            
            # Get SOURCE-SIGNAL and DESTINATION-SIGNAL elements
            source_list = gateway.xpath(".//*[local-name()='SOURCE-SIGNAL']")
            dest_list = gateway.xpath(".//*[local-name()='DESTINATION-SIGNAL']")
            
            if source_list and dest_list:
                source = source_list[0]
                dest = dest_list[0]
                
                # Extract source signal info
                source_signal_list = source.xpath(".//*[local-name()='SIGNAL-REF']/text()")
                source_signal = source_signal_list[0].split("/")[-1] if source_signal_list else ""
                
                source_pdu_list = source.xpath(".//*[local-name()='I-PDU-REF']/text()")
                source_pdu = source_pdu_list[0].split("/")[-1] if source_pdu_list else ""
                
                # Extract destination signal info
                dest_signal_list = dest.xpath(".//*[local-name()='SIGNAL-REF']/text()")
                dest_signal = dest_signal_list[0].split("/")[-1] if dest_signal_list else ""
                
                dest_pdu_list = dest.xpath(".//*[local-name()='I-PDU-REF']/text()")
                dest_pdu = dest_pdu_list[0].split("/")[-1] if dest_pdu_list else ""
                
                # Extract transformation and update indication
                transformation_list = gateway.xpath(".//*[local-name()='TRANSFORMATION']/text()")
                transformation = transformation_list[0] if transformation_list else None
                
                update_indication_list = gateway.xpath(".//*[local-name()='UPDATE-INDICATION']/text()")
                update_indication = update_indication_list[0].lower() == "true" if update_indication_list else False
                
                signal_gateway = SignalGateway(
                    name=name,
                    source_signal=source_signal,
                    destination_signal=dest_signal,
                    source_pdu=source_pdu,
                    destination_pdu=dest_pdu,
                    transformation=transformation,
                    update_indication=update_indication
                )
                signal_gateways.append(signal_gateway)
                
        return signal_gateways
        
    def _extract_network_interfaces(self, document: ARXMLDocument) -> List[NetworkInterface]:
        """Extract network interface configurations."""
        interfaces = []
        
        # Extract CAN interfaces
        can_interfaces = document.root.xpath(".//*[local-name()='CAN-CLUSTER']")
        for can_if in can_interfaces:
            name_list = can_if.xpath(".//*[local-name()='SHORT-NAME']/text()")
            name = name_list[0] if name_list else ""
            
            controller_ref_list = can_if.xpath(".//*[local-name()='CAN-CONTROLLER-REF']/text()")
            controller_ref = controller_ref_list[0] if controller_ref_list else ""
            
            interface = NetworkInterface(
                name=name,
                interface_type="CAN",
                controller_ref=controller_ref,
                cluster_ref=name,
                supported_protocols=["CAN", "CAN-FD"]
            )
            interfaces.append(interface)
            
        # Extract Ethernet interfaces
        eth_interfaces = document.root.xpath(".//*[local-name()='ETHERNET-CLUSTER']")
        for eth_if in eth_interfaces:
            name_list = eth_if.xpath(".//*[local-name()='SHORT-NAME']/text()")
            name = name_list[0] if name_list else ""
            
            controller_ref_list = eth_if.xpath(".//*[local-name()='ETHERNET-CONTROLLER-REF']/text()")
            controller_ref = controller_ref_list[0] if controller_ref_list else ""
            
            vlan_id_list = eth_if.xpath(".//*[local-name()='VLAN-ID']/text()")
            vlan_id = self._safe_int(vlan_id_list[0] if vlan_id_list else None)
            
            interface = NetworkInterface(
                name=name,
                interface_type="ETHERNET",
                controller_ref=controller_ref,
                cluster_ref=name,
                vlan_id=vlan_id,
                supported_protocols=["TCP", "UDP", "SOME/IP", "DoIP"]
            )
            interfaces.append(interface)
            
        # Extract LIN interfaces
        lin_interfaces = document.root.xpath(".//*[local-name()='LIN-CLUSTER']")
        for lin_if in lin_interfaces:
            name_list = lin_if.xpath(".//*[local-name()='SHORT-NAME']/text()")
            name = name_list[0] if name_list else ""
            
            controller_ref_list = lin_if.xpath(".//*[local-name()='LIN-CONTROLLER-REF']/text()")
            controller_ref = controller_ref_list[0] if controller_ref_list else ""
            
            interface = NetworkInterface(
                name=name,
                interface_type="LIN",
                controller_ref=controller_ref,
                cluster_ref=name,
                supported_protocols=["LIN"]
            )
            interfaces.append(interface)
            
        # Extract FlexRay interfaces
        fr_interfaces = document.root.xpath(".//*[local-name()='FLEXRAY-CLUSTER']")
        for fr_if in fr_interfaces:
            name_list = fr_if.xpath(".//*[local-name()='SHORT-NAME']/text()")
            name = name_list[0] if name_list else ""
            
            controller_ref_list = fr_if.xpath(".//*[local-name()='FLEXRAY-CONTROLLER-REF']/text()")
            controller_ref = controller_ref_list[0] if controller_ref_list else ""
            
            interface = NetworkInterface(
                name=name,
                interface_type="FLEXRAY",
                controller_ref=controller_ref,
                cluster_ref=name,
                supported_protocols=["FLEXRAY"]
            )
            interfaces.append(interface)
            
        return interfaces
        
    def _extract_protocol_conversions(self, document: ARXMLDocument) -> List[ProtocolConversion]:
        """Extract protocol conversion configurations."""
        conversions = []
        
        conv_elements = document.root.xpath(".//*[local-name()='PROTOCOL-CONVERSION']")
        for conversion in conv_elements:
            name_list = conversion.xpath(".//*[local-name()='SHORT-NAME']/text()")
            name = name_list[0] if name_list else ""
            
            source_proto_list = conversion.xpath(".//*[local-name()='SOURCE-PROTOCOL']/text()")
            source_proto = source_proto_list[0] if source_proto_list else ""
            
            dest_proto_list = conversion.xpath(".//*[local-name()='DESTINATION-PROTOCOL']/text()")
            dest_proto = dest_proto_list[0] if dest_proto_list else ""
            
            conv_type_list = conversion.xpath(".//*[local-name()='CONVERSION-TYPE']/text()")
            conv_type = conv_type_list[0] if conv_type_list else ""
            
            params = {}
            param_elements = conversion.xpath(".//*[local-name()='PARAMETER']")
            for param in param_elements:
                param_name_list = param.xpath(".//*[local-name()='SHORT-NAME']/text()")
                param_name = param_name_list[0] if param_name_list else ""
                
                param_value_list = param.xpath(".//*[local-name()='VALUE']/text()")
                param_value = param_value_list[0] if param_value_list else ""
                
                if param_name:
                    params[param_name] = param_value
                    
            protocol_conversion = ProtocolConversion(
                name=name,
                source_protocol=source_proto,
                destination_protocol=dest_proto,
                conversion_type=conv_type,
                parameters=params
            )
            conversions.append(protocol_conversion)
            
        return conversions
        
    def _extract_multicast_groups(self, document: ARXMLDocument) -> List[Dict[str, Any]]:
        """Extract multicast group configurations."""
        multicast_groups = []
        
        groups = document.root.xpath(".//*[local-name()='MULTICAST-GROUP']")
        for group in groups:
            name_list = group.xpath(".//*[local-name()='SHORT-NAME']/text()")
            name = name_list[0] if name_list else ""
            
            group_addr_list = group.xpath(".//*[local-name()='GROUP-ADDRESS']/text()")
            group_address = group_addr_list[0] if group_addr_list else ""
            
            port_list = group.xpath(".//*[local-name()='PORT']/text()")
            port = self._safe_int(port_list[0] if port_list else None)
            
            multicast = {
                "name": name,
                "group_address": group_address,
                "port": port,
                "members": []
            }
            
            members = group.xpath(".//*[local-name()='MEMBER']")
            for member in members:
                member_name_list = member.xpath(".//*[local-name()='SHORT-NAME']/text()")
                member_name = member_name_list[0] if member_name_list else ""
                
                member_addr_list = member.xpath(".//*[local-name()='IP-ADDRESS']/text()")
                member_address = member_addr_list[0] if member_addr_list else ""
                
                multicast["members"].append({
                    "name": member_name,
                    "address": member_address
                })
                
            multicast_groups.append(multicast)
            
        return multicast_groups
        
    def _analyze_gateway_metrics(
        self, 
        routing_paths: List[RoutingPath],
        signal_gateways: List[SignalGateway],
        network_interfaces: List[NetworkInterface]
    ) -> Dict[str, Any]:
        """Analyze gateway performance metrics."""
        metrics = {}
        
        # Calculate gateway load
        total_routes = len(routing_paths) + len(signal_gateways)
        metrics["gateway_load"] = total_routes
        
        # Calculate routing distribution
        routing_by_type = {}
        for path in routing_paths:
            routing_by_type[path.routing_type] = routing_by_type.get(path.routing_type, 0) + 1
        metrics["routing_distribution"] = routing_by_type
        
        # Calculate network utilization
        network_utilization = {}
        for interface in network_interfaces:
            network_utilization[interface.interface_type] = network_utilization.get(interface.interface_type, 0) + 1
        metrics["network_utilization"] = network_utilization
        
        # Calculate buffer requirements
        total_buffer = sum(path.buffer_size or 0 for path in routing_paths)
        metrics["total_buffer_size"] = total_buffer
        
        # Calculate protocol diversity
        protocols = set()
        for interface in network_interfaces:
            protocols.update(interface.supported_protocols)
        metrics["protocol_diversity"] = len(protocols)
        metrics["supported_protocols"] = list(protocols)
        
        return metrics
        
    def _analyze_routing_complexity(self, routing_paths: List[RoutingPath]) -> Dict[str, Any]:
        """Analyze routing complexity metrics."""
        complexity = {}
        
        # Calculate routing fan-out
        source_fanout = {}
        dest_fanin = {}
        
        for path in routing_paths:
            source_fanout[path.source_pdu] = source_fanout.get(path.source_pdu, 0) + 1
            dest_fanin[path.destination_pdu] = dest_fanin.get(path.destination_pdu, 0) + 1
            
        complexity["max_fanout"] = max(source_fanout.values()) if source_fanout else 0
        complexity["avg_fanout"] = sum(source_fanout.values()) / len(source_fanout) if source_fanout else 0
        complexity["max_fanin"] = max(dest_fanin.values()) if dest_fanin else 0
        complexity["avg_fanin"] = sum(dest_fanin.values()) / len(dest_fanin) if dest_fanin else 0
        
        # Identify routing hotspots
        hotspots = [pdu for pdu, count in source_fanout.items() if count > 5]
        complexity["routing_hotspots"] = hotspots
        
        # Calculate routing depth
        module_transitions = set()
        for path in routing_paths:
            if path.source_module and path.destination_module:
                module_transitions.add((path.source_module, path.destination_module))
        complexity["module_transitions"] = len(module_transitions)
        
        return complexity
        
    def _validate_gateway_configuration(
        self,
        routing_paths: List[RoutingPath],
        signal_gateways: List[SignalGateway],
        network_interfaces: List[NetworkInterface]
    ) -> Dict[str, Any]:
        """Validate gateway configuration for consistency and correctness."""
        validation = {"errors": [], "warnings": [], "info": []}
        
        # Check for duplicate routing paths
        seen_routes = set()
        for path in routing_paths:
            route_key = (path.source_pdu, path.destination_pdu)
            if route_key in seen_routes:
                validation["errors"].append(
                    f"Duplicate routing path: {path.source_pdu} -> {path.destination_pdu}"
                )
            seen_routes.add(route_key)
            
        # Check for circular routing
        for path in routing_paths:
            if path.source_pdu == path.destination_pdu:
                validation["errors"].append(
                    f"Circular routing detected: {path.name}"
                )
                
        # Check buffer configurations
        for path in routing_paths:
            if path.routing_type == "TP" and not path.buffer_size:
                validation["warnings"].append(
                    f"TP routing path '{path.name}' without buffer size configuration"
                )
                
        # Check signal gateway consistency
        signal_pdus = set()
        for sg in signal_gateways:
            signal_pdus.add(sg.source_pdu)
            signal_pdus.add(sg.destination_pdu)
            
        # Check network interface coverage
        if len(network_interfaces) < 2:
            validation["warnings"].append(
                "Gateway requires at least 2 network interfaces"
            )
            
        # Check for unused interfaces
        used_interfaces = set()
        for path in routing_paths:
            if path.source_module:
                used_interfaces.add(path.source_module)
            if path.destination_module:
                used_interfaces.add(path.destination_module)
                
        for interface in network_interfaces:
            if interface.name not in used_interfaces:
                validation["info"].append(
                    f"Network interface '{interface.name}' appears to be unused"
                )
                
        return validation
        
    def _find_gateway_patterns(self, document: ARXMLDocument) -> Dict[str, List[Dict]]:
        """Find gateway-specific patterns in the document."""
        pattern_finder = PatternFinder()
        patterns = {}
        
        # Define gateway-specific patterns
        gateway_patterns = [
            PatternDefinition(
                name="routing_path_pattern",
                pattern=".//ROUTING-PATH",
                pattern_type=PatternType.XPATH,
                description="PDU routing path definitions"
            ),
            PatternDefinition(
                name="signal_gateway_pattern",
                pattern=".//SIGNAL-GATEWAY",
                pattern_type=PatternType.XPATH,
                description="Signal gateway mappings"
            ),
            PatternDefinition(
                name="multicast_pattern",
                pattern=".//MULTICAST-GROUP",
                pattern_type=PatternType.XPATH,
                description="Multicast group configurations"
            ),
            PatternDefinition(
                name="protocol_conversion_pattern",
                pattern=".//PROTOCOL-CONVERSION",
                pattern_type=PatternType.XPATH,
                description="Protocol conversion definitions"
            )
        ]
        
        # Find patterns
        for pattern_def in gateway_patterns:
            found = pattern_finder.find_xpath_patterns(document.root, [pattern_def])
            if found:
                patterns[pattern_def.name] = [
                    {
                        "location": match.location,
                        "value": str(match.value) if match.value else "",
                        "confidence": match.confidence,
                        "context": match.context
                    }
                    for match in found
                ]
                
        # Find structural patterns
        structural = pattern_finder.find_structural_patterns(document.root)
        if structural:
            patterns["structural"] = [
                {
                    "location": match.location,
                    "value": str(match.value) if match.value else "",
                    "pattern_type": match.pattern_type.value if hasattr(match.pattern_type, 'value') else str(match.pattern_type),
                    "confidence": match.confidence
                }
                for match in structural
            ]
            
        return patterns
        
    def _generate_recommendations(
        self,
        metrics: Dict[str, Any],
        complexity: Dict[str, Any],
        validation: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Check gateway load
        if metrics.get("gateway_load", 0) > 1000:
            recommendations.append(
                "High gateway load detected. Consider distributing routing across multiple gateways."
            )
            
        # Check routing complexity
        if complexity.get("max_fanout", 0) > 10:
            recommendations.append(
                f"High routing fan-out detected (max: {complexity['max_fanout']}). "
                "Consider optimizing routing topology."
            )
            
        # Check for routing hotspots
        if complexity.get("routing_hotspots"):
            recommendations.append(
                f"Routing hotspots detected: {', '.join(complexity['routing_hotspots'])}. "
                "Consider load balancing."
            )
            
        # Check buffer utilization
        if metrics.get("total_buffer_size", 0) > 1048576:  # 1MB
            recommendations.append(
                "Large total buffer size. Review buffer requirements and optimize where possible."
            )
            
        # Check validation errors
        if validation.get("errors"):
            recommendations.append(
                f"Critical configuration errors found: {len(validation['errors'])} errors. "
                "Review and fix configuration issues."
            )
            
        # Check protocol diversity
        if metrics.get("protocol_diversity", 0) > 5:
            recommendations.append(
                "High protocol diversity. Ensure proper protocol conversion configurations."
            )
            
        # Add positive feedback if configuration is good
        if not validation.get("errors") and not validation.get("warnings"):
            recommendations.append(
                "Gateway configuration appears to be well-structured and consistent."
            )
            
        return recommendations
        
    def _count_routing_types(self, routing_paths: List[RoutingPath]) -> Dict[str, int]:
        """Count routing paths by type."""
        counts = {}
        for path in routing_paths:
            counts[path.routing_type] = counts.get(path.routing_type, 0) + 1
        return counts
        
    def _count_network_types(self, interfaces: List[NetworkInterface]) -> Dict[str, int]:
        """Count network interfaces by type."""
        counts = {}
        for interface in interfaces:
            counts[interface.interface_type] = counts.get(interface.interface_type, 0) + 1
        return counts
        
    def _calculate_routing_statistics(self, routing_paths: List[RoutingPath]) -> Dict[str, Any]:
        """Calculate routing statistics."""
        stats = {
            "total_paths": len(routing_paths),
            "if_routing_count": sum(1 for p in routing_paths if p.routing_type == "IF"),
            "tp_routing_count": sum(1 for p in routing_paths if p.routing_type == "TP"),
            "multicast_count": sum(1 for p in routing_paths if p.routing_type == "MULTICAST"),
            "buffered_paths": sum(1 for p in routing_paths if p.buffer_size),
            "total_buffer_size": sum(p.buffer_size or 0 for p in routing_paths)
        }
        return stats
        
    def _calculate_signal_statistics(self, signal_gateways: List[SignalGateway]) -> Dict[str, Any]:
        """Calculate signal gateway statistics."""
        stats = {
            "total_gateways": len(signal_gateways),
            "with_transformation": sum(1 for sg in signal_gateways if sg.transformation),
            "with_update_indication": sum(1 for sg in signal_gateways if sg.update_indication),
            "unique_source_signals": len(set(sg.source_signal for sg in signal_gateways)),
            "unique_dest_signals": len(set(sg.destination_signal for sg in signal_gateways))
        }
        return stats
        
    def _calculate_network_statistics(self, interfaces: List[NetworkInterface]) -> Dict[str, Any]:
        """Calculate network interface statistics."""
        stats = {
            "total_interfaces": len(interfaces),
            "can_interfaces": sum(1 for i in interfaces if i.interface_type == "CAN"),
            "ethernet_interfaces": sum(1 for i in interfaces if i.interface_type == "ETHERNET"),
            "lin_interfaces": sum(1 for i in interfaces if i.interface_type == "LIN"),
            "flexray_interfaces": sum(1 for i in interfaces if i.interface_type == "FLEXRAY"),
            "with_vlan": sum(1 for i in interfaces if i.vlan_id is not None)
        }
        return stats
        
    def _calculate_performance_metrics(
        self,
        routing_paths: List[RoutingPath],
        signal_gateways: List[SignalGateway]
    ) -> Dict[str, Any]:
        """Calculate gateway performance metrics."""
        metrics = {
            "estimated_latency": self._estimate_latency(routing_paths),
            "estimated_throughput": self._estimate_throughput(routing_paths, signal_gateways),
            "routing_efficiency": self._calculate_routing_efficiency(routing_paths),
            "buffer_efficiency": self._calculate_buffer_efficiency(routing_paths)
        }
        return metrics
        
    def _estimate_latency(self, routing_paths: List[RoutingPath]) -> float:
        """Estimate average gateway latency in microseconds."""
        base_latency = 10.0  # Base processing latency
        
        # Add latency based on routing type
        for path in routing_paths:
            if path.routing_type == "TP":
                base_latency += 5.0  # Additional latency for TP
            elif path.routing_type == "MULTICAST":
                base_latency += 2.0  # Additional latency for multicast
                
        return base_latency / len(routing_paths) if routing_paths else base_latency
        
    def _estimate_throughput(
        self,
        routing_paths: List[RoutingPath],
        signal_gateways: List[SignalGateway]
    ) -> float:
        """Estimate gateway throughput in messages per second."""
        # Simple estimation based on configuration
        base_throughput = 10000.0  # Base throughput
        
        # Reduce throughput based on complexity
        complexity_factor = 1.0 - (len(signal_gateways) * 0.001)
        routing_factor = 1.0 - (len(routing_paths) * 0.0005)
        
        return base_throughput * complexity_factor * routing_factor
        
    def _calculate_routing_efficiency(self, routing_paths: List[RoutingPath]) -> float:
        """Calculate routing efficiency percentage."""
        if not routing_paths:
            return 100.0
            
        # Calculate based on direct vs buffered routing
        direct_routes = sum(1 for p in routing_paths if p.gateway_type == "ON_THE_FLY")
        efficiency = (direct_routes / len(routing_paths)) * 100.0
        
        return efficiency
        
    def _calculate_buffer_efficiency(self, routing_paths: List[RoutingPath]) -> float:
        """Calculate buffer utilization efficiency."""
        if not routing_paths:
            return 100.0
            
        buffered_paths = [p for p in routing_paths if p.buffer_size]
        if not buffered_paths:
            return 100.0
            
        # Calculate efficiency based on buffer size distribution
        avg_buffer = sum(p.buffer_size for p in buffered_paths) / len(buffered_paths)
        variance = sum((p.buffer_size - avg_buffer) ** 2 for p in buffered_paths) / len(buffered_paths)
        
        # Lower variance means better efficiency
        efficiency = max(0, 100.0 - (variance / avg_buffer if avg_buffer > 0 else 0))
        
        return min(100.0, efficiency)
        
    def _routing_path_to_dict(self, routing_path: RoutingPath) -> Dict[str, Any]:
        """Convert RoutingPath to dictionary."""
        return {
            "name": routing_path.name,
            "source_pdu": routing_path.source_pdu,
            "destination_pdu": routing_path.destination_pdu,
            "source_module": routing_path.source_module,
            "destination_module": routing_path.destination_module,
            "routing_type": routing_path.routing_type,
            "gateway_type": routing_path.gateway_type,
            "buffer_size": routing_path.buffer_size,
            "threshold": routing_path.threshold
        }
        
    def _signal_gateway_to_dict(self, signal_gateway: SignalGateway) -> Dict[str, Any]:
        """Convert SignalGateway to dictionary."""
        return {
            "name": signal_gateway.name,
            "source_signal": signal_gateway.source_signal,
            "destination_signal": signal_gateway.destination_signal,
            "source_pdu": signal_gateway.source_pdu,
            "destination_pdu": signal_gateway.destination_pdu,
            "transformation": signal_gateway.transformation,
            "update_indication": signal_gateway.update_indication
        }
        
    def _network_interface_to_dict(self, interface: NetworkInterface) -> Dict[str, Any]:
        """Convert NetworkInterface to dictionary."""
        return {
            "name": interface.name,
            "interface_type": interface.interface_type,
            "controller_ref": interface.controller_ref,
            "cluster_ref": interface.cluster_ref,
            "vlan_id": interface.vlan_id,
            "supported_protocols": interface.supported_protocols
        }
        
    def _protocol_conversion_to_dict(self, conversion: ProtocolConversion) -> Dict[str, Any]:
        """Convert ProtocolConversion to dictionary."""
        return {
            "name": conversion.name,
            "source_protocol": conversion.source_protocol,
            "destination_protocol": conversion.destination_protocol,
            "conversion_type": conversion.conversion_type,
            "parameters": conversion.parameters
        }
        
    def _safe_int(self, value: Optional[str]) -> Optional[int]:
        """Safely convert string to integer."""
        if value:
            try:
                return int(value)
            except (ValueError, TypeError):
                pass
        return None
        
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get gateway-specific analysis patterns.
        
        Returns:
            List of pattern definitions
        """
        return [
            {
                "name": "routing_paths",
                "type": PatternType.XPATH,
                "xpath": ".//ROUTING-PATH",
                "description": "PDU routing path configurations"
            },
            {
                "name": "signal_gateways",
                "type": PatternType.XPATH,
                "xpath": ".//SIGNAL-GATEWAY",
                "description": "Signal gateway mappings"
            },
            {
                "name": "multicast_groups",
                "type": PatternType.XPATH,
                "xpath": ".//MULTICAST-GROUP",
                "description": "Multicast group definitions"
            },
            {
                "name": "protocol_conversions",
                "type": PatternType.XPATH,
                "xpath": ".//PROTOCOL-CONVERSION",
                "description": "Protocol conversion configurations"
            },
            {
                "name": "network_clusters",
                "type": PatternType.XPATH,
                "xpath": ".//*[contains(local-name(), '-CLUSTER')]",
                "description": "Network cluster configurations"
            },
            {
                "name": "gateway_modules",
                "type": PatternType.XPATH,
                "xpath": ".//GATEWAY-MODULE-INSTANTIATION",
                "description": "Gateway module instantiations"
            }
        ]