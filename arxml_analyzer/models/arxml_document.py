"""ARXML Document model."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from lxml import etree
import os


@dataclass
class ARXMLDocument:
    """ARXML document model."""
    
    root: Union[etree._Element, etree._ElementTree]
    file_path: str
    namespaces: Dict[str, str] = field(default_factory=dict)
    _cached_xpath_results: Dict[str, Any] = field(default_factory=dict, init=False)
    
    def __post_init__(self):
        """Initialize cached results."""
        self._cached_xpath_results = {}
    
    def xpath(self, expression: str, use_cache: bool = True) -> List:
        """
        Execute XPath expression with caching support.
        
        Args:
            expression: XPath expression to execute
            use_cache: Whether to use caching
            
        Returns:
            List of matching elements
        """
        if use_cache and expression in self._cached_xpath_results:
            return self._cached_xpath_results[expression]
        
        result = self.root.xpath(expression, namespaces=self.namespaces)
        
        if use_cache:
            self._cached_xpath_results[expression] = result
        
        return result
    
    def get_file_size(self) -> int:
        """Get file size in bytes."""
        return os.path.getsize(self.file_path)
    
    def get_element_count(self) -> int:
        """Get total element count in document."""
        return len(self.xpath('.//*'))
    
    def get_autosar_version(self) -> Optional[str]:
        """Get AUTOSAR version from document."""
        # Check for AUTOSAR schema version attribute
        schema_location = self.root.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation')
        if schema_location:
            # Extract version from schema location
            parts = schema_location.split()
            for part in parts:
                if 'AUTOSAR' in part and '.xsd' in part:
                    # Try to extract version pattern (e.g., 4-2-2, 4.2.2)
                    import re
                    version_match = re.search(r'(\d+[-.]?\d+[-.]?\d+)', part)
                    if version_match:
                        return version_match.group(1).replace('-', '.')
        
        # Check for explicit version element
        version_elements = self.xpath('//AR:AUTOSAR/@xsi:schemaLocation', use_cache=False)
        if version_elements:
            return str(version_elements[0])
        
        return None
    
    def clear_cache(self):
        """Clear XPath cache."""
        self._cached_xpath_results.clear()