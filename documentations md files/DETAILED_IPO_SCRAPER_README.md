# Detailed IPO Data Scraper Documentation

## Overview
This comprehensive IPO detail scraper fetches in-depth data for all IPO IDs collected in the summary table. It scrapes detailed information from investorgain.com and saves it to the master IPO table.

## Features
- ✅ Scrapes detailed IPO data for all collected IPO IDs (1000+ IPOs from 2019-2025)
- ✅ Prevents duplicate scraping with intelligent skip logic
- ✅ Supports year filtering and batch processing
- ✅ Comprehensive error handling and logging
- ✅ Progress tracking and statistics
- ✅ Database viewer for analysis

## Database Structure
The detailed IPO data is stored in the `ipo_master_data` table with the following key fields:

### Basic Information
- `ipo_id` - Unique IPO identifier
- `company_full_name_scraped` - Full company name
- `ipo_category` - IPO category (Mainline/SME)
- `detail_url` - URL of the detailed IPO page
- `scraping_date` - When the data was scraped

### IPO Details
- `issue_price_band` - Price band of the IPO
- `issue_size_cr` - Issue size in crores
- `shares_per_lot` - Number of shares per lot
- `min_order_quantity` - Minimum order quantity

### Important Dates
- `ipo_open_date` - IPO opening date
- `ipo_close_date` - IPO closing date
- `listing_date` - Listing date
- `basis_of_allotment_date` - Basis of allotment date

### Additional Information
- `about_company_text` - Company description
- `ipo_strengths_json` - IPO strengths (stored as JSON)
- `ipo_objectives_json` - IPO objectives (stored as JSON)
- `contact_company_address_json` - Contact information
- `company_logo_url` - Company logo URL
- `local_logo_path` - Local logo file path

## Usage

### 1. Quick Start (Interactive Mode)
```bash
python run_detailed_ipo_scraper.py
```

This will show you an interactive menu:
```
1. Scrape ALL IPO detailed data (from all years)
2. Scrape specific year
3. Test mode (scrape 5 IPOs only)
4. Scrape recent year (2024-2025)
```

### 2. Command Line Usage
```bash
# Test mode - scrape 5 IPOs only
python detailed_ipo_scraper.py --test

# Scrape specific year
python detailed_ipo_scraper.py --year 2024

# Scrape with limit
python detailed_ipo_scraper.py --limit 50

# Re-scrape existing records (don't skip)
python detailed_ipo_scraper.py --year 2025 --no-skip

# Scrape all IPOs (use with caution - 1000+ IPOs)
python detailed_ipo_scraper.py
```

### 3. View Database
```bash
# Interactive database viewer
python view_detailed_ipo_database.py

# Quick stats
python view_detailed_ipo_database.py
# Then choose option 1 for statistics
```

## Scraping Flow

### Data Sources
The scraper uses IPO IDs from the `ipo_summary_data` table and scrapes detailed information from:
- https://www.investorgain.com/ipo/[ipo-name]/[ipo-id]/

### Extraction Process
1. **Company Information**: Name, logo, about text
2. **IPO Details**: Price band, size, lot size, dates
3. **Strengths & Objectives**: Key highlights and use of funds
4. **Contact Information**: Company address, registrar, lead manager
5. **Additional Data**: Last updated date, PDF URLs

### Data Processing
- HTML parsing using BeautifulSoup
- Data normalization and cleaning
- JSON serialization for complex data
- Local logo downloading and storage

## Performance & Optimization

### Intelligent Skipping
- By default, skips IPOs that already have detailed data
- Use `--no-skip` to force re-scraping
- Prevents unnecessary API calls

### Rate Limiting
- Random delays between requests (1-3 seconds)
- Prevents overwhelming the server
- Maintains scraping stability

### Progress Tracking
- Real-time progress updates every 10 IPOs
- Comprehensive final statistics
- Error tracking and reporting

## Example Output

### Scraping Progress
```
2025-07-05 00:43:19,055 - INFO - Processing 1/1000: IPO ID 1317
2025-07-05 00:43:19,820 - INFO - Scraping IPO ID: 1317 from URL: https://www.investorgain.com/ipo/anthem-biosciences-ipo/1317/
2025-07-05 00:43:54,113 - INFO - Successfully processed IPO ID: 1317
```

### Final Statistics
```
============================================================
SCRAPING COMPLETED
Total processed: 1000
Successfully scraped: 950
Skipped (already exists): 45
Errors: 5
============================================================
```

### Database Statistics
```
📊 Total detailed records: 950
📈 Records by category:
------------------------------
Mainline: 600 records
SME: 350 records
```

## Error Handling

### Common Issues
1. **Network Errors**: Automatic retry with backoff
2. **Data Parsing Errors**: Logged but don't stop the process
3. **Database Errors**: Rollback and continue with next IPO

### Logging
- Comprehensive logging to `detailed_ipo_scraper.log`
- Console output for real-time monitoring
- Error categorization and reporting

## Data Validation

### Quality Checks
- Validates required fields before saving
- Handles missing or malformed data gracefully
- Preserves original data in raw format

### Deduplication
- Uses IPO ID as unique identifier
- Updates existing records on re-scrape
- Maintains data integrity

## Recommendations

### For Large Scale Scraping
1. **Start with Test Mode**: Always test with `--test` first
2. **Year-wise Processing**: Process one year at a time
3. **Monitor Logs**: Watch for errors and adjust as needed
4. **Use Skip Logic**: Let the system skip existing records

### For Maintenance
1. **Regular Updates**: Run monthly to get new IPO data
2. **Data Validation**: Periodically check data quality
3. **Backup Database**: Regular backups of the SQLite file

## Current Status
- ✅ **Ready for Production**: Fully tested and validated
- ✅ **1000+ IPOs Available**: Complete dataset from 2019-2025
- ✅ **Intelligent Processing**: Skip existing, handle errors
- ✅ **Comprehensive Logging**: Full audit trail

## Next Steps
1. Run in test mode to verify setup
2. Choose your scraping strategy (year-wise or all)
3. Monitor progress and logs
4. Use the database viewer to explore data
5. Integrate with your analysis workflows

The detailed IPO scraper is now ready to process all your IPO data efficiently and reliably!
