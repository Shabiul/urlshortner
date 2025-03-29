import os
import logging
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Configure the SQLAlchemy database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define URL model
class URL(db.Model):
    __tablename__ = 'urls'
    
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    visits = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<URL {self.short_code}>'

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# URL Shortener functions
def generate_short_code(length=6):
    """Generate a random short code of specified length."""
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        # Check if code already exists
        existing = URL.query.filter_by(short_code=code).first()
        if not existing:
            return code

@app.route('/')
def index():
    """Render the main page with URL shortening form and history."""
    recent_urls = URL.query.order_by(URL.created_at.desc()).limit(10).all()
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
        
        # Check if URL already exists in the database
        existing_url = URL.query.filter_by(original_url=long_url).first()
        if existing_url:
            short_code = existing_url.short_code
        else:
            # Generate a new short code and save to database
            short_code = generate_short_code()
            new_url = URL(original_url=long_url, short_code=short_code)
            db.session.add(new_url)
            db.session.commit()
        
        # Create the full short URL
        short_url = request.host_url + short_code
        
        logging.debug(f"Generated short URL: {short_url}")
        
        # Handle regular web request
        flash('URL shortened successfully!', 'success')
        recent_urls = URL.query.order_by(URL.created_at.desc()).limit(10).all()
        return render_template('index.html', 
                              short_url=short_url, 
                              original_url=long_url, 
                              recent_urls=recent_urls)
    
    except Exception as e:
        logging.error(f"Error shortening URL: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """Redirect from shortened URL to original URL."""
    logging.debug(f"Redirect request for code: {short_code}")
    url_entry = URL.query.filter_by(short_code=short_code).first()
    
    if url_entry:
        # Increment visit counter
        url_entry.visits += 1
        db.session.commit()
        
        logging.debug(f"URL expanded: {short_code} -> {url_entry.original_url}")
        logging.debug(f"Redirecting to: {url_entry.original_url}")
        return redirect(url_entry.original_url)
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
