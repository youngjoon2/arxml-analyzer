# ARXML Test Data

This directory contains ARXML files for testing purposes.

## Directory Structure

```
data/
├── official/          # Official AUTOSAR example files
│   ├── ecuc/         # ECUC (ECU Configuration) files
│   ├── swc/          # Software Component description files
│   ├── interface/    # Interface definition files
│   ├── system/       # System description files
│   ├── communication/# Communication matrix files
│   └── diagnostic/   # Diagnostic description files
├── samples/          # Sample ARXML files from various sources
│   └── ...           # Same subdirectory structure as official/
└── test_fixtures/    # Small test fixture files
    └── ...           # Same subdirectory structure as official/
```

## File Sources

### Official AUTOSAR Examples
- AUTOSAR Classic Platform examples
- AUTOSAR Adaptive Platform examples 
- AUTOSAR official demonstrations

### Sample Files
- Open-source AUTOSAR projects
- Public automotive ECU configurations
- Community-contributed examples

## Downloaded Files and Sources

### Communication Stack Files
- **ArcCore_EcucDefs_CanSM.arxml**: CAN State Manager configuration from sics-sse/moped
- **ArcCore_EcucDefs_CanTp.arxml**: CAN Transport Protocol configuration from sics-sse/moped
- **ArcCore_EcucDefs_Com.arxml**: AUTOSAR COM module configuration from sics-sse/moped
- **ArcCore_EcucDefs_PduR.arxml**: PDU Router configuration from sics-sse/moped
- **ArcCore_EcucDefs_SoAd.arxml**: Socket Adapter configuration from sics-sse/moped

### Diagnostic Stack Files  
- **AUTOSAR_MOD_DiagnosticManagement_Blueprint.arxml**: Adaptive Platform diagnostic blueprint from autosaros/Standards
- **ArcCore_EcucDefs_Dcm.arxml**: Diagnostic Communication Manager from sics-sse/moped
- **ArcCore_EcucDefs_Dem.arxml**: Diagnostic Event Manager from sics-sse/moped

### ECUC Configuration Files
- **ArcCore_EcucDefs_BswM.arxml**: Basic Software Manager from sics-sse/moped
- **ArcCore_EcucDefs_ComM.arxml**: Communication Manager from sics-sse/moped  
- **ArcCore_EcucDefs_EcuM.arxml**: ECU State Manager from sics-sse/moped
- **ArcCore_EcucDefs_Fee.arxml**: Flash EEPROM Emulation from sics-sse/moped
- **ArcCore_EcucDefs_MemIf.arxml**: Memory Abstraction Interface from sics-sse/moped
- **ArcCore_EcucDefs_NvM.arxml**: NvRam Manager from sics-sse/moped
- **ArcCore_EcucDefs_WdgM.arxml**: Watchdog Manager from sics-sse/moped

### Interface and Runtime Files
- **ArcCore_EcucDefs_Rte.arxml**: Runtime Environment configuration from sics-sse/moped

### System Configuration Files
- **AUTOSAR_MOD_UpdateAndConfigManagement_Blueprint.arxml**: Adaptive Platform management blueprint from autosaros/Standards
- **EcuExtract.arxml**: ECU extraction example from patrikja/autosar
- **SCU_Configuration.arxml**: System Control Unit configuration from sics-sse/moped

## Repository Information and Licenses

### sics-sse/moped
- **Repository**: https://github.com/sics-sse/moped
- **Description**: Mobile Open Platform for Experimental Development - AUTOSAR-based platform
- **License**: BSD 3-Clause License
- **Files**: Most ArcCore_EcucDefs_*.arxml files and SCU_Configuration.arxml

### autosaros/Standards  
- **Repository**: https://github.com/autosaros/Standards
- **Description**: AUTOSAR Standards collection for Adaptive and Classic platforms
- **License**: Proprietary AUTOSAR license (check individual files)
- **Files**: AUTOSAR_MOD_*.arxml blueprint files

### patrikja/autosar
- **Repository**: https://github.com/patrikja/autosar  
- **Description**: Simplified AUTOSAR modeling examples
- **License**: MIT License
- **Files**: EcuExtract.arxml

## Usage

These files are used for:
1. Unit testing of analyzers
2. Integration testing of CLI
3. Performance benchmarking
4. Feature validation

## License

Files in this directory may have different licenses. Please check individual files or subdirectories for specific license information.