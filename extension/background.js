// Background service worker for Screenshot Sherlock

chrome.runtime.onInstalled.addListener(() => {
  console.log('Screenshot Sherlock extension installed');
});

// API Base URL
const API_BASE_URL = 'http://localhost:8000/api';

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'captureScreenshot') {
    captureScreenshot()
      .then(sendResponse)
      .catch(error => sendResponse({ error: error.message }));
    return true; // Keep channel open for async response
  }
  
  if (request.action === 'getAuthToken') {
    chrome.storage.local.get(['authToken'], (result) => {
      sendResponse({ token: result.authToken });
    });
    return true;
  }
  
  if (request.action === 'setAuthToken') {
    chrome.storage.local.set({ authToken: request.token }, () => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === 'initiateSelection') {
    // ... existing selection logic ...
    chrome.tabs.query({ active: true, lastFocusedWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (tab) {
        // Check if we can inject script (skip restricted URLs)
        if (tab.url.startsWith('chrome://') || tab.url.startsWith('edge://') || tab.url.startsWith('about:') || tab.url.startsWith('https://chrome.google.com/webstore')) {
            console.warn("Cannot run on this page");
            return;
        }

        const sendMessage = () => {
            chrome.tabs.sendMessage(tab.id, { action: 'startSelection' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error("Could not start selection:", chrome.runtime.lastError.message);
                }
            });
        };

        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
        }).then(() => {
            setTimeout(sendMessage, 100);
        }).catch(err => {
            console.log("Injection skipped or failed, trying message:", err);
            sendMessage();
        });
      }
    });
    return true;
  }
  
  if (request.action === 'cropCapture') {
    handleCropCapture(request.area, sender.tab.id);
    return true;
  }

  if (request.action === 'performAnalysis') {
    performAnalysis(request.authToken, request.imageData)
      .then(data => sendResponse({ success: true, data: data }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

async function performAnalysis(authToken, imageData) {
  // 1. Upload
  const blob = await (await fetch(`data:image/png;base64,${imageData}`)).blob();
  const formData = new FormData();
  formData.append('image', blob, 'snippet.png');

  const uploadRes = await fetch(`${API_BASE_URL}/screenshot/upload`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${authToken}` },
    body: formData
  });
  
  if (!uploadRes.ok) {
    const err = await uploadRes.text();
    throw new Error('Upload failed: ' + err);
  }
  const { conversation_id } = await uploadRes.json();

  // 2. Analyze
  const analyzeRes = await fetch(`${API_BASE_URL}/analyze/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ conversation_id })
  });

  if (!analyzeRes.ok) {
    const err = await analyzeRes.text();
    throw new Error('Analysis failed: ' + err);
  }
  return await analyzeRes.json();
}

async function handleCropCapture(area, tabId) {
  try {
    // 1. Capture the full visible tab
    const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: 'png' });
    
    // 2. Crop it using OffscreenCanvas
    const croppedDataUrl = await cropImage(dataUrl, area);
    
    // 3. Send back to content script to display sidebar
    // Instead of opening new tab, we inject the result into the current page
    chrome.tabs.sendMessage(tabId, { 
        action: 'analyzeCropped', 
        imageData: croppedDataUrl.split(',')[1] 
    });
    
  } catch (error) {
    console.error('Crop failed:', error);
  }
}

async function cropImage(dataUrl, area) {
  // Create offscreen canvas
  const response = await fetch(dataUrl);
  const blob = await response.blob();
  const bitmap = await createImageBitmap(blob);
  
  const canvas = new OffscreenCanvas(area.width, area.height);
  const ctx = canvas.getContext('2d');
  
  // Draw the slice
  // drawImage(image, sx, sy, sWidth, sHeight, dx, dy, dWidth, dHeight)
  // Note: area.x/y are in CSS pixels. We need to multiply by devicePixelRatio if the screenshot is high DPI.
  // captureVisibleTab returns high DPI image on Retina screens.
  // The area object from content script already has devicePixelRatio attached or we can use it.
  const scale = area.devicePixelRatio || 1;
  
  ctx.drawImage(
    bitmap,
    area.x * scale, area.y * scale, area.width * scale, area.height * scale,
    0, 0, area.width, area.height
  );
  
  const blobResult = await canvas.convertToBlob({ type: 'image/png' });
  const reader = new FileReader();
  return new Promise(resolve => {
    reader.onloadend = () => resolve(reader.result);
    reader.readAsDataURL(blobResult);
  });
}

async function captureScreenshot() {
  try {
    // Use lastFocusedWindow to ensure we get the user's active browser window
    // 'currentWindow: true' can sometimes be ambiguous when the popup is open
    const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
    const tab = tabs[0];
    
    if (!tab) {
      // Fallback: try getting any active tab
      const [anyTab] = await chrome.tabs.query({ active: true });
      if (!anyTab) throw new Error('No active tab found to capture');
      
      // Use the fallback tab
      const dataUrl = await chrome.tabs.captureVisibleTab(anyTab.windowId, {
        format: 'png',
        quality: 100
      });
      
      return {
        success: true,
        imageData: dataUrl.split(',')[1],
        format: 'png'
      };
    }
    
    // Capture the visible tab of the specific window
    const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, {
      format: 'png',
      quality: 100
    });
    
    // Convert data URL to base64
    const base64 = dataUrl.split(',')[1];
    
    return {
      success: true,
      imageData: base64,
      format: 'png'
    };
  } catch (error) {
    console.error('Screenshot capture error:', error);
    // Check for common permission error
    if (error.message.includes('MAX_CAPTURE_VISIBLE_TAB_CALLS_PER_SECOND')) {
      throw new Error('Too many screenshots taken. Please wait a moment.');
    }
    throw new Error(`Screenshot capture failed: ${error.message}`);
  }
}

