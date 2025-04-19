#!/bin/bash
# Launch script for Gemini Terminal Agent

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "No .env file found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env file from template. Please edit it with your API keys."
        echo "Exiting. Run this script again after setting up your API keys."
        exit 1
    else
        echo "No .env.example file found. Please create a .env file with your API keys."
        exit 1
    fi
fi

# Print ASCII banner if it exists
if [ -f ".github/gemini-agent-banner.txt" ]; then
    cat .github/gemini-agent-banner.txt
    echo ""
    echo ""
fi

# Run the agent
echo "Starting Gemini Terminal Agent..."
python main.py
