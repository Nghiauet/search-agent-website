from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

@asynccontextmanager
async def make_graph():
    """
    Create and configure a LangGraph agent with search capabilities.
    This function is used as the entrypoint for the LangGraph API server.
    """
    # Choose the model based on available API keys
    if os.getenv("GOOGLE_GENAI_API_KEY"):
        model = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
    else:
        model = ChatOpenAI(model="gpt-4o")
    
    # Configure the search server
    search_server_config = {
        "command": "python",
        "args": ["-m", "search_server.search_mcp_server", "--transport", "stdio"],
        "transport": "stdio",
    }
    
    # Connect to the MCP server
    async with MultiServerMCPClient(
        {
            "search_engine": search_server_config
        }
    ) as client:
        # Get tools from the MCP server
        tools = client.get_tools()
        
        # Create the agent with MCP tools
        agent = create_react_agent(model, tools)
        
        # Yield the configured agent
        yield agent
