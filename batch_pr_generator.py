#!/usr/bin/env python3
"""
Batch PR Generator

This script combines markdown reports from phase folders into a single
comprehensive Pull Request description ready for GitHub.
"""

import os
import re
from datetime import datetime

def read_file_content(file_path):
    """Read and return the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return ""

def get_phase_files(phase_dir):
    """Get all markdown files in the specified phase directory, sorted by name."""
    if not os.path.exists(phase_dir):
        return []
        
    files = [f for f in os.listdir(phase_dir) if f.endswith('.md') and os.path.isfile(os.path.join(phase_dir, f))]
    return sorted(files)

def create_pr_description():
    """Create a comprehensive PR description from all phase reports."""
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        print(f"Error: {exports_dir} directory does not exist.")
        return False
    
    # Define phase order for the PR description
    phases = [
        "planning",
        "solution_design",
        "ticket_breakdown",
        "implementation",
        "testing",
        "reporting"
    ]
    
    # Start building the PR description
    pr_content = [
        "# 🚀 TerraFusionPlatform Pull Request",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "This PR includes changes developed through the TerraFusionPlatform ICSF DevOps AI System.",
        "",
        "---",
        ""
    ]
    
    # Process each phase in order
    for phase in phases:
        phase_dir = os.path.join(exports_dir, phase)
        phase_files = get_phase_files(phase_dir)
        
        if not phase_files:
            continue
            
        # Add phase header
        phase_name = phase.replace("_", " ").title()
        pr_content.append(f"## {phase_name} Phase")
        pr_content.append("")
        
        # Process each file in the phase
        for file_name in phase_files:
            file_path = os.path.join(phase_dir, file_name)
            content = read_file_content(file_path)
            
            if content:
                # Clean up the content - remove any top-level headers (we'll use the filename instead)
                content_lines = content.split('\n')
                clean_lines = []
                
                # Skip potential title headers at the beginning
                start_idx = 0
                for i, line in enumerate(content_lines):
                    if i == 0 and line.startswith('# '):
                        # Use this title as the section title, but formatted as an h3
                        title = line[2:].strip()
                        clean_lines.append(f"### {title}")
                        start_idx = i + 1
                        break
                
                # If we didn't find a title, use the filename
                if start_idx == 0:
                    # Clean up the filename to create a nice title
                    title = os.path.splitext(file_name)[0]
                    title = title.replace('_', ' ').title()
                    clean_lines.append(f"### {title}")
                
                # Add the rest of the content, indenting any headers
                for line in content_lines[start_idx:]:
                    if re.match(r'^#{1,6}\s', line):
                        # This is a header, add one more # to demote it one level
                        clean_lines.append('#' + line)
                    else:
                        clean_lines.append(line)
                
                pr_content.append('\n'.join(clean_lines))
                pr_content.append("\n---\n")
        
    # Add footer
    pr_content.append("\n## Additional Information")
    pr_content.append("\n**🔍 Testing Instructions:**")
    pr_content.append("- Clone this branch and follow the steps in the Testing phase section")
    pr_content.append("- Verify all acceptance criteria have been met")
    pr_content.append("\n**📋 Checklist:**")
    pr_content.append("- [ ] Code follows the project style guide")
    pr_content.append("- [ ] Tests are passing")
    pr_content.append("- [ ] Documentation has been updated")
    pr_content.append("- [ ] UI changes include screenshots")
    pr_content.append("\n🔥 Built with ❤️ using the Immersive CyberSecurity Simulation Framework (ICSF).")
    
    # Write the PR description to a file
    output_path = "PR_description.md"
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write('\n'.join(pr_content))
        print(f"✅ PR description successfully written to {output_path}")
        return True
    except Exception as e:
        print(f"Error writing PR description: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔄 Generating comprehensive PR description...")
    if create_pr_description():
        print("✅ PR description generation complete!")
        print("📋 You can now use PR_description.md for your GitHub Pull Request.")
    else:
        print("❌ PR description generation failed!")