/**
 * LifeSync Dashboard - Authentication Logic
 */

const AuthPage = {
    async init() {
        // Check if already authenticated
        const isAuth = await Auth.check();
        if (isAuth && !window.location.pathname.includes('dashboard')) {
            window.location.href = '/dashboard';
        }
    }
};

// Sidebar User Info
const UserInfo = {
    async load() {
        const user = Auth.getUser();
        if (user) {
            const nameEl = document.querySelector('.user-name');
            const emailEl = document.querySelector('.user-email');
            const avatarEl = document.querySelector('.user-avatar');
            if (nameEl) nameEl.textContent = user.username;
            if (emailEl) emailEl.textContent = user.email;
            if (avatarEl) avatarEl.textContent = user.username.charAt(0).toUpperCase();
        }
    }
};
