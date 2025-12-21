"""
Unified Grok AI analyzer for technical analysis and transcript summarization.
Combines functionality from multiple v2 scripts into a single module.
"""

import json
import requests
from typing import Dict, Any, Optional


class GrokAnalyzer:
    """
    Grok AI analyzer for:
    - Technical indicator analysis with detailed Tech_Summary
    - Earnings transcript summarization
    """
    
    def __init__(self, api_key: str, model: str = 'grok-4-1-fast-reasoning',
                 max_tokens: int = 2000, verbose: bool = False):
        """
        Initialize Grok analyzer.
        
        Args:
            api_key: Grok API key
            model: Model to use (default: grok-4-1-fast-reasoning)
            max_tokens: Max tokens for response (default: 2000 for detailed analysis)
            verbose: Print detailed progress
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max(max_tokens, 1500)  # Enforce minimum for detailed analysis
        self.base_url = 'https://api.x.ai/v1/chat/completions'
        self.verbose = verbose
    
    def _call_api(self, prompt: str, temperature: float = 0.3,
                  json_response: bool = False, timeout: int = 120) -> Optional[str]:
        """
        Make API call to Grok.
        
        Returns:
            Response content string, or None on error
        """
        try:
            payload = {
                'model': self.model,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': temperature,
                'max_tokens': self.max_tokens,
            }
            
            if json_response:
                payload['response_format'] = {'type': 'json_object'}
            else:
                payload['search'] = False  # No web search for summarization
            
            response = requests.post(
                self.base_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 429:
                if self.verbose:
                    print(f"    ⚠️  Rate limited")
                return None
            
            if response.status_code != 200:
                if self.verbose:
                    print(f"    ❌ API error: {response.status_code}")
                return None
            
            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Strip markdown code blocks if present
            if content.startswith('```'):
                lines = content.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                content = '\n'.join(lines)
            
            return content
            
        except requests.exceptions.Timeout:
            if self.verbose:
                print(f"    ❌ Request timeout")
            return None
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Error: {e}")
            return None
    
    # =========================================================================
    # TECHNICAL ANALYSIS
    # =========================================================================
    
    def analyze_technicals(self, ticker: str, tech_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze technical indicators and return a bullish score plus detailed summary.
        
        Args:
            ticker: Stock ticker symbol
            tech_data: Dict of technical indicator values
            
        Returns:
            Dict with Bullish_Score, Bullish_Reason, Tech_Summary
        """
        if self.verbose:
            print(f"    🤖 Analyzing technicals for {ticker} with Grok...")
        
        # Format technicals for the prompt
        tech_str = "\n".join([
            f"{k}: {v}" for k, v in tech_data.items() 
            if k not in ('Ticker', 'Status', 'Updated', 'Bullish_Score', 'Bullish_Reason', 'Tech_Summary')
        ])
        
        prompt = f"""You are a veteran technical analyst with 20+ years of experience. Analyze these indicators for {ticker} and provide both a score and detailed breakdown.

TECHNICAL INDICATORS:
{tech_str}

Provide your analysis in this exact JSON format:

{{
  "Bullish_Score": <integer 1-10>,
  "Bullish_Reason": "<one sentence headline - e.g., 'Strong uptrend with momentum confirmation' or 'Bearish breakdown below key support'>",
  "Tech_Summary": "<detailed analysis with each point separated by || - see format below>"
}}

SCORING GUIDE:
1-2: Strong Bearish (confirmed downtrend, breaking support, negative momentum across indicators)
3-4: Bearish (downtrend or topping pattern, weakening momentum)
5-6: Neutral (sideways/consolidation, mixed signals, waiting for breakout direction)
7-8: Bullish (uptrend, positive momentum, holding support)
9-10: Strong Bullish (confirmed uptrend, breakout, momentum acceleration)

TECH_SUMMARY FORMAT - Use || as separator between points. Cover these 7 areas:

TREND: Is price above or below key MAs (20/50/200)? MAs stacked bullishly (20>50>200) or bearishly? ADX strength? || MOMENTUM: RSI overbought (>70), oversold (<30), or neutral? MACD bullish or bearish? Any divergences? || SUPPORT: Key support levels from BB lower, swing lows, MAs. How close is price? || RESISTANCE: Key resistance from BB upper, 52W high, MAs overhead. How close? || VOLUME: OBV confirming trend or diverging? Relative volume conviction? || RISK: What invalidates this setup? Where's the stop loss? || VERDICT: What would you do - buy, wait for pullback, avoid? Be specific with price levels.

Example format: "TREND: Price at $182 sits below 20-day ($186) and 50-day ($187) but above 200-day ($154), MAs not stacked cleanly, ADX 26 shows moderate trend strength. || MOMENTUM: RSI 39 neutral-bearish, MACD negative with histogram contracting, no divergence. || ..."

Be specific with actual price levels from the data. Don't hedge - take a stance."""

        content = self._call_api(prompt, temperature=0.3, json_response=True)
        
        if not content:
            return {
                'Bullish_Score': '',
                'Bullish_Reason': 'API Error',
                'Tech_Summary': ''
            }
        
        try:
            result = json.loads(content)
            
            # Convert || separators to newlines for better Sheet readability
            tech_summary = result.get('Tech_Summary', '')
            if '||' in tech_summary:
                tech_summary = tech_summary.replace(' || ', '\n').replace('|| ', '\n').replace(' ||', '\n').replace('||', '\n')
            
            if self.verbose:
                print(f"    ✅ Tech analysis complete: Score={result.get('Bullish_Score')}")
            
            return {
                'Bullish_Score': result.get('Bullish_Score', ''),
                'Bullish_Reason': (result.get('Bullish_Reason', '') or '')[:200],
                'Tech_Summary': tech_summary[:3000] if len(tech_summary) > 3000 else tech_summary
            }
            
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"    ❌ JSON parse error: {e}")
            return {
                'Bullish_Score': '',
                'Bullish_Reason': 'Failed to parse response',
                'Tech_Summary': ''
            }
    
    # =========================================================================
    # TRANSCRIPT SUMMARIZATION
    # =========================================================================
    
    def summarize_transcript(self, ticker: str, period: str, text: str) -> Dict[str, Any]:
        """
        Summarize an earnings transcript.
        
        Args:
            ticker: Stock ticker symbol
            period: Earnings period (e.g., "2024Q4")
            text: Full transcript text
            
        Returns:
            Dict with Key_Metrics, Guidance, Tone, Summary
        """
        if not text or len(text) < 500:
            return {
                'Key_Metrics': 'N/A',
                'Guidance': 'N/A',
                'Tone': 'N/A',
                'Summary': 'Transcript too short to summarize'
            }
        
        if self.verbose:
            print(f"    🤖 Summarizing {ticker} {period} with Grok...")
        
        # Truncate text to avoid token limits
        max_chars = 60000  # ~15000 tokens
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        prompt = f"""You are a senior equity research analyst. Analyze this earnings call transcript for {ticker} ({period}).

TRANSCRIPT (may be truncated):
{truncated_text}

Provide a structured analysis with exactly these 4 fields:

KEY_METRICS: Extract the actual reported numbers vs expectations. Format: "Rev: $X.XB (+X% YoY, beat/missed by $XM or X%), EPS: $X.XX (beat/missed by $X.XX)". Include segment breakdowns if material (e.g., "Data Center: $XB +X% YoY"). If numbers are unclear, state what IS clear.

GUIDANCE: What did they guide for next quarter AND full year? Did they RAISE, MAINTAIN, or LOWER prior guidance? Include specific targets: revenue range, EPS range, margin expectations, CapEx plans. Note any language hedging ("at least", "approximately", "subject to").

TONE: Classify based on FACTS, not management spin. Use these rules:
- BULLISH: Beat on revenue AND/OR EPS (whichever reported), AND guidance raised OR maintained with positive commentary. Strong demand signals.
- CAUTIOUS: Beat but lowered forward guidance, OR mixed results (beat one metric/missed other), OR maintained guidance with explicit headwinds mentioned (tariffs, delays, macro concerns).
- NEUTRAL: Roughly in-line results with maintained guidance, no clear positive or negative direction.
- BEARISH: Missed on revenue OR EPS, OR lowered guidance, OR disclosed significant new risks (customer loss, demand weakness, margin compression).
If only revenue is reported (no EPS), base it on revenue vs expectations. Output exactly one word.

SUMMARY: Write 5-7 sentences covering:
1. Did they BEAT or MISS? By how much and why?
2. What business segments/products drove the results?
3. Key RISKS mentioned (competition, tariffs, supply chain, customer concentration, macro)
4. Key OPPORTUNITIES/CATALYSTS (new products, markets, partnerships, contracts)
5. How does this compare to prior quarter trajectory - accelerating or decelerating?
6. What should investors watch for next quarter?

Be specific with numbers. Avoid vague language like "strong results" - say "beat by 8%" instead.

OUTPUT FORMAT (use exactly this format):
KEY_METRICS: [your detailed metrics here]
GUIDANCE: [your guidance analysis here]
TONE: [one word only]
SUMMARY: [your 5-7 sentence summary here]

Do not include any other text, preamble, or explanation."""

        content = self._call_api(prompt, temperature=0.2, json_response=False)
        
        if not content:
            return self._empty_summary("API Error")
        
        result = self._parse_summary(content)
        
        if self.verbose:
            print(f"    ✅ Summary complete: Tone={result['Tone']}")
        
        return result
    
    def _parse_summary(self, content: str) -> Dict[str, Any]:
        """Parse Grok's transcript summary response into structured fields."""
        result = {
            'Key_Metrics': 'N/A',
            'Guidance': 'N/A',
            'Tone': 'Neutral',
            'Summary': 'N/A'
        }
        
        # Clean up markdown formatting
        content = content.replace('**', '').replace('__', '')
        
        lines = content.strip().split('\n')
        current_field = None
        current_value = []
        
        for line in lines:
            line = line.strip()
            line_upper = line.upper().lstrip('*_#- ')
            
            if line_upper.startswith('KEY_METRICS:') or line_upper.startswith('KEY METRICS:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Key_Metrics'
                if ':' in line:
                    current_value = [line.split(':', 1)[1].strip()]
                else:
                    current_value = []
            elif line_upper.startswith('GUIDANCE:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Guidance'
                if ':' in line:
                    current_value = [line.split(':', 1)[1].strip()]
                else:
                    current_value = []
            elif line_upper.startswith('TONE:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Tone'
                if ':' in line:
                    tone_val = line.split(':', 1)[1].strip()
                    tone_val = tone_val.replace('*', '').replace('_', '').strip()
                    current_value = [tone_val.split()[0] if tone_val else 'Neutral']
                else:
                    current_value = ['Neutral']
            elif line_upper.startswith('SUMMARY:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Summary'
                if ':' in line:
                    current_value = [line.split(':', 1)[1].strip()]
                else:
                    current_value = []
            elif current_field and line:
                current_value.append(line)
        
        # Don't forget the last field
        if current_field:
            result[current_field] = ' '.join(current_value).strip()
        
        # Truncate long values for sheet
        max_lengths = {
            'Key_Metrics': 1500,
            'Guidance': 1500,
            'Tone': 20,
            'Summary': 2000
        }
        for key, max_len in max_lengths.items():
            if len(result[key]) > max_len:
                result[key] = result[key][:max_len-3] + '...'
        
        return result
    
    def _empty_summary(self, reason: str) -> Dict[str, Any]:
        """Return empty summary dict with reason."""
        return {
            'Key_Metrics': 'N/A',
            'Guidance': 'N/A',
            'Tone': 'N/A',
            'Summary': f'Summary unavailable: {reason}'
        }

