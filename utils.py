# utils.py

import re
import time
import json
import zlib
import brotli
import requests
import os
from urllib.parse import urlparse
from datetime import datetime
from config import COMMON_HEADERS # Import COMMON_HEADERS from config

def clean_text(text):
    """
    Cleans extracted text by removing extra spaces, newlines, non-breaking spaces,
    and consolidating multiple spaces. Also removes common symbols for numeric conversion.
    """
    if text is None:
        return ""
    text = str(text).replace('\xa0', ' ').replace('\n', ' ').strip()
    text = re.sub(r'\s+', ' ', text) # Replace multiple spaces with a single space
    text = text.replace('&#8377;', '').replace('₹', '').replace(',', '').replace('x', '').replace('%', '')
    return text

def convert_to_int(value):
    """Converts a cleaned string to an integer, returning None if conversion fails."""
    try:
        return int(float(value)) if value is not None and value.strip() else None
    except (ValueError, TypeError):
        return None

def convert_to_float(value):
    """Converts a cleaned string to a float, returning None if conversion fails."""
    try:
        # Handle cases where value might be like "₹ 1,234.56"
        cleaned_value = re.sub(r'[₹,$]', '', str(value)).replace(',', '')
        return float(cleaned_value) if cleaned_value.strip() else None
    except (ValueError, TypeError):
        return None

def parse_date_status(date_string):
    """
    Attempts to parse date and determine if it's past, present, or future.
    Handles ordinal suffixes (st, nd, rd, th) in dates.
    Returns tuple: (parsed_date_str_YYYY-MM-DD, status, original_string)
    """
    if not date_string or date_string == 'N/A':
        return 'N/A', 'Unknown', date_string

    cleaned_date_string = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_string, flags=re.IGNORECASE)

    date_formats_to_try = [
        '%d %b %Y',     # e.g., "3 Jul 2025"
        '%d %B %Y',     # e.g., "3 July 2025"
        '%d/%m/%Y',     # e.g., "03/07/2025"
        '%d-%m-%Y',     # e.g., "03-07-2025"
        '%B %d, %Y',    # e.g., "July 3, 2025"
        '%b %d, %Y',    # e.g., "Jul 3, 2025"
        '%d %b %Y %H:%M:%S', # For last updated timestamps
        '%d-%m-%Y %H:%M:%S'
    ]

    current_date = datetime.now()

    for fmt in date_formats_to_try:
        try:
            parsed_date = datetime.strptime(cleaned_date_string, fmt)
            if parsed_date.date() < current_date.date():
                status = 'Past'
            elif parsed_date.date() == current_date.date():
                status = 'Today'
            else:
                status = 'Future'
            return parsed_date.strftime('%Y-%m-%d'), status, date_string
        except ValueError:
            continue

    if any(word in date_string.lower() for word in ['tba', 'tbd', 'to be announced', 'to be decided']):
        return 'TBA', 'TBA', date_string
    elif 'n/a' in date_string.lower():
        return 'N/A', 'N/A', date_string
    else:
        return 'N/A', 'Unknown', date_string

def make_robust_request(url, custom_headers=None, is_api=False, timeout=15, retry_attempts=3, backoff_factor=2):
    """
    Makes a robust HTTP GET request with retries and handles common compressions.
    """
    request_headers = COMMON_HEADERS.copy()
    if custom_headers:
        request_headers.update(custom_headers)

    # Adjust headers based on whether it's an API call or HTML page call
    if is_api:
        request_headers["Accept"] = "*/*"
        request_headers["Sec-Fetch-Dest"] = "empty"
        request_headers["Sec-Fetch-Mode"] = "cors"
        request_headers["Sec-Fetch-Site"] = "same-site"
        request_headers["Host"] = "webnodejs.investorgain.com"
        request_headers["Referer"] = "https://www.investorgain.com/"
    else:
        request_headers["Sec-Fetch-Dest"] = "document"
        request_headers["Sec-Fetch-Mode"] = "navigate"
        request_headers["Sec-Fetch-Site"] = "same-origin"
        request_headers["Host"] = "www.investorgain.com"
        request_headers["Referer"] = "https://www.investorgain.com/ipo-list/"


    for attempt in range(retry_attempts):
        try:
            response = requests.get(url, headers=request_headers, timeout=timeout)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            decoded_content = response.text
            if not decoded_content and response.content:
                content_encoding = response.headers.get('Content-Encoding')
                if content_encoding == 'gzip':
                    decoded_content = zlib.decompress(response.content, 16 + zlib.MAX_WBITS).decode('utf-8', errors='ignore')
                elif content_encoding == 'br':
                    decoded_content = brotli.decompress(response.content).decode('utf-8', errors='ignore')
                elif content_encoding == 'deflate':
                    decoded_content = zlib.decompress(response.content, -zlib.MAX_WBITS).decode('utf-8', errors='ignore')
                else:
                    decoded_content = response.content.decode('utf-8', errors='ignore')

            if not decoded_content:
                raise requests.exceptions.RequestException(f"Received empty content for {url}")

            return decoded_content

        except requests.exceptions.RequestException as e:
            print(f"  Request error for {url} (Attempt {attempt + 1}/{retry_attempts}): {e}")
            if attempt < retry_attempts - 1:
                time.sleep(backoff_factor ** attempt) # Exponential backoff
        except (json.JSONDecodeError, zlib.error, brotli.Error) as e:
            print(f"  Decoding error for {url} (Attempt {attempt + 1}/{retry_attempts}): {e}")
            if attempt < retry_attempts - 1:
                time.sleep(backoff_factor ** attempt)
        except Exception as e:
            print(f"  Unexpected error for {url} (Attempt {attempt + 1}/{retry_attempts}): {e}")
            if attempt < retry_attempts - 1:
                time.sleep(backoff_factor ** attempt)

    print(f"  Failed to fetch {url} after {retry_attempts} attempts.")
    return None

def process_issue_size_from_api(issue_size_raw):
    """
    Processes the issue_size field from the API response.
    Converts from format like "&#8377;3395.00 Cr" to "3395.00 Cr"
    """
    if not issue_size_raw or issue_size_raw == 'N/A':
        return 'N/A'
    
    # Remove HTML entities for rupee symbol and other characters
    processed = issue_size_raw.replace('&#8377;', '').replace('₹', '')
    # Remove any leading/trailing whitespace
    processed = processed.strip()
    
    return processed if processed else 'N/A'

def download_logo(logo_url, company_name, ipo_id, base_dir="download/investorgain/logo"):
    """
    Downloads a company logo from the given URL and saves it locally.
    
    Args:
        logo_url (str): The URL of the company logo
        company_name (str): The company name for filename generation
        ipo_id (str): The IPO ID for unique identification
        base_dir (str): The base directory path for saving logos
    
    Returns:
        str: The local file path if successful, None if failed
    """
    if not logo_url or logo_url == 'N/A' or logo_url == '':
        return None
    
    try:
        # Create the directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Parse the URL to get the file extension
        parsed_url = urlparse(logo_url)
        path = parsed_url.path
        
        # Get file extension from URL, default to .png if not found
        if '.' in path:
            file_extension = path.split('.')[-1].lower()
            # Validate common image extensions
            if file_extension not in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg']:
                file_extension = 'png'
        else:
            file_extension = 'png'
        
        # Clean company name for filename (remove special characters)
        clean_company_name = re.sub(r'[^\w\s-]', '', company_name.strip())
        clean_company_name = re.sub(r'[-\s]+', '_', clean_company_name)
        
        # Create filename with company name and IPO ID
        filename = f"{clean_company_name}_{ipo_id}.{file_extension}"
        local_path = os.path.join(base_dir, filename)
        
        # Check if file already exists
        if os.path.exists(local_path):
            print(f"  [Logo] Logo already exists: {local_path}")
            return local_path
        
        # Download the logo
        print(f"  [Logo] Downloading logo from: {logo_url}")
        response = requests.get(logo_url, headers=COMMON_HEADERS, timeout=10)
        response.raise_for_status()
        
        # Save the logo to local file
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"  [Logo] Logo saved successfully: {local_path}")
        return local_path
        
    except requests.exceptions.RequestException as e:
        print(f"  [Logo] Error downloading logo from {logo_url}: {e}")
        return None
    except OSError as e:
        print(f"  [Logo] Error saving logo to {local_path}: {e}")
        return None
    except Exception as e:
        print(f"  [Logo] Unexpected error downloading logo: {e}")
        return None

