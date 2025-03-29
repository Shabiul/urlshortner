import json
import logging
import os
import sys
from urllib.parse import urlparse

from flask import Flask, flash, redirect, render_template, request, url_for, abort

from url_shortener import URLShortener

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-default-secret-key")

# Initialize URL shortener
shortener = URLShortener()

def main():
    # This function is called by the Node.js Firebase Function
    path = sys.argv[1] if len(sys.argv) > 1 else '/'
    method = sys.argv[2] if len(sys.argv) > 2 else 'GET'
    body = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    
    if path == '/':
        # Handle index
        return render_template('index.html', recent_urls=shortener.get_recent_urls(10))
    elif path.startswith('/shorten'):
        # Handle shortening
        if method == 'POST':
            try:
                long_url = body.get('url', '')
                
                # Basic URL validation
                if not long_url:
                    return json.dumps({'error': 'URL is required'})
                
                result = urlparse(long_url)
                if not all([result.scheme, result.netloc]):
                    return json.dumps({'error': 'Invalid URL format'})
                
                # Generate short URL
                short_code = shortener.shorten(long_url)
                short_url = f"https://your-firebase-app.web.app/{short_code}"
                
                return json.dumps({
                    'success': True,
                    'short_url': short_url,
                    'original_url': long_url,
                    'recent_urls': shortener.get_recent_urls(10)
                })
            
            except Exception as e:
                logging.error(f"Error shortening URL: {str(e)}")
                return json.dumps({'error': f'An error occurred: {str(e)}'})
    else:
        # Handle redirect from short code
        short_code = path[1:]  # Remove leading slash
        original_url = shortener.expand(short_code)
        
        if original_url:
            return json.dumps({'redirect': original_url})
        else:
            return json.dumps({'error': 'Sorry, that shortened URL was not found'})

if __name__ == '__main__':
    result = main()
    print(result)