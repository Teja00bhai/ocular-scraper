# QuickCommerce Scraper Implementation Notes

## Factory Pattern Implementation

The QuickCommerce Scraper has been refactored to use the Factory Pattern, providing a scalable and extensible architecture for supporting multiple e-commerce platforms.

### Design Overview

1. **Abstract Base Class**
   - `BaseScraper` defines the common interface for all platform scrapers
   - Implements abstract methods that all concrete scrapers must implement
   - Provides common utility functions like file saving and context management

2. **Concrete Implementations**
   - `ZeptoScraper` implements the Zepto-specific scraping logic
   - `BlinkitScraper` implements the Blinkit-specific scraping logic
   - Each concrete class handles platform-specific navigation, search, and data extraction

3. **Factory Class**
   - `ScraperFactory` manages the creation of appropriate scraper instances
   - Maintains a registry of available platform scrapers
   - Provides dynamic scraper instantiation based on platform name
   - Supports runtime registration of new platform scrapers

4. **Main Controller**
   - `quickcomm_scraper.py` provides a unified interface for all platforms
   - Uses the factory to create the appropriate scraper based on user input
   - Handles command-line arguments, logging, and result output

### Class Diagram

```
BaseScraper (ABC)
    |
    |-- ZeptoScraper
    |
    |-- BlinkitScraper
    |
    |-- [Future Platform Scrapers]

ScraperFactory
    |-- create_scraper(platform, **kwargs)
    |-- register_scraper(platform, scraper_class)
    |-- get_available_platforms()
```

### Key Benefits

1. **Extensibility**: Adding support for new platforms requires minimal changes
2. **Encapsulation**: Platform-specific logic is isolated in dedicated classes
3. **Maintainability**: Common functionality is shared through the base class
4. **Testability**: Each component can be tested independently
5. **Flexibility**: Runtime configuration of which platforms to use

## Playwright Integration Summary

### Completed Tasks
1. **Playwright Implementation**
   - Added Playwright as the primary browser automation engine
   - Created `zepto_scraper.py` with async-based scraping functionality
   - Implemented proper resource cleanup and error handling

2. **Configuration and Setup**
   - Updated dependencies to include Playwright
   - Added instructions for installing Playwright browser binaries
   - Configured logging for better debugging

3. **Script Updates**
   - Updated `main.py` to support Playwright mode
   - Created `run_src.py` with command-line arguments for mode selection
   - Deprecated legacy Selenium mode

4. **Testing**
   - Created comprehensive test script (`test_zepto_scraper.py`)
   - Implemented tests for imports, browser launch, initialization, navigation, and data extraction
   - Added fallback mechanisms for tests that depend on live site behavior

### Limitations and Known Issues

1. **Anti-Bot Measures**
   - Zepto website has anti-bot protections that may block automated access
   - Location verification may be required for successful product searches
   - API responses may be empty or limited when accessed via automation

2. **Asyncio Implementation**
   - The Playwright implementation uses asyncio, which requires careful handling
   - Nested event loops can cause issues (e.g., "asyncio.run() cannot be called from a running event loop")
   - Tests and scripts must properly manage async contexts

3. **Data Extraction**
   - Product extraction may require additional handling for different page states
   - Mock data is used in tests to ensure consistent validation

### Next Steps

1. **Enhanced Anti-Bot Mitigation**
   - Implement more sophisticated browser fingerprinting
   - Add proxy rotation capabilities
   - Introduce random delays and human-like interaction patterns

2. **Improved Error Handling**
   - Add more granular error handling for network issues
   - Implement automatic retries with exponential backoff
   - Create detailed error logs for debugging

3. **Extended Testing**
   - Create more comprehensive integration tests
   - Add unit tests for individual components
   - Implement CI/CD pipeline for automated testing

4. **Performance Optimization**
   - Profile and optimize browser resource usage
   - Implement parallel processing for multiple keywords/regions
   - Add caching mechanisms to reduce redundant requests

## API Response Interception Architecture

### Browser UI + Response Interception Approach

The Zepto scraper uses a hybrid approach that combines browser UI automation with API response interception. This architecture provides several key advantages:

1. **Leverages Zepto's Frontend Code**
   - Instead of reverse-engineering complex API requests, we let Zepto's own JavaScript handle:
     - Session token generation
     - CSRF token management
     - Device fingerprinting
     - Location/GPS parameters
     - Complex filter parameters
     - API authentication

2. **Implementation Strategy**
   - Playwright automates the browser UI (fills search box, clicks buttons)
   - Zepto's JavaScript code constructs the complex API request with all required parameters
   - Playwright intercepts the response when Zepto's code calls the API
   - Raw API responses are saved for debugging and further processing

3. **Key Advantages**
   - **No reverse engineering** - Zepto's code does the heavy lifting
   - **Always up-to-date** - If they change API parameters, the scraper still works
   - **Handles authentication** - Session management happens automatically
   - **Deals with anti-bot measures** - Uses a real browser session
   - **Location-aware** - Gets region-specific product results naturally

4. **Implementation Details**
   - Request interception is specifically targeted at the `/api/v3/search` endpoint
   - Both headed and headless modes are supported:
     - Headed mode: Better for interactive debugging and handling complex UI interactions
     - Headless mode: More efficient for production runs
   - Raw API responses are saved as JSON files in the output directory

### Code Example

```python
# Set up response interception
async def handle_response(route, request):
    # Let the request continue and capture the response
    response = await route.continue_()
    if "api/v3/search" in request.url:
        # Save the raw API response
        response_body = await response.json()
        # Process the data
        products = extract_zepto_data(response_body, keyword, region)
        return products

# Enable request interception
await page.route("**/*", handle_response)

# Let Zepto's UI handle the API complexity
search_input = await page.wait_for_selector("input[type='search']")
await search_input.fill(keyword)
await search_input.press("Enter")
```

## Usage Examples

### Basic Usage
```bash
python run_src.py --keywords "milk" "bread" --regions "560001" --headless
```

### Advanced Usage
```bash
python run_src.py --keywords "milk" "bread" --regions "560001" "400001" --headless --mode playwright --log-level DEBUG --output-dir custom_outputs
```

## Troubleshooting

If you encounter issues with the Playwright implementation:

1. Ensure Playwright is properly installed:
   ```bash
   pip install playwright
   python -m playwright install chromium
   ```

2. Check log files in the `src/logs/` directory for detailed error messages

3. Try running with `--log-level DEBUG` for more verbose output

4. For location-specific issues, consider using a VPN or proxy that matches the target region
