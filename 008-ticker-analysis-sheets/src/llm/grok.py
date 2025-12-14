import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add shared_core to path
sys.path.append(str(Path(__file__).parents[3] / "000-shared-core" / "src"))

try:
    from shared_core.llm.client import LLMClient as SharedLLMClient
except ImportError:
    logging.warning("Could not import shared_core. Ensure 000-shared-core is in python path.")
    SharedLLMClient = None

from src.utils.logging import setup_logger
from src.llm.prompts import get_summarization_prompt, get_technical_analysis_prompt

logger = setup_logger(__name__)

class GrokSummarizer:
    """Use Grok to summarize earnings transcripts and analyze technicals via Shared Core."""
    
    def __init__(self, api_key: str, model: str = 'grok-4-1-fast-reasoning', 
                 max_tokens: int = 400):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        
        if SharedLLMClient:
            self.client = SharedLLMClient("grok", api_key, {"model": model, "max_tokens": max_tokens})
        else:
            raise ImportError("Shared Core library not available")

    def summarize(self, ticker: str, period: str, text: str) -> Dict[str, str]:
        """Summarize a transcript. Returns dict with Key_Metrics, Guidance, Tone, Summary."""
        if not text or len(text) < 500:
            return {
                'Key_Metrics': 'N/A',
                'Guidance': 'N/A',
                'Tone': 'N/A',
                'Summary': 'Transcript too short to summarize'
            }
        
        logger.info(f"🤖 Summarizing {ticker} {period} with Grok...")
        
        # Truncate text
        max_chars = 30000 
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        prompt = get_summarization_prompt(ticker, period, truncated_text)
        
        try:
            content = self.client.call_llm(
                prompt=prompt,
                system_message="You are a helpful financial analyst."
            )
            
            if not content:
                return self._empty_summary("Empty response")
            
            return self._parse_summary(content)
            
        except Exception as e:
            logger.error(f"Failed to summarize {ticker}: {e}")
            return self._empty_summary(str(e)[:50])

    def analyze_technicals(self, ticker: str, tech_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical indicators and return a bullish score (1-10)."""
        logger.info(f"🤖 Analyzing technicals for {ticker} with Grok...")
            
        # Format technicals for the prompt
        tech_str = "\n".join([f"{k}: {v}" for k, v in tech_data.items() 
                            if k not in ('Ticker', 'Status', 'Updated')])
        
        prompt = get_technical_analysis_prompt(ticker, tech_str)

        try:
            content = self.client.call_llm(
                prompt=prompt,
                system_message="You are a technical analysis expert. Return only valid JSON.",
                max_tokens=self.max_tokens
            )
            
            # Clean generic markdown if present
            content = content.strip().replace('```json', '').replace('```', '').strip()
            
            try:
                result = json.loads(content)
                return {
                    'Bullish_Score': result.get('Bullish_Score', ''),
                    'Bullish_Reason': result.get('Bullish_Reason', '')
                }
            except json.JSONDecodeError:
                return {'Bullish_Score': '', 'Bullish_Reason': "Failed to parse JSON"}
                
        except Exception as e:
            logger.error(f"Failed to analyze technicals for {ticker}: {e}")
            return {'Bullish_Score': '', 'Bullish_Reason': str(e)[:50]}

    def _parse_summary(self, content: str) -> Dict[str, str]:
        """Parse Grok's response into structured fields."""
        result = {
            'Key_Metrics': 'N/A',
            'Guidance': 'N/A',
            'Tone': 'Neutral',
            'Summary': 'N/A'
        }
        
        lines = content.strip().split('\n')
        current_field = None
        current_value = []
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('KEY_METRICS:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Key_Metrics'
                current_value = [line.split(':', 1)[1].strip() if ':' in line else '']
            elif line.upper().startswith('GUIDANCE:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Guidance'
                current_value = [line.split(':', 1)[1].strip() if ':' in line else '']
            elif line.upper().startswith('TONE:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Tone'
                tone_val = line.split(':', 1)[1].strip() if ':' in line else 'Neutral'
                current_value = [tone_val.split()[0] if tone_val else 'Neutral'] 
            elif line.upper().startswith('SUMMARY:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Summary'
                current_value = [line.split(':', 1)[1].strip() if ':' in line else '']
            elif current_field and line:
                current_value.append(line)
        
        if current_field:
            result[current_field] = ' '.join(current_value).strip()
        
        # Truncate
        for key in result:
            if len(result[key]) > 500:
                result[key] = result[key][:497] + '...'
        
        return result
    
    def _empty_summary(self, reason: str) -> Dict[str, str]:
        return {
            'Key_Metrics': 'N/A',
            'Guidance': 'N/A',
            'Tone': 'N/A',
            'Summary': f'Summary unavailable: {reason}'
        }
