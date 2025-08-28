"""Document Profiler for automatic ARXML structure discovery.

This module provides functionality to automatically profile ARXML documents
to discover their structure, patterns, and naming conventions without
relying on hardcoded element names or structures.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from pathlib import Path
import xml.etree.ElementTree as etree
import re
from enum import Enum


class NamingConvention(Enum):
    """Common naming conventions in ARXML."""
    UPPER_CASE = "UPPER_CASE"           # ECUC-MODULE-CONFIGURATION
    LOWER_CASE = "lower_case"           # module-configuration
    PASCAL_CASE = "PascalCase"          # ModuleConfiguration
    CAMEL_CASE = "camelCase"            # moduleConfiguration
    SNAKE_CASE = "snake_case"           # module_configuration
    KEBAB_CASE = "kebab-case"           # module-configuration
    MIXED = "mixed"                     # Mix of conventions


@dataclass
class ElementPattern:
    """Represents a discovered element pattern."""
    tag_name: str
    frequency: int
    depth_levels: Set[int] = field(default_factory=set)
    parent_tags: Set[str] = field(default_factory=set)
    child_tags: Set[str] = field(default_factory=set)
    attributes: Set[str] = field(default_factory=set)
    text_patterns: List[str] = field(default_factory=list)
    naming_convention: Optional[NamingConvention] = None
    is_container: bool = False
    is_reference: bool = False
    is_parameter: bool = False


@dataclass
class DocumentProfile:
    """Complete profile of an ARXML document structure."""
    document_type: str = "UNKNOWN"
    namespace: Optional[str] = None
    namespaces: Dict[str, str] = field(default_factory=dict)
    root_element: Optional[str] = None
    element_patterns: Dict[str, ElementPattern] = field(default_factory=dict)
    naming_conventions: Dict[str, NamingConvention] = field(default_factory=dict)
    common_attributes: Set[str] = field(default_factory=set)
    reference_patterns: List[Tuple[str, str]] = field(default_factory=list)
    parameter_patterns: List[Tuple[str, str]] = field(default_factory=list)
    container_patterns: List[str] = field(default_factory=list)
    hierarchy_depth: int = 0
    statistics: Dict[str, Any] = field(default_factory=dict)


class DocumentProfiler:
    """Profiles ARXML documents to discover their structure automatically."""
    
    def __init__(self):
        """Initialize the document profiler."""
        self._profile: Optional[DocumentProfile] = None
        self._element_cache: Dict[str, ElementPattern] = {}
        
        # Pattern matchers for common AUTOSAR elements
        self._container_patterns = [
            re.compile(r'.*CONTAINER.*', re.IGNORECASE),
            re.compile(r'.*CONTAINERS$', re.IGNORECASE),
            re.compile(r'.*-VALUES$', re.IGNORECASE),
            re.compile(r'.*ELEMENTS$', re.IGNORECASE)
        ]
        
        self._parameter_patterns = [
            re.compile(r'.*PARAM.*', re.IGNORECASE),
            re.compile(r'.*PARAMETER.*', re.IGNORECASE),
            re.compile(r'.*VALUE$', re.IGNORECASE),
            re.compile(r'.*-VALUE$', re.IGNORECASE)
        ]
        
        self._reference_patterns = [
            re.compile(r'.*REF$', re.IGNORECASE),
            re.compile(r'.*-REF$', re.IGNORECASE),
            re.compile(r'.*REFERENCE.*', re.IGNORECASE),
            re.compile(r'.*REF-.*', re.IGNORECASE)
        ]
        
        # Module type indicators
        self._module_indicators = {
            'ECUC': ['ECUC', 'ECU-CONFIGURATION', 'MODULE-CONFIGURATION'],
            'SYSTEM': ['SYSTEM', 'SYSTEM-DESCRIPTION', 'SYSTEMS'],
            'SWC': ['SW-COMPONENT', 'SOFTWARE-COMPONENT', 'APPLICATION-SW'],
            'INTERFACE': ['PORT-INTERFACE', 'INTERFACE', 'SERVICE-INTERFACE'],
            'GATEWAY': ['GATEWAY', 'PDU-R', 'ROUTING', 'PDUR'],
            'DIAGNOSTIC': ['DIAGNOSTIC', 'DCM', 'DEM', 'DIAG'],
            'COMMUNICATION': ['COM', 'COMMUNICATION', 'CAN', 'LIN', 'ETHERNET'],
            'MCAL': ['MCAL', 'MICROCONTROLLER', 'MCU', 'PORT', 'DIO']
        }
    
    def profile_document(self, root: etree.Element) -> DocumentProfile:
        """Profile an ARXML document to discover its structure.
        
        Args:
            root: Root element of the document
            
        Returns:
            DocumentProfile containing discovered patterns
        """
        self._profile = DocumentProfile()
        self._element_cache.clear()
        
        # Extract namespace information
        self._extract_namespaces(root)
        
        # Analyze document structure
        self._analyze_structure(root, depth=0)
        
        # Detect document type
        self._detect_document_type()
        
        # Analyze naming conventions
        self._analyze_naming_conventions()
        
        # Identify special element types
        self._identify_element_types()
        
        # Calculate statistics
        self._calculate_statistics()
        
        return self._profile
    
    def _extract_namespaces(self, root: etree.Element) -> None:
        """Extract namespace information from the root element.
        
        Args:
            root: Root element of the document
        """
        if hasattr(root, 'nsmap') and root.nsmap:
            self._profile.namespaces = dict(root.nsmap)
            # Get default namespace
            if None in root.nsmap:
                self._profile.namespace = root.nsmap[None]
        
        # Extract root element name
        tag = root.tag
        if '}' in tag:
            namespace, local_name = tag.rsplit('}', 1)
            self._profile.namespace = namespace.lstrip('{')
            self._profile.root_element = local_name
        else:
            self._profile.root_element = tag
    
    def _analyze_structure(self, element: etree.Element, depth: int = 0) -> None:
        """Recursively analyze document structure.
        
        Args:
            element: Current element to analyze
            depth: Current depth in the tree
        """
        # Update hierarchy depth
        self._profile.hierarchy_depth = max(self._profile.hierarchy_depth, depth)
        
        # Get element tag without namespace
        tag = self._get_local_name(element.tag)
        
        # Get or create element pattern
        if tag not in self._element_cache:
            self._element_cache[tag] = ElementPattern(tag_name=tag, frequency=0)
        
        pattern = self._element_cache[tag]
        pattern.frequency += 1
        pattern.depth_levels.add(depth)
        
        # Record parent information
        parent = element.getparent() if hasattr(element, 'getparent') else None
        if parent is not None:
            parent_tag = self._get_local_name(parent.tag)
            pattern.parent_tags.add(parent_tag)
        
        # Record attributes
        pattern.attributes.update(element.attrib.keys())
        self._profile.common_attributes.update(element.attrib.keys())
        
        # Record text patterns
        if element.text and element.text.strip():
            text = element.text.strip()
            # Store sample text patterns (limit to avoid memory issues)
            if len(pattern.text_patterns) < 10:
                pattern.text_patterns.append(text[:100])  # Store first 100 chars
        
        # Analyze children
        child_tags = set()
        for child in element:
            child_tag = self._get_local_name(child.tag)
            child_tags.add(child_tag)
            self._analyze_structure(child, depth + 1)
        
        pattern.child_tags.update(child_tags)
        
        # Store in profile
        self._profile.element_patterns[tag] = pattern
    
    def _get_local_name(self, tag: str) -> str:
        """Extract local name from a tag with namespace.
        
        Args:
            tag: Tag name possibly with namespace
            
        Returns:
            Local tag name without namespace
        """
        if '}' in tag:
            return tag.rsplit('}', 1)[1]
        return tag
    
    def _detect_document_type(self) -> None:
        """Detect the type of ARXML document based on element patterns."""
        # Count indicators for each type
        type_scores = defaultdict(int)
        
        for element_tag in self._profile.element_patterns.keys():
            upper_tag = element_tag.upper()
            
            for doc_type, indicators in self._module_indicators.items():
                for indicator in indicators:
                    if indicator in upper_tag:
                        type_scores[doc_type] += 1
        
        # Set document type based on highest score
        if type_scores:
            self._profile.document_type = max(type_scores, key=type_scores.get)
        
        # Store scores in statistics
        self._profile.statistics['type_scores'] = dict(type_scores)
    
    def _analyze_naming_conventions(self) -> None:
        """Analyze naming conventions used in the document."""
        for tag, pattern in self._profile.element_patterns.items():
            convention = self._detect_naming_convention(tag)
            pattern.naming_convention = convention
            
            # Count conventions
            if convention not in self._profile.naming_conventions:
                self._profile.naming_conventions[convention] = convention
    
    def _detect_naming_convention(self, name: str) -> NamingConvention:
        """Detect the naming convention of a string.
        
        Args:
            name: String to analyze
            
        Returns:
            Detected naming convention
        """
        if not name:
            return NamingConvention.MIXED
        
        # Check for all uppercase
        if name.isupper() or (name.replace('-', '').replace('_', '').isupper()):
            return NamingConvention.UPPER_CASE
        
        # Check for all lowercase
        if name.islower():
            if '-' in name:
                return NamingConvention.KEBAB_CASE
            elif '_' in name:
                return NamingConvention.SNAKE_CASE
            else:
                return NamingConvention.LOWER_CASE
        
        # Check for PascalCase
        if name[0].isupper() and not '_' in name and not '-' in name:
            return NamingConvention.PASCAL_CASE
        
        # Check for camelCase
        if name[0].islower() and any(c.isupper() for c in name[1:]):
            return NamingConvention.CAMEL_CASE
        
        return NamingConvention.MIXED
    
    def _identify_element_types(self) -> None:
        """Identify special element types (containers, parameters, references)."""
        for tag, pattern in self._profile.element_patterns.items():
            # Check if it's a container
            for container_pattern in self._container_patterns:
                if container_pattern.match(tag):
                    pattern.is_container = True
                    self._profile.container_patterns.append(tag)
                    break
            
            # Check if it's a parameter
            for param_pattern in self._parameter_patterns:
                if param_pattern.match(tag):
                    pattern.is_parameter = True
                    # Store with parent for context
                    for parent in pattern.parent_tags:
                        self._profile.parameter_patterns.append((parent, tag))
                    break
            
            # Check if it's a reference
            for ref_pattern in self._reference_patterns:
                if ref_pattern.match(tag):
                    pattern.is_reference = True
                    # Store with parent for context
                    for parent in pattern.parent_tags:
                        self._profile.reference_patterns.append((parent, tag))
                    break
    
    def _calculate_statistics(self) -> None:
        """Calculate various statistics about the document."""
        stats = self._profile.statistics
        
        # Element statistics
        stats['total_elements'] = sum(p.frequency for p in self._profile.element_patterns.values())
        stats['unique_elements'] = len(self._profile.element_patterns)
        stats['max_depth'] = self._profile.hierarchy_depth
        
        # Type statistics
        stats['container_count'] = sum(1 for p in self._profile.element_patterns.values() if p.is_container)
        stats['parameter_count'] = sum(1 for p in self._profile.element_patterns.values() if p.is_parameter)
        stats['reference_count'] = sum(1 for p in self._profile.element_patterns.values() if p.is_reference)
        
        # Most frequent elements
        sorted_patterns = sorted(
            self._profile.element_patterns.values(),
            key=lambda x: x.frequency,
            reverse=True
        )
        stats['top_elements'] = [
            {'tag': p.tag_name, 'count': p.frequency}
            for p in sorted_patterns[:10]
        ]
        
        # Naming convention distribution
        convention_counts = Counter(
            p.naming_convention for p in self._profile.element_patterns.values()
        )
        stats['naming_conventions'] = dict(convention_counts)
    
    def get_element_xpath(self, element_name: str, use_namespace: bool = True) -> str:
        """Generate XPath for an element based on profiled patterns.
        
        Args:
            element_name: Name of the element
            use_namespace: Whether to include namespace in XPath
            
        Returns:
            Generated XPath expression
        """
        if use_namespace and self._profile.namespace:
            # Use local-name() for namespace-agnostic XPath
            return f".//*[local-name()='{element_name}']"
        else:
            return f".//{element_name}"
    
    def get_container_elements(self) -> List[str]:
        """Get all identified container element names.
        
        Returns:
            List of container element names
        """
        return [
            tag for tag, pattern in self._profile.element_patterns.items()
            if pattern.is_container
        ]
    
    def get_parameter_elements(self) -> List[str]:
        """Get all identified parameter element names.
        
        Returns:
            List of parameter element names
        """
        return [
            tag for tag, pattern in self._profile.element_patterns.items()
            if pattern.is_parameter
        ]
    
    def get_reference_elements(self) -> List[str]:
        """Get all identified reference element names.
        
        Returns:
            List of reference element names
        """
        return [
            tag for tag, pattern in self._profile.element_patterns.items()
            if pattern.is_reference
        ]
    
    def suggest_patterns_for_type(self, element_type: str) -> List[str]:
        """Suggest element patterns based on document type.
        
        Args:
            element_type: Type of elements to find (e.g., 'module', 'container')
            
        Returns:
            List of suggested element names
        """
        suggestions = []
        search_terms = {
            'module': ['MODULE', 'MOD'],
            'container': ['CONTAINER', 'CONT'],
            'parameter': ['PARAM', 'PARAMETER', 'VALUE'],
            'reference': ['REF', 'REFERENCE'],
            'configuration': ['CONFIG', 'CONFIGURATION', 'CONF']
        }
        
        if element_type.lower() in search_terms:
            terms = search_terms[element_type.lower()]
            for tag in self._profile.element_patterns.keys():
                upper_tag = tag.upper()
                if any(term in upper_tag for term in terms):
                    suggestions.append(tag)
        
        return suggestions
    
    def export_profile(self) -> Dict[str, Any]:
        """Export the document profile as a dictionary.
        
        Returns:
            Dictionary representation of the profile
        """
        return {
            'document_type': self._profile.document_type,
            'namespace': self._profile.namespace,
            'namespaces': self._profile.namespaces,
            'root_element': self._profile.root_element,
            'statistics': self._profile.statistics,
            'container_patterns': self._profile.container_patterns,
            'parameter_patterns': [
                {'parent': p, 'tag': t} for p, t in self._profile.parameter_patterns
            ],
            'reference_patterns': [
                {'parent': p, 'tag': t} for p, t in self._profile.reference_patterns
            ],
            'naming_conventions': {
                k.value: v.value for k, v in self._profile.naming_conventions.items()
            }
        }