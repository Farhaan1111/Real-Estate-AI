// Common functionality for all pages
class RealEstateApp {
    constructor() {
        this.initTheme();
        this.initAnimations();
        this.initEventListeners();
    }

    initTheme() {
        // Theme initialization
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
    }

    initAnimations() {
        // Initialize scroll animations
        this.initScrollAnimations();
        
        // Initialize floating animations
        this.initFloatingElements();
    }

    initEventListeners() {
        // Global event listeners
        document.addEventListener('click', this.handleGlobalClick.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    }

    initScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe elements with animation classes
        document.querySelectorAll('.feature-card, .stat-card, .card-dark').forEach(el => {
            observer.observe(el);
        });
    }

    initFloatingElements() {
        // Add floating animation to specific elements
        const floatingElements = document.querySelectorAll('.feature-icon, .hero-title');
        floatingElements.forEach(el => {
            el.classList.add('floating');
        });
    }

    handleGlobalClick(e) {
        // Handle quick action clicks
        if (e.target.closest('.quick-action')) {
            e.preventDefault();
            const action = e.target.closest('.quick-action');
            this.handleQuickAction(action);
        }
    }

    handleKeyboardShortcuts(e) {
        // Global keyboard shortcuts
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            document.querySelector('input[type="search"]')?.focus();
        }
    }

    handleQuickAction(action) {
        // Handle quick action functionality
        const text = action.textContent.trim();
        console.log('Quick action:', text);
        
        // Add visual feedback
        action.classList.add('pulse');
        setTimeout(() => {
            action.classList.remove('pulse');
        }, 600);
    }

    // Utility methods
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : 'info'}-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    formatNumber(number) {
        return new Intl.NumberFormat().format(number);
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.realEstateApp = new RealEstateApp();
});