# Gemini Terminal Agent

A powerful terminal-based agent using Google's Gemini model with web search capabilities. This agent lets you interact with Gemini through your terminal while leveraging real-time web search for up-to-date information.


## Features

- 🤖 **Conversational AI Interface** - Talk with Google's Gemini models directly from your terminal
- 🔍 **Web Search Integration** - Get real-time information from the web
- 💬 **Conversation History** - Maintain context throughout your conversation
- 🛠️ **Advanced Search Options** - Filter by domains, exclude sites, and more
- 📝 **Clean, Modular Architecture** - Well-structured codebase that's easy to extend

## Installation

### Prerequisites

- Python 3.9+
- Google API key for Gemini models
- Google Custom Search Engine (CSE) API key and ID

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/gemini-terminal-agent.git
   cd gemini-terminal-agent
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root with your API keys:
   ```
   GOOGLE_GENAI_API_KEY=your_gemini_api_key_here
   SEARCH_ENGINE_API_KEY=your_google_api_key_here
   SEARCH_ENGINE_CSE_ID=your_cse_id_here
   DEFAULT_MODEL=gemini-2.5-flash-preview-04-17
   ```

## Setting Up Google Search Engine

To use the web search functionality, you need to set up a Google Custom Search Engine:

1. **Get a Google API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Navigate to "APIs & Services" > "Library"
   - Search for "Custom Search API" and enable it
   - Go to "APIs & Services" > "Credentials"
   - Create an API key and copy it (this will be your `SEARCH_ENGINE_API_KEY`)

2. **Create a Custom Search Engine**:
   - Go to [Programmable Search Engine](https://programmablesearchengine.google.com/about/)
   - Click "Create a Programmable Search Engine"
   - Add sites to search (use `*.com` to search the entire web)
   - Give your search engine a name
   - In "Customize" > "Basics", enable "Search the entire web"
   - Get your Search Engine ID from the "Setup" > "Basics" page (this will be your `SEARCH_ENGINE_CSE_ID`)

3. **Get a Gemini API Key**:
   - Go to [Google AI Studio](https://ai.google.dev/)
   - Sign in with your Google account
   - Go to "API Keys" and create a new API key
   - Copy the API key (this will be your `GOOGLE_GENAI_API_KEY`)

## Usage

Run the agent from the terminal:

```bash
python main.py
```

### Commands

- Type your question or prompt to interact with the agent
- Type `help` to see available tools and commands
- Type `clear` to clear the conversation history
- Type `exit`, `quit`, or `q` to exit the program

### Example Queries

```
>>> What is the capital of France?
Paris is the capital of France. It is located in the north-central part of the country on the Seine River.

>>> search for recent developments in quantum computing
Searching the web for recent developments in quantum computing...
[Agent response with up-to-date information]

>>> help
🔍 Available Tools:
  - search: Search for information online based on a query
  - advanced_search: Perform an advanced search with domain filtering and time range options

⌨️ Terminal Commands:
  - help: Show this help message
  - clear: Clear conversation history
  - exit/quit/q: Exit the program
```

## Project Structure

```
gemini-terminal-agent/
│
├── main.py               # Main entry point
├── search_server.py      # Search server entry point
├── .env                  # Environment variables (not versioned)
│
├── agent/                # Agent implementation
│   ├── __init__.py
│   ├── terminal_agent.py # Core agent implementation
│   └── config.py         # Agent configuration
│
├── search/               # Search functionality
│   ├── __init__.py
│   ├── server.py         # MCP search server
│   ├── engine.py         # Search engine implementation
│   └── content.py        # Web content extraction 
│
└── utils/                # Shared utilities
    ├── __init__.py
    ├── config.py         # Global configuration
    └── logging.py        # Logging setup
```

## Advanced Configuration

You can customize the agent's behavior by modifying settings in your `.env` file:

```
# Model settings
DEFAULT_MODEL=gemini-2.5-flash-preview-04-17
# Other models: gemini-1.5-pro, gemini-1.5-flash

# Search settings
MAX_CONCURRENT_REQUESTS=5
CONNECTION_TIMEOUT=10
CONTENT_TIMEOUT=15
MAX_CONTENT_LENGTH=5000
CACHE_TTL=3600
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project uses [LangChain](https://github.com/hwchase17/langchain) for the agent framework
- Web search functionality powered by Google Custom Search Engine
- Built with Google's Gemini models
