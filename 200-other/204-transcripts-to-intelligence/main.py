#!/usr/bin/env python3
"""
PodcastAlpha - YouTube Podcast Intelligence Pipeline

Transform YouTube podcasts into actionable intelligence: 
topic summaries, business ideas, and investment theses.

Usage:
    python main.py <youtube_url> [options]
    
Examples:
    python main.py "https://youtube.com/watch?v=VIDEO_ID"
    python main.py VIDEO_ID --output-dir ./reports
    python main.py VIDEO_ID --skip-investment  # Skip investment analysis
    python main.py VIDEO_ID --enrich-ideas     # Full business enrichment
    python main.py VIDEO_ID --lenses gavin_baker karpathy  # Multi-lens analysis
    python main.py VIDEO_ID --podcaster-automation  # Automation ideas for podcaster
    python main.py --process-queue             # Process videos from queue.yaml
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from src.utils import sanitize_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Transform YouTube podcasts into actionable intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s "https://youtube.com/watch?v=NHAzpG95ptI"
    %(prog)s NHAzpG95ptI --output-dir ./reports
    %(prog)s VIDEO_ID --max-chunks 5  # Limit chunks for testing
    %(prog)s VIDEO_ID --skip-topics   # Skip topic extraction
    
Business Enrichment:
    %(prog)s VIDEO_ID --enrich-ideas                 # Full enrichment pipeline
    %(prog)s VIDEO_ID --enrich-ideas --skip-non-viable  # Skip non-viable ideas
    
Multi-Lens Investment Analysis:
    %(prog)s VIDEO_ID --lenses gavin_baker karpathy  # Specific lenses
    %(prog)s VIDEO_ID --all-lenses                   # All investor lenses
    %(prog)s VIDEO_ID --list-lenses                  # Show available lenses
    
Podcaster Automation:
    %(prog)s VIDEO_ID --podcaster-automation          # Automation ideas for podcaster
    
Queue Processing:
    %(prog)s --process-queue                          # Process queue.yaml
    %(prog)s --process-queue --limit 5                # Process max 5 videos
        """,
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        help="YouTube URL or video ID (optional if using --process-queue)",
    )
    
    # Queue processing
    parser.add_argument(
        "--process-queue",
        action="store_true",
        help="Process videos from queue.yaml instead of a single URL",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of videos to process from queue",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="./data/outputs",
        help="Output directory for reports (default: ./data/outputs)",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=None,
        help="Maximum chunks to analyze (for testing/cost control)",
    )
    
    # Analysis toggles
    parser.add_argument(
        "--skip-topics",
        action="store_true",
        help="Skip topic extraction",
    )
    parser.add_argument(
        "--skip-ideas",
        action="store_true",
        help="Skip business ideas generation",
    )
    parser.add_argument(
        "--skip-investment",
        action="store_true", 
        help="Skip investment thesis extraction",
    )
    
    # Business enrichment options
    parser.add_argument(
        "--enrich-ideas",
        action="store_true",
        help="Run full business enrichment (niche validation, lead gen, competitors)",
    )
    parser.add_argument(
        "--skip-non-viable",
        action="store_true",
        help="Skip enrichment for non-viable niches (requires --enrich-ideas)",
    )
    parser.add_argument(
        "--min-viability",
        type=int,
        default=5,
        help="Minimum viability score (1-10) to continue enrichment (default: 5)",
    )
    
    # Multi-lens investment options
    parser.add_argument(
        "--lenses",
        nargs="+",
        help="Investor lenses to use (e.g., gavin_baker karpathy)",
    )
    parser.add_argument(
        "--all-lenses",
        action="store_true",
        help="Run all available investor lenses",
    )
    parser.add_argument(
        "--list-lenses",
        action="store_true",
        help="List available investor lenses and exit",
    )
    
    # Podcaster automation
    parser.add_argument(
        "--podcaster-automation",
        action="store_true",
        help="Analyze transcript for automation opportunities for the podcaster",
    )
    parser.add_argument(
        "--max-opportunities",
        type=int,
        default=5,
        help="Maximum automation opportunities to analyze (default: 5)",
    )
    parser.add_argument(
        "--min-urgency",
        choices=["high", "medium", "low"],
        help="Minimum urgency level for opportunities to analyze",
    )
    
    # Validation options
    parser.add_argument(
        "--validate-quotes",
        action="store_true",
        help="Validate extracted quotes against transcript",
    )
    parser.add_argument(
        "--validate-tickers",
        action="store_true",
        help="Validate stock tickers with yfinance",
    )
    
    # General options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle --list-lenses
    if args.list_lenses:
        list_available_lenses()
        sys.exit(0)
    
    # Handle --process-queue
    if args.process_queue:
        run_queue_processing(args)
        sys.exit(0)
    
    # Require URL if not using queue
    if not args.url:
        parser.error("the following arguments are required: url (or use --process-queue)")
    
    # Check for API key
    if not os.environ.get("OPENROUTER_API_KEY"):
        logger.error("OPENROUTER_API_KEY environment variable required")
        logger.info("Set it with: export OPENROUTER_API_KEY='sk-or-...'")
        sys.exit(1)
    
    try:
        run_pipeline(args)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if args.verbose:
            raise
        sys.exit(1)


def list_available_lenses():
    """Print available investor lenses."""
    from src.analysis.investment.models import get_all_lenses
    
    print("\n🔍 Available Investor Lenses:")
    print("=" * 60)
    
    for lens in get_all_lenses():
        print(f"\n  {lens.key}")
        print(f"    Name: {lens.name}")
        print(f"    Focus: {', '.join(lens.focus_areas[:2])}")
    
    print("\n" + "=" * 60)
    print("Usage: python main.py VIDEO_ID --lenses gavin_baker karpathy")
    print("       python main.py VIDEO_ID --all-lenses")


def run_queue_processing(args):
    """Run the queue processor."""
    import subprocess
    
    cmd = [sys.executable, "scripts/process_queue.py"]
    
    if args.limit:
        cmd.extend(["--limit", str(args.limit)])
    
    if args.verbose:
        cmd.append("--verbose")
    
    logger.info("Running queue processor...")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def run_pipeline(args) -> None:
    """Run the full analysis pipeline."""
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
    
    # Step 1: Extract video ID
    print("\n" + "="*60)
    print("🎬 PODCASTALPHA - Podcast Intelligence Pipeline")
    print("="*60 + "\n")
    
    video_id = extract_video_id(args.url)
    logger.info(f"Video ID: {video_id}")
    
    # Step 2: Get transcript
    logger.info("📝 Fetching transcript...")
    result = transcribe(video_id)
    logger.info(
        f"   Got {result.word_count:,} words via {result.method.value} "
        f"({result.duration_seconds/60:.1f} min)"
    )
    
    # Get metadata
    video_title = result.metadata.get("video_title", f"Video {video_id}")
    channel = result.metadata.get("channel", "Unknown")
    
    # Step 3: Segment transcript
    logger.info("✂️  Segmenting transcript...")
    segmenter = TranscriptSegmenter()
    chunks = segmenter.segment_by_words(result.full_text, words_per_chunk=500)
    logger.info(f"   Created {chunks.num_chunks} chunks")
    
    # Limit chunks if requested
    chunks_to_analyze = chunks.chunks
    if args.max_chunks:
        chunks_to_analyze = chunks_to_analyze[:args.max_chunks]
        logger.info(f"   Limiting to {len(chunks_to_analyze)} chunks")
    
    # Initialize results
    topic_result = None
    ideas_result = None
    enriched_result = None
    thesis_result = None
    lens_result = None
    lens_comparison = None
    automation_result = None
    total_cost = 0.0
    
    # Step 4: Topic extraction
    if not args.skip_topics:
        logger.info("🎯 Extracting topics...")
        extractor = TopicExtractor()
        topic_result = extractor.extract(chunks_to_analyze)
        total_cost += topic_result.total_cost_usd
        logger.info(
            f"   Found {len(topic_result.all_topics)} topics "
            f"(${topic_result.total_cost_usd:.4f})"
        )
    
    # Step 5: Business ideas (with optional enrichment)
    if not args.skip_ideas:
        if args.enrich_ideas:
            # Full enrichment pipeline
            logger.info("💡 Running business enrichment pipeline...")
            pipeline = BusinessPipeline()
            enriched_result = pipeline.run(
                transcript=result.full_text[:10000],
                num_ideas=3,
                validate_niche=True,
                generate_leads=True,
                analyze_competitors=True,
                skip_non_viable=args.skip_non_viable,
                min_viability_score=args.min_viability,
            )
            total_cost += enriched_result.total_cost_usd
            
            # Create legacy-compatible result for reporting
            from src.analysis.business import BusinessIdeasResult
            ideas_result = BusinessIdeasResult(
                ideas=[e.idea for e in enriched_result.ideas],
                cost_usd=enriched_result.generation_cost_usd,
            )
            
            logger.info(
                f"   Generated {enriched_result.num_ideas} ideas, "
                f"{len(enriched_result.viable_ideas)} viable "
                f"(${enriched_result.total_cost_usd:.4f})"
            )
        else:
            # Simple idea generation
            logger.info("💡 Generating business ideas...")
            generator = BusinessIdeaGenerator()
            ideas_result = generator.generate(result.full_text[:10000])
            total_cost += ideas_result.cost_usd
            logger.info(
                f"   Generated {ideas_result.num_ideas} ideas "
                f"(${ideas_result.cost_usd:.4f})"
            )
    
    # Step 6: Investment thesis (with optional multi-lens)
    if not args.skip_investment:
        if args.all_lenses or args.lenses:
            # Multi-lens analysis
            logger.info("📈 Running multi-lens investment analysis...")
            runner = LensRunner()
            
            if args.all_lenses:
                lens_result = runner.run_all_lenses(
                    transcript=result.full_text[:10000],
                    parallel=True,
                )
            else:
                lens_result = runner.run_lenses(
                    transcript=result.full_text[:10000],
                    lens_keys=args.lenses,
                    parallel=True,
                )
            
            total_cost += lens_result.total_cost_usd
            
            # Compare lenses
            comparator = LensComparator()
            lens_comparison = comparator.compare(lens_result)
            
            logger.info(
                f"   Ran {lens_result.num_lenses} lenses, "
                f"{len(lens_comparison.consensus_stocks)} consensus picks "
                f"(${lens_result.total_cost_usd:.4f})"
            )
            
            # Create thesis result from consensus for reporting
            from src.analysis.investment import InvestmentTheme, StockRecommendation, InvestmentThesisResult
            thesis_themes = []
            for analysis in lens_result.analyses:
                if analysis.themes:
                    stocks = [
                        StockRecommendation(
                            ticker=s.ticker,
                            company=s.company,
                            exchange=s.exchange,
                            rationale=s.rationale,
                        )
                        for s in analysis.stocks[:3]
                    ]
                    thesis_themes.append(InvestmentTheme(
                        industry=analysis.lens.name,
                        sub_industry=analysis.themes[0] if analysis.themes else "",
                        thesis=analysis.key_insight,
                        supporting_quote=analysis.supporting_quotes[0] if analysis.supporting_quotes else "",
                        catalysts=analysis.opportunities[:2],
                        stocks=stocks,
                    ))
            
            thesis_result = InvestmentThesisResult(
                themes=thesis_themes[:5],
                cost_usd=lens_result.total_cost_usd,
            )
        else:
            # Standard investment thesis
            logger.info("📈 Extracting investment themes...")
            thesis_extractor = InvestmentThesisExtractor()
            thesis_result = thesis_extractor.extract(result.full_text[:10000])
            total_cost += thesis_result.cost_usd
            logger.info(
                f"   Found {thesis_result.num_themes} themes with "
                f"{len(thesis_result.all_tickers)} tickers "
                f"(${thesis_result.cost_usd:.4f})"
            )
    
    # Step 7: Podcaster automation analysis (optional)
    if args.podcaster_automation:
        logger.info("🤖 Analyzing automation opportunities for podcaster...")
        automation_pipeline = PodcasterAutomationPipeline()
        automation_result = automation_pipeline.run(
            transcript=result.full_text[:10000],
            max_opportunities=args.max_opportunities,
            min_urgency=args.min_urgency,
        )
        total_cost += automation_result.total_cost_usd
        logger.info(
            f"   Found {automation_result.num_opportunities} opportunities "
            f"(${automation_result.total_cost_usd:.4f})"
        )
    
    # Step 9: Validate quotes (optional)
    if args.validate_quotes and topic_result:
        logger.info("✅ Validating quotes...")
        validator = QuoteValidator(result.full_text)
        quotes = [a.quote.text for a in topic_result.analyses if a.quote.text]
        summary = validator.validation_summary(quotes)
        logger.info(
            f"   {summary['valid_quotes']}/{summary['total_quotes']} quotes valid "
            f"({summary['validation_rate']:.0%})"
        )
    
    # Step 10: Validate tickers (optional)
    if args.validate_tickers and thesis_result:
        logger.info("✅ Validating tickers...")
        ticker_validator = TickerValidator()
        summary = ticker_validator.validation_summary(thesis_result.all_tickers)
        logger.info(
            f"   {summary['valid_count']}/{summary['total_tickers']} tickers valid"
        )
    
    # Step 11: Generate outputs
    logger.info("📄 Generating reports...")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename from title (using sanitize_filename for safety)
    safe_title = sanitize_filename(video_title, max_length=50)
    date_str = datetime.now().strftime("%Y-%m-%d")
    base_name = f"{date_str}_{safe_title}"
    
    # Markdown report
    reporter = MarkdownReporter()
    report = reporter.generate(
        video_title=video_title,
        video_id=video_id,
        channel=channel,
        topics=topic_result,
        business_ideas=ideas_result,
        investment_thesis=thesis_result,
        transcript_preview=result.full_text[:500],
        metadata={
            "duration_minutes": result.duration_seconds / 60,
            "word_count": result.word_count,
        },
    )
    md_path = reporter.save(report, output_dir / f"{base_name}.md")
    logger.info(f"   Saved: {md_path}")
    
    # JSON export (with enriched data if available)
    exporter = JSONExporter()
    export_data = exporter.export(
        video_title=video_title,
        video_id=video_id,
        channel=channel,
        duration_seconds=result.duration_seconds,
        word_count=result.word_count,
        topics=topic_result,
        business_ideas=ideas_result,
        investment_thesis=thesis_result,
    )
    
    # Add enriched data to export
    if enriched_result:
        export_data["enriched_business_ideas"] = enriched_result.to_dict()
    
    if lens_result and lens_comparison:
        export_data["multi_lens_analysis"] = {
            "lens_results": lens_result.to_dict(),
            "comparison": lens_comparison.to_dict(),
        }
    
    if automation_result:
        export_data["podcaster_automation"] = automation_result.to_dict()
    
    json_path = exporter.save(export_data, output_dir / f"{base_name}.json")
    logger.info(f"   Saved: {json_path}")
    
    # Summary
    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETE")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"   Video: {video_title}")
    print(f"   Duration: {result.duration_seconds/60:.1f} min")
    print(f"   Words: {result.word_count:,}")
    if topic_result:
        print(f"   Topics: {len(topic_result.all_topics)}")
    if ideas_result:
        print(f"   Business Ideas: {ideas_result.num_ideas}")
        if enriched_result:
            print(f"   Viable Ideas: {len(enriched_result.viable_ideas)}")
    if thesis_result:
        print(f"   Investment Themes: {thesis_result.num_themes}")
        print(f"   Stock Picks: {', '.join(thesis_result.all_tickers[:5])}")
    if lens_comparison and lens_comparison.consensus_stocks:
        print(f"   Consensus Picks: {', '.join(s.ticker for s in lens_comparison.top_picks[:5])}")
    if automation_result:
        print(f"   Automation Opportunities: {automation_result.num_opportunities}")
        if automation_result.high_priority_opportunities:
            print(f"   High Priority: {len(automation_result.high_priority_opportunities)}")
    print(f"\n💰 Total Cost: ${total_cost:.4f}")
    print(f"\n📁 Reports saved to: {output_dir}/")
    print(f"   - {base_name}.md")
    print(f"   - {base_name}.json")


if __name__ == "__main__":
    main()
