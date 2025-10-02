"""
EDR Printing Package
===================

Extracted EDR (Event Detail Report) printing capabilities from product-connections-manager.
This package provides automated Event Detail Report generation and printing for
Walmart's Retail Link Event Management System.

Usage:
    from product_connections_implementation.edr_printer import EDRReportGenerator

    generator = EDRReportGenerator()
    generator.authenticate()
    report_data = generator.get_edr_report(event_id="606034")
    html_report = generator.generate_html_report(report_data)
"""

from .edr_printer import *

__version__ = "1.0.0"
__author__ = "Extracted from product-connections-manager by CyberISeeYou"