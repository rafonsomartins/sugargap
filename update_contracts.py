#!/usr/bin/env python3
"""
Sugar Contract Updater - Fetches SUGAR11 futures from BarChart API
Updates Supabase database with current contract prices
Uses bc-utils library for BarChart API access
"""

import os
import sys
import logging
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

CONTRACT_MONTHS = [
    ("H", 3),   # March
    ("K", 5),   # May
    ("N", 7),   # July
    ("V", 10),  # October
]

# Add bc-utils to path (in same directory for GitHub Actions)
current_dir = os.path.dirname(os.path.abspath(__file__))
bc_utils_path = os.path.join(current_dir, 'bc-utils')
sys.path.insert(0, bc_utils_path)

try:
    from bcutils.bc_utils import create_bc_session, get_historical_prices_for_contract, Resolution
    from bcutils.config import CONTRACT_MAP
except ImportError as e:
    print(f"❌ Error importing bc-utils: {e}")
    print("Make sure bc-utils directory exists and is properly installed")
    sys.exit(1)

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
    
    return create_client(url, service_key)

def get_current_contract_names(reference_date: datetime | None = None):
    if reference_date is None:
        reference_date = datetime.now()

    year = reference_date.year
    month = reference_date.month

    contracts = []

    # We search current year and next year to guarantee 3 contracts
    for y in (year, year + 1):
        for code, contract_month in CONTRACT_MONTHS:
            # Skip contracts already expired this year
            if y == year and contract_month <= month:
                continue

            contracts.append(f"SB{code}{str(y)[-2:]}")

            if len(contracts) == 3:
                return contracts

    return contracts

def get_barchart_credentials():
    """Get BarChart credentials from environment"""
    username = os.getenv('BARCHART_USERNAME')
    password = os.getenv('BARCHART_PASSWORD')
    
    if not username or not password:
        logger.error("BarChart credentials not found in environment variables")
        raise ValueError("Missing BARCHART_USERNAME or BARCHART_PASSWORD")
    
    return {'barchart_username': username, 'barchart_password': password}

def fetch_contract_price(session, contract_symbol):
    """Fetch current price for a single contract"""
    try:
        logger.info(f"Fetching price for {contract_symbol}")
        
        # Get recent price data (last few days to ensure we get latest closing price)
        df = get_historical_prices_for_contract(session, contract_symbol, Resolution.Day)
        
        if df is None or df.empty:
            logger.warning(f"No data available for {contract_symbol}")
            return None
        
        # Get the most recent close price
        latest_close = df['Close'].iloc[-1]
        logger.info(f"{contract_symbol}: ${latest_close:.2f}")
        
        return float(latest_close)
        
    except Exception as e:
        logger.error(f"Error fetching price for {contract_symbol}: {e}")
        return None

def update_supabase_contracts(supabase: Client, contracts_data):
    """Update Supabase database with new contract prices"""
    try:
        if len(contracts_data) != 3:
            raise ValueError("Expected exactly 3 contract prices")
        
        # Prepare data for Supabase insertion
        contract_record = {
            'contract_name_1': contracts_data[0]['symbol'],
            'contract_1': contracts_data[0]['price'],
            'contract_name_2': contracts_data[1]['symbol'],
            'contract_2': contracts_data[1]['price'],
            'contract_name_3': contracts_data[2]['symbol'],
            'contract_3': contracts_data[2]['price'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Insert new record into contracts table
        result = supabase.table('contracts').insert(contract_record).execute()
        
        if result.data:
            logger.info("✅ Contracts updated in Supabase successfully")
            for contract in contracts_data:
                logger.info(f"   {contract['symbol']}: ${contract['price']:.2f}")
        else:
            logger.error("Failed to insert contracts into Supabase")
            
    except Exception as e:
        logger.error(f"Failed to update Supabase contracts: {e}")
        raise

def main():
    """Main function"""
    try:
        logger.info("🚀 Starting sugar contracts update...")
        
        # Get current contract symbols based on date
        contract_symbols = get_current_contract_names()
        logger.info(f"📋 Contracts to fetch: {', '.join(contract_symbols)}")
        
        # Get BarChart credentials
        credentials = get_barchart_credentials()
        
        # Create BarChart session
        logger.info("🔗 Creating BarChart session...")
        session = create_bc_session(credentials)
        
        # Fetch prices for all contracts
        contracts_data = []
        for symbol in contract_symbols:
            price = fetch_contract_price(session, symbol)
            if price is not None:
                contracts_data.append({
                    'symbol': symbol,
                    'price': price
                })
            else:
                logger.error(f"Failed to fetch price for {symbol}")
                sys.exit(1)
        
        # Validate we got all 3 prices
        if len(contracts_data) != 3:
            logger.error(f"Expected 3 contract prices, got {len(contracts_data)}")
            sys.exit(1)
        
        # Update Supabase database
        supabase = get_supabase_client()
        update_supabase_contracts(supabase, contracts_data)
        
        logger.info("🎉 Contract update completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Contract update failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
