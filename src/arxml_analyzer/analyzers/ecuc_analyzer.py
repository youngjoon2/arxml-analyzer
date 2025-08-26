"""ECUC (ECU Configuration) analyzer for ARXML files."""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
import re
from lxml import etree

from ..core.analyzer.base_analyzer import (
    BaseAnalyzer, 
    AnalysisResult, 
    AnalysisMetadata,
    AnalysisLevel,
    AnalysisStatus
)
from ..core.analyzer.pattern_finder import PatternFinder, PatternType
from ..models.arxml_document import ARXMLDocument
from ..utils.exceptions import AnalysisError


@dataclass
class ECUCModule:
    """Represents an ECUC module configuration."""
    name: str
    definition_ref: str
    containers: List[Dict[str, Any]] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)
    sub_containers: List['ECUCModule'] = field(default_factory=list)
    

@dataclass 
class ECUCParameter:
    """Represents an ECUC parameter."""
    name: str
    definition_ref: str
    value: Any
    parameter_type: str  # BOOLEAN, INTEGER, STRING, ENUMERATION, etc.
    is_symbolic: bool = False
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    default_value: Optional[Any] = None


class ECUCAnalyzer(BaseAnalyzer):
    """Analyzer for ECUC (ECU Configuration) ARXML files.
    
    Analyzes:
    - Module configurations
    - Parameter values and constraints
    - Container structures
    - Reference integrity
    - Configuration dependencies
    """
    
    def __init__(self):
        """Initialize the ECUC analyzer."""
        super().__init__(name="ECUCAnalyzer", version="1.0.0")
        self._supported_types = {"ECUC", "ECU_CONFIGURATION"}
        self._pattern_finder = PatternFinder()
        self._modules: Dict[str, ECUCModule] = {}
        self._parameters: Dict[str, List[ECUCParameter]] = {}
        self._references: Dict[str, List[str]] = {}
        
    def analyze(self, document: ARXMLDocument) -> AnalysisResult:
        """Analyze ECUC configuration in the ARXML document.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            Analysis results with ECUC-specific findings
        """
        # Create result with metadata
        metadata = AnalysisMetadata(
            analyzer_name=self.name,
            analyzer_version=self.version,
            arxml_type="ECUC"
        )
        result = AnalysisResult(metadata=metadata)
        
        try:
            # Extract ECUC modules
            self._extract_modules(document, result)
            
            # Analyze parameters
            self._analyze_parameters(result)
            
            # Analyze container structures
            self._analyze_containers(result)
            
            # Check reference integrity
            self._check_references(result)
            
            # Analyze dependencies
            self._analyze_dependencies(result)
            
            # Find patterns
            self._find_patterns(document, result)
            
            # Generate statistics
            self._generate_statistics(result)
            
            # Generate recommendations
            self._generate_recommendations(result)
            
            metadata.status = AnalysisStatus.COMPLETED
            
        except Exception as e:
            metadata.status = AnalysisStatus.FAILED
            metadata.errors.append(str(e))
            
        return result
    
    def _extract_modules(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Extract ECUC module configurations.
        
        Args:
            document: ARXML document
            result: Analysis result to update
        """
        modules = []
        
        # Use default namespace if not provided
        namespaces = document.namespaces or {}
        if not namespaces:
            # Try to extract namespace from root element
            if document.root.nsmap:
                namespaces = {'ar': document.root.nsmap.get(None, 'http://www.autosar.org/schema/r4.0')}
            else:
                namespaces = {'ar': 'http://www.autosar.org/schema/r4.0'}
        
        # Find ECUC module configuration elements - use findall with Clark notation
        ns = '{http://www.autosar.org/schema/r4.0}'
        module_configs = document.root.findall(f".//{ns}ECUC-MODULE-CONFIGURATION-VALUES", namespaces=None)
        
        for module_elem in module_configs:
            module = self._parse_module(module_elem, namespaces)
            if module:
                self._modules[module.name] = module
                modules.append({
                    'name': module.name,
                    'definition_ref': module.definition_ref,
                    'container_count': len(module.containers),
                    'parameter_count': len(module.parameters),
                    'reference_count': len(module.references)
                })
        
        result.details['modules'] = modules
        result.summary['total_modules'] = len(modules)
        
    def _parse_module(self, element: etree.Element, namespaces: Dict[str, str]) -> Optional[ECUCModule]:
        """Parse a single ECUC module configuration.
        
        Args:
            element: Module configuration XML element
            namespaces: XML namespaces
            
        Returns:
            Parsed ECUCModule or None
        """
        try:
            # Extract module name using namespace directly
            short_name = element.find(".//{http://www.autosar.org/schema/r4.0}SHORT-NAME")
            if short_name is None:
                return None
                
            module = ECUCModule(
                name=short_name.text,
                definition_ref=element.get('DEFINITION-REF', '')
            )
            
            # Extract containers
            containers = element.xpath(".//{http://www.autosar.org/schema/r4.0}ECUC-CONTAINER-VALUE")
            for container in containers:
                container_data = self._parse_container(container, namespaces)
                if container_data:
                    module.containers.append(container_data)
            
            # Extract parameters
            params = element.xpath(".//{http://www.autosar.org/schema/r4.0}ECUC-PARAMETER-VALUE")
            for param in params:
                param_data = self._parse_parameter(param, namespaces)
                if param_data:
                    module.parameters.append(param_data)
            
            # Extract references
            refs = element.xpath(".//{http://www.autosar.org/schema/r4.0}ECUC-REFERENCE-VALUE")
            for ref in refs:
                ref_data = self._parse_reference(ref, namespaces)
                if ref_data:
                    module.references.append(ref_data)
            
            return module
            
        except Exception as e:
            # Log error but continue processing
            return None
    
    def _parse_container(self, element: etree.Element, namespaces: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse an ECUC container value.
        
        Args:
            element: Container XML element
            namespaces: XML namespaces
            
        Returns:
            Container data dictionary or None
        """
        try:
            short_name = element.find(".//{http://www.autosar.org/schema/r4.0}SHORT-NAME")
            if short_name is None:
                return None
            
            container = {
                'name': short_name.text,
                'definition_ref': element.get('DEFINITION-REF', ''),
                'parameters': [],
                'sub_containers': []
            }
            
            # Extract nested parameters
            params = element.xpath(".//{http://www.autosar.org/schema/r4.0}ECUC-NUMERICAL-PARAM-VALUE | .//{http://www.autosar.org/schema/r4.0}ECUC-TEXTUAL-PARAM-VALUE")
            for param in params:
                param_data = self._parse_parameter(param, namespaces)
                if param_data:
                    container['parameters'].append(param_data)
            
            # Extract nested containers
            sub_containers = element.xpath(".//{http://www.autosar.org/schema/r4.0}ECUC-CONTAINER-VALUE")
            for sub in sub_containers:
                if sub != element:  # Avoid self-reference
                    sub_data = self._parse_container(sub, namespaces)
                    if sub_data:
                        container['sub_containers'].append(sub_data)
            
            return container
            
        except Exception:
            return None
    
    def _parse_parameter(self, element: etree.Element, namespaces: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse an ECUC parameter value.
        
        Args:
            element: Parameter XML element
            namespaces: XML namespaces
            
        Returns:
            Parameter data dictionary or None
        """
        try:
            definition_ref = element.find(".//{http://www.autosar.org/schema/r4.0}DEFINITION-REF")
            if definition_ref is None:
                return None
            
            param = {
                'name': definition_ref.text.split('/')[-1] if definition_ref.text else 'unknown',
                'definition_ref': definition_ref.text,
                'type': element.tag.split('}')[-1] if '}' in element.tag else element.tag
            }
            
            # Extract value based on parameter type
            if 'NUMERICAL' in param['type']:
                value_elem = element.find(".//{http://www.autosar.org/schema/r4.0}VALUE")
                param['value'] = int(value_elem.text) if value_elem is not None and value_elem.text else None
                param['parameter_type'] = 'INTEGER'
            elif 'TEXTUAL' in param['type']:
                value_elem = element.find(".//{http://www.autosar.org/schema/r4.0}VALUE")
                param['value'] = value_elem.text if value_elem is not None else None
                param['parameter_type'] = 'STRING'
            elif 'BOOLEAN' in param['type']:
                value_elem = element.find(".//{http://www.autosar.org/schema/r4.0}VALUE")
                param['value'] = value_elem.text.lower() == 'true' if value_elem is not None and value_elem.text else None
                param['parameter_type'] = 'BOOLEAN'
            else:
                value_elem = element.find(".//{http://www.autosar.org/schema/r4.0}VALUE")
                param['value'] = value_elem.text if value_elem is not None else None
                param['parameter_type'] = 'UNKNOWN'
            
            # Check if symbolic
            param['is_symbolic'] = element.find(".//{http://www.autosar.org/schema/r4.0}IS-SYMBOLIC") is not None
            
            return param
            
        except Exception:
            return None
    
    def _parse_reference(self, element: etree.Element, namespaces: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse an ECUC reference value.
        
        Args:
            element: Reference XML element  
            namespaces: XML namespaces
            
        Returns:
            Reference data dictionary or None
        """
        try:
            definition_ref = element.find(".//{http://www.autosar.org/schema/r4.0}DEFINITION-REF")
            value_ref = element.find(".//{http://www.autosar.org/schema/r4.0}VALUE-REF")
            
            if definition_ref is None:
                return None
            
            return {
                'name': definition_ref.text.split('/')[-1] if definition_ref.text else 'unknown',
                'definition_ref': definition_ref.text,
                'value_ref': value_ref.text if value_ref is not None else None,
                'type': 'REFERENCE'
            }
            
        except Exception:
            return None
    
    def _analyze_parameters(self, result: AnalysisResult) -> None:
        """Analyze ECUC parameters for issues and patterns.
        
        Args:
            result: Analysis result to update
        """
        all_params = []
        param_stats = {
            'total': 0,
            'by_type': {},
            'symbolic_count': 0,
            'with_default': 0,
            'out_of_range': []
        }
        
        for module in self._modules.values():
            # Analyze module parameters
            for param in module.parameters:
                all_params.append(param)
                param_stats['total'] += 1
                
                # Count by type
                ptype = param.get('parameter_type', 'UNKNOWN')
                param_stats['by_type'][ptype] = param_stats['by_type'].get(ptype, 0) + 1
                
                # Check symbolic parameters
                if param.get('is_symbolic'):
                    param_stats['symbolic_count'] += 1
                
                # Check for potential issues
                if ptype == 'INTEGER' and param.get('value') is not None:
                    # Check common ranges
                    value = param['value']
                    if value < 0 or value > 65535:
                        param_stats['out_of_range'].append({
                            'parameter': param['name'],
                            'value': value,
                            'module': module.name
                        })
            
            # Also analyze container parameters
            for container in module.containers:
                self._analyze_container_params(container, all_params, param_stats, module.name)
        
        result.details['parameter_analysis'] = param_stats
        result.summary['total_parameters'] = param_stats['total']
        
        # Add warnings for out-of-range parameters
        for oor in param_stats['out_of_range']:
            result.metadata.warnings.append(
                f"Parameter '{oor['parameter']}' in module '{oor['module']}' has potentially out-of-range value: {oor['value']}"
            )
    
    def _analyze_container_params(self, container: Dict[str, Any], all_params: List[Dict], 
                                 param_stats: Dict[str, Any], module_name: str) -> None:
        """Recursively analyze container parameters.
        
        Args:
            container: Container data
            all_params: List to append parameters to
            param_stats: Statistics dictionary to update
            module_name: Parent module name
        """
        for param in container.get('parameters', []):
            all_params.append(param)
            param_stats['total'] += 1
            
            ptype = param.get('parameter_type', 'UNKNOWN')
            param_stats['by_type'][ptype] = param_stats['by_type'].get(ptype, 0) + 1
            
            if param.get('is_symbolic'):
                param_stats['symbolic_count'] += 1
        
        # Recurse into sub-containers
        for sub_container in container.get('sub_containers', []):
            self._analyze_container_params(sub_container, all_params, param_stats, module_name)
    
    def _analyze_containers(self, result: AnalysisResult) -> None:
        """Analyze container structures and hierarchies.
        
        Args:
            result: Analysis result to update
        """
        container_stats = {
            'total': 0,
            'max_depth': 0,
            'avg_params_per_container': 0,
            'empty_containers': [],
            'deep_nesting': []
        }
        
        total_params = 0
        
        for module in self._modules.values():
            for container in module.containers:
                depth = self._calculate_container_depth(container)
                container_stats['total'] += 1
                container_stats['max_depth'] = max(container_stats['max_depth'], depth)
                
                # Check for empty containers
                if not container.get('parameters') and not container.get('sub_containers'):
                    container_stats['empty_containers'].append({
                        'name': container['name'],
                        'module': module.name
                    })
                
                # Check for deep nesting
                if depth > 5:
                    container_stats['deep_nesting'].append({
                        'name': container['name'],
                        'module': module.name,
                        'depth': depth
                    })
                
                # Count parameters
                total_params += len(container.get('parameters', []))
        
        # Calculate average
        if container_stats['total'] > 0:
            container_stats['avg_params_per_container'] = total_params / container_stats['total']
        
        result.details['container_analysis'] = container_stats
        result.summary['total_containers'] = container_stats['total']
        
        # Add warnings for deep nesting
        for deep in container_stats['deep_nesting']:
            result.metadata.warnings.append(
                f"Container '{deep['name']}' in module '{deep['module']}' has deep nesting (depth: {deep['depth']})"
            )
    
    def _calculate_container_depth(self, container: Dict[str, Any], current_depth: int = 1) -> int:
        """Calculate the maximum depth of a container hierarchy.
        
        Args:
            container: Container data
            current_depth: Current recursion depth
            
        Returns:
            Maximum depth found
        """
        if not container.get('sub_containers'):
            return current_depth
        
        max_depth = current_depth
        for sub in container['sub_containers']:
            depth = self._calculate_container_depth(sub, current_depth + 1)
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _check_references(self, result: AnalysisResult) -> None:
        """Check reference integrity and find broken references.
        
        Args:
            result: Analysis result to update
        """
        ref_stats = {
            'total': 0,
            'broken': [],
            'circular': [],
            'external': []
        }
        
        all_refs = {}
        
        for module in self._modules.values():
            for ref in module.references:
                ref_stats['total'] += 1
                
                ref_path = ref.get('value_ref')
                if ref_path:
                    # Store reference for circular dependency check
                    if module.name not in all_refs:
                        all_refs[module.name] = []
                    all_refs[module.name].append(ref_path)
                    
                    # Check if reference is external
                    if ref_path.startswith('/') and not any(ref_path.endswith(m.name) for m in self._modules.values()):
                        ref_stats['external'].append({
                            'reference': ref['name'],
                            'target': ref_path,
                            'module': module.name
                        })
                else:
                    # Broken reference (no value)
                    ref_stats['broken'].append({
                        'reference': ref['name'],
                        'module': module.name
                    })
        
        # Check for circular references (simplified check)
        for module_name, refs in all_refs.items():
            for ref in refs:
                # Check if target references back to source
                target_module = ref.split('/')[-1] if '/' in ref else ref
                if target_module in all_refs:
                    if any(module_name in r for r in all_refs[target_module]):
                        ref_stats['circular'].append({
                            'from': module_name,
                            'to': target_module
                        })
        
        result.details['reference_analysis'] = ref_stats
        result.summary['total_references'] = ref_stats['total']
        
        # Add warnings for reference issues
        for broken in ref_stats['broken']:
            result.metadata.warnings.append(
                f"Broken reference '{broken['reference']}' in module '{broken['module']}'"
            )
        
        for circular in ref_stats['circular']:
            result.metadata.warnings.append(
                f"Potential circular reference between '{circular['from']}' and '{circular['to']}'"
            )
    
    def _analyze_dependencies(self, result: AnalysisResult) -> None:
        """Analyze module dependencies and configuration relationships.
        
        Args:
            result: Analysis result to update
        """
        dependencies = {
            'module_dependencies': {},
            'common_parameters': {},
            'configuration_groups': []
        }
        
        # Build dependency graph based on references
        for module in self._modules.values():
            deps = set()
            
            for ref in module.references:
                ref_path = ref.get('value_ref', '')
                if '/' in ref_path:
                    # Extract potential module reference
                    parts = ref_path.split('/')
                    for part in parts:
                        if part in self._modules and part != module.name:
                            deps.add(part)
            
            if deps:
                dependencies['module_dependencies'][module.name] = list(deps)
        
        # Find common parameters across modules
        param_modules = {}
        for module in self._modules.values():
            for param in module.parameters:
                param_name = param['name']
                if param_name not in param_modules:
                    param_modules[param_name] = []
                param_modules[param_name].append(module.name)
        
        # Filter to show only parameters used in multiple modules
        dependencies['common_parameters'] = {
            name: modules for name, modules in param_modules.items() 
            if len(modules) > 1
        }
        
        # Identify configuration groups (modules with similar parameters)
        if len(self._modules) > 1:
            groups = self._find_configuration_groups()
            dependencies['configuration_groups'] = groups
        
        result.details['dependencies'] = dependencies
        result.summary['module_dependencies'] = len(dependencies['module_dependencies'])
    
    def _find_configuration_groups(self) -> List[Dict[str, Any]]:
        """Find groups of modules with similar configurations.
        
        Returns:
            List of configuration groups
        """
        groups = []
        processed = set()
        
        for module1 in self._modules.values():
            if module1.name in processed:
                continue
            
            group = {
                'modules': [module1.name],
                'common_params': []
            }
            
            # Find modules with similar parameters
            module1_params = {p['name'] for p in module1.parameters}
            
            for module2 in self._modules.values():
                if module2.name != module1.name and module2.name not in processed:
                    module2_params = {p['name'] for p in module2.parameters}
                    
                    # Check similarity (> 50% common parameters)
                    common = module1_params & module2_params
                    if len(common) > 0 and len(common) / max(len(module1_params), len(module2_params)) > 0.5:
                        group['modules'].append(module2.name)
                        group['common_params'] = list(common)
                        processed.add(module2.name)
            
            if len(group['modules']) > 1:
                groups.append(group)
                processed.add(module1.name)
        
        return groups
    
    def _find_patterns(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Find ECUC-specific patterns in the document.
        
        Args:
            document: ARXML document
            result: Analysis result to update
        """
        # Find naming patterns using xpath
        naming_patterns = []
        
        # Find all module and container names
        module_names = document.root.xpath(
            ".//{http://www.autosar.org/schema/r4.0}ECUC-MODULE-CONFIGURATION-VALUES/{http://www.autosar.org/schema/r4.0}SHORT-NAME"
        )
        container_names = document.root.xpath(
            ".//{http://www.autosar.org/schema/r4.0}ECUC-CONTAINER-VALUE/{http://www.autosar.org/schema/r4.0}SHORT-NAME"
        )
        
        # Check naming conventions
        for elem in module_names + container_names:
            if elem.text:
                # Check for common patterns
                if re.match(r'^[A-Z][a-zA-Z0-9]+$', elem.text):
                    naming_patterns.append({
                        'pattern': 'PascalCase',
                        'element': elem.text,
                        'type': 'module' if elem in module_names else 'container'
                    })
        
        if naming_patterns:
            result.patterns['naming'] = naming_patterns[:10]  # Limit to first 10
        
        # Find configuration patterns
        config_patterns = []
        
        # Pattern: Modules with same definition reference
        def_refs = {}
        for module in self._modules.values():
            def_ref = module.definition_ref
            if def_ref:
                if def_ref not in def_refs:
                    def_refs[def_ref] = []
                def_refs[def_ref].append(module.name)
        
        for def_ref, modules in def_refs.items():
            if len(modules) > 1:
                config_patterns.append({
                    'pattern': 'shared_definition',
                    'definition': def_ref,
                    'modules': modules,
                    'count': len(modules)
                })
        
        if config_patterns:
            result.patterns['configuration'] = config_patterns
        
        # Find structural patterns - container hierarchies
        structure_patterns = []
        for module in self._modules.values():
            if module.containers:
                # Check for common structural patterns
                flat_containers = [c for c in module.containers if not c.get('sub_containers')]
                nested_containers = [c for c in module.containers if c.get('sub_containers')]
                
                if flat_containers and nested_containers:
                    structure_patterns.append({
                        'pattern': 'mixed_hierarchy',
                        'module': module.name,
                        'flat_count': len(flat_containers),
                        'nested_count': len(nested_containers)
                    })
        
        if structure_patterns:
            result.patterns['structure'] = structure_patterns
    
    def _generate_statistics(self, result: AnalysisResult) -> None:
        """Generate statistics for the ECUC configuration.
        
        Args:
            result: Analysis result to update
        """
        stats = {
            'modules': {
                'count': len(self._modules),
                'avg_containers': 0,
                'avg_parameters': 0,
                'avg_references': 0
            },
            'parameters': {
                'total': result.details.get('parameter_analysis', {}).get('total', 0),
                'by_type': result.details.get('parameter_analysis', {}).get('by_type', {}),
                'symbolic_ratio': 0
            },
            'containers': {
                'total': result.details.get('container_analysis', {}).get('total', 0),
                'max_depth': result.details.get('container_analysis', {}).get('max_depth', 0),
                'empty_count': len(result.details.get('container_analysis', {}).get('empty_containers', []))
            },
            'references': {
                'total': result.details.get('reference_analysis', {}).get('total', 0),
                'broken_count': len(result.details.get('reference_analysis', {}).get('broken', [])),
                'external_count': len(result.details.get('reference_analysis', {}).get('external', []))
            },
            'complexity': {
                'dependency_count': len(result.details.get('dependencies', {}).get('module_dependencies', {})),
                'common_param_count': len(result.details.get('dependencies', {}).get('common_parameters', {})),
                'config_group_count': len(result.details.get('dependencies', {}).get('configuration_groups', []))
            }
        }
        
        # Calculate averages
        if len(self._modules) > 0:
            total_containers = sum(len(m.containers) for m in self._modules.values())
            total_parameters = sum(len(m.parameters) for m in self._modules.values())
            total_references = sum(len(m.references) for m in self._modules.values())
            
            stats['modules']['avg_containers'] = total_containers / len(self._modules)
            stats['modules']['avg_parameters'] = total_parameters / len(self._modules)
            stats['modules']['avg_references'] = total_references / len(self._modules)
        
        # Calculate symbolic ratio
        param_analysis = result.details.get('parameter_analysis', {})
        if param_analysis.get('total', 0) > 0:
            stats['parameters']['symbolic_ratio'] = (
                param_analysis.get('symbolic_count', 0) / param_analysis['total']
            )
        
        result.statistics.update(stats)
    
    def _generate_recommendations(self, result: AnalysisResult) -> None:
        """Generate recommendations based on analysis.
        
        Args:
            result: Analysis result to update
        """
        # Check for empty containers
        container_analysis = result.details.get('container_analysis', {})
        if container_analysis.get('empty_containers'):
            result.add_recommendation(
                f"Found {len(container_analysis['empty_containers'])} empty containers. "
                "Consider removing unused containers or adding required parameters."
            )
        
        # Check for deep nesting
        if container_analysis.get('max_depth', 0) > 5:
            result.add_recommendation(
                "Deep container nesting detected (>5 levels). "
                "Consider flattening the hierarchy for better maintainability."
            )
        
        # Check for broken references
        ref_analysis = result.details.get('reference_analysis', {})
        if ref_analysis.get('broken'):
            result.add_recommendation(
                f"Found {len(ref_analysis['broken'])} broken references. "
                "Review and fix missing reference targets."
            )
        
        # Check for circular references
        if ref_analysis.get('circular'):
            result.add_recommendation(
                "Circular references detected. "
                "Review module dependencies to avoid circular dependencies."
            )
        
        # Check parameter distribution
        param_analysis = result.details.get('parameter_analysis', {})
        if param_analysis.get('out_of_range'):
            result.add_recommendation(
                f"Found {len(param_analysis['out_of_range'])} parameters with potentially out-of-range values. "
                "Review parameter constraints and valid ranges."
            )
        
        # Check for configuration groups
        dependencies = result.details.get('dependencies', {})
        if dependencies.get('configuration_groups'):
            result.add_recommendation(
                f"Found {len(dependencies['configuration_groups'])} groups of similar modules. "
                "Consider using shared configuration templates or inheritance."
            )
        
        # Check module count
        if len(self._modules) > 20:
            result.add_recommendation(
                f"Large number of modules detected ({len(self._modules)}). "
                "Consider modularizing or splitting the configuration for better management."
            )
        
        # Check for missing parameter types
        if 'UNKNOWN' in param_analysis.get('by_type', {}):
            unknown_count = param_analysis['by_type']['UNKNOWN']
            result.add_recommendation(
                f"Found {unknown_count} parameters with unknown types. "
                "Ensure all parameters have properly defined types."
            )
    
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns this analyzer looks for.
        
        Returns:
            List of pattern definitions
        """
        return [
            {
                'name': 'shared_definition',
                'description': 'Modules sharing the same definition reference',
                'type': 'configuration'
            },
            {
                'name': 'naming_consistency',
                'description': 'Consistent naming patterns for modules and containers',
                'type': 'naming'
            },
            {
                'name': 'parameter_groups',
                'description': 'Groups of commonly used parameters',
                'type': 'configuration'
            },
            {
                'name': 'container_hierarchy',
                'description': 'Container nesting and structural patterns',
                'type': 'structural'
            },
            {
                'name': 'reference_patterns',
                'description': 'Common reference patterns and dependencies',
                'type': 'dependency'
            }
        ]