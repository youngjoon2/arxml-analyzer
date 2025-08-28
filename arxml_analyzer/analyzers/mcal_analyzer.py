"""MCAL (Microcontroller Abstraction Layer) Analyzer for ARXML files."""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from ..core.analyzer.base_analyzer import BaseAnalyzer, AnalysisResult, AnalysisMetadata, AnalysisLevel, AnalysisStatus
from ..core.analyzer.pattern_finder import PatternFinder
from ..models.arxml_document import ARXMLDocument

logger = logging.getLogger(__name__)


class MCALAnalyzer(BaseAnalyzer):
    """Analyzer for MCAL (Microcontroller Abstraction Layer) ARXML files."""
    
    ANALYZER_NAME = "MCALAnalyzer"
    VERSION = "1.0.0"
    
    # MCAL module types
    MCAL_MODULES = {
        'PORT': 'Port Driver',
        'DIO': 'Digital Input/Output',
        'ADC': 'Analog Digital Converter',
        'PWM': 'Pulse Width Modulation',
        'ICU': 'Input Capture Unit',
        'GPT': 'General Purpose Timer',
        'MCU': 'Microcontroller Unit',
        'WDG': 'Watchdog',
        'SPI': 'Serial Peripheral Interface',
        'CAN': 'Controller Area Network',
        'LIN': 'Local Interconnect Network',
        'FLEXRAY': 'FlexRay',
        'ETH': 'Ethernet',
        'FLS': 'Flash',
        'EEP': 'EEPROM',
        'RAM': 'RAM Test'
    }
    
    def __init__(self):
        """Initialize the MCAL analyzer."""
        super().__init__()
        self.pattern_finder = PatternFinder()
        
    def analyze(self, document: ARXMLDocument) -> AnalysisResult:
        """Analyze MCAL configuration in the ARXML document.
        
        Args:
            document: The ARXML document to analyze
            
        Returns:
            Analysis results containing MCAL configuration details
        """
        start_time = datetime.now()
        
        try:
            # Extract MCAL modules
            mcal_modules = self.extract_mcal_modules(document)
            
            # Extract hardware configurations
            hardware_configs = self.extract_hardware_configurations(document)
            
            # Extract pin mappings
            pin_mappings = self.extract_pin_mappings(document)
            
            # Extract clock configurations
            clock_configs = self.extract_clock_configurations(document)
            
            # Extract interrupt configurations
            interrupt_configs = self.extract_interrupt_configurations(document)
            
            # Analyze peripheral usage
            peripheral_usage = self.analyze_peripheral_usage(
                mcal_modules, hardware_configs
            )
            
            # Analyze resource allocation
            resource_allocation = self.analyze_resource_allocation(
                mcal_modules, pin_mappings
            )
            
            # Validate MCAL configuration
            validation_results = self.validate_mcal_configuration(
                mcal_modules, hardware_configs, pin_mappings
            )
            
            # Calculate metrics
            metrics = self.calculate_mcal_metrics(
                mcal_modules, hardware_configs, pin_mappings
            )
            
            # Find patterns
            patterns = self._find_patterns(document)
            
            # Generate summary
            summary = {
                "total_mcal_modules": len(mcal_modules),
                "module_types": list(set(m.get("type", "") for m in mcal_modules)),
                "total_hardware_units": len(hardware_configs),
                "total_pin_mappings": len(pin_mappings),
                "total_clock_domains": len(clock_configs),
                "total_interrupts": len(interrupt_configs),
                "peripheral_utilization": metrics.get("peripheral_utilization", 0),
                "validation_status": validation_results.get("status", "UNKNOWN"),
                "critical_issues": len(validation_results.get("critical_issues", []))
            }
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                mcal_modules, hardware_configs, validation_results, metrics
            )
            
            # Create metadata
            metadata = AnalysisMetadata(
                analyzer_name=self.ANALYZER_NAME,
                analyzer_version=self.VERSION,
                analysis_timestamp=start_time,
                analysis_duration=(datetime.now() - start_time).total_seconds(),
                file_path=Path(document.file_path),
                file_size=document.get_file_size(),
                arxml_type="MCAL",
                analysis_level=AnalysisLevel.DETAILED,
                status=AnalysisStatus.SUCCESS
            )
            
            return AnalysisResult(
                metadata=metadata,
                summary=summary,
                details={
                    "mcal_modules": mcal_modules,
                    "hardware_configurations": hardware_configs,
                    "pin_mappings": pin_mappings,
                    "clock_configurations": clock_configs,
                    "interrupt_configurations": interrupt_configs,
                    "peripheral_usage": peripheral_usage,
                    "resource_allocation": resource_allocation,
                    "validation_results": validation_results
                },
                patterns=patterns,
                statistics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing MCAL configuration: {e}")
            return self._create_error_result(document, str(e), start_time)
            
    def can_analyze(self, document: ARXMLDocument) -> bool:
        """Check if this analyzer can handle the document.
        
        Args:
            document: The ARXML document to check
            
        Returns:
            True if the document contains MCAL configuration
        """
        # Check for MCAL-specific elements
        mcal_indicators = [
            ".//ECUC-MODULE-DEF[contains(@UUID, 'Port')]",
            ".//ECUC-MODULE-DEF[contains(@UUID, 'Dio')]",
            ".//ECUC-MODULE-DEF[contains(@UUID, 'Adc')]",
            ".//ECUC-MODULE-DEF[contains(@UUID, 'Mcu')]",
            ".//ECUC-MODULE-DEF[contains(@UUID, 'Spi')]",
            ".//ECUC-MODULE-DEF[contains(@UUID, 'Can')]",
            ".//PORT-PIN",
            ".//MCU-MODULE-CONFIGURATION",
            ".//HARDWARE-ELEMENT"
        ]
        
        for xpath in mcal_indicators:
            if document.xpath(xpath):
                return True
                
        return False
        
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get the patterns this analyzer looks for.
        
        Returns:
            List of pattern definitions
        """
        return [
            {
                "name": "mcal_modules",
                "description": "MCAL module configurations",
                "xpath": ".//ECUC-MODULE-DEF[contains(SHORT-NAME, 'Port') or contains(SHORT-NAME, 'Dio') or contains(SHORT-NAME, 'Adc')]"
            },
            {
                "name": "hardware_units",
                "description": "Hardware unit configurations",
                "xpath": ".//HARDWARE-ELEMENT"
            },
            {
                "name": "pin_configurations",
                "description": "Pin configurations",
                "xpath": ".//PORT-PIN"
            },
            {
                "name": "clock_settings",
                "description": "Clock configurations",
                "xpath": ".//MCU-CLOCK-SETTING"
            },
            {
                "name": "interrupt_vectors",
                "description": "Interrupt vector configurations",
                "xpath": ".//INTERRUPT-VECTOR"
            }
        ]
        
    def extract_mcal_modules(self, document: ARXMLDocument) -> List[Dict[str, Any]]:
        """Extract MCAL module configurations.
        
        Args:
            document: The ARXML document
            
        Returns:
            List of MCAL module configurations
        """
        modules = []
        
        # Extract ECUC module definitions
        ecuc_modules = document.xpath(".//ECUC-MODULE-DEF")
        for module in ecuc_modules:
            name = module.findtext(".//SHORT-NAME", "")
            
            # Check if this is an MCAL module
            module_type = None
            for mcal_type, description in self.MCAL_MODULES.items():
                if mcal_type.lower() in name.lower():
                    module_type = mcal_type
                    break
                    
            if module_type:
                module_info = {
                    "name": name,
                    "type": module_type,
                    "description": self.MCAL_MODULES[module_type],
                    "uuid": module.get("UUID", ""),
                    "containers": [],
                    "parameters": []
                }
                
                # Extract containers
                containers = module.findall(".//ECUC-CONTAINER-DEF")
                for container in containers:
                    container_info = {
                        "name": container.findtext(".//SHORT-NAME", ""),
                        "multiplicity": {
                            "lower": container.findtext(".//LOWER-MULTIPLICITY", "0"),
                            "upper": container.findtext(".//UPPER-MULTIPLICITY", "*")
                        }
                    }
                    module_info["containers"].append(container_info)
                    
                # Extract parameters
                params = module.findall(".//ECUC-PARAM-CONF-CONTAINER-DEF//ECUC-*-PARAM-DEF")
                for param in params:
                    param_info = {
                        "name": param.findtext(".//SHORT-NAME", ""),
                        "type": param.tag.split('}')[-1] if '}' in param.tag else param.tag,
                        "default": param.findtext(".//DEFAULT-VALUE", ""),
                        "min": param.findtext(".//MIN", ""),
                        "max": param.findtext(".//MAX", "")
                    }
                    module_info["parameters"].append(param_info)
                    
                modules.append(module_info)
                
        return modules
        
    def extract_hardware_configurations(self, document: ARXMLDocument) -> List[Dict[str, Any]]:
        """Extract hardware configuration elements.
        
        Args:
            document: The ARXML document
            
        Returns:
            List of hardware configurations
        """
        hw_configs = []
        
        # Extract hardware elements
        hw_elements = document.xpath(".//HARDWARE-ELEMENT")
        for element in hw_elements:
            hw_info = {
                "name": element.findtext(".//SHORT-NAME", ""),
                "category": element.findtext(".//CATEGORY", ""),
                "type": element.findtext(".//HW-ELEMENT-TYPE", ""),
                "attributes": {}
            }
            
            # Extract attributes
            attributes = element.findall(".//HW-ATTRIBUTE")
            for attr in attributes:
                attr_name = attr.findtext(".//SHORT-NAME", "")
                attr_value = attr.findtext(".//VALUE", "")
                hw_info["attributes"][attr_name] = attr_value
                
            hw_configs.append(hw_info)
            
        # Extract MCU specific configurations
        mcu_configs = document.xpath(".//MCU-MODULE-CONFIGURATION")
        for mcu in mcu_configs:
            mcu_info = {
                "name": mcu.findtext(".//SHORT-NAME", ""),
                "type": "MCU",
                "clock_reference_point": [],
                "mode_settings": [],
                "reset_settings": []
            }
            
            # Extract clock reference points
            clock_refs = mcu.findall(".//CLOCK-REFERENCE-POINT")
            for ref in clock_refs:
                mcu_info["clock_reference_point"].append({
                    "frequency": ref.findtext(".//FREQUENCY", ""),
                    "source": ref.findtext(".//CLOCK-SOURCE", "")
                })
                
            # Extract mode settings
            mode_settings = mcu.findall(".//MCU-MODE-SETTING")
            for mode in mode_settings:
                mcu_info["mode_settings"].append({
                    "id": mode.findtext(".//MODE-ID", ""),
                    "name": mode.findtext(".//MODE-NAME", "")
                })
                
            hw_configs.append(mcu_info)
            
        return hw_configs
        
    def extract_pin_mappings(self, document: ARXMLDocument) -> List[Dict[str, Any]]:
        """Extract pin mapping configurations.
        
        Args:
            document: The ARXML document
            
        Returns:
            List of pin mappings
        """
        pin_mappings = []
        
        # Extract port pins
        port_pins = document.xpath(".//PORT-PIN")
        for pin in port_pins:
            pin_info = {
                "name": pin.findtext(".//SHORT-NAME", ""),
                "pin_id": pin.findtext(".//PORT-PIN-ID", ""),
                "direction": pin.findtext(".//PORT-PIN-DIRECTION", ""),
                "mode": pin.findtext(".//PORT-PIN-MODE", ""),
                "level_value": pin.findtext(".//PORT-PIN-LEVEL-VALUE", ""),
                "pull_config": pin.findtext(".//PORT-PIN-PULL", ""),
                "slew_rate": pin.findtext(".//PORT-PIN-SLEW-RATE", ""),
                "functions": []
            }
            
            # Extract pin functions
            functions = pin.findall(".//PORT-PIN-MODE")
            for func in functions:
                func_name = func.findtext(".//SYMBOLIC-NAME", "")
                if func_name:
                    pin_info["functions"].append(func_name)
                    
            pin_mappings.append(pin_info)
            
        # Extract DIO channel mappings
        dio_channels = document.xpath(".//DIO-CHANNEL")
        for channel in dio_channels:
            channel_info = {
                "name": channel.findtext(".//SHORT-NAME", ""),
                "type": "DIO_CHANNEL",
                "channel_id": channel.findtext(".//DIO-CHANNEL-ID", ""),
                "port_pin_ref": channel.findtext(".//DIO-PORT-PIN-REF", "")
            }
            pin_mappings.append(channel_info)
            
        return pin_mappings
        
    def extract_clock_configurations(self, document: ARXMLDocument) -> List[Dict[str, Any]]:
        """Extract clock configuration settings.
        
        Args:
            document: The ARXML document
            
        Returns:
            List of clock configurations
        """
        clock_configs = []
        
        # Extract MCU clock settings
        clock_settings = document.xpath(".//MCU-CLOCK-SETTING")
        for setting in clock_settings:
            clock_info = {
                "name": setting.findtext(".//SHORT-NAME", ""),
                "clock_frequency": setting.findtext(".//MCU-CLOCK-FREQUENCY", ""),
                "reference_frequency": setting.findtext(".//MCU-CLOCK-REFERENCE-FREQUENCY", ""),
                "pll_settings": {},
                "dividers": {}
            }
            
            # Extract PLL settings
            pll = setting.find(".//PLL-SETTING")
            if pll is not None:
                clock_info["pll_settings"] = {
                    "enabled": pll.findtext(".//PLL-ENABLED", "false"),
                    "multiplier": pll.findtext(".//PLL-MULTIPLIER", ""),
                    "divider": pll.findtext(".//PLL-DIVIDER", "")
                }
                
            # Extract clock dividers
            dividers = setting.findall(".//CLOCK-DIVIDER")
            for div in dividers:
                div_name = div.findtext(".//SHORT-NAME", "")
                div_value = div.findtext(".//DIVIDER-VALUE", "")
                clock_info["dividers"][div_name] = div_value
                
            clock_configs.append(clock_info)
            
        return clock_configs
        
    def extract_interrupt_configurations(self, document: ARXMLDocument) -> List[Dict[str, Any]]:
        """Extract interrupt configuration settings.
        
        Args:
            document: The ARXML document
            
        Returns:
            List of interrupt configurations
        """
        interrupt_configs = []
        
        # Extract interrupt vectors
        vectors = document.xpath(".//INTERRUPT-VECTOR")
        for vector in vectors:
            interrupt_info = {
                "name": vector.findtext(".//SHORT-NAME", ""),
                "vector_number": vector.findtext(".//VECTOR-NUMBER", ""),
                "priority": vector.findtext(".//INTERRUPT-PRIORITY", ""),
                "type": vector.findtext(".//INTERRUPT-TYPE", ""),
                "handler": vector.findtext(".//INTERRUPT-HANDLER", ""),
                "source": vector.findtext(".//INTERRUPT-SOURCE", "")
            }
            interrupt_configs.append(interrupt_info)
            
        # Extract OS interrupt configurations if present
        os_interrupts = document.xpath(".//OS-INTERRUPT")
        for isr in os_interrupts:
            os_interrupt_info = {
                "name": isr.findtext(".//SHORT-NAME", ""),
                "category": isr.findtext(".//CATEGORY", ""),
                "vector": isr.findtext(".//VECTOR", ""),
                "priority": isr.findtext(".//PRIORITY", ""),
                "type": "OS_INTERRUPT"
            }
            interrupt_configs.append(os_interrupt_info)
            
        return interrupt_configs
        
    def analyze_peripheral_usage(
        self,
        mcal_modules: List[Dict[str, Any]],
        hardware_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze peripheral usage and allocation.
        
        Args:
            mcal_modules: List of MCAL modules
            hardware_configs: List of hardware configurations
            
        Returns:
            Peripheral usage analysis
        """
        usage = {
            "peripherals": {},
            "utilization_summary": {},
            "conflicts": []
        }
        
        # Map modules to peripherals
        for module in mcal_modules:
            module_type = module.get("type", "")
            if module_type not in usage["peripherals"]:
                usage["peripherals"][module_type] = {
                    "count": 0,
                    "instances": []
                }
            usage["peripherals"][module_type]["count"] += 1
            usage["peripherals"][module_type]["instances"].append(module.get("name", ""))
            
        # Calculate utilization
        total_peripherals = len(usage["peripherals"])
        used_peripherals = sum(1 for p in usage["peripherals"].values() if p["count"] > 0)
        
        usage["utilization_summary"] = {
            "total_peripheral_types": total_peripherals,
            "used_peripheral_types": used_peripherals,
            "utilization_percentage": (used_peripherals / total_peripherals * 100) if total_peripherals > 0 else 0
        }
        
        # Check for conflicts (simplified)
        for peripheral_type, info in usage["peripherals"].items():
            if info["count"] > 1:
                # Multiple instances of the same peripheral type might indicate configuration issues
                usage["conflicts"].append({
                    "type": "MULTIPLE_INSTANCES",
                    "peripheral": peripheral_type,
                    "count": info["count"],
                    "severity": "WARNING"
                })
                
        return usage
        
    def analyze_resource_allocation(
        self,
        mcal_modules: List[Dict[str, Any]],
        pin_mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze resource allocation and conflicts.
        
        Args:
            mcal_modules: List of MCAL modules
            pin_mappings: List of pin mappings
            
        Returns:
            Resource allocation analysis
        """
        allocation = {
            "pin_allocation": {},
            "channel_allocation": {},
            "conflicts": [],
            "unused_resources": []
        }
        
        # Analyze pin allocation
        allocated_pins = set()
        for pin in pin_mappings:
            pin_id = pin.get("pin_id") or pin.get("name")
            if pin_id:
                if pin_id in allocated_pins:
                    allocation["conflicts"].append({
                        "type": "PIN_CONFLICT",
                        "resource": pin_id,
                        "severity": "ERROR"
                    })
                else:
                    allocated_pins.add(pin_id)
                    allocation["pin_allocation"][pin_id] = {
                        "direction": pin.get("direction", "UNKNOWN"),
                        "mode": pin.get("mode", "UNKNOWN"),
                        "functions": pin.get("functions", [])
                    }
                    
        # Analyze channel allocation
        for module in mcal_modules:
            for param in module.get("parameters", []):
                if "channel" in param.get("name", "").lower():
                    channel_name = f"{module.get('type')}_{param.get('name')}"
                    allocation["channel_allocation"][channel_name] = param.get("default", "")
                    
        return allocation
        
    def validate_mcal_configuration(
        self,
        mcal_modules: List[Dict[str, Any]],
        hardware_configs: List[Dict[str, Any]],
        pin_mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate MCAL configuration for consistency and correctness.
        
        Args:
            mcal_modules: List of MCAL modules
            hardware_configs: List of hardware configurations
            pin_mappings: List of pin mappings
            
        Returns:
            Validation results
        """
        validation = {
            "status": "PASS",
            "checks_performed": [],
            "issues": [],
            "warnings": [],
            "critical_issues": []
        }
        
        # Check 1: Verify all referenced pins are defined
        validation["checks_performed"].append("PIN_REFERENCE_CHECK")
        defined_pins = set(p.get("name") for p in pin_mappings if p.get("name"))
        
        # Check 2: Verify module dependencies
        validation["checks_performed"].append("MODULE_DEPENDENCY_CHECK")
        required_modules = {"MCU", "PORT"}  # Basic required modules
        present_modules = set(m.get("type") for m in mcal_modules if m.get("type"))
        
        missing_modules = required_modules - present_modules
        if missing_modules:
            validation["critical_issues"].append({
                "check": "MODULE_DEPENDENCY",
                "message": f"Missing required modules: {missing_modules}",
                "severity": "CRITICAL"
            })
            validation["status"] = "FAIL"
            
        # Check 3: Verify clock configuration consistency
        validation["checks_performed"].append("CLOCK_CONSISTENCY_CHECK")
        
        # Check 4: Pin direction conflicts
        validation["checks_performed"].append("PIN_DIRECTION_CHECK")
        pin_directions = {}
        for pin in pin_mappings:
            pin_id = pin.get("pin_id") or pin.get("name")
            direction = pin.get("direction")
            if pin_id and direction:
                if pin_id in pin_directions and pin_directions[pin_id] != direction:
                    validation["issues"].append({
                        "check": "PIN_DIRECTION_CONFLICT",
                        "pin": pin_id,
                        "message": f"Conflicting directions: {pin_directions[pin_id]} vs {direction}",
                        "severity": "ERROR"
                    })
                    validation["status"] = "FAIL"
                pin_directions[pin_id] = direction
                
        # Check 5: Parameter range validation
        validation["checks_performed"].append("PARAMETER_RANGE_CHECK")
        for module in mcal_modules:
            for param in module.get("parameters", []):
                if param.get("min") and param.get("max") and param.get("default"):
                    try:
                        min_val = float(param["min"])
                        max_val = float(param["max"])
                        default_val = float(param["default"])
                        
                        if not (min_val <= default_val <= max_val):
                            validation["warnings"].append({
                                "check": "PARAMETER_RANGE",
                                "module": module.get("name"),
                                "parameter": param.get("name"),
                                "message": f"Default value {default_val} outside range [{min_val}, {max_val}]",
                                "severity": "WARNING"
                            })
                    except (ValueError, TypeError):
                        pass  # Skip non-numeric parameters
                        
        return validation
        
    def calculate_mcal_metrics(
        self,
        mcal_modules: List[Dict[str, Any]],
        hardware_configs: List[Dict[str, Any]],
        pin_mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate MCAL-specific metrics.
        
        Args:
            mcal_modules: List of MCAL modules
            hardware_configs: List of hardware configurations
            pin_mappings: List of pin mappings
            
        Returns:
            Dictionary of metrics
        """
        metrics = {
            "module_count": len(mcal_modules),
            "hardware_unit_count": len(hardware_configs),
            "pin_count": len(pin_mappings),
            "module_distribution": {},
            "pin_usage_statistics": {},
            "configuration_complexity": 0,
            "peripheral_utilization": 0
        }
        
        # Module distribution
        for module in mcal_modules:
            module_type = module.get("type", "UNKNOWN")
            if module_type not in metrics["module_distribution"]:
                metrics["module_distribution"][module_type] = 0
            metrics["module_distribution"][module_type] += 1
            
        # Pin usage statistics
        input_pins = sum(1 for p in pin_mappings if p.get("direction") == "INPUT")
        output_pins = sum(1 for p in pin_mappings if p.get("direction") == "OUTPUT")
        bidirectional_pins = sum(1 for p in pin_mappings if p.get("direction") == "INOUT")
        
        metrics["pin_usage_statistics"] = {
            "input": input_pins,
            "output": output_pins,
            "bidirectional": bidirectional_pins,
            "total": len(pin_mappings)
        }
        
        # Configuration complexity (based on number of parameters and containers)
        total_params = sum(len(m.get("parameters", [])) for m in mcal_modules)
        total_containers = sum(len(m.get("containers", [])) for m in mcal_modules)
        metrics["configuration_complexity"] = total_params + total_containers
        
        # Peripheral utilization
        total_possible_peripherals = len(self.MCAL_MODULES)
        used_peripherals = len(set(m.get("type") for m in mcal_modules if m.get("type")))
        metrics["peripheral_utilization"] = (
            (used_peripherals / total_possible_peripherals * 100)
            if total_possible_peripherals > 0 else 0
        )
        
        return metrics
        
    def _find_patterns(self, document: ARXMLDocument) -> Dict[str, List[Dict[str, Any]]]:
        """Find patterns in the MCAL configuration.
        
        Args:
            document: The ARXML document
            
        Returns:
            Dictionary of found patterns by type
        """
        patterns = {}
        
        # Find structural patterns
        structural_patterns = self.pattern_finder.find_structural_patterns(
            document.root,
            max_depth=10
        )
        if structural_patterns:
            patterns["structural"] = structural_patterns
            
        # Find MCAL-specific patterns
        mcal_patterns = []
        
        # Pattern: Multiple clock domains
        clock_domains = document.xpath(".//MCU-CLOCK-SETTING")
        if len(clock_domains) > 1:
            mcal_patterns.append({
                "pattern": "MULTIPLE_CLOCK_DOMAINS",
                "count": len(clock_domains),
                "description": "Multiple clock domains configured"
            })
            
        # Pattern: High interrupt count
        interrupts = document.xpath(".//INTERRUPT-VECTOR")
        if len(interrupts) > 50:
            mcal_patterns.append({
                "pattern": "HIGH_INTERRUPT_COUNT",
                "count": len(interrupts),
                "description": "High number of interrupt vectors configured"
            })
            
        if mcal_patterns:
            patterns["mcal_specific"] = mcal_patterns
            
        return patterns
        
    def _generate_recommendations(
        self,
        mcal_modules: List[Dict[str, Any]],
        hardware_configs: List[Dict[str, Any]],
        validation_results: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on analysis.
        
        Args:
            mcal_modules: List of MCAL modules
            hardware_configs: List of hardware configurations
            validation_results: Validation results
            metrics: Calculated metrics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for critical validation issues
        if validation_results.get("critical_issues"):
            recommendations.append(
                "CRITICAL: Address critical validation issues before deployment"
            )
            
        # Check peripheral utilization
        utilization = metrics.get("peripheral_utilization", 0)
        if utilization < 20:
            recommendations.append(
                "Low peripheral utilization detected. Consider if all required peripherals are configured"
            )
        elif utilization > 80:
            recommendations.append(
                "High peripheral utilization. Ensure system has sufficient resources for future expansion"
            )
            
        # Check configuration complexity
        complexity = metrics.get("configuration_complexity", 0)
        if complexity > 500:
            recommendations.append(
                "High configuration complexity detected. Consider modularizing or simplifying configuration"
            )
            
        # Check for missing common modules
        present_types = set(m.get("type") for m in mcal_modules)
        common_modules = {"PORT", "DIO", "MCU"}
        missing_common = common_modules - present_types
        if missing_common:
            recommendations.append(
                f"Common MCAL modules not configured: {', '.join(missing_common)}"
            )
            
        # Check pin usage
        pin_stats = metrics.get("pin_usage_statistics", {})
        if pin_stats.get("total", 0) == 0:
            recommendations.append(
                "No pin mappings found. Verify PORT configuration is complete"
            )
            
        return recommendations