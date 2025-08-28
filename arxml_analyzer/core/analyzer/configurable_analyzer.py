"""Configurable base analyzer that uses document profiling for adaptive analysis.

This module provides a base class for analyzers that can adapt to different
ARXML document structures without hardcoded element names.
"""

from typing import Dict, Any, List, Optional, Set
from abc import abstractmethod
import xml.etree.ElementTree as etree
from pathlib import Path
import json

from .base_analyzer import BaseAnalyzer, AnalysisResult, AnalysisMetadata, AnalysisStatus
from ..profiler.document_profiler import DocumentProfiler, DocumentProfile
from ...models.arxml_document import ARXMLDocument


class ConfigurableAnalyzer(BaseAnalyzer):
    """Base analyzer that uses document profiling for adaptive analysis.
    
    This class provides a framework for creating analyzers that can
    adapt to different ARXML structures without hardcoding element names.
    """
    
    def __init__(self, name: str = "ConfigurableAnalyzer", version: str = "1.0.0"):
        """Initialize the configurable analyzer.
        
        Args:
            name: Name of the analyzer
            version: Version of the analyzer
        """
        super().__init__(name=name, version=version)
        self._profiler = DocumentProfiler()
        self._profile: Optional[DocumentProfile] = None
        self._config: Dict[str, Any] = {}
        self._element_mappings: Dict[str, List[str]] = {}
        
    def analyze(self, document: ARXMLDocument) -> AnalysisResult:
        """Analyze an ARXML document using adaptive profiling.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            Analysis results
        """
        # Create result with metadata
        metadata = AnalysisMetadata(
            analyzer_name=self.name,
            analyzer_version=self.version,
            arxml_type="ADAPTIVE"
        )
        result = AnalysisResult(metadata=metadata)
        
        try:
            # Profile the document structure
            self._profile = self._profiler.profile_document(document.root)
            
            # Load or generate configuration based on profile
            self._configure_for_document_type()
            
            # Perform adaptive analysis
            self._perform_adaptive_analysis(document, result)
            
            # Add profile information to results
            result.details['document_profile'] = self._profiler.export_profile()
            
            metadata.status = AnalysisStatus.COMPLETED
            
        except Exception as e:
            metadata.status = AnalysisStatus.FAILED
            metadata.errors.append(f"Analysis failed: {str(e)}")
            
        return result
    
    def _configure_for_document_type(self) -> None:
        """Configure the analyzer based on the detected document type."""
        if not self._profile:
            return
            
        doc_type = self._profile.document_type
        
        # Map logical element types to actual element names found in document
        self._element_mappings = {
            'modules': self._profiler.suggest_patterns_for_type('module'),
            'containers': self._profiler.get_container_elements(),
            'parameters': self._profiler.get_parameter_elements(),
            'references': self._profiler.get_reference_elements(),
            'configurations': self._profiler.suggest_patterns_for_type('configuration')
        }
        
        # Load type-specific configuration if available
        config_file = self._get_config_file_for_type(doc_type)
        if config_file and config_file.exists():
            self._load_configuration(config_file)
        else:
            # Use default adaptive configuration
            self._config = self._generate_default_config()
    
    def _get_config_file_for_type(self, doc_type: str) -> Optional[Path]:
        """Get configuration file path for a document type.
        
        Args:
            doc_type: Type of document
            
        Returns:
            Path to configuration file or None
        """
        # Configuration files stored in configs directory
        config_dir = Path(__file__).parent.parent.parent / "configs"
        if not config_dir.exists():
            return None
            
        config_file = config_dir / f"{doc_type.lower()}_config.json"
        return config_file if config_file.exists() else None
    
    def _load_configuration(self, config_file: Path) -> None:
        """Load configuration from a JSON file.
        
        Args:
            config_file: Path to configuration file
        """
        try:
            with open(config_file, 'r') as f:
                self._config = json.load(f)
        except Exception as e:
            # Fall back to default config on error
            self._config = self._generate_default_config()
    
    def _generate_default_config(self) -> Dict[str, Any]:
        """Generate default configuration based on document profile.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'analyze_containers': len(self._element_mappings.get('containers', [])) > 0,
            'analyze_parameters': len(self._element_mappings.get('parameters', [])) > 0,
            'analyze_references': len(self._element_mappings.get('references', [])) > 0,
            'max_depth': self._profile.hierarchy_depth if self._profile else 10,
            'extract_patterns': True,
            'validate_references': True
        }
    
    def _perform_adaptive_analysis(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Perform adaptive analysis based on document profile.
        
        Args:
            document: ARXML document to analyze
            result: Analysis result to update
        """
        # Analyze modules if found
        if 'modules' in self._element_mappings:
            self._analyze_modules(document, result)
        
        # Analyze containers if configured
        if self._config.get('analyze_containers') and 'containers' in self._element_mappings:
            self._analyze_containers(document, result)
        
        # Analyze parameters if configured
        if self._config.get('analyze_parameters') and 'parameters' in self._element_mappings:
            self._analyze_parameters(document, result)
        
        # Analyze references if configured
        if self._config.get('analyze_references') and 'references' in self._element_mappings:
            self._analyze_references(document, result)
        
        # Extract patterns if configured
        if self._config.get('extract_patterns'):
            self._extract_patterns(document, result)
    
    def _analyze_modules(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Analyze module elements found in the document.
        
        Args:
            document: ARXML document
            result: Analysis result to update
        """
        modules = []
        module_tags = self._element_mappings.get('modules', [])
        
        for tag in module_tags:
            xpath = self._profiler.get_element_xpath(tag)
            elements = self._find_elements_by_xpath(document.root, xpath)
            
            for elem in elements:
                module_info = self._extract_element_info(elem)
                if module_info:
                    modules.append(module_info)
        
        if modules:
            result.details['modules'] = modules
            result.summary['total_modules'] = len(modules)
    
    def _analyze_containers(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Analyze container elements found in the document.
        
        Args:
            document: ARXML document
            result: Analysis result to update
        """
        containers = []
        container_tags = self._element_mappings.get('containers', [])
        
        for tag in container_tags:
            xpath = self._profiler.get_element_xpath(tag)
            elements = self._find_elements_by_xpath(document.root, xpath)
            
            for elem in elements:
                container_info = self._extract_element_info(elem)
                if container_info:
                    # Add container-specific information
                    container_info['child_count'] = len(list(elem))
                    containers.append(container_info)
        
        if containers:
            result.details['containers'] = containers
            result.summary['total_containers'] = len(containers)
    
    def _analyze_parameters(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Analyze parameter elements found in the document.
        
        Args:
            document: ARXML document
            result: Analysis result to update
        """
        parameters = []
        param_tags = self._element_mappings.get('parameters', [])
        
        for tag in param_tags:
            xpath = self._profiler.get_element_xpath(tag)
            elements = self._find_elements_by_xpath(document.root, xpath)
            
            for elem in elements:
                param_info = self._extract_parameter_info(elem)
                if param_info:
                    parameters.append(param_info)
        
        if parameters:
            result.details['parameters'] = parameters
            result.summary['total_parameters'] = len(parameters)
            
            # Add parameter type statistics
            param_types = {}
            for param in parameters:
                ptype = param.get('type', 'UNKNOWN')
                param_types[ptype] = param_types.get(ptype, 0) + 1
            result.statistics['parameter_types'] = param_types
    
    def _analyze_references(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Analyze reference elements found in the document.
        
        Args:
            document: ARXML document
            result: Analysis result to update
        """
        references = []
        ref_tags = self._element_mappings.get('references', [])
        
        for tag in ref_tags:
            xpath = self._profiler.get_element_xpath(tag)
            elements = self._find_elements_by_xpath(document.root, xpath)
            
            for elem in elements:
                ref_info = self._extract_reference_info(elem)
                if ref_info:
                    references.append(ref_info)
        
        if references:
            result.details['references'] = references
            result.summary['total_references'] = len(references)
            
            # Check for broken references if configured
            if self._config.get('validate_references'):
                broken_refs = self._validate_references(references, document)
                if broken_refs:
                    result.metadata.warnings.append(
                        f"Found {len(broken_refs)} potentially broken references"
                    )
                    result.details['broken_references'] = broken_refs
    
    def _extract_patterns(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Extract patterns from the document.
        
        Args:
            document: ARXML document
            result: Analysis result to update
        """
        patterns = {}
        
        # Naming patterns
        if self._profile:
            patterns['naming_conventions'] = {
                k.value: v for k, v in self._profile.naming_conventions.items()
            }
        
        # Structural patterns
        patterns['hierarchy_depth'] = self._profile.hierarchy_depth if self._profile else 0
        patterns['element_diversity'] = len(self._element_mappings.get('modules', []))
        
        # Add to results
        result.patterns.update(patterns)
    
    def _find_elements_by_xpath(self, root: etree.Element, xpath: str) -> List[etree.Element]:
        """Find elements using XPath expression.
        
        Args:
            root: Root element to search from
            xpath: XPath expression
            
        Returns:
            List of matching elements
        """
        try:
            # Try with namespaces if available
            if self._profile and self._profile.namespaces:
                return root.xpath(xpath, namespaces=self._profile.namespaces)
            else:
                # Fall back to namespace-agnostic search
                return root.findall(xpath.replace('//', './/'))
        except Exception:
            return []
    
    def _extract_element_info(self, element: etree.Element) -> Dict[str, Any]:
        """Extract generic information from an element.
        
        Args:
            element: XML element
            
        Returns:
            Dictionary with element information
        """
        info = {
            'tag': self._get_local_name(element.tag),
            'attributes': dict(element.attrib)
        }
        
        # Try to find common identifiers
        for attr in ['name', 'NAME', 'id', 'ID', 'uuid', 'UUID']:
            if attr in element.attrib:
                info['identifier'] = element.attrib[attr]
                break
        
        # Look for SHORT-NAME element (common in AUTOSAR)
        short_name = self._find_child_text(element, ['SHORT-NAME', 'short-name', 'ShortName'])
        if short_name:
            info['name'] = short_name
        
        # Look for DEFINITION-REF (common in AUTOSAR)
        def_ref = self._find_child_text(element, ['DEFINITION-REF', 'definition-ref', 'DefinitionRef'])
        if def_ref:
            info['definition_ref'] = def_ref
        
        return info
    
    def _extract_parameter_info(self, element: etree.Element) -> Dict[str, Any]:
        """Extract parameter-specific information.
        
        Args:
            element: Parameter XML element
            
        Returns:
            Dictionary with parameter information
        """
        info = self._extract_element_info(element)
        
        # Try to find value
        value_elem = self._find_child(element, ['VALUE', 'value', 'Value'])
        if value_elem is not None:
            info['value'] = value_elem.text
        
        # Try to determine parameter type
        tag = self._get_local_name(element.tag).upper()
        if 'NUMERICAL' in tag or 'INTEGER' in tag or 'FLOAT' in tag:
            info['type'] = 'NUMERICAL'
        elif 'TEXTUAL' in tag or 'STRING' in tag:
            info['type'] = 'TEXTUAL'
        elif 'BOOLEAN' in tag or 'BOOL' in tag:
            info['type'] = 'BOOLEAN'
        else:
            info['type'] = 'UNKNOWN'
        
        return info
    
    def _extract_reference_info(self, element: etree.Element) -> Dict[str, Any]:
        """Extract reference-specific information.
        
        Args:
            element: Reference XML element
            
        Returns:
            Dictionary with reference information
        """
        info = self._extract_element_info(element)
        
        # Get reference target (text content or specific attribute)
        if element.text and element.text.strip():
            info['target'] = element.text.strip()
        else:
            # Look for common reference attributes
            for attr in ['dest', 'DEST', 'target', 'TARGET', 'ref', 'REF']:
                if attr in element.attrib:
                    info['target'] = element.attrib[attr]
                    break
        
        # Determine reference type if possible
        tag = self._get_local_name(element.tag).upper()
        if 'DEFINITION' in tag:
            info['ref_type'] = 'DEFINITION'
        elif 'VALUE' in tag:
            info['ref_type'] = 'VALUE'
        else:
            info['ref_type'] = 'GENERIC'
        
        return info
    
    def _validate_references(self, references: List[Dict[str, Any]], 
                           document: ARXMLDocument) -> List[Dict[str, Any]]:
        """Validate references to check for broken links.
        
        Args:
            references: List of reference information
            document: ARXML document
            
        Returns:
            List of broken references
        """
        broken = []
        
        # Build a set of valid targets (simplified validation)
        valid_targets = set()
        
        # Collect all identifiable elements as potential targets
        for tag in self._profile.element_patterns.keys() if self._profile else []:
            xpath = self._profiler.get_element_xpath(tag)
            elements = self._find_elements_by_xpath(document.root, xpath)
            
            for elem in elements:
                # Add various identifiers as valid targets
                for attr in ['name', 'NAME', 'id', 'ID', 'uuid', 'UUID']:
                    if attr in elem.attrib:
                        valid_targets.add(elem.attrib[attr])
                
                # Add SHORT-NAME as valid target
                short_name = self._find_child_text(elem, ['SHORT-NAME', 'short-name'])
                if short_name:
                    valid_targets.add(short_name)
        
        # Check each reference
        for ref in references:
            target = ref.get('target')
            if target:
                # Simple check: target should exist in valid targets or be a path
                if '/' in target:
                    # Path reference - check last component
                    last_component = target.split('/')[-1]
                    if last_component not in valid_targets:
                        broken.append(ref)
                elif target not in valid_targets:
                    broken.append(ref)
        
        return broken
    
    def _find_child(self, element: etree.Element, names: List[str]) -> Optional[etree.Element]:
        """Find a child element with any of the given names.
        
        Args:
            element: Parent element
            names: List of possible child names
            
        Returns:
            First matching child element or None
        """
        for child in element:
            local_name = self._get_local_name(child.tag)
            if local_name in names or local_name.upper() in [n.upper() for n in names]:
                return child
        return None
    
    def _find_child_text(self, element: etree.Element, names: List[str]) -> Optional[str]:
        """Find text content of a child element.
        
        Args:
            element: Parent element
            names: List of possible child names
            
        Returns:
            Text content of first matching child or None
        """
        child = self._find_child(element, names)
        if child is not None and child.text:
            return child.text.strip()
        return None
    
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
    
    @abstractmethod
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns this analyzer looks for.
        
        Returns:
            List of pattern definitions
        """
        # Subclasses should override this to provide specific patterns
        return []