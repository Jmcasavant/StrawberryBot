"""Games cog for fun strawberry-based games."""
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass

from utils.core import COLORS, setup_logger

logger = setup_logger(__name__)

@dataclass
class Card:
    """Represents a playing card."""
    suit: str
    rank: str
    value: int
    emoji: str

class BlackjackGame:
    """Represents a blackjack game session."""
    
    SUITS = {
        'hearts': '♥️',
        'diamonds': '♦️',
        'clubs': '♣️',
        'spades': '♠️'
    }
    
    RANKS = {
        'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
        '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10
    }
    
    def __init__(self):
        self.deck: List[Card] = []
        self.player_hand: List[Card] = []
        self.player_split_hand: Optional[List[Card]] = None
        self.dealer_hand: List[Card] = []
        self.hand_doubled: bool = False  # Track if main hand was doubled
        self.split_hand_doubled: bool = False  # Track if split hand was doubled
        self.create_deck()
        
    def create_deck(self) -> None:
        """Create and shuffle a new deck of cards."""
        self.deck = []
        for suit_name, suit_emoji in self.SUITS.items():
            for rank, value in self.RANKS.items():
                # Create a visually appealing card emoji
                emoji = f"{rank}{suit_emoji}"
                self.deck.append(Card(suit_name, rank, value, emoji))
        random.shuffle(self.deck)
        
    def deal_card(self) -> Optional[Card]:
        """Deal one card from the deck."""
        if not self.deck:
            self.create_deck()
        return self.deck.pop() if self.deck else None
        
    def calculate_hand(self, hand: List[Card]) -> int:
        """Calculate the value of a hand, handling aces appropriately."""
        value = 0
        aces = 0
        
        # First count non-aces
        for card in hand:
            if card.rank == 'A':
                aces += 1
            else:
                value += card.value
                
        # Then add aces optimally
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
                
        return value
        
    def is_soft_17(self, hand: List[Card]) -> bool:
        """Check if the hand is a soft 17 (contains an ace counted as 11)."""
        if self.calculate_hand(hand) != 17:
            return False
            
        # Count aces that are being counted as 11
        value_without_aces = sum(card.value for card in hand if card.rank != 'A')
        aces = sum(1 for card in hand if card.rank == 'A')
        
        # If we have any aces and one can be counted as 11 (value <= 6)
        return aces > 0 and value_without_aces <= 6
        
    def format_hand(self, hand: List[Card], hide_first: bool = False) -> str:
        """Format a hand for display."""
        if not hand:
            return "No cards"
            
        if hide_first:
            return f"🎴 {' '.join(card.emoji for card in hand[1:])}"
            
        # Format each card with consistent spacing
        return ' '.join(card.emoji for card in hand)

    def format_dealer_hand(self, hand: List[Card], hide_second: bool = False) -> str:
        """Format dealer's hand, optionally hiding the second card."""
        if not hand:
            return "No cards"
            
        if hide_second and len(hand) > 1:
            return f"{hand[0].emoji} 🎴"
            
        return ' '.join(card.emoji for card in hand)

    def can_split(self, hand: List[Card]) -> bool:
        """Check if a hand can be split."""
        return len(hand) == 2 and hand[0].value == hand[1].value
        
    def split_hand(self) -> None:
        """Split the player's hand into two separate hands."""
        if not self.can_split(self.player_hand):
            return
            
        # Create split hand with second card
        self.player_split_hand = [self.player_hand.pop()]
        
        # Deal new cards to both hands
        self.player_hand.append(self.deal_card())
        self.player_hand.append(self.deal_card())

    def has_soft_11(self, hand: List[Card]) -> bool:
        """Check if the hand has a soft 11 (Ace + any card)."""
        if len(hand) != 2:
            return False
        # Check if one card is an Ace and total is 11
        has_ace = any(card.rank == 'A' for card in hand)
        total = self.calculate_hand(hand)
        return has_ace and total == 11

    def can_double_down(self, hand: List[Card]) -> bool:
        """Check if a hand can be doubled down (any initial two cards)."""
        return len(hand) == 2  # Can only double down on initial two cards

class Games(commands.Cog):
    """Games and fun commands."""
    
    # Roulette wheel configuration
    RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
    GREEN_NUMBERS = [0]
    
    WHEEL = {num: 'red' for num in RED_NUMBERS}
    WHEEL.update({num: 'black' for num in BLACK_NUMBERS})
    WHEEL.update({num: 'green' for num in GREEN_NUMBERS})
    
    # Pre-calculate odds
    TOTAL_NUMBERS = len(RED_NUMBERS) + len(BLACK_NUMBERS) + len(GREEN_NUMBERS)
    RED_CHANCE = (len(RED_NUMBERS) / TOTAL_NUMBERS) * 100
    BLACK_CHANCE = (len(BLACK_NUMBERS) / TOTAL_NUMBERS) * 100
    GREEN_CHANCE = (len(GREEN_NUMBERS) / TOTAL_NUMBERS) * 100
    
    # Payout multipliers
    PAYOUT = {
        'red': 2,
        'black': 2,
        'green': 50
    }
    
    # Color emoji mapping
    COLOR_EMOJIS = {
        'red': '🔴',
        'black': '⚫',
        'green': '🟢'
    }
    
    # Footer messages
    FOOTER_MESSAGES = [
        "Better luck next time! 🍀",
        "The house always wins... or does it? 🤔",
        "Time to go double or nothing! 💰",
        "That was a close one! 😅",
        "Keep rolling! 🎲",
        "Fortune favors the bold! ⚔️",
        "May the odds be ever in your favor! 🎯"
    ]
    
    def __init__(self, bot):
        self.bot = bot
        self.roulette_games: Dict[int, bool] = {}
        self.blackjack_games: Dict[int, BlackjackGame] = {}
        self.game_counter = 0  # Add counter for unique game IDs
        
    def get_next_game_id(self) -> str:
        """Generate a unique game ID."""
        self.game_counter += 1
        return f"BJ{self.game_counter:04d}"
        
    async def create_bet_embed(self, user: discord.User, bet: int) -> discord.Embed:
        """Create the initial betting embed."""
        embed = discord.Embed(
            title="Roulette",
            description=(
                f"{user.display_name} is betting 🍓 {bet:,}\n"
                "Choose your bet:"
            ),
            color=COLORS['economy']
        )
        
        embed.add_field(
            name="Options",
            value=(
                f"Red (2x, {self.RED_CHANCE:.1f}%)\n"
                f"Black (2x, {self.BLACK_CHANCE:.1f}%)\n"
                f"Green (50x, {self.GREEN_CHANCE:.1f}%)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Potential Winnings",
            value=(
                f"Red: 🍓 {bet * self.PAYOUT['red']:,}\n"
                f"Black: 🍓 {bet * self.PAYOUT['black']:,}\n"
                f"Green: 🍓 {bet * self.PAYOUT['green']:,}"
            ),
            inline=False
        )
        
        return embed
        
    async def create_result_embed(
        self,
        user: discord.User,
        bet: int,
        bet_choice: str,
        result_number: int,
        won: bool,
        winnings: int,
        new_balance: int
    ) -> discord.Embed:
        """Create the result embed."""
        result_color = self.WHEEL[result_number]
        bet_emoji = self.COLOR_EMOJIS[bet_choice]
        result_emoji = self.COLOR_EMOJIS[result_color]
        
        embed = discord.Embed(
            title="Roulette Results",
            description=(
                f"Result: {result_number} ({result_emoji})\n"
                f"{user.display_name}'s bet: {bet_emoji}"
            ),
            color=COLORS['success'] if won else COLORS['error']
        )
        
        if won:
            # Show net winnings (winnings minus original bet)
            net_winnings = winnings - bet
            embed.add_field(
                name="Winner!",
                value=f"+🍓 {net_winnings:,}",
                inline=True
            )
        else:
            embed.add_field(
                name="Lost",
                value=f"-🍓 {bet:,}",
                inline=True
            )
            
        embed.add_field(
            name="Balance",
            value=f"🍓 {new_balance:,}",
            inline=True
        )
        
        return embed
        
    async def spin_animation(
        self,
        message: discord.Message,
        user: discord.User,
        bet: int,
        bet_choice: str,
        bet_emoji: str
    ) -> Tuple[int, str]:
        """Run the spinning animation and return the result."""
        embed = discord.Embed(
            title="🎰 Strawberry Roulette",
            description=(
                f"**{user.display_name}** bets 🍓 **{bet:,}** on **{bet_emoji}**\n"
                "Spinning the wheel..."
            ),
            color=COLORS['economy']
        )
        
        await message.edit(embed=embed)
        
        # Animation
        numbers = list(self.WHEEL.keys())
        for _ in range(3):
            await asyncio.sleep(0.7)
            temp_number = random.choice(numbers)
            temp_emoji = self.COLOR_EMOJIS[self.WHEEL[temp_number]]
            embed.description = (
                f"**{user.display_name}** bets 🍓 **{bet:,}** on **{bet_emoji}**\n"
                f"Spinning... {temp_number} ({temp_emoji})"
            )
            await message.edit(embed=embed)
            
        result_number = random.choice(numbers)
        return result_number, self.WHEEL[result_number]
        
    @app_commands.command(name='roulette', description='Play strawberry roulette')
    @app_commands.describe(bet="Amount of strawberries to bet")
    async def roulette(self, interaction: discord.Interaction, bet: int) -> None:
        """Play strawberry roulette with an interactive menu."""
        if bet <= 0:
            await interaction.response.send_message("❌ Bet amount must be positive!", ephemeral=True)
            return
            
        data = self.bot.game.get_player_data(interaction.user.id)
        if data['strawberries'] < bet:
            await interaction.response.send_message(
                f"❌ You only have 🍓 {data['strawberries']:,} strawberries!",
                ephemeral=True
            )
            return
            
        if interaction.user.id in self.roulette_games:
            await interaction.response.send_message(
                "❌ You already have a roulette game in progress!",
                ephemeral=True
            )
            return
            
        self.roulette_games[interaction.user.id] = True
        
        try:
            # Show betting options
            embed = await self.create_bet_embed(interaction.user, bet)
            await interaction.response.send_message(embed=embed)
            selection_msg = await interaction.original_response()
            
            # Add reactions
            try:
                for emoji in self.COLOR_EMOJIS.values():
                    await selection_msg.add_reaction(emoji)
            except discord.HTTPException as e:
                logger.error(f"Failed to add reactions: {e}")
                await interaction.followup.send("❌ Error setting up the game!", ephemeral=True)
                return
            
            def reaction_check(reaction, user):
                return (
                    user == interaction.user and
                    str(reaction.emoji) in self.COLOR_EMOJIS.values() and
                    reaction.message.id == selection_msg.id
                )
            
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=reaction_check)
                emoji = str(reaction.emoji)
                bet_choice = {emoji: color for color, emoji in self.COLOR_EMOJIS.items()}[emoji]
                
                await selection_msg.delete()
            except asyncio.TimeoutError:
                await selection_msg.edit(content="❌ Bet cancelled - no choice made in time!", embed=None)
                await selection_msg.clear_reactions()
                return
            except discord.NotFound:
                pass
                
            # Run game
            spin_msg = await interaction.channel.send("🎰 Spinning...")
            result_number, result_color = await self.spin_animation(
                spin_msg,
                interaction.user,
                bet,
                bet_choice,
                self.COLOR_EMOJIS[bet_choice]
            )
            
            # Calculate results
            won = bet_choice == result_color
            winnings = bet * self.PAYOUT[bet_choice] if won else 0
            
            # Update balance
            if won:
                await self.bot.game.add_strawberries(interaction.user.id, winnings - bet)  # Add winnings minus original bet
            else:
                await self.bot.game.remove_strawberries(interaction.user.id, bet)  # Just remove the original bet
                
            new_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
            
            # Show results
            result_embed = await self.create_result_embed(
                interaction.user,
                bet,
                bet_choice,
                result_number,
                won,
                winnings,
                new_balance
            )
            
            await spin_msg.edit(embed=result_embed)
            
        except Exception as e:
            logger.error(f"Error in roulette game: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ An error occurred during the game. Please try again.",
                ephemeral=True
            )
        finally:
            if interaction.user.id in self.roulette_games:
                del self.roulette_games[interaction.user.id]
                
    async def create_blackjack_embed(
        self,
        user: discord.User,
        game: BlackjackGame,
        bet: int,
        hide_dealer: bool = True,
        game_over: bool = False,
        result: str = "",
        split_hand_index: Optional[int] = None,
        balance_change: int = 0,
        current_balance: Optional[int] = None,
        starting_balance: Optional[int] = None,
        insurance_offered: bool = False,
        insurance_bet: Optional[int] = None,
        insurance_result: Optional[str] = None,
        results: Optional[List[str]] = None
    ) -> discord.Embed:
        """Create the blackjack game embed."""
        # Get the active hand
        active_hand = (game.player_split_hand if split_hand_index == 1 
                      else game.player_hand)
        player_value = game.calculate_hand(active_hand)
        dealer_value = game.calculate_hand(game.dealer_hand)
        
        embed = discord.Embed(
            title="Blackjack",
            color=COLORS['economy']
        )
        
        # Show dealer's hand
        if insurance_offered:
            # During insurance offer, show first card (Ace) and hide second
            dealer_hand = game.format_dealer_hand(game.dealer_hand, hide_second=True)
            dealer_score = "?"  # Still hide total during insurance
        else:
            dealer_hand = game.format_hand(game.dealer_hand, hide_first=hide_dealer)
        dealer_score = "?" if hide_dealer else f"**{dealer_value}**"
            
        embed.add_field(
            name="Dealer's Hand",
            value=f"{dealer_hand}\n💭 Value: {dealer_score}",
            inline=False
        )
        
        # Show player's hands
        if game.player_split_hand is not None:
            # Show both hands when split
            hand1_value = game.calculate_hand(game.player_hand)
            hand2_value = game.calculate_hand(game.player_split_hand)
            
            # Format hands with clearer indicators for which is active
            hand1_prefix = "▶️" if split_hand_index == 0 else "  "
            hand2_prefix = "▶️" if split_hand_index == 1 else "  "
            
            embed.add_field(
                name=f"{user.display_name}'s Hands",
                value=(
                    f"**Hand 1:**\n"
                    f"{hand1_prefix} {game.format_hand(game.player_hand)}\n"
                    f"💭 Value: **{hand1_value}**\n"
                    f"\n"  # Extra line for visual separation
                    f"**Hand 2:**\n"
                    f"{hand2_prefix} {game.format_hand(game.player_split_hand)}\n"
                    f"💭 Value: **{hand2_value}**"
                ),
                inline=False
            )
            
            # If game is over, show results in a separate field for clarity
            if game_over and results and len(results) > 1:
                embed.add_field(
                    name="Hand Results",
                    value=(
                        f"**Hand 1:** {results[0]}\n"
                        f"**Hand 2:** {results[1]}"
                    ),
                    inline=False
                )
        else:
            # Show single hand
            player_hand = game.format_hand(active_hand)
            embed.add_field(
                name=f"{user.display_name}'s Hand",
                value=f"{player_hand}\n💭 Value: **{player_value}**",
                inline=False
            )
        
        # Add bet and balance info
        bet_field = "💰 **Bet Breakdown:**\n"
        
        # Calculate total bet amount
        total_bet = bet * (2 if game.hand_doubled else 1)
        if game.player_split_hand:
            split_bet = bet * (2 if game.split_hand_doubled else 1)
            total_bet += split_bet
            
        # Show main hand bet
        bet_field += f"Main Hand: 🍓 **{bet:,}**"
        if game.hand_doubled:
            bet_field += f" → 🍓 **{bet * 2:,}** (Doubled)"
        bet_field += "\n"
        
        # Show split hand bet if applicable
        if game.player_split_hand:
            bet_field += f"Split Hand: 🍓 **{bet:,}**"
            if game.split_hand_doubled:
                bet_field += f" → 🍓 **{split_bet:,}** (Doubled)"
            bet_field += "\n"
            
        # Show total bet amount
        if game.player_split_hand or game.hand_doubled or game.split_hand_doubled:
            bet_field += f"Total Bet: 🍓 **{total_bet:,}**\n"
            
        # Add insurance bet info if applicable
        if insurance_bet is not None:
            bet_field += f"\n🛡️ **Insurance:**\n"
            bet_field += f"Insurance Bet: 🍓 **{insurance_bet:,}**"
            if insurance_result:
                if "WIN" in insurance_result:
                    bet_field += f" → Won: 🍓 **+{insurance_bet * 2:,}**"
                else:
                    bet_field += f" → Lost"
            bet_field += "\n"
            
        # Show game result if game is over
        if game_over:
            bet_field += f"\n\n💫 **Game Results:**\n"
            if results and len(results) > 1:
                # For split hands, just show total outcome
                if all("wins" in r.lower() for r in results):
                    bet_field += "Both hands lost\n"
                elif all("win" in r.lower() for r in results):
                    bet_field += "Both hands won!\n"
                elif all("push" in r.lower() for r in results):
                    bet_field += "Both hands pushed\n"
                else:
                    # Mixed results are shown in the Hand Results field
                    bet_field += "See Hand Results above\n"
            else:
                bet_field += f"{result}\n"
                
            if "Push" in result:
                bet_field += f"🔄 Bet returned\n"
            elif balance_change > 0:
                bet_field += f"💰 Won: 🍓 **+{balance_change:,}**\n"
            else:
                bet_field += f"💸 Lost: 🍓 **{balance_change:,}**\n"
                
        # Always show current balance with clear indication of locked bets
        if current_balance is not None:
            bet_field += f"\n💳 **Balance Summary:**\n"
            bet_field += f"Starting Balance: 🍓 **{starting_balance:,}**\n"
            if game_over:
                bet_field += f"Final Balance: 🍓 **{current_balance:,}**"
            else:
                bet_field += f"Current Balance: 🍓 **{current_balance:,}**\n"
                bet_field += f"Locked in Bets: 🍓 **{total_bet:,}**\n"
                bet_field += f"Potential Win: 🍓 **{current_balance + (total_bet * 2):,}**"
        
        embed.add_field(
            name="Bet & Balance Information",
            value=bet_field,
            inline=True
        )
        
        if game_over:
            if "win" in result.lower():
                color = COLORS['success']
                result = f"✨ {result}"
            elif "push" in result.lower():
                color = COLORS['info']
                result = f"🔄 {result}"
            else:
                color = COLORS['error']
                result = f"❌ {result}"
            embed.color = color
            embed.add_field(
                name="Result",
                value=result,
                inline=True
            )
        else:
            if not hide_dealer or insurance_offered:  # Show options during insurance and regular play
                if insurance_offered:
                    options = [
                        "[1] YES   🛡️ Take insurance (costs half your bet)",
                        "[2] NO    ❌ Skip insurance"
                    ]
                else:
                    options = [
                        "[1] HIT   👊 Draw another card",
                        "[2] STAND ✋ Keep current hand"
                    ]
                    
                    # Add split option if available
                    if (not game.player_split_hand and 
                        game.can_split(game.player_hand)):
                        options.append("[3] SPLIT ⚔️ Split matching cards")
                        
                    # Add double down option if initial hand
                    active_hand = game.player_split_hand if split_hand_index == 1 else game.player_hand
                    if game.can_double_down(active_hand):
                        options.append("[4] DOUBLE 💰 Double bet and draw one card")
                
                embed.add_field(
                    name="Your Options",
                    value=f"```\n{chr(10).join(options)}\n```",
                    inline=False
                )
                
        # Add game state footer
        if not game_over:
            if hide_dealer:
                state = "🎲 Dealing cards..."
            elif insurance_offered:
                state = "🛡️ Insurance offered - Dealer showing Ace"
            elif game.player_split_hand:
                state = f"🎮 Playing Hand {split_hand_index + 1}/2..."
            else:
                state = "🎮 Your turn..."
            embed.set_footer(text=state)
            
        return embed
        
    @app_commands.command(name='blackjack', description='Play blackjack with strawberries')
    @app_commands.describe(bet="Amount of strawberries to bet")
    async def blackjack(self, interaction: discord.Interaction, bet: int) -> None:
        """Play blackjack with strawberry betting."""
        game_id = self.get_next_game_id()
        logger.info(f"[{game_id}] New blackjack game started by {interaction.user.name} (ID: {interaction.user.id})")
        
        if bet <= 0:
            logger.info(f"[{game_id}] Rejected - Invalid bet amount: {bet}")
            await interaction.response.send_message("❌ Bet amount must be positive!", ephemeral=True)
            return
                
        data = self.bot.game.get_player_data(interaction.user.id)
        starting_balance = data['strawberries']  # Store starting balance before any bets
        
        if starting_balance < bet:
            logger.info(f"[{game_id}] Rejected - Insufficient balance. Has: {starting_balance}, Needed: {bet}")
            await interaction.response.send_message(
                f"❌ You only have 🍓 {starting_balance:,} strawberries!",
                ephemeral=True
            )
            return
            
        if interaction.user.id in self.blackjack_games:
            await interaction.response.send_message(
                "❌ You already have a blackjack game in progress!",
                ephemeral=True
            )
            return
            
        # Deduct bet immediately to prevent exploits
        await self.bot.game.remove_strawberries(interaction.user.id, bet)
        logger.info(f"[BLACKJACK] {interaction.user.name} (ID: {interaction.user.id}) started game with bet: {bet}")
        logger.info(f"[BALANCE] Initial bet deducted. User {interaction.user.id} bet: -{bet}")

        # Get initial balance after bet deduction
        current_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
            
        # Start new game
        game = BlackjackGame()
        self.blackjack_games[interaction.user.id] = game
        split_hand_index = 0  # Initialize split hand index at the start
        game_over = False  # Initialize game_over flag
        
        try:
            # Initial deal - one card at a time
            # First card to player
            first_card = game.deal_card()
            game.player_hand.append(first_card)
            logger.info(f"[CARDS] Player dealt first card: {first_card.rank}{first_card.suit}")
            embed = await self.create_blackjack_embed(
                interaction.user,
                game,
                bet,
                hide_dealer=True,
                split_hand_index=split_hand_index,
                current_balance=current_balance,
                starting_balance=starting_balance
            )
            await interaction.response.send_message(embed=embed)
            game_msg = await interaction.original_response()
            await asyncio.sleep(1)

            # First card to dealer (face up)
            first_dealer_card = game.deal_card()
            game.dealer_hand.append(first_dealer_card)
            logger.info(f"[CARDS] Dealer dealt first card (up): {first_dealer_card.rank}{first_dealer_card.suit}")
            embed = await self.create_blackjack_embed(
                interaction.user,
                game,
                bet,
                hide_dealer=True,  # Still hide at first to maintain animation
                split_hand_index=split_hand_index,
                current_balance=current_balance,
                starting_balance=starting_balance
            )
            await game_msg.edit(embed=embed)
            await asyncio.sleep(1)

            # Second card to player
            second_player_card = game.deal_card()
            game.player_hand.append(second_player_card)
            logger.info(f"[CARDS] Player dealt second card: {second_player_card.rank}{second_player_card.suit}")
            embed = await self.create_blackjack_embed(
                interaction.user,
                game,
                bet,
                hide_dealer=True,
                split_hand_index=split_hand_index,
                current_balance=current_balance,
                starting_balance=starting_balance
            )
            await game_msg.edit(embed=embed)
            await asyncio.sleep(1)

            # Second card to dealer (face down)
            second_dealer_card = game.deal_card()
            game.dealer_hand.append(second_dealer_card)
            logger.info(f"[CARDS] Dealer dealt second card (down): {second_dealer_card.rank}{second_dealer_card.suit}")
            
            # Check for insurance if dealer's first card is an Ace
            insurance_taken = False
            insurance_bet = None
            insurance_result = None
            if first_dealer_card.rank == 'A':  # Check first card
                logger.info(f"[INSURANCE] Insurance offered - Dealer showing Ace ({first_dealer_card.rank}{first_dealer_card.suit})")
                # Offer insurance with first card visible
                embed = await self.create_blackjack_embed(
                    interaction.user,
                    game,
                    bet,
                    hide_dealer=False,  # Show dealer's first card for insurance
                    insurance_offered=True,
                    split_hand_index=split_hand_index,
                    current_balance=current_balance,
                    starting_balance=starting_balance
                )
                await game_msg.edit(embed=embed)
                
                # Add insurance reactions
                await game_msg.add_reaction('🛡️')  # Yes
                await game_msg.add_reaction('❌')   # No
                
                try:
                    reaction, user = await self.bot.wait_for(
                        'reaction_add',
                        timeout=60.0,
                        check=lambda reaction, user: (
                            user == interaction.user and
                            str(reaction.emoji) in ['🛡️', '❌'] and
                            reaction.message.id == game_msg.id
                        )
                    )
                    
                    took_insurance = str(reaction.emoji) == '🛡️'
                    try:
                        await reaction.remove(interaction.user)
                    except:
                        pass
                    
                    insurance_bet = bet // 2  # Calculate insurance bet
                    if took_insurance:
                        # Check if player has enough for insurance
                        if self.bot.game.get_player_data(interaction.user.id)['strawberries'] < insurance_bet:
                            await interaction.followup.send(
                                "❌ Not enough strawberries for insurance!",
                                ephemeral=True
                            )
                            insurance_bet = None  # Reset if they can't afford it
                        else:
                            insurance_taken = True
                            # Place insurance bet
                            await self.bot.game.remove_strawberries(interaction.user.id, insurance_bet)
                            logger.info(f"[INSURANCE] User {interaction.user.id} took insurance for {insurance_bet}")
                            
                            # Update display to show insurance bet
                            current_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
                            embed = await self.create_blackjack_embed(
                                interaction.user,
                                game,
                                bet,
                                hide_dealer=False,
                                insurance_offered=True,
                                split_hand_index=split_hand_index,
                                insurance_bet=insurance_bet,
                                current_balance=current_balance,
                                starting_balance=starting_balance
                            )
                            await game_msg.edit(embed=embed)
                            await asyncio.sleep(2)  # Give time to see insurance bet placed
                            
                            # Check if dealer has blackjack
                            dealer_value = game.calculate_hand(game.dealer_hand)
                            if dealer_value == 21:
                                # Insurance wins 2:1 (pays double the insurance bet)
                                insurance_win = insurance_bet * 2
                                await self.bot.game.add_strawberries(interaction.user.id, insurance_win)
                                insurance_result = "WIN"
                                logger.info(f"[INSURANCE] Insurance WIN - User {interaction.user.id} won {insurance_win} (2:1 payout on {insurance_bet} bet) (Dealer had: {game.dealer_hand[0].rank}{game.dealer_hand[0].suit}, {game.dealer_hand[1].rank}{game.dealer_hand[1].suit})")
                                
                                # Update display to show insurance win
                                current_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
                                embed = await self.create_blackjack_embed(
                                    interaction.user,
                                    game,
                                    bet,
                                    hide_dealer=False,
                                    insurance_offered=True,
                                    split_hand_index=split_hand_index,
                                    insurance_bet=insurance_bet,
                                    insurance_result=insurance_result,
                                    current_balance=current_balance,
                                    starting_balance=starting_balance
                                )
                                await game_msg.edit(embed=embed)
                                await asyncio.sleep(2)  # Give time to see insurance result
                            else:
                                insurance_result = "LOSS"
                                logger.info(f"[INSURANCE] Insurance LOSS - User {interaction.user.id} lost {insurance_bet} (Dealer had: {game.dealer_hand[0].rank}{game.dealer_hand[0].suit}, {game.dealer_hand[1].rank}{game.dealer_hand[1].suit})")
                                
                                # Update display to show insurance loss
                                current_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
                                embed = await self.create_blackjack_embed(
                                    interaction.user,
                                    game,
                                    bet,
                                    hide_dealer=False,
                                    insurance_offered=True,
                                    split_hand_index=split_hand_index,
                                    insurance_bet=insurance_bet,
                                    insurance_result=insurance_result,
                                    current_balance=current_balance,
                                    starting_balance=starting_balance
                                )
                                await game_msg.edit(embed=embed)
                                await asyncio.sleep(2)  # Give time to see insurance result
                    else:
                        insurance_bet = None  # Reset if they decline insurance
                    
                    # Clear insurance reactions
                    await game_msg.clear_reactions()
                    
                except asyncio.TimeoutError:
                    game_msg.clear_reactions()
                    await interaction.followup.send(
                        "Insurance declined (timeout)",
                        ephemeral=True
                    )

            # Update display after insurance decision
            embed = await self.create_blackjack_embed(
                interaction.user,
                game,
                bet,
                hide_dealer=True,  # Keep second card hidden
                split_hand_index=split_hand_index,
                insurance_bet=insurance_bet,
                insurance_result=insurance_result,
                current_balance=current_balance,
                starting_balance=starting_balance
            )
            await game_msg.edit(embed=embed)
            await asyncio.sleep(1)
            
            # Store these values early but don't reveal yet
            player_value = game.calculate_hand(game.player_hand)
            dealer_value = game.calculate_hand(game.dealer_hand)
            has_blackjack = player_value == 21 or dealer_value == 21
            
            # Now check for natural blackjack after insurance has been handled
            if has_blackjack:
                game_over = True  # Set game over for natural blackjack
                # Natural blackjack
                if player_value == 21 and dealer_value == 21:
                    result = "Push (Both have blackjack)"
                    winnings = bet  # Return the original bet
                    logger.info(f"[OUTCOME] PUSH - Both blackjack. User {interaction.user.id} cards: {[f'{c.rank}{c.suit}' for c in game.player_hand]}, Dealer cards: {[f'{c.rank}{c.suit}' for c in game.dealer_hand]}")
                elif player_value == 21:
                    result = "Blackjack! You win 2.5x!"
                    winnings = int(bet * 2.5)
                    logger.info(f"[OUTCOME] WIN - Player blackjack. User {interaction.user.id} cards: {[f'{c.rank}{c.suit}' for c in game.player_hand]}, Dealer cards: {[f'{c.rank}{c.suit}' for c in game.dealer_hand]}")
                else:
                    result = "Dealer has blackjack"
                    winnings = 0
                    logger.info(f"[OUTCOME] LOSS - Dealer blackjack. User {interaction.user.id} cards: {[f'{c.rank}{c.suit}' for c in game.player_hand]}, Dealer cards: {[f'{c.rank}{c.suit}' for c in game.dealer_hand]}")
                    
                # Calculate balance change
                balance_change = winnings - bet
                
                # Update balance (only add winnings since bet was already deducted)
                if winnings > 0:
                    await self.bot.game.add_strawberries(interaction.user.id, winnings)
                    logger.info(f"[BALANCE] Natural blackjack payout. User {interaction.user.id} won: +{winnings} (Net: {balance_change})")
                    
                # Keep the pre-game balance for display
                display_balance = current_balance  # Use the balance from before winnings were added
                logger.info(f"[{game_id}] Final balance: {self.bot.game.get_player_data(interaction.user.id)['strawberries']}")
                
                # Show final results
                results = None  # No additional results for natural blackjack
                embed = await self.create_blackjack_embed(
                    interaction.user,
                    game,
                    bet,
                    hide_dealer=False,
                    game_over=True,
                    result=result,
                    results=results,
                    balance_change=balance_change,
                    current_balance=display_balance,  # Use pre-game balance
                    split_hand_index=split_hand_index,
                    insurance_bet=insurance_bet,
                    insurance_result=insurance_result,
                    starting_balance=starting_balance
                )
                await game_msg.edit(embed=embed)
                return
                
            # Regular game - continue with first move if no blackjack
            current_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
            embed = await self.create_blackjack_embed(
                interaction.user, 
                game, 
                bet,
                hide_dealer=False,  # Show dealer's up card for first decision
                split_hand_index=split_hand_index,
                current_balance=current_balance,
                starting_balance=starting_balance
            )
            
            await game_msg.edit(embed=embed)
            
            # Add action reactions
            await game_msg.add_reaction('👊')  # Hit
            await game_msg.add_reaction('✋')  # Stand
            if game.can_split(game.player_hand) and not game.player_split_hand:
                # Only show split option if player can afford it
                if self.bot.game.get_player_data(interaction.user.id)['strawberries'] >= bet:
                    await game_msg.add_reaction('⚔️')  # Split
            if game.can_double_down(game.player_hand):
                # Only show double down option if player can afford it
                if self.bot.game.get_player_data(interaction.user.id)['strawberries'] >= bet:
                    await game_msg.add_reaction('💰')  # Double down
            
            # Player's turn
            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        'reaction_add',
                        timeout=30.0,
                        check=lambda reaction, user: (
                            user == interaction.user and
                            str(reaction.emoji) in ['👊', '✋', '⚔️', '💰'] and
                            reaction.message.id == game_msg.id
                        )
                    )
                    
                    action = str(reaction.emoji)
                    try:
                        await reaction.remove(interaction.user)
                    except:
                        pass

                    if action == '⚔️' and game.can_split(game.player_hand):
                        if self.bot.game.get_player_data(interaction.user.id)['strawberries'] < bet:
                            logger.info(f"[SPLIT] Failed - User {interaction.user.id} insufficient balance for split")
                            await interaction.followup.send(
                                "❌ Not enough strawberries to split!",
                                ephemeral=True
                            )
                            continue
                            
                        await self.bot.game.remove_strawberries(interaction.user.id, bet)
                        logger.info(f"[SPLIT] User {interaction.user.id} split hand. Additional bet: -{bet}")
                        game.split_hand()
                        
                        # Update display with split hands and new balance
                        current_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
                        embed = await self.create_blackjack_embed(
                            interaction.user,
                            game,
                            bet,
                            hide_dealer=False,
                            split_hand_index=split_hand_index,
                            current_balance=current_balance,
                            starting_balance=starting_balance
                        )
                        await game_msg.edit(embed=embed)
                        continue
                        
                    if action == '👊':  # Hit
                        active_hand = game.player_split_hand if split_hand_index == 1 else game.player_hand
                        card = game.deal_card()
                        active_hand.append(card)
                        player_value = game.calculate_hand(active_hand)
                        
                        # Update display after hit
                        current_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
                        embed = await self.create_blackjack_embed(
                            interaction.user,
                            game,
                            bet,
                            hide_dealer=False,
                            split_hand_index=split_hand_index,
                            current_balance=current_balance,
                            starting_balance=starting_balance
                        )
                        await game_msg.edit(embed=embed)
                        
                        # Check for bust or 21
                        if player_value > 21:
                            if game.player_split_hand and split_hand_index == 0:
                                # If first hand busts, move to second hand
                                split_hand_index = 1
                                embed = await self.create_blackjack_embed(
                                    interaction.user,
                                    game,
                                    bet,
                                    hide_dealer=False,
                                    split_hand_index=split_hand_index,
                                    current_balance=current_balance,
                                    starting_balance=starting_balance
                                )
                                await game_msg.edit(embed=embed)
                                continue
                            else:
                                # If no split hand or second hand busts, end turn
                                break
                        elif player_value == 21:
                            # Automatically stand at 21
                            if game.player_split_hand and split_hand_index == 0:
                                # Move to second hand if available
                                split_hand_index = 1
                                embed = await self.create_blackjack_embed(
                                    interaction.user,
                                    game,
                                    bet,
                                    hide_dealer=False,
                                    split_hand_index=split_hand_index,
                                    current_balance=current_balance,
                                    starting_balance=starting_balance
                                )
                                await game_msg.edit(embed=embed)
                                continue
                            else:
                                # End turn if no split hand or on second hand
                                break
                        continue
                        
                    if action == '✋':  # Stand
                        if game.player_split_hand and split_hand_index == 0:
                            # Move to second hand
                            split_hand_index = 1
                            current_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
                            embed = await self.create_blackjack_embed(
                                interaction.user,
                                game,
                                bet,
                                hide_dealer=False,
                                split_hand_index=split_hand_index,
                                current_balance=current_balance,
                                starting_balance=starting_balance
                            )
                            await game_msg.edit(embed=embed)
                            continue
                        else:
                            break  # Move to dealer's turn
                        
                    if action == '💰':  # Double down
                        active_hand = game.player_split_hand if split_hand_index == 1 else game.player_hand
                        if not game.can_double_down(active_hand):
                            continue
                            
                        # Check if player can afford double down
                        if self.bot.game.get_player_data(interaction.user.id)['strawberries'] < bet:
                            await interaction.followup.send(
                                "❌ Not enough strawberries to double down!",
                                ephemeral=True
                            )
                            continue
                            
                        # Remove additional bet
                        await self.bot.game.remove_strawberries(interaction.user.id, bet)
                        logger.info(f"[DOUBLE] User {interaction.user.id} doubled bet: -{bet}")
                        
                        # Set doubled flag for current hand
                        if split_hand_index == 1:
                            game.split_hand_doubled = True
                        else:
                            game.hand_doubled = True
                            
                        # Deal one card and end turn for this hand
                        card = game.deal_card()
                        active_hand.append(card)
                        
                        # Update display with new balance
                        current_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
                        embed = await self.create_blackjack_embed(
                            interaction.user,
                            game,
                            bet,
                            hide_dealer=False,
                            split_hand_index=split_hand_index,
                            current_balance=current_balance,
                            starting_balance=starting_balance
                        )
                        await game_msg.edit(embed=embed)
                        
                        if game.player_split_hand and split_hand_index == 0:
                            # Move to second hand if available
                            split_hand_index = 1
                            continue
                        else:
                            break  # Move to dealer's turn
                        
                except asyncio.TimeoutError:
                    game_over = True
                    embed = await self.create_blackjack_embed(
                        interaction.user,
                        game,
                        bet,
                        hide_dealer=False,
                        game_over=True,
                        result="Game cancelled - no action taken in time",
                        split_hand_index=split_hand_index,
                        current_balance=self.bot.game.get_player_data(interaction.user.id)['strawberries'],
                        starting_balance=starting_balance
                    )
                    await game_msg.edit(embed=embed)
                    return

                except asyncio.TimeoutError:
                    game_over = True
                    embed = await self.create_blackjack_embed(
                    interaction.user,
                    game,
                    bet,
                    hide_dealer=False,
                    game_over=True,
                    result="Game cancelled - no action taken in time",
                    split_hand_index=split_hand_index,
                    current_balance=self.bot.game.get_player_data(interaction.user.id)['strawberries'],
                    starting_balance=starting_balance
                )
                await game_msg.edit(embed=embed)
                return
                
            # Dealer's turn after all player actions are complete
            if not game_over:
                game_over = True  # Set game over for normal game completion
                
                # Check if player has busted before dealer plays
                player_value = game.calculate_hand(game.player_hand)
                split_value = game.calculate_hand(game.player_split_hand) if game.player_split_hand else 22
                
                # Only play dealer's hand if at least one player hand hasn't busted
                if player_value <= 21 or split_value <= 21:
                    # Dealer draws until 17 or higher
                    while (game.calculate_hand(game.dealer_hand) < 17 or 
                           game.is_soft_17(game.dealer_hand)):
                        game.dealer_hand.append(game.deal_card())
                    
                dealer_value = game.calculate_hand(game.dealer_hand)
                
                # Calculate results for both hands
                results = []
                total_winnings = 0
                hands = [game.player_hand]
                bets = [bet]  # Track bet for each hand
                
                # Add split hand if it exists
                if game.player_split_hand:
                    hands.append(game.player_split_hand)
                    bets.append(bet)
                
                # Calculate results for each hand independently
                for i, (hand, current_bet) in enumerate(zip(hands, bets)):
                    player_value = game.calculate_hand(hand)
                    hand_cards = [f"{c.rank}{c.suit}" for c in hand]
                    doubled = (i == 0 and game.hand_doubled) or (i == 1 and game.split_hand_doubled)
                    
                    if doubled:
                        current_bet *= 2
                        logger.info(f"[{game_id}] Hand {i+1} was doubled - Bet: {current_bet}")
                    
                    logger.info(f"[{game_id}] Evaluating Hand {i+1}: Cards={hand_cards}, Value={player_value}, Bet={current_bet}")
                    
                    if player_value > 21:
                        results.append("Dealer wins (Bust)")
                        logger.info(f"[{game_id}] Hand {i+1} BUST - Value: {player_value}")
                        # No need to do anything with balance here since bet was already deducted at start
                        logger.info(f"[{game_id}] Hand {i+1} lost bet of {current_bet}")
                        continue
                    
                    dealer_cards = [f"{c.rank}{c.suit}" for c in game.dealer_hand]
                    logger.info(f"[{game_id}] Dealer final hand: Cards={dealer_cards}, Value={dealer_value}")
                    
                    if dealer_value > 21:
                        results.append("Win (Dealer busts)")
                        total_winnings += current_bet * 2  # Win pays 2x bet
                        logger.info(f"[{game_id}] Hand {i+1} WIN (Dealer bust) - Won: {current_bet * 2}")
                    elif dealer_value > player_value:
                        results.append("Dealer wins")
                        logger.info(f"[{game_id}] Hand {i+1} LOSS - Dealer: {dealer_value} > Player: {player_value}")
                    elif dealer_value < player_value:
                        results.append("Win")
                        total_winnings += current_bet * 2  # Win pays 2x bet
                        logger.info(f"[{game_id}] Hand {i+1} WIN - Player: {player_value} > Dealer: {dealer_value}")
                    else:
                        results.append("Push")
                        total_winnings += current_bet  # Return the original bet for push
                        logger.info(f"[{game_id}] Hand {i+1} PUSH - Both: {player_value}, Returning bet: {current_bet}")
                
                # Format final result for split hands
                if len(results) > 1:
                    result = f"Hand 1: {results[0]}\nHand 2: {results[1]}"
                else:
                    result = results[0]
                
                # Calculate total bet including any doubles
                total_bet = bet * (2 if game.hand_doubled else 1)
                if game.player_split_hand:
                    total_bet += bet * (2 if game.split_hand_doubled else 1)
                
                # Calculate balance change for display
                balance_change = total_winnings - total_bet
                
                # Add any winnings or returned bets
                if total_winnings > 0:
                    if "Push" in result:  # Push case
                        # For push, we only need to return the original bet since it was already deducted
                        await self.bot.game.add_strawberries(interaction.user.id, total_bet)
                        logger.info(f"[{game_id}] Returned push bet to balance: +{total_bet}")
                        balance_change = 0  # No net change for push
                        display_balance = starting_balance  # Use starting balance for push since no change
                    else:
                        await self.bot.game.add_strawberries(interaction.user.id, total_winnings)
                        logger.info(f"[{game_id}] Added winnings to balance: +{total_winnings}")
                        display_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']  # Show actual final balance
                else:
                    # For losses, show the actual final balance (starting balance - bet)
                    display_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
                
                # Log final balance state
                final_balance = self.bot.game.get_player_data(interaction.user.id)['strawberries']
                logger.info(f"[{game_id}] Game over - Starting balance: {starting_balance}, Final balance: {final_balance}, Net change: {final_balance - starting_balance}")
                
                # Show final results
                embed = await self.create_blackjack_embed(
                    interaction.user,
                    game,
                    bet,
                    hide_dealer=False,
                    game_over=True,
                    result=result,
                    results=results,
                    balance_change=balance_change,
                    current_balance=display_balance,  # Use pre-game balance
                    split_hand_index=split_hand_index,
                    insurance_bet=insurance_bet,
                    insurance_result=insurance_result,
                    starting_balance=starting_balance
                )
                await game_msg.edit(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in blackjack game: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ An error occurred during the game. Please try again.",
                ephemeral=True
            )
        finally:
            if interaction.user.id in self.blackjack_games:
                del self.blackjack_games[interaction.user.id]

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(Games(bot)) 