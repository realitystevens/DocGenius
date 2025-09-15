/**
 * DocGenius Chat Handler
 * Handles AI chat interactions, message display, and conversation management
 */

class ChatHandler {
    constructor() {
        this.conversations = [];
        this.currentConversation = null;
        this.isTyping = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.initializeElements();
        this.bindEvents();
        this.loadConversations();
    }

    initializeElements() {
        // Chat elements
        this.chatContainer = document.getElementById('chatContainer');
        this.welcomeScreen = document.getElementById('welcomeScreen');
        this.chatMessages = document.getElementById('chatMessages');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        // Input elements
        this.chatForm = document.getElementById('chatForm');
        this.chatInputContainer = document.getElementById('chatInputContainer');
        this.questionInput = document.getElementById('questionInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.clearInputBtn = document.getElementById('clearInputBtn');
        this.voiceBtn = document.getElementById('voiceBtn');
        
        // Quick actions
        this.quickActions = document.getElementById('quickActions');
        
        // Conversation list
        this.conversationList = document.getElementById('conversationList');
        this.conversationsEmptyState = document.getElementById('conversationsEmptyState');
        this.clearConversations = document.getElementById('clearConversations');
    }

    bindEvents() {
        // Chat form submission
        this.chatForm?.addEventListener('submit', (e) => this.handleChatSubmit(e));
        
        // Input events
        this.questionInput?.addEventListener('input', () => this.handleInputChange());
        this.questionInput?.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.clearInputBtn?.addEventListener('click', () => this.clearInput());
        
        // Quick actions
        this.quickActions?.addEventListener('click', (e) => this.handleQuickAction(e));
        
        // Voice input (placeholder)
        this.voiceBtn?.addEventListener('click', () => this.handleVoiceInput());
        
        // Conversation management
        this.clearConversations?.addEventListener('click', () => this.handleClearConversations());
        
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleGlobalKeyboard(e));
    }

    handleChatSubmit(event) {
        event.preventDefault();
        
        const question = this.questionInput?.value.trim();
        if (!question) return;
        
        const activeFile = window.app?.fileHandler?.getActiveFile();
        if (!activeFile) {
            window.app?.showToast('Please select a file first', 'error');
            return;
        }
        
        this.sendMessage(question, activeFile);
    }

    handleInputChange() {
        const hasValue = this.questionInput?.value.trim().length > 0;
        if (this.sendBtn) {
            this.sendBtn.disabled = !hasValue || this.isTyping;
        }
    }

    handleKeyDown(event) {
        // Ctrl/Cmd + Enter to send
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            event.preventDefault();
            this.handleChatSubmit(event);
        }
        
        // Escape to clear
        if (event.key === 'Escape') {
            this.clearInput();
        }
    }

    handleQuickAction(event) {
        const button = event.target.closest('.quick-action');
        if (!button) return;
        
        const question = button.dataset.question;
        if (question) {
            this.questionInput.value = question;
            this.handleInputChange();
            this.questionInput.focus();
        }
    }

    handleVoiceInput() {
        // Placeholder for voice input functionality
        window.app?.showToast('Voice input feature coming soon!', 'info');
    }

    handleGlobalKeyboard(event) {
        // Ctrl/Cmd + U for upload
        if ((event.ctrlKey || event.metaKey) && event.key === 'u') {
            event.preventDefault();
            window.app?.fileHandler?.triggerFileSelect();
        }
        
        // Focus input with / key (like Discord/Slack)
        if (event.key === '/' && !event.ctrlKey && !event.metaKey && 
            !['input', 'textarea'].includes(event.target.tagName.toLowerCase())) {
            event.preventDefault();
            this.questionInput?.focus();
        }
    }

    async sendMessage(question, file) {
        // Show UI changes
        this.showChatInterface(true);
        this.addMessage('user', question);
        this.clearInput();
        this.showTyping(true);
        this.isTyping = true;
        this.handleInputChange();

        try {
            // Prepare request
            const formData = new FormData();
            formData.append('question', question);
            formData.append('extractedFileText', file.extracted_text);

            // Send request with retry logic
            const response = await this.sendWithRetry('/api/chat', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to get response');
            }

            // Add AI response
            this.addMessage('assistant', data.answer);
            
            // Save conversation
            this.saveConversation(question, data.answer, file.file_name);
            
            // Reset retry count on success
            this.retryCount = 0;
            
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage('assistant', this.getErrorMessage(error), true);
        } finally {
            this.showTyping(false);
            this.isTyping = false;
            this.handleInputChange();
        }
    }

    async sendWithRetry(url, options, retryCount = 0) {
        try {
            const response = await fetch(url, options);
            
            // If rate limited, wait and retry
            if (response.status === 429 && retryCount < this.maxRetries) {
                const waitTime = Math.pow(2, retryCount) * 1000; // Exponential backoff
                await this.wait(waitTime);
                return this.sendWithRetry(url, options, retryCount + 1);
            }
            
            return response;
        } catch (error) {
            if (retryCount < this.maxRetries) {
                const waitTime = Math.pow(2, retryCount) * 1000;
                await this.wait(waitTime);
                return this.sendWithRetry(url, options, retryCount + 1);
            }
            throw error;
        }
    }

    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    getErrorMessage(error) {
        if (error.message.includes('429') || error.message.includes('rate limit')) {
            return 'I\'m experiencing high demand right now. Please try again in a moment.';
        }
        
        if (error.message.includes('network') || error.message.includes('fetch')) {
            return 'I\'m having trouble connecting. Please check your internet connection and try again.';
        }
        
        return 'I encountered an error while processing your request. Please try again.';
    }

    showChatInterface(show) {
        if (this.welcomeScreen && this.chatMessages && this.chatInputContainer) {
            this.welcomeScreen.hidden = show;
            this.chatMessages.hidden = !show;
            this.chatInputContainer.hidden = !show;
        }
    }

    addMessage(role, content, isError = false) {
        if (!this.messagesContainer) return;

        const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const avatar = role === 'user' ? 'You' : '🤖';
        const authorName = role === 'user' ? 'You' : 'DocGenius';

        const messageElement = document.createElement('div');
        messageElement.className = `message ${role} ${isError ? 'error' : ''}`;
        messageElement.dataset.messageId = messageId;
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                ${avatar}
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author">${authorName}</span>
                    <span class="message-time">${timestamp}</span>
                </div>
                <div class="message-text">${this.formatMessage(content)}</div>
                <div class="message-actions">
                    <button class="message-action" data-action="copy" title="Copy message">
                        <span class="material-symbols-outlined">content_copy</span>
                    </button>
                    ${role === 'assistant' && !isError ? `
                        <button class="message-action" data-action="retry" title="Regenerate response">
                            <span class="material-symbols-outlined">refresh</span>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        // Add to container
        this.messagesContainer.appendChild(messageElement);

        // Bind actions
        this.bindMessageActions(messageElement);

        // Scroll to bottom
        this.scrollToBottom();

        // Return element for further manipulation
        return messageElement;
    }

    bindMessageActions(messageElement) {
        const copyBtn = messageElement.querySelector('[data-action="copy"]');
        const retryBtn = messageElement.querySelector('[data-action="retry"]');

        copyBtn?.addEventListener('click', () => {
            const text = messageElement.querySelector('.message-text').textContent;
            this.copyToClipboard(text);
        });

        retryBtn?.addEventListener('click', () => {
            // Find the user message that prompted this response
            const userMessage = this.findPreviousUserMessage(messageElement);
            if (userMessage) {
                const question = userMessage.querySelector('.message-text').textContent;
                const activeFile = window.app?.fileHandler?.getActiveFile();
                if (activeFile) {
                    this.sendMessage(question, activeFile);
                }
            }
        });
    }

    findPreviousUserMessage(assistantMessage) {
        let current = assistantMessage.previousElementSibling;
        while (current) {
            if (current.classList.contains('message') && current.classList.contains('user')) {
                return current;
            }
            current = current.previousElementSibling;
        }
        return null;
    }

    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            window.app?.showToast('Copied to clipboard', 'success');
        } catch (error) {
            console.error('Copy failed:', error);
            window.app?.showToast('Failed to copy to clipboard', 'error');
        }
    }

    formatMessage(content) {
        // Basic formatting for AI responses
        return content
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^\s*/, '<p>')
            .replace(/\s*$/, '</p>')
            .replace(/<p><\/p>/g, '')
            // Bold text **text**
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic text *text*
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Code blocks ```code```
            .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>')
            // Inline code `code`
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }

    showTyping(show) {
        if (this.typingIndicator) {
            this.typingIndicator.hidden = !show;
            if (show) {
                this.scrollToBottom();
            }
        }
    }

    scrollToBottom() {
        if (this.messagesContainer) {
            setTimeout(() => {
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            }, 100);
        }
    }

    clearInput() {
        if (this.questionInput) {
            this.questionInput.value = '';
            this.handleInputChange();
        }
    }

    saveConversation(question, answer, fileName) {
        const conversation = {
            id: `conv_${Date.now()}`,
            question,
            answer,
            fileName,
            timestamp: new Date().toISOString()
        };
        
        this.conversations.unshift(conversation);
        this.updateConversationsList();
    }

    async loadConversations() {
        try {
            const response = await fetch('/api/conversations');
            if (response.ok) {
                const data = await response.json();
                this.conversations = data.conversations || [];
                this.updateConversationsList();
            }
        } catch (error) {
            console.error('Failed to load conversations:', error);
            this.conversations = [];
            this.updateConversationsList();
        }
    }

    updateConversationsList() {
        if (!this.conversationList) return;

        if (this.conversations.length === 0) {
            this.showConversationsEmptyState(true);
            return;
        }

        this.showConversationsEmptyState(false);
        
        this.conversationList.innerHTML = this.conversations.map((conv, index) => `
            <li class="conversation-item" data-conversation-id="${conv.id}" role="listitem">
                <div class="conversation-icon">
                    ${index + 1}
                </div>
                <div class="conversation-content">
                    <h4 class="conversation-question" title="${conv.question}">
                        ${this.truncateText(conv.question, 50)}
                    </h4>
                    <p class="conversation-preview" title="${conv.answer}">
                        ${this.truncateText(conv.answer, 60)}
                    </p>
                </div>
            </li>
        `).join('');

        // Bind conversation click events
        this.bindConversationEvents();
    }

    bindConversationEvents() {
        const items = this.conversationList?.querySelectorAll('.conversation-item');
        items?.forEach(item => {
            item.addEventListener('click', () => {
                const convId = item.dataset.conversationId;
                this.loadConversation(convId);
            });
        });
    }

    loadConversation(conversationId) {
        const conversation = this.conversations.find(c => c.id === conversationId);
        if (!conversation) return;

        // Clear current messages
        if (this.messagesContainer) {
            this.messagesContainer.innerHTML = '';
        }

        // Show chat interface
        this.showChatInterface(true);

        // Add messages
        this.addMessage('user', conversation.question);
        this.addMessage('assistant', conversation.answer);
    }

    showConversationsEmptyState(show) {
        if (this.conversationsEmptyState) {
            this.conversationsEmptyState.style.display = show ? 'flex' : 'none';
        }
        if (this.conversationList) {
            this.conversationList.style.display = show ? 'none' : 'block';
        }
    }

    async handleClearConversations() {
        if (!confirm('Are you sure you want to clear all conversations?')) {
            return;
        }

        try {
            const response = await fetch('/api/conversations', {
                method: 'DELETE'
            });

            if (response.ok) {
                this.conversations = [];
                this.updateConversationsList();
                
                // Clear current chat
                if (this.messagesContainer) {
                    this.messagesContainer.innerHTML = '';
                }
                this.showChatInterface(false);
                
                window.app?.showToast('Conversations cleared', 'success');
            } else {
                throw new Error('Failed to clear conversations');
            }
        } catch (error) {
            console.error('Clear conversations error:', error);
            window.app?.showToast('Failed to clear conversations', 'error');
        }
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength).trim() + '...';
    }

    // Public API
    clearChat() {
        if (this.messagesContainer) {
            this.messagesContainer.innerHTML = '';
        }
        this.showChatInterface(false);
    }

    getCurrentConversation() {
        return this.currentConversation;
    }

    refreshConversations() {
        return this.loadConversations();
    }
}

// Export for module usage
export default ChatHandler;