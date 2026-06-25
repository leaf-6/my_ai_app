// ============================================================
// voice.js - 语音功能（懒加载）
// ============================================================

console.log('🎤 语音模块已加载');

const voiceInputBtn = document.getElementById('voiceInputBtn');
const voiceOutputBtn = document.getElementById('voiceOutputBtn');
const inputEl = document.getElementById('messageInput');

let isListening = false;
let recognition = null;

// ============================================================
// 语音输入（麦克风）
// ============================================================
function initVoiceInput() {
    if (voiceInputBtn) {
        voiceInputBtn.addEventListener('click', toggleVoiceInput);
    }
}

function toggleVoiceInput() {
    if (isListening) {
        if (recognition) recognition.stop();
        return;
    }
    startVoiceInput();
}

function startVoiceInput() {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        alert('浏览器不支持语音识别，请使用 Chrome 或 Edge');
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        inputEl.value = transcript;
        isListening = false;
        voiceInputBtn.textContent = '🎤';
        voiceInputBtn.classList.remove('listening');
        // 自动发送
        if (window.sendMessage) {
            window.sendMessage();
        } else {
            // 触发发送按钮点击
            document.getElementById('sendBtn')?.click();
        }
    };

    recognition.onerror = function(event) {
        console.error('语音识别错误:', event.error);
        isListening = false;
        voiceInputBtn.textContent = '🎤';
        voiceInputBtn.classList.remove('listening');
        if (event.error === 'not-allowed') {
            alert('请允许浏览器使用麦克风权限');
        }
    };

    recognition.onend = function() {
        isListening = false;
        voiceInputBtn.textContent = '🎤';
        voiceInputBtn.classList.remove('listening');
    };

    try {
        recognition.start();
        isListening = true;
        voiceInputBtn.textContent = '⏹️';
        voiceInputBtn.classList.add('listening');
    } catch (e) {
        console.error('启动语音识别失败:', e);
    }
}

// ============================================================
// 语音输出（朗读）
// ============================================================
function initVoiceOutput() {
    if (voiceOutputBtn) {
        voiceOutputBtn.addEventListener('click', speakLastAIResponse);
    }
}

function speakLastAIResponse() {
    const aiMessages = document.querySelectorAll('.message.ai');
    if (aiMessages.length === 0) {
        alert('没有可朗读的AI回复');
        return;
    }
    const lastAiMessage = aiMessages[aiMessages.length - 1];
    const text = lastAiMessage.textContent || lastAiMessage.innerText;
    if (text && !text.startsWith('❌') && !text.startsWith('👋')) {
        speakText(text);
    } else {
        alert('没有可朗读的有效回复');
    }
}

function speakText(text) {
    if (!window.speechSynthesis) {
        alert('浏览器不支持语音合成');
        return;
    }
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const zhVoice = voices.find(v => v.lang.startsWith('zh'));
    if (zhVoice) {
        utterance.voice = zhVoice;
    }

    window.speechSynthesis.speak(utterance);
}

// 预加载语音列表
if (window.speechSynthesis) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = function() {
        window.speechSynthesis.getVoices();
    };
}

// ============================================================
// 初始化
// ============================================================
export function initVoice() {
    initVoiceInput();
    initVoiceOutput();
    console.log('🎤 语音功能已初始化');
}

// 自动初始化（如果 core.js 调用）
initVoice();