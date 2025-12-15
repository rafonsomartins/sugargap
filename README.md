# Python Market Data Scripts

This directory contains Python scripts for fetching market data and updating the Supabase database.

## Scripts

### 1. `update_exchange_rate.py`
Fetches EUR/USD exchange rate from Alpha Vantage API and updates Supabase.

**Features:**
- Fetches real-time EUR/USD exchange rate from Alpha Vantage
- Updates `exchangerate` table in Supabase
- Comprehensive error handling and logging

### 2. `update_contracts.py`
Fetches SUGAR11 futures prices from BarChart API and updates Supabase.

**Features:**
- Automatically calculates which 3 contracts to fetch based on current date
- Uses bc-utils library for BarChart API access
- Updates `contracts` table in Supabase
- Comprehensive error handling and logging

## Contract Logic

The script automatically determines which 3 futures contracts to fetch based on the current date:

- **January-February**: SBH{YY}, SBK{YY}, SBN{YY} (current year)
- **March-April**: SBK{YY}, SBN{YY}, SBV{YY} (current year)
- **May-June**: SBN{YY}, SBV{YY}, SBH{YY+1} (current + next year)
- **July-September**: SBV{YY}, SBH{YY+1}, SBK{YY+1} (next year contracts)
- **October-December**: SBH{YY+1}, SBK{YY+1}, SBN{YY+1} (next year)

Where:
- H = March, K = May, N = July, V = October
- YY = Two-digit year (e.g., 25 for 2025)

## Setup

### 1. Install Dependencies
```bash
cd python
pip install -r requirements.txt
```

### 2. Clone bc-utils Repository
```bash
# Clone the bc-utils repository to the current directory
git clone https://github.com/your-username/bc-utils.git
```

**Note:** For GitHub Actions, the bc-utils repo is cloned automatically during the workflow.

### 3. Environment Variables
Create a `.env` file in the project root with:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here

# Alpha Vantage API
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# BarChart API
BARCHART_USERNAME=your_username
BARCHART_PASSWORD=your_password
```

## Usage

### Manual Execution

**Update Exchange Rate:**
```bash
cd python
python update_exchange_rate.py
```

**Update Contracts:**
```bash
cd python
python update_contracts.py
```

### GitHub Actions (Automated)

The scripts run automatically via GitHub Actions:
- **Exchange Rate**: Every hour
- **Contracts**: Daily at 18:30 UTC

#### Setting up GitHub Secrets

In your GitHub repository, go to Settings → Secrets and variables → Actions, and add:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `ALPHA_VANTAGE_API_KEY`
- `BARCHART_USERNAME`
- `BARCHART_PASSWORD`

## Database Schema

The scripts expect these Supabase tables:

### `contracts` table:
- `contract_name_1` (string): First contract symbol (e.g., 'SBH26')
- `contract_1` (number): First contract price
- `contract_name_2` (string): Second contract symbol
- `contract_2` (number): Second contract price
- `contract_name_3` (string): Third contract symbol
- `contract_3` (number): Third contract price
- `timestamp` (timestamp): When data was recorded

### `exchangerate` table:
- `exchange` (number): EUR/USD exchange rate
- `timestamp` (timestamp): When rate was recorded

## Logging

Both scripts provide detailed logging:
- Info level: Normal operations and successful updates
- Warning level: Non-critical issues (e.g., using fallback data)
- Error level: Critical failures that prevent updates

## Error Handling

- **API Failures**: Scripts will log errors and exit with non-zero status
- **Database Failures**: Connection and insertion errors are handled gracefully
- **Missing Credentials**: Scripts validate all required environment variables
- **Data Validation**: Prices and rates are validated before database insertion

## Troubleshooting

1. **Import Error for bc-utils**: Ensure bc-utils is cloned to the parent directory
2. **Supabase Connection**: Verify SUPABASE_URL and SUPABASE_ANON_KEY are correct
3. **API Rate Limits**: Alpha Vantage free tier has rate limits; consider upgrading if needed
4. **BarChart Authentication**: Ensure credentials are valid and account has API access
