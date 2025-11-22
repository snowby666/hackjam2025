// Popup script for Screenshot Sherlock

const API_BASE_URL = 'http://localhost:8000/api';

let authToken = null;
let currentMode = 'visible'; // visible, full, selection

// DOM Elements
const views = {
  auth: document.getElementById('authView'),
  main: document.getElementById('mainView'),
  settings: document.getElementById('settingsView')
};

const authForm = {
  form: document.getElementById('authForm'),
  email: document.getElementById('emailInput'),
  password: document.getElementById('passwordInput'),
  submitBtn: document.querySelector('#authForm button[type="submit"]'),
  btnText: document.querySelector('#authForm .btn-text'),
  loader: document.querySelector('#authForm .loader'),
  tabs: document.querySelectorAll('.tab-trigger')
};

const mainUI = {
  captureBtn: document.getElementById('captureBtn'),
  captureText: document.getElementById('captureBtnText'),
  loader: document.querySelector('#captureBtn .loader'),
  analysesList: document.getElementById('analysesList'),
  themeToggle: document.getElementById('themeToggle'),
  settingsBtn: document.getElementById('settingsBtn'),
  refreshBtn: document.getElementById('refreshBtn'),
  logoutBtn: document.getElementById('logoutBtn'),
  modeBtns: document.querySelectorAll('.mode-btn'),
  analysisOverlay: document.getElementById('analysisOverlay'),
  closeAnalysisBtn: document.getElementById('closeAnalysis'),
  deleteAnalysisBtn: document.getElementById('deleteAnalysisBtn'),
  analysisContent: document.getElementById('analysisContent')
};

const settingsUI = {
  view: document.getElementById('settingsView'),
  backBtn: document.getElementById('backFromSettings'),
  logoutBtn: document.getElementById('logoutBtnSettings'),
  saveBtn: document.getElementById('saveSettings'),
  emailDisplay: document.getElementById('userEmailDisplay'),
  uuidDisplay: document.getElementById('userUuidDisplay'),
  prefAttachment: document.getElementById('prefAttachment'),
  prefGoal: document.getElementById('prefGoal'),
  prefAdvanced: document.getElementById('prefAdvanced')
};

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  // Inject Toast
  if (!document.getElementById('toast')) {
    const toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast-notification';
    toast.innerHTML = `<span id="toastIcon">✅</span> <span id="toastMessage">Message</span>`;
    document.body.appendChild(toast);
  }

  // Reset UI state
  mainUI.analysisOverlay.classList.add('translate-y-full');
  
  // Load auth token
  authToken = await getAuthToken();
  
  // Initialize Theme
  initTheme();
  
  // Check authentication status
  if (!authToken) {
    showAuthView();
  } else {
    showMainView();
  }
  
  setupEventListeners();
});

function setupEventListeners() {
  // Auth Tabs
  authForm.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      authForm.tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const action = tab.dataset.tab;
      authForm.btnText.textContent = action === 'login' ? 'Sign In' : 'Create Account';
    });
  });

  // Auth Submit
  authForm.form.addEventListener('submit', handleAuth);

  // Logout / Theme / Refresh
  mainUI.logoutBtn.addEventListener('click', handleLogout);
  mainUI.themeToggle.addEventListener('click', toggleTheme);
  mainUI.refreshBtn.addEventListener('click', async () => {
    await loadRecentAnalyses();
    showToast("Refreshed!");
  });
  mainUI.settingsBtn.addEventListener('click', showSettingsView);

  // Screenshot Modes
  mainUI.modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      mainUI.modeBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentMode = btn.dataset.mode;
    });
  });

  // Capture Button
  mainUI.captureBtn.addEventListener('click', handleCapture);

  // Close Analysis Overlay
  mainUI.closeAnalysisBtn.addEventListener('click', closeAnalysis);
  
  // Delete Analysis
  mainUI.deleteAnalysisBtn.addEventListener('click', deleteCurrentAnalysis);

  // Settings view events
  settingsUI.backBtn.addEventListener('click', showMainView);
  settingsUI.logoutBtn.addEventListener('click', handleLogout);
  settingsUI.saveBtn.addEventListener('click', saveSettings);
}

// --- Authentication ---

async function handleAuth(e) {
  e.preventDefault();
  const email = authForm.email.value;
  const password = authForm.password.value;
  const isLogin = document.querySelector('.tab-trigger.active').dataset.tab === 'login';
  
  setAuthLoading(true);
  
  try {
    let endpoint = isLogin ? '/auth/login' : '/auth/register';
    let body;
    let headers = {};

    if (isLogin) {
      body = `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;
      headers['Content-Type'] = 'application/x-www-form-urlencoded';
    } else {
      body = JSON.stringify({ email, password });
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: headers,
      body: body
    });

    if (!response.ok) {
      // If login failed, try register (if in register mode)
      if (!isLogin) throw new Error('Registration failed');
      
      const error = await response.json();
      throw new Error(error.detail || 'Authentication failed');
    }

    const data = await response.json();
    authToken = data.access_token;
    await setAuthToken(authToken);
    
    showMainView();
    authForm.form.reset();
    
  } catch (error) {
    alert(error.message);
  } finally {
    setAuthLoading(false);
  }
}

function setAuthLoading(isLoading) {
  authForm.submitBtn.disabled = isLoading;
  authForm.loader.classList.toggle('hidden', !isLoading);
  authForm.btnText.style.opacity = isLoading ? '0' : '1';
}

async function handleLogout() {
  authToken = null;
  await setAuthToken(null);
  showAuthView();
}

// --- UI State Management ---

function hideAllViews() {
  Object.values(views).forEach(view => {
    if (view) view.classList.add('hidden');
  });
}

function showAuthView() {
  hideAllViews();
  views.auth.classList.remove('hidden');
  mainUI.logoutBtn.classList.add('hidden');
}

async function showMainView() {
  hideAllViews();
  views.main.classList.remove('hidden');
  mainUI.logoutBtn.classList.remove('hidden');
  await loadRecentAnalyses();
}

async function showSettingsView() {
  hideAllViews();
  views.settings.classList.remove('hidden');
  await loadUserSettings();
}

function initTheme() {
  const isDark = localStorage.getItem('theme') === 'dark' || 
                 (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
  if (isDark) document.body.classList.add('dark');
}

function toggleTheme() {
  document.body.classList.toggle('dark');
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
}

// --- Screenshot & Analysis ---

async function handleCapture() {
  setCaptureLoading(true);
  
  try {
    let screenshotData;

    if (currentMode === 'selection') {
      // Send message to background to initiate selection flow
      // We do this via background so the process survives popup closing
      chrome.runtime.sendMessage({ action: 'initiateSelection' });
      window.close();
      return;
    } else {
      screenshotData = await captureScreenshot();
    }

    const uploadResult = await uploadScreenshot(screenshotData.imageData);
    const analysis = await analyzeScreenshot(uploadResult.conversation_id);
    
    showAnalysis(analysis);
    await loadRecentAnalyses();
    
  } catch (error) {
    console.error('Capture error:', error);
    alert('Error: ' + error.message);
  } finally {
    setCaptureLoading(false);
  }
}

function setCaptureLoading(isLoading) {
  mainUI.captureBtn.disabled = isLoading;
  mainUI.loader.classList.toggle('hidden', !isLoading);
  mainUI.captureText.textContent = isLoading ? 'Analyzing...' : 'Analyze Conversation';
}

async function loadRecentAnalyses() {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations/`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    const conversations = await response.json();
    
    mainUI.analysesList.innerHTML = conversations.map(conv => renderAnalysisCard(conv)).join('');
    
    // Attach event listeners after rendering
    document.querySelectorAll('.analysis-card[data-id]').forEach(card => {
      card.addEventListener('click', () => {
        if (card.dataset.id && card.dataset.id !== 'undefined') {
            viewAnalysis(card.dataset.id);
        }
      });
    });
  } catch (error) {
    console.error('Failed to load history', error);
  }
}

function renderAnalysisCard(conv) {
  const score = conv.latest_interest_score;
  const hasAnalysis = score !== null && score !== undefined;
  const name = conv.participant_name || 'Unknown';
  const platform = conv.platform || 'Chat';
  const dateObj = new Date(conv.updated_at || Date.now());
  const dateStr = dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  
  // Calculate time difference in minutes
  const timeDiff = (Date.now() - dateObj.getTime()) / (1000 * 60);
  
  // If no analysis yet...
  if (!hasAnalysis) {
    // If it's been more than 10 minutes, assume failure
    if (timeDiff > 10) {
       return `
        <div class="analysis-card" style="border-left: 4px solid #ef4444;">
          <div class="card-top">
            <div class="card-user">
              <div class="card-avatar" style="background: #fee2e2; color: #ef4444;">❌</div>
              <div class="card-meta">
                <span class="card-name">${name}</span>
                <span class="card-platform">${platform}</span>
              </div>
            </div>
            <span class="card-date">${dateStr}</span>
          </div>
          <div class="card-status" style="color: #ef4444; justify-content: space-between;">
            <span>Analysis Failed</span>
            <button class="copy-pill" style="background: #fee2e2; color: #ef4444;" onclick="event.stopPropagation(); retryAnalysis('${conv.id}')">Retry</button>
          </div>
        </div>
      `;
    }
  
    // Otherwise show pending state
    return `
      <div class="analysis-card opacity-70" style="cursor: default;">
        <div class="card-top">
          <div class="card-user">
            <div class="card-avatar">⏳</div>
            <div class="card-meta">
              <span class="card-name">${name}</span>
              <span class="card-platform">${platform}</span>
            </div>
          </div>
          <span class="card-date">${dateStr}</span>
        </div>
        <div class="card-status">
          <div class="status-dot"></div>
          Analysis Pending...
        </div>
      </div>
    `;
  }

  const colorClass = score > 75 ? '#22c55e' : score > 40 ? '#eab308' : '#ef4444';
  
  return `
    <div class="analysis-card" data-id="${conv.latest_analysis_id}">
      <div class="card-top">
        <div class="card-user">
          <div class="card-avatar">👤</div>
          <div class="card-meta">
            <span class="card-name">${name}</span>
            <span class="card-platform">${platform}</span>
          </div>
        </div>
        <span class="card-date">${dateStr}</span>
      </div>
      
      <div class="card-score-row">
        <span class="card-score-val" style="color: ${colorClass}">${score}%</span>
        <div class="card-score-bar-container">
          <div class="card-score-bar-fill" style="width: ${score}%; background-color: ${colorClass}"></div>
        </div>
      </div>
      
      <div class="card-status">
        <div class="status-dot active"></div>
        Click to view details
      </div>
    </div>
  `;
}

let currentAnalysisId = null;

async function retryAnalysis(conversationId) {
  if (!confirm("Retry analysis for this conversation?")) return;
  
  try {
    // We can't fully retry without the original image unless we stored it (which we usually don't for privacy/storage reasons in this MVP)
    // But if the user just wants to delete the failed entry, we can offer that.
    // Or if the backend supports re-analyzing existing conversation images (if stored).
    // Assuming backend stores images in 'screenshots' array of conversation.
    
    const response = await fetch(`${API_BASE_URL}/analyze/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ conversation_id: conversationId, screenshot_index: 0 })
    });
    
    if (!response.ok) throw new Error('Retry failed');
    
    showToast("Analysis started...");
    await loadRecentAnalyses(); // Refresh to show pending
  } catch (error) {
    alert('Failed to retry analysis: ' + error.message);
  }
}

async function viewAnalysis(analysisId) {
  currentAnalysisId = analysisId;
  try {
    const response = await fetch(`${API_BASE_URL}/analyze/${analysisId}`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    const analysis = await response.json();
    showAnalysis(analysis);
  } catch (error) {
    alert('Failed to load analysis');
  }
}

async function deleteCurrentAnalysis() {
  if (!currentAnalysisId) return;
  
  if (!confirm("Are you sure you want to delete this analysis?")) return;
  
  try {
    const response = await fetch(`${API_BASE_URL}/analyze/${currentAnalysisId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    if (!response.ok) throw new Error("Failed to delete");
    
    showToast("Analysis deleted", "🗑️");
    closeAnalysis();
    await loadRecentAnalyses();
  } catch (error) {
    alert("Error deleting analysis");
  }
}

function showAnalysis(analysis) {
  mainUI.analysisContent.innerHTML = `
    <div class="space-y-4">
      <!-- Score Section -->
      <div class="score-container-large">
        <div class="score-ring" style="--score-deg: ${analysis.interest_score * 3.6}deg">
          <div class="score-inner">
            <div class="score-val-large">${analysis.interest_score}</div>
            <div class="score-label-large">Interest</div>
          </div>
        </div>
      </div>

      <!-- Wingman Wisdom (Top Priority) -->
      <div class="section-card wingman-box">
        <div class="section-title" style="color: var(--primary)">
          <span>🕊️</span> Wingman Wisdom
        </div>
        <p class="wingman-text">
          ${analysis.wingman_notes}
        </p>
      </div>

      <!-- Vibe Report -->
      <div class="section-card">
        <div class="section-title">📊 Vibe Report</div>
        <div class="vibe-grid">
          <div class="vibe-item">
            <span class="vibe-value">${analysis.vibe_report.overall_mood}</span>
            <span class="vibe-key">Mood</span>
          </div>
          <div class="vibe-item">
            <span class="vibe-value">${analysis.vibe_report.engagement_level}</span>
            <span class="vibe-key">Engagement</span>
          </div>
          <div class="vibe-item">
            <span class="vibe-value">${analysis.vibe_report.communication_style}</span>
            <span class="vibe-key">Style</span>
          </div>
        </div>
      </div>

      <!-- Flags -->
      ${renderFlags(analysis.green_flags, 'green')}
      ${renderFlags(analysis.red_flags, 'red')}

      <!-- Replies -->
      <div>
        <div class="section-title" style="margin-bottom: 0.5rem; margin-left: 0.5rem;">
          💬 Suggested Replies
        </div>
        <div>
          ${analysis.suggested_replies.map((reply, i) => `
            <div class="reply-card-btn" data-text="${reply.text.replace(/"/g, '&quot;')}">
              <p class="reply-text pointer-events-none">${reply.text}</p>
              <div class="reply-meta pointer-events-none">
                <span class="reply-tone">${reply.tone}</span>
                <div>
                  <span class="reply-success">${Math.round(reply.success_probability * 100)}% Success</span>
                </div>
              </div>
              <div style="margin-top:8px; text-align:right;">
                <button class="copy-pill copy-reply" data-text="${reply.text.replace(/"/g, '&quot;')}">Copy</button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
  
  mainUI.analysisOverlay.classList.remove('translate-y-full');

  // Attach listeners
  document.querySelectorAll('.copy-reply').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation(); // Prevent card click
      copyReply(btn.dataset.text);
    });
  });
  
  // Keep card listeners for full card click copy behavior if desired
  document.querySelectorAll('.reply-card-btn').forEach(card => {
    card.addEventListener('click', () => {
       copyReply(card.dataset.text);
    });
  });
}

function renderFlags(flags, type) {
  if (!flags || flags.length === 0) return '';
  const color = type === 'green' ? '#16a34a' : '#dc2626';
  const icon = type === 'green' ? '✅' : '⚠️';
  const title = type === 'green' ? 'Green Flags' : 'Red Flags';
  
  return `
    <div class="section-card" style="border-left: 4px solid ${color}">
      <div class="section-title" style="color: ${color}">
        <span>${icon}</span> ${title}
      </div>
      <ul class="flag-list">
        ${flags.map(flag => `
          <li class="flag-item">
            <span class="flag-icon">•</span>
            <span>
              <strong style="font-weight:600; text-transform:capitalize">${flag.type.replace(/_/g, ' ')}</strong>: 
              ${flag.evidence}
            </span>
          </li>
        `).join('')}
      </ul>
    </div>
  `;
}

function closeAnalysis() {
  mainUI.analysisOverlay.classList.add('translate-y-full');
}

// --- Helpers from utils (inlined for safety) ---
async function getAuthToken() {
  if (typeof chrome !== 'undefined' && chrome.storage) {
    return new Promise((resolve) => {
      chrome.storage.local.get(['authToken'], (result) => {
        resolve(result.authToken);
      });
    });
  }
  return null;
}

async function setAuthToken(token) {
  if (typeof chrome !== 'undefined' && chrome.storage) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ authToken: token }, () => {
        resolve();
      });
    });
  }
}

async function captureScreenshot() {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ action: 'captureScreenshot' }, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else if (response.error) {
        reject(new Error(response.error));
      } else {
        resolve(response);
      }
    });
  });
}

async function uploadScreenshot(imageData) {
  const blob = await base64ToBlob(imageData, 'image/png');
  const formData = new FormData();
  formData.append('image', blob, 'screenshot.png');
  
  const response = await fetch(`${API_BASE_URL}/screenshot/upload`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${authToken}` },
    body: formData
  });
  
  if (!response.ok) throw new Error('Upload failed');
  return await response.json();
}

async function analyzeScreenshot(conversationId) {
  const response = await fetch(`${API_BASE_URL}/analyze/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({ conversation_id: conversationId })
  });
  
  if (!response.ok) throw new Error('Analysis failed');
  return await response.json();
}

async function base64ToBlob(base64, mimeType) {
  const res = await fetch(`data:${mimeType};base64,${base64}`);
  return await res.blob();
}

// --- Toast ---
function showToast(message, icon = '✅') {
  const toast = document.getElementById('toast');
  const msg = document.getElementById('toastMessage');
  const ico = document.getElementById('toastIcon');
  
  if (!toast) return;
  
  msg.textContent = message;
  ico.textContent = icon;
  
  toast.classList.add('visible');
  
  setTimeout(() => {
    toast.classList.remove('visible');
  }, 3000);
}

// Global for onclick handlers - Removed inline handlers
function copyReply(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast("Reply copied to clipboard!");
  }).catch(() => {
    showToast("Failed to copy", "❌");
  });
};

// --- Settings Logic ---
async function loadUserSettings() {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    if (!response.ok) return;

    const user = await response.json();
    settingsUI.emailDisplay.textContent = user.email;
    settingsUI.uuidDisplay.textContent = user.uuid || '—';

    if (user.preferences) {
      if (user.preferences.attachment_style) settingsUI.prefAttachment.value = user.preferences.attachment_style;
      if (user.preferences.dating_goal) settingsUI.prefGoal.value = user.preferences.dating_goal;
      // Robust boolean check
      const adv = user.preferences.advanced_mode;
      settingsUI.prefAdvanced.checked = (adv === true || adv === 'true');
    }
  } catch (error) {
    console.error('Failed to load settings', error);
  }
}

async function saveSettings() {
  const originalText = settingsUI.saveBtn.textContent;
  settingsUI.saveBtn.disabled = true;
  settingsUI.saveBtn.textContent = 'Saving...';
  try {
    const prefs = {
      attachment_style: settingsUI.prefAttachment.value,
      dating_goal: settingsUI.prefGoal.value,
      communication_style: 'direct',
      advanced_mode: settingsUI.prefAdvanced.checked
    };
    const response = await fetch(`${API_BASE_URL}/auth/profile`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(prefs)
    });
    if (!response.ok) throw new Error('Failed to save');
    settingsUI.saveBtn.textContent = 'Saved!';
    setTimeout(() => settingsUI.saveBtn.textContent = originalText, 2000);
  } catch (error) {
    alert('Unable to save settings');
    settingsUI.saveBtn.textContent = originalText;
  } finally {
    settingsUI.saveBtn.disabled = false;
  }
}
