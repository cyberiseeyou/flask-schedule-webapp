/**
 * AI Assistant Component
 *
 * Handles chat interactions with the AI assistant
 */

class AIAssistant {
    constructor() {
        // DOM elements
        this.container = document.getElementById('ai-chat-container');
        this.toggleBtn = document.getElementById('ai-chat-toggle');
        this.closeBtn = document.getElementById('ai-chat-close');
        this.chatWindow = document.getElementById('ai-chat-window');
        this.messagesContainer = document.getElementById('ai-messages');
        this.suggestionsContainer = document.getElementById('ai-suggestions');
        this.suggestionsList = document.getElementById('ai-suggestions-list');
        this.input = document.getElementById('ai-input');
        this.sendBtn = document.getElementById('ai-send-btn');

        // State
        this.isOpen = false;
        this.conversationId = null;
        this.conversationHistory = [];
        this.pendingConfirmation = null;

        this.init();
    }

    init() {
        // Event listeners
        this.toggleBtn.addEventListener('click', () => this.toggleChat());
        this.closeBtn.addEventListener('click', () => this.closeChat());
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keydown', (e) => this.handleInputKeydown(e));

        // Auto-resize textarea
        this.input.addEventListener('input', () => this.autoResizeInput());

        // Keyboard shortcut (Ctrl+K or Cmd+K)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.toggleChat();
            }
        });

        // Load suggestions
        this.loadSuggestions();

        // Check AI health
        this.checkHealth();
    }

    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        this.chatWindow.style.display = 'flex';
        this.isOpen = true;
        this.input.focus();

        // Show/hide suggestions based on messages
        if (this.conversationHistory.length === 0) {
            this.suggestionsContainer.style.display = 'block';
        } else {
            this.suggestionsContainer.style.display = 'none';
        }
    }

    closeChat() {
        this.chatWindow.style.display = 'none';
        this.isOpen = false;
    }

    async loadSuggestions() {
        try {
            const response = await fetch('/api/ai/suggestions');
            if (!response.ok) return;

            const data = await response.json();
            this.renderSuggestions(data.suggestions);
        } catch (error) {
            console.error('Failed to load suggestions:', error);
        }
    }

    renderSuggestions(suggestions) {
        this.suggestionsList.innerHTML = '';

        suggestions.forEach(suggestion => {
            const chip = document.createElement('div');
            chip.className = 'ai-suggestion-chip';
            chip.innerHTML = `
                <span class="ai-suggestion-icon">${suggestion.icon}</span>
                <span>${suggestion.label}</span>
            `;
            chip.addEventListener('click', () => {
                this.input.value = suggestion.query;
                this.sendMessage();
            });
            this.suggestionsList.appendChild(chip);
        });
    }

    handleInputKeydown(e) {
        // Send on Enter (without Shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    autoResizeInput() {
        this.input.style.height = 'auto';
        this.input.style.height = this.input.scrollHeight + 'px';
    }

    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;

        // Clear input
        this.input.value = '';
        this.autoResizeInput();

        // Hide suggestions
        this.suggestionsContainer.style.display = 'none';

        // Add user message to chat
        this.addMessage('user', message);

        // Show loading indicator
        const loadingId = this.showLoading();

        try {
            // Send to API
            const response = await fetch('/api/ai/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    conversation_id: this.conversationId,
                    history: this.conversationHistory
                })
            });

            // Remove loading
            this.removeLoading(loadingId);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to get response');
            }

            const data = await response.json();

            // Update conversation
            this.conversationId = data.conversation_id;
            this.conversationHistory.push(
                { role: 'user', content: message },
                { role: 'assistant', content: data.response }
            );

            // Add assistant response
            this.addMessage('assistant', data.response, data);

        } catch (error) {
            console.error('Error sending message:', error);
            this.removeLoading(loadingId);
            this.addMessage('assistant', `Sorry, I encountered an error: ${error.message}`);
        }
    }

    addMessage(role, content, data = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ${role}-message`;

        const avatar = document.createElement('div');
        avatar.className = `ai-message-avatar ${role}-avatar`;
        avatar.textContent = role === 'user' ? '👤' : '🤖';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'ai-message-content';

        const bubble = document.createElement('div');
        bubble.className = 'ai-message-bubble';
        bubble.textContent = content;

        contentDiv.appendChild(bubble);

        // Add actions if present
        if (data && data.actions) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'ai-message-actions';

            data.actions.forEach(action => {
                const btn = document.createElement('button');
                btn.className = 'ai-action-btn';
                btn.textContent = action.label;
                btn.addEventListener('click', () => {
                    if (action.action.startsWith('/')) {
                        window.location.href = action.action;
                    }
                });
                actionsDiv.appendChild(btn);
            });

            contentDiv.appendChild(actionsDiv);
        }

        // Add confirmation if required
        if (data && data.requires_confirmation) {
            const confirmDiv = this.createConfirmationUI(data.confirmation_data);
            contentDiv.appendChild(confirmDiv);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    createConfirmationUI(confirmationData) {
        const confirmDiv = document.createElement('div');
        confirmDiv.className = 'ai-confirmation';

        const text = document.createElement('div');
        text.className = 'ai-confirmation-text';
        text.textContent = 'Do you want to proceed?';

        const actions = document.createElement('div');
        actions.className = 'ai-confirmation-actions';

        const confirmBtn = document.createElement('button');
        confirmBtn.className = 'ai-confirm-btn confirm';
        confirmBtn.textContent = 'Confirm';
        confirmBtn.addEventListener('click', () => this.confirmAction(confirmationData, confirmDiv));

        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'ai-confirm-btn cancel';
        cancelBtn.textContent = 'Cancel';
        cancelBtn.addEventListener('click', () => {
            confirmDiv.remove();
            this.addMessage('assistant', 'Action cancelled.');
        });

        actions.appendChild(confirmBtn);
        actions.appendChild(cancelBtn);

        confirmDiv.appendChild(text);
        confirmDiv.appendChild(actions);

        return confirmDiv;
    }

    async confirmAction(confirmationData, confirmDiv) {
        // Disable buttons
        const buttons = confirmDiv.querySelectorAll('button');
        buttons.forEach(btn => btn.disabled = true);

        try {
            const response = await fetch('/api/ai/confirm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    confirmation_data: confirmationData
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to confirm action');
            }

            const data = await response.json();

            // Remove confirmation UI
            confirmDiv.remove();

            // Add result message
            this.addMessage('assistant', data.response, data);

        } catch (error) {
            console.error('Error confirming action:', error);
            confirmDiv.remove();
            this.addMessage('assistant', `Error: ${error.message}`);
        }
    }

    showLoading() {
        const loadingId = `loading-${Date.now()}`;
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'ai-message assistant-message';

        const avatar = document.createElement('div');
        avatar.className = 'ai-message-avatar bot-avatar';
        avatar.textContent = '🤖';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'ai-message-content';

        const bubble = document.createElement('div');
        bubble.className = 'ai-message-bubble';

        const loading = document.createElement('div');
        loading.className = 'ai-loading';
        loading.innerHTML = `
            <div class="ai-loading-dot"></div>
            <div class="ai-loading-dot"></div>
            <div class="ai-loading-dot"></div>
        `;

        bubble.appendChild(loading);
        contentDiv.appendChild(bubble);
        loadingDiv.appendChild(avatar);
        loadingDiv.appendChild(contentDiv);

        this.messagesContainer.appendChild(loadingDiv);
        this.scrollToBottom();

        return loadingId;
    }

    removeLoading(loadingId) {
        const loadingDiv = document.getElementById(loadingId);
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/ai/health');
            const data = await response.json();

            if (data.status === 'error') {
                console.warn('AI Assistant not configured:', data.message);
                // Optionally disable the chat button
                // this.toggleBtn.disabled = true;
                // this.toggleBtn.title = 'AI Assistant not configured';
            }
        } catch (error) {
            console.error('Failed to check AI health:', error);
        }
    }
}
