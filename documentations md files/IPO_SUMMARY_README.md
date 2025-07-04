# IPO Summary Data Scraper

This module provides functionality to scrape and store year-wise IPO summary data from investorgain.com.

## Features

- Fetches IPO summary data for multiple years (2019-2025)
- Processes different IPO statuses (Upcoming, Open, Closing Today, Close, Listed)
- Extracts listing prices and gains for listed IPOs
- Handles date parsing and formatting
- Prevents duplicate data insertion
- Supports both SQLite and SQL Server databases

## Files

- `ipo_summary_scraper.py` - Main scraper class and functionality
- `ipo_summary_utility.py` - Utility script for various operations
- `test_ipo_summary_scraper.py` - Test script for validation

## Database Schema

The scraper creates an `ipo_summary_data` table with the following structure:

```sql
CREATE TABLE ipo_summary_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    ipo_id TEXT NOT NULL,
    ipo_name TEXT NOT NULL,
    status TEXT,
    list_price REAL,
    list_gain TEXT,
    ipo_size TEXT,
    pe_ratio TEXT,
    ipo_price TEXT,
    lot_size TEXT,
    open_date TEXT,
    close_date TEXT,
    boa_date TEXT,
    listing_date TEXT,
    url_rewrite TEXT,
    display_order INTEGER,
    highlight_row TEXT,
    ipo_category TEXT,
    rating TEXT,
    raw_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ipo_id, year)
);
```

## Usage

### Quick Start

```python
from ipo_summary_scraper import IPOSummaryScraper

# Create scraper instance
scraper = IPOSummaryScraper()

# Scrape all years
results = scraper.scrape_all_years()

# Scrape specific years
results = scraper.scrape_all_years([2025, 2024, 2023])
```

### Using the Utility Script

```bash
# Create the database table
python ipo_summary_utility.py create-table

# Scrape all years
python ipo_summary_utility.py scrape-all

# Scrape specific year
python ipo_summary_utility.py scrape-year --year 2025

# Scrape recent years (2023-2025)
python ipo_summary_utility.py scrape-recent

# View database statistics
python ipo_summary_utility.py stats
```

### Testing

```bash
# Run test script
python test_ipo_summary_scraper.py
```

## Status Classification

The scraper classifies IPOs into the following statuses:

- **Upcoming**: IPOs that are announced but not yet open
- **Open**: IPOs currently accepting applications
- **Closing Today**: IPOs closing on the current date
- **Close**: IPOs that have closed but not yet listed
- **Listed**: IPOs that have been listed on the exchange

For listed IPOs, the scraper extracts:
- `list_price`: The listing price
- `list_gain`: The gain/loss percentage

## API Endpoints

The scraper uses the following API endpoints:

- 2023-2025: `https://webnodejs.investorgain.com/cloud/report/data-read/394/1/7/{year}/2025-26/0/all?search=&v=22-55`
- 2019-2022: `https://webnodejs.investorgain.com/cloud/report/data-read/394/1/7/{year}/2025-26/0/all?search=&v=23-18`

## Expected Record Counts

Based on the API documentation:
- 2025: 141 records
- 2024: 337 records  
- 2023: 244 records
- 2022: 151 records
- 2021: 121 records
- 2020: 36 records
- 2019: 6 records

## Data Processing

The scraper performs the following data processing:

1. **Status Extraction**: Parses HTML status badges to determine IPO status
2. **Date Parsing**: Converts date strings like "3-Jul-25" to "2025-07-03"
3. **Text Cleaning**: Removes HTML entities and extra whitespace
4. **Duplicate Prevention**: Uses unique constraints to prevent duplicate entries
5. **JSON Storage**: Stores raw API response for future reference

## Error Handling

The scraper includes comprehensive error handling:
- Network timeout and retry logic
- JSON parsing error handling
- Database connection error handling
- Individual record processing error handling
- Detailed logging for debugging

## Configuration

The scraper uses configuration from `config.py`:
- Database settings (SQLite/SQL Server)
- API URLs and headers
- Expected record counts

## Dependencies

- requests
- json
- re
- datetime
- logging
- sqlite3/pyodbc (for database connectivity)

## Notes

- The scraper respects rate limits and includes appropriate delays
- All dates are stored in YYYY-MM-DD format
- Raw API responses are preserved in the `raw_data` field
- The scraper can be run multiple times safely (idempotent)
- Existing records are updated rather than duplicated
