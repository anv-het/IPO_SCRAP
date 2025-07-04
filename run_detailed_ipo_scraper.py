#!/usr/bin/env python3
"""
Run Detailed IPO Scraper
Easy-to-use interface for scraping detailed IPO data
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from detailed_ipo_scraper import DetailedIPOScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function with user-friendly interface"""
    print("=" * 60)
    print("DETAILED IPO DATA SCRAPER")
    print("=" * 60)
    
    # Create scraper instance
    scraper = DetailedIPOScraper()
    
    try:
        # Connect to database
        if not scraper.connect_database():
            print("❌ Failed to connect to database. Exiting.")
            return
        
        print("✅ Database connected successfully")
        
        # Get user preferences
        print("\nChoose scraping options:")
        print("1. Scrape ALL IPO detailed data (from all years)")
        print("2. Scrape specific year")
        print("3. Test mode (scrape 5 IPOs only)")
        print("4. Scrape recent year (2024-2025)")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        year_filter = None
        limit = None
        skip_existing = True
        
        if choice == "1":
            print("\n🚀 Starting to scrape ALL IPO detailed data...")
            confirm = input("This will process all 1000+ IPOs. Continue? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Operation cancelled.")
                return
        
        elif choice == "2":
            year = input("Enter year (2019-2025): ").strip()
            try:
                year_filter = int(year)
                if year_filter < 2019 or year_filter > 2025:
                    print("❌ Year must be between 2019 and 2025")
                    return
                print(f"🚀 Starting to scrape detailed data for year {year_filter}...")
            except ValueError:
                print("❌ Invalid year format")
                return
        
        elif choice == "3":
            limit = 5
            print("🧪 Test mode: Processing 5 IPOs only...")
        
        elif choice == "4":
            print("🚀 Starting to scrape recent years (2024-2025)...")
            # We'll process both years
            for year in [2024, 2025]:
                print(f"\n📅 Processing year {year}...")
                scraper.scrape_all_detailed_data(year_filter=year, limit=None, skip_existing=skip_existing)
            
            print("\n✅ Completed processing recent years")
            return
        
        else:
            print("❌ Invalid choice")
            return
        
        # Ask about skipping existing records
        if choice != "3":  # Skip this question for test mode
            skip_input = input("\nSkip IPOs that already have detailed data? (y/n, default: y): ").strip().lower()
            skip_existing = skip_input != 'n'
        
        # Run scraping
        scraper.scrape_all_detailed_data(year_filter, limit, skip_existing)
        
        print("\n✅ Scraping completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Error in main execution: {e}")
    finally:
        # Close database connection
        scraper.close_database()
        print("\n🔒 Database connection closed")


if __name__ == "__main__":
    main()
