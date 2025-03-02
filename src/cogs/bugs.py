"""Bug reporting and management commands."""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
from datetime import datetime

from src.utils.core import setup_logger, COLORS

logger = setup_logger(__name__)

class Bugs(commands.Cog):
    """Bug reporting and management commands."""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name='report', description='Report a bug in a game')
    @app_commands.describe(
        game_type="The type of game where the bug occurred",
        description="Detailed description of what happened"
    )
    @app_commands.choices(game_type=[
        app_commands.Choice(name="Blackjack", value="blackjack"),
        app_commands.Choice(name="Roulette", value="roulette")
    ])
    async def report(
        self,
        interaction: discord.Interaction,
        game_type: str,
        description: str
    ) -> None:
        """Report a bug in a game."""
        try:
            # Get relevant game state based on game type
            game_state = {}
            if game_type == "blackjack":
                if interaction.user.id in self.bot.blackjack_games:
                    game = self.bot.blackjack_games[interaction.user.id]
                    game_state = {
                        "player_hand": [f"{c.rank}{c.suit}" for c in game.player_hand],
                        "dealer_hand": [f"{c.rank}{c.suit}" for c in game.dealer_hand],
                        "split_hand": [f"{c.rank}{c.suit}" for c in (game.player_split_hand or [])],
                        "hand_doubled": game.hand_doubled,
                        "split_hand_doubled": game.split_hand_doubled
                    }
            
            # Create the bug report
            report_id = self.bot.bug_tracker.create_report(
                user_id=interaction.user.id,
                game_type=game_type,
                description=description,
                game_state=game_state
            )
            
            # Send confirmation
            embed = discord.Embed(
                title="🐛 Bug Report Submitted",
                description=(
                    f"Thank you for reporting this bug! We'll investigate the issue.\n"
                    f"Your report ID is: `{report_id}`"
                ),
                color=COLORS['info']
            )
            
            embed.add_field(
                name="Game",
                value=game_type.title(),
                inline=True
            )
            
            embed.add_field(
                name="Description",
                value=description,
                inline=False
            )
            
            if game_state:
                embed.add_field(
                    name="Game State Captured",
                    value="✅ Current game state was recorded",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Bug report {report_id} created by user {interaction.user.id}")
            
        except Exception as e:
            logger.error(f"Error creating bug report: {e}")
            await interaction.response.send_message(
                "❌ Failed to create bug report! Please try again.",
                ephemeral=True
            )
            
    @app_commands.command(name='bugs', description='View bug reports')
    @app_commands.describe(
        report_id="Specific report ID to view",
        status="Filter by status"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Open", value="open"),
        app_commands.Choice(name="Investigating", value="investigating"),
        app_commands.Choice(name="Fixed", value="fixed"),
        app_commands.Choice(name="Closed", value="closed")
    ])
    @app_commands.default_permissions(administrator=True)
    async def bugs(
        self,
        interaction: discord.Interaction,
        report_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> None:
        """View bug reports (Admin only)."""
        try:
            if report_id:
                # View specific report
                report = self.bot.bug_tracker.get_report(report_id)
                if not report:
                    await interaction.response.send_message(
                        f"❌ Bug report `{report_id}` not found!",
                        ephemeral=True
                    )
                    return
                    
                embed = discord.Embed(
                    title=f"🐛 Bug Report {report.id}",
                    color=COLORS['info']
                )
                
                # Add reporter info
                reporter = self.bot.get_user(report.user_id)
                embed.add_field(
                    name="Reporter",
                    value=reporter.mention if reporter else f"User {report.user_id}",
                    inline=True
                )
                
                # Add game type
                embed.add_field(
                    name="Game",
                    value=report.game_type.title(),
                    inline=True
                )
                
                # Add status
                embed.add_field(
                    name="Status",
                    value=report.status.title(),
                    inline=True
                )
                
                # Add timestamp
                timestamp = datetime.fromisoformat(report.timestamp)
                embed.add_field(
                    name="Reported",
                    value=discord.utils.format_dt(timestamp, 'R'),
                    inline=True
                )
                
                # Add description
                embed.add_field(
                    name="Description",
                    value=report.description,
                    inline=False
                )
                
                # Add game state if available
                if report.game_state:
                    state_str = "\n".join(
                        f"{k}: {v}"
                        for k, v in report.game_state.items()
                    )
                    embed.add_field(
                        name="Game State",
                        value=f"```\n{state_str}\n```",
                        inline=False
                    )
                    
                # Add admin notes if any
                if report.admin_notes:
                    embed.add_field(
                        name="Admin Notes",
                        value=report.admin_notes,
                        inline=False
                    )
                    
                await interaction.response.send_message(embed=embed)
                
            else:
                # List all reports
                reports = self.bot.bug_tracker.get_all_reports(status)
                if not reports:
                    await interaction.response.send_message(
                        "No bug reports found!" +
                        (f" (with status: {status})" if status else ""),
                        ephemeral=True
                    )
                    return
                    
                # Create summary embed
                embed = discord.Embed(
                    title="🐛 Bug Reports",
                    description=f"Found {len(reports)} reports" +
                              (f" with status: {status}" if status else ""),
                    color=COLORS['info']
                )
                
                # Add each report as a field
                for report in reports[:25]:  # Limit to 25 reports
                    reporter = self.bot.get_user(report.user_id)
                    reporter_name = reporter.name if reporter else f"User {report.user_id}"
                    
                    timestamp = datetime.fromisoformat(report.timestamp)
                    relative_time = discord.utils.format_dt(timestamp, 'R')
                    
                    value = (
                        f"By: {reporter_name}\n"
                        f"Game: {report.game_type.title()}\n"
                        f"Status: {report.status.title()}\n"
                        f"Reported: {relative_time}"
                    )
                    
                    embed.add_field(
                        name=f"Report {report.id}",
                        value=value,
                        inline=True
                    )
                    
                if len(reports) > 25:
                    embed.set_footer(text=f"Showing 25/{len(reports)} reports")
                    
                await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            logger.error(f"Error viewing bug reports: {e}")
            await interaction.response.send_message(
                "❌ Failed to retrieve bug reports!",
                ephemeral=True
            )
            
    @app_commands.command(name='update_bug', description='Update a bug report')
    @app_commands.describe(
        report_id="The ID of the report to update",
        status="New status for the report",
        notes="Admin notes to add/update"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Open", value="open"),
        app_commands.Choice(name="Investigating", value="investigating"),
        app_commands.Choice(name="Fixed", value="fixed"),
        app_commands.Choice(name="Closed", value="closed")
    ])
    @app_commands.default_permissions(administrator=True)
    async def update_bug(
        self,
        interaction: discord.Interaction,
        report_id: str,
        status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> None:
        """Update a bug report's status or add notes (Admin only)."""
        try:
            if not (status or notes):
                await interaction.response.send_message(
                    "❌ Please provide either a new status or notes to update!",
                    ephemeral=True
                )
                return
                
            success = self.bot.bug_tracker.update_report(
                report_id=report_id,
                status=status,
                admin_notes=notes
            )
            
            if not success:
                await interaction.response.send_message(
                    f"❌ Bug report `{report_id}` not found!",
                    ephemeral=True
                )
                return
                
            # Get updated report
            report = self.bot.bug_tracker.get_report(report_id)
            
            # Create confirmation embed
            embed = discord.Embed(
                title=f"✅ Bug Report {report_id} Updated",
                color=COLORS['success']
            )
            
            if status:
                embed.add_field(
                    name="New Status",
                    value=status.title(),
                    inline=True
                )
                
            if notes:
                embed.add_field(
                    name="Admin Notes",
                    value=notes,
                    inline=False
                )
                
            await interaction.response.send_message(embed=embed)
            
            # Try to notify the reporter if status changed to fixed
            if status == "fixed":
                try:
                    reporter = self.bot.get_user(report.user_id)
                    if reporter:
                        notify_embed = discord.Embed(
                            title="🐛 Bug Report Update",
                            description=f"Your bug report `{report_id}` has been marked as fixed!",
                            color=COLORS['success']
                        )
                        
                        if notes:
                            notify_embed.add_field(
                                name="Admin Notes",
                                value=notes,
                                inline=False
                            )
                            
                        await reporter.send(embed=notify_embed)
                except:
                    pass  # Ignore errors in notification
                    
        except Exception as e:
            logger.error(f"Error updating bug report: {e}")
            await interaction.response.send_message(
                "❌ Failed to update bug report!",
                ephemeral=True
            )

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(Bugs(bot)) 