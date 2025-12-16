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

- Export clips to JSON file for batch processing by JobHunter Agent
- Filter and search saved clips
- Delete individual clips
- Sync across devices (optional)
