"""Composite validator that combines multiple validators."""

from typing import List, Optional, Dict, Any
from pathlib import Path
import time

from arxml_analyzer.core.validator.base_validator import (
    BaseValidator,
    ValidationResult,
    ValidationIssue,
    ValidationLevel,
    ValidationType
)
from arxml_analyzer.core.validator.schema_validator import SchemaValidator
from arxml_analyzer.core.validator.reference_validator import ReferenceValidator
from arxml_analyzer.core.validator.rule_validator import RuleValidator
from arxml_analyzer.models.arxml_document import ARXMLDocument


class CompositeValidator(BaseValidator):
    """Combines multiple validators for comprehensive validation."""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize composite validator.
        
        Args:
            schema_path: Optional path to XSD schema file
        """
        super().__init__()
        self.validators: List[BaseValidator] = []
        
        # Add default validators
        self.add_validator(SchemaValidator(schema_path))
        self.add_validator(ReferenceValidator())
        self.add_validator(RuleValidator())
    
    def add_validator(self, validator: BaseValidator):
        """Add a validator to the composite.
        
        Args:
            validator: Validator to add
        """
        self.validators.append(validator)
    
    def remove_validator(self, validator_type: type):
        """Remove validators of a specific type.
        
        Args:
            validator_type: Type of validator to remove
        """
        self.validators = [v for v in self.validators if not isinstance(v, validator_type)]
    
    def can_validate(self, document: ARXMLDocument) -> bool:
        """Check if any validator can handle this document.
        
        Args:
            document: ARXML document to check
            
        Returns:
            True if at least one validator can handle the document
        """
        return any(validator.can_validate(document) for validator in self.validators)
    
    def validate(self, document: ARXMLDocument) -> ValidationResult:
        """Run all applicable validators on the document.
        
        Args:
            document: ARXML document to validate
            
        Returns:
            Combined ValidationResult from all validators
        """
        start_time = time.time()
        all_issues: List[ValidationIssue] = []
        combined_statistics: Dict[str, Any] = {
            "validators_run": 0,
            "validators_skipped": 0,
            "by_validator": {}
        }
        combined_metadata: Dict[str, Any] = {
            "validator_name": self.name,
            "validator_version": self.version,
            "file_path": document.file_path,
            "validators": []
        }
        
        # Run each validator
        for validator in self.validators:
            validator_name = validator.__class__.__name__
            
            if not validator.can_validate(document):
                combined_statistics["validators_skipped"] += 1
                continue
            
            try:
                # Run validator
                result = validator.validate(document)
                
                # Collect issues
                all_issues.extend(result.issues)
                
                # Collect statistics
                combined_statistics["validators_run"] += 1
                combined_statistics["by_validator"][validator_name] = {
                    "issues": len(result.issues),
                    "errors": result.error_count,
                    "warnings": result.warning_count,
                    "info": result.info_count,
                    "statistics": result.statistics
                }
                
                # Add to metadata
                combined_metadata["validators"].append({
                    "name": validator_name,
                    "version": getattr(validator, 'version', 'unknown'),
                    "duration": result.duration
                })
                
            except Exception as e:
                # Validator failed
                import traceback
                all_issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        type=ValidationType.STRUCTURE,
                        message=f"Validator '{validator_name}' failed: {str(e)}",
                        details={"traceback": traceback.format_exc()}
                    )
                )
                combined_statistics["by_validator"][validator_name] = {
                    "error": str(e)
                }
        
        # Calculate overall statistics
        combined_statistics["total_issues"] = len(all_issues)
        combined_statistics["total_errors"] = sum(1 for i in all_issues if i.level == ValidationLevel.ERROR)
        combined_statistics["total_warnings"] = sum(1 for i in all_issues if i.level == ValidationLevel.WARNING)
        combined_statistics["total_info"] = sum(1 for i in all_issues if i.level == ValidationLevel.INFO)
        
        # Determine overall validity (no errors)
        is_valid = combined_statistics["total_errors"] == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=all_issues,
            statistics=combined_statistics,
            metadata=combined_metadata,
            duration=time.time() - start_time
        )