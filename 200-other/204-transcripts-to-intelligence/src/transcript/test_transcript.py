#!/usr/bin/env python3
"""
Test script for the transcript module.

Tests all transcription strategies against a real YouTube video,
displays the results, and saves transcripts to data/transcripts/.

Usage:
    python -m src.transcript.test_transcript <youtube_url_or_id>
    
Example:
    python -m src.transcript.test_transcript "https://www.youtube.com/watch?v=NHAzpG95ptI"
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Output directory for saved transcripts (project_root/data/transcripts)
TRANSCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "transcripts"


def slugify(text: str, max_length: int = 60) -> str:
    """Convert text to a safe filename slug."""
    # Remove special characters, keep alphanumerics and spaces
    text = re.sub(r"[^\w\s-]", "", text.lower())
    # Replace spaces with underscores
    text = re.sub(r"[\s_]+", "_", text)
    # Trim to max length
    return text[:max_length].strip("_")


def get_video_metadata(video_id: str) -> dict:
    """Fetch video metadata using yt-dlp."""
    try:
        import yt_dlp
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        return {
            "title": info.get("title", "unknown"),
            "channel": info.get("channel", "unknown"),
            "upload_date": info.get("upload_date", ""),  # Format: YYYYMMDD
            "duration": info.get("duration", 0),
        }
    except Exception as e:
        logger.warning(f"Could not fetch metadata: {e}")
        return {
            "title": video_id,
            "channel": "unknown",
            "upload_date": "",
            "duration": 0,
        }


def save_transcript(result, metadata: dict, output_dir: Path) -> tuple[Path, Path]:
    """
    Save transcript to text and JSON files.
    
    Filename format: YYYY-MM-DD_episode-title.txt/.json
    
    Returns:
        Tuple of (txt_path, json_path)
    """
    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse upload date or use today
    upload_date = metadata.get("upload_date", "")
    if upload_date and len(upload_date) == 8:
        date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Create filename slug from title
    title_slug = slugify(metadata.get("title", "transcript"))
    base_filename = f"{date_str}_{title_slug}"
    
    # Save as plain text
    txt_path = output_dir / f"{base_filename}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# {metadata.get('title', 'Unknown')}\n")
        f.write(f"# Channel: {metadata.get('channel', 'Unknown')}\n")
        f.write(f"# Date: {date_str}\n")
        f.write(f"# Duration: {result.duration_seconds / 60:.1f} minutes\n")
        f.write(f"# Words: {result.word_count:,}\n")
        f.write(f"# Method: {result.method.value}\n")
        f.write("\n" + "="*60 + "\n\n")
        f.write(result.full_text)
    
    # Save as JSON with metadata and segments
    json_path = output_dir / f"{base_filename}.json"
    json_data = {
        "video_id": result.video_id,
        "title": metadata.get("title"),
        "channel": metadata.get("channel"),
        "upload_date": date_str,
        **result.to_dict(),
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    return txt_path, json_path


def test_strategy(strategy, video_id: str, metadata: dict, save: bool = True) -> Optional[dict]:
    """Test a single strategy and return results."""
    
    strategy_name = strategy.method.value
    print(f"\n{'='*60}")
    print(f"Testing: {strategy_name.upper()}")
    print(f"{'='*60}")
    
    try:
        # Check availability
        print(f"Checking availability...", end=" ")
        available = strategy.is_available(video_id)
        
        if not available:
            print("❌ Not available")
            return {"strategy": strategy_name, "success": False, "error": "Not available"}
        
        print("✅ Available")
        
        # Transcribe
        print(f"Transcribing...", end=" ")
        result = strategy.transcribe(video_id)
        print("✅ Done")
        
        # Display results
        print(f"\n📊 Results:")
        print(f"   Method:      {result.method.value}")
        print(f"   Language:    {result.language}")
        print(f"   Confidence:  {result.confidence_score:.2f}")
        print(f"   Word Count:  {result.word_count:,}")
        print(f"   Duration:    {result.duration_seconds:.1f}s ({result.duration_seconds/60:.1f} min)")
        print(f"   Cost:        ${result.cost_usd:.4f}")
        print(f"   Auto-gen:    {result.is_auto_generated}")
        print(f"   Segments:    {len(result.segments)}")
        
        print(f"\n📝 Preview (first 500 chars):")
        print(f"   {result.preview(500)}")
        
        # Save transcript
        saved_paths = None
        if save:
            txt_path, json_path = save_transcript(result, metadata, TRANSCRIPTS_DIR)
            print(f"\n💾 Saved to:")
            print(f"   {txt_path}")
            print(f"   {json_path}")
            saved_paths = {"txt": str(txt_path), "json": str(json_path)}
        
        return {
            "strategy": strategy_name,
            "success": True,
            "word_count": result.word_count,
            "confidence": result.confidence_score,
            "duration": result.duration_seconds,
            "cost": result.cost_usd,
            "saved": saved_paths,
        }
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return {"strategy": strategy_name, "success": False, "error": str(e)}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test transcript fetching strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s "https://www.youtube.com/watch?v=NHAzpG95ptI"
    %(prog)s NHAzpG95ptI
    %(prog)s NHAzpG95ptI --strategy ytdlp
    %(prog)s NHAzpG95ptI --no-save
        """,
    )
    parser.add_argument(
        "url",
        help="YouTube URL or video ID",
    )
    parser.add_argument(
        "--strategy",
        choices=["youtube_api", "ytdlp", "whisper_api", "all"],
        default="all",
        help="Which strategy to test (default: all)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save transcript to file",
    )
    parser.add_argument(
        "--openai-key",
        help="OpenAI API key for Whisper (or set OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Import here to avoid import errors if dependencies missing
    try:
        from .orchestrator import extract_video_id
        from .strategies import YouTubeAPIStrategy, YtdlpStrategy, WhisperAPIStrategy
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root:")
        print("  cd /path/to/transcripts_to_intelligence")
        print("  python -m src.transcript.test_transcript <url>")
        sys.exit(1)
    
    # Extract video ID
    try:
        video_id = extract_video_id(args.url)
        print(f"\n🎬 Video ID: {video_id}")
        print(f"   URL: https://www.youtube.com/watch?v={video_id}")
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Fetch video metadata
    print(f"\n📋 Fetching video metadata...")
    metadata = get_video_metadata(video_id)
    print(f"   Title:   {metadata['title']}")
    print(f"   Channel: {metadata['channel']}")
    if metadata['upload_date']:
        d = metadata['upload_date']
        print(f"   Date:    {d[:4]}-{d[4:6]}-{d[6:8]}")
    
    # Build strategy list
    strategies = []
    
    if args.strategy in ("youtube_api", "all"):
        strategies.append(YouTubeAPIStrategy())
    
    if args.strategy in ("ytdlp", "all"):
        strategies.append(YtdlpStrategy())
    
    if args.strategy in ("whisper_api", "all"):
        whisper = WhisperAPIStrategy(api_key=args.openai_key)
        if whisper.api_key:
            strategies.append(whisper)
        elif args.strategy == "whisper_api":
            print("❌ Whisper API requires OPENAI_API_KEY environment variable or --openai-key")
            sys.exit(1)
        else:
            print("ℹ️  Skipping Whisper API (no API key configured)")
    
    if not strategies:
        print("❌ No strategies to test")
        sys.exit(1)
    
    # Run tests (only save on first success to avoid duplicates)
    results = []
    saved_already = False
    
    for strategy in strategies:
        should_save = not args.no_save and not saved_already
        result = test_strategy(strategy, video_id, metadata, save=should_save)
        results.append(result)
        
        if result["success"] and should_save:
            saved_already = True
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for r in results:
        status = "✅" if r["success"] else "❌"
        if r["success"]:
            print(f"{status} {r['strategy']:15} | {r['word_count']:,} words | conf: {r['confidence']:.2f} | ${r['cost']:.4f}")
        else:
            print(f"{status} {r['strategy']:15} | {r.get('error', 'Unknown error')}")
    
    # Exit with success if at least one strategy worked
    success_count = sum(1 for r in results if r["success"])
    print(f"\n{success_count}/{len(results)} strategies succeeded")
    
    sys.exit(0 if success_count > 0 else 1)


if __name__ == "__main__":
    main()
