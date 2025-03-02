"""
Base cog implementation with enhanced functionality.

This module provides a base cog class with:
- Shared utility methods
- Error handling
- Permission checking
- Caching integration
- Database access
- Logging
"""

import logging
from typing import Optional, Any, TypeVar, Type, cast, List
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from discord import app_commands
from src.utils.database.session import db
from src.utils.database.models import User, ServerConfig
from src.utils.cache.redis_cache import RedisCache
from src.config.settings import get_config

# Type variable for model classes
T = TypeVar("T")

class BaseCog(commands.Cog):
    """
    Enhanced base cog with utility methods and integrations.
    
    Features:
    - Database integration
    - Caching support
    - Permission checking
    - Error handling
    - Logging
    - Utility methods
    """
    
    def __init__(self, bot: commands.Bot):
        """
        Initialize the cog.
        
        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.logger = logging.getLogger(f"strawberry.cogs.{self.__class__.__name__}")
        self.cache = RedisCache(prefix=f"{self.__class__.__name__.lower()}:")
        self.features = get_config("features")
    
    async def get_user_data(
        self,
        user_id: int,
        *,
        use_cache: bool = True
    ) -> Optional[User]:
        """
        Get user data from database with caching.
        
        Args:
            user_id: Discord user ID
            use_cache: Whether to use cache
            
        Returns:
            User data or None if not found
        """
        # Try cache first
        if use_cache:
            cached = await self.cache.get(f"user:{user_id}")
            if cached:
                return User(**cached)
        
        # Query database
        async with db.session() as session:
            result = await session.get(User, user_id)
            if result:
                # Cache for next time
                await self.cache.set(f"user:{user_id}", result.__dict__)
            return result
    
    async def get_server_config(
        self,
        guild_id: int,
        *,
        use_cache: bool = True
    ) -> Optional[ServerConfig]:
        """
        Get server configuration with caching.
        
        Args:
            guild_id: Discord server ID
            use_cache: Whether to use cache
            
        Returns:
            Server config or None if not found
        """
        # Try cache first
        if use_cache:
            cached = await self.cache.get(f"server:{guild_id}")
            if cached:
                return ServerConfig(**cached)
        
        # Query database
        async with db.session() as session:
            result = await session.get(ServerConfig, guild_id)
            if result:
                # Cache for next time
                await self.cache.set(f"server:{guild_id}", result.__dict__)
            return result
    
    async def check_feature_enabled(
        self,
        feature: str,
        guild_id: Optional[int] = None
    ) -> bool:
        """
        Check if a feature is enabled globally and for the server.
        
        Args:
            feature: Feature name to check
            guild_id: Optional server ID to check
            
        Returns:
            True if feature is enabled
        """
        # Check global feature flag
        if not self.features.get(f"{feature}_enabled", True):
            return False
        
        # Check server config if provided
        if guild_id:
            config = await self.get_server_config(guild_id)
            if config:
                return getattr(config, f"{feature}_enabled", True)
        
        return True
    
    async def has_permission(
        self,
        ctx: commands.Context,
        permission: str
    ) -> bool:
        """
        Check if user has required permission.
        
        Args:
            ctx: Command context
            permission: Permission to check
            
        Returns:
            True if user has permission
        """
        # Bot owner always has permission
        if await self.bot.is_owner(ctx.author):
            return True
        
        # Check Discord permissions
        if isinstance(ctx.channel, discord.TextChannel):
            return getattr(ctx.channel.permissions_for(ctx.author), permission, False)
        
        return False
    
    async def get_or_create(
        self,
        model: Type[T],
        defaults: Optional[dict] = None,
        **kwargs: Any
    ) -> tuple[T, bool]:
        """
        Get an existing record or create a new one.
        
        Args:
            model: Model class
            defaults: Default values for new record
            **kwargs: Lookup parameters
            
        Returns:
            Tuple of (record, created)
        """
        async with db.session() as session:
            instance = await session.get(model, kwargs)
            if instance:
                return cast(T, instance), False
            
            # Create new instance
            defaults = defaults or {}
            kwargs.update(defaults)
            instance = model(**kwargs)
            session.add(instance)
            await session.commit()
            return instance, True
    
    @staticmethod
    def format_timedelta(delta: timedelta) -> str:
        """
        Format a timedelta into a human-readable string.
        
        Args:
            delta: Time difference
            
        Returns:
            Formatted string
        """
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds or not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    async def create_embed(
        self,
        title: str,
        description: Optional[str] = None,
        color: Optional[discord.Color] = None,
        **kwargs: Any
    ) -> discord.Embed:
        """
        Create a consistent Discord embed.
        
        Args:
            title: Embed title
            description: Optional description
            color: Optional color
            **kwargs: Additional embed parameters
            
        Returns:
            Discord embed
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=color or discord.Color.blurple(),
            timestamp=datetime.utcnow(),
            **kwargs
        )
        
        # Add bot name to footer
        embed.set_footer(
            text=f"{self.bot.user.name if self.bot.user else 'StrawberryBot'}",
            icon_url=self.bot.user.avatar.url if self.bot.user and self.bot.user.avatar else None
        )
        
        return embed
    
    async def log_error(
        self,
        error: Exception,
        ctx: Optional[commands.Context] = None
    ) -> None:
        """
        Log an error with context.
        
        Args:
            error: The error to log
            ctx: Optional command context
        """
        if ctx:
            self.logger.error(
                f"Error in {ctx.command} invoked by {ctx.author} (ID: {ctx.author.id})"
                f" in {ctx.guild.name} (ID: {ctx.guild.id}): {str(error)}",
                exc_info=error
            )
        else:
            self.logger.error(f"Error: {str(error)}", exc_info=error)
    
    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError
    ) -> None:
        """
        Handle command errors.
        
        Args:
            ctx: Command context
            error: The error that occurred
        """
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=await self.create_embed(
                    "❌ Permission Denied",
                    "You don't have permission to use this command.",
                    color=discord.Color.red()
                )
            )
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                embed=await self.create_embed(
                    "⏳ Command on Cooldown",
                    f"Please wait {self.format_timedelta(timedelta(seconds=error.retry_after))}.",
                    color=discord.Color.orange()
                )
            )
            return
        
        # Log unexpected errors
        await self.log_error(error, ctx)
        await ctx.send(
            embed=await self.create_embed(
                "❌ Error",
                "An unexpected error occurred. Please try again later.",
                color=discord.Color.red()
            )
        )
    
    async def check_permissions_v2(
        self,
        ctx: discord.Interaction,
        command_name: str,
        required_permissions: discord.Permissions
    ) -> bool:
        """
        Check if a user has permission to use a command using the V2 permission system.
        
        Args:
            ctx: Interaction context
            command_name: Name of the command being checked
            required_permissions: Base permissions required for the command
            
        Returns:
            True if user has permission
        """
        if not ctx.guild:
            return False  # DMs not supported
            
        # 1. Check if guild has V2 permissions enabled
        if not ctx.guild.features.has("APPLICATION_COMMAND_PERMISSIONS_V2"):
            # Fall back to old permission system
            return await self.has_permission(ctx, required_permissions)
            
        # 2. Check default member permissions
        if not ctx.user.guild_permissions >= required_permissions:
            # User doesn't meet base permission requirements
            return False
            
        # 3. Check app-level permissions
        server_config = await self.get_server_config(ctx.guild.id)
        if server_config:
            # Check if user has admin role
            if server_config.admin_role_id:
                admin_role = ctx.guild.get_role(server_config.admin_role_id)
                if admin_role and admin_role in ctx.user.roles:
                    return True
                    
            # Check custom permissions from server config
            custom_perms = server_config.custom_settings.get("command_permissions", {})
            if command_name in custom_perms:
                cmd_perms = custom_perms[command_name]
                
                # Check role permissions
                allowed_roles = cmd_perms.get("allowed_roles", [])
                if allowed_roles:
                    user_roles = [role.id for role in ctx.user.roles]
                    if not any(role_id in allowed_roles for role_id in user_roles):
                        return False
                
                # Check user permissions
                allowed_users = cmd_perms.get("allowed_users", [])
                if allowed_users and ctx.user.id not in allowed_users:
                    return False
                    
                # Check channel permissions
                allowed_channels = cmd_perms.get("allowed_channels", [])
                if allowed_channels and ctx.channel.id not in allowed_channels:
                    return False
        
        # 4. Cache the result to avoid repeated checks
        cache_key = f"perms:{ctx.guild.id}:{ctx.user.id}:{command_name}"
        await self.cache.set(cache_key, True, ttl=300)  # Cache for 5 minutes
        
        return True
    
    async def set_command_permissions(
        self,
        guild_id: int,
        command_name: str,
        allowed_roles: Optional[List[int]] = None,
        allowed_users: Optional[List[int]] = None,
        allowed_channels: Optional[List[int]] = None
    ) -> bool:
        """
        Set command-level permissions for a specific command.
        
        Args:
            guild_id: ID of the guild
            command_name: Name of the command
            allowed_roles: List of role IDs that can use the command
            allowed_users: List of user IDs that can use the command
            allowed_channels: List of channel IDs where the command can be used
            
        Returns:
            True if permissions were set successfully
        """
        async with db.session() as session:
            server_config = await session.get(ServerConfig, guild_id)
            if not server_config:
                return False
                
            # Get or initialize command permissions
            custom_settings = server_config.custom_settings or {}
            command_permissions = custom_settings.get("command_permissions", {})
            
            # Update permissions for the command
            command_permissions[command_name] = {
                "allowed_roles": allowed_roles or [],
                "allowed_users": allowed_users or [],
                "allowed_channels": allowed_channels or []
            }
            
            # Save back to database
            custom_settings["command_permissions"] = command_permissions
            server_config.custom_settings = custom_settings
            await session.commit()
            
            # Clear cached permissions
            cache_key = f"perms:{guild_id}:*:{command_name}"
            await self.cache.clear_prefix(cache_key)
            
            return True 