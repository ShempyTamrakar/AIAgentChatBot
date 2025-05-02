// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-btn');
const clearButton = document.getElementById('clear-chat');
const welcomeMessage = document.querySelector('.welcome-message');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Scroll to bottom of chat
    scrollToBottom();
    
    // Hide welcome message if chat history exists
    if (chatMessages.children.length > 0) {
        welcomeMessage.style.display = 'none';
    }
});

// Event Listeners
sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
clearButton.addEventListener('click', clearChat);

// Send Message Function
function sendMessage() {
    const message = userInput.value.trim();
    
    if (message === '') return;
    
    // Hide welcome message when user starts chatting
    welcomeMessage.style.display = 'none';
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Clear input
    userInput.value = '';
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    // Send message to server
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        typingIndicator.remove();
        
        // Add bot response to chat
        addMessageToChat(data.response, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);
        typingIndicator.remove();
        addMessageToChat('Sorry, there was an error processing your request.', 'bot');
    });
}

// Add Message to Chat
function addMessageToChat(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    
    const contentElement = document.createElement('div');
    contentElement.classList.add('message-content');
    
    if (sender === 'bot') {
        // Process message text for better formatting
        message = message.replace(/\n/g, '<br>');
        message = message.replace(/•/g, '&bull;');
        
        // Format lists for better appearance
        if (message.includes('<br>&bull;')) {
            message = message.replace(/<br>&bull;/g, '<br><span class="bullet">&bull;</span>');
        }
        
        // Style tables if present
        if (message.includes('|')) {
            const lines = message.split('<br>');
            let formattedLines = [];
            let inTable = false;
            
            for (const line of lines) {
                if (line.includes('|') && line.includes('-+-')) {
                    // This is a table separator line
                    formattedLines.push('<hr class="table-separator">');
                    inTable = true;
                } else if (line.includes('|')) {
                    // This is a table row
                    const cells = line.split('|').map(cell => cell.trim());
                    let formattedRow = inTable ? '<div class="table-row">' : '<div class="table-header">';
                    
                    for (const cell of cells) {
                        if (cell) {
                            formattedRow += `<div class="table-cell">${cell}</div>`;
                        }
                    }
                    
                    formattedRow += '</div>';
                    formattedLines.push(formattedRow);
                    
                    if (!inTable) inTable = true;
                } else {
                    // Regular text
                    inTable = false;
                    formattedLines.push(line);
                }
            }
            
            message = formattedLines.join('<br>');
        }
    }
    
    contentElement.innerHTML = message;
    messageElement.appendChild(contentElement);
    
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

// Add Typing Indicator
function addTypingIndicator() {
    const typingElement = document.createElement('div');
    typingElement.classList.add('message', 'bot-message', 'typing-indicator');
    
    const contentElement = document.createElement('div');
    contentElement.classList.add('message-content');
    contentElement.innerHTML = '<span></span><span></span><span></span>';
    
    typingElement.appendChild(contentElement);
    chatMessages.appendChild(typingElement);
    scrollToBottom();
    
    return typingElement;
}

// Scroll to Bottom of Chat
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Clear Chat
function clearChat() {
    fetch('/clear', {
        method: 'POST',
    })
    .then(() => {
        // Clear chat messages
        chatMessages.innerHTML = '';
        
        // Show welcome message again
        welcomeMessage.style.display = 'block';
    })
    .catch(error => {
        console.error('Error clearing chat:', error);
    });
}