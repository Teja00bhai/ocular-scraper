#!/usr/bin/env python3
"""
Example usage of the QuickCommerce Scraper with Factory Pattern
"""
import os
import sys
import asyncio
import logging

# Add the project root directory to Python path to fix import issues
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.factory.scraper_factory import ScraperFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ExampleUsage")

async def scrape_multiple_platforms(keywords, platforms=None):
    """
    Example of scraping multiple platforms for the same keywords
    
    Args:
        keywords: List of keywords to search for
        platforms: List of platforms to scrape (default: all available)
    """
    if platforms is None:
        platforms = ScraperFactory.get_available_platforms()
    
    logger.info(f"Scraping platforms: {platforms}")
    logger.info(f"Searching for keywords: {keywords}")
    
    results = {}
    
    for platform in platforms:
        logger.info(f"Creating {platform} scraper")
        
        # Create scraper using factory
        scraper = ScraperFactory.create_scraper(
            platform=platform,
            headless=True,
            timeout=30000,
            output_dir="src/outputs"
        )
        
        if not scraper:
            logger.error(f"Failed to create scraper for {platform}")
            continue
        
        platform_results = {}
        
        try:
            # Initialize and use scraper with context manager
            async with scraper:
                # Navigate to site
                site_loaded = await scraper.navigate_to_site()
                
                if not site_loaded:
                    logger.error(f"Failed to navigate to {platform} site")
                    continue
                
                # Search for each keyword
                for keyword in keywords:
                    logger.info(f"Searching for '{keyword}' on {platform}")
                    
                    # Search for keyword
                    response_data = await scraper.search_for_keyword(keyword)
                    
                    if response_data:
                        # Extract structured data
                        extracted_data = scraper.extract_data(response_data, keyword)
                        platform_results[keyword] = {
                            "success": True,
                            "products_found": len(extracted_data),
                            "first_product": extracted_data[0] if extracted_data else None
                        }
                    else:
                        platform_results[keyword] = {
                            "success": False,
                            "products_found": 0
                        }
        
        except Exception as e:
            logger.error(f"Error scraping {platform}: {e}")
            platform_results["error"] = str(e)
        
        results[platform] = platform_results
    
    return results

def print_results(results):
    """Print results in a readable format"""
    print("\n===== SCRAPING RESULTS =====\n")
    
    for platform, platform_results in results.items():
        print(f"Platform: {platform}")
        
        if "error" in platform_results:
            print(f"  Error: {platform_results['error']}")
            continue
        
        for keyword, keyword_results in platform_results.items():
            success = "✓" if keyword_results.get("success", False) else "✗"
            products = keyword_results.get("products_found", 0)
            print(f"  Keyword '{keyword}': {success} ({products} products)")
            
            # Show first product as example
            first_product = keyword_results.get("first_product")
            if first_product:
                print("    Example product:")
                print(f"      Name: {first_product.get('product_name', 'N/A')}")
                print(f"      Price: {first_product.get('selling_price', 'N/A')}")
                print(f"      Brand: {first_product.get('brand', 'N/A')}")
        
        print()

async def main():
    """Main entry point"""
    # Example keywords
    keywords = ["milk", "bread"]
    
    # Example 1: Scrape all available platforms
    # results = await scrape_multiple_platforms(keywords)
    
    # Example 2: Scrape specific platforms
    results = await scrape_multiple_platforms(keywords, ["zepto", "blinkit"])
    
    # Print results
    print_results(results)

if __name__ == "__main__":
    asyncio.run(main())
