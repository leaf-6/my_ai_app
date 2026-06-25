// ============================================================
// rename.js - 重命名对话（懒加载）
// ============================================================

console.log('✏️ 重命名模块已加载');

const renameModal = document.getElementById('renameModal');
const renameInput = document.getElementById('renameInput');
const renameCancel = document.getElementById('renameCancel');
const renameConfirm = document.getElementById('renameConfirm');
const currentChatTitle = document.getElementById('currentChatTitle');

let currentSessionId = null;

// 从全局获取 currentSessionId
function getCurrentSessionId() {
    // 尝试从 window 获取
    if (window.currentSessionId !== undefined) {
        return window.currentSessionId;
    }
    // 或者从 localStorage 获取
    return localStorage.getItem('currentSessionId');
}

export function openRenameModal() {
    const currentTitle = currentChatTitle.textContent;
    renameInput.value = currentTitle;
    renameModal.classList.add('show');
    renameInput.focus();
    renameInput.select();

    // 存储当前会话ID
    currentSessionId = getCurrentSessionId();
}

function closeRenameModal() {
    renameModal.classList.remove('show');
}

async function confirmRename() {
    const newTitle = renameInput.value.trim();
    if (!newTitle) {
        alert('请输入新名称');
        return;
    }
    if (!currentSessionId) {
        alert('没有选中的对话');
        return;
    }

    try {
        // 更新前端显示（后端需要加 PATCH 接口）
        currentChatTitle.textContent = newTitle;
        // 刷新侧边栏
        if (window.loadSessions && window.renderHistoryList) {
            const sessions = await window.loadSessions();
            window.renderHistoryList(sessions, currentSessionId);
        }
        closeRenameModal();
    } catch (err) {
        alert('重命名失败: ' + err.message);
    }
}

// 事件绑定
renameCancel.addEventListener('click', closeRenameModal);
renameConfirm.addEventListener('click', confirmRename);

// 点击弹窗外关闭
renameModal.addEventListener('click', function(e) {
    if (e.target === this) {
        closeRenameModal();
    }
});

// 回车确认
renameInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        confirmRename();
    }
});

// 挂载到 window
window.openRenameModal = openRenameModal;