// ============================================================
// search.js - 搜索功能（懒加载）
// ============================================================

console.log('🔍 搜索模块已加载');

let searchKeyword = '';

function highlightText(text, keyword) {
    if (!keyword || !text) return text;
    const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<span class="highlight">$1</span>');
}

function filterMessages(keyword) {
    searchKeyword = keyword.trim();
    const allMessages = document.querySelectorAll('#messageContainer .message');
    allMessages.forEach(msg => {
        const text = msg.textContent || msg.innerText;
        if (!searchKeyword || text.toLowerCase().includes(searchKeyword.toLowerCase())) {
            msg.style.display = '';
            if (searchKeyword) {
                const html = msg.innerHTML;
                if (!html.includes('highlight')) {
                    const originalText = msg.textContent || msg.innerText;
                    msg.innerHTML = highlightText(originalText, searchKeyword);
                }
            } else {
                const originalText = msg.textContent || msg.innerText;
                msg.innerHTML = originalText;
            }
        } else {
            msg.style.display = 'none';
        }
    });
}

const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', function() {
        filterMessages(this.value);
    });
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            filterMessages(searchInput.value);
        }
    });
}

// 导出供其他模块使用
export { filterMessages, highlightText };