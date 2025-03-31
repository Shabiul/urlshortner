import random
import string
import logging
from datetime import datetime
from collections import deque

class URLShortener:
    
    
    def __init__(self):
        self.url_to_code = {}  
        self.code_to_url = {}  
        self.recent_urls = deque(maxlen=100)  
        self.code_length = 6  
        logging.debug("URL Shortener initialized")
    
    def shorten(self, url):
        if url in self.url_to_code:
            code = self.url_to_code[url]
            logging.debug(f"URL already shortened: {url} -> {code}")
            return code
        
        code = self._generate_unique_code()
        
        self.url_to_code[url] = code
        self.code_to_url[code] = url
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.recent_urls.appendleft({
            'original_url': url,
            'short_code': code,
            'timestamp': timestamp
        })
        
        logging.debug(f"URL shortened: {url} -> {code}")
        return code
    
    def expand(self, code):
        
        if code in self.code_to_url:
            url = self.code_to_url[code]
            logging.debug(f"URL expanded: {code} -> {url}")
            return url
        logging.debug(f"No URL found for code: {code}")
        return None
    
    def get_recent_urls(self, count=10):
        
        return list(self.recent_urls)[:count]
    
    def _generate_unique_code(self):
        
        while True:
            code = ''.join(random.choices(
                string.ascii_letters + string.digits, 
                k=self.code_length
            ))
            
            if code not in self.code_to_url:
                return code
