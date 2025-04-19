# MCP Agent with Search Capabilities

This project implements an AI assistant using Google's Gemini model with web search capabilities through the Multi-modal Collaborative Protocol (MCP).

## Features

- Terminal-based AI assistant using Gemini models
- Web search capabilities using Google Custom Search API
- Advanced search options (domain filtering, etc.)
- Robust error handling and fallback mechanisms

## Installation

### Prerequisites

- Python 3.10 or higher
- Conda or pip for package management
- Google API keys (Gemini API and Custom Search API)

### Setup

1. Clone this repository
2. Create and activate a virtual environment:

```bash
conda create -n mcp-agent python=3.13
conda activate mcp-agent
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Run the dependency installer to ensure all needed packages are installed:

```bash
python install_dependencies.py
```

5. Create a `.env` file with your API keys:

```
# API Keys
GOOGLE_GENAI_API_KEY=your_gemini_api_key
DEFAULT_MODEL=gemini-2.5-flash-preview-04-17

# Server Settings
MCP_SERVER_PORT=8000

# Search Engine Settings
SEARCH_ENGINE_API_KEY=your_google_search_api_key
SEARCH_ENGINE_CSE_ID=your_custom_search_engine_id
```

## Usage

### Running the Agent

To start the Gemini terminal agent:

```bash
python gemini_agent.py
```

This will launch an interactive terminal where you can chat with the agent and ask it to search for information online.

### Commands

The agent supports the following commands:

- `help`: Display available tools and commands
- `clear`: Clear conversation history
- `exit`, `quit`, or `q`: Exit the program

### Testing

To test the search functionality:

```bash
python test_search.py
```

To test both the search and agent functionality:

```bash
python test.py
```

## Troubleshooting

### Browser Content Issues

If you encounter errors related to "Brotli compression" when the agent tries to access certain websites, ensure you have the Brotli library installed:

```bash
pip install brotli
```

You can also run the dependency installer to fix this:

```bash
python install_dependencies.py
```

### API Key Issues

If you encounter authentication errors, check that your API keys are correctly set in the `.env` file.

### Connection Issues

If search results fail to load, check your internet connection and whether the Google Custom Search API is working properly.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
