#!/bin/bash
# Run web-based MCP Agent

# Ensure script is executable
chmod +x web_app.py

# Create static directory if it doesn't exist
mkdir -p static

# Run the web application
python web_app.py
