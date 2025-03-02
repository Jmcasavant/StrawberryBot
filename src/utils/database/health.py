"""Database health check utilities."""
import logging
from datetime import datetime
from sqlalchemy import text
from src.utils.database.session import db

logger = logging.getLogger(__name__)

async def check_database_health():
    """Check database connection and performance."""
    try:
        async with db.get_session() as session:
            # Basic connectivity
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            
            # Connection info
            result = await session.execute(text("""
                SELECT 
                    current_timestamp as time,
                    current_database() as database,
                    current_user as user,
                    version() as version
            """))
            info = result.mappings().first()
            
            # Connection count
            result = await session.execute(text("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE datname = current_database()
            """))
            connections = result.scalar()
            
            logger.info(
                f"Database health check passed:\n"
                f"Time: {info['time']}\n"
                f"Database: {info['database']}\n"
                f"User: {info['user']}\n"
                f"Version: {info['version']}\n"
                f"Active connections: {connections}"
            )
            return True
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False 