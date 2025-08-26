"""
Utility functions for Zepto API Scraper
"""
import os
import sys
import time
import logging
import traceback
import functools
from typing import Any, Callable, TypeVar, cast

# Type variable for function return type
T = TypeVar('T')

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """Set up a logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create handlers
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()
    
    # Create formatters and add to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def retry(max_retries: int = 3, delay: int = 2, backoff: int = 2, 
          exceptions: tuple = (Exception,), logger=None) -> Callable:
    """
    Retry decorator with exponential backoff
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        exceptions: Exceptions to catch and retry
        logger: Logger to use for logging retries
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            mtries, mdelay = max_retries, delay
            
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    msg = f"{func.__name__} failed: {str(e)}. Retrying in {mdelay} seconds..."
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                        
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            
            # Final attempt
            return func(*args, **kwargs)
        
        return cast(Callable[..., T], wrapper)
    
    return decorator

def safe_execute(func: Callable, *args: Any, logger=None, default_return=None, **kwargs: Any) -> Any:
    """
    Execute a function safely, catching and logging any exceptions
    
    Args:
        func: Function to execute
        args: Positional arguments to pass to the function
        logger: Logger to use for logging exceptions
        default_return: Value to return if an exception occurs
        kwargs: Keyword arguments to pass to the function
        
    Returns:
        Function result or default_return if an exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_msg = f"Error in {func.__name__}: {str(e)}"
        if logger:
            logger.error(error_msg)
            logger.error(traceback.format_exc())
        else:
            print(error_msg)
            print(traceback.format_exc())
        
        return default_return

def create_directory_if_not_exists(directory_path: str) -> None:
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        
def get_timestamp_str() -> str:
    """Get current timestamp as string"""
    return time.strftime("%Y%m%d_%H%M%S")

class ProgressTracker:
    """Simple progress tracker for long-running tasks"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.start_time = time.time()
        self.description = description
        
    def update(self, increment: int = 1) -> None:
        """Update progress"""
        self.current += increment
        self._print_progress()
        
    def _print_progress(self) -> None:
        """Print progress to console"""
        if self.total == 0:
            percentage = 100
        else:
            percentage = int(self.current / self.total * 100)
            
        elapsed = time.time() - self.start_time
        
        if self.current > 0 and elapsed > 0:
            items_per_sec = self.current / elapsed
            eta = (self.total - self.current) / items_per_sec if items_per_sec > 0 else 0
            eta_str = f"ETA: {int(eta)}s" if eta > 0 else "ETA: done"
        else:
            eta_str = "ETA: calculating..."
            
        print(f"\r{self.description}: {self.current}/{self.total} ({percentage}%) {eta_str}", end="")
        
        if self.current >= self.total:
            print()  # New line when complete
            
    def complete(self) -> None:
        """Mark task as complete"""
        self.current = self.total
        self._print_progress()
