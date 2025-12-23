"""
Prompt Loader

Loads prompt templates from external markdown files with YAML frontmatter.
Enables easy editing of prompts without code changes.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

__all__ = ["PromptLoader", "PromptTemplate"]

logger = logging.getLogger(__name__)

# Default prompts directory relative to project root
DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


@dataclass
class PromptTemplate:
    """A loaded prompt template with metadata.
    
    Attributes:
        name: Human-readable name of the prompt.
        version: Version string for tracking changes.
        system_prompt: The system/context prompt for the LLM.
        user_prompt: The user prompt template with {placeholders}.
        parameters: List of expected parameter names.
        path: Source file path.
        metadata: Additional frontmatter fields.
    """
    name: str
    version: str
    system_prompt: str
    user_prompt: str
    parameters: List[str] = field(default_factory=list)
    path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def format(self, **kwargs) -> tuple[str, str]:
        """Format the prompt templates with provided values.
        
        Args:
            **kwargs: Values for template placeholders.
            
        Returns:
            Tuple of (formatted_system_prompt, formatted_user_prompt).
            
        Raises:
            KeyError: If a required parameter is missing.
        """
        # Check for missing parameters
        missing = set(self.parameters) - set(kwargs.keys())
        if missing:
            raise KeyError(f"Missing required parameters: {missing}")
        
        # Format both prompts
        system = self.system_prompt.format(**kwargs) if self.system_prompt else ""
        user = self.user_prompt.format(**kwargs)
        
        return system, user
    
    def format_user(self, **kwargs) -> str:
        """Format just the user prompt template.
        
        Args:
            **kwargs: Values for template placeholders.
            
        Returns:
            Formatted user prompt string.
        """
        return self.user_prompt.format(**kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "version": self.version,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "parameters": self.parameters,
            "path": str(self.path) if self.path else None,
            "metadata": self.metadata,
        }


class PromptLoader:
    """Loads prompt templates from external markdown files.
    
    Prompt files use YAML frontmatter for metadata and markdown sections
    for system and user prompts.
    
    Example file format:
        ---
        name: Business Idea Generator
        version: 1.0
        parameters:
          - transcript
          - num_ideas
        ---
        # System Prompt
        You are a startup strategist...
        
        # User Prompt
        Analyze this transcript and generate {num_ideas} ideas:
        {transcript}
    
    Example usage:
        >>> loader = PromptLoader()
        >>> template = loader.load("business/idea_generation.md")
        >>> system, user = template.format(transcript="...", num_ideas=3)
    """
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt files.
                         Defaults to project's prompts/ directory.
        """
        self.prompts_dir = Path(prompts_dir) if prompts_dir else DEFAULT_PROMPTS_DIR
        self._cache: Dict[str, PromptTemplate] = {}
    
    def load(self, path: str, use_cache: bool = True) -> PromptTemplate:
        """Load a prompt template from a file.
        
        Args:
            path: Path relative to prompts directory (e.g., "business/idea_generation.md").
            use_cache: Whether to use cached templates.
            
        Returns:
            PromptTemplate with parsed content.
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist.
            ValueError: If the file format is invalid.
        """
        if use_cache and path in self._cache:
            return self._cache[path]
        
        full_path = self.prompts_dir / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {full_path}")
        
        template = self._parse_file(full_path)
        
        if use_cache:
            self._cache[path] = template
        
        return template
    
    def load_all(self, directory: str) -> Dict[str, PromptTemplate]:
        """Load all prompt files from a directory.
        
        Args:
            directory: Directory path relative to prompts root.
            
        Returns:
            Dictionary mapping filename (without extension) to PromptTemplate.
        """
        dir_path = self.prompts_dir / directory
        
        if not dir_path.exists():
            logger.warning(f"Prompts directory not found: {dir_path}")
            return {}
        
        templates = {}
        for file_path in dir_path.glob("*.md"):
            try:
                relative_path = file_path.relative_to(self.prompts_dir)
                template = self.load(str(relative_path))
                templates[file_path.stem] = template
            except Exception as e:
                logger.error(f"Failed to load prompt {file_path}: {e}")
                continue
        
        return templates
    
    def list_prompts(self, directory: str = "") -> List[str]:
        """List available prompt files in a directory.
        
        Args:
            directory: Directory path relative to prompts root.
            
        Returns:
            List of prompt file paths (relative to prompts root).
        """
        search_dir = self.prompts_dir / directory if directory else self.prompts_dir
        
        if not search_dir.exists():
            return []
        
        prompts = []
        for file_path in search_dir.rglob("*.md"):
            if file_path.name != "README.md":
                relative = file_path.relative_to(self.prompts_dir)
                prompts.append(str(relative))
        
        return sorted(prompts)
    
    def list_lenses(self) -> List[str]:
        """List available investor lens prompts.
        
        Returns:
            List of lens names (e.g., ["gavin_baker", "karpathy"]).
        """
        lenses_dir = self.prompts_dir / "investment" / "lenses"
        
        if not lenses_dir.exists():
            return []
        
        return sorted([
            f.stem for f in lenses_dir.glob("*.md")
            if f.name != "README.md"
        ])
    
    def clear_cache(self):
        """Clear the template cache."""
        self._cache.clear()
    
    def _parse_file(self, file_path: Path) -> PromptTemplate:
        """Parse a prompt file into a PromptTemplate.
        
        Args:
            file_path: Full path to the prompt file.
            
        Returns:
            Parsed PromptTemplate.
            
        Raises:
            ValueError: If the file format is invalid.
        """
        content = file_path.read_text(encoding="utf-8")
        
        # Parse YAML frontmatter
        frontmatter, body = self._parse_frontmatter(content)
        
        # Parse prompt sections
        system_prompt, user_prompt = self._parse_sections(body)
        
        # Extract metadata
        name = frontmatter.get("name", file_path.stem.replace("_", " ").title())
        version = str(frontmatter.get("version", "1.0"))
        parameters = frontmatter.get("parameters", [])
        
        # Auto-detect parameters from placeholders if not specified
        if not parameters:
            parameters = self._extract_parameters(user_prompt)
        
        # Remove known fields from metadata
        metadata = {
            k: v for k, v in frontmatter.items()
            if k not in ("name", "version", "parameters")
        }
        
        return PromptTemplate(
            name=name,
            version=version,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            parameters=parameters,
            path=file_path,
            metadata=metadata,
        )
    
    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from content.
        
        Args:
            content: Full file content.
            
        Returns:
            Tuple of (frontmatter_dict, remaining_body).
        """
        # Match frontmatter block
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            frontmatter_text = match.group(1)
            body = match.group(2)
            
            try:
                frontmatter = yaml.safe_load(frontmatter_text) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse frontmatter: {e}")
                frontmatter = {}
            
            return frontmatter, body
        
        # No frontmatter found
        return {}, content
    
    def _parse_sections(self, body: str) -> tuple[str, str]:
        """Parse system and user prompt sections from body.
        
        Args:
            body: Markdown body after frontmatter.
            
        Returns:
            Tuple of (system_prompt, user_prompt).
        """
        # Split by headers
        sections = re.split(r"^#+\s*", body, flags=re.MULTILINE)
        
        system_prompt = ""
        user_prompt = ""
        
        for section in sections:
            if not section.strip():
                continue
            
            # Extract header and content
            lines = section.strip().split("\n", 1)
            header = lines[0].lower().strip()
            content = lines[1].strip() if len(lines) > 1 else ""
            
            if "system" in header:
                system_prompt = content
            elif "user" in header or "prompt" in header:
                user_prompt = content
        
        # If no sections found, treat entire body as user prompt
        if not user_prompt and not system_prompt:
            user_prompt = body.strip()
        
        return system_prompt, user_prompt
    
    def _extract_parameters(self, template: str) -> List[str]:
        """Extract parameter names from template placeholders.
        
        Args:
            template: Prompt template string.
            
        Returns:
            List of unique parameter names.
        """
        # Match {parameter} but not {{escaped}}
        pattern = r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})"
        matches = re.findall(pattern, template)
        
        # Return unique parameters in order of first appearance
        seen = set()
        params = []
        for match in matches:
            if match not in seen:
                seen.add(match)
                params.append(match)
        
        return params


# Convenience function for simple usage
def load_prompt(path: str, prompts_dir: Optional[Path] = None) -> PromptTemplate:
    """Load a single prompt template.
    
    Args:
        path: Path relative to prompts directory.
        prompts_dir: Optional custom prompts directory.
        
    Returns:
        PromptTemplate instance.
    """
    loader = PromptLoader(prompts_dir)
    return loader.load(path)

