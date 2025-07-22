/**
 * Chat functionality for HR Resume Assistant
 * Handles real-time chat with AI assistant representing the candidate
 */

class ChatInterface {
    constructor() {
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.quickQuestions = document.querySelectorAll('.quick-question');
        
        this.isWaiting = false;
        this.chatHistory = [];
        
        this.init();
    }

    init() {
        if (!this.messageForm || !this.messageInput || !this.sendBtn) {
            console.error('Chat interface elements not found');
            return;
        }

        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.focusInput();
        
        console.log('Chat interface initialized');
    }

    setupEventListeners() {
        // Form submission
        this.messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSendMessage();
        });

        // Quick question buttons
        this.quickQuestions.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = btn.getAttribute('data-question');
                this.sendQuickQuestion(question);
            });
        });

        // Auto-resize message input
        this.messageInput.addEventListener('input', this.autoResizeInput.bind(this));

        // Clear chat functionality
        if (window.clearChat) {
            // Function defined globally or in template
        } else {
            window.clearChat = () => this.clearChat();
        }
    }

    setupKeyboardShortcuts() {
        this.messageInput.addEventListener('keydown', (e) => {
            // Enter to send (without Shift)
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!this.isWaiting && this.messageInput.value.trim()) {
                    this.handleSendMessage();
                }
            }
            
            // Shift+Enter for new line (default behavior)
            // Escape to clear input
            if (e.key === 'Escape') {
                this.messageInput.value = '';
                this.autoResizeInput();
            }
        });
    }

    focusInput() {
        setTimeout(() => {
            if (this.messageInput) {
                this.messageInput.focus();
                // Scroll to bottom when focusing to ensure input is visible
                this.scrollToBottom();
            }
        }, 300);
    }

    autoResizeInput() {
        this.messageInput.style.height = 'auto';
        const maxHeight = 120;
        const scrollHeight = Math.min(this.messageInput.scrollHeight, maxHeight);
        this.messageInput.style.height = scrollHeight + 'px';
    }

    async handleSendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isWaiting) {
            return;
        }

        // Add user message to chat
        this.addUserMessage(message);
        
        // Clear input and prepare for response
        this.messageInput.value = '';
        this.autoResizeInput();
        this.setWaitingState(true);

        try {
            // Use streaming for real-time response
            await this.sendMessageStreaming(message);
            
        } catch (error) {
            console.error('Streaming chat error:', error);
            
            // Try fallback to regular API if streaming fails
            try {
                console.log('Attempting fallback to non-streaming API...');
                const response = await this.sendMessageToAPI(message);
                
                if (response.response) {
                    this.addAssistantMessage(response.response);
                    window.resumeAssistant.showToast('Response received (fallback mode)', 'info');
                } else {
                    throw new Error('No response received from fallback API');
                }
            } catch (fallbackError) {
                console.error('Fallback also failed:', fallbackError);
                
                let errorMessage = 'Failed to get response. Please try again.';
                
                // Provide specific guidance based on error type
                if (error.message.includes('Failed to fetch')) {
                    errorMessage = 'Connection failed. Please check your internet connection and try again.';
                } else if (error.message.includes('timeout')) {
                    errorMessage = 'Request timed out. The AI service might be busy. Please try again in a moment.';
                } else if (error.message.includes('401')) {
                    errorMessage = 'Authentication failed. Please check if the DeepSeek API key is configured correctly.';
                } else if (error.message.includes('429')) {
                    errorMessage = 'Too many requests. Please wait a moment before trying again.';
                } else if (error.message.includes('500')) {
                    errorMessage = 'Server error. Please try again or contact support if the problem persists.';
                }
                
                this.addErrorMessage(errorMessage);
                window.resumeAssistant.showToast('Failed to send message', 'error');
            }
        } finally {
            this.setWaitingState(false);
            this.focusInput();
        }
    }

    async sendMessageStreaming(message) {
        return new Promise((resolve, reject) => {
            // Create assistant message placeholder for streaming
            const assistantMessage = this.createStreamingMessageElement();
            this.appendMessage(assistantMessage);
            
            // Update state to show we're streaming
            this.setWaitingState(true, true);
            
            const contentElement = assistantMessage.querySelector('.message-content');
            let fullResponse = '';
            let hasStartedStreaming = false;
            
            // Create fetch request for streaming
            fetch('/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                function readStream() {
                    reader.read().then(({ done, value }) => {
                        if (done) {
                            // Stream completed naturally - finalize message
                            if (fullResponse) {
                                const formattedText = this.formatMessage(fullResponse);
                                contentElement.innerHTML = formattedText;
                                assistantMessage.classList.remove('streaming');
                                
                                this.chatHistory.push({
                                    role: 'assistant',
                                    content: fullResponse,
                                    timestamp: new Date()
                                });
                            }
                            resolve(fullResponse);
                            return;
                        }

                        // Process the chunk
                        const chunk = decoder.decode(value, { stream: true });
                        const lines = chunk.split('\n');

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    
                                    if (data.type === 'chunk' && data.chunk) {
                                        if (!hasStartedStreaming) {
                                            hasStartedStreaming = true;
                                            // Remove the initial cursor, we'll add it back with content
                                            contentElement.innerHTML = '';
                                        }
                                        fullResponse += data.chunk;
                                        this.updateStreamingMessage(contentElement, fullResponse);
                                    } else if (data.type === 'complete') {
                                        // Streaming completed - remove cursor and finalize message
                                        const formattedText = this.formatMessage(fullResponse);
                                        contentElement.innerHTML = formattedText;
                                        assistantMessage.classList.remove('streaming');
                                        
                                        this.chatHistory.push({
                                            role: 'assistant',
                                            content: fullResponse,
                                            timestamp: new Date()
                                        });
                                        resolve(fullResponse);
                                        return;
                                    } else if (data.type === 'error') {
                                        throw new Error(data.error);
                                    }
                                } catch (e) {
                                    // Skip invalid JSON
                                    continue;
                                }
                            }
                        }

                        // Continue reading
                        readStream.call(this);
                    }).catch(error => {
                        console.error('Stream reading error:', error);
                        reject(error);
                    });
                }

                readStream.call(this);
            })
            .catch(error => {
                console.error('Streaming request failed:', error);
                // Remove the assistant message placeholder on error
                if (assistantMessage && assistantMessage.parentNode) {
                    assistantMessage.parentNode.removeChild(assistantMessage);
                }
                reject(error);
            });
        });
    }

    createStreamingMessageElement() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-bubble assistant-message streaming';
        
        const timestamp = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageDiv.innerHTML = `
            <div class="message-header">
                <i class="fas fa-robot text-primary me-2"></i>
                <strong>Candidate Assistant</strong>
                <small class="text-muted ms-auto">${timestamp}</small>
            </div>
            <div class="message-content mt-2">
                <div class="streaming-cursor">▋</div>
            </div>
        `;

        // Add cursor animation
        const style = document.createElement('style');
        if (!document.getElementById('streaming-cursor-style')) {
            style.id = 'streaming-cursor-style';
            style.textContent = `
                .streaming-cursor {
                    animation: blink 1s infinite;
                    color: var(--primary-color);
                    font-weight: bold;
                }
                @keyframes blink {
                    0%, 50% { opacity: 1; }
                    51%, 100% { opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        return messageDiv;
    }

    updateStreamingMessage(contentElement, fullText) {
        // Format the message and add cursor
        const formattedText = this.formatMessage(fullText);
        contentElement.innerHTML = formattedText + '<span class="streaming-cursor">▋</span>';
        
        // Ensure scrolling works during streaming - force scroll immediately
        this.forceScrollToBottom();
    }

    forceScrollToBottom() {
        // Multiple methods to ensure scrolling works during streaming
        if (this.messagesContainer) {
            // Method 1: Direct scroll
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            
            // Method 2: Smooth scroll with immediate fallback
            try {
                this.messagesContainer.scrollTo({
                    top: this.messagesContainer.scrollHeight,
                    behavior: 'smooth'
                });
            } catch (e) {
                // Fallback for older browsers
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            }
        }
    }

    async sendMessageToAPI(message) {
        return await window.resumeAssistant.makeAPICall('/chat/message', {
            method: 'POST',
            body: JSON.stringify({
                message: message
            })
        });
    }

    sendQuickQuestion(question) {
        if (this.isWaiting) {
            window.resumeAssistant.showToast('Please wait for the current response', 'warning');
            return;
        }
        
        this.messageInput.value = question;
        this.autoResizeInput();
        this.focusInput();
        
        // Auto-send after a brief delay
        setTimeout(() => {
            this.handleSendMessage();
        }, 300);
    }

    addUserMessage(message) {
        const messageElement = this.createMessageElement(message, 'user');
        this.appendMessage(messageElement);
        this.chatHistory.push({ role: 'user', content: message, timestamp: new Date() });
    }

    addAssistantMessage(message) {
        const messageElement = this.createMessageElement(message, 'assistant');
        this.appendMessage(messageElement);
        this.chatHistory.push({ role: 'assistant', content: message, timestamp: new Date() });
    }

    addErrorMessage(errorText) {
        const messageElement = this.createErrorMessage(errorText);
        this.appendMessage(messageElement);
    }

    createMessageElement(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-bubble ${role}-message`;
        
        const timestamp = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        if (role === 'user') {
            messageDiv.innerHTML = `
                <div class="message-header">
                    <small class="text-muted me-auto">${timestamp}</small>
                    <strong>HR Manager</strong>
                    <i class="fas fa-user-tie text-success ms-2"></i>
                </div>
                <div class="message-content mt-2">
                    ${this.formatMessage(content)}
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-header">
                    <i class="fas fa-robot text-primary me-2"></i>
                    <strong>Candidate Assistant</strong>
                    <small class="text-muted ms-auto">${timestamp}</small>
                </div>
                <div class="message-content mt-2">
                    ${this.formatMessage(content)}
                </div>
            `;
        }

        return messageDiv;
    }

    createErrorMessage(errorText) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-bubble error-message';
        messageDiv.innerHTML = `
            <div class="message-header">
                <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                <strong>System</strong>
                <small class="text-muted ms-auto">Error</small>
            </div>
            <div class="message-content mt-2">
                <p class="text-danger mb-0">${errorText}</p>
                <small class="text-muted">Please try again or start a new session if the problem persists.</small>
            </div>
        `;
        messageDiv.style.background = 'linear-gradient(135deg, #f8d7da, #f1aeb5)';
        messageDiv.style.borderLeft = '4px solid #dc3545';
        
        return messageDiv;
    }

    formatMessage(content) {
        // Convert plain text to HTML with basic formatting
        let formatted = content
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Wrap in paragraph tags if not already formatted
        if (!formatted.includes('<p>')) {
            formatted = '<p>' + formatted + '</p>';
        }
        
        // Handle lists
        formatted = formatted.replace(/^[•\-\*]\s(.+)$/gm, '<li>$1</li>');
        if (formatted.includes('<li>')) {
            formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        }
        
        return formatted;
    }

    appendMessage(messageElement) {
        this.messagesContainer.appendChild(messageElement);
        
        // Scroll to bottom with smooth animation
        this.scrollToBottom();
        
        // Animate message appearance
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            messageElement.style.transition = 'all 0.4s ease';
            messageElement.style.opacity = '1';
            messageElement.style.transform = 'translateY(0)';
        }, 50);
    }

    scrollToBottom() {
        // Ensure the messages container exists and scroll to bottom
        if (this.messagesContainer) {
            setTimeout(() => {
                this.messagesContainer.scrollTo({
                    top: this.messagesContainer.scrollHeight,
                    behavior: 'smooth'
                });
            }, 100); // Small delay to ensure DOM is updated
        }
    }

    setWaitingState(isWaiting, isStreaming = false) {
        this.isWaiting = isWaiting;
        
        if (isWaiting) {
            // Never show typing indicator when streaming (to avoid duplicate messages)
            if (!isStreaming) {
                this.showTypingIndicator();
            } else {
                // Make sure typing indicator is hidden when streaming
                this.hideTypingIndicator();
            }
            window.resumeAssistant.showLoading(this.sendBtn, isStreaming ? 'Responding...' : 'Thinking...');
            this.messageInput.disabled = true;
        } else {
            this.hideTypingIndicator();
            window.resumeAssistant.hideLoading(this.sendBtn, 'Send');
            this.messageInput.disabled = false;
        }
    }

    showTypingIndicator() {
        // Remove existing typing indicator
        this.hideTypingIndicator();
        
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'message-bubble assistant-message typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-header">
                <i class="fas fa-robot text-primary me-2"></i>
                <strong>Candidate Assistant</strong>
                <small class="text-muted ms-auto">typing...</small>
            </div>
            <div class="message-content mt-2">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        // Add typing animation styles - Dark theme
        const style = document.createElement('style');
        style.textContent = `
            .typing-dots {
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }
            .typing-dots span {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: var(--primary-color);
                animation: typing 1.4s infinite ease-in-out both;
            }
            .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
            .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
            @keyframes typing {
                0%, 80%, 100% {
                    transform: scale(0.8);
                    opacity: 0.5;
                }
                40% {
                    transform: scale(1);
                    opacity: 1;
                }
            }
            /* Dark theme styling for typing indicator */
            .typing-indicator {
                background: linear-gradient(135deg, var(--bg-tertiary), #2d3748) !important;
                color: var(--text-primary) !important;
                border-left: 4px solid var(--primary-color) !important;
            }
            .typing-indicator .message-header {
                color: var(--text-primary) !important;
            }
            .typing-indicator .message-header strong {
                color: var(--text-primary) !important;
            }
            .typing-indicator .message-header small {
                color: var(--text-secondary) !important;
            }
        `;
        
        if (!document.getElementById('typing-style')) {
            style.id = 'typing-style';
            document.head.appendChild(style);
        }
        
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            // Remove all messages except the welcome message
            const messages = this.messagesContainer.querySelectorAll('.message-bubble:not(:first-child)');
            messages.forEach(message => message.remove());
            
            this.chatHistory = [];
            window.resumeAssistant.showToast('Chat cleared', 'info');
            this.focusInput();
        }
    }

    // Export chat history for debugging or saving
    exportChat() {
        const chatData = {
            timestamp: new Date().toISOString(),
            messages: this.chatHistory
        };
        
        const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-history-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }

    // Get current session stats
    getSessionStats() {
        return {
            totalMessages: this.chatHistory.length,
            userMessages: this.chatHistory.filter(m => m.role === 'user').length,
            assistantMessages: this.chatHistory.filter(m => m.role === 'assistant').length,
            sessionStarted: this.chatHistory.length > 0 ? this.chatHistory[0].timestamp : null,
            lastMessage: this.chatHistory.length > 0 ? this.chatHistory[this.chatHistory.length - 1].timestamp : null
        };
    }

    // Test API connection
    async testAPIConnection() {
        if (this.isWaiting) {
            window.resumeAssistant.showToast('Please wait for current operation to complete', 'warning');
            return;
        }

        try {
            window.resumeAssistant.showToast('Testing API connection...', 'info');
            
            const response = await fetch('/health');
            const data = await response.json();
            
            if (response.ok && data.status === 'healthy') {
                if (data.api_configured) {
                    if (data.api_test === 'success') {
                        window.resumeAssistant.showToast('✅ API connection successful!', 'success');
                        this.addSystemMessage('API test successful! DeepSeek API is connected and working properly.');
                    } else if (data.api_test.startsWith('failed_')) {
                        const statusCode = data.api_test.split('_')[1];
                        window.resumeAssistant.showToast(`❌ API test failed (${statusCode})`, 'error');
                        this.addSystemMessage(`API test failed with status code ${statusCode}. Please check your API key and account status.`);
                    } else if (data.api_test.startsWith('error_')) {
                        const errorMsg = data.api_test.split('_')[1];
                        window.resumeAssistant.showToast('❌ API connection error', 'error');
                        this.addSystemMessage(`API connection error: ${errorMsg}. Please check your internet connection.`);
                    }
                } else {
                    window.resumeAssistant.showToast('❌ API not configured', 'error');
                    this.addSystemMessage('DeepSeek API key is not configured. Please set up your .env file with a valid DEEPSEEK_API_KEY.');
                }
            } else {
                window.resumeAssistant.showToast('❌ Health check failed', 'error');
                this.addSystemMessage('System health check failed. Please contact support.');
            }
        } catch (error) {
            console.error('API test failed:', error);
            window.resumeAssistant.showToast('❌ Test failed', 'error');
            this.addSystemMessage('Failed to test API connection. Please check your internet connection and try again.');
        }
    }

    addSystemMessage(message) {
        const messageElement = this.createSystemMessage(message);
        this.appendMessage(messageElement);
    }

    createSystemMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-bubble system-message';
        
        const timestamp = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageDiv.innerHTML = `
            <div class="message-header">
                <i class="fas fa-cog text-info me-2"></i>
                <strong>System</strong>
                <small class="text-muted ms-auto">${timestamp}</small>
            </div>
            <div class="message-content mt-2">
                <p class="text-info mb-0">${message}</p>
            </div>
        `;
        
        messageDiv.style.background = 'linear-gradient(135deg, #e3f2fd, #bbdefb)';
        messageDiv.style.borderLeft = '4px solid #0dcaf0';
        
        return messageDiv;
    }
}

// Global functions for template access
function clearChat() {
    if (window.chatInterface) {
        window.chatInterface.clearChat();
    }
}

function testAPI() {
    if (window.chatInterface) {
        window.chatInterface.testAPIConnection();
    }
}

// Initialize chat interface when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();
}); 