"""
EDR Printer Module
==================

This module provides Event Detail Report (EDR) generation and printing capabilities
for Walmart's Retail Link Event Management System.

Classes:
    - EDRReportGenerator: Core EDR data retrieval and HTML generation
    - AutomatedEDRPrinter: Automated batch processing with minimal interaction
    - EnhancedEDRPrinter: Advanced PDF consolidation with custom formatting
"""

# Conditionally import classes to avoid WeasyPrint dependency issues
try:
    from .edr_report_generator import EDRReportGenerator
    _generator_available = True
except ImportError:
    _generator_available = False
    EDRReportGenerator = None

try:
    from .automated_edr_printer import AutomatedEDRPrinter
    _automated_available = True
except ImportError:
    _automated_available = False
    AutomatedEDRPrinter = None

try:
    from .enhanced_edr_printer import EnhancedEDRPrinter
    _enhanced_available = True
except ImportError:
    _enhanced_available = False
    EnhancedEDRPrinter = None

__all__ = []
if _generator_available:
    __all__.append("EDRReportGenerator")
if _automated_available:
    __all__.append("AutomatedEDRPrinter")
if _enhanced_available:
    __all__.append("EnhancedEDRPrinter")