"""Main bot module."""
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import sys
import re
import random
import asyncio
from typing import Optional, List
from pathlib import Path

from utils.strawberry_game import StrawberryGame
from utils.core import (
    INTENTS,
    ACTIVITY,
    STRAWBERRY_MESSAGES,
    STRAWBERRY_LAYOUTS,
    MIN_RANDOM_STRAWBERRIES,
    MAX_RANDOM_STRAWBERRIES,
    COLORS,
    setup_logger,
    OWNER_ID
)
from utils.bug_tracker import BugTracker

logger = setup_logger(__name__)

class StrawberryBot(commands.Bot):
    """Main bot class with enhanced functionality."""
    
    def __init__(self):
        super().__init__(
            command_prefix="!",  # Fallback prefix
            intents=INTENTS,
            activity=ACTIVITY
        )
        
        # Initialize game state
        self.game = StrawberryGame()
        
        # Initialize bug tracker
        self.bug_tracker = BugTracker()
        
        # Store the bot's owner ID
        self.owner_id = OWNER_ID
        
    async def setup_hook(self) -> None:
        """Initialize the bot and load all cogs."""
        try:
            logger.info("Starting bot setup...")
            
            # Load cogs one at a time with error handling
            for cog in ['admin', 'economy', 'games', 'voice', 'minecraft']:
                try:
                    logger.info(f"Loading {cog} cog...")
                    cog_path = f"cogs.{cog}"
                    await self.load_extension(cog_path)
                    logger.info(f"Successfully loaded {cog} cog")
                except Exception as e:
                    logger.error(f"Failed to load {cog} cog: {e}", exc_info=True)
                    if cog in ['admin', 'economy', 'games']:  # Critical cogs
                        raise  # Re-raise for critical cogs
                    else:
                        logger.warning(f"Continuing without {cog} cog")
            
            # Start game auto-save with timeout
            try:
                logger.info("Starting game auto-save...")
                async with asyncio.timeout(5.0):  # 5 second timeout
                    await self.game.start()
                logger.info("Game auto-save started successfully")
            except asyncio.TimeoutError:
                logger.error("Timeout while starting game auto-save")
                raise
            except Exception as e:
                logger.error(f"Failed to start game auto-save: {e}", exc_info=True)
                raise
            
            # Sync commands with timeout
            try:
                logger.info("Syncing commands...")
                async with asyncio.timeout(10.0):  # 10 second timeout
                    await self.tree.sync()
                logger.info("Commands synced successfully")
            except asyncio.TimeoutError:
                logger.error("Timeout while syncing commands")
                raise
            except Exception as e:
                logger.error(f"Failed to sync commands: {e}", exc_info=True)
                raise
            
            # Add error handling for interaction timeouts
            self.tree.on_error = self.on_app_command_error
            
            logger.info("Bot setup completed successfully")
            
        except Exception as e:
            logger.error(f"Critical error during setup: {e}", exc_info=True)
            raise
            
    async def close(self) -> None:
        """Clean up and close the bot."""
        # Stop game auto-save
        await self.game.stop()
        
        # Call parent close
        await super().close()
        
    async def load_extensions(self) -> None:
        """Load all cog extensions."""
        cog_dir = Path(__file__).parent / "cogs"
        for cog in ['admin', 'voice', 'economy', 'games', 'minecraft', 'bugs']:
            try:
                cog_path = f"cogs.{cog}"
                await self.load_extension(cog_path)
            except Exception as e:
                logger.error(f"Error loading {cog} cog: {e}", exc_info=True)
                raise  # Re-raise to prevent partial loading
                
    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        logger.info(f"Bot ready - {self.user} ({self.user.id})")
        logger.info(f"Active in {len(self.guilds)} guilds with {len(set(self.get_all_members()))} users")
        
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when the bot joins a new guild."""
        logger.info(f"Joined guild: {guild.name} ({guild.id})")
        
        try:
            channel = next((
                chan for chan in guild.text_channels
                if chan.permissions_for(guild.me).send_messages
            ), None)
            
            if channel:
                embed = discord.Embed(
                    title="🍓 Thanks for adding Strawberry Bot!",
                    description="Use slash commands like `/daily` and `/strawberries` to get started!",
                    color=COLORS['success']
                )
                await channel.send(embed=embed)
                await self.tree.sync(guild=guild)
                
        except Exception as e:
            logger.error(f"Error in guild join for {guild.name}: {e}")
            
    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages."""
        # Ignore messages from bots
        if message.author.bot:
            return
            
        # Check for strawberry mentions
        if re.search(r'strawberr(y|ies)', message.content, re.IGNORECASE):
            await self.send_random_strawberries(message.channel)
            
    async def send_random_strawberries(self, channel: discord.TextChannel) -> None:
        """Send a random strawberry message."""
        try:
            count = random.randint(MIN_RANDOM_STRAWBERRIES, MAX_RANDOM_STRAWBERRIES)
            layout = random.choice(STRAWBERRY_LAYOUTS)
            
            # Create strawberry message
            strawberries = f"{layout} " * (count // len(layout.split()))
            if count % len(layout.split()):
                strawberries += "🍓 " * (count % len(layout.split()))
                
            embed = discord.Embed(
                title=random.choice(STRAWBERRY_MESSAGES),
                description=strawberries,
                color=COLORS['economy']
            )
            
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending strawberry message: {e}")
            
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """Handle errors in slash commands."""
        error_message = f"Error in command '{interaction.command.name if interaction.command else 'unknown'}': {str(error)}"
        logger.error(error_message, exc_info=error)
        
        try:
            if isinstance(error, app_commands.CommandOnCooldown):
                await interaction.response.send_message(
                    f"⏰ Command on cooldown! Try again in {error.retry_after:.1f}s",
                    ephemeral=True
                )
            elif isinstance(error, app_commands.MissingPermissions):
                await interaction.response.send_message(
                    "❌ You don't have permission to use this command!",
                    ephemeral=True
                )
            else:
                # Check if interaction is already responded to
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An error occurred! Please try again later.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An error occurred! Please try again later.",
                        ephemeral=True
                    )
        except Exception as e:
            logger.error(f"Error handling command error: {e}", exc_info=True)
            
    async def on_interaction(self, interaction: discord.Interaction):
        """Log all interactions for debugging."""
        if interaction.type == discord.InteractionType.application_command:
            logger.debug(  # Changed to debug level since this is verbose
                f"Command: {interaction.command.name} from {interaction.user.id}"
            )
        await super().on_interaction(interaction)

def main():
    """Main entry point for the bot."""
    load_dotenv()
    token = os.getenv("DISCORD_BOT_TOKEN")
    
    if not token:
        logger.error("No Discord bot token found in .env file")
        sys.exit(1)
        
    bot = StrawberryBot()
    
    try:
        bot.run(token, log_handler=None)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main() 