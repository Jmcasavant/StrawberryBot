# The Strawberry Boy Discord Bot 🍓

A fun Discord bot that manages strawberries, plays games, and follows users in voice channels.

## Features

- 🎮 **Games**
  - Strawberry Roulette: Bet your strawberries with different odds
- 💰 **Economy**
  - Daily rewards
  - Transfer strawberries between users
  - Check your strawberry balance
- 🎵 **Voice**
  - Join voice channels
  - Follow users between channels
- 🛠️ **Admin**
  - Purge messages
  - Give/set strawberry amounts

## Commands

The bot primarily uses Discord's slash commands (/) for all functionality.

### Available Commands
- `/strawberries [user]` - Check strawberry balance
- `/daily` - Get your daily strawberries
- `/transfer <user> <amount>` - Transfer strawberries to another user
- `/roulette <bet>` - Play strawberry roulette with interactive betting
- `/join` - Join your voice channel
- `/leave` - Leave current voice channel
- `/follow <user>` - Follow a user between channels
- `/unfollow` - Stop following the current user
- `/purge [amount] [user]` - Delete messages (Admin only)
- `/set <user> <amount>` - Set user's strawberry count (Admin only)
- `/cleanup [days]` - Clean up inactive users (Admin only)

Note: Slash commands (/) provide better autocomplete and parameter hints.

## Setup

1. Clone the repository
2. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_BOT_TOKEN=your_token_here
   ```
3. Install dependencies:
   ```bash
   pip install discord.py python-dotenv
   ```
4. Run the bot:
   ```bash
   python src/bot.py
   ```

## Project Structure

```
TheStrawberryBoy/
├── src/
│   ├── __init__.py
│   ├── bot.py              # Main bot setup and event handlers
│   ├── cogs/
│   │   ├── __init__.py
│   │   ├── admin.py       # Admin commands
│   │   ├── voice.py       # Voice channel commands
│   │   ├── economy.py     # Strawberry economy commands
│   │   └── games.py       # Games like roulette
│   ├── utils/
│   │   ├── __init__.py
│   │   └── strawberry_game.py  # StrawberryGame class
├── data/
│   └── strawberry_data.json
├── .env
└── README.md
```

## Contributing

Feel free to submit issues and enhancement requests! 