#!/usr/bin/env python3
"""
ARXML Universal Analyzer - Main Entry Point

A comprehensive tool for analyzing AUTOSAR ARXML files.
"""

import sys
from pathlib import Path

# Add the module path
sys.path.insert(0, str(Path(__file__).parent))

from arxml_analyzer.cli.main import main

if __name__ == "__main__":
    main()