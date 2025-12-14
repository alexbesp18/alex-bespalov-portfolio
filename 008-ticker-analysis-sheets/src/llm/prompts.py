def get_summarization_prompt(ticker: str, period: str, text: str) -> str:
    """
    Generate the prompt for summarizing earnings transcripts.
    """
    return f"""Analyze this earnings call transcript for {ticker} ({period}).

TRANSCRIPT (may be truncated):
{text}

Provide a structured summary with exactly these 4 fields:

KEY_METRICS: Extract revenue and EPS vs expectations. Use format like "Rev: $X.XB (+X% YoY, beat by X%), EPS: $X.XX (beat/miss by $X.XX)". If exact numbers unclear, use directional language like "beat expectations" or "missed estimates".

GUIDANCE: Summarize forward guidance. Did they raise, maintain, or lower? Include any specific targets mentioned.

TONE: One word only: Bullish, Cautious, Neutral, or Bearish. Base this on management's language and outlook.

SUMMARY: 2-3 sentences capturing the most important themes, risks, or opportunities mentioned.

OUTPUT FORMAT (use exactly this format):
KEY_METRICS: [your metrics here]
GUIDANCE: [your guidance here]
TONE: [one word]
SUMMARY: [your summary here]

Do not include any other text or explanation."""

def get_technical_analysis_prompt(ticker: str, tech_str: str) -> str:
    """
    Generate the prompt for analyzing technical indicators.
    """
    return f"""Analyze the technical indicators for {ticker} and provide a "Bullish Score" from 1 to 10.

TECHNICAL INDICATORS:
{tech_str}

SCORING GUIDE:
1-3: Bearish (Downtrend, negative momentum, breakdown)
4-6: Neutral (Sideways, mixed signals, consolidation)
7-10: Bullish (Uptrend, positive momentum, breakout)

OUTPUT FORMAT (JSON only):
{{
  "Bullish_Score": <int 1-10>,
  "Bullish_Reason": "<one short sentence explaining why>"
}}"""
