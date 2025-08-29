"""
Interface Analyzer for ARXML files.

This analyzer extracts and analyzes interface definitions from ARXML files,
including sender-receiver interfaces, client-server interfaces, mode-switch interfaces,
and their data types and operations.
"""

from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from ..core.analyzer.base_analyzer import BaseAnalyzer, AnalysisResult, AnalysisLevel
from ..models.arxml_document import ARXMLDocument
from ..utils.exceptions import AnalysisError

logger = logging.getLogger(__name__)


@dataclass
class DataElementInfo:
    """Data element information for interfaces."""
    name: str
    data_type: str
    type_ref: str
    init_value: Optional[Any] = None
    is_queued: bool = False
    queue_length: Optional[int] = None


@dataclass
class OperationInfo:
    """Operation information for client-server interfaces."""
    name: str
    arguments: List[Dict[str, str]] = field(default_factory=list)
    return_type: Optional[str] = None
    possible_errors: List[str] = field(default_factory=list)


@dataclass
class ModeGroupInfo:
    """Mode group information for mode-switch interfaces."""
    name: str
    type_ref: str
    modes: List[str] = field(default_factory=list)
    initial_mode: Optional[str] = None


@dataclass
class InterfaceInfo:
    """Interface information container."""
    name: str
    interface_type: str  # SENDER-RECEIVER, CLIENT-SERVER, MODE-SWITCH, etc.
    is_service: bool = False
    data_elements: List[DataElementInfo] = field(default_factory=list)
    operations: List[OperationInfo] = field(default_factory=list)
    mode_groups: List[ModeGroupInfo] = field(default_factory=list)
    invalidation_policies: List[Dict[str, Any]] = field(default_factory=list)
    package_path: Optional[str] = None


class InterfaceAnalyzer(BaseAnalyzer):
    """Analyzer for Interface definition ARXML files."""
    
    def __init__(self):
        """Initialize the Interface analyzer."""
        super().__init__(name="InterfaceAnalyzer", version="1.0.0")
        self.supported_types = ["INTERFACE", "PORT-INTERFACE"]
        
    def can_analyze(self, document: ARXMLDocument) -> bool:
        """Check if this analyzer can handle the document."""
        interface_elements = [
            "SENDER-RECEIVER-INTERFACE",
            "CLIENT-SERVER-INTERFACE",
            "MODE-SWITCH-INTERFACE",
            "PARAMETER-INTERFACE",
            "NV-DATA-INTERFACE",
            "TRIGGER-INTERFACE"
        ]
        
        for elem_type in interface_elements:
            # Use namespace-agnostic XPath
            if document.xpath(f"//*[local-name()='{elem_type}']"):
                return True
        return False
        
    def analyze(self, document: ARXMLDocument) -> AnalysisResult:
        """Perform interface analysis on the document."""
        import time
        from datetime import datetime
        from pathlib import Path
        from ..core.analyzer.base_analyzer import AnalysisMetadata, AnalysisStatus, AnalysisResult
        
        start_time = time.time()
        
        # Run implementation
        details = self._analyze_implementation(document)
        
        # Create metadata
        metadata = AnalysisMetadata(
            analyzer_name=self.name,
            analyzer_version=self.version,
            analysis_timestamp=datetime.now(),
            analysis_duration=time.time() - start_time,
            file_path=Path(document.file_path) if document.file_path else None,
            file_size=document.get_file_size() if hasattr(document, 'get_file_size') and document.file_path else 0,
            arxml_type="INTERFACE",
            analysis_level=self._analysis_level,
            status=AnalysisStatus.COMPLETED
        )
        
        # Create result
        result = AnalysisResult(metadata=metadata)
        result.details = details
        
        # Generate summary
        result.summary = {
            "total_interfaces": details.get("total_interfaces", 0),
            "interface_types": details.get("statistics", {}).get("interface_types", {}),
            "unique_data_types": details.get("data_type_usage", {}).get("unique_types", 0),
            "total_operations": details.get("operation_complexity", {}).get("total_operations", 0)
        }
        
        return result
    
    def _analyze_implementation(self, document: ARXMLDocument) -> Dict[str, Any]:
        """Implement the actual interface analysis logic."""
        try:
            interfaces = self._extract_interfaces(document)
            interface_statistics = self._calculate_interface_statistics(interfaces)
            data_type_usage = self._analyze_data_type_usage(interfaces)
            operation_complexity = self._analyze_operation_complexity(interfaces)
            interface_relationships = self._analyze_interface_relationships(interfaces)
            validation_results = self._validate_interfaces(interfaces)
            
            return {
                "interfaces": [self._interface_to_dict(iface) for iface in interfaces],
                "statistics": interface_statistics,
                "data_type_usage": data_type_usage,
                "operation_complexity": operation_complexity,
                "relationships": interface_relationships,
                "validation": validation_results,
                "total_interfaces": len(interfaces)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing interface document: {e}")
            raise AnalysisError(f"Interface analysis failed: {e}")
            
    def _extract_interfaces(self, document: ARXMLDocument) -> List[InterfaceInfo]:
        """Extract all interfaces from the document."""
        interfaces = []
        
        # Extract Sender-Receiver interfaces
        sr_interfaces = self._extract_sr_interfaces(document)
        interfaces.extend(sr_interfaces)
        
        # Extract Client-Server interfaces
        cs_interfaces = self._extract_cs_interfaces(document)
        interfaces.extend(cs_interfaces)
        
        # Extract Mode-Switch interfaces
        ms_interfaces = self._extract_ms_interfaces(document)
        interfaces.extend(ms_interfaces)
        
        # Extract Parameter interfaces
        param_interfaces = self._extract_param_interfaces(document)
        interfaces.extend(param_interfaces)
        
        # Extract NV-Data interfaces
        nv_interfaces = self._extract_nv_interfaces(document)
        interfaces.extend(nv_interfaces)
        
        # Extract Trigger interfaces
        trigger_interfaces = self._extract_trigger_interfaces(document)
        interfaces.extend(trigger_interfaces)
        
        return interfaces
        
    def _extract_sr_interfaces(self, document: ARXMLDocument) -> List[InterfaceInfo]:
        """Extract Sender-Receiver interfaces."""
        interfaces = []
        sr_elements = document.xpath("//*[local-name()='SENDER-RECEIVER-INTERFACE']")
        
        for sr_elem in sr_elements:
            interface = InterfaceInfo(
                name=self._get_text(sr_elem, "SHORT-NAME"),
                interface_type="SENDER-RECEIVER",
                is_service=self._get_text(sr_elem, "IS-SERVICE") == "true"
            )
            
            # Get package path
            interface.package_path = self._get_package_path(sr_elem)
            
            # Extract data elements
            data_elements = sr_elem.xpath(".//*[local-name()='DATA-ELEMENTS']/*[local-name()='VARIABLE-DATA-PROTOTYPE']")
            for de_elem in data_elements:
                data_element = DataElementInfo(
                    name=self._get_text(de_elem, "SHORT-NAME"),
                    data_type="VARIABLE",
                    type_ref=self._get_attr(de_elem, ".//TYPE-TREF", "DEST") or ""
                )
                
                # Get type reference
                type_trefs = de_elem.xpath(".//*[local-name()='TYPE-TREF']")
                if type_trefs and type_trefs[0].text:
                    data_element.type_ref = type_trefs[0].text
                    
                # Get init value if present
                init_value_elems = de_elem.xpath(".//*[local-name()='INIT-VALUE']//*[local-name()='VALUE']")
                if init_value_elems:
                    data_element.init_value = init_value_elems[0].text
                    
                # Check if queued
                is_queued = self._get_text(de_elem, "IS-QUEUED") == "true"
                data_element.is_queued = is_queued
                if is_queued:
                    queue_length = self._get_text(de_elem, "QUEUE-LENGTH")
                    if queue_length:
                        data_element.queue_length = int(queue_length)
                        
                interface.data_elements.append(data_element)
                
            # Extract invalidation policies
            inv_policies = sr_elem.xpath(".//*[local-name()='INVALIDATION-POLICYS']/*[local-name()='INVALIDATION-POLICY']")
            for policy in inv_policies:
                policy_info = {
                    "data_element": self._get_text(policy, ".//DATA-ELEMENT-REF"),
                    "handle_invalid": self._get_text(policy, "HANDLE-INVALID")
                }
                interface.invalidation_policies.append(policy_info)
                
            interfaces.append(interface)
            
        return interfaces
        
    def _extract_cs_interfaces(self, document: ARXMLDocument) -> List[InterfaceInfo]:
        """Extract Client-Server interfaces."""
        interfaces = []
        cs_elements = document.xpath("//*[local-name()='CLIENT-SERVER-INTERFACE']")
        
        for cs_elem in cs_elements:
            interface = InterfaceInfo(
                name=self._get_text(cs_elem, "SHORT-NAME"),
                interface_type="CLIENT-SERVER",
                is_service=self._get_text(cs_elem, "IS-SERVICE") == "true"
            )
            
            interface.package_path = self._get_package_path(cs_elem)
            
            # Extract operations
            operations = cs_elem.xpath(".//*[local-name()='OPERATIONS']/*[local-name()='CLIENT-SERVER-OPERATION']")
            for op_elem in operations:
                operation = OperationInfo(
                    name=self._get_text(op_elem, "SHORT-NAME")
                )
                
                # Extract arguments
                arguments = op_elem.xpath(".//*[local-name()='ARGUMENTS']/*[local-name()='ARGUMENT-DATA-PROTOTYPE']")
                for arg_elem in arguments:
                    arg_info = {
                        "name": self._get_text(arg_elem, "SHORT-NAME"),
                        "type": self._get_attr(arg_elem, ".//TYPE-TREF", "DEST") or "",
                        "type_ref": self._get_text(arg_elem, ".//TYPE-TREF") or "",
                        "direction": self._get_text(arg_elem, "DIRECTION") or "IN"
                    }
                    operation.arguments.append(arg_info)
                    
                # Extract return type (if exists)
                return_elems = op_elem.xpath(".//*[local-name()='RETURN']/*[local-name()='VARIABLE-DATA-PROTOTYPE']")
                if return_elems:
                    operation.return_type = self._get_text(return_elems[0], ".//TYPE-TREF")
                    
                # Extract possible errors
                errors = op_elem.xpath(".//*[local-name()='POSSIBLE-ERROR-REFS']/*[local-name()='POSSIBLE-ERROR-REF']")
                for error_elem in errors:
                    if error_elem.text:
                        operation.possible_errors.append(error_elem.text)
                        
                interface.operations.append(operation)
                
            interfaces.append(interface)
            
        return interfaces
        
    def _extract_ms_interfaces(self, document: ARXMLDocument) -> List[InterfaceInfo]:
        """Extract Mode-Switch interfaces."""
        interfaces = []
        ms_elements = document.xpath("//*[local-name()='MODE-SWITCH-INTERFACE']")
        
        for ms_elem in ms_elements:
            interface = InterfaceInfo(
                name=self._get_text(ms_elem, "SHORT-NAME"),
                interface_type="MODE-SWITCH",
                is_service=self._get_text(ms_elem, "IS-SERVICE") == "true"
            )
            
            interface.package_path = self._get_package_path(ms_elem)
            
            # Extract mode groups
            mode_groups = ms_elem.xpath(".//*[local-name()='MODE-GROUP']")
            for mg_elem in mode_groups:
                mode_group = ModeGroupInfo(
                    name=self._get_text(mg_elem, "SHORT-NAME"),
                    type_ref=self._get_text(mg_elem, ".//TYPE-TREF") or ""
                )
                
                # Extract initial mode
                mode_group.initial_mode = self._get_text(mg_elem, ".//INITIAL-MODE-REF")
                
                interface.mode_groups.append(mode_group)
                
            interfaces.append(interface)
            
        return interfaces
        
    def _extract_param_interfaces(self, document: ARXMLDocument) -> List[InterfaceInfo]:
        """Extract Parameter interfaces."""
        interfaces = []
        param_elements = document.xpath("//*[local-name()='PARAMETER-INTERFACE']")
        
        for param_elem in param_elements:
            interface = InterfaceInfo(
                name=self._get_text(param_elem, "SHORT-NAME"),
                interface_type="PARAMETER",
                is_service=self._get_text(param_elem, "IS-SERVICE") == "true"
            )
            
            interface.package_path = self._get_package_path(param_elem)
            
            # Extract parameters as data elements
            parameters = param_elem.xpath(".//*[local-name()='PARAMETERS']/*[local-name()='PARAMETER-DATA-PROTOTYPE']")
            for p_elem in parameters:
                data_element = DataElementInfo(
                    name=self._get_text(p_elem, "SHORT-NAME"),
                    data_type="PARAMETER",
                    type_ref=self._get_text(p_elem, ".//TYPE-TREF") or ""
                )
                
                # Get init value if present
                init_value_elems = p_elem.xpath(".//*[local-name()='INIT-VALUE']//*[local-name()='VALUE']")
                if init_value_elems:
                    data_element.init_value = init_value_elems[0].text
                    
                interface.data_elements.append(data_element)
                
            interfaces.append(interface)
            
        return interfaces
        
    def _extract_nv_interfaces(self, document: ARXMLDocument) -> List[InterfaceInfo]:
        """Extract NV-Data interfaces."""
        interfaces = []
        nv_elements = document.xpath("//*[local-name()='NV-DATA-INTERFACE']")
        
        for nv_elem in nv_elements:
            interface = InterfaceInfo(
                name=self._get_text(nv_elem, "SHORT-NAME"),
                interface_type="NV-DATA",
                is_service=self._get_text(nv_elem, "IS-SERVICE") == "true"
            )
            
            interface.package_path = self._get_package_path(nv_elem)
            
            # Extract NV data
            nv_data = nv_elem.xpath(".//*[local-name()='NV-DATAS']/*[local-name()='VARIABLE-DATA-PROTOTYPE']")
            for nv_data_elem in nv_data:
                data_element = DataElementInfo(
                    name=self._get_text(nv_data_elem, "SHORT-NAME"),
                    data_type="NV-DATA",
                    type_ref=self._get_text(nv_data_elem, ".//TYPE-TREF") or ""
                )
                interface.data_elements.append(data_element)
                
            interfaces.append(interface)
            
        return interfaces
        
    def _extract_trigger_interfaces(self, document: ARXMLDocument) -> List[InterfaceInfo]:
        """Extract Trigger interfaces."""
        interfaces = []
        trigger_elements = document.xpath("//*[local-name()='TRIGGER-INTERFACE']")
        
        for trigger_elem in trigger_elements:
            interface = InterfaceInfo(
                name=self._get_text(trigger_elem, "SHORT-NAME"),
                interface_type="TRIGGER",
                is_service=self._get_text(trigger_elem, "IS-SERVICE") == "true"
            )
            
            interface.package_path = self._get_package_path(trigger_elem)
            
            # Extract triggers as data elements (simplified)
            triggers = trigger_elem.xpath(".//*[local-name()='TRIGGERS']/*[local-name()='TRIGGER']")
            for t_elem in triggers:
                data_element = DataElementInfo(
                    name=self._get_text(t_elem, "SHORT-NAME"),
                    data_type="TRIGGER",
                    type_ref=""
                )
                interface.data_elements.append(data_element)
                
            interfaces.append(interface)
            
        return interfaces
        
    def _calculate_interface_statistics(self, interfaces: List[InterfaceInfo]) -> Dict[str, Any]:
        """Calculate statistics about interfaces."""
        type_counts = defaultdict(int)
        service_interfaces = 0
        
        for iface in interfaces:
            type_counts[iface.interface_type] += 1
            if iface.is_service:
                service_interfaces += 1
                
        # Calculate data elements per interface type
        data_elements_by_type = defaultdict(list)
        operations_by_type = defaultdict(list)
        
        for iface in interfaces:
            if iface.data_elements:
                data_elements_by_type[iface.interface_type].append(len(iface.data_elements))
            if iface.operations:
                operations_by_type[iface.interface_type].append(len(iface.operations))
                
        return {
            "interface_types": dict(type_counts),
            "service_interfaces": service_interfaces,
            "non_service_interfaces": len(interfaces) - service_interfaces,
            "avg_data_elements": {
                itype: sum(counts) / len(counts) if counts else 0
                for itype, counts in data_elements_by_type.items()
            },
            "avg_operations": {
                itype: sum(counts) / len(counts) if counts else 0
                for itype, counts in operations_by_type.items()
            }
        }
        
    def _analyze_data_type_usage(self, interfaces: List[InterfaceInfo]) -> Dict[str, Any]:
        """Analyze data type usage across interfaces."""
        type_refs = defaultdict(int)
        type_categories = defaultdict(int)
        
        for iface in interfaces:
            for de in iface.data_elements:
                if de.type_ref:
                    type_refs[de.type_ref] += 1
                    # Categorize by common patterns
                    if "uint" in de.type_ref.lower():
                        type_categories["unsigned_integer"] += 1
                    elif "sint" in de.type_ref.lower() or "int" in de.type_ref.lower():
                        type_categories["signed_integer"] += 1
                    elif "float" in de.type_ref.lower() or "real" in de.type_ref.lower():
                        type_categories["floating_point"] += 1
                    elif "bool" in de.type_ref.lower():
                        type_categories["boolean"] += 1
                    elif "string" in de.type_ref.lower():
                        type_categories["string"] += 1
                    else:
                        type_categories["complex"] += 1
                        
        # Find most used types
        most_used_types = sorted(type_refs.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "unique_types": len(type_refs),
            "type_categories": dict(type_categories),
            "most_used_types": most_used_types,
            "total_type_references": sum(type_refs.values())
        }
        
    def _analyze_operation_complexity(self, interfaces: List[InterfaceInfo]) -> Dict[str, Any]:
        """Analyze complexity of operations in client-server interfaces."""
        operation_stats = []
        
        for iface in interfaces:
            for op in iface.operations:
                complexity = len(op.arguments) + len(op.possible_errors)
                if op.return_type:
                    complexity += 1
                    
                operation_stats.append({
                    "interface": iface.name,
                    "operation": op.name,
                    "arg_count": len(op.arguments),
                    "error_count": len(op.possible_errors),
                    "has_return": op.return_type is not None,
                    "complexity": complexity
                })
                
        if not operation_stats:
            return {
                "total_operations": 0,
                "avg_complexity": 0,
                "max_complexity": 0,
                "complexity_distribution": {}
            }
            
        complexities = [op["complexity"] for op in operation_stats]
        
        # Categorize complexity
        complexity_distribution = {
            "simple": sum(1 for c in complexities if c <= 3),
            "moderate": sum(1 for c in complexities if 3 < c <= 6),
            "complex": sum(1 for c in complexities if c > 6)
        }
        
        return {
            "total_operations": len(operation_stats),
            "avg_complexity": sum(complexities) / len(complexities),
            "max_complexity": max(complexities),
            "min_complexity": min(complexities),
            "complexity_distribution": complexity_distribution,
            "most_complex_operations": sorted(operation_stats, key=lambda x: x["complexity"], reverse=True)[:5]
        }
        
    def _analyze_interface_relationships(self, interfaces: List[InterfaceInfo]) -> Dict[str, Any]:
        """Analyze relationships between interfaces based on shared data types."""
        type_to_interfaces = defaultdict(list)
        
        for iface in interfaces:
            for de in iface.data_elements:
                if de.type_ref:
                    type_to_interfaces[de.type_ref].append(iface.name)
                    
        # Find interfaces that share data types
        shared_types = {k: v for k, v in type_to_interfaces.items() if len(v) > 1}
        
        # Calculate interface coupling
        interface_connections = defaultdict(set)
        for type_ref, iface_list in shared_types.items():
            for i in range(len(iface_list)):
                for j in range(i + 1, len(iface_list)):
                    interface_connections[iface_list[i]].add(iface_list[j])
                    interface_connections[iface_list[j]].add(iface_list[i])
                    
        return {
            "shared_data_types": len(shared_types),
            "most_shared_types": sorted(
                [(k, len(v)) for k, v in shared_types.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "interface_coupling": {
                k: len(v) for k, v in interface_connections.items()
            },
            "avg_coupling": sum(len(v) for v in interface_connections.values()) / len(interface_connections) if interface_connections else 0
        }
        
    def _validate_interfaces(self, interfaces: List[InterfaceInfo]) -> Dict[str, Any]:
        """Validate interface definitions."""
        issues = []
        warnings = []
        
        for iface in interfaces:
            # Check for empty interfaces
            if not iface.data_elements and not iface.operations and not iface.mode_groups:
                warnings.append(f"Interface '{iface.name}' has no elements/operations")
                
            # Check for missing type references
            for de in iface.data_elements:
                if not de.type_ref:
                    issues.append(f"Data element '{de.name}' in '{iface.name}' has no type reference")
                    
            # Check for duplicate data elements
            de_names = [de.name for de in iface.data_elements]
            duplicates = [name for name in de_names if de_names.count(name) > 1]
            if duplicates:
                issues.append(f"Interface '{iface.name}' has duplicate data elements: {set(duplicates)}")
                
            # Check operations
            for op in iface.operations:
                # Check for nameless arguments
                for arg in op.arguments:
                    if not arg.get("name"):
                        issues.append(f"Operation '{op.name}' in '{iface.name}' has unnamed argument")
                        
        return {
            "valid": len(issues) == 0,
            "issue_count": len(issues),
            "warning_count": len(warnings),
            "issues": issues[:10],  # Limit to first 10
            "warnings": warnings[:10]
        }
        
    def _interface_to_dict(self, interface: InterfaceInfo) -> Dict[str, Any]:
        """Convert InterfaceInfo to dictionary."""
        return {
            "name": interface.name,
            "type": interface.interface_type,
            "is_service": interface.is_service,
            "package": interface.package_path,
            "data_elements": [
                {
                    "name": de.name,
                    "data_type": de.data_type,
                    "type_ref": de.type_ref,
                    "init_value": de.init_value,
                    "is_queued": de.is_queued,
                    "queue_length": de.queue_length
                }
                for de in interface.data_elements
            ],
            "operations": [
                {
                    "name": op.name,
                    "arguments": op.arguments,
                    "return_type": op.return_type,
                    "possible_errors": op.possible_errors
                }
                for op in interface.operations
            ],
            "mode_groups": [
                {
                    "name": mg.name,
                    "type_ref": mg.type_ref,
                    "initial_mode": mg.initial_mode,
                    "modes": mg.modes
                }
                for mg in interface.mode_groups
            ],
            "invalidation_policies": interface.invalidation_policies
        }
        
    def _get_text(self, element, xpath: str) -> Optional[str]:
        """Safely get text from an element."""
        if element is None:
            return None
        # Use XPath with local-name() for namespace-agnostic search
        if xpath == "SHORT-NAME":
            results = element.xpath(f"*[local-name()='SHORT-NAME']")
        elif xpath.startswith(".//"):
            tag = xpath.split('/')[-1]
            results = element.xpath(f".//*[local-name()='{tag}']")
        else:
            tag = xpath.split('/')[-1] if '/' in xpath else xpath
            results = element.xpath(f"*[local-name()='{tag}']")
        
        return results[0].text if results else None
        
    def _get_attr(self, element, xpath: str, attr: str) -> Optional[str]:
        """Safely get attribute from an element."""
        if element is None:
            return None
        # Use XPath with local-name() for namespace-agnostic search
        if xpath.startswith(".//"):
            tag = xpath.split('/')[-1]
            results = element.xpath(f".//*[local-name()='{tag}']")
        else:
            tag = xpath.split('/')[-1] if '/' in xpath else xpath
            results = element.xpath(f"*[local-name()='{tag}']")
        
        return results[0].get(attr) if results else None
        
    def _get_package_path(self, element) -> Optional[str]:
        """Get the package path of an element."""
        packages = []
        parent = element.getparent()
        
        while parent is not None:
            # Check for AR-PACKAGE in a namespace-agnostic way
            if parent.tag.endswith("AR-PACKAGE") or parent.tag.split('}')[-1] == "AR-PACKAGE":
                # Find SHORT-NAME in a namespace-agnostic way
                name_elems = parent.xpath("*[local-name()='SHORT-NAME']")
                if name_elems and name_elems[0].text:
                    packages.insert(0, name_elems[0].text)
            parent = parent.getparent()
            
        return "/" + "/".join(packages) if packages else None
        
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Return Interface-specific patterns for analysis."""
        return [
            {
                "name": "Data Element Pattern",
                "type": "XPATH",
                "xpath": "//DATA-ELEMENTS/VARIABLE-DATA-PROTOTYPE",
                "description": "Extract data element definitions"
            },
            {
                "name": "Operation Pattern",
                "type": "XPATH",
                "xpath": "//OPERATIONS/CLIENT-SERVER-OPERATION",
                "description": "Extract client-server operations"
            },
            {
                "name": "Type Reference Pattern",
                "type": "REFERENCE",
                "xpath": "//TYPE-TREF",
                "description": "Analyze data type references"
            },
            {
                "name": "Interface Hierarchy",
                "type": "STRUCTURAL",
                "xpath": "//AR-PACKAGE",
                "description": "Analyze interface package structure"
            }
        ]