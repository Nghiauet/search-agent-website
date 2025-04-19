@echo off
REM Launch script for Gemini Terminal Agent on Windows

REM Check if virtual environment exists
if exist venv\ (
    echo Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if .env file exists
if not exist .env (
    echo No .env file found. Creating from template...
    if exist .env.example (
        copy .env.example .env
        echo Created .env file from template. Please edit it with your API keys.
        echo Exiting. Run this script again after setting up your API keys.
        pause
        exit /b 1
    ) else (
        echo No .env.example file found. Please create a .env file with your API keys.
        pause
        exit /b 1
    )
)

REM Print ASCII banner if it exists
if exist .github\gemini-agent-banner.txt (
    type .github\gemini-agent-banner.txt
    echo.
    echo.
)

REM Run the agent
echo Starting Gemini Terminal Agent...
python main.py
pause
