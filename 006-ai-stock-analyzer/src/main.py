#!/usr/bin/env python3
"""
AI Stock Analyzer - CLI Entry Point

Multi-agent AI system for technical stock analysis.
Uses Claude, GPT, Grok, and Gemini for consensus-based recommendations.

Usage:
    python -m src.main                    # Process tickers from Google Sheet
    python -m src.main AAPL MSFT NVDA     # Analyze specific tickers
    python -m src.main --help             # Show help

Example:
    python -m src.main --config config.json AAPL
"""

import argparse
import logging
import sys
from typing import List, Optional

from src.config import Settings
from src.constants import __version__
from src.validation import validate_tickers, ValidationError


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='ai-stock-analyzer',
        description='Multi-agent AI technical stock analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         Process tickers from Google Sheet
  %(prog)s AAPL MSFT NVDA          Analyze specific stocks
  %(prog)s -v AAPL                 Verbose output for debugging
  %(prog)s --config my-config.json Alternate config file
        """
    )
    
    parser.add_argument(
        'tickers',
        nargs='*',
        help='Stock tickers to analyze (e.g., AAPL MSFT). If empty, reads from Google Sheet.'
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='Path to config file (default: config.json)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose (debug) output'
    )
    
    parser.add_argument(
        '--start-row',
        type=int,
        default=2,
        help='Starting row for Google Sheets data (default: 2)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    return parser.parse_args()


def main(tickers: Optional[List[str]] = None, config_path: str = 'config.json') -> int:
    """
    Main entry point for the analyzer.
    
    Args:
        tickers: Optional list of tickers to analyze
        config_path: Path to config file
        
    Returns:
        Exit code (0 for success)
    """
    logger = logging.getLogger(__name__)
    
    logger.info("""
╔══════════════════════════════════════════════════════════════════════╗
║          AI STOCK ANALYZER - MULTI-AGENT TECHNICAL ANALYSIS          ║
║                  1 Credit Per Stock | 90% API Savings                 ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Load configuration
        settings = Settings.from_config_file(config_path)
        logger.info(f"Loaded config from {config_path}")
        
        # Import analyzer here to avoid circular imports
        from src.analysis.analyzer import TechnicalAnalyzer
        
        # Initialize analyzer
        analyzer = TechnicalAnalyzer(settings)
        
        # Run analysis
        if tickers:
            analyzer.process_tickers(tickers=tickers)
        else:
            analyzer.process_tickers()
        
        logger.info("\n✅ ANALYSIS COMPLETE\n")
        return 0
    
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return 2
        
    except FileNotFoundError as e:
        logger.error(f"Config file not found: {e}")
        logger.error("Please create config.json based on config.json.example")
        return 1
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Analysis interrupted by user")
        return 130
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


def cli() -> None:
    """CLI entry point."""
    args = parse_args()
    setup_logging(args.verbose)
    
    tickers = None
    if args.tickers:
        try:
            tickers = validate_tickers(args.tickers)
        except ValidationError as e:
            logging.getLogger(__name__).error(f"Invalid tickers: {e}")
            sys.exit(2)
    
    exit_code = main(tickers=tickers, config_path=args.config)
    sys.exit(exit_code)


if __name__ == '__main__':
    cli()
