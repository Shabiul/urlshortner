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
from config import get_database_url
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure database connection pooling for high traffic
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,  # Maximum number of database connections to keep
    'pool_recycle': 300,  # Recycle connections after 5 minutes
    'pool_pre_ping': True,  # Check connection validity before use
    'max_overflow': 20,  # Allow up to 20 connections beyond pool_size when needed
    'connect_args': {
        'connect_timeout': 10,  # Set connection timeout to 10 seconds
        'application_name': 'url_shortener',  # Identify application in database logs
    },
    'pool_timeout': 30,  # Maximum time to wait for a connection from the pool
    'echo_pool': True if app.debug else False  # Echo pool activity to logs in debug mode
}

db = SQLAlchemy(app)

# Create database tables if they don't exist
with app.app_context():
    try:
        db.create_all()
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")

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
    
    # Health monitoring
    last_checked = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    status_code = db.Column(db.Integer, nullable=True)
    response_time = db.Column(db.Float, nullable=True)  # in milliseconds
    
    # Custom expiration settings
    expiration_type = db.Column(db.String(20), default='never')  # never, date, visits, both
    max_visits = db.Column(db.Integer, nullable=True)  # URL expires after this many visits
    
    def __repr__(self):
        return f'<URL {self.short_code}>'
        
    def is_expired(self):
        """Check if the URL has expired."""
        # Check time-based expiration
        time_expired = False
        if self.expires_at is not None:
            time_expired = datetime.utcnow() > self.expires_at
            
        # Check visits-based expiration
        visits_expired = False
        if self.max_visits is not None and self.expiration_type in ['visits', 'both']:
            visits_expired = self.visits >= self.max_visits
            
        # URL is expired if either condition is met for 'both' type,
        # or if the specific condition is met for 'date' or 'visits' types
        if self.expiration_type == 'both':
            return time_expired or visits_expired
        elif self.expiration_type == 'date':
            return time_expired
        elif self.expiration_type == 'visits':
            return visits_expired
        
        # 'never' type never expires
        return False
    
    def get_health_status(self):
        """Get health status description of the URL."""
        if not self.is_active:
            return "Inactive"
        if not self.last_checked:
            return "Not checked"
        if self.status_code is None:
            return "Unknown"
        
        if 200 <= self.status_code < 300:
            return "Healthy"
        elif 300 <= self.status_code < 400:
            return "Redirecting"
        elif 400 <= self.status_code < 500:
            return "Client Error"
        elif 500 <= self.status_code < 600:
            return "Server Error"
        else:
            return f"Status: {self.status_code}"
    
    def get_response_time_category(self):
        """Get response time category (fast, medium, slow)."""
        if self.response_time is None:
            return "Unknown"
        
        if self.response_time < 300:  # Less than 300ms
            return "Fast"
        elif self.response_time < 1000:  # Less than 1 second
            return "Medium"
        else:  # 1 second or more
            return "Slow"

# Database tables are already created at app initialization

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
    try:
        recent_urls = URL.query.order_by(URL.created_at.desc()).limit(10).all()
        return render_template('index.html', recent_urls=recent_urls)
    except Exception as e:
        logging.error(f"Database error in index route: {str(e)}")
        # Return page without recent URLs if database is temporarily unavailable
        return render_template('index.html', recent_urls=[], db_error=True)

@app.route('/shorten', methods=['POST'])
def shorten_url():
    """Handle URL shortening form submission."""
    long_url = request.form.get('url', '')
    custom_alias = request.form.get('alias', '').strip()
    expiration_type = request.form.get('expiration_type', 'never')
    expiration_days = request.form.get('expiration', '')
    max_visits = request.form.get('max_visits', '')
    
    logging.debug(f"Received URL shortening request for: {long_url}, alias: {custom_alias}, " +
                 f"expiration_type: {expiration_type}, expiration: {expiration_days}, max_visits: {max_visits}")
    
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
        max_visits_count = None
        
        # Process based on expiration type
        if expiration_type in ['date', 'both'] and expiration_days:
            try:
                # Convert to float to support decimal values (for minutes)
                days = float(expiration_days)
                if days > 0:
                    # For minutes calculations (when days < 1)
                    if days < 1:
                        minutes = int(days * 24 * 60)  # Convert fraction of day to minutes
                        expires_at = datetime.utcnow() + timedelta(minutes=minutes)
                    else:
                        # For regular days
                        expires_at = datetime.utcnow() + timedelta(days=days)
            except ValueError:
                # If conversion fails, no expiration will be set
                logging.warning(f"Invalid expiration value: {expiration_days}")
        
        # Process visit-based expiration
        if expiration_type in ['visits', 'both'] and max_visits:
            try:
                max_visits_count = int(max_visits)
                if max_visits_count <= 0:
                    max_visits_count = None
                    expiration_type = 'date' if expiration_type == 'both' else 'never'
                    logging.warning(f"Invalid max visits value: {max_visits}, must be > 0")
            except ValueError:
                max_visits_count = None
                expiration_type = 'date' if expiration_type == 'both' else 'never'
                logging.warning(f"Invalid max visits value: {max_visits}, must be an integer")
        
        # Handle custom alias if provided
        if custom_alias:
            # Validate custom alias format (letters, numbers, hyphen, underscore)
            if not re.match(r'^[a-zA-Z0-9_-]+$', custom_alias):
                flash('Custom alias can only contain letters, numbers, hyphens, and underscores.', 'danger')
                return redirect(url_for('index'))
            
            # Check for reserved keywords or potentially harmful patterns
            if custom_alias.lower() in ['api', 'admin', 'static', 'health', 'shorten', 'logout', 'login', 'register']:
                flash('This alias is a reserved word and cannot be used. Please choose another.', 'danger')
                return redirect(url_for('index'))
                
            # Enforce minimum and maximum length
            if len(custom_alias) < 3:
                flash('Custom alias must be at least 3 characters long.', 'danger')
                return redirect(url_for('index'))
                
            if len(custom_alias) > 30:
                flash('Custom alias must be no more than 30 characters long.', 'danger')
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
                is_custom=is_custom,
                expiration_type=expiration_type,
                max_visits=max_visits_count
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
        # Provide a user-friendly error message
        if "SSL connection" in str(e) or "operational error" in str(e).lower():
            error_message = "Sorry, we're having trouble connecting to our database. Please try again in a moment."
        elif "IntegrityError" in str(e) or "duplicate" in str(e).lower():
            error_message = "This custom name is already taken. Please try a different one."
        elif "timeout" in str(e).lower():
            error_message = "The request took too long to process. Please try again."
        else:
            error_message = "Something went wrong. We're looking into it. Please try again soon."
            
        flash(error_message, 'danger')
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
        expiration_type = data.get('expiration_type', 'never')
        max_visits = data.get('max_visits')
        
        # Process max visits if provided
        max_visits_count = None
        if expiration_type in ['visits', 'both'] and max_visits:
            try:
                max_visits_count = int(max_visits)
                if max_visits_count <= 0:
                    max_visits_count = None
                    expiration_type = 'date' if expiration_type == 'both' else 'never'
            except (ValueError, TypeError) as e:
                logging.warning(f"Invalid API max_visits value: {max_visits}. Error: {e}")
                max_visits_count = None
                expiration_type = 'date' if expiration_type == 'both' else 'never'
                
        # Set expiration date if provided
        expires_at = None
        if expiration_type in ['date', 'both'] and expiration_days:
            try:
                # Handle both int and float values
                days = float(expiration_days) if isinstance(expiration_days, (int, float, str)) else 0
                if days > 0:
                    # For minutes calculations (when days < 1)
                    if days < 1:
                        minutes = int(days * 24 * 60)  # Convert fraction of day to minutes
                        expires_at = datetime.utcnow() + timedelta(minutes=minutes)
                    else:
                        # For regular days
                        expires_at = datetime.utcnow() + timedelta(days=days)
            except (ValueError, TypeError) as e:
                logging.warning(f"Invalid API expiration value: {expiration_days}. Error: {e}")
        
        # Handle custom alias if provided
        if custom_alias:
            # Validate custom alias format
            if not re.match(r'^[a-zA-Z0-9_-]+$', custom_alias):
                return jsonify({'error': 'Custom alias can only contain letters, numbers, hyphens, and underscores'}), 400
            
            # Check for reserved keywords or potentially harmful patterns
            if custom_alias.lower() in ['api', 'admin', 'static', 'health', 'shorten', 'logout', 'login', 'register']:
                return jsonify({'error': 'This alias is a reserved word and cannot be used'}), 400
                
            # Enforce minimum and maximum length
            if len(custom_alias) < 3:
                return jsonify({'error': 'Custom alias must be at least 3 characters long'}), 400
                
            if len(custom_alias) > 30:
                return jsonify({'error': 'Custom alias must be no more than 30 characters long'}), 400
                
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
                is_custom=is_custom,
                expiration_type=expiration_type,
                max_visits=max_visits_count
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
            'is_custom': is_custom,
            'expiration_type': expiration_type,
            'max_visits': max_visits_count
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
        'is_expired': url_entry.is_expired(),
        'expiration_type': url_entry.expiration_type,
        'max_visits': url_entry.max_visits,
        'last_checked': url_entry.last_checked.isoformat() if url_entry.last_checked else None,
        'is_active': url_entry.is_active,
        'status_code': url_entry.status_code,
        'response_time': url_entry.response_time
    }
    
    return jsonify(response), 200

# Add a health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

# Connection pooling configuration is already defined at the top of the file

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
