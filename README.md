# YouTube Transcript Scraper

Scrapes YouTube video transcripts and metadata, saving them as local `.txt` files organized by channel name. No API key required.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Scrape URLs from file — folders named after each video's channel
python3 main.py scrape urls.txt

# Override the folder name (all videos go into transcripts/MyFolder/)
python3 main.py scrape urls.txt --folder "MyFolder"

# Force overwrite of existing files
python3 main.py scrape urls.txt --force
```

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
| `main.py` | CLI entry point — `scrape` command |
| `scraper.py` | YouTube scraping logic (yt-dlp + youtube-transcript-api) |
| `urls.txt` | Input file with YouTube URLs |
| `transcripts/` | Output folder for saved transcripts |

