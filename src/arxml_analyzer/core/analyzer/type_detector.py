"""ARXML type automatic detection module."""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ...models.arxml_document import ARXMLDocument

logger = logging.getLogger(__name__)


@dataclass
class DetectedType:
    """Detected ARXML type information."""
    name: str
    confidence: float  # 0.0 to 1.0
    matched_patterns: List[str]
    element_count: int


class TypeDetector:
    """ARXML type automatic detector."""
    
    # Type detection patterns with XPath expressions
    TYPE_PATTERNS = {
        'SYSTEM': {
            'patterns': [
                './/AR-PACKAGES//ELEMENTS//SYSTEM',
                './/SYSTEM-MAPPING',
                './/FIBEX-ELEMENTS',
                './/SYSTEM-VERSION'
            ],
            'priority': 1
        },
        'ECU_EXTRACT': {
            'patterns': [
                './/ECU-INSTANCE',
                './/ECU-EXTRACT',
                './/CONNECTORS//CAN-COMMUNICATION-CONNECTOR',
                './/CONNECTORS//ETHERNET-COMMUNICATION-CONNECTOR',
                './/ECU-CONFIGURATION-VALUES'
            ],
            'priority': 2
        },
        'SWC': {
            'patterns': [
                './/APPLICATION-SW-COMPONENT-TYPE',
                './/COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE',
                './/SERVICE-SW-COMPONENT-TYPE',
                './/SWC-INTERNAL-BEHAVIOR',
                './/SW-COMPONENT-PROTOTYPE',
                './/SWC-IMPLEMENTATION'
            ],
            'priority': 3
        },
        'INTERFACE': {
            'patterns': [
                './/SENDER-RECEIVER-INTERFACE',
                './/CLIENT-SERVER-INTERFACE',
                './/MODE-SWITCH-INTERFACE',
                './/NV-DATA-INTERFACE',
                './/PARAMETER-INTERFACE',
                './/TRIGGER-INTERFACE'
            ],
            'priority': 4
        },
        'ECUC': {
            'patterns': [
                './/ECUC-MODULE-CONFIGURATION-VALUES',
                './/ECUC-CONTAINER-VALUE',
                './/ECUC-VALUE-COLLECTION',
                './/ECUC-PARAMETER-VALUES',
                './/ECUC-MODULE-DEF'
            ],
            'priority': 5
        },
        'MCAL': {
            'patterns': [
                './/MCAL-MODULE-CONFIGURATION',
                './/DIO-CONFIG',
                './/PORT-CONFIG',
                './/ADC-CONFIG',
                './/PWM-CONFIG',
                './/CAN-CONFIG',
                './/LIN-CONFIG',
                './/MCU-CONFIG',
                './/GPT-CONFIG',
                './/WDG-CONFIG'
            ],
            'priority': 6
        },
        'DIAGNOSTIC': {
            'patterns': [
                './/DCM-MODULE-CONFIGURATION',
                './/DEM-EVENT-PARAMETER',
                './/DIAGNOSTIC-EXTRACT',
                './/DIAGNOSTIC-SERVICE-TABLE',
                './/DIAGNOSTIC-TROUBLE-CODE',
                './/DIAGNOSTIC-DATA-IDENTIFIER'
            ],
            'priority': 7
        },
        'GATEWAY': {
            'patterns': [
                './/GATEWAY-MAPPING',
                './/I-PDU-MAPPING',
                './/SIGNAL-MAPPING',
                './/PDU-R-ROUTING-PATH',
                './/PDU-R-ROUTING-TABLE',
                './/GATEWAY-MODULE-CONFIGURATION'
            ],
            'priority': 8
        },
        'COMMUNICATION': {
            'patterns': [
                './/I-SIGNAL',
                './/I-SIGNAL-GROUP',
                './/I-PDU',
                './/N-PDU',
                './/DCM-I-PDU',
                './/CAN-FRAME',
                './/FLEXRAY-FRAME',
                './/ETHERNET-FRAME',
                './/LIN-FRAME'
            ],
            'priority': 9
        },
        'BSW': {
            'patterns': [
                './/BSW-MODULE-DESCRIPTION',
                './/BSW-MODULE-ENTRY',
                './/BSW-MODULE-DEPENDENCY',
                './/SERVICE-MAPPING',
                './/BSW-IMPLEMENTATION'
            ],
            'priority': 10
        },
        'CALIBRATION': {
            'patterns': [
                './/CALIBRATION-PARAMETER-VALUE',
                './/CALIBRATION-DATA',
                './/SW-AXIS-TYPE',
                './/SW-VALUE-CONT'
            ],
            'priority': 11
        },
        'TIMING': {
            'patterns': [
                './/TIMING-EVENT',
                './/TIMING-CONSTRAINT',
                './/TIME-SYNCHRONIZATION',
                './/TIMING-EXTENSION'
            ],
            'priority': 12
        }
    }
    
    def __init__(self, min_confidence: float = 0.3):
        """
        Initialize type detector.
        
        Args:
            min_confidence: Minimum confidence threshold for detection
        """
        self.min_confidence = min_confidence
    
    def detect(self, document: ARXMLDocument) -> List[DetectedType]:
        """
        Detect ARXML types in document.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            List of detected types sorted by confidence
        """
        detected_types = []
        
        logger.info("Starting ARXML type detection")
        
        for type_name, type_config in self.TYPE_PATTERNS.items():
            patterns = type_config['patterns']
            priority = type_config['priority']
            
            matched_patterns = []
            total_elements = 0
            
            for pattern in patterns:
                try:
                    elements = document.xpath(pattern)
                    if elements:
                        matched_patterns.append(pattern)
                        total_elements += len(elements)
                        logger.debug(f"Pattern '{pattern}' matched {len(elements)} elements")
                except Exception as e:
                    logger.warning(f"Error evaluating pattern '{pattern}': {e}")
            
            if matched_patterns:
                # Calculate confidence based on matched patterns and priority
                pattern_ratio = len(matched_patterns) / len(patterns)
                priority_factor = 1.0 - (priority - 1) * 0.05  # Higher priority gets higher factor
                confidence = pattern_ratio * priority_factor
                
                if confidence >= self.min_confidence:
                    detected_type = DetectedType(
                        name=type_name,
                        confidence=confidence,
                        matched_patterns=matched_patterns,
                        element_count=total_elements
                    )
                    detected_types.append(detected_type)
                    logger.info(f"Detected type: {type_name} (confidence: {confidence:.2f})")
        
        # Sort by confidence (descending)
        detected_types.sort(key=lambda x: x.confidence, reverse=True)
        
        # If no specific types detected, classify as GENERIC
        if not detected_types:
            detected_types.append(DetectedType(
                name='GENERIC',
                confidence=1.0,
                matched_patterns=['*'],
                element_count=document.get_element_count()
            ))
            logger.info("No specific type detected, classified as GENERIC")
        
        return detected_types
    
    def detect_primary(self, document: ARXMLDocument) -> str:
        """
        Detect primary ARXML type.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            Primary type name
        """
        detected = self.detect(document)
        return detected[0].name if detected else 'GENERIC'
    
    def detect_all(self, document: ARXMLDocument) -> List[str]:
        """
        Get all detected type names.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            List of all detected type names
        """
        detected = self.detect(document)
        return [dt.name for dt in detected]
    
    def get_type_statistics(self, document: ARXMLDocument) -> Dict[str, Any]:
        """
        Get detailed statistics for detected types.
        
        Args:
            document: ARXML document to analyze
            
        Returns:
            Dictionary with type statistics
        """
        detected = self.detect(document)
        
        stats = {
            'primary_type': detected[0].name if detected else 'UNKNOWN',
            'all_types': [dt.name for dt in detected],
            'type_details': []
        }
        
        for dt in detected:
            stats['type_details'].append({
                'name': dt.name,
                'confidence': f"{dt.confidence:.2%}",
                'element_count': dt.element_count,
                'patterns_matched': len(dt.matched_patterns),
                'patterns_total': len(self.TYPE_PATTERNS[dt.name]['patterns']) if dt.name != 'GENERIC' else 0
            })
        
        return stats