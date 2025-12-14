"""CLI entry point for the investment agent."""

import argparse
import sys
from pathlib import Path

from src.agent.investment_agent import InvestmentAgent
from src.config import Settings
from src.utils.logging import setup_logging


def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="AI-powered investment analysis agent for processing transcripts"
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Input folder path (default: input/)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output folder path (default: output/)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Optional log file path"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    try:
        # Load settings
        from src.config import get_settings
        settings = get_settings()
        
        # Validate API keys are configured
        settings.validate_api_keys()
        
        # Override paths if provided
        if args.input:
            settings.input_folder = args.input
        if args.output:
            settings.output_folder = args.output
        
        # Create and run agent
        agent = InvestmentAgent(settings)
        agent.run()
        
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

