"""Standard XML parser implementation."""

import lxml.etree as ET
from typing import Optional, Dict, Any
import logging

from .base_parser import BaseParser
from ...models.arxml_document import ARXMLDocument
from ...utils.exceptions import ParsingError

logger = logging.getLogger(__name__)


class XMLParser(BaseParser):
    """Standard XML parser using lxml."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize XML parser.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.encoding = config.get('encoding', 'utf-8') if config else 'utf-8'
        self.remove_blank_text = config.get('remove_blank_text', True) if config else True
    
    def parse(self, file_path: str) -> ARXMLDocument:
        """
        Parse ARXML file using lxml.
        
        Args:
            file_path: Path to ARXML file
            
        Returns:
            ARXMLDocument object
            
        Raises:
            ParsingError: If parsing fails
        """
        try:
            logger.info(f"Parsing file: {file_path}")
            
            # Create parser with options
            parser = ET.XMLParser(
                encoding=self.encoding,
                remove_blank_text=self.remove_blank_text,
                resolve_entities=False,
                huge_tree=True  # Enable parsing of large files
            )
            
            # Parse the file
            tree = ET.parse(file_path, parser)
            root = tree.getroot()
            
            # Extract namespaces
            namespaces = self._extract_namespaces(root)
            
            # Create document object
            document = ARXMLDocument(
                root=root,
                file_path=file_path,
                namespaces=namespaces
            )
            
            logger.info(f"Successfully parsed {file_path}")
            logger.debug(f"Found {document.get_element_count()} elements")
            
            return document
            
        except ET.ParseError as e:
            logger.error(f"XML parse error in {file_path}: {e}")
            raise ParsingError(f"Failed to parse {file_path}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error parsing {file_path}: {e}")
            raise ParsingError(f"Unexpected error parsing {file_path}: {e}") from e
    
    def validate_syntax(self, file_path: str) -> bool:
        """
        Validate XML syntax.
        
        Args:
            file_path: Path to ARXML file
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            parser = ET.XMLParser(encoding=self.encoding)
            ET.parse(file_path, parser)
            logger.debug(f"Syntax validation passed for {file_path}")
            return True
        except ET.ParseError as e:
            logger.warning(f"Syntax validation failed for {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during syntax validation of {file_path}: {e}")
            return False
    
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
        
        logger.debug(f"Extracted namespaces: {list(namespaces.keys())}")
        return namespaces