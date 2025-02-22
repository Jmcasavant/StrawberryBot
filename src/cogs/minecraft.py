"""Minecraft integration cog for server interaction."""
import discord
from discord import app_commands
from discord.ext import commands
from mctools import RCONClient
from typing import Optional, Dict
import asyncio
import socket
import json
from datetime import datetime
from pathlib import Path
import re
import random
import logging

from utils.core import COLORS, setup_logger, OWNER_ID, DATA_DIR

logger = setup_logger(__name__)

# RCON Configuration
# Update these values with your server details
RCON_CONFIG = {
    'ip': '207.244.234.30',  # Your Minecraft server IP
    'port': 26095,           # Your RCON port
    'password': 'aFKeU2QL'   # Your RCON password
}

class Minecraft(commands.GroupCog, group_name="mc"):
    """Minecraft server integration commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.is_connected = False
        self.rcon = None
        # Initialize RCON connection in cog_load instead of __init__
        logger.info("Minecraft cog initialized")
        
    async def cog_load(self) -> None:
        """Called when the cog is loaded."""
        try:
            # Add timeout to RCON connection
            async with asyncio.timeout(5.0):  # 5 second timeout
                self.rcon = RCONClient(RCON_CONFIG['ip'], RCON_CONFIG['port'])
                self.is_connected = self.rcon.login(RCON_CONFIG['password'])
                if not self.is_connected:
                    logger.warning("Failed to connect to Minecraft server - check credentials")
        except asyncio.TimeoutError:
            logger.warning("Timeout while connecting to Minecraft server")
        except ConnectionRefusedError:
            logger.warning(f"Could not connect to Minecraft server - {RCON_CONFIG['ip']}:{RCON_CONFIG['port']}")
        except Exception as e:
            logger.error(f"Minecraft server connection error: {e}")
        
        logger.info("Minecraft cog loaded")

    def is_admin_or_owner(self, interaction: discord.Interaction) -> bool:
        """Check if user is owner, MC server owner, or has admin permissions."""
        MC_SERVER_OWNER = 231261911998660609  # Minecraft server owner's ID
        return (interaction.user.id == OWNER_ID or 
                interaction.user.id == MC_SERVER_OWNER or
                (interaction.guild and interaction.user.guild_permissions.administrator))

    def clean_response(self, response: str) -> str:
        """Clean ANSI color codes and other formatting from responses."""
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', response)
        
        # Extract the actual data part after "has the following entity data:"
        if "has the following entity data:" in cleaned:
            cleaned = cleaned.split("has the following entity data:", 1)[1].strip()
            
        # Remove extra whitespace and empty lines
        cleaned = '\n'.join(line.strip() for line in cleaned.split('\n') if line.strip())
        return cleaned

    @app_commands.command(name='status', description='Check Minecraft server status (Admin only)')
    @app_commands.guild_only()
    async def status(self, interaction: discord.Interaction) -> None:
        """Check the Minecraft server status."""
        if not self.is_admin_or_owner(interaction):
            await interaction.response.send_message(
                "❌ Only administrators and the MC server owner can use this command!",
                ephemeral=True
            )
            return
            
        await interaction.response.defer(ephemeral=True)
        
        if not self.is_connected:
            await interaction.followup.send(
                "❌ Not connected to any Minecraft server!"
            )
            return
            
        try:
            # Get server status using RCON
            response = self.rcon.command("list")  # Gets online players
            
            embed = discord.Embed(
                title="🎮 Minecraft Server Status",
                color=COLORS['success']
            )
            
            # Add server info
            embed.add_field(
                name="Server Address",
                value=f"`{RCON_CONFIG['ip']}`",
                inline=True
            )
            
            # Parse and add player list
            if "There are" in response:
                embed.add_field(
                    name="Players Online",
                    value=self.clean_response(response),
                    inline=False
                )
            
            # Add timestamp
            embed.set_footer(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting server status: {e}")
            await interaction.followup.send(
                "❌ Failed to get server status!"
            )

    @app_commands.command(name='command', description='Execute a Minecraft server command (Admin only)')
    @app_commands.describe(
        command="The command to execute (without /)"
    )
    @app_commands.guild_only()
    async def execute(
        self,
        interaction: discord.Interaction,
        command: str
    ) -> None:
        """Execute a Minecraft server command."""
        if not self.is_admin_or_owner(interaction):
            await interaction.response.send_message(
                "❌ Only administrators and the MC server owner can execute server commands!",
                ephemeral=True
            )
            return
            
        if not self.is_connected:
            await interaction.response.send_message(
                "❌ Not connected to any Minecraft server!",
                ephemeral=True
            )
            return
            
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Log command execution attempt
            logger.info(f"Minecraft command requested by {interaction.user} ({interaction.user.id}): {command}")
            
            response = self.rcon.command(command)
            cleaned_response = self.clean_response(response)
            
            embed = discord.Embed(
                title="🎮 Minecraft Command Executed",
                description=f"Command: `{command}`",
                color=COLORS['success']
            )
            
            if cleaned_response:
                embed.add_field(
                    name="Response",
                    value=f"```{cleaned_response}```",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Response",
                    value="Command executed successfully (no output)",
                    inline=False
                )
                
            await interaction.followup.send(embed=embed)
            logger.info(f"Minecraft command executed successfully by {interaction.user.id}")
            
        except Exception as e:
            logger.error(f"Error executing Minecraft command: {e}")
            await interaction.followup.send(
                "❌ Failed to execute command!"
            )

    @app_commands.command(name='playerinfo', description='Get detailed information about a player')
    @app_commands.describe(
        player="The player's username"
    )
    @app_commands.guild_only()
    async def playerinfo(
        self,
        interaction: discord.Interaction,
        player: str
    ) -> None:
        """Get detailed information about a player."""
        if not self.is_admin_or_owner(interaction):
            await interaction.response.send_message(
                "❌ Only administrators and the MC server owner can use this command!",
                ephemeral=True
            )
            return
            
        if not self.is_connected:
            await interaction.response.send_message(
                "❌ Not connected to any Minecraft server!",
                ephemeral=True
            )
            return
            
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get player data using various commands
            health = self.rcon.command(f"data get entity {player} Health")
            position = self.rcon.command(f"data get entity {player} Pos")
            gamemode = self.rcon.command(f"data get entity {player} playerGameType")
            xp = self.rcon.command(f"data get entity {player} XpLevel")
            
            embed = discord.Embed(
                title=f"📊 Player Info: {player}",
                color=COLORS['info']
            )
            
            # Parse and add data to embed
            if "no entity was found" not in health.lower():
                # Format health (remove 'f' suffix and round to 1 decimal)
                health_value = self.clean_response(health).split(':', 1)[-1].strip()
                try:
                    health_num = float(health_value.rstrip('f'))
                    health_str = f"{health_num:.1f} ❤️"
                except ValueError:
                    health_str = health_value

                # Format position (extract coordinates and round)
                pos_value = self.clean_response(position).split(':', 1)[-1].strip()
                try:
                    # Extract numbers from the position string
                    coords = re.findall(r'-?\d+\.?\d*', pos_value)
                    if len(coords) >= 3:
                        x, y, z = map(float, coords[:3])
                        pos_str = f"X: {x:.1f}, Y: {y:.1f}, Z: {z:.1f}"
                    else:
                        pos_str = pos_value
                except:
                    pos_str = pos_value

                # Format game mode (convert number to name)
                gamemode_value = self.clean_response(gamemode).split(':', 1)[-1].strip()
                try:
                    mode_num = int(gamemode_value)
                    mode_names = {
                        0: "Survival",
                        1: "Creative",
                        2: "Adventure",
                        3: "Spectator"
                    }
                    mode_str = mode_names.get(mode_num, f"Unknown ({mode_num})")
                except ValueError:
                    mode_str = gamemode_value

                # Format XP level (remove any suffixes)
                xp_value = self.clean_response(xp).split(':', 1)[-1].strip()
                try:
                    xp_num = int(float(xp_value.rstrip('f')))
                    xp_str = f"Level {xp_num} ✨"
                except ValueError:
                    xp_str = xp_value

                embed.add_field(
                    name="Health",
                    value=health_str,
                    inline=True
                )
                embed.add_field(
                    name="Position",
                    value=pos_str,
                    inline=True
                )
                embed.add_field(
                    name="Game Mode",
                    value=mode_str,
                    inline=True
                )
                embed.add_field(
                    name="XP Level",
                    value=xp_str,
                    inline=True
                )
            else:
                embed.description = f"❌ Player {player} not found or not online"
                
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Player info error for {player}: {e}")
            await interaction.followup.send(
                "❌ Failed to get player information!",
                ephemeral=True
            )

    def format_item_name(self, item_id: str) -> str:
        """Format item name for display, handling mod namespaces."""
        # Split namespace and item name
        parts = item_id.split(':')
        if len(parts) == 2:
            namespace, name = parts
            # Format the name
            name = name.replace('_', ' ').title()
            
            # Special formatting for mod namespaces
            if namespace != 'minecraft':
                # Handle special cases for better readability
                if namespace == 'everycomp':
                    # Extract the actual mod name from everycomp items
                    if 'ch/' in name.lower():
                        parts = name.split('/')
                        if len(parts) >= 3:
                            mod_name = parts[1].replace('_', ' ').upper()
                            item_name = parts[-1].title()
                            return f"**{mod_name}**: {item_name}"
                
                # Format namespace in a consistent way
                namespace = namespace.replace('_', ' ').upper()
                return f"**{namespace}**: {name}"
            return name
        return item_id.replace('_', ' ').title()

    def format_enchantments(self, enchants: list) -> str:
        """Format enchantment list for display."""
        if not enchants:
            return ""
        formatted = []
        for ench in enchants:
            name = ench.get('id', '').split(':')[-1].replace('_', ' ').title()
            level = ench.get('lvl', 1)
            if isinstance(level, str) and level.endswith('s'):
                level = level[:-1]  # Remove 's' suffix
            formatted.append(f"{name} {level}")
        return f" ({', '.join(formatted)})" if formatted else ""

    def parse_backpack_contents(self, items_data: str) -> list:
        """Parse backpack contents into a structured format."""
        items = []
        try:
            # Extract items from the backpack data
            matches = re.finditer(r'{Slot:\s*(\d+)b,\s*(?:Count:\s*(\d+)b,\s*)?(?:tag:\s*({[^}]+}),\s*)?id:\s*"([^"]+)"', items_data)
            for match in matches:
                slot = int(match.group(1))
                count = int(match.group(2) if match.group(2) else 1)
                tag = match.group(3)
                item_id = match.group(4)
                
                # Format the item name
                name = self.format_item_name(item_id)
                
                # Add enchantments if present
                if tag and 'Enchantments' in tag:
                    enchants_match = re.findall(r'Enchantments:\[(.*?)\]', tag)
                    if enchants_match:
                        enchants = eval(f"[{enchants_match[0]}]")
                        name += self.format_enchantments(enchants)
                
                items.append((slot, count, name))
            
            return sorted(items, key=lambda x: x[0])  # Sort by slot number
        except Exception as e:
            logger.error(f"Error parsing backpack contents: {e}")
            return []

    def split_field_content(self, items: list, prefix: str = "") -> list:
        """Split a list of items into chunks that fit within Discord's field value limit."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for item in items:
            # Calculate length with newline
            item_length = len(item) + 1
            
            # If adding this item would exceed limit, start new chunk
            if current_length + item_length > 1000:  # Leave some buffer
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0
                
            current_chunk.append(item)
            current_length += item_length
            
        # Add remaining items
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        # Add prefix to first chunk if provided
        if chunks and prefix:
            chunks[0] = prefix + chunks[0]
            
        return chunks

    def format_backpack_contents(self, items_data: str, max_items: int = 10) -> str:
        """Format backpack contents with a reasonable limit."""
        try:
            bp_items = items_data.split('}, {')
            if not bp_items:
                return ""
                
            contents = ["  📦 Backpack Contents:"]
            shown_items = 0
            
            # Group items by mod
            grouped_items = {}
            
            for bp_item in bp_items:
                if shown_items >= max_items:
                    remaining = len(bp_items) - shown_items
                    if remaining > 0:
                        contents.append(f"    • ...and {remaining} more items")
                    break
                    
                bp_id_match = re.search(r'id:"([^"]+)"', bp_item)
                bp_count_match = re.search(r'Count:(\d+)b', bp_item)
                
                if bp_id_match:
                    item_id = bp_id_match.group(1)
                    bp_count = int(bp_count_match.group(1)) if bp_count_match else 1
                    
                    # Get formatted name and determine mod
                    parts = item_id.split(':')
                    if len(parts) == 2:
                        mod_name = parts[0].upper() if parts[0] != 'minecraft' else 'VANILLA'
                    else:
                        mod_name = 'VANILLA'
                        
                    # Format the item name
                    bp_name = self.format_item_name(item_id)
                    
                    # Add to grouped items
                    if mod_name not in grouped_items:
                        grouped_items[mod_name] = []
                    grouped_items[mod_name].append(f"    • {bp_count}x {bp_name}")
                    shown_items += 1
            
            # Add grouped items to contents
            for mod_name, items in sorted(grouped_items.items()):
                if mod_name != 'VANILLA':
                    contents.extend(items)
            
            # Add vanilla items last
            if 'VANILLA' in grouped_items:
                contents.extend(grouped_items['VANILLA'])
                    
            return "\n".join(contents)
        except Exception as e:
            logger.error(f"Error formatting backpack contents: {e}")
            return "  📦 Error reading contents"

    @app_commands.command(name='inventory', description='View a player\'s inventory')
    @app_commands.describe(
        player="The player's username"
    )
    @app_commands.guild_only()
    async def inventory(
        self,
        interaction: discord.Interaction,
        player: str
    ) -> None:
        """View a player's inventory contents."""
        if not self.is_admin_or_owner(interaction):
            await interaction.response.send_message(
                "❌ Only administrators and the MC server owner can view inventories!",
                ephemeral=True
            )
            return
            
        if not self.is_connected:
            await interaction.response.send_message(
                "❌ Not connected to any Minecraft server!",
                ephemeral=True
            )
            return
            
        await interaction.response.defer(ephemeral=True)
        
        try:
            # First check if player is online
            list_response = self.rcon.command("list")
            if player not in self.clean_response(list_response):
                await interaction.followup.send(
                    f"❌ Player {player} is not online!"
                )
                return

            # Get inventory data
            inventory = self.rcon.command(f"data get entity {player} Inventory")
            logger.info(f"Raw inventory data: {inventory}")
            
            if "no entity was found" in inventory.lower():
                await interaction.followup.send(
                    f"❌ Player {player} not found!"
                )
                return
                
            # Parse inventory data
            cleaned_inv = self.clean_response(inventory)
            logger.info(f"Cleaned inventory data: {cleaned_inv}")
            
            # Create embed
            embed = discord.Embed(
                title=f"🎒 {player}'s Inventory",
                color=COLORS['info']
            )
            
            # Group items by section
            sections = {
                'hotbar': [],      # 0-8
                'main': [],        # 9-35
                'armor': [],       # 100-103
                'offhand': [],     # -106
                'accessories': []  # 90+
            }
            
            # Split items and process each one
            items = cleaned_inv.strip('[]').split('}, {')
            for item_str in items:
                # Clean up the item string
                item_str = item_str.strip('{}')
                
                # Extract slot
                slot_match = re.search(r'Slot:\s*(-?\d+)b', item_str)
                if not slot_match:
                    continue
                slot = int(slot_match.group(1))
                
                # Extract item ID
                id_match = re.search(r'id:\s*"([^"]+)"', item_str)
                if not id_match:
                    continue
                item_id = id_match.group(1)
                
                # Extract count
                count_match = re.search(r'Count:\s*(\d+)b', item_str)
                count = int(count_match.group(1)) if count_match else 1
                
                # Format item name
                item_name = self.format_item_name(item_id)
                item_text = f"{count}x {item_name}"
                
                # Add enchantments if present
                enchants_match = re.search(r'Enchantments:\[(.*?)\]', item_str)
                if enchants_match:
                    enchants_str = enchants_match.group(1)
                    enchants = []
                    for ench in re.finditer(r'{id:"([^"]+)",lvl:(\d+)s?}', enchants_str):
                        enchants.append({
                            'id': ench.group(1),
                            'lvl': ench.group(2)
                        })
                    if enchants:
                        item_text += self.format_enchantments(enchants)
                
                # Add damage info if present
                damage_match = re.search(r'Damage:\s*(\d+)', item_str)
                if damage_match:
                    item_text += f" (Durability: {damage_match.group(1)})"
                
                # Handle backpack contents
                if "backpack" in item_id.lower():
                    items_match = re.search(r'Items:\[(.*?)\]', item_str)
                    if items_match:
                        bp_items = items_match.group(1).split('}, {')
                        if bp_items:
                            item_text += "\n" + self.format_backpack_contents(items_match.group(1))
                
                # Add to appropriate section
                if 0 <= slot <= 8:
                    sections['hotbar'].append(item_text)
                elif 9 <= slot <= 35:
                    sections['main'].append(item_text)
                elif 100 <= slot <= 103:
                    sections['armor'].append(item_text)
                elif slot == -106:
                    sections['offhand'].append(item_text)
                elif slot >= 90:
                    sections['accessories'].append(item_text)
            
            # Add sections to embed
            if sections['hotbar']:
                embed.add_field(
                    name="📱 Hotbar",
                    value="\n".join(sections['hotbar']),
                    inline=False
                )
                
            # Split main inventory into multiple fields if needed
            if sections['main']:
                chunks = self.split_field_content(sections['main'])
                for i, chunk in enumerate(chunks):
                    name = "Main Inventory" if i == 0 else "📦 Main Inventory (continued)"
                    embed.add_field(
                        name=name,
                        value=chunk,
                        inline=False
                    )
                    
            if sections['armor']:
                embed.add_field(
                    name="🛡️ Armor",
                    value="\n".join(sections['armor']),
                    inline=False
                )
                
            if sections['offhand']:
                embed.add_field(
                    name="👋 Offhand",
                    value="\n".join(sections['offhand']),
                    inline=False
                )
                
            if sections['accessories']:
                embed.add_field(
                    name="💍 Accessories",
                    value="\n".join(sections['accessories']),
                    inline=False
                )
            
            if not any(sections.values()):
                embed.description = "Empty inventory"
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error viewing inventory: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ Failed to view inventory! Check logs for details."
            )

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(Minecraft(bot)) 