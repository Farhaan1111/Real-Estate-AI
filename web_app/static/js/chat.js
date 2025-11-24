class ModernChatApp {
    constructor() {
        this.startTime = null;
        this.messageCount = 0;
        this.initializeEventListeners();
        this.loadHistory();
        this.startTime = Date.now();
        
        // Check for URL parameter
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('query');
        if (query) {
            document.getElementById('queryInput').value = decodeURIComponent(query);
            this.sendMessage();
        }
    }

    initializeEventListeners() {
        // Form submission
        document.getElementById('chatForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // Clear history
        document.getElementById('clearHistory').addEventListener('click', () => {
            this.clearHistory();
        });

        // Quick questions
        document.querySelectorAll('.quick-action, .quick-action-modern').forEach(button => {
            button.addEventListener('click', (e) => {
                const question = e.target.getAttribute('data-question');
                document.getElementById('queryInput').value = question;
                this.sendMessage();
            });
        });

        // Enter key to send (with Shift+Enter for new line)
        document.getElementById('queryInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        document.getElementById('queryInput').addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    async sendMessage() {
        const input = document.getElementById('queryInput');
        const query = input.value.trim();
        
        if (!query) return;

        // Disable input while processing
        input.disabled = true;
        document.getElementById('sendButton').disabled = true;
        document.getElementById('sendButton').innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        // Add user message to chat
        this.addMessage(query, 'user');
        input.value = '';
        input.style.height = 'auto';
        
        this.showTypingIndicator();
        this.messageCount++;

        const startTime = Date.now();
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });
            const data = await response.json();
            const responseTime = Date.now() - startTime;
            
            this.hideTypingIndicator();
            if (data.success) {
                this.addMessage(data.response, 'ai', data);
                this.updateAnalytics(data, responseTime);
            } else {
                this.addMessage(data.response || 'Sorry, I encountered an error.', 'ai');
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('Sorry, there was a network error. Please try again.', 'ai');
            console.error('Error:', error);
        }

        // Re-enable input
        input.disabled = false;
        document.getElementById('sendButton').disabled = false;
        document.getElementById('sendButton').innerHTML = '<i class="fas fa-paper-plane"></i>';
        input.focus();
        
        this.scrollToBottom();
    }

    addMessage(content, sender, data = null) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        let messageContent = `
            <div class="message-content">${this.formatMessage(content)}</div>
            <div class="message-time">${timestamp}</div>
        `;
        
        if (sender === 'ai' && data) {
            messageContent += this.createMetadataBadges(data);
        }
        
        messageDiv.innerHTML = messageContent;
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Convert URLs to links
        content = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" class="text-primary">$1</a>');
        
        // Convert bullet points
        content = content.replace(/•\s*(.+)/g, '<li>$1</li>');
        content = content.replace(/(<li>.*<\/li>)/s, '<ul class="mb-2">$1</ul>');
        
        // Convert numbers with units (like 100 sqm)
        content = content.replace(/(\d+)\s*(sqm|sq\.?m|meters?)/gi, '<strong class="text-accent">$1 $2</strong>');
        
        // Convert project names
        content = content.replace(/(UNNATHI\s+\w+)/gi, '<strong class="text-primary">$1</strong>');
        
        return content;
    }

    createMetadataBadges(data) {
        let badges = '';
        
        if (data.query_type) {
            badges += `<span class="badge bg-primary me-1">${data.query_type}</span>`;
        }
        
        if (data.categories && data.categories.length > 0) {
            badges += `<span class="badge bg-secondary me-1">${data.categories.join(', ')}</span>`;
        }
        
        if (data.documents_used > 0) {
            badges += `<span class="badge bg-info me-1">${data.documents_used} docs</span>`;
        }

        if (badges) {
            badges = `<div class="message-metadata mt-2">${badges}</div>`;
        }
        
        return badges;
    }

    showTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'block';
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'none';
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async loadHistory() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = '';
            
            if (data.history && data.history.length > 0) {
                data.history.forEach(item => {
                    this.addMessage(item.query, 'user');
                    this.addMessage(item.response, 'ai');
                });
            } else {
                // Add welcome message
                this.addMessage('Hello! I\'m your Real Estate AI assistant. I can help you find detailed information about RERA projects, building specifications, locations, timelines, and more. How can I assist you today?', 'ai');
            }
            
            this.scrollToBottom();
        } catch (error) {
            console.error('Error loading history:', error);
            // Add welcome message even if history fails
            this.addMessage('Hello! I\'m your Real Estate AI assistant. How can I help you today?', 'ai');
        }
    }

    async clearHistory() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            try {
                await fetch('/api/clear_history', { method: 'POST' });
                const messagesContainer = document.getElementById('chatMessages');
                messagesContainer.innerHTML = '';
                this.addMessage('Hello! I\'m your Real Estate AI assistant. How can I help you today?', 'ai');
                this.messageCount = 0;
                this.updateAnalytics();
            } catch (error) {
                console.error('Error clearing history:', error);
                alert('Error clearing history. Please try again.');
            }
        }
    }

    updateAnalytics(data = null, responseTime = 0) {
        // Update basic stats
        document.getElementById('documentsCount').textContent = data?.documents_used || 0;
        document.getElementById('responseTime').textContent = responseTime;
        document.getElementById('messageCount').textContent = this.messageCount;
        document.getElementById('ragScore').textContent = data?.documents_used ? 'High' : 'Low';
        
        // Update detailed analytics
        const analyticsDetails = document.getElementById('analyticsDetails');
        if (data && data.query_type) {
            analyticsDetails.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <small><strong>Query Type:</strong> ${data.query_type}</small>
                    </div>
                    <div class="col-md-6">
                        <small><strong>Categories:</strong> ${data.categories?.join(', ') || 'N/A'}</small>
                    </div>
                </div>
                ${data.reasoning ? `<div class="row mt-2"><div class="col-12"><small><strong>Reasoning:</strong> ${data.reasoning}</small></div></div>` : ''}
                ${data.entities ? `<div class="row mt-1"><div class="col-12"><small><strong>Entities:</strong> ${Object.keys(data.entities).join(', ')}</small></div></div>` : ''}
            `;
        } else {
            analyticsDetails.innerHTML = '<small class="text-muted">Send a message to see analytics...</small>';
        }
    }
}

// Initialize modern chat app when page loads
document.addEventListener('DOMContentLoaded', () => {
    new ModernChatApp();
});