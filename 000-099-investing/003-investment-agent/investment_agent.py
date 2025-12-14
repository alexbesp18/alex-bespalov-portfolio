import os
import json
from datetime import datetime

class InvestmentAgent:
    def __init__(self):
        """Initialize the agent with config"""
        self.config = self.load_config()
        self.provider = None
        self.client = None
        self.model_name = None
        self.max_tokens = None
        self.settings = {}
        
    def load_config(self):
        """Load configuration from config.json"""
        config_path = "config.json"
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                "config.json not found. Please copy config.json to the same directory as this script."
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_model_mapping(self, provider, model_key):
        """Map config model names to actual API model strings"""
        mappings = {
            "claude": {
                "sonnet-4.5": "claude-sonnet-4-20250514",
                "opus-4.1": "claude-opus-4-20250514"
            },
            "openai": {
                "gpt-5": "gpt-5",
                "gpt-5-mini": "gpt-5-mini",
                "gpt-5-nano": "gpt-5-nano"
            },
            "grok": {
                "grok-4": "grok-4",
                "grok-4-fast": "grok-4-fast",
                "grok-3-mini": "grok-3-mini"
            },
            "gemini": {
                "gemini-2.5-pro": "gemini-2.5-pro",
                "gemini-2.5-flash": "gemini-2.5-flash"
            }
        }
        return mappings.get(provider, {}).get(model_key, model_key)
    
    def select_model(self):
        """Interactive model selection"""
        print("\n" + "="*60)
        print("🤖 SELECT YOUR LLM PROVIDER")
        print("="*60)
        
        # Get enabled providers
        providers = []
        if self.config["claude_settings"]["enabled"]:
            providers.append(("Claude", "claude", self.config["claude_settings"]))
        if self.config["openai_settings"]["enabled"]:
            providers.append(("OpenAI", "openai", self.config["openai_settings"]))
        if self.config["grok_settings"]["enabled"]:
            providers.append(("Grok", "grok", self.config["grok_settings"]))
        if self.config["gemini_settings"]["enabled"]:
            providers.append(("Gemini", "gemini", self.config["gemini_settings"]))
        
        if not providers:
            raise ValueError("No providers enabled in config.json")
        
        # Display providers
        for i, (name, key, settings) in enumerate(providers, 1):
            model = settings["model"]
            print(f"{i}. {name} ({model})")
        
        # Get selection
        while True:
            try:
                choice = input(f"\nSelect provider (1-{len(providers)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(providers):
                    selected_name, selected_key, selected_settings = providers[idx]
                    print(f"✅ Selected: {selected_name} - {selected_settings['model']}")
                    return selected_key, selected_settings
                else:
                    print(f"❌ Please enter a number between 1 and {len(providers)}")
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Invalid input. Please enter a number.")
    
    def initialize_client(self, provider, settings):
        """Initialize the appropriate API client"""
        self.provider = provider
        self.settings = settings
        
        if provider == "claude":
            from anthropic import Anthropic
            api_key = self.config["api_keys"]["anthropic"]
            if not api_key:
                raise ValueError("Anthropic API key not set in config.json")
            self.client = Anthropic(api_key=api_key)
            self.model_name = self.get_model_mapping("claude", settings["model"])
            self.max_tokens = settings["max_tokens"]
            
        elif provider == "openai":
            from openai import OpenAI
            api_key = self.config["api_keys"]["openai"]
            if not api_key:
                raise ValueError("OpenAI API key not set in config.json")
            self.client = OpenAI(api_key=api_key)  # Responses API compatible client
            self.model_name = self.get_model_mapping("openai", settings["model"])
            self.max_tokens = settings["max_tokens"]
            
        elif provider == "grok":
            # OpenAI-compatible client pointed at xAI endpoint
            from openai import OpenAI
            api_key = self.config["api_keys"]["xai"]
            if not api_key:
                raise ValueError("XAI API key not set in config.json")
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
            self.model_name = self.get_model_mapping("grok", settings["model"])
            self.max_tokens = settings["max_tokens"]
            
        elif provider == "gemini":
            import google.generativeai as genai
            api_key = self.config["api_keys"]["google"]
            if not api_key:
                raise ValueError("Google API key not set in config.json")
            genai.configure(api_key=api_key)
            self.client = genai
            self.model_name = self.get_model_mapping("gemini", settings["model"])
            self.max_tokens = settings["max_tokens"]

        # normalize any caps and budgets after init
        self._sanitize_caps()

    def _sanitize_caps(self):
        """Normalize caps and budgets to avoid common API errors"""
        try:
            if self.provider == "claude" and self.settings.get("use_extended_thinking"):
                mb = int(self.settings.get("thinking_budget_tokens", 0))
                mt = int(self.settings.get("max_tokens", 0))
                if mb >= mt:
                    # keep budget strictly less than max tokens
                    self.settings["thinking_budget_tokens"] = max(mt - 1, 0)
            if self.provider == "grok":
                # Grok-4 uses a combined context window around 256k, keep output conservative
                self.max_tokens = min(self.max_tokens or 0, 128000)
        except Exception:
            # do not fail init on a sanitization issue
            pass

    def call_llm(self, prompt, max_tokens=None):
        """Universal LLM call that works with any provider"""
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        if self.provider == "claude":
            # Anthropic Messages API with optional thinking budget
            thinking_arg = None
            if self.settings.get("use_extended_thinking"):
                try:
                    think_budget = min(
                        int(self.settings.get("thinking_budget_tokens", 0)),
                        int(self.settings.get("max_tokens", 0)) - 1
                    )
                    if think_budget > 0:
                        # Correct shape per SDK: {"type": "enabled", "budget_tokens": N}
                        thinking_arg = {"type": "enabled", "budget_tokens": think_budget}
                except Exception:
                    thinking_arg = None

            # Use streaming for very large generations
            if max_tokens and max_tokens > 16000:
                response_text = ""
                try:
                    with self.client.messages.stream(
                        model=self.model_name,
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}],
                        thinking=thinking_arg if thinking_arg else None
                    ) as stream:
                        for text in stream.text_stream:
                            response_text += text
                            print(text, end="", flush=True)
                    print()  # New line after streaming
                    return response_text
                except Exception:
                    # Fallback to non-streaming without thinking param if stream fails
                    pass

            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                    thinking=thinking_arg if thinking_arg else None,
                    timeout=600.0  # generous timeout
                )
                # Anthropic returns a list of content blocks
                return "".join([blk.text for blk in response.content if getattr(blk, "text", None)])
            except Exception as e:
                raise RuntimeError(f"Claude call failed: {e}")
            
        elif self.provider == "openai":
            # OpenAI Responses API, optional web search tool
            use_web = self.settings.get("web_search", {}).get("enabled", False)
            reasoning_effort = self.settings.get("reasoning_effort", "medium")

            tools = [{"type": "web_search"}] if use_web else None
            try:
                resp = self.client.responses.create(
                    model=self.model_name,
                    input=[{"role": "user", "content": prompt}],
                    max_output_tokens=max_tokens,
                    reasoning={"effort": reasoning_effort},
                    tools=tools
                )
                # Unified text
                return getattr(resp, "output_text", None) or self._responses_text_fallback(resp)
            except Exception as e:
                raise RuntimeError(f"OpenAI call failed: {e}")
            
        elif self.provider == "grok":
            # xAI Grok via OpenAI-compatible chat.completions API
            try:
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens
                )
                return resp.choices[0].message.content
            except Exception as e:
                raise RuntimeError(f"Grok call failed: {e}")
            
        elif self.provider == "gemini":
            # Google Gemini with optional Search Grounding
            try:
                model = self.client.GenerativeModel(self.model_name)
                use_web = self.settings.get("web_search", {}).get("enabled", False)

                gen_cfg = {
                    "max_output_tokens": max_tokens,
                    "temperature": self.settings.get("temperature", 0.7)
                }

                if use_web:
                    try:
                        response = model.generate_content(
                            prompt,
                            tools=["google_search"],
                            generation_config=gen_cfg,
                        )
                    except Exception:
                        # Fallback for environments without tools arg support
                        response = model.generate_content(prompt, generation_config=gen_cfg)
                else:
                    response = model.generate_content(prompt, generation_config=gen_cfg)

                # Gemini text accessor
                return getattr(response, "text", None) or self._gemini_text_fallback(response)
            except Exception as e:
                raise RuntimeError(f"Gemini call failed: {e}")
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    @staticmethod
    def _responses_text_fallback(resp):
        """Fallback to collect text from Responses API structured output"""
        try:
            if hasattr(resp, "output") and isinstance(resp.output, list):
                parts = []
                for item in resp.output:
                    if isinstance(item, dict):
                        txt = item.get("content", "")
                        parts.append(txt if isinstance(txt, str) else "")
                return "\n".join([p for p in parts if p])
        except Exception:
            pass
        return ""

    @staticmethod
    def _gemini_text_fallback(response):
        """Fallback to collect text from Gemini responses"""
        try:
            if hasattr(response, "candidates"):
                parts = []
                for c in response.candidates:
                    if hasattr(c, "content") and hasattr(c.content, "parts"):
                        for p in c.content.parts:
                            if hasattr(p, "text"):
                                parts.append(p.text)
                return "\n".join(parts)
        except Exception:
            pass
        return ""

    def read_input_file(self, input_folder="input"):
        """Read the first txt file from input folder"""
        if not os.path.exists(input_folder):
            raise FileNotFoundError(f"Input folder '{input_folder}' not found")
        
        txt_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
        if not txt_files:
            raise FileNotFoundError("No .txt files found in input folder")
        
        input_path = os.path.join(input_folder, txt_files[0])
        print(f"📄 Reading: {txt_files[0]}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def run_prompt_1(self, transcript):
        """Extract investment themes and verticals"""
        print("\n🔍 STEP 1: Extracting investment themes...")
        
        prompt = f"""Extract all investment themes and verticals discussed in this podcast/report. For each, list the theme name, timestamp mentioned if available, and a one sentence rationale for why it is compelling. Format as a numbered list.

Transcript or Report:
{transcript}"""
        
        response = self.call_llm(prompt)
        print("✅ Themes extracted")
        return response
    
    def run_prompt_2(self, themes):
        """Find publicly traded companies for each theme"""
        print("\n🏢 STEP 2: Finding publicly traded companies...")
        
        prompt = f"""Based on these investment themes:

{themes}

For each theme above, list US publicly traded companies that directly operate in these spaces, no OTC stocks. Include: ticker symbol, market cap Small, Mid, or Large, and primary business line. Format as a clear table.

Use this format:
| Ticker | Market Cap | Primary Business | Theme |"""
        
        response = self.call_llm(prompt)
        print("✅ Companies identified")
        return response
    
    def run_prompt_3(self, companies):
        """Filter to companies with recent positive catalysts"""
        print("\n📊 STEP 3: Filtering for recent earnings catalysts...")
        
        prompt = f"""Based on this company list:

{companies}

Goal: filter to ONLY companies with earnings in the last 90 days that show:
- revenue or demand acceleration
- positive guidance, ideally tied to the relevant theme
- demand outpacing supply
- margin expansion

Rules:
- If the active provider supports web search, use it to confirm dates and pull the specific figures.
- Cite source links inline next to each metric.
- If you cannot find reliable sources, exclude the company.

For each qualifying company provide:
1) Ticker
2) Market Cap Small, Mid, or Large
3) Key earnings metrics with numbers and dates [link]
4) One sentence INVEST RIGHT NOW thesis

Output as a numbered list, one block per company. Do not fabricate metrics."""
        
        response = self.call_llm(prompt)
        print("✅ Filtered to high conviction picks")
        return response
    
    def extract_console_summary(self, final_output):
        """Extract key info for console display"""
        print("\n" + "="*60)
        print("🎯 TOP INVESTMENT OPPORTUNITIES")
        print("="*60)
        
        # Parse the output for key information
        lines = final_output.split('\n')
        companies = []
        current_company = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_company:
                    companies.append(current_company)
                    current_company = {}
                continue
            
            lower_line = line.lower()
            if 'ticker' in lower_line and ':' in line:
                if current_company:
                    companies.append(current_company)
                current_company = {'ticker': line.split(':', 1)[-1].strip()}
            elif current_company:
                if 'market cap' in lower_line or 'cap size' in lower_line:
                    current_company['cap'] = line.split(':', 1)[-1].strip()
                elif 'price' in lower_line:
                    current_company['price'] = line.split(':', 1)[-1].strip()
                elif 'thesis' in lower_line or 'invest' in lower_line:
                    part = line.split(':', 1)
                    current_company['thesis'] = (part[-1] if len(part) > 1 else line).strip()
        
        # Add last company if exists
        if current_company:
            companies.append(current_company)
        
        # Display companies
        if companies:
            for company in companies:
                self.print_company_summary(company)
        else:
            print("\n📋 See full output file for detailed analysis")
    
    def print_company_summary(self, company):
        """Print formatted company summary"""
        ticker = company.get('ticker', 'N/A')
        cap = company.get('cap', 'N/A')
        price = company.get('price', 'N/A')
        thesis = company.get('thesis', 'N/A')
        
        print(f"\n📌 {ticker}")
        print(f"   Cap Size: {cap}")
        print(f"   Price: {price}")
        print(f"   💡 {thesis}")
    
    def save_output(self, step1, step2, step3, output_folder="output"):
        """Save all outputs to a file"""
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_folder, f"analysis_{timestamp}.txt")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("INVESTMENT ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model: {self.provider.upper()} - {self.model_name}\n")
            f.write("="*80 + "\n\n")
            
            f.write("STEP 1: INVESTMENT THEMES\n")
            f.write("-"*80 + "\n")
            f.write(step1 + "\n\n")
            
            f.write("="*80 + "\n")
            f.write("STEP 2: PUBLICLY TRADED COMPANIES\n")
            f.write("-"*80 + "\n")
            f.write(step2 + "\n\n")
            
            f.write("="*80 + "\n")
            f.write("STEP 3: HIGH CONVICTION PICKS Recent Earnings Catalysts\n")
            f.write("-"*80 + "\n")
            f.write(step3 + "\n")
        
        print(f"\n💾 Full analysis saved to: {output_path}")
        return output_path
    
    def run(self):
        """Main execution flow"""
        print("🚀 Investment Analysis Agent Starting...")
        print("="*60)
        
        try:
            # Select model
            provider, settings = self.select_model()
            
            # Initialize client
            self.initialize_client(provider, settings)
            
            # Read input
            transcript = self.read_input_file()
            
            # Run 3 sequential prompts
            step1_themes = self.run_prompt_1(transcript)
            step2_companies = self.run_prompt_2(step1_themes)
            step3_filtered = self.run_prompt_3(step2_companies)
            
            # Save outputs
            self.save_output(step1_themes, step2_companies, step3_filtered)
            
            # Display console summary
            self.extract_console_summary(step3_filtered)
            
            print("\n" + "="*60)
            print("✅ Analysis Complete!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            raise

if __name__ == "__main__":
    agent = InvestmentAgent()
    agent.run()
