document.addEventListener('DOMContentLoaded', function() {
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
});