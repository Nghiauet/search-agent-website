"""
Configuration for the terminal agent.
"""
from mcp import StdioServerParameters
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from utils.config import settings
from utils.logging import logger

def create_model(model_name=None, temperature=0.7, api_key=None):
    """
    Create a Gemini model instance.
    
    Args:
        model_name: Name of the model to use (defaults to settings.DEFAULT_MODEL)
        temperature: Model temperature (0.0 to 1.0)
        api_key: Google API key (defaults to settings.GOOGLE_GENAI_API_KEY)
        
    Returns:
        ChatGoogleGenerativeAI: Configured model instance
    """
    model_name = model_name or settings.DEFAULT_MODEL
    api_key = api_key or settings.GOOGLE_GENAI_API_KEY
    
    if not api_key:
        raise ValueError("GOOGLE_GENAI_API_KEY must be set in environment variables or .env file")
    
    logger.info(f"Creating Gemini model: {model_name}")
    
    # Configure the Gemini model
    model = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        convert_system_message_to_human=True,
        # Safety settings with proper enum values
        safety_settings={
            4: 2  # HARASSMENT: BLOCK_MEDIUM_AND_ABOVE (using enum values)
        }
    )
    
    return model

def create_server_params(server_script="search.server"):
    """
    Create MCP server parameters.
    
    Args:
        server_script: Module path to the server script
        
    Returns:
        StdioServerParameters: Configured server parameters
    """
    return StdioServerParameters(
        command="python",
        args=["-m", server_script, "--transport", "stdio"],
    )

def format_messages(history, user_input):
    """
    Format message history for the model.
    
    Args:
        history: List of conversation history messages
        user_input: Current user input
        
    Returns:
        list: Formatted messages for the model
    """
    if not history:
        # First message in conversation
        return [HumanMessage(content=user_input)]
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
        
        return messages

def get_help_text(tools):
    """
    Generate help text for available tools and commands.
    
    Args:
        tools: List of available tools
        
    Returns:
        str: Formatted help text
    """
    help_text = "\n🔍 Available Tools:"
    for tool in tools:
        help_text += f"\n  - {tool.name}: {tool.description}"
    
    help_text += "\n\n⌨️ Terminal Commands:"
    help_text += "\n  - help: Show this help message"
    help_text += "\n  - clear: Clear conversation history"
    help_text += "\n  - exit/quit/q: Exit the program"
    
    return help_text
