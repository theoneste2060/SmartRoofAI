// AI Chat JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    
    // Focus on input
    if (messageInput) {
        messageInput.focus();
    }
    
    // Scroll to bottom of chat
    scrollToBottom();
});

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    messageInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response');
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add bot response
        addMessage(data.response, 'bot');
        
    } catch (error) {
        console.error('Error:', error);
        removeTypingIndicator();
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    }
}

function sendQuickMessage(message) {
    const messageInput = document.getElementById('messageInput');
    messageInput.value = message;
    sendMessage();
}

function addMessage(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <strong>${sender === 'user' ? 'You' : 'SmartRoof AI'}:</strong> ${message}
        </div>
        <div class="message-time">${timeString}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing-indicator';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="message-content">
            <strong>SmartRoof AI:</strong> <span class="typing-dots">
                <span>.</span><span>.</span><span>.</span>
            </span>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
    
    // Add CSS for typing animation
    const style = document.createElement('style');
    style.textContent = `
        .typing-dots span {
            animation: typing 1.4s infinite;
        }
        .typing-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes typing {
            0%, 60%, 100% { opacity: 0; }
            30% { opacity: 1; }
        }
    `;
    
    if (!document.getElementById('typing-style')) {
        style.id = 'typing-style';
        document.head.appendChild(style);
    }
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// FAQ responses for common questions
const faqResponses = {
    'hello': "Hello! I'm here to help you with any questions about roofing materials and services. What can I assist you with today?",
    'help': "I can help you with:\n• Product information and recommendations\n• Shipping and delivery options\n• Warranty and return policies\n• Installation guidance\n• Material calculations\n• Pricing and bulk orders\n\nWhat would you like to know more about?",
    'bye': "Thank you for using SmartRoof! Feel free to reach out anytime if you have more questions. Have a great day!",
    'thanks': "You're welcome! I'm glad I could help. Is there anything else you'd like to know about our roofing solutions?"
};

// Enhanced message processing
function processMessage(message) {
    const lowerMessage = message.toLowerCase();
    
    // Check for FAQ keywords
    for (const [keyword, response] of Object.entries(faqResponses)) {
        if (lowerMessage.includes(keyword)) {
            return response;
        }
    }
    
    // Default to sending to server
    return null;
}

// Chat statistics
let chatStats = {
    messagesCount: 0,
    sessionStart: new Date(),
    topics: []
};

function updateChatStats(message, sender) {
    if (sender === 'user') {
        chatStats.messagesCount++;
        
        // Simple topic detection
        const topics = ['shipping', 'warranty', 'installation', 'materials', 'pricing'];
        for (const topic of topics) {
            if (message.toLowerCase().includes(topic)) {
                if (!chatStats.topics.includes(topic)) {
                    chatStats.topics.push(topic);
                }
            }
        }
    }
}

// Export chat functions
window.ChatBot = {
    sendMessage,
    sendQuickMessage,
    addMessage,
    chatStats
};
