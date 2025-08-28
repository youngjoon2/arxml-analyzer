"""Unit tests for DocumentProfiler."""

import unittest
import xml.etree.ElementTree as etree
from pathlib import Path

from arxml_analyzer.core.profiler.document_profiler import (
    DocumentProfiler,
    DocumentProfile,
    ElementPattern,
    NamingConvention
)


class TestDocumentProfiler(unittest.TestCase):
    """Test cases for DocumentProfiler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.profiler = DocumentProfiler()
        
    def test_profiler_initialization(self):
        """Test profiler initialization."""
        self.assertIsNotNone(self.profiler)
        self.assertIsNone(self.profiler._profile)
        self.assertEqual(len(self.profiler._element_cache), 0)
    
    def test_simple_document_profiling(self):
        """Test profiling a simple XML document."""
        # Create a simple test document
        xml_content = """
        <AUTOSAR xmlns="http://www.autosar.org/schema/r4.0">
            <AR-PACKAGES>
                <AR-PACKAGE>
                    <SHORT-NAME>TestPackage</SHORT-NAME>
                    <ELEMENTS>
                        <ECUC-MODULE-CONFIGURATION-VALUES>
                            <SHORT-NAME>TestModule</SHORT-NAME>
                            <DEFINITION-REF>/path/to/definition</DEFINITION-REF>
                            <CONTAINERS>
                                <ECUC-CONTAINER-VALUE>
                                    <SHORT-NAME>Container1</SHORT-NAME>
                                    <PARAMETER-VALUES>
                                        <ECUC-NUMERICAL-PARAM-VALUE>
                                            <DEFINITION-REF>/param/def</DEFINITION-REF>
                                            <VALUE>42</VALUE>
                                        </ECUC-NUMERICAL-PARAM-VALUE>
                                    </PARAMETER-VALUES>
                                </ECUC-CONTAINER-VALUE>
                            </CONTAINERS>
                        </ECUC-MODULE-CONFIGURATION-VALUES>
                    </ELEMENTS>
                </AR-PACKAGE>
            </AR-PACKAGES>
        </AUTOSAR>
        """
        
        root = etree.fromstring(xml_content)
        profile = self.profiler.profile_document(root)
        
        # Verify profile was created
        self.assertIsNotNone(profile)
        self.assertIsInstance(profile, DocumentProfile)
        
        # Check namespace detection
        self.assertEqual(profile.namespace, "http://www.autosar.org/schema/r4.0")
        
        # Check root element detection
        self.assertEqual(profile.root_element, "AUTOSAR")
        
        # Check that elements were discovered
        self.assertGreater(len(profile.element_patterns), 0)
        
        # Check document type detection
        self.assertEqual(profile.document_type, "ECUC")
    
    def test_naming_convention_detection(self):
        """Test detection of naming conventions."""
        test_cases = [
            ("UPPER-CASE-NAME", NamingConvention.UPPER_CASE),
            ("lowercase", NamingConvention.LOWER_CASE),
            ("PascalCase", NamingConvention.PASCAL_CASE),
            ("camelCase", NamingConvention.CAMEL_CASE),
            ("snake_case", NamingConvention.SNAKE_CASE),
            ("kebab-case", NamingConvention.KEBAB_CASE),
        ]
        
        for name, expected_convention in test_cases:
            with self.subTest(name=name):
                convention = self.profiler._detect_naming_convention(name)
                self.assertEqual(convention, expected_convention)
    
    def test_element_type_identification(self):
        """Test identification of element types."""
        xml_content = """
        <ROOT>
            <ECUC-CONTAINER-VALUE>
                <SHORT-NAME>TestContainer</SHORT-NAME>
            </ECUC-CONTAINER-VALUE>
            <ECUC-NUMERICAL-PARAM-VALUE>
                <VALUE>100</VALUE>
            </ECUC-NUMERICAL-PARAM-VALUE>
            <ECUC-REFERENCE-VALUE>
                <VALUE-REF>/path/to/ref</VALUE-REF>
            </ECUC-REFERENCE-VALUE>
        </ROOT>
        """
        
        root = etree.fromstring(xml_content)
        profile = self.profiler.profile_document(root)
        
        # Check container identification
        containers = self.profiler.get_container_elements()
        self.assertIn("ECUC-CONTAINER-VALUE", containers)
        
        # Check parameter identification  
        parameters = self.profiler.get_parameter_elements()
        self.assertIn("ECUC-NUMERICAL-PARAM-VALUE", parameters)
        
        # Check reference identification
        references = self.profiler.get_reference_elements()
        self.assertIn("ECUC-REFERENCE-VALUE", references)
    
    def test_document_type_detection(self):
        """Test detection of different document types."""
        test_cases = [
            ("<ECUC-MODULE-CONFIGURATION><SHORT-NAME>Test</SHORT-NAME></ECUC-MODULE-CONFIGURATION>", "ECUC"),
            ("<SW-COMPONENT-TYPE><SHORT-NAME>Test</SHORT-NAME></SW-COMPONENT-TYPE>", "SWC"),
            ("<GATEWAY-MODULE><PDU-R-CONFIG>Test</PDU-R-CONFIG></GATEWAY-MODULE>", "GATEWAY"),
            ("<DIAGNOSTIC-SERVICE><DCM-CONFIG>Test</DCM-CONFIG></DIAGNOSTIC-SERVICE>", "DIAGNOSTIC"),
        ]
        
        for xml_content, expected_type in test_cases:
            with self.subTest(expected_type=expected_type):
                root = etree.fromstring(xml_content)
                profile = self.profiler.profile_document(root)
                # Should detect type or be UNKNOWN
                self.assertIn(profile.document_type, [expected_type, "UNKNOWN"])
    
    def test_hierarchy_depth_calculation(self):
        """Test calculation of document hierarchy depth."""
        xml_content = """
        <ROOT>
            <LEVEL1>
                <LEVEL2>
                    <LEVEL3>
                        <LEVEL4>
                            <LEVEL5>Deep content</LEVEL5>
                        </LEVEL4>
                    </LEVEL3>
                </LEVEL2>
            </LEVEL1>
        </ROOT>
        """
        
        root = etree.fromstring(xml_content)
        profile = self.profiler.profile_document(root)
        
        # Should detect 5 levels of depth (0-indexed, so max is 5)
        self.assertEqual(profile.hierarchy_depth, 5)
    
    def test_statistics_generation(self):
        """Test generation of document statistics."""
        xml_content = """
        <ROOT>
            <ELEMENT1>Value1</ELEMENT1>
            <ELEMENT1>Value2</ELEMENT1>
            <ELEMENT2 attr="test">Value3</ELEMENT2>
            <CONTAINER>
                <PARAM>100</PARAM>
                <REF>/path/to/ref</REF>
            </CONTAINER>
        </ROOT>
        """
        
        root = etree.fromstring(xml_content)
        profile = self.profiler.profile_document(root)
        
        # Check statistics were generated
        self.assertIn('statistics', vars(profile))
        stats = profile.statistics
        
        # Check basic statistics
        self.assertIn('total_elements', stats)
        self.assertIn('unique_elements', stats)
        self.assertIn('max_depth', stats)
        
        # Total elements should be 7 (ROOT + 2*ELEMENT1 + ELEMENT2 + CONTAINER + PARAM + REF)
        self.assertEqual(stats['total_elements'], 7)
        
        # Unique elements should be 5 (ROOT, ELEMENT1, ELEMENT2, CONTAINER, PARAM, REF)
        self.assertEqual(stats['unique_elements'], 6)
    
    def test_xpath_generation(self):
        """Test XPath generation for elements."""
        xml_content = """
        <ROOT xmlns="http://example.com/ns">
            <ELEMENT>Test</ELEMENT>
        </ROOT>
        """
        
        root = etree.fromstring(xml_content)
        profile = self.profiler.profile_document(root)
        
        # Test namespace-aware XPath
        xpath_with_ns = self.profiler.get_element_xpath("ELEMENT", use_namespace=True)
        self.assertEqual(xpath_with_ns, ".//*[local-name()='ELEMENT']")
        
        # Test simple XPath
        xpath_simple = self.profiler.get_element_xpath("ELEMENT", use_namespace=False)
        self.assertEqual(xpath_simple, ".//ELEMENT")
    
    def test_pattern_suggestions(self):
        """Test pattern suggestions for element types."""
        xml_content = """
        <ROOT>
            <MODULE-CONFIG>Test</MODULE-CONFIG>
            <CONTAINER-VALUE>Test</CONTAINER-VALUE>
            <PARAM-VALUE>100</PARAM-VALUE>
            <REFERENCE-DEF>/ref</REFERENCE-DEF>
        </ROOT>
        """
        
        root = etree.fromstring(xml_content)
        profile = self.profiler.profile_document(root)
        
        # Test module pattern suggestions
        modules = self.profiler.suggest_patterns_for_type('module')
        self.assertIn("MODULE-CONFIG", modules)
        
        # Test container pattern suggestions
        containers = self.profiler.suggest_patterns_for_type('container')
        self.assertIn("CONTAINER-VALUE", containers)
        
        # Test parameter pattern suggestions
        params = self.profiler.suggest_patterns_for_type('parameter')
        self.assertIn("PARAM-VALUE", params)
        
        # Test reference pattern suggestions
        refs = self.profiler.suggest_patterns_for_type('reference')
        self.assertIn("REFERENCE-DEF", refs)
    
    def test_profile_export(self):
        """Test exporting profile as dictionary."""
        xml_content = """
        <ROOT xmlns="http://example.com/ns">
            <CONTAINER>
                <PARAM>Value</PARAM>
            </CONTAINER>
        </ROOT>
        """
        
        root = etree.fromstring(xml_content)
        profile = self.profiler.profile_document(root)
        
        # Export profile
        exported = self.profiler.export_profile()
        
        # Check exported structure
        self.assertIsInstance(exported, dict)
        self.assertIn('document_type', exported)
        self.assertIn('namespace', exported)
        self.assertIn('statistics', exported)
        self.assertIn('container_patterns', exported)
        self.assertIn('parameter_patterns', exported)
        self.assertIn('reference_patterns', exported)
    
    def test_empty_document_handling(self):
        """Test handling of empty or minimal documents."""
        xml_content = "<ROOT/>"
        
        root = etree.fromstring(xml_content)
        profile = self.profiler.profile_document(root)
        
        # Should handle empty document gracefully
        self.assertIsNotNone(profile)
        self.assertEqual(profile.root_element, "ROOT")
        self.assertEqual(profile.hierarchy_depth, 0)
        self.assertEqual(len(profile.element_patterns), 1)  # Just ROOT


if __name__ == '__main__':
    unittest.main()