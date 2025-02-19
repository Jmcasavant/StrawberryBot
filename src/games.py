"""Games cog for fun strawberry-based games."""
import discord
from discord import app_commands
from discord.ext import commands
import random
from typing import Optional, List, Union
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
                    f"🟢 Green (35x, {green_chance:.1f}% chance)"
                ),
                inline=False
            )
            
            embed.add_field(
                name="Number Bet",
                value=(
                    f"Type any number 0-36 (35x, {number_chance:.1f}% chance)\n"
                    "Examples: 0, 7, 23, 36"
                ),
                inline=False
            )
            
            # Add expected value information
            red_ev = (red_chance/100 * bet * 2) - bet
            black_ev = (black_chance/100 * bet * 2) - bet
            green_ev = (green_chance/100 * bet * 35) - bet
            number_ev = (number_chance/100 * bet * 35) - bet
            
            embed.add_field(
                name="Expected Value",
                value=(
                    f"🔴 Red: {red_ev:+.1f}\n"
                    f"⚫ Black: {black_ev:+.1f}\n"
                    f"🟢 Green: {green_ev:+.1f}\n"
                    f"Number: {number_ev:+.1f}"
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
                
            def message_check(m):
                if m.author != interaction.user or m.channel != interaction.channel:
                    return False
                try:
                    num = int(m.content)
                    return 0 <= num <= 36
                except ValueError:
                    return False
                    
            try:
                # Wait for either a reaction or a message
                tasks = [
                    asyncio.create_task(self.bot.wait_for('reaction_add', timeout=30.0, check=reaction_check)),
                    asyncio.create_task(self.bot.wait_for('message', timeout=30.0, check=message_check))
                ]
                
                done, pending = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Get the result and cancel pending tasks
                result = done.pop().result()
                for task in pending:
                    task.cancel()
                    
                # Clean up selection message
                try:
                    await selection_msg.delete()
                except:
                    pass
                    
                if isinstance(result, tuple):  # Reaction result
                    reaction, _ = result
                    emoji = str(reaction.emoji)
                    bet_type = 'color'
                    bet_choice = {
                        "🔴": "red",
                        "⚫": "black",
                        "🟢": "green"
                    }[emoji]
                else:  # Message result
                    bet_type = 'number'
                    bet_choice = int(result.content)
                    try:
                        await result.delete()  # Try to delete the number message
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
            
            # Simulate wheel spin with animation
            for _ in range(3):
                await asyncio.sleep(1)
                embed.description = embed.description.rstrip('.') + "."
                await spin_msg.edit(embed=embed)
                
            # Get result
            result_number = random.randint(0, 36)
            result_color = wheel[result_number]
            
            # Calculate winnings
            won = False
            if bet_type == 'color':
                if bet_choice == result_color:
                    winnings = bet * (35 if result_color == 'green' else 2)
                    won = True
                else:
                    winnings = 0
            else:  # number bet
                if bet_choice == result_number:
                    winnings = bet * 35
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