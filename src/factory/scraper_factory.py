"""
Scraper Factory - Factory pattern implementation for QuickCommerce scrapers
"""
import logging
from typing import Dict, Any, Optional, Type

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.zepto_scraper import ZeptoScraper
# Uncomment when implemented
# from src.scrapers.blinkit_scraper import BlinkitScraper

# Configure logging
logger = logging.getLogger("ScraperFactory")

class ScraperFactory:
    """
    Factory class for creating different QuickCommerce platform scrapers
    """
    
    # Registry of available scrapers
    _scrapers = {
        "zepto": ZeptoScraper,
        # Add more platforms here as they are implemented
        # "blinkit": BlinkitScraper,
        # "swiggy": SwiggyScraper,
    }
    
    @classmethod
    def register_scraper(cls, platform: str, scraper_class: Type[BaseScraper]) -> None:
        """
        Register a new scraper class for a platform
        
        Args:
            platform: Platform name (lowercase)
            scraper_class: Scraper class that inherits from BaseScraper
        """
        if not issubclass(scraper_class, BaseScraper):
            raise TypeError(f"Scraper class must inherit from BaseScraper")
        
        cls._scrapers[platform.lower()] = scraper_class
        logger.info(f"Registered scraper for platform: {platform}")
    
    @classmethod
    def create_scraper(cls, platform: str, **kwargs) -> Optional[BaseScraper]:
        """
        Create a scraper for the specified platform
        
        Args:
            platform: Platform name (case-insensitive)
            **kwargs: Additional arguments to pass to the scraper constructor
            
        Returns:
            An instance of the appropriate scraper, or None if platform not supported
        """
        platform = platform.lower()
        
        if platform not in cls._scrapers:
            logger.error(f"Unsupported platform: {platform}")
            logger.info(f"Available platforms: {', '.join(cls._scrapers.keys())}")
            return None
        
        try:
            # Create an instance of the appropriate scraper class
            scraper = cls._scrapers[platform](**kwargs)
            logger.info(f"Created scraper for platform: {platform}")
            return scraper
        except Exception as e:
            logger.error(f"Error creating scraper for platform {platform}: {e}")
            return None
    
    @classmethod
    def get_available_platforms(cls) -> list:
        """
        Get a list of all available platforms
        
        Returns:
            List of platform names
        """
        return list(cls._scrapers.keys())
