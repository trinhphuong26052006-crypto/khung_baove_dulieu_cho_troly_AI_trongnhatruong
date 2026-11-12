/**
 * ============================================================================
 * TRỢ LÝ AI NHÀ TRƯỜNG - FRONTEND JAVASCRIPT
 * Hỗ trợ: Lưu phiên chat cũ (New Chat), Tìm kiếm từ khóa thông minh
 * ============================================================================
 */

let rolesData = {};
let sampleQueries = [];
let currentChatHistory = []; // Lưu các lượt hỏi đáp của phiên chat hiện tại

function getApiUrl(endpoint, params = {}) {
    if (window.API_BASE === 'api.php') {
        const query = new URLSearchParams({ action: endpoint, ...params }).toString();
        return `api.php?${query}`;
    }
    const query = new URLSearchParams(params).toString();
    return query ? `/api/${endpoint}?${query}` : `/api/${endpoint}`;
}

document.addEventListener("DOMContentLoaded", async () => {
    await loadRoles();
    await loadConfig();
    await loadSampleQueries();
    renderSavedChatSessions();

    // Hỗ trợ phím tắt ⌘K / Ctrl+K để focus vào ô tìm kiếm
    document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
            e.preventDefault();
            const searchInput = document.getElementById("searchTestInput");
            if (searchInput) searchInput.focus();
        }
    });
});

async function loadRoles() {
    try {
        const res = await fetch(getApiUrl("roles"));
        rolesData = await res.json();
    } catch (err) {
        console.error("Lỗi khi tải vai trò:", err);
    }
}

async function loadConfig() {
    try {
        const res = await fetch(getApiUrl("config"));
        const cfg = await res.json();
        const badge = document.getElementById("currentModeBadge");
        if (badge) {
            const isControlled = cfg.ENABLE_RBAC_PRERETRIEVAL !== false;
            badge.className = `badge-mode ${isControlled ? 'controlled' : 'baseline'}`;
            badge.innerText = isControlled ? '🛡️ Controlled Mode' : '⚠️ Baseline Mode';
        }
    } catch (err) {
        console.error("Lỗi tải cấu hình:", err);
    }
}

async function loadSampleQueries() {
    const listEl = document.getElementById("sampleQueryList");
    try {
        const res = await fetch(getApiUrl("sample-queries"));
        sampleQueries = await res.json();
        renderSampleQueryList(sampleQueries);
    } catch (err) {
        listEl.innerHTML = '<div style="font-size: 0.75rem; color: #f87171; padding: 8px;">Lỗi tải câu hỏi mẫu</div>';
    }
}

function renderSampleQueryList(queries) {
    const listEl = document.getElementById("sampleQueryList");
    if (!queries || queries.length === 0) {
        listEl.innerHTML = '<div style="font-size: 0.78rem; color: #94a3b8; padding: 12px; text-align: center;">Không tìm thấy câu hỏi phù hợp</div>';
        return;
    }

    listEl.innerHTML = "";
    queries.forEach((item) => {
        const div = document.createElement("div");
        div.className = "query-item";
        const icon = item.category === "attack" ? "🛡️" : "💬";
        div.innerHTML = `
            <span class="query-item-icon">${icon}</span>
            <span class="query-item-title" title="[${item.role}] ${escapeHtml(item.query)}">[${item.role}] ${escapeHtml(item.query)}</span>
        `;
        div.onclick = () => selectSampleQuery(item);
        listEl.appendChild(div);
    });
}

/**
 * TÌM KIẾM THEO TỪ KHÓA THÔNG MINH (Không dấu, không phân biệt hoa thường)
 */
function filterSampleQueries(keyword) {
    const kw = removeVietnameseTones(keyword.trim().toLowerCase());
    if (!kw) {
        renderSampleQueryList(sampleQueries);
        return;
    }

    const filtered = sampleQueries.filter(item => {
        const qText = removeVietnameseTones((item.query || "").toLowerCase());
        const rText = removeVietnameseTones((item.role || "").toLowerCase());
        const cText = removeVietnameseTones((item.category || "").toLowerCase());
        const docId = removeVietnameseTones((item.target_doc_id || "").toLowerCase());
        return qText.includes(kw) || rText.includes(kw) || cText.includes(kw) || docId.includes(kw);
    });

    renderSampleQueryList(filtered);
}

function selectSampleQuery(item) {
    document.getElementById("queryInput").value = item.query;
    document.getElementById("queryInput").focus();
}

/**
 * GỬI CÂU HỎI & HỘI THOẠI
 */
async function handleSendMessage(e) {
    e.preventDefault();
    const input = document.getElementById("queryInput");
    const query = input.value.trim();
    if (!query) return;

    const role = document.getElementById("roleSelect") ? document.getElementById("roleSelect").value : "SinhVien";
    const sendBtn = document.getElementById("sendBtn");

    // Ẩn hero canvas khi bắt đầu cuộc trò chuyện
    const heroCanvas = document.querySelector(".zynovate-hero-canvas");
    if (heroCanvas) {
        heroCanvas.style.display = "none";
    }

    appendUserMessage(query);
    currentChatHistory.push({ type: 'user', text: query, time: new Date().toLocaleTimeString('vi-VN', {hour: '2-digit', minute:'2-digit'}) });
    input.value = "";
    sendBtn.disabled = true;

    const loadingId = appendLoadingMessage();

    try {
        const res = await fetch(getApiUrl("chat"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query, role: role })
        });
        const data = await res.json();

        removeMessage(loadingId);
        appendAiResponse(data);
        currentChatHistory.push({ type: 'ai', data: data });

        // Tự động lưu/cập nhật phiên chat hiện tại vào LocalStorage
        saveCurrentSessionToStorage();
    } catch (err) {
        removeMessage(loadingId);
        appendErrorMessage("Đã xảy ra lỗi khi kết nối tới máy chủ.");
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

function appendUserMessage(text) {
    const chatContainer = document.getElementById("chatMessages");
    const container = document.createElement("div");
    container.className = "user-message-container";
    container.innerHTML = `<div class="user-bubble">${escapeHtml(text)}</div>`;
    chatContainer.appendChild(container);
    scrollToBottom();
}

function appendLoadingMessage() {
    const id = "loading-" + Date.now();
    const chatContainer = document.getElementById("chatMessages");
    const container = document.createElement("div");
    container.id = id;
    container.className = "ai-message-container";
    container.innerHTML = `
        <div class="ai-avatar">AI</div>
        <div class="ai-bubble" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.85rem;">
            <span>Đang tra cứu quyền hạn và tổng hợp tài liệu...</span>
        </div>
    `;
    chatContainer.appendChild(container);
    scrollToBottom();
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendAiResponse(data) {
    const chatContainer = document.getElementById("chatMessages");
    const container = document.createElement("div");
    container.className = "ai-message-container";

    const actionPill = data.action_taken || "PASSED";
    const sources = data.sources || [];

    let sourcesHtml = "";
    if (sources.length > 0) {
        let cardsHtml = sources.map((s) => `
            <div class="source-card">
                <div class="source-card-header">
                    <span class="source-title">
                        📄 [${escapeHtml(s.doc_id)}] ${escapeHtml(s.title)}
                    </span>
                    <span class="source-tag ${s.classification}">${s.classification}</span>
                </div>
                <div class="source-snippet">
                    "${escapeHtml(s.snippet)}"
                </div>
                <div class="source-actions">
                    <button class="view-doc-btn" onclick="openDocModal('${s.doc_id}')">
                        🔍 Xem tài liệu gốc
                    </button>
                </div>
            </div>
        `).join("");

        sourcesHtml = `
            <div class="sources-container">
                <div class="sources-header" onclick="toggleSources(this)">
                    <span>📚 Nguồn trích dẫn (${sources.length} tài liệu)</span>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="sources-list">
                    ${cardsHtml}
                </div>
            </div>
        `;
    } else {
        sourcesHtml = `
            <div class="sources-container" style="border-top: none; margin-top: 8px;">
                <div style="font-size: 0.75rem; color: var(--text-muted); font-style: italic;">
                    ℹ️ Không có tài liệu nào trong phạm vi được phép trích xuất.
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="ai-avatar">AI</div>
        <div class="ai-bubble">
            <div class="ai-meta-header">
                <div>
                    <strong>AI Assistant</strong> &bull; <span>${data.latency_ms || 0}ms</span> &bull; <span>${escapeHtml(data.mode || 'Controlled')}</span>
                </div>
                <span class="status-pill ${actionPill}">${actionPill}</span>
            </div>
            <div style="white-space: pre-wrap;">${escapeHtml(data.answer)}</div>
            ${sourcesHtml}
        </div>
    `;

    chatContainer.appendChild(container);
    scrollToBottom();
}

function appendErrorMessage(msg) {
    const chatContainer = document.getElementById("chatMessages");
    const container = document.createElement("div");
    container.className = "ai-message-container";
    container.innerHTML = `
        <div class="ai-avatar" style="background: #ef4444;">!</div>
        <div class="ai-bubble" style="border-color: #ef4444; color: #b91c1c;">
            ${escapeHtml(msg)}
        </div>
    `;
    chatContainer.appendChild(container);
    scrollToBottom();
}

/**
 * ============================================================================
 * TÍNH NĂNG NEW CHAT & LƯU TRỮ CÁC ĐOẠN CHAT CŨ (LOCALSTORAGE)
 * ============================================================================
 */
let currentSessionId = "session_" + Date.now();

function createNewChat() {
    // Nếu phiên hiện tại đã có tin nhắn thì lưu hoàn tất
    if (currentChatHistory.length > 0) {
        saveCurrentSessionToStorage();
    }

    // Reset lại màn hình chat mới
    currentChatHistory = [];
    currentSessionId = "session_" + Date.now();

    const chatContainer = document.getElementById("chatMessages");
    chatContainer.innerHTML = `
        <div class="zynovate-hero-canvas">
            <div class="glowing-orb"></div>
            <h2 class="zyn-hero-title">
                Cuộc trò chuyện mới
            </h2>
            <p class="zyn-hero-subtitle">
                Hãy nhập câu hỏi bất kỳ về học vụ, quy chế hoặc thử nghiệm kiểm soát phân quyền RBAC.
            </p>
        </div>
    `;

    document.getElementById("queryInput").value = "";
    document.getElementById("queryInput").focus();
    renderSavedChatSessions();
}

function saveCurrentSessionToStorage() {
    if (currentChatHistory.length === 0) return;

    let sessions = JSON.parse(localStorage.getItem("ai_chat_sessions") || "[]");
    const firstUserMsg = currentChatHistory.find(m => m.type === 'user');
    const title = firstUserMsg ? firstUserMsg.text : "Đoạn chat mới";

    const existingIdx = sessions.findIndex(s => s.id === currentSessionId);
    const sessionData = {
        id: currentSessionId,
        title: title,
        timestamp: new Date().toLocaleString('vi-VN'),
        messages: currentChatHistory
    };

    if (existingIdx >= 0) {
        sessions[existingIdx] = sessionData;
    } else {
        sessions.unshift(sessionData); // Đưa lên đầu
    }

    // Giữ tối đa 15 phiên chat gần nhất
    if (sessions.length > 15) sessions = sessions.slice(0, 15);
    localStorage.setItem("ai_chat_sessions", JSON.stringify(sessions));
    renderSavedChatSessions();
}

function renderSavedChatSessions() {
    const container = document.getElementById("chatHistorySection");
    const list = document.getElementById("savedChatList");
    if (!container || !list) return;

    const sessions = JSON.parse(localStorage.getItem("ai_chat_sessions") || "[]");
    if (sessions.length === 0) {
        container.style.display = "none";
        return;
    }

    container.style.display = "block";
    list.innerHTML = "";

    sessions.forEach(sess => {
        const item = document.createElement("div");
        item.className = "query-item";
        item.style.padding = "6px 10px";
        item.style.fontSize = "0.76rem";
        if (sess.id === currentSessionId) {
            item.style.background = "#eff6ff";
            item.style.color = "#1951fc";
            item.style.fontWeight = "700";
        }
        item.innerHTML = `
            <span style="font-size: 0.85rem;">🗨️</span>
            <span class="query-item-title" title="${escapeHtml(sess.title)}">${escapeHtml(sess.title)}</span>
        `;
        item.onclick = () => loadSavedSession(sess.id);
        list.appendChild(item);
    });
}

function loadSavedSession(sessionId) {
    const sessions = JSON.parse(localStorage.getItem("ai_chat_sessions") || "[]");
    const sess = sessions.find(s => s.id === sessionId);
    if (!sess) return;

    currentSessionId = sess.id;
    currentChatHistory = sess.messages || [];

    const chatContainer = document.getElementById("chatMessages");
    chatContainer.innerHTML = "";

    currentChatHistory.forEach(msg => {
        if (msg.type === 'user') {
            appendUserMessage(msg.text);
        } else if (msg.type === 'ai') {
            appendAiResponse(msg.data);
        }
    });

    renderSavedChatSessions();
}

function clearAllChats() {
    if (confirm("Bạn có chắc muốn xóa tất cả lịch sử các đoạn chat cũ đã lưu không?")) {
        localStorage.removeItem("ai_chat_sessions");
        currentChatHistory = [];
        createNewChat();
    }
}

function toggleSources(headerEl) {
    const list = headerEl.nextElementSibling;
    const icon = headerEl.querySelector(".toggle-icon");
    if (list.style.display === "none") {
        list.style.display = "flex";
        icon.innerText = "▼";
    } else {
        list.style.display = "none";
        icon.innerText = "▶";
    }
}

async function openDocModal(docId) {
    const modal = document.getElementById("docModal");
    const titleEl = document.getElementById("modalDocTitle");
    const idEl = document.getElementById("modalDocId");
    const classEl = document.getElementById("modalDocClassification");
    const bodyEl = document.getElementById("modalDocBody");

    bodyEl.innerText = "Đang tải nội dung văn bản...";
    modal.style.display = "flex";

    try {
        const res = await fetch(getApiUrl("document", { doc_id: docId }));
        const doc = await res.json();
        titleEl.innerText = doc.title || docId;
        idEl.innerText = `Mã: ${docId} | Đơn vị: ${doc.department || 'Nhà trường'}`;
        classEl.className = `source-tag ${doc.classification}`;
        classEl.innerText = doc.classification;
        bodyEl.innerText = doc.content || "Không tìm thấy nội dung văn bản.";
    } catch (err) {
        bodyEl.innerText = "Lỗi nạp văn bản: " + err.message;
    }
}

function closeDocModal() {
    document.getElementById("docModal").style.display = "none";
}

function scrollToBottom() {
    const c = document.getElementById("chatMessages");
    c.scrollTop = c.scrollHeight;
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function removeVietnameseTones(str) {
    return str
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/đ/g, 'd').replace(/Đ/g, 'D');
}
