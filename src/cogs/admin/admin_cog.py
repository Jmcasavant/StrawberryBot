"""
Admin commands for StrawberryBot.

This module provides administrative commands for:
- Bot management
- Permission control
- Server configuration
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
from src.utils.base_cog import BaseCog
from src.utils.helpers.decorators import owner_only, admin_only

class AdminCog(BaseCog):
    """Administrative commands for bot management."""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
    
    @app_commands.command(name="setperms", description="Set command permissions (Bot Owner Only)")
    @app_commands.describe(
        command_name="The command to set permissions for",
        roles="Role IDs (comma-separated)",
        users="User IDs (comma-separated)",
        channels="Channel IDs (comma-separated)"
    )
    @owner_only()
    async def set_permissions(
        self,
        interaction: discord.Interaction,
        command_name: str,
        roles: Optional[str] = None,
        users: Optional[str] = None,
        channels: Optional[str] = None
    ):
        """
        Set permissions for a command.
        Only the bot owner can use this command.
        """
        # Parse IDs
        role_ids = [int(x.strip()) for x in roles.split(",")] if roles else None
        user_ids = [int(x.strip()) for x in users.split(",")] if users else None
        channel_ids = [int(x.strip()) for x in channels.split(",")] if channels else None
        
        # Set permissions
        success = await self.set_command_permissions(
            interaction.guild.id,
            command_name,
            role_ids,
            user_ids,
            channel_ids
        )
        
        if success:
            # Create a readable summary
            perms_summary = []
            if role_ids:
                role_mentions = [f"<@&{role_id}>" for role_id in role_ids]
                perms_summary.append(f"Roles: {', '.join(role_mentions)}")
            if user_ids:
                user_mentions = [f"<@{user_id}>" for user_id in user_ids]
                perms_summary.append(f"Users: {', '.join(user_mentions)}")
            if channel_ids:
                channel_mentions = [f"<#{channel_id}>" for channel_id in channel_ids]
                perms_summary.append(f"Channels: {', '.join(channel_mentions)}")
            
            summary = "\n".join(perms_summary) if perms_summary else "Default permissions"
            
            embed = await self.create_embed(
                "✅ Permissions Updated",
                f"Command: `{command_name}`\n{summary}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = await self.create_embed(
                "❌ Error",
                "Failed to update permissions. Make sure the command exists.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="clearperms", description="Clear command permissions (Bot Owner Only)")
    @app_commands.describe(command_name="The command to clear permissions for")
    @owner_only()
    async def clear_permissions(
        self,
        interaction: discord.Interaction,
        command_name: str
    ):
        """
        Clear all custom permissions for a command.
        Only the bot owner can use this command.
        """
        # Clear permissions by setting all to None
        success = await self.set_command_permissions(
            interaction.guild.id,
            command_name,
            None,
            None,
            None
        )
        
        if success:
            embed = await self.create_embed(
                "✅ Permissions Cleared",
                f"Command `{command_name}` restored to default permissions.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = await self.create_embed(
                "❌ Error",
                "Failed to clear permissions. Make sure the command exists.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="listperms", description="List command permissions (Bot Owner Only)")
    @owner_only()
    async def list_permissions(self, interaction: discord.Interaction):
        """
        List all custom permissions in the server.
        Only the bot owner can use this command.
        """
        server_config = await self.get_server_config(interaction.guild.id)
        if not server_config or not server_config.custom_settings.get("command_permissions"):
            embed = await self.create_embed(
                "Command Permissions",
                "No custom permissions set.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Build permissions summary
        perms = server_config.custom_settings["command_permissions"]
        summary = []
        
        for command, settings in perms.items():
            parts = []
            if settings.get("allowed_roles"):
                role_mentions = [f"<@&{role_id}>" for role_id in settings["allowed_roles"]]
                parts.append(f"Roles: {', '.join(role_mentions)}")
            if settings.get("allowed_users"):
                user_mentions = [f"<@{user_id}>" for user_id in settings["allowed_users"]]
                parts.append(f"Users: {', '.join(user_mentions)}")
            if settings.get("allowed_channels"):
                channel_mentions = [f"<#{channel_id}>" for channel_id in settings["allowed_channels"]]
                parts.append(f"Channels: {', '.join(channel_mentions)}")
            
            summary.append(f"**{command}**\n" + "\n".join(parts))
        
        embed = await self.create_embed(
            "Command Permissions",
            "\n\n".join(summary),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    await bot.add_cog(AdminCog(bot)) 