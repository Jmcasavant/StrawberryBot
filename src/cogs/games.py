"""Games cog for fun strawberry-based games."""
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

from utils.core import COLORS, setup_logger

logger = setup_logger(__name__)

class Games(commands.Cog):
    """Games and fun commands."""
    
    # Roulette wheel configuration
    WHEEL = {
        0: 'green',  # Two green slots for 2% chance
        1: 'green',
        **{i: 'red' for i in range(2, 51)},      # 49 red slots for 49% chance
        **{i: 'black' for i in range(51, 100)}   # 49 black slots for 49% chance
    }
    
    # Color emoji mapping
    COLOR_EMOJIS = {
        'red': '🔴',
        'black': '⚫',
        'green': '🟢'
    }
    
    def __init__(self, bot):
        self.bot = bot
        self.roulette_games = {}
        
    @app_commands.command(name='roulette', description='Play strawberry roulette')
    @app_commands.describe(
        bet="Amount of strawberries to bet"
    )
    async def roulette(
        self,
        interaction: discord.Interaction,
        bet: int
    ) -> None:
        """Play strawberry roulette with an interactive menu."""
        # Validate bet
        if bet <= 0:
            await interaction.response.send_message("❌ Bet amount must be positive!", ephemeral=True)
            return
            
        # Check if user has enough strawberries
        data = self.bot.game.get_player_data(interaction.user.id)
        if data['strawberries'] < bet:
            await interaction.response.send_message(
                f"❌ You only have 🍓 {data['strawberries']:,} strawberries!",
                ephemeral=True
            )
            return
            
        # Prevent multiple games
        if interaction.user.id in self.roulette_games:
            await interaction.response.send_message(
                "❌ You already have a roulette game in progress!",
                ephemeral=True
            )
            return
            
        self.roulette_games[interaction.user.id] = True
        
        try:
            # Calculate chances
            total_numbers = 100  # 98 red/black + 2 green
            red_numbers = len([n for n in self.WHEEL if self.WHEEL[n] == 'red'])
            black_numbers = len([n for n in self.WHEEL if self.WHEEL[n] == 'black'])
            green_numbers = len([n for n in self.WHEEL if self.WHEEL[n] == 'green'])
            
            red_chance = (red_numbers / total_numbers) * 100
            black_chance = (black_numbers / total_numbers) * 100
            green_chance = (green_numbers / total_numbers) * 100
            number_chance = (1 / total_numbers) * 100
            
            # Show betting options
            embed = discord.Embed(
                title="🎰 Strawberry Roulette",
                description=(
                    f"**{interaction.user.display_name}** is betting 🍓 **{bet:,}** strawberries\n"
                    "Choose what to bet on:"
                ),
                color=COLORS['economy']
            )
            
            embed.add_field(
                name="Color Bets",
                value=(
                    f"🔴 Red (2x, {red_chance:.1f}% chance)\n"
                    f"⚫ Black (2x, {black_chance:.1f}% chance)\n"
                    f"🟢 Green (50x, {green_chance:.1f}% chance)"
                ),
                inline=False
            )
            
            # Add potential winnings
            embed.add_field(
                name="Potential Winnings",
                value=(
                    f"🔴 Red: 🍓 **{bet * 2:,}**\n"
                    f"⚫ Black: 🍓 **{bet * 2:,}**\n"
                    f"🟢 Green: 🍓 **{bet * 50:,}**"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            selection_msg = await interaction.original_response()
            
            # Add reaction options
            try:
                for emoji in self.COLOR_EMOJIS.values():
                    await selection_msg.add_reaction(emoji)
            except discord.HTTPException as e:
                logger.error(f"Failed to add reactions: {e}")
                await interaction.followup.send("❌ Error setting up the game!", ephemeral=True)
                del self.roulette_games[interaction.user.id]
                return
                
            def reaction_check(reaction, user):
                return (
                    user == interaction.user and
                    str(reaction.emoji) in self.COLOR_EMOJIS.values() and
                    reaction.message.id == selection_msg.id
                )
                
            try:
                # Wait for reaction with proper timeout handling
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=reaction_check)
                emoji = str(reaction.emoji)
                bet_choice = {
                    emoji: color for color, emoji in self.COLOR_EMOJIS.items()
                }[emoji]
                bet_emoji = self.COLOR_EMOJIS[bet_choice]
                
                # Clean up selection message
                try:
                    await selection_msg.delete()
                except discord.NotFound:
                    pass  # Message already deleted
                except discord.HTTPException as e:
                    logger.warning(f"Failed to delete selection message: {e}")
                    
            except asyncio.TimeoutError:
                try:
                    await selection_msg.clear_reactions()
                    await selection_msg.edit(
                        content="❌ Bet cancelled - no choice made in time!",
                        embed=None
                    )
                except discord.NotFound:
                    pass  # Message already deleted
                except discord.HTTPException as e:
                    logger.warning(f"Failed to clean up timed out message: {e}")
                    await interaction.followup.send(
                        "❌ Bet cancelled - no choice made in time!",
                        ephemeral=True
                    )
                finally:
                    del self.roulette_games[interaction.user.id]
                    return
                
            # Spinning animation
            embed = discord.Embed(
                title="🎰 Strawberry Roulette",
                description=(
                    f"**{interaction.user.display_name}** bets 🍓 **{bet:,}** on **{bet_emoji}**\n"
                    "Spinning the wheel..."
                ),
                color=COLORS['economy']
            )
            
            try:
                spin_msg = await interaction.channel.send(embed=embed)
                
                # Enhanced spinning animation with random numbers and colors
                for _ in range(3):
                    await asyncio.sleep(0.7)
                    temp_number = random.randint(0, 99)
                    temp_color = self.WHEEL[temp_number]
                    temp_emoji = self.COLOR_EMOJIS[temp_color]
                    embed.description = (
                        f"**{interaction.user.display_name}** bets 🍓 **{bet:,}** on **{bet_emoji}**\n"
                        f"Spinning... {temp_number} ({temp_emoji})"
                    )
                    await spin_msg.edit(embed=embed)
                    
                # Get result with proper error handling
                result_number = random.randint(0, 99)
                result_color = self.WHEEL[result_number]
                result_emoji = self.COLOR_EMOJIS[result_color]
                
                # Calculate winnings
                won = bet_choice == result_color
                winnings = bet * (50 if result_color == 'green' else 2) if won else 0
                
                # Update user's balance with error handling
                try:
                    if won:
                        await self.bot.game.add_strawberries(interaction.user.id, winnings)
                    else:
                        await self.bot.game.remove_strawberries(interaction.user.id, bet)
                except Exception as e:
                    logger.error(f"Failed to update balance for user {interaction.user.id}: {e}")
                    await interaction.followup.send(
                        "❌ Error updating your balance. Please contact an administrator.",
                        ephemeral=True
                    )
                    return
                    
                # Get new balance
                try:
                    new_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
                except Exception as e:
                    logger.error(f"Failed to get new balance for user {interaction.user.id}: {e}")
                    new_balance = "Unknown"
                
                # Create result embed
                embed = discord.Embed(
                    title="🎰 Roulette Results",
                    description=(
                        f"The ball landed on **{result_number}** ({result_emoji})\n"
                        f"**{interaction.user.display_name}**'s bet: {bet_emoji}"
                    ),
                    color=COLORS['success'] if won else COLORS['error']
                )
                
                if won:
                    embed.add_field(
                        name="🎉 YOU WON! 🎉",
                        value=f"+🍓 **{winnings:,}**",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="😢 You Lost",
                        value=f"-🍓 **{bet:,}**",
                        inline=True
                    )
                    
                embed.add_field(
                    name="New Balance",
                    value=f"🍓 **{new_balance:,}**" if isinstance(new_balance, int) else "❌ Error getting balance",
                    inline=True
                )
                
                # Add stats with proper percentage formatting
                win_chance = 2.0 if bet_choice == 'green' else 49.0
                potential_win = bet * (50 if bet_choice == 'green' else 2)
                embed.add_field(
                    name="Odds",
                    value=(
                        f"Chance to win: **{win_chance:.1f}%**\n"
                        f"Potential win: 🍓 **{potential_win:,}**"
                    ),
                    inline=False
                )
                
                # Add a random footer message
                footer_messages = [
                    "Better luck next time! 🍀",
                    "The house always wins... or does it? 🤔",
                    "Time to go double or nothing! 💰",
                    "That was a close one! 😅",
                    "Keep rolling! 🎲",
                    "Fortune favors the bold! ⚔️",
                    "May the odds be ever in your favor! 🎯"
                ]
                embed.set_footer(text=random.choice(footer_messages))
                
                await spin_msg.edit(embed=embed)
                
            except discord.HTTPException as e:
                logger.error(f"Discord API error during roulette game: {e}")
                await interaction.followup.send(
                    "❌ Error displaying game results. Please try again.",
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Unexpected error during roulette game: {e}")
                await interaction.followup.send(
                    "❌ An unexpected error occurred. Please try again.",
                    ephemeral=True
                )
                
        finally:
            # Clean up game state
            if interaction.user.id in self.roulette_games:
                del self.roulette_games[interaction.user.id]
                
async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(Games(bot)) 