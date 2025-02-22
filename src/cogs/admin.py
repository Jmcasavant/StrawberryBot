"""Admin cog for bot management commands."""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from utils.core import COLORS, setup_logger, OWNER_ID

logger = setup_logger(__name__)

class Admin(commands.Cog):
    """Administrative commands for bot management."""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Admin cog initialized")
        
    async def cog_load(self) -> None:
        """Called when the cog is loaded."""
        logger.info("Admin cog loaded")
        
    def is_owner_or_has_perms(self, interaction: discord.Interaction) -> bool:
        """Check if user is owner or has required permissions."""
        return interaction.user.id == OWNER_ID or interaction.channel.permissions_for(interaction.user).manage_messages
        
    @app_commands.command(name='set', description='Set a user\'s strawberry balance (Admin only)')
    @app_commands.describe(
        user="The user to set strawberries for",
        amount="Amount to set their strawberries to"
    )
    async def set(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        amount: int
    ) -> None:
        """Set a user's strawberry balance (Admin only)."""
        # Check if user is owner or admin
        if not (interaction.user.id == OWNER_ID or interaction.user.guild_permissions.administrator):
            await interaction.response.send_message(
                "❌ This command is only available to administrators!",
                ephemeral=True
            )
            return

        if amount < 0:
            await interaction.response.send_message(
                "❌ Amount cannot be negative!",
                ephemeral=True
            )
            return
            
        try:
            # Set strawberries
            await self.bot.game.set_strawberries(user.id, amount)
            
            embed = discord.Embed(
                title="💫 Strawberries Set",
                description=(
                    f"Set {user.mention}'s balance to 🍓 **{amount:,}**"
                ),
                color=COLORS['success']
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(
                f"Admin {interaction.user.id} set {user.id}'s strawberries to {amount}"
            )
            
        except Exception as e:
            logger.error(f"Error setting strawberries: {e}")
            await interaction.response.send_message(
                "❌ Failed to set strawberries!",
                ephemeral=True
            )
            
    @app_commands.command(name='cleanup', description='Clean up inactive users from the database (Admin only)')
    @app_commands.describe(
        days="Number of days of inactivity (default: 30)"
    )
    @app_commands.default_permissions(administrator=True)
    async def cleanup(
        self,
        interaction: discord.Interaction,
        days: Optional[int] = 30
    ) -> None:
        """Clean up inactive users from the database."""
        # Check if user is owner or admin
        if not (interaction.user.id == OWNER_ID or interaction.user.guild_permissions.administrator):
            await interaction.response.send_message(
                "❌ This command is only available to administrators!",
                ephemeral=True
            )
            return

        if days <= 0:
            await interaction.response.send_message(
                "❌ Days must be positive!",
                ephemeral=True
            )
            return
            
        try:
            # Defer response since this might take a while
            await interaction.response.defer(ephemeral=True)
            
            # Perform cleanup
            removed = await self.bot.game.cleanup_inactive_users(days)
            
            embed = discord.Embed(
                title="🧹 Database Cleanup",
                description=f"Removed {removed} inactive users",
                color=COLORS['success']
            )
            
            if removed:
                # Show some examples of removed users
                examples = removed[:5]
                users = []
                for user_id in examples:
                    user = self.bot.get_user(user_id)
                    users.append(
                        user.mention if user else f"User {user_id}"
                    )
                    
                embed.add_field(
                    name="Examples",
                    value="\n".join(users),
                    inline=False
                )
                
                if len(removed) > 5:
                    embed.set_footer(
                        text=f"And {len(removed) - 5} more..."
                    )
                    
            await interaction.followup.send(embed=embed)
            
            logger.info(
                f"Admin {interaction.user.id} cleaned up {len(removed)} inactive users"
            )
            
        except Exception as e:
            logger.error(f"Error cleaning up users: {e}")
            await interaction.followup.send(
                "❌ Failed to clean up users!",
                ephemeral=True
            )
            
    @app_commands.command(name='purge', description='Clean up messages in a channel')
    @app_commands.describe(
        amount="Number of messages to delete (default: 10)",
        user="Only delete messages from this user (optional)"
    )
    @app_commands.guild_only()  # Ensure command only works in servers
    async def purge(
        self,
        interaction: discord.Interaction,
        amount: Optional[int] = 10,
        user: Optional[discord.User] = None
    ) -> None:
        """Clean up messages in a channel."""
        logger.info(f"Purge command invoked by {interaction.user.id} for {amount} messages")

        # Check bot permissions first
        if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
            await interaction.response.send_message(
                "❌ I don't have permission to delete messages in this channel!",
                ephemeral=True
            )
            return

        # Check user permissions with owner bypass
        if not self.is_owner_or_has_perms(interaction):
            await interaction.response.send_message(
                "❌ You need the 'Manage Messages' permission to use this command!",
                ephemeral=True
            )
            return
        
        try:
            # Validate input
            if amount <= 0 or amount > 1000:
                logger.warning(f"Invalid amount ({amount}) specified for purge command")
                await interaction.response.send_message(
                    "❌ Please specify a number between 1 and 1000.",
                    ephemeral=True
                )
                return

            # Send immediate acknowledgment
            await interaction.response.send_message(
                f"🗑️ Deleting {amount} messages...",
                ephemeral=True
            )
            
            # Get messages to delete
            messages_to_delete = []
            search_limit = amount * 3 if user else amount  # Search more messages if filtering by user
            
            async for message in interaction.channel.history(limit=search_limit):
                if len(messages_to_delete) >= amount:
                    break
                if user is None or message.author == user:
                    messages_to_delete.append(message)
            
            logger.debug(f"Found {len(messages_to_delete)} messages to delete")
            
            if not messages_to_delete:
                await interaction.edit_original_response(
                    content="❌ No messages found to delete!"
                )
                return
            
            # Delete messages in chunks to avoid rate limits
            chunk_size = 100
            deleted_count = 0
            
            for i in range(0, len(messages_to_delete), chunk_size):
                chunk = messages_to_delete[i:i + chunk_size]
                try:
                    await interaction.channel.delete_messages(chunk)
                    deleted_count += len(chunk)
                    logger.debug(f"Deleted chunk of {len(chunk)} messages")
                    
                    # Update progress message every chunk
                    progress = f"🗑️ Deleted {deleted_count}/{len(messages_to_delete)} messages..."
                    await interaction.edit_original_response(content=progress)
                    
                    await asyncio.sleep(1)  # Small delay between chunks
                except discord.HTTPException as e:
                    if 'message_id' in str(e):  # Message too old
                        logger.warning(f"Skipped old messages: {e}")
                        continue
                    logger.error(f"HTTP error while deleting messages: {e}")
                    raise
            
            # Send completion message
            if deleted_count > 0:
                final_message = (
                    f"✨ Successfully deleted {deleted_count} message{'s' if deleted_count != 1 else ''}"
                    f"{f' from {user.display_name}' if user else ''}!"
                )
                await interaction.edit_original_response(content=final_message)
                logger.info(f"Successfully purged {deleted_count} messages")
            else:
                await interaction.edit_original_response(
                    content="❌ No messages were deleted. They might be too old (>14 days)."
                )
                logger.warning("No messages were deleted during purge")
            
        except discord.Forbidden as e:
            logger.error(f"Permission error during purge: {e}")
            await interaction.edit_original_response(
                content="❌ I don't have permission to delete messages!"
            )
        except Exception as e:
            logger.error(f"Unexpected error during purge: {e}", exc_info=True)
            await interaction.edit_original_response(
                content="❌ An error occurred while purging messages!"
            )
            
async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(Admin(bot)) 