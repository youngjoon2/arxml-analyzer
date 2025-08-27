"""Base analyzer interface for ARXML analysis."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...models.arxml_document import ARXMLDocument
from ...utils.exceptions import AnalysisError


class AnalysisLevel(Enum):
    """Analysis depth levels."""
    BASIC = "basic"        # Quick overview
    STANDARD = "standard"  # Standard analysis
    DETAILED = "detailed"  # Deep analysis with all details
    CUSTOM = "custom"      # Custom analysis with specific patterns


class AnalysisStatus(Enum):
    """Analysis execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"    # Completed with warnings


@dataclass
class AnalysisMetadata:
    """Metadata for analysis results."""
    analyzer_name: str
    analyzer_version: str = "1.0.0"
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    analysis_duration: float = 0.0  # seconds
    file_path: Optional[Path] = None
    file_size: int = 0  # bytes
    arxml_type: str = "unknown"
    analysis_level: AnalysisLevel = AnalysisLevel.STANDARD
    status: AnalysisStatus = AnalysisStatus.PENDING
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    

@dataclass
class AnalysisResult:
    """Container for analysis results."""
    metadata: AnalysisMetadata
    summary: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    patterns: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def add_pattern(self, pattern_name: str, pattern_data: Dict[str, Any]) -> None:
        """Add a discovered pattern to results."""
        if pattern_name not in self.patterns:
            self.patterns[pattern_name] = []
        self.patterns[pattern_name].append(pattern_data)
    
    def add_statistic(self, stat_name: str, value: Any) -> None:
        """Add a statistical metric."""
        self.statistics[stat_name] = value
    
    def add_recommendation(self, recommendation: str) -> None:
        """Add an analysis recommendation."""
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)
    
    def merge(self, other: 'AnalysisResult') -> None:
        """Merge another analysis result into this one."""
        # Merge summaries
        self.summary.update(other.summary)
        
        # Merge details
        for key, value in other.details.items():
            if key in self.details and isinstance(self.details[key], dict) and isinstance(value, dict):
                self.details[key].update(value)
            else:
                self.details[key] = value
        
        # Merge patterns
        for pattern_name, patterns in other.patterns.items():
            if pattern_name not in self.patterns:
                self.patterns[pattern_name] = []
            self.patterns[pattern_name].extend(patterns)
        
        # Merge statistics
        self.statistics.update(other.statistics)
        
        # Merge recommendations
        for rec in other.recommendations:
            self.add_recommendation(rec)
        
        # Merge errors and warnings
        self.metadata.errors.extend(other.metadata.errors)
        self.metadata.warnings.extend(other.metadata.warnings)


class BaseAnalyzer(ABC):
    """Abstract base class for all ARXML analyzers."""
    
    def __init__(self, name: str = None, version: str = "1.0.0"):
        """Initialize the analyzer.
        
        Args:
            name: Analyzer name (defaults to class name)
            version: Analyzer version
        """
        self.name = name or self.__class__.__name__
        self.version = version
        self._supported_types: Set[str] = set()
        self._analysis_level = AnalysisLevel.STANDARD
    
    @property
    def supported_types(self) -> Set[str]:
        """Get supported ARXML types."""
        return self._supported_types
    
    @supported_types.setter
    def supported_types(self, types: Set[str]) -> None:
        """Set supported ARXML types."""
        self._supported_types = types
    
    @property
    def analysis_level(self) -> AnalysisLevel:
        """Get current analysis level."""
        return self._analysis_level
    
    @analysis_level.setter
    def analysis_level(self, level: AnalysisLevel) -> None:
        """Set analysis level."""
        self._analysis_level = level
    
    def can_analyze(self, document: ARXMLDocument) -> bool:
        """Check if this analyzer can handle the document.
        
        Args:
            document: ARXML document to check
            
        Returns:
            True if analyzer supports this document type
        """
        if not self._supported_types:
            return True  # Generic analyzer supports all types
        
        # Check if document has detected types
        if hasattr(document, 'detected_types') and document.detected_types:
            # Check if any detected type is supported
            for dtype in document.detected_types:
                if dtype.get('type') in self._supported_types:
                    return True
        
        return False
    
    def pre_analyze(self, document: ARXMLDocument) -> None:
        """Pre-analysis hook for setup.
        
        Args:
            document: Document to analyze
        """
        pass
    
    def post_analyze(self, document: ARXMLDocument, result: AnalysisResult) -> None:
        """Post-analysis hook for cleanup.
        
        Args:
            document: Analyzed document
            result: Analysis result
        """
        pass
    
    @abstractmethod
    def analyze(self, document: ARXMLDocument) -> AnalysisResult:
        """Perform analysis on the ARXML document.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            Analysis results
            
        Raises:
            AnalysisError: If analysis fails
        """
        pass
    
    def analyze_safe(self, document: ARXMLDocument) -> AnalysisResult:
        """Safe analysis with error handling.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            Analysis results (may be partial on error)
        """
        import time
        
        # Create metadata
        metadata = AnalysisMetadata(
            analyzer_name=self.name,
            analyzer_version=self.version,
            file_path=Path(document.file_path) if document.file_path else None,
            file_size=document.get_file_size(),
            arxml_type=self._detect_primary_type(document),
            analysis_level=self._analysis_level
        )
        
        # Create result container
        result = AnalysisResult(metadata=metadata)
        
        try:
            # Update status
            metadata.status = AnalysisStatus.IN_PROGRESS
            start_time = time.time()
            
            # Pre-analysis
            self.pre_analyze(document)
            
            # Main analysis
            analysis_result = self.analyze(document)
            
            # Merge results
            if analysis_result:
                result.merge(analysis_result)
            
            # Post-analysis
            self.post_analyze(document, result)
            
            # Update metadata
            metadata.analysis_duration = time.time() - start_time
            metadata.status = AnalysisStatus.COMPLETED if not metadata.warnings else AnalysisStatus.PARTIAL
            
        except AnalysisError as e:
            metadata.status = AnalysisStatus.FAILED
            metadata.errors.append(str(e))
        except Exception as e:
            metadata.status = AnalysisStatus.FAILED
            metadata.errors.append(f"Unexpected error: {str(e)}")
        
        return result
    
    def _detect_primary_type(self, document: ARXMLDocument) -> str:
        """Detect the primary ARXML type.
        
        Args:
            document: ARXML document
            
        Returns:
            Primary type name
        """
        if hasattr(document, 'detected_types') and document.detected_types:
            # Get type with highest confidence
            primary = max(document.detected_types, key=lambda x: x.get('confidence', 0))
            return primary.get('type', 'unknown')
        return 'unknown'
    
    @abstractmethod
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns this analyzer looks for.
        
        Returns:
            List of pattern definitions
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate analyzer configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if configuration is valid
        """
        return True
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}', version='{self.version}')"