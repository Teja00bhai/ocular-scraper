# QuickComm Scraper Suite

## Zepto API Data Extraction Tool

A modern browser automation tool for extracting product data from Zepto's backend APIs using Playwright for superior performance and anti-detection capabilities.

### Architecture Overview

- **Playwright Engine**: Uses modern Playwright framework for performance and reliability
- **Factory Pattern**: Built with extensible architecture to support multiple e-commerce platforms
- **API Interception**: Captures backend API calls to extract structured data

### Features

- Automated extraction of product data from Zepto search results
- Multi-keyword search support
- Automated location selection for delivery address
- Position-weighted Share of Voice (SOV) calculation
- Detailed product information extraction (pricing, ratings, availability)
- Sponsored product identification
- Robust error handling and retry mechanisms
- Comprehensive logging
- Production-ready with anti-detection capabilities

### Installation

#### Option 1: Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/quickcomm-scraper.git
cd quickcomm-scraper

# Install dependencies
pip install -r requirements.txt

# For Playwright mode: Install browser binaries
pip install playwright
python -m playwright install chromium
```

#### Option 2: Using Conda (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/quickcomm-scraper.git
cd quickcomm-scraper

# Create conda environment
conda env create -f environment.yml

# Activate the environment
conda activate scraper

# Install Playwright browser binaries
python -m playwright install chromium

# Alternatively, create manually
conda create --name scraper python=3.10
conda activate scraper
pip install -r requirements.txt
python -m playwright install chromium
```

### Usage

```bash
# Basic usage with default platform (Zepto) and keywords
python quickcomm_scraper.py --keywords "milk,bread"


# Set delivery location
python quickcomm_scraper.py --keywords "milk,bread" --location "Mumbai, Maharashtra"

# Specify output directory
python quickcomm_scraper.py --keywords "milk,bread" --output-dir "custom_outputs"

# Run in headless mode
python quickcomm_scraper.py --keywords "milk,bread" --headless

# List available platforms
python quickcomm_scraper.py --list-platforms

# Test specific platform implementation
python test_scraper_factory.py --platform zepto --keywords "milk,bread"
```

### Project Structure

```
src/
├── __init__.py         # Package initialization
├── config/             # Configuration settings
├── factory/            # Factory pattern implementation
│   ├── __init__.py     # Package initialization
│   └── scraper_factory.py # Factory for creating scrapers
├── scrapers/           # Scraper implementations
│   ├── __init__.py     # Package initialization
│   ├── base_scraper.py # Abstract base scraper class
│   └── zepto_scraper.py # Zepto implementation
├── utils/              # Utility functions
├── outputs/            # CSV/JSON results
└── logs/               # Debug and execution logs
├── config.py           # Configuration settings
├── data_processor.py   # Data processing and SOV calculation
```

### Output Files

- **zepto_products_{timestamp}.csv**: Detailed product data
- **sov_analysis_{timestamp}.csv**: Share of Voice analysis by brand, keyword, and region
- **summary_report_{timestamp}.json**: Summary statistics of the extraction

### Extending for Other Platforms

The architecture uses the Factory Pattern for easy extension to other e-commerce platforms:

1. Create a new scraper class in `src/scrapers/` that inherits from `BaseScraper`
2. Implement all required abstract methods:
   - `initialize()`: Set up browser and other resources
   - `navigate_to_site()`: Navigate to the platform's website
   - `search_for_keyword()`: Perform search and capture API responses
   - `extract_data()`: Process API responses into structured data
   - `close()`: Clean up resources
3. Register your new scraper in `ScraperFactory._scrapers` dictionary

**Example:**

```python
# In src/scrapers/new_platform_scraper.py
from src.scrapers.base_scraper import BaseScraper

class NewPlatformScraper(BaseScraper):
    # Implement required methods
    ...

# In src/factory/scraper_factory.py
from src.scrapers.new_platform_scraper import NewPlatformScraper

class ScraperFactory:
    _scrapers = {
        "zepto": ZeptoScraper,
        "new_platform": NewPlatformScraper,  # Register new scraper
    }
```
