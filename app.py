import os
import re
import logging
import random
import string
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
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
    short_code = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    visits = db.Column(db.Integer, default=0)
    is_custom = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<URL {self.short_code}>'
        
    def is_expired(self):
        """Check if the URL has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

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
    custom_alias = request.form.get('alias', '').strip()
    expiration_days = request.form.get('expiration', '')
    
    logging.debug(f"Received URL shortening request for: {long_url}, alias: {custom_alias}, expiration: {expiration_days}")
    
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
        
        # Set expiration date if provided
        expires_at = None
        if expiration_days and expiration_days.isdigit():
            days = int(expiration_days)
            if days > 0:
                expires_at = datetime.utcnow() + timedelta(days=days)
        
        # Handle custom alias if provided
        if custom_alias:
            # Validate custom alias format (letters, numbers, hyphen, underscore)
            if not re.match(r'^[a-zA-Z0-9_-]+$', custom_alias):
                flash('Custom alias can only contain letters, numbers, hyphens, and underscores.', 'danger')
                return redirect(url_for('index'))
            
            # Check if custom alias already exists
            existing_alias = URL.query.filter_by(short_code=custom_alias).first()
            if existing_alias:
                flash('This custom alias is already taken. Please choose another.', 'danger')
                return redirect(url_for('index'))
            
            short_code = custom_alias
            is_custom = True
        else:
            # Check if URL already exists in the database (only for non-custom URLs)
            existing_url = URL.query.filter_by(original_url=long_url, is_custom=False).first()
            if existing_url and not existing_url.is_expired():
                short_code = existing_url.short_code
                is_custom = False
                
                # Update expiration if needed
                if expires_at and expires_at != existing_url.expires_at:
                    existing_url.expires_at = expires_at
                    db.session.commit()
            else:
                # Generate a new short code
                short_code = generate_short_code()
                is_custom = False
        
        # Create or update the URL entry
        if custom_alias or not existing_url or existing_url.is_expired():
            new_url = URL(
                original_url=long_url,
                short_code=short_code,
                expires_at=expires_at,
                is_custom=is_custom
            )
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
    
    if not url_entry:
        logging.debug(f"No URL found for code: {short_code}")
        flash('This shortened URL does not exist.', 'danger')
        return render_template('index.html', error="Sorry, that shortened URL was not found."), 404
    
    # Check if the URL has expired
    if url_entry.is_expired():
        logging.debug(f"Expired URL: {short_code}")
        flash('This shortened URL has expired.', 'warning')
        return render_template('index.html', error="Sorry, this shortened URL has expired."), 410
        
    # Increment visit counter
    url_entry.visits += 1
    db.session.commit()
    
    logging.debug(f"URL expanded: {short_code} -> {url_entry.original_url}")
    logging.debug(f"Redirecting to: {url_entry.original_url}")
    return redirect(url_entry.original_url)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('index.html', error="Sorry, that shortened URL was not found."), 404

# API endpoints
@app.route('/api/shorten', methods=['POST'])
def api_shorten_url():
    """API endpoint for shortening URLs."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Ensure URL has scheme
        if not urlparse(url).scheme:
            url = 'http://' + url
        
        # Validate URL format
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return jsonify({'error': 'Invalid URL format'}), 400
        
        # Handle optional parameters
        custom_alias = data.get('alias', '').strip()
        expiration_days = data.get('expiration')
        
        # Set expiration date if provided
        expires_at = None
        if expiration_days and isinstance(expiration_days, int) and expiration_days > 0:
            expires_at = datetime.utcnow() + timedelta(days=expiration_days)
        
        # Handle custom alias if provided
        if custom_alias:
            # Validate custom alias format
            if not re.match(r'^[a-zA-Z0-9_-]+$', custom_alias):
                return jsonify({'error': 'Custom alias can only contain letters, numbers, hyphens, and underscores'}), 400
            
            # Check if custom alias already exists
            existing_alias = URL.query.filter_by(short_code=custom_alias).first()
            if existing_alias:
                return jsonify({'error': 'This custom alias is already taken'}), 409
            
            short_code = custom_alias
            is_custom = True
        else:
            # Check if URL already exists in the database (only for non-custom URLs)
            existing_url = URL.query.filter_by(original_url=url, is_custom=False).first()
            if existing_url and not existing_url.is_expired():
                short_code = existing_url.short_code
                is_custom = False
                
                # Update expiration if needed
                if expires_at and expires_at != existing_url.expires_at:
                    existing_url.expires_at = expires_at
                    db.session.commit()
            else:
                # Generate a new short code
                short_code = generate_short_code()
                is_custom = False
        
        # Create or update the URL entry
        if custom_alias or not existing_url or existing_url.is_expired():
            new_url = URL(
                original_url=url,
                short_code=short_code,
                expires_at=expires_at,
                is_custom=is_custom
            )
            db.session.add(new_url)
            db.session.commit()
        
        # Create the full short URL
        short_url = request.host_url + short_code
        
        response = {
            'original_url': url,
            'short_code': short_code,
            'short_url': short_url,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'is_custom': is_custom
        }
        
        return jsonify(response), 201
    
    except Exception as e:
        logging.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<short_code>', methods=['GET'])
def api_url_status(short_code):
    """API endpoint to get URL stats."""
    url_entry = URL.query.filter_by(short_code=short_code).first()
    
    if not url_entry:
        return jsonify({'error': 'URL not found'}), 404
    
    response = {
        'short_code': url_entry.short_code,
        'original_url': url_entry.original_url,
        'created_at': url_entry.created_at.isoformat(),
        'expires_at': url_entry.expires_at.isoformat() if url_entry.expires_at else None,
        'visits': url_entry.visits,
        'is_custom': url_entry.is_custom,
        'is_expired': url_entry.is_expired()
    }
    
    return jsonify(response), 200

# Add a health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

# Add configuration for database connection pooling for high traffic
# This helps with handling high load by reusing database connections
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,  # Maximum number of database connections to keep
    'pool_recycle': 300,  # Recycle connections after 5 minutes
    'pool_pre_ping': True,  # Check connection validity before use
    'max_overflow': 20  # Allow up to 20 connections beyond pool_size when needed
}

# Add a cleanup job route to remove or archive expired URLs
# This can be called periodically by a cron job or scheduler
@app.route('/api/cleanup', methods=['POST'])
def cleanup_expired_urls():
    """Clean up expired URLs to keep the database efficient."""
    try:
        # Check for API key or admin auth - should be implemented in production
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
            
        # In production, you would validate the token here
        # token = auth_header.split(' ')[1]
        # if not validate_admin_token(token):
        #     return jsonify({'error': 'Unauthorized'}), 401
        
        # Get action type: 'delete' or 'mark'
        action = request.args.get('action', 'mark')
        
        # Find all expired URLs
        now = datetime.utcnow()
        expired_urls = URL.query.filter(
            URL.expires_at.isnot(None),
            URL.expires_at < now
        ).all()
        
        count = len(expired_urls)
        
        if action == 'delete':
            # Delete expired URLs
            for url in expired_urls:
                db.session.delete(url)
            db.session.commit()
            return jsonify({
                'message': f'Deleted {count} expired URLs',
                'count': count
            })
        else:
            # Mark URLs as expired (already handled by the is_expired method)
            return jsonify({
                'message': f'Found {count} expired URLs',
                'count': count
            })
    
    except Exception as e:
        logging.error(f"Cleanup error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
