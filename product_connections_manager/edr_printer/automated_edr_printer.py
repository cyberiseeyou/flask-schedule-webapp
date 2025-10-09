"""
Automated EDR Printer
=====================

This module provides a completely automated EDR report generation and printing system.
No user interaction required once configured.

Usage:
    python automated_edr_printer.py

Configuration:
    Edit the DEFAULT_EVENT_IDS list below to specify which events to process.
    Ensure authentication credentials are properly set in EDRReportGenerator.
"""

from .edr_report_generator import EDRReportGenerator
import sys
import datetime
from typing import List, Optional


class AutomatedEDRPrinter:
    """
    Fully automated EDR report printer with no user interaction.
    """
    
    def __init__(self):
        self.generator = EDRReportGenerator()
        
        # Default event IDs to process (edit these as needed)
        self.DEFAULT_EVENT_IDS = [
            "606034",  # Example event ID
            # Add more event IDs here as needed
        ]
    
    def authenticate_once(self) -> bool:
        """
        Perform authentication once for the entire session.
        
        Returns:
            True if authentication successful, False otherwise
        """
        print("🔐 Performing one-time authentication...")
        success = self.generator.authenticate()
        if success:
            print("✅ Authentication successful - token will be reused for all reports")
            return True
        else:
            print("❌ Authentication failed")
            return False
    
    def set_authentication_manually(self, auth_token: str) -> None:
        """
        Set authentication token manually (for automation scenarios where 
        MFA was completed separately).
        
        Args:
            auth_token: Pre-obtained authentication token
        """
        self.generator.auth_token = auth_token
        print(f"🔑 Authentication token set manually")
    
    def process_event_list(self, event_ids: Optional[List[str]] = None, 
                          save_copies: bool = True, 
                          print_reports: bool = True) -> dict:
        """
        Process a list of event IDs automatically.
        
        Args:
            event_ids: List of event IDs to process (uses default if None)
            save_copies: Whether to save permanent copies of reports
            print_reports: Whether to send reports to printer
            
        Returns:
            Dictionary with processing results for each event ID
        """
        if event_ids is None:
            event_ids = self.DEFAULT_EVENT_IDS
        
        if not self.generator.auth_token:
            print("❌ No authentication token available")
            print("📋 You must authenticate manually first or set token with set_authentication_manually()")
            return {}
        
        results = {}
        total_events = len(event_ids)
        
        print(f"🤖 Starting automated processing of {total_events} events...")
        print(f"💾 Save copies: {'Yes' if save_copies else 'No'}")
        print(f"🖨️ Print reports: {'Yes' if print_reports else 'No'}")
        print("-" * 60)
        
        for i, event_id in enumerate(event_ids, 1):
            print(f"\n📋 Processing event {i}/{total_events}: {event_id}")
            
            try:
                if print_reports:
                    # Full workflow: generate and print
                    success = self.generator.generate_and_print_edr_report(
                        event_id=event_id, 
                        save_copy=save_copies
                    )
                    results[event_id] = {
                        'success': success,
                        'generated': success,
                        'printed': success,
                        'saved': save_copies if success else False,
                        'error': None
                    }
                else:
                    # Generate and save only
                    edr_data = self.generator.get_edr_report(event_id)
                    if edr_data:
                        html_report = self.generator.generate_html_report(edr_data)
                        saved_file = None
                        if save_copies:
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            saved_file = self.generator.save_html_report(
                                html_report, 
                                f"edr_report_{event_id}_{timestamp}.html"
                            )
                        
                        results[event_id] = {
                            'success': True,
                            'generated': True,
                            'printed': False,
                            'saved': saved_file is not None,
                            'saved_file': saved_file,
                            'error': None
                        }
                        print(f"✅ Event {event_id} processed successfully")
                    else:
                        results[event_id] = {
                            'success': False,
                            'generated': False,
                            'printed': False,
                            'saved': False,
                            'error': 'Failed to retrieve EDR data'
                        }
                        print(f"❌ Event {event_id} failed: Could not retrieve data")
                        
            except Exception as e:
                results[event_id] = {
                    'success': False,
                    'generated': False,
                    'printed': False,
                    'saved': False,
                    'error': str(e)
                }
                print(f"❌ Event {event_id} failed: {e}")
        
        return results
    
    def print_summary(self, results: dict) -> None:
        """
        Print a summary of processing results.
        
        Args:
            results: Results dictionary from process_event_list()
        """
        print("\n" + "=" * 60)
        print("📊 PROCESSING SUMMARY")
        print("=" * 60)
        
        total_events = len(results)
        successful_events = sum(1 for r in results.values() if r['success'])
        failed_events = total_events - successful_events
        
        print(f"📋 Total Events: {total_events}")
        print(f"✅ Successful: {successful_events}")
        print(f"❌ Failed: {failed_events}")
        
        if failed_events > 0:
            print(f"\n❌ Failed Events:")
            for event_id, result in results.items():
                if not result['success']:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"   • {event_id}: {error_msg}")
        
        if successful_events > 0:
            print(f"\n✅ Successful Events:")
            for event_id, result in results.items():
                if result['success']:
                    status_parts = []
                    if result.get('generated'):
                        status_parts.append("Generated")
                    if result.get('printed'):
                        status_parts.append("Printed")
                    if result.get('saved'):
                        status_parts.append("Saved")
                    
                    status = " + ".join(status_parts)
                    print(f"   • {event_id}: {status}")
        
        print("=" * 60)
    
    def run_automated_batch(self, event_ids: Optional[List[str]] = None, authenticate: bool = True) -> bool:
        """
        Run a complete automated batch job.
        
        Args:
            event_ids: List of event IDs to process (uses default if None)
            authenticate: Whether to perform authentication (default: True)
            
        Returns:
            True if all events processed successfully, False otherwise
        """
        print("🤖 AUTOMATED EDR PRINTER")
        print("========================")
        print(f"⏰ Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Authenticate once if needed
        if authenticate and not self.generator.auth_token:
            if not self.authenticate_once():
                print("❌ Authentication failed - cannot proceed")
                return False
        
        # Process all events with existing authentication
        results = self.process_event_list(
            event_ids=event_ids,
            save_copies=True,
            print_reports=True
        )
        
        # Print summary
        self.print_summary(results)
        
        # Return overall success
        all_successful = all(r['success'] for r in results.values())
        
        print(f"⏰ Completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Overall Status: {'✅ SUCCESS' if all_successful else '❌ PARTIAL FAILURE'}")
        
        return all_successful


def main():
    """Main entry point for automated EDR printing."""
    printer = AutomatedEDRPrinter()
    
    # Check command line arguments for event IDs
    event_ids = None
    if len(sys.argv) > 1:
        event_ids = sys.argv[1:]
        print(f"📋 Using event IDs from command line: {event_ids}")
    else:
        print(f"📋 Using default event IDs: {printer.DEFAULT_EVENT_IDS}")
    
    print(f"\n🔐 Authentication Required")
    print("You will be prompted for MFA code once, then all reports will be processed automatically.")
    print()
    
    # Run the automated batch with authentication
    success = printer.run_automated_batch(event_ids, authenticate=True)
    return success


if __name__ == "__main__":
    exit_code = 0 if main() else 1
    sys.exit(exit_code)
