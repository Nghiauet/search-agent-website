import asyncio
import os
import sys
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import settings

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain.tools.base import BaseTool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

# Set up environment to load API keys
from dotenv import load_dotenv
load_dotenv()

# Ensure API keys are set in environment
def setup_environment():
    """Setup environment variables for API keys if needed."""
    # If GOOGLE_GENAI_API_KEY is in settings but not in environment, set it
    if settings.GOOGLE_GENAI_API_KEY and "GOOGLE_GENAI_API_KEY" not in os.environ:
        os.environ["GOOGLE_GENAI_API_KEY"] = settings.GOOGLE_GENAI_API_KEY
    
    # Ensure Google API key is set for authentication
    if settings.GOOGLE_GENAI_API_KEY and "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_GENAI_API_KEY

# Initialize environment
setup_environment()

async def create_agent_with_search(
    model_provider: str = "openai",
    model_name: str = "gpt-4o",
    search_server_transport: str = "stdio",
    search_server_port: int = 8000
):
    """
    Create an agent with search capabilities using MCP tools.
    
    Args:
        model_provider: The model provider to use (openai or google)
        model_name: The model name to use
        search_server_transport: The transport method for the search server
        search_server_port: The port for HTTP-based transports
        
    Returns:
        Agent instance that can be used to answer queries
    """
    # Configure the model
    if model_provider.lower() == "openai":
        model = ChatOpenAI(
            model=model_name,
            openai_api_key=settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        )
    elif model_provider.lower() == "google":
        model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GOOGLE_GENAI_API_KEY or os.getenv("GOOGLE_GENAI_API_KEY")
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")
    
    # Configure the search server connection
    search_server_config = {
        "command": "python",
        "args": ["-m", "search_server.search_mcp_server", "--transport", search_server_transport],
        "transport": search_server_transport,
    }
    
    # Use URL for HTTP-based transports
    if search_server_transport in ["sse", "ws"]:
        protocol = "http" if search_server_transport == "sse" else "ws"
        search_server_config = {
            "url": f"{protocol}://localhost:{search_server_port}/{search_server_transport}",
            "transport": search_server_transport,
        }
    
    # Connect to the MCP server(s)
    async with MultiServerMCPClient(
        {
            "search_engine": search_server_config
        }
    ) as client:
        # Get all tools from the MCP servers
        tools = client.get_tools()
        
        # Create the agent with the tools
        agent = create_react_agent(model, tools)
        
        # Return the configured agent
        return agent

async def run_agent_query(agent, query: str):
    """
    Run a query through the agent and return the response.
    
    Args:
        agent: The configured agent instance
        query: The query to process
        
    Returns:
        Agent response
    """
    try:
        response = await agent.ainvoke({"messages": query})
        return response
    except Exception as e:
        logger.exception(f"Error running agent query: {e}")
        return {"error": str(e)}

async def main():
    """
    Main function to demonstrate the agent usage.
    """
    # Create the agent
    agent = await create_agent_with_search(
        model_provider="openai",  # or "google"
        model_name="gpt-4o",      # or "gemini-1.5-pro"
        search_server_transport="stdio"
    )
    
    # Example queries
    queries = [
        "What is the current price of Bitcoin?",
        "What are the latest developments in AI?",
        "Tell me about the LangChain MCP adapters"
    ]
    
    for query in queries:
        print(f"\n\n{'='*80}\nQuery: {query}\n{'='*80}")
        response = await run_agent_query(agent, query)
        print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())
