/**
 * DisasterShield — Application Controller
 * Handles tab navigation, interactive decision-tree chatbot state machine,
 * 72-hour emergency go-bag checklist, and official references.
 * 100% deterministic rule-based emergency guidance.
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
  checkedItems: new Set()
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
    checklist: document.getElementById('paneChecklist'),
    flowchart: document.getElementById('paneFlowchart'),
    sources: document.getElementById('paneSources')
  };

  Object.entries(panes).forEach(([tab, pane]) => {
    if (pane) pane.classList.toggle('active', tab === targetTabId);
  });

  // Requirement 7: Hide footer on mobile for all views except landing page
  const footer = document.querySelector('.app-footer');
  if (footer) {
    footer.classList.toggle('hide-on-mobile', targetTabId !== 'home');
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // If switching to flowchart tab, refresh flowchart
  if (targetTabId === 'flowchart' && window.FlowchartViewer) {
    const disasterToLoad = AppState.activeDisasterId || 'earthquake';
    window.FlowchartViewer.loadFlowchart(disasterToLoad);
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

    // Update Chat UI Header (Desktop & Mobile)
    const badge = document.getElementById('chatDisasterBadge');
    if (badge) badge.textContent = session.disaster_name;

    const title = document.getElementById('chatDisasterTitle');
    if (title) title.textContent = `${session.disaster_name} Safety Assessment`;

    const tracker = document.getElementById('chatStepTracker');
    if (tracker) tracker.textContent = `Step ${session.step} of 4`;

    const activeInd = document.getElementById('chatActiveIndicator');
    if (activeInd) activeInd.style.display = 'inline-block';

    const mobTitle = document.getElementById('chatMobileDisasterTitle');
    if (mobTitle) mobTitle.textContent = `${session.disaster_name} Safety`;

    const mobTracker = document.getElementById('chatMobileStepTracker');
    if (mobTracker) mobTracker.textContent = `Step ${session.step} of 4`;

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
  scrollChatToBottom(msgDiv);

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

    const tracker = document.getElementById('chatStepTracker');
    if (tracker) tracker.textContent = `Step ${stepResult.step} of 4`;
    const mobTracker = document.getElementById('chatMobileStepTracker');
    if (mobTracker) mobTracker.textContent = `Step ${stepResult.step} of 4`;

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
  scrollChatToBottom(msgDiv);
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
  scrollChatToBottom(container);
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

function scrollChatToBottom(targetElem) {
  const viewport = document.getElementById('chatViewport');
  const messagesList = document.getElementById('chatMessagesList');
  if (!viewport) return;
  setTimeout(() => {
    const target = targetElem || (messagesList ? messagesList.lastElementChild : null);
    if (target && target.offsetTop !== undefined) {
      const scrollPos = Math.max(0, target.offsetTop - 12);
      viewport.scrollTo({ top: scrollPos, behavior: 'smooth' });
    } else {
      viewport.scrollTo({ top: viewport.scrollHeight, behavior: 'smooth' });
    }
  }, 60);
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

  // Setup Disaster Cards click handlers (whole card tappable)
  document.querySelectorAll('.disaster-card').forEach(card => {
    card.addEventListener('click', (e) => {
      const disaster = card.dataset.disaster;
      if (disaster) startDisasterChat(disaster);
    });
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        const disaster = card.dataset.disaster;
        if (disaster) startDisasterChat(disaster);
      }
    });
  });

  // Setup Chat Header Action Buttons (Desktop)
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

  // Setup Mobile Compact Controls & Overflow Menu (Item 1)
  const btnMobileRestart = document.getElementById('btnMobileRestartChat');
  if (btnMobileRestart) btnMobileRestart.addEventListener('click', () => {
    if (AppState.activeDisasterId) startDisasterChat(AppState.activeDisasterId);
  });

  const btnChatOverflow = document.getElementById('btnChatOverflow');
  const chatOverflowMenu = document.getElementById('chatOverflowMenu');
  if (btnChatOverflow && chatOverflowMenu) {
    btnChatOverflow.addEventListener('click', (e) => {
      e.stopPropagation();
      const isHidden = chatOverflowMenu.style.display === 'none' || !chatOverflowMenu.style.display;
      chatOverflowMenu.style.display = isHidden ? 'flex' : 'none';
      btnChatOverflow.setAttribute('aria-expanded', String(isHidden));
    });

    document.addEventListener('click', (e) => {
      if (!chatOverflowMenu.contains(e.target) && e.target !== btnChatOverflow) {
        chatOverflowMenu.style.display = 'none';
        btnChatOverflow.setAttribute('aria-expanded', 'false');
      }
    });
  }

  const btnMobileChange = document.getElementById('btnMobileChangeDisaster');
  if (btnMobileChange) btnMobileChange.addEventListener('click', () => {
    if (chatOverflowMenu) chatOverflowMenu.style.display = 'none';
    switchTab('home');
  });

  const btnMobileFlowchart = document.getElementById('btnMobileViewFlowchart');
  if (btnMobileFlowchart) btnMobileFlowchart.addEventListener('click', () => {
    if (chatOverflowMenu) chatOverflowMenu.style.display = 'none';
    switchTab('flowchart');
    if (window.FlowchartViewer && AppState.activeDisasterId) {
      window.FlowchartViewer.loadFlowchart(AppState.activeDisasterId);
    }
  });

  const btnMobileCopy = document.getElementById('btnMobileCopyTranscript');
  if (btnMobileCopy) btnMobileCopy.addEventListener('click', () => {
    if (chatOverflowMenu) chatOverflowMenu.style.display = 'none';
    copyTranscript();
  });

  const btnMobileDown = document.getElementById('btnMobileDownloadTranscript');
  if (btnMobileDown) btnMobileDown.addEventListener('click', () => {
    if (chatOverflowMenu) chatOverflowMenu.style.display = 'none';
    downloadTranscript();
  });

  const btnMobileRestartMenu = document.getElementById('btnMobileRestartMenu');
  if (btnMobileRestartMenu) btnMobileRestartMenu.addEventListener('click', () => {
    if (chatOverflowMenu) chatOverflowMenu.style.display = 'none';
    if (AppState.activeDisasterId) startDisasterChat(AppState.activeDisasterId);
  });

  // Setup Emergency Helplines Modal (Item 4)
  const btnCall112 = document.getElementById('btnCall112');
  const helplinesModal = document.getElementById('emergencyHelplinesModal');
  const btnCloseHelplines = document.getElementById('btnCloseHelplines');
  const btnDismissHelplines = document.getElementById('btnDismissHelplines');

  function openHelplines() {
    if (helplinesModal) helplinesModal.style.display = 'flex';
  }
  function closeHelplines() {
    if (helplinesModal) helplinesModal.style.display = 'none';
  }

  if (btnCall112) btnCall112.addEventListener('click', openHelplines);
  if (btnCloseHelplines) btnCloseHelplines.addEventListener('click', closeHelplines);
  if (btnDismissHelplines) btnDismissHelplines.addEventListener('click', closeHelplines);
  if (helplinesModal) {
    helplinesModal.addEventListener('click', (e) => {
      if (e.target === helplinesModal) closeHelplines();
    });
  }

  // Setup Mobile Nav Toggle (Item 6)
  const btnNavToggle = document.getElementById('btnNavToggle');
  const mainNavLinks = document.getElementById('mainNavLinks');
  if (btnNavToggle && mainNavLinks) {
    btnNavToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = mainNavLinks.classList.toggle('mobile-open');
      btnNavToggle.setAttribute('aria-expanded', String(isOpen));
    });

    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        mainNavLinks.classList.remove('mobile-open');
        btnNavToggle.setAttribute('aria-expanded', 'false');
      });
    });

    document.addEventListener('click', (e) => {
      if (!mainNavLinks.contains(e.target) && e.target !== btnNavToggle) {
        mainNavLinks.classList.remove('mobile-open');
        btnNavToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Escape key closes modals and dropdowns
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeHelplines();
      if (chatOverflowMenu) chatOverflowMenu.style.display = 'none';
      if (mainNavLinks) mainNavLinks.classList.remove('mobile-open');
    }
  });

  // Default About section collapsed on small screens (Item 5)
  const aboutCollapsible = document.getElementById('aboutCollapsible');
  if (aboutCollapsible && window.innerWidth <= 640) {
    aboutCollapsible.removeAttribute('open');
  }

  // Setup Checklist reset button
  const btnResetChk = document.getElementById('btnResetChecklist');
  if (btnResetChk) btnResetChk.addEventListener('click', resetChecklist);

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
