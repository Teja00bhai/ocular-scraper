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
    
    def __init__(self, headless: bool = True, timeout: int = 30000, output_dir: str = "outputs", location: Optional[str] = None):
        """
        Initialize the Zepto scraper
        
        Args:
            headless: Whether to run the browser in headless mode
            timeout: Timeout in milliseconds for browser operations
            output_dir: Directory to save output files
            location: Optional location to set (e.g., "Mumbai, Maharashtra")
        """
        super().__init__(headless, timeout, output_dir)
        self.base_url = "https://www.zeptonow.com"
        self.search_results = {}
        self._current_keyword = None
        self.location = location
        
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
                # print("got this api call", response.url)
                if (response.url.endswith("/search") and response.request.method == "POST"):

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
                        
                        # Initialize version tracking if needed
                        if not hasattr(self, 'response_versions'):
                            self.response_versions = {}
                        if keyword not in self.response_versions:
                            self.response_versions[keyword] = 0
                        
                        # Increment version for this keyword
                        self.response_versions[keyword] += 1
                        
                        # Store the response data
                        self.search_results[keyword] = json_data
                        self.logger.info(f"Successfully captured API data for keyword: '{keyword}' (version {self.response_versions[keyword]})")
                    except Exception as e:
                        self.logger.error(f"Error parsing response JSON: {e}")
                    
            except Exception as e:
                self.logger.error(f"Error handling response: {e}")
        
        # Register the response handler
        self.page.on("response", handle_response)
        self.logger.info("Response interception set up")
    
    async def _wait_for_api_response(self, keyword: str, timeout: int = 10):
        """Wait for new API response to be captured"""
        self.logger.info(f"Waiting for API response for keyword: '{keyword}'")
        
        # Initialize version tracking if needed
        if not hasattr(self, 'response_versions'):
            self.response_versions = {}
        if keyword not in self.response_versions:
            self.response_versions[keyword] = 0
        
        # Get current version for this keyword
        current_version = self.response_versions.get(keyword, 0)
        
        for i in range(timeout * 30):  # Check every 100ms for up to timeout seconds
            # Check if we have a new version
            if keyword in self.search_results and self.response_versions.get(keyword, 0) >= current_version:
                self.logger.info(f"New API response captured for '{keyword}' (version {self.response_versions[keyword]})")
                return True
            await asyncio.sleep(0.1)
        
        self.logger.warning(f"Timeout waiting for new API response for '{keyword}'")
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
            
            # # Take a screenshot for debugging
            # os.makedirs("src/logs", exist_ok=True)
            # await self.page.screenshot(path="src/logs/zepto_homepage.png")
            
            # Set location if provided
            if self.location:
                await self._set_location(self.location)
            
            return "Zepto" in title
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to Zepto: {e}")
            return False
        
    async def _set_location(self, location: str) -> bool:
        """
        Set the delivery location
        
        Args:
            location: Location string (e.g., "Mumbai, Maharashtra")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Setting location to: {location}")
            
            # Take screenshot before location change
            # await self.page.screenshot(path="src/logs/before_location_change.png")
            
            # Find and click the location button using XPath
            location_button_xpath = "//button[@aria-label='Select Location']"
            try:
                # Use wait_for_selector with XPath
                location_button = await self.page.wait_for_selector(location_button_xpath, timeout=5000)
                if location_button:
                    self.logger.info(f"Found location button with XPath: {location_button_xpath}")
                    await location_button.click()
                    self.logger.info("Clicked location button")
                else:
                    raise Exception("Location button is null")
            except Exception as e:
                self.logger.error(f"Could not find location button: {e}")
                return False
            
            # Wait for the location modal to appear using XPath for the input field
            search_input_xpath = "//input[@placeholder='Search a new address']"
            try:
                await self.page.wait_for_selector(search_input_xpath, timeout=5000)
                self.logger.info("Location modal appeared")
                
                # # Take screenshot of location modal
                # await self.page.screenshot(path="src/logs/location_modal.png")
            except Exception as e:
                self.logger.error(f"Location modal did not appear: {e}")
                return False
            
            # Find and fill the location search input using XPath
            try:
                search_input = await self.page.wait_for_selector(search_input_xpath, timeout=5000)
                if search_input:
                    self.logger.info(f"Found location search input with XPath: {search_input_xpath}")
                    await search_input.fill(location)
                    self.logger.info(f"Entered location: {location}")
                    
                    # Wait a moment for suggestions to load - use explicit wait instead of sleep
                    await self.page.wait_for_timeout(1000)
                else:
                    raise Exception("Search input is null")
            except Exception as e:
                self.logger.error(f"Could not find location search input: {e}")
                return False
            
            # Take screenshot of location suggestions
            # await self.page.screenshot(path="src/logs/location_suggestions.png")
            
            # Try to find and click on the first suggestion using data-testid attribute
            suggestion_xpath = "//div[@data-testid='address-search-item']"
            try:
                suggestion = await self.page.wait_for_selector(suggestion_xpath, timeout=3000)
                if suggestion:
                    await suggestion.click()
                    self.logger.info("Clicked on location suggestion using data-testid")
                else:
                    raise Exception("No suggestion element found")
            except Exception as e:
                self.logger.warning(f"Could not find location suggestion with data-testid: {e}")
                
                # Fallback: Try to find any clickable element in the suggestions list
                try:
                    # Look for any div with role="button" that might be a suggestion
                    clicked = await self.page.evaluate("""
                        () => {
                            const suggestions = document.querySelectorAll('div[role="button"]');
                            for (const suggestion of suggestions) {
                                if (suggestion.textContent && suggestion.textContent.length > 5) {
                                    suggestion.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    
                    if not clicked:
                        self.logger.warning("Could not find any location suggestions")
                        # Close the modal by pressing Escape
                        await self.page.keyboard.press('Escape')
                        return False
                    else:
                        self.logger.info("Used JavaScript fallback to click on a suggestion")
                except Exception as e:
                    self.logger.warning(f"JavaScript fallback also failed: {e}")
                    return False
            
            # Wait for confirm button and click it - using XPath with contains for partial match on aria-label
            confirm_button_xpath = "//button[contains(@aria-label, 'Confirm')]"
            try:
                # Use explicit wait with timeout
                confirm_button = await self.page.wait_for_selector(confirm_button_xpath, timeout=5000)
                if confirm_button:
                    await confirm_button.click()
                    self.logger.info("Clicked confirm location button")
                    
                    # Wait a moment for the confirmation to process
                    await self.page.wait_for_timeout(1000)
                else:
                    self.logger.warning("Confirm button found but is null")
            except Exception as e:
                self.logger.warning(f"Could not find confirm button: {e}")
                # Not critical, might not be needed in some cases
            
            # Check if we're back on the main page (modal closed)
            try:
                # Wait for the search box to be visible, indicating we're back on the main page
                await self.page.wait_for_selector("//a[@aria-label='Search for products']", timeout=5000)
                self.logger.info("Successfully set location and returned to main page")
            except Exception as e:
                self.logger.warning(f"Could not confirm return to main page: {e}")
                # Try to press escape to close any remaining modals
                await self.page.keyboard.press('Escape')
            
            # Take screenshot after location change
            # await self.page.screenshot(path="src/logs/after_location_change.png")
            
            self.logger.info(f"Successfully set location to: {location}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting location: {e}")
            # Try to close the modal if it's still open
            try:
                await self.page.keyboard.press('Escape')
            except:
                pass
            return False
    
    async def search_for_keyword(self, keyword: str) -> Dict[str, Any]:
        """
        Search for a keyword on Zepto and capture API responses
        
        Args:
            keyword: Search keyword
            
        Returns:
            Dict[str, Any]: The search results data
        """
        try:
            # Store current keyword for API interception
            self._current_keyword = keyword
            
            # Try different search input selectors
            search_input = None
            search_selectors = [
                "a[aria-label='Search for products']",
                "input[placeholder*='Search']",
                "input[type='search']",
                "div[role='search']",
                ".search-input",
                "[data-testid='search-input']",
                "button[aria-label='Search']",
                ".search-bar",
                "#search-input"
            ]
            
            for selector in search_selectors:
                try:
                    search_input = await self.page.wait_for_selector(selector, timeout=2000)
                    if search_input:
                        self.logger.info(f"Found search input with selector: {selector}")
                        break
                except Exception:
                    continue
            
            # If we found the search element, use it
            if search_input:
                # Check if it's a search icon/link or an input field
                tag_name = await search_input.evaluate("el => el.tagName.toLowerCase()")
                
                if tag_name == "a" or tag_name == "button" or tag_name == "div":
                    # It's a search icon or button, click it first
                    self.logger.info("Found search icon, clicking it")
                    await search_input.click()
                    await self.page.wait_for_load_state("networkidle", timeout=5000)
                    
                    # Now try to find the actual input field
                    try:
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
                self.logger.info(f"Navigated to search URL: {search_url}")
            
            # Wait for search results to load
            await self.page.wait_for_load_state("networkidle", timeout=5000)
            await self._wait_for_api_response(keyword, timeout=5)
            
            # Initialize API responses collection if needed
            if not hasattr(self, 'api_responses'):
                self.api_responses = {}
            
            if keyword not in self.api_responses:
                self.api_responses[keyword] = []
            
            # Add the initial response to our collection
            if keyword in self.search_results:
                self.api_responses[keyword].append(self.search_results[keyword])
                self.logger.info(f"Captured initial API response for '{keyword}'")
            
            # Scroll to load more results - minimal implementation
            max_scrolls = 5
            for i in range(max_scrolls):
                # Use END key for more effective scrolling
                await self.page.keyboard.press('End')
                await self.page.wait_for_load_state("networkidle", timeout=3000)
                await asyncio.sleep(1.5)
                
                # Capture new responses if available
                if keyword in self.search_results and self.search_results[keyword] not in self.api_responses[keyword]:
                    self.api_responses[keyword].append(self.search_results[keyword])
                    self.logger.info(f"Captured new API response after scroll #{i+1}")
                elif i >= 2:
                    # Stop if no new responses after 3 attempts
                    break
            
            # Return the collected API responses
            total_responses = len(self.api_responses.get(keyword, []))
            self.logger.info(f"Finished scrolling. Captured {total_responses} API responses")
            
            return self.api_responses.get(keyword, [])
            
        except Exception as e:
            self.logger.error(f"Error searching for '{keyword}': {e}")
            return {}
    
    def extract_data(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Extract structured data from all Zepto API responses collected for a keyword
        
        Args:
            keyword: Search keyword used
            
        Returns:
            List of structured product data dictionaries
        """
        all_products = []
        seen_product_ids = set()  # To avoid duplicate products
        
        try:
            # Check if we have API responses for this keyword
            if not hasattr(self, 'api_responses') or keyword not in self.api_responses or not self.api_responses[keyword]:
                # Fall back to single response if api_responses not available
                if keyword in self.search_results:
                    responses_to_process = [self.search_results[keyword]]
                    self.logger.info(f"Using single search result for '{keyword}'")
                else:
                    self.logger.warning(f"No API responses found for keyword '{keyword}'")
                    return all_products
            else:
                responses_to_process = self.api_responses[keyword]
                self.logger.info(f"Processing {len(responses_to_process)} API responses for '{keyword}'")
            
            # Process each API response
            for response_index, response_data in enumerate(responses_to_process):
                products = []
                
                # Check if the response has the expected structure
                if not response_data or "layout" not in response_data:
                    self.logger.warning(f"Invalid API response format for response #{response_index}")
                    continue
                    
                # Process each widget in the layout
                for widget in response_data.get("layout", []):
                    # Look for product grid widgets
                    if widget.get("widgetId", "").startswith("PRODUCT_GRID") or widget.get("widgetName", "").startswith("PRODUCT_GRID"):
                        # Extract product data from resolver
                        resolver_data = widget.get("data", {}).get("resolver", {}).get("data", {})
                        items = resolver_data.get("items", [])
                        
                        # Process each product item
                        for position, item in enumerate(items):
                            # Get product ID to check for duplicates
                            product = item.get("product", {})
                            product_id = product.get("id", "")
                            
                            # Skip if we've already seen this product
                            if product_id and product_id in seen_product_ids:
                                continue
                            
                            # Mark as seen
                            if product_id:
                                seen_product_ids.add(product_id)
                            
                            product_data = {}
                            
                            # Extract basic product info
                            product_data["search_keyword"] = keyword
                            product_data["position"] = position
                            product_data["page"] = response_index + 1  # Add page number
                            
                            # Extract product details
                            product_data["product_id"] = product_id
                            product_data["product_name"] = product.get("name", "")
                            product_data["brand"] = product.get("brand", "")
                            product_data["category"] = product.get("primaryCategoryName", "")
                            
                            # Extract image URL from product variant
                            product_variant = item.get("productVariant", {})
                            images = product_variant.get("images", [])
                            image_url = images[0].get("path", "") if images else ""
                            product_data["image_url"] = image_url
                            
                            # Construct product URL
                            product_data["product_url"] = f"https://www.zeptonow.com/product/{product_id}" if product_id else ""
                            
                            # Extract pricing information
                            product_data["mrp"] = item.get("mrp", 0) / 100 if item.get("mrp") else 0  # Convert to rupees
                            product_data["selling_price"] = item.get("discountedSellingPrice", 0) / 100 if item.get("discountedSellingPrice") else 0
                            product_data["discount_percent"] = item.get("discountPercent", 0)
                            
                            # Extract additional information
                            product_data["is_in_stock"] = not item.get("outOfStock", True)
                            product_data["available_quantity"] = item.get("availableQuantity", 0)
                            
                            # Extract rating information
                            rating_summary = product_variant.get("ratingSummary", {})
                            product_data["average_rating"] = rating_summary.get("averageRating", 0)
                            product_data["total_ratings"] = rating_summary.get("totalRatings", 0)
                            
                            # Check if product is sponsored/promoted
                            product_data["is_sponsored"] = False
                            if "campaignType" in item or "campaignId" in item or (item.get("pricingCampaigns") and len(item.get("pricingCampaigns", [])) > 0):
                                product_data["is_sponsored"] = True
                            
                            # Extract product attributes
                            product_data["weight"] = product_variant.get("weightInGms", 0)
                            product_data["pack_size"] = product_variant.get("packsize", "")
                            product_data["unit_of_measure"] = product_variant.get("unitOfMeasure", "")
                            
                            products.append(product_data)
                
                self.logger.info(f"Extracted {len(products)} products from response #{response_index}")
                all_products.extend(products)
            
            self.logger.info(f"Total unique products extracted for '{keyword}': {len(all_products)}")
            
        except Exception as e:
            self.logger.error(f"Error extracting products from API responses: {e}")
            
        return all_products
        
        
    async def save_raw_responses(self, keyword):
        """Save the raw API responses to a JSON file for examination

        Args:
            keyword (str): The search keyword

        Returns:
            str: Path to the saved file or None if no responses found
        """
        if not hasattr(self, 'api_responses') or keyword not in self.api_responses or not self.api_responses[keyword]:
            self.logger.warning(f"No raw API responses found for keyword '{keyword}'")
            return None
            
        # Create a clean filename from the keyword
        import re
        clean_keyword = re.sub(r'[^\w\s]', '', keyword).lower().replace(' ', '_')
        
        # Create timestamp for unique filename
        import time
        timestamp = int(time.time())
        filename = f"{clean_keyword}_raw_responses_{timestamp}"
        
        # Create output directory for raw responses
        raw_dir = os.path.join(self.output_dir, 'raw_responses')
        os.makedirs(raw_dir, exist_ok=True)
        
        # Create results object with metadata
        results_data = {
            "keyword": keyword,
            "platform": "Zepto",
            "timestamp": timestamp,
            "location": self.location or "Not specified",
            "total_responses": len(self.api_responses[keyword]),
            "responses": self.api_responses[keyword]
        }
        
        # Save to file
        output_path = os.path.join(raw_dir, f"{filename}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved raw API responses to {output_path}")
        return output_path
        
    def save_results(self, keyword, products):
        """Save the extracted products to a JSON file

        Args:
            keyword (str): The search keyword
            products (list): List of extracted product dictionaries

        Returns:
            str: Path to the saved file
        """
        if not products:
            self.logger.warning(f"No products to save for keyword '{keyword}'")
            return ""
            
        # Create a clean filename from the keyword
        import re
        clean_keyword = re.sub(r'[^\w\s]', '', keyword).lower().replace(' ', '_')
        filename = f"{clean_keyword}_results"
        
        # Create results object with metadata
        import time
        results_data = {
            "keyword": keyword,
            "platform": "Zepto",
            "timestamp": int(time.time()),
            "location": self.location or "Not specified",
            "total_products": len(products),
            "products": products
        }
        
        # Save to file using the base class method
        return self.save_response_to_file(results_data, filename)
