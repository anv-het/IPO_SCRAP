# scrapers/ipo_data_scrapers.py

from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin
import pandas as pd # Used for financial data parsing

# Import helper functions and config from parent directories
from utils import clean_text, convert_to_int, convert_to_float, parse_date_status, make_robust_request
from config import BASE_URL, IPO_LIST_API_URL, GMP_API_URL_TEMPLATE, SUBSCRIPTION_API_URL_TEMPLATE

# --- Core Scraper Functions ---

def fetch_ipo_list_from_api():
    """
    Fetches the list of IPOs from the Investorgain API.
    """
    print("  [API] Fetching IPO list...")
    try:
        response_content = make_robust_request(IPO_LIST_API_URL, is_api=True)
        if response_content:
            data = json.loads(response_content)
            if data.get("msg") == 1 and "ipoList" in data:
                print(f"  [API] Successfully fetched {len(data['ipoList'])} IPOs.")
                return data["ipoList"]
            else:
                print(f"  [API] Response not as expected: {data}")
        return []
    except Exception as e:
        print(f"  [API] Error fetching IPO list: {e}")
        return []

def extract_company_name_and_logo(soup, ipo_id=None):
    """
    Extracts Company Name and Logo URL from a BeautifulSoup object.
    Also downloads the logo locally if ipo_id is provided.
    """
    from utils import download_logo  # Import here to avoid circular imports
    
    company_data = {'company_full_name_scraped': 'N/A', 'company_logo_url': 'N/A', 'local_logo_path': None}
    
    ipo_name_tag = soup.find('div', class_='col-lg-6')
    if ipo_name_tag:
        h1_tag = ipo_name_tag.find('h1')
        if h1_tag:
            company_data['company_full_name_scraped'] = clean_text(h1_tag.get_text(strip=True))
            # print(f"  [Name/Logo] Found company name from h1: {company_data['company_full_name_scraped']}")
    
    if company_data['company_full_name_scraped'] == 'N/A':
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            if 'IPO' in title_text:
                company_name = title_text.split('IPO')[0].strip()
                company_data['company_full_name_scraped'] = clean_text(company_name)
                # print(f"  [Name/Logo] Found company name from title: {company_data['company_full_name_scraped']}")

    logo_img_tag = soup.find('div', class_='div-logo')
    if logo_img_tag:
        img_tag = logo_img_tag.find('img')
        if img_tag:
            logo_src = img_tag.get('src')
            if logo_src:
                company_data['company_logo_url'] = urljoin(BASE_URL, logo_src)
                # print(f"  [Name/Logo] Found logo URL: {company_data['company_logo_url']}")
                
                # Download logo locally if ipo_id is provided
                if ipo_id and company_data['company_full_name_scraped'] != 'N/A':
                    local_path = download_logo(
                        company_data['company_logo_url'], 
                        company_data['company_full_name_scraped'], 
                        ipo_id
                    )
                    company_data['local_logo_path'] = local_path
    
    return company_data

def extract_company_about(soup):
    """
    Extracts the 'About Company' paragraph(s) from a BeautifulSoup object.
    """
    about_company_text = "N/A"
    about_h3 = soup.find('h3', itemprop="about")

    if about_h3:
        about_content_container = None
        current_sibling = about_h3.next_sibling
        while current_sibling:
            if isinstance(current_sibling, str) and not current_sibling.strip():
                current_sibling = current_sibling.next_sibling
                continue
            if current_sibling.name == 'div':
                about_content_container = current_sibling
                break
            current_sibling = current_sibling.next_sibling

        if about_content_container:
            about_paragraphs = []
            for p_tag in about_content_container.find_all('p'):
                paragraph_text = clean_text(p_tag.get_text())
                if paragraph_text:
                    about_paragraphs.append(paragraph_text)
            if about_paragraphs:
                about_company_text = "\n\n".join(about_paragraphs)
                # print(f"  [About] Extracted about company text (snippet): {about_company_text[:100]}...")
        # else:
            # print("  [About] No 'About Company' content container found.")
    # else:
        # print("  [About] No 'About Company' h3 tag found.")

    return {'about_company_text': about_company_text}

def extract_ipo_important_dates(soup):
    """
    Extracts IPO Important Dates from tables in a BeautifulSoup object.
    """
    dates_data = {}
    date_field_patterns = {
        "ipo_open_date": re.compile(r'Opening Date', re.IGNORECASE),
        "ipo_close_date": re.compile(r'Closing Date', re.IGNORECASE),
        "basis_of_allotment_date": re.compile(r'Basis of Allotment Date', re.IGNORECASE),
        "refunds_initiation_date": re.compile(r'Refunds Initiation', re.IGNORECASE),
        "credit_shares_demat_date": re.compile(r'Credit of Shares to Demat', re.IGNORECASE),
        "listing_date": re.compile(r'Listing Date', re.IGNORECASE),
    }

    all_strong_tags = soup.find_all('strong')
    found_any_date = False
    for output_key, pattern in date_field_patterns.items():
        found = False
        for strong_tag in all_strong_tags:
            strong_text = clean_text(strong_tag.get_text())
            if pattern.search(strong_text):
                target_td = strong_tag.find_parent('td')
                if target_td:
                    value_td = target_td.find_next_sibling('td')
                    if value_td:
                        value = clean_text(value_td.get_text(strip=True))
                        dates_data[output_key] = value
                        found = True
                        found_any_date = True
                        break
        if not found:
            dates_data[output_key] = 'N/A'

    # if found_any_date:
        # print(f"  [Dates] Extracted dates: {', '.join([f'{k}: {v}' for k, v in dates_data.items() if v != 'N/A'])}")
    # else:
        # print("  [Dates] No important dates found.")

    # Add parsed status for key dates
    for key in ['ipo_open_date', 'ipo_close_date', 'listing_date']:
        parsed_date_str, status, _ = parse_date_status(dates_data.get(key, 'N/A'))
        dates_data[f'{key}_status'] = status
        if parsed_date_str != 'N/A' and parsed_date_str != 'TBA':
            dates_data[key] = parsed_date_str # Update to YYYY-MM-DD format

    return dates_data

def extract_ipo_main_details_table(soup):
    """
    Extracts various IPO details from the main details table in a BeautifulSoup object.
    This includes issue price, issue size, promoter holding, etc.
    Updated to use the same logic as the working individual script.
    """
    main_details = {}
    # print("  [Main Details] Attempting to extract main IPO details table...")

    # Use the same approach as the working individual script
    main_details_table = soup.find('table', class_='table table-bordered table-striped table-hover w-auto')
    
    if not main_details_table:
        # print("  [Main Details] IPO Details table not found.")
        return main_details

    # Define patterns matching your working individual script
    detail_field_patterns_map = {
        "issue_price_band": re.compile(r'Issue Price', re.IGNORECASE),
        "drhp_url": re.compile(r'DRHP', re.IGNORECASE),
        "rhp_url": re.compile(r'RHP', re.IGNORECASE),
        "anchor_list_url": re.compile(r'Anchor List', re.IGNORECASE),
        "listing_at": re.compile(r'Listing At|Listing On', re.IGNORECASE),
        "retail_quota": re.compile(r'Retail Quota|Retail Allotment %', re.IGNORECASE),
        "issue_type": re.compile(r'Issue Type', re.IGNORECASE),
        "issue_size_cr": re.compile(r'Issue Size', re.IGNORECASE),
        "fresh_issue_amount": re.compile(r'Fresh Issue', re.IGNORECASE),
        "face_value": re.compile(r'Face Value', re.IGNORECASE),
        "promoter_holding_pre_ipo": re.compile(r'Promoter Holding Pre IPO', re.IGNORECASE),
        "promoter_holding_post_ipo": re.compile(r'Promoter Holding Post IPO', re.IGNORECASE),
    }

    print("  ✓ Found main IPO details table.")
    for row in main_details_table.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label_element = cells[0]
            value_element = cells[1]

            label_text = clean_text(label_element.get_text(strip=True))
            value = 'N/A'

            # 1. Prioritize 'data-title' for dates (as some dates might be hidden in text)
            if 'data-title' in value_element.attrs and \
               any(re.search(pattern, label_text) for pattern in [r'Issue Opening Date', r'Issue Closing Date']):
                value = clean_text(value_element['data-title'])
            else:
                # 2. Check for any link within the value element
                found_link_element = value_element.find('a', href=True)
                if found_link_element:
                    link_href = found_link_element['href']
                    # If it's a relative URL, make it absolute
                    if link_href.startswith('/'):
                        # Base domain for Investorgain.com relative URLs
                        value = f"https://www.investorgain.com{link_href}"
                    else:
                        value = link_href
                else:
                    # 3. Fallback to get_text() if no specific pattern matched
                    value = clean_text(value_element.get_text(strip=True))
            
            # Ensure that if value is an empty string after cleaning, it defaults to 'N/A'
            if not value and value != '':
                value = 'N/A'

            # Check against all patterns
            for output_key, pattern in detail_field_patterns_map.items():
                if pattern.search(label_text):
                    main_details[output_key] = value
                    break  # Move to the next row once a match is found for this row

    # Ensure all expected keys are present, even if N/A
    for key in detail_field_patterns_map.keys():
        if key not in main_details:
            main_details[key] = 'N/A'
    
    # if main_details:
        # print(f"  [Main Details] Successfully extracted main IPO details.")
    # else:
        # print("  [Main Details] No main IPO details extracted.")

    return main_details

def scrape_ipo_lots_table(soup):
    """
    Scrapes the "IPO Lots" table from a BeautifulSoup object.
    Refined to better extract 'shares_per_lot'.
    """
    ipo_lots_data = {}
    # print("  [Lots] Attempting to extract IPO Lots table...")

    ipo_lots_table = None
    for h2_tag in soup.find_all('h2'):
        h2_text_content = clean_text(h2_tag.get_text())
        if re.search(r'IPO.*Lots', h2_text_content, re.IGNORECASE):
            ipo_lots_table = h2_tag.find_next_sibling('table', class_='table table-bordered table-striped table-hover w-auto')
            if ipo_lots_table:
                break

    if ipo_lots_table:
        # print("  [Lots] Found 'IPO Lots' table.")
        lot_field_patterns_map = {
            "issue_price_band": re.compile(r'Issue Price', re.IGNORECASE),
            "min_order_quantity": re.compile(r'Market Lot', re.IGNORECASE),
            "shares_per_lot_raw": re.compile(r'Individual Investor', re.IGNORECASE),
            "min_hni_lots": re.compile(r'Min HNI Lots', re.IGNORECASE),
            "min_small_hni_lots": re.compile(r'Min Small HNI Lots', re.IGNORECASE),
            "min_big_hni_lots": re.compile(r'Min Big HNI Lots', re.IGNORECASE),
        }

        for row in ipo_lots_table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label_text = clean_text(cells[0].get_text(strip=True))
                value = clean_text(cells[1].get_text(strip=True))
                if not value and value != '':
                    value = 'N/A'

                for output_key, pattern in lot_field_patterns_map.items():
                    if pattern.search(label_text):
                        ipo_lots_data[output_key] = value
                        break
        
        # Post-processing for shares_per_lot
        min_order_q = ipo_lots_data.get('min_order_quantity', '')
        match_shares = re.search(r'(\d+)\s*Shares', min_order_q, re.IGNORECASE)
        if match_shares:
            ipo_lots_data['shares_per_lot'] = clean_text(match_shares.group(1))
            # print(f"  [Lots] Extracted shares_per_lot from 'Market Lot': {ipo_lots_data['shares_per_lot']}")
        elif ipo_lots_data.get('shares_per_lot_raw') and ipo_lots_data.get('shares_per_lot_raw') != 'N/A':
             if convert_to_int(ipo_lots_data.get('shares_per_lot_raw')) is not None:
                 ipo_lots_data['shares_per_lot'] = ipo_lots_data['shares_per_lot_raw']
                 # print(f"  [Lots] Extracted shares_per_lot from 'Individual Investor': {ipo_lots_data['shares_per_lot']}")
             else:
                 ipo_lots_data['shares_per_lot'] = 'N/A'
        else:
            ipo_lots_data['shares_per_lot'] = 'N/A'
            # print("  [Lots] Could not reliably extract shares_per_lot.")

        if 'shares_per_lot_raw' in ipo_lots_data:
            del ipo_lots_data['shares_per_lot_raw']

    # else:
        # print("  [Lots] 'IPO Lots' table not found for extraction.")

    expected_keys = [
        "issue_price_band", "min_order_quantity", "shares_per_lot",
        "min_hni_lots", "min_small_hni_lots", "min_big_hni_lots"
    ]
    for key in expected_keys:
        if key not in ipo_lots_data:
            ipo_lots_data[key] = 'N/A'

    return ipo_lots_data

#lets debug this we cant get the gmp data 
def fetch_gmp_data_for_ipo(ipo_id):
    """
    Fetches GMP data for a specific IPO ID from the Investorgain API.
    """
    gmp_api_url = GMP_API_URL_TEMPLATE.format(ipo_id=ipo_id)
    print(f"  [GMP API] Fetching GMP data for IPO ID {ipo_id} from URL: {gmp_api_url}")
    try:
        response_content = make_robust_request(gmp_api_url, is_api=True)
        print(f"  [GMP API] Response content for ID {ipo_id}: {response_content}...")  # Debugging line
        if response_content:
            data = json.loads(response_content)
            if data.get("msg") == 1:
                print(f"  [GMP API] Successfully fetched GMP data for IPO ID {ipo_id}.")
                return data
            else:
                print(f"  [GMP API] API response not as expected for IPO ID {ipo_id}: {data}")
        return None
    except Exception as e:
        print(f"  [GMP API] Error fetching GMP data for IPO ID {ipo_id}: {e}")
        return None

def parse_gmp_api_data(gmp_data_array):
    """
    Parses the 'ipoGmpData' list from the GMP API response.
    """
    gmp_json_data = {}

    if gmp_data_array and isinstance(gmp_data_array, list) and len(gmp_data_array) > 0:
        print(f"  [GMP Parse] Found {len(gmp_data_array)} GMP entries in API response.")
        latest_gmp = gmp_data_array[0]
        print(f"  [GMP Parse] Latest GMP entry: {latest_gmp}")
        gmp_json_data = {
            "gmp_latest": clean_text(latest_gmp.get("gmp", "N/A")),
            "estimated_listing_price": clean_text(latest_gmp.get("estimated_listing_price", "N/A")),
            "gmp_comments": clean_text(latest_gmp.get("gmp_comments", "N/A")),
            "subject_to_sauda": clean_text(latest_gmp.get("subject_to_sauda", "N/A")),
        }
        print(f"  [GMP Parse] Extracted latest GMP: {gmp_json_data.get('gmp_latest')}, Est. Listing: {gmp_json_data.get('estimated_listing_price')}")
    else:
        print("  [GMP Parse] No latest GMP data found in API response.")
    return gmp_json_data

def parse_gmp_trend_table(html_table_string):
    """
    Parses the HTML table string (ipoGmpTable) to extract day-wise GMP trends.
    """
    gmp_trend_data = []
    if not html_table_string:
        # print("  [GMP Trend] No HTML table string provided for GMP trend.")
        return gmp_trend_data

    soup = BeautifulSoup(html_table_string, 'html.parser')
    table = soup.find('table')

    if not table or not table.find('thead') or not table.find('tbody'):
        # print("  [GMP Trend] GMP trend table structure not found.")
        return gmp_trend_data

    headers = [clean_text(th.get_text()) for th in table.find('thead').find_all('th')]
    header_to_output_key_map = {
        "GMP Date": "gmp_date", "IPO Price": "ipo_price", "GMP": "gmp",
        "Sub2 Sauda Rate": "sub2_sauda_rate", "Estimated Listing Price": "estimated_listing_price",
        "Estimated Profit": "estimated_profit", "Last Updated": "last_updated_gmp_trend"
    }

    body_rows = table.find('tbody').find_all('tr')
    for row in body_rows:
        row_data = {}
        cells = row.find_all('td')
        if len(cells) >= len(headers):
            for i, cell in enumerate(cells):
                if i < len(headers):
                    raw_header = headers[i]
                    output_key = header_to_output_key_map.get(raw_header, raw_header.lower().replace(' ', '_'))
                    cell_text = clean_text(cell.get_text(separator=" ", strip=True))
                    row_data[output_key] = cell_text
            gmp_trend_data.append(row_data)
    
    # print(f"  [GMP Trend] Parsed {len(gmp_trend_data)} GMP trend entries.")
    return gmp_trend_data

def extract_ipo_strengths(soup):
    """
    Extracts IPO Strengths from the detail page.
    """
    strengths = []
    # print("  [Strengths] Attempting to extract IPO strengths...")
    for h3 in soup.find_all('h3'):
        cleaned_h3_text = clean_text(h3.get_text())
        if re.search(r'strengths', cleaned_h3_text, re.IGNORECASE):
            div = h3.find_next_sibling('div')
            if div:
                ul = div.find('ul')
                if ul:
                    strengths = [clean_text(li.get_text()) for li in ul.find_all('li') if clean_text(li.get_text())]
                    break
    # if strengths:
        # print(f"  [Strengths] Extracted {len(strengths)} strengths.")
    # else:
        # print("  [Strengths] No IPO strengths found.")
    return strengths

def extract_ipo_objectives(soup):
    """
    Extracts IPO Objectives from the detail page.
    """
    objectives = []
    # print("  [Objectives] Attempting to extract IPO objectives...")
    try:
        table = soup.find("table", {"id": "ObjectiveIssue"})
        if not table:
            for h3 in soup.find_all("h3"):
                if "IPO Objective" in h3.get_text():
                    table = h3.find_next_sibling('table') or h3.find_next('table')
                    if table:
                        break
        
        if table:
            rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    objective_entry = {
                        "s_no": clean_text(cols[0].get_text()),
                        "object": clean_text(cols[1].get_text()),
                        "amount": clean_text(cols[2].get_text()) if len(cols) > 2 else ""
                    }
                    objectives.append(objective_entry)
            # print(f"  [Objectives] Extracted {len(objectives)} IPO objectives.")
        # else:
            # print("  [Objectives] No IPO objectives table found.")
    except Exception as e:
        print(f"  [Objectives] Error extracting IPO objectives: {e}")
    return objectives

def fetch_ipo_subscription_data(ipo_id):
    """
    Fetches IPO subscription data for a specific IPO ID from the Investorgain API.
    """
    subscription_api_url = SUBSCRIPTION_API_URL_TEMPLATE.format(ipo_id=ipo_id)
    # print(f"  [Subscription API] Fetching Subscription data for IPO ID {ipo_id}...")
    try:
        response_content = make_robust_request(subscription_api_url, is_api=True)
        if response_content:
            data = json.loads(response_content)
            if data.get("msg") == 1:
                # print(f"  [Subscription API] Successfully fetched Subscription data for IPO ID {ipo_id}.")
                return data
            # else:
                # print(f"  [Subscription API] API response not as expected for IPO ID {ipo_id}: {data}")
        return None
    except Exception as e:
        print(f"  [Subscription API] Error fetching Subscription data for IPO ID {ipo_id}: {e}")
        return None

def parse_ipo_bidding_data_json(bidding_data_array):
    """
    Parses the 'ipoBiddingData' list from the Subscription API response.
    """
    parsed_data = []
    if not bidding_data_array:
        # print("  [Subscription Parse] No bidding history data array provided.")
        return parsed_data

    for entry in bidding_data_array:
        parsed_entry = {
            "bid_date": clean_text(entry.get("bid_date", "N/A")),
            "qib_ratio": convert_to_float(clean_text(entry.get("qib", "N/A"))),
            "nii_ratio": convert_to_float(clean_text(entry.get("nii", "N/A"))),
            "rii_ratio": convert_to_float(clean_text(entry.get("rii", "N/A"))),
            "emp_ratio": convert_to_float(clean_text(entry.get("emp", "N/A"))),
            "total_ratio": convert_to_float(clean_text(entry.get("total", "N/A"))),
            "qib_shares_bid_for": convert_to_int(clean_text(entry.get("qib_shares_bid_for", "N/A"))),
            "total_shares_bid_for": convert_to_int(clean_text(entry.get("total_shares_bid_for", "N/A")))
        }
        parsed_data.append(parsed_entry)
    # print(f"  [Subscription Parse] Parsed {len(parsed_data)} bidding history entries.")
    return parsed_data

def parse_ipo_share_allocation(html_string):
    """
    Parses the 'listItemsHTML' to extract IPO Share Allocation data.
    """
    allocation_data = []
    retail_quota = None  # Initialize retail_quota to None
    
    if not html_string:
        # print("  [Allocation] No HTML string provided for share allocation.")
        return allocation_data, retail_quota

    soup = BeautifulSoup(html_string, 'html.parser')
    list_items = soup.find_all('li')

    allocation_regex = re.compile(r'(.+?):\s*([\d,\.]+\s*(?:Shares)?)\s*\(([\d\.]+)\%\)')

    for item in list_items:
        text = item.get_text().strip()
        match = allocation_regex.search(text)
        if match:
            category = clean_text(match.group(1))
            shares_allocated = convert_to_int(clean_text(match.group(2).replace(' Shares', '')))
            allocation_pct = convert_to_float(clean_text(match.group(3)))
            
            # Check if this is retail individual investor category
            if re.search(r'retail.*individual.*investor', category.lower()):
                retail_quota = f"{allocation_pct}%"
            
            allocation_data.append({
                "category": category,
                "shares_allocated": shares_allocated,
                "allocation_pct": allocation_pct
            })
        # else:
            # print(f"  [Allocation] Warning: Could not parse list item for share allocation (regex mismatch): '{text}'")
            # allocation_data.append({
            #     "category": clean_text(text),
            #     "shares_allocated": None,
            #     "allocation_pct": None,
            #     "parsing_error": True
            # })
    # print(f"  [Allocation] Parsed {len(allocation_data)} share allocation entries.")
    return allocation_data, retail_quota

def parse_ipo_daywise_subscription_table(html_table_string):
    """
    Parses the HTML table string for IPO Day-wise Subscription.
    """
    daywise_data = []
    if not html_table_string:
        # print("  [Daywise Sub] No HTML string provided for daywise subscription.")
        return daywise_data

    soup = BeautifulSoup(html_table_string, 'html.parser')
    table = soup.find('table', caption="IPO Bidding Live Updates from BSE, NSE")
    if not table:
        table = soup.find('table', class_='table-striped')
        if not table:
            # print("  [Daywise Sub] Daywise subscription table not found.")
            return daywise_data

    headers = [clean_text(th.get_text()) for th in table.find('thead').find_all('th')]
    header_mapping = {
        'Day': 'day_number', 'Bid Date': 'date_time', 'QIB': 'qib_ratio',
        'NII': 'nii_ratio', 'SNII (Below ₹10L)': 'snii_ratio', 'SNII': 'snii_ratio',
        'BNII (Above ₹10L)': 'bnii_ratio', 'BNII': 'bnii_ratio', 'RII': 'rii_ratio',
        'Retail': 'rii_ratio', 'Total': 'total_ratio'
    }

    output_keys = [header_mapping.get(h, clean_text(h).lower().replace(' ', '_')) for h in headers]

    body_rows = table.find('tbody').find_all('tr')
    for row in body_rows:
        row_data = {}
        cells = row.find_all('td')
        if len(cells) < len(output_keys):
            continue

        for i, cell in enumerate(cells):
            if i < len(output_keys):
                key = output_keys[i]
                value = clean_text(cell.get_text())
                if key == 'day_number':
                    row_data[key] = convert_to_int(value)
                elif '_ratio' in key:
                    row_data[key] = convert_to_float(value)
                else:
                    row_data[key] = value
        daywise_data.append(row_data)
    # print(f"  [Daywise Sub] Parsed {len(daywise_data)} daywise subscription entries.")
    return daywise_data

def parse_ipo_shares_bid_amount_table(html_table_string):
    """
    Parses the HTML table string for IPO Shares Bid Amount.
    """
    bid_amount_data = []
    if not html_table_string:
        # print("  [Bid Amount] No HTML string provided for bid amount table.")
        return bid_amount_data

    soup = BeautifulSoup(html_table_string, 'html.parser')
    
    target_table = None
    all_tables = soup.find_all('table')
    for table in all_tables:
        headers = [clean_text(th.get_text()) for th in table.find('thead').find_all('th')] if table.find('thead') else []
        if 'Category' in headers and 'Shares Offered' in headers and 'Shares Bid' in headers and any('Amount' in h for h in headers):
            target_table = table
            break

    if not target_table:
        # print("  [Bid Amount] Shares bid amount table not found.")
        return bid_amount_data

    headers = [clean_text(th.get_text()) for th in target_table.find('thead').find_all('th')]
    header_mapping = {
        'Category': 'category', 'Shares Offered': 'shares_offered',
        'Shares Bid': 'shares_bid', 'Amount (Cr.)': 'bid_amount_cr', 'Amount (Cr)': 'bid_amount_cr'
    }
    output_keys = [header_mapping.get(h, clean_text(h).lower().replace(' ', '_')) for h in headers]

    body_rows = target_table.find('tbody').find_all('tr')
    for row in body_rows:
        row_data = {}
        cells = row.find_all('td')
        if len(cells) < len(output_keys):
            continue

        for i, cell in enumerate(cells):
            if i < len(output_keys):
                key = output_keys[i]
                value = clean_text(cell.get_text())
                if key in ['shares_offered', 'shares_bid']:
                    row_data[key] = convert_to_int(value)
                elif key == 'bid_amount_cr':
                    row_data[key] = convert_to_float(value)
                else:
                    row_data[key] = value
        bid_amount_data.append(row_data)
    # print(f"  [Bid Amount] Parsed {len(bid_amount_data)} shares bid amount entries.")
    return bid_amount_data


def scrape_and_format_financial_data(soup):
    """
    Scrapes and formats company financial data from a BeautifulSoup object.
    """
    financial_data = None
    # print("  [Financials] Attempting to extract financial data...")
    table = soup.find('table', {'id': 'financialTable'})
    if not table:
        heading = soup.find('h2', string=lambda text: text and 'Financial Information' in text)
        if heading:
            parent_div = heading.find_next('div', class_='table-responsive')
            if parent_div:
                table = parent_div.find('table')

    if table:
        rows = table.find_all('tr')
        data = []
        for row in rows:
            cols = [clean_text(col.get_text()) for col in row.find_all(['td', 'th'])]
            data.append(cols)

        if len(data) > 1:
            headers = data[0]
            rows_data = data[1:]
            
            output_formatted = []
            for row_vals in rows_data:
                entry = {}
                for i, header in enumerate(headers):
                    if i < len(row_vals):
                        value = row_vals[i]
                        if i > 0:
                            entry[header] = convert_to_float(value)
                        else:
                            entry[header] = value
                output_formatted.append(entry)
            financial_data = {"Company Financial Information (Restated Consolidated)": output_formatted}
            # print(f"  [Financials] Extracted financial data with {len(output_formatted)} rows.")
        # else:
            # print("  [Financials] Insufficient financial data found in table.")
    # else:
        # print("  [Financials] Financial table not found.")
    return financial_data

def scrape_peer_comparison(soup):
    """
    Extracts peer comparison data from the table in a BeautifulSoup object.
    """
    peer_comparison_data = []
    # print("  [Peer Comparison] Attempting to extract peer comparison data...")
    table = None
    for h2 in soup.find_all("h2"):
        if "Peer Comparison" in h2.get_text():
            table = h2.find_next("table")
            if table:
                break

    if not table:
        expected_headers = {"Company", "EPS Basic", "EPS Diluted", "NAV", "P/E(x)", "RoNW", "Financial statements"}
        for t in soup.find_all("table"):
            headers = [clean_text(th.get_text()) for th in t.find_all('th')]
            if expected_headers.issubset(set(headers)):
                table = t
                break

    if table:
        headers = [clean_text(th.get_text()) for th in table.find("thead").find_all("th")]
        rows = table.find("tbody").find_all("tr")

        for row in rows:
            cols = row.find_all("td")
            row_data = {}
            for i in range(min(len(cols), len(headers))):
                row_data[headers[i]] = clean_text(cols[i].get_text())
            peer_comparison_data.append(row_data)
        # print(f"  [Peer Comparison] Extracted {len(peer_comparison_data)} peer comparison rows.")
    # else:
        # print("  [Peer Comparison] Peer comparison table not found.")
    return peer_comparison_data

def extract_contact_sections(soup):
    """
    Extracts Company Address, IPO Registrar, and Lead Manager details from a BeautifulSoup object.
    """
    data = {
        "contact_company_address_json": {},
        "contact_ipo_registrar_json": {},
        "contact_ipo_lead_manager_json": []
    }
    # print("  [Contact] Attempting to extract contact details...")

    def _extract_address_card(card):
        result = {"name": "N/A", "address": "N/A", "website": "N/A", "phone": "N/A", "email": "N/A"}
        try:
            body = card.find("div", class_="card-body")
            if not body: return result
            
            name_tag = body.find("strong")
            if name_tag:
                result["name"] = clean_text(name_tag.get_text())
                
                address_parts = []
                current_node = name_tag.next_sibling
                while current_node:
                    if getattr(current_node, "name", None) == "strong":
                        break
                    text = ''
                    if isinstance(current_node, str):
                        text = current_node.strip()
                    else:
                        text = current_node.get_text(strip=True)
                    if text:
                        address_parts.append(text)
                    current_node = current_node.next_sibling
                result["address"] = ', '.join(address_parts).replace(",,", ",").strip()

                for strong_tag in body.find_all("strong")[1:]:
                    label = clean_text(strong_tag.get_text()).lower()
                    next_node = strong_tag.next_sibling
                    while next_node and (isinstance(next_node, str) and not next_node.strip()):
                        next_node = next_node.next_sibling
                    value = clean_text(next_node.get_text() if next_node and not isinstance(next_node, str) else next_node)
                    if "website" in label: result["website"] = value
                    elif "phone" in label: result["phone"] = value
                    elif "email" in label: result["email"] = value
        except Exception as e:
            print(f"  [Contact] Error extracting address card: {e}")
        return result

    def _extract_lead_manager(card):
        managers = []
        try:
            body = card.find("div", class_="card-body")
            ol = body.find("ol")
            if ol:
                managers = [clean_text(li.get_text()) for li in ol.find_all("li")]
        except Exception as e:
            print(f"  [Contact] Error extracting lead managers: {e}")
        return managers

    cards = soup.find_all("div", class_="card")
    # found_any_contact = False
    for card in cards:
        h3 = card.find("h3")
        if not h3: continue
        heading = clean_text(h3.get_text())

        if "Company Address" in heading:
            data["contact_company_address_json"] = _extract_address_card(card)
            # found_any_contact = True
        elif "Registrar" in heading:
            data["contact_ipo_registrar_json"] = _extract_address_card(card)
            # found_any_contact = True
        elif "Lead Manager" in heading:
            data["contact_ipo_lead_manager_json"] = _extract_lead_manager(card)
            # found_any_contact = True
    
    # if found_any_contact:
        # print("  [Contact] Successfully extracted some contact details.")
    # else:
        # print("  [Contact] No contact details sections found.")

    return data

def extract_last_updated(soup):
    """
    Extracts the "Last Updated on" timestamp from the page.
    """
    last_updated_info = "N/A"
    # print("  [Last Updated] Attempting to extract last updated timestamp...")
    try:
        row_divs = soup.find_all("div", class_="row")
        for row in row_divs:
            col_div = row.find("div", class_="col-12")
            if col_div:
                p_tag = col_div.find("p")
                if p_tag and "Last Updated on" in p_tag.get_text():
                    last_updated_info = clean_text(p_tag.get_text().replace("Last Updated on", ""))
                    # print(f"  [Last Updated] Found from row div: {last_updated_info}")
                    return last_updated_info

        for p in soup.find_all("p"):
            text = clean_text(p.get_text())
            if "Last Updated on" in text:
                last_updated_info = text.replace("Last Updated on", "")
                # print(f"  [Last Updated] Found from p tag: {last_updated_info}")
                return last_updated_info

        match = re.search(r"\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}", soup.get_text())
        if match:
            last_updated_info = clean_text(match.group(0))
            # print(f"  [Last Updated] Found from regex match: {last_updated_info}")
            return last_updated_info

        # print("  [Last Updated] No last updated info found.")
        return "N/A"
    except Exception as e:
        print(f"  [Last Updated] Error extracting last updated info: {e}")
        return "N/A"

