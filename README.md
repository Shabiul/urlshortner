# URL Shortener Application

A robust URL shortening service built with Python Flask and PostgreSQL, featuring user authentication, custom short URLs, analytics, and API support.

## Tech Stack

### Backend
- **Flask**: Web framework for handling HTTP requests and routing
- **SQLAlchemy**: ORM for database interactions
- **PostgreSQL**: Primary database
- **Flask-Login**: User authentication management
- **Gunicorn**: Production WSGI HTTP Server

### Frontend
- **Bootstrap**: Responsive UI design
- **Font Awesome**: Icons and visual elements
- **Jinja2**: Template engine

## Features

### URL Management
- Shorten long URLs to custom or auto-generated codes
- Support for custom aliases
- URL expiration settings (time-based and visit-based)
- URL health monitoring
- Visit tracking and analytics

### User Features
- User registration and authentication
- Personal dashboard
- URL management (create, edit, delete)
- Account settings management

### API Support
- RESTful API endpoints for URL operations
- URL status checking
- Analytics retrieval
- API key authentication

### Security
- Password hashing with Werkzeug
- CSRF protection
- Session management
- Database connection pooling
- Input validation and sanitization

### Analytics & Monitoring
- Visit counting
- Referrer tracking
- User agent logging
- Response time monitoring
- Health status checking

## Project Structure
```
├── static/          # Static assets
├── templates/       # HTML templates
├── app.py          # Main application logic
├── config.py       # Configuration management
├── forms.py        # Form definitions
├── main.py         # Application entry point
├── url_shortener.py # URL shortening logic
```

## API Endpoints

### URL Operations
- `POST /api/shorten`: Create short URL
- `GET /api/status/<short_code>`: Get URL statistics
- `GET /health`: Service health check
- `POST /api/cleanup`: Maintenance endpoint

### Parameters
Short URL creation supports:
- Custom aliases
- Expiration settings
- Visit limits
- Custom tracking parameters

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Session security key

## Getting Started (Replit Setup)
1. **Fork the project** on Replit.
2. **Configure environment variables** in the Replit Secrets tab:
   - `DATABASE_URL`: Your PostgreSQL connection string.
   - `SESSION_SECRET`: A random secure string.
3. **Click the "Run" button** to start the server.

The application will be available at the provided Replit URL.

## Local Setup
1. **Clone the repository:**
   ```sh
   git clone <repo_url>
   cd url-shortener
   ```
2. **Set up a virtual environment:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Configure environment variables:**
   Create a `.env` file in the root directory and add:
   ```env
   DATABASE_URL=your_postgresql_connection_string
   SESSION_SECRET=your_secure_random_string
   ```
5. **Run database migrations:**
   ```sh
   flask db upgrade
   ```
6. **Start the application:**
   ```sh
   flask run
   ```

The application will be available at `http://127.0.0.1:5000/`. 

