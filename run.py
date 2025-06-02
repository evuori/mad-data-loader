#!/usr/bin/env python3
"""
Convenience script to run the main application from the project root directory.
This script adds the src directory to the Python path and then runs the main application.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
project_root = Path(__file__).parent
sys.path.insert(0, str(src_dir))

# Change to the src directory for proper relative imports
os.chdir(src_dir)

# Import and run the main function
from main import main

if __name__ == "__main__":
    # Fix config file paths that are relative to project root
    for i, arg in enumerate(sys.argv):
        if arg == "--config-file" and i + 1 < len(sys.argv):
            # If the config file path doesn't start with /, make it relative to project root
            config_path = sys.argv[i + 1]
            if not config_path.startswith('/') and not config_path.startswith('../'):
                sys.argv[i + 1] = str(project_root / config_path)
        elif arg.startswith('--config-file='):
            # Handle --config-file=path format
            config_path = arg.split('=', 1)[1]
            if not config_path.startswith('/') and not config_path.startswith('../'):
                sys.argv[i] = f"--config-file={project_root / config_path}"
    
    # If no config file specified, set the default to project root
    if '--config-file' not in sys.argv and not any(arg.startswith('--config-file=') for arg in sys.argv):
        sys.argv.extend(['--config-file', str(project_root / 'config' / 'pages.json')])
    
    sys.exit(main()) 