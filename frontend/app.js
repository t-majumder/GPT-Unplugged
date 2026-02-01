let chatHistory = [];
let forceRetrieve = false;
let showDebug = false;

function el(id) { return document.getElementById(id); }

// CHANGE THIS TO YOUR TAILSCALE IP
const BACKEND_BASE = "http://localhost:8000"; // <-- YOUR Tailscale IP here

// Example : "http://101.85.111.87:8000"; 
// 101.85.111.87 --> only replace this portion with your IP address from tailscale

function apiBase() {
  return BACKEND_BASE;
}


function initThemeToggle() {
  const themeToggle = document.getElementById("theme-toggle");
  const htmlEl = document.documentElement;

  if (!themeToggle) return;

  const icon = themeToggle.querySelector("i");
  const label = themeToggle.querySelector("span");

  const saved = localStorage.getItem("theme");
  if (saved) {
    htmlEl.setAttribute("data-theme", saved);
    if (icon) icon.className = saved === "dark" ? "fas fa-sun" : "fas fa-moon";
    if (label) label.textContent = saved === "dark" ? "Light Mode" : "Dark Mode";
  }

  themeToggle.addEventListener("click", () => {
    const cur = htmlEl.getAttribute("data-theme") || "light";
    const next = cur === "dark" ? "light" : "dark";

    htmlEl.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);

    if (icon) icon.className = next === "dark" ? "fas fa-sun" : "fas fa-moon";
    if (label) label.textContent = next === "dark" ? "Light Mode" : "Dark Mode";
  });
}

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return await res.json();
}

function setStatus(text) {
  el("statusText").textContent = text;
}

//  -------------------  Helpers  ------------------- 
function splitByCodeFences(text) {
  const parts = [];
  const re = /```[\s\S]*?```/g;
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push({ type: "text", value: text.slice(last, m.index) });
    parts.push({ type: "code", value: m[0] });
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push({ type: "text", value: text.slice(last) });
  return parts;
}

function isProbablyMathBlock(s) {
  const t = s.trim();
  if (!t) return false;
  return /\\(frac|sum|int|sqrt|mathbf|boxed|omega|lambda|cdot|pm|leq|geq|rightarrow|left|right)/.test(t)
      || /[_^=<>]/.test(t)
      || /[0-9]\s*[+\-*/]/.test(t);
}

function fixCommonLatexTypos(s) {
  let out = s;
  out = out.replace(/\\sum\s*\{([^}]+)\}\s*\^/g, (m, inner) => `\\sum_{${inner}}^`);
  out = out.replace(/\\sum\s*\{([^}]+)\}/g, (m, inner) => `\\sum_{${inner}}`);
  out = out.replace(/\\prod\s*\{([^}]+)\}/g, (m, inner) => `\\prod_{${inner}}`);
  out = out.replace(/\\int\s*([0-9])/g, "\\int_$1");
  out = out.replace(/\\mathbf\{([a-zA-Z]+)\}\s*([a-zA-Z0-9]+)/g, (m, v, idx) => `\\mathbf{${v}}_${idx}`);
  out = out.replace(/\\mathbf\{x\}\s*j/g, "\\mathbf{x}_j");
  out = out.replace(/\(\s*\\omega\s*=\s*/g, "\\(\\omega = ");
  out = out.replace(/\\boxed\{\s*,/g, "\\boxed{");
  out = out.replace(/;;+/g, ";");
  return out;
}

function convertBracketMathToDisplay(s) {
  return s.replace(/\n\[\s*\n([\s\S]*?)\n\]\s*\n/g, (m, inner) => {
    const body = inner.trim();
    if (!isProbablyMathBlock(body)) return m;
    return `\n$$\n${body}\n$$\n`;
  });
}

function autocloseDisplayMath(s) {
  const count = (s.match(/\$\$/g) || []).length;
  if (count % 2 === 1) return s + "\n$$\n";
  return s;
}

function convertParenInlineMath(s) {
  return s.replace(/(?<![a-zA-Z\\])\(([^()]{1,300})\)/g, (match, inner) => {
    if (!isProbablyMathBlock(inner)) return match;
    return `\\(${inner.trim()}\\)`;
  });
}

function convertBracketDisplayMath(s) {
  s = s.replace(/(?:^|\n)\s*\[\s*\n([\s\S]*?)\n\s*\]\s*(?:\n|$)/g, (match, inner) => {
    if (!isProbablyMathBlock(inner)) return match;
    return `\n$$\n${inner.trim()}\n$$\n`;
  });

  s = s.replace(/(?<![(\w\]])\[([^\[\]\n]{2,300})\](?!\()/g, (match, inner) => {
    if (!isProbablyMathBlock(inner)) return match;
    return `$$${inner.trim()}$$`;
  });

  return s;
}

function fixTrailingCommasInMath(s) {
  s = s.replace(/,(\s*\$\$)/g,       '$1'); 
  s = s.replace(/,(\s*\\\])/g,       '$1'); 
  s = s.replace(/,(\s*\\\))/g,       '$1'); 
  s = s.replace(/,(\s*\]\s*(?:\n|$))/g, '$1'); 
  return s;
}

function normalizeDelimitersToStandard(s) {
  s = s.replace(/\\\[([\s\S]*?)\\\]/g, (m, inner) => `$$\n${inner.trim()}\n$$`);
  s = s.replace(/\\\(([\s\S]*?)\\\)/g, (m, inner) => `$${inner.trim()}$`);
  return s;
}


function normalizeMathDelimiters(text) {
  const parts = splitByCodeFences(text);

  const fixed = parts.map(p => {
    if (p.type === "code") return p.value;
    let t = p.value;
    t = fixCommonLatexTypos(t);
    t = convertBracketMathToDisplay(t);
    t = convertParenInlineMath(t);                     
    t = convertBracketDisplayMath(t);                  
    t = fixTrailingCommasInMath(t);                    
    t = normalizeDelimitersToStandard(t);              
    t = autocloseDisplayMath(t);                       

    return t;
  }).join("");

  return fixed;
}

function updateEmptyState() {
  const empty = el("emptyState");
  const messages = el("messages");
  if (!empty || !messages) return;

  const hasMessages = messages.querySelectorAll(".msg").length > 0;
  empty.style.display = hasMessages ? "none" : "flex";
}

/* ----------------- Markdown + LaTeX rendering ----------------- */

function renderAssistantMarkdown(rawText) {
  const normalized = normalizeMathDelimiters(rawText);

  marked.setOptions({ breaks: true, gfm: true });
  const html = marked.parse(normalized);

  const clean = DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    ADD_ATTR: ['target', 'rel']
  });

  return `<div class="md">${clean}</div>`;
}

let mathJaxTimer = null;
function scheduleMathJaxTypeset(container) {
  if (!window.MathJax || !window.MathJax.typesetPromise) return;
  if (mathJaxTimer) clearTimeout(mathJaxTimer);
  mathJaxTimer = setTimeout(() => {
    window.MathJax.typesetPromise([container]).catch(() => {});
  }, 180);
}

/* ----------------- Message DOM helpers ----------------- */

function addUserMessage(content) {
  const messages = el("messages");
  const div = document.createElement("div");
  div.className = "msg user";
  div.textContent = content;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  updateEmptyState();
  return div;
}

function addAssistantMessage(initialRawText = "") {
  const messages = el("messages");
  const div = document.createElement("div");
  div.className = "msg assistant";
  div.innerHTML = renderAssistantMarkdown(initialRawText);
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  scheduleMathJaxTypeset(div);
  updateEmptyState();
  return div;
}

function updateAssistantMessage(div, rawText) {
  div.innerHTML = renderAssistantMarkdown(rawText);
  el("messages").scrollTop = el("messages").scrollHeight;
  scheduleMathJaxTypeset(div);
}

function addLoadingBubble() {
  const messages = el("messages");
  const div = document.createElement("div");
  div.className = "msg assistant";
  div.innerHTML = `
    <div class="loading-row">
      <div class="spinner"></div>
      <div class="dots"><span></span><span></span><span></span></div>
      <div style="opacity:.8">Thinking...</div>
    </div>
  `;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

function clearChat() {
  chatHistory = [];
  el("messages").innerHTML = '<div id="emptyState" class="empty-state"></div>';
  el("routeHint").textContent = "";
  el("ragMetaLine").textContent = "";
  updateEmptyState();
}

function toggleSidebar() {
  const sidebar = el("sidebar");
  const appRoot = el("appRoot");
  const overlay = el("sidebarOverlay");
  
  if (window.innerWidth <= 820) {
    const isOpen = sidebar.classList.contains("show-mobile");
    
    if (isOpen) {
      sidebar.classList.remove("show-mobile");
      overlay.classList.remove("active");
    } else {
      sidebar.classList.add("show-mobile");
      overlay.classList.add("active");
    }
  } 
  else {
    sidebar.classList.toggle("minimized");
    appRoot.classList.toggle("sidebar-min");
  }
}

/* ----------------- Backend resolution ----------------- */

async function resolveBackendBase() {
  try {
    const data = await fetchJSON(`/api/models`);
    ACTIVE_BACKEND = "";
    return data;
  } catch (_) {
    const data = await fetchJSON(`${DEFAULT_BACKEND}/api/models`);
    ACTIVE_BACKEND = DEFAULT_BACKEND;
    return data;
  }
}

async function loadModels() {
  const data = await fetchJSON(`${apiBase()}/api/models`);
  const models = data.models || [];
  const sel = el("modelSelect");
  sel.innerHTML = "";

  if (models.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No models found";
    sel.appendChild(opt);
    return;
  }

  for (const m of models) {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    sel.appendChild(opt);
  }
}

async function refreshStatus() {
  try {
    const s = await fetchJSON(`${apiBase()}/api/status`);
    setStatus(s.db_ready ? `DB ready ✅ (${s.pdf_count} PDFs)` : `DB not ready ⚠️ (${s.pdf_count} PDFs)`);
  } catch (e) {
    setStatus("Backend not reachable ❌");
  }
}

async function uploadPDFs() {
  const input = el("pdfInput");
  if (!input.files || input.files.length === 0) {
    alert("Select at least one PDF.");
    return;
  }
  setStatus("Uploading PDFs...");

  for (const file of input.files) {
    const fd = new FormData();
    fd.append("file", file);
    await fetchJSON(`${apiBase()}/api/upload`, { method: "POST", body: fd });
  }
  setStatus("Upload complete ✅");
  await refreshStatus();
}

async function vectorize() {
  setStatus("Vectorizing... (can take time for many PDFs)");
  const out = await fetchJSON(`${apiBase()}/api/vectorize`, { method: "POST" });
  setStatus(`Vectorized ✅ PDFs: ${out.pdfs}, chunks: ${out.chunks}`);
  await refreshStatus();
}

/* ----------------- Streaming chat ----------------- */

async function sendChatStream() {
  const msg = el("chatInput").value.trim();
  if (!msg) return;

  const modelName = el("modelSelect").value;
  if (!modelName) {
    addAssistantMessage("No model selected / no models loaded. Check backend connectivity.");
    return;
  }

  addUserMessage(msg);
  el("chatInput").value = "";

  const reqHistory = chatHistory.slice();
  const payload = {
    message: msg,
    model_name: modelName,
    history: reqHistory,
    force_retrieval: forceRetrieve ? true : null
  };

  el("routeHint").textContent = "Thinking...";
  el("ragMetaLine").textContent = "";

  const loadingEl = addLoadingBubble();
  const assistantEl = addAssistantMessage("");
  let removedLoading = false;

  let assistantRaw = "";

  const appendText = (t) => {
    if (!removedLoading) {
      removedLoading = true;
      loadingEl.remove();
    }
    assistantRaw += t;
    updateAssistantMessage(assistantEl, assistantRaw);
  };

  let res;
  try {
    res = await fetch(`${apiBase()}/api/chat_stream`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
  } catch (e) {
    loadingEl.remove();
    updateAssistantMessage(assistantEl, `Error: Failed to reach backend. ${e.message}`);
    return;
  }

  if (!res.ok || !res.body) {
    const t = await res.text();
    loadingEl.remove();
    updateAssistantMessage(assistantEl, `Error: ${t || res.status}`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  let ragMeta = null;
  let debugObj = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);

      let eventName = "message";
      let dataLine = "";

      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) eventName = line.replace("event:", "").trim();
        if (line.startsWith("data:")) dataLine += line.replace("data:", "").trim();
      }
      if (!dataLine) continue;

      let data;
      try { data = JSON.parse(dataLine); } catch { data = { text: dataLine }; }

      if (eventName === "meta") {
        const decision = data.decision || "DIRECT";
        const retrieved = data.retrieved ?? 0;
        el("routeHint").textContent = `Route: ${decision} • Retrieved: ${retrieved}`;
      } else if (eventName === "rag_meta") {
        ragMeta = data;
        el("ragMetaLine").textContent =
          `RAG Meta: context_chars=${ragMeta.context_chars} • chunks_used=${(ragMeta.chunks_used || []).length}`;
      } else if (eventName === "debug") {
        debugObj = data;
      } else if (eventName === "token") {
        appendText(data.text || "");
      } else if (eventName === "error") {
        appendText(`\n\n**[ERROR]** ${data.message || "Unknown error"}`);
      } else if (eventName === "done") {
        if (!removedLoading) {
          removedLoading = true;
          loadingEl.remove();
        }
        if (showDebug) {
          if (ragMeta && (ragMeta.chunks_used || []).length) {
            appendText(
              `\n\n---\n**DEBUG (chunks used):**\n` +
              ragMeta.chunks_used.slice(0, 4)
                .map((c, i) => `\n\n**#${i+1}** ${c.source}${c.page!=null ? ` p${c.page}` : ""}\n\n${c.preview}`)
                .join("")
            );
          } else if (debugObj) {
            appendText(`\n\n---\n**DEBUG (retrieval):**\n\n\`\`\`json\n${JSON.stringify(debugObj, null, 2)}\n\`\`\``);
          }
        }
      }
    }
  }

  if (!removedLoading) loadingEl.remove();

  chatHistory.push({role: "user", content: msg});
  chatHistory.push({role: "assistant", content: assistantRaw});
}

/* ----------------- Init ----------------- */

async function bootstrap() {
  el("uploadBtn").addEventListener("click", uploadPDFs);
  el("vectorizeBtn").addEventListener("click", vectorize);
  el("sendBtn").addEventListener("click", sendChatStream);
  el("clearBtn").addEventListener("click", clearChat);
  el("hamburgerBtn").addEventListener("click", toggleSidebar);

  const overlay = el("sidebarOverlay");
  if (overlay) {
    overlay.addEventListener("click", toggleSidebar);
  }

  const forceToggle = el("forceRetrieveToggle");
  const debugToggle = el("showDebugToggle");

  forceToggle.addEventListener("change", () => {
    forceRetrieve = forceToggle.checked;
  });

  debugToggle.addEventListener("change", () => {
    showDebug = debugToggle.checked;
  });

  el("chatInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChatStream();
    }
  });

  await loadModels();
  await refreshStatus();
  updateEmptyState();
}


bootstrap();
