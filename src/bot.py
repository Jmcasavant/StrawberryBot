"""
StrawberryBot - A feature-rich Discord bot.

This module initializes and runs the bot with:
- Enhanced error handling
- Database integration
- Caching support
- Logging
- Command management
- Event handling
"""

import asyncio
import logging
import sys
from typing import Optional, List
import discord
from discord.ext import commands
from src.config.settings import get_config
from src.utils.database.session import db
from src.utils.cache.redis_cache import RedisCache
from src.utils.helpers.common import format_duration, chunk_text
from src.utils.strawberry_game import StrawberryGame

# Set up logging
logger = logging.getLogger("strawberry")

class StrawberryBot(commands.Bot):
    """
    Enhanced Discord bot with advanced features.
    
    Features:
    - Database integration
    - Redis caching
    - Advanced error handling
    - Command management
    - Event handling
    - Performance monitoring
    - Strawberry game system
    """
    
    def __init__(self):
        """Initialize the bot with configuration."""
        # Load configuration
        self.config = get_config("bot")
        self.features = get_config("features")
        intents = discord.Intents(**get_config("intents"))
        
        # Initialize base bot
        super().__init__(
            command_prefix=self.config["command_prefix"],
            intents=intents,
            case_insensitive=self.config["case_insensitive"],
            strip_after_prefix=self.config["strip_after_prefix"]
        )
        
        # Initialize cache
        self.cache = RedisCache(prefix="bot:")
        
        # Initialize game system
        self.game = StrawberryGame()
        
        # Store start time for uptime tracking
        self.start_time = discord.utils.utcnow()
        
        # Command statistics
        self.command_stats = {}
    
    async def setup_hook(self) -> None:
        """
        Initialize bot systems before connecting to Discord.
        This is called automatically by discord.py.
        """
        try:
            logger.info("Starting bot setup...")
            
            # Initialize database
            await db.init()
            logger.info("Database initialized")
            
            # Initialize cache
            await self.cache.connect()
            logger.info("Cache initialized")
            
            # Initialize game system
            await self.game.start()
            logger.info("Game system initialized")
            
            # Load cogs
            await self.load_extensions()
            logger.info("Extensions loaded")
            
            # Sync commands
            await self.tree.sync()
            logger.info("Commands synced")
            
            logger.info("Bot setup completed successfully")
            
        except Exception as e:
            logger.error("Failed to complete bot setup", exc_info=e)
            raise
    
    async def load_extensions(self) -> None:
        """Load all enabled cog extensions."""
        extension_list = [
            "cogs.admin",
            "cogs.economy",
            "cogs.games",
            "cogs.voice",
            "cogs.bugs"
        ]
        
        for extension in extension_list:
            try:
                await self.load_extension(f"src.{extension}")
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}", exc_info=e)
                if "admin" in extension:  # Critical extension
                    raise
    
    async def close(self) -> None:
        """Clean up resources when shutting down."""
        logger.info("Shutting down bot...")
        
        # Close database connection
        await db.close()
        logger.info("Database connection closed")
        
        # Close cache connection
        await self.cache.disconnect()
        logger.info("Cache connection closed")
        
        # Stop game system
        await self.game.stop()
        logger.info("Game system stopped")
        
        # Close Discord connection
        await super().close()
        logger.info("Discord connection closed")
    
    async def on_ready(self) -> None:
        """Handle bot ready event."""
        logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Set presence
        activity = discord.Game(name="with strawberries 🍓")
        await self.change_presence(activity=activity)
    
    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError
    ) -> None:
        """
        Handle command errors globally.
        
        Args:
            ctx: Command context
            error: The error that occurred
        """
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "❌ You don't have permission to use this command.",
                delete_after=10
            )
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏳ Command on cooldown. Try again in {format_duration(error.retry_after)}.",
                delete_after=10
            )
            return
        
        # Log unexpected errors
        logger.error(
            f"Error in command {ctx.command} invoked by {ctx.author}"
            f" (ID: {ctx.author.id}) in {ctx.guild.name} (ID: {ctx.guild.id})",
            exc_info=error
        )
        
        await ctx.send(
            "❌ An unexpected error occurred. Please try again later.",
            delete_after=10
        )
    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """
        Handle bot joining a new server.
        
        Args:
            guild: The guild that was joined
        """
        logger.info(f"Joined guild {guild.name} (ID: {guild.id})")
        
        # Send welcome message
        system_channel = guild.system_channel
        if system_channel and system_channel.permissions_for(guild.me).send_messages:
            welcome_message = (
                "👋 Hello! I'm StrawberryBot, your friendly Discord companion!\n\n"
                "🎮 I can help with:\n"
                "• Fun games and economy system\n"
                "• Voice channel management\n"
                "• Server administration\n"
                f"• And more!\n\n"
                f"Use `{self.command_prefix}help` to see all commands."
            )
            await system_channel.send(welcome_message)
    
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """
        Handle bot leaving a server.
        
        Args:
            guild: The guild that was left
        """
        logger.info(f"Left guild {guild.name} (ID: {guild.id})")
    
    async def on_message(self, message: discord.Message) -> None:
        """
        Handle message events.
        
        Args:
            message: The message that was sent
        """
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Process commands
        await self.process_commands(message)
    
    def run(self, token: Optional[str] = None) -> None:
        """
        Run the bot with error handling.
        
        Args:
            token: Bot token (optional, can be loaded from config)
        """
        token = token or self.config.get("token")
        if not token:
            logger.error("No bot token provided")
            sys.exit(1)
        
        try:
            logger.info("Starting bot...")
            super().run(token)
        except discord.LoginFailure:
            logger.error("Failed to login: Invalid token")
            sys.exit(1)
        except Exception as e:
            logger.error("Failed to start bot", exc_info=e)
            sys.exit(1)

if __name__ == "__main__":
    # Set up logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/bot.log", encoding="utf-8")
        ]
    )
    
    # Create and run bot
    bot = StrawberryBot()
    bot.run() 