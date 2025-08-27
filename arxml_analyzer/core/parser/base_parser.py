"""Base parser abstract class."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ...models.arxml_document import ARXMLDocument


class BaseParser(ABC):
    """Abstract base class for ARXML parsers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize parser.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
    
    @abstractmethod
    def parse(self, file_path: str) -> ARXMLDocument:
        """
        Parse ARXML file and return document object.
        
        Args:
            file_path: Path to ARXML file
            
        Returns:
            ARXMLDocument object
        """
        pass
    
    @abstractmethod
    def validate_syntax(self, file_path: str) -> bool:
        """
        Validate XML syntax.
        
        Args:
            file_path: Path to ARXML file
            
        Returns:
            True if syntax is valid, False otherwise
        """
        pass