"""
SWC (Software Component) Analyzer for ARXML files.

This analyzer extracts and analyzes Software Component information from ARXML files,
including component types, ports, interfaces, runnables, and data access patterns.
"""

from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from ..core.analyzer.base_analyzer import BaseAnalyzer, AnalysisResult, AnalysisLevel
from ..core.analyzer.cross_reference_analyzer import CrossReferenceAnalyzer, DependencyGraph
from ..models.arxml_document import ARXMLDocument
from ..utils.exceptions import AnalysisError

logger = logging.getLogger(__name__)


@dataclass
class PortInfo:
    """Software Component Port information."""
    name: str
    port_type: str  # P-PORT, R-PORT, PR-PORT
    interface_ref: str
    interface_type: str  # SENDER-RECEIVER, CLIENT-SERVER, etc.


@dataclass
class RunnableInfo:
    """Runnable entity information."""
    name: str
    symbol: Optional[str] = None
    min_start_interval: Optional[float] = None
    can_be_invoked_concurrently: bool = False
    data_read_access: List[str] = field(default_factory=list)
    data_write_access: List[str] = field(default_factory=list)
    server_call_points: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)


@dataclass
class SWCInfo:
    """Software Component information."""
    name: str
    component_type: str  # APPLICATION, COMPLEX_DEVICE_DRIVER, SERVICE, etc.
    category: Optional[str] = None
    provided_ports: List[PortInfo] = field(default_factory=list)
    required_ports: List[PortInfo] = field(default_factory=list)
    pr_ports: List[PortInfo] = field(default_factory=list)
    runnables: List[RunnableInfo] = field(default_factory=list)
    internal_behavior: Optional[str] = None


class SWCAnalyzer(BaseAnalyzer):
    """Analyzer for Software Component (SWC) ARXML files."""
    
    def __init__(self):
        """Initialize the SWC analyzer."""
        super().__init__(name="SWCAnalyzer", version="1.0.0")
        self.supported_types = ["SWC", "APPLICATION-SW-COMPONENT-TYPE", "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE"]
        
    def can_analyze(self, element) -> bool:
        """Check if this analyzer can handle the element/document."""
        # Support both ARXMLDocument and element
        if hasattr(element, 'xpath'):
            swc_elements = [
                "APPLICATION-SW-COMPONENT-TYPE",
                "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE", 
                "SERVICE-SW-COMPONENT-TYPE",
                "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
                "CALIBRATION-PARAMETER-SW-COMPONENT-TYPE",
                "ECU-ABSTRACTION-SW-COMPONENT-TYPE",
                "NV-BLOCK-SW-COMPONENT-TYPE"
            ]
            
            # Use namespace-agnostic XPath with local-name()
            for elem_type in swc_elements:
                if element.xpath(f"//*[local-name()='{elem_type}']"):
                    return True
        return False
        
    def analyze(self, document: ARXMLDocument) -> AnalysisResult:
        """Perform SWC analysis on the document."""
        import time
        from datetime import datetime
        from pathlib import Path
        from ..core.analyzer.base_analyzer import AnalysisMetadata, AnalysisStatus, AnalysisResult
        
        start_time = time.time()
        
        # Run implementation
        details = self._analyze_implementation(document)
        
        # Handle both ARXMLDocument and direct element
        file_path = None
        file_size = 0
        if hasattr(document, 'file_path'):
            file_path = Path(document.file_path) if document.file_path else None
            if hasattr(document, 'get_file_size') and file_path:
                file_size = document.get_file_size()
        
        # Create metadata
        metadata = AnalysisMetadata(
            analyzer_name=self.name,
            analyzer_version=self.version,
            analysis_timestamp=datetime.now(),
            analysis_duration=time.time() - start_time,
            file_path=file_path,
            file_size=file_size,
            arxml_type="SWC",
            analysis_level=self._analysis_level,
            status=AnalysisStatus.COMPLETED
        )
        
        # Create result
        result = AnalysisResult(metadata=metadata)
        result.details = details
        
        # Generate summary
        result.summary = {
            "total_components": details.get("total_components", 0),
            "total_ports": details.get("port_statistics", {}).get("total_ports", 0),
            "total_runnables": details.get("runnable_statistics", {}).get("total_runnables", 0),
            "interfaces_used": len(details.get("interface_usage", {}))
        }
        
        return result
    
    def _analyze_implementation(self, document: ARXMLDocument) -> Dict[str, Any]:
        """Implement the actual SWC analysis logic."""
        try:
            swc_components = self._extract_swc_components(document)
            port_statistics = self._calculate_port_statistics(swc_components)
            runnable_statistics = self._calculate_runnable_statistics(swc_components)
            interface_usage = self._analyze_interface_usage(swc_components)
            complexity_metrics = self._calculate_complexity_metrics(swc_components)
            
            # Add cross-reference analysis if detailed level
            cross_references = None
            if self.analysis_level == AnalysisLevel.DETAILED:
                cross_references = self._analyze_cross_references(document)
            
            result = {
                "components": [self._swc_to_dict(swc) for swc in swc_components],
                "port_statistics": port_statistics,
                "runnable_statistics": runnable_statistics,
                "interface_usage": interface_usage,
                "complexity_metrics": complexity_metrics,
                "total_components": len(swc_components)
            }
            
            if cross_references:
                result["cross_references"] = cross_references
                
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing SWC document: {e}")
            raise AnalysisError(f"SWC analysis failed: {e}")
            
    def _extract_swc_components(self, document: ARXMLDocument) -> List[SWCInfo]:
        """Extract all software components from the document."""
        components = []
        
        # Define all SWC element types
        swc_types = [
            ("APPLICATION-SW-COMPONENT-TYPE", "APPLICATION"),
            ("COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE", "COMPLEX_DEVICE_DRIVER"),
            ("SERVICE-SW-COMPONENT-TYPE", "SERVICE"),
            ("SENSOR-ACTUATOR-SW-COMPONENT-TYPE", "SENSOR_ACTUATOR"),
            ("CALIBRATION-PARAMETER-SW-COMPONENT-TYPE", "CALIBRATION"),
            ("ECU-ABSTRACTION-SW-COMPONENT-TYPE", "ECU_ABSTRACTION"),
            ("NV-BLOCK-SW-COMPONENT-TYPE", "NV_BLOCK")
        ]
        
        # Get namespaces from document root
        namespaces = {}
        # Handle both ARXMLDocument and direct element
        root = document.root if hasattr(document, 'root') else document
        if hasattr(root, 'nsmap') and root.nsmap:
            if None in root.nsmap:
                namespaces['ar'] = root.nsmap[None]
        
        for elem_type, comp_type in swc_types:
            # Use local-name() to be namespace-agnostic
            swc_elements = document.xpath(f'//*[local-name()="{elem_type}"]')
            
            for swc_elem in swc_elements:
                swc_info = SWCInfo(
                    name=self._get_text(swc_elem, "SHORT-NAME"),
                    component_type=comp_type,
                    category=self._get_text(swc_elem, "CATEGORY")
                )
                
                # Extract ports
                swc_info.provided_ports = self._extract_ports(swc_elem, "P-PORT-PROTOTYPE")
                swc_info.required_ports = self._extract_ports(swc_elem, "R-PORT-PROTOTYPE")
                swc_info.pr_ports = self._extract_ports(swc_elem, "PR-PORT-PROTOTYPE")
                
                # Extract internal behavior and runnables
                internal_behavior = swc_elem.find(".//SWC-INTERNAL-BEHAVIOR")
                if internal_behavior is not None:
                    swc_info.internal_behavior = self._get_text(internal_behavior, "SHORT-NAME")
                    swc_info.runnables = self._extract_runnables(internal_behavior)
                    
                components.append(swc_info)
                
        return components
        
    def _extract_ports(self, swc_elem, port_type: str) -> List[PortInfo]:
        """Extract port information from a SWC element."""
        ports = []
        # Use xpath with local-name to be namespace-agnostic
        port_elements = swc_elem.xpath(f'.//*[local-name()="PORTS"]/*[local-name()="{port_type}"]')
        
        for port_elem in port_elements:
            # Determine interface reference element name based on port type
            if port_type == "P-PORT-PROTOTYPE":
                interface_ref_elem = "PROVIDED-INTERFACE-TREF"
            elif port_type == "R-PORT-PROTOTYPE":
                interface_ref_elem = "REQUIRED-INTERFACE-TREF"
            else:  # PR-PORT-PROTOTYPE
                interface_ref_elem = "PROVIDED-REQUIRED-INTERFACE-TREF"
                
            # Find interface reference with namespace-agnostic xpath
            interface_tref_list = port_elem.xpath(f'.//*[local-name()="{interface_ref_elem}"]')
            interface_ref = ""
            interface_type = ""
            
            if interface_tref_list:
                interface_tref = interface_tref_list[0]
                interface_ref = interface_tref.text if interface_tref.text else ""
                interface_type = interface_tref.get("DEST", "")
                
            port_info = PortInfo(
                name=self._get_text(port_elem, "SHORT-NAME"),
                port_type=port_type.replace("-PROTOTYPE", ""),
                interface_ref=interface_ref,
                interface_type=interface_type
            )
            ports.append(port_info)
            
        return ports
        
    def _extract_runnables(self, internal_behavior) -> List[RunnableInfo]:
        """Extract runnable entities from internal behavior."""
        runnables = []
        runnable_elements = internal_behavior.findall(".//RUNNABLE-ENTITY")
        
        for runnable_elem in runnable_elements:
            runnable_info = RunnableInfo(
                name=self._get_text(runnable_elem, "SHORT-NAME"),
                symbol=self._get_text(runnable_elem, "SYMBOL")
            )
            
            # Extract timing information
            min_interval = self._get_text(runnable_elem, "MINIMUM-START-INTERVAL")
            if min_interval:
                try:
                    runnable_info.min_start_interval = float(min_interval)
                except ValueError:
                    pass
                    
            # Extract concurrency information
            concurrent = self._get_text(runnable_elem, "CAN-BE-INVOKED-CONCURRENTLY")
            runnable_info.can_be_invoked_concurrently = concurrent == "true"
            
            # Extract data access
            for read_access in runnable_elem.findall(".//DATA-READ-ACCESSS/VARIABLE-ACCESS"):
                access_name = self._get_text(read_access, "SHORT-NAME")
                if access_name:
                    runnable_info.data_read_access.append(access_name)
                    
            for write_access in runnable_elem.findall(".//DATA-WRITE-ACCESSS/VARIABLE-ACCESS"):
                access_name = self._get_text(write_access, "SHORT-NAME")
                if access_name:
                    runnable_info.data_write_access.append(access_name)
                    
            # Extract server call points
            for server_call in runnable_elem.findall(".//SERVER-CALL-POINTS/SYNCHRONOUS-SERVER-CALL-POINT"):
                call_name = self._get_text(server_call, "SHORT-NAME")
                if call_name:
                    runnable_info.server_call_points.append(call_name)
                    
            # Extract events
            for event_elem in internal_behavior.findall(".//EVENTS/*"):
                event_name = self._get_text(event_elem, "SHORT-NAME")
                runnable_ref = self._get_text(event_elem, ".//RUNNABLE-ENTITY-REF")
                if event_name and runnable_ref and runnable_ref.endswith(runnable_info.name):
                    runnable_info.events.append(event_name)
                    
            runnables.append(runnable_info)
            
        return runnables
        
    def _calculate_port_statistics(self, components: List[SWCInfo]) -> Dict[str, Any]:
        """Calculate statistics about ports."""
        total_provided = sum(len(c.provided_ports) for c in components)
        total_required = sum(len(c.required_ports) for c in components)
        total_pr = sum(len(c.pr_ports) for c in components)
        
        interface_types = defaultdict(int)
        for comp in components:
            for port in comp.provided_ports + comp.required_ports + comp.pr_ports:
                interface_types[port.interface_type] += 1
                
        return {
            "total_ports": total_provided + total_required + total_pr,
            "provided_ports": total_provided,
            "required_ports": total_required,
            "pr_ports": total_pr,
            "interface_types": dict(interface_types),
            "avg_ports_per_component": (total_provided + total_required + total_pr) / len(components) if components else 0
        }
        
    def _calculate_runnable_statistics(self, components: List[SWCInfo]) -> Dict[str, Any]:
        """Calculate statistics about runnables."""
        all_runnables = []
        for comp in components:
            all_runnables.extend(comp.runnables)
            
        periodic_runnables = [r for r in all_runnables if r.min_start_interval is not None]
        concurrent_runnables = [r for r in all_runnables if r.can_be_invoked_concurrently]
        
        intervals = [r.min_start_interval for r in periodic_runnables if r.min_start_interval]
        
        return {
            "total_runnables": len(all_runnables),
            "periodic_runnables": len(periodic_runnables),
            "concurrent_runnables": len(concurrent_runnables),
            "min_interval": min(intervals) if intervals else None,
            "max_interval": max(intervals) if intervals else None,
            "avg_interval": sum(intervals) / len(intervals) if intervals else None,
            "avg_runnables_per_component": len(all_runnables) / len(components) if components else 0
        }
        
    def _analyze_interface_usage(self, components: List[SWCInfo]) -> Dict[str, Any]:
        """Analyze interface usage patterns."""
        interface_refs = defaultdict(list)
        
        for comp in components:
            for port in comp.provided_ports:
                if port.interface_ref:
                    interface_refs[port.interface_ref].append(f"{comp.name}.{port.name}")
            for port in comp.required_ports:
                if port.interface_ref:
                    interface_refs[port.interface_ref].append(f"{comp.name}.{port.name}")
            for port in comp.pr_ports:
                if port.interface_ref:
                    interface_refs[port.interface_ref].append(f"{comp.name}.{port.name}")
                    
        # Find most used interfaces
        interface_usage_count = {k: len(v) for k, v in interface_refs.items()}
        most_used = sorted(interface_usage_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "unique_interfaces": len(interface_refs),
            "most_used_interfaces": most_used,
            "avg_interface_usage": sum(interface_usage_count.values()) / len(interface_usage_count) if interface_usage_count else 0
        }
        
    def _calculate_complexity_metrics(self, components: List[SWCInfo]) -> Dict[str, Any]:
        """Calculate complexity metrics for the components."""
        complexities = []
        
        for comp in components:
            # Component complexity based on ports, runnables, and data access
            port_complexity = len(comp.provided_ports) + len(comp.required_ports) + len(comp.pr_ports)
            runnable_complexity = len(comp.runnables) * 2  # Weighted higher
            
            data_access_complexity = 0
            for runnable in comp.runnables:
                data_access_complexity += len(runnable.data_read_access) + len(runnable.data_write_access)
                data_access_complexity += len(runnable.server_call_points) * 2  # Server calls are more complex
                
            total_complexity = port_complexity + runnable_complexity + data_access_complexity
            complexities.append(total_complexity)
            
        if not complexities:
            return {
                "min_complexity": 0,
                "max_complexity": 0,
                "avg_complexity": 0,
                "complexity_distribution": {}
            }
            
        # Categorize complexity
        complexity_distribution = {
            "simple": sum(1 for c in complexities if c <= 10),
            "moderate": sum(1 for c in complexities if 10 < c <= 25),
            "complex": sum(1 for c in complexities if 25 < c <= 50),
            "very_complex": sum(1 for c in complexities if c > 50)
        }
        
        return {
            "min_complexity": min(complexities),
            "max_complexity": max(complexities),
            "avg_complexity": sum(complexities) / len(complexities),
            "complexity_distribution": complexity_distribution
        }
        
    def _swc_to_dict(self, swc: SWCInfo) -> Dict[str, Any]:
        """Convert SWCInfo to dictionary."""
        return {
            "name": swc.name,
            "type": swc.component_type,
            "category": swc.category,
            "ports": {
                "provided": [{"name": p.name, "interface": p.interface_ref, "type": p.interface_type} 
                            for p in swc.provided_ports],
                "required": [{"name": p.name, "interface": p.interface_ref, "type": p.interface_type}
                            for p in swc.required_ports],
                "pr": [{"name": p.name, "interface": p.interface_ref, "type": p.interface_type}
                      for p in swc.pr_ports]
            },
            "runnables": [
                {
                    "name": r.name,
                    "symbol": r.symbol,
                    "min_interval": r.min_start_interval,
                    "concurrent": r.can_be_invoked_concurrently,
                    "data_read": r.data_read_access,
                    "data_write": r.data_write_access,
                    "server_calls": r.server_call_points,
                    "events": r.events
                }
                for r in swc.runnables
            ],
            "internal_behavior": swc.internal_behavior
        }
    
    def _analyze_cross_references(self, document: ARXMLDocument) -> Dict[str, Any]:
        """Analyze cross-references and generate dependency graph.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            Cross-reference analysis results
        """
        try:
            analyzer = CrossReferenceAnalyzer()
            graph = analyzer.analyze_document(document)
            report = analyzer.generate_report()
            
            # Add graph visualization data
            report['graph_data'] = {
                'node_count': len(graph.nodes),
                'edge_count': len(graph.edges),
                'graphviz': graph.to_graphviz() if len(graph.nodes) < 100 else None,  # Limit for large graphs
                'json': graph.to_json()
            }
            
            return report
            
        except Exception as e:
            logger.warning(f"Cross-reference analysis failed: {e}")
            return {
                'error': str(e),
                'summary': {
                    'total_elements': 0,
                    'total_references': 0,
                    'broken_references': 0,
                    'unused_elements': 0,
                    'circular_dependencies': 0
                }
            }
        
    def _get_text(self, element, tag: str) -> Optional[str]:
        """Safely get text from an element, namespace-agnostic."""
        if element is None:
            return None
        # Try direct child first
        found = element.find(f'.//{{{element.nsmap[None]}}}{tag}') if element.nsmap and None in element.nsmap else element.find(f'.//{tag}')
        if found is None:
            # Try with local-name
            found = element.xpath(f'.//*[local-name()="{tag}"]')
            if found:
                found = found[0]
            else:
                return None
        return found.text if found is not None else None
        
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Return SWC-specific patterns for analysis."""
        return [
            {
                "name": "Port Connection Pattern",
                "type": "STRUCTURAL",
                "xpath": "//PORTS/*",
                "description": "Analyze port connections and interfaces"
            },
            {
                "name": "Runnable Timing Pattern",
                "type": "XPATH",
                "xpath": "//RUNNABLE-ENTITY/MINIMUM-START-INTERVAL",
                "description": "Extract runnable timing requirements"
            },
            {
                "name": "Data Access Pattern",
                "type": "STRUCTURAL",
                "xpath": "//VARIABLE-ACCESS",
                "description": "Analyze data read/write patterns"
            },
            {
                "name": "Event-Runnable Mapping",
                "type": "REFERENCE",
                "xpath": "//EVENTS/*/RUNNABLE-ENTITY-REF",
                "description": "Map events to runnable entities"
            }
        ]