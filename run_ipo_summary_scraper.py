#!/usr/bin/env python3
"""
Complete IPO Summary Data Scraper
Scrapes year-wise IPO summary data from investorgain.com and saves to database
"""

import argparse
import sys
from datetime import datetime
from ipo_summary_scraper import IPOSummaryScraper
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ipo_summary_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the IPO summary scraper"""
    parser = argparse.ArgumentParser(description='IPO Summary Data Scraper')
    parser.add_argument(
        '--years', 
        nargs='+', 
        type=int, 
        help='Specific years to scrape (e.g., --years 2025 2024)',
        default=None
    )
    parser.add_argument(
        '--all-years', 
        action='store_true',
        help='Scrape all available years (2019-2025)'
    )
    parser.add_argument(
        '--current-year-only', 
        action='store_true',
        help='Scrape current year only'
    )
    
    args = parser.parse_args()
    
    # Determine which years to scrape
    current_year = datetime.now().year
    
    if args.current_year_only:
        years_to_scrape = [current_year]
    elif args.years:
        years_to_scrape = args.years
    elif args.all_years:
        years_to_scrape = [2025, 2024, 2023, 2022, 2021, 2020, 2019]
    else:
        # Default: scrape recent years
        years_to_scrape = [2025, 2024, 2023,2022, 2021, 2020, 2019]
    
    # Validate years
    valid_years = list(range(2019, 2026))  # 2019 to 2025
    invalid_years = [year for year in years_to_scrape if year not in valid_years]
    
    if invalid_years:
        logger.error(f"Invalid years specified: {invalid_years}")
        logger.error(f"Valid years are: {valid_years}")
        sys.exit(1)
    
    logger.info("="*60)
    logger.info("IPO SUMMARY DATA SCRAPER STARTED")
    logger.info("="*60)
    logger.info(f"Target years: {years_to_scrape}")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize scraper
    scraper = IPOSummaryScraper()
    
    try:
        # Run the scraper
        results = scraper.scrape_all_years(years_to_scrape)
        
        # Print detailed results
        print("\n" + "="*60)
        print("IPO SUMMARY SCRAPING RESULTS")
        print("="*60)
        
        total_records = 0
        for year in sorted(results.keys(), reverse=True):
            count = results[year]
            print(f"Year {year:4d}: {count:3d} records saved")
            total_records += count
        
        print("-" * 60)
        print(f"Total records saved: {total_records}")
        print("="*60)
        
        # Log completion
        logger.info(f"Scraping completed successfully!")
        logger.info(f"Total records processed: {total_records}")
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if total_records == 0:
            logger.warning("No records were saved. Please check the API or database connection.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        sys.exit(1)
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
