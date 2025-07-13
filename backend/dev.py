#!/usr/bin/env python3
"""
Development script with hot reload enabled
"""

import os
import sys

# Set development environment
os.environ["ENVIRONMENT"] = "development"
os.environ["DEV"] = "true"

# Add dev flag to sys.argv for run.py detection
if "--dev" not in sys.argv:
    sys.argv.append("--dev")

# Import and run the main script
from run import main

if __name__ == "__main__":
    main() 