"""
StrawberryBot launcher script.
This script ensures proper Python path setup before running the bot.
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import and run the bot
from src.bot import StrawberryBot

if __name__ == "__main__":
    bot = StrawberryBot()
    bot.run() 