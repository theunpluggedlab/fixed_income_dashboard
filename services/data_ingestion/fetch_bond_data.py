import os
from datetime import datetime

import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
from loguru import logger

# Set up series dictionaries for data fetching
treasury_series = {
    'DGS1MO': '1-Month Treasury',
    'DGS3MO': '3-Month Treasury',
    'DGS6MO': '6-Month Treasury',
    'DGS1': '1-Year Treasury',
    'DGS2': '2-Year Treasury',
    'DGS5': '5-Year Treasury',
    'DGS7': '7-Year Treasury',
    'DGS10': '10-Year Treasury',
    'DGS20': '20-Year Treasury',
    'DGS30': '30-Year Treasury',
    'T10Y2Y': '10Y-2Y Spread',
}

etf_series = {
    'TLT': 'iShares 20+ Year Treasury Bond ETF',
    'LQD': 'iShares iBoxx $ Inv Grade Corporate Bond ETF',
}

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Fetch data and save as Parquet
start_date = '2000-01-01'  # Adjust as needed
end_date = datetime.today().strftime('%Y-%m-%d')
logger.info(
    f'Start date for all series is defined as: {start_date}. The end time is {end_date}.'
)

# Fetch Treasury and Spread data natively using pandas_datareader (no FRED API Key needed)
for series_id, name in treasury_series.items():
    logger.info(f'Fetching {name} ({series_id}) from FRED...')
    try:
        # Fetch series
        df = web.DataReader(series_id, 'fred', start_date, end_date)
        df.index.name = 'date'
        df.rename(columns={series_id: 'yield'}, inplace=True)

        # Save each series to individual Parquet file
        file_path = f'data/{series_id.lower()}.parquet'
        df.to_parquet(file_path)

        logger.success(f'Saved to {file_path}')

    except Exception as e:
        logger.error(f'Error fetching {series_id}: {e}')

# Fetch ETF prices using yfinance
for series_id, name in etf_series.items():
    logger.info(f'Fetching {name} ({series_id}) from Yahoo Finance...')
    try:
        ticker = yf.Ticker(series_id)
        df_hist = ticker.history(start=start_date, end=end_date)
        
        if not df_hist.empty:
            # Drop timezone for parquet compatibility
            df_hist.index = df_hist.index.tz_localize(None)
            df_hist.index.name = 'date'
            
            # Save the Close price (rename to price for clarity)
            df = df_hist[['Close']].rename(columns={'Close': 'price'})
            
            file_path = f'data/{series_id.lower()}.parquet'
            df.to_parquet(file_path)
            
            logger.success(f'Saved to {file_path}')
        else:
            logger.warning(f'No data found for {series_id}')
            
    except Exception as e:
        logger.error(f'Error fetching {series_id}: {e}')

logger.info('Data fetch complete!')
