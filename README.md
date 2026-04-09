# YouTube Transcript Scraper

Scrapes YouTube video transcripts and metadata, saving them as local `.txt` files organized by channel name. No API key required.

## Setup

```bash
pip install -r requirements.txt
```

## Authentication (required)

YouTube blocks unauthenticated requests. You need to export a `cookies.txt` file from your browser once before running.

**One-time setup:**
1. Install the **"Get cookies.txt LOCALLY"** extension in your browser (available in the Chrome Web Store; works in Arc, Chrome, Brave, etc.)
2. Go to `youtube.com` and make sure you are logged in
3. Click the extension → **Export as cookies.txt**
4. Save the file as `cookies.txt` in the project folder

Re-export every few weeks when cookies expire. `cookies.txt` is in `.gitignore` and will not be committed.

## Configuration

Edit the top of `main.py` to set defaults so you don't need to type arguments each time:

```python
URLS_FILE    = "urls.txt"    # Default URLs file
FOLDER       = None          # Output folder name (None = use channel name)
PLAYLIST_URL = None          # Set to a playlist URL to skip the file entirely
DELAY        = 10            # Seconds to wait between videos
```

`COOKIES_FILE` in `scraper.py` sets the path to your cookies file (default: `"cookies.txt"`).

## Usage

```bash
# Scrape from a URLs file — folders named after each video's channel
python3 main.py scrape urls.txt

# Override the folder name
python3 main.py scrape urls.txt --folder "MyFolder"

# Force overwrite of existing files
python3 main.py scrape urls.txt --force

# Use defaults from main.py config (no arguments needed)
python3 main.py scrape
```

## Playlist

Pass a playlist URL directly. The scraper saves all video URLs to `<folder>_urls.txt` first, then processes each one. If the run is interrupted, retry from the saved file without re-fetching the playlist.

```bash
# Fetch playlist, save URLs to dasny2026_1_urls.txt, then scrape
python3 main.py scrape --playlist "https://www.youtube.com/playlist?list=PLreAVA3oHbxvXKgav6zvvFwRFv7ysigm0" --folder "dasny2026_1"

# Retry from saved URLs file (skips already-scraped videos)
python3 main.py scrape dasny2026_1_urls.txt --folder "dasny2026_1"
```

You can also set `PLAYLIST_URL` and `FOLDER` in `main.py` and run without arguments.

## urls.txt format

One YouTube URL per line. Lines starting with `#` are ignored.

```
# DeFi conference talks
https://www.youtube.com/watch?v=abc123
https://youtu.be/xyz789
```

Supported URL formats: `youtube.com/watch?v=`, `youtu.be/`, `/shorts/`, `/embed/`, bare 11-char video IDs.

## Output structure

```
transcripts/
  <Channel Name>/
    Video Title.txt
    Another Video.txt
  <Another Channel>/
    Some Talk.txt
```

Each `.txt` file contains a metadata header followed by the full transcript:

```
Title: ...
Channel: ...
URL: ...
Language: en
Auto-generated: yes/no
Speakers: ...

Description:
...

--- TRANSCRIPT ---

<full transcript text>
```

## Using transcripts with Claude

Drag the `transcripts/` folder (or a channel subfolder) into a Claude.ai project to use the files for Q&A, summaries, and analysis.

## Files

| File | Purpose |
|------|---------|
| `main.py` | CLI entry point — `scrape` command and configuration constants |
| `scraper.py` | YouTube scraping logic (yt-dlp + youtube-transcript-api) |
| `cookies.txt` | Browser cookies for YouTube auth (not committed to git) |
| `urls.txt` | Input file with YouTube URLs |
| `transcripts/` | Output folder for saved transcripts |
