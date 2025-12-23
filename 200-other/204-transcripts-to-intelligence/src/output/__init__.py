"""
Output Module

Provides report generation in multiple formats:
- Markdown reports
- JSON exports
"""

from .markdown import MarkdownReporter, generate_report
from .json_export import JSONExporter, export_json

__all__ = [
    "MarkdownReporter",
    "generate_report",
    "JSONExporter",
    "export_json",
]

__version__ = "0.1.0"
