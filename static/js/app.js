/**
 * DisasterShield — Application Controller
 * Handles tabs, chat state machine, interactive checklist, and official references.
 */

const AppState = {
  currentTab: 'home',
  activeDisasterId: null,
  activeDisasterName: '',
  currentNodeId: null,
  stepNumber: 1,
  isComplete: false,
  history: [],
  checklistData: null,
  checkedItems: new Set(),
  ragFilterCategory: '',
  isRagLoading: false
};

// ==========================================================================
// TOAST NOTIFICATIONS
// ==========================================================================
function showToast(message) {
  const toast = document.getElementById('toastNotification');
  const msgElem = document.getElementById('toastMessage');
  if (!toast || !msgElem) return;

  msgElem.textContent = message;
  toast.classList.add('show');
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.classList.remove('show');
  }, 2600);
}
window.showToast = showToast;

// ==========================================================================
// TAB SWITCHING
// ==========================================================================
function switchTab(targetTabId) {
  AppState.currentTab = targetTabId;

  // Update navbar button states
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === targetTabId);
  });

  // Update tab pane visibility
  const panes = {
    home: document.getElementById('paneHome'),
    chat: document.getElementById('paneChat'),
    rag: document.getElementById('paneRag'),
    docAdmin: document.getElementById('paneDocAdmin'),
    checklist: document.getElementById('paneChecklist'),
    flowchart: document.getElementById('paneFlowchart'),
    sources: document.getElementById('paneSources')
  };

  Object.entries(panes).forEach(([tab, pane]) => {
    if (pane) pane.classList.toggle('active', tab === targetTabId);
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // If switching to flowchart tab, refresh flowchart
  if (targetTabId === 'flowchart' && window.FlowchartViewer) {
    const disasterToLoad = AppState.activeDisasterId || 'earthquake';
    window.FlowchartViewer.loadFlowchart(disasterToLoad);
  }

  // If switching to RAG tab, initialize welcome stream if empty
  if (targetTabId === 'rag') {
    initRagAssistant();
  }

  // If switching to Document Repository tab, load indexed catalog
  if (targetTabId === 'docAdmin') {
    loadDocumentCatalog();
  }
}

// ==========================================================================
// CHATBOT INTERACTION LOGIC
// ==========================================================================
async function startDisasterChat(disasterId) {
  try {
    const response = await fetch('/api/chat/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ disaster_id: disasterId })
    });

    const data = await response.json();
    if (data.status !== 'success') {
      showToast('Error starting assessment: ' + data.message);
      return;
    }

    const session = data.session;
    AppState.activeDisasterId = session.disaster_id;
    AppState.activeDisasterName = session.disaster_name;
    AppState.currentNodeId = session.current_node_id;
    AppState.stepNumber = session.step;
    AppState.isComplete = false;
    AppState.history = session.history;

    // Update Chat UI Header
    document.getElementById('chatDisasterBadge').textContent = session.disaster_name;
    document.getElementById('chatDisasterTitle').textContent = `${session.disaster_name} Safety Assessment`;
    document.getElementById('chatStepTracker').textContent = `Step ${session.step} of 4`;
    document.getElementById('chatActiveIndicator').style.display = 'inline-block';

    // Reset Chat Messages Container
    const messagesList = document.getElementById('chatMessagesList');
    messagesList.innerHTML = '';

    // Render Initial Bot Question
    renderBotQuestion(session.node);

    // Switch to Chat Tab
    switchTab('chat');
  } catch (err) {
    console.error('Chat start failed:', err);
    showToast('Failed to connect to assessment engine.');
  }
}

function renderBotQuestion(node) {
  const messagesList = document.getElementById('chatMessagesList');
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-msg bot';

  const urgencyClass = (node.urgency || 'normal').toLowerCase();

  msgDiv.innerHTML = `
    <div class="chat-avatar" aria-hidden="true">DS</div>
    <div class="chat-bubble">
      <div class="bubble-meta">
        <span class="bubble-author">DisasterShield Bot</span>
        <span class="bubble-timestamp">${now}</span>
        <span class="bubble-urgency ${urgencyClass}">${node.urgency || 'ASSESSMENT'}</span>
      </div>
      <div class="bubble-prompt">${escapeHtml(node.prompt)}</div>
      ${node.context ? `<div class="bubble-context">${escapeHtml(node.context)}</div>` : ''}
    </div>
  `;

  messagesList.appendChild(msgDiv);
  scrollChatToBottom();

  // Render selectable buttons in bottom tray
  renderOptionButtons(node.options || []);
}

function renderOptionButtons(options) {
  const trayGrid = document.getElementById('optionsButtonsGrid');
  trayGrid.innerHTML = '';

  if (!options || options.length === 0) return;

  options.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = 'option-chip-btn';
    btn.dataset.optionId = opt.id;
    btn.innerHTML = `
      <span class="option-chip-text">${escapeHtml(opt.text)}</span>
      ${opt.description ? `<span class="option-chip-desc">${escapeHtml(opt.description)}</span>` : ''}
    `;

    btn.addEventListener('click', () => handleOptionClick(opt.id, opt.text));
    trayGrid.appendChild(btn);
  });
}

async function handleOptionClick(optionId, optionText) {
  // Render user's answer message
  renderUserAnswer(optionText);

  // Disable options tray while processing
  const trayGrid = document.getElementById('optionsButtonsGrid');
  trayGrid.innerHTML = '<div style="padding: 0.75rem; color: #64748b; font-size: 0.875rem;">Evaluating official safety protocol...</div>';

  try {
    const response = await fetch('/api/chat/step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        disaster_id: AppState.activeDisasterId,
        current_node_id: AppState.currentNodeId,
        option_id: optionId,
        history: AppState.history
      })
    });

    const data = await response.json();
    if (data.status !== 'success') {
      showToast('Error: ' + data.message);
      return;
    }

    const stepResult = data.step_result;
    AppState.currentNodeId = stepResult.current_node_id;
    AppState.stepNumber = stepResult.step;
    AppState.isComplete = stepResult.is_complete;
    AppState.history = stepResult.history;

    document.getElementById('chatStepTracker').textContent = `Step ${stepResult.step} of 4`;

    if (stepResult.is_complete) {
      // Terminal Guidance reached!
      renderTerminalGuidance(stepResult.guidance);
      renderTerminalTray();
    } else {
      // Continue next question
      renderBotQuestion(stepResult.node);
    }
  } catch (err) {
    console.error('Chat step error:', err);
    showToast('Failed to evaluate step.');
  }
}

function renderUserAnswer(text) {
  const messagesList = document.getElementById('chatMessagesList');
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-msg user';
  msgDiv.innerHTML = `
    <div class="chat-avatar" aria-hidden="true">YOU</div>
    <div class="chat-bubble">
      <div class="bubble-meta">
        <span class="bubble-author">Your Selection</span>
        <span class="bubble-timestamp">${now}</span>
      </div>
      <div class="bubble-answer">${escapeHtml(text)}</div>
    </div>
  `;

  messagesList.appendChild(msgDiv);
  scrollChatToBottom();
}

function renderTerminalGuidance(guidance) {
  const messagesList = document.getElementById('chatMessagesList');
  const sevClass = (guidance.severity || 'urgent').toLowerCase();

  const container = document.createElement('div');
  container.className = 'guidance-card-container';

  // Build Immediate actions list
  let immediateListHtml = '';
  (guidance.immediate_actions || []).forEach(action => {
    immediateListHtml += `
      <li class="guidance-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="guidance-item-icon check">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span>${escapeHtml(action)}</span>
      </li>
    `;
  });

  // Build Actions to avoid list
  let avoidListHtml = '';
  (guidance.actions_to_avoid || []).forEach(item => {
    avoidListHtml += `
      <li class="guidance-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="guidance-item-icon cross">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        <span>${escapeHtml(item)}</span>
      </li>
    `;
  });

  // Build Preventive list
  let preventListHtml = '';
  (guidance.preventive_measures || []).forEach(item => {
    preventListHtml += `
      <li class="guidance-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="guidance-item-icon bullet">
          <circle cx="12" cy="12" r="4"/>
        </svg>
        <span>${escapeHtml(item)}</span>
      </li>
    `;
  });

  // Build Emergency Contacts
  let contactsHtml = '';
  (guidance.emergency_contacts || []).forEach(contact => {
    contactsHtml += `
      <a href="tel:${contact.number}" class="contact-pill" title="Dial ${contact.name}">
        <strong>${contact.number}</strong>
        <span>${contact.name}</span>
      </a>
    `;
  });

  container.innerHTML = `
    <div class="guidance-banner ${sevClass}">
      <div class="guidance-status-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:1.25rem;height:1.25rem;">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <span>${escapeHtml(guidance.status)}</span>
      </div>
      <span class="guidance-severity-tag">${guidance.severity}</span>
    </div>

    <div class="guidance-body">
      <div class="guidance-summary-box">
        ${escapeHtml(guidance.summary)}
      </div>

      <div class="guidance-section-block">
        <h4 class="guidance-section-title alert">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:1rem;height:1rem;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Immediate Life-Safety Actions (Do Right Now):
        </h4>
        <ul class="guidance-list">
          ${immediateListHtml}
        </ul>
      </div>

      ${avoidListHtml ? `
        <div class="guidance-section-block">
          <h4 class="guidance-section-title avoid">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:1rem;height:1rem;"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            Actions to Strictly AVOID:
          </h4>
          <ul class="guidance-list">
            ${avoidListHtml}
          </ul>
        </div>
      ` : ''}

      ${preventListHtml ? `
        <div class="guidance-section-block">
          <h4 class="guidance-section-title prevent">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:1rem;height:1rem;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            Preventive & Recovery Measures:
          </h4>
          <ul class="guidance-list">
            ${preventListHtml}
          </ul>
        </div>
      ` : ''}

      <div class="guidance-contacts-bar">
        <div class="contacts-bar-title">Immediate Emergency Contacts (Tap to Dial):</div>
        <div class="contacts-pills-row">
          ${contactsHtml}
        </div>
      </div>

      ${guidance.official_reference ? `
        <div class="guidance-official-source">
          Verified Official Source: ${escapeHtml(guidance.official_reference)}
        </div>
      ` : ''}
    </div>
  `;

  messagesList.appendChild(container);
  scrollChatToBottom();
}

function renderTerminalTray() {
  const trayGrid = document.getElementById('optionsButtonsGrid');
  trayGrid.innerHTML = `
    <div class="terminal-actions-bar" style="grid-column: 1 / -1;">
      <span>Assessment Complete. What would you like to do next?</span>
      <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
        <button class="btn btn-primary btn-sm" id="btnRestartFromTray">
          Restart Assessment
        </button>
        <button class="btn btn-outline btn-sm" id="btnReturnHomeFromTray">
          Change Disaster
        </button>
        <button class="btn btn-secondary btn-sm" id="btnCopyTranscriptTray">
          Copy Transcript
        </button>
      </div>
    </div>
  `;

  document.getElementById('btnRestartFromTray').addEventListener('click', () => {
    if (AppState.activeDisasterId) startDisasterChat(AppState.activeDisasterId);
  });

  document.getElementById('btnReturnHomeFromTray').addEventListener('click', () => {
    switchTab('home');
  });

  document.getElementById('btnCopyTranscriptTray').addEventListener('click', copyTranscript);
}

function scrollChatToBottom() {
  const viewport = document.getElementById('chatViewport');
  if (viewport) {
    setTimeout(() => {
      viewport.scrollTo({ top: viewport.scrollHeight, behavior: 'smooth' });
    }, 50);
  }
}

// ==========================================================================
// TRANSCRIPT GENERATION & DOWNLOAD
// ==========================================================================
async function copyTranscript() {
  if (AppState.history.length === 0) {
    showToast('No active conversation history to copy.');
    return;
  }

  try {
    const response = await fetch('/api/chat/transcript', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        history: AppState.history,
        disaster_name: AppState.activeDisasterName
      })
    });

    const data = await response.json();
    if (data.status === 'success') {
      await navigator.clipboard.writeText(data.transcript);
      showToast('Full conversation transcript copied to clipboard!');
    }
  } catch (err) {
    console.error('Copy transcript failed:', err);
    showToast('Failed to generate transcript.');
  }
}

async function downloadTranscript() {
  if (AppState.history.length === 0) {
    showToast('No active conversation to download.');
    return;
  }

  try {
    const response = await fetch('/api/chat/transcript', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        history: AppState.history,
        disaster_name: AppState.activeDisasterName
      })
    });

    const data = await response.json();
    if (data.status === 'success') {
      const blob = new Blob([data.transcript], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const filename = `DisasterShield_Transcript_${AppState.activeDisasterId || 'Report'}_${new Date().toISOString().slice(0, 10)}.txt`;
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast('Transcript downloaded as ' + filename);
    }
  } catch (err) {
    console.error('Download transcript failed:', err);
    showToast('Failed to download transcript.');
  }
}

// ==========================================================================
// CHECKLIST LOGIC
// ==========================================================================
async function loadChecklist() {
  const container = document.getElementById('checklistCategoriesGrid');
  if (!container) return;

  // Load persisted checks from localStorage
  const savedChecks = localStorage.getItem('disastershield_checklist');
  if (savedChecks) {
    try {
      AppState.checkedItems = new Set(JSON.parse(savedChecks));
    } catch (e) {
      AppState.checkedItems = new Set();
    }
  }

  try {
    const response = await fetch('/api/checklist');
    const data = await response.json();
    if (data.status === 'success') {
      AppState.checklistData = data.data;
      renderChecklist(data.data);
      updateChecklistProgress();
    }
  } catch (err) {
    console.error('Failed to load checklist:', err);
  }
}

function renderChecklist(data) {
  const container = document.getElementById('checklistCategoriesGrid');
  container.innerHTML = '';

  (data.categories || []).forEach(cat => {
    const catCard = document.createElement('div');
    catCard.className = 'checklist-category-card';

    catCard.innerHTML = `
      <div class="category-header">
        <h3 class="category-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:1.25rem;height:1.25rem;color:var(--brand-blue);">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          </svg>
          ${escapeHtml(cat.name)}
        </h3>
        <span class="meta-tag">${cat.items.length} items</span>
      </div>
      <div class="category-items-list" id="cat_items_${cat.id}"></div>
    `;

    const itemsList = catCard.querySelector(`#cat_items_${cat.id}`);

    cat.items.forEach(item => {
      const isChecked = AppState.checkedItems.has(item.id);
      const itemRow = document.createElement('div');
      itemRow.className = `checklist-item ${isChecked ? 'checked' : ''}`;
      itemRow.id = `item_row_${item.id}`;

      const prioClass = (item.priority || 'medium').toLowerCase();

      itemRow.innerHTML = `
        <input type="checkbox" class="item-checkbox" id="chk_${item.id}" ${isChecked ? 'checked' : ''} aria-label="${item.label}">
        <div class="item-content">
          <div class="item-label-row">
            <label class="item-label" for="chk_${item.id}">${escapeHtml(item.label)}</label>
            <span class="priority-tag ${prioClass}">${item.priority}</span>
          </div>
          <p class="item-detail">${escapeHtml(item.detail)}</p>
        </div>
      `;

      itemRow.querySelector(`#chk_${item.id}`).addEventListener('change', (e) => {
        if (e.target.checked) {
          AppState.checkedItems.add(item.id);
          itemRow.classList.add('checked');
        } else {
          AppState.checkedItems.delete(item.id);
          itemRow.classList.remove('checked');
        }
        saveChecklistState();
        updateChecklistProgress();
      });

      itemsList.appendChild(itemRow);
    });

    container.appendChild(catCard);
  });
}

function saveChecklistState() {
  localStorage.setItem('disastershield_checklist', JSON.stringify(Array.from(AppState.checkedItems)));
}

function updateChecklistProgress() {
  if (!AppState.checklistData) return;

  let totalItems = 0;
  AppState.checklistData.categories.forEach(cat => totalItems += cat.items.length);
  const packedCount = AppState.checkedItems.size;
  const pct = totalItems > 0 ? Math.round((packedCount / totalItems) * 100) : 0;

  const pctElem = document.getElementById('checklistPercentage');
  const barElem = document.getElementById('checklistProgressBar');
  const countElem = document.getElementById('checklistCounter');

  if (pctElem) pctElem.textContent = `${pct}%`;
  if (barElem) barElem.style.width = `${pct}%`;
  if (countElem) countElem.textContent = `${packedCount} of ${totalItems} items packed`;
}

function resetChecklist() {
  if (confirm('Are you sure you want to reset all checklist items?')) {
    AppState.checkedItems.clear();
    saveChecklistState();
    document.querySelectorAll('.checklist-item').forEach(el => el.classList.remove('checked'));
    document.querySelectorAll('.item-checkbox').forEach(el => el.checked = false);
    updateChecklistProgress();
    showToast('Checklist reset.');
  }
}

// ==========================================================================
// SOURCES & HOTLINES LOADER
// ==========================================================================
async function loadSources() {
  try {
    const response = await fetch('/api/sources');
    const data = await response.json();
    if (data.status === 'success') {
      renderHotlines(data.data.hotlines || []);
      renderStatutorySources(data.data.sources || []);
    }
  } catch (err) {
    console.error('Failed to load sources:', err);
  }
}

function renderHotlines(hotlines) {
  const container = document.getElementById('hotlinesGrid');
  if (!container) return;

  container.innerHTML = '';
  hotlines.forEach(item => {
    const card = document.createElement('div');
    card.className = 'hotline-card';
    card.innerHTML = `
      <div class="hotline-num-badge">${item.number}</div>
      <div class="hotline-name">${escapeHtml(item.service)}</div>
      <div class="hotline-scope">${escapeHtml(item.scope)}</div>
      <div class="hotline-authority">${escapeHtml(item.authority)}</div>
    `;
    container.appendChild(card);
  });
}

function renderStatutorySources(sources) {
  const container = document.getElementById('sourcesList');
  if (!container) return;

  container.innerHTML = '';
  sources.forEach(src => {
    const card = document.createElement('article');
    card.className = 'source-card';

    let rulesHtml = '';
    (src.rules_mapped || []).forEach(rule => {
      rulesHtml += `<li>${escapeHtml(rule)}</li>`;
    });

    card.innerHTML = `
      <div class="source-card-top">
        <h4 class="source-org">${escapeHtml(src.organization)}</h4>
        <span class="source-category">${escapeHtml(src.category)}</span>
      </div>
      <div class="source-title-text">${escapeHtml(src.title)}</div>
      <p class="source-desc">${escapeHtml(src.description)}</p>

      <div class="source-rules-mapped">
        <strong>Directly Mapped Safety Rules in DisasterShield:</strong>
        <ul>${rulesHtml}</ul>
      </div>

      <a href="${src.url}" target="_blank" rel="noopener noreferrer" class="source-link-btn">
        <span>Visit Official Website (${src.url})</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:0.875rem;height:0.875rem;"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
      </a>
    `;
    container.appendChild(card);
  });
}

// Utility: Escape HTML string
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ==========================================================================
// INITIALIZATION ON DOM READY
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  // Setup Tab Navigation
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  const brandLink = document.getElementById('brandHomeLink');
  if (brandLink) brandLink.addEventListener('click', (e) => {
    e.preventDefault();
    switchTab('home');
  });

  const footerSourcesLink = document.getElementById('footerSourcesLink');
  if (footerSourcesLink) footerSourcesLink.addEventListener('click', (e) => {
    e.preventDefault();
    switchTab('sources');
  });

  // Setup Disaster Cards click handlers
  document.querySelectorAll('.start-chat-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const disaster = e.currentTarget.dataset.disaster;
      if (disaster) startDisasterChat(disaster);
    });
  });

  // Setup Chat Header Action Buttons
  const btnRestart = document.getElementById('btnRestartChat');
  if (btnRestart) btnRestart.addEventListener('click', () => {
    if (AppState.activeDisasterId) startDisasterChat(AppState.activeDisasterId);
  });

  const btnChange = document.getElementById('btnChangeDisaster');
  if (btnChange) btnChange.addEventListener('click', () => switchTab('home'));

  const btnViewFlowchart = document.getElementById('btnViewFlowchartPath');
  if (btnViewFlowchart) btnViewFlowchart.addEventListener('click', () => {
    switchTab('flowchart');
    if (window.FlowchartViewer && AppState.activeDisasterId) {
      window.FlowchartViewer.loadFlowchart(AppState.activeDisasterId);
    }
  });

  const btnCopy = document.getElementById('btnCopyTranscript');
  if (btnCopy) btnCopy.addEventListener('click', copyTranscript);

  const btnDownload = document.getElementById('btnDownloadTranscript');
  if (btnDownload) btnDownload.addEventListener('click', downloadTranscript);

  // Setup Checklist reset button
  const btnResetChk = document.getElementById('btnResetChecklist');
  if (btnResetChk) btnResetChk.addEventListener('click', resetChecklist);

  // Setup RAG Knowledge Assistant Form
  const ragForm = document.getElementById('ragQueryForm');
  if (ragForm) {
    ragForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const input = document.getElementById('ragInputText');
      if (input) askRAG(input.value);
    });
  }

  // Setup Suggested Question Chips
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.textContent.trim();
      const input = document.getElementById('ragInputText');
      if (input) input.value = q;
      askRAG(q);
    });
  });

  // Setup RAG Category Filter Chips
  document.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      AppState.ragFilterCategory = chip.dataset.category || '';
      showToast(`RAG category filter: ${AppState.ragFilterCategory ? AppState.ragFilterCategory.toUpperCase() : 'ALL'}`);
    });
  });

  // Setup PDF File Input Drag & Drop Label
  const pdfInput = document.getElementById('pdfFileInput');
  if (pdfInput) {
    pdfInput.addEventListener('change', () => {
      const dropText = document.getElementById('fileDropText');
      if (dropText && pdfInput.files && pdfInput.files.length > 0) {
        dropText.textContent = `Selected: ${pdfInput.files[0].name} (${(pdfInput.files[0].size / 1024).toFixed(1)} KB)`;
      }
    });
  }

  // Setup Document Upload Form
  const uploadForm = document.getElementById('docUploadForm');
  if (uploadForm) {
    uploadForm.addEventListener('submit', handleDocUpload);
  }

  // Setup Rebuild Index Button
  const btnRebuild = document.getElementById('btnRebuildIndex');
  if (btnRebuild) {
    btnRebuild.addEventListener('click', handleRebuildIndex);
  }

  // Initialize Sub-modules
  loadChecklist();
  loadSources();
  if (window.FlowchartViewer) window.FlowchartViewer.init();

  // If user visits page without starting chat, show prompt in chat tab
  const messagesList = document.getElementById('chatMessagesList');
  if (messagesList && messagesList.children.length === 0) {
    messagesList.innerHTML = `
      <div style="text-align: center; padding: 3rem 1rem; color: #64748b;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:3rem;height:3rem;margin-bottom:1rem;color:#94a3b8;">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <h3 style="font-size:1.15rem; color:#0f172a; margin-bottom:0.5rem;">No Assessment Active</h3>
        <p style="font-size:0.875rem; max-width:400px; margin:0 auto 1.5rem;">
          Please select a disaster scenario from the Home screen to begin your situation-specific safety guidance.
        </p>
        <button class="btn btn-primary" onclick="switchTab('home')">Go to Disaster Selection</button>
      </div>
    `;
  }
});

// ==========================================================================
// MODE B: RAG KNOWLEDGE ASSISTANT CONTROLLER
// ==========================================================================

function initRagAssistant() {
  const streamList = document.getElementById('ragStreamList');
  if (!streamList || streamList.children.length > 0) return;

  streamList.innerHTML = `
    <div class="rag-welcome-card">
      <div class="rag-welcome-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
      </div>
      <div class="rag-welcome-content">
        <h3>Welcome to the Disaster Knowledge Assistant</h3>
        <p>
          Ask any disaster preparedness, mitigation, or response question. Answers are retrieved via
          <strong>FAISS dense vector search</strong> and <strong>sparse keyword matching</strong> directly from official PDF guidelines
          published by the <strong>National Disaster Management Authority (NDMA)</strong>, <strong>Geological Survey of India (GSI)</strong>, and <strong>Central Water Commission (CWC)</strong>.
        </p>
        <div class="rag-welcome-tips">
          <span>Tip: Click any suggested question above or type your own question below. Filter by category if you want targeted answers.</span>
        </div>
      </div>
    </div>
  `;
}

function formatRagText(text) {
  if (!text) return '';
  let formatted = escapeHtml(text);

  // Bold **text**
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Parse lines for bullet and numbered lists
  const lines = formatted.split('\n');
  let inList = false;
  let outLines = [];

  for (let line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      if (!inList) {
        outLines.push('<ul class="rag-answer-list">');
        inList = true;
      }
      outLines.push(`<li>${trimmed.substring(2)}</li>`);
    } else if (/^\d+\.\s/.test(trimmed)) {
      if (!inList) {
        outLines.push('<ol class="rag-answer-list">');
        inList = true;
      }
      outLines.push(`<li>${trimmed.replace(/^\d+\.\s/, '')}</li>`);
    } else {
      if (inList) {
        outLines.push('</ul>');
        inList = false;
      }
      if (trimmed.length > 0) {
        outLines.push(`<p class="rag-answer-p">${trimmed}</p>`);
      }
    }
  }
  if (inList) outLines.push('</ul>');

  return outLines.join('');
}

function renderRagUserMessage(query) {
  const streamList = document.getElementById('ragStreamList');
  if (!streamList) return;

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const userDiv = document.createElement('div');
  userDiv.className = 'rag-msg user';
  userDiv.innerHTML = `
    <div class="rag-msg-avatar user" aria-hidden="true">YOU</div>
    <div class="rag-msg-bubble user">
      <div class="rag-msg-meta">
        <span class="rag-msg-author">You</span>
        <span class="rag-msg-time">${now}</span>
        ${AppState.ragFilterCategory ? `<span class="rag-msg-category-tag">${escapeHtml(AppState.ragFilterCategory.toUpperCase())}</span>` : ''}
      </div>
      <div class="rag-msg-text">${escapeHtml(query)}</div>
    </div>
  `;
  streamList.appendChild(userDiv);
  scrollRagToBottom();
}

function renderRagLoadingIndicator() {
  const streamList = document.getElementById('ragStreamList');
  if (!streamList) return null;

  const loaderId = 'ragLoader_' + Date.now();
  const loadDiv = document.createElement('div');
  loadDiv.id = loaderId;
  loadDiv.className = 'rag-msg bot rag-loading';
  loadDiv.innerHTML = `
    <div class="rag-msg-avatar bot" aria-hidden="true">RAG</div>
    <div class="rag-msg-bubble bot">
      <div class="rag-searching-state">
        <div class="rag-spinner" aria-hidden="true"></div>
        <div>
          <div class="rag-searching-title">Searching Official Disaster Guidelines...</div>
          <div class="rag-searching-subtitle">Querying FAISS vector index &amp; verifying statutory citations</div>
        </div>
      </div>
    </div>
  `;
  streamList.appendChild(loadDiv);
  scrollRagToBottom();
  return loaderId;
}

function removeRagLoadingIndicator(loaderId) {
  if (!loaderId) return;
  const el = document.getElementById(loaderId);
  if (el) el.remove();
}

function renderRagAssistantAnswer(data) {
  const streamList = document.getElementById('ragStreamList');
  if (!streamList) return;

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const botDiv = document.createElement('div');
  botDiv.className = 'rag-msg bot';

  let emergencyBannerHtml = '';
  if (data.is_emergency) {
    emergencyBannerHtml = `
      <div class="rag-emergency-alert-banner" role="alert">
        <div class="alert-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </div>
        <div class="alert-content">
          <strong>CRITICAL EMERGENCY ALERT — Immediate Life Safety Risk Detected</strong>
          <p>If you or someone near you is in immediate danger, do not rely on chat assistance. Contact emergency services now:</p>
          <div class="emergency-helpline-chips">
            <a href="tel:112" class="hotline-chip emergency-main"><strong>112</strong> Pan-India Emergency</a>
            <a href="tel:1078" class="hotline-chip"><strong>1078</strong> NDRF Disaster Rescue</a>
            <a href="tel:101" class="hotline-chip"><strong>101</strong> Fire &amp; Rescue</a>
            <a href="tel:108" class="hotline-chip"><strong>108</strong> Medical Ambulance</a>
          </div>
        </div>
      </div>
    `;
  }

  let statusBadgeHtml = '';
  if (data.evidence_found) {
    statusBadgeHtml = `<span class="rag-status-badge verified" title="Retrieved from official statutory documents">&#x2713; Verified Official Evidence (${data.retrieved_chunks_count} passages)</span>`;
  } else {
    statusBadgeHtml = `<span class="rag-status-badge insufficient" title="Knowledge base did not yield sufficient official passages">&#x26A0; Insufficient Evidence</span>`;
  }

  // Build Citations & Expandable Evidence Tray
  let citationsHtml = '';
  if (data.citations && data.citations.length > 0) {
    let citationBadges = '';
    let evidencePassagesHtml = '';

    data.citations.forEach((cit, idx) => {
      const citNum = idx + 1;
      const docTitle = cit.document_title || cit.document_id;
      const pageStr = cit.page_number ? `p. ${cit.page_number}` : 'Official Guideline';
      const authority = cit.issuing_organization || 'Official Authority';

      citationBadges += `
        <span class="citation-pill" title="${escapeHtml(authority)} — ${escapeHtml(docTitle)}">
          <span class="citation-index">[${citNum}]</span>
          <span class="citation-title">${escapeHtml(docTitle)}</span>
          <span class="citation-page">(${escapeHtml(pageStr)})</span>
        </span>
      `;

      evidencePassagesHtml += `
        <div class="evidence-passage-card">
          <div class="evidence-passage-top">
            <span class="evidence-badge">[${citNum}] ${escapeHtml(authority)}</span>
            <span class="evidence-page-tag">${escapeHtml(pageStr)}</span>
            ${cit.disaster_category ? `<span class="evidence-cat-tag">${escapeHtml(cit.disaster_category.toUpperCase())}</span>` : ''}
          </div>
          <div class="evidence-doc-name">${escapeHtml(docTitle)}</div>
          ${cit.section_heading ? `<div class="evidence-section-name">&sect; ${escapeHtml(cit.section_heading)}</div>` : ''}
          <blockquote class="evidence-quote">${escapeHtml(cit.snippet || cit.content || '')}</blockquote>
          ${cit.source_url ? `<a href="${cit.source_url}" target="_blank" rel="noopener noreferrer" class="evidence-url-link"><span>Verify Official Document (${escapeHtml(cit.source_url)})</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-sm"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg></a>` : ''}
        </div>
      `;
    });

    const drawerId = 'evidenceDrawer_' + Math.floor(Math.random() * 100000);
    citationsHtml = `
      <div class="rag-citations-container">
        <div class="citations-header">
          <span class="citations-title">Verified Official References:</span>
          <div class="citations-badges-list">${citationBadges}</div>
        </div>
        <div class="evidence-accordion">
          <button type="button" class="evidence-toggle-btn" onclick="toggleEvidenceDrawer('${drawerId}')">
            <span>Inspect Retrieved Evidence Passages (${data.citations.length})</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-sm chevron-icon"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
          <div id="${drawerId}" class="evidence-drawer" style="display:none;">
            ${evidencePassagesHtml}
          </div>
        </div>
      </div>
    `;
  }

  botDiv.innerHTML = `
    <div class="rag-msg-avatar bot" aria-hidden="true">RAG</div>
    <div class="rag-msg-bubble bot">
      <div class="rag-msg-meta">
        <span class="rag-msg-author">DisasterShield Knowledge Assistant</span>
        <span class="rag-msg-time">${now}</span>
        ${statusBadgeHtml}
      </div>
      ${emergencyBannerHtml}
      <div class="rag-answer-body">
        ${formatRagText(data.answer)}
      </div>
      ${citationsHtml}
    </div>
  `;

  streamList.appendChild(botDiv);
  scrollRagToBottom();
}

function toggleEvidenceDrawer(drawerId) {
  const drawer = document.getElementById(drawerId);
  if (!drawer) return;
  const isHidden = drawer.style.display === 'none';
  drawer.style.display = isHidden ? 'block' : 'none';
}
window.toggleEvidenceDrawer = toggleEvidenceDrawer;

function scrollRagToBottom() {
  const vp = document.getElementById('ragConversationViewport');
  if (vp) {
    vp.scrollTop = vp.scrollHeight;
  }
}

async function askRAG(queryText, category) {
  if (!queryText || !queryText.trim() || AppState.isRagLoading) return;
  const cleanQuery = queryText.trim();

  AppState.isRagLoading = true;
  const submitBtn = document.getElementById('btnSubmitRAG');
  if (submitBtn) submitBtn.disabled = true;

  // Clear welcome card if present
  const welcomeCard = document.querySelector('.rag-welcome-card');
  if (welcomeCard) welcomeCard.remove();

  renderRagUserMessage(cleanQuery);
  const loaderId = renderRagLoadingIndicator();

  try {
    const payload = {
      query: cleanQuery,
      category: category || AppState.ragFilterCategory || null
    };

    const response = await fetch('/api/rag/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    removeRagLoadingIndicator(loaderId);

    if (data.status === 'success') {
      renderRagAssistantAnswer(data);
    } else {
      renderRagErrorCard(data.message || 'Error generating grounded answer.');
    }
  } catch (err) {
    console.error('RAG request failed:', err);
    removeRagLoadingIndicator(loaderId);
    renderRagErrorCard('Failed to reach RAG assistant. Please check your local server.');
  } finally {
    AppState.isRagLoading = false;
    if (submitBtn) submitBtn.disabled = false;
    const input = document.getElementById('ragInputText');
    if (input) {
      input.value = '';
      input.focus();
    }
  }
}

function renderRagErrorCard(errorMessage) {
  const streamList = document.getElementById('ragStreamList');
  if (!streamList) return;

  const errDiv = document.createElement('div');
  errDiv.className = 'rag-msg bot';
  errDiv.innerHTML = `
    <div class="rag-msg-avatar bot" aria-hidden="true">RAG</div>
    <div class="rag-msg-bubble bot">
      <div class="rag-error-box">
        <strong>Error Processing Request</strong>
        <p>${escapeHtml(errorMessage)}</p>
      </div>
    </div>
  `;
  streamList.appendChild(errDiv);
  scrollRagToBottom();
}

// ==========================================================================
// DOCUMENT REPOSITORY & ADMIN CONTROLLER
// ==========================================================================

async function loadDocumentCatalog() {
  const tableBody = document.getElementById('indexedDocsTableBody');
  const countBadge = document.getElementById('indexedDocsCount');
  if (!tableBody) return;

  try {
    const response = await fetch('/api/rag/documents');
    const data = await response.json();

    if (data.status !== 'success') {
      tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:red; padding:1.5rem;">Failed to load documents: ${escapeHtml(data.message)}</td></tr>`;
      return;
    }

    const docs = data.documents || [];
    if (countBadge) countBadge.textContent = `${docs.length} ${docs.length === 1 ? 'document' : 'documents'}`;

    if (docs.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center; color:#64748b; padding:2.5rem;">
            No official documents indexed yet. Upload an official PDF above to build your vector knowledge base.
          </td>
        </tr>
      `;
      return;
    }

    let rowsHtml = '';
    docs.forEach(doc => {
      const fileSizeKB = (doc.file_size_bytes / 1024).toFixed(1);
      const titleLink = doc.source_url
        ? `<a href="${doc.source_url}" target="_blank" rel="noopener noreferrer" class="doc-table-link">${escapeHtml(doc.title)}</a>`
        : `<strong>${escapeHtml(doc.title)}</strong>`;

      rowsHtml += `
        <tr>
          <td>
            ${titleLink}
            <div class="doc-table-sub">${escapeHtml(doc.filename)}</div>
          </td>
          <td>${escapeHtml(doc.issuing_organization || 'Official')}</td>
          <td><span class="doc-category-badge cat-${doc.disaster_category}">${escapeHtml(doc.disaster_category.toUpperCase())}</span></td>
          <td>${doc.page_count}</td>
          <td>${doc.chunk_count}</td>
          <td>${fileSizeKB} KB</td>
          <td>
            <button class="btn-table-delete" onclick="handleDocDelete('${doc.doc_id}', '${escapeHtml(doc.title.replace(/'/g, ''))}')" title="Delete document from vector index">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-sm"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              <span>Delete</span>
            </button>
          </td>
        </tr>
      `;
    });

    tableBody.innerHTML = rowsHtml;
  } catch (err) {
    console.error('Failed to load documents catalog:', err);
    tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:red; padding:1.5rem;">Failed to connect to document server.</td></tr>`;
  }
}

async function handleDocUpload(e) {
  e.preventDefault();
  const form = document.getElementById('docUploadForm');
  const fileInput = document.getElementById('pdfFileInput');
  const statusMsg = document.getElementById('uploadStatusMsg');
  const submitBtn = document.getElementById('btnUploadSubmit');

  if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
    showToast('Please select a PDF file to upload.');
    return;
  }

  const formData = new FormData(form);

  if (statusMsg) {
    statusMsg.style.display = 'block';
    statusMsg.className = 'upload-status-msg info';
    statusMsg.innerHTML = '<span class="status-spinner"></span> Extracting text, creating chunks &amp; generating embeddings...';
  }
  if (submitBtn) submitBtn.disabled = true;

  try {
    const response = await fetch('/api/rag/upload', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (data.status === 'success') {
      if (statusMsg) {
        statusMsg.className = 'upload-status-msg success';
        statusMsg.textContent = `Success: "${data.document.title}" indexed (${data.document.pages} pages, ${data.document.chunks} chunks).`;
      }
      showToast('Document indexed into vector store.');
      form.reset();
      const dropText = document.getElementById('fileDropText');
      if (dropText) dropText.textContent = 'Click or drag official PDF file here';
      loadDocumentCatalog();
    } else {
      if (statusMsg) {
        statusMsg.className = 'upload-status-msg error';
        statusMsg.textContent = `Upload failed: ${data.message}`;
      }
      showToast('Upload rejected: ' + data.message);
    }
  } catch (err) {
    console.error('Upload failed:', err);
    if (statusMsg) {
      statusMsg.className = 'upload-status-msg error';
      statusMsg.textContent = 'Network error while uploading document.';
    }
    showToast('Upload failed due to network error.');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function handleDocDelete(docId, docTitle) {
  if (!confirm(`Are you sure you want to remove "${docTitle}" and its associated vectors from the FAISS index?`)) {
    return;
  }

  try {
    const response = await fetch(`/api/rag/documents/${encodeURIComponent(docId)}`, {
      method: 'DELETE'
    });
    const data = await response.json();

    if (data.status === 'success') {
      showToast(`Removed "${docTitle}" from knowledge base.`);
      loadDocumentCatalog();
    } else {
      showToast(`Delete failed: ${data.message}`);
    }
  } catch (err) {
    console.error('Delete request failed:', err);
    showToast('Network error while deleting document.');
  }
}
window.handleDocDelete = handleDocDelete;

async function handleRebuildIndex() {
  if (!confirm('Rebuild the entire FAISS vector index from stored official PDFs? This re-extracts and re-embeds all documents.')) {
    return;
  }

  showToast('Rebuilding vector index...');
  try {
    const response = await fetch('/api/rag/rebuild', {
      method: 'POST'
    });
    const data = await response.json();

    if (data.status === 'success') {
      showToast(`Index rebuilt successfully (${data.indexed_chunks} chunks).`);
      loadDocumentCatalog();
    } else {
      showToast(`Rebuild failed: ${data.message}`);
    }
  } catch (err) {
    console.error('Rebuild request failed:', err);
    showToast('Failed to rebuild vector index.');
  }
}
