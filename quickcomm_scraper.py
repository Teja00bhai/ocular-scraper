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
    regions: Optional[List[str]] = None,
    headless: bool = True,
    output_dir: str = "src/outputs",
    timeout: int = 30000
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
        output_dir=output_dir
    )
    
    if not scraper:
        logger.error(f"Failed to create scraper for platform: {platform}")
        return {
            "platform": platform,
            "success": False,
            "error": "Failed to create scraper"
        }
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize results
    results = {
        "platform": platform,
        "success": True,
        "keywords": {},
        "data_captured": 0
    }
    
    try:
        # Initialize scraper
        async with scraper:
            # Navigate to site
            site_loaded = await scraper.navigate_to_site()
            
            if not site_loaded:
                logger.error(f"Failed to navigate to {platform} site")
                results["success"] = False
                results["error"] = f"Failed to navigate to {platform} site"
                return results
            
            # Process each keyword
            for keyword in keywords:
                logger.info(f"Searching for '{keyword}' on {platform}")
                
                # If regions are provided, search for each region
                if regions and len(regions) > 0:
                    keyword_results = {}
                    
                    for region in regions:
                        logger.info(f"Searching in region '{region}'")
                        response_data = await scraper.search_for_keyword(keyword, region)
                        
                        # Extract structured data
                        if response_data:
                            extracted_data = scraper.extract_data(response_data, keyword)
                            keyword_results[region] = {
                                "success": True,
                                "products_found": len(extracted_data)
                            }
                            results["data_captured"] += 1
                        else:
                            keyword_results[region] = {
                                "success": False,
                                "products_found": 0
                            }
                    
                    results["keywords"][keyword] = keyword_results
                else:
                    # Search without region
                    response_data = await scraper.search_for_keyword(keyword)
                    
                    # Extract structured data
                    if response_data:
                        extracted_data = scraper.extract_data(response_data, keyword)
                        results["keywords"][keyword] = {
                            "success": True,
                            "products_found": len(extracted_data)
                        }
                        results["data_captured"] += 1
                    else:
                        results["keywords"][keyword] = {
                            "success": False,
                            "products_found": 0
                        }
    
    except Exception as e:
        logger.error(f"Error scraping {platform}: {e}")
        results["success"] = False
        results["error"] = str(e)
    
    return results

def main():
    """Main entry point for the script"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="QuickCommerce Scraper")
    parser.add_argument("--platform", default="zepto", help="Platform to scrape (default: zepto)")
    parser.add_argument("--keywords", help="Search keywords (comma-separated)")
    parser.add_argument("--regions", help="Regions/locations to search in (comma-separated)")
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
    
    # If not just listing platforms, process keywords and regions
    if not args.list_platforms:
        keywords = [k.strip() for k in args.keywords.split(",")]
        regions = [r.strip() for r in args.regions.split(",")] if args.regions else None
        
        logger.info(f"Starting {args.platform} search with keywords: {keywords}")
        if regions:
            logger.info(f"Searching in regions: {regions}")
    
    # Run the scraper if not just listing platforms
    if not args.list_platforms:
        results = asyncio.run(scrape_platform(
            platform=args.platform,
            keywords=keywords,
            regions=regions,
            headless=args.headless,
            output_dir=args.output_dir,
            timeout=args.timeout
        ))
        
        # Print summary
        logger.info("Search results summary:")
        if results["success"]:
            print(f"Platform: {results['platform']}")
            print(f"Data captured: {results['data_captured']} responses")
            
            for keyword, keyword_results in results["keywords"].items():
                if isinstance(keyword_results, dict) and "success" in keyword_results:
                    # Single region case
                    status = "✓" if keyword_results["success"] else "✗"
                    products = keyword_results.get("products_found", 0)
                    print(f"  - '{keyword}': {status} ({products} products)")
                else:
                    # Multiple regions case
                    print(f"  - '{keyword}':")
                    for region, region_results in keyword_results.items():
                        status = "✓" if region_results["success"] else "✗"
                        products = region_results.get("products_found", 0)
                        print(f"    - Region '{region}': {status} ({products} products)")
        else:
            print(f"Platform: {results['platform']} - Failed: {results.get('error', 'Unknown error')}")
    

if __name__ == "__main__":
    main()
