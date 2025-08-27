"""XSD schema validator for ARXML files."""

import lxml.etree as ET
from pathlib import Path
from typing import Optional, List, Dict, Any
import time
from datetime import datetime

from arxml_analyzer.core.validator.base_validator import (
    BaseValidator,
    ValidationResult,
    ValidationIssue,
    ValidationLevel,
    ValidationType
)
from arxml_analyzer.models.arxml_document import ARXMLDocument


class SchemaValidator(BaseValidator):
    """Validates ARXML against XSD schema."""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize schema validator.
        
        Args:
            schema_path: Optional path to XSD schema file
        """
        super().__init__()
        self.schema_path: Optional[Path] = schema_path
        self.schema: Optional[ET.XMLSchema] = None
        
        if schema_path and schema_path.exists():
            self._load_schema(schema_path)
    
    def _load_schema(self, schema_path: Path):
        """Load XSD schema from file.
        
        Args:
            schema_path: Path to XSD schema file
        """
        try:
            schema_doc = ET.parse(str(schema_path))
            self.schema = ET.XMLSchema(schema_doc)
        except Exception as e:
            raise ValueError(f"Failed to load schema: {e}")
    
    def can_validate(self, document: ARXMLDocument) -> bool:
        """Check if validator can handle this document.
        
        Args:
            document: ARXML document to check
            
        Returns:
            True (schema validation applies to all ARXML files)
        """
        return True
    
    def validate(self, document: ARXMLDocument) -> ValidationResult:
        """Validate document against XSD schema.
        
        Args:
            document: ARXML document to validate
            
        Returns:
            ValidationResult with schema validation issues
        """
        start_time = time.time()
        issues: List[ValidationIssue] = []
        statistics: Dict[str, Any] = {
            "total_elements": 0,
            "validated_elements": 0,
            "schema_used": str(self.schema_path) if self.schema_path else "None"
        }
        
        # Count total elements
        statistics["total_elements"] = len(document.root.xpath(".//*"))
        
        # If no schema is loaded, try to find AUTOSAR schema reference
        if not self.schema:
            schema_location = self._find_schema_location(document)
            if schema_location:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.INFO,
                        type=ValidationType.SCHEMA,
                        message=f"Schema reference found: {schema_location}",
                        suggestion="Provide XSD schema file for validation"
                    )
                )
            else:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        type=ValidationType.SCHEMA,
                        message="No schema provided and no schema reference found in document",
                        suggestion="Provide XSD schema file with --schema option"
                    )
                )
        
        # Perform schema validation if schema is available
        if self.schema:
            try:
                self.schema.validate(document.root)
                statistics["validated_elements"] = statistics["total_elements"]
                
                # Get validation errors from schema
                for error in self.schema.error_log:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            type=ValidationType.SCHEMA,
                            message=error.message,
                            line_number=error.line,
                            column_number=error.column,
                            element_path=error.path,
                            details={
                                "domain": error.domain_name,
                                "type": error.type_name
                            }
                        )
                    )
            except ET.DocumentInvalid as e:
                for error in e.error_log:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            type=ValidationType.SCHEMA,
                            message=str(error),
                            line_number=error.line,
                            column_number=error.column
                        )
                    )
        
        # Check basic ARXML structure even without schema
        structure_issues = self._validate_basic_structure(document)
        issues.extend(structure_issues)
        
        # Determine overall validity
        is_valid = all(issue.level != ValidationLevel.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            statistics=statistics,
            metadata={
                "validator_name": self.name,
                "validator_version": self.version,
                "file_path": document.file_path,
                "autosar_version": document.get_autosar_version()
            },
            duration=time.time() - start_time
        )
    
    def _find_schema_location(self, document: ARXMLDocument) -> Optional[str]:
        """Find schema location from document.
        
        Args:
            document: ARXML document
            
        Returns:
            Schema location if found
        """
        # Check for xsi:schemaLocation or xsi:noNamespaceSchemaLocation
        xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
        
        schema_location = document.root.get(f"{{{xsi_ns}}}schemaLocation")
        if schema_location:
            # schemaLocation contains namespace and location pairs
            parts = schema_location.split()
            if len(parts) >= 2:
                return parts[1]  # Return the location part
        
        no_ns_location = document.root.get(f"{{{xsi_ns}}}noNamespaceSchemaLocation")
        if no_ns_location:
            return no_ns_location
        
        return None
    
    def _validate_basic_structure(self, document: ARXMLDocument) -> List[ValidationIssue]:
        """Validate basic ARXML structure.
        
        Args:
            document: ARXML document
            
        Returns:
            List of structure validation issues
        """
        issues: List[ValidationIssue] = []
        
        # Check root element (handle namespace)
        local_name = ET.QName(document.root).localname if document.root.tag.startswith('{') else document.root.tag
        if local_name != "AUTOSAR":
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    type=ValidationType.STRUCTURE,
                    message=f"Root element must be 'AUTOSAR', found '{local_name}'"
                )
            )
        
        # Check for AR-PACKAGES (handle namespaces)
        # Try without namespace first
        packages = document.xpath("//AR-PACKAGE")
        
        # If not found, try with namespace
        if not packages and document.namespaces:
            # Try with default namespace
            for ns in document.namespaces.values():
                packages = document.root.xpath(f"//{{{ns}}}AR-PACKAGE")
                if packages:
                    break
        
        if not packages:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    type=ValidationType.STRUCTURE,
                    message="No AR-PACKAGE elements found in document"
                )
            )
        
        # Check for duplicate SHORT-NAMEs within same parent
        self._check_duplicate_short_names(document, issues)
        
        # Check for empty required elements
        self._check_empty_elements(document, issues)
        
        return issues
    
    def _check_duplicate_short_names(self, document: ARXMLDocument, issues: List[ValidationIssue]):
        """Check for duplicate SHORT-NAME elements.
        
        Args:
            document: ARXML document
            issues: List to append issues to
        """
        try:
            # Find all elements with SHORT-NAME
            # Use simpler XPath to avoid namespace issues
            all_elements = document.root.xpath(".//*")
            
            for element in all_elements:
                short_names = {}
                for child in element:
                    # Look for SHORT-NAME child element
                    for subchild in child:
                        if hasattr(subchild, 'tag'):
                            tag = subchild.tag
                            if isinstance(tag, str):
                                local_name = ET.QName(tag).localname if tag.startswith('{') else tag
                                if local_name == "SHORT-NAME" and subchild.text:
                                    short_name = subchild.text
                                    if short_name in short_names:
                                        parent_tag = element.tag
                                        if parent_tag.startswith('{'):
                                            parent_tag = ET.QName(parent_tag).localname
                                        issues.append(
                                            ValidationIssue(
                                                level=ValidationLevel.ERROR,
                                                type=ValidationType.CONSISTENCY,
                                                message=f"Duplicate SHORT-NAME '{short_name}' in {parent_tag}",
                                                element_path=None
                                            )
                                        )
                                    else:
                                        short_names[short_name] = child
                                    break
        except Exception:
            # Skip this check if there's an error
            pass
    
    def _check_empty_elements(self, document: ARXMLDocument, issues: List[ValidationIssue]):
        """Check for empty required elements.
        
        Args:
            document: ARXML document
            issues: List to append issues to
        """
        # Check for empty SHORT-NAME elements
        try:
            # Use simpler iteration to avoid XPath issues
            all_elements = document.root.xpath(".//*")
            
            for elem in all_elements:
                if hasattr(elem, 'tag'):
                    tag = elem.tag
                    if isinstance(tag, str):
                        local_name = ET.QName(tag).localname if tag.startswith('{') else tag
                        if local_name == "SHORT-NAME":
                            if not elem.text or not elem.text.strip():
                                parent = elem.getparent()
                                parent_tag = parent.tag if parent is not None else 'unknown'
                                # Handle namespace in tag
                                if parent_tag.startswith('{'):
                                    parent_tag = ET.QName(parent_tag).localname
                                issues.append(
                                    ValidationIssue(
                                        level=ValidationLevel.ERROR,
                                        type=ValidationType.STRUCTURE,
                                        message=f"Empty SHORT-NAME in {parent_tag}",
                                        element_path=None
                                    )
                                )
        except Exception:
            # Skip this check if there's an error
            pass