import os

def get_database_url():
    """
    Get the database URL from environment variables, with Postgres dialect compatibility fix.
    
    Returns:
        str: The database URL
    """
    # Use the DATABASE_URL provided by the environment
    database_url = os.environ.get('DATABASE_URL')
    
    # Fix for SQLAlchemy postgres:// vs postgresql:// issue in some environments
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"Using database URL: {database_url}")
    return database_url