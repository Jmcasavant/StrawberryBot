"""Admin cog for bot management commands."""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from utils.core import COLORS, COMMAND_GROUPS, setup_logger

logger = setup_logger(__name__)

class Admin(commands.Cog):
    """Administrative commands for bot management."""
    
    def __init__(self, bot):
        self.bot = bot
        
    # Traditional command
    @commands.command(name='purge')
    async def purge_command(self, ctx, amount: int = 5, user: Optional[discord.Member] = None) -> None:
        """Clean up messages in a channel.
        
        Usage:
        !sb purge <amount>          - Delete <amount> messages
        !sb purge <amount> @user    - Delete <amount> messages from @user
        """
        try:
            # Delete messages
            def check(message):
                if user:
                    return message.author == user
                return True
                
            # Add 1 to include command message
            deleted = await ctx.channel.purge(
                limit=amount + 1,
                check=check
            )
            
            # Send result
            if user:
                result_msg = await ctx.send(
                    f"✨ Deleted {len(deleted)-1} messages from {user.mention}!"
                )
            else:
                result_msg = await ctx.send(
                    f"✨ Deleted {len(deleted)-1} messages!"
                )
            
            # Auto-delete the result message after 3 seconds
            await asyncio.sleep(3)
            await result_msg.delete()
            
            # Log the action
            logger.info(
                f"Purge: {ctx.author} deleted {len(deleted)-1} messages"
                f"{f' from {user}' if user else ''} in #{ctx.channel}"
            )
            
        except discord.Forbidden:
            await ctx.send("❌ I need the 'Manage Messages' permission!")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
            logger.error(f"Error purging messages: {e}")
            
    admin = app_commands.Group(
        name=COMMAND_GROUPS['admin']['name'],
        description=COMMAND_GROUPS['admin']['description'],
        default_permissions=discord.Permissions(administrator=True)
    )
    
    @admin.command(name='give')
    @app_commands.describe(
        user="The user to give strawberries to",
        amount="Amount of strawberries to give"
    )
    async def give(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        amount: int
    ) -> None:
        """Give strawberries to a user (Admin only)."""
        if amount <= 0:
            await interaction.response.send_message(
                "❌ Amount must be positive!",
                ephemeral=True
            )
            return
            
        try:
            # Add strawberries
            await self.bot.game.add_strawberries(user.id, amount)
            
            # Get new balance
            new_balance = self.bot.game.get_player_data(user.id)['strawberries']
            
            embed = discord.Embed(
                title="🎁 Strawberries Given",
                description=f"Given 🍓 **{amount:,}** to {user.mention}",
                color=COLORS['success']
            )
            
            embed.add_field(
                name="New Balance",
                value=f"🍓 {new_balance:,}",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(
                f"Admin {interaction.user.id} gave {amount} strawberries to {user.id}"
            )
            
        except Exception as e:
            logger.error(f"Error giving strawberries: {e}")
            await interaction.response.send_message(
                "❌ Failed to give strawberries!",
                ephemeral=True
            )
            
    @admin.command(name='set')
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
            
    @admin.command(name='cleanup')
    @app_commands.describe(
        days="Number of days of inactivity (default: 30)"
    )
    async def cleanup(
        self,
        interaction: discord.Interaction,
        days: Optional[int] = 30
    ) -> None:
        """Clean up inactive users from the database."""
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
            
    # Slash command version of purge
    @admin.command(name='purge')
    @app_commands.describe(
        amount="Number of messages to delete (default: 100)",
        user="Only delete messages from this user (optional)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge_slash(
        self,
        interaction: discord.Interaction,
        amount: Optional[int] = 100,
        user: Optional[discord.User] = None
    ) -> None:
        """Clean up messages in a channel."""
        if amount <= 0:
            await interaction.response.send_message(
                "❌ Amount must be positive!",
                ephemeral=True
            )
            return
            
        if amount > 1000:
            await interaction.response.send_message(
                "❌ Cannot delete more than 1000 messages at once!",
                ephemeral=True
            )
            return
            
        try:
            # Defer response since this might take a while
            await interaction.response.defer(ephemeral=True)
            
            # Delete messages
            def check(message):
                return user is None or message.author == user
                
            deleted = await interaction.channel.purge(
                limit=amount,
                check=check,
                reason=f"Purge command used by {interaction.user}"
            )
            
            # Send result
            await interaction.followup.send(
                f"✨ Deleted {len(deleted)} messages!",
                ephemeral=True
            )
            
            logger.info(
                f"Admin {interaction.user.id} purged {len(deleted)} messages in "
                f"channel {interaction.channel.id}"
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to delete messages!",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error purging messages: {e}")
            await interaction.followup.send(
                "❌ Failed to purge messages!",
                ephemeral=True
            )
            
async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(Admin(bot)) 