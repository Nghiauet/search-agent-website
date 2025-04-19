# MCP Agent Web Interface

This is a web-based interface for the MCP Agent chatbot. It provides the same functionality as the terminal version but with a more user-friendly web interface.

## Features

- Chat with the MCP Agent in a web browser
- Clean, responsive UI that works on desktop and mobile
- Markdown support for formatted responses
- Session management to maintain conversation history
- Same powerful search capabilities as the terminal version

## How to Run

### On macOS/Linux:

1. Make sure you have all the required dependencies installed:
   ```
   pip install -r requirements.txt
   ```

2. Make the run script executable:
   ```
   chmod +x run_web.sh
   ```

3. Run the web application:
   ```
   ./run_web.sh
   ```

### On Windows:

1. Make sure you have all the required dependencies installed:
   ```
   pip install -r requirements.txt
   ```

2. Run the web application:
   ```
   run_web.bat
   ```

## Accessing the Web Interface

Once the application is running, open your web browser and navigate to:

```
http://localhost:8001
```

(The port number may vary if you have customized the MCP_SERVER_PORT in your .env file)

## Usage

- Type your message in the text area at the bottom of the screen and click "Send" or press Enter
- Click "Clear Chat" to start a new conversation
- Click "Help" to see available tools and commands

## Technical Details

The web interface uses:
- aiohttp for the web server
- HTML, CSS, and JavaScript for the frontend
- The same MCP Agent backend as the terminal version

## Requirements

The web interface has the same requirements as the terminal version, plus:
- aiohttp (Python web server)

Enjoy chatting with your MCP Agent in the web interface!
