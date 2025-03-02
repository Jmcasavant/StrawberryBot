# 🍓 StrawberryBot

A fun Discord bot built with discord.py that lets users collect and manage strawberries while playing games.

## 📁 Project Structure
```
StrawberryBot/
├── src/                    # Source code
│   ├── bot.py             # Main bot initialization
│   ├── cogs/              # Bot command categories
│   │   ├── economy.py     # Economy system
│   │   └── games.py       # Game commands
│   ├── utils/             # Utility modules
│   │   ├── cache/        # Redis caching system
│   │   ├── database/     # Database operations
│   │   ├── helpers/      # Helper functions
│   │   └── core.py       # Core utilities
│   └── config/           # Configuration files
│       └── settings.py   # Bot settings
├── logs/                  # Log files
├── data/                  # Data storage
├── run.py                # Bot launcher
└── requirements.txt      # Dependencies
```

## 🚀 Features
- 🍓 Strawberry collection and management
- 💰 Daily rewards with streak bonuses
- 📊 Leaderboard system
- 🎮 Interactive games
- 💾 Persistent data storage
- ⚡ Redis caching for performance

## 🛠 Setup

1. Clone the repository:
```bash
git clone https://github.com/jmcasavant/StrawberryBot.git
cd StrawberryBot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file:
```env
DISCORD_TOKEN=your_token_here
OWNER_ID=your_id_here
REDIS_URL=your_redis_url_here  # Optional, for caching
```

5. Start the bot:
```bash
python run.py
```

## 📝 Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support
Join our [Discord server](https://discord.gg/your-invite) for support and updates.