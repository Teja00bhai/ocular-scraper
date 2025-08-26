"""
Zepto Scraper Implementation
"""
import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple

from playwright.async_api import async_playwright, Response, Page

from src.scrapers.base_scraper import BaseScraper

class ZeptoScraper(BaseScraper):
    """
    Zepto-specific scraper implementation
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000, output_dir: str = "outputs"):
        """
        Initialize the Zepto scraper
        
        Args:
            headless: Whether to run the browser in headless mode
            timeout: Timeout in milliseconds for browser operations
            output_dir: Directory to save output files
        """
        super().__init__(headless, timeout, output_dir)
        self.base_url = "https://www.zeptonow.com"
        self.search_results = {}
        self._current_keyword = None
        
    async def initialize(self) -> bool:
        """
        Initialize the Playwright browser and context
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing Playwright browser")
            
            # Launch Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless
            )
            
            # Create context with viewport size
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set up response interception
            await self._setup_response_interception()
            
            self.logger.info("Playwright browser initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return False
    
    async def close(self) -> None:
        """Clean up resources"""
        self.logger.info("Cleaning up Playwright resources")
        
        if hasattr(self, 'page') and self.page:
            await self.page.close()
            
        if hasattr(self, 'context') and self.context:
            await self.context.close()
            
        if hasattr(self, 'browser') and self.browser:
            await self.browser.close()
            
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
            
        self.logger.info("Playwright resources cleaned up")
    
    async def _setup_response_interception(self):
        """Set up response event listener to capture Zepto API calls"""
        
        async def handle_response(response: Response):
            try:
                # Check if this is the Zepto search API
                if (response.url.startswith("https://api.zepto.com/api/v3/search") or
                    "search" in response.url and response.request.method == "POST"):
                    
                    self.logger.info(f"Intercepted Zepto search API call: {response.url}")
                    
                    try:
                        # Get the JSON response
                        json_data = await response.json()
                        
                        # Extract keyword from request body or use current keyword
                        keyword = self._current_keyword or "unknown"
                        
                        # Optional: Try to extract keyword from request body
                        try:
                            request_body = response.request.post_data
                            if request_body:
                                # Parse request body to get search query
                                import urllib.parse
                                if "query=" in request_body:
                                    keyword = urllib.parse.unquote(
                                        request_body.split("query=")[1].split("&")[0]
                                    )
                        except Exception as e:
                            self.logger.debug(f"Could not extract keyword from request: {e}")
                        
                        # Store the response data
                        self.search_results[keyword] = json_data
                        self.logger.info(f"Successfully captured API data for keyword: '{keyword}'")
                    except Exception as e:
                        self.logger.error(f"Error parsing response JSON: {e}")
                    
            except Exception as e:
                self.logger.error(f"Error handling response: {e}")
        
        # Register the response handler
        self.page.on("response", handle_response)
        self.logger.info("Response interception set up")
    
    async def _wait_for_api_response(self, keyword: str, timeout: int = 10):
        """Wait for API response to be captured"""
        self.logger.info(f"Waiting for API response for keyword: '{keyword}'")
        
        for i in range(timeout * 10):  # Check every 100ms for up to timeout seconds
            if keyword in self.search_results:
                self.logger.info(f"API response captured for '{keyword}'")
                return True
            await asyncio.sleep(0.1)
        
        self.logger.warning(f"Timeout waiting for API response for '{keyword}'")
        return False
    
    async def navigate_to_site(self) -> bool:
        """
        Navigate to Zepto website
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info(f"Navigating to {self.base_url}")
        
        try:
            # Navigate to Zepto
            await self.page.goto(self.base_url, timeout=self.timeout)
            
            # Wait for page to load
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            
            # Check if page loaded successfully
            title = await self.page.title()
            self.logger.info(f"Page loaded with title: {title}")
            
            # Take a screenshot for debugging
            os.makedirs("src/logs", exist_ok=True)
            await self.page.screenshot(path="src/logs/zepto_homepage.png")
            
            return "Zepto" in title
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to Zepto: {e}")
            return False
    
    async def _js_input_search(self, keyword):
        """Helper method to perform search using JavaScript input handling"""
        self.logger.info("Using direct JavaScript input search")
        await self.page.evaluate(f"""
            (keyword) => {{{{  // Double braces to escape f-string
                const inputs = Array.from(document.querySelectorAll('input'));
                const searchInput = inputs.find(input => 
                    (input.placeholder && input.placeholder.toLowerCase().includes('search')) ||
                    (input.getAttribute('aria-label') && input.getAttribute('aria-label').toLowerCase().includes('search')));
                    
                if (searchInput) {{{{  // Double braces to escape f-string
                    searchInput.focus();
                    searchInput.value = keyword;
                    searchInput.dispatchEvent(new Event('input', {{{{ bubbles: true }}}}));
                    searchInput.dispatchEvent(new KeyboardEvent('keydown', {{{{ key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }}}}));
                }}}}
            }}}}
        """, keyword)
    
    async def search_for_keyword(self, keyword: str, region: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for a keyword on Zepto
        
        Args:
            keyword: Search keyword
            region: Optional region/location code (not used for Zepto)
            
        Returns:
            Dict containing search results data
        """
        self.logger.info(f"Searching for '{keyword}'")
        
        # Set current keyword for response tracking
        self._current_keyword = keyword
        
        # Clear any previous search results for this keyword
        if keyword in self.search_results:
            del self.search_results[keyword]
        
        try:
            # Create screenshot directory
            screenshot_dir = "src/logs"
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # Take a full page screenshot for debugging
            await self.page.screenshot(path=f"{screenshot_dir}/before_search.png", full_page=True)
            
            # Try different search input selectors
            search_input = None
            
            # List of possible selectors for the search input
            selectors = [
                "a[aria-label='Search for products']",
                "a[data-testid='search-bar-icon']",
                "a.flex.items-center",
                "div.inline-block a",
                "input[placeholder*='Search']",
                "input[type='search']",
                ".MuiInputBase-input",
                "input.search-input",
                "input[aria-label*='search' i]",
                "[data-testid='search-input']"
            ]
            
            # Try each selector
            for selector in selectors:
                try:
                    search_input = await self.page.query_selector(selector)
                    if search_input:
                        self.logger.info(f"Found search input with selector: {selector}")
                        break
                except Exception as e:
                    self.logger.debug(f"Error with selector {selector}: {e}")
            
            # If we found the search element, use it
            if search_input:
                # Take screenshot of the search area
                await self.page.screenshot(path=f"{screenshot_dir}/search_area.png")
                
                # Check if it's a search icon/link or an input field
                tag_name = await search_input.evaluate("el => el.tagName.toLowerCase()")
                
                if tag_name == 'a':
                    # It's the search icon/link, click it first
                    self.logger.info("Found search icon, clicking it")
                    await search_input.click()
                    
                    # Wait for search input to appear after clicking the icon
                    try:
                        # Wait for any input field to appear after clicking search icon
                        search_input_field = await self.page.wait_for_selector(
                            "input[placeholder*='Search'], input[type='search'], input.search-input",
                            timeout=5000
                        )
                        
                        if search_input_field:
                            # Now we have the actual input field, use it
                            await search_input_field.fill(keyword)
                            await search_input_field.press('Enter')
                            self.logger.info(f"Entered search term: {keyword}")
                        else:
                            self.logger.warning("Could not find search input field after clicking search icon")
                    except Exception as e:
                        self.logger.warning(f"Error finding search input after clicking icon: {e}")
                else:
                    # It's already an input field, use it directly
                    await search_input.click()
                    await search_input.fill(keyword)
                    await search_input.press('Enter')
                    self.logger.info(f"Entered search term: {keyword}")
            else:
                # If we couldn't find the search input, try direct URL navigation
                self.logger.warning("Could not find search input, falling back to URL navigation")
                search_url = f"{self.base_url}/search?q={keyword}"
                await self.page.goto(search_url, timeout=self.timeout)
            
            # Wait for search results
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            
            # Take screenshot of search results
            await self.page.screenshot(path=f"{screenshot_dir}/search_results.png", full_page=True)
            
            # Wait for the API response to be captured
            await self._wait_for_api_response(keyword)
            
            # Return the search results
            if keyword in self.search_results:
                self.logger.info(f"Successfully captured API data for '{keyword}'")
                
                # Save the response to a file
                file_path = self.save_response_to_file(
                    self.search_results[keyword], 
                    f"{keyword.replace(' ', '_')}_results"
                )
                self.logger.info(f"Saved search results to {file_path}")
                
                return self.search_results[keyword]
            else:
                self.logger.warning(f"Could not capture API data for '{keyword}'")
                return {}
        
        except Exception as e:
            self.logger.error(f"Error searching for '{keyword}': {e}")
            return {}
    
    def extract_data(self, response_data: Dict[str, Any], keyword: str) -> List[Dict[str, Any]]:
        """
        Extract structured data from Zepto API response
        
        Args:
            response_data: Raw API response data
            keyword: Search keyword used
            
        Returns:
            List of structured product data dictionaries
        """
        products = []
        
        try:
            # Check if the response has the expected structure
            if not response_data or "layout" not in response_data:
                self.logger.warning(f"Invalid API response format for keyword '{keyword}'")
                return products
                
            # Process each widget in the layout
            for widget in response_data.get("layout", []):
                # Look for product grid widgets
                if widget.get("widgetId", "").startswith("PRODUCT_GRID") or widget.get("widgetName", "").startswith("PRODUCT_GRID"):
                    # Extract product data from resolver
                    resolver_data = widget.get("data", {}).get("resolver", {}).get("data", {})
                    items = resolver_data.get("items", [])
                    
                    # Process each product item
                    for position, item in enumerate(items):
                        product_data = {}
                        
                        # Extract basic product info
                        product_data["search_keyword"] = keyword
                        product_data["position"] = position
                        
                        # Extract product details
                        product = item.get("product", {})
                        product_data["product_id"] = product.get("productId", "")
                        product_data["product_name"] = product.get("name", "")
                        product_data["brand"] = product.get("brand", "")
                        product_data["category"] = product.get("primaryCategoryName", "")
                        product_data["image_url"] = product.get("imageUrl", "")
                        product_data["product_url"] = f"https://www.zeptonow.com/product/{product.get('productId', '')}" if product.get("productId") else ""
                        
                        # Extract pricing information
                        product_data["mrp"] = item.get("mrp", 0) / 100 if item.get("mrp") else 0  # Convert to rupees
                        product_data["selling_price"] = item.get("discountedSellingPrice", 0) / 100 if item.get("discountedSellingPrice") else 0
                        product_data["discount_percent"] = item.get("discountPercent", 0)
                        
                        # Extract additional information
                        product_data["is_in_stock"] = not item.get("outOfStock", True)
                        product_data["available_quantity"] = item.get("availableQuantity", 0)
                        
                        # Extract rating information
                        rating_summary = product.get("ratingSummary", {})
                        product_data["average_rating"] = rating_summary.get("averageRating", 0)
                        product_data["total_ratings"] = rating_summary.get("totalRatings", 0)
                        
                        # Check if product is sponsored/promoted
                        product_data["is_sponsored"] = False
                        if "campaignType" in item or "campaignId" in item:
                            product_data["is_sponsored"] = True
                        
                        # Extract product attributes
                        product_data["weight"] = product.get("weightInGms", 0)
                        product_data["pack_size"] = product.get("packsize", "")
                        product_data["unit_of_measure"] = product.get("unitOfMeasure", "")
                        product_data["nutritional_info"] = product.get("nutritionalInfo", "")
                        
                        products.append(product_data)
                        
            self.logger.info(f"Extracted {len(products)} products for keyword '{keyword}'")
            
        except Exception as e:
            self.logger.error(f"Error extracting products from API response: {e}")
            
        return products
