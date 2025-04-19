#!/usr/bin/env python3
"""
Main entry point for the MCP Agent.
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logging import setup_logging
from utils.config import settings
from agent.terminal_agent import run_agent

def setup_environment():
    """Setup environment variables for API keys if needed."""
    # If GOOGLE_GENAI_API_KEY is in settings but not in environment, set it
    if settings.GOOGLE_GENAI_API_KEY and "GOOGLE_GENAI_API_KEY" not in os.environ:
        os.environ["GOOGLE_GENAI_API_KEY"] = settings.GOOGLE_GENAI_API_KEY
    
    # Ensure Google API key is set for authentication
    if settings.GOOGLE_GENAI_API_KEY and "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_GENAI_API_KEY

async def main():
    """Main function to run the Gemini Terminal Agent."""
    # Configure logging
    setup_logging()
    
    # Setup environment variables
    setup_environment()
    
    # Run the agent
    await run_agent()

if __name__ == "__main__":
    # Run the application
    asyncio.run(main())
