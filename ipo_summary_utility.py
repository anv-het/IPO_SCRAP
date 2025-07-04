"""
IPO Summary Scraper Utility
This script provides various utility functions for managing IPO summary data.
"""

import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ipo_summary_scraper import IPOSummaryScraper, IPOSummaryDatabaseManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_all_years():
    """Scrape all years"""
    logger.info("Starting full scrape for all years")
    scraper = IPOSummaryScraper()
    results = scraper.scrape_all_years()
    
    print("\nFull Scrape Results:")
    print("=" * 40)
    total = 0
    for year, count in sorted(results.items()):
        print(f"Year {year}: {count} records")
        total += count
    print(f"\nTotal records saved: {total}")

def scrape_specific_year(year):
    """Scrape a specific year"""
    logger.info(f"Starting scrape for year {year}")
    scraper = IPOSummaryScraper()
    results = scraper.scrape_all_years([year])
    
    print(f"\nScrape Results for {year}:")
    print("=" * 30)
    print(f"Records saved: {results.get(year, 0)}")

def scrape_recent_years():
    """Scrape recent years (2023-2025)"""
    logger.info("Starting scrape for recent years (2023-2025)")
    scraper = IPOSummaryScraper()
    results = scraper.scrape_all_years([2025, 2024, 2023])
    
    print("\nRecent Years Scrape Results:")
    print("=" * 35)
    total = 0
    for year in [2025, 2024, 2023]:
        count = results.get(year, 0)
        print(f"Year {year}: {count} records")
        total += count
    print(f"\nTotal records saved: {total}")

def view_database_stats():
    """View database statistics"""
    logger.info("Retrieving database statistics")
    
    db_manager = IPOSummaryDatabaseManager()
    db_manager.connect()
    
    if not db_manager.conn:
        print("Failed to connect to database")
        return
    
    try:
        # Get total records
        db_manager.cursor.execute("SELECT COUNT(*) FROM ipo_summary_data")
        total_records = db_manager.cursor.fetchone()[0]
        
        # Get records by year
        db_manager.cursor.execute("""
            SELECT year, COUNT(*) as count 
            FROM ipo_summary_data 
            GROUP BY year 
            ORDER BY year DESC
        """)
        year_stats = db_manager.cursor.fetchall()
        
        # Get records by status
        db_manager.cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM ipo_summary_data 
            GROUP BY status 
            ORDER BY count DESC
        """)
        status_stats = db_manager.cursor.fetchall()
        
        print("\nDatabase Statistics:")
        print("=" * 40)
        print(f"Total IPO Records: {total_records}")
        
        print("\nRecords by Year:")
        print("-" * 20)
        for year, count in year_stats:
            print(f"  {year}: {count}")
        
        print("\nRecords by Status:")
        print("-" * 20)
        for status, count in status_stats:
            status_name = status if status else "Unknown"
            print(f"  {status_name}: {count}")
        
    except Exception as e:
        logger.error(f"Error retrieving database stats: {e}")
    finally:
        db_manager.close()

def create_table():
    """Create IPO summary table"""
    logger.info("Creating IPO summary table")
    
    db_manager = IPOSummaryDatabaseManager()
    db_manager.connect()
    
    if not db_manager.conn:
        print("Failed to connect to database")
        return
    
    try:
        db_manager.create_ipo_summary_table()
        print("✅ IPO summary table created successfully")
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        print("❌ Failed to create table")
    finally:
        db_manager.close()

def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description="IPO Summary Scraper Utility")
    parser.add_argument('action', choices=[
        'scrape-all', 'scrape-year', 'scrape-recent', 'stats', 'create-table'
    ], help='Action to perform')
    parser.add_argument('--year', type=int, help='Specific year to scrape (for scrape-year action)')
    
    args = parser.parse_args()
    
    if args.action == 'scrape-all':
        scrape_all_years()
    elif args.action == 'scrape-year':
        if not args.year:
            print("Error: --year parameter is required for scrape-year action")
            sys.exit(1)
        scrape_specific_year(args.year)
    elif args.action == 'scrape-recent':
        scrape_recent_years()
    elif args.action == 'stats':
        view_database_stats()
    elif args.action == 'create-table':
        create_table()

if __name__ == "__main__":
    main()
