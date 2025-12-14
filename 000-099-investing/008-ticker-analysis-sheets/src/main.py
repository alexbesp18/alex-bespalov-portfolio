import sys
import argparse
from typing import List
from concurrent.futures import ThreadPoolExecutor

from src.config import get_settings
from src.utils.logging import setup_logger
from src.utils.sheets import SheetManager
from src.fetchers.technicals import TwelveDataFetcher
from src.fetchers.transcripts import TranscriptFetcher
from src.llm.grok import GrokSummarizer
from src.llm.prompts import get_summarization_prompt

logger = setup_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Ticker Analysis Sheets Loader")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to sheets")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tickers to process")
    parser.add_argument("--tickers", type=str, help="Comma-separated list of tickers to check")
    args = parser.parse_args()
    
    try:
        settings = get_settings()
        logger.setLevel(settings.log_level)
    except Exception as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file or environment variables.")
        sys.exit(1)
        
    logger.info("🚀 Starting Ticker Analysis Loader")
    
    # Initialize components
    try:
        sheets = SheetManager(
            settings.google_service_account_path, 
            settings.google_sheet_name
        )
        tech_fetcher = TwelveDataFetcher(settings.twelve_data_api_key)
        transcript_fetcher = TranscriptFetcher()
        grok = GrokSummarizer(settings.grok_api_key, settings.llm_model)
    except Exception as e:
        logger.critical(f"Initialization failed: {e}")
        sys.exit(1)
        
    # Get Tickers
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
    else:
        try:
            tickers = sheets.get_tickers('Tickers') # Assuming main tab is 'Tickers'
            logger.info(f"Found {len(tickers)} tickers in sheet")
        except Exception as e:
            logger.error(f"Failed to get tickers: {e}")
            sys.exit(1)

    if args.limit > 0:
        tickers = tickers[:args.limit]
        
    # Processing Loop
    # We can do this serially or in parallel. TwelveData is 8 req/min for free, maybe higher for paid.
    # Grok also has limits. Serial is safer for now effectively, or low worker count.
    
    results_tech = []
    results_transcripts = []
    
    for ticker in tickers:
        logger.info(f"--- Processing {ticker} ---")
        
        # 1. Technicals
        tech_data = tech_fetcher.fetch_and_calculate(ticker)
        
        if tech_data.get('Status') == 'OK':
            # 1.5 Analyze Technicals (Bullish Score)
            analysis = grok.analyze_technicals(ticker, tech_data)
            tech_data.update(analysis)
        
        results_tech.append(tech_data)
        
        # 2. Transcripts
        t_data = transcript_fetcher.fetch_latest(ticker)
        if t_data.get('Status') == 'OK' and t_data.get('Full_Text'):
            # Summarize
            summary = grok.summarize(
                ticker, 
                t_data['Period'], 
                t_data['Full_Text']
            )
            # Merge
            t_data.update(summary)
            # Remove full text to save space in sheet (optional, usually we do)
            del t_data['Full_Text']
            
        results_transcripts.append(t_data)
        
    # Write results
    if not args.dry_run:
        logger.info("Writing results to Google Sheets...")
        try:
            sheets.write_tech_data('Technical_Data', results_tech)
            sheets.write_transcripts('Transcript_Summary', results_transcripts)
            logger.info("✅ Done!")
        except Exception as e:
            logger.error(f"Failed to write results: {e}")
    else:
        logger.info("Dry run complete. No data written.")

if __name__ == "__main__":
    main()
