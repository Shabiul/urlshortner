import os
import logging
from app import app, db

# Configure logging
logging.basicConfig(level=logging.INFO)

def migrate_database():
    """Migrate database schema to match current model definitions."""
    try:
        with app.app_context():
            # Create tables if they don't exist
            db.create_all()
            
            # Check if migration is needed
            engine = db.engine
            inspector = db.inspect(engine)
            
            # Get existing columns for the URL table
            columns = inspector.get_columns('urls')
            column_names = [col['name'] for col in columns]
            
            logging.info(f"Existing columns: {column_names}")
            
            # Check for missing columns and add them
            missing_columns = []
            
            if 'expires_at' not in column_names:
                missing_columns.append("ALTER TABLE urls ADD COLUMN expires_at TIMESTAMP;")
                
            if 'is_custom' not in column_names:
                missing_columns.append("ALTER TABLE urls ADD COLUMN is_custom BOOLEAN DEFAULT false;")
                
            # Health monitoring columns
            if 'last_checked' not in column_names:
                missing_columns.append("ALTER TABLE urls ADD COLUMN last_checked TIMESTAMP;")
                
            if 'is_active' not in column_names:
                missing_columns.append("ALTER TABLE urls ADD COLUMN is_active BOOLEAN DEFAULT true;")
                
            if 'status_code' not in column_names:
                missing_columns.append("ALTER TABLE urls ADD COLUMN status_code INTEGER;")
                
            if 'response_time' not in column_names:
                missing_columns.append("ALTER TABLE urls ADD COLUMN response_time FLOAT;")
                
            # Custom expiration settings
            if 'expiration_type' not in column_names:
                missing_columns.append("ALTER TABLE urls ADD COLUMN expiration_type VARCHAR(20) DEFAULT 'never';")
                
            if 'max_visits' not in column_names:
                missing_columns.append("ALTER TABLE urls ADD COLUMN max_visits INTEGER;")
            
            # Apply missing column migrations
            if missing_columns:
                logging.info("Applying database migrations...")
                with engine.connect() as conn:
                    for statement in missing_columns:
                        logging.info(f"Executing: {statement}")
                        conn.execute(db.text(statement))
                        conn.commit()
                logging.info("Database migration completed successfully.")
            else:
                logging.info("No migrations needed. Database schema is up to date.")
                
            return True
    except Exception as e:
        logging.error(f"Migration error: {str(e)}")
        return False

if __name__ == "__main__":
    migrate_database()