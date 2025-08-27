"""Custom exceptions for ARXML Analyzer."""


class ARXMLAnalyzerError(Exception):
    """Base exception for ARXML Analyzer."""
    pass


class ParsingError(ARXMLAnalyzerError):
    """Exception raised when parsing fails."""
    pass


class ValidationError(ARXMLAnalyzerError):
    """Exception raised when validation fails."""
    pass


class AnalysisError(ARXMLAnalyzerError):
    """Exception raised during analysis."""
    pass


class PluginError(ARXMLAnalyzerError):
    """Exception raised in plugin operations."""
    pass


class ConfigurationError(ARXMLAnalyzerError):
    """Exception raised for configuration issues."""
    pass