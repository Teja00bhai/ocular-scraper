#!/usr/bin/env python3
"""
QuickCommerce Scraper - Main controller file for scraping multiple e-commerce platforms
"""
import os
import sys
import json
import asyncio
import argparse
import logging
from typing import Dict, List, Any, Optional

# Add the project root directory to Python path to fix import issues
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.factory.scraper_factory import ScraperFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QuickCommScraper")

async def scrape_platform(
    platform: str,
    keywords: List[str],
    headless: bool = True,
    output_dir: str = "src/outputs",
    timeout: int = 30000,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scrape a platform for multiple keywords and regions
    
    Args:
        platform: Platform name (e.g., 'zepto', 'blinkit')
        keywords: List of search keywords
        regions: Optional list of regions/locations
        headless: Whether to run in headless mode
        output_dir: Directory to save output files
        timeout: Timeout in milliseconds for browser operations
        
    Returns:
        Dictionary with results summary
    """
    # Create scraper using factory
    scraper = ScraperFactory.create_scraper(
        platform=platform,
        headless=headless,
        timeout=timeout,
        output_dir=output_dir,
        location=location
    )
    
    if not scraper:
        logger.error(f"Failed to create scraper for platform: {platform}")
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        results = {"platform": platform, "data_captured": 0, "keywords": {}}
        
        async with scraper:
            # Navigate to site
            site_loaded = await scraper.navigate_to_site()
            
            if not site_loaded:
                logger.error(f"Failed to navigate to {platform} site")
                results["success"] = False
                results["error"] = f"Failed to navigate to {platform} site"
                return results
            
            for keyword in keywords:
                logger.info(f"Searching for '{keyword}' on {platform}...")
                await scraper.search_for_keyword(keyword)
                
                # Save raw API responses first for examination
                raw_responses_file = await scraper.save_raw_responses(keyword)
                if raw_responses_file:
                    logger.info(f"Saved raw API responses for '{keyword}' to {raw_responses_file}")
                
                # # Extract structured data from all collected API responses
                # extracted_data = scraper.extract_data(keyword)
                
                # if extracted_data:
                #     # Save the extracted data to a file
                #     output_file = scraper.save_results(keyword, extracted_data)
                    
                #     results["keywords"][keyword] = {
                #         "success": True,
                #         "products_found": len(extracted_data),
                #         "output_file": output_file,
                #         "raw_responses_file": raw_responses_file
                #     }
                #     results["data_captured"] += 1
                #     logger.info(f"Saved {len(extracted_data)} products for '{keyword}' to {output_file}")
                # else:
                #     results["keywords"][keyword] = {
                #         "success": False, 
                #         "reason": "No products found",
                #         "raw_responses_file": raw_responses_file
                #     }
                #     logger.warning(f"No products found for '{keyword}' on {platform}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error scraping {platform}: {e}")
        return {"platform": platform, "error": str(e)}
    
    return results

def main():
    """Main entry point for the script"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="QuickCommerce Scraper")
    parser.add_argument("--platform", default="zepto", help="Platform to scrape (default: zepto)")
    parser.add_argument("--keywords", help="Search keywords (comma-separated)")
    parser.add_argument("--location", help="Delivery location to set (e.g., 'Mumbai, Maharashtra')")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--output-dir", default="src/outputs", help="Directory to save search results data")
    parser.add_argument("--timeout", type=int, default=30000, help="Timeout in milliseconds for browser operations")
    parser.add_argument("--list-platforms", action="store_true", help="List available platforms and exit")
    
    args = parser.parse_args()
    
    # Check if keywords are provided when not just listing platforms
    if not args.list_platforms and not args.keywords:
        parser.error("--keywords is required unless --list-platforms is specified")
    
    # List available platforms if requested
    if args.list_platforms:
        platforms = ScraperFactory.get_available_platforms()
        print("Available platforms:")
        for platform in platforms:
            print(f"  - {platform}")
        return
    
    # If not just listing platforms, process keywords
    if not args.list_platforms:
        keywords = [k.strip() for k in args.keywords.split(",")]
        
        logger.info(f"Starting {args.platform} search with keywords: {keywords}")
        if args.location:
            logger.info(f"Setting delivery location to: {args.location}")
    
    # Run the scraper if not just listing platforms
    if not args.list_platforms:
        results = asyncio.run(scrape_platform(
            platform=args.platform,
            keywords=keywords,
            headless=args.headless,
            output_dir=args.output_dir,
            timeout=args.timeout,
            location=args.location
        ))
        
        # Print summary
        logger.info("Search results summary:")
        if results["success"]:
            print(f"Platform: {results['platform']}")
            print(f"Data captured: {results['data_captured']} responses")
            
            for keyword, keyword_results in results["keywords"].items():
                status = "✓" if keyword_results["success"] else "✗"
                products = keyword_results.get("products_found", 0)
                output_file = keyword_results.get("output_file", "")
                output_info = f" → {output_file}" if output_file else ""
                print(f"  - '{keyword}': {status} ({products} products){output_info}")
        else:
            print(f"Platform: {results['platform']} - Failed: {results.get('error', 'Unknown error')}")
    

if __name__ == "__main__":
    main()
