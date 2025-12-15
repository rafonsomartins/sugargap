#!/usr/bin/env python3
"""
Exchange Rate Updater - Fetches EUR/USD from Alpha Vantage API
Updates Supabase database with current exchange rate
"""

import os
import sys
import requests
import logging
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Create Supabase client with service role key for insertions"""
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_key:
        logger.error("Supabase credentials not found in environment variables")
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    
    try:
        # Create client with explicit parameters only
        return create_client(
            supabase_url=url,
            supabase_key=service_key
        )
    except TypeError as e:
        # Fallback for older versions
        logger.warning(f"TypeError creating client, trying fallback: {e}")
        return create_client(url, service_key)

def fetch_exchange_rate() -> float:
    """Fetch EUR/USD exchange rate from Alpha Vantage API"""
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        logger.error("Alpha Vantage API key not found in environment variables")
        raise ValueError("Missing ALPHA_VANTAGE_API_KEY")
    
    try:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey={api_key}"
        
        logger.info("Fetching EUR/USD exchange rate from Alpha Vantage...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'Realtime Currency Exchange Rate' in data:
            rate_info = data['Realtime Currency Exchange Rate']
            rate = float(rate_info['5. Exchange Rate'])
            last_refreshed = rate_info['6. Last Refreshed']
            
            logger.info(f"✅ EUR/USD rate: {rate} (last refreshed: {last_refreshed})")
            return rate
        else:
            logger.error(f"Unexpected API response: {data}")
            raise ValueError("Invalid response from Alpha Vantage API")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch exchange rate: {e}")
        raise
    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse exchange rate: {e}")
        raise

def update_supabase_exchange_rate(supabase: Client, rate: float) -> None:
    """Update Supabase database with new exchange rate"""
    try:
        # Insert new exchange rate (table name should match your schema)
        result = supabase.table('exchangerate').insert({
            'exchange': rate,
            'timestamp': datetime.now().isoformat()
        }).execute()
        
        if result.data:
            logger.info(f"✅ Exchange rate updated in Supabase: {rate}")
        else:
            logger.error("Failed to insert exchange rate into Supabase")
            
    except Exception as e:
        logger.error(f"Failed to update Supabase: {e}")
        raise

def main():
    """Main function"""
    try:
        logger.info("🔄 Starting EUR/USD exchange rate update...")
        
        # Fetch exchange rate
        rate = fetch_exchange_rate()
        
        # Update Supabase database
        supabase = get_supabase_client()
        update_supabase_exchange_rate(supabase, rate)
        
        logger.info("🎉 Exchange rate update completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Exchange rate update failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
