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
            # Define roulette wheel
            wheel = {
                0: 'green',
                32: 'red', 19: 'red', 21: 'red', 25: 'red', 34: 'red',
                27: 'red', 36: 'red', 30: 'red', 23: 'red', 5: 'red',
                16: 'red', 1: 'red', 14: 'red', 9: 'red', 18: 'red',
                7: 'red', 12: 'red', 3: 'red',
                26: 'black', 35: 'black', 28: 'black', 22: 'black',
                29: 'black', 31: 'black', 20: 'black', 33: 'black',
                24: 'black', 10: 'black', 8: 'black', 11: 'black',
                13: 'black', 6: 'black', 17: 'black', 2: 'black',
                4: 'black', 15: 'black'
            }
            
            # Calculate chances
            total_numbers = 37  # 0-36
            red_numbers = len([n for n in wheel if wheel[n] == 'red'])
            black_numbers = len([n for n in wheel if wheel[n] == 'black'])
            green_numbers = len([n for n in wheel if wheel[n] == 'green'])
            
            red_chance = (red_numbers / total_numbers) * 100
            black_chance = (black_numbers / total_numbers) * 100
            green_chance = (green_numbers / total_numbers) * 100
            
            # Show betting options
            embed = discord.Embed(
                title="🎰 Strawberry Roulette",
                description=(
                    f"**{interaction.user.display_name}** is betting 🍓 **{bet:,}** strawberries\n"
                    "Choose your bet:"
                ),
                color=COLORS['economy']
            )
            
            embed.add_field(
                name="Color Bets",
                value=(
                    f"🔴 Red (2x payout, {red_chance:.0f}%)\n"
                    f"⚫ Black (2x payout, {black_chance:.0f}%)\n"
                    f"🟢 Green (35x payout, {green_chance:.0f}%)"
                ),
                inline=False
            )
            
            # Add potential winnings
            embed.add_field(
                name="Potential Winnings",
                value=(
                    f"🔴 Red: 🍓 **{bet * 2:,}**\n"
                    f"⚫ Black: 🍓 **{bet * 2:,}**\n"
                    f"🟢 Green: 🍓 **{bet * 35:,}**"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            selection_msg = await interaction.original_response()
            
            # Add reaction options
            try:
                for emoji in ["🔴", "⚫", "🟢"]:
                    await selection_msg.add_reaction(emoji)
            except Exception as e:
                logger.error(f"Error adding reactions: {e}")
                await interaction.followup.send("❌ Error setting up the game!", ephemeral=True)
                del self.roulette_games[interaction.user.id]
                return
                
            def reaction_check(reaction, user):
                return (
                    user == interaction.user and
                    str(reaction.emoji) in ["🔴", "⚫", "🟢"] and
                    reaction.message.id == selection_msg.id
                )
                
            try:
                # Wait for reaction
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=reaction_check)
                emoji = str(reaction.emoji)
                bet_choice = {
                    "🔴": "red",
                    "⚫": "black",
                    "🟢": "green"
                }[emoji]
                
                # Clean up selection message
                try:
                    await selection_msg.delete()
                except:
                    pass
                    
            except asyncio.TimeoutError:
                try:
                    await selection_msg.clear_reactions()
                    await selection_msg.edit(content="❌ Bet cancelled - no choice made in time!", embed=None)
                except:
                    await interaction.followup.send("❌ Bet cancelled - no choice made in time!")
                del self.roulette_games[interaction.user.id]
                return
                
            # Spinning animation
            embed = discord.Embed(
                title="🎰 Strawberry Roulette",
                description=(
                    f"**{interaction.user.display_name}** bets 🍓 **{bet:,}** on **{bet_choice}**\n"
                    "Spinning the wheel..."
                ),
                color=COLORS['economy']
            )
            
            spin_msg = await interaction.channel.send(embed=embed)
            
            # Enhanced spinning animation
            for i in range(3):
                await asyncio.sleep(0.7)
                temp_number = random.randint(0, 36)
                temp_color = wheel[temp_number]
                embed.description = (
                    f"**{interaction.user.display_name}** bets 🍓 **{bet:,}** on **{bet_choice}**\n"
                    f"Spinning... {temp_number} ({temp_color})"
                )
                await spin_msg.edit(embed=embed)
                
            # Get result
            result_number = random.randint(0, 36)
            result_color = wheel[result_number]
            
            # Calculate winnings
            won = False
            if bet_choice == result_color:
                winnings = bet * (35 if result_color == 'green' else 2)
                won = True
            else:
                winnings = 0
                    
            # Update user's balance
            if won:
                await self.bot.game.add_strawberries(interaction.user.id, winnings)
            else:
                await self.bot.game.remove_strawberries(interaction.user.id, bet)
                
            # Get new balance
            new_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
            
            # Create result embed
            embed = discord.Embed(
                title="🎰 Roulette Results",
                description=(
                    f"The ball landed on **{result_number}** ({result_color})\n"
                    f"**{interaction.user.display_name}**'s bet: {bet_choice}"
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
                value=f"🍓 **{new_balance:,}**",
                inline=True
            )
            
            # Add stats
            embed.add_field(
                name="Odds",
                value=(
                    f"Chance to win: **{green_chance if bet_choice == 'green' else red_chance:.0f}%**\n"
                    f"Potential win: 🍓 **{bet * (35 if bet_choice == 'green' else 2):,}**"
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
            
        finally:
            # Clean up game state
            if interaction.user.id in self.roulette_games:
                del self.roulette_games[interaction.user.id]
                
async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(Games(bot)) 