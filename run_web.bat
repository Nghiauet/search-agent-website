@echo off
:: Run web-based MCP Agent

:: Create static directory if it doesn't exist
if not exist static mkdir static

:: Run the web application
python web_app.py
