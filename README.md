# MCP Agent with Gemini

A terminal-based agent using Google Gemini model with search capabilities.

## Refactored Architecture

The code has been refactored to improve structure, maintainability, and readability while keeping the same functionality. Key improvements include:

1. **Modular Structure**: Code is organized into clear modules with specific responsibilities
2. **Separation of Concerns**: Agent logic, search functionality, and utilities are cleanly separated
3. **Improved Error Handling**: More consistent error handling throughout the codebase
4. **Centralized Logging**: Consistent logging configuration across all components
5. **Better Configuration Management**: Centralized settings with environment variable support

## Project Structure

```
mcp-agent/
│
├── main.py               # Main entry point for the application
├── search_server.py      # Entry point for running the search server
├── .env                  # Environment variables
├── README.md             # Project documentation
│
├── agent/                # Agent implementation
│   ├── __init__.py
│   ├── terminal_agent.py # Core agent implementation
│   └── config.py         # Configuration for the agent
│
├── search/               # Search functionality
│   ├── __init__.py
│   ├── server.py         # MCP search server implementation
│   ├── engine.py         # Search engine implementation
│   └── content.py        # Web content extraction 
│
└── utils/                # Shared utilities
    ├── __init__.py
    ├── config.py         # Global configuration
    └── logging.py        # Centralized logging setup
```

## Setup and Usage

1. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **Configure environment variables** in a `.env` file:
   ```
   GOOGLE_GENAI_API_KEY=your_api_key_here
   SEARCH_ENGINE_API_KEY=your_search_api_key_here
   SEARCH_ENGINE_CSE_ID=your_search_cse_id_here
   DEFAULT_MODEL=gemini-2.5-flash-preview-04-17
   ```

3. **Run the agent**:
   ```
   python main.py
   ```

## Features

- **Terminal Interface**: Easy-to-use interactive terminal
- **Web Search**: Query the web for information
- **Conversation History**: Maintains context across interactions
- **Advanced Search Options**: Domain filtering and more

## Commands

- **help**: Show available tools and commands
- **clear**: Clear conversation history
- **exit/quit/q**: Exit the program

## Advanced Configuration

You can customize the agent behavior by modifying settings in the `.env` file:

- **DEFAULT_MODEL**: Choose which Gemini model to use
- **MAX_CONCURRENT_REQUESTS**: Control the concurrency of requests
- **CACHE_TTL**: Set the cache time-to-live in seconds
- **MAX_CONTENT_LENGTH**: Maximum content length to extract from websites
