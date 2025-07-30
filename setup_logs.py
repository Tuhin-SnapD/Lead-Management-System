#!/usr/bin/env python
"""
Setup script to create logs directory and ensure proper permissions.
"""

import os
import sys
from pathlib import Path

def setup_logs():
    """Create logs directory if it doesn't exist."""
    # Get the project root directory
    project_root = Path(__file__).parent
    logs_dir = project_root / 'logs'
    
    try:
        # Create logs directory if it doesn't exist
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created logs directory: {logs_dir}")
        else:
            print(f"Logs directory already exists: {logs_dir}")
        
        # Create a .gitkeep file to ensure the directory is tracked by git
        gitkeep_file = logs_dir / '.gitkeep'
        if not gitkeep_file.exists():
            gitkeep_file.touch()
            print(f"Created .gitkeep file: {gitkeep_file}")
        
        # Test if the directory is writable
        test_file = logs_dir / 'test_write.tmp'
        try:
            test_file.touch()
            test_file.unlink()  # Remove the test file
            print("✓ Logs directory is writable")
        except (PermissionError, OSError) as e:
            print(f"⚠ Warning: Logs directory may not be writable: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error setting up logs directory: {e}")
        return False

if __name__ == '__main__':
    success = setup_logs()
    sys.exit(0 if success else 1) 