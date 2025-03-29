import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify
from urllib.parse import urlparse
import url_shortener

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Initialize URL shortener
shortener = url_shortener.URLShortener()

@app.route('/')
def index():
    """Render the main page with URL shortening form and history."""
    recent_urls = shortener.get_recent_urls(10)  # Get the 10 most recent shortened URLs
    return render_template('index.html', recent_urls=recent_urls)

@app.route('/shorten', methods=['POST'])
def shorten_url():
    """Handle URL shortening form submission."""
    long_url = request.form.get('url', '')
    
    logging.debug(f"Received URL shortening request for: {long_url}")
    
    # Validate URL
    if not long_url:
        flash('Please enter a URL', 'danger')
        return redirect(url_for('index'))
    
    # Ensure URL has scheme
    if not urlparse(long_url).scheme:
        long_url = 'http://' + long_url
    
    try:
        # Validate URL format
        result = urlparse(long_url)
        if not all([result.scheme, result.netloc]):
            flash('Invalid URL format. Please enter a valid URL.', 'danger')
            return redirect(url_for('index'))
        
        # Generate short URL
        short_code = shortener.shorten(long_url)
        short_url = request.host_url + short_code
        
        logging.debug(f"Generated short URL: {short_url}")
        
        # Handle regular web request
        flash('URL shortened successfully!', 'success')
        return render_template('index.html', 
                              short_url=short_url, 
                              original_url=long_url, 
                              recent_urls=shortener.get_recent_urls(10))
    
    except Exception as e:
        logging.error(f"Error shortening URL: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """Redirect from shortened URL to original URL."""
    logging.debug(f"Redirect request for code: {short_code}")
    original_url = shortener.expand(short_code)
    
    if original_url:
        logging.debug(f"Redirecting to: {original_url}")
        return redirect(original_url)
    else:
        logging.debug(f"No URL found for code: {short_code}")
        abort(404)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('index.html', error="Sorry, that shortened URL was not found."), 404

# Add a health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
