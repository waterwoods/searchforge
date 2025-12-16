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

    // Show preview (first 1200 chars)
    const PREVIEW_LENGTH = 1200;
    const preview = textToUse.slice(0, PREVIEW_LENGTH);
    previewEl.value = preview + (textToUse.length > PREVIEW_LENGTH ? '\n\n... (truncated for preview)' : '');

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
  const MAX_TEXT_LENGTH = 12000; // New limit for saved text

  // Get selected text
  const selection = window.getSelection()?.toString() || '';

  // Smart text extraction with LinkedIn-specific logic
  let bodyText = '';
  try {
    const host = window.location.host || '';
    const path = window.location.pathname || '';

    // Priority: LinkedIn job detail pages
    if (host.includes('linkedin.com') && path.includes('/jobs/')) {
      const candidates = [
        'main div.jobs-details__main-content',
        'section.jobs-description__container',
        'div.jobs-description-content__text',
        'div.jobs-description__content',
        'div.show-more-less-html__markup',
      ];

      for (const sel of candidates) {
        const el = document.querySelector(sel);
        if (el && el.innerText && el.innerText.trim().length > 500) {
          bodyText = el.innerText.trim();
          break;
        }
      }
    }

    // Fallback to full body text if LinkedIn-specific extraction didn't work
    if (!bodyText) {
      bodyText = document.body.innerText || document.body.textContent || '';
    }
  } catch (e) {
    console.error('Error getting body text:', e);
    // Final fallback
    bodyText = document.body.innerText || document.body.textContent || '';
  }

  // Clean and truncate
  const cleanSelection = selection.trim();
  const cleanBodyText = bodyText
    .replace(/\s+/g, ' ')  // Replace multiple whitespace with single space
    .trim()
    .slice(0, MAX_TEXT_LENGTH);  // Truncate to MAX_TEXT_LENGTH chars

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

// Export clips as JSON
async function exportClipsAsJson() {
  const exportBtn = document.getElementById('export-json-btn');
  const exportStatusEl = document.getElementById('export-status');

  exportBtn.disabled = true;
  exportStatusEl.textContent = 'Exporting...';
  exportStatusEl.className = '';

  try {
    // 1. Read storage
    const { jobhunter_clips } = await chrome.storage.local.get('jobhunter_clips');
    const clips = Array.isArray(jobhunter_clips) ? jobhunter_clips : [];

    // 2. Construct export object
    const exportPayload = {
      version: 1,
      exported_at: new Date().toISOString(),
      clips: clips
    };

    // 3. Serialize to JSON string with 2-space indentation
    const jsonStr = JSON.stringify(exportPayload, null, 2);

    // 4. Generate filename with timestamp
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `jobhunter_clips_${ts}.json`;

    // 5. Create Blob and trigger download
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // Update UI status
    if (clips.length === 0) {
      exportStatusEl.textContent = 'No clips in storage, exported empty list.';
      exportStatusEl.className = 'success';
    } else {
      exportStatusEl.textContent = `Exported ${clips.length} clips to ${filename}`;
      exportStatusEl.className = 'success';
    }

    exportBtn.disabled = false;

  } catch (err) {
    console.error('Export failed:', err);
    exportStatusEl.textContent = `Export failed: ${err.message}`;
    exportStatusEl.className = 'error';
    exportBtn.disabled = false;
  }
}

// Initialize when popup opens
document.addEventListener('DOMContentLoaded', () => {
  initializePopup();

  // Bind export button
  const exportBtn = document.getElementById('export-json-btn');
  if (exportBtn) {
    exportBtn.onclick = exportClipsAsJson;
  }
});
