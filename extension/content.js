// Content script for Screenshot Sherlock

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getPageInfo') {
    sendResponse({
      url: window.location.href,
      title: document.title
    });
  } else if (request.action === 'startSelection') {
    startSelectionMode().then(area => {
      // Send directly to background instead of returning to (closed) popup
      chrome.runtime.sendMessage({ action: 'cropCapture', area: area });
    }).catch(err => {
      console.error('Selection failed:', err);
    });
    return true; // Async response
  } else if (request.action === 'downloadPdf') {
    createPdfFromImage(request.imageData);
  } else if (request.action === 'analyzeCropped') {
    // Show sidebar with loading state, then trigger analysis
    injectWingmanSidebar(request.imageData);
  }
});

// --- Selection Mode ---
let selectionCanvas = null;
let selectionCtx = null;
let startX, startY, endX, endY;
let isSelecting = false;

function startSelectionMode() {
  return new Promise((resolve, reject) => {
    if (selectionCanvas) return; // Already active

    // Create overlay
    selectionCanvas = document.createElement('canvas');
    selectionCanvas.style.position = 'fixed';
    selectionCanvas.style.top = '0';
    selectionCanvas.style.left = '0';
    selectionCanvas.style.width = '100vw';
    selectionCanvas.style.height = '100vh';
    selectionCanvas.style.zIndex = '2147483647'; // Max z-index
    selectionCanvas.style.cursor = 'crosshair';
    
    // Handle High DPI displays
    const dpr = window.devicePixelRatio || 1;
    selectionCanvas.width = window.innerWidth * dpr;
    selectionCanvas.height = window.innerHeight * dpr;
    
    document.body.appendChild(selectionCanvas);
    selectionCtx = selectionCanvas.getContext('2d');
    selectionCtx.scale(dpr, dpr);

    // Draw initial dim background
    drawSelection();

    // Handlers
    const onMouseDown = (e) => {
      isSelecting = true;
      startX = e.clientX;
      startY = e.clientY;
      endX = e.clientX;
      endY = e.clientY;
      drawSelection();
    };

    const onMouseMove = (e) => {
      // Always update mouse position for cursor feedback or hover effects if needed
      if (isSelecting) {
        endX = e.clientX;
        endY = e.clientY;
        drawSelection();
      }
    };

    const onMouseUp = (e) => {
      if (!isSelecting) return;
      isSelecting = false;
      endX = e.clientX;
      endY = e.clientY;
      
      // Calculate area
      const x = Math.min(startX, endX);
      const y = Math.min(startY, endY);
      const width = Math.abs(endX - startX);
      const height = Math.abs(endY - startY);

      // Cleanup
      cleanupSelection();

      if (width < 5 || height < 5) {
        // Just a click, treat as cancel
        reject(new Error('Selection too small'));
        return;
      }

      // Resolve with coordinates relative to viewport, adjusted for DPR in background script if needed
      // We return standard CSS pixels here, background script will handle scaling
      resolve({
        x: x,
        y: y,
        width: width,
        height: height,
        devicePixelRatio: dpr
      });
    };

    const onKeyDown = (e) => {
      if (e.key === 'Escape') {
        cleanupSelection();
        reject(new Error('Selection cancelled'));
      }
    };

    selectionCanvas.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('keydown', onKeyDown);

    function cleanupSelection() {
      if (selectionCanvas) {
        selectionCanvas.remove();
        selectionCanvas = null;
      }
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('keydown', onKeyDown);
    }
  });
}

function drawSelection() {
  if (!selectionCtx) return;
  const w = window.innerWidth;
  const h = window.innerHeight;

  // Clear entire canvas
  selectionCtx.clearRect(0, 0, w, h);

  // Draw dim background
  selectionCtx.fillStyle = 'rgba(0, 0, 0, 0.5)';
  selectionCtx.fillRect(0, 0, w, h);

  if (typeof startX !== 'undefined') {
    // Calculate selection rect
    const x = Math.min(startX, endX);
    const y = Math.min(startY, endY);
    const width = Math.abs(endX - startX);
    const height = Math.abs(endY - startY);
    
    // Clear selection area (make it transparent)
    selectionCtx.clearRect(x, y, width, height);
    
    // Draw border
    selectionCtx.strokeStyle = '#fff';
    selectionCtx.lineWidth = 2;
    selectionCtx.setLineDash([5, 5]);
    selectionCtx.strokeRect(x, y, width, height);
    
    // Draw label
    if (width > 50) {
      selectionCtx.fillStyle = '#fff';
      selectionCtx.font = '14px sans-serif';
      selectionCtx.setLineDash([]);
      selectionCtx.fillText('Crop to snap', x + width/2 - 40, y + height/2);
    }
  }
}

// --- PDF Generation ---
async function createPdfFromImage(dataUrl) {
  // Simple print approach works best for extensions without external deps
  const win = window.open('', '_blank');
  if (win) {
    win.document.write(`
      <html>
        <head>
          <title>Screenshot Sherlock PDF</title>
          <style>
            body { margin: 0; background: #333; display: flex; justify-content: center; min-height: 100vh; align-items: center; }
            img { max-width: 100%; box-shadow: 0 5px 15px rgba(0,0,0,0.3); background: white; }
            @media print { body { background: white; display: block; } img { box-shadow: none; } }
          </style>
        </head>
        <body>
          <img src="data:image/png;base64,${dataUrl}" onload="window.print();" />
        </body>
      </html>
    `);
    win.document.close();
  } else {
    alert('Please allow popups to print PDF');
  }
}

// State for sidebar
let sidebarState = {
  images: [], // Array of base64 strings
  isOpen: false,
  isAnalyzing: false
};

// Inject wingman sidebar if enabled
function injectWingmanSidebar(newImageData = null) {
  // Add new image if provided
  if (newImageData) {
    if (sidebarState.images.length >= 5) {
      alert("Maximum 5 screenshots allowed. Please remove some to add more.");
      return;
    }
    sidebarState.images.push(newImageData);
  }

  sidebarState.isOpen = true;
  
  // Check if sidebar already exists
  let sidebar = document.getElementById('sherlock-wingman-sidebar');
  
  if (!sidebar) {
    sidebar = document.createElement('div');
    sidebar.id = 'sherlock-wingman-sidebar';
    
    // Add styles
    if (!document.getElementById('sherlock-sidebar-styles')) {
      const style = document.createElement('style');
      style.id = 'sherlock-sidebar-styles';
      style.textContent = `
        #sherlock-wingman-sidebar {
          position: fixed;
          right: 0;
          top: 0;
          width: 400px;
          height: 100vh;
          background: #ffffff;
          box-shadow: -5px 0 30px rgba(0,0,0,0.15);
          z-index: 2147483647;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          overflow-y: auto;
          transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          color: #0f172a;
          display: flex;
          flex-direction: column;
        }
        .sherlock-header {
          padding: 20px;
          border-bottom: 1px solid #e2e8f0;
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(255,255,255,0.9);
          backdrop-filter: blur(10px);
          position: sticky;
          top: 0;
          z-index: 10;
        }
        .sherlock-brand { display: flex; align-items: center; gap: 10px; }
        .sherlock-brand-icon { font-size: 20px; }
        .sherlock-brand-text h3 { margin: 0; font-size: 16px; font-weight: 700; color: #0f172a; }
        .sherlock-brand-text p { margin: 0; font-size: 12px; color: #64748b; }
        
        #sherlock-close {
          background: transparent;
          border: none;
          cursor: pointer;
          padding: 8px;
          border-radius: 50%;
          transition: background 0.2s;
          color: #64748b;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        #sherlock-close:hover { background: #f1f5f9; color: #0f172a; }
        
        .sherlock-content { padding: 20px; flex: 1; display: flex; flex-direction: column; gap: 20px; }
        
        /* Gallery Grid */
        .sherlock-gallery {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          gap: 10px;
        }
        .sherlock-thumb {
          position: relative;
          aspect-ratio: 1;
          border-radius: 8px;
          overflow: hidden;
          border: 2px solid #e2e8f0;
          background: #f8fafc;
        }
        .sherlock-thumb img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        .sherlock-remove-img {
          position: absolute;
          top: 4px;
          right: 4px;
          background: rgba(0,0,0,0.6);
          color: white;
          border: none;
          border-radius: 50%;
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          font-size: 12px;
        }
        .sherlock-add-more {
          aspect-ratio: 1;
          border: 2px dashed #cbd5e1;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          color: #64748b;
          transition: all 0.2s;
        }
        .sherlock-add-more:hover { border-color: #6366f1; color: #6366f1; background: #eff6ff; }
        
        /* Actions */
        .sherlock-actions {
          display: flex;
          gap: 10px;
        }
        .sherlock-btn {
          flex: 1;
          padding: 12px;
          border-radius: 8px;
          border: none;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }
        .sherlock-btn-primary {
          background: #6366f1;
          color: white;
          box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
        }
        .sherlock-btn-primary:hover { background: #4f46e5; transform: translateY(-1px); }
        .sherlock-btn-primary:disabled { background: #94a3b8; cursor: not-allowed; transform: none; box-shadow: none; }
        
        .sherlock-btn-secondary {
          background: #f1f5f9;
          color: #0f172a;
        }
        .sherlock-btn-secondary:hover { background: #e2e8f0; }

        /* Results */
        .sherlock-result-card {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        }
        .sherlock-score-ring {
          width: 120px;
          height: 120px;
          border-radius: 50%;
          border: 8px solid #f1f5f9;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          margin: 0 auto 20px;
          position: relative;
        }
        .sherlock-score-val { font-size: 32px; font-weight: 800; color: #0f172a; line-height: 1; }
        .sherlock-score-label { font-size: 10px; text-transform: uppercase; color: #64748b; font-weight: 600; margin-top: 4px; }
        
        .sherlock-section-title {
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #64748b;
          font-weight: 600;
          margin-bottom: 10px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .sherlock-reply-box {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .sherlock-reply-box:hover { border-color: #6366f1; background: #eff6ff; }
        .sherlock-reply-meta { display: flex; justify-content: space-between; font-size: 11px; margin-top: 6px; color: #64748b; }
        
        /* Loading */
        .sherlock-loading {
          text-align: center;
          padding: 40px 0;
        }
        .spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #e2e8f0;
          border-top-color: #6366f1;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 15px;
        }
      `;
      document.head.appendChild(style);
    }
    document.body.appendChild(sidebar);
  }

  renderSidebarContent(sidebar);
}

function renderSidebarContent(sidebar) {
  const content = `
    <div class="sherlock-header">
      <div class="sherlock-brand">
        <div class="sherlock-brand-icon">🕵️‍♀️</div>
        <div class="sherlock-brand-text">
          <h3>Sherlock</h3>
          <p>AI Wingman</p>
        </div>
      </div>
      <button id="sherlock-close">✕</button>
    </div>
    
    <div class="sherlock-content">
      <div class="sherlock-section">
        <div class="sherlock-section-title">Captured Context</div>
        <div class="sherlock-gallery" id="sherlock-gallery">
          <!-- Images injected by JS -->
        </div>
      </div>

      <div class="sherlock-actions">
        <button id="sherlock-analyze-btn" class="sherlock-btn sherlock-btn-primary" ${sidebarState.images.length === 0 ? 'disabled' : ''}>
          ${sidebarState.isAnalyzing ? '<div class="spinner" style="width:16px;height:16px;border-width:2px;margin:0;"></div> Analyzing...' : '✨ Analyze Context'}
        </button>
        <button id="sherlock-add-btn" class="sherlock-btn sherlock-btn-secondary">
          ➕ Add More
        </button>
      </div>

      <div id="sherlock-results-area">
        <!-- Results will appear here -->
      </div>
    </div>
  `;
  
  sidebar.innerHTML = content;
  
  // Event Listeners
  document.getElementById('sherlock-close').addEventListener('click', () => {
    sidebar.remove();
    sidebarState = { images: [], isOpen: false, isAnalyzing: false };
  });
  
  document.getElementById('sherlock-add-btn').addEventListener('click', () => {
    // Trigger selection mode again
    sidebar.style.display = 'none'; // Hide sidebar temporarily
    startSelectionMode().then(area => {
        sidebar.style.display = 'block'; // Show sidebar back
        chrome.runtime.sendMessage({ action: 'cropCapture', area: area });
    }).catch(() => {
        sidebar.style.display = 'block';
    });
  });
  
  document.getElementById('sherlock-analyze-btn').addEventListener('click', async () => {
    if (sidebarState.isAnalyzing) return;
    sidebarState.isAnalyzing = true;
    renderSidebarContent(sidebar); // Re-render to show loading state
    
    try {
      const { authToken } = await chrome.storage.local.get(['authToken']);
      if (!authToken) throw new Error("Please login in the extension popup first.");
      
      // Upload the LAST image for now (MVP) or handle batch analysis
      // The backend supports one screenshot per analysis currently.
      // We'll use the last captured image.
      const lastImage = sidebarState.images[sidebarState.images.length - 1];
      
      const blob = await (await fetch(`data:image/png;base64,${lastImage}`)).blob();
      const formData = new FormData();
      formData.append('image', blob, 'snippet.png');

      // Use background script for API calls to avoid CORS/CSP issues
      chrome.runtime.sendMessage({
          action: 'performAnalysis',
          authToken: authToken,
          imageData: lastImage
      }, (response) => {
          sidebarState.isAnalyzing = false;
          if (response && response.success) {
              renderResults(response.data);
          } else {
              alert("Analysis failed: " + (response ? response.error : "Unknown error"));
              renderSidebarContent(sidebar); // Reset UI
          }
      });
      
    } catch (error) {
      sidebarState.isAnalyzing = false;
      alert(error.message);
      renderSidebarContent(sidebar);
    }
  });

  // Render Gallery
  const gallery = document.getElementById('sherlock-gallery');
  sidebarState.images.forEach((img, idx) => {
    const thumb = document.createElement('div');
    thumb.className = 'sherlock-thumb';
    thumb.innerHTML = `
      <img src="data:image/png;base64,${img}" />
      <button class="sherlock-remove-img" data-idx="${idx}">×</button>
    `;
    gallery.appendChild(thumb);
  });
  
  // Remove handler
  document.querySelectorAll('.sherlock-remove-img').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const idx = parseInt(e.target.dataset.idx);
      sidebarState.images.splice(idx, 1);
      renderSidebarContent(sidebar);
    });
  });
}

function renderResults(analysis) {
  const container = document.getElementById('sherlock-results-area');
  if (!container) return; 
  
  const scoreColor = analysis.interest_score > 75 ? '#22c55e' : analysis.interest_score > 40 ? '#eab308' : '#ef4444';
  
  // Helper to escape quotes
  const escape = (str) => (str || '').replace(/'/g, "\\'");

  container.innerHTML = `
    <div class="sherlock-result-card">
      <div class="sherlock-score-ring" style="border-color: ${scoreColor}20">
        <div class="sherlock-score-val" style="color: ${scoreColor}">${analysis.interest_score}</div>
        <div class="sherlock-score-label">Interest</div>
      </div>
      
      ${analysis.participant_name && analysis.participant_name !== "Unknown" ? `
        <div style="text-align: center; margin-bottom: 20px;">
            <button id="sherlock-osint-btn" class="sherlock-btn sherlock-btn-secondary" style="font-size: 12px; padding: 8px 12px; width: auto; display: inline-flex; margin: 0 auto;">
                🔍 Check "${analysis.participant_name}"
            </button>
            <div id="sherlock-osint-results" style="margin-top: 10px; text-align: left;"></div>
        </div>
      ` : ''}

      <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 20px; text-align: center;">
        <div style="background:#f8fafc; padding:8px; border-radius:8px;">
            <div style="font-weight:600; font-size:12px; text-transform:capitalize;">${analysis.vibe_report.overall_mood}</div>
            <div style="font-size:10px; color:#64748b;">Mood</div>
        </div>
        <div style="background:#f8fafc; padding:8px; border-radius:8px;">
            <div style="font-weight:600; font-size:12px; text-transform:capitalize;">${analysis.vibe_report.engagement_level}</div>
            <div style="font-size:10px; color:#64748b;">Engagement</div>
        </div>
        <div style="background:#f8fafc; padding:8px; border-radius:8px;">
            <div style="font-weight:600; font-size:12px; text-transform:capitalize;">${analysis.vibe_report.communication_style}</div>
            <div style="font-size:10px; color:#64748b;">Style</div>
        </div>
      </div>

      <div class="sherlock-section-title">🕊️ Wingman Wisdom</div>
      <p style="font-size: 14px; line-height: 1.6; color: #334155; margin-bottom: 20px;">
        ${analysis.wingman_notes}
      </p>
      
      <div class="sherlock-section-title">💬 Suggested Replies</div>
      <div class="sherlock-replies">
        ${analysis.suggested_replies.map(r => `
          <div class="sherlock-reply-box copy-trigger" data-text="${escape(r.text)}">
            <div style="font-size: 13px; color: #0f172a;">${r.text}</div>
            <div class="sherlock-reply-meta">
              <span style="text-transform:capitalize">${r.tone}</span>
              <span style="color: ${scoreColor}; font-weight:600">${Math.round(r.success_probability * 100)}%</span>
            </div>
            <div style="text-align:right; margin-top:4px; font-size:10px; color:#6366f1; font-weight:600; opacity:0; transition:opacity 0.2s;" class="copy-hint">Click to copy</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
  
  // Scroll to results
  container.scrollIntoView({ behavior: 'smooth' });

  // Add copy handlers using standard event listeners instead of inline onclick
  container.querySelectorAll('.copy-trigger').forEach(el => {
      el.addEventListener('click', () => {
          const text = el.dataset.text;
          navigator.clipboard.writeText(text).then(() => {
              const hint = el.querySelector('.copy-hint');
              const original = hint.textContent;
              hint.textContent = "Copied!";
              hint.style.opacity = 1;
              setTimeout(() => {
                  hint.textContent = original;
                  hint.style.opacity = 0;
              }, 2000);
          });
      });
      
      // Show hint on hover
      el.addEventListener('mouseenter', () => {
          el.querySelector('.copy-hint').style.opacity = 1;
      });
      el.addEventListener('mouseleave', () => {
          el.querySelector('.copy-hint').style.opacity = 0;
      });
  });

  // OSINT Handler
  const osintBtn = document.getElementById('sherlock-osint-btn');
  if (osintBtn) {
    osintBtn.addEventListener('click', async () => {
        const osintContainer = document.getElementById('sherlock-osint-results');
        osintBtn.disabled = true;
        osintBtn.textContent = 'Checking...';
        
        try {
            const { authToken } = await chrome.storage.local.get(['authToken']);
            // We need the conversation ID from the analysis process, but here we only have the analysis object.
            // We'll assume we can use the participant name directly via the new endpoint I created.
            // Or better, we use the 'analyze_context' endpoint if we had conversation_id.
            // Since we don't have conversation_id easily here without passing it through, 
            // let's use the direct username check endpoint with the name.
            // Note: The name might need cleaning.
            
            const name = analysis.participant_name.replace("@", "").trim();
            const response = await fetch(`http://localhost:8000/api/osint/check/${encodeURIComponent(name)}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            
            if (!response.ok) throw new Error('Check failed');
            const data = await response.json();
            
            if (data.found_accounts && data.found_accounts.length > 0) {
                osintContainer.innerHTML = `
                    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 10px; border-radius: 6px; font-size: 12px;">
                        <div style="font-weight: 600; color: #166534; margin-bottom: 5px;">Found Profiles:</div>
                        <ul style="margin: 0; padding-left: 20px; color: #15803d;">
                            ${data.found_accounts.map(acc => `
                                <li><a href="${acc.url}" target="_blank" style="color: inherit; text-decoration: underline;">${acc.site}</a></li>
                            `).join('')}
                        </ul>
                    </div>
                `;
            } else {
                osintContainer.innerHTML = `
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 6px; font-size: 12px; color: #64748b;">
                        No public profiles found for this exact username.
                    </div>
                `;
            }
            osintBtn.textContent = 'Check Complete';
        } catch (e) {
            osintBtn.textContent = 'Check Failed';
            console.error(e);
        } finally {
            osintBtn.disabled = false;
        }
    });
  }
}

// Removed old functions to clean up
async function performAnalysis(imageData) {} // Deprecated, moved to background
function renderSidebarResults(analysis) {} // Deprecated


// Check if wingman mode should be active
chrome.storage.local.get(['wingmanMode'], (result) => {
  if (result.wingmanMode) {
    injectWingmanSidebar();
  }
});

