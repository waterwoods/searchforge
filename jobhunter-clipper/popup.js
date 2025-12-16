// Get current tab info and extract text
async function initializePopup() {
  const statusEl = document.getElementById('status');
  const urlEl = document.getElementById('url');
  const previewEl = document.getElementById('jd-preview');
  const savedCountEl = document.getElementById('saved-count');
  const clipBtn = document.getElementById('clip-btn');

  // Clear status
  statusEl.textContent = '';
  statusEl.className = '';

  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab || !tab.id) {
      throw new Error('No active tab found');
    }

    // Display URL
    urlEl.textContent = tab.url || 'N/A';

    // Extract text from page
    let pageText = { selectionText: '', fullTextSample: '' };

    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: extractPageText
      });

      if (results && results[0] && results[0].result) {
        pageText = results[0].result;
      }
    } catch (err) {
      console.error('Error executing script:', err);
      // Some pages (like chrome://) don't allow script injection
      statusEl.textContent = 'Cannot extract text from this page (may be restricted)';
      statusEl.className = 'error';
      clipBtn.disabled = true;
      return;
    }

    // Determine which text to use for preview and saving
    const textToUse = pageText.selectionText.trim() || pageText.fullTextSample.trim();

    if (!textToUse) {
      previewEl.value = 'No text found on this page.';
      clipBtn.disabled = true;
      return;
    }

    // Show preview (first 1000 chars)
    const preview = textToUse.slice(0, 1000);
    previewEl.value = preview + (textToUse.length > 1000 ? '\n\n... (truncated for preview)' : '');

    // Load saved clips count
    await updateSavedCount();

    // Set up save button handler
    clipBtn.disabled = false;
    clipBtn.onclick = async () => {
      await saveClip(tab.url, tab.title, textToUse);
    };

  } catch (error) {
    console.error('Error initializing popup:', error);
    statusEl.textContent = `Failed to initialize: ${error.message}`;
    statusEl.className = 'error';
    clipBtn.disabled = true;
  }
}

// Function injected into page to extract text
function extractPageText() {
  // Get selected text
  const selection = window.getSelection()?.toString() || '';

  // Get body text
  let bodyText = '';
  try {
    bodyText = document.body.innerText || document.body.textContent || '';
  } catch (e) {
    console.error('Error getting body text:', e);
  }

  // Clean and truncate
  const cleanSelection = selection.trim();
  const cleanBodyText = bodyText
    .replace(/\s+/g, ' ')  // Replace multiple whitespace with single space
    .trim()
    .slice(0, 4000);  // Truncate to 4000 chars

  return {
    selectionText: cleanSelection,
    fullTextSample: cleanBodyText
  };
}

// Update saved clips count display
async function updateSavedCount() {
  try {
    const result = await chrome.storage.local.get('jobhunter_clips');
    const clips = result.jobhunter_clips || [];
    document.getElementById('saved-count').textContent = `Saved clips: ${clips.length}`;
  } catch (error) {
    console.error('Error updating saved count:', error);
  }
}

// Save clip to storage
async function saveClip(url, title, text) {
  const statusEl = document.getElementById('status');
  const clipBtn = document.getElementById('clip-btn');

  clipBtn.disabled = true;
  statusEl.textContent = 'Saving...';
  statusEl.className = '';

  try {
    // Get existing clips
    const result = await chrome.storage.local.get('jobhunter_clips');
    const clips = result.jobhunter_clips || [];

    // Create new clip object
    const newClip = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      url: url || '',
      title: title || 'Untitled',
      clippedAt: new Date().toISOString(),
      source: 'manual-clip-v1',
      text: text
    };

    // Add to array
    clips.push(newClip);

    // Save to storage
    await chrome.storage.local.set({ jobhunter_clips: clips });

    // Update UI
    await updateSavedCount();

    statusEl.textContent = 'Saved!';
    statusEl.className = 'success';

    // Clear success message after 2 seconds
    setTimeout(() => {
      statusEl.textContent = '';
      statusEl.className = '';
    }, 2000);

    clipBtn.disabled = false;

  } catch (error) {
    console.error('Error saving clip:', error);
    statusEl.textContent = `Failed to clip: ${error.message}`;
    statusEl.className = 'error';
    clipBtn.disabled = false;
  }
}

// Initialize when popup opens
document.addEventListener('DOMContentLoaded', initializePopup);
