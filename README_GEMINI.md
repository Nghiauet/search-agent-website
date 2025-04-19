# Gemini Terminal Agent

This is a terminal-based agent using Google's Gemini model with integrated search capabilities.

## Features

- Uses Google Gemini model instead of OpenAI's models
- Integrates with search engine tools via MCP (Machine Communication Protocol)
- Interactive terminal interface for querying the agent
- Conversation history management
- Search web for information using Google Custom Search API

## Prerequisites

- Python 3.9+
- Google Gemini API key
- Google Custom Search Engine ID and API key

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure your `.env` file is properly configured with the following variables:

```
# API Keys
GOOGLE_GENAI_API_KEY=your_gemini_api_key
DEFAULT_MODEL=gemini-2.5-flash-preview-04-17  # or other Gemini model

# Search Engine Settings
SEARCH_ENGINE_API_KEY=your_google_api_key
SEARCH_ENGINE_CSE_ID=your_custom_search_engine_id
```

3. Make the run script executable:

```bash
python make_executable.py
```

## Running the Agent

You can run the agent in two ways:

### Method 1: Using the shell script

```bash
./run_agent.sh
```

This script will:
- Check if Python is installed
- Create a virtual environment if it doesn't exist
- Install dependencies
- Run the agent

### Method 2: Direct Python execution

```bash
python gemini_agent.py
```

## Usage

Once the agent is running, you can interact with it via the terminal:

- Type your query and press Enter to send it to the agent
- Type `help` to see available tools and commands
- Type `clear` to clear the conversation history
- Type `exit`, `quit`, or `q` to exit the program

## Example Queries

Here are some example queries you can try:

1. General knowledge questions:
   - "What is quantum computing?"
   - "Explain the process of photosynthesis."

2. Using search capabilities:
   - "Find the latest news about artificial intelligence."
   - "Search for information about climate change solutions."

3. Advanced search with domain filtering:
   - "Search for Python tutorials on python.org and stackoverflow.com."
   - "Find research papers about machine learning but exclude Wikipedia."

## Troubleshooting

If you encounter any issues:

1. Check that your API keys are correctly set in the `.env` file.
2. Ensure all dependencies are installed.
3. Check the logs for any error messages.
4. Verify that you're using a valid Gemini model name in the `.env` file.

## Customization

You can customize the agent by modifying:

- The Gemini model parameters in `gemini_agent.py`
- The search functionality in `search_server/search_mcp_server.py`
- The search utilities in `utils/search_utils.py`
