"""
Command decorators for StrawberryBot.

This module provides decorators for:
- Permission checking
- Cooldowns
- Error handling
- Feature toggles
"""

import functools
from typing import Callable, Optional, Union
import discord
from discord import app_commands
from discord.ext import commands
from src.config.settings import is_owner

def owner_only() -> Callable:
    """
    Decorator that ensures only the bot owner can use the command.
    This is the highest level of permission and overrides all other checks.
    
    Returns:
        Decorated command function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            # Check if user is an owner
            if not is_owner(interaction.user.id):
                await interaction.response.send_message(
                    "❌ This command can only be used by the bot owner.",
                    ephemeral=True
                )
                return
            
            # Execute command if owner
            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator

def requires_permissions_v2(
    *,
    required_permissions: discord.Permissions,
    error_message: Optional[str] = None
) -> Callable:
    """
    Decorator to check command permissions using the V2 system.
    
    Args:
        required_permissions: Base permissions required for the command
        error_message: Custom error message to show on failure
        
    Returns:
        Decorated command function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            # Always allow bot owners
            if is_owner(interaction.user.id):
                return await func(self, interaction, *args, **kwargs)
            
            # Get command name
            command_name = func.__name__
            
            # Check permissions
            has_permission = await self.check_permissions_v2(
                interaction,
                command_name,
                required_permissions
            )
            
            if not has_permission:
                # Send error message
                message = error_message or "❌ You don't have permission to use this command."
                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )
                return
            
            # Execute command if permitted
            return await func(self, interaction, *args, **kwargs)
        
        # Add command metadata
        if isinstance(func, app_commands.Command):
            func.default_permissions = required_permissions
        
        return wrapper
    return decorator

def admin_only() -> Callable:
    """
    Decorator for commands that require administrator permissions.
    
    Returns:
        Decorated command function
    """
    return requires_permissions_v2(
        required_permissions=discord.Permissions(administrator=True),
        error_message="❌ This command requires administrator permissions."
    )

def moderator_only() -> Callable:
    """
    Decorator for commands that require moderator permissions.
    
    Returns:
        Decorated command function
    """
    mod_permissions = discord.Permissions(
        manage_messages=True,
        kick_members=True,
        ban_members=True
    )
    return requires_permissions_v2(
        required_permissions=mod_permissions,
        error_message="❌ This command requires moderator permissions."
    )

def custom_permissions(
    *,
    allowed_roles: Optional[list[int]] = None,
    allowed_users: Optional[list[int]] = None,
    allowed_channels: Optional[list[int]] = None,
    error_message: Optional[str] = None
) -> Callable:
    """
    Decorator for commands with custom permission requirements.
    
    Args:
        allowed_roles: List of role IDs that can use the command
        allowed_users: List of user IDs that can use the command
        allowed_channels: List of channel IDs where the command can be used
        error_message: Custom error message to show on failure
        
    Returns:
        Decorated command function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            # Always allow bot owners
            if is_owner(interaction.user.id):
                return await func(self, interaction, *args, **kwargs)
            
            if not interaction.guild:
                await interaction.response.send_message(
                    "❌ This command can only be used in servers.",
                    ephemeral=True
                )
                return
            
            # Set up custom permissions for the command
            command_name = func.__name__
            await self.set_command_permissions(
                interaction.guild.id,
                command_name,
                allowed_roles,
                allowed_users,
                allowed_channels
            )
            
            # Check permissions
            has_permission = await self.check_permissions_v2(
                interaction,
                command_name,
                discord.Permissions()  # No base permissions required
            )
            
            if not has_permission:
                message = error_message or "❌ You don't have permission to use this command."
                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )
                return
            
            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator 