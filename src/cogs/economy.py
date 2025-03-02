"""Economy cog for managing strawberry-related commands."""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional, List, Union
from datetime import datetime, timedelta

from src.utils.core import COLORS, setup_logger

logger = setup_logger(__name__)

class Economy(commands.Cog):
    """Economy commands for managing strawberries."""
    
    def __init__(self, bot):
        self.bot = bot
        
    async def cog_load(self) -> None:
        """Called when the cog is loaded."""
        pass
        
    @app_commands.command(name='strawberries', description='Check strawberry balance and stats')
    @app_commands.describe(user="The user to check (optional)")
    async def strawberries(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None
    ) -> None:
        """Check strawberry balance and stats."""
        try:
            await interaction.response.send_message("Fetching strawberry data...", ephemeral=True)
            
            target = user or interaction.user
            data = self.bot.game.get_player_data(target.id)
            rank = await self.bot.game.get_rank(target.id)
            
            embed = discord.Embed(
                title=f"🍓 {target.display_name}'s Strawberries",
                color=COLORS['economy']
            )
            
            # Add stats
            embed.add_field(
                name="Balance",
                value=f"🍓 {data['strawberries']:,}",
                inline=True
            )
            embed.add_field(
                name="Rank",
                value=f"#{rank:,}",
                inline=True
            )
            embed.add_field(
                name="Streak",
                value=f"🔥 {data['streak']} days",
                inline=True
            )
            
            # Add streak bonus info
            if data['streak'] > 0:
                bonus = min(data['streak'] * 0.1, 1.0)  # Cap at 100%
                embed.add_field(
                    name="Streak Bonus",
                    value=f"+{bonus:.0%}",
                    inline=True
                )
                
            await interaction.edit_original_response(embed=embed)
                
        except Exception as e:
            logger.error(f"Balance check error for {interaction.user.id}: {e}")
            error_msg = "❌ Failed to retrieve strawberry data!"
            try:
                await interaction.edit_original_response(content=error_msg)
            except:
                await interaction.followup.send(error_msg, ephemeral=True)
                
    @app_commands.command(name='daily', description='Claim your daily strawberry reward')
    @app_commands.checks.cooldown(1, 86400)  # Once per day
    async def daily(self, interaction: discord.Interaction) -> None:
        """Claim daily strawberry reward."""
        try:
            # Check if user can claim
            can_claim, time_until_next = self.bot.game.can_claim_daily(interaction.user.id)
            if not can_claim:
                hours, remainder = divmod(time_until_next.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                await interaction.response.send_message(
                    f"❌ You can claim again in {int(hours)}h {int(minutes)}m",
                    ephemeral=True
                )
                return
            
            await interaction.response.send_message("Claiming daily reward...", ephemeral=True)
            reward = await self.bot.game.claim_daily(interaction.user.id)
            
            if reward > 0:
                data = self.bot.game.get_player_data(interaction.user.id)
                streak = data['streak']
                
                embed = discord.Embed(
                    title="Daily Strawberries Claimed! 🍓",
                    description=f"You received 🍓 **{reward:,}** strawberries!",
                    color=COLORS['success']
                )
                
                if streak > 1:
                    embed.add_field(
                        name="Streak",
                        value=f"🔥 {streak} days",
                        inline=True
                    )
                    
                    bonus = min(streak * 0.1, 1.0)
                    embed.add_field(
                        name="Bonus",
                        value=f"+{bonus:.0%}",
                        inline=True
                    )
                    
                await interaction.edit_original_response(embed=embed)
                    
        except Exception as e:
            logger.error(f"Daily claim error for {interaction.user.id}: {e}")
            error_msg = "❌ Failed to claim daily reward!"
            try:
                await interaction.edit_original_response(content=error_msg)
            except:
                await interaction.followup.send(error_msg, ephemeral=True)
                
    @app_commands.command(name='transfer', description='Transfer strawberries to another user')
    @app_commands.describe(
        user="The user to transfer strawberries to",
        amount="Amount of strawberries to transfer"
    )
    async def transfer(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        amount: int
    ) -> None:
        """Transfer strawberries to another user."""
        logger.info(f"Transfer command invoked by {interaction.user.id}")
        try:
            # Send immediate acknowledgment
            await interaction.response.send_message("Processing transfer...", ephemeral=True)
            
            if amount <= 0:
                await interaction.edit_original_response(
                    content="❌ Amount must be positive!"
                )
                return
                
            if user.bot:
                await interaction.edit_original_response(
                    content="❌ You can't transfer strawberries to bots!"
                )
                return
                
            if user.id == interaction.user.id:
                await interaction.edit_original_response(
                    content="❌ You can't transfer strawberries to yourself!"
                )
                return
                
            # Attempt transfer
            success = await self.bot.game.transfer_strawberries(
                interaction.user.id,
                user.id,
                amount
            )
            
            if success:
                embed = discord.Embed(
                    title="Transfer Successful! 🍓",
                    description=(
                        f"Transferred 🍓 **{amount:,}** strawberries to "
                        f"{user.mention}!"
                    ),
                    color=COLORS['success']
                )
                
                # Add new balances
                sender_data = self.bot.game.get_player_data(interaction.user.id)
                receiver_data = self.bot.game.get_player_data(user.id)
                
                embed.add_field(
                    name="Your New Balance",
                    value=f"🍓 {sender_data['strawberries']:,}",
                    inline=True
                )
                embed.add_field(
                    name=f"{user.display_name}'s New Balance",
                    value=f"🍓 {receiver_data['strawberries']:,}",
                    inline=True
                )
                
                await interaction.edit_original_response(embed=embed)
                logger.info(f"Successfully transferred {amount} strawberries from {interaction.user.id} to {user.id}")
            else:
                await interaction.edit_original_response(
                    content="❌ Insufficient strawberries for transfer!"
                )
                logger.warning(f"Failed transfer attempt from {interaction.user.id} - insufficient funds")
                
        except Exception as e:
            logger.error(f"Error transferring strawberries: {e}", exc_info=True)
            error_msg = "❌ Failed to transfer strawberries!"
            try:
                await interaction.edit_original_response(content=error_msg)
            except:
                await interaction.followup.send(error_msg, ephemeral=True)
            
    @app_commands.command(name='leaderboard', description='View the strawberry leaderboard')
    @app_commands.describe(page="Page number to view (default: 1)")
    async def leaderboard(
        self,
        interaction: discord.Interaction,
        page: Optional[int] = 1
    ) -> None:
        """View the strawberry leaderboard."""
        if page < 1:
            await interaction.response.send_message(
                "❌ Page number must be positive!",
                ephemeral=True
            )
            return
            
        try:
            # Get leaderboard data
            leaderboard = await self.bot.game.get_leaderboard()
            
            # Calculate pagination
            items_per_page = 10
            total_pages = (len(leaderboard) + items_per_page - 1) // items_per_page
            page = min(page, total_pages)
            
            start_idx = (page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(leaderboard))
            
            # Create embed
            embed = discord.Embed(
                title="🍓 Strawberry Leaderboard",
                color=COLORS['economy']
            )
            
            # Add leaderboard entries
            description = []
            for i, (user_id, strawberries) in enumerate(
                leaderboard[start_idx:end_idx],
                start=start_idx + 1
            ):
                user = self.bot.get_user(user_id)
                name = user.display_name if user else f"User {user_id}"
                
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = "👑"
                    
                description.append(
                    f"{medal} **#{i}** {name}: 🍓 {strawberries:,}"
                )
                
            embed.description = "\n".join(description)
            
            # Add pagination info
            embed.set_footer(
                text=f"Page {page}/{total_pages} • "
                f"Total Players: {len(leaderboard):,}"
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error displaying leaderboard: {e}")
            await interaction.response.send_message(
                "❌ Failed to retrieve leaderboard!",
                ephemeral=True
            )
            
async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(Economy(bot)) 