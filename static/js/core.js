// ============================================================
// core.js - 核心功能
// ============================================================

const API_BASE = 'http://127.0.0.1:8000';

// ============================================================
// 认证相关
// ============================================================
function getToken() {
    return localStorage.getItem('ai_token');
}

function getUserId() {
    return localStorage.getItem('ai_user_id');
}

function getUsername() {
    return localStorage.getItem('ai_username') || '用户';
}

function logout() {
    localStorage.removeItem('ai_token');
    localStorage.removeItem('ai_user_id');
    localStorage.removeItem('ai_username');
    window.location.href = '/static/login.html';
}

const token = getToken();
if (!token) {
    window.location.href = '/static/login.html';
}

// ============================================================
// API 调用
// ============================================================
async function apiFetch(path, options = {}) {
    try {
        const res = await fetch(API_BASE + path, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token,
                ...(options.headers || {})
            }
        });
        if (res.status === 401) {
            logout();
            return;
        }
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: '请求失败' }));
            throw new Error(err.detail || '请求失败');
        }
        return res.json();
    } catch (err) {
        if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
            throw new Error('网络连接失败，请检查服务是否启动');
        }
        throw err;
    }
}

async function loadSessions() {
    return apiFetch('/api/sessions');
}

async function loadMessages(sessionId) {
    return apiFetch(`/api/sessions/${sessionId}/messages`);
}

async function createSession(title = '新对话') {
    return apiFetch('/api/sessions', {
        method: 'POST',
        body: JSON.stringify({ title })
    });
}

async function deleteSession(sessionId) {
    return apiFetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
}

// ============================================================
// 全局状态
// ============================================================
let currentSessionId = null;
let isWaiting = false;

// ============================================================
// DOM 引用
// ============================================================
const messagesEl = document.getElementById('messageContainer');
const inputEl = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const historyListEl = document.getElementById('historyList');
const newChatBtn = document.getElementById('newChatBtn');
const currentChatTitle = document.getElementById('currentChatTitle');
const modelSelect = document.getElementById('modelSelect');

// ============================================================
// 按钮引用（用于懒加载）
// ============================================================
const renameBtn = document.getElementById('renameBtn');
const exportBtn = document.getElementById('exportBtn');
const themeBtn = document.getElementById('themeBtn');
const searchInput = document.getElementById('searchInput');
const voiceInputBtn = document.getElementById('voiceInputBtn');
const voiceOutputBtn = document.getElementById('voiceOutputBtn');

const scrollBtn = document.getElementById('scrollBottomBtn');

// 显示用户名
const header = document.querySelector('.chat-header');
if (header) {
    const userInfo = document.createElement('span');
    userInfo.style.cssText = 'font-size: 13px; color: #64748b; margin-left: 4px;';
    userInfo.textContent = '👤 ' + getUsername();
    header.insertBefore(userInfo, renameBtn);
}

// ============================================================
// 滚动按钮逻辑
// ============================================================
if (scrollBtn) {
    messagesEl.addEventListener('scroll', function() {
        const isAtBottom = messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 100;
        if (isAtBottom) {
            scrollBtn.classList.remove('visible');
        } else {
            scrollBtn.classList.add('visible');
        }
    });

    scrollBtn.addEventListener('click', function() {
        messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
    });
}

// ============================================================
// 骨架屏
// ============================================================
function renderSkeleton() {
    const div = document.createElement('div');
    div.className = 'skeleton-message';
    div.innerHTML = `
        <div class="skeleton skeleton-text skeleton-text medium"></div>
        <div class="skeleton skeleton-text skeleton-text long"></div>
        <div class="skeleton skeleton-text skeleton-text short"></div>
    `;
    return div;
}

// ============================================================
// UI 渲染
// ============================================================
function renderMessage(text, sender, timestamp) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;

    if (sender === 'ai') {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.textContent = '📋';
        copyBtn.title = '复制';
        copyBtn.style.cssText = `
            position: absolute;
            top: 4px;
            right: 6px;
            background: rgba(255,255,255,0.85);
            border: 1px solid #d0d7de;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            padding: 2px 6px;
            color: #64748b;
            z-index: 10;
        `;
        copyBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const textContent = div.textContent || div.innerText;
            navigator.clipboard.writeText(textContent).then(() => {
                copyBtn.textContent = '✅';
                setTimeout(() => { copyBtn.textContent = '📋'; }, 1500);
            }).catch(() => {
                const range = document.createRange();
                range.selectNode(div);
                window.getSelection().removeAllRanges();
                window.getSelection().addRange(range);
                document.execCommand('copy');
                copyBtn.textContent = '✅';
                setTimeout(() => { copyBtn.textContent = '📋'; }, 1500);
            });
        });
        div.appendChild(copyBtn);
    }

    const displayText = text.replace(/\n/g, '<br>');
    div.innerHTML = displayText;

    if (timestamp) {
        const timeSpan = document.createElement('div');
        timeSpan.className = 'time';
        const date = new Date(timestamp);
        timeSpan.textContent = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
        div.appendChild(timeSpan);
    }

    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    return div;
}

function renderMessages(messages) {
    messagesEl.innerHTML = '';
    if (!messages || messages.length === 0) {
        renderMessage('👋 你好！我是你的 AI 助手，有什么问题尽管问我吧！', 'ai');
        return;
    }
    for (const msg of messages) {
        renderMessage(msg.text, msg.sender, msg.timestamp);
    }
    messagesEl.scrollTop = messagesEl.scrollHeight;

    if (scrollBtn) {
        setTimeout(() => {
            const isAtBottom = messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 100;
            if (isAtBottom) {
                scrollBtn.classList.remove('visible');
            } else {
                scrollBtn.classList.add('visible');
            }
        }, 50);
    }
}

function renderHistoryList(sessions, currentId) {
    historyListEl.innerHTML = '';
    if (!sessions || sessions.length === 0) {
        historyListEl.innerHTML = '<div class="empty-history">暂无历史对话<br>点击「新建」开始聊天</div>';
        return;
    }
    for (const s of sessions) {
        const div = document.createElement('div');
        div.className = 'history-item' + (s.id === currentId ? ' active' : '');
        const time = new Date(s.updated_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
        div.innerHTML = `
            <span class="title">${s.title || '未命名'}</span>
            <button class="delete-btn" data-id="${s.id}">✕</button>
            <div class="meta">${s.message_count} 条消息 · ${time}</div>
        `;
        div.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-btn')) return;
            switchSession(s.id);
        });
        const delBtn = div.querySelector('.delete-btn');
        delBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!confirm('删除此对话？')) return;
            try {
                await deleteSession(s.id);
                await refreshAll();
            } catch (err) {
                alert('删除失败: ' + err.message);
            }
        });
        historyListEl.appendChild(div);
    }
    const active = historyListEl.querySelector('.active');
    if (active) active.scrollIntoView({ block: 'nearest' });
}

// ============================================================
// 核心操作
// ============================================================
async function switchSession(sessionId) {
    if (sessionId === currentSessionId) return;
    currentSessionId = sessionId;

    messagesEl.innerHTML = '';
    messagesEl.appendChild(renderSkeleton());
    messagesEl.appendChild(renderSkeleton());

    // 重新添加滚动按钮
    if (!document.getElementById('scrollBottomBtn')) {
        const btn = document.createElement('button');
        btn.className = 'scroll-bottom-btn';
        btn.id = 'scrollBottomBtn';
        btn.textContent = '↓';
        messagesEl.appendChild(btn);
    }

    try {
        const messages = await loadMessages(sessionId);
        renderMessages(messages);
        const sessions = await loadSessions();
        const found = sessions.find(s => s.id === sessionId);
        currentChatTitle.textContent = found ? found.title : '新对话';
        renderHistoryList(sessions, currentSessionId);
    } catch (err) {
        console.error('加载消息失败:', err);
        messagesEl.innerHTML = '<div class="message ai">❌ 加载消息失败</div>';
    }
    inputEl.focus();
}

async function refreshAll() {
    try {
        const sessions = await loadSessions();
        if (sessions.length === 0) {
            const newSession = await createSession('新对话');
            currentSessionId = newSession.id;
            renderMessages([]);
            currentChatTitle.textContent = '新对话';
            renderHistoryList([newSession], currentSessionId);
            return;
        }
        if (!currentSessionId || !sessions.find(s => s.id === currentSessionId)) {
            currentSessionId = sessions[0].id;
        }
        const messages = await loadMessages(currentSessionId);
        renderMessages(messages);
        const found = sessions.find(s => s.id === currentSessionId);
        currentChatTitle.textContent = found ? found.title : '新对话';
        renderHistoryList(sessions, currentSessionId);
    } catch (err) {
        console.error('刷新失败:', err);
        historyListEl.innerHTML = '<div class="empty-history">❌ 加载失败: ' + err.message + '</div>';
    }
}

async function newChat() {
    try {
        const newSession = await createSession('新对话');
        currentSessionId = newSession.id;
        await refreshAll();
        inputEl.focus();
    } catch (err) {
        alert('创建失败: ' + err.message);
    }
}

// ============================================================
// 发送消息
// ============================================================
async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isWaiting || !currentSessionId) return;

    inputEl.value = '';
    isWaiting = true;
    sendBtn.disabled = true;
    inputEl.disabled = true;

    renderMessage(text, 'user');

    const aiDiv = document.createElement('div');
    aiDiv.className = 'message ai';
    aiDiv.id = 'streamingMessage';
    aiDiv.textContent = '';
    messagesEl.appendChild(aiDiv);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    let fullReply = '';

    try {
        const response = await fetch(API_BASE + '/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                message: text,
                user_id: currentSessionId,
                model: modelSelect.value
            })
        });

        if (response.status === 401) {
            logout();
            return;
        }

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: '请求失败' }));
            throw new Error(err.detail || '请求失败');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;
                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.done) {
                            aiDiv.id = '';
                            break;
                        }
                        if (parsed.content) {
                            fullReply += parsed.content;
                            aiDiv.textContent = fullReply;
                            messagesEl.scrollTop = messagesEl.scrollHeight;
                        }
                    } catch (e) {}
                }
            }
        }

        if (!fullReply) {
            aiDiv.textContent = '（AI没有返回内容）';
        }

        const sessions = await loadSessions();
        renderHistoryList(sessions, currentSessionId);
        const found = sessions.find(s => s.id === currentSessionId);
        if (found) currentChatTitle.textContent = found.title;

    } catch (err) {
        const placeholder = document.getElementById('streamingMessage');
        if (placeholder) placeholder.remove();
        renderMessage('❌ ' + err.message, 'ai');
    } finally {
        isWaiting = false;
        sendBtn.disabled = false;
        inputEl.disabled = false;
        inputEl.focus();

        if (scrollBtn) {
            setTimeout(() => {
                const isAtBottom = messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 100;
                if (isAtBottom) {
                    scrollBtn.classList.remove('visible');
                } else {
                    scrollBtn.classList.add('visible');
                }
            }, 100);
        }
    }
}

// ============================================================
// 事件绑定（核心功能）
// ============================================================
sendBtn.addEventListener('click', sendMessage);
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); sendMessage(); }
});
newChatBtn.addEventListener('click', newChat);

// ============================================================
// 启动
// ============================================================
async function init() {
    await refreshAll();
    inputEl.focus();
}

init();

// ============================================================
// 懒加载功能
// ============================================================

// 1. 搜索功能（在 searchInput 获取焦点时加载）
searchInput.addEventListener('focus', async function() {
    if (!window.searchModuleLoaded) {
        try {
            const module = await import('./search.js');
            window.searchModuleLoaded = true;
            console.log('✅ 搜索模块已加载');
        } catch (err) {
            console.error('搜索模块加载失败:', err);
        }
    }
});

// 2. 语音功能（点击麦克风时加载）
voiceInputBtn.addEventListener('click', async function() {
    if (!window.voiceModuleLoaded) {
        try {
            const module = await import('./voice.js');
            window.voiceModuleLoaded = true;
            console.log('✅ 语音模块已加载');
            // 如果模块有初始化函数，调用它
            if (module.initVoice) {
                module.initVoice();
            }
        } catch (err) {
            console.error('语音模块加载失败:', err);
        }
    }
});

// 3. 暗黑模式（点击月亮时加载）
themeBtn.addEventListener('click', async function() {
    if (!window.themeModuleLoaded) {
        try {
            const module = await import('./theme.js');
            window.themeModuleLoaded = true;
            console.log('✅ 暗黑模式模块已加载');
            if (module.toggleTheme) {
                module.toggleTheme();
            }
        } catch (err) {
            console.error('暗黑模式模块加载失败:', err);
        }
    } else {
        // 如果已加载，直接调用
        if (window.toggleTheme) {
            window.toggleTheme();
        }
    }
});

// 4. 导出功能（点击导出时加载）
exportBtn.addEventListener('click', async function() {
    if (!window.exportModuleLoaded) {
        try {
            const module = await import('./export.js');
            window.exportModuleLoaded = true;
            console.log('✅ 导出模块已加载');
            if (module.exportChat) {
                module.exportChat();
            }
        } catch (err) {
            console.error('导出模块加载失败:', err);
        }
    } else {
        if (window.exportChat) {
            window.exportChat();
        }
    }
});

// 5. 重命名功能（点击重命名时加载）
renameBtn.addEventListener('click', async function() {
    if (!window.renameModuleLoaded) {
        try {
            const module = await import('./rename.js');
            window.renameModuleLoaded = true;
            console.log('✅ 重命名模块已加载');
            if (module.openRenameModal) {
                module.openRenameModal();
            }
        } catch (err) {
            console.error('重命名模块加载失败:', err);
        }
    } else {
        if (window.openRenameModal) {
            window.openRenameModal();
        }
    }
});