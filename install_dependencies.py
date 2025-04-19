#!/usr/bin/env python
"""
Helper script to install dependencies for the MCP agent.
This will install Brotli if it's not already installed, which is needed for handling compressed web content.
"""

import sys
import subprocess
import importlib

def check_package(package_name):
    """Check if a package is installed."""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """Install a package using pip."""
    print(f"Installing {package_name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
    print(f"{package_name} installed successfully.")

def main():
    """Main function to check and install dependencies."""
    print("Checking for required dependencies...")
    
    # Check for Brotli
    if not check_package("brotli"):
        print("Brotli is not installed. This is needed for handling compressed web content.")
        install_package("brotli")
    else:
        print("Brotli is already installed.")
    
    # Check for aiohttp
    if not check_package("aiohttp"):
        print("aiohttp is not installed. This is required for HTTP requests.")
        install_package("aiohttp")
    else:
        print("aiohttp is already installed.")
    
    # Check for beautiful soup
    if not check_package("bs4"):
        print("BeautifulSoup (bs4) is not installed. This is required for HTML parsing.")
        install_package("bs4")
    else:
        print("BeautifulSoup is already installed.")

    print("\nAll dependencies installed. You can now run the agent with:")
    print("python gemini_agent.py")

if __name__ == "__main__":
    main()
