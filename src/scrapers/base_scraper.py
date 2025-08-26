"""
Base Scraper Abstract Base Class for QuickCommerce Platforms
"""
import os
import json
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union

class BaseScraper(ABC):
    """
    Abstract Base Class for all QuickCommerce platform scrapers
    All platform-specific scrapers must implement these methods
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000, output_dir: str = "outputs"):
        """
        Initialize the base scraper
        
        Args:
            headless: Whether to run the browser in headless mode
            timeout: Timeout in milliseconds for browser operations
            output_dir: Directory to save output files
        """
        self.headless = headless
        self.timeout = timeout
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the scraper (setup browser, etc.)
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Clean up resources"""
        pass
    
    @abstractmethod
    async def navigate_to_site(self) -> bool:
        """
        Navigate to the e-commerce platform site
        
        Returns:
            bool: True if navigation successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def search_for_keyword(self, keyword: str, region: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for a keyword on the platform
        
        Args:
            keyword: Search term
            region: Optional region/location code
            
        Returns:
            Dict containing search results data
        """
        pass
    
    @abstractmethod
    def extract_data(self, response_data: Dict[str, Any], keyword: str) -> List[Dict[str, Any]]:
        """
        Extract structured data from API response
        
        Args:
            response_data: Raw API response data
            keyword: Search keyword used
            
        Returns:
            List of structured product data dictionaries
        """
        pass
    
    def save_response_to_file(self, data: Dict[str, Any], filename: str) -> str:
        """
        Save API response data to a JSON file
        
        Args:
            data: Data to save
            filename: Base filename (without extension)
            
        Returns:
            Path to the saved file
        """
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create filename with timestamp
        import time
        timestamp = int(time.time())
        file_path = os.path.join(self.output_dir, f"{filename}_{timestamp}.json")
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved response data to {file_path}")
        return file_path
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
