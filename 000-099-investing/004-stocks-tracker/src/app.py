"""
Stock Tracker Application - Main Streamlit App.

Streamlit-based web interface for tracking and analyzing stock market data.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st

# Add src directory to path for Streamlit compatibility
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from api_client import StockDataClient
from calculator import StockCalculator
from config import get_stocks_config_path, logger

# Constants
REQUIRED_CONFIG_KEYS = ["stocks", "sectors"]
DEFAULT_DURATION_INDEX = 3  # "1 year"


def load_config() -> Dict[str, Any]:
    """
    Load stocks and sectors configuration from JSON file.

    Returns:
        Dictionary containing 'stocks' and 'sectors' keys.

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
        KeyError: If required keys are missing
        ValueError: If config structure is invalid
    """
    config_path = get_stocks_config_path()
    
    if not config_path.exists():
        error_msg = f"Configuration file not found: {config_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in config file {config_path}: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    
    # Validate required keys
    missing_keys = [key for key in REQUIRED_CONFIG_KEYS if key not in config]
    if missing_keys:
        error_msg = f"Missing required keys in config: {missing_keys}"
        logger.error(error_msg)
        raise KeyError(error_msg)
    
    # Validate structure
    if not isinstance(config.get("stocks"), list):
        error_msg = "Config 'stocks' must be a list"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not isinstance(config.get("sectors"), list):
        error_msg = "Config 'sectors' must be a list"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Loaded configuration with {len(config['stocks'])} stocks and {len(config['sectors'])} sectors")
    return config


def main() -> None:
    """
    Main Streamlit application entry point.
    
    Initializes the UI, loads configuration, and handles user interactions
    for stock market data analysis.
    """
    st.set_page_config(
        page_title="Stock Tracker",
        page_icon="📈",
        layout="wide"
    )

    st.title("📈 Stock Price Tracker")
    st.markdown("Track stock prices with historical data from Yahoo Finance (free API)")

    # Load configuration with error handling
    try:
        config = load_config()
    except (FileNotFoundError, ValueError, KeyError) as e:
        logger.error(f"Failed to load configuration: {e}", exc_info=True)
        st.error(f"❌ Configuration Error: {e}")
        st.info("Please ensure config/stocks.json exists and is properly formatted.")
        return
    
    stocks = config.get("stocks", [])
    sectors = config.get("sectors", [])
    
    if not stocks:
        st.warning("⚠️ No stocks configured. Please add stocks to config/stocks.json")
        return
    
    logger.info(f"Application started with {len(stocks)} stocks configured")

    # Sidebar controls
    st.sidebar.header("Settings")

    # Duration dropdown
    duration_options = ["1 month", "3 months", "6 months", "1 year", "2 years", "5 years"]
    selected_duration = st.sidebar.selectbox(
        "Select Duration",
        duration_options,
        index=DEFAULT_DURATION_INDEX
    )
    
    logger.debug(f"User selected duration: {selected_duration}")

    # Sector filter
    sector_filter = st.sidebar.multiselect(
        "Filter by Sector",
        ["All"] + sectors,
        default=["All"]
    )

    # Stock selection
    stock_symbols = [stock['symbol'] for stock in stocks]
    selected_stocks = st.sidebar.multiselect(
        "Select Stocks (leave empty for all)",
        stock_symbols,
        default=[]
    )

    # Apply filters
    filtered_stocks = stocks

    if "All" not in sector_filter and sector_filter:
        filtered_stocks = [s for s in filtered_stocks if s['sector'] in sector_filter]

    if selected_stocks:
        filtered_stocks = [s for s in filtered_stocks if s['symbol'] in selected_stocks]

    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        logger.info("User triggered data refresh")
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data Source:** Yahoo Finance (yfinance)")

    # Main content
    if not filtered_stocks:
        st.warning("No stocks match your filter criteria. Please adjust your filters.")
        return

    st.subheader(f"Showing {len(filtered_stocks)} stocks for {selected_duration}")

    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Fetch and display data
    results = []
    errors = []

    logger.info(f"Fetching data for {len(filtered_stocks)} stocks with duration {selected_duration}")

    for idx, stock in enumerate(filtered_stocks):
        # Validate stock structure
        if not isinstance(stock, dict) or "symbol" not in stock:
            error_msg = f"Invalid stock entry: {stock}"
            logger.warning(error_msg)
            errors.append(error_msg)
            continue
        
        symbol = stock.get("symbol", "").strip().upper()
        name = stock.get("name", "Unknown")
        sector = stock.get("sector", "Unknown")
        
        # Validate symbol
        if not symbol or len(symbol) > 10:  # Reasonable max length for ticker
            error_msg = f"Invalid stock symbol: {symbol}"
            logger.warning(error_msg)
            errors.append(f"{symbol}: Invalid symbol format")
            continue

        status_text.text(f"Fetching data for {symbol}...")
        progress_bar.progress((idx + 1) / len(filtered_stocks))

        # Fetch historical data
        logger.debug(f"Fetching data for {symbol} ({name})")
        hist_data = StockDataClient.get_historical_data(symbol, selected_duration)

        if hist_data is not None and not hist_data.empty:
            # Calculate metrics
            metrics = StockCalculator.calculate_metrics(hist_data)

            if metrics:
                results.append({
                    'Symbol': symbol,
                    'Name': name,
                    'Sector': sector,
                    'Start Price': metrics['start_price'],
                    'Min Price': metrics['min_price'],
                    'Max Price': metrics['max_price'],
                    'Current Price': metrics['current_price'],
                    '% of Max': metrics['current_percentile'],
                    'Position': metrics['current_percentile'],  # For thermometer (0-100)
                    'Change %': metrics['change_percent']
                })
            else:
                error_msg = f"{symbol}: Unable to calculate metrics"
                logger.warning(error_msg)
                errors.append(error_msg)
        else:
            error_msg = f"{symbol}: No data available"
            logger.warning(error_msg)
            errors.append(error_msg)

    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

    # Display errors if any
    if errors:
        with st.expander(f"⚠️ Errors ({len(errors)} stocks failed)", expanded=not results):
            for error in errors:
                st.text(error)

    # Display results
    if results:
        # Create DataFrame
        df = pd.DataFrame(results)

        # Display stock data table with proper formatting
        st.subheader("Individual Stock Performance")
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Sector": st.column_config.TextColumn("Sector", width="medium"),
                "Start Price": st.column_config.NumberColumn("Start Price", format="$%.2f"),
                "Min Price": st.column_config.NumberColumn("Min Price", format="$%.2f"),
                "Max Price": st.column_config.NumberColumn("Max Price", format="$%.2f"),
                "Current Price": st.column_config.NumberColumn("Current Price", format="$%.2f"),
                "% of Max": st.column_config.NumberColumn("% of Max", format="%.2f%%"),
                "Position": st.column_config.ProgressColumn(
                    "Price Position",
                    help="Current price position between min (0%) and max (100%)",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                ),
                "Change %": st.column_config.NumberColumn("Change %", format="%.2f%%"),
            }
        )

        # Calculate sector aggregations
        st.subheader("Sector Performance (Equal-Weighted)")

        sector_data = {}
        for result in results:
            sector = result['Sector']
            if sector not in sector_data:
                sector_data[sector] = {
                    'stocks': [],
                    'changes': [],
                    'percentiles': []
                }
            sector_data[sector]['stocks'].append(result['Symbol'])
            sector_data[sector]['changes'].append(result['Change %'])
            sector_data[sector]['percentiles'].append(result['% of Max'])

        sector_summary = []
        for sector, data in sector_data.items():
            avg_change = sum(data['changes']) / len(data['changes'])
            avg_percentile = sum(data['percentiles']) / len(data['percentiles'])
            stock_count = len(data['stocks'])
            positive_count = sum(1 for c in data['changes'] if c > 0)

            sector_summary.append({
                'Sector': sector,
                'Stock Count': stock_count,
                'Avg Change %': avg_change,
                'Avg % of Max': avg_percentile,
                'Position': avg_percentile,
                'Positive Stocks': f"{positive_count}/{stock_count}"
            })

        # Sort by average change descending
        sector_summary.sort(key=lambda x: x['Avg Change %'], reverse=True)
        sector_df = pd.DataFrame(sector_summary)

        st.dataframe(
            sector_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Sector": st.column_config.TextColumn("Sector", width="medium"),
                "Stock Count": st.column_config.NumberColumn("Stocks", format="%d"),
                "Avg Change %": st.column_config.NumberColumn("Avg Change %", format="%.2f%%"),
                "Avg % of Max": st.column_config.NumberColumn("Avg % of Max", format="%.2f%%"),
                "Position": st.column_config.ProgressColumn(
                    "Avg Position",
                    help="Average price position for sector",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                ),
                "Positive Stocks": st.column_config.TextColumn("Positive", width="small"),
            }
        )

        # Summary statistics
        st.subheader("Overall Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg_change = sum([r['Change %'] for r in results]) / len(results)
            st.metric("Average Change", f"{avg_change:+.2f}%")

        with col2:
            positive_stocks = sum([1 for r in results if r['Change %'] > 0])
            st.metric("Positive Stocks", f"{positive_stocks}/{len(results)}")

        with col3:
            avg_percentile = sum([r['% of Max'] for r in results]) / len(results)
            st.metric("Avg % of Max", f"{avg_percentile:.2f}%")

        with col4:
            st.metric("Total Sectors", len(sector_data))

        # Download option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Stock Data as CSV",
            data=csv,
            file_name=f"stock_data_{selected_duration.replace(' ', '_')}.csv",
            mime="text/csv"
        )

    else:
        st.error("Unable to fetch data for any stocks. Please check the terminal for error details or try again later.")


if __name__ == "__main__":
    main()
