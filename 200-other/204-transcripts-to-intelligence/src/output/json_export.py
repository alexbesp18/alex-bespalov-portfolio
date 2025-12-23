"""
JSON Export

Exports analysis results to structured JSON format.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from src.analysis import (
    TopicExtractionResult,
    BusinessIdeasResult,
    InvestmentThesisResult,
    SegmentationResult,
)

__all__ = ["JSONExporter", "export_json"]


class JSONExporter:
    """Exports analysis results to JSON format.
    
    Example:
        >>> exporter = JSONExporter()
        >>> data = exporter.export(
        ...     video_title="2026 Predictions",
        ...     topics=topic_result,
        ... )
        >>> exporter.save(data, "output/report.json")
    """
    
    def __init__(self, pretty: bool = True):
        """Initialize exporter.
        
        Args:
            pretty: Whether to format JSON with indentation.
        """
        self.pretty = pretty
    
    def export(
        self,
        video_title: str,
        video_url: Optional[str] = None,
        video_id: Optional[str] = None,
        channel: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        word_count: Optional[int] = None,
        topics: Optional[TopicExtractionResult] = None,
        business_ideas: Optional[BusinessIdeasResult] = None,
        investment_thesis: Optional[InvestmentThesisResult] = None,
        transcript_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Export analysis results to dictionary.
        
        Args:
            video_title: Title of the video.
            video_url: YouTube URL.
            video_id: YouTube video ID.
            channel: Channel name.
            duration_seconds: Video duration.
            word_count: Transcript word count.
            topics: Topic extraction results.
            business_ideas: Business ideas results.
            investment_thesis: Investment thesis results.
            transcript_text: Full transcript text.
            metadata: Additional metadata.
            
        Returns:
            Dictionary containing all analysis data.
        """
        data: Dict[str, Any] = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "video": {
                "title": video_title,
                "video_id": video_id,
                "url": video_url or (
                    f"https://www.youtube.com/watch?v={video_id}" 
                    if video_id else None
                ),
                "channel": channel,
                "duration_seconds": duration_seconds,
                "word_count": word_count,
            },
        }
        
        # Calculate costs
        total_cost = 0.0
        
        # Topics
        if topics:
            data["topics"] = {
                "all_topics": topics.all_topics,
                "num_chunks": topics.num_chunks,
                "cost_usd": topics.total_cost_usd,
                "analyses": [a.to_dict() for a in topics.analyses],
            }
            total_cost += topics.total_cost_usd
        
        # Business Ideas
        if business_ideas:
            data["business_ideas"] = {
                "num_ideas": business_ideas.num_ideas,
                "cost_usd": business_ideas.cost_usd,
                "ideas": [i.to_dict() for i in business_ideas.ideas],
            }
            total_cost += business_ideas.cost_usd
        
        # Investment Thesis
        if investment_thesis:
            data["investment_thesis"] = {
                "num_themes": investment_thesis.num_themes,
                "all_tickers": investment_thesis.all_tickers,
                "valid_tickers": investment_thesis.valid_tickers,
                "cost_usd": investment_thesis.cost_usd,
                "themes": [t.to_dict() for t in investment_thesis.themes],
            }
            total_cost += investment_thesis.cost_usd
        
        # Transcript
        if transcript_text:
            data["transcript"] = {
                "full_text": transcript_text,
                "word_count": len(transcript_text.split()),
            }
        
        # Metadata
        data["metadata"] = {
            "total_cost_usd": total_cost,
            **(metadata or {}),
        }
        
        return data
    
    def to_json(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to JSON string.
        
        Args:
            data: Dictionary to convert.
            
        Returns:
            JSON string.
        """
        if self.pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
    
    def save(self, data: Dict[str, Any], path: str | Path) -> Path:
        """Save data to JSON file.
        
        Args:
            data: Dictionary to save.
            path: Output file path.
            
        Returns:
            Path to saved file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            if self.pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)
        
        return path


def export_json(**kwargs) -> Dict[str, Any]:
    """Convenience function to export to JSON.
    
    See JSONExporter.export() for arguments.
    """
    exporter = JSONExporter()
    return exporter.export(**kwargs)
