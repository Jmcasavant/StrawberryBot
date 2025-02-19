"""Core utilities for the bot."""
import discord
import logging
import sys
from typing import Dict, List, Final
from pathlib import Path
from datetime import datetime
from discord import app_commands

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / 'data'
LOGS_DIR = ROOT_DIR / 'logs'

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Bot settings
OWNER_ID: Final[int] = 159529126842204160

# Discord settings
INTENTS = discord.Intents.all()
INTENTS.message_content = True  # For commands
INTENTS.members = True          # For member tracking
INTENTS.voice_states = True     # For voice features
INTENTS.guilds = True          # For server events
INTENTS.reactions = True       # For reaction-based features

# Activity status
ACTIVITY = discord.Activity(
    type=discord.ActivityType.playing,
    name="/help | Collecting strawberries 🍓"
)

# Economy settings
STARTING_STRAWBERRIES: Final[int] = 10
DAILY_REWARD: Final[int] = 5
DAILY_STREAK_BONUS: Final[int] = 2  # Extra strawberries per day of streak
MAX_STREAK_BONUS: Final[int] = 10   # Cap the streak bonus

# Roulette settings
MIN_BET: Final[int] = 1
MAX_BET: Final[int] = 1000  # Prevent excessive betting

# Random strawberry response settings
MIN_RANDOM_STRAWBERRIES: Final[int] = 3
MAX_RANDOM_STRAWBERRIES: Final[int] = 15
STRAWBERRY_LAYOUTS: Final[List[str]] = [
    "🍓",
    "🍓 ✨",
    "✨ 🍓 ✨",
    "🌟 🍓 🌟"
]
STRAWBERRY_MESSAGES: Final[List[str]] = [
    "Here, have some strawberries! 🍓",
    "Fresh strawberries for everyone! 🍓",
    "Strawberry time! 🍓",
    "Did someone say strawberries? 🍓",
    "Spreading strawberry joy! 🍓"
]

# Command cooldowns (in seconds)
COOLDOWNS = {
    'roulette': 30,
    'transfer': 60,
    'daily': 86400,  # 24 hours
    'shop': 5,
}

# Rate limits (per minute)
RATE_LIMITS = {
    'commands': 60,      # General commands
    'games': 10,         # Game commands
    'economy': 30,       # Economy commands
}

# Display settings
MAX_DISPLAY_STRAWBERRIES: Final[int] = 50
DISPLAY_CHUNK_SIZE: Final[int] = 10

# Error messages
ERROR_MESSAGES = {
    'cooldown': "⏰ Command on cooldown. Try again in {time}.",
    'permission': "❌ You don't have permission to use this command!",
    'invalid_amount': "❌ Please enter a valid amount!",
    'insufficient_funds': "❌ You don't have enough strawberries!",
    'bot_error': "❌ An error occurred! Please try again later.",
    'command_error': "❌ Error executing command: {error}",
    'not_in_voice': "❌ You're not in a voice channel!",
    'already_connected': "❌ Already connected to a voice channel!",
    'no_permission': "❌ You don't have permission to use this command!",
    'invalid_user': "❌ Please specify a valid user!",
    'self_transfer': "❌ You can't transfer strawberries to yourself!",
    'bot_transfer': "❌ You can't transfer strawberries to bots!"
}

# Colors for embeds
COLORS = {
    'success': 0x2ecc71,  # Green
    'error': 0xe74c3c,    # Red
    'info': 0x3498db,     # Blue
    'warning': 0xf1c40f,  # Yellow
    'economy': 0xe91e63   # Pink
}

# Logging setup
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with file and console handlers.
    
    Args:
        name: The name of the logger, typically __name__
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
        
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler - new file each day
    today = datetime.now().strftime('%Y-%m-%d')
    file_handler = logging.FileHandler(
        LOGS_DIR / f'{today}.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger 