#!/usr/bin/env python3
"""
Auto Folder MD Reports

This script organizes markdown reports from the exports directory into
phase-specific folders for better organization.
"""

import os
import re
import shutil
from datetime import datetime

# Define phase names and their corresponding patterns
PHASES = {
    "planning": ["ux_audit", "data_flow", "problem_list", "planning"],
    "solution_design": ["ux_plan", "data_awareness", "solution", "design"],
    "ticket_breakdown": ["ticket", "task", "acceptance_criteria"],
    "implementation": ["code_change", "unit_test", "implementation"],
    "testing": ["end_to_end", "validation", "testing", "test_result"],
    "reporting": ["completion", "report", "summary"]
}

def ensure_phase_folders():
    """Ensure all phase folders exist within the exports directory."""
    if not os.path.exists("exports"):
        os.makedirs("exports")
        
    for phase in PHASES.keys():
        phase_dir = os.path.join("exports", phase)
        if not os.path.exists(phase_dir):
            os.makedirs(phase_dir)
            print(f"Created directory: {phase_dir}")

def determine_phase(filename):
    """Determine which phase a file belongs to based on its name."""
    filename_lower = filename.lower()
    
    for phase, patterns in PHASES.items():
        for pattern in patterns:
            if pattern in filename_lower:
                return phase
    
    # Default to a misc folder if no pattern matches
    return "misc"

def organize_reports():
    """Organize markdown reports into phase-specific folders."""
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        print(f"Error: {exports_dir} directory does not exist.")
        return
        
    # Ensure phase folders exist
    ensure_phase_folders()
    
    # Track movement of files
    moved_files = []
    
    # Find and move .md files
    for filename in os.listdir(exports_dir):
        file_path = os.path.join(exports_dir, filename)
        
        # Only process .md files directly in the exports directory
        if os.path.isfile(file_path) and filename.endswith(".md"):
            phase = determine_phase(filename)
            
            # Create misc directory if needed
            if phase == "misc":
                misc_dir = os.path.join(exports_dir, "misc")
                if not os.path.exists(misc_dir):
                    os.makedirs(misc_dir)
            
            # Move the file to its appropriate phase directory
            phase_dir = os.path.join(exports_dir, phase)
            dest_path = os.path.join(phase_dir, filename)
            
            try:
                # If a file with the same name exists, add a timestamp
                if os.path.exists(dest_path):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    base, ext = os.path.splitext(filename)
                    new_filename = f"{base}_{timestamp}{ext}"
                    dest_path = os.path.join(phase_dir, new_filename)
                
                shutil.move(file_path, dest_path)
                moved_files.append((filename, phase))
                print(f"Moved {filename} to {phase} directory")
            except Exception as e:
                print(f"Error moving {filename}: {str(e)}")
    
    # Print summary
    if moved_files:
        print("\nSummary of file movements:")
        for filename, phase in moved_files:
            print(f"  - {filename} → {phase}")
    else:
        print("\nNo files were moved. Make sure there are .md files in the exports directory.")

if __name__ == "__main__":
    print("🔄 Starting organization of markdown reports...")
    organize_reports()
    print("✅ Organization complete!")