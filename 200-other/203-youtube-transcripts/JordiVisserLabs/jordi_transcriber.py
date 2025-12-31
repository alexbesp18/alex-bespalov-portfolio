#!/usr/bin/env python3
"""
Download transcripts for the most recent videos from @JordiVisserLabs.

- Skips Shorts (videos with duration < 60 seconds, if duration is known)
- Saves transcripts into: ~/Desktop/YouTube_Transcripts/JordiVisserLabs/<YYYY-MM-DD>/
- Tracks processed video IDs so reruns only grab new videos
"""

import sys
import json
import time
import re
import traceback
from pathlib import Path
from datetime import datetime

# How many recent videos to process
MAX_VIDEOS = 40

# Channel config
CHANNEL_NAME = "JordiVisserLabs"
CHANNEL_URL = "https://www.youtube.com/@JordiVisserLabs"

# Base directory for all transcripts
BASE_DIR = Path.home() / "Desktop" / "YouTube_Transcripts"

# Try to import required packages and fail nicely if missing
try:
    import yt_dlp
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("Missing dependencies.")
    print("Install them with:")
    print("  pip install yt-dlp youtube-transcript-api")
    sys.exit(1)


class YouTubeChannelTranscriber:
    def __init__(self, channel_name: str, channel_url: str, base_dir: Path) -> None:
        self.channel_name = channel_name
        self.channel_url = channel_url

        self.output_dir = base_dir / channel_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.processed_videos_file = self.output_dir / ".processed_videos.json"
        self.tracking_file = self.output_dir / "download_tracking.txt"

        self.processed_videos = self.load_processed_videos()
        self.update_tracking_file()

        print(f"Initialized channel: {self.channel_name}")
        print(f"Output directory: {self.output_dir}")
        print(f"Already processed videos: {len(self.processed_videos)}")

    # ---------- bookkeeping ----------

    def load_processed_videos(self) -> set:
        """Load list of already processed video IDs."""
        if self.processed_videos_file.exists():
            try:
                with open(self.processed_videos_file, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                # If file is corrupted, start fresh
                traceback.print_exc()
        return set()

    def save_processed_videos(self) -> None:
        """Save list of processed video IDs."""
        with open(self.processed_videos_file, "w", encoding="utf-8") as f:
            json.dump(sorted(self.processed_videos), f, indent=2)
        self.update_tracking_file()

    def update_tracking_file(self) -> None:
        """Update visible tracking file with download statistics."""
        with open(self.tracking_file, "w", encoding="utf-8") as f:
            f.write("YouTube Channel Download Tracking\n")
            f.write(f"Channel: {self.channel_name}\n")
            f.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total Videos Downloaded: {len(self.processed_videos)}\n\n")
            f.write("Video IDs Processed:\n")
            f.write("-" * 60 + "\n")
            for vid_id in sorted(self.processed_videos):
                f.write(f"{vid_id}\n")

    # ---------- core helpers ----------

    @staticmethod
    def clean_filename(filename: str) -> str:
        """Clean filename for filesystem compatibility."""
        filename = re.sub(r'[<>:"/\\|?*]', "", filename)
        filename = re.sub(r"\s+", " ", filename)
        if len(filename) > 200:
            filename = filename[:200]
        return filename.strip() or "untitled"

    def get_channel_videos(self, max_videos: int = 10) -> list:
        """
        Get recent videos from the channel.

        Attempts to use the "Videos" tab and exclude Shorts
        by skipping entries with duration < 60 seconds when duration is known.
        """
        print(f"\nFetching up to {max_videos} videos from {self.channel_name}...")

        ydl_opts = {
            "quiet": True,
            "extract_flat": "in_playlist",
            "playlistend": max_videos,
            "ignoreerrors": True,
            "no_warnings": True,
        }

        videos = []

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.channel_url, download=False)

                # Try to find a "Videos" playlist section, otherwise fall back
                playlist_entries = None

                if info.get("_type") == "playlist" and info.get("entries"):
                    videos_section = None
                    for entry in info["entries"]:
                        if not entry:
                            continue
                        if entry.get("_type") == "playlist":
                            title = (entry.get("title") or "").lower()
                            if "videos" in title and "shorts" not in title:
                                videos_section = entry
                                break

                    if videos_section and videos_section.get("url"):
                        print("Found 'Videos' tab, extracting items...")
                        try:
                            sub_info = ydl.extract_info(
                                videos_section["url"], download=False
                            )
                            playlist_entries = sub_info.get("entries") or []
                        except Exception:
                            # Fall back to whatever entries we already have
                            traceback.print_exc()
                            playlist_entries = videos_section.get("entries") or []
                    else:
                        playlist_entries = info.get("entries") or []
                else:
                    playlist_entries = info.get("entries") or []

                # Collect video info
                for entry in playlist_entries or []:
                    if not entry:
                        continue
                    vid_id = entry.get("id")
                    if not vid_id or len(vid_id) != 11:
                        continue

                    duration = entry.get("duration") or 0
                    # Skip Shorts if duration is known and < 60 seconds
                    if duration != 0 and duration < 60:
                        continue

                    title = entry.get("title") or "Untitled"
                    videos.append(
                        {
                            "id": vid_id,
                            "title": title,
                            "url": f"https://www.youtube.com/watch?v={vid_id}",
                            "duration": duration,
                        }
                    )

                    if len(videos) >= max_videos:
                        break

            print(f"Found {len(videos)} videos (excluding Shorts where possible).")
            return videos

        except Exception as e:
            print(f"Error while fetching channel videos: {e}")
            traceback.print_exc()
            return []

    def get_transcript(self, video_id: str, video_title: str = "Unknown") -> str | None:
        """
        Fetch transcript text for a given video ID.

        Works with both:
        - Older versions that expose YouTubeTranscriptApi.get_transcript(...)
        - Newer versions that use YouTubeTranscriptApi().fetch(...)
        """
        try:
            # Newer versions: instance method + FetchedTranscript
            if not hasattr(YouTubeTranscriptApi, "get_transcript"):
                api = YouTubeTranscriptApi()
                fetched = api.fetch(video_id)  # defaults to English where available
                raw_entries = fetched.to_raw_data()
            else:
                # Older versions: classic classmethod API
                raw_entries = YouTubeTranscriptApi.get_transcript(video_id)

            formatted = []
            for entry in raw_entries:
                start = entry.get("start", 0.0)
                timestamp = f"[{int(start // 60):02d}:{int(start % 60):02d}]"
                text = entry.get("text", "")
                formatted.append(f"{timestamp} {text}")

            return "\n".join(formatted)

        except Exception as e:
            print(f"  No transcript for {video_id} ({video_title}): {e}")
            return None

    def save_transcript(self, video_id: str, title: str, transcript: str) -> Path:
        """Save transcript into a dated text file."""
        today = datetime.now()
        date_folder = self.output_dir / today.strftime("%Y-%m-%d")
        date_folder.mkdir(exist_ok=True)

        safe_title = self.clean_filename(title)
        filename = date_folder / f"{safe_title}_{video_id}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Title: {title}\n")
            f.write(f"Video ID: {video_id}\n")
            f.write(f"URL: https://www.youtube.com/watch?v={video_id}\n")
            f.write(f"Date Saved: {today.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Channel: {self.channel_name}\n")
            f.write("-" * 50 + "\n\n")
            f.write(transcript)

        return filename

    def process_new_videos(self, max_videos: int = 10) -> dict:
        """Fetch, transcribe, and save new videos only."""
        videos = self.get_channel_videos(max_videos=max_videos)

        if not videos:
            print("No videos found.")
            return {
                "status": "no_videos_found",
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "total": 0,
            }

        success_count = 0
        failed_count = 0
        skipped_count = 0

        total = len(videos)
        print(f"\nProcessing up to {total} videos")

        for idx, v in enumerate(videos, start=1):
            vid_id = v["id"]
            title = v["title"]

            if vid_id in self.processed_videos:
                skipped_count += 1
                print(f"[{idx}/{total}] Skipping already processed: {title}")
                continue

            print(f"[{idx}/{total}] Fetching transcript for: {title}")
            transcript = self.get_transcript(vid_id, title)
            if not transcript:
                failed_count += 1
                continue

            out_file = self.save_transcript(vid_id, title, transcript)
            self.processed_videos.add(vid_id)
            self.save_processed_videos()
            success_count += 1
            print(f"  Saved transcript to: {out_file}")

            # Be a good API citizen
            time.sleep(1.5)

        print("\nSummary:")
        print(f"  Processed: {success_count}")
        print(f"  Failed:   {failed_count}")
        print(f"  Skipped:  {skipped_count}")

        return {
            "status": "success",
            "processed": success_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "total": total,
        }


def main() -> None:
    transcriber = YouTubeChannelTranscriber(
        channel_name=CHANNEL_NAME,
        channel_url=CHANNEL_URL,
        base_dir=BASE_DIR,
    )
    result = transcriber.process_new_videos(max_videos=MAX_VIDEOS)
    print("\nDone.")
    print(result)


if __name__ == "__main__":
    main()
