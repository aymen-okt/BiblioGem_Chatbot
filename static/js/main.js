let currentChatId = Date.now();
let chatToDelete = null;

// Update to store context per chat
let chatContexts = {};

document.addEventListener('DOMContentLoaded', () => {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.getElementById('darkModeToggle').checked = savedTheme === 'dark';

    // Theme switch handler
    document.getElementById('darkModeToggle').addEventListener('change', (e) => {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });

    // Load last chat if exists
    const chats = JSON.parse(localStorage.getItem('bookChats') || '{}');
    const chatIds = Object.keys(chats);
    if (chatIds.length > 0) {
        currentChatId = chatIds[chatIds.length - 1];
        const lastChat = chats[currentChatId];
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';
        lastChat.forEach(msg => {
            addMessageToChat(msg.role, msg.content);
        });
    }

    updateChatList();
    addSearchToChatHistory();
});

function addThinkingAnimation() {
    const chatMessages = document.getElementById('chat-messages');
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message assistant thinking-animation';
    thinkingDiv.innerHTML = `
        <div class="thinking-text">Thinking</div>
        <div class="thinking-dots">
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
        </div>
    `;
    chatMessages.appendChild(thinkingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return thinkingDiv;
}

function sendMessage() {
    const input = document.getElementById('user-input');
    const query = input.value.trim();
    
    if (!query) return;
    
    // Get current chat's context
    const currentContext = chatContexts[currentChatId] || {
        lastTopic: null,
        category: null,
        followUp: false
    };
    
    // Save user message
    addMessageToChat('user', query);
    saveChat(query, 'user');
    
    // Clear and disable input
    input.value = '';
    input.disabled = true;

    // Add thinking animation
    const thinkingAnimation = addThinkingAnimation();

    // Check if it's a follow-up question
    const isFollowUp = isFollowUpQuestion(query);
    
    if (isCasualConversation(query)) {
        setTimeout(() => {
            thinkingAnimation.remove();
            const response = getCasualResponse(query);
            addMessageToChat('assistant', response);
            saveChat(response, 'assistant');
            input.disabled = false;
            input.focus();
        }, 1500); // Longer delay to show thinking animation
        return;
    }

    // Handle book recommendations with context
    fetch('/get_recommendation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            query: query,
            context: {
                lastTopic: currentContext.lastTopic,
                category: currentContext.category,
                isFollowUp: isFollowUp,
                originalQuery: query.toLowerCase(),
                previousRecommendations: currentContext.recommendations || []
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove thinking animation
        thinkingAnimation.remove();

        // Store the response and recommendations in context
        chatContexts[currentChatId] = {
            lastTopic: query,
            category: data.category || currentContext.category,
            followUp: true,
            recommendations: data.recommendations || [],
            lastResponse: data.response
        };

        // Add response to chat
        addMessageToChat('assistant', data.response);
        saveChat(data.response, 'assistant');

        // Display recommendations if they exist
        if (data.recommendations && data.recommendations.length > 0) {
            displayRecommendations(data.recommendations);
            saveChat(JSON.stringify(data.recommendations), 'recommendations');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        thinkingAnimation.remove();
        addMessageToChat('error', 'Sorry, something went wrong. Please try again.');
    })
    .finally(() => {
        input.disabled = false;
        input.focus();
    });
}

function addMessageToChat(role, content) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    if (role === 'assistant') {
        // Format book titles with bold and styling
        content = content.replace(/\*\*(.*?)\*\*/g, '<span class="book-title">$1</span>');
        // Also format plain book titles that are followed by descriptions
        content = content.replace(/([A-Z][A-Za-z\s]+) by ([A-Za-z\s]+)/g, '<span class="book-title">$1</span> by $2');
        messageDiv.innerHTML = content;
    } else {
        const p = document.createElement('p');
        p.textContent = content;
        messageDiv.appendChild(p);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageDiv;
}

function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations-container');
    
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = `
        <div class="message assistant recommendations">
            <p class="recommendations-title">📚 Here are some books you might enjoy:</p>
            ${recommendations.map(book => `
                <div class="book-recommendation">
                    <span class="book-title">${book.title}</span>
                    <div class="book-meta">
                        <span>📖 ${book.category}</span>
                        <span>⏱️ ${book.reading_time}</span>
                    </div>
                    ${book.themes && book.themes.length > 0 ? `
                        <div class="themes-container">
                            ${book.themes.map(theme => `<span class="theme-tag">${theme}</span>`).join('')}
                        </div>
                    ` : ''}
                    <p class="book-summary">${book.summary}</p>
                </div>
            `).join('')}
        </div>
    `;
}

// Handle enter key in input
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initial focus
document.getElementById('user-input').focus();

// Function to save chat to localStorage
function saveChat(message, role) {
    const chats = JSON.parse(localStorage.getItem('bookChats') || '{}');
    if (!chats[currentChatId]) {
        chats[currentChatId] = [];
    }
    chats[currentChatId].push({
        role: role,
        content: message,
        timestamp: new Date().toISOString()
    });
    localStorage.setItem('bookChats', JSON.stringify(chats));
    updateChatList();
    autoSaveChat();
}

// Function to start a new chat
function startNewChat() {
    currentChatId = Date.now().toString();
    chatContexts[currentChatId] = {
        lastTopic: null,
        category: null,
        followUp: false
    };
    
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="message assistant">
            <p>Hello! 📚 I'm your AI book recommender, ready to help you discover your perfect next read.</p>
            <p>Here are some ways you can ask for recommendations:</p>
            <ul class="suggestion-list">
                <li data-query="Recommend me some fantasy books">🏰 "Recommend me some fantasy books"</li>
                <li data-query="Books about personal development">🌱 "Books about personal development"</li>
                <li data-query="Best science fiction novels">🚀 "Best science fiction novels"</li>
                <li data-query="Popular romance books">💕 "Popular romance books"</li>
            </ul>
            <p>What kind of books would you like to explore today?</p>
        </div>
    `;
    
    // Add click handlers to suggestions
    const suggestions = chatMessages.querySelectorAll('.suggestion-list li');
    suggestions.forEach(suggestion => {
        suggestion.addEventListener('click', () => {
            const query = suggestion.getAttribute('data-query');
            const input = document.getElementById('user-input');
            input.value = query;
            sendMessage();
        });
    });
    
    document.getElementById('recommendations-container').innerHTML = '';
    document.getElementById('user-input').value = '';
    saveChat(chatMessages.innerHTML, 'assistant');
}

function updateChatList() {
    const chatList = document.getElementById('chatList');
    const chats = JSON.parse(localStorage.getItem('bookChats') || '{}');
    
    chatList.innerHTML = '';
    
    Object.entries(chats).reverse().forEach(([chatId, messages]) => {
        const firstMessage = messages.find(m => m.role === 'user')?.content || 'New Chat';
        const date = new Date(parseInt(chatId)).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        
        const chatItem = document.createElement('div');
        chatItem.className = `chat-item ${chatId === currentChatId ? 'active' : ''}`;
        chatItem.innerHTML = `
            <div class="chat-info">
                <div class="chat-preview">${firstMessage.substring(0, 40)}${firstMessage.length > 40 ? '...' : ''}</div>
                <div class="chat-date">${date}</div>
            </div>
            <button 
                class="delete-chat" 
                onclick="showDeleteModal('${chatId}')" 
                title="Delete Chat"
                aria-label="Delete Chat"
            ></button>
        `;
        
        chatItem.addEventListener('click', (e) => {
            if (!e.target.classList.contains('delete-chat')) {
                loadChat(chatId);
            }
        });
        
        // Add hover effect to parent when delete button is hovered
        const deleteBtn = chatItem.querySelector('.delete-chat');
        deleteBtn.addEventListener('mouseenter', () => {
            chatItem.style.borderColor = '#ef4444';
        });
        deleteBtn.addEventListener('mouseleave', () => {
            chatItem.style.borderColor = chatId === currentChatId ? 
                'var(--secondary-color)' : 'var(--border-color)';
        });
        
        chatList.appendChild(chatItem);
    });
}

function loadChat(chatId) {
    const chats = JSON.parse(localStorage.getItem('bookChats') || '{}');
    const chat = chats[chatId];
    
    if (chat) {
        currentChatId = chatId;
        
        // Initialize or load context
        chatContexts[chatId] = chatContexts[chatId] || {
            lastTopic: null,
            category: null,
            followUp: false,
            recommendations: [],
            lastResponse: null
        };
        
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';
        
        // Display messages and recommendations
        chat.forEach(msg => {
            if (msg.role === 'recommendations') {
                const recommendations = JSON.parse(msg.content);
                displayRecommendations(recommendations);
            } else {
                addMessageToChat(msg.role, msg.content);
            }
        });
        
        updateChatList();
    }
}

function exportChats() {
    const chats = localStorage.getItem('bookChats');
    const blob = new Blob([chats], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `book-chats-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function importChats() {
    document.getElementById('importInput').click();
}

document.getElementById('importInput').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const importedChats = JSON.parse(e.target.result);
                const existingChats = JSON.parse(localStorage.getItem('bookChats') || '{}');
                const mergedChats = { ...existingChats, ...importedChats };
                localStorage.setItem('bookChats', JSON.stringify(mergedChats));
                updateChatList();
            } catch (error) {
                console.error('Error importing chats:', error);
                alert('Invalid chat file format');
            }
        };
        reader.readAsText(file);
    }
});

function showDeleteModal(chatId) {
    chatToDelete = chatId;
    const modal = document.getElementById('deleteModal');
    modal.style.display = 'flex';
    // Trigger animation
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    modal.classList.remove('show');
    // Wait for animation to complete before hiding
    setTimeout(() => {
        modal.style.display = 'none';
        chatToDelete = null;
    }, 300);
}

// Close modal when clicking outside
document.getElementById('deleteModal').addEventListener('click', (e) => {
    if (e.target.id === 'deleteModal') {
        closeDeleteModal();
    }
});

// Add keyboard support
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('deleteModal').style.display === 'flex') {
        closeDeleteModal();
    }
});

function confirmDelete() {
    if (chatToDelete) {
        const chats = JSON.parse(localStorage.getItem('bookChats') || '{}');
        delete chats[chatToDelete];
        localStorage.setItem('bookChats', JSON.stringify(chats));
        
        if (chatToDelete === currentChatId) {
            startNewChat();
        }
        
        updateChatList();
        closeDeleteModal();
    }
}

// Add auto-save functionality
function autoSaveChat() {
    const chats = JSON.parse(localStorage.getItem('bookChats') || '{}');
    fetch('/save_chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            id: currentChatId,
            messages: chats[currentChatId]
        })
    }).catch(error => console.error('Auto-save failed:', error));
}

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + N for new chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        startNewChat();
    }
    
    // Ctrl/Cmd + Enter to send message
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
    
    // Escape to clear input
    if (e.key === 'Escape' && document.activeElement === document.getElementById('user-input')) {
        e.preventDefault();
        document.getElementById('user-input').value = '';
    }
});

// Add retry functionality
let lastQuery = '';
function retryLastQuery() {
    const input = document.getElementById('user-input');
    input.value = lastQuery;
    sendMessage();
}

// Enhance chat history with search
function addSearchToChatHistory() {
    const sidebar = document.querySelector('.sidebar-header');
    sidebar.innerHTML += `
        <div class="chat-search">
            <input 
                type="text" 
                placeholder="Search conversations..." 
                id="chatSearch"
                aria-label="Search conversations"
            >
        </div>
    `;

    document.getElementById('chatSearch').addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const chatItems = document.querySelectorAll('.chat-item');
        
        chatItems.forEach(item => {
            const text = item.querySelector('.chat-preview').textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? 'flex' : 'none';
        });
    });
}

// Add function to detect casual conversation
function isCasualConversation(query) {
    const casualPatterns = [
        /how are you/i,
        /how('s| is) it going/i,
        /what('s| is) up/i,
        /hello|hi|hey/i,
        /good (morning|afternoon|evening)/i,
        /who are you/i,
        /what can you do/i
    ];
    
    return casualPatterns.some(pattern => pattern.test(query));
}

// Add function to generate casual responses
function getCasualResponse(query) {
    const responses = {
        how: `I'm doing great, thanks for asking! 😊 I love helping people discover amazing books. What kind of books interest you? I'd be happy to recommend something that matches your taste!`,
        hello: `Hello! It's wonderful to chat with you! 👋 I'm excited to help you find your next favorite book. What genres or themes do you enjoy?`,
        who: `I'm an AI book recommender, passionate about connecting readers with books they'll love! 📚 I know quite a bit about literature and enjoy making personalized recommendations. What would you like to know?`,
        what: `I'm here to help you discover great books! I can recommend books based on your interests, suggest similar books to ones you've enjoyed, or help you explore new genres. What would you like to explore?`
    };

    query = query.toLowerCase();
    if (query.includes('how are you') || query.includes("how's it going")) return responses.how;
    if (query.match(/^(hi|hello|hey)/)) return responses.hello;
    if (query.includes('who are you')) return responses.who;
    if (query.includes('what can you do')) return responses.what;

    return `I'm doing great! I love chatting about books and helping people find their next great read. What kind of books interest you? 📚`;
}

// Add function to detect follow-up questions
function isFollowUpQuestion(query) {
    const followUpPatterns = [
        /^what about/i,
        /^how about/i,
        /^and/i,
        /^what else/i,
        /^tell me more/i,
        /^more/i
    ];
    
    return followUpPatterns.some(pattern => pattern.test(query.trim()));
} 