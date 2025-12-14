"""Investment analysis agent that processes transcripts through LLM pipeline."""

import os
from datetime import datetime
from pathlib import Path
from typing import Literal

from src.config import Settings, get_settings
from src.llm.client import LLMClient
from src.utils.logging import get_logger
from src.utils.parsing import (
    InvestmentOpportunity,
    parse_opportunities_response,
    parse_companies_response,
    parse_themes_response,
)

logger = get_logger(__name__)


class InvestmentAgent:
    """Agent that analyzes investment transcripts through a 3-step LLM pipeline."""
    
    def __init__(self, settings: Settings | None = None):
        """Initialize the agent with configuration.
        
        Args:
            settings: Application settings. If None, uses global settings.
        """
        self.settings = settings or get_settings()
        self.llm_client: LLMClient | None = None
        self.provider: str = ""
        
        # Setup logging
        from src.utils.logging import setup_logging
        setup_logging(self.settings.log_level, self.settings.log_file)
    
    def _load_prompt(self, prompt_name: str) -> str:
        """Load a prompt template from file.
        
        Args:
            prompt_name: Name of prompt file (without .txt extension)
            
        Returns:
            Prompt template string
        """
        prompt_path = Path(__file__).parent.parent / "llm" / "prompts" / f"{prompt_name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _get_model_mapping(self, provider: str, model_key: str) -> str:
        """Map config model names to actual API model strings.
        
        Args:
            provider: Provider name
            model_key: Model key from config
            
        Returns:
            Actual API model string
        """
        mappings = {
            "claude": {
                "sonnet-4.5": "claude-sonnet-4-20250514",
                "opus-4.1": "claude-opus-4-20250514"
            },
            "openai": {
                "gpt-5": "gpt-5",
                "gpt-5-mini": "gpt-5-mini",
                "gpt-5-nano": "gpt-5-nano",
                "gpt-4": "gpt-4",
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
    
    def select_model(self) -> tuple[str, dict]:
        """Interactive model selection.
        
        Returns:
            Tuple of (provider_key, provider_settings)
        """
        print("\n" + "="*60)
        print("🤖 SELECT YOUR LLM PROVIDER")
        print("="*60)
        
        # Get enabled providers
        providers = []
        if self.settings.claude_enabled:
            providers.append(("Claude", "claude", self.settings.get_provider_settings("claude")))
        if self.settings.openai_enabled:
            providers.append(("OpenAI", "openai", self.settings.get_provider_settings("openai")))
        if self.settings.grok_enabled:
            providers.append(("Grok", "grok", self.settings.get_provider_settings("grok")))
        if self.settings.gemini_enabled:
            providers.append(("Gemini", "gemini", self.settings.get_provider_settings("gemini")))
        
        if not providers:
            raise ValueError("No providers enabled in configuration")
        
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
    
    def initialize_client(self, provider: str, provider_settings: dict) -> None:
        """Initialize the LLM client for the selected provider.
        
        Args:
            provider: Provider name
            provider_settings: Provider-specific settings
        """
        self.provider = provider
        self.llm_client = LLMClient(self.settings, provider, provider_settings)
        logger.info(f"Initialized {provider} client with model {self.llm_client.model_name}")
    
    def read_input_file(self, input_folder: Path | str | None = None) -> str:
        """Read the first txt file from input folder.
        
        Args:
            input_folder: Path to input folder. Uses settings default if None.
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If folder or files not found
            ValueError: If file is empty or too large
        """
        if input_folder is None:
            input_folder = self.settings.input_folder
        else:
            input_folder = Path(input_folder)
        
        if not input_folder.exists():
            raise FileNotFoundError(f"Input folder '{input_folder}' not found")
        
        if not input_folder.is_dir():
            raise ValueError(f"Input path '{input_folder}' is not a directory")
        
        txt_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
        if not txt_files:
            raise FileNotFoundError("No .txt files found in input folder")
        
        input_path = input_folder / txt_files[0]
        print(f"📄 Reading: {txt_files[0]}")
        logger.info(f"Reading input file: {input_path}")
        
        # Check file size (warn if > 10MB)
        file_size = input_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            logger.warning(f"Input file is large ({file_size / 1024 / 1024:.1f}MB). Processing may take time.")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode file '{input_path}'. File must be UTF-8 encoded.") from e
        
        if not content.strip():
            raise ValueError(f"Input file '{input_path}' is empty")
        
        return content
    
    def run_prompt_1(self, transcript: str) -> str:
        """Extract investment themes and verticals.
        
        Args:
            transcript: Input transcript text
            
        Returns:
            LLM response with themes
            
        Raises:
            ValueError: If transcript is empty
            RuntimeError: If LLM client is not initialized
        """
        if not transcript or not transcript.strip():
            raise ValueError("Transcript is empty")
        
        if not self.llm_client:
            raise RuntimeError("LLM client not initialized. Call initialize_client() first.")
        
        print("\n🔍 STEP 1: Extracting investment themes...")
        logger.info("Running prompt 1: Theme extraction")
        
        prompt_template = self._load_prompt("theme_extraction")
        prompt = prompt_template.format(transcript=transcript)
        
        response = self.llm_client.call_llm(prompt)
        print("✅ Themes extracted")
        logger.info("Theme extraction completed")
        return response
    
    def run_prompt_2(self, themes: str) -> str:
        """Find publicly traded companies for each theme.
        
        Args:
            themes: Themes from step 1
            
        Returns:
            LLM response with companies
            
        Raises:
            ValueError: If themes input is empty
            RuntimeError: If LLM client is not initialized
        """
        if not themes or not themes.strip():
            raise ValueError("Themes input is empty")
        
        if not self.llm_client:
            raise RuntimeError("LLM client not initialized. Call initialize_client() first.")
        
        print("\n🏢 STEP 2: Finding publicly traded companies...")
        logger.info("Running prompt 2: Company identification")
        
        prompt_template = self._load_prompt("company_identification")
        prompt = prompt_template.format(themes=themes)
        
        response = self.llm_client.call_llm(prompt)
        print("✅ Companies identified")
        logger.info("Company identification completed")
        return response
    
    def run_prompt_3(self, companies: str) -> str:
        """Filter to companies with recent positive catalysts.
        
        Args:
            companies: Companies from step 2
            
        Returns:
            LLM response with filtered opportunities
            
        Raises:
            ValueError: If companies input is empty
            RuntimeError: If LLM client is not initialized
        """
        if not companies or not companies.strip():
            raise ValueError("Companies input is empty")
        
        if not self.llm_client:
            raise RuntimeError("LLM client not initialized. Call initialize_client() first.")
        
        print("\n📊 STEP 3: Filtering for recent earnings catalysts...")
        logger.info("Running prompt 3: Catalyst filtering")
        
        prompt_template = self._load_prompt("catalyst_filtering")
        prompt = prompt_template.format(companies=companies)
        
        response = self.llm_client.call_llm(prompt)
        print("✅ Filtered to high conviction picks")
        logger.info("Catalyst filtering completed")
        return response
    
    def extract_console_summary(self, final_output: str) -> None:
        """Extract key info for console display using structured parsing.
        
        Args:
            final_output: Final LLM response text
        """
        print("\n" + "="*60)
        print("🎯 TOP INVESTMENT OPPORTUNITIES")
        print("="*60)
        
        try:
            opportunities = parse_opportunities_response(final_output)
            if opportunities:
                for opp in opportunities:
                    self.print_company_summary(opp)
            else:
                print("\n📋 See full output file for detailed analysis")
        except Exception as e:
            logger.warning(f"Failed to parse structured output: {e}")
            print("\n📋 See full output file for detailed analysis")
    
    def print_company_summary(self, opportunity: InvestmentOpportunity) -> None:
        """Print formatted company summary.
        
        Args:
            opportunity: InvestmentOpportunity object
        """
        print(f"\n📌 {opportunity.ticker}")
        print(f"   Cap Size: {opportunity.market_cap}")
        print(f"   💡 {opportunity.thesis}")
    
    def save_output(
        self,
        step1: str,
        step2: str,
        step3: str,
        output_folder: Path | str | None = None
    ) -> Path:
        """Save all outputs to a file.
        
        Args:
            step1: Step 1 output (themes)
            step2: Step 2 output (companies)
            step3: Step 3 output (opportunities)
            output_folder: Output folder path. Uses settings default if None.
            
        Returns:
            Path to saved output file
        """
        if output_folder is None:
            output_folder = self.settings.output_folder
        else:
            output_folder = Path(output_folder)
        
        output_folder.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_folder / f"analysis_{timestamp}.txt"
        
        model_name = self.llm_client.model_name if self.llm_client else "unknown"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("INVESTMENT ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model: {self.provider.upper()} - {model_name}\n")
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
        logger.info(f"Output saved to: {output_path}")
        return output_path
    
    def run(self) -> None:
        """Main execution flow."""
        print("🚀 Investment Analysis Agent Starting...")
        print("="*60)
        logger.info("Starting investment analysis agent")
        
        try:
            # Select model
            provider, provider_settings = self.select_model()
            
            # Initialize client
            self.initialize_client(provider, provider_settings)
            
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
            logger.info("Investment analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}", exc_info=True)
            print(f"\n❌ Error: {str(e)}")
            raise

