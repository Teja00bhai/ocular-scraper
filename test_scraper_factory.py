#!/usr/bin/env python3
"""
Test script for QuickCommerce Scraper Factory implementation
"""
import os
import sys
import asyncio
import argparse
import logging
from typing import List

# Add the project root directory to Python path to fix import issues
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.factory.scraper_factory import ScraperFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestScraperFactory")

async def test_scraper(platform: str, keywords: List[str], headless: bool = True):
    """
    Test a scraper implementation
    
    Args:
        platform: Platform name (e.g., 'zepto', 'blinkit')
        keywords: List of search keywords
        headless: Whether to run in headless mode
    """
    logger.info(f"Testing {platform} scraper with keywords: {keywords}")
    
    # Create scraper using factory
    scraper = ScraperFactory.create_scraper(
        platform=platform,
        headless=headless,
        timeout=30000,
        output_dir="src/outputs"
    )
    
    if not scraper:
        logger.error(f"Failed to create scraper for platform: {platform}")
        return
    
    try:
        # Initialize scraper
        async with scraper:
            # Navigate to site
            logger.info(f"Navigating to {platform} site")
            site_loaded = await scraper.navigate_to_site()
            
            if not site_loaded:
                logger.error(f"Failed to navigate to {platform} site")
                return
            
            logger.info(f"Successfully navigated to {platform} site")
            
            # Process each keyword
            for keyword in keywords:
                logger.info(f"Searching for '{keyword}' on {platform}")
                
                # Search for keyword
                response_data = await scraper.search_for_keyword(keyword)
                
                # Check if we got a response
                if response_data:
                    logger.info(f"Successfully got response for '{keyword}'")
                    
                    # Extract structured data
                    extracted_data = scraper.extract_data(response_data, keyword)
                    logger.info(f"Extracted {len(extracted_data)} products for '{keyword}'")
                    
                    # Print first product as example
                    if extracted_data:
                        logger.info(f"Example product: {extracted_data[0]}")
                else:
                    logger.warning(f"No response data for '{keyword}'")
    
    except Exception as e:
        logger.error(f"Error testing {platform} scraper: {e}")

def main():
    """Main entry point for the test script"""
    parser = argparse.ArgumentParser(description="Test QuickCommerce Scraper Factory")
    parser.add_argument("--platform", default="zepto", help="Platform to test (default: zepto)")
    parser.add_argument("--keywords", default="milk,bread", help="Search keywords (comma-separated)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--list-platforms", action="store_true", help="List available platforms and exit")
    
    args = parser.parse_args()
    
    # List available platforms if requested
    if args.list_platforms:
        platforms = ScraperFactory.get_available_platforms()
        print("Available platforms:")
        for platform in platforms:
            print(f"  - {platform}")
        return
    
    # Process keywords
    keywords = [k.strip() for k in args.keywords.split(",")]
    
    # Create output directory
    os.makedirs("src/outputs", exist_ok=True)
    
    # Run the test
    asyncio.run(test_scraper(args.platform, keywords, args.headless))

if __name__ == "__main__":
    main()
