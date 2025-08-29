"""Cross-reference analysis and dependency graph generation for ARXML documents."""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import re
from collections import defaultdict
import json

from ...models.arxml_document import ARXMLDocument


@dataclass
class Reference:
    """Represents a reference from one element to another."""
    
    source_element: str  # XPath or identifier of source element
    source_type: str  # Type of source element (e.g., 'RUNNABLE', 'PORT')
    target_element: str  # XPath or identifier of target element
    target_type: str  # Type of target element
    reference_type: str  # Type of reference (e.g., 'PORT_ACCESS', 'SIGNAL_MAPPING')
    file_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph."""
    
    identifier: str  # Unique identifier for the node
    element_type: str  # Type of element (e.g., 'SWC', 'INTERFACE', 'SIGNAL')
    name: str  # Human-readable name
    file_path: Optional[Path] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    incoming_refs: List[Reference] = field(default_factory=list)
    outgoing_refs: List[Reference] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """Represents the complete dependency graph."""
    
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    edges: List[Reference] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: DependencyNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.identifier] = node
    
    def add_edge(self, reference: Reference) -> None:
        """Add an edge (reference) to the graph."""
        self.edges.append(reference)
        
        # Update node references
        if reference.source_element in self.nodes:
            self.nodes[reference.source_element].outgoing_refs.append(reference)
        if reference.target_element in self.nodes:
            self.nodes[reference.target_element].incoming_refs.append(reference)
    
    def get_node_dependencies(self, node_id: str) -> Tuple[Set[str], Set[str]]:
        """Get dependencies and dependents of a node.
        
        Args:
            node_id: Identifier of the node
            
        Returns:
            Tuple of (dependencies, dependents)
        """
        if node_id not in self.nodes:
            return set(), set()
        
        node = self.nodes[node_id]
        dependencies = {ref.target_element for ref in node.outgoing_refs}
        dependents = {ref.source_element for ref in node.incoming_refs}
        
        return dependencies, dependents
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the graph.
        
        Returns:
            List of circular dependency paths
        """
        circular_deps = []
        visited = set()
        rec_stack = []
        
        def dfs(node_id: str, path: List[str]) -> None:
            """Depth-first search for circular dependencies."""
            if node_id in rec_stack:
                # Found circular dependency
                cycle_start = rec_stack.index(node_id)
                circular_deps.append(rec_stack[cycle_start:] + [node_id])
                return
            
            if node_id in visited:
                return
            
            visited.add(node_id)
            rec_stack.append(node_id)
            
            if node_id in self.nodes:
                for ref in self.nodes[node_id].outgoing_refs:
                    dfs(ref.target_element, path + [node_id])
            
            rec_stack.pop()
        
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])
        
        return circular_deps
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate graph statistics."""
        stats = {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'node_types': defaultdict(int),
            'reference_types': defaultdict(int),
            'max_in_degree': 0,
            'max_out_degree': 0,
            'isolated_nodes': 0,
            'circular_dependencies': len(self.find_circular_dependencies())
        }
        
        for node in self.nodes.values():
            stats['node_types'][node.element_type] += 1
            in_degree = len(node.incoming_refs)
            out_degree = len(node.outgoing_refs)
            
            stats['max_in_degree'] = max(stats['max_in_degree'], in_degree)
            stats['max_out_degree'] = max(stats['max_out_degree'], out_degree)
            
            if in_degree == 0 and out_degree == 0:
                stats['isolated_nodes'] += 1
        
        for ref in self.edges:
            stats['reference_types'][ref.reference_type] += 1
        
        self.statistics = stats
        return stats
    
    def to_graphviz(self) -> str:
        """Generate Graphviz DOT format representation.
        
        Returns:
            DOT format string
        """
        dot_lines = ['digraph DependencyGraph {']
        dot_lines.append('  rankdir=LR;')
        dot_lines.append('  node [shape=box];')
        
        # Add nodes with type-specific styling
        type_colors = {
            'SWC': 'lightblue',
            'INTERFACE': 'lightgreen',
            'SIGNAL': 'lightyellow',
            'PORT': 'lightcoral',
            'RUNNABLE': 'lightgray'
        }
        
        for node_id, node in self.nodes.items():
            color = type_colors.get(node.element_type, 'white')
            label = f"{node.name}\\n[{node.element_type}]"
            dot_lines.append(f'  "{node_id}" [label="{label}", fillcolor={color}, style=filled];')
        
        # Add edges with reference type labels
        for ref in self.edges:
            label = ref.reference_type.replace('_', ' ')
            dot_lines.append(f'  "{ref.source_element}" -> "{ref.target_element}" [label="{label}"];')
        
        dot_lines.append('}')
        return '\n'.join(dot_lines)
    
    def to_json(self) -> str:
        """Generate JSON representation for visualization tools.
        
        Returns:
            JSON string
        """
        graph_data = {
            'nodes': [
                {
                    'id': node_id,
                    'type': node.element_type,
                    'name': node.name,
                    'file': str(node.file_path) if node.file_path else None,
                    'attributes': node.attributes
                }
                for node_id, node in self.nodes.items()
            ],
            'edges': [
                {
                    'source': ref.source_element,
                    'target': ref.target_element,
                    'type': ref.reference_type,
                    'metadata': ref.metadata
                }
                for ref in self.edges
            ],
            'statistics': self.statistics
        }
        return json.dumps(graph_data, indent=2)


class CrossReferenceAnalyzer:
    """Analyzes cross-references and builds dependency graphs."""
    
    def __init__(self) -> None:
        """Initialize the cross-reference analyzer."""
        self.graph: DependencyGraph = DependencyGraph()
        self.reference_patterns: Dict[str, str] = {
            # Common reference patterns in ARXML
            'INTERFACE_REF': '//*[local-name()="PROVIDED-INTERFACE-TREF" or local-name()="REQUIRED-INTERFACE-TREF" or local-name()="PROVIDED-REQUIRED-INTERFACE-TREF"]',
            'PORT_REF': '//*[local-name()="PORT-PROTOTYPE-REF" or local-name()="CONTEXT-P-PORT-REF" or local-name()="CONTEXT-R-PORT-REF"]',
            'TYPE_REF': '//*[local-name()="TYPE-TREF"]',
            'DEFINITION_REF': '//*[local-name()="DEFINITION-REF"]',
            'VALUE_REF': '//*[local-name()="VALUE-REF"]',
            'TARGET_REF': '//*[local-name()="TARGET-DATA-PROTOTYPE-REF" or local-name()="TARGET-PROVIDED-OPERATION-REF" or local-name()="TARGET-REQUIRED-OPERATION-REF"]'
        }
    
    def analyze_document(self, document: ARXMLDocument) -> DependencyGraph:
        """Analyze cross-references in a single document.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            Dependency graph for the document
        """
        # Extract elements and build nodes
        self._extract_elements(document)
        
        # Find and process references
        self._extract_references(document)
        
        # Calculate statistics
        self.graph.calculate_statistics()
        
        return self.graph
    
    def analyze_documents(self, documents: List[ARXMLDocument]) -> DependencyGraph:
        """Analyze cross-references across multiple documents.
        
        Args:
            documents: List of ARXML documents to analyze
            
        Returns:
            Combined dependency graph
        """
        for doc in documents:
            self._extract_elements(doc)
        
        for doc in documents:
            self._extract_references(doc)
        
        self.graph.calculate_statistics()
        
        return self.graph
    
    def _extract_elements(self, document: ARXMLDocument) -> None:
        """Extract elements and create nodes in the dependency graph.
        
        Args:
            document: ARXML document to process
        """
        # Extract software components
        swc_types = [
            'APPLICATION-SW-COMPONENT-TYPE',
            'COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE',
            'SERVICE-SW-COMPONENT-TYPE',
            'SENSOR-ACTUATOR-SW-COMPONENT-TYPE'
        ]
        for swc_type in swc_types:
            swc_elements = document.xpath(f'//*[local-name()="{swc_type}"]')
            for elem in swc_elements:
                self._create_node_from_element(elem, 'SWC', document.file_path)
        
        # Extract interfaces
        interface_types = [
            'SENDER-RECEIVER-INTERFACE',
            'CLIENT-SERVER-INTERFACE',
            'MODE-SWITCH-INTERFACE',
            'PARAMETER-INTERFACE',
            'NV-DATA-INTERFACE'
        ]
        for iface_type in interface_types:
            interface_elements = document.xpath(f'//*[local-name()="{iface_type}"]')
            for elem in interface_elements:
                self._create_node_from_element(elem, 'INTERFACE', document.file_path)
        
        # Extract ports
        port_types = ['P-PORT-PROTOTYPE', 'R-PORT-PROTOTYPE', 'PR-PORT-PROTOTYPE']
        for port_type in port_types:
            port_elements = document.xpath(f'//*[local-name()="{port_type}"]')
            for elem in port_elements:
                self._create_node_from_element(elem, 'PORT', document.file_path)
        
        # Extract signals
        signal_elements = document.xpath('//*[local-name()="I-SIGNAL" or local-name()="SIGNAL"]')
        for elem in signal_elements:
            self._create_node_from_element(elem, 'SIGNAL', document.file_path)
        
        # Extract runnables
        runnable_elements = document.xpath('//*[local-name()="RUNNABLE-ENTITY"]')
        for elem in runnable_elements:
            self._create_node_from_element(elem, 'RUNNABLE', document.file_path)
    
    def _create_node_from_element(self, element: Any, element_type: str, file_path: Optional[Path]) -> None:
        """Create a dependency node from an XML element.
        
        Args:
            element: XML element
            element_type: Type of the element
            file_path: Path to the source file
        """
        # Get element name using XPath
        try:
            # Try to find SHORT-NAME child element
            name_elems = element.xpath('./*[local-name()="SHORT-NAME"]')
            if name_elems and name_elems[0].text:
                name = name_elems[0].text
                identifier = f"{element_type}:{name}"
                
                # Extract additional attributes
                attributes = {}
                
                # Get UUID if available
                uuid_elems = element.xpath('.//*[local-name()="UUID"]')
                if uuid_elems and uuid_elems[0].text:
                    attributes['uuid'] = uuid_elems[0].text
                
                # Get category if available
                category_elems = element.xpath('.//*[local-name()="CATEGORY"]')
                if category_elems and category_elems[0].text:
                    attributes['category'] = category_elems[0].text
                
                # Create node
                node = DependencyNode(
                    identifier=identifier,
                    element_type=element_type,
                    name=name,
                    file_path=file_path,
                    attributes=attributes
                )
                
                self.graph.add_node(node)
        except Exception as e:
            # Skip elements without SHORT-NAME
            pass
    
    def _extract_references(self, document: ARXMLDocument) -> None:
        """Extract references and create edges in the dependency graph.
        
        Args:
            document: ARXML document to process
        """
        for ref_type, pattern in self.reference_patterns.items():
            ref_elements = document.xpath(pattern)
            
            for ref_elem in ref_elements:
                self._process_reference(ref_elem, ref_type, document.file_path)
    
    def _process_reference(self, ref_element: Any, ref_type: str, file_path: Optional[Path]) -> None:
        """Process a reference element and create an edge.
        
        Args:
            ref_element: Reference XML element
            ref_type: Type of reference
            file_path: Path to the source file
        """
        try:
            # Get reference target
            dest_attr = ref_element.get('DEST')
            ref_value = ref_element.text
            
            if ref_value:
                # Find source element (parent with SHORT-NAME)
                source_elem = ref_element
                source_name = None
                source_type = None
                
                while source_elem is not None:
                    name_elems = source_elem.xpath('./*[local-name()="SHORT-NAME"]')
                    if name_elems and name_elems[0].text:
                        source_name = name_elems[0].text
                        source_type = self._get_element_type(source_elem)
                        break
                    source_elem = source_elem.getparent()
                
                if source_name and source_type:
                    # Extract target name from reference value
                    target_name = ref_value.split('/')[-1] if '/' in ref_value else ref_value
                    target_type = dest_attr if dest_attr else 'UNKNOWN'
                    
                    # Create reference
                    reference = Reference(
                        source_element=f"{source_type}:{source_name}",
                        source_type=source_type,
                        target_element=f"{target_type}:{target_name}",
                        target_type=target_type,
                        reference_type=ref_type,
                        file_path=file_path,
                        metadata={'ref_path': ref_value}
                    )
                    
                    self.graph.add_edge(reference)
        except Exception as e:
            # Skip problematic references
            pass
    
    def _get_element_type(self, element: Any) -> str:
        """Determine the type of an XML element.
        
        Args:
            element: XML element
            
        Returns:
            Element type string
        """
        tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        if 'SW-COMPONENT' in tag_name:
            return 'SWC'
        elif 'INTERFACE' in tag_name:
            return 'INTERFACE'
        elif 'PORT' in tag_name:
            return 'PORT'
        elif 'SIGNAL' in tag_name:
            return 'SIGNAL'
        elif 'RUNNABLE' in tag_name:
            return 'RUNNABLE'
        elif 'MODULE' in tag_name:
            return 'MODULE'
        else:
            return tag_name.upper().replace('-', '_')
    
    def find_broken_references(self) -> List[Reference]:
        """Find references that point to non-existent targets.
        
        Returns:
            List of broken references
        """
        broken_refs = []
        
        for ref in self.graph.edges:
            if ref.target_element not in self.graph.nodes:
                broken_refs.append(ref)
        
        return broken_refs
    
    def find_unused_elements(self) -> List[DependencyNode]:
        """Find elements that are not referenced by any other element.
        
        Returns:
            List of unused elements
        """
        unused = []
        
        for node_id, node in self.graph.nodes.items():
            if len(node.incoming_refs) == 0 and node.element_type != 'SWC':
                # SWCs are typically top-level and may not be referenced
                unused.append(node)
        
        return unused
    
    def find_most_referenced(self, top_n: int = 10) -> List[Tuple[DependencyNode, int]]:
        """Find the most referenced elements.
        
        Args:
            top_n: Number of top elements to return
            
        Returns:
            List of (node, reference_count) tuples
        """
        ref_counts = [(node, len(node.incoming_refs)) 
                      for node in self.graph.nodes.values()]
        ref_counts.sort(key=lambda x: x[1], reverse=True)
        
        return ref_counts[:top_n]
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive cross-reference analysis report.
        
        Returns:
            Analysis report dictionary
        """
        broken_refs = self.find_broken_references()
        unused_elements = self.find_unused_elements()
        most_referenced = self.find_most_referenced()
        circular_deps = self.graph.find_circular_dependencies()
        
        report = {
            'summary': {
                'total_elements': len(self.graph.nodes),
                'total_references': len(self.graph.edges),
                'broken_references': len(broken_refs),
                'unused_elements': len(unused_elements),
                'circular_dependencies': len(circular_deps)
            },
            'statistics': self.graph.statistics,
            'broken_references': [
                {
                    'source': ref.source_element,
                    'target': ref.target_element,
                    'type': ref.reference_type
                }
                for ref in broken_refs[:10]  # Limit to first 10
            ],
            'unused_elements': [
                {
                    'element': node.identifier,
                    'type': node.element_type,
                    'name': node.name
                }
                for node in unused_elements[:10]  # Limit to first 10
            ],
            'most_referenced': [
                {
                    'element': node.identifier,
                    'type': node.element_type,
                    'name': node.name,
                    'reference_count': count
                }
                for node, count in most_referenced
            ],
            'circular_dependencies': [
                {'cycle': cycle}
                for cycle in circular_deps[:5]  # Limit to first 5
            ]
        }
        
        return report