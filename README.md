# The Strawberry Boy Discord Bot 🍓

A fun Discord bot that manages strawberries, plays games, and provides Minecraft server integration.

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
- 🎮 **Minecraft Integration**
  - Server status monitoring
  - Player information and inventory viewing
  - Server command execution
  - RCON integration

## Commands

### General Commands
- `/strawberries [user]` - Check strawberry balance
- `/daily` - Get your daily strawberries
- `/transfer <user> <amount>` - Transfer strawberries to another user
- `/roulette <bet>` - Play strawberry roulette with interactive betting

### Voice Commands
- `/join` - Join your voice channel
- `/leave` - Leave current voice channel
- `/follow <user>` - Follow a user between channels
- `/unfollow` - Stop following the current user

### Admin Commands
- `/purge [amount] [user]` - Delete messages (Admin only)
- `/set <user> <amount>` - Set user's strawberry count (Admin only)
- `/cleanup [days]` - Clean up inactive users (Admin only)

### Minecraft Commands (Admin only)
- `/mc status` - Check server status and online players
- `/mc command <command>` - Execute any Minecraft server command
- `/mc playerinfo <player>` - Get detailed player information:
  - ❤️ Current health
  - 📍 Position coordinates
  - 🎮 Game mode
  - ✨ XP level
- `/mc inventory <player>` - View a player's inventory contents

## Setup

1. Clone the repository
2. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_BOT_TOKEN=your_token_here
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure RCON settings in `src/cogs/minecraft.py`:
   ```python
   RCON_CONFIG = {
       'ip': 'your_server_ip',      # Your Minecraft server IP
       'port': 25575,               # Your RCON port (default: 25575)
       'password': 'your_password'  # Your RCON password
   }
   ```
5. Run the bot:
   ```bash
   python src/bot.py
   ```

## Minecraft Integration

The bot uses RCON to communicate with your Minecraft server. To set up:

1. Enable RCON in your `server.properties`:
   ```
   enable-rcon=true
   rcon.password=your_secure_password
   rcon.port=25575
   ```
2. Update the RCON settings in the code as shown in the setup instructions above
3. The bot will automatically connect to your Minecraft server on startup

## Project Structure

```
StrawberryBot/
├── src/                      # Source code directory
│   ├── bot.py               # Main bot setup and event handlers
│   ├── cogs/                # Discord bot command categories
│   │   ├── admin.py        # Administrative commands
│   │   ├── economy.py      # Strawberry economy system
│   │   ├── games.py        # User-facing game commands (roulette, etc.)
│   │   ├── minecraft.py    # Minecraft server integration
│   │   └── voice.py        # Voice channel features
│   └── utils/              # Utility modules
│       ├── core.py         # Core settings and utilities
│       ├── base_cog.py     # Base cog functionality
│       └── strawberry_game.py  # Backend game logic (economy, stats, data management)
├── data/                    # Data storage directory
├── logs/                    # Log files directory
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

### Directory Overview

- `src/`: Main source code
  - `cogs/`: Each file represents a category of bot commands
    - `games.py`: Implements user-facing game commands and interactions
  - `utils/`: Shared utilities and core functionality
    - `strawberry_game.py`: Handles game state, economy logic, and data persistence
- `data/`: Persistent data storage (e.g., user stats, settings)
- `logs/`: Daily log files for debugging and monitoring

## Contributing

Feel free to submit issues and enhancement requests! 