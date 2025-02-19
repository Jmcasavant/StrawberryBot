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
    COMMAND_PREFIX,
    STRAWBERRY_MESSAGES,
    STRAWBERRY_LAYOUTS,
    MIN_RANDOM_STRAWBERRIES,
    MAX_RANDOM_STRAWBERRIES,
    COLORS,
    COMMAND_GROUPS,
    COMMAND_DESCRIPTIONS,
    setup_logger
)

logger = setup_logger(__name__)

class StrawberryBot(commands.Bot):
    """Main bot class with enhanced functionality."""
    
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(COMMAND_PREFIX),
            intents=INTENTS,
            activity=ACTIVITY,
            case_insensitive=True
        )
        self.game = StrawberryGame()
        
        # Remove default help command
        self.remove_command('help')
        
    async def setup_hook(self) -> None:
        """Initialize the bot and load all cogs."""
        # Load all cogs
        await self.load_extensions()
        
        # Start game auto-save
        await self.game.start()
        
        # Sync all commands
        await self.tree.sync()
        
        logger.info("Bot setup completed")
        
    async def close(self) -> None:
        """Clean up and close the bot."""
        # Stop game auto-save
        await self.game.stop()
        
        # Call parent close
        await super().close()
        
    async def load_extensions(self) -> None:
        """Load all cog extensions."""
        for cog in ['admin', 'voice', 'economy', 'games']:
            try:
                await self.load_extension(f'cogs.{cog}')
                logger.info(f"Loaded {cog} cog")
            except Exception as e:
                logger.error(f"Error loading {cog} cog: {e}")
                
    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Print some useful info
        logger.info(f"Connected to {len(self.guilds)} guilds")
        logger.info(f"Serving {len(set(self.get_all_members()))} unique users")
        
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
                        "Use `/help` to see all commands.\n"
                        "Start earning strawberries with `/daily`!"
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
            
        # Process commands first
        await self.process_commands(message)
        
        # Check for strawberry mentions (not in commands)
        if not message.content.startswith(COMMAND_PREFIX):
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
            logger.error(f"Error in slash command: {str(error)}", exc_info=error)
            await interaction.response.send_message(
                "❌ An error occurred! Please try again later.",
                ephemeral=True
            )

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