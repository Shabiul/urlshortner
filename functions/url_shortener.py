import random
import string
import logging
from datetime import datetime
from collections import deque

class URLShortener:
    """
    A simple in-memory URL shortener implementation.
    
    This class provides methods to shorten URLs, expand shortened URLs,
    and retrieve recently shortened URLs.
    """
    
    def __init__(self):
        """Initialize the URL shortener with empty mappings."""
        self.url_to_code = {}  # Maps original URLs to short codes
        self.code_to_url = {}  # Maps short codes to original URLs
        self.recent_urls = deque(maxlen=100)  # Store recently shortened URLs
        self.code_length = 6  # Length of short codes
        logging.debug("URL Shortener initialized")
    
    def shorten(self, url):
        """
        Shorten a URL by generating a unique code.
        
        Args:
            url (str): The URL to shorten
            
        Returns:
            str: The generated short code
        """
        # If URL already shortened, return existing code
        if url in self.url_to_code:
            code = self.url_to_code[url]
            logging.debug(f"URL already shortened: {url} -> {code}")
            return code
        
        # Generate a unique short code
        code = self._generate_unique_code()
        
        # Store mappings
        self.url_to_code[url] = code
        self.code_to_url[code] = url
        
        # Add to recent URLs
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.recent_urls.appendleft({
            'original_url': url,
            'short_code': code,
            'timestamp': timestamp
        })
        
        logging.debug(f"URL shortened: {url} -> {code}")
        return code
    
    def expand(self, code):
        """
        Expand a short code to its original URL.
        
        Args:
            code (str): The short code to expand
            
        Returns:
            str: The original URL or None if not found
        """
        if code in self.code_to_url:
            url = self.code_to_url[code]
            logging.debug(f"URL expanded: {code} -> {url}")
            return url
        logging.debug(f"No URL found for code: {code}")
        return None
    
    def get_recent_urls(self, count=10):
        """
        Get the most recently shortened URLs.
        
        Args:
            count (int): Maximum number of URLs to return
            
        Returns:
            list: List of dictionaries containing URL info
        """
        return list(self.recent_urls)[:count]
    
    def _generate_unique_code(self):
        """
        Generate a unique code that doesn't exist yet.
        
        Returns:
            str: A unique short code
        """
        while True:
            # Generate a random code with letters and digits
            code = ''.join(random.choices(
                string.ascii_letters + string.digits, 
                k=self.code_length
            ))
            
            # Check if code already exists
            if code not in self.code_to_url:
                return code
