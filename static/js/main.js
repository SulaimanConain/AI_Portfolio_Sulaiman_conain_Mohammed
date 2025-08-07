/**
 * Main JavaScript file for HR Resume Assistant
 * Contains common utilities and shared functionality
 */

// Global utilities and helper functions
class ResumeAssistant {
    constructor() {
        this.apiBaseUrl = '';
        this.init();
    }

    init() {
        console.log('HR Resume Assistant initialized');
        this.setupEventListeners();
        this.checkSessionStatus();
        this.initGlobalSoundEffects();
    }

    setupEventListeners() {
        // Global event listeners
        document.addEventListener('DOMContentLoaded', () => {
            this.fadeInElements();
        });
    }

    // Session management
    checkSessionStatus() {
        // This could be extended to check session validity
        console.log('Checking session status...');
    }

    // Reset session function (called from navigation)
    resetSession() {
        if (confirm('Are you sure you want to start a new session? This will clear the current resume and chat history.')) {
            fetch('/reset', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/';
                } else {
                    this.showToast('Failed to reset session', 'error');
                }
            })
            .catch(error => {
                console.error('Error resetting session:', error);
                this.showToast('Error resetting session', 'error');
            });
        }
    }

    initGlobalSoundEffects() {
        try {
            const links = document.querySelectorAll('a.nav-link, .navbar .btn');
            const hover = new Audio('https://actions.google.com/sounds/v1/cartoon/clang_and_wobble.ogg');
            const click = new Audio('https://actions.google.com/sounds/v1/cartoon/wood_plank_flicks.ogg');
            const defaultVolume = 0.3;
            hover.volume = defaultVolume;
            click.volume = defaultVolume;
            links.forEach(el => {
                el.addEventListener('mouseenter', () => { hover.currentTime = 0; hover.play().catch(()=>{}); });
                el.addEventListener('click', () => { click.currentTime = 0; click.play().catch(()=>{}); });
            });
        } catch (e) {
            console.warn('Sound effects init failed:', e);
        }
    }

    // Utility functions
    showToast(message, type = 'info', duration = 3000) {
        // Create toast notification
        const toastContainer = this.getOrCreateToastContainer();
        const toast = this.createToastElement(message, type);
        
        toastContainer.appendChild(toast);
        
        // Show with animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            this.removeToast(toast);
        }, duration);
    }

    getOrCreateToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    createToastElement(message, type) {
        const toast = document.createElement('div');
        const colorMap = {
            success: '#198754',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#0dcaf0'
        };
        
        toast.style.cssText = `
            background: white;
            border-left: 4px solid ${colorMap[type] || colorMap.info};
            border-radius: 8px;
            padding: 16px 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            max-width: 350px;
            opacity: 0;
            transform: translateX(100px);
            transition: all 0.3s ease;
            font-family: Inter, sans-serif;
            font-size: 14px;
            line-height: 1.4;
        `;
        
        toast.innerHTML = `
            <div style="display: flex; align-items: center;">
                <i class="fas fa-${this.getIconForType(type)} me-2" style="color: ${colorMap[type]}"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; margin-left: auto; font-size: 16px; cursor: pointer; color: #999;">×</button>
            </div>
        `;
        
        toast.classList.add('toast-notification');
        return toast;
    }

    getIconForType(type) {
        const iconMap = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return iconMap[type] || iconMap.info;
    }

    removeToast(toast) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    // Loading states
    showLoading(element, text = 'Loading...') {
        const spinner = element.querySelector('.spinner-border');
        const btnText = element.querySelector('.btn-text');
        
        if (spinner) spinner.classList.remove('d-none');
        if (btnText) btnText.textContent = text;
        element.disabled = true;
    }

    hideLoading(element, originalText) {
        const spinner = element.querySelector('.spinner-border');
        const btnText = element.querySelector('.btn-text');
        
        if (spinner) spinner.classList.add('d-none');
        if (btnText) btnText.textContent = originalText;
        element.disabled = false;
    }

    // Animation utilities
    fadeInElements() {
        const elements = document.querySelectorAll('.card, .feature-item');
        elements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'all 0.6s ease';
            
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    // Form validation utilities
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    validateRequired(value) {
        return value && value.trim().length > 0;
    }

    // API utilities
    async makeAPICall(url, options = {}) {
        console.log('Making API call to:', url, 'with options:', options);
        
        const defaultOptions = {
            headers: {}
        };

        // Only set Content-Type for JSON requests, not for FormData
        if (options.headers && !options.headers['Content-Type'] && 
            options.body && typeof options.body === 'string') {
            defaultOptions.headers['Content-Type'] = 'application/json';
        }

        const finalOptions = { ...defaultOptions, ...options };
        
        // Don't set Content-Type for FormData - let browser set it with boundary
        if (finalOptions.body instanceof FormData) {
            delete finalOptions.headers['Content-Type'];
        }

        console.log('Final options:', finalOptions);

        try {
            const response = await fetch(url, finalOptions);
            console.log('Response status:', response.status);
            console.log('Response headers:', [...response.headers.entries()]);
            
            const data = await response.json();
            console.log('Response data:', data);

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    // Text utilities
    truncateText(text, maxLength = 100) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    }

    // Date utilities
    formatDate(dateString) {
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString('en-US', options);
    }

    // Storage utilities
    setLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.warn('Could not save to localStorage:', e);
        }
    }

    getLocalStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.warn('Could not read from localStorage:', e);
            return defaultValue;
        }
    }
}

// Global functions that can be called from templates
function resetSession() {
    if (window.resumeAssistant) {
        window.resumeAssistant.resetSession();
    }
}

// Initialize the application
window.resumeAssistant = new ResumeAssistant();

// Export for use in other scripts
window.ResumeAssistant = ResumeAssistant; 