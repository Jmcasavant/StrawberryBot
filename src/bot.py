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
    setup_logger
)

logger = setup_logger(__name__)

class StrawberryBot(commands.Bot):
    """Main bot class with enhanced functionality."""
    
    def __init__(self):
        super().__init__(
            command_prefix=None,  # No prefix needed for slash commands
            intents=INTENTS,
            activity=ACTIVITY,
            case_insensitive=True
        )
        self.game = StrawberryGame()
        
    async def setup_hook(self) -> None:
        """Initialize the bot and load all cogs."""
        try:
            # Load all cogs
            logger.info("Starting to load extensions...")
            await self.load_extensions()
            logger.info("Successfully loaded all extensions")
            
            # Start game auto-save
            logger.info("Starting game auto-save...")
            await self.game.start()
            logger.info("Game auto-save started")
            
            # Sync all commands with detailed logging
            logger.info("Starting command sync process...")
            try:
                synced = await self.tree.sync()
                logger.info(f"Successfully synced {len(synced)} slash command(s)")
                for cmd in synced:
                    logger.info(f"Synced command: {cmd.name}")
            except Exception as sync_error:
                logger.error(f"Error during command sync: {sync_error}", exc_info=True)
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
        for cog in ['admin', 'voice', 'economy', 'games']:
            try:
                cog_path = f"cogs.{cog}"
                logger.info(f"Loading cog from {cog_path}")
                await self.load_extension(cog_path)
                logger.info(f"Successfully loaded {cog} cog")
            except Exception as e:
                logger.error(f"Error loading {cog} cog: {e}", exc_info=True)
                raise  # Re-raise to prevent partial loading
                
    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Print some useful info
        logger.info(f"Connected to {len(self.guilds)} guilds")
        logger.info(f"Serving {len(set(self.get_all_members()))} unique users")
        
        # Ensure commands are synced
        try:
            synced = await self.tree.sync()
            logger.info(f"Re-synced {len(synced)} slash command(s)")
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")
        
        logger.info("Bot is ready!")
        
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when the bot joins a new guild."""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Try to send a welcome message
        try:
            # Find the first channel we can send messages in
            channel = next((
                chan for chan in guild.text_channels
                if chan.permissions_for(guild.me).send_messages
            ), None)
            
            if channel:
                embed = discord.Embed(
                    title="🍓 Thanks for adding Strawberry Bot!",
                    description=(
                        "Use slash commands like `/daily` and `/strawberries` to get started!"
                    ),
                    color=COLORS['success']
                )
                await channel.send(embed=embed)
                
                # Sync slash commands for the new guild
                await self.tree.sync(guild=guild)
                
        except Exception as e:
            logger.error(f"Error sending welcome message to {guild.name}: {e}")
            
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
            logger.info(
                f"Received command interaction: {interaction.command.name} from {interaction.user.id}"
            )
        await super().on_interaction(interaction)

def main():
    """Main entry point for the bot."""
    # Load environment variables
    load_dotenv()
    token = os.getenv("DISCORD_BOT_TOKEN")
    
    if not token:
        logger.error("No Discord bot token found in .env file")
        sys.exit(1)
        
    # Create and run bot
    bot = StrawberryBot()
    
    try:
        logger.info("Starting bot...")
        bot.run(token, log_handler=None)  # Disable discord.py's logging
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main() 