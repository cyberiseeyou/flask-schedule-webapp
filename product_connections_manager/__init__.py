"""
Product Connections Manager Platform
====================================

A comprehensive platform for managing Product Connections operations, 
including automated EDR printing, event management, and retail link integrations.

Author: CyberISeeYou
License: MIT
Repository: https://github.com/cyberiseeyou/product-connections-manager-platform
"""

__version__ = "1.0.0"
__author__ = "CyberISeeYou"
__email__ = "cyberiseeyou@gmail.com"
__license__ = "MIT"

from .edr_printer import EnhancedEDRPrinter, AutomatedEDRPrinter, EDRReportGenerator

__all__ = [
    "EnhancedEDRPrinter",
    "AutomatedEDRPrinter", 
    "EDRReportGenerator",
]
