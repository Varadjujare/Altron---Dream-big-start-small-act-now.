
/**
 * Command Palette Controller
 */
const CommandPalette = {
    isOpen: false,
    activeIndex: 0,
    commands: [
        { id: 'home', title: 'Go to Home', icon: '🏠', action: () => window.location.href = '/home' },
        { id: 'dashboard', title: 'Go to Dashboard', icon: '📊', action: () => window.location.href = '/dashboard' },
        { id: 'tasks', title: 'Go to Tasks', icon: '📝', action: () => window.location.href = '/tasks' },
        { id: 'habits', title: 'Go to Habits', icon: '✅', action: () => window.location.href = '/habits' },
        { id: 'calendar', title: 'Go to Calendar', icon: '📅', action: () => window.location.href = '/calendar' },
        { id: 'analytics', title: 'Go to Analytics', icon: '📈', action: () => window.location.href = '/analytics' },
        { id: 'theme', title: 'Toggle Theme', icon: '🌓', action: () => Theme.toggle() },
        { id: 'logout', title: 'Logout', icon: '🚪', action: () => Auth.logout() }
    ],

    init() {
        this.render();
        this.bindEvents();
    },

    render() {
        if (document.getElementById('cmdPalette')) return;

        const html = `
            <div class="cmd-overlay" id="cmdOverlay">
                <div class="cmd-modal">
                    <div class="cmd-header">
                        <input type="text" class="cmd-input" id="cmdInput" placeholder="Type a command or search...">
                    </div>
                    <div class="cmd-list" id="cmdList"></div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', html);
    },

    bindEvents() {
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.toggle();
            }
            
            if (!this.isOpen) return;

            if (e.key === 'Escape') this.close();
            if (e.key === 'ArrowDown') this.navigate(1);
            if (e.key === 'ArrowUp') this.navigate(-1);
            if (e.key === 'Enter') this.execute();
        });

        document.getElementById('cmdInput').addEventListener('input', (e) => this.filter(e.target.value));
        document.getElementById('cmdOverlay').addEventListener('click', (e) => {
            if (e.target === document.getElementById('cmdOverlay')) this.close();
        });
    },

    toggle() {
        this.isOpen ? this.close() : this.open();
    },

    open() {
        this.isOpen = true;
        document.getElementById('cmdOverlay').classList.add('open');
        document.getElementById('cmdInput').value = '';
        document.getElementById('cmdInput').focus();
        this.filter('');
    },

    close() {
        this.isOpen = false;
        document.getElementById('cmdOverlay').classList.remove('open');
    },

    filter(query) {
        const filtered = this.commands.filter(cmd => 
            cmd.title.toLowerCase().includes(query.toLowerCase())
        );
        this.renderList(filtered);
    },

    renderList(items) {
        const list = document.getElementById('cmdList');
        if (items.length === 0) {
            list.innerHTML = '<div class="text-muted p-2 text-center">No commands found</div>';
            return;
        }
        
        this.currentItems = items;
        this.activeIndex = 0;

        list.innerHTML = items.map((cmd, index) => `
            <div class="cmd-item ${index === 0 ? 'active' : ''}" data-index="${index}" onclick="CommandPalette.executeIndex(${index})">
                <div class="flex items-center">
                    <span class="cmd-item-icon">${cmd.icon}</span>
                    <span>${cmd.title}</span>
                </div>
                ${index < 9 ? `<span class="cmd-shortcut">⏎</span>` : ''}
            </div>
        `).join('');
    },

    navigate(dir) {
        const items = document.querySelectorAll('.cmd-item');
        if (!items.length) return;

        items[this.activeIndex].classList.remove('active');
        this.activeIndex = (this.activeIndex + dir + items.length) % items.length;
        items[this.activeIndex].classList.add('active');
        items[this.activeIndex].scrollIntoView({ block: 'nearest' });
    },

    execute() {
        if (this.currentItems && this.currentItems[this.activeIndex]) {
            this.currentItems[this.activeIndex].action();
            this.close();
        }
    },

    executeIndex(index) {
        this.activeIndex = index;
        this.execute();
    }
};

// Auto-init
document.addEventListener('DOMContentLoaded', () => CommandPalette.init());
