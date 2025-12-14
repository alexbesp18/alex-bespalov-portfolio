"""
Unified LLM client with retry logic and multi-model support.

Supports Claude, GPT, Grok, and Gemini with automatic retries
and consistent error handling, powered by shared_core.
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add shared_core to path (robust relative path)
sys.path.append(str(Path(__file__).parents[3] / "000-shared-core" / "src"))

try:
    from shared_core.llm.client import LLMClient as SharedLLMClient
except ImportError:
    # Fallback if path setup fails or running in different context
    logging.warning("Could not import shared_core. Ensure 000-shared-core is in python path.")
    SharedLLMClient = None

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from src.config import Settings
from src.constants import MAX_RETRY_ATTEMPTS, RETRY_MIN_WAIT, RETRY_MAX_WAIT
from src.llm.models import TechnicalAnalysisResult

logger = logging.getLogger(__name__)

# Load prompt template
PROMPT_TEMPLATE_PATH = Path(__file__).parent / "prompts" / "analysis.txt"


def load_prompt_template() -> str:
    """Load the analysis prompt template from file."""
    with open(PROMPT_TEMPLATE_PATH, 'r') as f:
        return f.read()


ANALYSIS_PROMPT_TEMPLATE = load_prompt_template()


class LLMClient:
    """
    Unified client for multiple LLM providers.
    
    Provides consistent interface for calling Claude, GPT, Grok, and Gemini
    with built-in retry logic and error handling.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize LLM clients based on settings.
        
        Args:
            settings: Application settings with API keys and model configs
        """
        self.settings = settings
        self._init_clients()
    
    def _init_clients(self) -> None:
        """Initialize all enabled LLM clients using SharedLLMClient."""
        api_keys = self.settings.api_keys
        
        # Claude
        if self.settings.claude_settings.enabled and api_keys.anthropic:
            settings = {
                "model": self.settings.claude_settings.model,
                "use_extended_thinking": getattr(self.settings.claude_settings, "use_extended_thinking", False),
                "thinking_budget_tokens": getattr(self.settings.claude_settings, "thinking_budget_tokens", 0)
            }
            # Add max_tokens
            if hasattr(self.settings.claude_settings, "max_tokens"):
                settings["max_tokens"] = self.settings.claude_settings.max_tokens

            self.claude_client = SharedLLMClient("claude", api_keys.anthropic, settings)
            logger.info(f"Claude initialized: {self.claude_client.model_name}")
        else:
            self.claude_client = None
            logger.warning("Claude disabled or API key missing")
        
        # OpenAI
        if self.settings.openai_settings.enabled and api_keys.openai:
            settings = {
                "model": self.settings.openai_settings.model,
                "reasoning_effort": getattr(self.settings.openai_settings, "reasoning_effort", "medium"),
                "max_tokens": getattr(self.settings.openai_settings, "max_tokens", 4096)
            }
            self.openai_client = SharedLLMClient("openai", api_keys.openai, settings)
            logger.info(f"GPT initialized: {self.openai_client.model_name}")
        else:
            self.openai_client = None
            logger.warning("GPT disabled or API key missing")
        
        # Grok
        if self.settings.grok_settings.enabled and api_keys.xai:
            settings = {
                "model": self.settings.grok_settings.model,
                "max_tokens": getattr(self.settings.grok_settings, "max_tokens", 4096)
            }
            self.grok_client = SharedLLMClient("grok", api_keys.xai, settings)
            logger.info(f"Grok initialized: {self.grok_client.model_name}")
        else:
            self.grok_client = None
            logger.warning("Grok disabled or API key missing")
        
        # Gemini
        if self.settings.gemini_settings.enabled and api_keys.google:
            settings = {
                "model": self.settings.gemini_settings.model,
                "temperature": getattr(self.settings.gemini_settings, "temperature", 0.7),
                "max_tokens": getattr(self.settings.gemini_settings, "max_tokens", 8000)
            }
            self.gemini_client = SharedLLMClient("gemini", api_keys.google, settings)
            logger.info(f"Gemini initialized: {self.gemini_client.model_name}")
        else:
            self.gemini_client = None
            logger.warning("Gemini disabled or API key missing")
    
    def create_analysis_prompt(self, ticker: str, market_data: Dict) -> str:
        """Create analysis prompt from template and market data."""
        ind = market_data['indicators']
        quote = market_data['quote']
        levels = market_data['levels']
        
        return ANALYSIS_PROMPT_TEMPLATE.format(
            ticker=ticker,
            price=quote['price'],
            change=quote['change'],
            percent_change=quote['percent_change'],
            volume=quote['volume'],
            previous_close=quote['previous_close'],
            sma_20=ind['sma_20'],
            sma_50=ind['sma_50'],
            sma_200=ind['sma_200'],
            rsi=ind['rsi'],
            macd=ind['macd'],
            macd_signal=ind['macd_signal'],
            macd_hist=ind['macd_hist'],
            stoch_k=ind['stoch_k'],
            stoch_d=ind['stoch_d'],
            atr=ind['atr'],
            bb_upper=ind['bb_upper'],
            bb_middle=ind['bb_middle'],
            bb_lower=ind['bb_lower'],
            closest_support=levels['closest_support'],
            key_support=levels['key_support'],
            closest_resistance=levels['closest_resistance'],
            strongest_resistance=levels['strongest_resistance']
        )
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        text = text.strip()
        text = re.sub(r'```json\s*|\s*```', '', text).strip()
        return json.loads(text)
    
    def _validate_analysis_result(self, data: Dict[str, Any]) -> TechnicalAnalysisResult:
        """Validate analysis result using Pydantic model."""
        return TechnicalAnalysisResult.model_validate(data)
    
    def analyze_with_gemini(self, ticker: str, market_data: Dict) -> Dict:
        """Analyze with Gemini."""
        if not self.gemini_client:
            return {'success': False, 'model': 'gemini', 'error': 'Gemini disabled', 'cost': 0.0}
        
        logger.info(f"Gemini analyzing {ticker}")
        prompt = self.create_analysis_prompt(ticker, market_data)
        
        try:
            # We don't pass system message for Gemini usually or it's part of settings
            # We'll just call it directly.
            response_text = self.gemini_client.call_llm(prompt)
            
            result = self._parse_json_response(response_text)
            result.update({
                'model': 'gemini',
                'success': True,
                'cost': 0.0,
                'ma_20': market_data['indicators']['sma_20'],
                'ma_50': market_data['indicators']['sma_50'],
                'ma_200': market_data['indicators']['sma_200'],
                'rsi': market_data['indicators']['rsi']
            })
            
            logger.info(f"Gemini result for {ticker}: score {result.get('technical_score', 'N/A')}/10")
            return result
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return {'success': False, 'model': 'gemini', 'error': str(e), 'cost': 0.0}
    
    def analyze_with_grok(self, ticker: str, market_data: Dict) -> Dict:
        """Analyze with Grok."""
        if not self.grok_client:
            return {'success': False, 'model': 'grok', 'error': 'Grok disabled', 'cost': 0.0}
        
        logger.info(f"Grok analyzing {ticker}")
        prompt = self.create_analysis_prompt(ticker, market_data)
        
        try:
            response_text = self.grok_client.call_llm(
                prompt=prompt,
                system_message="You are a technical analysis expert. Return only valid JSON."
            )
            
            result = self._parse_json_response(response_text)
            result.update({
                'model': 'grok',
                'success': True,
                'cost': 0.0,
                'ma_20': market_data['indicators']['sma_20'],
                'ma_50': market_data['indicators']['sma_50'],
                'ma_200': market_data['indicators']['sma_200'],
                'rsi': market_data['indicators']['rsi']
            })
            
            logger.info(f"Grok result for {ticker}: score {result.get('technical_score', 'N/A')}/10")
            return result
        except Exception as e:
            logger.error(f"Grok analysis failed: {e}")
            return {'success': False, 'model': 'grok', 'error': str(e), 'cost': 0.0}
    
    def analyze_with_gpt(self, ticker: str, market_data: Dict) -> Dict:
        """Analyze with GPT."""
        if not self.openai_client:
            return {'success': False, 'model': 'gpt', 'error': 'GPT disabled', 'cost': 0.0}
        
        logger.info(f"GPT analyzing {ticker}")
        prompt = self.create_analysis_prompt(ticker, market_data)
        
        try:
            response_text = self.openai_client.call_llm(
                prompt=prompt,
                system_message="You are a technical analysis expert. Return only valid JSON."
            )
            
            result = self._parse_json_response(response_text)
            result.update({
                'model': 'gpt',
                'success': True,
                'cost': 0.01,
                'ma_20': market_data['indicators']['sma_20'],
                'ma_50': market_data['indicators']['sma_50'],
                'ma_200': market_data['indicators']['sma_200'],
                'rsi': market_data['indicators']['rsi']
            })
            
            logger.info(f"GPT result for {ticker}: score {result.get('technical_score', 'N/A')}/10")
            return result
        except Exception as e:
            logger.error(f"GPT analysis failed: {e}")
            return {'success': False, 'model': 'gpt', 'error': str(e), 'cost': 0.0}
    
    def arbitrate_with_claude(
        self,
        ticker: str,
        results: List[Dict],
        discrepancies: Dict
    ) -> Dict:
        """Use Claude to arbitrate between agent results."""
        if not self.claude_client:
            return {'success': False, 'error': 'Claude disabled for arbitration'}
        
        logger.info(f"Claude arbitrating for {ticker}")
        
        arbitration_prompt = f"""The following agents analyzed {ticker} and have disagreements.
Review their technical analyses and provide a final consensus.

AGENT ANALYSES:
{json.dumps(results, indent=2)}

DISAGREEMENT AREAS:
{json.dumps(discrepancies, indent=2)}

Provide a balanced final technical analysis in this EXACT JSON format:
{{
    "technical_score": <0-10>,
    "optimal_entry": <price>,
    "closest_support": <price>,
    "key_support": <price>,
    "closest_resistance": <price>,
    "strongest_resistance": <price>,
    "reasoning": "<explanation of your technical arbitration>"
}}
"""
        
        try:
            response_text = self.claude_client.call_llm(prompt=arbitration_prompt)
            result = self._parse_json_response(response_text)
            result['cost'] = 0.01
            
            logger.info(f"Claude arbitrated {ticker}: score {result.get('technical_score', 'N/A')}/10")
            return result
        except Exception as e:
            logger.error(f"Claude arbitration failed: {e}")
            return {'success': False, 'error': str(e)}
