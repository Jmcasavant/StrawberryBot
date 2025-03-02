"""
Configuration management for StrawberryBot.

This module handles all configuration settings for the bot, including:
- Environment variables
- Discord-specific settings
- Database configurations
- Caching settings
- Feature flags
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Bot Configuration
BOT_CONFIG = {
    "token": os.getenv("DISCORD_TOKEN"),
    "owner_id": int(os.getenv("OWNER_ID", 0)),  # Primary bot owner
    "owner_ids": [int(id.strip()) for id in os.getenv("ADDITIONAL_OWNER_IDS", "").split(",") if id.strip()],  # Additional owners
    "command_prefix": "!",
    "case_insensitive": True,
    "strip_after_prefix": True,
    "private_mode": os.getenv("PRIVATE_MODE", "true").lower() == "true",  # Whether bot is private or public
}

# Discord Intents Configuration
INTENT_CONFIG = {
    "messages": True,
    "guilds": True,
    "members": True,
    "voice_states": True,
    "message_content": True,
    "reactions": True,
}

# Redis Cache Configuration
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "password": os.getenv("REDIS_PASSWORD"),
    "decode_responses": True,
}

# Database Configuration
DATABASE_CONFIG = {
    "url": os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATA_DIR}/strawberry.db"),
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
}

# Game Configuration
GAME_CONFIG = {
    "min_bet": 1,
    "max_bet": 1000,
    "daily_amount": 100,
    "starting_amount": 500,
    "roulette_cooldown": 60,  # seconds
    "daily_cooldown": 86400,  # 24 hours in seconds
}

# Logging Configuration
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOGS_DIR / "strawberry.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": True,
        },
    },
}

# Feature Flags
FEATURES = {
    "voice_enabled": True,
    "economy_enabled": True,
    "games_enabled": True,
    "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
}

def get_config(key: str) -> Dict[str, Any]:
    """
    Get configuration dictionary by key.
    
    Args:
        key: The configuration section to retrieve
        
    Returns:
        Dict containing the requested configuration
    
    Raises:
        KeyError: If the configuration section doesn't exist
    """
    configs = {
        "bot": BOT_CONFIG,
        "intents": INTENT_CONFIG,
        "redis": REDIS_CONFIG,
        "database": DATABASE_CONFIG,
        "game": GAME_CONFIG,
        "logging": LOG_CONFIG,
        "features": FEATURES,
    }
    return configs[key]

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Safely get an environment variable.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        
    Returns:
        The environment variable value or default
    """
    return os.getenv(key, default)

def is_owner(user_id: int) -> bool:
    """
    Check if a user ID belongs to a bot owner.
    
    Args:
        user_id: Discord user ID to check
        
    Returns:
        True if user is a bot owner
    """
    return user_id == BOT_CONFIG["owner_id"] or user_id in BOT_CONFIG["owner_ids"] 