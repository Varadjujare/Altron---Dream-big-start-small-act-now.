/**
 * LifeSync Dashboard - API Communication Layer
 */

const API = {
    baseUrl: '',
    
    async request(endpoint, options = {}) {
        const url = this.baseUrl + endpoint;
        const config = {
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            // Handle non-JSON responses (like 500 HTML pages)
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                const data = await response.json();
                if (!response.ok && !data.success) {
                    throw new Error(data.message || 'API request failed');
                }
                return data;
            } else {
                const text = await response.text();
                console.error('API Non-JSON Response:', text);
                throw new Error('Server error: Received non-JSON response');
            }
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    post(endpoint, data) {
        return this.request(endpoint, { method: 'POST', body: JSON.stringify(data) });
    },
    
    put(endpoint, data) {
        return this.request(endpoint, { method: 'PUT', body: JSON.stringify(data) });
    },
    
    patch(endpoint, data) {
        return this.request(endpoint, { method: 'PATCH', body: JSON.stringify(data) });
    },
    
    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// Auth Helper
const Auth = {
    async check() {
        const result = await API.get('/api/auth/check');
        return result.authenticated;
    },
    
    async requireAuth() {
        const isAuth = await this.check();
        if (!isAuth) {
            window.location.href = '/';
            return false;
        }
        return true;
    },
    
    getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },
    
    async logout() {
        await API.post('/api/auth/logout');
        localStorage.removeItem('user');
        sessionStorage.removeItem('introShown');
        window.location.href = '/';
    }
};

// Toast Notifications
const Toast = {
    container: null,
    
    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },
    
    show(message, type = 'info', duration = 3000) {
        this.init();
        const toast = document.createElement('div');
        toast.className = 'toast';
        const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
        toast.innerHTML = `<span style="color: var(--${type})">${icons[type]}</span><span>${message}</span>`;
        this.container.appendChild(toast);
        setTimeout(() => { toast.style.animation = 'slideIn 0.3s ease reverse forwards'; setTimeout(() => toast.remove(), 300); }, duration);
    },
    
    success(message) { this.show(message, 'success'); },
    error(message) { this.show(message, 'error'); },
    warning(message) { this.show(message, 'warning'); },
    info(message) { this.show(message, 'info'); }
};

// Date Utilities
const DateUtils = {
    format(date, format = 'YYYY-MM-DD') {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        if (format === 'YYYY-MM-DD') return `${year}-${month}-${day}`;
        if (format === 'display') return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        return `${year}-${month}-${day}`;
    },
    
    today() { return this.format(new Date()); },
    
    getDaysInMonth(year, month) { return new Date(year, month + 1, 0).getDate(); },
    
    getMonthName(month) { return new Date(2000, month, 1).toLocaleDateString('en-US', { month: 'long' }); },
    
    getDayName(date) { return new Date(date).toLocaleDateString('en-US', { weekday: 'short' }); }
};
