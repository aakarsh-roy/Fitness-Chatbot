const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const typingIndicator = document.getElementById('typing-indicator');

// Voice recognition setup
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'en-US';
recognition.continuous = false;
recognition.interimResults = false;

function formatTimestamp() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function addMessage(message, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
    
    const timestamp = document.createElement('div');
    timestamp.className = 'timestamp';
    timestamp.textContent = formatTimestamp();

    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = message;

    messageDiv.appendChild(content);
    messageDiv.appendChild(timestamp);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Voice input handling
document.getElementById('voice-input').addEventListener('click', function() {
    recognition.start();
    this.classList.add('recording');
});

recognition.onresult = function(event) {
    const voiceInput = event.results[0][0].transcript;
    document.getElementById('user-message').value = voiceInput;
    document.getElementById('voice-input').classList.remove('recording');
};

recognition.onend = function() {
    document.getElementById('voice-input').classList.remove('recording');
};

// Export chat
document.getElementById('export-chat').addEventListener('click', function() {
    const messages = Array.from(chatMessages.children).map(msg => {
        const content = msg.querySelector('.message-content').innerText;
        const timestamp = msg.querySelector('.timestamp').innerText;
        const isUser = msg.classList.contains('user-message');
        return `[${timestamp}] ${isUser ? 'You' : 'Bot'}: ${content}`;
    }).join('\n');

    const blob = new Blob([messages], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fitness-chat-history.txt';
    a.click();
});

// Clear chat
document.getElementById('clear-chat').addEventListener('click', function() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        chatMessages.innerHTML = '';
        fetch('/clear-session', { method: 'POST' });
    }
});

// Preset questions
document.querySelectorAll('.preset-question').forEach(button => {
    button.addEventListener('click', function() {
        document.getElementById('user-message').value = this.textContent;
        chatForm.dispatchEvent(new Event('submit'));
    });
});

// Initialize chat with welcome message
document.addEventListener('DOMContentLoaded', function() {
    addMessage("Hello! I'm your fitness diet planner. How can I assist you today?");
});

// Handle form submission
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const userInput = document.getElementById('user-message');
    const message = userInput.value;
    
    if (!message.trim()) return;

    // Add user message to chat
    addMessage(message, true);
    userInput.value = '';

    // Show typing indicator
    typingIndicator.classList.remove('hidden');

    try {
        // Send message to backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        
        // Hide typing indicator
        typingIndicator.classList.add('hidden');
        
        // Add bot response to chat
        addMessage(data.response);
    } catch (error) {
        console.error('Error:', error);
        typingIndicator.classList.add('hidden');
        addMessage('Sorry, something went wrong. Please try again.');
    }
});

