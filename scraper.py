import re
from dataclasses import dataclass, field
from urllib.parse import urlparse, parse_qs
from typing import Optional

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled


class ScraperError(Exception):
    pass


@dataclass
class VideoData:
    video_id: str
    url: str
    title: str
    channel: str
    description: str
    transcript_text: str
    language_code: str
    is_generated: bool
    speakers: list[str] = field(default_factory=list)


def extract_video_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        vid = parsed.path.lstrip("/").split("/")[0]
        if vid:
            return vid
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[0] in ("shorts", "embed", "v"):
            return path_parts[1]
    # bare 11-char ID
    if re.match(r"^[A-Za-z0-9_-]{11}$", url.strip()):
        return url.strip()
    raise ValueError(f"Could not extract video ID from URL: {url}")


def fetch_metadata(video_id: str) -> dict:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
            if info and info.get("_type") == "playlist":
                info = info["entries"][0]
            return info
    except yt_dlp.utils.DownloadError as e:
        raise ScraperError(f"Could not fetch metadata for {video_id}: {e}") from e


def fetch_playlist_urls(playlist_url: str) -> list[str]:
    """Return a list of video URLs from a YouTube playlist."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,  # get IDs only, no per-video metadata fetch
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            if not info:
                raise ScraperError(f"Could not fetch playlist: {playlist_url}")
            entries = info.get("entries") or []
            urls = []
            for entry in entries:
                vid_id = entry.get("id")
                if vid_id:
                    urls.append(f"https://www.youtube.com/watch?v={vid_id}")
            if not urls:
                raise ScraperError(f"No videos found in playlist: {playlist_url}")
            return urls
    except yt_dlp.utils.DownloadError as e:
        raise ScraperError(f"Could not fetch playlist {playlist_url}: {e}") from e


def fetch_transcript(video_id: str) -> tuple[str, str, bool]:
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        text = " ".join(s.text.strip() for s in transcript)
        lang = getattr(transcript, "language_code", "en")
        is_generated = getattr(transcript, "is_generated", True)
        return text, lang, is_generated
    except TranscriptsDisabled as e:
        raise ScraperError(f"Transcripts disabled for {video_id}") from e
    except NoTranscriptFound as e:
        raise ScraperError(f"No transcript found for {video_id}") from e
    except Exception as e:
        raise ScraperError(f"Error fetching transcript for {video_id}: {e}") from e


def extract_speakers_heuristic(title: str, description: str) -> list[str]:
    speakers = []

    # Title colon pattern: "John Doe: Topic Title"
    title_match = re.match(r"^([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+){0,2})\s*:", title)
    if title_match:
        speakers.append(title_match.group(1).strip())

    if speakers:
        return speakers

    # Description keyword patterns
    patterns = [
        r"[Ss]peakers?\s*:?\s*(.+)",
        r"[Ff]eaturing\s+(.+)",
        r"[Pp]resented\s+by\s+(.+)",
        r"[Tt]alk\s+by\s+(.+)",
        r"[Ww]ith\s+([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)+.*)",
    ]

    desc_lines = description.split("\n") if description else []
    for line in desc_lines[:30]:  # only check first 30 lines
        line = line.strip()
        if not line:
            continue
        for pattern in patterns:
            m = re.search(pattern, line)
            if m:
                raw = m.group(1)
                # split on comma, semicolon, ampersand, or " and "
                parts = re.split(r",|;|&|\band\b", raw, flags=re.IGNORECASE)
                for part in parts:
                    name = part.strip().strip(".")
                    if name and len(name) < 60:
                        speakers.append(name)
                break
        if speakers:
            break

    return speakers


def scrape_video(url: str) -> VideoData:
    video_id = extract_video_id(url)
    info = fetch_metadata(video_id)

    title = info.get("title", "Unknown Title")
    channel = info.get("uploader") or info.get("channel") or "Unknown Channel"
    description = info.get("description") or ""

    transcript_text, language_code, is_generated = fetch_transcript(video_id)
    speakers = extract_speakers_heuristic(title, description)

    return VideoData(
        video_id=video_id,
        url=url,
        title=title,
        channel=channel,
        description=description,
        transcript_text=transcript_text,
        language_code=language_code,
        is_generated=is_generated,
        speakers=speakers,
    )
