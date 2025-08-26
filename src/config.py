"""
Configuration settings for Zepto API Scraper
"""
import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "outputs"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Browser settings
HEADLESS = True
WINDOW_SIZE = "1920,1080"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
CHROME_DEBUGGING_PORT = 9222

# Zepto settings
ZEPTO_BASE_URL = "https://www.zeptonow.com"

# Search settings
SEARCH_KEYWORDS = [
    'hair care', 'shampoo', 'conditioner', 'hair oil', 
    'face wash', 'moisturizer', 'sunscreen', 'toothpaste',
    'snacks', 'biscuits', 'chocolates', 'soft drinks'
]

# Region settings (pincodes)
REGIONS = ['560001', '400001', '110001']  # Bangalore, Mumbai, Delhi

# Timing settings
REQUEST_TIMEOUT = 60  # seconds
PAGE_LOAD_WAIT = 20  # seconds
SEARCH_RESULTS_WAIT = 15  # seconds
RATE_LIMIT_DELAY = 2  # seconds between searches

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# API patterns to capture
API_PATTERNS = [
    "api.zepto.com/api/v3/search",
    "api.zepto.com/api/v1/search"
]
