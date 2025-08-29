"""Custom exceptions for ARXML Analyzer."""

from typing import Optional, Dict, Any


class ARXMLAnalyzerError(Exception):
    """Base exception for ARXML Analyzer.
    
    Attributes:
        message: Error message
        details: Additional error details
        error_code: Optional error code for programmatic handling
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 error_code: Optional[str] = None) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
            details: Additional error details
            error_code: Optional error code
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = error_code
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ParsingError(ARXMLAnalyzerError):
    """Exception raised when parsing fails.
    
    Typically occurs when:
    - XML is malformed
    - File is not accessible
    - Encoding issues
    """
    pass


class ValidationError(ARXMLAnalyzerError):
    """Exception raised when validation fails.
    
    Typically occurs when:
    - Schema validation fails
    - Required elements are missing
    - Invalid attribute values
    """
    pass


class AnalysisError(ARXMLAnalyzerError):
    """Exception raised during analysis.
    
    Typically occurs when:
    - Analyzer cannot process the document
    - Required patterns not found
    - Analysis logic fails
    """
    pass


class CrossReferenceError(AnalysisError):
    """Exception raised during cross-reference analysis.
    
    Typically occurs when:
    - Broken references are detected
    - Circular dependencies found
    - Reference resolution fails
    """
    pass


class TypeDetectionError(ARXMLAnalyzerError):
    """Exception raised when type detection fails.
    
    Typically occurs when:
    - Document type cannot be determined
    - Confidence is below threshold
    - Multiple conflicting types detected
    """
    pass


class PluginError(ARXMLAnalyzerError):
    """Exception raised in plugin operations.
    
    Typically occurs when:
    - Plugin loading fails
    - Plugin execution errors
    - Plugin compatibility issues
    """
    pass


class ConfigurationError(ARXMLAnalyzerError):
    """Exception raised for configuration issues.
    
    Typically occurs when:
    - Invalid configuration values
    - Missing required configuration
    - Configuration file parsing errors
    """
    pass


class FileOperationError(ARXMLAnalyzerError):
    """Exception raised for file operation issues.
    
    Typically occurs when:
    - File not found
    - Permission denied
    - I/O errors
    """
    pass