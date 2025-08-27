"""Pattern finding utilities for ARXML analysis."""

import re
from typing import Dict, List, Any, Optional, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import xml.etree.ElementTree as etree
from collections import defaultdict, Counter


class PatternType(Enum):
    """Types of patterns that can be detected."""
    XPATH = "xpath"              # XPath-based patterns
    REGEX = "regex"              # Regular expression patterns
    STRUCTURAL = "structural"    # Structural patterns in XML
    SEMANTIC = "semantic"        # Semantic patterns (domain-specific)
    STATISTICAL = "statistical"  # Statistical patterns
    SEQUENCE = "sequence"        # Sequential patterns
    REFERENCE = "reference"      # Reference patterns


@dataclass
class PatternDefinition:
    """Definition of a pattern to search for."""
    name: str
    pattern_type: PatternType
    pattern: Union[str, Dict[str, Any], Callable]
    description: str = ""
    severity: str = "info"  # info, warning, error, critical
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternMatch:
    """Represents a pattern match found in the document."""
    pattern_name: str
    pattern_type: PatternType
    location: str  # XPath or line number
    value: Any
    context: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PatternFinder:
    """Finds patterns in ARXML documents."""
    
    def __init__(self):
        """Initialize pattern finder."""
        self.patterns: Dict[str, PatternDefinition] = {}
        self.matches: List[PatternMatch] = []
        self._namespaces: Dict[str, str] = {}
    
    def register_pattern(self, pattern_def: PatternDefinition) -> None:
        """Register a pattern definition.
        
        Args:
            pattern_def: Pattern definition to register
        """
        self.patterns[pattern_def.name] = pattern_def
    
    def register_patterns(self, patterns: List[PatternDefinition]) -> None:
        """Register multiple pattern definitions.
        
        Args:
            patterns: List of pattern definitions
        """
        for pattern in patterns:
            self.register_pattern(pattern)
    
    def find_xpath_patterns(
        self, 
        root: etree.Element, 
        patterns: Optional[List[PatternDefinition]] = None
    ) -> List[PatternMatch]:
        """Find XPath-based patterns.
        
        Args:
            root: Root element to search
            patterns: Specific patterns to search for (uses all if None)
            
        Returns:
            List of pattern matches
        """
        matches = []
        xpath_patterns = patterns or [
            p for p in self.patterns.values() 
            if p.pattern_type == PatternType.XPATH
        ]
        
        for pattern_def in xpath_patterns:
            try:
                elements = root.xpath(
                    pattern_def.pattern, 
                    namespaces=self._namespaces
                )
                
                for elem in elements:
                    # Get element path
                    path = root.getroottree().getpath(elem)
                    
                    # Get element value
                    value = elem.text if hasattr(elem, 'text') else str(elem)
                    
                    # Create match
                    match = PatternMatch(
                        pattern_name=pattern_def.name,
                        pattern_type=PatternType.XPATH,
                        location=path,
                        value=value,
                        context=self._get_element_context(elem),
                        metadata={
                            'severity': pattern_def.severity,
                            'category': pattern_def.category,
                            'tags': pattern_def.tags
                        }
                    )
                    matches.append(match)
                    
            except Exception as e:
                # Log pattern matching error
                print(f"Error matching XPath pattern '{pattern_def.name}': {str(e)}")
        
        return matches
    
    def find_regex_patterns(
        self, 
        content: str, 
        patterns: Optional[List[PatternDefinition]] = None
    ) -> List[PatternMatch]:
        """Find regex-based patterns in text content.
        
        Args:
            content: Text content to search
            patterns: Specific patterns to search for
            
        Returns:
            List of pattern matches
        """
        matches = []
        regex_patterns = patterns or [
            p for p in self.patterns.values() 
            if p.pattern_type == PatternType.REGEX
        ]
        
        lines = content.split('\n')
        
        for pattern_def in regex_patterns:
            try:
                regex = re.compile(pattern_def.pattern, re.MULTILINE)
                
                for line_num, line in enumerate(lines, 1):
                    for match_obj in regex.finditer(line):
                        match = PatternMatch(
                            pattern_name=pattern_def.name,
                            pattern_type=PatternType.REGEX,
                            location=f"line:{line_num}:{match_obj.start()}",
                            value=match_obj.group(),
                            context=line.strip(),
                            metadata={
                                'groups': match_obj.groups(),
                                'severity': pattern_def.severity,
                                'category': pattern_def.category
                            }
                        )
                        matches.append(match)
                        
            except Exception as e:
                print(f"Error matching regex pattern '{pattern_def.name}': {str(e)}")
        
        return matches
    
    def find_structural_patterns(
        self, 
        root: etree.Element
    ) -> List[PatternMatch]:
        """Find structural patterns in XML.
        
        Args:
            root: Root element to analyze
            
        Returns:
            List of structural pattern matches
        """
        matches = []
        
        # Pattern 1: Deep nesting
        max_depth = self._calculate_max_depth(root)
        if max_depth > 10:
            matches.append(PatternMatch(
                pattern_name="deep_nesting",
                pattern_type=PatternType.STRUCTURAL,
                location="/",
                value=max_depth,
                context=f"Maximum nesting depth: {max_depth}",
                metadata={'severity': 'warning' if max_depth > 15 else 'info'}
            ))
        
        # Pattern 2: Large fanout (many children)
        fanout_nodes = self._find_high_fanout_nodes(root, threshold=50)
        for node_path, child_count in fanout_nodes:
            matches.append(PatternMatch(
                pattern_name="high_fanout",
                pattern_type=PatternType.STRUCTURAL,
                location=node_path,
                value=child_count,
                context=f"Node has {child_count} children",
                metadata={'severity': 'warning' if child_count > 100 else 'info'}
            ))
        
        # Pattern 3: Duplicate structures
        duplicates = self._find_duplicate_structures(root)
        for dup_info in duplicates:
            matches.append(PatternMatch(
                pattern_name="duplicate_structure",
                pattern_type=PatternType.STRUCTURAL,
                location=dup_info['location'],
                value=dup_info['count'],
                context=dup_info['structure'],
                confidence=0.8,
                metadata={'severity': 'info', 'paths': dup_info['paths']}
            ))
        
        return matches
    
    def find_reference_patterns(
        self, 
        root: etree.Element
    ) -> List[PatternMatch]:
        """Find reference patterns (broken refs, circular refs, etc).
        
        Args:
            root: Root element to analyze
            
        Returns:
            List of reference pattern matches
        """
        matches = []
        
        # Find all reference attributes
        ref_attrs = ['REF', 'DEST', 'TARGET-REF', 'BASE-REF']
        all_refs = {}
        all_ids = set()
        
        # Collect all IDs
        for elem in root.xpath('//*[@UUID or @ID or @SHORT-NAME]'):
            if elem.get('UUID'):
                all_ids.add(elem.get('UUID'))
            if elem.get('ID'):
                all_ids.add(elem.get('ID'))
            if elem.get('SHORT-NAME'):
                all_ids.add(elem.get('SHORT-NAME'))
        
        # Collect all references
        for attr in ref_attrs:
            refs = root.xpath(f'//*[@{attr}]')
            for ref_elem in refs:
                ref_value = ref_elem.get(attr)
                path = root.getroottree().getpath(ref_elem)
                
                if ref_value not in all_refs:
                    all_refs[ref_value] = []
                all_refs[ref_value].append(path)
        
        # Find broken references
        for ref_value, paths in all_refs.items():
            if ref_value not in all_ids and not ref_value.startswith('/'):
                for path in paths:
                    matches.append(PatternMatch(
                        pattern_name="broken_reference",
                        pattern_type=PatternType.REFERENCE,
                        location=path,
                        value=ref_value,
                        context=f"Reference '{ref_value}' not found",
                        confidence=0.9,
                        metadata={'severity': 'error'}
                    ))
        
        # Find unused IDs
        used_ids = set(all_refs.keys())
        unused_ids = all_ids - used_ids
        for unused_id in unused_ids:
            matches.append(PatternMatch(
                pattern_name="unused_id",
                pattern_type=PatternType.REFERENCE,
                location="global",
                value=unused_id,
                context=f"ID '{unused_id}' is defined but never referenced",
                confidence=0.7,
                metadata={'severity': 'info'}
            ))
        
        return matches
    
    def find_statistical_patterns(
        self, 
        root: etree.Element
    ) -> List[PatternMatch]:
        """Find statistical patterns and anomalies.
        
        Args:
            root: Root element to analyze
            
        Returns:
            List of statistical pattern matches
        """
        matches = []
        
        # Element frequency analysis
        element_counts = Counter()
        for elem in root.iter():
            element_counts[elem.tag] = element_counts.get(elem.tag, 0) + 1
        
        # Find rare elements (potential anomalies)
        total_elements = sum(element_counts.values())
        for tag, count in element_counts.items():
            frequency = count / total_elements
            if frequency < 0.001 and count == 1:  # Very rare, single occurrence
                matches.append(PatternMatch(
                    pattern_name="rare_element",
                    pattern_type=PatternType.STATISTICAL,
                    location=f"element:{tag}",
                    value=count,
                    context=f"Element '{tag}' appears only {count} time(s)",
                    confidence=0.6,
                    metadata={'frequency': frequency, 'severity': 'info'}
                ))
        
        # Attribute distribution analysis
        attr_values = defaultdict(Counter)
        for elem in root.iter():
            for attr, value in elem.items():
                attr_values[attr][value] += 1
        
        # Find attributes with unusual value distributions
        for attr, values in attr_values.items():
            if len(values) == 1:  # Attribute always has same value
                value = list(values.keys())[0]
                count = values[value]
                if count > 10:  # Only if used frequently
                    matches.append(PatternMatch(
                        pattern_name="constant_attribute",
                        pattern_type=PatternType.STATISTICAL,
                        location=f"attribute:{attr}",
                        value=value,
                        context=f"Attribute '{attr}' always has value '{value}'",
                        confidence=0.8,
                        metadata={'count': count, 'severity': 'info'}
                    ))
        
        return matches
    
    def find_all_patterns(
        self, 
        root: etree.Element, 
        content: Optional[str] = None
    ) -> List[PatternMatch]:
        """Find all registered patterns.
        
        Args:
            root: Root element to search
            content: Optional text content for regex patterns
            
        Returns:
            All pattern matches found
        """
        all_matches = []
        
        # XPath patterns
        all_matches.extend(self.find_xpath_patterns(root))
        
        # Regex patterns (if content provided)
        if content:
            all_matches.extend(self.find_regex_patterns(content))
        
        # Structural patterns
        all_matches.extend(self.find_structural_patterns(root))
        
        # Reference patterns
        all_matches.extend(self.find_reference_patterns(root))
        
        # Statistical patterns
        all_matches.extend(self.find_statistical_patterns(root))
        
        self.matches = all_matches
        return all_matches
    
    def group_matches_by_type(
        self, 
        matches: Optional[List[PatternMatch]] = None
    ) -> Dict[PatternType, List[PatternMatch]]:
        """Group matches by pattern type.
        
        Args:
            matches: Matches to group (uses self.matches if None)
            
        Returns:
            Dictionary grouped by pattern type
        """
        matches = matches or self.matches
        grouped = defaultdict(list)
        
        for match in matches:
            grouped[match.pattern_type].append(match)
        
        return dict(grouped)
    
    def group_matches_by_severity(
        self, 
        matches: Optional[List[PatternMatch]] = None
    ) -> Dict[str, List[PatternMatch]]:
        """Group matches by severity.
        
        Args:
            matches: Matches to group
            
        Returns:
            Dictionary grouped by severity
        """
        matches = matches or self.matches
        grouped = defaultdict(list)
        
        for match in matches:
            severity = match.metadata.get('severity', 'info')
            grouped[severity].append(match)
        
        return dict(grouped)
    
    def get_summary(
        self, 
        matches: Optional[List[PatternMatch]] = None
    ) -> Dict[str, Any]:
        """Get summary of pattern matches.
        
        Args:
            matches: Matches to summarize
            
        Returns:
            Summary dictionary
        """
        matches = matches or self.matches
        
        summary = {
            'total_matches': len(matches),
            'by_type': {},
            'by_severity': {},
            'by_pattern': {},
            'unique_patterns': set()
        }
        
        # Count by type
        for match in matches:
            ptype = match.pattern_type.value
            summary['by_type'][ptype] = summary['by_type'].get(ptype, 0) + 1
            
            # Count by severity
            severity = match.metadata.get('severity', 'info')
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            # Count by pattern name
            pname = match.pattern_name
            summary['by_pattern'][pname] = summary['by_pattern'].get(pname, 0) + 1
            summary['unique_patterns'].add(pname)
        
        summary['unique_patterns'] = len(summary['unique_patterns'])
        
        return summary
    
    # Helper methods
    
    def _get_element_context(self, elem: etree.Element, max_length: int = 100) -> str:
        """Get context string for an element."""
        context_parts = []
        
        # Add tag name
        context_parts.append(f"<{elem.tag}")
        
        # Add key attributes
        for attr in ['SHORT-NAME', 'UUID', 'ID', 'TYPE']:
            if elem.get(attr):
                context_parts.append(f'{attr}="{elem.get(attr)}"')
        
        context = ' '.join(context_parts) + '>'
        
        # Add text content if short enough
        if elem.text and len(elem.text.strip()) < 50:
            context += elem.text.strip()
        
        return context[:max_length]
    
    def _calculate_max_depth(self, elem: etree.Element, depth: int = 0) -> int:
        """Calculate maximum depth of XML tree."""
        if len(elem) == 0:
            return depth
        
        max_child_depth = depth
        for child in elem:
            child_depth = self._calculate_max_depth(child, depth + 1)
            max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth
    
    def _find_high_fanout_nodes(
        self, 
        root: etree.Element, 
        threshold: int = 50
    ) -> List[tuple]:
        """Find nodes with many children."""
        high_fanout = []
        
        for elem in root.iter():
            child_count = len(elem)
            if child_count >= threshold:
                path = root.getroottree().getpath(elem)
                high_fanout.append((path, child_count))
        
        return high_fanout
    
    def _find_duplicate_structures(
        self, 
        root: etree.Element, 
        min_occurrences: int = 3
    ) -> List[Dict[str, Any]]:
        """Find duplicate structural patterns."""
        structure_hashes = defaultdict(list)
        
        # Create structural hash for each element
        for elem in root.iter():
            if len(elem) > 0:  # Only elements with children
                struct_hash = self._get_structure_hash(elem)
                path = root.getroottree().getpath(elem)
                structure_hashes[struct_hash].append(path)
        
        # Find duplicates
        duplicates = []
        for struct_hash, paths in structure_hashes.items():
            if len(paths) >= min_occurrences:
                duplicates.append({
                    'structure': struct_hash,
                    'count': len(paths),
                    'paths': paths[:5],  # Limit to first 5 examples
                    'location': paths[0]
                })
        
        return duplicates
    
    def _get_structure_hash(self, elem: etree.Element) -> str:
        """Get a hash representing element structure."""
        structure = []
        structure.append(elem.tag)
        
        # Include child tags
        child_tags = [child.tag for child in elem]
        structure.append(f"children:{','.join(sorted(set(child_tags)))}")
        
        # Include attributes (not values)
        attrs = sorted(elem.keys())
        if attrs:
            structure.append(f"attrs:{','.join(attrs)}")
        
        return '|'.join(structure)