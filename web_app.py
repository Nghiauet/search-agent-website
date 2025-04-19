#!/usr/bin/env python3
"""
Web-based interface for the MCP Agent.
"""
import asyncio
import os
import sys
import json
from aiohttp import web

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logging import setup_logging, logger
from utils.config import settings
from agent.config import create_model, create_server_params
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

# Setup logging
setup_logging()

# Create the model
model_name = settings.DEFAULT_MODEL
api_key = settings.GOOGLE_GENAI_API_KEY or settings.GOOGLE_API_KEY
model = create_model(model_name, api_key=api_key)

# Configure the server connection
server_params = create_server_params("search.server")

# Initialize other fields
agent = None
tools = []
history = {}

# Create the web app
app = web.Application()
routes = web.RouteTableDef()

# Serve static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# Create static directory if it doesn't exist
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Create HTML file
HTML_PATH = os.path.join(static_dir, 'index.html')
with open(HTML_PATH, 'w') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Agent Chat</title>
    <link rel="stylesheet" href="/static/style.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
    <div class="chat-container">
        <header>
            <h1>🤖 MCP Agent Chat 🤖</h1>
        </header>
        <div class="chat-box" id="chatBox"></div>
        <div class="input-area">
            <textarea id="userInput" placeholder="Type your message here..."></textarea>
            <div class="button-container">
                <button id="sendButton">Send</button>
                <button id="clearButton">Clear Chat</button>
                <button id="helpButton">Help</button>
            </div>
        </div>
        <div id="statusBar">Ready</div>
    </div>
    <script src="/static/script.js"></script>
</body>
</html>""")

# Create CSS file
CSS_PATH = os.path.join(static_dir, 'style.css')
with open(CSS_PATH, 'w') as f:
    f.write("""* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

body {
    background-color: #f5f7fb;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.chat-container {
    width: 90%;
    max-width: 1000px;
    height: 90vh;
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

header {
    background-color: #4a6ee0;
    color: white;
    padding: 15px 20px;
    text-align: center;
}

.chat-box {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.message {
    max-width: 80%;
    padding: 12px 15px;
    border-radius: 10px;
    line-height: 1.5;
    position: relative;
}

.user-message {
    align-self: flex-end;
    background-color: #4a6ee0;
    color: white;
    border-bottom-right-radius: 0;
}

.bot-message {
    align-self: flex-start;
    background-color: #f0f2f5;
    color: #333;
    border-bottom-left-radius: 0;
}

.thinking {
    align-self: center;
    background-color: transparent;
    color: #666;
    font-style: italic;
    padding: 5px;
}

.input-area {
    padding: 15px;
    border-top: 1px solid #eee;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

textarea {
    width: 100%;
    padding: 12px 15px;
    border: 1px solid #ddd;
    border-radius: 8px;
    resize: none;
    height: 80px;
    font-size: 16px;
}

.button-container {
    display: flex;
    gap: 10px;
}

button {
    padding: 10px 20px;
    background-color: #4a6ee0;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #3558c8;
}

#clearButton {
    background-color: #e74c3c;
}

#clearButton:hover {
    background-color: #c0392b;
}

#helpButton {
    background-color: #27ae60;
}

#helpButton:hover {
    background-color: #219653;
}

#statusBar {
    padding: 8px 15px;
    background-color: #f5f5f5;
    color: #666;
    font-size: 14px;
    border-top: 1px solid #eee;
}

/* Markdown styling */
.bot-message p {
    margin-bottom: 10px;
}

.bot-message ul, .bot-message ol {
    margin-left: 20px;
    margin-bottom: 10px;
}

.bot-message code {
    background: #f0f0f0;
    padding: 2px 4px;
    border-radius: 4px;
    font-family: monospace;
}

.bot-message pre {
    background: #f8f8f8;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    margin-bottom: 10px;
}

.bot-message pre code {
    background: transparent;
    padding: 0;
}

/* Responsive styles */
@media (max-width: 768px) {
    .chat-container {
        width: 95%;
        height: 95vh;
    }
    
    .message {
        max-width: 90%;
    }
}""")

# Create JavaScript file
JS_PATH = os.path.join(static_dir, 'script.js')
with open(JS_PATH, 'w') as f:
    f.write("""document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chatBox');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const clearButton = document.getElementById('clearButton');
    const helpButton = document.getElementById('helpButton');
    const statusBar = document.getElementById('statusBar');
    
    // Session ID to track conversation history
    const sessionId = Date.now().toString();
    
    // Add event listeners
    sendButton.addEventListener('click', sendMessage);
    clearButton.addEventListener('click', clearChat);
    helpButton.addEventListener('click', showHelp);
    
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Function to send message
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        userInput.value = '';
        
        // Show thinking message
        const thinkingId = 'thinking-' + Date.now();
        addThinkingMessage(thinkingId);
        
        // Update status
        statusBar.textContent = 'Agent is thinking...';
        
        // Send message to server
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove thinking message
            const thinkingElement = document.getElementById(thinkingId);
            if (thinkingElement) {
                thinkingElement.remove();
            }
            
            // Add agent response
            addMessage(data.response, 'bot');
            
            // Update status
            statusBar.textContent = `Response time: ${data.response_time.toFixed(2)}s`;
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Remove thinking message
            const thinkingElement = document.getElementById(thinkingId);
            if (thinkingElement) {
                thinkingElement.remove();
            }
            
            // Add error message
            addMessage('An error occurred. Please try again.', 'bot');
            
            // Update status
            statusBar.textContent = 'Error: Failed to get response';
        });
    }
    
    // Function to add message to chat
    function addMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender + '-message');
        
        // Parse markdown for bot messages
        if (sender === 'bot') {
            messageElement.innerHTML = marked.parse(message);
        } else {
            messageElement.textContent = message;
        }
        
        chatBox.appendChild(messageElement);
        
        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    // Function to add thinking message
    function addThinkingMessage(id) {
        const thinkingElement = document.createElement('div');
        thinkingElement.id = id;
        thinkingElement.classList.add('message', 'thinking');
        thinkingElement.textContent = 'Thinking...';
        chatBox.appendChild(thinkingElement);
        
        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    // Function to clear chat
    function clearChat() {
        // Clear chat UI
        chatBox.innerHTML = '';
        
        // Clear chat history on server
        fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            statusBar.textContent = data.message;
            
            // Add system message
            addMessage('Chat history cleared.', 'bot');
        })
        .catch(error => {
            console.error('Error:', error);
            statusBar.textContent = 'Error: Failed to clear chat history';
        });
    }
    
    // Function to show help
    function showHelp() {
        fetch('/api/help')
        .then(response => response.json())
        .then(data => {
            addMessage(data.help_text, 'bot');
            statusBar.textContent = 'Help information displayed';
        })
        .catch(error => {
            console.error('Error:', error);
            statusBar.textContent = 'Error: Failed to get help information';
        });
    }
    
    // Add welcome message
    addMessage('Welcome to MCP Agent! How can I assist you today?', 'bot');
});""")

# Initialize MCP agent
async def initialize_agent():
    global agent, tools
    
    # Connect to the MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # Get the available tools
            tools = await load_mcp_tools(session)
            
            # Print the available tools
            logger.info(f"Available tools: {[tool.name for tool in tools]}")
            
            # Create the ReAct agent with Gemini model
            agent = create_react_agent(model, tools)
            
            logger.info("Agent initialized successfully")
            return True


@routes.post('/api/chat')
async def handle_chat(request):
    try:
        # Parse request data
        data = await request.json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        # Initialize history for new sessions
        if session_id not in history:
            history[session_id] = []
        
        # Check for special commands
        if user_message.lower() in ("exit", "quit", "q"):
            return web.json_response({
                "response": "Exit command received. You can close the browser window or tab to end the session.",
                "response_time": 0.1
            })
            
        logger.info(f"Processing user query: {user_message}")
        
        # Format messages for the model
        from agent.config import format_messages
        messages = format_messages(history[session_id], user_message)
        
        # Invoke the agent
        start_time = asyncio.get_event_loop().time()
        try:
            response = await agent.ainvoke({"messages": messages})
        except Exception as e:
            logger.warning(f"Error with standard message format: {str(e)}")
            # Fall back to an alternative format if needed
            formatted_messages = [{"role": "user" if i % 2 == 0 else "assistant", 
                                 "content": msg.content} for i, msg in enumerate(messages)]
            response = await agent.ainvoke({"messages": formatted_messages})
        
        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time
        
        # Extract the assistant's response
        assistant_message = extract_response(response)
        
        # Update conversation history
        history[session_id].append({"role": "user", "content": user_message})
        history[session_id].append({"role": "assistant", "content": assistant_message})
        
        # Log completion
        logger.info(f"Agent responded in {response_time:.2f}s")
        
        return web.json_response({
            "response": assistant_message,
            "response_time": response_time
        })
        
    except Exception as e:
        logger.exception(f"Error handling chat request: {str(e)}")
        return web.json_response({
            "response": f"An error occurred: {str(e)}",
            "response_time": 0
        }, status=500)


@routes.post('/api/clear')
async def handle_clear(request):
    try:
        data = await request.json()
        session_id = data.get('session_id', 'default')
        
        # Clear session history
        if session_id in history:
            history[session_id] = []
            
        return web.json_response({
            "message": "Chat history cleared successfully"
        })
        
    except Exception as e:
        logger.exception(f"Error clearing chat history: {str(e)}")
        return web.json_response({
            "message": f"Error clearing chat history: {str(e)}"
        }, status=500)


@routes.get('/api/help')
async def handle_help(request):
    try:
        from agent.config import get_help_text
        help_text = get_help_text(tools)
        
        return web.json_response({
            "help_text": help_text
        })
        
    except Exception as e:
        logger.exception(f"Error getting help text: {str(e)}")
        return web.json_response({
            "help_text": f"Error retrieving help information: {str(e)}"
        }, status=500)


def extract_response(response):
    """Extract the assistant's response from the response object."""
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


async def setup_environment():
    """Setup environment variables for API keys if needed."""
    # If GOOGLE_GENAI_API_KEY is in settings but not in environment, set it
    if settings.GOOGLE_GENAI_API_KEY and "GOOGLE_GENAI_API_KEY" not in os.environ:
        os.environ["GOOGLE_GENAI_API_KEY"] = settings.GOOGLE_GENAI_API_KEY
    
    # Ensure Google API key is set for authentication
    if settings.GOOGLE_GENAI_API_KEY and "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_GENAI_API_KEY


async def start_background_tasks(app):
    # Setup environment variables
    await setup_environment()
    
    # Initialize agent
    await initialize_agent()


async def cleanup_background_tasks(app):
    # Clean up resources
    pass


# Setup routes
app.add_routes(routes)
app.add_routes([web.static('/static', static_dir)])
app.router.add_get('/', lambda request: web.HTTPFound('/static/index.html'))

# Setup background tasks
app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)


if __name__ == "__main__":
    port = settings.MCP_SERVER_PORT + 1  # Use a different port than the search server
    print(f"\n🌐 Starting MCP Web Agent on http://localhost:{port}")
    print("Press Ctrl+C to exit")
    web.run_app(app, port=port)
