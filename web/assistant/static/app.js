/**
 * SCHOOL AI ASSISTANT - FRONTEND JAVASCRIPT
 * Chat AI, RBAC, conversation history, and document references.
 */

let rolesData = {};
let sampleQueries = [];
let currentChatHistory = [];
let currentSessionId = "session_" + Date.now();

// ============================================================
// 1. STORAGE AND API CONFIGURATION
// ============================================================

function getChatStorageKey() {
  const emailEl = document.getElementById("currentUserEmail");
  const userEmail = emailEl ? emailEl.value : "default";

  return "ai_chat_sessions_" + userEmail;
}

function getApiUrl(endpoint, params = {}) {
  if (window.API_BASE === "api.php") {
    const query = new URLSearchParams({
      action: endpoint,
      ...params,
    }).toString();

    return `api.php?${query}`;
  }

  const query = new URLSearchParams(params).toString();

  return query ? `/api/${endpoint}?${query}` : `/api/${endpoint}`;
}

// ============================================================
// 2. INITIALIZATION
// ============================================================

document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([loadRoles(), loadConfig(), loadSampleQueries()]);

  renderSavedChatSessions();

  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      document.getElementById("searchTestInput")?.focus();
    }
  });
});

// ============================================================
// 3. LOAD ROLES AND CONFIGURATION
// ============================================================

async function loadRoles() {
  try {
    const res = await fetch(getApiUrl("roles"), {
      credentials: "same-origin",
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    rolesData = await res.json();
  } catch (err) {
    console.error("Failed to load roles:", err);
  }
}

async function loadConfig() {
  try {
    const res = await fetch(getApiUrl("config"), {
      credentials: "same-origin",
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const cfg = await res.json();
    const badge = document.getElementById("currentModeBadge");

    if (!badge) return;

    const rbac = cfg.ENABLE_RBAC_PRERETRIEVAL === true;
    const filter = cfg.ENABLE_OUTPUT_FILTER === true;

    const mode =
      rbac && filter ? "Controlled" : !rbac && !filter ? "Baseline" : "Custom";

    badge.textContent =
      mode === "Controlled"
        ? "Protected (Controlled)"
        : mode === "Baseline"
          ? "Baseline (Unprotected)"
          : "Custom Configuration";

    badge.dataset.mode = mode;
  } catch (err) {
    console.error("Unable to load configuration:", err);
  }
}

// ============================================================
// 4. SAMPLE TEST QUERIES
// ============================================================

async function loadSampleQueries() {
  const listEl = document.getElementById("sampleQueryList");

  try {
    const res = await fetch(getApiUrl("sample-queries"), {
      credentials: "same-origin",
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();

    sampleQueries = Array.isArray(data) ? data : [];

    const count = document.getElementById("sampleQueryCount");

    if (count) {
      count.textContent = `${sampleQueries.length} Cases`;
    }

    renderSampleQueryList(sampleQueries);
  } catch (err) {
    console.error("Failed to load sample queries:", err);

    if (listEl) {
      listEl.textContent = "Failed to load sample queries.";
    }
  }
}

function renderSampleQueryList(queries) {
  const listEl = document.getElementById("sampleQueryList");

  if (!listEl) return;

  listEl.innerHTML = "";

  if (!Array.isArray(queries) || queries.length === 0) {
    listEl.textContent = "No matching test cases found.";
    return;
  }

  queries.forEach((item) => {
    const div = document.createElement("div");

    div.className = "query-item";

    const icon = item.category === "attack" ? "🛡️" : "💬";

    const label = `[${item.role || "?"}] ${item.query || ""}`;

    div.innerHTML = `
      <span class="query-item-icon">${icon}</span>
      <span
        class="query-item-title"
        title="${escapeHtml(label)}"
      >
        ${escapeHtml(label)}
      </span>
    `;

    div.addEventListener("click", () => selectSampleQuery(item));

    listEl.appendChild(div);
  });
}

function filterSampleQueries(keyword) {
  const kw = removeVietnameseTones(
    String(keyword || "")
      .trim()
      .toLowerCase(),
  );

  if (!kw) {
    renderSampleQueryList(sampleQueries);
    renderSavedChatSessions();
    return;
  }

  const filtered = sampleQueries.filter((item) => {
    const fields = [item.query, item.role, item.category, item.target_doc_id];

    return fields.some((field) => {
      const value = removeVietnameseTones(String(field || "").toLowerCase());

      return value.includes(kw);
    });
  });

  renderSampleQueryList(filtered);
  renderSavedChatSessions();
}

function selectSampleQuery(item) {
  const input = document.getElementById("queryInput");

  if (!input) return;

  input.value = item.query || "";
  input.focus();
}

// ============================================================
// 5. SEND QUERY AND RECEIVE RESPONSE
// ============================================================

async function handleSendMessage(e) {
  e.preventDefault();

  const input = document.getElementById("queryInput");
  const sendBtn = document.getElementById("sendBtn");

  if (!input || !sendBtn) return;

  const query = input.value.trim();

  if (!query || sendBtn.disabled) return;

  const role = document.getElementById("roleSelect")?.value || "SinhVien";

  document.querySelector(".zynovate-hero-canvas")?.remove();

  appendUserMessage(query);

  currentChatHistory.push({
    type: "user",
    text: query,
    time: new Date().toLocaleTimeString("en-US"),
  });

  input.value = "";
  sendBtn.disabled = true;

  const loadingId = appendLoadingMessage();

  try {
    const res = await fetch(getApiUrl("chat"), {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query, role }),
    });

    const responseText = await res.text();

    let data;

    try {
      data = JSON.parse(responseText);
    } catch (parseError) {
      console.error("Invalid JSON response:", {
        httpStatus: res.status,
        responsePreview: responseText.slice(0, 500),
      });

      throw new Error(
        `Chat API returned invalid JSON (HTTP ${res.status}). ` +
          "Check the browser Console and PHP error log.",
      );
    }

    if (!data || typeof data !== "object" || Array.isArray(data)) {
      throw new Error("Chat API returned an unexpected response format.");
    }

    if (
      !res.ok ||
      String(data.status || "").toUpperCase() === "ERROR" ||
      data.error
    ) {
      console.error("Chat API request failed:", {
        httpStatus: res.status,
        status: data.status,
        action: data.action_taken,
        error: data.error,
      });

      const serverMessage =
        typeof data.error === "string" && data.error.trim()
          ? data.error.trim()
          : typeof data.answer === "string" && data.answer.trim()
            ? data.answer.trim()
            : `Chat API failed (HTTP ${res.status}).`;

      throw new Error(serverMessage);
    }

    removeMessage(loadingId);

    appendAiResponse(data);

    currentChatHistory.push({
      type: "ai",
      data,
    });

    saveCurrentSessionToStorage();
  } catch (err) {
    removeMessage(loadingId);

    console.error("Chat request error:", err);

    const message =
      err instanceof TypeError
        ? "Cannot connect to Chat API. Check Apache and the Network tab."
        : err?.message || "An unexpected error occurred.";

    appendErrorMessage(message);

    saveCurrentSessionToStorage();
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

// ============================================================
// 6. CHAT MESSAGE COMPONENTS
// ============================================================

function appendUserMessage(text) {
  const chatContainer = document.getElementById("chatMessages");

  if (!chatContainer) return;

  const container = document.createElement("div");

  container.className = "user-message-container";

  container.innerHTML = `
    <div class="user-bubble">
      ${escapeHtml(text)}
    </div>
  `;

  chatContainer.appendChild(container);

  scrollToBottom();
}

function appendLoadingMessage() {
  const id = "loading-" + Date.now();

  const chatContainer = document.getElementById("chatMessages");

  if (!chatContainer) return id;

  const container = document.createElement("div");

  container.id = id;
  container.className = "ai-message-container";

  container.innerHTML = `
    <div class="ai-avatar">AI</div>

    <div
      class="ai-bubble"
      style="
        display:flex;
        align-items:center;
        gap:8px;
        color:var(--text-muted);
        font-size:0.85rem;
      "
    >
      <span>
        Checking access permissions and retrieving relevant documents...
      </span>
    </div>
  `;

  chatContainer.appendChild(container);

  scrollToBottom();

  return id;
}

function removeMessage(id) {
  document.getElementById(id)?.remove();
}

// ============================================================
// 7. NORMALIZE SECURITY EVENT STATUS
// ============================================================

function normalizeSecurityStatus(status, action) {
  const statusMap = {
    PASSED: "PASSED",
    PASS: "PASSED",
    ALLOWED: "PASSED",
    ALLOW: "PASSED",

    REDACTED: "REDACTED",
    REDACT: "REDACTED",

    BLOCKED: "BLOCKED",
    BLOCK: "BLOCKED",
    BLOCKED_INPUT: "BLOCKED",
    REJECTED_INPUT: "BLOCKED",

    DENIED: "DENIED",
    DENY: "DENIED",
  };

  const normalizedStatus = String(status || "UNKNOWN")
    .trim()
    .toUpperCase();

  const normalizedAction = String(action || "UNKNOWN")
    .trim()
    .toUpperCase();

  return statusMap[normalizedStatus] || statusMap[normalizedAction] || "OTHER";
}

// ============================================================
// 8. RENDER AI RESPONSE AND SECURITY STATUS
// ============================================================

function appendAiResponse(data) {
  const chatContainer = document.getElementById("chatMessages");

  if (!chatContainer) return;

  const container = document.createElement("div");

  container.className = "ai-message-container";

  const status = String(data.status || "UNKNOWN")
    .trim()
    .toUpperCase();

  const action = String(data.action_taken || "UNKNOWN")
    .trim()
    .toUpperCase();

  // Keep BLOCKED and DENIED as separate security outcomes.
  // Backend status takes priority over action_taken.
  const displayStatus = normalizeSecurityStatus(status, action);

  const denial =
    data.denial_reason === "UNAUTHORIZED_DOCUMENT" ||
    ["DENIED", "BLOCKED"].includes(displayStatus);

  const rawSources = Array.isArray(data.sources) ? data.sources : [];

  // Backend authorization remains the security authority.
  // The frontend only controls which references are displayed.
  const sources = denial
    ? []
    : rawSources.filter((source) => source && source.doc_id && source.title);

  const latency = Number.isFinite(Number(data.latency_ms))
    ? Math.round(Number(data.latency_ms))
    : 0;

  const answer =
    data.denial_reason === "UNAUTHORIZED_DOCUMENT"
      ? "You are not authorized to access this document. Please contact the administrator if you need assistance."
      : String(data.answer || "No response content is available.");

  let sourcesHtml = "";

  if (sources.length > 0) {
    const cardsHtml = sources
      .map((source) => {
        const classification = ["Public", "Internal", "Restricted"].includes(
          source.classification,
        )
          ? source.classification
          : "";

        return `
          <div class="source-card">

            <div class="source-card-header">

              <span class="source-title">
                📄 [${escapeHtml(source.doc_id)}]
                ${escapeHtml(source.title)}
              </span>

              <span class="source-tag ${classification}">
                ${escapeHtml(source.classification || "")}
              </span>

            </div>

            <div class="source-snippet">
              ${escapeHtml(source.snippet || "")}
            </div>

            <div class="source-actions">
              <span class="source-preview-note">
                References authorized by the system
              </span>
            </div>

          </div>
        `;
      })
      .join("");

    sourcesHtml = `
      <div class="sources-container">

        <button
          type="button"
          class="sources-header"
          aria-expanded="false"
        >
          <span>
            📚 References (${sources.length})
          </span>

          <span class="toggle-icon">▶</span>
        </button>

        <div class="sources-list" hidden>
          ${cardsHtml}
        </div>

      </div>
    `;
  }

  container.innerHTML = `
    <div class="ai-avatar">AI</div>

    <div class="ai-bubble">

      <div class="ai-meta-header">

        <div>
          <strong>AI Assistant</strong>
          &bull;
          <span>${latency}ms</span>
          &bull;
          <span>${escapeHtml(data.mode || "Controlled")}</span>
        </div>

        <span class="status-pill ${displayStatus}">
          ${displayStatus}
        </span>

      </div>

      <div
        class="ai-answer-text"
        style="white-space:pre-wrap"
      >
        ${escapeHtml(answer)}
      </div>

      ${sourcesHtml}

    </div>
  `;

  const toggle = container.querySelector(".sources-header");

  const sourceList = container.querySelector(".sources-list");

  if (sourceList) {
    sourceList.style.display = "none";
  }

  if (toggle) {
    toggle.addEventListener("click", () => {
      toggleSources(toggle);
    });
  }

  chatContainer.appendChild(container);

  scrollToBottom();
}

// ============================================================
// 9. ERROR MESSAGE
// ============================================================

function appendErrorMessage(message) {
  const chatContainer = document.getElementById("chatMessages");

  if (!chatContainer) return;

  const container = document.createElement("div");

  container.className = "ai-message-container";

  container.innerHTML = `
    <div
      class="ai-avatar"
      style="background:#ef4444;"
    >!</div>

    <div
      class="ai-bubble"
      style="border-color:#ef4444;color:#b91c1c;"
    >
      ${escapeHtml(message)}
    </div>
  `;

  chatContainer.appendChild(container);

  scrollToBottom();
}

// ============================================================
// 10. SAVE AND RESTORE CHAT HISTORY
// ============================================================

function readSavedSessions() {
  try {
    const data = JSON.parse(localStorage.getItem(getChatStorageKey()) || "[]");

    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn("Invalid chat history:", err);

    return [];
  }
}

function createNewChat() {
  if (currentChatHistory.length > 0) {
    saveCurrentSessionToStorage();
  }

  currentChatHistory = [];

  currentSessionId = "session_" + Date.now();

  const chatContainer = document.getElementById("chatMessages");

  if (chatContainer) {
    chatContainer.innerHTML = `
      <div class="zynovate-hero-canvas">

        <h2 class="zyn-hero-title">
          New Conversation
        </h2>

        <p class="zyn-hero-subtitle">
          Ask any question about academic services and policies
          or test RBAC access control.
        </p>

      </div>
    `;
  }

  const input = document.getElementById("queryInput");

  if (input) {
    input.value = "";
    input.focus();
  }

  renderSavedChatSessions();
}

function saveCurrentSessionToStorage() {
  if (currentChatHistory.length === 0) return;

  const sessions = readSavedSessions();

  const firstUserMsg = currentChatHistory.find(
    (message) => message.type === "user",
  );

  const title = firstUserMsg ? firstUserMsg.text : "New Chat";

  const existingIdx = sessions.findIndex(
    (session) => session.id === currentSessionId,
  );

  const sessionData = {
    id: currentSessionId,
    title,
    timestamp: new Date().toLocaleString("en-US"),
    messages: currentChatHistory,
  };

  if (existingIdx >= 0) {
    sessions[existingIdx] = sessionData;
  } else {
    sessions.unshift(sessionData);
  }

  // Keep a maximum of 15 recent chat sessions.
  if (sessions.length > 15) {
    sessions.length = 15;
  }

  try {
    localStorage.setItem(getChatStorageKey(), JSON.stringify(sessions));
  } catch (err) {
    console.warn("Unable to save chat history:", err);
  }

  renderSavedChatSessions();
}

function renderSavedChatSessions() {
  const container = document.getElementById("chatHistorySection");

  const list = document.getElementById("savedChatList");

  if (!container || !list) return;

  const sessions = readSavedSessions();

  const search = removeVietnameseTones(
    (document.getElementById("searchTestInput")?.value || "").toLowerCase(),
  );

  const filtered = sessions.filter((session) => {
    const title = removeVietnameseTones(
      String(session.title || "").toLowerCase(),
    );

    return title.includes(search);
  });

  container.style.display = sessions.length ? "block" : "none";

  list.innerHTML = "";

  filtered.forEach((session) => {
    const item = document.createElement("div");

    item.className = "query-item";

    item.style.padding = "6px 10px";
    item.style.fontSize = "0.76rem";

    if (session.id === currentSessionId) {
      item.style.background = "#f0edff";
      item.style.color = "#6252ec";
      item.style.fontWeight = "700";
    }

    item.innerHTML = `
      <span>🗨️</span>

      <span
        class="query-item-title"
        title="${escapeHtml(session.title || "")}"
      >
        ${escapeHtml(session.title || "Chat")}
      </span>
    `;

    item.addEventListener("click", () => {
      loadSavedSession(session.id);
    });

    list.appendChild(item);
  });
}

function loadSavedSession(sessionId) {
  const sessions = readSavedSessions();

  const session = sessions.find((item) => item.id === sessionId);

  if (!session) return;

  currentSessionId = session.id;

  currentChatHistory = Array.isArray(session.messages) ? session.messages : [];

  const chatContainer = document.getElementById("chatMessages");

  if (!chatContainer) return;

  chatContainer.innerHTML = "";

  currentChatHistory.forEach((message) => {
    if (message.type === "user") {
      appendUserMessage(message.text);
    } else if (message.type === "ai") {
      appendAiResponse(message.data);
    }
  });

  renderSavedChatSessions();
}

function clearAllChats() {
  const confirmed = confirm(
    "Are you sure you want to clear all saved chat history?",
  );

  if (!confirmed) return;

  localStorage.removeItem(getChatStorageKey());

  currentChatHistory = [];

  createNewChat();
}

// ============================================================
// 11. DOCUMENT SOURCE CONTROLS
// ============================================================

function toggleSources(headerEl) {
  const list = headerEl.nextElementSibling;

  if (!list) return;

  const expanded = headerEl.getAttribute("aria-expanded") === "true";

  headerEl.setAttribute("aria-expanded", String(!expanded));

  list.hidden = expanded;

  list.style.display = expanded ? "none" : "flex";

  const icon = headerEl.querySelector(".toggle-icon");

  if (icon) {
    icon.textContent = expanded ? "▶" : "▼";
  }
}

async function openDocModal(docId) {
  // Full-document viewing remains disabled until server-side
  // document-level authorization is implemented.
  appendErrorMessage(
    "Full-document viewing is temporarily disabled until the API enforces document-level authorization.",
  );
}

function closeDocModal() {
  const modal = document.getElementById("docModal");

  if (modal) {
    modal.style.display = "none";
  }
}

// ============================================================
// 12. GENERAL UTILITIES
// ============================================================

function scrollToBottom() {
  const container = document.getElementById("chatMessages");

  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

function escapeHtml(text) {
  if (text === null || text === undefined) {
    return "";
  }

  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function removeVietnameseTones(str) {
  return String(str || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D");
}
