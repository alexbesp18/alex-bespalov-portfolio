"""
Analysis Module Base Classes

Provides base classes for building modular, extensible analysis modules.
Enables plugin architecture where new modules can be added by:
1. Creating a new prompt file in prompts/
2. Creating a module that extends AnalysisModule
3. Registering in the module registry
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar

from ..prompts import PromptLoader, PromptTemplate
from .llm_client import LLMClient, get_client

__all__ = [
    "AnalysisModule",
    "AnalysisResult",
    "ModuleRegistry",
    "register_module",
    "get_module",
    "list_modules",
]

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="AnalysisModule")


@dataclass
class AnalysisResult:
    """Base result class for analysis modules.
    
    All analysis modules should return results that extend this class
    or at minimum include these fields.
    
    Attributes:
        success: Whether the analysis completed successfully.
        cost_usd: LLM API cost for the analysis.
        data: The analysis output data.
        error: Error message if analysis failed.
    """
    success: bool
    cost_usd: float
    data: Dict[str, Any]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "cost_usd": self.cost_usd,
            "data": self.data,
            "error": self.error,
        }


class AnalysisModule(ABC):
    """Base class for all analysis modules.
    
    Provides a consistent interface for analysis modules that:
    - Load prompts from external files
    - Use LLM clients for generation
    - Return structured results
    
    To create a new module:
    1. Create a prompt file in prompts/
    2. Extend this class
    3. Implement analyze() and prompt_path property
    4. Register with ModuleRegistry
    
    Example:
        >>> class SentimentAnalyzer(AnalysisModule):
        ...     @property
        ...     def prompt_path(self) -> str:
        ...         return "analysis/sentiment.md"
        ...     
        ...     def analyze(self, transcript: str, **kwargs) -> AnalysisResult:
        ...         template = self.get_template()
        ...         system, user = template.format(transcript=transcript)
        ...         response = self.client.complete(user, system)
        ...         return AnalysisResult(
        ...             success=True,
        ...             cost_usd=response.cost_usd,
        ...             data=response.parse_json(),
        ...         )
    """
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        """Initialize the analysis module.
        
        Args:
            client: Pre-configured LLM client.
            provider: LLM provider if creating new client.
            model: Model to use if creating new client.
            prompt_loader: Custom prompt loader.
        """
        if client:
            self.client = client
        else:
            kwargs = {"model": model} if model else {}
            self.client = get_client(provider, **kwargs)
        
        self.prompt_loader = prompt_loader or PromptLoader()
        self._template: Optional[PromptTemplate] = None
    
    @property
    @abstractmethod
    def prompt_path(self) -> str:
        """Path to prompt file relative to prompts/ directory.
        
        Example: "business/idea_generation.md"
        """
        pass
    
    @property
    def name(self) -> str:
        """Human-readable name for this module."""
        return self.__class__.__name__
    
    @property
    def description(self) -> str:
        """Description of what this module does."""
        return self.__doc__ or "No description available"
    
    @abstractmethod
    def analyze(self, transcript: str, **kwargs) -> AnalysisResult:
        """Run analysis on transcript.
        
        Args:
            transcript: The transcript text to analyze.
            **kwargs: Additional parameters for the analysis.
            
        Returns:
            AnalysisResult with the analysis output.
        """
        pass
    
    def get_template(self) -> Optional[PromptTemplate]:
        """Load and cache the prompt template.
        
        Returns:
            PromptTemplate if found, None otherwise.
        """
        if self._template is None:
            try:
                self._template = self.prompt_loader.load(self.prompt_path)
            except FileNotFoundError:
                logger.warning(f"Prompt file not found: {self.prompt_path}")
                self._template = None
        return self._template
    
    def validate_template(self) -> bool:
        """Check if the prompt template exists and is valid.
        
        Returns:
            True if template is valid, False otherwise.
        """
        template = self.get_template()
        return template is not None


class ModuleRegistry:
    """Registry for analysis modules.
    
    Enables plugin architecture where modules can be registered
    and discovered at runtime.
    
    Example:
        >>> registry = ModuleRegistry()
        >>> registry.register("sentiment", SentimentAnalyzer)
        >>> module = registry.get("sentiment")
        >>> result = module.analyze(transcript)
    """
    
    _instance: Optional["ModuleRegistry"] = None
    _modules: Dict[str, Type[AnalysisModule]] = {}
    
    def __new__(cls) -> "ModuleRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._modules = {}
        return cls._instance
    
    def register(
        self,
        key: str,
        module_class: Type[AnalysisModule],
        override: bool = False,
    ) -> None:
        """Register an analysis module.
        
        Args:
            key: Unique key for the module (e.g., "business_ideas").
            module_class: The module class to register.
            override: Whether to override existing registration.
            
        Raises:
            ValueError: If key already exists and override=False.
        """
        if key in self._modules and not override:
            raise ValueError(f"Module already registered: {key}")
        
        self._modules[key] = module_class
        logger.debug(f"Registered module: {key} -> {module_class.__name__}")
    
    def get(
        self,
        key: str,
        **init_kwargs,
    ) -> Optional[AnalysisModule]:
        """Get an initialized module by key.
        
        Args:
            key: The module key.
            **init_kwargs: Arguments passed to module __init__.
            
        Returns:
            Initialized module instance, or None if not found.
        """
        module_class = self._modules.get(key)
        if module_class:
            return module_class(**init_kwargs)
        return None
    
    def list(self) -> List[str]:
        """List all registered module keys."""
        return list(self._modules.keys())
    
    def info(self) -> List[Dict[str, str]]:
        """Get info about all registered modules."""
        return [
            {
                "key": key,
                "name": cls.__name__,
                "description": cls.__doc__ or "",
            }
            for key, cls in self._modules.items()
        ]
    
    def clear(self) -> None:
        """Clear all registrations (for testing)."""
        self._modules.clear()


# Global registry instance
_registry = ModuleRegistry()


def register_module(key: str, override: bool = False):
    """Decorator to register an analysis module.
    
    Example:
        >>> @register_module("sentiment")
        ... class SentimentAnalyzer(AnalysisModule):
        ...     pass
    """
    def decorator(cls: Type[AnalysisModule]) -> Type[AnalysisModule]:
        _registry.register(key, cls, override=override)
        return cls
    return decorator


def get_module(key: str, **kwargs) -> Optional[AnalysisModule]:
    """Get a registered module by key.
    
    Args:
        key: The module key.
        **kwargs: Arguments passed to module __init__.
        
    Returns:
        Initialized module instance, or None if not found.
    """
    return _registry.get(key, **kwargs)


def list_modules() -> List[str]:
    """List all registered module keys."""
    return _registry.list()


def get_registry() -> ModuleRegistry:
    """Get the global module registry."""
    return _registry

