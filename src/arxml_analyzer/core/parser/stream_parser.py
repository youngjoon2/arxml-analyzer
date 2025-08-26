"""Streaming parser for large ARXML files."""

import lxml.etree as ET
from typing import Optional, Dict, Any, Generator
import logging
import os

from .base_parser import BaseParser
from ...models.arxml_document import ARXMLDocument
from ...utils.exceptions import ParsingError

logger = logging.getLogger(__name__)


class StreamParser(BaseParser):
    """Streaming parser for memory-efficient parsing of large files."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize streaming parser.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.chunk_size = config.get('chunk_size', 1024 * 1024) if config else 1024 * 1024
        self.max_depth = config.get('max_depth', 10) if config else 10
    
    def parse(self, file_path: str) -> ARXMLDocument:
        """
        Parse ARXML file using iterative parsing.
        
        Args:
            file_path: Path to ARXML file
            
        Returns:
            ARXMLDocument object
            
        Raises:
            ParsingError: If parsing fails
        """
        try:
            logger.info(f"Stream parsing file: {file_path}")
            
            # Get file size for progress tracking
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size / (1024*1024):.2f} MB")
            
            # Create iterative parser
            context = ET.iterparse(
                file_path,
                events=('start', 'end'),
                huge_tree=True
            )
            context = iter(context)
            
            # Get root element
            event, root = next(context)
            
            # Extract namespaces from root
            namespaces = self._extract_namespaces(root)
            
            # Create document with minimal memory footprint
            document = ARXMLDocument(
                root=root,
                file_path=file_path,
                namespaces=namespaces
            )
            
            # Process elements iteratively
            element_count = 0
            for event, elem in context:
                if event == 'end':
                    element_count += 1
                    
                    # Process element if needed
                    self._process_element(elem)
                    
                    # Clear processed elements to save memory
                    # Keep only structure, clear text and attributes for large elements
                    if elem.tag not in self._get_preserve_tags():
                        elem.clear(keep_tail=True)
                        while elem.getprevious() is not None:
                            del elem.getparent()[0]
                    
                    # Log progress
                    if element_count % 10000 == 0:
                        logger.debug(f"Processed {element_count} elements")
            
            logger.info(f"Stream parsing completed. Processed {element_count} elements")
            return document
            
        except ET.ParseError as e:
            logger.error(f"XML parse error in {file_path}: {e}")
            raise ParsingError(f"Failed to parse {file_path}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error parsing {file_path}: {e}")
            raise ParsingError(f"Unexpected error parsing {file_path}: {e}") from e
    
    def validate_syntax(self, file_path: str) -> bool:
        """
        Validate XML syntax using streaming.
        
        Args:
            file_path: Path to ARXML file
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            # Use iterparse to validate syntax
            for event, elem in ET.iterparse(file_path, events=('start',)):
                elem.clear()
                break  # Just check if parsing starts successfully
            return True
        except ET.ParseError as e:
            logger.warning(f"Syntax validation failed for {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during syntax validation of {file_path}: {e}")
            return False
    
    def stream_elements(self, file_path: str, tag_filter: Optional[str] = None) -> Generator[ET.Element, None, None]:
        """
        Stream elements from file with optional tag filtering.
        
        Args:
            file_path: Path to ARXML file
            tag_filter: Optional tag name to filter elements
            
        Yields:
            XML elements matching the filter
        """
        try:
            context = ET.iterparse(file_path, events=('end',), huge_tree=True)
            
            for event, elem in context:
                if tag_filter is None or elem.tag == tag_filter:
                    yield elem
                    
                # Clear element after yielding
                elem.clear(keep_tail=True)
                while elem.getprevious() is not None:
                    del elem.getparent()[0]
                    
        except ET.ParseError as e:
            logger.error(f"Error streaming elements from {file_path}: {e}")
            raise ParsingError(f"Failed to stream elements from {file_path}: {e}") from e
    
    def _extract_namespaces(self, root: ET.Element) -> Dict[str, str]:
        """
        Extract namespaces from root element.
        
        Args:
            root: Root element
            
        Returns:
            Dictionary of namespace prefixes to URIs
        """
        namespaces = dict(root.nsmap) if root.nsmap else {}
        
        # Remove None key (default namespace) and replace with 'ar'
        if None in namespaces:
            namespaces['ar'] = namespaces.pop(None)
        
        return namespaces
    
    def _process_element(self, element: ET.Element):
        """
        Process individual element during streaming.
        
        Args:
            element: XML element to process
        """
        # This method can be overridden in subclasses for custom processing
        pass
    
    def _get_preserve_tags(self) -> set:
        """
        Get set of tags that should be preserved in memory.
        
        Returns:
            Set of tag names to preserve
        """
        # Preserve important structural elements
        return {
            'AUTOSAR',
            'AR-PACKAGES',
            'AR-PACKAGE',
            'ELEMENTS',
            'SHORT-NAME',
            'LONG-NAME',
            'UUID'
        }