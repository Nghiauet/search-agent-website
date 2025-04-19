#!/usr/bin/env python3
"""
Entry point for running the MCP search server.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from search.server import main

if __name__ == "__main__":
    # Run the search server
    main()
