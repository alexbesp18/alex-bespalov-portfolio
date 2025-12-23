"""
Prompts Module

Provides infrastructure for loading and managing external prompt files
with YAML frontmatter metadata.
"""

from .loader import PromptLoader, PromptTemplate

__all__ = ["PromptLoader", "PromptTemplate"]

