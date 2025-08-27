# ARXML Universal Analyzer

A comprehensive Python tool for analyzing AUTOSAR ARXML files with support for multiple document types and output formats.

## Features

- 🔍 **Auto-detection** of ARXML document types
- 📊 **Multiple analyzers** for different ARXML types:
  - ECUC (ECU Configuration)
  - SWC (Software Component)
  - Interface definitions
  - Gateway configurations  
  - Diagnostic configurations (DCM/DEM)
- 🎨 **Multiple output formats**: JSON, YAML, Tree, Table, CSV
- ⚡ **Stream processing** for large files
- ✅ **Validation** and **comparison** capabilities
- 📈 **Statistics** and **metrics** generation

## Installation

### Using uv (recommended)
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Using pip
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Quick Start

### Basic Usage
```bash
# Analyze an ARXML file (auto-detect type)
python main.py analyze example.arxml

# Specify output format
python main.py analyze example.arxml --output json

# Save to file
python main.py analyze example.arxml --output json -f result.json

# Use streaming for large files
python main.py analyze large_file.arxml --stream
```

### Other Commands
```bash
# Validate ARXML file
python main.py validate example.arxml

# Compare two files
python main.py compare file1.arxml file2.arxml

# Get statistics
python main.py stats example.arxml
```

## Supported ARXML Types

- **ECUC**: ECU Configuration modules
- **SWC**: Software Components 
- **Interface**: Port interfaces (S/R, C/S, Mode-Switch, etc.)
- **Gateway**: PDU routing and signal gateway configurations
- **Diagnostic**: DCM/DEM configurations and DTCs
- **System**: System descriptions
- **ECU Extract**: ECU extraction files
- **MCAL**: Microcontroller Abstraction Layer
- **Communication**: Communication matrix
- **BSW**: Basic Software modules

## Project Structure

```
arxml-analyzer/
├── main.py                 # Main entry point
├── arxml_analyzer/         # Core package
│   ├── analyzers/          # Type-specific analyzers
│   ├── cli/                # CLI interface
│   ├── core/               # Core components
│   │   ├── analyzer/       # Base analyzer & patterns
│   │   ├── parser/         # XML parsers
│   │   ├── reporter/       # Output formatters
│   │   └── validator/      # Validation components
│   ├── models/             # Data models
│   └── utils/              # Utilities
├── tests/                  # Test suites
├── data/                   # Sample ARXML files
└── docs/                   # Documentation
```

## Development

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_diagnostic_analyzer.py -v

# With coverage
pytest tests/ --cov=arxml_analyzer --cov-report=html
```

### Code Quality
```bash
# Format code
black arxml_analyzer tests

# Sort imports
isort arxml_analyzer tests

# Type checking
mypy arxml_analyzer

# Linting
flake8 arxml_analyzer
```

## Documentation

- [Requirements](docs/REQUIREMENTS.md) - Detailed requirements specification
- [Implementation](docs/IMPLEMENTATION.md) - Implementation details
- [TODO](docs/TODO.md) - Development roadmap

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please use the [GitHub Issues](https://github.com/yourusername/arxml-analyzer/issues) page.