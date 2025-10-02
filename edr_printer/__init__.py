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

from .edr_report_generator import EDRReportGenerator
from .automated_edr_printer import AutomatedEDRPrinter
from .enhanced_edr_printer import EnhancedEDRPrinter

__all__ = [
    "EDRReportGenerator",
    "AutomatedEDRPrinter", 
    "EnhancedEDRPrinter",
]
