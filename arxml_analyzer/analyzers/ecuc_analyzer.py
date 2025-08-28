"""ECUC (ECU Configuration) analyzer - Version 2 with adaptive analysis.

This version uses DocumentProfiler and ConfigurableAnalyzer for better adaptability
across different AUTOSAR tool chains and naming conventions.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
import re

from ..core.analyzer.configurable_analyzer import ConfigurableAnalyzer
from ..core.analyzer.base_analyzer import (
    AnalysisResult, 
    AnalysisMetadata,
    AnalysisLevel,
    AnalysisStatus
)
from ..models.arxml_document import ARXMLDocument


@dataclass
class ECUCModule:
    """Represents an ECUC module configuration (adaptive version)."""
    name: str
    element_tag: str
    definition_ref: Optional[str] = None
    containers: List[Dict[str, Any]] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)


# Backward compatibility alias
ECUCParameter = Dict[str, Any]


class ECUCAnalyzer(ConfigurableAnalyzer):
    """Adaptive ECUC analyzer that doesn't rely on hardcoded element names.
    
    This analyzer:
    - Automatically discovers ECUC structure
    - Adapts to different tool naming conventions
    - Works with various AUTOSAR versions
    - Provides the same analysis capabilities as V1 but with better flexibility
    """
    
    def __init__(self):
        """Initialize the adaptive ECUC analyzer."""
        super().__init__(name="ECUCAnalyzer", version="2.0.0")
        self._modules: Dict[str, ECUCModule] = {}
        
    def analyze(self, document: ARXMLDocument) -> AnalysisResult:
        """Analyze ECUC configuration using adaptive profiling.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            Analysis results with ECUC-specific findings
        """
        # First profile the document
        result = super().analyze(document)
        
        # Check if this is actually an ECUC document
        if self._profile and self._profile.document_type not in ['ECUC', 'UNKNOWN']:
            # If it's clearly not ECUC, update the type
            result.metadata.arxml_type = self._profile.document_type
            result.metadata.warnings.append(
                f"Document appears to be {self._profile.document_type}, not ECUC. "
                "Analysis may be limited."
            )
        else:
            result.metadata.arxml_type = "ECUC"
        
        # Perform ECUC-specific analysis
        self._analyze_ecuc_specific(document, result)
        
        return result
    
    def _analyze_ecuc_specific(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Perform ECUC-specific analysis.
        
        Args:
            document: ARXML document
            result: Analysis result to update
        """
        # Find module configurations using adaptive patterns
        self._discover_ecuc_modules(document, result)
        
        # Analyze module structures
        self._analyze_module_structures(result)
        
        # Check configuration consistency
        self._check_configuration_consistency(result)
        
        # Generate ECUC-specific recommendations
        self._generate_ecuc_recommendations(result)
    
    def _discover_ecuc_modules(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Discover ECUC modules using pattern matching.
        
        Args:
            document: ARXML document
            result: Analysis result to update
        """
        modules = []
        
        # Look for elements that match module patterns
        # Common patterns: MODULE, CONFIGURATION, CONFIG
        module_patterns = [
            r'.*MODULE.*CONFIGURATION.*',
            r'.*MODULE.*CONFIG.*',
            r'.*ECUC.*MODULE.*',
            r'.*CONFIG.*VALUES.*'
        ]
        
        discovered_module_tags = set()
        
        # Search through profiled elements
        if self._profile:
            for tag, pattern in self._profile.element_patterns.items():
                for module_pattern in module_patterns:
                    if re.match(module_pattern, tag.upper()):
                        discovered_module_tags.add(tag)
                        break
        
        # Extract module information
        for tag in discovered_module_tags:
            xpath = self._profiler.get_element_xpath(tag)
            elements = self._find_elements_by_xpath(document.root, xpath)
            
            for elem in elements:
                module_info = self._extract_ecuc_module(elem, tag)
                if module_info:
                    self._modules[module_info.name] = module_info
                    modules.append({
                        'name': module_info.name,
                        'type': tag,
                        'definition_ref': module_info.definition_ref,
                        'container_count': len(module_info.containers),
                        'parameter_count': len(module_info.parameters),
                        'reference_count': len(module_info.references)
                    })
        
        # Also check for modules in already identified containers
        if not modules and 'containers' in result.details:
            # Some ECUC files might structure modules as containers
            for container in result.details.get('containers', []):
                if self._is_likely_module(container):
                    module = ECUCModule(
                        name=container.get('name', 'unknown'),
                        element_tag=container.get('tag', 'container')
                    )
                    self._modules[module.name] = module
                    modules.append({
                        'name': module.name,
                        'type': 'container-based',
                        'container_count': container.get('child_count', 0)
                    })
        
        if modules:
            result.details['ecuc_modules'] = modules
            result.summary['ecuc_module_count'] = len(modules)
    
    def _extract_ecuc_module(self, element: Any, tag: str) -> Optional[ECUCModule]:
        """Extract ECUC module information from an element.
        
        Args:
            element: XML element
            tag: Element tag name
            
        Returns:
            ECUCModule instance or None
        """
        # Extract basic module information
        module_info = self._extract_element_info(element)
        if not module_info:
            return None
        
        module = ECUCModule(
            name=module_info.get('name', module_info.get('identifier', 'unknown')),
            element_tag=tag,
            definition_ref=module_info.get('definition_ref')
        )
        
        # Look for containers within the module
        container_patterns = ['CONTAINER', 'CONT', 'SUB-CONTAINER']
        for child in element:
            child_tag = self._get_local_name(child.tag)
            
            # Check if it's a container
            is_container = any(
                pattern in child_tag.upper() 
                for pattern in container_patterns
            )
            
            if is_container:
                container_info = self._extract_container_info(child)
                if container_info:
                    module.containers.append(container_info)
            
            # Check if it's a parameter
            elif self._is_parameter_element(child_tag):
                param_info = self._extract_parameter_info(child)
                if param_info:
                    module.parameters.append(param_info)
            
            # Check if it's a reference
            elif self._is_reference_element(child_tag):
                ref_info = self._extract_reference_info(child)
                if ref_info:
                    module.references.append(ref_info)
        
        # Also check for grouped parameters/references
        self._extract_grouped_elements(element, module)
        
        return module
    
    def _extract_container_info(self, element: Any) -> Dict[str, Any]:
        """Extract container information adaptively.
        
        Args:
            element: Container element
            
        Returns:
            Container information dictionary
        """
        info = self._extract_element_info(element)
        
        # Count nested elements
        param_count = 0
        ref_count = 0
        sub_container_count = 0
        
        for child in element:
            child_tag = self._get_local_name(child.tag)
            if self._is_parameter_element(child_tag):
                param_count += 1
            elif self._is_reference_element(child_tag):
                ref_count += 1
            elif 'CONTAINER' in child_tag.upper():
                sub_container_count += 1
        
        info.update({
            'parameter_count': param_count,
            'reference_count': ref_count,
            'sub_container_count': sub_container_count
        })
        
        return info
    
    def _extract_grouped_elements(self, element: Any, module: ECUCModule) -> None:
        """Extract parameters and references from grouped sections.
        
        Args:
            element: Module element
            module: Module to update
        """
        # Look for PARAMETER-VALUES or similar groupings
        param_group_patterns = ['PARAMETER-VALUES', 'PARAM-VALUES', 'PARAMETERS']
        ref_group_patterns = ['REFERENCE-VALUES', 'REF-VALUES', 'REFERENCES']
        
        for child in element:
            child_tag = self._get_local_name(child.tag).upper()
            
            # Check for parameter groups
            if any(pattern in child_tag for pattern in param_group_patterns):
                for param_elem in child:
                    param_info = self._extract_parameter_info(param_elem)
                    if param_info:
                        module.parameters.append(param_info)
            
            # Check for reference groups
            elif any(pattern in child_tag for pattern in ref_group_patterns):
                for ref_elem in child:
                    ref_info = self._extract_reference_info(ref_elem)
                    if ref_info:
                        module.references.append(ref_info)
    
    def _is_parameter_element(self, tag: str) -> bool:
        """Check if an element tag indicates a parameter.
        
        Args:
            tag: Element tag name
            
        Returns:
            True if likely a parameter element
        """
        upper_tag = tag.upper()
        param_indicators = ['PARAM', 'PARAMETER', 'VALUE', 'NUMERICAL', 'TEXTUAL', 'BOOLEAN']
        return any(indicator in upper_tag for indicator in param_indicators)
    
    def _is_reference_element(self, tag: str) -> bool:
        """Check if an element tag indicates a reference.
        
        Args:
            tag: Element tag name
            
        Returns:
            True if likely a reference element
        """
        upper_tag = tag.upper()
        ref_indicators = ['REF', 'REFERENCE']
        # Exclude DEFINITION-REF which is usually an attribute
        return any(indicator in upper_tag for indicator in ref_indicators) and 'DEFINITION' not in upper_tag
    
    def _is_likely_module(self, container: Dict[str, Any]) -> bool:
        """Check if a container is likely an ECUC module.
        
        Args:
            container: Container information
            
        Returns:
            True if likely a module
        """
        name = container.get('name', '').upper()
        tag = container.get('tag', '').upper()
        
        module_indicators = ['MODULE', 'ECUC', 'CONFIG', 'CONFIGURATION']
        return any(indicator in name or indicator in tag for indicator in module_indicators)
    
    def _analyze_module_structures(self, result: AnalysisResult) -> None:
        """Analyze the structure of discovered modules.
        
        Args:
            result: Analysis result to update
        """
        if not self._modules:
            return
        
        structure_analysis = {
            'total_parameters': 0,
            'total_containers': 0,
            'total_references': 0,
            'parameter_types': {},
            'max_nesting_depth': 0,
            'modules_with_issues': []
        }
        
        for module in self._modules.values():
            # Count totals
            structure_analysis['total_parameters'] += len(module.parameters)
            structure_analysis['total_containers'] += len(module.containers)
            structure_analysis['total_references'] += len(module.references)
            
            # Analyze parameter types
            for param in module.parameters:
                ptype = param.get('type', 'UNKNOWN')
                structure_analysis['parameter_types'][ptype] = \
                    structure_analysis['parameter_types'].get(ptype, 0) + 1
            
            # Check for potential issues
            if len(module.parameters) == 0 and len(module.containers) == 0:
                structure_analysis['modules_with_issues'].append({
                    'module': module.name,
                    'issue': 'Empty module (no parameters or containers)'
                })
            
            # Check for missing references
            for ref in module.references:
                if not ref.get('target'):
                    structure_analysis['modules_with_issues'].append({
                        'module': module.name,
                        'issue': f"Reference without target: {ref.get('name', 'unknown')}"
                    })
        
        result.details['module_structure_analysis'] = structure_analysis
        
        # Add warnings for issues
        for issue in structure_analysis['modules_with_issues']:
            result.metadata.warnings.append(
                f"Module '{issue['module']}': {issue['issue']}"
            )
    
    def _check_configuration_consistency(self, result: AnalysisResult) -> None:
        """Check for configuration consistency across modules.
        
        Args:
            result: Analysis result to update
        """
        if len(self._modules) < 2:
            return
        
        consistency_checks = {
            'common_parameters': {},
            'parameter_conflicts': [],
            'cross_references': []
        }
        
        # Find common parameters across modules
        param_modules = {}
        for module in self._modules.values():
            for param in module.parameters:
                param_name = param.get('name', param.get('identifier', 'unknown'))
                if param_name != 'unknown':
                    if param_name not in param_modules:
                        param_modules[param_name] = []
                    param_modules[param_name].append({
                        'module': module.name,
                        'value': param.get('value')
                    })
        
        # Identify common parameters and conflicts
        for param_name, occurrences in param_modules.items():
            if len(occurrences) > 1:
                consistency_checks['common_parameters'][param_name] = occurrences
                
                # Check for conflicting values
                values = set(occ['value'] for occ in occurrences if occ['value'] is not None)
                if len(values) > 1:
                    consistency_checks['parameter_conflicts'].append({
                        'parameter': param_name,
                        'modules': [occ['module'] for occ in occurrences],
                        'values': list(values)
                    })
        
        # Check for cross-module references
        for module in self._modules.values():
            for ref in module.references:
                target = ref.get('target', '')
                # Check if target refers to another module
                for other_module in self._modules.values():
                    if other_module.name != module.name:
                        if other_module.name in target or target in other_module.name:
                            consistency_checks['cross_references'].append({
                                'from_module': module.name,
                                'to_module': other_module.name,
                                'reference': ref.get('name', 'unknown')
                            })
        
        result.details['configuration_consistency'] = consistency_checks
        
        # Add warnings for conflicts
        for conflict in consistency_checks['parameter_conflicts']:
            result.metadata.warnings.append(
                f"Parameter '{conflict['parameter']}' has conflicting values across modules: {conflict['values']}"
            )
    
    def _generate_ecuc_recommendations(self, result: AnalysisResult) -> None:
        """Generate ECUC-specific recommendations.
        
        Args:
            result: Analysis result to update
        """
        # Check module count
        module_count = len(self._modules)
        if module_count == 0:
            result.add_recommendation(
                "No ECUC modules found. Verify that this is an ECUC configuration file "
                "or check if the document uses non-standard naming conventions."
            )
        elif module_count > 50:
            result.add_recommendation(
                f"Large number of ECUC modules ({module_count}). "
                "Consider splitting the configuration into multiple files for better maintainability."
            )
        
        # Check for empty modules
        empty_modules = [
            m.name for m in self._modules.values() 
            if len(m.parameters) == 0 and len(m.containers) == 0
        ]
        if empty_modules:
            result.add_recommendation(
                f"Found {len(empty_modules)} empty modules. "
                "Review and populate required parameters or remove unused modules."
            )
        
        # Check parameter distribution
        structure_analysis = result.details.get('module_structure_analysis', {})
        if structure_analysis.get('parameter_types', {}).get('UNKNOWN', 0) > 0:
            result.add_recommendation(
                "Some parameters have unknown types. "
                "Ensure all parameters are properly typed for validation."
            )
        
        # Check for configuration conflicts
        consistency = result.details.get('configuration_consistency', {})
        if consistency.get('parameter_conflicts'):
            result.add_recommendation(
                "Found conflicting parameter values across modules. "
                "Review and align configuration values for consistency."
            )
        
        # Check reference validity
        if structure_analysis.get('modules_with_issues'):
            ref_issues = [
                issue for issue in structure_analysis['modules_with_issues']
                if 'Reference' in issue.get('issue', '')
            ]
            if ref_issues:
                result.add_recommendation(
                    f"Found {len(ref_issues)} reference issues. "
                    "Validate all references point to valid targets."
                )
    
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns this analyzer looks for.
        
        Returns:
            List of pattern definitions
        """
        return [
            {
                'name': 'ecuc_module_structure',
                'description': 'ECUC module configuration structure',
                'type': 'structural'
            },
            {
                'name': 'parameter_consistency',
                'description': 'Consistent parameter values across modules',
                'type': 'consistency'
            },
            {
                'name': 'reference_integrity',
                'description': 'Valid references between configuration elements',
                'type': 'integrity'
            },
            {
                'name': 'container_hierarchy',
                'description': 'Proper container nesting and organization',
                'type': 'structural'
            },
            {
                'name': 'naming_convention',
                'description': 'Consistent naming patterns for modules and parameters',
                'type': 'convention'
            }
        ]