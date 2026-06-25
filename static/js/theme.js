// ============================================================
// theme.js - 暗黑模式（懒加载）
// ============================================================

console.log('🌙 暗黑模式模块已加载');

const themeBtn = document.getElementById('themeBtn');

let darkMode = localStorage.getItem('darkMode') === 'true';

function applyTheme() {
    if (darkMode) {
        document.body.classList.add('dark-mode');
        themeBtn.textContent = '☀️';
    } else {
        document.body.classList.remove('dark-mode');
        themeBtn.textContent = '🌙';
    }
}

export function toggleTheme() {
    darkMode = !darkMode;
    localStorage.setItem('darkMode', darkMode);
    applyTheme();
}

// 初始化
applyTheme();

// 直接挂载到 window，供 core.js 调用
window.toggleTheme = toggleTheme;