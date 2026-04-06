import re
import os
import time

import click

from scraper import scrape_video, fetch_playlist_urls, ScraperError

# --- Configuration ---
URLS_FILE = "urls.txt"   # Default URLs file, e.g. "dasny2026_3.txt"
FOLDER = None            # Output folder override (None = use channel name)
PLAYLIST_URL = None      # Set to a playlist URL to skip the file entirely, e.g.:
                         # "https://www.youtube.com/playlist?list=PLxxx"
DELAY = 3                # Seconds to wait between videos (increase if getting blocked)


def sanitize_name(name: str, max_len: int = 80) -> str:
    """Remove filesystem-unsafe characters and truncate."""
    name = re.sub(r'[/\\:*?"<>|]', "", name)
    name = name.strip()
    return name[:max_len]


def write_transcript_file(path: str, video_data) -> None:
    upload_date = ""
    speakers = ", ".join(video_data.speakers) if video_data.speakers else "Unknown"
    auto_generated = "yes" if video_data.is_generated else "no"

    content = (
        f"Title: {video_data.title}\n"
        f"Channel: {video_data.channel}\n"
        f"URL: {video_data.url}\n"
        f"Language: {video_data.language_code}\n"
        f"Auto-generated: {auto_generated}\n"
        f"Speakers: {speakers}\n"
        f"\nDescription:\n{video_data.description}\n"
        f"\n--- TRANSCRIPT ---\n\n"
        f"{video_data.transcript_text}\n"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


@click.group()
def cli():
    """YouTube transcript scraper — saves transcripts as local .txt files."""


@cli.command()
@click.argument("urls_file", default=URLS_FILE, required=False)
@click.option("--playlist", default=PLAYLIST_URL, help="YouTube playlist URL (overrides urls_file).")
@click.option("--folder", default=FOLDER, help="Override folder name (default: channel name).")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
def scrape(urls_file: str, playlist: str, folder: str, force: bool):
    """Scrape YouTube transcripts and save as .txt files."""
    if playlist:
        click.echo(f"Fetching playlist: {playlist}")
        try:
            lines = fetch_playlist_urls(playlist)
        except ScraperError as e:
            raise click.ClickException(str(e))
        click.echo(f"Found {len(lines)} videos.\n")
    else:
        with open(urls_file, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]

    if not lines:
        click.echo("No URLs found.")
        return

    saved = skipped = failed = 0

    for url in lines:
        click.echo(f"\nProcessing: {url}")
        try:
            video_data = scrape_video(url)

            folder_name = sanitize_name(folder) if folder else sanitize_name(video_data.channel)
            if not folder_name:
                folder_name = "Unknown_Channel"

            out_dir = os.path.join("transcripts", folder_name)
            os.makedirs(out_dir, exist_ok=True)

            filename = sanitize_name(video_data.title) + ".txt"
            filepath = os.path.join(out_dir, filename)

            if os.path.exists(filepath) and not force:
                click.echo(f"  [skip] Already exists: {filepath}")
                skipped += 1
                continue

            write_transcript_file(filepath, video_data)

            click.echo(f"  Title:    {video_data.title}")
            click.echo(f"  Channel:  {video_data.channel}")
            click.echo(f"  Speakers: {', '.join(video_data.speakers) or 'Unknown'}")
            click.echo(f"  Saved:    {filepath}")
            saved += 1

        except ScraperError as e:
            click.echo(f"  [error] {e}", err=True)
            failed += 1

        if url != lines[-1]:
            click.echo(f"  Waiting {DELAY}s...")
            time.sleep(DELAY)

    click.echo(f"\nDone. {saved} saved, {skipped} skipped, {failed} failed.")


if __name__ == "__main__":
    cli()
