import os
import logging
import json
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
    # Check if this is an API request from Firebase
    if request.headers.get('X-Firebase-Forwarded'):
        recent_urls = shortener.get_recent_urls(10)
        # Format the URLs with the correct domain
        for url in recent_urls:
            url['short_url'] = request.host_url + url['short_code']
        return jsonify({
            'recent_urls': recent_urls
        })
    
    # Regular web request
    recent_urls = shortener.get_recent_urls(10)
    return render_template('index.html', recent_urls=recent_urls)

@app.route('/shorten', methods=['POST'])
def shorten_url():
    """Handle URL shortening form submission."""
    # Handling JSON requests from the Firebase proxy
    if request.headers.get('X-Firebase-Forwarded') and request.is_json:
        data = request.get_json()
        long_url = data.get('url', '')
    else:
        long_url = request.form.get('url', '')
    
    logging.debug(f"Received URL shortening request for: {long_url}")
    
    # Validate URL
    if not long_url:
        if request.headers.get('X-Firebase-Forwarded'):
            return jsonify({'error': 'Please enter a URL'})
        flash('Please enter a URL', 'danger')
        return redirect(url_for('index'))
    
    # Ensure URL has scheme
    if not urlparse(long_url).scheme:
        long_url = 'http://' + long_url
    
    try:
        # Validate URL format
        result = urlparse(long_url)
        if not all([result.scheme, result.netloc]):
            if request.headers.get('X-Firebase-Forwarded'):
                return jsonify({'error': 'Invalid URL format. Please enter a valid URL.'})
            flash('Invalid URL format. Please enter a valid URL.', 'danger')
            return redirect(url_for('index'))
        
        # Generate short URL
        short_code = shortener.shorten(long_url)
        short_url = request.host_url + short_code
        
        logging.debug(f"Generated short URL: {short_url}")
        
        # Handle Firebase request
        if request.headers.get('X-Firebase-Forwarded'):
            return jsonify({
                'short_url': short_url,
                'original_url': long_url,
                'recent_urls': shortener.get_recent_urls(10)
            })
        
        # Handle regular web request
        flash(f'URL shortened successfully!', 'success')
        return render_template('index.html', 
                              short_url=short_url, 
                              original_url=long_url, 
                              recent_urls=shortener.get_recent_urls(10))
    
    except Exception as e:
        logging.error(f"Error shortening URL: {str(e)}")
        if request.headers.get('X-Firebase-Forwarded'):
            return jsonify({'error': f'An error occurred: {str(e)}'})
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
    if request.headers.get('X-Firebase-Forwarded'):
        return jsonify({'error': 'Sorry, that shortened URL was not found.'}), 404
    return render_template('index.html', error="Sorry, that shortened URL was not found."), 404

# Add a health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for Firebase Functions."""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
