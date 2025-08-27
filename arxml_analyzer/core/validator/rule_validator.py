"""Rule-based validator for ARXML files."""

from typing import Dict, List, Any, Callable
import re
import time
from dataclasses import dataclass

from arxml_analyzer.core.validator.base_validator import (
    BaseValidator,
    ValidationResult,
    ValidationIssue,
    ValidationLevel,
    ValidationType
)
from arxml_analyzer.models.arxml_document import ARXMLDocument


@dataclass
class ValidationRule:
    """Single validation rule."""
    id: str
    name: str
    description: str
    level: ValidationLevel
    check_function: Callable[[ARXMLDocument], List[ValidationIssue]]
    category: str = "general"
    enabled: bool = True


class RuleValidator(BaseValidator):
    """Validates ARXML against configurable business rules."""
    
    def __init__(self):
        """Initialize rule validator."""
        super().__init__()
        self.rules: List[ValidationRule] = []
        self._register_default_rules()
    
    def add_rule(self, rule: ValidationRule):
        """Add a validation rule.
        
        Args:
            rule: Validation rule to add
        """
        self.rules.append(rule)
    
    def remove_rule(self, rule_id: str):
        """Remove a validation rule by ID.
        
        Args:
            rule_id: ID of rule to remove
        """
        self.rules = [r for r in self.rules if r.id != rule_id]
    
    def enable_rule(self, rule_id: str, enabled: bool = True):
        """Enable or disable a rule.
        
        Args:
            rule_id: ID of rule to modify
            enabled: Whether to enable the rule
        """
        for rule in self.rules:
            if rule.id == rule_id:
                rule.enabled = enabled
                break
    
    def can_validate(self, document: ARXMLDocument) -> bool:
        """Check if validator can handle this document.
        
        Args:
            document: ARXML document to check
            
        Returns:
            True (rule validation applies to all ARXML files)
        """
        return True
    
    def validate(self, document: ARXMLDocument) -> ValidationResult:
        """Validate document against all enabled rules.
        
        Args:
            document: ARXML document to validate
            
        Returns:
            ValidationResult with rule validation issues
        """
        start_time = time.time()
        issues: List[ValidationIssue] = []
        statistics: Dict[str, Any] = {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules if r.enabled),
            "rules_passed": 0,
            "rules_failed": 0,
            "rules_by_category": {}
        }
        
        # Group rules by category for statistics
        for rule in self.rules:
            if rule.category not in statistics["rules_by_category"]:
                statistics["rules_by_category"][rule.category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }
            statistics["rules_by_category"][rule.category]["total"] += 1
        
        # Run each enabled rule
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                rule_issues = rule.check_function(document)
                
                # Add rule ID to each issue
                for issue in rule_issues:
                    issue.rule_id = rule.id
                    issues.append(issue)
                
                # Update statistics
                if rule_issues:
                    statistics["rules_failed"] += 1
                    statistics["rules_by_category"][rule.category]["failed"] += 1
                else:
                    statistics["rules_passed"] += 1
                    statistics["rules_by_category"][rule.category]["passed"] += 1
                    
            except Exception as e:
                # Rule execution failed
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        type=ValidationType.RULE,
                        message=f"Rule '{rule.name}' failed to execute: {str(e)}",
                        rule_id=rule.id
                    )
                )
                statistics["rules_failed"] += 1
        
        # Determine overall validity
        is_valid = all(issue.level != ValidationLevel.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            statistics=statistics,
            metadata={
                "validator_name": self.name,
                "validator_version": self.version,
                "file_path": document.file_path
            },
            duration=time.time() - start_time
        )
    
    def _register_default_rules(self):
        """Register default validation rules."""
        
        # Naming convention rules
        self.add_rule(ValidationRule(
            id="RULE_001",
            name="SHORT-NAME Format",
            description="SHORT-NAME should follow naming convention",
            level=ValidationLevel.WARNING,
            category="naming",
            check_function=self._check_short_name_format
        ))
        
        self.add_rule(ValidationRule(
            id="RULE_002",
            name="Package Naming",
            description="AR-PACKAGE names should be uppercase",
            level=ValidationLevel.INFO,
            category="naming",
            check_function=self._check_package_naming
        ))
        
        # Structure rules
        self.add_rule(ValidationRule(
            id="RULE_003",
            name="Container Multiplicity",
            description="Check container multiplicity constraints",
            level=ValidationLevel.ERROR,
            category="structure",
            check_function=self._check_container_multiplicity
        ))
        
        self.add_rule(ValidationRule(
            id="RULE_004",
            name="Parameter Ranges",
            description="Numerical parameters should be within defined ranges",
            level=ValidationLevel.ERROR,
            category="values",
            check_function=self._check_parameter_ranges
        ))
        
        # ECUC specific rules
        self.add_rule(ValidationRule(
            id="RULE_005",
            name="ECUC Module Configuration",
            description="ECUC modules should have required containers",
            level=ValidationLevel.ERROR,
            category="ecuc",
            check_function=self._check_ecuc_module_config
        ))
        
        # SWC specific rules
        self.add_rule(ValidationRule(
            id="RULE_006",
            name="Port Interface Consistency",
            description="Ports should reference existing interfaces",
            level=ValidationLevel.ERROR,
            category="swc",
            check_function=self._check_port_interface_consistency
        ))
        
        # Documentation rules
        self.add_rule(ValidationRule(
            id="RULE_007",
            name="Description Presence",
            description="Important elements should have descriptions",
            level=ValidationLevel.INFO,
            category="documentation",
            check_function=self._check_descriptions
        ))
    
    def _check_short_name_format(self, document: ARXMLDocument) -> List[ValidationIssue]:
        """Check SHORT-NAME naming convention.
        
        Args:
            document: ARXML document
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Pattern: Should start with letter, contain only letters, numbers, underscore
        pattern = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')
        
        short_names = document.xpath("//SHORT-NAME")
        for elem in short_names:
            if elem.text and not pattern.match(elem.text):
                parent = elem.getparent()
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        type=ValidationType.RULE,
                        message=f"SHORT-NAME '{elem.text}' does not follow naming convention",
                        element_path=document.root.getpath(parent) if hasattr(document.root, 'getpath') else None,
                        suggestion="Use only letters, numbers, and underscores; start with a letter"
                    )
                )
        
        return issues
    
    def _check_package_naming(self, document: ARXMLDocument) -> List[ValidationIssue]:
        """Check AR-PACKAGE naming convention.
        
        Args:
            document: ARXML document
            
        Returns:
            List of validation issues
        """
        issues = []
        
        packages = document.xpath("//AR-PACKAGE/SHORT-NAME")
        for elem in packages:
            if elem.text and not elem.text.isupper():
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.INFO,
                        type=ValidationType.RULE,
                        message=f"Package name '{elem.text}' should be uppercase",
                        suggestion=f"Consider renaming to '{elem.text.upper()}'"
                    )
                )
        
        return issues
    
    def _check_container_multiplicity(self, document: ARXMLDocument) -> List[ValidationIssue]:
        """Check container multiplicity constraints.
        
        Args:
            document: ARXML document
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for containers with multiplicity constraints
        container_defs = document.xpath("//ECUC-PARAM-CONF-CONTAINER-DEF")
        
        for container_def in container_defs:
            lower_mult = container_def.find(".//LOWER-MULTIPLICITY")
            upper_mult = container_def.find(".//UPPER-MULTIPLICITY-INFINITE")
            
            if lower_mult is not None and lower_mult.text == "1":
                # This container is required
                short_name = container_def.find("SHORT-NAME")
                if short_name is not None and short_name.text:
                    # Check if container instances exist
                    container_path = self._build_element_path(container_def)
                    instances = document.xpath(f"//ECUC-CONTAINER-VALUE[DEFINITION-REF='{container_path}']")
                    
                    if not instances:
                        issues.append(
                            ValidationIssue(
                                level=ValidationLevel.ERROR,
                                type=ValidationType.RULE,
                                message=f"Required container '{short_name.text}' is missing",
                                details={
                                    "container_definition": container_path
                                }
                            )
                        )
        
        return issues
    
    def _check_parameter_ranges(self, document: ARXMLDocument) -> List[ValidationIssue]:
        """Check numerical parameter ranges.
        
        Args:
            document: ARXML document
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check numerical parameter values
        num_params = document.xpath("//ECUC-NUMERICAL-PARAM-VALUE")
        
        for param in num_params:
            value_elem = param.find("VALUE")
            def_ref = param.find("DEFINITION-REF")
            
            if value_elem is not None and value_elem.text and def_ref is not None and def_ref.text:
                try:
                    value = float(value_elem.text)
                    
                    # Try to find the parameter definition
                    param_def_xpath = f"//ECUC-INTEGER-PARAM-DEF[contains('{def_ref.text}', SHORT-NAME)]"
                    param_defs = document.xpath(param_def_xpath)
                    
                    for param_def in param_defs:
                        min_elem = param_def.find(".//MIN")
                        max_elem = param_def.find(".//MAX")
                        
                        if min_elem is not None and min_elem.text:
                            min_val = float(min_elem.text)
                            if value < min_val:
                                issues.append(
                                    ValidationIssue(
                                        level=ValidationLevel.ERROR,
                                        type=ValidationType.RULE,
                                        message=f"Parameter value {value} is below minimum {min_val}",
                                        details={
                                            "parameter": def_ref.text,
                                            "value": value,
                                            "min": min_val
                                        }
                                    )
                                )
                        
                        if max_elem is not None and max_elem.text:
                            max_val = float(max_elem.text)
                            if value > max_val:
                                issues.append(
                                    ValidationIssue(
                                        level=ValidationLevel.ERROR,
                                        type=ValidationType.RULE,
                                        message=f"Parameter value {value} exceeds maximum {max_val}",
                                        details={
                                            "parameter": def_ref.text,
                                            "value": value,
                                            "max": max_val
                                        }
                                    )
                                )
                                
                except ValueError:
                    pass  # Not a numerical value
        
        return issues
    
    def _check_ecuc_module_config(self, document: ARXMLDocument) -> List[ValidationIssue]:
        """Check ECUC module configuration completeness.
        
        Args:
            document: ARXML document
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check ECUC module configurations
        modules = document.xpath("//ECUC-MODULE-CONFIGURATION-VALUES")
        
        for module in modules:
            short_name = module.find("SHORT-NAME")
            containers = module.xpath(".//ECUC-CONTAINER-VALUE")
            
            if short_name is not None and short_name.text:
                if not containers:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.WARNING,
                            type=ValidationType.RULE,
                            message=f"ECUC module '{short_name.text}' has no container configurations",
                            suggestion="Add required container configurations"
                        )
                    )
        
        return issues
    
    def _check_port_interface_consistency(self, document: ARXMLDocument) -> List[ValidationIssue]:
        """Check port-interface consistency.
        
        Args:
            document: ARXML document
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Collect all interfaces
        interfaces = set()
        for iface in document.xpath("//SENDER-RECEIVER-INTERFACE | //CLIENT-SERVER-INTERFACE"):
            short_name = iface.find("SHORT-NAME")
            if short_name is not None and short_name.text:
                interfaces.add(self._build_element_path(iface))
        
        # Check port prototypes
        ports = document.xpath("//P-PORT-PROTOTYPE | //R-PORT-PROTOTYPE | //PR-PORT-PROTOTYPE")
        
        for port in ports:
            interface_ref = port.find(".//PROVIDED-INTERFACE-REF | .//REQUIRED-INTERFACE-REF")
            if interface_ref is not None and interface_ref.text:
                if interface_ref.text not in interfaces:
                    port_name = port.find("SHORT-NAME")
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            type=ValidationType.RULE,
                            message=f"Port '{port_name.text if port_name is not None else 'unknown'}' references non-existent interface",
                            details={
                                "interface_ref": interface_ref.text
                            }
                        )
                    )
        
        return issues
    
    def _check_descriptions(self, document: ARXMLDocument) -> List[ValidationIssue]:
        """Check for missing descriptions.
        
        Args:
            document: ARXML document
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Elements that should have descriptions
        important_elements = [
            "ECUC-MODULE-DEF",
            "APPLICATION-SW-COMPONENT-TYPE",
            "SENDER-RECEIVER-INTERFACE",
            "CLIENT-SERVER-INTERFACE"
        ]
        
        for elem_type in important_elements:
            elements = document.xpath(f"//{elem_type}")
            for elem in elements:
                desc = elem.find(".//DESC | .//L-2")
                short_name = elem.find("SHORT-NAME")
                
                if desc is None or (hasattr(desc, 'text') and not desc.text):
                    if short_name is not None and short_name.text:
                        issues.append(
                            ValidationIssue(
                                level=ValidationLevel.INFO,
                                type=ValidationType.RULE,
                                message=f"{elem_type} '{short_name.text}' lacks description",
                                suggestion="Add meaningful description for better documentation"
                            )
                        )
        
        return issues
    
    def _build_element_path(self, element) -> str:
        """Build full path for an element.
        
        Args:
            element: XML element
            
        Returns:
            Full path string
        """
        path_parts = []
        current = element
        
        while current is not None:
            short_name = current.find("SHORT-NAME")
            if short_name is not None and short_name.text:
                path_parts.insert(0, short_name.text)
            current = current.getparent()
        
        return "/" + "/".join(path_parts) if path_parts else ""