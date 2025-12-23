"""
Markdown Report Generator

Generates formatted Markdown reports from transcript analysis results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.analysis import (
    TopicExtractionResult,
    BusinessIdeasResult,
    InvestmentThesisResult,
    SegmentationResult,
)

__all__ = ["MarkdownReporter", "generate_report"]


class MarkdownReporter:
    """Generates comprehensive Markdown reports from analysis results.
    
    Example:
        >>> reporter = MarkdownReporter()
        >>> report = reporter.generate(
        ...     video_title="2026 Predictions",
        ...     topics=topic_result,
        ...     business_ideas=ideas_result,
        ...     investment_thesis=thesis_result,
        ... )
        >>> reporter.save(report, "output/report.md")
    """
    
    def __init__(self, include_timestamps: bool = True):
        """Initialize reporter.
        
        Args:
            include_timestamps: Whether to include segment timestamps.
        """
        self.include_timestamps = include_timestamps
    
    def generate(
        self,
        video_title: str,
        video_url: Optional[str] = None,
        video_id: Optional[str] = None,
        channel: Optional[str] = None,
        topics: Optional[TopicExtractionResult] = None,
        business_ideas: Optional[BusinessIdeasResult] = None,
        investment_thesis: Optional[InvestmentThesisResult] = None,
        transcript_preview: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a complete Markdown report.
        
        Args:
            video_title: Title of the video.
            video_url: YouTube URL.
            video_id: YouTube video ID.
            channel: Channel name.
            topics: Topic extraction results.
            business_ideas: Business ideas results.
            investment_thesis: Investment thesis results.
            transcript_preview: First N chars of transcript.
            metadata: Additional metadata to include.
            
        Returns:
            Complete Markdown report as string.
        """
        sections = []
        
        # Header
        sections.append(self._generate_header(
            video_title, video_url, video_id, channel, metadata
        ))
        
        # Table of Contents
        toc_items = []
        if topics:
            toc_items.append("- [Key Topics](#key-topics)")
        if business_ideas and business_ideas.ideas:
            toc_items.append("- [Business Ideas](#business-ideas)")
        if investment_thesis and investment_thesis.themes:
            toc_items.append("- [Investment Themes](#investment-themes)")
        
        if toc_items:
            sections.append("## Contents\n" + "\n".join(toc_items))
        
        # Topics Section
        if topics:
            sections.append(self._generate_topics_section(topics))
        
        # Business Ideas Section
        if business_ideas and business_ideas.ideas:
            sections.append(self._generate_business_ideas_section(business_ideas))
        
        # Investment Thesis Section
        if investment_thesis and investment_thesis.themes:
            sections.append(self._generate_investment_section(investment_thesis))
        
        # Transcript Preview
        if transcript_preview:
            sections.append(self._generate_transcript_section(transcript_preview))
        
        # Footer
        sections.append(self._generate_footer(topics, business_ideas, investment_thesis))
        
        return "\n\n---\n\n".join(sections)
    
    def _generate_header(
        self,
        title: str,
        url: Optional[str],
        video_id: Optional[str],
        channel: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> str:
        """Generate report header."""
        lines = [f"# 📊 {title}"]
        
        meta_items = []
        if channel:
            meta_items.append(f"**Channel:** {channel}")
        if url:
            meta_items.append(f"**URL:** [{url}]({url})")
        elif video_id:
            yt_url = f"https://www.youtube.com/watch?v={video_id}"
            meta_items.append(f"**URL:** [{yt_url}]({yt_url})")
        
        meta_items.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        if metadata:
            if "duration_minutes" in metadata:
                meta_items.append(f"**Duration:** {metadata['duration_minutes']:.1f} min")
            if "word_count" in metadata:
                meta_items.append(f"**Words:** {metadata['word_count']:,}")
        
        lines.append("\n".join(meta_items))
        
        return "\n\n".join(lines)
    
    def _generate_topics_section(self, topics: TopicExtractionResult) -> str:
        """Generate topics section."""
        lines = ["## 🎯 Key Topics"]
        
        # Topic summary
        if topics.all_topics:
            topic_tags = " • ".join(f"`{t}`" for t in topics.all_topics[:10])
            lines.append(f"\n{topic_tags}")
        
        # Per-chunk analysis
        lines.append("\n### Segment Analysis\n")
        
        for analysis in topics.analyses:
            time_str = ""
            if self.include_timestamps:
                start = self._format_time(analysis.start_seconds)
                end = self._format_time(analysis.end_seconds)
                time_str = f" ({start} - {end})"
            
            lines.append(f"#### Segment {analysis.chunk_index + 1}{time_str}")
            lines.append(f"\n{analysis.summary}\n")
            
            if analysis.quote.text:
                lines.append(f"> \"{analysis.quote.text}\"")
                if analysis.quote.speaker != "Unknown":
                    lines.append(f"> — {analysis.quote.speaker}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_business_ideas_section(self, ideas: BusinessIdeasResult) -> str:
        """Generate business ideas section."""
        lines = ["## 💡 Business Ideas"]
        lines.append("\n*24-hour actionable ideas inspired by this content:*\n")
        
        for i, idea in enumerate(ideas.ideas, 1):
            lines.append(f"### {i}. {idea.title}")
            lines.append(f"\n{idea.description}\n")
            
            lines.append(f"**Target Market:** {idea.target_market}")
            lines.append(f"**Estimated Cost:** {idea.estimated_cost}\n")
            
            # Quote
            if idea.supporting_quote:
                lines.append(f"> \"{idea.supporting_quote}\"\n")
            
            # Execution plan
            lines.append("**24-Hour Plan:**")
            lines.append(f"- ⏰ Hours 1-4: {idea.execution_plan.hours_1_4}")
            lines.append(f"- 🔧 Hours 5-12: {idea.execution_plan.hours_5_12}")
            lines.append(f"- 🚀 Hours 13-24: {idea.execution_plan.hours_13_24}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_investment_section(self, thesis: InvestmentThesisResult) -> str:
        """Generate investment thesis section."""
        lines = ["## 📈 Investment Themes"]
        
        # Ticker summary
        if thesis.valid_tickers:
            tickers = " ".join(f"`${t}`" for t in thesis.valid_tickers)
            lines.append(f"\n**Tickers:** {tickers}\n")
        
        for i, theme in enumerate(thesis.themes, 1):
            lines.append(f"### {i}. {theme.industry}: {theme.sub_industry}")
            lines.append(f"\n{theme.thesis}\n")
            
            # Quote
            if theme.supporting_quote:
                lines.append(f"> \"{theme.supporting_quote}\"\n")
            
            # Catalysts
            if theme.catalysts:
                lines.append("**Catalysts:**")
                for catalyst in theme.catalysts:
                    lines.append(f"- {catalyst}")
                lines.append("")
            
            # Stocks
            if theme.stocks:
                lines.append("**Stock Picks:**")
                lines.append("| Ticker | Company | Exchange | Rationale |")
                lines.append("|--------|---------|----------|-----------|")
                for stock in theme.stocks:
                    lines.append(
                        f"| ${stock.ticker} | {stock.company} | "
                        f"{stock.exchange} | {stock.rationale} |"
                    )
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_transcript_section(self, preview: str) -> str:
        """Generate transcript preview section."""
        lines = ["## 📝 Transcript Preview"]
        lines.append(f"\n```\n{preview[:1000]}...\n```")
        return "\n".join(lines)
    
    def _generate_footer(
        self,
        topics: Optional[TopicExtractionResult],
        ideas: Optional[BusinessIdeasResult],
        thesis: Optional[InvestmentThesisResult],
    ) -> str:
        """Generate report footer with costs."""
        lines = ["## 📊 Analysis Metadata"]
        
        total_cost = 0.0
        if topics:
            total_cost += topics.total_cost_usd
        if ideas:
            total_cost += ideas.cost_usd
        if thesis:
            total_cost += thesis.cost_usd
        
        lines.append(f"\n- **Total LLM Cost:** ${total_cost:.4f}")
        lines.append(f"- **Generated by:** PodcastAlpha")
        lines.append(f"- **Timestamp:** {datetime.now().isoformat()}")
        
        return "\n".join(lines)
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def save(self, report: str, path: str | Path) -> Path:
        """Save report to file.
        
        Args:
            report: Markdown content.
            path: Output file path.
            
        Returns:
            Path to saved file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        return path


def generate_report(**kwargs) -> str:
    """Convenience function to generate a report.
    
    See MarkdownReporter.generate() for arguments.
    """
    reporter = MarkdownReporter()
    return reporter.generate(**kwargs)
