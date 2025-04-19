"""
Terminal-based agent using Google Gemini model with search capabilities.
"""
import asyncio
import re
from typing import List, Dict, Any, Optional
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

from utils.logging import logger
from utils.config import settings
from agent.config import create_model, create_server_params, format_messages, get_help_text

class GeminiTerminalAgent:
    """Terminal-based agent using Google Gemini model with search capabilities."""
    
    def __init__(self, model_name=None, api_key=None, server_module="search.server"):
        """
        Initialize the Gemini Agent.
        
        Args:
            model_name: Name of the Gemini model to use
            api_key: Google API key for authentication
            server_module: Module path to the search server
        """
        self.model_name = model_name or settings.DEFAULT_MODEL
        self.api_key = api_key or settings.GOOGLE_GENAI_API_KEY or settings.GOOGLE_API_KEY
        
        # Create the model
        self.model = create_model(self.model_name, api_key=self.api_key)
        
        # Configure the server connection
        self.server_params = create_server_params(server_module)
        
        # Initialize other fields
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
                
                # Process special commands
                if await self._process_commands(user_input, history):
                    continue
                
                # Process regular query
                await self._process_query(user_input, history)
                
            except KeyboardInterrupt:
                print("\nInterrupted by user. Exiting...")
                break
            except Exception as e:
                self._handle_error(e)
    
    async def _process_commands(self, user_input, history):
        """
        Process special commands.
        
        Args:
            user_input: User input string
            history: Conversation history
            
        Returns:
            bool: True if a command was processed, False otherwise
        """
        # Check for exit commands
        if user_input.lower() in ("exit", "quit", "q"):
            print("Exiting Gemini Terminal Agent. Goodbye!")
            return True
        
        # Check for help command
        if user_input.lower() == "help":
            print(get_help_text(self.tools))
            return True
        
        # Check for clear command
        if user_input.lower() == "clear":
            history.clear()
            print("Conversation history cleared.")
            return True
        
        # No command was processed
        return False
    
    async def _process_query(self, user_input, history):
        """
        Process a regular user query.
        
        Args:
            user_input: User input string
            history: Conversation history
        """
        # Prepare for processing
        print("\nThinking...\n")
        logger.info(f"Processing user query: {user_input}")
        logger.debug(f"Using model: {self.model_name} with {len(self.tools)} tools")
        
        if history:
            logger.debug(f"Chat history contains {len(history)} messages")
        else:
            logger.debug("This is a new conversation without history")
        
        # Format messages for the model
        messages = format_messages(history, user_input)
        
        # Invoke the agent
        start_time = asyncio.get_event_loop().time()
        try:
            response = await self.agent.ainvoke({"messages": messages})
        except Exception as e:
            logger.warning(f"Error with standard message format: {str(e)}")
            # Fall back to an alternative format if needed
            formatted_messages = [{"role": "user" if i % 2 == 0 else "assistant", 
                                 "content": msg.content} for i, msg in enumerate(messages)]
            response = await self.agent.ainvoke({"messages": formatted_messages})
        
        end_time = asyncio.get_event_loop().time()
        
        # Extract and display the response
        assistant_message = self._extract_response(response)
        print(f"\n{assistant_message}")
        print(f"\n(Response time: {end_time - start_time:.2f}s)")
        
        # Log search information if applicable
        self._log_search_info(response)
        
        # Update conversation history
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": assistant_message})
        
        # Log completion
        logger.info(f"Agent responded in {end_time - start_time:.2f}s")
        logger.debug(f"Response: {assistant_message[:500]}..." if len(assistant_message) > 500 
                   else f"Response: {assistant_message}")
    
    def _extract_response(self, response):
        """
        Extract the assistant's response from the response object.
        
        Args:
            response: Response object from the agent
            
        Returns:
            str: Extracted assistant message
        """
        try:
            # Handle dict response with messages
            if isinstance(response, dict) and 'messages' in response:
                messages_list = response['messages']
                if isinstance(messages_list, list) and len(messages_list) > 0:
                    last_message = messages_list[-1]
                    if hasattr(last_message, 'content'):
                        return last_message.content
                    else:
                        return str(last_message)
            
            # Handle AIMessage response
            elif hasattr(response, 'content'):
                return response.content
            
            # Fallback for unknown response format
            return str(response)
            
        except Exception as e:
            logger.error(f"Error extracting response: {str(e)}")
            return f"Error processing response: {str(e)}"
    
    def _log_search_info(self, response):
        """
        Log information about search operations.
        
        Args:
            response: Response object from the agent
        """
        # Skip if response doesn't have the expected format
        if not isinstance(response, dict) or 'messages' not in response:
            return
        
        messages_list = response['messages']
        search_performed = False
        
        # Check for tool usage and search results
        for msg in messages_list:
            # Log tool calls
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    logger.info(f"🔍 SEARCH REQUEST: Agent is using tool '{tool_call['name']}'")
                    if 'args' in tool_call and 'query' in tool_call['args']:
                        logger.info(f"🔍 SEARCH QUERY: '{tool_call['args']['query']}'")
            
            # Log search tool responses
            if hasattr(msg, 'name') and msg.name in ['search', 'advanced_search'] and hasattr(msg, 'content'):
                search_performed = True
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
        
        # Log a search summary if search was performed
        if search_performed:
            logger.info("📋 SEARCH SUMMARY: Search was performed to answer this query")
    
    def _handle_error(self, error):
        """
        Handle and log errors.
        
        Args:
            error: Exception object
        """
        logger.exception(f"Error processing query: {str(error)}")
        
        # If there's a response variable, log details about it for debugging
        if 'response' in locals():
            logger.error(f"Response type: {type(response)}")
            logger.error(f"Response content: {response}")
        
        # Display error message to user
        print(f"\nAn error occurred: {str(error)}")
        print("Please try again with a different query.")


async def run_agent():
    """Run the Gemini Terminal Agent."""
    # Initialize and run the agent
    agent = GeminiTerminalAgent()
    await agent.initialize()
