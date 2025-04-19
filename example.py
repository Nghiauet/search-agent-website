import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def main():
    """Example of using the search MCP server directly."""
    # Configure the language model
    model = ChatOpenAI(model="gpt-4o")
    
    # Configure the server parameters for stdio connection
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "search_server.search_mcp_server", "--transport", "stdio"],
    )
    
    # Connect to the MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # Get the available tools
            tools = await load_mcp_tools(session)
            
            # Print the available tools
            print(f"Available tools: {[tool.name for tool in tools]}")
            
            # Create the agent
            agent = create_react_agent(model, tools)
            
            # Run a test query
            query = "What is the latest news about artificial intelligence?"
            print(f"\nQuery: {query}")
            
            agent_response = await agent.ainvoke({"messages": query})
            print(f"\nResponse: {agent_response}")

if __name__ == "__main__":
    # Make sure Python can find the modules
    sys.path.append(".")
    
    # Run the example
    asyncio.run(main())
