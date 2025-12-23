#!/usr/bin/env python3
"""
Queue Processor

Processes videos from queue.yaml file. Used by GitHub Actions
for automated batch processing.

Usage:
    python scripts/process_queue.py                    # Process all pending
    python scripts/process_queue.py --limit 5          # Process max 5 videos
    python scripts/process_queue.py --dry-run          # Show what would be processed
    python scripts/process_queue.py --url VIDEO_URL    # Process single URL (bypass queue)
"""

import argparse
import logging
import os
import sys
import tempfile
import unicodedata
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

QUEUE_FILE = PROJECT_ROOT / "queue.yaml"
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

# YouTube URL validation patterns
YOUTUBE_PATTERNS = [
    r'^(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
    r'^(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
    r'^(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    r'^(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    r'^([a-zA-Z0-9_-]{11})$',
]
COMPILED_PATTERNS = [re.compile(p) for p in YOUTUBE_PATTERNS]


def validate_youtube_url(url: str) -> bool:
    """Validate that a string is a valid YouTube URL or video ID.
    
    Args:
        url: The URL or video ID to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    for pattern in COMPILED_PATTERNS:
        if pattern.match(url):
            return True
    return False


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """Sanitize a string to be safe for use as a filename.
    
    Removes or replaces dangerous characters, prevents path traversal.
    
    Args:
        name: The string to sanitize.
        max_length: Maximum length of the result.
        
    Returns:
        Safe filename string.
    """
    if not name:
        return "untitled"
    
    # Normalize unicode
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    
    # Remove path separators and dangerous patterns
    name = re.sub(r'[/\\]', '_', name)
    name = re.sub(r'\.\.', '', name)
    
    # Replace non-alphanumeric (except space, dash, underscore)
    name = re.sub(r'[^\w\s-]', '', name)
    
    # Replace whitespace with underscore
    name = re.sub(r'\s+', '_', name)
    
    # Replace multiple underscores with single
    name = re.sub(r'_+', '_', name)
    
    # Lowercase and strip
    name = name.lower().strip('_')
    
    # Truncate
    if len(name) > max_length:
        name = name[:max_length].rstrip('_')
    
    return name or "untitled"


def load_queue() -> Dict[str, Any]:
    """Load the queue file."""
    if not QUEUE_FILE.exists():
        logger.warning(f"Queue file not found: {QUEUE_FILE}")
        return {"videos": [], "processed": []}
    
    with open(QUEUE_FILE, "r") as f:
        data = yaml.safe_load(f) or {}
    
    return {
        "videos": data.get("videos", []),
        "processed": data.get("processed", []),
    }


def save_queue(queue: Dict[str, Any]) -> None:
    """Save the queue file atomically.
    
    Uses write-to-temp-then-rename pattern to prevent corruption
    if the process crashes mid-write.
    """
    # Write to temporary file first
    temp_path = QUEUE_FILE.with_suffix('.yaml.tmp')
    
    try:
        with open(temp_path, "w") as f:
            yaml.dump(queue, f, default_flow_style=False, sort_keys=False)
        
        # Atomic rename (on POSIX systems)
        temp_path.rename(QUEUE_FILE)
    except Exception as e:
        # Clean up temp file on failure
        if temp_path.exists():
            temp_path.unlink()
        raise e


def get_pending_videos(queue: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get pending videos sorted by priority."""
    videos = queue.get("videos", [])
    
    if not videos:
        return []
    
    # Sort by priority
    priority_order = {"high": 0, "normal": 1, "low": 2}
    
    sorted_videos = sorted(
        videos,
        key=lambda v: priority_order.get(v.get("priority", "normal"), 1)
    )
    
    return sorted_videos


def process_video(video: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """Process a single video.
    
    Returns:
        Result dict with status, outputs, error, etc.
    """
    url = video.get("url", "")
    options = video.get("options", {})
    
    if not url:
        return {"status": "error", "error": "No URL provided"}
    
    # Validate URL
    if not validate_youtube_url(url):
        logger.error(f"Invalid YouTube URL: {url}")
        return {"status": "error", "error": f"Invalid YouTube URL: {url}"}
    
    logger.info(f"Processing: {url}")
    
    if dry_run:
        logger.info(f"  [DRY RUN] Would process with options: {options}")
        return {"status": "dry_run", "url": url, "options": options}
    
    # Import here to avoid circular imports
    from src.transcript import transcribe, extract_video_id
    from src.analysis import (
        TranscriptSegmenter,
        TopicExtractor,
        QuoteValidator,
        TickerValidator,
    )
    from src.analysis.business import BusinessPipeline, BusinessIdeaGenerator
    from src.analysis.investment import (
        InvestmentThesisExtractor,
        LensRunner,
        LensComparator,
    )
    from src.analysis.podcaster_automation import PodcasterAutomationPipeline
    from src.output import MarkdownReporter, JSONExporter
    
    start_time = datetime.now()
    result = {
        "status": "processing",
        "url": url,
        "started_at": start_time.isoformat(),
    }
    
    try:
        # Extract video ID
        video_id = extract_video_id(url)
        result["video_id"] = video_id
        
        # Get transcript
        logger.info(f"  Fetching transcript...")
        transcript_result = transcribe(video_id)
        
        video_title = transcript_result.metadata.get("video_title", f"Video {video_id}")
        channel = transcript_result.metadata.get("channel", "Unknown")
        
        result["video_title"] = video_title
        result["channel"] = channel
        result["word_count"] = transcript_result.word_count
        result["duration_seconds"] = transcript_result.duration_seconds
        
        # Segment transcript
        logger.info(f"  Segmenting transcript...")
        segmenter = TranscriptSegmenter()
        chunks = segmenter.segment_by_words(transcript_result.full_text, words_per_chunk=500)
        
        total_cost = 0.0
        outputs = {}
        
        # Topic extraction
        if not options.get("skip_topics", False):
            logger.info(f"  Extracting topics...")
            extractor = TopicExtractor()
            topic_result = extractor.extract(chunks.chunks)
            total_cost += topic_result.total_cost_usd
            outputs["topics"] = topic_result.to_dict()
        
        # Business ideas
        if not options.get("skip_ideas", False):
            if options.get("enrich_ideas", False):
                logger.info(f"  Running business enrichment pipeline...")
                pipeline = BusinessPipeline()
                enriched_result = pipeline.run(
                    transcript=transcript_result.full_text[:10000],
                    num_ideas=3,
                    validate_niche=True,
                    generate_leads=True,
                    analyze_competitors=True,
                )
                total_cost += enriched_result.total_cost_usd
                outputs["enriched_business_ideas"] = enriched_result.to_dict()
            else:
                logger.info(f"  Generating business ideas...")
                generator = BusinessIdeaGenerator()
                ideas_result = generator.generate(transcript_result.full_text[:10000])
                total_cost += ideas_result.cost_usd
                outputs["business_ideas"] = ideas_result.to_dict()
        
        # Investment thesis
        if not options.get("skip_investment", False):
            lenses = options.get("lenses", [])
            all_lenses = options.get("all_lenses", False)
            
            if all_lenses or lenses:
                logger.info(f"  Running multi-lens investment analysis...")
                runner = LensRunner()
                
                if all_lenses:
                    lens_result = runner.run_all_lenses(
                        transcript=transcript_result.full_text[:10000],
                        parallel=True,
                    )
                else:
                    lens_result = runner.run_lenses(
                        transcript=transcript_result.full_text[:10000],
                        lens_keys=lenses,
                        parallel=True,
                    )
                
                total_cost += lens_result.total_cost_usd
                
                comparator = LensComparator()
                comparison = comparator.compare(lens_result)
                
                outputs["multi_lens_analysis"] = {
                    "lens_results": lens_result.to_dict(),
                    "comparison": comparison.to_dict(),
                }
            else:
                logger.info(f"  Extracting investment themes...")
                thesis_extractor = InvestmentThesisExtractor()
                thesis_result = thesis_extractor.extract(transcript_result.full_text[:10000])
                total_cost += thesis_result.cost_usd
                outputs["investment_thesis"] = thesis_result.to_dict()
        
        # Podcaster automation
        if options.get("podcaster_automation", False):
            logger.info(f"  Running podcaster automation analysis...")
            automation_pipeline = PodcasterAutomationPipeline()
            automation_result = automation_pipeline.run(
                transcript=transcript_result.full_text[:10000],
            )
            total_cost += automation_result.total_cost_usd
            outputs["podcaster_automation"] = automation_result.to_dict()
        
        # Save outputs
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Use sanitize_filename for safe, consistent naming
        safe_title = sanitize_filename(video_title, max_length=50)
        date_str = datetime.now().strftime("%Y-%m-%d")
        base_name = f"{date_str}_{safe_title}"
        
        # Save JSON
        exporter = JSONExporter()
        export_data = {
            "video_id": video_id,
            "video_title": video_title,
            "channel": channel,
            "processed_at": datetime.now().isoformat(),
            "options": options,
            "total_cost_usd": total_cost,
            **outputs,
        }
        json_path = exporter.save(export_data, OUTPUT_DIR / f"{base_name}.json")
        
        # Update result
        end_time = datetime.now()
        result.update({
            "status": "success",
            "completed_at": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "total_cost_usd": total_cost,
            "output_file": str(json_path),
        })
        
        logger.info(f"  ✅ Complete: ${total_cost:.4f}")
        
        # Send email notification
        try:
            from src.notifications.resend_email import send_video_notification
            
            # Extract data for email
            business_ideas_list = outputs.get("enriched_business_ideas", {}).get("ideas", [])
            if not business_ideas_list:
                business_ideas_list = outputs.get("business_ideas", {}).get("ideas", [])
            
            consensus = outputs.get("multi_lens_analysis", {}).get("comparison", {}).get("consensus_stocks", [])
            consensus_tickers = [s.get("ticker", s) if isinstance(s, dict) else s for s in consensus[:5]]
            
            topics_data = outputs.get("topics", {})
            topics_count = len(topics_data.get("all_topics", [])) if topics_data else 0
            
            send_video_notification(
                video_title=video_title,
                video_url=url,
                channel=channel,
                duration_minutes=transcript_result.duration_seconds / 60,
                topics_count=topics_count,
                business_ideas=business_ideas_list,
                consensus_stocks=consensus_tickers,
                total_cost=total_cost,
                output_file=str(json_path),
            )
        except Exception as email_err:
            logger.warning(f"  Email notification failed: {email_err}")
        
    except Exception as e:
        result.update({
            "status": "error",
            "error": str(e),
            "completed_at": datetime.now().isoformat(),
        })
        logger.error(f"  ❌ Failed: {e}")
    
    return result


def process_queue(
    limit: Optional[int] = None,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """Process pending videos from queue.
    
    Args:
        limit: Maximum number of videos to process.
        dry_run: If True, don't actually process, just log.
        
    Returns:
        List of processing results.
    """
    queue = load_queue()
    pending = get_pending_videos(queue)
    
    if not pending:
        logger.info("No pending videos in queue")
        return []
    
    if limit:
        pending = pending[:limit]
    
    logger.info(f"Processing {len(pending)} videos...")
    
    results = []
    
    for video in pending:
        result = process_video(video, dry_run=dry_run)
        results.append(result)
        
        # Move to processed if not dry run
        if not dry_run and result.get("status") in ("success", "error"):
            # Remove from pending
            queue["videos"] = [
                v for v in queue.get("videos", [])
                if v.get("url") != video.get("url")
            ]
            
            # Add to processed
            processed_entry = {
                **video,
                "processed_at": datetime.now().isoformat(),
                "status": result.get("status"),
            }
            if result.get("error"):
                processed_entry["error"] = result["error"]
            
            queue.setdefault("processed", []).append(processed_entry)
            
            # Save queue
            save_queue(queue)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Process videos from queue.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of videos to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without running",
    )
    parser.add_argument(
        "--url",
        help="Process a single URL (bypasses queue)",
    )
    parser.add_argument(
        "--enrich-ideas",
        action="store_true",
        help="Run full business enrichment (for --url mode)",
    )
    parser.add_argument(
        "--all-lenses",
        action="store_true",
        help="Run all investor lenses (for --url mode)",
    )
    parser.add_argument(
        "--podcaster-automation",
        action="store_true",
        help="Run podcaster automation analysis (for --url mode)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check for API key
    if not os.environ.get("OPENROUTER_API_KEY"):
        logger.error("OPENROUTER_API_KEY environment variable required")
        sys.exit(1)
    
    # Process single URL if provided
    if args.url:
        video = {
            "url": args.url,
            "priority": "high",
            "options": {
                "enrich_ideas": args.enrich_ideas,
                "all_lenses": args.all_lenses,
                "podcaster_automation": args.podcaster_automation,
            },
        }
        result = process_video(video, dry_run=args.dry_run)
        
        if result.get("status") == "success":
            print(f"\n✅ Processed: {result.get('video_title')}")
            print(f"   Output: {result.get('output_file')}")
            print(f"   Cost: ${result.get('total_cost_usd', 0):.4f}")
        elif result.get("status") == "error":
            print(f"\n❌ Failed: {result.get('error')}")
            sys.exit(1)
        
        return
    
    # Process queue
    results = process_queue(limit=args.limit, dry_run=args.dry_run)
    
    # Summary
    if results:
        success = sum(1 for r in results if r.get("status") == "success")
        errors = sum(1 for r in results if r.get("status") == "error")
        total_cost = sum(r.get("total_cost_usd", 0) for r in results)
        
        print(f"\n📊 Queue Processing Complete")
        print(f"   Processed: {len(results)}")
        print(f"   Success: {success}")
        print(f"   Errors: {errors}")
        print(f"   Total Cost: ${total_cost:.4f}")
        
        if errors > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()

