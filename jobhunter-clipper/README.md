# JobHunter Clipper

A Chrome extension (Manifest V3) that allows you to clip job postings from any website and save them to local storage for later processing by the JobHunter Agent.

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked**
4. Select the `jobhunter-clipper` directory (the one containing this README.md file)
5. The extension icon should now appear in your browser toolbar

## Usage

1. Navigate to any job posting page (LinkedIn, company website, etc.)
2. (Optional) Select the job description text you want to clip by highlighting it with your mouse
3. Click the **JobHunter Clipper** icon in your browser toolbar
4. Review the preview of the text that will be saved
5. Click **Save clip** to store it locally

## Export JSON

- Click the extension icon on any job page.
- Click "Save clip" a few times to store some jobs.
- Click "Export JSON" to download a file like `jobhunter_clips_2025-12-16T231001.json`.
- The JSON structure:

```json
{
  "version": 1,
  "exported_at": "2025-12-16T23:10:01.123Z",
  "clips": [
    {
      "id": "1765923047859-ux6o6iyir",
      "url": "https://www.linkedin.com/jobs/view/xxxx",
      "title": "Lead Data Engineer | The Walt Disney Company | LinkedIn",
      "clippedAt": "2025-12-16T22:10:47.859Z",
      "source": "manual-clip-v1",
      "text": "......完整的 JD 文本（已截断到上限，例如 12000 字符）"
    }
  ]
}
```

- If there are no clips in storage, the export will still generate a valid JSON file with an empty `clips: []` array.

## Features

- **Smart LinkedIn extraction**: On LinkedIn job detail pages, the extension automatically targets the job description content area, avoiding navigation and ads for cleaner text extraction.
- **Extended text limit**: Supports up to 12,000 characters per clip (increased from 4,000).
- **Preview mode**: Shows first 1,200 characters in the preview, while saving the full text (up to 12,000 chars).

## Data Storage

- Clips are stored in Chrome's local storage under the key `jobhunter_clips`
- Each clip contains:
  - `id`: Unique identifier
  - `url`: Source page URL
  - `title`: Page title
  - `clippedAt`: ISO timestamp
  - `source`: "manual-clip-v1"
  - `text`: The extracted job description text

## Viewing Stored Data

To view your saved clips:
1. Open Chrome DevTools (F12)
2. Go to **Application** tab
3. Navigate to **Storage** → **Extension Storage**
4. Find `chrome.storage.local` and expand `jobhunter_clips`

## Future Enhancements

- Filter and search saved clips
- Delete individual clips
- Sync across devices (optional)
