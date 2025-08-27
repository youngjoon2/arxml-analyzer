"""Base validator for ARXML validation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum

from arxml_analyzer.models.arxml_document import ARXMLDocument


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationType(Enum):
    """Types of validation."""
    SCHEMA = "schema"          # XSD schema validation
    STRUCTURE = "structure"    # Document structure validation
    REFERENCE = "reference"    # Reference integrity validation
    RULE = "rule"             # Business rule validation
    CONSISTENCY = "consistency" # Data consistency validation


@dataclass
class ValidationIssue:
    """Single validation issue."""
    level: ValidationLevel
    type: ValidationType
    message: str
    element_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Complete validation result."""
    is_valid: bool
    issues: List[ValidationIssue]
    statistics: Dict[str, Any]
    metadata: Dict[str, Any]
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.ERROR)
    
    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.WARNING)
    
    @property
    def info_count(self) -> int:
        """Count of info-level issues."""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.INFO)


class BaseValidator(ABC):
    """Abstract base class for ARXML validators."""
    
    def __init__(self):
        """Initialize validator."""
        self.name: str = self.__class__.__name__
        self.version: str = "1.0.0"
    
    @abstractmethod
    def validate(self, document: ARXMLDocument) -> ValidationResult:
        """Validate ARXML document.
        
        Args:
            document: ARXML document to validate
            
        Returns:
            ValidationResult containing all issues found
        """
        pass
    
    @abstractmethod
    def can_validate(self, document: ARXMLDocument) -> bool:
        """Check if this validator can handle the document.
        
        Args:
            document: ARXML document to check
            
        Returns:
            True if validator can handle this document type
        """
        pass
    
    def validate_safe(self, document: ARXMLDocument) -> ValidationResult:
        """Safe validation with error handling.
        
        Args:
            document: ARXML document to validate
            
        Returns:
            ValidationResult with errors captured as issues
        """
        import time
        start_time = time.time()
        
        try:
            if not self.can_validate(document):
                return ValidationResult(
                    is_valid=False,
                    issues=[
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            type=ValidationType.STRUCTURE,
                            message=f"Document type not supported by {self.name}"
                        )
                    ],
                    statistics={},
                    metadata={
                        "validator_name": self.name,
                        "validator_version": self.version
                    },
                    duration=time.time() - start_time
                )
            
            result = self.validate(document)
            result.duration = time.time() - start_time
            return result
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                issues=[
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        type=ValidationType.STRUCTURE,
                        message=f"Validation failed: {str(e)}"
                    )
                ],
                statistics={},
                metadata={
                    "validator_name": self.name,
                    "validator_version": self.version,
                    "error": str(e)
                },
                duration=time.time() - start_time
            )