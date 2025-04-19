import asyncio
import sys
import os
import re
from typing import List, Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
from loguru import logger

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.config import settings

# Configure logging
logger.remove()
# Console logger
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
# File logger for more detailed logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent_logs.log')
logger.add(
    log_file,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="10 MB",  # Rotate log files when they reach 10MB
    retention=3  # Keep only the 3 most recent log files
)

# Load environment variables
load_dotenv()

# Ensure API keys are properly set in environment
def setup_environment():
    """Setup environment variables for API keys if needed."""
    # If GOOGLE_GENAI_API_KEY is in settings but not in environment, set it
    if settings.GOOGLE_GENAI_API_KEY and "GOOGLE_GENAI_API_KEY" not in os.environ:
        os.environ["GOOGLE_GENAI_API_KEY"] = settings.GOOGLE_GENAI_API_KEY
        logger.info("Set GOOGLE_GENAI_API_KEY from settings")
    
    # Ensure Google API key is set for authentication
    if settings.GOOGLE_GENAI_API_KEY and "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_GENAI_API_KEY
        logger.info("Set GOOGLE_API_KEY from GOOGLE_GENAI_API_KEY settings")

# Initialize environment
setup_environment()

class GeminiTerminalAgent:
    """Terminal-based agent using Google Gemini model with search capabilities."""
    
    def __init__(self):
        """Initialize the Gemini Agent."""
        self.model_name = settings.DEFAULT_MODEL
        self.api_key = settings.GOOGLE_GENAI_API_KEY or os.getenv("GOOGLE_GENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_GENAI_API_KEY must be set in environment variables or .env file")
        
        logger.info(f"Initializing Gemini agent with model: {self.model_name}")
        
        # Configure the Gemini model
        self.model = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
            # Safety settings with proper enum values according to Google API specs
            safety_settings={
                4: 2  # HARASSMENT: BLOCK_MEDIUM_AND_ABOVE (using enum values)
            }
        )
        
        self.server_params = StdioServerParameters(
            command="python",
            args=["-m", "search_server.search_mcp_server", "--transport", "stdio"],
        )
        
        self.agent = None
        self.tools = []
    
    async def initialize(self):
        """Initialize the agent with MCP tools."""
        # Connect to the MCP server
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                
                # Get the available tools
                self.tools = await load_mcp_tools(session)
                
                # Print the available tools
                logger.info(f"Available tools: {[tool.name for tool in self.tools]}")
                
                # Create the ReAct agent with Gemini model
                self.agent = create_react_agent(self.model, self.tools)
                
                # Start the interactive terminal loop
                await self.run_terminal()
    
    async def run_terminal(self):
        """Run the interactive terminal interface."""
        print("\n🤖 Gemini Terminal Agent 🤖")
        print("Type 'exit', 'quit', or 'q' to exit the program.")
        print("Type 'help' to see available tools and commands.")
        print("-" * 50)
        
        history = []
        
        while True:
            try:
                # Get user input
                user_input = input("\n>>> ")
                
                # Check for exit commands
                if user_input.lower() in ("exit", "quit", "q"):
                    print("Exiting Gemini Terminal Agent. Goodbye!")
                    break
                
                # Check for help command
                if user_input.lower() == "help":
                    self._print_help()
                    continue
                
                # Check for clear command
                if user_input.lower() == "clear":
                    history = []
                    print("Conversation history cleared.")
                    continue
                
                # Process the query through the agent
                print("\nThinking...\n")
                logger.info(f"Processing user query: {user_input}")
                logger.info(f"Query will be processed using model: {self.model_name}")
                logger.debug(f"Agent has {len(self.tools)} tools available: {[tool.name for tool in self.tools]}")
                
                # Show chat history for context
                if history:
                    logger.debug(f"Chat history contains {len(history)} messages")
                else:
                    logger.debug("This is a new conversation without history")
                
                # Prepare the messages format for the agent
                
                if not history:
                    # First message in conversation as LangChain message object
                    messages = [HumanMessage(content=user_input)]
                else:
                    # Convert history to LangChain message objects
                    messages = []
                    for msg in history:
                        if msg["role"] == "user":
                            messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            messages.append(AIMessage(content=msg["content"]))
                    
                    # Add the current user message
                    messages.append(HumanMessage(content=user_input))
                
                # Invoke the agent
                start_time = asyncio.get_event_loop().time()
                try:
                    # Try with the LangChain message objects directly
                    logger.debug(f"Invoking agent with messages: {messages}")
                    response = await self.agent.ainvoke({"messages": messages})
                    logger.debug(f"Raw agent response: {response}")
                except Exception as invoke_error:
                    logger.warning(f"Error with message objects: {str(invoke_error)}")
                    # Fall back to the older format if needed
                    formatted_messages = [{"role": "user" if isinstance(msg, HumanMessage) else "assistant", 
                                          "content": msg.content} for msg in messages]
                    response = await self.agent.ainvoke({"messages": formatted_messages})
                end_time = asyncio.get_event_loop().time()
                
                # Extract the assistant's response from the response object
                # Looking at the error, it seems the response is a dict with a 'messages' key that contains a list
                # where the last message is an AIMessage object
                if isinstance(response, dict) and 'messages' in response:
                    messages_list = response['messages']
                    if isinstance(messages_list, list) and len(messages_list) > 0:
                        last_message = messages_list[-1]
                        if hasattr(last_message, 'content'):
                            assistant_message = last_message.content
                            
                            # Log detailed information about tool usage and search results
                            for i, msg in enumerate(messages_list):
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    for tool_call in msg.tool_calls:
                                        logger.info(f"🔍 SEARCH REQUEST: Agent is using tool '{tool_call['name']}'")
                                        if 'args' in tool_call and 'query' in tool_call['args']:
                                            logger.info(f"🔍 SEARCH QUERY: '{tool_call['args']['query']}'")
                                            
                                if hasattr(msg, 'name') and msg.name:
                                    if msg.name in ['search', 'advanced_search'] and hasattr(msg, 'content'):
                                        # This is a search result
                                        logger.info(f"📊 SEARCH RESULTS RECEIVED from {msg.name}")
                                        
                                        # Parse and log sources from the content
                                        if hasattr(msg, 'content') and msg.content:
                                            content = msg.content
                                            # Extract and log sources
                                            sources = re.findall(r'SOURCE \d+: (.+?)\nURL: (.+?)\n', content)
                                            if sources:
                                                logger.info(f"📚 Found {len(sources)} sources in search results:")
                                                for j, (title, url) in enumerate(sources, 1):
                                                    logger.info(f"  Source {j}: {title} - {url}")
                                            else:
                                                logger.info("No specific sources found in search results")
                                                
                                            # Log a preview of the search results content
                                            logger.debug(f"Full search results: {content[:1000]}..." if len(content) > 1000 else f"Full search results: {content}")
                                    else:
                                        # Other tool response
                                        logger.info(f"Tool response from {msg.name}: {msg.content[:200]}..." 
                                                  if len(msg.content) > 200 else f"Tool response from {msg.name}: {msg.content}")
                        else:
                            assistant_message = str(last_message)
                    else:
                        assistant_message = "No response generated."
                elif hasattr(response, 'content'):
                    # Direct AIMessage object
                    assistant_message = response.content
                else:
                    # Fallback
                    logger.warning(f"Unexpected response format: {type(response)}")
                    assistant_message = str(response)
                
                # Display the response
                print(f"\n{assistant_message}")
                print(f"\n(Response time: {end_time - start_time:.2f}s)")
                
                # Log the final response and timing
                logger.info(f"Agent responded in {end_time - start_time:.2f}s")
                logger.debug(f"Final response content: {assistant_message[:500]}..." 
                          if len(assistant_message) > 500 else f"Final response content: {assistant_message}")
                
                # Log a search summary if search was performed
                search_performed = False
                for msg in messages_list if isinstance(response, dict) and 'messages' in response else []:
                    if hasattr(msg, 'name') and msg.name in ['search', 'advanced_search']:
                        search_performed = True
                        break
                
                if search_performed:
                    logger.info("📋 SEARCH SUMMARY: Search was performed to answer this query")
                    logger.info(f"🕒 Total interaction time: {end_time - start_time:.2f}s")
                    logger.info(f"🤖 Final answer length: {len(assistant_message)} characters")
                else:
                    logger.info("No search was performed to answer this query")
                
                # Update history
                history.append({"role": "user", "content": user_input})
                history.append({"role": "assistant", "content": assistant_message})
                
                # Debug the response format for future reference
                logger.debug(f"Response type: {type(response)}")
                if isinstance(response, dict):
                    logger.debug(f"Response keys: {list(response.keys())}")
                    if 'messages' in response:
                        logger.debug(f"Messages type: {type(response['messages'])}")
                        if isinstance(response['messages'], list) and len(response['messages']) > 0:
                            logger.debug(f"Last message type: {type(response['messages'][-1])}")
                
            except KeyboardInterrupt:
                print("\nInterrupted by user. Exiting...")
                break
            except Exception as e:
                logger.exception(f"Error processing query: {str(e)}")
                
                # Log more details about the response for debugging
                if 'response' in locals():
                    logger.error(f"Response type: {type(response)}")
                    logger.error(f"Response content: {response}")
                    
                    # Try to recursively inspect the response structure
                    if hasattr(response, "__dict__"):
                        logger.error(f"Response attributes: {response.__dict__}")
                    elif isinstance(response, dict):
                        logger.error(f"Response keys: {response.keys()}")
                        # Inspect messages key if present
                        if 'messages' in response:
                            messages = response['messages']
                            logger.error(f"Messages type: {type(messages)}")
                            if isinstance(messages, list):
                                logger.error(f"Messages count: {len(messages)}")
                                for i, msg in enumerate(messages):
                                    logger.error(f"Message {i} type: {type(msg)}")
                                    if hasattr(msg, '__dict__'):
                                        logger.error(f"Message {i} attributes: {msg.__dict__}")
                
                print(f"\nAn error occurred: {str(e)}")
                print("Please try again with a different query.")
    
    def _print_help(self):
        """Print help information."""
        print("\n🔍 Available Tools:")
        for tool in self.tools:
            print(f"  - {tool.name}: {tool.description}")
        
        print("\n⌨️ Terminal Commands:")
        print("  - help: Show this help message")
        print("  - clear: Clear conversation history")
        print("  - exit/quit/q: Exit the program")

async def main():
    """Main function to run the Gemini Terminal Agent."""
    # Make sure Python can find the modules
    sys.path.append(".")
    
    # Initialize and run the agent
    agent = GeminiTerminalAgent()
    await agent.initialize()

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
