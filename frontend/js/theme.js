/**
 * LifeSync Dashboard - Theme Management
 */

const Theme = {
    storageKey: 'lifesync-theme',
    
    init() {
        // Always default to dark — light is never auto-restored on page load.
        // Users can toggle to light within a session, but every fresh load starts dark.
        this.apply('dark');
    },
    
    apply(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(this.storageKey, theme);
        
        // Sync with backend if logged in
        const user = localStorage.getItem('user');
        if (user) {
            API.put('/api/auth/preferences', { theme }).catch(() => {});
        }
    },
    
    toggle() {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = current === 'dark' ? 'light' : 'dark';
        document.body.classList.add('theme-transitioning');
        this.apply(newTheme);
        setTimeout(() => document.body.classList.remove('theme-transitioning'), 300);
    },
    
    get() {
        return document.documentElement.getAttribute('data-theme') || 'dark';
    }
};

// Auto-init on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Theme.init());
} else {
    Theme.init();
}
