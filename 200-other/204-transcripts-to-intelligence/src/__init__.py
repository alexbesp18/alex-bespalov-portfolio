"""
src package

PodcastAlpha - YouTube Podcast Intelligence Pipeline

Modules:
- transcript: Multi-strategy YouTube transcript extraction
- analysis: LLM-powered analysis (topics, ideas, investment, podcaster automation)
- prompts: External prompt template loading
- output: Report generation (Markdown, JSON)
- notifications: Multi-channel notifications (Slack, Discord, Email)
"""

from . import transcript
from . import analysis
from . import prompts
from . import output
from . import notifications

__all__ = ["transcript", "analysis", "prompts", "output", "notifications"]
