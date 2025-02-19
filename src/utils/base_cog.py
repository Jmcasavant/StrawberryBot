"""Base cog with common functionality."""
import discord
from discord.ext import commands
from typing import Optional, Union, Dict, Any
from .core import setup_logger, COLORS, ERROR_MESSAGES

logger = setup_logger(__name__)

class BaseCog(commands.Cog):
    """Base cog class with common functionality for all cogs."""
    
    def __init__(self, bot):
        self.bot = bot
        
    async def create_embed(
        self,
        title: str,
        description: Optional[str] = None,
        color: Optional[int] = None,
        fields: Optional[Dict[str, Union[str, bool]]] = None,
        footer: Optional[str] = None,
        thumbnail: Optional[str] = None
    ) -> discord.Embed:
        """Create a Discord embed with consistent styling.
        
        Args:
            title: Embed title
            description: Optional embed description
            color: Optional color override (uses info color by default)
            fields: Optional dict of field names and values
            footer: Optional footer text
            thumbnail: Optional thumbnail URL
            
        Returns:
            discord.Embed: Formatted embed
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=color or COLORS['info']
        )
        
        if fields:
            for name, value in fields.items():
                # Check if the value is a tuple with a value and inline flag
                if isinstance(value, tuple):
                    embed.add_field(name=name, value=value[0], inline=value[1])
                else:
                    embed.add_field(name=name, value=value, inline=False)
                    
        if footer:
            embed.set_footer(text=footer)
            
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        return embed
        
    async def error_embed(
        self,
        error_key: str,
        **kwargs: Any
    ) -> discord.Embed:
        """Create an error embed with consistent styling.
        
        Args:
            error_key: Key for the error message in ERROR_MESSAGES
            **kwargs: Format arguments for the error message
            
        Returns:
            discord.Embed: Formatted error embed
        """
        error_msg = ERROR_MESSAGES.get(
            error_key,
            ERROR_MESSAGES['bot_error']
        ).format(**kwargs)
        
        return await self.create_embed(
            title="Error",
            description=error_msg,
            color=COLORS['error']
        )
        
    async def success_embed(
        self,
        title: str,
        description: Optional[str] = None,
        **kwargs: Any
    ) -> discord.Embed:
        """Create a success embed with consistent styling.
        
        Args:
            title: Success message title
            description: Optional success description
            **kwargs: Additional embed arguments
            
        Returns:
            discord.Embed: Formatted success embed
        """
        return await self.create_embed(
            title=title,
            description=description,
            color=COLORS['success'],
            **kwargs
        )
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Global error handler for all cogs.
        
        Args:
            ctx: Command context
            error: The error that was raised
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                embed=await self.error_embed(
                    'cooldown',
                    time=f"{error.retry_after:.1f}s"
                )
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=await self.error_embed('permission'))
        else:
            logger.error(f"Error in {ctx.command}: {str(error)}", exc_info=error)
            await ctx.send(embed=await self.error_embed('bot_error')) 