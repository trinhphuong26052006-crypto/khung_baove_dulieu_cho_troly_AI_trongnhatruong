/**
 * ============================================================================
 * TRỢ LÝ AI NHÀ TRƯỜNG - FRONTEND JAVASCRIPT
 * ============================================================================
 */

let rolesData = {};
let sampleQueries = [];

document.addEventListener("DOMContentLoaded", async () => {
    await loadRoles();
    await loadConfig();
    await loadSampleQueries();

    // Lắng nghe thay đổi Role
    document.getElementById("roleSelect").addEventListener("change", (e) => {
        updateRoleUI(e.target.value);
    });

    // Lắng nghe toggle Chế độ
    document.getElementById("toggleRbac").addEventListener("change", updateSystemConfig);
    document.getElementById("toggleFilter").addEventListener("change", updateSystemConfig);
});

async function loadRoles() {
    try {
        const res = await fetch("/api/roles");
        rolesData = await res.json();
        updateRoleUI("SinhVien");
    } catch (err) {
        console.error("Lỗi khi tải vai trò:", err);
    }
}

function updateRoleUI(role) {
    const roleInfo = rolesData[role] || {
        name: role,
        accessible: ["Public"],
        description: "Vai trò cơ bản"
    };

    const roleBadge = document.getElementById("roleBadge");
    const roleLevels = document.getElementById("roleLevels");
    const roleDescription = document.getElementById("roleDescription");
    const activeRoleBadge = document.getElementById("activeRoleBadge");

    roleBadge.className = `role-tag ${role}`;
    roleBadge.innerText = role;

    activeRoleBadge.className = `role-tag ${role}`;
    activeRoleBadge.innerText = role;

    roleDescription.innerText = roleInfo.description;
    roleLevels.innerText = roleInfo.accessible.join(", ");
    roleLevels.style.color = role === "SinhVien" ? "#34d399" : (role === "GiangVien" ? "#fbbf24" : "#f87171");
}

async function loadConfig() {
    try {
        const res = await fetch("/api/config");
        const cfg = await res.json();
        document.getElementById("toggleRbac").checked = cfg.ENABLE_RBAC_PRERETRIEVAL;
        document.getElementById("toggleFilter").checked = cfg.ENABLE_OUTPUT_FILTER;
        updateModeBadge(cfg.ENABLE_RBAC_PRERETRIEVAL);
    } catch (err) {
        console.error("Lỗi tải cấu hình:", err);
    }
}

async function updateSystemConfig() {
    const enableRbac = document.getElementById("toggleRbac").checked;
    const enableFilter = document.getElementById("toggleFilter").checked;

    try {
        const res = await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                ENABLE_RBAC_PRERETRIEVAL: enableRbac,
                ENABLE_OUTPUT_FILTER: enableFilter
            })
        });
        const data = await res.json();
        updateModeBadge(enableRbac);
    } catch (err) {
        console.error("Lỗi cập nhật cấu hình:", err);
    }
}

function updateModeBadge(isControlled) {
    const badge = document.getElementById("currentModeBadge");
    const explainText = document.getElementById("modeExplainText");
    if (isControlled) {
        badge.className = "badge-mode controlled";
        badge.innerText = "🛡️ Controlled Mode";
        explainText.innerHTML = 'Chế độ: <strong style="color: #60a5fa;">Controlled (Có phòng thủ RBAC)</strong>';
    } else {
        badge.className = "badge-mode baseline";
        badge.innerText = "⚠️ Baseline Mode";
        explainText.innerHTML = 'Chế độ: <strong style="color: #fbbf24;">Baseline (Không phòng thủ)</strong>';
    }
}

async function loadSampleQueries() {
    const listEl = document.getElementById("sampleQueryList");
    try {
        const res = await fetch("/api/sample-queries");
        sampleQueries = await res.json();

        if (!sampleQueries || sampleQueries.length === 0) {
            listEl.innerHTML = '<div style="font-size: 0.75rem; color: var(--text-muted); padding: 8px;">Không có ca test</div>';
            return;
        }

        listEl.innerHTML = "";
        sampleQueries.forEach((item) => {
            const div = document.createElement("div");
            div.className = "query-item";
            const icon = item.category === "attack" ? "⚠️" : "💬";
            div.innerHTML = `<span style="margin-right: 4px;">${icon}</span> [${item.role}] ${escapeHtml(item.query)}`;
            div.title = `[${item.role}] ${item.query} (${item.category})`;
            div.onclick = () => selectSampleQuery(item);
            listEl.appendChild(div);
        });
    } catch (err) {
        listEl.innerHTML = '<div style="font-size: 0.75rem; color: #f87171; padding: 8px;">Lỗi tải câu hỏi mẫu</div>';
    }
}

function selectSampleQuery(item) {
    document.getElementById("roleSelect").value = item.role;
    updateRoleUI(item.role);
    document.getElementById("queryInput").value = item.query;
    document.getElementById("queryInput").focus();
}

async function handleSendMessage(e) {
    e.preventDefault();
    const input = document.getElementById("queryInput");
    const query = input.value.trim();
    if (!query) return;

    const role = document.getElementById("roleSelect").value;
    const sendBtn = document.getElementById("sendBtn");

    // Hiển thị tin nhắn người dùng
    appendUserMessage(query);
    input.value = "";
    sendBtn.disabled = true;

    // Hiển thị tin nhắn tạm Loading
    const loadingId = appendLoadingMessage();

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query, role: role })
        });
        const data = await res.json();

        // Xóa bubble loading và hiển thị kết quả AI
        removeMessage(loadingId);
        appendAiResponse(data);
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

    // Xử lý tạo HTML danh sách tài liệu nguồn (Courdx Style)
    let sourcesHtml = "";
    if (sources.length > 0) {
        let cardsHtml = sources.map((s, idx) => `
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
                    <strong>AI Assistant</strong> • <span>${data.latency_ms}ms</span> • <span>${escapeHtml(data.mode)}</span>
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
        <div class="ai-bubble" style="border-color: #ef4444; color: #fca5a5;">
            ${escapeHtml(msg)}
        </div>
    `;
    chatContainer.appendChild(container);
    scrollToBottom();
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
        const res = await fetch(`/api/document?doc_id=${encodeURIComponent(docId)}`);
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

