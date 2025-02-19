"""Economy cog for managing strawberry-related commands."""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional, List, Union
from datetime import datetime, timedelta

from utils.core import COLORS, COMMAND_GROUPS, setup_logger

logger = setup_logger(__name__)

class Economy(commands.Cog):
    """Economy commands for managing strawberries."""
    
    def __init__(self, bot):
        self.bot = bot
        
    economy = app_commands.Group(
        name=COMMAND_GROUPS['economy']['name'],
        description=COMMAND_GROUPS['economy']['description']
    )
    
    # Traditional command
    @commands.command(name='strawberries', aliases=['bal', 'balance'])
    async def strawberries_command(self, ctx, user: Optional[discord.User] = None) -> None:
        """Check strawberry balance and stats."""
        await self._show_strawberries(ctx, user)
        
    # Slash command version
    @economy.command(name='strawberries')
    async def strawberries_slash(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None
    ) -> None:
        """Check strawberry balance and stats."""
        await self._show_strawberries(interaction, user)
        
    async def _show_strawberries(
        self,
        ctx_or_interaction: Union[commands.Context, discord.Interaction],
        user: Optional[discord.User] = None
    ) -> None:
        """Shared logic for showing strawberry balance."""
        target = user or (ctx_or_interaction.user if isinstance(ctx_or_interaction, discord.Interaction) 
                         else ctx_or_interaction.author)
        
        try:
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
                
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(embed=embed)
            else:
                await ctx_or_interaction.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error checking strawberries: {e}")
            error_msg = "❌ Failed to retrieve strawberry data!"
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(error_msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(error_msg)
                
    # Traditional command
    @commands.command(name='daily')
    @commands.cooldown(1, 86400, commands.BucketType.user)  # Once per day
    async def daily_command(self, ctx) -> None:
        """Claim daily strawberry reward."""
        await self._claim_daily(ctx)
        
    # Slash command version
    @economy.command(name='daily')
    @app_commands.checks.cooldown(1, 86400)  # Once per day
    async def daily_slash(self, interaction: discord.Interaction) -> None:
        """Claim daily strawberry reward."""
        await self._claim_daily(interaction)
        
    async def _claim_daily(
        self,
        ctx_or_interaction: Union[commands.Context, discord.Interaction]
    ) -> None:
        """Shared logic for claiming daily reward."""
        try:
            user_id = (ctx_or_interaction.user.id if isinstance(ctx_or_interaction, discord.Interaction)
                      else ctx_or_interaction.author.id)
            
            # Get reward amount with streak bonus
            reward = await self.bot.game.claim_daily(user_id)
            
            if reward > 0:
                data = self.bot.game.get_player_data(user_id)
                streak = data['streak']
                
                embed = discord.Embed(
                    title="Daily Strawberries Claimed! 🍓",
                    description=f"You received 🍓 **{reward:,}** strawberries!",
                    color=COLORS['success']
                )
                
                # Add streak info
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
                    
                # Add next claim time
                next_claim = datetime.now() + timedelta(days=1)
                embed.set_footer(text=f"Next claim: {next_claim.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                if isinstance(ctx_or_interaction, discord.Interaction):
                    await ctx_or_interaction.response.send_message(embed=embed)
                else:
                    await ctx_or_interaction.send(embed=embed)
            else:
                error_msg = "❌ You've already claimed your daily reward!"
                if isinstance(ctx_or_interaction, discord.Interaction):
                    await ctx_or_interaction.response.send_message(error_msg, ephemeral=True)
                else:
                    await ctx_or_interaction.send(error_msg)
                    
        except Exception as e:
            logger.error(f"Error claiming daily reward: {e}")
            error_msg = "❌ Failed to claim daily reward!"
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(error_msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(error_msg)
            
    @economy.command(name='transfer')
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
        if amount <= 0:
            await interaction.response.send_message(
                "❌ Amount must be positive!",
                ephemeral=True
            )
            return
            
        if user.bot:
            await interaction.response.send_message(
                "❌ You can't transfer strawberries to bots!",
                ephemeral=True
            )
            return
            
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ You can't transfer strawberries to yourself!",
                ephemeral=True
            )
            return
            
        try:
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
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    "❌ Insufficient strawberries for transfer!",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error transferring strawberries: {e}")
            await interaction.response.send_message(
                "❌ Failed to transfer strawberries!",
                ephemeral=True
            )
            
    @economy.command(name='leaderboard')
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