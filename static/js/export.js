// ============================================================
// export.js - 导出聊天记录（懒加载）
// ============================================================

console.log('📥 导出模块已加载');

const currentChatTitle = document.getElementById('currentChatTitle');

export function exportChat() {
    const messages = document.querySelectorAll('#messageContainer .message:not([style*="display: none"])');
    if (messages.length === 0) {
        alert('没有可导出的消息');
        return;
    }

    let text = `📋 聊天记录\n`;
    text += `导出时间: ${new Date().toLocaleString()}\n`;
    text += `对话: ${currentChatTitle.textContent}\n`;
    text += `═`.repeat(50) + '\n\n';

    for (const msg of messages) {
        const sender = msg.classList.contains('user') ? '👤 我' : '🤖 AI';
        const content = msg.textContent || msg.innerText;
        if (content && !content.startsWith('👋') && !content.startsWith('❌')) {
            text += `${sender}: ${content}\n\n`;
        }
    }

    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `聊天记录_${new Date().toISOString().slice(0,10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 挂载到 window
window.exportChat = exportChat;