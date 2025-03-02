"""Database initialization script."""
import asyncio
import logging
from sqlalchemy.exc import SQLAlchemyError
from src.utils.database.session import db
from src.utils.database.models import Base

logger = logging.getLogger(__name__)

async def init_database():
    """Initialize the database with all tables."""
    try:
        # Create tables
        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database initialized successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def verify_connection():
    """Verify database connection."""
    try:
        async with db.engine.connect() as conn:
            await conn.execute("SELECT 1")
            logger.info("Database connection verified")
            
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        raise

async def main():
    """Main initialization function."""
    logger.info("Starting database initialization")
    
    try:
        # Verify connection
        await verify_connection()
        
        # Initialize database
        await init_database()
        
        logger.info("Database setup complete")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise
    finally:
        # Clean up connections
        await db.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 