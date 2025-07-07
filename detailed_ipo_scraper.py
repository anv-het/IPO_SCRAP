#!/usr/bin/env python3
"""
Comprehensive IPO Detail Scraper
This script fetches detailed IPO data for all IPO IDs collected in the summary table.
It scrapes from investorgain.com and saves to the master IPO table.
"""

import re
import sys
import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from scrapers.ipo_data_scrapers import (
    extract_company_name_and_logo,
    extract_company_about,
    extract_ipo_important_dates,
    extract_ipo_main_details_table,
    extract_ipo_strengths,
    extract_ipo_objectives,
    extract_contact_sections,
    extract_last_updated,
    scrape_ipo_lots_table,
    scrape_and_format_financial_data,
    scrape_peer_comparison,
    parse_ipo_share_allocation,
    fetch_gmp_data_for_ipo,
    parse_gmp_api_data,
    fetch_ipo_subscription_data,
    parse_ipo_bidding_data_json
)
from utils import make_robust_request, clean_text
from config import BASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('detailed_ipo_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DetailedIPOScraper:
    """Scraper for detailed IPO data from investorgain.com"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.base_url = BASE_URL
        self.scraped_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
    def connect_database(self):
        """Connect to the database"""
        self.db_manager.connect()
        if not self.db_manager.conn:
            logger.error("Failed to connect to database")
            return False
        return True
    
    def close_database(self):
        """Close database connection"""
        if self.db_manager:
            self.db_manager.close()
    
    def get_ipo_summary_data(self, ipo_id: str) -> Dict:
        """Get IPO summary data for a specific IPO ID"""
        try:
            query = """
                SELECT ipo_name, ipo_category, ipo_size, pe_ratio, ipo_price, lot_size,
                       open_date, close_date, boa_date, listing_date, url_rewrite
                FROM ipo_summary_data 
                WHERE ipo_id = ? 
                LIMIT 1
            """
            self.db_manager.cursor.execute(query, (ipo_id,))
            result = self.db_manager.cursor.fetchone()

            print(f"Fetching summary data for IPO ID: {ipo_id}")
            # print(f"Query executed: {query}")
            # print(f"Result: {result}")
            
            if result:
                return {
                    'company_short_name_api': result[0],
                    'ipo_category': result[1], 
                    'issue_size_cr': result[2],
                    'pe_ratio': result[3],
                    'ipo_price': result[4],
                    'shares_per_lot': result[5],
                    'ipo_open_date': result[6],
                    'ipo_close_date': result[7],
                    'basis_of_allotment_date': result[8],
                    'listing_date': result[9],
                    'url_rewrite': result[10]
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting summary data for IPO ID {ipo_id}: {e}")
            return {}
    
    def get_ipo_ids_from_summary(self, year_filter: Optional[int] = None, limit: Optional[int] = None) -> List[Tuple[str, str]]:
        """
        Get IPO IDs and URLs from the summary table
        Returns list of tuples (ipo_id, url_rewrite)
        """
        try:
            if year_filter:
                query = "SELECT ipo_id, url_rewrite FROM ipo_summary_data WHERE year = ? AND ipo_id IS NOT NULL AND url_rewrite IS NOT NULL"
                params = (year_filter,)
            else:
                query = "SELECT ipo_id, url_rewrite FROM ipo_summary_data WHERE ipo_id IS NOT NULL AND url_rewrite IS NOT NULL"
                params = ()
            
            if limit:
                query += f" LIMIT {limit}"
                
            self.db_manager.cursor.execute(query, params)
            results = self.db_manager.cursor.fetchall()
            
            logger.info(f"Found {len(results)} IPO IDs to process")
            return [(str(row[0]), str(row[1])) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting IPO IDs from summary table: {e}")
            return []
    
    def check_if_detailed_data_exists(self, ipo_id: str) -> bool:
        """Check if detailed data already exists for this IPO ID"""
        try:
            self.db_manager.cursor.execute(
                "SELECT COUNT(*) FROM ipo_master_data WHERE ipo_id = ?",
                (ipo_id,)
            )
            count = self.db_manager.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logger.error(f"Error checking existing data for IPO ID {ipo_id}: {e}")
            return False
    
    def scrape_detailed_ipo_data(self, ipo_id: str, url_rewrite: str) -> Optional[Dict]:
        """
        Scrape detailed IPO data for a specific IPO ID
        """
        try:
            # Construct the full URL
            if url_rewrite.startswith('/'):
                detail_url = f"{self.base_url}{url_rewrite}"
            else:
                detail_url = f"{self.base_url}/{url_rewrite}"
            
            logger.info(f"Scraping IPO ID: {ipo_id} from URL: {detail_url}")
            
            # Make request to get the page content
            response_content = make_robust_request(detail_url)
            if not response_content:
                logger.error(f"Failed to fetch content for IPO ID: {ipo_id}")
                return None
            
            # Parse the HTML content
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response_content, 'html.parser')
            
            # Extract all the detailed data
            ipo_data = {
                'ipo_id': ipo_id,
                'detail_url': detail_url,
                'scraping_date': datetime.now().isoformat()
            }
            
            # Get summary data from the database to fill missing fields
            summary_data = self.get_ipo_summary_data(ipo_id)
            if summary_data:
                ipo_data.update(summary_data)
                logger.info(f"Updated IPO data with summary info for IPO ID: {ipo_id}")
            
            # Extract company name and logo
            company_data = extract_company_name_and_logo(soup, ipo_id)
            ipo_data.update(company_data)
            
            # Extract company about
            ipo_data['about_company_text'] = extract_company_about(soup)
            
            # Extract basic IPO info from main details table (includes issue_type)
            basic_info = extract_ipo_main_details_table(soup)
            print(f"basicinfo length: {len(basic_info)}")
            print(f"basic_info: {basic_info}")
            ipo_data.update(basic_info)
            
            # Extract IPO dates
            dates_info = extract_ipo_important_dates(soup)
            ipo_data.update(dates_info)
            
            # 1. Extract IPO Lots data (shares_per_lot, min_order_quantity, issue_price_band, etc.)
            lots_data = scrape_ipo_lots_table(soup)
            if lots_data:
                ipo_data.update(lots_data)
                logger.info(f"Extracted lots data for IPO ID: {ipo_id}")
            
            # 2. Extract Company Financial data
            financial_data = scrape_and_format_financial_data(soup)
            if financial_data:
                ipo_data['company_financials_json'] = json.dumps(financial_data, ensure_ascii=False)
                logger.info(f"Extracted financial data for IPO ID: {ipo_id}")
            
            # 3. Extract Peer Comparison data
            peer_data = scrape_peer_comparison(soup)
            if peer_data:
                ipo_data['peer_comparison_json'] = json.dumps(peer_data, ensure_ascii=False)
                logger.info(f"Extracted peer comparison data for IPO ID: {ipo_id}")
            
            # Extract strengths and objectives
            ipo_data['ipo_strengths_json'] = extract_ipo_strengths(soup)
            ipo_data['ipo_objectives_json'] = extract_ipo_objectives(soup)
            
            # Extract contact information
            contact_info = extract_contact_sections(soup)
            ipo_data.update(contact_info)
            
            # Extract last updated info
            last_updated = extract_last_updated(soup)
            if last_updated:
                ipo_data['last_updated_on_page'] = last_updated
            
            # 4. Extract GMP data from API
            gmp_data = self.extract_gmp_data(ipo_id)
            if gmp_data:
                ipo_data.update(gmp_data)
                logger.info(f"Extracted GMP data for IPO ID: {ipo_id}")
            
            # 5. Extract subscription data and retail quota
            subscription_data = self.extract_subscription_data(ipo_id)
            if subscription_data:
                ipo_data.update(subscription_data)
                logger.info(f"Extracted subscription data for IPO ID: {ipo_id}")
            
            # Extract additional details
            additional_details = self.extract_additional_details(soup, ipo_id)
            ipo_data.update(additional_details)
            
            logger.info(f"Successfully scraped detailed data for IPO ID: {ipo_id}")
            return ipo_data
            
        except Exception as e:
            logger.error(f"Error scraping detailed data for IPO ID {ipo_id}: {e}")
            return None
    
    def extract_gmp_data(self, ipo_id: str) -> Dict:
        """Extract GMP data using the API for a specific IPO ID"""
        gmp_data = {
            'gmp_latest': 'N/A',
            'estimated_listing_price': 'N/A',
            'gmp_comments': 'N/A',
            'subject_to_sauda': 'N/A'
        }
        
        try:
            # Fetch GMP data from API
            api_gmp_data = fetch_gmp_data_for_ipo(ipo_id)
            
            if api_gmp_data and api_gmp_data.get("msg") == 1:
                # Parse the GMP data
                ipo_gmp_data = api_gmp_data.get("ipoGmpData", [])
                parsed_gmp_data = parse_gmp_api_data(ipo_gmp_data)
                
                if parsed_gmp_data:
                    gmp_data.update(parsed_gmp_data)
                    logger.info(f"Successfully extracted GMP data from API for IPO ID: {ipo_id}")
            
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error extracting GMP data for IPO ID {ipo_id}: {e}")
            return gmp_data
    
    def extract_subscription_data(self, ipo_id: str) -> Dict:
        """Extract subscription data and retail quota for a specific IPO ID"""
        subscription_data = {
            'retail_quota': 'N/A'
        }
        
        try:
            # Fetch subscription data from API
            api_subscription_data = fetch_ipo_subscription_data(ipo_id)
            
            if api_subscription_data and api_subscription_data.get("msg") == 1:
                # Check for share allocation data
                allocation_html = api_subscription_data.get("listItemsHTML", "")
                if allocation_html:
                    allocation_data, retail_quota = parse_ipo_share_allocation(allocation_html)
                    if retail_quota:
                        subscription_data['retail_quota'] = retail_quota
                        logger.info(f"Extracted retail quota: {retail_quota} for IPO ID: {ipo_id}")
            
            return subscription_data
            
        except Exception as e:
            logger.error(f"Error extracting subscription data for IPO ID {ipo_id}: {e}")
            return subscription_data
    
    def extract_table_data(self, table) -> Optional[Dict]:
        """Extract data from HTML table"""
        try:
            if not table:
                return None
            
            headers = []
            rows = []
            
            # Extract headers
            header_row = table.find('tr')
            if header_row:
                headers = [clean_text(th.get_text()) for th in header_row.find_all(['th', 'td'])]
            
            # Extract data rows
            for row in table.find_all('tr')[1:]:  # Skip header row
                row_data = [clean_text(td.get_text()) for td in row.find_all(['td', 'th'])]
                if row_data:
                    rows.append(row_data)
            
            if headers and rows:
                return {
                    'headers': headers,
                    'rows': rows
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return None
    
    def extract_additional_details(self, soup, ipo_id: str) -> Dict:
        """
        Extract additional IPO details using structured data first (main table),
        then fallback to regex where necessary.
        """
        additional_data = {
            'min_order_quantity': 'N/A',
            'fresh_issue_amount': 'N/A',
            'face_value': 'N/A',
            'promoter_holding_pre_ipo': 'N/A',
            'promoter_holding_post_ipo': 'N/A',
            'listing_at': 'N/A',
            'retail_quota': 'N/A',
            'issue_type': 'N/A'
        }

        try:
            # Step 1: Get main details table
            basic_info = extract_ipo_main_details_table(soup)
            print(f"✅ Extracted {len(basic_info)} main table fields for IPO ID {ipo_id}")
            print(f"→ Main Table Data: {basic_info}")

            # Step 2: Fill in from main table
            keys_to_copy = [
                'fresh_issue_amount', 'face_value', 'promoter_holding_pre_ipo',
                'promoter_holding_post_ipo', 'listing_at', 'retail_quota', 'issue_type'
            ]
            for key in keys_to_copy:
                val = basic_info.get(key, 'N/A')
                if val and val != 'N/A':
                    additional_data[key] = val

            # Step 3: Regex fallback from full text
            all_text = soup.get_text(separator=' ', strip=True)

            # Issue type fix (e.g., 'Book Build IssueSME IPO Issue Size')
            if 'Issue Size' in additional_data['issue_type']:
                match = re.search(r'Issue Type[:\s]*([A-Za-z\s]+?)(?:SME|IPO|Issue Size|$)', all_text, re.IGNORECASE)
                if match:
                    cleaned_type = match.group(1).strip()
                    if cleaned_type:
                        additional_data['issue_type'] = cleaned_type

            # Face value fallback
            if additional_data['face_value'] == 'N/A':
                face_value_match = re.search(r'Face Value[:\s]*₹?(\d+)', all_text, re.IGNORECASE)
                if face_value_match:
                    additional_data['face_value'] = face_value_match.group(1).strip()

            # Fresh issue amount fallback
            if additional_data['fresh_issue_amount'] == 'N/A':
                fresh_issue_match = re.search(r'Fresh Issue[:\s]*₹?([0-9,.\s]+(?:Cr|Crore))', all_text, re.IGNORECASE)
                if fresh_issue_match:
                    additional_data['fresh_issue_amount'] = fresh_issue_match.group(1).strip()

            # Min order quantity (from Market Lot or Shares Per Lot)
            moq_match = re.search(r'(?:Market Lot|Minimum Order Quantity|Shares Per Lot)[:\s]*([0-9,]+)', all_text, re.IGNORECASE)
            if moq_match:
                additional_data['min_order_quantity'] = moq_match.group(1).strip()

            # Promoter holdings fallback
            if additional_data['promoter_holding_pre_ipo'] == 'N/A':
                promoter_pre_match = re.search(r'Promoter Holding.*?Pre.*?(\d+(?:\.\d+)?%)', all_text, re.IGNORECASE)
                if promoter_pre_match:
                    additional_data['promoter_holding_pre_ipo'] = promoter_pre_match.group(1)

            if additional_data['promoter_holding_post_ipo'] == 'N/A':
                promoter_post_match = re.search(r'Promoter Holding.*?Post.*?(\d+(?:\.\d+)?%)', all_text, re.IGNORECASE)
                if promoter_post_match:
                    additional_data['promoter_holding_post_ipo'] = promoter_post_match.group(1)

            # Retail quota fallback - normalize values like "35", "35.00", "35% of the Net Issue"
            if additional_data['retail_quota'] == 'N/A':
                retail_quota_match = re.search(
                    r'(?:Retail Quota|Retail Allocation|Retail Individual Investors).*?(?P<percent>\d+(?:\.\d+)?)(\s*%?)',
                    all_text, re.IGNORECASE
                ) 
                if retail_quota_match:
                    percent = retail_quota_match.group('percent')
                    if percent:
                        additional_data['retail_quota'] = f"{percent}%"


            # Listing exchange fallback (cleanup BSE/NSE only)
            if additional_data['listing_at'] == 'N/A':
                listing_match = re.search(r'Listing (?:at|on)[:\s]*([A-Za-z,\s]+)', all_text, re.IGNORECASE)
                if listing_match:
                    raw = listing_match.group(1).strip().upper()
                    exchanges = re.findall(r'(BSE|NSE)', raw)
                    if exchanges:
                        additional_data['listing_at'] = ', '.join(sorted(set(exchanges)))

            print(f"📦 Final Additional Data for IPO ID {ipo_id}: {additional_data}")
            return additional_data

        except Exception as e:
            logger.error(f"❌ Error extracting additional details for IPO ID {ipo_id}: {e}")
            return additional_data
    
    def save_detailed_data(self, ipo_data: Dict) -> bool:
        """Save detailed IPO data to the database"""
        try:
            # Ensure the master table exists
            self.db_manager.create_table()
            
            # Insert or update the data
            success = self.db_manager.insert_or_update_ipo_data(ipo_data)
            
            if success:
                logger.info(f"Successfully saved detailed data for IPO ID: {ipo_data['ipo_id']}")
                return True
            else:
                logger.error(f"Failed to save detailed data for IPO ID: {ipo_data['ipo_id']}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving detailed data: {e}")
            return False
    
    def scrape_all_detailed_data(self, year_filter: Optional[int] = None, limit: Optional[int] = None, skip_existing: bool = True):
        """
        Scrape detailed data for all IPO IDs in the summary table
        """
        logger.info("Starting comprehensive IPO detailed data scraping")
        logger.info(f"Year filter: {year_filter}, Limit: {limit}, Skip existing: {skip_existing}")
        
        # Get all IPO IDs from summary table
        ipo_ids = self.get_ipo_ids_from_summary(year_filter, limit)
        
        if not ipo_ids:
            logger.warning("No IPO IDs found to process")
            return
        
        logger.info(f"Processing {len(ipo_ids)} IPO IDs")
        
        for i, (ipo_id, url_rewrite) in enumerate(ipo_ids, 1):
            try:
                logger.info(f"Processing {i}/{len(ipo_ids)}: IPO ID {ipo_id}")
                
                # Check if detailed data already exists
                if skip_existing and self.check_if_detailed_data_exists(ipo_id):
                    logger.info(f"Detailed data already exists for IPO ID: {ipo_id}, skipping...")
                    self.skipped_count += 1
                    continue
                
                # Scrape detailed data
                detailed_data = self.scrape_detailed_ipo_data(ipo_id, url_rewrite)
                
                if detailed_data:
                    # Save to database
                    if self.save_detailed_data(detailed_data):
                        self.scraped_count += 1
                        logger.info(f"Successfully processed IPO ID: {ipo_id}")
                    else:
                        self.error_count += 1
                        logger.error(f"Failed to save IPO ID: {ipo_id}")
                else:
                    self.error_count += 1
                    logger.error(f"Failed to scrape IPO ID: {ipo_id}")
                
                # Add random delay to avoid overwhelming the server
                delay = random.uniform(1, 3)
                time.sleep(delay)
                
                # Progress update every 10 items
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(ipo_ids)} processed, {self.scraped_count} scraped, {self.skipped_count} skipped, {self.error_count} errors")
                
            except Exception as e:
                logger.error(f"Error processing IPO ID {ipo_id}: {e}")
                self.error_count += 1
                continue
        
        # Final summary
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETED")
        logger.info(f"Total processed: {len(ipo_ids)}")
        logger.info(f"Successfully scraped: {self.scraped_count}")
        logger.info(f"Skipped (already exists): {self.skipped_count}")
        logger.info(f"Errors: {self.error_count}")
        logger.info("=" * 60)


def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape detailed IPO data for all IPO IDs in summary table")
    parser.add_argument('--year', type=int, help='Filter by specific year (optional)')
    parser.add_argument('--limit', type=int, help='Limit number of IPOs to process (optional)')
    parser.add_argument('--no-skip', action='store_true', help='Do not skip existing records (re-scrape all)')
    parser.add_argument('--test', action='store_true', help='Test mode - process only 5 IPOs')
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = DetailedIPOScraper()
    
    try:
        # Connect to database
        if not scraper.connect_database():
            logger.error("Failed to connect to database. Exiting.")
            return
        
        # Set parameters
        year_filter = args.year
        limit = 5 if args.test else args.limit
        skip_existing = not args.no_skip
        
        # Run scraping
        scraper.scrape_all_detailed_data(year_filter, limit, skip_existing)
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    finally:
        # Close database connection
        scraper.close_database()


if __name__ == "__main__":
    main()
