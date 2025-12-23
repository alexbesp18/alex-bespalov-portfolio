#!/usr/bin/env python3
"""
Channel Monitor - Detect new videos from tracked YouTube channels.

Reads channels.yaml, fetches latest videos via yt-dlp, and adds
new (unprocessed) videos to queue.yaml for processing.

Usage:
    python scripts/channel_monitor.py              # Check all enabled channels
    python scripts/channel_monitor.py --dry-run    # Show what would be added
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
CHANNELS_FILE = PROJECT_ROOT / "channels.yaml"
QUEUE_FILE = PROJECT_ROOT / "queue.yaml"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_channels() -> List[Dict[str, Any]]:
    """Load channel configurations."""
    if not CHANNELS_FILE.exists():
        logger.error(f"Channels file not found: {CHANNELS_FILE}")
        return []
    
    with open(CHANNELS_FILE) as f:
        data = yaml.safe_load(f) or {}
    
    return [c for c in data.get("channels", []) if c.get("enabled", True)]


def load_queue() -> Dict[str, Any]:
    """Load the queue file."""
    if not QUEUE_FILE.exists():
        return {"videos": [], "processed": []}
    
    with open(QUEUE_FILE) as f:
        data = yaml.safe_load(f) or {}
    
    # Use `or []` to handle null/None values in YAML
    return {
        "videos": data.get("videos") or [],
        "processed": data.get("processed") or [],
    }


def save_queue(queue: Dict[str, Any]) -> None:
    """Save queue atomically."""
    temp_path = QUEUE_FILE.with_suffix('.yaml.tmp')
    try:
        with open(temp_path, "w") as f:
            yaml.dump(queue, f, default_flow_style=False, sort_keys=False)
        temp_path.rename(QUEUE_FILE)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise e


def get_channel_videos(channel_url: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch latest videos from a YouTube channel using yt-dlp."""
    try:
        # Use yt-dlp to get video list (flat playlist = metadata only, no download)
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--playlist-end", str(limit),
            "--print", "%(id)s|%(title)s|%(upload_date)s",
            "--no-warnings",
            channel_url,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            logger.error(f"yt-dlp error: {result.stderr}")
            return []
        
        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line or "|" not in line:
                continue
            
            parts = line.split("|", 2)
            if len(parts) >= 2:
                video_id = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else "Unknown"
                upload_date = parts[2].strip() if len(parts) > 2 else None
                
                videos.append({
                    "id": video_id,
                    "title": title,
                    "upload_date": upload_date,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                })
        
        return videos
    
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout fetching videos from {channel_url}")
        return []
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        return []


def get_all_known_video_ids(queue: Dict[str, Any]) -> set:
    """Get set of all video IDs that are queued or processed."""
    known = set()
    
    # Videos in queue
    videos = queue.get("videos") or []
    for v in videos:
        if not v:
            continue
        url = v.get("url", "") if isinstance(v, dict) else str(v)
        # Extract video ID from URL or use as-is
        if "watch?v=" in url:
            vid = url.split("watch?v=")[1].split("&")[0]
        else:
            vid = url
        if vid:
            known.add(vid)
    
    # Already processed videos
    processed = queue.get("processed") or []
    for v in processed:
        if not v:
            continue
        url = v.get("url", "") if isinstance(v, dict) else str(v)
        if "watch?v=" in url:
            vid = url.split("watch?v=")[1].split("&")[0]
        else:
            vid = url
        if vid:
            known.add(vid)
    
    return known


def check_channel(
    channel: Dict[str, Any],
    queue: Dict[str, Any],
    known_ids: set,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """Check a channel for new videos and add to queue."""
    name = channel.get("name", "Unknown")
    url = channel.get("url", "")
    limit = channel.get("check_last_n", 5)
    options = channel.get("options", {})
    
    if not url:
        logger.warning(f"No URL for channel: {name}")
        return []
    
    logger.info(f"Checking channel: {name}")
    
    videos = get_channel_videos(url, limit=limit)
    logger.info(f"  Found {len(videos)} recent videos")
    
    new_videos = []
    for video in videos:
        if video["id"] not in known_ids:
            new_videos.append(video)
            known_ids.add(video["id"])  # Prevent duplicates across channels
    
    if not new_videos:
        logger.info(f"  No new videos")
        return []
    
    logger.info(f"  {len(new_videos)} new video(s) to add")
    
    for video in new_videos:
        queue_entry = {
            "url": video["url"],
            "priority": "normal",
            "options": options,
            "added_at": datetime.now().isoformat(),
            "source_channel": name,
            "title": video["title"],
        }
        
        if dry_run:
            logger.info(f"    [DRY RUN] Would add: {video['title'][:50]}...")
        else:
            queue["videos"].append(queue_entry)
            logger.info(f"    Added: {video['title'][:50]}...")
    
    return new_videos


def main():
    parser = argparse.ArgumentParser(description="Check channels for new videos")
    parser.add_argument("--dry-run", action="store_true", help="Don't modify queue")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    channels = load_channels()
    if not channels:
        logger.info("No enabled channels found")
        return
    
    logger.info(f"Checking {len(channels)} channel(s)...")
    
    queue = load_queue()
    known_ids = get_all_known_video_ids(queue)
    
    total_new = 0
    for channel in channels:
        new_videos = check_channel(channel, queue, known_ids, dry_run=args.dry_run)
        total_new += len(new_videos)
    
    if total_new > 0 and not args.dry_run:
        save_queue(queue)
        logger.info(f"Queue updated with {total_new} new video(s)")
    
    # Output for GitHub Actions
    print(f"\n📺 Channel Monitor Complete")
    print(f"   Channels checked: {len(channels)}")
    print(f"   New videos found: {total_new}")
    
    # Set output for GitHub Actions
    if total_new > 0:
        print(f"::set-output name=new_videos::{total_new}")
        sys.exit(0)
    else:
        print("::set-output name=new_videos::0")
        sys.exit(0)


if __name__ == "__main__":
    main()

