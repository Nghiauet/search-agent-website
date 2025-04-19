# MCP Search Agent

This project demonstrates how to create an agent that uses the Model Context Protocol (MCP) to integrate a search engine with large language models (LLMs) via LangChain and LangGraph.

## Features

- 🔍 Search Engine MCP Server: Implements the MCP protocol for web search capabilities
- 🤖 Agent Integration: Connect the search tools to LangChain and LangGraph agents
- 🧩 Multiple LLM Support: Works with OpenAI and Google Gemini models
- 📊 Flexible Transport: Supports various transport methods (stdio, SSE, WebSocket)

## Project Structure

```
mcp-agent/
├── search_server/              # Search engine MCP server
│   └── search_mcp_server.py    # MCP server implementation 
├── client/                     # Client implementations
│   ├── agent.py                # LangChain agent with search tools
│   └── graph.py                # LangGraph implementation
├── utils/                      # Utilities
│   ├── config.py               # Configuration management
│   └── search_utils.py         # Search engine utilities
├── example.py                  # Example script
├── requirements.txt            # Project dependencies
├── .env.example                # Environment variable template
└── README.md                   # Project documentation
```

## Installation

1. Clone the repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example` and add your API keys:

```bash
cp .env.example .env
# Edit the .env file with your API keys
```

## Usage

### Running the Search MCP Server

You can run the search MCP server directly:

```bash
python -m search_server.search_mcp_server --transport stdio
```

Supported transport options:
- `stdio`: Standard input/output (default)
- `sse`: Server-Sent Events over HTTP
- `ws`: WebSocket

For HTTP-based transports, you can specify a port:

```bash
python -m search_server.search_mcp_server --transport sse --port 8000
```

### Using the Agent

Run the example script:

```bash
python example.py
```

This will:
1. Start the search MCP server
2. Connect the agent to the server
3. Run sample queries through the agent

### Using with LangGraph

To use with LangGraph API server:

```bash
langchain serve
```

This will:
1. Load the graph configuration from langgraph.json
2. Start the LangGraph API server
3. Make the agent available at the API endpoint

## Customization

### Adding New MCP Servers

You can add additional MCP servers by:

1. Creating a new server module in the `search_server` directory
2. Adding the server configuration to the `MultiServerMCPClient` in `client/agent.py`

### Using Different LLMs

The project supports OpenAI and Google Gemini models. You can configure which model to use:

```python
agent = await create_agent_with_search(
    model_provider="openai",  # or "google"
    model_name="gpt-4o",      # or "gemini-1.5-pro"
    search_server_transport="stdio"
)
```

## License

MIT
