// Chrome storage utility functions

function getStorageItem(key) {
  return new Promise((resolve) => {
    chrome.storage.local.get([key], (result) => {
      resolve(result[key]);
    });
  });
}

function setStorageItem(key, value) {
  return new Promise((resolve) => {
    chrome.storage.local.set({ [key]: value }, () => {
      resolve();
    });
  });
}

function removeStorageItem(key) {
  return new Promise((resolve) => {
    chrome.storage.local.remove([key], () => {
      resolve();
    });
  });
}

function clearStorage() {
  return new Promise((resolve) => {
    chrome.storage.local.clear(() => {
      resolve();
    });
  });
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getStorageItem,
    setStorageItem,
    removeStorageItem,
    clearStorage
  };
}

