/**
 * DocGenius Main Application
 * Coordinates all application components and provides the main app interface
 */

import FileHandler from './fileHandler.js';
import ChatHandler from './chatHandler.js';
import UIHandler from './uiHandler.js';

class DocGeniusApp {
    constructor() {
        this.fileHandler = null;
        this.chatHandler = null;
        this.uiHandler = null;
        this.activeFile = null;
        
        this.init();
    }

    async init() {
        try {
            // Show loading
            this.showInitialLoading(true);
            
            // Initialize components
            this.uiHandler = new UIHandler();
            this.fileHandler = new FileHandler();
            this.chatHandler = new ChatHandler();
            
            // Set up component communication
            this.setupComponentCommunication();
            
            // Setup global error handling
            this.setupErrorHandling();
            
            // Initialize app state
            await this.initializeAppState();
            
            // Hide loading
            this.showInitialLoading(false);
            
            console.log('DocGenius app initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize DocGenius app:', error);
            this.handleInitializationError(error);
        }
    }

    setupComponentCommunication() {
        // Make components accessible to each other through the global app instance
        window.app = this;
        
        // Set up specific communication patterns
        this.setupFileSelection();
    }

    setupFileSelection() {
        // When a file is selected, update the chat interface
        const originalSelectFile = this.fileHandler.selectFile.bind(this.fileHandler);
        this.fileHandler.selectFile = (fileId) => {
            originalSelectFile(fileId);
            const file = this.fileHandler.getActiveFile();
            this.setActiveFile(file);
        };
    }

    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.showToast('An unexpected error occurred', 'error');
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showToast('An unexpected error occurred', 'error');
            event.preventDefault();
        });

        // Network error detection
        window.addEventListener('offline', () => {
            this.showToast('You are now offline. Some features may not work.', 'error');
        });

        window.addEventListener('online', () => {
            this.showToast('You are back online!', 'success');
        });
    }

    async initializeAppState() {
        // Load initial data
        await Promise.all([
            this.fileHandler?.loadExistingFiles(),
            this.chatHandler?.loadConversations()
        ]);

        // Check if there are existing files and auto-select the first one
        const files = this.fileHandler?.getAllFiles();
        if (files && files.length > 0) {
            this.fileHandler?.selectFile('file_0');
        }

        // Set up auto-save if enabled
        if (this.uiHandler?.getSettings().autoSave) {
            this.setupAutoSave();
        }
    }

    setupAutoSave() {
        // Periodically save application state
        setInterval(() => {
            this.saveAppState();
        }, 30000); // Save every 30 seconds

        // Save on page unload
        window.addEventListener('beforeunload', () => {
            this.saveAppState();
        });
    }

    saveAppState() {
        try {
            const state = {
                activeFileId: this.activeFileId,
                timestamp: new Date().toISOString()
            };
            localStorage.setItem('docgenius_app_state', JSON.stringify(state));
        } catch (error) {
            console.error('Failed to save app state:', error);
        }
    }

    loadAppState() {
        try {
            const saved = localStorage.getItem('docgenius_app_state');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (error) {
            console.error('Failed to load app state:', error);
        }
        return null;
    }

    showInitialLoading(show) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.setAttribute('aria-hidden', !show);
        }
    }

    handleInitializationError(error) {
        // Hide loading
        this.showInitialLoading(false);
        
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'initialization-error';
        errorDiv.innerHTML = `
            <div class="error-content">
                <h2>Failed to Initialize DocGenius</h2>
                <p>There was an error starting the application. Please refresh the page to try again.</p>
                <button onclick="window.location.reload()" class="btn btn-primary">
                    Refresh Page
                </button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
    }

    // Public API methods for components to use

    setActiveFile(file) {
        this.activeFile = file;
        
        // Update UI to show file context
        if (file) {
            // Show chat input if file is selected
            const chatInputContainer = document.getElementById('chatInputContainer');
            if (chatInputContainer) {
                chatInputContainer.hidden = false;
            }
            
            // Update welcome screen
            const welcomeScreen = document.getElementById('welcomeScreen');
            if (welcomeScreen) {
                welcomeScreen.hidden = true;
            }
        } else {
            // Hide chat input if no file selected
            const chatInputContainer = document.getElementById('chatInputContainer');
            if (chatInputContainer) {
                chatInputContainer.hidden = true;
            }
            
            // Show welcome screen
            const welcomeScreen = document.getElementById('welcomeScreen');
            if (welcomeScreen) {
                welcomeScreen.hidden = false;
            }
        }
    }

    getActiveFile() {
        return this.activeFile;
    }

    showToast(message, type = 'error', duration = 5000) {
        if (this.uiHandler) {
            this.uiHandler.showToast(message, type, duration);
        } else {
            // Fallback if UI handler not ready
            console.log(`Toast (${type}): ${message}`);
        }
    }

    showLoading(show) {
        if (this.uiHandler) {
            this.uiHandler.showLoading(show);
        }
    }

    // Component access methods
    getFileHandler() {
        return this.fileHandler;
    }

    getChatHandler() {
        return this.chatHandler;
    }

    getUIHandler() {
        return this.uiHandler;
    }

    // Utility methods
    async refreshAll() {
        this.showLoading(true);
        try {
            await Promise.all([
                this.fileHandler?.refreshFiles(),
                this.chatHandler?.refreshConversations()
            ]);
            this.showToast('Data refreshed successfully', 'success');
        } catch (error) {
            console.error('Refresh failed:', error);
            this.showToast('Failed to refresh data', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async clearAllData() {
        if (!confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
            return;
        }

        this.showLoading(true);
        try {
            // Clear conversations
            await this.chatHandler?.handleClearConversations();
            
            // Clear local storage
            localStorage.removeItem('docgenius_app_state');
            localStorage.removeItem('docgenius_settings');
            
            // Reset active file
            this.setActiveFile(null);
            
            this.showToast('All data cleared successfully', 'success');
        } catch (error) {
            console.error('Clear data failed:', error);
            this.showToast('Failed to clear all data', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Keyboard shortcuts
    setupGlobalKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Ctrl/Cmd + Shift + R for refresh
            if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'R') {
                event.preventDefault();
                this.refreshAll();
            }
            
            // Ctrl/Cmd + Shift + D for clear data (debug)
            if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'D') {
                event.preventDefault();
                this.clearAllData();
            }
        });
    }

    // Health check
    async performHealthCheck() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            
            if (response.ok && data.status === 'healthy') {
                console.log('Health check passed:', data);
                return true;
            } else {
                console.warn('Health check failed:', data);
                return false;
            }
        } catch (error) {
            console.error('Health check error:', error);
            return false;
        }
    }

    // Analytics (if needed)
    trackEvent(event, properties = {}) {
        // Placeholder for analytics tracking
        console.log('Event tracked:', event, properties);
    }

    // Development helpers
    getDebugInfo() {
        return {
            version: '2.0.0',
            userAgent: navigator.userAgent,
            activeFile: this.activeFile,
            fileCount: this.fileHandler?.getAllFiles().length || 0,
            conversationCount: this.chatHandler?.conversations.length || 0,
            settings: this.uiHandler?.getSettings(),
            timestamp: new Date().toISOString()
        };
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new DocGeniusApp();
});

// For debugging in console
window.DocGeniusApp = DocGeniusApp;