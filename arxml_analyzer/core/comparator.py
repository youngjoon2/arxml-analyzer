"""ARXML file comparator."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
import difflib
import lxml.etree as ET

from arxml_analyzer.models.arxml_document import ARXMLDocument


class DifferenceType(Enum):
    """Type of difference between elements."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"


@dataclass
class ElementDifference:
    """Represents a difference between two elements."""
    type: DifferenceType
    path: str
    element1: Optional[Any] = None
    element2: Optional[Any] = None
    details: Dict[str, Any] = field(default_factory=dict)
    

@dataclass
class ComparisonResult:
    """Result of ARXML comparison."""
    file1_path: str
    file2_path: str
    total_differences: int
    added_elements: List[ElementDifference]
    removed_elements: List[ElementDifference]
    modified_elements: List[ElementDifference]
    moved_elements: List[ElementDifference]
    statistics: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_identical(self) -> bool:
        """Check if files are identical."""
        return self.total_differences == 0


class ARXMLComparator:
    """Compares two ARXML documents."""
    
    def __init__(self, ignore_order: bool = False, ignore_comments: bool = True):
        """Initialize comparator.
        
        Args:
            ignore_order: Whether to ignore element order
            ignore_comments: Whether to ignore comments
        """
        self.ignore_order = ignore_order
        self.ignore_comments = ignore_comments
    
    def compare(self, doc1: ARXMLDocument, doc2: ARXMLDocument) -> ComparisonResult:
        """Compare two ARXML documents.
        
        Args:
            doc1: First document
            doc2: Second document
            
        Returns:
            ComparisonResult with all differences
        """
        added = []
        removed = []
        modified = []
        moved = []
        
        # Build element maps for both documents
        elements1 = self._build_element_map(doc1)
        elements2 = self._build_element_map(doc2)
        
        # Find added and removed elements
        paths1 = set(elements1.keys())
        paths2 = set(elements2.keys())
        
        added_paths = paths2 - paths1
        removed_paths = paths1 - paths2
        common_paths = paths1 & paths2
        
        # Create difference objects for added elements
        for path in added_paths:
            added.append(ElementDifference(
                type=DifferenceType.ADDED,
                path=path,
                element2=elements2[path],
                details=self._get_element_details(elements2[path])
            ))
        
        # Create difference objects for removed elements
        for path in removed_paths:
            removed.append(ElementDifference(
                type=DifferenceType.REMOVED,
                path=path,
                element1=elements1[path],
                details=self._get_element_details(elements1[path])
            ))
        
        # Check for modifications in common elements
        for path in common_paths:
            elem1 = elements1[path]
            elem2 = elements2[path]
            
            differences = self._compare_elements(elem1, elem2)
            if differences:
                modified.append(ElementDifference(
                    type=DifferenceType.MODIFIED,
                    path=path,
                    element1=elem1,
                    element2=elem2,
                    details=differences
                ))
        
        # Detect moved elements (elements with same content but different path)
        moved = self._detect_moved_elements(elements1, elements2, removed_paths, added_paths)
        
        # Calculate statistics
        statistics = {
            "file1_elements": len(elements1),
            "file2_elements": len(elements2),
            "common_elements": len(common_paths),
            "added_count": len(added),
            "removed_count": len(removed),
            "modified_count": len(modified),
            "moved_count": len(moved)
        }
        
        return ComparisonResult(
            file1_path=doc1.file_path,
            file2_path=doc2.file_path,
            total_differences=len(added) + len(removed) + len(modified) + len(moved),
            added_elements=added,
            removed_elements=removed,
            modified_elements=modified,
            moved_elements=moved,
            statistics=statistics
        )
    
    def _build_element_map(self, document: ARXMLDocument) -> Dict[str, Any]:
        """Build a map of element paths to elements.
        
        Args:
            document: ARXML document
            
        Returns:
            Dictionary mapping paths to elements
        """
        element_map = {}
        
        def process_element(elem, path=""):
            """Process element recursively."""
            # Get element's SHORT-NAME if available
            short_name = None
            for child in elem:
                if hasattr(child, 'tag'):
                    tag = child.tag
                    if isinstance(tag, str):
                        local_name = ET.QName(tag).localname if tag.startswith('{') else tag
                        if local_name == "SHORT-NAME":
                            short_name = child.text
                            break
            
            # Build current path
            if short_name:
                current_path = f"{path}/{short_name}" if path else f"/{short_name}"
            else:
                # Use tag name with index for elements without SHORT-NAME
                tag_name = elem.tag
                if tag_name.startswith('{'):
                    tag_name = ET.QName(tag_name).localname
                
                # Count siblings with same tag
                parent = elem.getparent()
                if parent is not None:
                    siblings = [e for e in parent if hasattr(e, 'tag') and e.tag == elem.tag]
                    index = siblings.index(elem)
                    current_path = f"{path}/{tag_name}[{index}]" if path else f"/{tag_name}[{index}]"
                else:
                    current_path = f"/{tag_name}"
            
            element_map[current_path] = elem
            
            # Process children
            for child in elem:
                if hasattr(child, 'tag'):
                    process_element(child, current_path)
        
        process_element(document.root)
        return element_map
    
    def _compare_elements(self, elem1, elem2) -> Dict[str, Any]:
        """Compare two elements for differences.
        
        Args:
            elem1: First element
            elem2: Second element
            
        Returns:
            Dictionary of differences
        """
        differences = {}
        
        # Compare text content
        text1 = elem1.text.strip() if elem1.text else ""
        text2 = elem2.text.strip() if elem2.text else ""
        
        if text1 != text2:
            differences["text"] = {
                "old": text1,
                "new": text2
            }
        
        # Compare attributes
        attrs1 = dict(elem1.attrib) if hasattr(elem1, 'attrib') else {}
        attrs2 = dict(elem2.attrib) if hasattr(elem2, 'attrib') else {}
        
        if attrs1 != attrs2:
            attr_diffs = {}
            all_attrs = set(attrs1.keys()) | set(attrs2.keys())
            
            for attr in all_attrs:
                val1 = attrs1.get(attr)
                val2 = attrs2.get(attr)
                if val1 != val2:
                    attr_diffs[attr] = {
                        "old": val1,
                        "new": val2
                    }
            
            if attr_diffs:
                differences["attributes"] = attr_diffs
        
        # Compare number of children (structure change)
        children1 = [c for c in elem1 if hasattr(c, 'tag')]
        children2 = [c for c in elem2 if hasattr(c, 'tag')]
        
        if len(children1) != len(children2):
            differences["children_count"] = {
                "old": len(children1),
                "new": len(children2)
            }
        
        return differences
    
    def _detect_moved_elements(self, elements1: Dict[str, Any], elements2: Dict[str, Any],
                              removed_paths: Set[str], added_paths: Set[str]) -> List[ElementDifference]:
        """Detect elements that were moved to different locations.
        
        Args:
            elements1: Element map from first document
            elements2: Element map from second document
            removed_paths: Set of removed element paths
            added_paths: Set of added element paths
            
        Returns:
            List of moved element differences
        """
        moved = []
        
        # Build content signatures for removed elements
        removed_signatures = {}
        for path in removed_paths:
            elem = elements1[path]
            signature = self._get_element_signature(elem)
            if signature:
                removed_signatures[signature] = (path, elem)
        
        # Check if any added elements match removed element signatures
        for path in added_paths:
            elem = elements2[path]
            signature = self._get_element_signature(elem)
            
            if signature and signature in removed_signatures:
                old_path, old_elem = removed_signatures[signature]
                moved.append(ElementDifference(
                    type=DifferenceType.MOVED,
                    path=path,
                    element1=old_elem,
                    element2=elem,
                    details={
                        "old_path": old_path,
                        "new_path": path
                    }
                ))
        
        return moved
    
    def _get_element_signature(self, elem) -> Optional[str]:
        """Get a signature for an element based on its content.
        
        Args:
            elem: Element to get signature for
            
        Returns:
            Signature string or None
        """
        # Create signature from element tag, text, and key attributes
        parts = []
        
        # Add tag
        tag = elem.tag
        if tag.startswith('{'):
            tag = ET.QName(tag).localname
        parts.append(tag)
        
        # Add text content if significant
        if elem.text and elem.text.strip():
            parts.append(f"text={elem.text.strip()[:50]}")
        
        # Add key attributes
        if hasattr(elem, 'attrib'):
            for attr in sorted(elem.attrib.keys()):
                if attr in ['DEST', 'UUID', 'ID']:
                    parts.append(f"{attr}={elem.attrib[attr]}")
        
        # Add child structure
        children = [c for c in elem if hasattr(c, 'tag')]
        if children:
            child_tags = []
            for child in children[:5]:  # First 5 children
                child_tag = child.tag
                if child_tag.startswith('{'):
                    child_tag = ET.QName(child_tag).localname
                child_tags.append(child_tag)
            parts.append(f"children={','.join(child_tags)}")
        
        return "|".join(parts) if len(parts) > 1 else None
    
    def _get_element_details(self, elem) -> Dict[str, Any]:
        """Get details about an element.
        
        Args:
            elem: Element to get details for
            
        Returns:
            Dictionary of element details
        """
        details = {}
        
        # Add tag
        tag = elem.tag
        if tag.startswith('{'):
            tag = ET.QName(tag).localname
        details["tag"] = tag
        
        # Add text
        if elem.text and elem.text.strip():
            details["text"] = elem.text.strip()
        
        # Add attributes
        if hasattr(elem, 'attrib') and elem.attrib:
            details["attributes"] = dict(elem.attrib)
        
        # Add child count
        children = [c for c in elem if hasattr(c, 'tag')]
        details["children_count"] = len(children)
        
        return details