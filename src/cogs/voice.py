"""Voice cog for voice channel related commands."""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Dict
import asyncio

from src.utils.core import COLORS, setup_logger

logger = setup_logger(__name__)

class Voice(commands.Cog):
    """Voice channel related commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.following: Dict[int, int] = {}  # user_id: target_id
        
    @app_commands.command(name='join', description='Join your voice channel')
    async def join(self, interaction: discord.Interaction) -> None:
        """Join your voice channel."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in servers!",
                ephemeral=True
            )
            return
            
        # Check if user is in a voice channel
        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ You need to be in a voice channel first!",
                ephemeral=True
            )
            return
            
        try:
            channel = interaction.user.voice.channel
            
            # Check if bot has permission to join
            if not channel.permissions_for(interaction.guild.me).connect:
                await interaction.response.send_message(
                    "❌ I don't have permission to join that channel!",
                    ephemeral=True
                )
                return
                
            # Join channel
            await channel.connect()
            
            embed = discord.Embed(
                title="🎵 Joined Voice Channel",
                description=f"Connected to {channel.mention}",
                color=COLORS['success']
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Joined voice channel {channel.id} in guild {interaction.guild.id}")
            
        except discord.ClientException:
            # Already in a voice channel
            await interaction.response.send_message(
                "❌ I'm already in a voice channel!",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error joining voice channel: {e}")
            await interaction.response.send_message(
                "❌ Failed to join voice channel!",
                ephemeral=True
            )
            
    @app_commands.command(name='leave', description='Leave the current voice channel')
    async def leave(self, interaction: discord.Interaction) -> None:
        """Leave the voice channel."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in servers!",
                ephemeral=True
            )
            return
            
        try:
            voice = interaction.guild.voice_client
            if voice:
                channel = voice.channel
                await voice.disconnect()
                
                embed = discord.Embed(
                    title="👋 Left Voice Channel",
                    description=f"Disconnected from {channel.mention}",
                    color=COLORS['success']
                )
                
                await interaction.response.send_message(embed=embed)
                logger.info(f"Left voice channel {channel.id} in guild {interaction.guild.id}")
            else:
                await interaction.response.send_message(
                    "❌ I'm not in a voice channel!",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error leaving voice channel: {e}")
            await interaction.response.send_message(
                "❌ Failed to leave voice channel!",
                ephemeral=True
            )
            
    @app_commands.command(name='follow', description='Follow a user between voice channels')
    @app_commands.describe(
        user="The user to follow between voice channels"
    )
    async def follow(
        self,
        interaction: discord.Interaction,
        user: discord.User
    ) -> None:
        """Follow a user between voice channels."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in servers!",
                ephemeral=True
            )
            return
            
        if user.bot:
            await interaction.response.send_message(
                "❌ You can't follow bots!",
                ephemeral=True
            )
            return
            
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ You can't follow yourself!",
                ephemeral=True
            )
            return
            
        member = interaction.guild.get_member(user.id)
        if not member:
            await interaction.response.send_message(
                "❌ That user is not in this server!",
                ephemeral=True
            )
            return
            
        try:
            # Start following
            self.following[interaction.user.id] = user.id
            
            embed = discord.Embed(
                title="👣 Following User",
                description=f"Now following {user.mention}",
                color=COLORS['success']
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"User {interaction.user.id} started following {user.id}")
            
            # Start following loop
            while interaction.user.id in self.following:
                if not member.voice:
                    # Target not in voice
                    continue
                    
                user_member = interaction.guild.get_member(interaction.user.id)
                if not user_member or not user_member.voice:
                    # Follower not in voice
                    continue
                    
                if (
                    user_member.voice.channel and
                    member.voice.channel and
                    user_member.voice.channel != member.voice.channel
                ):
                    # Move to target's channel
                    try:
                        await user_member.move_to(member.voice.channel)
                        logger.info(
                            f"Moved {interaction.user.id} to channel {member.voice.channel.id}"
                        )
                    except discord.Forbidden:
                        # No permission to move
                        del self.following[interaction.user.id]
                        await interaction.followup.send(
                            "❌ I don't have permission to move you between channels!",
                            ephemeral=True
                        )
                        break
                        
                await asyncio.sleep(1)  # Check every second
                
        except Exception as e:
            logger.error(f"Error following user: {e}")
            await interaction.followup.send(
                "❌ Failed to follow user!",
                ephemeral=True
            )
            if interaction.user.id in self.following:
                del self.following[interaction.user.id]
                
    @app_commands.command(name='unfollow', description='Stop following users')
    async def unfollow(self, interaction: discord.Interaction) -> None:
        """Stop following users."""
        if interaction.user.id in self.following:
            target_id = self.following[interaction.user.id]
            del self.following[interaction.user.id]
            
            user = self.bot.get_user(target_id)
            name = user.mention if user else f"User {target_id}"
            
            embed = discord.Embed(
                title="🛑 Stopped Following",
                description=f"No longer following {name}",
                color=COLORS['success']
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"User {interaction.user.id} stopped following {target_id}")
        else:
            await interaction.response.send_message(
                "❌ You're not following anyone!",
                ephemeral=True
            )
            
async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(Voice(bot)) 