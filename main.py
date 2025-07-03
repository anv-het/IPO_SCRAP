# main.py

import time
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import from our new structured modules
from config import BASE_URL, MAX_WORKERS, REQUEST_TIMEOUT, RETRY_ATTEMPTS, RETRY_BACKOFF_FACTOR
from utils import make_robust_request, process_issue_size_from_api, download_logo
from scrapers.ipo_data_scrapers import (
    fetch_ipo_list_from_api, extract_company_name_and_logo,
    extract_company_about, extract_ipo_important_dates, extract_ipo_main_details_table,
    scrape_ipo_lots_table, fetch_gmp_data_for_ipo, parse_gmp_api_data, parse_gmp_trend_table,
    extract_ipo_strengths, extract_ipo_objectives, fetch_ipo_subscription_data,
    parse_ipo_bidding_data_json, parse_ipo_share_allocation, parse_ipo_daywise_subscription_table,
    parse_ipo_shares_bid_amount_table, scrape_and_format_financial_data,
    scrape_peer_comparison, extract_contact_sections, extract_last_updated
)
from database.db_manager import DatabaseManager

def scrape_and_store_ipo_data():
    """
    Orchestrates the scraping of all IPO data and stores it in the database.
    """
    db_manager = DatabaseManager()
    db_manager.connect()
    if not db_manager.conn:
        print("Failed to connect to database. Exiting.")
        return

    db_manager.create_table()

    ipo_list = fetch_ipo_list_from_api()
    if not ipo_list:
        print("No IPOs fetched from API. Exiting scraping process.")
        db_manager.close()
        return

    print(f"\nStarting detailed scraping and database storage for {len(ipo_list)} IPOs...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for ipo_entry in ipo_list:
            ipo_id = ipo_entry.get('id')
            company_short_name = ipo_entry.get('company_short_name', 'N/A')
            url_rewrite_folder_name = ipo_entry.get('urlrewrite_folder_name')
            url_rewrite_folder_name_main = ipo_entry.get('urlrewrite_folder_name_main', 'ipo')

            if not ipo_id or not url_rewrite_folder_name:
                print(f"Skipping IPO ({company_short_name}) due to missing ID or URL components.")
                continue

            detail_url = f"{BASE_URL}/{url_rewrite_folder_name_main}/{url_rewrite_folder_name}/{ipo_id}/"
            futures[executor.submit(process_single_ipo, ipo_entry, detail_url)] = company_short_name

        for i, future in enumerate(as_completed(futures), 1):
            company_name = futures[future]
            print(f"\n--- Processing IPO {i}/{len(futures)}: {company_name} ---")
            try:
                ipo_data = future.result()
                if ipo_data:
                    db_manager.insert_or_update_ipo_data(ipo_data)
                else:
                    print(f"  Skipped {company_name}: No data returned from processing.")
            except Exception as e:
                print(f"  Error processing {company_name}: {e}")

    db_manager.close()
    print("\nScraping and database storage complete!")

def process_single_ipo(ipo_entry, detail_url):
    """
    Processes a single IPO by scraping its detail page and related APIs,
    then consolidating all data into a single dictionary.
    """
    ipo_id = ipo_entry.get('id')
    company_short_name_api = ipo_entry.get('company_short_name', 'N/A')
    ipo_category_api = ipo_entry.get('ipo_category', 'N/A')
    
    # Extract and process issue_size from API data
    issue_size_from_api = ipo_entry.get('issue_size', 'N/A')
    processed_issue_size = process_issue_size_from_api(issue_size_from_api)

    # Initialize with basic API data and default placeholders
    consolidated_data = {
        'ipo_id': str(ipo_id), # Ensure ID is string for consistency
        'company_short_name_api': company_short_name_api,
        'ipo_category': ipo_category_api,
        'detail_url': detail_url,
        'scraping_date': datetime.now().isoformat(),
        # Initialize all other fields to None or empty structures
        'company_full_name_scraped': None, 'company_logo_url': None, 'local_logo_path': None,
        'ipo_open_date': None, 'ipo_close_date': None, 'listing_date': None,
        'basis_of_allotment_date': None, 'refunds_initiation_date': None, 'credit_shares_demat_date': None,
        'ipo_open_date_status': None, 'ipo_close_date_status': None, 'listing_date_status': None,
        'about_company_text': None,
        'issue_price_band': None, 'issue_size_cr': processed_issue_size,  # Use API data as default
        'shares_per_lot': None, 'min_order_quantity': None,
        'gmp_latest': None, 'estimated_listing_price': None, 'gmp_trend_history_json': [],
        'ipo_strengths_json': [], 'ipo_objectives_json': [],
        'subscription_bidding_history_json': [], 'subscription_share_allocation_json': [],
        'subscription_daywise_table_json': [], 'subscription_shares_bid_amount_table_json': [],
        'company_financials_json': None, 'peer_comparison_json': [],
        'contact_company_address_json': {}, 'contact_ipo_registrar_json': {}, 'contact_ipo_lead_manager_json': [],
        'last_updated_on_page': None,
        # Fields from main details table (initialized to None, will be updated)
        'drhp_url': None, 'rhp_url': None, 'anchor_list_url': None,
        'retail_quota': None, 'issue_type': None, 'fresh_issue_amount': None,
        'face_value': None, 'promoter_holding_pre_ipo': None, 'promoter_holding_post_ipo': None,
        'listing_at': None, 'gmp_comments': None, 'subject_to_sauda': None
    }

    print(f"  Fetching detail page for {company_short_name_api} (ID: {ipo_id})...")
    html_content = make_robust_request(detail_url)

    if not html_content:
        print(f"  Failed to fetch detail page for {company_short_name_api}. Returning partial data.")
        return consolidated_data

    soup = BeautifulSoup(html_content, 'lxml')

    # --- Scrape data from HTML page ---
    try:
        consolidated_data.update(extract_company_name_and_logo(soup, ipo_id))
        consolidated_data.update(extract_company_about(soup))
        consolidated_data.update(extract_ipo_important_dates(soup))
        consolidated_data.update(extract_ipo_main_details_table(soup))
        consolidated_data.update(scrape_ipo_lots_table(soup))
        consolidated_data['ipo_strengths_json'] = extract_ipo_strengths(soup)
        consolidated_data['ipo_objectives_json'] = extract_ipo_objectives(soup)
        
        financials = scrape_and_format_financial_data(soup)
        if financials:
            consolidated_data['company_financials_json'] = financials.get('Company Financial Information (Restated Consolidated)')

        consolidated_data['peer_comparison_json'] = scrape_peer_comparison(soup)
        consolidated_data.update(extract_contact_sections(soup))
        consolidated_data['last_updated_on_page'] = extract_last_updated(soup)

    except Exception as e:
        print(f"  Error during HTML page scraping for {company_short_name_api}: {e}")

    # --- Scrape data from APIs (GMP, Subscription) ---
    try:
        gmp_api_response = fetch_gmp_data_for_ipo(ipo_id)
        if gmp_api_response:
            latest_gmp_details = parse_gmp_api_data(gmp_api_response.get("ipoGmpData", []))
            consolidated_data.update(latest_gmp_details)
            gmp_trend_table_data = parse_gmp_trend_table(gmp_api_response.get("ipoGmpTable", ""))
            consolidated_data["gmp_trend_history_json"] = gmp_trend_table_data
        else:
            print(f"  No GMP API response for {company_short_name_api}.")

        subscription_api_response = fetch_ipo_subscription_data(ipo_id)
        if subscription_api_response and subscription_api_response.get('data'):
            data_section = subscription_api_response['data']
            consolidated_data["subscription_bidding_history_json"] = parse_ipo_bidding_data_json(
                data_section.get("ipoBiddingData", [])
            )
            allocation_data, retail_quota_from_api = parse_ipo_share_allocation(
                data_section.get("listItemsHTML", "")
            )
            consolidated_data["subscription_share_allocation_json"] = allocation_data
            
            # Update retail_quota if we got it from API and it's not already set from table
            if retail_quota_from_api and (not consolidated_data.get('retail_quota') or consolidated_data.get('retail_quota') == 'N/A'):
                consolidated_data['retail_quota'] = retail_quota_from_api
            consolidated_data["subscription_daywise_table_json"] = parse_ipo_daywise_subscription_table(
                data_section.get("sResultIPOBidding", "")
            )
            consolidated_data["subscription_shares_bid_amount_table_json"] = parse_ipo_shares_bid_amount_table(
                data_section.get("sResultIPOBidding", "")
            )
        else:
            print(f"  No Subscription API response for {company_short_name_api}.")

    except Exception as e:
        print(f"  Error during API data fetching for {company_short_name_api}: {e}")

    return consolidated_data

if __name__ == "__main__":
    print("=== IPO Data Scraper & Database Storage Project ===")
    scrape_and_store_ipo_data()
    print("\nProject execution finished.")
    print("You can now query the 'ipo_data_investorgain.db' SQLite database to access the scraped IPO information.")

