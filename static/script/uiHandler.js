/**
 * DocGenius UI Handler
 * Handles UI interactions, modals, settings, and responsive behavior
 */

class UIHandler {
    constructor() {
        this.sidebarOpen = false;
        this.currentTheme = 'light';
        this.settings = {
            theme: 'light',
            autoSave: true
        };
        
        this.initializeElements();
        this.bindEvents();
        this.loadSettings();
        this.setupResponsiveDesign();
    }

    initializeElements() {
        // Layout elements
        this.app = document.getElementById('app');
        this.sidebar = document.getElementById('sidebar');
        this.mainContent = document.getElementById('mainContent');
        
        // Mobile elements
        this.mobileMenuToggle = document.getElementById('mobileMenuToggle');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        
        // Modal elements
        this.modalOverlay = document.getElementById('modalOverlay');
        this.settingsModal = document.getElementById('settingsModal');
        this.helpModal = document.getElementById('helpModal');
        
        // Header buttons
        this.settingsBtn = document.getElementById('settingsBtn');
        this.helpBtn = document.getElementById('helpBtn');
        
        // Toast elements
        this.errorToast = document.getElementById('errorToast');
        this.successToast = document.getElementById('successToast');
        
        // Settings elements
        this.themeSelect = document.getElementById('themeSelect');
        this.autoSaveCheckbox = document.getElementById('autoSaveCheckbox');
        
        // Loading overlay
        this.loadingOverlay = document.getElementById('loadingOverlay');
    }

    bindEvents() {
        // Mobile menu toggle
        this.mobileMenuToggle?.addEventListener('click', () => this.toggleSidebar());
        this.sidebarToggle?.addEventListener('click', () => this.toggleSidebar());
        
        // Modal triggers
        this.settingsBtn?.addEventListener('click', () => this.openModal('settings'));
        this.helpBtn?.addEventListener('click', () => this.openModal('help'));
        
        // Modal overlay click to close
        this.modalOverlay?.addEventListener('click', (e) => {
            if (e.target === this.modalOverlay) {
                this.closeModal();
            }
        });
        
        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });
        
        // Settings
        this.themeSelect?.addEventListener('change', (e) => this.changeTheme(e.target.value));
        this.autoSaveCheckbox?.addEventListener('change', (e) => this.toggleAutoSave(e.target.checked));
        
        // Toast close buttons
        document.querySelectorAll('.toast-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const toast = e.target.closest('.toast');
                this.hideToast(toast);
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Resize handler
        window.addEventListener('resize', () => this.handleResize());
        
        // Click outside sidebar to close on mobile
        document.addEventListener('click', (e) => this.handleOutsideClick(e));
    }

    toggleSidebar() {
        this.sidebarOpen = !this.sidebarOpen;
        this.updateSidebarState();
    }

    updateSidebarState() {
        if (this.sidebar) {
            this.sidebar.classList.toggle('open', this.sidebarOpen);
        }
        
        // Add/remove overlay on mobile
        if (window.innerWidth <= 1024) {
            this.toggleSidebarOverlay(this.sidebarOpen);
        }
        
        // Update body scroll
        document.body.style.overflow = (this.sidebarOpen && window.innerWidth <= 1024) ? 'hidden' : '';
    }

    toggleSidebarOverlay(show) {
        let overlay = document.querySelector('.sidebar-overlay');
        
        if (show && !overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            overlay.addEventListener('click', () => this.toggleSidebar());
            document.body.appendChild(overlay);
            
            // Trigger reflow and add active class
            setTimeout(() => overlay.classList.add('active'), 10);
        } else if (!show && overlay) {
            overlay.classList.remove('active');
            setTimeout(() => overlay.remove(), 300);
        }
    }

    handleOutsideClick(event) {
        if (this.sidebarOpen && window.innerWidth <= 1024) {
            if (!this.sidebar?.contains(event.target) && 
                !this.mobileMenuToggle?.contains(event.target) &&
                !this.sidebarToggle?.contains(event.target)) {
                this.toggleSidebar();
            }
        }
    }

    openModal(type) {
        if (!this.modalOverlay) return;
        
        // Hide all modals first
        document.querySelectorAll('.modal').forEach(modal => {
            modal.hidden = true;
        });
        
        // Show specific modal
        if (type === 'settings' && this.settingsModal) {
            this.settingsModal.hidden = false;
            this.updateSettingsUI();
        } else if (type === 'help' && this.helpModal) {
            this.helpModal.hidden = false;
        }
        
        // Show overlay
        this.modalOverlay.hidden = false;
        
        // Focus management
        setTimeout(() => {
            const focusable = this.modalOverlay.querySelector('button, input, select');
            focusable?.focus();
        }, 100);
    }

    closeModal() {
        if (this.modalOverlay) {
            this.modalOverlay.hidden = true;
        }
        
        // Hide all modals
        document.querySelectorAll('.modal').forEach(modal => {
            modal.hidden = true;
        });
        
        // Save settings when closing settings modal
        this.saveSettings();
    }

    handleKeyboardShortcuts(event) {
        // Escape to close modal
        if (event.key === 'Escape') {
            if (!this.modalOverlay?.hidden) {
                this.closeModal();
            } else if (this.sidebarOpen && window.innerWidth <= 1024) {
                this.toggleSidebar();
            }
        }
        
        // Ctrl/Cmd + ? for help
        if ((event.ctrlKey || event.metaKey) && event.key === '?') {
            event.preventDefault();
            this.openModal('help');
        }
        
        // Ctrl/Cmd + , for settings
        if ((event.ctrlKey || event.metaKey) && event.key === ',') {
            event.preventDefault();
            this.openModal('settings');
        }
    }

    changeTheme(theme) {
        this.settings.theme = theme;
        this.currentTheme = theme;
        this.applyTheme(theme);
        this.saveSettings();
    }

    applyTheme(theme) {
        const body = document.body;
        
        // Remove existing theme classes
        body.classList.remove('theme-light', 'theme-dark', 'theme-auto');
        
        // Add new theme class
        body.classList.add(`theme-${theme}`);
        
        // Set data attribute for CSS
        body.dataset.theme = theme;
        
        // For auto theme, check system preference
        if (theme === 'auto') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            body.classList.add(prefersDark ? 'theme-dark' : 'theme-light');
        }
    }

    toggleAutoSave(enabled) {
        this.settings.autoSave = enabled;
        this.saveSettings();
    }

    updateSettingsUI() {
        if (this.themeSelect) {
            this.themeSelect.value = this.settings.theme;
        }
        if (this.autoSaveCheckbox) {
            this.autoSaveCheckbox.checked = this.settings.autoSave;
        }
    }

    loadSettings() {
        try {
            const saved = localStorage.getItem('docgenius_settings');
            if (saved) {
                this.settings = { ...this.settings, ...JSON.parse(saved) };
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
        
        // Apply loaded settings
        this.applyTheme(this.settings.theme);
        this.updateSettingsUI();
    }

    saveSettings() {
        try {
            localStorage.setItem('docgenius_settings', JSON.stringify(this.settings));
        } catch (error) {
            console.error('Failed to save settings:', error);
        }
    }

    showToast(message, type = 'error', duration = 5000) {
        const toast = type === 'success' ? this.successToast : this.errorToast;
        if (!toast) return;
        
        // Set message
        const messageElement = toast.querySelector('.toast-message');
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        // Show toast
        toast.classList.add('show');
        
        // Auto-hide after duration
        setTimeout(() => {
            this.hideToast(toast);
        }, duration);
    }

    hideToast(toast) {
        if (toast) {
            toast.classList.remove('show');
        }
    }

    showLoading(show) {
        if (this.loadingOverlay) {
            this.loadingOverlay.setAttribute('aria-hidden', !show);
        }
    }

    setupResponsiveDesign() {
        // Initial setup
        this.handleResize();
        
        // Watch for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', () => {
                if (this.settings.theme === 'auto') {
                    this.applyTheme('auto');
                }
            });
        }
    }

    handleResize() {
        const isMobile = window.innerWidth <= 1024;
        
        // Close sidebar on desktop resize
        if (!isMobile && this.sidebarOpen) {
            this.sidebarOpen = false;
            this.updateSidebarState();
        }
        
        // Update mobile menu toggle visibility
        if (this.mobileMenuToggle) {
            this.mobileMenuToggle.style.display = isMobile ? 'flex' : 'none';
        }
        
        // Remove body scroll lock if not mobile
        if (!isMobile) {
            document.body.style.overflow = '';
        }
    }

    // Animation utilities
    fadeIn(element, duration = 300) {
        if (!element) return Promise.resolve();
        
        return new Promise(resolve => {
            element.style.opacity = '0';
            element.style.display = 'block';
            
            const animation = element.animate([
                { opacity: 0 },
                { opacity: 1 }
            ], {
                duration,
                easing: 'ease-out'
            });
            
            animation.onfinish = () => {
                element.style.opacity = '';
                resolve();
            };
        });
    }

    fadeOut(element, duration = 300) {
        if (!element) return Promise.resolve();
        
        return new Promise(resolve => {
            const animation = element.animate([
                { opacity: 1 },
                { opacity: 0 }
            ], {
                duration,
                easing: 'ease-in'
            });
            
            animation.onfinish = () => {
                element.style.display = 'none';
                element.style.opacity = '';
                resolve();
            };
        });
    }

    slideDown(element, duration = 300) {
        if (!element) return Promise.resolve();
        
        return new Promise(resolve => {
            const height = element.scrollHeight;
            element.style.height = '0';
            element.style.overflow = 'hidden';
            element.style.display = 'block';
            
            const animation = element.animate([
                { height: '0px' },
                { height: `${height}px` }
            ], {
                duration,
                easing: 'ease-out'
            });
            
            animation.onfinish = () => {
                element.style.height = '';
                element.style.overflow = '';
                resolve();
            };
        });
    }

    // Utility methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Public API
    isMobile() {
        return window.innerWidth <= 1024;
    }

    getSettings() {
        return { ...this.settings };
    }

    updateSetting(key, value) {
        this.settings[key] = value;
        this.saveSettings();
    }
}

// Export for module usage
export default UIHandler;