// Screenshot capture utility

async function captureVisibleTab() {
  return new Promise((resolve, reject) => {
    chrome.tabs.captureVisibleTab(null, { format: 'png' }, (dataUrl) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        // Convert data URL to base64
        const base64 = dataUrl.split(',')[1];
        resolve({
          dataUrl,
          base64,
          format: 'png'
        });
      }
    });
  });
}

async function captureCurrentTab() {
  return new Promise((resolve, reject) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length === 0) {
        reject(new Error('No active tab found'));
        return;
      }
      
      chrome.tabs.captureVisibleTab(null, { format: 'png' }, (dataUrl) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          const base64 = dataUrl.split(',')[1];
          resolve({
            dataUrl,
            base64,
            format: 'png',
            tabId: tabs[0].id,
            url: tabs[0].url
          });
        }
      });
    });
  });
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    captureVisibleTab,
    captureCurrentTab
  };
}

