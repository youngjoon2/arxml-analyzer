"""Reference integrity validator for ARXML files."""

from typing import Dict, List, Set, Any
import time
from collections import defaultdict
import lxml.etree as ET

from arxml_analyzer.core.validator.base_validator import (
    BaseValidator,
    ValidationResult,
    ValidationIssue,
    ValidationLevel,
    ValidationType
)
from arxml_analyzer.models.arxml_document import ARXMLDocument


class ReferenceValidator(BaseValidator):
    """Validates reference integrity in ARXML documents."""
    
    def __init__(self):
        """Initialize reference validator."""
        super().__init__()
    
    def can_validate(self, document: ARXMLDocument) -> bool:
        """Check if validator can handle this document.
        
        Args:
            document: ARXML document to check
            
        Returns:
            True (reference validation applies to all ARXML files)
        """
        return True
    
    def validate(self, document: ARXMLDocument) -> ValidationResult:
        """Validate reference integrity.
        
        Args:
            document: ARXML document to validate
            
        Returns:
            ValidationResult with reference validation issues
        """
        start_time = time.time()
        issues: List[ValidationIssue] = []
        statistics: Dict[str, Any] = {
            "total_references": 0,
            "valid_references": 0,
            "invalid_references": 0,
            "unused_definitions": 0,
            "circular_references": 0
        }
        
        # Collect all referenceable elements
        definitions = self._collect_definitions(document)
        
        # Collect all references
        references = self._collect_references(document)
        statistics["total_references"] = len(references)
        
        # Validate references
        invalid_refs = self._validate_references(references, definitions, document, issues)
        statistics["invalid_references"] = len(invalid_refs)
        statistics["valid_references"] = statistics["total_references"] - statistics["invalid_references"]
        
        # Find unused definitions
        unused = self._find_unused_definitions(definitions, references, issues)
        statistics["unused_definitions"] = len(unused)
        
        # Check for circular references
        circular = self._detect_circular_references(document, issues)
        statistics["circular_references"] = len(circular)
        
        # Check reference consistency
        self._check_reference_consistency(document, issues)
        
        # Determine overall validity
        is_valid = all(issue.level != ValidationLevel.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            statistics=statistics,
            metadata={
                "validator_name": self.name,
                "validator_version": self.version,
                "file_path": document.file_path,
                "definition_count": len(definitions)
            },
            duration=time.time() - start_time
        )
    
    def _collect_definitions(self, document: ARXMLDocument) -> Dict[str, Any]:
        """Collect all referenceable elements.
        
        Args:
            document: ARXML document
            
        Returns:
            Dictionary of path -> element
        """
        definitions = {}
        
        # Elements that can be referenced
        referenceable_tags = [
            "ECUC-MODULE-DEF",
            "ECUC-PARAM-CONF-CONTAINER-DEF",
            "ECUC-CONTAINER-DEF",
            "ECUC-PARAMETER-DEF",
            "ECUC-REFERENCE-DEF",
            "APPLICATION-SW-COMPONENT-TYPE",
            "P-PORT-PROTOTYPE",
            "R-PORT-PROTOTYPE",
            "SENDER-RECEIVER-INTERFACE",
            "CLIENT-SERVER-INTERFACE",
            "DATA-TYPE",
            "IMPLEMENTATION-DATA-TYPE"
        ]
        
        for tag in referenceable_tags:
            elements = document.xpath(f"//{tag}")
            for elem in elements:
                # Build full path
                path = self._build_element_path(elem)
                if path:
                    definitions[path] = elem
        
        return definitions
    
    def _collect_references(self, document: ARXMLDocument) -> List[Dict[str, Any]]:
        """Collect all reference elements.
        
        Args:
            document: ARXML document
            
        Returns:
            List of reference information
        """
        references = []
        
        # Reference elements patterns
        ref_patterns = [
            "//DEFINITION-REF",
            "//CONTAINER-DEF-REF",
            "//PARAMETER-REF",
            "//REFERENCE-REF",
            "//ECUC-MODULE-DEF-REF",
            "//DATA-TYPE-REF",
            "//INTERFACE-REF",
            "//PORT-REF",
            "//*[@DEST]"  # Elements with DEST attribute
        ]
        
        for pattern in ref_patterns:
            ref_elems = document.xpath(pattern)
            for ref_elem in ref_elems:
                ref_text = ref_elem.text
                if ref_text:
                    references.append({
                        "element": ref_elem,
                        "path": ref_text,
                        "type": ref_elem.tag,
                        "dest": ref_elem.get("DEST")
                    })
        
        return references
    
    def _validate_references(self, references: List[Dict], definitions: Dict[str, Any], 
                           document: ARXMLDocument, issues: List[ValidationIssue]) -> Set[str]:
        """Validate all references.
        
        Args:
            references: List of references to validate
            definitions: Dictionary of available definitions
            document: ARXML document
            issues: List to append issues to
            
        Returns:
            Set of invalid reference paths
        """
        invalid_refs = set()
        
        for ref in references:
            ref_path = ref["path"]
            
            # Check if reference exists
            if ref_path not in definitions:
                invalid_refs.add(ref_path)
                
                # Try to get element path safely
                element_path = None
                try:
                    if hasattr(document.root, 'getpath'):
                        element_path = document.root.getpath(ref["element"])
                except (ValueError, AttributeError):
                    pass
                
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        type=ValidationType.REFERENCE,
                        message=f"Invalid reference: {ref_path}",
                        element_path=element_path,
                        details={
                            "reference_type": ref["type"],
                            "destination_type": ref["dest"]
                        }
                    )
                )
            
            # Check DEST attribute matches target element type
            elif ref["dest"]:
                target_elem = definitions[ref_path]
                target_tag = target_elem.tag
                # Handle namespace in tag
                if target_tag.startswith('{'):
                    target_tag = ET.QName(target_tag).localname
                
                if target_tag != ref["dest"]:
                    # Try to get element path safely
                    element_path = None
                    try:
                        if hasattr(document.root, 'getpath'):
                            element_path = document.root.getpath(ref["element"])
                    except (ValueError, AttributeError):
                        pass
                    
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            type=ValidationType.REFERENCE,
                            message=f"Reference type mismatch: expected {ref['dest']}, found {target_tag}",
                            element_path=element_path,
                            details={
                                "reference": ref_path,
                                "expected_type": ref["dest"],
                                "actual_type": target_tag
                            }
                        )
                    )
        
        return invalid_refs
    
    def _find_unused_definitions(self, definitions: Dict[str, Any], references: List[Dict],
                                issues: List[ValidationIssue]) -> Set[str]:
        """Find definitions that are not referenced.
        
        Args:
            definitions: Dictionary of definitions
            references: List of references
            issues: List to append issues to
            
        Returns:
            Set of unused definition paths
        """
        # Collect all referenced paths
        referenced_paths = {ref["path"] for ref in references}
        
        # Find unused definitions
        unused = set()
        for def_path in definitions:
            if def_path not in referenced_paths:
                unused.add(def_path)
                elem = definitions[def_path]
                
                # Only warn for certain element types
                important_types = ["ECUC-MODULE-DEF", "APPLICATION-SW-COMPONENT-TYPE"]
                if elem.tag in important_types:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.WARNING,
                            type=ValidationType.REFERENCE,
                            message=f"Unused definition: {def_path}",
                            details={
                                "element_type": elem.tag
                            }
                        )
                    )
        
        return unused
    
    def _detect_circular_references(self, document: ARXMLDocument, 
                                   issues: List[ValidationIssue]) -> List[List[str]]:
        """Detect circular reference chains.
        
        Args:
            document: ARXML document
            issues: List to append issues to
            
        Returns:
            List of circular reference chains
        """
        circular_chains = []
        
        # Build reference graph
        ref_graph = defaultdict(set)
        refs = document.xpath("//*[contains(local-name(), '-REF')]")
        
        for ref in refs:
            if ref.text:
                parent_path = self._build_element_path(ref.getparent())
                if parent_path:
                    ref_graph[parent_path].add(ref.text)
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in ref_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    circular_chains.append(cycle)
                    
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            type=ValidationType.REFERENCE,
                            message=f"Circular reference detected: {' -> '.join(cycle)}",
                            details={
                                "cycle_length": len(cycle) - 1
                            }
                        )
                    )
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        # Check each component
        for node in ref_graph:
            if node not in visited:
                has_cycle(node, [])
        
        return circular_chains
    
    def _check_reference_consistency(self, document: ARXMLDocument, issues: List[ValidationIssue]):
        """Check reference consistency rules.
        
        Args:
            document: ARXML document
            issues: List to append issues to
        """
        # Check that container references match their definitions
        containers = document.xpath("//ECUC-CONTAINER-VALUE")
        
        for container in containers:
            def_ref = container.find("DEFINITION-REF")
            if def_ref is not None and def_ref.text:
                # Check that parameter values match the container definition
                param_values = container.xpath(".//ECUC-NUMERICAL-PARAM-VALUE | .//ECUC-TEXTUAL-PARAM-VALUE")
                
                for param_value in param_values:
                    param_ref = param_value.find("DEFINITION-REF")
                    if param_ref is not None and param_ref.text:
                        # Parameter ref should be under the container def
                        if not param_ref.text.startswith(def_ref.text):
                            issues.append(
                                ValidationIssue(
                                    level=ValidationLevel.WARNING,
                                    type=ValidationType.CONSISTENCY,
                                    message="Parameter reference not consistent with container definition",
                                    details={
                                        "container_def": def_ref.text,
                                        "parameter_ref": param_ref.text
                                    }
                                )
                            )
    
    def _build_element_path(self, element) -> str:
        """Build full path for an element.
        
        Args:
            element: XML element
            
        Returns:
            Full path string
        """
        path_parts = []
        current = element
        
        while current is not None:
            # Handle namespace in SHORT-NAME search
            short_name = current.find("SHORT-NAME")
            if short_name is None:
                # Try with namespace
                for child in current:
                    if hasattr(child, 'tag'):
                        tag = child.tag
                        if isinstance(tag, str):
                            local_name = ET.QName(tag).localname if tag.startswith('{') else tag
                            if local_name == "SHORT-NAME":
                                short_name = child
                                break
            
            if short_name is not None and short_name.text:
                path_parts.insert(0, short_name.text)
            current = current.getparent()
        
        return "/" + "/".join(path_parts) if path_parts else ""