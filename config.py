# config.py

# Base URL for the Investorgain website
BASE_URL = "https://www.investorgain.com"

# API URLs
IPO_LIST_API_URL = "https://webnodejs.investorgain.com/cloud/ipo/list-read"
GMP_API_URL_TEMPLATE = "https://webnodejs.investorgain.com/cloud/ipo/ipo-gmp-read/{ipo_id}/true"
SUBSCRIPTION_API_URL_TEMPLATE = "https://webnodejs.investorgain.com/cloud/ipo/ipo-subscription-read/{ipo_id}"

# Year-wise IPO Summary API URLs
IPO_SUMMARY_API_URL_TEMPLATE = "https://webnodejs.investorgain.com/cloud/report/data-read/394/1/7/{year}/2025-26/0/all"

# Expected total records by year (as of July 2025)
EXPECTED_RECORDS_BY_YEAR = {
    2025: 141,
    2024: 337,
    2023: 244,
    2022: 151,
    2021: 121,
    2020: 36,
    2019: 6
}

# Common HTTP Headers to mimic a browser
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# --- Database Configuration ---
# Set to True to use SQL Server, False to use SQLite
USE_SQL_SERVER = False 

# SQLite Database Configuration
SQLITE_DB_NAME = "ipo_data_investorgain.db"

# SQL Server Database Configuration
SQL_SERVER_DB_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': '192.168.102.120',
    'database': 'E-IPO',
    'username': 'sa',
    'password': '963852'
}

# --- Scraper settings ---
MAX_WORKERS = 5 # Number of concurrent threads for scraping detail pages
REQUEST_TIMEOUT = 15 # Timeout for HTTP requests in seconds
RETRY_ATTEMPTS = 3 # Number of retry attempts for failed requests
RETRY_BACKOFF_FACTOR = 2 # Factor for exponential backoff (2^attempt_number)

# --- Logo Download Settings ---
DOWNLOAD_LOGOS = True # Set to True to download logos locally
LOGO_DOWNLOAD_DIR = "company_logos" # Directory to save downloaded logos

# Log file (optional, if you want to implement file logging)
# LOG_FILE = "scraper_log.log"